# Memory Layer - Medium-Term Memory
"""
Medium-Term Memory - User Profile, Preferences, and Habits

Features:
- Structured user profile storage
- Real-time preference updates
- Habit pattern learning
- Incremental update and merge support
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import json
import threading
import os


@dataclass
class UserProfile:
    """User profile structure."""
    name: Optional[str] = None
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    interests: List[str] = field(default_factory=list)
    profession: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "language": self.language,
            "timezone": self.timezone,
            "interests": self.interests,
            "profession": self.profession,
            "custom_fields": self.custom_fields,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        return cls(
            name=data.get("name"),
            language=data.get("language", "zh-CN"),
            timezone=data.get("timezone", "Asia/Shanghai"),
            interests=data.get("interests", []),
            profession=data.get("profession"),
            custom_fields=data.get("custom_fields", {}),
        )


@dataclass
class Preference:
    """User preference record."""
    key: str  # Preference dimension
    value: Any
    confidence: float = 1.0  # Confidence 0-1
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "explicit"  # "explicit" | "implicit"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "updated_at": self.updated_at,
            "source": self.source,
        }


@dataclass
class Habit:
    """User habit pattern."""
    pattern: str  # Habit description
    frequency: float  # Occurrence frequency 0-1
    last_observed: str = field(default_factory=lambda: datetime.now().isoformat())
    context: str = "general"  # Trigger context
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "frequency": self.frequency,
            "last_observed": self.last_observed,
            "context": self.context,
        }


class MediumTermMemory:
    """
    Medium-Term Memory - User Profile, Preferences, and Habits
    
    Example:
        >>> memory = MediumTermMemory(agent_id="agent_001")
        >>> 
        >>> # Set user profile
        >>> memory.set_profile(UserProfile(name="Zhang San", language="zh-CN"))
        >>> 
        >>> # Update preferences
        >>> memory.update_preference("response_style", "concise", confidence=0.8)
        >>> 
        >>> # Record habits
        >>> memory.record_habit("Usually asks questions on weekday mornings", context="time")
    """
    
    def __init__(
        self,
        agent_id: str,
        storage_path: Optional[str] = None,
        auto_save: bool = True,
    ):
        """
        Initialize medium-term memory.
        
        Args:
            agent_id: Agent identifier
            storage_path: Persistence file path
            auto_save: Whether to auto-save changes
        """
        self._agent_id = agent_id
        self._storage_path = storage_path
        self._auto_save = auto_save
        self._lock = threading.RLock()
        
        self._profile: Optional[UserProfile] = None
        self._preferences: Dict[str, Preference] = {}
        self._habits: List[Habit] = []
        
        if storage_path and os.path.exists(storage_path):
            self._load()
    
    def set_profile(self, profile: UserProfile) -> None:
        """Set user profile."""
        with self._lock:
            self._profile = profile
            if self._auto_save:
                self._save()
    
    def get_profile(self) -> Optional[UserProfile]:
        """Get user profile."""
        return self._profile
    
    def update_preference(
        self,
        key: str,
        value: Any,
        confidence: float = 1.0,
        source: str = "implicit",
    ) -> Preference:
        """
        Update a preference.
        
        Args:
            key: Preference key
            value: Preference value
            confidence: Confidence level
            source: Source of the preference
            
        Returns:
            Updated Preference
        """
        with self._lock:
            preference = Preference(
                key=key,
                value=value,
                confidence=confidence,
                source=source,
            )
            
            self._preferences[key] = preference
            
            if self._auto_save:
                self._save()
            
            return preference
    
    def get_preference(self, key: str) -> Optional[Preference]:
        """Get a preference by key."""
        return self._preferences.get(key)
    
    def get_all_preferences(self) -> Dict[str, Preference]:
        """Get all preferences."""
        return self._preferences.copy()
    
    def record_habit(
        self,
        pattern: str,
        frequency: float = 0.5,
        context: str = "general",
    ) -> Habit:
        """
        Record a habit.
        
        Args:
            pattern: Habit description
            frequency: Occurrence frequency
            context: Trigger context
            
        Returns:
            Created Habit
        """
        with self._lock:
            # Check for existing similar habit
            for habit in self._habits:
                if habit.pattern == pattern:
                    # Update existing
                    habit.frequency = (habit.frequency + frequency) / 2
                    habit.last_observed = datetime.now().isoformat()
                    
                    if self._auto_save:
                        self._save()
                    
                    return habit
            
            # Create new habit
            habit = Habit(
                pattern=pattern,
                frequency=frequency,
                context=context,
            )
            
            self._habits.append(habit)
            
            if self._auto_save:
                self._save()
            
            return habit
    
    def get_habits(
        self,
        context: Optional[str] = None,
        min_frequency: float = 0.0,
    ) -> List[Habit]:
        """
        Get habits with optional filtering.
        
        Args:
            context: Filter by context
            min_frequency: Minimum frequency threshold
            
        Returns:
            List of matching Habit objects
        """
        with self._lock:
            habits = self._habits
            
            if context:
                habits = [h for h in habits if h.context == context]
            
            if min_frequency > 0:
                habits = [h for h in habits if h.frequency >= min_frequency]
            
            return habits
    
    def get_summary(self) -> Dict[str, Any]:
        """Get memory summary."""
        with self._lock:
            return {
                "profile": self._profile.to_dict() if self._profile else None,
                "preferences_count": len(self._preferences),
                "habits_count": len(self._habits),
                "habits": [h.to_dict() for h in self._habits],
            }
    
    def _save(self) -> None:
        """Save to disk."""
        if not self._storage_path:
            return
        
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
                
                data = {
                    "profile": self._profile.to_dict() if self._profile else None,
                    "preferences": {
                        k: v.to_dict() for k, v in self._preferences.items()
                    },
                    "habits": [h.to_dict() for h in self._habits],
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
                
                if data.get("profile"):
                    self._profile = UserProfile.from_dict(data["profile"])
                
                self._preferences = {
                    k: Preference(**v) for k, v in data.get("preferences", {}).items()
                }
                
                self._habits = [Habit(**h) for h in data.get("habits", [])]
            except Exception:
                pass
