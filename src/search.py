"""High-level search facade built on the GRAG retriever."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

from pymongo.collection import Collection

from .config import EMBEDDING_MODEL
from .database import MongoDBClient
from .retrieval import GragConfig, GragRetriever
from .utils import embed_text, get_embedding_model

logger = logging.getLogger(__name__)


class SearchManager:
    """Expose graph-aware retrieval while preserving the legacy API surface."""

    def __init__(
        self,
        client: Optional[MongoDBClient] = None,
        collection_name: str = "nodes",
        embedding_model_name: Optional[str] = None,
        grag_config: Optional[GragConfig] = None,
        auto_refresh: bool = True,
    ) -> None:
        self.client = client or MongoDBClient()
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name or EMBEDDING_MODEL
        self._collection: Optional[Collection] = None
        self._embedding_model = None
        self._retriever: Optional[GragRetriever] = None
        self._grag_config = grag_config or GragConfig()
        self._auto_refresh = auto_refresh

    # ------------------------------------------------------------------
    # Lazy properties
    # ------------------------------------------------------------------

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            self._collection = self.client.get_collection(self.collection_name)
        return self._collection

    @property
    def embedding_model(self):
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model(self.embedding_model_name)
        return self._embedding_model

    @property
    def retriever(self) -> GragRetriever:
        if self._retriever is None:
            self._retriever = GragRetriever(
                collection=self.collection,
                embed_function=embed_text,
                config=self._grag_config,
            )
        elif self._auto_refresh:
            # Refresh lazily to avoid rebuilding the graph on every request
            self._retriever.refresh_index(force=False)
        return self._retriever

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def refresh_index(self, force: bool = True) -> None:
        """Force a rebuild of the cached graph index."""
        self.retriever.refresh_index(force=force)

    def get_search_stats(self) -> Dict[str, Any]:
        """Return combined collection/index statistics for monitoring."""
        total_nodes = self.collection.count_documents({})
        index_stats = self.retriever.get_index_stats()
        nodes_with_embeddings = index_stats.get("total_nodes", 0)
        nodes_without_embeddings = max(total_nodes - nodes_with_embeddings, 0)

        stats = {
            "total_nodes": total_nodes,
            "total_nodes_with_embeddings": nodes_with_embeddings,
            "nodes_without_embeddings": nodes_without_embeddings,
            "embedding_model": self.embedding_model_name,
            "indexed_edges": index_stats.get("total_edges", 0),
            "embedding_dim": index_stats.get("embedding_dim"),
            "graph_last_built_at": index_stats.get("last_built_at"),
        }
        logger.info("Search stats: %s", stats)
        return stats

    # ------------------------------------------------------------------
    # Core search flows
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Primary search entry point using graph-aware retrieval."""
        try:
            return self.retriever.retrieve(query, top_k=top_k, threshold=threshold)
        except Exception as exc:
            logger.exception("GRAG search failed: %s", exc)
            raise

    # Backwards compatibility for older callers --------------------------------
    def cosine_search(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Alias retained for compatibility with historical code paths."""
        return self.search(query, top_k=top_k, threshold=threshold)

    def search_by_content(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.search(query, top_k=top_k)

    def batch_search(self, queries: Sequence[str], top_k: int = 5, threshold: float = 0.0) -> Dict[str, List[Dict[str, Any]]]:
        results: Dict[str, List[Dict[str, Any]]] = {}
        for i, query in enumerate(queries):
            logger.info("Processing batch query %s/%s", i + 1, len(queries))
            try:
                results[query] = self.search(query, top_k=top_k, threshold=threshold)
            except Exception as exc:
                logger.error("Failed to process batch query '%s': %s", query, exc)
                results[query] = []
        return results

    def get_similar_nodes(self, node_id: str, top_k: int = 5, exclude_self: bool = True) -> List[Dict[str, Any]]:
        """Return nodes that resemble the provided ``node_id``."""
        record = self.collection.find_one({"nodeid": node_id})
        if not record:
            logger.warning("Node %s not found", node_id)
            return []

        query_parts = [record.get("text", ""), record.get("notes", ""), record.get("richText", "")]
        query = "\n".join(part for part in query_parts if part).strip()
        if not query:
            logger.warning("Node %s has no textual content for similarity search", node_id)
            return []

        raw_results = self.search(query, top_k=top_k + (1 if exclude_self else 0), threshold=-1.0)
        filtered = [item for item in raw_results if not exclude_self or item.get("nodeid") != node_id]
        return filtered[:top_k]

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def get_model_specific_search_config(self) -> Dict[str, Any]:
        model = self.embedding_model
        return {
            "model_id": getattr(model, "MODEL_ID", self.embedding_model_name),
            "model_name": getattr(model, "MODEL_NAME", self.embedding_model_name),
            "max_seq_length": getattr(model, "MAX_SEQ_LENGTH", None),
            "recommended_top_k": 10,
            "recommended_threshold": 0.0,
            "supports_batch": True,
            "similarity_metric": "grag",
        }
