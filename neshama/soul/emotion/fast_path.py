# Soul Layer - Emotion Fast Path
"""
EmotionFastPath - High-performance emotion processing pipeline.

From game event → emotion state → response hint in <10ms.
No LLM calls, pure Python computation.

Features:
- Event-driven emotion updates
- Response hint generation based on current emotion state
- Integration with CompositeEmotion engine
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import time


# Response tone options
class ResponseTone(Enum):
    FRIENDLY = "friendly"
    HOSTILE = "hostile"
    NERVOUS = "nervous"
    JOYFUL = "joyful"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    TRUSTING = "trusting"
    NEUTRAL = "neutral"
    PROUD = "proud"
    GRATEFUL = "grateful"


class Urgency(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Action suggestion types
class SuggestedAction(Enum):
    DIALOGUE_FRIENDLY = "dialogue_friendly"
    DIALOGUE_HOSTILE = "dialogue_hostile"
    DIALOGUE_CAUTIOUS = "dialogue_cautious"
    QUEST_OFFER = "quest_offer"
    QUEST_REFUSE = "quest_refuse"
    SHARE_INFO = "share_info"
    WITHHOLD_INFO = "withhold_info"
    FLEE = "flee"
    ATTACK = "attack"
    GIVE_GIFT = "give_gift"
    RECEIVE_GIFT = "receive_gift"
    CONSOLATION = "consolation"
    CELEBRATION = "celebration"
    WARNING = "warning"


# Tone to emotion mapping for hint generation
TONE_EMOTION_MAPPING: Dict[ResponseTone, Dict[str, float]] = {
    ResponseTone.FRIENDLY: {"trust": 0.6, "joy": 0.4},
    ResponseTone.HOSTILE: {"anger": 0.7, "disgust": 0.3},
    ResponseTone.NERVOUS: {"fear": 0.5, "anticipation": 0.3, "anxiety": 0.2},
    ResponseTone.JOYFUL: {"joy": 0.7, "surprise": 0.2},
    ResponseTone.SAD: {"sadness": 0.7, "fear": 0.2},
    ResponseTone.ANGRY: {"anger": 0.8, "disgust": 0.2},
    ResponseTone.FEARFUL: {"fear": 0.7, "surprise": 0.2},
    ResponseTone.SURPRISED: {"surprise": 0.6, "joy": 0.3},
    ResponseTone.TRUSTING: {"trust": 0.7, "joy": 0.3},
    ResponseTone.NEUTRAL: {"trust": 0.3, "joy": 0.2},
    ResponseTone.PROUD: {"joy": 0.5, "anger": 0.3},
    ResponseTone.GRATEFUL: {"trust": 0.5, "joy": 0.4},
}


@dataclass
class ResponseHint:
    """
    Hints for generating NPC response behavior.
    
    Unity C# can consume this directly.
    
    Attributes:
        tone: Suggested emotional tone for response
        urgency: How urgent the response should be
        suggested_actions: List of suggested actions
        confidence: Confidence score (0-1) for these hints
        reasoning: Brief explanation of the hint
    """
    tone: ResponseTone
    urgency: Urgency
    suggested_actions: List[SuggestedAction]
    confidence: float = 0.8
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Unity-friendly flat dict."""
        return {
            "tone": self.tone.value,
            "urgency": self.urgency.value,
            "suggested_actions": [a.value for a in self.suggested_actions],
            "confidence": round(self.confidence, 2),
            "reasoning": self.reasoning,
        }


