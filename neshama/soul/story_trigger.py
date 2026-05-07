# Soul Layer - Story Trigger Module
"""
StoryTriggerEngine - Emotion-driven story event triggering system.

Monitors NPC emotional states and triggers story events when conditions are met.

Trigger Types:
- EMOTION_THRESHOLD: Single emotion exceeds threshold
- EMOTION_COMBO: Multiple emotions at specific levels
- EMOTION_CHANGE: Rapid emotion value changes
- RELATIONSHIP_THRESHOLD: NPC-player relationship reaches threshold
- MULTI_NPC_CONDITION: Multiple NPCs meet conditions simultaneously
- TIME_BASED: Emotion persists for specified duration

Pure rule-based triggering, no LLM calls.
Target: <5ms per trigger check.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import uuid
import logging
import threading

logger = logging.getLogger(__name__)


class TriggerConditionType(Enum):
    """Types of trigger conditions."""
    EMOTION_THRESHOLD = "emotion_threshold"
    EMOTION_COMBO = "emotion_combo"
    EMOTION_CHANGE = "emotion_change"
    RELATIONSHIP_THRESHOLD = "relationship_threshold"
    MULTI_NPC_CONDITION = "multi_npc_condition"
    TIME_BASED = "time_based"


class ConditionOperator(Enum):
    """Logical operators for combining conditions."""
    AND = "and"
    OR = "or"


class StoryEffectType(Enum):
    """Types of story effects."""
    SPAWN_QUEST = "spawn_quest"
    UNLOCK_DIALOGUE = "unlock_dialogue"
    CHANGE_FACTION = "change_faction"
    TRIGGER_WORLD_EVENT = "trigger_world_event"
    MODIFY_NPC = "modify_npc"
    SEND_NOTIFICATION = "send_notification"


@dataclass
class TriggerCondition:
    """A single condition for story triggering."""
    condition_type: TriggerConditionType
    npc_id: Optional[str] = None  # None = check all NPCs
    emotion: Optional[str] = None
    threshold: Optional[float] = None
    direction: Optional[str] = None  # "rising", "falling", "any"
    change_magnitude: Optional[float] = None  # For EMOTION_CHANGE
    emotions: Optional[Dict[str, float]] = None  # For EMOTION_COMBO
    relationship_type: Optional[str] = None  # For RELATIONSHIP_THRESHOLD
    relationship_target: Optional[str] = None
    duration_seconds: Optional[float] = None  # For TIME_BASED
    operator: ConditionOperator = ConditionOperator.AND  # For combining with other conditions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_type": self.condition_type.value,
            "npc_id": self.npc_id,
            "emotion": self.emotion,
            "threshold": self.threshold,
            "direction": self.direction,
            "change_magnitude": self.change_magnitude,
            "emotions": self.emotions,
            "relationship_type": self.relationship_type,
            "relationship_target": self.relationship_target,
            "duration_seconds": self.duration_seconds,
            "operator": self.operator.value,
        }


@dataclass
class StoryEffect:
    """An effect to execute when story trigger fires."""
    effect_type: StoryEffectType
    target: str  # NPC ID / World Event ID / Quest ID
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type.value,
            "target": self.target,
            "params": self.params,
        }


@dataclass
class StoryTrigger:
    """A story trigger configuration."""
    trigger_id: str
    name: str
    description: str
    conditions: List[TriggerCondition]
    effects: List[StoryEffect]
    cooldown: float = 60.0  # Seconds before same trigger can fire again
    priority: int = 0  # Higher = checked first
    one_shot: bool = False  # Fire only once
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "name": self.name,
            "description": self.description,
            "conditions": [c.to_dict() for c in self.conditions],
            "effects": [e.to_dict() for e in self.effects],
            "cooldown": self.cooldown,
            "priority": self.priority,
            "one_shot": self.one_shot,
            "enabled": self.enabled,
        }


@dataclass
class TriggeredEvent:
    """A triggered story event."""
    trigger_id: str
    trigger_name: str
    npc_id: Optional[str]
    triggered_at: datetime = field(default_factory=datetime.now)
    effects: List[StoryEffect] = field(default_factory=list)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "trigger_id": self.trigger_id,
            "trigger_name": self.trigger_name,
            "npc_id": self.npc_id,
            "triggered_at": self.triggered_at.isoformat(),
            "effects": [e.to_dict() for e in self.effects],
        }


class StoryTriggerEngine:
    """
    Engine for monitoring emotions and triggering story events.
    
    Maintains:
    - Registered triggers
    - Trigger history (for cooldown/one-shot)
    - Emotion snapshots (for change detection)
    - Time tracking (for duration-based triggers)
    
    Example:
        >>> engine = StoryTriggerEngine()
        >>> 
        >>> # Register a trigger
        >>> engine.register_trigger(StoryTrigger(
        ...     trigger_id="rage_lockdown",
        ...     name="NPC暴怒封锁",
        ...     conditions=[TriggerCondition(
        ...         condition_type=TriggerConditionType.EMOTION_THRESHOLD,
        ...         emotion="anger", threshold=0.8
        ...     )],
        ...     effects=[StoryEffect(
        ...         effect_type=StoryEffectType.TRIGGER_WORLD_EVENT,
        ...         target="area_lockdown"
        ...     )]
        ... ))
        >>> 
        >>> # Check triggers (call every tick)
        >>> events = engine.check_triggers(npc_emotions={"anger": 0.85})
        >>> for event in events:
        ...     print(f"Triggered: {event.trigger_name}")
    """
    
    def __init__(self):
        """Initialize the story trigger engine."""
        # Registered triggers
        self._triggers: Dict[str, StoryTrigger] = {}
        
        # Trigger history: trigger_id -> list of last triggered times
        self._trigger_history: Dict[str, List[datetime]] = defaultdict(list)
        
        # One-shot triggers that have fired
        self._fired_one_shot: Set[str] = set()
        
        # Emotion snapshots for change detection: npc_id -> {emotion -> (value, timestamp)}
        self._emotion_snapshots: Dict[str, Dict[str, Tuple[float, datetime]]] = defaultdict(dict)
        
        # Duration tracking: npc_id -> {trigger_id -> start_time}
        self._duration_tracking: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        
        # Active triggered events
        self._active_events: Dict[str, TriggeredEvent] = {}
        
        # Callbacks for when triggers fire
        self._callbacks: List[Callable[[TriggeredEvent], None]] = []
        
        # Thread lock for thread safety
        self._lock = threading.Lock()
        
        logger.info("StoryTriggerEngine initialized")
    
    def register_trigger(self, trigger: StoryTrigger) -> bool:
        """
        Register a story trigger.
        
        Args:
            trigger: The trigger to register
            
        Returns:
            True if registered, False if trigger_id already exists
        """
        with self._lock:
            if trigger.trigger_id in self._triggers:
                logger.warning(f"Trigger {trigger.trigger_id} already exists")
                return False
            
            self._triggers[trigger.trigger_id] = trigger
            logger.info(f"Registered trigger: {trigger.trigger_id} ({trigger.name})")
            return True
    
    def unregister_trigger(self, trigger_id: str) -> bool:
        """Unregister a story trigger."""
        with self._lock:
            if trigger_id in self._triggers:
                del self._triggers[trigger_id]
                logger.info(f"Unregistered trigger: {trigger_id}")
                return True
            return False
    
    def get_trigger(self, trigger_id: str) -> Optional[StoryTrigger]:
        """Get a trigger by ID."""
        return self._triggers.get(trigger_id)
    
    def list_triggers(self) -> List[StoryTrigger]:
        """List all registered triggers."""
        return list(self._triggers.values())
    
    def enable_trigger(self, trigger_id: str, enabled: bool = True):
        """Enable or disable a trigger."""
        with self._lock:
            if trigger_id in self._triggers:
                self._triggers[trigger_id].enabled = enabled
                logger.info(f"Trigger {trigger_id} {'enabled' if enabled else 'disabled'}")
    
    def check_triggers(
        self,
        npc_emotions: Optional[Dict[str, Dict[str, float]]] = None,
        # npc_emotions: {npc_id: {emotion: value}}
        npc_relationships: Optional[Dict[str, Dict[str, str]]] = None,
        # npc_relationships: {npc_id: {target_id: relationship_type}}
    ) -> List[TriggeredEvent]:
        """
        Check all triggers against current state.
        
        Args:
            npc_emotions: Current emotion states keyed by NPC ID
            npc_relationships: Current relationship states
            
        Returns:
            List of triggered events
        """
        triggered_events = []
        now = datetime.now()
        
        npc_emotions = npc_emotions or {}
        npc_relationships = npc_relationships or {}
        
        with self._lock:
            # Sort triggers by priority (higher first)
            sorted_triggers = sorted(
                [t for t in self._triggers.values() if t.enabled],
                key=lambda x: -x.priority
            )
            
            for trigger in sorted_triggers:
                # Skip one-shot triggers that already fired
                if trigger.one_shot and trigger.trigger_id in self._fired_one_shot:
                    continue
                
                # Check cooldown
                if self._is_in_cooldown(trigger.trigger_id, now):
                    continue
                
                # Check all conditions
                if self._check_conditions(trigger, npc_emotions, npc_relationships, now):
                    # Fire the trigger
                    event = self._fire_trigger(trigger, now)
                    triggered_events.append(event)
                    
                    # Update history
                    self._trigger_history[trigger.trigger_id].append(now)
                    
                    # Mark one-shot
                    if trigger.one_shot:
                        self._fired_one_shot.add(trigger.trigger_id)
                    
                    # Notify callbacks
                    for callback in self._callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
        
        return triggered_events
    
    def _is_in_cooldown(self, trigger_id: str, now: datetime) -> bool:
        """Check if trigger is in cooldown period."""
        if trigger_id not in self._trigger_history:
            return False
        
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return False
        
        last_triggered = self._trigger_history[trigger_id][-1]
        elapsed = (now - last_triggered).total_seconds()
        return elapsed < trigger.cooldown
    
    def _check_conditions(
        self,
        trigger: StoryTrigger,
        npc_emotions: Dict[str, Dict[str, float]],
        npc_relationships: Dict[str, Dict[str, str]],
        now: datetime,
    ) -> bool:
        """Check if all conditions of a trigger are met."""
        if not trigger.conditions:
            return False
        
        results = []
        
        for condition in trigger.conditions:
            result = self._check_single_condition(condition, npc_emotions, npc_relationships, now)
            results.append(result)
        
        # Combine results based on operators
        # For simplicity, we use the first condition's operator as the global operator
        if not results:
            return False
        
        # Default to AND logic
        return all(results)
    
    def _check_single_condition(
        self,
        condition: TriggerCondition,
        npc_emotions: Dict[str, Dict[str, float]],
        npc_relationships: Dict[str, Dict[str, str]],
        now: datetime,
    ) -> bool:
        """Check a single condition."""
        ctype = condition.condition_type
        
        if ctype == TriggerConditionType.EMOTION_THRESHOLD:
            return self._check_emotion_threshold(condition, npc_emotions)
        
        elif ctype == TriggerConditionType.EMOTION_COMBO:
            return self._check_emotion_combo(condition, npc_emotions)
        
        elif ctype == TriggerConditionType.EMOTION_CHANGE:
            return self._check_emotion_change(condition, npc_emotions, now)
        
        elif ctype == TriggerConditionType.RELATIONSHIP_THRESHOLD:
            return self._check_relationship_threshold(condition, npc_relationships)
        
        elif ctype == TriggerConditionType.MULTI_NPC_CONDITION:
            return self._check_multi_npc(condition, npc_emotions)
        
        elif ctype == TriggerConditionType.TIME_BASED:
            return self._check_time_based(condition, npc_emotions, now)
        
        return False
    
    def _check_emotion_threshold(
        self,
        condition: TriggerCondition,
        npc_emotions: Dict[str, Dict[str, float]],
    ) -> bool:
        """Check if emotion exceeds threshold."""
        npc_id = condition.npc_id
        emotion = condition.emotion
        threshold = condition.threshold
        direction = condition.direction or "rising"
        
        if not npc_id or not emotion or threshold is None:
            return False
        
        # Check specific NPC
        if npc_id in npc_emotions:
            value = npc_emotions[npc_id].get(emotion, 0.0)
            
            if direction == "rising":
                return value >= threshold
            elif direction == "falling":
                return value <= threshold
            else:  # "any"
                return value >= threshold
        
        return False
    
    def _check_emotion_combo(
        self,
        condition: TriggerCondition,
        npc_emotions: Dict[str, Dict[str, float]],
    ) -> bool:
        """Check if emotion combo is satisfied."""
        npc_id = condition.npc_id
        required_emotions = condition.emotions
        
        if not npc_id or not required_emotions:
            return False
        
        if npc_id not in npc_emotions:
            return False
        
        current = npc_emotions[npc_id]
        
        for emotion, threshold in required_emotions.items():
            if current.get(emotion, 0.0) < threshold:
                return False
        
        return True
    
    def _check_emotion_change(
        self,
        condition: TriggerCondition,
        npc_emotions: Dict[str, Dict[str, float]],
        now: datetime,
    ) -> bool:
        """Check if emotion changed significantly."""
        npc_id = condition.npc_id
        emotion = condition.emotion
        magnitude = condition.change_magnitude
        direction = condition.direction
        
        if not npc_id or not emotion or magnitude is None:
            return False
        
        if npc_id not in npc_emotions:
            return False
        
        current_value = npc_emotions[npc_id].get(emotion, 0.0)
        
        # Update snapshot
        if npc_id not in self._emotion_snapshots:
            self._emotion_snapshots[npc_id] = {}
        
        if emotion in self._emotion_snapshots[npc_id]:
            prev_value, _ = self._emotion_snapshots[npc_id][emotion]
            change = abs(current_value - prev_value)
            
            # Check direction if specified
            if direction == "rising" and current_value <= prev_value:
                self._emotion_snapshots[npc_id][emotion] = (current_value, now)
                return False
            elif direction == "falling" and current_value >= prev_value:
                self._emotion_snapshots[npc_id][emotion] = (current_value, now)
                return False
            
            # Check magnitude
            if change >= magnitude:
                self._emotion_snapshots[npc_id][emotion] = (current_value, now)
                return True
        else:
            # First time seeing this emotion, can't detect change
            self._emotion_snapshots[npc_id][emotion] = (current_value, now)
        
        return False
    
    def _check_relationship_threshold(
        self,
        condition: TriggerCondition,
        npc_relationships: Dict[str, Dict[str, str]],
    ) -> bool:
        """Check if relationship meets threshold."""
        npc_id = condition.npc_id
        target = condition.relationship_target
        rel_type = condition.relationship_type
        
        if not npc_id or not target or not rel_type:
            return False
        
        if npc_id not in npc_relationships:
            return False
        
        current_rel = npc_relationships[npc_id].get(target)
        return current_rel == rel_type
    
    def _check_multi_npc(
        self,
        condition: TriggerCondition,
        npc_emotions: Dict[str, Dict[str, float]],
    ) -> bool:
        """Check if multiple NPCs meet conditions."""
        # This requires a more complex params structure
        # For now, check if at least 2 NPCs have the specified emotion above threshold
        emotion = condition.emotion
        threshold = condition.threshold
        
        if not emotion or threshold is None:
            return False
        
        count = 0
        for npc_id, emotions in npc_emotions.items():
            if emotions.get(emotion, 0.0) >= threshold:
                count += 1
        
        return count >= 2
    
    def _check_time_based(
        self,
        condition: TriggerCondition,
        npc_emotions: Dict[str, Dict[str, float]],
        now: datetime,
    ) -> bool:
        """Check if emotion has persisted for duration."""
        npc_id = condition.npc_id
        emotion = condition.emotion
        threshold = condition.threshold
        duration = condition.duration_seconds
        
        if not npc_id or not emotion or threshold is None or duration is None:
            return False
        
        if npc_id not in npc_emotions:
            return False
        
        value = npc_emotions[npc_id].get(emotion, 0.0)
        
        # Tracking key
        tracking_key = f"{npc_id}:{emotion}"
        
        if value >= threshold:
            # Emotion is above threshold
            if tracking_key not in self._duration_tracking.get(npc_id, {}):
                # Start tracking
                if npc_id not in self._duration_tracking:
                    self._duration_tracking[npc_id] = {}
                self._duration_tracking[npc_id][tracking_key] = now
            
            # Check duration
            start_time = self._duration_tracking[npc_id][tracking_key]
            elapsed = (now - start_time).total_seconds()
            return elapsed >= duration
        else:
            # Emotion dropped, reset tracking
            if npc_id in self._duration_tracking and tracking_key in self._duration_tracking[npc_id]:
                del self._duration_tracking[npc_id][tracking_key]
        
        return False
    
    def _fire_trigger(self, trigger: StoryTrigger, now: datetime) -> TriggeredEvent:
        """Fire a trigger and create an event."""
        # Find the NPC involved (if any)
        npc_id = None
        for condition in trigger.conditions:
            if condition.npc_id:
                npc_id = condition.npc_id
                break
        
        event = TriggeredEvent(
            trigger_id=trigger.trigger_id,
            trigger_name=trigger.name,
            npc_id=npc_id,
            triggered_at=now,
            effects=trigger.effects.copy(),
        )
        
        # Store active event
        self._active_events[event.event_id] = event
        
        logger.info(f"Trigger fired: {trigger.trigger_id} ({trigger.name})")
        return event
    
    def subscribe(self, callback: Callable[[TriggeredEvent], None]):
        """Subscribe to trigger events."""
        self._callbacks.append(callback)
    
    def unsubscribe(self, callback: Callable[[TriggeredEvent], None]):
        """Unsubscribe from trigger events."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_active_events(self) -> List[TriggeredEvent]:
        """Get all currently active triggered events."""
        return list(self._active_events.values())
    
    def clear_history(self, trigger_id: Optional[str] = None):
        """Clear trigger history."""
        with self._lock:
            if trigger_id:
                self._trigger_history.pop(trigger_id, None)
                self._fired_one_shot.discard(trigger_id)
            else:
                self._trigger_history.clear()
                self._fired_one_shot.clear()


# Global instance for convenience
_global_engine: Optional[StoryTriggerEngine] = None


def get_story_trigger_engine() -> StoryTriggerEngine:
    """Get the global story trigger engine instance."""
    global _global_engine
    if _global_engine is None:
        _global_engine = StoryTriggerEngine()
    return _global_engine


def create_story_trigger_engine() -> StoryTriggerEngine:
    """Create a new story trigger engine (for testing)."""
    return StoryTriggerEngine()
