# Soul Layer - Knowledge Management Module
"""
Knowledge Graph for storing and retrieving learned information.

Features:
- Concept nodes with attributes
- Weighted connections between concepts
- Semantic similarity search
- Importance tracking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import json
import threading
import os


class KnowledgeType(Enum):
    """Types of knowledge."""
    FACT = "fact"                    # Factual information
    CONCEPT = "concept"               # Abstract concept
    PROCEDURE = "procedure"           # How-to knowledge
    PREFERENCE = "preference"        # User preferences
    RELATIONSHIP = "relationship"     # Relationship between entities
    EXPERIENCE = "experience"         # Learned from interaction


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph."""
    id: str
    content: str                     # Main content
    knowledge_type: KnowledgeType
    attributes: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5          # 0-1, importance score
    confidence: float = 0.5           # 0-1, confidence in accuracy
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    source: str = "interaction"       # Where this was learned
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "knowledge_type": self.knowledge_type.value,
            "attributes": self.attributes,
            "importance": self.importance,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "source": self.source,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeNode":
        return cls(
            id=data["id"],
            content=data["content"],
            knowledge_type=KnowledgeType(data["knowledge_type"]),
            attributes=data.get("attributes", {}),
            importance=data.get("importance", 0.5),
            confidence=data.get("confidence", 0.5),
            created_at=data.get("created_at", datetime.now().isoformat()),
            accessed_at=data.get("accessed_at", datetime.now().isoformat()),
            access_count=data.get("access_count", 0),
            source=data.get("source", "interaction"),
            tags=data.get("tags", []),
        )


@dataclass
class KnowledgeConnection:
    """Connection between knowledge nodes."""
    source_id: str
    target_id: str
    relationship: str                  # e.g., "is_a", "part_of", "related_to"
    weight: float = 0.5              # Connection strength
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship": self.relationship,
            "weight": self.weight,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeConnection":
        return cls(**data)


# Global knowledge graph instance
knowledge_graph = None


