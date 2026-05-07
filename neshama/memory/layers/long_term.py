# Memory Layer - Long-Term Memory
"""
Long-Term Memory - Persistent Knowledge Storage

Features:
- Knowledge entries with semantic indexing
- Vector storage for similarity search
- Structured knowledge representation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import json
import threading
import os


@dataclass
class KnowledgeEntry:
    """A knowledge entry."""
    id: str
    content: str
    knowledge_type: str = "general"  # e.g., "fact", "concept", "procedure"
    importance: float = 0.5         # 0-1
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "knowledge_type": self.knowledge_type,
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            knowledge_type=data.get("knowledge_type", "general"),
            importance=data.get("importance", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            accessed_at=data.get("accessed_at", datetime.now().isoformat()),
            access_count=data.get("access_count", 0),
        )


class LongTermMemory:
    """
    Long-Term Memory - Persistent Knowledge Storage
    
    Example:
        >>> memory = LongTermMemory(agent_id="agent_001")
        >>> 
        >>> # Add knowledge
        >>> entry = memory.add("Python is a programming language", tags=["programming"])
        >>> 
        >>> # Search
        >>> results = memory.search("programming language")
        >>> 
        >>> # Retrieve
        >>> entry = memory.get("entry_id")
    """
    
    def __init__(
        self,
        agent_id: str,
        storage_path: Optional[str] = None,
        vector_store: Optional[Any] = None,
        auto_save: bool = True,
    ):
        """
        Initialize long-term memory.
        
        Args:
            agent_id: Agent identifier
            storage_path: Persistence file path
            vector_store: Vector store for similarity search
            auto_save: Whether to auto-save changes
        """
        self._agent_id = agent_id
        self._storage_path = storage_path
        self._vector_store = vector_store
        self._auto_save = auto_save
        self._lock = threading.RLock()
        
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._word_index: Dict[str, Set[str]] = {}  # word -> entry_ids
        
        if storage_path and os.path.exists(storage_path):
            self._load()
    
    def add(
        self,
        content: str,
        knowledge_type: str = "general",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        entry_id: Optional[str] = None,
    ) -> KnowledgeEntry:
        """
        Add a knowledge entry.
        
        Args:
            content: Knowledge content
            knowledge_type: Type of knowledge
            importance: Importance level
            tags: Tags for categorization
            metadata: Additional metadata
            entry_id: Custom entry ID
            
        Returns:
            Created KnowledgeEntry
        """
        with self._lock:
            import uuid
            
            entry = KnowledgeEntry(
                id=entry_id or str(uuid.uuid4())[:8],
                content=content,
                knowledge_type=knowledge_type,
                importance=importance,
                tags=tags or [],
                metadata=metadata or {},
            )
            
            self._entries[entry.id] = entry
            self._index_entry(entry)
            
            if self._auto_save:
                self._save()
            
            return entry
    
    def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a knowledge entry by ID."""
        with self._lock:
            entry = self._entries.get(entry_id)
            
            if entry:
                entry.accessed_at = datetime.now().isoformat()
                entry.access_count += 1
            
            return entry
    
    def search(
        self,
        query: str,
        limit: int = 10,
        knowledge_type: Optional[str] = None,
        min_importance: float = 0.0,
    ) -> List[KnowledgeEntry]:
        """
        Search for knowledge entries.
        
        Args:
            query: Search query
            limit: Maximum results
            knowledge_type: Filter by type
            min_importance: Minimum importance threshold
            
        Returns:
            List of matching KnowledgeEntries
        """
        with self._lock:
            query_words = set(query.lower().split())
            results = []
            
            # Find entries containing query words
            matching_ids = set()
            for word in query_words:
                if word in self._word_index:
                    matching_ids.update(self._word_index[word])
            
            # Also check full content
            for entry_id, entry in self._entries.items():
                if query.lower() in entry.content.lower():
                    matching_ids.add(entry_id)
            
            # Build results
            for entry_id in matching_ids:
                entry = self._entries[entry_id]
                
                # Apply filters
                if knowledge_type and entry.knowledge_type != knowledge_type:
                    continue
                if entry.importance < min_importance:
                    continue
                
                results.append(entry)
            
            # Sort by relevance and importance
            results.sort(
                key=lambda e: (
                    sum(1 for w in query_words if w in e.content.lower()) +
                    e.importance
                ),
                reverse=True
            )
            
            return results[:limit]
    
    def get_by_tag(self, tag: str) -> List[KnowledgeEntry]:
        """Get all entries with a specific tag."""
        with self._lock:
            return [
                entry for entry in self._entries.values()
                if tag in entry.tags
            ]
    
    def delete(self, entry_id: str) -> bool:
        """Delete a knowledge entry."""
        with self._lock:
            if entry_id not in self._entries:
                return False
            
            entry = self._entries[entry_id]
            
            # Remove from index
            for word in entry.content.lower().split():
                if word in self._word_index:
                    self._word_index[word].discard(entry_id)
            
            for tag in entry.tags:
                if tag in self._word_index:
                    self._word_index[tag].discard(entry_id)
            
            del self._entries[entry_id]
            
            if self._auto_save:
                self._save()
            
            return True
    
    def _index_entry(self, entry: KnowledgeEntry):
        """Update search index for an entry."""
        words = set(entry.content.lower().split())
        
        for word in words:
            if word not in self._word_index:
                self._word_index[word] = set()
            self._word_index[word].add(entry.id)
        
        for tag in entry.tags:
            if tag not in self._word_index:
                self._word_index[tag] = set()
            self._word_index[tag].add(entry.id)
    
    def _save(self) -> None:
        """Save to disk."""
        if not self._storage_path:
            return
        
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
                
                data = {
                    "entries": {
                        k: v.to_dict() for k, v in self._entries.items()
                    }
                }
                
                with open(self._storage_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
    
    def _load(self) -> None:
        """Load from disk."""
        if not self._storage_path or not os.path.exists(self._storage_path):
            return
        
        with self._lock:
            try:
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._entries = {
                    k: KnowledgeEntry.from_dict(v)
                    for k, v in data.get("entries", {}).items()
                }
                
                # Rebuild index
                self._word_index = {}
                for entry in self._entries.values():
                    self._index_entry(entry)
            except Exception:
                pass
    
    @property
    def count(self) -> int:
        """Get number of entries."""
        return len(self._entries)
