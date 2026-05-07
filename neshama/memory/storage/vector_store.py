# Memory Layer - Vector Store
"""
Vector Storage for Embeddings

Simple in-memory vector storage with similarity search.
For production, replace with proper vector DB (Pinecone, Milvus, etc.)
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import threading
import math


@dataclass
class VectorEntry:
    """A vector entry with metadata."""
    id: str
    vector: List[float]
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    """Search result with score."""
    id: str
    score: float
    metadata: Dict[str, Any]


class VectorStore:
    """
    Simple Vector Storage.
    
    Provides basic vector storage and similarity search.
    For production, use a proper vector database.
    
    Example:
        >>> store = VectorStore(dimension=384)
        >>> store.add("id1", [0.1] * 384, {"text": "hello"})
        >>> results = store.search([0.1] * 384, top_k=5)
    """
    
    def __init__(
        self,
        dimension: int = 384,
        storage_path: Optional[str] = None,
        metric: str = "cosine",
    ):
        """
        Initialize vector store.
        
        Args:
            dimension: Vector dimension
            storage_path: Path for persistence
            metric: Similarity metric ("cosine" or "euclidean")
        """
        self._dimension = dimension
        self._storage_path = storage_path
        self._metric = metric
        self._lock = threading.RLock()
        
        self._vectors: Dict[str, List[float]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        
        if storage_path and os.path.exists(storage_path):
            self._load()
    
    def add(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a vector.
        
        Args:
            id: Unique identifier
            vector: Vector values
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        with self._lock:
            if len(vector) != self._dimension:
                return False
            
            self._vectors[id] = vector
            self._metadata[id] = metadata or {}
            
            self._save()
            return True
    
    def get(self, id: str) -> Optional[List[float]]:
        """Get a vector by ID."""
        return self._vectors.get(id)
    
    def get_with_metadata(self, id: str) -> Optional[Tuple[List[float], Dict]]:
        """Get vector with metadata."""
        vector = self._vectors.get(id)
        if vector is None:
            return None
        return vector, self._metadata.get(id, {})
    
    def delete(self, id: str) -> bool:
        """Delete a vector."""
        with self._lock:
            if id not in self._vectors:
                return False
            
            del self._vectors[id]
            if id in self._metadata:
                del self._metadata[id]
            
            self._save()
            return True
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_ids: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector
            top_k: Number of results
            filter_ids: Only search in these IDs
            
        Returns:
            List of SearchResults sorted by similarity
        """
        if len(query_vector) != self._dimension:
            return []
        
        candidates = filter_ids if filter_ids else list(self._vectors.keys())
        
        results = []
        for id in candidates:
            if id not in self._vectors:
                continue
            
            vector = self._vectors[id]
            
            if self._metric == "cosine":
                score = self._cosine_similarity(query_vector, vector)
            else:
                score = -self._euclidean_distance(query_vector, vector)  # Negate for sorting
            
            results.append(SearchResult(
                id=id,
                score=score,
                metadata=self._metadata.get(id, {}),
            ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity."""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(a * a for a in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _euclidean_distance(self, v1: List[float], v2: List[float]) -> float:
        """Calculate Euclidean distance."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
    
    def _save(self):
        """Save to disk."""
        if not self._storage_path:
            return
        
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
                
                data = {
                    "dimension": self._dimension,
                    "vectors": self._vectors,
                    "metadata": self._metadata,
                }
                
                with open(self._storage_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
            except Exception:
                pass
    
    def _load(self):
        """Load from disk."""
        if not self._storage_path or not os.path.exists(self._storage_path):
            return
        
        with self._lock:
            try:
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._dimension = data.get("dimension", self._dimension)
                self._vectors = data.get("vectors", {})
                self._metadata = data.get("metadata", {})
            except Exception:
                pass
    
    @property
    def count(self) -> int:
        """Get number of vectors."""
        return len(self._vectors)
    
    @property
    def dimension(self) -> int:
        """Get vector dimension."""
        return self._dimension
from dataclasses import dataclass