class KnowledgeGraph:
    """
    Knowledge Graph.
    
    Stores and manages learned knowledge with semantic connections.
    
    Example:
        >>> kg = KnowledgeGraph()
        >>> kg.add("Python is a programming language", KnowledgeType.FACT)
        >>> results = kg.search("programming")
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        auto_save: bool = True,
    ):
        """
        Initialize knowledge graph.
        
        Args:
            storage_path: Path for persistent storage
            auto_save: Whether to auto-save changes
        """
        self._storage_path = storage_path
        self._auto_save = auto_save
        self._lock = threading.RLock()
        
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._connections: List[KnowledgeConnection] = []
        self._index: Dict[str, Set[str]] = {}  # word -> node_ids
        
        if storage_path and os.path.exists(storage_path):
            self._load()
    
    def add(
        self,
        content: str,
        knowledge_type: KnowledgeType,
        attributes: Optional[Dict] = None,
        importance: float = 0.5,
        source: str = "interaction",
        tags: Optional[List[str]] = None,
    ) -> KnowledgeNode:
        """
        Add knowledge to the graph.
        
        Args:
            content: Knowledge content
            knowledge_type: Type of knowledge
            attributes: Additional attributes
            importance: Importance score (0-1)
            source: Source of this knowledge
            tags: Tags for categorization
            
        Returns:
            Created KnowledgeNode
        """
        with self._lock:
            import uuid
            node_id = str(uuid.uuid4())[:8]
            
            node = KnowledgeNode(
                id=node_id,
                content=content,
                knowledge_type=knowledge_type,
                attributes=attributes or {},
                importance=importance,
                source=source,
                tags=tags or [],
            )
            
            self._nodes[node_id] = node
            
            # Update index
            self._index_content(node)
            
            # Auto-save
            if self._auto_save:
                self._save()
            
            return node
    
    def connect(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        weight: float = 0.5,
    ) -> Optional[KnowledgeConnection]:
        """Create a connection between two nodes."""
        with self._lock:
            if source_id not in self._nodes or target_id not in self._nodes:
                return None
            
            connection = KnowledgeConnection(
                source_id=source_id,
                target_id=target_id,
                relationship=relationship,
                weight=weight,
            )
            
            self._connections.append(connection)
            
            if self._auto_save:
                self._save()
            
            return connection
    
    def search(
        self,
        query: str,
        limit: int = 10,
        knowledge_type: Optional[KnowledgeType] = None,
    ) -> List[KnowledgeNode]:
        """
        Search for knowledge.
        
        Args:
            query: Search query
            limit: Maximum results
            knowledge_type: Filter by type
            
        Returns:
            List of matching KnowledgeNodes
        """
        with self._lock:
            query_words = set(query.lower().split())
            results = []
            
            for node in self._nodes.values():
                # Filter by type
                if knowledge_type and node.knowledge_type != knowledge_type:
                    continue
                
                # Score based on word match
                content_words = set(node.content.lower().split())
                overlap = query_words & content_words
                
                if overlap:
                    score = len(overlap) / max(len(query_words), 1)
                    # Boost by importance
                    score *= (0.5 + node.importance * 0.5)
                    
                    results.append((score, node))
            
            # Sort by score
            results.sort(key=lambda x: x[0], reverse=True)
            
            return [node for _, node in results[:limit]]
    
    def get_related(
        self,
        node_id: str,
        limit: int = 5,
    ) -> List[KnowledgeNode]:
        """Get related knowledge nodes."""
        with self._lock:
            if node_id not in self._nodes:
                return []
            
            related_ids = set()
            
            for conn in self._connections:
                if conn.source_id == node_id:
                    related_ids.add(conn.target_id)
                elif conn.target_id == node_id:
                    related_ids.add(conn.source_id)
            
            results = []
            for rid in related_ids:
                if rid in self._nodes:
                    results.append(self._nodes[rid])
            
            return results[:limit]
    
    def access(self, node_id: str) -> Optional[KnowledgeNode]:
        """Mark knowledge as accessed."""
        with self._lock:
            node = self._nodes.get(node_id)
            if node:
                node.accessed_at = datetime.now().isoformat()
                node.access_count += 1
            return node
    
    def _index_content(self, node: KnowledgeNode):
        """Update search index for a node."""
        words = set(node.content.lower().split())
        words.update(node.content.lower())  # Also index full content
        
        for word in words:
            if word not in self._index:
                self._index[word] = set()
            self._index[word].add(node.id)
        
        # Also index tags
        for tag in node.tags:
            if tag not in self._index:
                self._index[tag] = set()
            self._index[tag].add(node.id)
    
    def _save(self):
        """Save to disk."""
        if not self._storage_path:
            return
        
        with self._lock:
            data = {
                "nodes": {k: v.to_dict() for k, v in self._nodes.items()},
                "connections": [c.to_dict() for c in self._connections],
            }
            
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load(self):
        """Load from disk."""
        if not self._storage_path or not os.path.exists(self._storage_path):
            return
        
        with self._lock:
            try:
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._nodes = {
                    k: KnowledgeNode.from_dict(v)
                    for k, v in data.get("nodes", {}).items()
                }
                
                self._connections = [
                    KnowledgeConnection.from_dict(c)
                    for c in data.get("connections", [])
                ]
                
                # Rebuild index
                self._index = {}
                for node in self._nodes.values():
                    self._index_content(node)
            except Exception:
                pass
    
    @property
    def size(self) -> int:
        """Get number of knowledge nodes."""
        return len(self._nodes)


def get_knowledge_graph() -> KnowledgeGraph:
    """Get or create global knowledge graph instance."""
    global knowledge_graph
    if knowledge_graph is None:
        knowledge_graph = KnowledgeGraph()
    return knowledge_graph


def add_knowledge(
    content: str,
    knowledge_type: KnowledgeType = KnowledgeType.FACT,
    **kwargs
) -> KnowledgeNode:
    """Convenience function to add knowledge."""
    return get_knowledge_graph().add(content, knowledge_type, **kwargs)


def retrieve_knowledge(
    query: str,
    limit: int = 10,
    **kwargs
) -> List[KnowledgeNode]:
    """Convenience function to retrieve knowledge."""
    return get_knowledge_graph().search(query, limit, **kwargs)
