# Soul Layer - Composite Emotion Module
"""
Composite Emotion System

Features:
- Composite emotion synthesis from base emotions
- Emotion decay over time
- Emotion conflict resolution
- Emotion threshold triggering

Design:
- Joy + Surprise → Delight
- Sadness + Anger → Resentment
- Fear + Disgust → Aversion
- Joy + Anticipation → Optimism
- Trust + Joy → Love
- Fear + Surprise → Shock
- Sadness + Disgust → Regret
- Anger + Disgust → Contempt
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import math


# Base emotion categories (must match EmotionCategory in recognizer.py)
class BaseEmotion(Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    DESIRE = "desire"  # For composite emotions like envy


# Predefined composite emotion recipes
COMPOSITE_RECIPES: Dict[str, Tuple[Tuple[BaseEmotion, float], ...]] = {
    "delight":      ((BaseEmotion.JOY, 0.6), (BaseEmotion.SURPRISE, 0.4)),
    "resentment":   ((BaseEmotion.SADNESS, 0.5), (BaseEmotion.ANGER, 0.5)),
    "aversion":     ((BaseEmotion.FEAR, 0.5), (BaseEmotion.DISGUST, 0.5)),
    "optimism":     ((BaseEmotion.JOY, 0.5), (BaseEmotion.ANTICIPATION, 0.5)),
    "love":         ((BaseEmotion.TRUST, 0.5), (BaseEmotion.JOY, 0.5)),
    "shock":        ((BaseEmotion.FEAR, 0.5), (BaseEmotion.SURPRISE, 0.5)),
    "regret":       ((BaseEmotion.SADNESS, 0.6), (BaseEmotion.DISGUST, 0.4)),
    "contempt":     ((BaseEmotion.ANGER, 0.6), (BaseEmotion.DISGUST, 0.4)),
    "gratitude":    ((BaseEmotion.JOY, 0.4), (BaseEmotion.TRUST, 0.6)),
    "guilt":        ((BaseEmotion.SADNESS, 0.5), (BaseEmotion.FEAR, 0.5)),
    "envy":         ((BaseEmotion.ANGER, 0.4), (BaseEmotion.DESIRE, 0.6)),
    "pride":        ((BaseEmotion.JOY, 0.5), (BaseEmotion.ANGER, 0.5)),  # self-anger
    "anxiety":      ((BaseEmotion.FEAR, 0.6), (BaseEmotion.ANTICIPATION, 0.4)),
    "nostalgia":    ((BaseEmotion.JOY, 0.4), (BaseEmotion.SADNESS, 0.6)),
    "relief":       ((BaseEmotion.JOY, 0.5), (BaseEmotion.FEAR, 0.5)),
}


# Opposing emotion pairs for conflict resolution
OPPOSING_PAIRS = [
    (BaseEmotion.JOY, BaseEmotion.SADNESS),
    (BaseEmotion.TRUST, BaseEmotion.DISGUST),
    (BaseEmotion.FEAR, BaseEmotion.ANGER),
    (BaseEmotion.ANTICIPATION, BaseEmotion.SURPRISE),
]


@dataclass
class EmotionState:
    """A single emotion state with its value."""
    emotion: str          # emotion name string
    intensity: float      # 0-1
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.intensity = max(0.0, min(1.0, self.intensity))


@dataclass
class CompositeEmotionResult:
    """Result of composite emotion computation."""
    name: str
    intensity: float
    components: Dict[str, float]  # base emotion -> contribution
    is_novel: bool = False  # True if not in predefined recipes


class CompositeEmotion:
    """
    Composite Emotion Engine.

    Synthesizes complex emotions from base emotions,
    handles decay, conflict resolution, and threshold triggers.

    Example:
        >>> engine = CompositeEmotion(neuroticism=0.3)
        >>> engine.set_base_emotion("joy", 0.8)
        >>> engine.set_base_emotion("surprise", 0.6)
        >>> result = engine.synthesize()
        >>> print(result.name, result.intensity)  # "delight", 0.72

        >>> # Trigger tick (call each frame/step)
        >>> engine.tick(delta_seconds=10.0)
    """

    # Default decay half-life in seconds for each emotion
    DEFAULT_HALF_LIFE: Dict[str, float] = {
        "joy": 120.0,
        "sadness": 180.0,
        "anger": 90.0,
        "fear": 60.0,
        "surprise": 30.0,
        "disgust": 90.0,
        "trust": 240.0,
        "anticipation": 120.0,
    }

    # Neuroticism modifies decay rate: high neuroticism = slower decay
    NEUROTICISM_DECAY_MODIFIER: float = 0.5  # multiplier range

    # Threshold for triggering behavior tendencies
    DEFAULT_THRESHOLD: float = 0.7

    def __init__(
        self,
        neuroticism: float = 0.5,
        base_decay_halflife: float = 120.0,
        conflict_strategy: str = "dominance",  # "dominance" | "cancel" | "blend"
    ):
        """
        Initialize CompositeEmotion engine.

        Args:
            neuroticism: OCEAN neuroticism score (0-1). High = slow decay.
            base_decay_halflife: Base half-life in seconds.
            conflict_strategy: How to handle opposing emotions.
        """
        self.neuroticism = neuroticism
        self.base_decay_halflife = base_decay_halflife
        self.conflict_strategy = conflict_strategy

        # Active base emotions
        self._emotions: Dict[str, EmotionState] = {}

        # Behavior tendency thresholds (emotion -> threshold)
        self._thresholds: Dict[str, float] = {}

        # Event callbacks: {emotion_name: [callable]}
        self._listeners: Dict[str, List] = {}

        # Last tick timestamp
        self._last_tick: datetime = datetime.now()

    # ── Base Emotion Management ────────────────────────────────────────────

    def set_base_emotion(
        self,
        emotion: str,
        intensity: float,
        timestamp: Optional[datetime] = None,
    ) -> EmotionState:
        """
        Set a base emotion intensity (overwrites previous value).

        Args:
            emotion: Emotion name (e.g. "joy", "surprise")
            intensity: 0-1 intensity value
            timestamp: Optional explicit timestamp

        Returns:
            The created/updated EmotionState
        """
        ts = timestamp or datetime.now()
        state = EmotionState(emotion=emotion.lower(), intensity=intensity, timestamp=ts)
        self._emotions[emotion.lower()] = state

        # Check threshold
        threshold = self._thresholds.get(emotion.lower(), self.DEFAULT_THRESHOLD)
        if intensity >= threshold:
            self._trigger(emotion.lower(), intensity)

        return state

    def adjust_emotion(self, emotion: str, delta: float) -> EmotionState:
        """
        Adjust an existing emotion by a delta, or set it if not present.

        Args:
            emotion: Emotion name
            delta: Amount to add (can be negative)

        Returns:
            Updated EmotionState
        """
        emotion = emotion.lower()
        current = self._emotions.get(emotion)
        if current:
            new_intensity = max(0.0, min(1.0, current.intensity + delta))
            return self.set_base_emotion(emotion, new_intensity, datetime.now())
        else:
            return self.set_base_emotion(emotion, max(0.0, min(1.0, delta)))

    def get_emotion(self, emotion: str) -> Optional[float]:
        """Get current intensity of a base emotion (0-1)."""
        state = self._emotions.get(emotion.lower())
        return state.intensity if state else None

    def get_all_emotions(self) -> Dict[str, float]:
        """Get all active base emotion intensities."""
        return {k: v.intensity for k, v in self._emotions.items()}

    def clear_emotions(self):
        """Clear all active emotions."""
        self._emotions.clear()

    # ── Synthesis ────────────────────────────────────────────────────────────

    def synthesize(self) -> CompositeEmotionResult:
        """
        Synthesize composite emotions from active base emotions.

        Returns:
            CompositeEmotionResult with the strongest composite emotion
        """
        if not self._emotions:
            return CompositeEmotionResult(name="neutral", intensity=0.0, components={})

        # Apply conflict resolution
        resolved = self._resolve_conflicts()

        # Single dominant emotion (no recipe needed for single emotion)
        sorted_emotions = sorted(resolved.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_emotions) == 1:
            top = sorted_emotions[0]
            return CompositeEmotionResult(
                name=top[0], intensity=top[1], components={top[0]: top[1]}
            )

        # Check predefined recipes (only when 2+ emotions present)
        composite = self._match_recipe(resolved)
        if composite:
            return composite

        # Ad-hoc composite: top 2 base emotions
        if len(sorted_emotions) >= 2:
            top1, top2 = sorted_emotions[0], sorted_emotions[1]
            name = f"{top1[0]}+{top2[0]}"
            intensity = (top1[1] + top2[1]) / 2 * 1.1  # slight boost
            intensity = min(1.0, intensity)
            components = {top1[0]: top1[1], top2[0]: top2[1]}
            return CompositeEmotionResult(
                name=name, intensity=intensity, components=components, is_novel=True
            )

        # Fallback: single dominant
        top = sorted_emotions[0]
        return CompositeEmotionResult(
            name=top[0], intensity=top[1], components={top[0]: top[1]}
        )

    def _resolve_conflicts(self) -> Dict[str, float]:
        """
        Resolve opposing emotion pairs.

        Strategies:
        - dominance: higher intensity wins, loser is reduced
        - cancel: opposing emotions reduce each other
        - blend: both emotions reduced proportionally
        """
        resolved = {k: v.intensity for k, v in self._emotions.items()}

        for emotion_a, emotion_b in OPPOSING_PAIRS:
            a_name = emotion_a.value
            b_name = emotion_b.value
            if a_name not in resolved or b_name not in resolved:
                continue

            a_val = resolved[a_name]
            b_val = resolved[b_name]

            if self.conflict_strategy == "dominance":
                if a_val > b_val:
                    resolved[b_name] = max(0, b_val - (a_val - b_val) * 0.5)
                elif b_val > a_val:
                    resolved[a_name] = max(0, a_val - (b_val - a_val) * 0.5)
                else:
                    resolved[a_name] = a_val * 0.5
                    resolved[b_name] = b_val * 0.5

            elif self.conflict_strategy == "cancel":
                diff = abs(a_val - b_val)
                resolved[a_name] = diff * 0.5
                resolved[b_name] = diff * 0.5

            else:  # blend
                avg = (a_val + b_val) / 2
                resolved[a_name] = avg
                resolved[b_name] = avg

        return resolved

    def _match_recipe(self, emotions: Dict[str, float]) -> Optional[CompositeEmotionResult]:
        """Try to match current emotions against predefined recipes."""
        best_match: Optional[CompositeEmotionResult] = None
        best_score = -1.0

        for recipe_name, components in COMPOSITE_RECIPES.items():
            score = 0.0
            weighted_sum = 0.0
            weight_total = 0.0
            present_weight = 0.0
            matched_components: Dict[str, float] = {}

            for emotion_enum, weight in components:
                emotion_name = emotion_enum.value
                weight_total += weight
                if emotion_name in emotions:
                    contrib = emotions[emotion_name] * weight
                    score += contrib
                    weighted_sum += contrib
                    present_weight += weight
                    matched_components[emotion_name] = emotions[emotion_name]

            if present_weight == 0:
                continue

            # Require at least 75% of recipe emotions to be present
            present_count = sum(
                1 for e, _ in components if e.value in emotions
            )
            if present_count < len(components) * 0.75:
                continue

            # Normalize by total weight, then penalize for missing components
            normalized = score / weight_total if weight_total > 0 else 0.0
            # Completeness bonus: reward having all recipe components
            completeness = present_weight / weight_total if weight_total > 0 else 0.0
            # Final score: weighted combination of match quality and completeness
            final_score = normalized * 0.6 + completeness * 0.4

            if final_score > best_score:
                best_score = final_score
                # Weighted intensity
                intensity = min(1.0, normalized * 1.2)
                best_match = CompositeEmotionResult(
                    name=recipe_name,
                    intensity=round(intensity, 4),
                    components=matched_components,
                    is_novel=False,
                )

        return best_match

    # ── Decay ────────────────────────────────────────────────────────────────

    def tick(self, delta_seconds: Optional[float] = None) -> None:
        """
        Advance time, applying decay to all emotions.

        Args:
            delta_seconds: Time elapsed in seconds. If None, computed from last tick.
        """
        if delta_seconds is None:
            now = datetime.now()
            delta_seconds = (now - self._last_tick).total_seconds()
            self._last_tick = now

        if delta_seconds <= 0:
            return

        # Neuroticism modifier: high neuroticism slows decay (emotions linger longer)
        # Formula: decay_modifier = 0.2 + 0.8 * (1 - neuroticism)
        # neuroticism=0 → decay_modifier=1.0 (full speed)
        # neuroticism=1 → decay_modifier=0.2 (20% speed, emotions last 5x longer)
        decay_modifier = 0.2 + 0.8 * (1.0 - self.neuroticism)
        decay_modifier = max(0.1, decay_modifier)  # minimum 10%

        to_remove = []
        for name, state in list(self._emotions.items()):
            halflife = self.DEFAULT_HALF_LIFE.get(name, self.base_decay_halflife)
            adjusted_halflife = halflife * decay_modifier

            # Exponential decay: intensity *= 0.5 ^ (dt / half_life)
            decay_factor = 0.5 ** (delta_seconds / adjusted_halflife)
            new_intensity = state.intensity * decay_factor

            if new_intensity < 0.01:  # drop below threshold
                to_remove.append(name)
            else:
                state.intensity = new_intensity
                state.timestamp = datetime.now()

        for name in to_remove:
            del self._emotions[name]

    def tick_and_get(self, delta_seconds: float) -> float:
        """
        Tick decay and return the intensity of the first emotion.

        Convenience method for testing.
        """
        self.tick(delta_seconds=delta_seconds)
        emotions = list(self._emotions.values())
        return emotions[0].intensity if emotions else 0.0

    # ── Threshold Triggers ────────────────────────────────────────────────────

    def set_threshold(self, emotion: str, threshold: float) -> None:
        """Set trigger threshold for a specific emotion."""
        self._thresholds[emotion.lower()] = max(0.0, min(1.0, threshold))

    def register_listener(self, emotion: str, callback) -> None:
        """Register a callback for when an emotion exceeds its threshold."""
        emotion = emotion.lower()
        if emotion not in self._listeners:
            self._listeners[emotion] = []
        self._listeners[emotion].append(callback)

    def _trigger(self, emotion: str, intensity: float) -> None:
        """Fire all registered listeners for an emotion trigger."""
        for callback in self._listeners.get(emotion, []):
            try:
                callback(emotion, intensity)
            except Exception:
                pass  # Don't let listener errors break the engine

    def get_triggered_emotions(self, threshold: float = None) -> List[str]:
        """Get list of emotions currently above threshold."""
        threshold = threshold or self.DEFAULT_THRESHOLD
        return [
            name for name, state in self._emotions.items()
            if state.intensity >= threshold
        ]

    # ── State Export ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Export current state as dictionary."""
        return {
            "base_emotions": {
                name: {
                    "intensity": round(state.intensity, 4),
                    "timestamp": state.timestamp.isoformat(),
                }
                for name, state in self._emotions.items()
            },
            "composite": self.synthesize().__dict__,
            "triggered": self.get_triggered_emotions(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs) -> "CompositeEmotion":
        """Reconstruct from dictionary."""
        engine = cls(**kwargs)
        for name, state_data in data.get("base_emotions", {}).items():
            from datetime import datetime
            ts = datetime.fromisoformat(state_data["timestamp"])
            engine.set_base_emotion(name, state_data["intensity"], timestamp=ts)
        return engine


# ── Convenience functions ─────────────────────────────────────────────────────

def create_composite_engine(neuroticism: float = 0.5) -> CompositeEmotion:
    """Create a configured CompositeEmotion engine."""
    return CompositeEmotion(neuroticism=neuroticism)


def synthesize_from_emotions(
    emotions: Dict[str, float],
    neuroticism: float = 0.5,
) -> CompositeEmotionResult:
    """
    One-shot synthesis from a dictionary of emotion intensities.

    Args:
        emotions: {emotion_name: intensity} dict
        neuroticism: OCEAN neuroticism score

    Returns:
        CompositeEmotionResult
    """
    engine = CompositeEmotion(neuroticism=neuroticism)
    for name, intensity in emotions.items():
        engine.set_base_emotion(name, intensity)
    return engine.synthesize()
