"""GRAG-inspired graph retrieval for the oncology knowledge graph.

This module ports the graph-centric retrieval strategy from the GRAG project
into the ``oncology-kg-ai`` codebase.  It builds an in-memory graph index that
combines the existing node embeddings with structural signals (hierarchy links,
manual cross-links) and uses that index to answer semantic queries by
retrieving the most relevant subgraphs.

The implementation focuses on the *retrieval* portion of GRAG – selecting an
informative, query-aware subgraph – while remaining compatible with the
existing MongoDB data model.  Downstream consumers (answer generation, CLI
search) continue to receive node-level payloads, augmented with contextual
metadata that describes how each node was selected from the graph.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

import networkx as nx
import numpy as np
import torch
import torch.nn.functional as F
from bson import ObjectId
from pymongo.collection import Collection

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GragConfig:
    """Tunable parameters for GRAG retrieval.

    Attributes:
        hops: Maximum number of hops to explore from each seed node.
        seed_top_k: Number of high-similarity seed nodes to expand per query.
        candidate_multiplier: Multiplier applied to ``top_k`` to decide how
            many candidates to score before truncating the final list.
        node_weight: Weight applied to the direct node/query similarity.
        subgraph_weight: Weight applied to the subgraph similarity signal.
        hop_decay: Multiplicative decay applied per hop when distributing
            subgraph scores to nodes further away from the seed.
        cache_ttl_seconds: Time-to-live for the cached graph index.  ``None``
            disables automatic rebuilds.
        max_context_neighbors: Maximum number of neighboring nodes to include
            in the contextual metadata returned with each hit.
        debug_logging: Enable verbose logging to help tune the retrieval flow.
    """

    hops: int = 2
    seed_top_k: int = 24
    candidate_multiplier: float = 3.0
    node_weight: float = 0.6
    subgraph_weight: float = 0.4
    hop_decay: float = 0.75
    cache_ttl_seconds: Optional[float] = 15 * 60
    max_context_neighbors: int = 6
    debug_logging: bool = False

    def __post_init__(self) -> None:
        if self.hops < 0:
            raise ValueError("hops must be non-negative")
        if self.seed_top_k <= 0:
            raise ValueError("seed_top_k must be positive")
        if self.candidate_multiplier < 1.0:
            raise ValueError("candidate_multiplier must be >= 1.0")
        if not (0.0 <= self.node_weight <= 1.0):
            raise ValueError("node_weight must be in [0, 1]")
        if not (0.0 <= self.subgraph_weight <= 1.0):
            raise ValueError("subgraph_weight must be in [0, 1]")
        if self.node_weight + self.subgraph_weight == 0:
            raise ValueError("node_weight and subgraph_weight cannot both be 0")
        if not (0.0 < self.hop_decay <= 1.0):
            raise ValueError("hop_decay must be in (0, 1]")
        if self.max_context_neighbors < 0:
            raise ValueError("max_context_neighbors must be >= 0")


# ---------------------------------------------------------------------------
# Internal data containers
# ---------------------------------------------------------------------------


def _coerce_object_id(value: Any) -> Any:
    """Best-effort conversion of Mongo references to :class:`ObjectId`.

    The source collections sometimes contain stringified ObjectIds.  This helper
    normalises those so the graph builder can reliably match edges.
    """

    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, dict) and "$oid" in value:
        try:
            return ObjectId(value["$oid"])
        except Exception:  # pragma: no cover - defensive guard
            return value
    if isinstance(value, str):
        try:
            return ObjectId(value)
        except Exception:
            return value
    return value


def _ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _ensure_string_list(items: Iterable[Any]) -> List[str]:
    return [str(item) for item in items if isinstance(item, str) or item is not None]


@dataclass
class GraphNode:
    """Lightweight representation of a node in the graph index."""

    index: int
    object_id: ObjectId
    object_id_str: str
    nodeid: str
    text: str
    rich_text: str
    notes: str
    links: List[str] = field(default_factory=list)
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    category: Optional[str] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    linked_ids: List[str] = field(default_factory=list)

    def to_result_payload(self) -> Dict[str, Any]:
        """Return the user-facing payload for this node."""

        return {
            "nodeid": self.nodeid,
            "id": self.object_id_str,
            "text": self.text or "",
            "richText": self.rich_text or "",
            "notes": self.notes or "",
            "links": list(self.links),
            "attributes": list(self.attributes),
        }


class GraphIndex:
    """Builds and caches a graph view of the MongoDB ``nodes`` collection."""

    _PROJECTION = {
        "nodeid": 1,
        "text": 1,
        "richText": 1,
        "notes": 1,
        "links": 1,
        "attributes": 1,
        "embedding": 1,
        "parentID": 1,
        "children": 1,
        "linkedNodes": 1,
        "category": 1,
    }

    def __init__(self, collection: Collection):
        self._collection = collection
        self._nodes: List[GraphNode] = []
        self._id_to_index: Dict[Any, int] = {}
        self._nodeid_to_index: Dict[str, int] = {}
        self._edge_relations: Dict[Tuple[int, int], Set[str]] = {}
        self._graph = nx.Graph()
        self._embedding_matrix: torch.Tensor = torch.empty((0, 0), dtype=torch.float32)
        self._embedding_dim: Optional[int] = None
        self._stats: Dict[str, Any] = {}
        self._build_index()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def node_embeddings(self) -> torch.Tensor:
        return self._embedding_matrix

    @property
    def embedding_dim(self) -> int:
        if self._embedding_dim is None:
            raise RuntimeError("Graph index has no embeddings.")
        return self._embedding_dim

    @property
    def num_nodes(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    @property
    def stats(self) -> Dict[str, Any]:
        return dict(self._stats)

    def get_node(self, index: int) -> GraphNode:
        return self._nodes[index]

    def sorted_neighbors(self, index: int) -> List[int]:
        neighbors = list(self._graph.neighbors(index))
        neighbors.sort(key=lambda idx: self._graph.degree(idx), reverse=True)
        return neighbors

    def describe_relations(self, index: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return neighbour summaries and relation types for context."""

        neighbours = self.sorted_neighbors(index)
        if limit is not None:
            neighbours = neighbours[:limit]
        context = []
        for neighbour_idx in neighbours:
            key = tuple(sorted((index, neighbour_idx)))
            relations = sorted(self._edge_relations.get(key, set()))
            neighbour_node = self.get_node(neighbour_idx)
            context.append({
                "nodeid": neighbour_node.nodeid,
                "relations": relations,
            })
        return context

    def shortest_path_lengths(self, source_index: int, cutoff: int) -> Dict[int, int]:
        """Compute hop distances up to ``cutoff`` for a given node."""

        if cutoff == 0:
            return {source_index: 0}
        lengths = nx.single_source_shortest_path_length(self._graph, source_index, cutoff=cutoff)
        return {int(idx): int(distance) for idx, distance in lengths.items()}

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    def _build_index(self) -> None:
        """Populate nodes, embeddings and structural edges from MongoDB."""

        cursor = self._collection.find({"embedding": {"$exists": True}}, self._PROJECTION)
        embeddings: List[np.ndarray] = []
        relation_queue: List[Tuple[Any, Any, str]] = []

        for record in cursor:
            embedding = record.get("embedding")
            if not embedding:
                continue
            embedding_array = np.asarray(embedding, dtype=np.float32)
            if embedding_array.ndim != 1:
                logger.debug("Skipping node %s with invalid embedding shape %s", record.get("_id"), embedding_array.shape)
                continue

            if self._embedding_dim is None:
                self._embedding_dim = embedding_array.shape[0]
            elif embedding_array.shape[0] != self._embedding_dim:
                logger.warning(
                    "Skipping node %s due to mismatched embedding dimension (expected %s, got %s)",
                    record.get("_id"),
                    self._embedding_dim,
                    embedding_array.shape[0],
                )
                continue

            node_index = len(self._nodes)
            nodeid = record.get("nodeid") or str(record.get("_id"))
            node = GraphNode(
                index=node_index,
                object_id=record.get("_id"),
                object_id_str=str(record.get("_id")),
                nodeid=nodeid,
                text=(record.get("text") or "").strip(),
                rich_text=(record.get("richText") or "").strip(),
                notes=(record.get("notes") or "").strip(),
                links=_ensure_string_list(_ensure_list(record.get("links"))),
                attributes=_ensure_list(record.get("attributes")),
                category=record.get("category"),
                parent_id=self._maybe_stringify(record.get("parentID")),
                children_ids=[self._maybe_stringify(child) for child in _ensure_list(record.get("children"))],
                linked_ids=[self._maybe_stringify(linked) for linked in _ensure_list(record.get("linkedNodes"))],
            )

            self._nodes.append(node)
            self._id_to_index[record.get("_id")] = node_index
            self._nodeid_to_index[nodeid] = node_index
            embeddings.append(embedding_array)

            relation_queue.extend(self._collect_relations(record, node.object_id))

        if not self._nodes:
            logger.warning("Graph index built with zero nodes. Retrieval will return empty results.")
            self._embedding_matrix = torch.empty((0, 0), dtype=torch.float32)
            self._stats = {"total_nodes": 0, "total_edges": 0}
            return

        embedding_matrix = np.vstack(embeddings)
        tensor = torch.from_numpy(embedding_matrix)
        self._embedding_matrix = F.normalize(tensor, dim=1, eps=1e-12)

        self._graph.add_nodes_from(range(len(self._nodes)))
        for src, dst, relation in relation_queue:
            self._bind_relation(src, dst, relation)

        self._stats = {
            "total_nodes": len(self._nodes),
            "total_edges": self._graph.number_of_edges(),
            "embedding_dim": self._embedding_dim,
        }

        logger.info(
            "Built graph index with %s nodes, %s edges (embedding dim %s)",
            self._stats["total_nodes"],
            self._stats["total_edges"],
            self._stats["embedding_dim"],
        )

    @staticmethod
    def _maybe_stringify(value: Any) -> Optional[str]:
        value = _coerce_object_id(value)
        if value is None:
            return None
        return str(value)

    def _collect_relations(self, record: Dict[str, Any], current_id: ObjectId) -> List[Tuple[Any, Any, str]]:
        relations: List[Tuple[Any, Any, str]] = []

        parent_id = _coerce_object_id(record.get("parentID"))
        if parent_id:
            relations.append((current_id, parent_id, "hierarchy"))

        for child in _ensure_list(record.get("children")):
            child_id = _coerce_object_id(child)
            if child_id:
                relations.append((current_id, child_id, "hierarchy"))

        for linked in _ensure_list(record.get("linkedNodes")):
            linked_id = _coerce_object_id(linked)
            if linked_id:
                relations.append((current_id, linked_id, "link"))

        return relations

    def _bind_relation(self, src_id: Any, dst_id: Any, relation: str) -> None:
        src_index = self._resolve_index(src_id)
        dst_index = self._resolve_index(dst_id)
        if src_index is None or dst_index is None or src_index == dst_index:
            return

        key = tuple(sorted((src_index, dst_index)))
        relation_set = self._edge_relations.setdefault(key, set())
        relation_set.add(relation)

        if not self._graph.has_edge(src_index, dst_index):
            self._graph.add_edge(src_index, dst_index)

    def _resolve_index(self, reference: Any) -> Optional[int]:
        if reference in self._id_to_index:
            return self._id_to_index[reference]
        # Fallback: some references may come through as strings -> match nodeid
        if isinstance(reference, str) and reference in self._nodeid_to_index:
            return self._nodeid_to_index[reference]
        return None


