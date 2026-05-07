# Soul Layer - Emotion Memory Module
"""
Emotion Memory Storage

Stores and retrieves emotional experiences and patterns.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import threading
import os


class EmotionPatternType(Enum):
    """Types of emotion patterns."""
    RECURRING = "recurring"        # Same emotion pattern observed multiple times
    TRIGGER = "trigger"           # Specific trigger for an emotion
    DEVELOPMENT = "development"    # Emotional development over time
    RESPONSE = "response"         # Typical response pattern


@dataclass
class EmotionEvent:
    """Record of an emotional event."""
    timestamp: str
    emotion: str
    intensity: float
    trigger: str
    context: str
    response: str
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "emotion": self.emotion,
            "intensity": self.intensity,
            "trigger": self.trigger,
            "context": self.context,
            "response": self.response,
            "user_id": self.user_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionEvent":
        return cls(**data)


@dataclass
class EmotionPattern:
    """Identified emotion pattern."""
    pattern_type: EmotionPatternType
    emotion: str
    frequency: float  # How often this pattern occurs
    triggers: List[str]
    description: str
    last_observed: str
    count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "emotion": self.emotion,
            "frequency": self.frequency,
            "triggers": self.triggers,
            "description": self.description,
            "last_observed": self.last_observed,
            "count": self.count,
        }


# Global emotion memory instance
_emotion_memory_instance = None


class EmotionMemory:
    """
    Emotion Memory.
    
    Stores emotional experiences and identifies patterns.
    
    Example:
        >>> memory = EmotionMemory()
        >>> memory.record(
        ...     emotion="joy",
        ...     intensity=0.8,
        ...     trigger="user shared good news",
        ...     context="They got promoted",
        ...     response="I expressed genuine happiness"
        ... )
        >>> patterns = memory.get_patterns(emotion="joy")
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        auto_save: bool = True,
    ):
        """
        Initialize emotion memory.
        
        Args:
            storage_path: Path for persistent storage
            auto_save: Whether to auto-save changes
        """
        self._storage_path = storage_path
        self._auto_save = auto_save
        self._lock = threading.RLock()
        
        self._events: List[EmotionEvent] = []
        self._patterns: Dict[str, List[EmotionPattern]] = {}
        
        if storage_path and os.path.exists(storage_path):
            self._load()
    
    def record(
        self,
        emotion: str,
        intensity: float,
        trigger: str,
        context: str = "",
        response: str = "",
        user_id: Optional[str] = None,
    ) -> EmotionEvent:
        """
        Record an emotional event.
        
        Args:
            emotion: Emotion category name
            intensity: Emotion intensity (0-1)
            trigger: What triggered this emotion
            context: Additional context
            response: How this was responded to
            user_id: Optional user identifier
            
        Returns:
            Created EmotionEvent
        """
        with self._lock:
            event = EmotionEvent(
                timestamp=datetime.now().isoformat(),
                emotion=emotion,
                intensity=intensity,
                trigger=trigger,
                context=context,
                response=response,
                user_id=user_id,
            )
            
            self._events.append(event)
            
            # Update patterns
            self._update_patterns(event)
            
            # Auto-save if enabled
            if self._auto_save:
                self._save()
            
            return event
    
    def get_recent(
        self,
        emotion: Optional[str] = None,
        limit: int = 10,
    ) -> List[EmotionEvent]:
        """
        Get recent emotional events.
        
        Args:
            emotion: Filter by emotion (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of recent EmotionEvents
        """
        with self._lock:
            events = self._events
            
            if emotion:
                events = [e for e in events if e.emotion == emotion]
            
            return events[-limit:]
    
    def get_patterns(
        self,
        emotion: Optional[str] = None,
        pattern_type: Optional[EmotionPatternType] = None,
    ) -> List[EmotionPattern]:
        """
        Get identified emotion patterns.
        
        Args:
            emotion: Filter by emotion (optional)
            pattern_type: Filter by pattern type (optional)
            
        Returns:
            List of EmotionPatterns
        """
        with self._lock:
            all_patterns = []
            
            for emotion_patterns in self._patterns.values():
                all_patterns.extend(emotion_patterns)
            
            if emotion:
                all_patterns = [p for p in all_patterns if p.emotion == emotion]
            
            if pattern_type:
                all_patterns = [p for p in all_patterns if p.pattern_type == pattern_type]
            
            return all_patterns
    
    def get_average_intensity(self, emotion: str) -> float:
        """Get average intensity for an emotion."""
        with self._lock:
            emotion_events = [e for e in self._events if e.emotion == emotion]
            
            if not emotion_events:
                return 0.0
            
            return sum(e.intensity for e in emotion_events) / len(emotion_events)
    
    def _update_patterns(self, event: EmotionEvent):
        """Update patterns based on new event."""
        emotion = event.emotion
        
        if emotion not in self._patterns:
            self._patterns[emotion] = []
        
        # Check for recurring pattern
        patterns = self._patterns[emotion]
        
        # Look for similar triggers
        for pattern in patterns:
            if any(
                trigger in event.trigger or event.trigger in trigger
                for trigger in pattern.triggers
            ):
                pattern.count += 1
                pattern.frequency = min(1.0, pattern.count / len(self._events))
                pattern.last_observed = event.timestamp
                return
        
        # Create new pattern if this is a recurring emotion
        if len([e for e in self._events if e.emotion == emotion]) >= 2:
            patterns.append(EmotionPattern(
                pattern_type=EmotionPatternType.TRIGGER,
                emotion=emotion,
                frequency=0.5,
                triggers=[event.trigger],
                description=f"Pattern triggered by: {event.trigger[:50]}",
                last_observed=event.timestamp,
                count=1,
            ))
    
    def _save(self):
        """Save memory to disk."""
        if not self._storage_path:
            return
        
        with self._lock:
            data = {
                "events": [e.to_dict() for e in self._events],
                "patterns": {
                    emotion: [p.to_dict() for p in patterns]
                    for emotion, patterns in self._patterns.items()
                }
            }
            
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load(self):
        """Load memory from disk."""
        if not self._storage_path or not os.path.exists(self._storage_path):
            return
        
        with self._lock:
            try:
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._events = [
                    EmotionEvent.from_dict(e) for e in data.get("events", [])
                ]
                
                self._patterns = {}
                for emotion, patterns_data in data.get("patterns", {}).items():
                    self._patterns[emotion] = [
                        EmotionPattern(
                            pattern_type=EmotionPatternType(p["pattern_type"]),
                            emotion=p["emotion"],
                            frequency=p["frequency"],
                            triggers=p["triggers"],
                            description=p["description"],
                            last_observed=p["last_observed"],
                            count=p.get("count", 0),
                        )
                        for p in patterns_data
                    ]
            except Exception:
                pass


def get_emotion_memory() -> EmotionMemory:
    """Get or create global emotion memory instance."""
    global _emotion_memory_instance
    if _emotion_memory_instance is None:
        _emotion_memory_instance = EmotionMemory()
    return _emotion_memory_instance


def record_emotion(
    emotion: str,
    intensity: float,
    trigger: str,
    **kwargs
) -> EmotionEvent:
    """Convenience function to record an emotion."""
    return get_emotion_memory().record(emotion, intensity, trigger, **kwargs)
