"""
Reflection Module

Provides reflection capabilities for AI agents.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ReflectionType(Enum):
    """Types of reflection."""
    SELF = "self"              # Self-examination
    LEARNING = "learning"      # Learning from experience
    IMPROVEMENT = "improvement"  # Identifying areas to improve
    PATTERN = "pattern"        # Pattern recognition
    GOAL = "goal"              # Goal evaluation


@dataclass
class Reflection:
    """
    A reflection entry.
    
    Attributes:
        type: Type of reflection
        content: Reflection content
        insights: Key insights gained
        action_items: Actions to take based on reflection
        timestamp: When the reflection was made
    """
    type: ReflectionType
    content: str
    insights: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "content": self.content,
            "insights": self.insights,
            "action_items": self.action_items,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class ReflectionManager:
    """
    Manages reflection entries for AI agents.
    
    Example:
        >>> manager = ReflectionManager()
        >>> manager.reflect(
        ...     ReflectionType.LEARNING,
        ...     "Learned about user preferences",
        ...     insights=["Users prefer concise responses"],
        ...     action_items=["Reduce response length"]
        ... )
    """
    
    def __init__(self):
        """Initialize reflection manager."""
        self._reflections: List[Reflection] = []
    
    def reflect(
        self,
        reflection_type: ReflectionType,
        content: str,
        insights: Optional[List[str]] = None,
        action_items: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Reflection:
        """
        Create a new reflection.
        
        Args:
            reflection_type: Type of reflection
            content: Reflection content
            insights: Key insights
            action_items: Action items
            metadata: Additional metadata
            
        Returns:
            Created Reflection
        """
        reflection = Reflection(
            type=reflection_type,
            content=content,
            insights=insights or [],
            action_items=action_items or [],
            metadata=metadata or {},
        )
        
        self._reflections.append(reflection)
        return reflection
    
    def get_recent(self, limit: int = 10) -> List[Reflection]:
        """Get recent reflections."""
        return self._reflections[-limit:] if limit > 0 else self._reflections
    
    def get_by_type(self, reflection_type: ReflectionType) -> List[Reflection]:
        """Get reflections by type."""
        return [r for r in self._reflections if r.type == reflection_type]
    
    def get_pending_actions(self) -> List[str]:
        """Get all pending action items."""
        actions = []
        for reflection in self._reflections:
            actions.extend(reflection.action_items)
        return actions
    
    def get_all(self) -> List[Reflection]:
        """Get all reflections."""
        return self._reflections.copy()