# ---------------------------------------------------------------------------
# Public retriever
# ---------------------------------------------------------------------------


class GragRetriever:
    """Graph-aware retrieval that replaces brute-force cosine search."""

    def __init__(
        self,
        collection: Collection,
        embed_function: Callable[[str], List[float]],
        config: Optional[GragConfig] = None,
    ) -> None:
        self._collection = collection
        self._embed_function = embed_function
        self._config = config or GragConfig()
        self._index: Optional[GraphIndex] = None
        self._last_built_at: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Index lifecycle
    # ------------------------------------------------------------------

    def refresh_index(self, force: bool = False) -> None:
        if self._index is not None and not force:
            if self._config.cache_ttl_seconds is None:
                return
            if self._last_built_at is not None:
                elapsed = (datetime.now(timezone.utc) - self._last_built_at).total_seconds()
                if elapsed < self._config.cache_ttl_seconds:
                    return
        if self._config.debug_logging:
            logger.debug("Rebuilding GRAG index (force=%s)", force)
        self._index = GraphIndex(self._collection)
        self._last_built_at = datetime.now(timezone.utc)

    def _ensure_index(self) -> GraphIndex:
        if self._index is None:
            self.refresh_index(force=True)
        else:
            self.refresh_index(force=False)
        if self._index is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Graph index could not be created")
        return self._index

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_index_stats(self) -> Dict[str, Any]:
        index = self._ensure_index()
        stats = index.stats
        stats["last_built_at"] = self._last_built_at.isoformat() if self._last_built_at else None
        return stats

    def retrieve(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Main search entry point.

        Args:
            query: Natural language query.
            top_k: Number of results to return.
            threshold: Minimum score required.  Scores follow cosine similarity
                conventions and are clamped to ``[-1, 1]``.
        """

        query = (query or "").strip()
        if not query:
            raise ValueError("Query must be a non-empty string")

        index = self._ensure_index()
        if index.num_nodes == 0:
            return []

        query_vector = self._embed_query(query, index.embedding_dim, index.node_embeddings.dtype)
        node_similarities = torch.matmul(index.node_embeddings, query_vector)

        seeds = min(index.num_nodes, max(top_k, self._config.seed_top_k))
        seed_scores, seed_indices = torch.topk(node_similarities, seeds)

        final_scores = torch.full((index.num_nodes,), fill_value=-1.0, dtype=torch.float32)
        candidate_indices: Set[int] = set()
        node_context: Dict[int, Dict[str, Any]] = {}

        for seed_idx, seed_score in zip(seed_indices.tolist(), seed_scores.tolist()):
            distances = index.shortest_path_lengths(seed_idx, self._config.hops)
            if seed_idx not in distances:
                distances[seed_idx] = 0
            subgraph_nodes = list(distances.keys())
            candidate_indices.update(subgraph_nodes)

            subgraph_embedding = self._compute_subgraph_embedding(index, subgraph_nodes)
            subgraph_score = float(torch.matmul(subgraph_embedding, query_vector))

            for node_idx in subgraph_nodes:
                node_score = float(node_similarities[node_idx])
                hop_distance = distances[node_idx]
                hop_factor = self._config.hop_decay ** hop_distance if self._config.hops > 0 else 1.0

                combined_score = (
                    self._config.node_weight * node_score
                    + self._config.subgraph_weight * subgraph_score * hop_factor
                )

                combined_score = float(max(min(combined_score, 1.0), -1.0))

                if combined_score > final_scores[node_idx]:
                    final_scores[node_idx] = combined_score
                    node_context[node_idx] = {
                        "seed_node": index.get_node(seed_idx).nodeid,
                        "hop_distance": hop_distance,
                        "subgraph_score": subgraph_score,
                        "local_similarity": node_score,
                    }

        # Ensure every candidate has at least its direct similarity score
        for idx in candidate_indices:
            if final_scores[idx] < node_similarities[idx]:
                final_scores[idx] = float(node_similarities[idx])

        if not candidate_indices:
            candidate_indices = set(seed_indices.tolist())
            for idx in candidate_indices:
                final_scores[idx] = float(node_similarities[idx])

        max_candidates = min(index.num_nodes, int(max(top_k, top_k * self._config.candidate_multiplier)))
        ordered_candidates = sorted(candidate_indices, key=lambda i: final_scores[i], reverse=True)[:max_candidates]

        results: List[Dict[str, Any]] = []
        for idx in ordered_candidates:
            score = float(final_scores[idx])
            if score < threshold:
                continue
            node = index.get_node(idx)
            payload = node.to_result_payload()
            payload["score"] = score
            context = node_context.get(idx, {
                "seed_node": node.nodeid,
                "hop_distance": 0,
                "subgraph_score": float(node_similarities[idx]),
                "local_similarity": float(node_similarities[idx]),
            })
            if self._config.max_context_neighbors > 0:
                context["neighbors"] = index.describe_relations(idx, self._config.max_context_neighbors)
            payload["graph_context"] = context
            results.append(payload)

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _embed_query(self, query: str, expected_dim: int, dtype: torch.dtype) -> torch.Tensor:
        embedding = self._embed_function(query)
        if embedding is None:
            raise RuntimeError("Embedding function returned None")
        vector = torch.as_tensor(embedding, dtype=dtype)
        if vector.ndim != 1:
            raise RuntimeError("Query embedding must be one-dimensional")
        if vector.shape[0] != expected_dim:
            raise RuntimeError(
                f"Query embedding dimension {vector.shape[0]} does not match index dimension {expected_dim}"
            )
        return F.normalize(vector, dim=0, eps=1e-12)

    @staticmethod
    def _compute_subgraph_embedding(index: GraphIndex, node_indices: List[int]) -> torch.Tensor:
        nodes_tensor = index.node_embeddings[node_indices]
        pooled = nodes_tensor.mean(dim=0)
        return F.normalize(pooled, dim=0, eps=1e-12)


__all__ = ["GragConfig", "GragRetriever", "GraphIndex", "GraphNode"]
