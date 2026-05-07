# Memory Layer - Short-Term Memory
"""
Short-Term Memory - Sliding Window Implementation

Features:
- Fixed capacity with automatic cleanup
- Conversation turn management
- Configurable forgetting strategy
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import threading
import os


@dataclass
class ConversationTurn:
    """Single conversation turn record."""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationTurn":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )


class ShortTermMemory:
    """
    Short-Term Memory - Sliding Window Implementation
    
    Example:
        >>> memory = ShortTermMemory(capacity=10)
        >>> memory.add("user", "Hello")
        >>> memory.add("assistant", "Hi! How can I help?")
        >>> 
        >>> # Get recent 5 turns
        >>> recent = memory.get_recent(n=5)
        >>> 
        >>> # Search history
        >>> results = memory.search("help")
    """
    
    def __init__(
        self,
        capacity: int = 20,
        auto_persist: bool = True,
        persist_path: Optional[str] = None,
    ):
        """
        Initialize short-term memory.
        
        Args:
            capacity: Sliding window capacity
            auto_persist: Whether to auto-persist
            persist_path: Persistence file path
        """
        self._capacity = capacity
        self._turns: List[ConversationTurn] = []
        self._auto_persist = auto_persist
        self._persist_path = persist_path
        self._lock = threading.RLock()
        
        if auto_persist and persist_path:
            self._load()
    
    def add(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a conversation turn.
        
        Args:
            role: Role ("user" | "assistant" | "system")
            content: Turn content
            metadata: Additional metadata
        """
        with self._lock:
            turn = ConversationTurn(
                role=role,
                content=content,
                metadata=metadata or {},
            )
            
            self._turns.append(turn)
            
            # Trim if over capacity
            if len(self._turns) > self._capacity:
                self._turns = self._turns[-self._capacity:]
            
            if self._auto_persist:
                self._save()
    
    def get_recent(self, n: int = 10) -> List[ConversationTurn]:
        """
        Get recent N turns.
        
        Args:
            n: Number of turns
            
        Returns:
            List of recent ConversationTurns
        """
        with self._lock:
            return self._turns[-n:] if n > 0 else self._turns[:]
    
    def get_context(self, include_recent: int = 10) -> str:
        """
        Get formatted context string.
        
        Args:
            include_recent: Include last N turns
            
        Returns:
            Formatted context string
        """
        with self._lock:
            recent = self._turns[-include_recent:] if include_recent else self._turns
            
            parts = []
            for turn in recent:
                role_label = turn.role.capitalize()
                parts.append(f"{role_label}: {turn.content}")
            
            return "\n".join(parts)
    
    def search(
        self,
        query: str,
        case_sensitive: bool = False,
    ) -> List[ConversationTurn]:
        """
        Search turns by content.
        
        Args:
            query: Search query
            case_sensitive: Whether to match case
            
        Returns:
            Matching turns
        """
        with self._lock:
            query_str = query if case_sensitive else query.lower()
            
            results = []
            for turn in self._turns:
                content = turn.content if case_sensitive else turn.content.lower()
                if query_str in content:
                    results.append(turn)
            
            return results
    
    def clear(self) -> None:
        """Clear all turns."""
        with self._lock:
            self._turns = []
            if self._auto_persist:
                self._save()
    
    def _save(self) -> None:
        """Save to disk."""
        if not self._persist_path:
            return
        
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
                
                data = [turn.to_dict() for turn in self._turns]
                
                with open(self._persist_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
    
    def _load(self) -> None:
        """Load from disk."""
        if not self._persist_path or not os.path.exists(self._persist_path):
            return
        
        with self._lock:
            try:
                with open(self._persist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._turns = [
                    ConversationTurn.from_dict(d) for d in data
                ]
            except Exception:
                pass
    
    @property
    def count(self) -> int:
        """Get number of turns."""
        return len(self._turns)
    
    @property
    def capacity(self) -> int:
        """Get capacity."""
        return self._capacity