@dataclass
class FastPathResult:
    """
    Result of the EmotionFastPath pipeline.
    
    Contains emotion state and response hints.
    """
    emotion_state: Dict[str, float]
    composite_emotion: Optional[str]
    composite_intensity: float
    response_hint: ResponseHint
    dominant_emotion: str
    dominant_intensity: float
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Unity-friendly flat dict."""
        return {
            "emotion_state": {k: round(v, 4) for k, v in self.emotion_state.items()},
            "composite_emotion": self.composite_emotion,
            "composite_intensity": round(self.composite_intensity, 4),
            "response_hint": self.response_hint.to_dict(),
            "dominant_emotion": self.dominant_emotion,
            "dominant_intensity": round(self.dominant_intensity, 4),
            "processing_time_ms": round(self.processing_time_ms, 2),
        }


class EmotionFastPath:
    """
    High-performance emotion processing pipeline.
    
    From game event → emotion state update → response hint.
    Target: <10ms total processing time.
    
    Example:
        >>> fast_path = EmotionFastPath(neuroticism=0.4)
        >>> event = GameEvent(GameEventType.PLAYER_HELPED, intensity=0.8)
        >>> result = fast_path.process(event)
        >>> print(result.response_hint.tone)  # ResponseTone.GRATEFUL
    """
    
    def __init__(
        self,
        neuroticism: float = 0.5,
        personality: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize the fast path.
        
        Args:
            neuroticism: OCEAN neuroticism score (0-1)
            personality: Full OCEAN personality profile
        """
        self._init_emotion_engine(neuroticism)
        from neshama.soul.emotion.game_event import GameEventEngine
        self._event_engine = GameEventEngine(personality=personality)
        self._processing_count = 0
    
    def _init_emotion_engine(self, neuroticism: float):
        """Initialize the composite emotion engine."""
        from neshama.soul.emotion.composite import CompositeEmotion
        self._emotion_engine = CompositeEmotion(neuroticism=neuroticism)
    
    def process(self, event) -> FastPathResult:
        """
        Process a game event through the fast path.
        
        Args:
            event: GameEvent from game_event.py
            
        Returns:
            FastPathResult with emotion state and response hints
        """
        start_time = time.perf_counter()
        
        # Step 1: Process event → emotion deltas
        deltas = self._event_engine.process_event(event)
        
        # Step 2: Apply deltas to emotion engine
        for delta in deltas:
            self._emotion_engine.adjust_emotion(delta.emotion, delta.scaled_by_intensity)
        
        # Step 3: Get current emotion state
        emotion_state = self._emotion_engine.get_all_emotions()
        
        # Step 4: Synthesize composite emotion
        composite_result = self._emotion_engine.synthesize()
        
        # Step 5: Generate response hint
        response_hint = self._generate_hint(emotion_state, composite_result)
        
        # Find dominant emotion
        if emotion_state:
            dominant = max(emotion_state.items(), key=lambda x: x[1])
            dominant_emotion = dominant[0]
            dominant_intensity = dominant[1]
        else:
            dominant_emotion = "neutral"
            dominant_intensity = 0.0
        
        processing_time = (time.perf_counter() - start_time) * 1000
        self._processing_count += 1
        
        return FastPathResult(
            emotion_state=emotion_state,
            composite_emotion=composite_result.name,
            composite_intensity=composite_result.intensity,
            response_hint=response_hint,
            dominant_emotion=dominant_emotion,
            dominant_intensity=dominant_intensity,
            processing_time_ms=processing_time,
        )
    
    def _generate_hint(
        self,
        emotion_state: Dict[str, float],
        composite: Any,
    ) -> ResponseHint:
        """Generate response hints based on emotion state."""
        from neshama.soul.emotion.composite import CompositeEmotionResult
        
        # Determine dominant tone based on emotion state
        tone, urgency, actions, reasoning = self._infer_response(
            emotion_state, composite
        )
        
        # Calculate confidence based on emotion clarity
        confidence = self._calculate_confidence(emotion_state)
        
        return ResponseHint(
            tone=tone,
            urgency=urgency,
            suggested_actions=actions,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def _infer_response(
        self,
        emotions: Dict[str, float],
        composite: Any,
    ) -> tuple:
        """Infer response parameters from emotions."""
        from neshama.soul.emotion.composite import CompositeEmotionResult
        
        # Default values
        tone = ResponseTone.NEUTRAL
        urgency = Urgency.LOW
        actions = [SuggestedAction.DIALOGUE_FRIENDLY]
        reasoning = "No strong emotion detected"
        
        if not emotions:
            return tone, urgency, actions, reasoning
        
        # Check for strong emotions and determine response
        anger = emotions.get("anger", 0.0)
        fear = emotions.get("fear", 0.0)
        joy = emotions.get("joy", 0.0)
        trust = emotions.get("trust", 0.0)
        sadness = emotions.get("sadness", 0.0)
        surprise = emotions.get("surprise", 0.0)
        disgust = emotions.get("disgust", 0.0)
        
        # Anger-based responses
        if anger > 0.6:
            tone = ResponseTone.HOSTILE
            urgency = Urgency.HIGH if anger > 0.8 else Urgency.MEDIUM
            actions = [SuggestedAction.DIALOGUE_HOSTILE]
            if anger > 0.8:
                actions.append(SuggestedAction.QUEST_REFUSE)
            reasoning = f"High anger ({anger:.2f})"
        elif anger > 0.3:
            tone = ResponseTone.ANGRY
            urgency = Urgency.MEDIUM
            actions = [SuggestedAction.DIALOGUE_HOSTILE, SuggestedAction.WITHHOLD_INFO]
            reasoning = f"Moderate anger ({anger:.2f})"
        
        # Fear-based responses
        elif fear > 0.6:
            tone = ResponseTone.FEARFUL
            urgency = Urgency.HIGH
            actions = [SuggestedAction.DIALOGUE_CAUTIOUS, SuggestedAction.FLEE]
            reasoning = f"High fear ({fear:.2f})"
        elif fear > 0.3:
            tone = ResponseTone.NERVOUS
            urgency = Urgency.MEDIUM
            actions = [SuggestedAction.DIALOGUE_CAUTIOUS]
            reasoning = f"Moderate fear ({fear:.2f})"
        
        # Joy-based responses
        elif joy > 0.5:
            tone = ResponseTone.JOYFUL
            urgency = Urgency.LOW
            actions = [SuggestedAction.DIALOGUE_FRIENDLY, SuggestedAction.CELEBRATION]
            if trust > 0.4:
                actions.append(SuggestedAction.SHARE_INFO)
                actions.append(SuggestedAction.QUEST_OFFER)
            reasoning = f"High joy ({joy:.2f})"
        
        # Trust-based responses
        elif trust > 0.5:
            tone = ResponseTone.TRUSTING
            urgency = Urgency.LOW
            actions = [SuggestedAction.DIALOGUE_FRIENDLY, SuggestedAction.SHARE_INFO]
            if composite and isinstance(composite, CompositeEmotionResult):
                if composite.name == "love":
                    actions.append(SuggestedAction.QUEST_OFFER)
            reasoning = f"High trust ({trust:.2f})"
        
        # Sadness-based responses
        elif sadness > 0.4:
            tone = ResponseTone.SAD
            urgency = Urgency.LOW
            actions = [SuggestedAction.CONSOLATION, SuggestedAction.DIALOGUE_CAUTIOUS]
            reasoning = f"Sadness detected ({sadness:.2f})"
        
        # Surprise-based responses
        elif surprise > 0.5:
            tone = ResponseTone.SURPRISED
            urgency = Urgency.MEDIUM
            actions = [SuggestedAction.DIALOGUE_CAUTIOUS]
            reasoning = f"Surprise detected ({surprise:.2f})"
        
        # Disgust-based responses
        elif disgust > 0.4:
            tone = ResponseTone.HOSTILE
            urgency = Urgency.MEDIUM
            actions = [SuggestedAction.DIALOGUE_HOSTILE, SuggestedAction.QUEST_REFUSE]
            reasoning = f"Disgust detected ({disgust:.2f})"
        
        # Composite emotion overrides
        if composite and isinstance(composite, CompositeEmotionResult) and composite.intensity > 0.5:
            composite_name = composite.name
            if composite_name == "gratitude":
                tone = ResponseTone.GRATEFUL
                actions = [SuggestedAction.GIVE_GIFT, SuggestedAction.SHARE_INFO]
                reasoning = "Gratitude composite emotion"
            elif composite_name == "pride":
                tone = ResponseTone.PROUD
                actions = [SuggestedAction.CELEBRATION, SuggestedAction.QUEST_OFFER]
                reasoning = "Pride composite emotion"
            elif composite_name == "love":
                tone = ResponseTone.TRUSTING
                actions = [SuggestedAction.SHARE_INFO, SuggestedAction.QUEST_OFFER]
                reasoning = "Love composite emotion"
        
        return tone, urgency, actions, reasoning
    
    def _calculate_confidence(self, emotions: Dict[str, float]) -> float:
        """Calculate confidence in the emotion interpretation."""
        if not emotions:
            return 0.5
        
        # More emotions = less clear signal = lower confidence
        num_emotions = len(emotions)
        if num_emotions <= 2:
            return 0.9
        
        # Check if there's a clear dominant emotion
        max_intensity = max(emotions.values()) if emotions else 0
        min_intensity = min(emotions.values()) if emotions else 0
        
        # Clear dominance = high confidence
        if max_intensity - min_intensity > 0.5:
            return 0.85
        
        # Many weak emotions = lower confidence
        if num_emotions >= 4:
            return 0.6
        
        return 0.75
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current emotion state without processing an event."""
        emotion_state = self._emotion_engine.get_all_emotions()
        composite = self._emotion_engine.synthesize()
        
        return {
            "emotion_state": {k: round(v, 4) for k, v in emotion_state.items()},
            "composite_emotion": composite.name,
            "composite_intensity": round(composite.intensity, 4),
            "dominant_emotion": max(emotion_state.items(), key=lambda x: x[1])[0] if emotion_state else "neutral",
        }
    
    def tick(self, delta_seconds: float):
        """Apply emotion decay."""
        self._emotion_engine.tick(delta_seconds)
    
    def clear(self):
        """Clear all emotions."""
        self._emotion_engine.clear_emotions()
    
    @property
    def processing_count(self) -> int:
        """Number of events processed."""
        return self._processing_count


def create_fast_path(
    neuroticism: float = 0.5,
    personality: Optional[Dict[str, float]] = None,
) -> EmotionFastPath:
    """Factory function to create an EmotionFastPath."""
    return EmotionFastPath(neuroticism=neuroticism, personality=personality)
