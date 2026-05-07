# Soul Layer - Emotion Driver Module
"""
EmotionDriver - Real-time emotion driving engine.

Features:
- Emotion decay over time (exponential decay to baseline)
- Emotion diffusion (similar emotions reinforce each other)
- Emotion conflict resolution (opposing emotions compete)
- Behavior trigger monitoring (threshold crossings trigger events)

The driver operates on pure numerical calculations, no LLM calls.
Target: <1ms per tick.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import math
import logging

logger = logging.getLogger(__name__)


# Base decay rates per emotion type (per second)
# Higher = faster decay, emotions return to baseline quicker
EMOTION_DECAY_RATES: Dict[str, float] = {
    "anger": 0.02,      # Anger decays slowly - grudges last
    "fear": 0.03,       # Fear decays moderately
    "sadness": 0.04,    # Sadness decays at medium rate
    "joy": 0.05,       # Joy decays faster
    "surprise": 0.08,   # Surprise fades quickly
    "disgust": 0.03,   # Disgust lingers
    "trust": 0.04,      # Trust decays at medium rate
    "anticipation": 0.05,  # Anticipation fades moderately
    "desire": 0.04,     # Desire decays at medium rate
    "love": 0.03,       # Love decays slowly
    "shock": 0.10,      # Shock fades very fast
    "anxiety": 0.02,    # Anxiety lingers (slow decay)
    "regret": 0.03,     # Regret lingers moderately
    "contempt": 0.02,   # Contempt is long-lasting
    "gratitude": 0.04,  # Gratitude decays at medium rate
    "guilt": 0.02,      # Guilt lingers
    "envy": 0.02,       # Envy is long-lasting
    "pride": 0.04,      # Pride fades moderately
    "optimism": 0.05,   # Optimism fades at medium rate
    "nostalgia": 0.02,  # Nostalgia lingers
    "relief": 0.05,     # Relief fades quickly
    "delight": 0.05,    # Delight fades moderately
    "resentment": 0.02, # Resentment is long-lasting
    "aversion": 0.03,  # Aversion lingers moderately
}

# Default decay rate for unknown emotions
DEFAULT_DECAY_RATE = 0.04

# Emotion similarity groups for diffusion
# Emotions in same group reinforce each other
EMOTION_SIMILARITY_GROUPS: List[Set[str]] = [
    {"joy", "love", "delight", "pride", "gratitude", "optimism", "relief", "nostalgia"},
    {"sadness", "regret", "guilt", "shock"},
    {"anger", "contempt", "resentment", "envy"},
    {"fear", "anxiety", "aversion"},
    {"surprise", "shock"},
    {"trust", "love", "gratitude"},
    {"anticipation", "desire", "optimism"},
    {"disgust", "contempt", "aversion"},
]

# Opposing emotion pairs for conflict resolution
EMOTION_OPPOSING_PAIRS: List[Tuple[str, str]] = [
    ("joy", "sadness"),
    ("trust", "disgust"),
    ("fear", "anger"),
    ("anticipation", "surprise"),
    ("joy", "anger"),  # joy and anger can compete
    ("trust", "fear"),  # trust and fear can compete
]


@dataclass
class EmotionEntry:
    """Single emotion entry with history."""
    name: str
    current: float          # Current intensity (0-1)
    baseline: float          # Natural baseline (0-1)
    decay_rate: float        # Decay rate (per second)
    last_update: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "current": round(self.current, 4),
            "baseline": round(self.baseline, 4),
            "decay_rate": round(self.decay_rate, 4),
            "last_update": self.last_update.isoformat(),
        }


@dataclass
class BehaviorTrigger:
    """A behavior trigger when emotion crosses threshold."""
    emotion: str
    threshold: float
    direction: str           # "rising" or "falling"
    value_at_trigger: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion": self.emotion,
            "threshold": self.threshold,
            "direction": self.direction,
            "value_at_trigger": round(self.value_at_trigger, 4),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EmotionTrajectoryPoint:
    """Single point in emotion trajectory prediction."""
    timestamp: float    # seconds from now
    emotions: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "seconds_from_now": round(self.timestamp, 2),
            "emotions": {k: round(v, 4) for k, v in self.emotions.items()},
        }


class EmotionDriver:
    """
    Real-time emotion driving engine.
    
    Manages the continuous evolution of emotions over time:
    - Decay: Emotions naturally return to baseline
    - Diffusion: Similar emotions reinforce each other
    - Conflict: Opposing emotions compete
    - Triggers: Threshold crossings trigger behavior changes
    
    Example:
        >>> driver = EmotionDriver(npc_id="tavern_keeper")
        >>> driver.set_emotion("anger", 0.8)
        >>> driver.set_emotion("trust", 0.5)
        >>> 
        >>> # Call tick every second
        >>> triggers = driver.tick("tavern_keeper", delta_seconds=1.0)
        >>> for trigger in triggers:
        ...     print(f"Triggered: {trigger.emotion} at {trigger.threshold}")
    """
    
    def __init__(
        self,
        npc_id: str,
        personality_neuroticism: float = 0.5,
        initial_emotions: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize EmotionDriver.
        
        Args:
            npc_id: NPC identifier
            personality_neuroticism: OCEAN neuroticism score (0-1)
                Higher values = emotions persist longer
            initial_emotions: Optional initial emotion state
        """
        self.npc_id = npc_id
        self.neuroticism = personality_neuroticism
        
        # Emotion storage: emotion_name -> EmotionEntry
        self._emotions: Dict[str, EmotionEntry] = {}
        
        # Track previous values for trigger detection
        self._prev_values: Dict[str, float] = {}
        
        # Pending triggers (cleared after retrieval)
        self._pending_triggers: List[BehaviorTrigger] = []
        
        # Diffusion strength (0-1)
        self._diffusion_strength = 0.1
        
        # Conflict resolution strength (0-1)
        self._conflict_strength = 0.15
        
        # Event pause flag (pauses decay when event is applied)
        self._decay_paused = False
        self._pause_until: Optional[datetime] = None
        
        # Initialize with defaults
        for emotion, rate in EMOTION_DECAY_RATES.items():
            self._emotions[emotion] = EmotionEntry(
                name=emotion,
                current=0.0,
                baseline=0.0,
                decay_rate=rate,
            )
        
        # Apply neuroticism modifier to all decay rates
        self._apply_neuroticism_modifier()
        
        # Set initial emotions if provided
        if initial_emotions:
            for emotion, value in initial_emotions.items():
                self.set_emotion(emotion, value)
    
    def _apply_neuroticism_modifier(self):
        """Apply neuroticism modifier to decay rates."""
        # Higher neuroticism = lower decay rate = emotions last longer
        modifier = 1.0 - (self.neuroticism * 0.5)  # Range: 0.5 to 1.0
        for entry in self._emotions.values():
            entry.decay_rate *= modifier
    
    def set_emotion(self, emotion: str, value: float, baseline: Optional[float] = None):
        """
        Set an emotion value.
        
        Args:
            emotion: Emotion name
            value: Intensity value (0-1)
            baseline: Optional custom baseline (defaults to value)
        """
        if emotion not in self._emotions:
            # Create new emotion entry with default decay
            decay_rate = EMOTION_DECAY_RATES.get(emotion, DEFAULT_DECAY_RATE)
            decay_rate *= (1.0 - (self.neuroticism * 0.5))
            self._emotions[emotion] = EmotionEntry(
                name=emotion,
                current=0.0,
                baseline=0.0,
                decay_rate=decay_rate,
            )
        
        entry = self._emotions[emotion]
        entry.current = max(0.0, min(1.0, value))
        entry.baseline = baseline if baseline is not None else entry.baseline
        entry.last_update = datetime.now()
        
        # Store previous value for trigger detection
        self._prev_values[emotion] = entry.current
    
    def get_emotion(self, emotion: str) -> float:
        """Get current value of an emotion."""
        if emotion in self._emotions:
            return self._emotions[emotion].current
        return 0.0
    
    def get_all_emotions(self) -> Dict[str, float]:
        """Get all current emotion values."""
        return {name: entry.current for name, entry in self._emotions.items()}
    
    def get_emotion_state(self) -> Dict[str, Any]:
        """Get full emotion state."""
        return {
            "npc_id": self.npc_id,
            "emotions": {name: entry.to_dict() for name, entry in self._emotions.items()},
            "pending_triggers": [t.to_dict() for t in self._pending_triggers],
        }
    
    def pause_decay(self, duration_seconds: float = 1.0):
        """
        Pause emotion decay (used when applying events).
        
        Args:
            duration_seconds: How long to pause
        """
        self._decay_paused = True
        self._pause_until = datetime.now()
    
    def resume_decay(self):
        """Resume emotion decay."""
        self._decay_paused = False
        self._pause_until = None
    
    def apply_event_delta(self, emotion_deltas: Dict[str, float]):
        """
        Apply emotion changes from a game event.
        
        This pauses decay, applies the delta, then resumes.
        
        Args:
            emotion_deltas: Dict of emotion -> delta to add
        """
        self.pause_decay()
        
        for emotion, delta in emotion_deltas.items():
            current = self.get_emotion(emotion)
            new_value = max(0.0, min(1.0, current + delta))
            self.set_emotion(emotion, new_value)
        
        self.resume_decay()
    
    def tick(self, delta_seconds: float) -> List[BehaviorTrigger]:
        """
        Advance emotion state by delta_seconds.
        
        This is the core loop:
        1. Apply decay
        2. Apply diffusion
        3. Resolve conflicts
        4. Check triggers
        
        Args:
            delta_seconds: Time elapsed since last tick
            
        Returns:
            List of BehaviorTrigger objects for threshold crossings
        """
        if self._decay_paused:
            return []
        
        triggers = []
        current_values = {}
        
        # Step 1: Apply decay to all emotions
        for name, entry in self._emotions.items():
            if entry.current != entry.baseline:
                # Exponential decay: current = baseline + (current - baseline) * exp(-decay_rate * time)
                diff = entry.current - entry.baseline
                decayed = entry.baseline + diff * math.exp(-entry.decay_rate * delta_seconds)
                entry.current = max(0.0, min(1.0, decayed))
                entry.last_update = datetime.now()
            current_values[name] = entry.current
        
        # Step 2: Apply diffusion (similar emotions reinforce)
        diffusion_changes = self._calculate_diffusion(current_values)
        for emotion, change in diffusion_changes.items():
            if emotion in self._emotions:
                self._emotions[emotion].current = max(0.0, min(1.0, 
                    self._emotions[emotion].current + change))
        
        # Step 3: Resolve conflicts (opposing emotions compete)
        conflict_changes = self._calculate_conflicts()
        for emotion, change in conflict_changes.items():
            if emotion in self._emotions:
                self._emotions[emotion].current = max(0.0, min(1.0,
                    self._emotions[emotion].current + change))
        
        # Step 4: Check for threshold triggers
        triggers = self._check_triggers()
        self._pending_triggers.extend(triggers)
        
        # Update previous values
        for name, entry in self._emotions.items():
            self._prev_values[name] = entry.current
        
        return triggers
    
    def _calculate_diffusion(self, current_values: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate emotion diffusion changes.
        
        Emotions in the same similarity group reinforce each other.
        """
        changes: Dict[str, float] = {}
        
        for group in EMOTION_SIMILARITY_GROUPS:
            # Find emotions in this group that have significant values
            group_emotions = {e: v for e, v in current_values.items() 
                            if e in group and v > 0.1}
            
            if len(group_emotions) > 1:
                # Calculate reinforcement
                avg_value = sum(group_emotions.values()) / len(group_emotions)
                for emotion in group_emotions:
                    if emotion in current_values:
                        # This emotion gets slightly boosted by similar emotions
                        other_avg = (sum(group_emotions.values()) - group_emotions[emotion]) / (len(group_emotions) - 1)
                        change = (other_avg - group_emotions[emotion]) * self._diffusion_strength * 0.1
                        changes[emotion] = changes.get(emotion, 0.0) + change
        
        return changes
    
    def _calculate_conflicts(self) -> Dict[str, float]:
        """
        Calculate emotion conflict resolution changes.
        
        Opposing emotions compete - the stronger one gradually suppresses the weaker.
        """
        changes: Dict[str, float] = {}
        
        for emotion1, emotion2 in EMOTION_OPPOSING_PAIRS:
            val1 = self._emotions.get(emotion1)
            val2 = self._emotions.get(emotion2)
            
            if val1 and val2:
                if val1.current > 0.1 and val2.current > 0.1:
                    # Both emotions are significant
                    diff = val1.current - val2.current
                    if abs(diff) > 0.1:
                        # Stronger emotion suppresses weaker
                        suppressed = emotion2 if diff > 0 else emotion1
                        stronger = emotion1 if diff > 0 else emotion2
                        change = -diff * self._conflict_strength * 0.05
                        changes[suppressed] = changes.get(suppressed, 0.0) + change
        
        return changes
    
    def _check_triggers(self) -> List[BehaviorTrigger]:
        """
        Check for threshold crossings and generate triggers.
        
        Triggers are generated when:
        - Emotion crosses a threshold from below (rising)
        - Emotion crosses a threshold from above (falling)
        """
        triggers = []
        
        # Common thresholds to check
        thresholds = [0.3, 0.5, 0.7, 0.8]
        
        for emotion, entry in self._emotions.items():
            prev = self._prev_values.get(emotion, entry.current)
            curr = entry.current
            
            for threshold in thresholds:
                # Rising trigger
                if prev < threshold <= curr:
                    triggers.append(BehaviorTrigger(
                        emotion=emotion,
                        threshold=threshold,
                        direction="rising",
                        value_at_trigger=curr,
                    ))
                # Falling trigger
                elif prev > threshold >= curr:
                    triggers.append(BehaviorTrigger(
                        emotion=emotion,
                        threshold=threshold,
                        direction="falling",
                        value_at_trigger=curr,
                    ))
        
        return triggers
    
    def get_active_triggers(self, min_threshold: float = 0.5) -> List[BehaviorTrigger]:
        """
        Get currently active triggers above threshold.
        
        Args:
            min_threshold: Minimum emotion value to consider
            
        Returns:
            List of BehaviorTrigger objects
        """
        active = []
        for emotion, entry in self._emotions.items():
            if entry.current >= min_threshold:
                active.append(BehaviorTrigger(
                    emotion=emotion,
                    threshold=min_threshold,
                    direction="active",
                    value_at_trigger=entry.current,
                ))
        return active
    
    def clear_triggers(self):
        """Clear all pending triggers."""
        self._pending_triggers.clear()
    
    def get_emotion_trajectory(
        self,
        duration_seconds: float,
        steps: int = 10,
    ) -> List[EmotionTrajectoryPoint]:
        """
        Predict emotion trajectory over time.
        
        Useful for AI planning and forecasting.
        
        Args:
            duration_seconds: How far into the future to predict
            steps: Number of trajectory points
            
        Returns:
            List of EmotionTrajectoryPoint objects
        """
        trajectory = []
        step_size = duration_seconds / max(1, steps - 1)
        
        # Clone current state for simulation
        sim_values = {name: entry.current for name, entry in self._emotions.items()}
        sim_baselines = {name: entry.baseline for name, entry in self._emotions.items()}
        sim_decays = {name: entry.decay_rate for name, entry in self._emotions.items()}
        
        for step in range(steps):
            time_elapsed = step * step_size
            
            # Calculate predicted values at this time
            predicted = {}
            for name in sim_values:
                baseline = sim_baselines.get(name, 0.0)
                current = sim_values.get(name, 0.0)
                decay_rate = sim_decays.get(name, DEFAULT_DECAY_RATE)
                
                if current != baseline:
                    diff = current - baseline
                    predicted[name] = baseline + diff * math.exp(-decay_rate * time_elapsed)
                else:
                    predicted[name] = baseline
            
            trajectory.append(EmotionTrajectoryPoint(
                timestamp=time_elapsed,
                emotions=predicted,
            ))
        
        return trajectory
    
    def get_dominant_emotion(self) -> Optional[Tuple[str, float]]:
        """
        Get the current dominant emotion.
        
        Returns:
            Tuple of (emotion_name, intensity) or None if no significant emotion
        """
        max_emotion = None
        max_value = 0.0
        
        for name, entry in self._emotions.items():
            if entry.current > max_value:
                max_value = entry.current
                max_emotion = name
        
        if max_value > 0.1:
            return (max_emotion, max_value)
        return None


# Global driver instances storage
_driver_instances: Dict[str, EmotionDriver] = {}


def get_driver(npc_id: str) -> EmotionDriver:
    """Get or create a driver instance for an NPC."""
    if npc_id not in _driver_instances:
        _driver_instances[npc_id] = EmotionDriver(npc_id=npc_id)
    return _driver_instances[npc_id]


def remove_driver(npc_id: str) -> bool:
    """Remove a driver instance."""
    if npc_id in _driver_instances:
        del _driver_instances[npc_id]
        return True
    return False
