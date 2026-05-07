# Soul Layer - Forgetting Mechanism Module
"""
Forgetting Mechanism based on Ebbinghaus forgetting curve.

Features:
- Memory decay over time
- Access-based reinforcement
- Priority-based retention
- Configurable forgetting parameters
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
import math
import os


class ForgettingCurve(Enum):
    """Forgetting curve models."""
    EBINGHAUS = "ebbinghaus"          # Classic exponential decay
    POWER = "power"                  # Power law decay
    STABLE = "stable"               # Slow forgetting for important items


@dataclass
class MemoryItem:
    """A memory item with decay properties."""
    id: str
    content: str
    created_at: str
    last_accessed: str
    access_count: int = 0
    importance: float = 0.5          # 0-1, higher = remember longer
    decay_rate: float = 0.1          # Base decay rate
    strength: float = 1.0            # Current memory strength 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "importance": self.importance,
            "decay_rate": self.decay_rate,
            "strength": self.strength,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryItem":
        return cls(**data)


@dataclass
class ForgettingConfig:
    """Configuration for forgetting mechanism."""
    curve_type: ForgettingCurve = ForgettingCurve.EBINGHAUS
    base_decay_rate: float = 0.1     # Base decay rate per hour
    reinforcement_boost: float = 0.2  # Strength boost on access
    min_strength_threshold: float = 0.1  # Below this, item is "forgotten"
    max_strength: float = 1.0         # Maximum memory strength
    access_decay_multiplier: float = 0.5  # Reduce decay rate after access


# Global forgetting mechanism instance
forgetting_mechanism = None


class ForgettingMechanism:
    """
    Forgetting Mechanism.
    
    Implements memory decay based on forgetting curves.
    
    Example:
        >>> fm = ForgettingMechanism()
        >>> fm.add("Important fact", importance=0.8)
        >>> # After some time...
        >>> items = fm.get_active_memories()
    """
    
    def __init__(
        self,
        config: Optional[ForgettingConfig] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize forgetting mechanism.
        
        Args:
            config: Configuration
            storage_path: Path for persistence
        """
        self._config = config or ForgettingConfig()
        self._storage_path = storage_path
        self._lock = threading.RLock()
        
        self._memories: Dict[str, MemoryItem] = {}
        
        if storage_path and os.path.exists(storage_path):
            self._load()
    
    def add(
        self,
        content: str,
        importance: float = 0.5,
        decay_rate: Optional[float] = None,
        memory_id: Optional[str] = None,
    ) -> MemoryItem:
        """
        Add a memory item.
        
        Args:
            content: Memory content
            importance: Importance level (0-1)
            decay_rate: Custom decay rate
            memory_id: Custom ID
            
        Returns:
            Created MemoryItem
        """
        with self._lock:
            import uuid
            now = datetime.now()
            
            item = MemoryItem(
                id=memory_id or str(uuid.uuid4())[:8],
                content=content,
                created_at=now.isoformat(),
                last_accessed=now.isoformat(),
                importance=importance,
                decay_rate=decay_rate or self._config.base_decay_rate,
                strength=1.0,
            )
            
            self._memories[item.id] = item
            self._save()
            
            return item
    
    def access(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Access a memory, reinforcing its strength.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Updated MemoryItem or None
        """
        with self._lock:
            item = self._memories.get(memory_id)
            if not item:
                return None
            
            # Apply decay first
            self._apply_decay(item)
            
            # Reinforce on access
            item.last_accessed = datetime.now().isoformat()
            item.access_count += 1
            
            # Boost strength based on importance
            boost = self._config.reinforcement_boost * item.importance
            item.strength = min(self._config.max_strength, item.strength + boost)
            
            # Reduce future decay rate
            item.decay_rate *= self._config.access_decay_multiplier
            
            self._save()
            return item
    
    def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a memory without marking as accessed."""
        return self._memories.get(memory_id)
    
    def get_active_memories(
        self,
        min_strength: float = 0.1,
        limit: int = 100,
    ) -> List[MemoryItem]:
        """
        Get active (non-forgotten) memories.
        
        Args:
            min_strength: Minimum strength threshold
            limit: Maximum number to return
            
        Returns:
            List of active MemoryItems
        """
        with self._lock:
            active = []
            
            for item in self._memories.values():
                # Apply decay
                self._apply_decay(item)
                
                if item.strength >= min_strength:
                    active.append(item)
            
            # Sort by strength (most salient first)
            active.sort(key=lambda x: x.strength * x.importance, reverse=True)
            
            return active[:limit]
    
    def process_forgetting(self) -> List[str]:
        """
        Process forgetting, removing items below threshold.
        
        Returns:
            List of forgotten memory IDs
        """
        with self._lock:
            forgotten = []
            threshold = self._config.min_strength_threshold
            
            for item in list(self._memories.values()):
                self._apply_decay(item)
                
                if item.strength < threshold:
                    forgotten.append(item.id)
                    del self._memories[item.id]
            
            if forgotten:
                self._save()
            
            return forgotten
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        with self._lock:
            total = len(self._memories)
            
            active = sum(
                1 for item in self._memories.values()
                if item.strength >= self._config.min_strength_threshold
            )
            
            avg_strength = sum(
                item.strength for item in self._memories.values()
            ) / max(total, 1)
            
            return {
                "total_memories": total,
                "active_memories": active,
                "forgotten": total - active,
                "average_strength": avg_strength,
            }
    
    def _apply_decay(self, item: MemoryItem):
        """Apply decay to a memory item."""
        if not item.last_accessed:
            return
        
        last = datetime.fromisoformat(item.last_accessed)
        hours_passed = (datetime.now() - last).total_seconds() / 3600
        
        if hours_passed < 0.01:  # Less than 36 seconds
            return
        
        # Calculate decay based on curve type
        if self._config.curve_type == ForgettingCurve.EBINGHAUS:
            # Exponential decay: S = e^(-t/r)
            effective_decay = item.decay_rate * (1 - item.importance * 0.5)
            decay = 1 - math.exp(-effective_decay * hours_passed)
        
        elif self._config.curve_type == ForgettingCurve.POWER:
            # Power law: S = 1 / (1 + t)^k
            k = 0.5 * (1 - item.importance * 0.3)
            decay = 1 - 1 / (1 + hours_passed) ** k
        
        else:  # STABLE
            decay = 0.01 * hours_passed * (1 - item.importance * 0.8)
        
        item.strength = max(0, item.strength - decay * item.strength)
    
    def _save(self):
        """Save to disk."""
        if not self._storage_path:
            return
        
        with self._lock:
            data = {
                "memories": {k: v.to_dict() for k, v in self._memories.items()},
                "config": {
                    "curve_type": self._config.curve_type.value,
                    "base_decay_rate": self._config.base_decay_rate,
                    "reinforcement_boost": self._config.reinforcement_boost,
                    "min_strength_threshold": self._config.min_strength_threshold,
                }
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
                
                self._memories = {
                    k: MemoryItem.from_dict(v)
                    for k, v in data.get("memories", {}).items()
                }
                
                config_data = data.get("config", {})
                if config_data:
                    self._config = ForgettingConfig(
                        curve_type=ForgettingCurve(config_data.get("curve_type", "ebbinghaus")),
                        base_decay_rate=config_data.get("base_decay_rate", 0.1),
                        reinforcement_boost=config_data.get("reinforcement_boost", 0.2),
                        min_strength_threshold=config_data.get("min_strength_threshold", 0.1),
                    )
            except Exception:
                pass


def get_forgetting_mechanism() -> ForgettingMechanism:
    """Get or create global forgetting mechanism instance."""
    global forgetting_mechanism
    if forgetting_mechanism is None:
        forgetting_mechanism = ForgettingMechanism()
    return forgetting_mechanism


def add_memory(content: str, **kwargs) -> MemoryItem:
    """Convenience function to add a memory."""
    return get_forgetting_mechanism().add(content, **kwargs)


def access_memory(memory_id: str) -> Optional[MemoryItem]:
    """Convenience function to access a memory."""
    return get_forgetting_mechanism().access(memory_id)


def process_forgetting() -> List[str]:
    """Convenience function to process forgetting."""
    return get_forgetting_mechanism().process_forgetting()


def get_memory_stats() -> Dict[str, Any]:
    """Convenience function to get memory stats."""
    return get_forgetting_mechanism().get_stats()
