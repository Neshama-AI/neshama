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
    
    def log_reflection(self, content: str, reflection_type: str = "general") -> MemoryEntry:
        """
        Log a reflection entry.
        
        Args:
            content: Reflection content.
            reflection_type: Type of reflection.
            
        Returns:
            Created MemoryEntry.
        """
        return self.log(
            content=content,
            memory_type=MemoryType.REFLECTION,
            tags=['reflection', reflection_type],
            metadata={'reflection_type': reflection_type}
        )
    
    def log_error(self, error: str, context: Optional[Dict] = None) -> MemoryEntry:
        """
        Log an error for later analysis.
        
        Args:
            error: Error description.
            context: Optional error context.
            
        Returns:
            Created MemoryEntry.
        """
        return self.log(
            content=error,
            memory_type=MemoryType.ERROR,
            tags=['error'],
            metadata={'context': context or {}}
        )
    
    def get_by_type(self, memory_type: MemoryType) -> List[MemoryEntry]:
        """Get all memories of a specific type."""
        return [m for m in self._memories if m.memory_type == memory_type]
    
    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get most recent memories."""
        return sorted(self._memories, key=lambda m: m.timestamp or "", reverse=True)[:limit]
    
    def search_by_tag(self, tag: str) -> List[MemoryEntry]:
        """Search memories by tag."""
        return [m for m in self._memories if tag in m.tags]
    
    def search(self, keyword: str) -> List[MemoryEntry]:
        """Search memories by keyword in content."""
        return [m for m in self._memories if keyword.lower() in m.content.lower()]
    
    def get_reflections(self) -> List[MemoryEntry]:
        """Get all reflection entries."""
        return self.get_by_type(MemoryType.REFLECTION)
    
    def get_errors(self) -> List[MemoryEntry]:
        """Get all error entries."""
        return self.get_by_type(MemoryType.ERROR)
    
    def get_emotion_log(self) -> List[Dict]:
        """Get emotion log."""
        return self._emotion_log.copy()
    
    def export_memory(
        self,
        include_types: Optional[List[MemoryType]] = None
    ) -> Dict:
        """
        Export all memories as dictionary.
        
        Args:
            include_types: Specific types to include. If None, include all.
            
        Returns:
            Dictionary with exported memories.
        """
        memories = self._memories
        if include_types:
            memories = [m for m in memories if m.memory_type in include_types]
        
        return {
            'exported_at': datetime.now().isoformat(),
            'total_entries': len(memories),
            'memories': [
                {
                    'content': m.content,
                    'type': m.memory_type.value,
                    'tags': m.tags,
                    'metadata': m.metadata,
                    'timestamp': m.timestamp
                }
                for m in memories
            ],
            'emotion_log': self._emotion_log
        }
    
    def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """
        Clear memories.
        
        Args:
            memory_type: Type to clear. If None, clear all.
            
        Returns:
            Number of entries cleared.
        """
        if memory_type is None:
            count = len(self._memories)
            self._memories.clear()
            return count
        
        before = len(self._memories)
        self._memories = [m for m in self._memories if m.memory_type != memory_type]
        return before - len(self._memories)
