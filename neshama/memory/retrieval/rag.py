# Memory Layer - RAG Retriever
"""
RAG (Retrieval-Augmented Generation) Retriever

Provides retrieval capabilities for knowledge augmentation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import threading


class RetrievalStrategy(Enum):
    """Retrieval strategy types."""
    SEMANTIC = "semantic"           # Semantic similarity search
    KEYWORD = "keyword"             # Keyword-based search
    HYBRID = "hybrid"               # Combine semantic and keyword
    BM25 = "bm25"                   # BM25 algorithm


@dataclass
class RetrievedChunk:
    """A retrieved knowledge chunk."""
    content: str
    source: str                    # Source identifier (e.g., "long_term")
    source_id: str                 # Source-specific ID
    score: float = 0.0             # Relevance score
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGRetriever:
    """
    RAG Retriever.
    
    Retrieves relevant knowledge chunks for augmentation.
    
    Example:
        >>> retriever = RAGRetriever(strategy=RetrievalStrategy.HYBRID)
        >>> retriever.register_source("kb", knowledge_base)
        >>> 
        >>> results = retriever.retrieve("How to cook rice?")
        >>> for chunk in results:
        ...     print(f"[{chunk.score:.2f}] {chunk.content}")
    """
    
    def __init__(
        self,
        strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC,
        default_top_k: int = 5,
        min_score_threshold: float = 0.0,
    ):
        """
        Initialize RAG retriever.
        
        Args:
            strategy: Retrieval strategy
            default_top_k: Default number of results
            min_score_threshold: Minimum relevance score
        """
        self._strategy = strategy
        self._default_top_k = default_top_k
        self._min_score_threshold = min_score_threshold
        self._lock = threading.RLock()
        
        # Registered sources: source_name -> source object
        self._sources: Dict[str, Any] = {}
    
    def register_source(self, name: str, source: Any):
        """
        Register a knowledge source.
        
        Args:
            name: Source name
            source: Source object (must implement search/retrieve)
        """
        with self._lock:
            self._sources[name] = source
    
    def unregister_source(self, name: str) -> bool:
        """Unregister a knowledge source."""
        with self._lock:
            if name in self._sources:
                del self._sources[name]
                return True
            return False
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        sources: Optional[List[str]] = None,
        **kwargs
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant knowledge chunks.
        
        Args:
            query: Search query
            top_k: Number of results (uses default if None)
            sources: Only search in these sources (all if None)
            **kwargs: Additional search parameters
            
        Returns:
            List of RetrievedChunks sorted by relevance
        """
        top_k = top_k or self._default_top_k
        all_chunks: List[RetrievedChunk] = []
        
        # Determine which sources to search
        search_sources = sources or list(self._sources.keys())
        
        for source_name in search_sources:
            source = self._sources.get(source_name)
            if not source:
                continue
            
            # Search based on source type
            chunks = self._search_source(source_name, source, query, top_k, **kwargs)
            all_chunks.extend(chunks)
        
        # Filter and sort
        filtered = [
            chunk for chunk in all_chunks
            if chunk.score >= self._min_score_threshold
        ]
        
        filtered.sort(key=lambda x: x.score, reverse=True)
        
        return filtered[:top_k]
    
    def _search_source(
        self,
        source_name: str,
        source: Any,
        query: str,
        top_k: int,
        **kwargs
    ) -> List[RetrievedChunk]:
        """Search a specific source."""
        chunks = []
        
        # Try different search methods based on source interface
        try:
            # Method 1: Direct search on long-term memory
            if hasattr(source, 'search'):
                results = source.search(query, limit=top_k, **kwargs)
                
                for result in results:
                    # Handle different result types
                    if hasattr(result, 'content'):
                        content = result.content
                        metadata = getattr(result, 'metadata', {})
                        score = getattr(result, 'importance', 0.5)
                    else:
                        content = str(result)
                        metadata = {}
                        score = 0.5
                    
                    chunks.append(RetrievedChunk(
                        content=content,
                        source=source_name,
                        source_id=getattr(result, 'id', ''),
                        score=score,
                        metadata=metadata,
                    ))
            
            # Method 2: Retrieve method
            elif hasattr(source, 'retrieve'):
                results = source.retrieve(query, limit=top_k, **kwargs)
                
                for result in results:
                    content = getattr(result, 'content', str(result))
                    chunks.append(RetrievedChunk(
                        content=content,
                        source=source_name,
                        source_id=getattr(result, 'id', ''),
                        score=getattr(result, 'score', 0.5),
                        metadata=getattr(result, 'metadata', {}),
                    ))
            
            # Method 3: get_context or similar
            elif hasattr(source, 'get_context'):
                context = source.get_context()
                chunks.append(RetrievedChunk(
                    content=context,
                    source=source_name,
                    source_id='context',
                    score=0.5,
                ))
        
        except Exception:
            pass
        
        return chunks
    
    def set_strategy(self, strategy: RetrievalStrategy):
        """Change retrieval strategy."""
        self._strategy = strategy
    
    def set_threshold(self, threshold: float):
        """Set minimum score threshold."""
        self._min_score_threshold = threshold
    
    def format_for_prompt(
        self,
        chunks: List[RetrievedChunk],
        include_source: bool = False,
    ) -> str:
        """
        Format retrieved chunks for prompt inclusion.
        
        Args:
            chunks: Retrieved chunks
            include_source: Whether to include source info
            
        Returns:
            Formatted string
        """
        if not chunks:
            return ""
        
        parts = []
        for i, chunk in enumerate(chunks, 1):
            part = f"[{i}] {chunk.content}"
            
            if include_source:
                part += f"\n    (Source: {chunk.source})"
            
            parts.append(part)
        
        header = "Relevant Knowledge:\n" if parts else ""
        return header + "\n".join(parts)
