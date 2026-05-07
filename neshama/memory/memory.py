# Memory Layer - Main Module
"""
Neshama Memory - Unified Memory Interface

Three-layer memory architecture:
- Short-term: Sliding window conversation memory
- Medium-term: User profile, preferences, habits
- Long-term: RAG knowledge base
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import threading

from .layers import ShortTermMemory, MediumTermMemory, LongTermMemory
from .storage import FileStorage, VectorStore
from .retrieval.rag import RAGRetriever, RetrievalStrategy


@dataclass
class MemoryConfig:
    """Memory configuration."""
    # Basic config
    agent_id: str = "default"
    storage_path: str = "./memory_data"
    
    # Short-term config
    short_term_capacity: int = 20
    short_term_persist: bool = True
    
    # Medium-term config
    medium_term_enabled: bool = True
    
    # Long-term config
    long_term_enabled: bool = True
    embedding_dim: int = 384
    
    # RAG config
    rag_top_k: int = 5
    rag_strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC


@dataclass
class MemoryStats:
    """Memory statistics."""
    short_term_count: int
    interaction_count: int
    long_term_count: int
    preferences_count: int
    habits_count: int


class Memory:
    """
    Neshama Memory - Unified Memory Interface
    
    Three-layer memory architecture:
    - Short-term: Sliding window conversation memory
    - Medium-term: User profile, preferences, habits
    - Long-term: RAG knowledge base
    
    Example:
        # Initialize
        memory = Memory(agent_id="my_agent")
        
        # Add conversation
        memory.add_turn("user", "Hello")
        memory.add_turn("assistant", "Hi!")
        
        # Get short-term context
        context = memory.get_short_term_context()
        
        # Get medium-term summary
        profile = memory.get_medium_term_summary()
        
        # RAG retrieval
        rag_context = memory.retrieve("relevant knowledge")
        
        # Get full context (for Agent)
        full_context = memory.get_context()
    """
    
    def __init__(
        self,
        agent_id: str = "default",
        config: Optional[MemoryConfig] = None,
    ):
        """
        Initialize Memory.
        
        Args:
            agent_id: Agent unique identifier
            config: Configuration object
        """
        self._config = config or MemoryConfig(agent_id=agent_id)
        self._agent_id = self._config.agent_id
        self._lock = threading.RLock()
        
        # Initialize storage layer
        self._file_storage = FileStorage(
            base_path=self._config.storage_path,
        )
        
        # Initialize vector storage
        self._vector_store = VectorStore(
            dimension=self._config.embedding_dim,
            storage_path=f"{self._config.storage_path}/vectors.json",
        )
        
        # Initialize three-layer memory
        self._init_short_term()
        self._init_medium_term()
        self._init_long_term()
        
        # Initialize RAG retriever
        self._init_rag()
    
    def _init_short_term(self) -> None:
        """Initialize short-term memory."""
        persist_path = None
        if self._config.short_term_persist:
            persist_path = f"{self._config.storage_path}/short_term.json"
        
        self._short_term = ShortTermMemory(
            capacity=self._config.short_term_capacity,
            auto_persist=self._config.short_term_persist,
            persist_path=persist_path,
        )
    
    def _init_medium_term(self) -> None:
        """Initialize medium-term memory."""
        self._medium_term = MediumTermMemory(
            agent_id=self._agent_id,
            storage_path=f"{self._config.storage_path}/medium_term_{self._agent_id}.json",
            auto_save=True,
        ) if self._config.medium_term_enabled else None
    
    def _init_long_term(self) -> None:
        """Initialize long-term memory."""
        self._long_term = LongTermMemory(
            agent_id=self._agent_id,
            storage_path=f"{self._config.storage_path}/long_term_{self._agent_id}.json",
            vector_store=self._vector_store,
        ) if self._config.long_term_enabled else None
    
    def _init_rag(self) -> None:
        """Initialize RAG retriever."""
        self._rag = RAGRetriever(
            strategy=self._config.rag_strategy,
            default_top_k=self._config.rag_top_k,
        )
        
        # Register long-term memory as knowledge source
        if self._long_term:
            self._rag.register_source("long_term", self._long_term)
    
    # ==================== Short-term Memory ====================
    
    def add_turn(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a conversation turn to short-term memory.
        
        Args:
            role: Role ("user" | "assistant" | "system")
            content: Turn content
            metadata: Additional metadata
        """
        self._short_term.add(role, content, metadata)
    
    def get_short_term_context(self, include_recent: int = 10) -> str:
        """Get formatted short-term context."""
        return self._short_term.get_context(include_recent)
    
    def get_short_term_recent(self, n: int = 10) -> List:
        """Get recent N turns."""
        return self._short_term.get_recent(n)
    
    # ==================== Medium-term Memory ====================
    
    def set_profile(self, profile) -> None:
        """Set user profile."""
        if self._medium_term:
            self._medium_term.set_profile(profile)
    
    def get_medium_term_summary(self) -> Dict[str, Any]:
        """Get medium-term memory summary."""
        if self._medium_term:
            return self._medium_term.get_summary()
        return {}
    
    def update_preference(self, key: str, value: Any, **kwargs) -> None:
        """Update a user preference."""
        if self._medium_term:
            self._medium_term.update_preference(key, value, **kwargs)
    
    def record_habit(self, pattern: str, **kwargs) -> None:
        """Record a user habit."""
        if self._medium_term:
            self._medium_term.record_habit(pattern, **kwargs)
    
    # ==================== Long-term Memory ====================
    
    def add_knowledge(
        self,
        content: str,
        knowledge_type: str = "general",
        **kwargs
    ):
        """Add knowledge to long-term memory."""
        if self._long_term:
            return self._long_term.add(content, knowledge_type, **kwargs)
        return None
    
    def retrieve(
        self,
        query: str,
        limit: int = 5,
        **kwargs
    ) -> List:
        """
        Retrieve relevant knowledge using RAG.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of relevant knowledge entries
        """
        if self._rag:
            return self._rag.retrieve(query, limit=limit, **kwargs)
        return []
    
    # ==================== Unified Context ====================
    
    def get_context(self) -> str:
        """
        Get full context for agent.
        
        Returns:
            Formatted context string combining all memory layers
        """
        parts = []
        
        # Add short-term context
        short_context = self.get_short_term_context()
        if short_context:
            parts.append(f"[Recent Conversation]\n{short_context}")
        
        # Add medium-term summary
        medium_summary = self.get_medium_term_summary()
        if medium_summary:
            parts.append(f"[User Profile]\n{self._format_medium_summary(medium_summary)}")
        
        # Note: Long-term/RAG context is typically retrieved separately
        # as part of the agent's reasoning process
        
        return "\n\n".join(parts) if parts else ""
    
    def _format_medium_summary(self, summary: Dict) -> str:
        """Format medium-term summary."""
        parts = []
        
        if summary.get("profile"):
            profile = summary["profile"]
            if profile.get("name"):
                parts.append(f"Name: {profile['name']}")
            if profile.get("interests"):
                parts.append(f"Interests: {', '.join(profile['interests'])}")
        
        prefs = summary.get("preferences", {})
        if prefs:
            parts.append(f"Preferences: {len(prefs)} recorded")
        
        habits = summary.get("habits", [])
        if habits:
            parts.append(f"Habits: {len(habits)} recorded")
        
        return "\n".join(parts) if parts else "No profile data"
    
    def get_stats(self) -> MemoryStats:
        """Get memory statistics."""
        return MemoryStats(
            short_term_count=self._short_term.count,
            interaction_count=self._short_term.count // 2,  # Approximate
            long_term_count=self._long_term.count if self._long_term else 0,
            preferences_count=len(self._medium_term.get_all_preferences()) if self._medium_term else 0,
            habits_count=len(self._medium_term.get_habits()) if self._medium_term else 0,
        )
