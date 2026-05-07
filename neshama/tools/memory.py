"""
Memory Management Module

Assists with memory logging and retrieval for AI agents.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """Types of memory."""
    SHORT_TERM = "short_term"    # 当日日志
    MEDIUM_TERM = "medium_term"  # 技能文件更新
    LONG_TERM = "long_term"      # OCEAN微调
    REFLECTION = "reflection"    # 反思记录
    EMOTION = "emotion"          # 情绪记录
    LEARNING = "learning"        # 学习记录
    ERROR = "error"              # 错误记录


@dataclass
class MemoryEntry:
    """A single memory entry."""
    content: str
    memory_type: MemoryType
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class MemoryManager:
    """
    Manages memory entries for AI agents.
    
    Memory is organized by type:
    - Short-term: Current day logs
    - Medium-term: Skill file updates
    - Long-term: OCEAN parameter adjustments
    
    Example:
        >>> manager = MemoryManager()
        >>> manager.log("Learned a new approach", MemoryType.LEARNING)
        >>> manager.log_emotion("happy", 7)
        >>> entries = manager.search_by_tag("important")
    """
    
    def __init__(self):
        """Initialize memory manager."""
        self._memories: List[MemoryEntry] = []
        self._emotion_log: List[Dict] = []
    
    def log(
        self,
        content: str,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryEntry:
        """
        Log a new memory entry.
        
        Args:
            content: Memory content.
            memory_type: Type of memory. Defaults to SHORT_TERM.
            tags: Optional tags for categorization.
            metadata: Optional additional metadata.
            
        Returns:
            Created MemoryEntry.
        """
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type or MemoryType.SHORT_TERM,
            tags=tags or [],
            metadata=metadata or {}
        )
        self._memories.append(entry)
        return entry
    
    def log_emotion(self, emotion: str, intensity: int) -> None:
        """
        Log an emotion event.
        
        Args:
            emotion: Emotion name.
            intensity: Emotion intensity (1-10).
        """
        self._emotion_log.append({
            'timestamp': datetime.now().isoformat(),
            'emotion': emotion,
            'intensity': intensity
        })
    
    def search_by_tag(self, tag: str) -> List[MemoryEntry]:
        """Search memories by tag."""
        return [m for m in self._memories if tag in m.tags]
    
    def search_by_type(self, memory_type: MemoryType) -> List[MemoryEntry]:
        """Search memories by type."""
        return [m for m in self._memories if m.memory_type == memory_type]
    
    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent memories."""
        return self._memories[-limit:] if limit > 0 else self._memories
    
    def get_all(self) -> List[MemoryEntry]:
        """Get all memories."""
        return self._memories.copy()
    
    @property
    def emotion_log(self) -> List[Dict]:
        """Get emotion log."""
        return self._emotion_log.copy()
