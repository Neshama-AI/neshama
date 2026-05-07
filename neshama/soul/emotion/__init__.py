# Soul Layer - Emotion Module
"""
Emotion System Module

Contains:
- recognizer.py - Emotion recognition
- responder.py - Emotion response generation
- memory.py - Emotion memory storage
"""

from .recognizer import (
    EmotionRecognizer,
    EmotionCategory,
    EmotionTag,
    EmotionPattern,
    emotion_recognizer,
    recognize_emotion
)

from .responder import (
    EmotionResponder,
    ResponseStrategy,
    ResponseTemplate,
    emotion_responder,
    generate_emotional_response
)

from .memory import (
    EmotionMemory,
    EmotionEvent,
    EmotionPattern as EmotionPatternData,
    EmotionPatternType,
    get_emotion_memory,
    record_emotion
)

from .composite import (
    CompositeEmotion,
    CompositeEmotionResult,
    EmotionState,
    BaseEmotion,
    create_composite_engine,
    synthesize_from_emotions,
)

from .game_event import (
    GameEventEngine,
    GameEvent,
    GameEventType,
    EmotionDelta,
    EventChainResult,
    create_game_event_engine,
)

from .fast_path import (
    EmotionFastPath,
    FastPathResult,
    ResponseHint,
    ResponseTone,
    Urgency,
    SuggestedAction,
    create_fast_path,
)

__all__ = [
    # Recognizer
    "EmotionRecognizer",
    "EmotionCategory",
    "EmotionTag",
    "EmotionPattern",
    "emotion_recognizer",
    "recognize_emotion",
    
    # Responder
    "EmotionResponder",
    "ResponseStrategy",
    "ResponseTemplate",
    "emotion_responder",
    "generate_emotional_response",
    
    # Memory
    "EmotionMemory",
    "EmotionEvent",
    "EmotionPatternType",
    "get_emotion_memory",
    "record_emotion",

    # Composite Emotion
    "CompositeEmotion",
    "CompositeEmotionResult",
    "EmotionState",
    "BaseEmotion",
    "create_composite_engine",
    "synthesize_from_emotions",

    # Game Event Engine
    "GameEventEngine",
    "GameEvent",
    "GameEventType",
    "EmotionDelta",
    "EventChainResult",
    "create_game_event_engine",

    # Fast Path
    "EmotionFastPath",
    "FastPathResult",
    "ResponseHint",
    "ResponseTone",
    "Urgency",
    "SuggestedAction",
    "create_fast_path",
]
