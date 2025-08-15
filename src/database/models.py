"""
Data models for MongoDB documents.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class NodeDocument:
    """Represents a node document in the MongoDB collection."""
    
    _id: Any
    text: Optional[str] = None
    richText: Optional[str] = None
    notes: Optional[str] = None
    links: Optional[List[str]] = None
    attributes: Optional[List[Dict[str, str]]] = None
    embedding: Optional[List[float]] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NodeDocument':
        """
        Create NodeDocument from dictionary.
        
        Args:
            data: Dictionary representation of the node
            
        Returns:
            NodeDocument instance
        """
        return cls(
            _id=data.get('_id'),
            text=data.get('text'),
            richText=data.get('richText'),
            notes=data.get('notes'),
            links=data.get('links', []),
            attributes=data.get('attributes', []),
            embedding=data.get('embedding')
        )
    
    def to_dict(self) -> dict:
        """
        Convert NodeDocument to dictionary.
        
        Returns:
            Dictionary representation of the node
        """
        result = {
            '_id': self._id,
        }
        
        if self.text is not None:
            result['text'] = self.text
        if self.richText is not None:
            result['richText'] = self.richText
        if self.notes is not None:
            result['notes'] = self.notes
        if self.links:
            result['links'] = self.links
        if self.attributes:
            result['attributes'] = self.attributes
        if self.embedding is not None:
            result['embedding'] = self.embedding
            
        return result
    
    def generate_text_content(self) -> str:
        """
        Generate a combined text representation of the node.
        
        Returns:
            Combined text content from all text fields
        """
        parts: List[str] = []

        text = (self.text or "").strip()
        if text:
            parts.append(f"Title: {text}")

        rich_text = (self.richText or "").strip()
        if rich_text:
            parts.append(f"Description: {rich_text}")

        notes = (self.notes or "").strip()
        if notes:
            parts.append(f"Notes: {notes}")

        links = self.links or []
        if links:
            str_links = [l for l in links if isinstance(l, str)]
            if str_links:
                parts.append("Links: " + ", ".join(str_links))

        attributes = self.attributes or []
        attr_parts: List[str] = []
        for attr in attributes:
            if not isinstance(attr, dict):
                continue
            name = (attr.get("name") or "").strip()
            value = (attr.get("value") or "").strip()
            if name and value:
                attr_parts.append(f"{name}: {value}")
        if attr_parts:
            parts.append("Attributes: " + ", ".join(attr_parts))

        return " ".join(parts)
    
    def has_embedding(self) -> bool:
        """
        Check if the node has an embedding.
        
        Returns:
            True if embedding exists, False otherwise
        """
        return self.embedding is not None and len(self.embedding) > 0
