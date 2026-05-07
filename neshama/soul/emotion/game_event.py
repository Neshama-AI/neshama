# Soul Layer - Game Event Engine
"""
GameEventEngine - Maps game events to emotion changes.

Pure rule-based event processing with no LLM calls.
Optimized for <10ms single computation.

Features:
- 15 game event types with emotion mappings
- Event intensity scaling (0-1)
- Event chain support for complex emotion scenarios
- OCEAN personality modifier support
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math


class GameEventType(Enum):
    """All supported game event types."""
    PLAYER_ATTACKED = "player_attacked"
    PLAYER_HELPED = "player_helped"
    ITEM_RECEIVED = "item_received"
    ITEM_LOST = "item_lost"
    QUEST_COMPLETED = "quest_completed"
    QUEST_FAILED = "quest_failed"
    NPC_INSULTED = "npc_insulted"
    NPC_COMPLIMENTED = "npc_complimented"
    ENVIRONMENT_CHANGED = "environment_changed"
    RELATIONSHIP_CHANGED = "relationship_changed"
    TIME_PASSED = "time_passed"
    COMBAT_STARTED = "combat_started"
    COMBAT_ENDED = "combat_ended"
    DEATH_WITNESSED = "death_witnessed"
    GIFT_GIVEN = "gift_given"


# Base emotion mappings: event_type -> [(emotion, base_delta), ...]
# Deltas are scaled by intensity (0-1) before application
EVENT_EMOTION_MAPPINGS: Dict[GameEventType, List[Tuple[str, float]]] = {
    GameEventType.PLAYER_ATTACKED: [
        ("anger", 0.3),
        ("fear", 0.2),
    ],
    GameEventType.PLAYER_HELPED: [
        ("trust", 0.4),
        ("joy", 0.3),
    ],
    GameEventType.ITEM_RECEIVED: [
        ("joy", 0.3),
        ("surprise", 0.2),
    ],
    GameEventType.ITEM_LOST: [
        ("sadness", 0.3),
        ("anger", 0.2),
    ],
    GameEventType.QUEST_COMPLETED: [
        ("joy", 0.4),
        ("pride", 0.3),
        ("anticipation", 0.2),
    ],
    GameEventType.QUEST_FAILED: [
        ("sadness", 0.3),
        ("anger", 0.2),
        ("fear", 0.15),
    ],
    GameEventType.NPC_INSULTED: [
        ("anger", 0.4),
        ("sadness", 0.2),
        ("disgust", 0.2),
    ],
    GameEventType.NPC_COMPLIMENTED: [
        ("joy", 0.3),
        ("trust", 0.3),
        ("surprise", 0.1),
    ],
    GameEventType.ENVIRONMENT_CHANGED: [
        ("fear", 0.2),
        ("surprise", 0.25),
        ("anticipation", 0.15),
    ],
    GameEventType.RELATIONSHIP_CHANGED: [
        ("trust", 0.3),
        ("sadness", 0.2),
    ],
    GameEventType.TIME_PASSED: [
        # Time passing slightly reduces strong emotions
        ("sadness", 0.05),
    ],
    GameEventType.COMBAT_STARTED: [
        ("fear", 0.35),
        ("anger", 0.25),
        ("surprise", 0.15),
    ],
    GameEventType.COMBAT_ENDED: [
        # Victory or defeat context matters, use neutral base
        ("joy", 0.2),
        ("fear", 0.1),
        ("sadness", 0.1),
    ],
    GameEventType.DEATH_WITNESSED: [
        ("sadness", 0.4),
        ("fear", 0.3),
        ("surprise", 0.2),
    ],
    GameEventType.GIFT_GIVEN: [
        ("joy", 0.35),
        ("trust", 0.35),
        ("surprise", 0.15),
    ],
}

# OCEAN personality modifiers affect emotion response
# Format: (personality_trait, threshold, multiplier)
# If trait_value >= threshold, apply multiplier to positive emotions
PERSONALITY_MODIFIERS: Dict[GameEventType, List[Tuple[str, float, float]]] = {
    GameEventType.PLAYER_HELPED: [
        ("extraversion", 0.7, 1.3),  # High extraversion = more joy
        ("agreeableness", 0.7, 1.2),  # High agreeableness = more trust
    ],
    GameEventType.NPC_INSULTED: [
        ("neuroticism", 0.7, 1.5),  # High neuroticism = more anger/sadness
        ("agreeableness", 0.7, 0.5),  # High agreeableness = less anger
    ],
    GameEventType.QUEST_COMPLETED: [
        ("extraversion", 0.6, 1.2),  # More expressive joy
        ("conscientiousness", 0.6, 1.3),  # More pride
    ],
    GameEventType.DEATH_WITNESSED: [
        ("neuroticism", 0.7, 1.4),  # More fearful/sad
        ("agreeableness", 0.6, 0.6),  # Less affected if agreeable
    ],
}


@dataclass
class GameEvent:
    """
    A game event that triggers emotion changes.
    
    Attributes:
        event_type: Type of the game event
        intensity: Event intensity from 0.0 to 1.0
        context: Optional context (e.g., attacker name, item id)
        timestamp: Optional timestamp (defaults to now)
        chain_id: Optional chain ID for grouping related events
    """
    event_type: GameEventType
    intensity: float = 1.0
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    chain_id: Optional[str] = None
    
    def __post_init__(self):
        self.intensity = max(0.0, min(1.0, self.intensity))


@dataclass
class EmotionDelta:
    """Represents an emotion change from an event."""
    emotion: str
    delta: float
    source_event: GameEventType
    scaled_by_intensity: float  # Final delta after intensity scaling


@dataclass
class EventChainResult:
    """Result of processing an event chain."""
    chain_id: str
    total_deltas: List[EmotionDelta]
    dominant_emotion: str
    dominant_intensity: float
    event_count: int


# Emotions considered "positive" for grudge factor reduction
POSITIVE_EMOTIONS = {"joy", "trust", "gratitude", "love", "relief", "delight", "optimism", "pride"}

# Grudge factor based on relationship type
# When an NPC has a negative relationship with the event source,
# positive emotion effects are reduced by (1 - grudge_factor)
RELATIONSHIP_GRUDGE_MAP: Dict[str, float] = {
    "hostile": 0.5,
    "dislikes": 0.4,
    "enemy": 0.6,
    "rival": 0.3,
    "suspicious": 0.2,
    "neutral": 0.0,
    "friendly": 0.0,
    "likes": 0.0,
    "allied": 0.0,
}


class GameEventEngine:
    """
    Rule-based game event to emotion mapping engine.
    
    Pure Python computation, no LLM calls.
    Optimized for <10ms per event processing.
    
    Example:
        >>> engine = GameEventEngine()
        >>> event = GameEvent(GameEventType.PLAYER_HELPED, intensity=0.8)
        >>> deltas = engine.process_event(event)
        >>> for delta in deltas:
        ...     print(f"{delta.emotion}: {delta.scaled_by_intensity:+.2f}")
    """
    
    def __init__(self, personality: Optional[Dict[str, float]] = None):
        """
        Initialize the GameEventEngine.
        
        Args:
            personality: Optional OCEAN personality scores (0-1 for each trait)
        """
        self.personality = personality or {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5,
        }
    
    def process_event(
        self,
        event: GameEvent,
        relationship_type: Optional[str] = None,
    ) -> List[EmotionDelta]:
        """
        Process a single game event and return emotion deltas.
        
        Args:
            event: The game event to process
            relationship_type: Optional relationship type between NPC and event source
                (e.g. "hostile", "dislikes", "friendly"). Used for grudge factor.
            
        Returns:
            List of EmotionDelta objects representing emotion changes
        """
        deltas = []
        base_mappings = EVENT_EMOTION_MAPPINGS.get(event.event_type, [])
        
        # Calculate grudge factor from relationship type
        grudge_factor = 0.0
        if relationship_type:
            grudge_factor = RELATIONSHIP_GRUDGE_MAP.get(
                relationship_type.lower(), 0.0
            )
        
        for emotion, base_delta in base_mappings:
            # Scale by intensity
            scaled = base_delta * event.intensity
            
            # Apply personality modifiers
            modifiers = PERSONALITY_MODIFIERS.get(event.event_type, [])
            for trait, threshold, multiplier in modifiers:
                trait_value = self.personality.get(trait, 0.5)
                if trait_value >= threshold:
                    # Only modify positive deltas (joy, trust, etc.)
                    if scaled > 0:
                        scaled *= multiplier
                    break
            
            # Apply grudge factor: reduce positive emotion deltas from hostile sources
            if grudge_factor > 0 and emotion in POSITIVE_EMOTIONS and scaled > 0:
                reduction = 1.0 - grudge_factor
                scaled *= reduction
            
            # Clamp to valid range
            scaled = max(-1.0, min(1.0, scaled))
            
            deltas.append(EmotionDelta(
                emotion=emotion,
                delta=base_delta,
                source_event=event.event_type,
                scaled_by_intensity=round(scaled, 4),
            ))
        
        return deltas
    
    def process_chain(self, events: List[GameEvent], chain_id: str) -> EventChainResult:
        """
        Process a chain of related events.
        
        Emotion changes are accumulated across the chain.
        
        Args:
            events: List of events in the chain
            chain_id: Unique identifier for this chain
            
        Returns:
            EventChainResult with accumulated emotion changes
        """
        all_deltas: Dict[str, List[EmotionDelta]] = {}
        
        for event in events:
            event.chain_id = chain_id
            deltas = self.process_event(event)
            for delta in deltas:
                if delta.emotion not in all_deltas:
                    all_deltas[delta.emotion] = []
                all_deltas[delta.emotion].append(delta)
        
        # Sum up all deltas per emotion
        total_deltas = []
        emotion_sums: Dict[str, float] = {}
        for emotion, deltas in all_deltas.items():
            total = sum(d.scaled_by_intensity for d in deltas)
            emotion_sums[emotion] = total
            total_deltas.append(EmotionDelta(
                emotion=emotion,
                delta=sum(d.delta for d in deltas),
                source_event=deltas[0].source_event,
                scaled_by_intensity=round(total, 4),
            ))
        
        # Find dominant emotion
        if emotion_sums:
            dominant = max(emotion_sums.items(), key=lambda x: abs(x[1]))
            dominant_emotion = dominant[0]
            dominant_intensity = abs(dominant[1])
        else:
            dominant_emotion = "neutral"
            dominant_intensity = 0.0
        
        return EventChainResult(
            chain_id=chain_id,
            total_deltas=total_deltas,
            dominant_emotion=dominant_emotion,
            dominant_intensity=dominant_intensity,
            event_count=len(events),
        )
    
    def get_event_info(self, event_type: GameEventType) -> Dict[str, Any]:
        """Get information about what emotions a given event type affects."""
        mappings = EVENT_EMOTION_MAPPINGS.get(event_type, [])
        return {
            "event_type": event_type.value,
            "affected_emotions": [emotion for emotion, _ in mappings],
            "base_deltas": {emotion: delta for emotion, delta in mappings},
        }
    
    def list_all_events(self) -> List[Dict[str, Any]]:
        """List all supported game events with their emotion mappings."""
        return [
            self.get_event_info(event_type)
            for event_type in GameEventType
        ]


def create_game_event_engine(personality: Optional[Dict[str, float]] = None) -> GameEventEngine:
    """Factory function to create a GameEventEngine."""
    return GameEventEngine(personality=personality)
