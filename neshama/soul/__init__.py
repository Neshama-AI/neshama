"""
Neshama Soul Module

The soul system that gives agents personality and emotional depth.
"""

from neshama.soul.emotion import (
    EmotionRecognizer,
    EmotionResponder,
    EmotionMemory,
    EmotionCategory,
    EmotionTag,
    EmotionPattern,
    CompositeEmotion,
    CompositeEmotionResult,
    EmotionState,
    BaseEmotion,
    create_composite_engine,
    synthesize_from_emotions,
)
from neshama.soul.loader import SoulLoader, SoulLoaderConfig
from neshama.soul.entity_graph import (
    EntityGraph,
    EntityNode,
    GraphEdge,
    EntityType,
    RelationType,
    EdgeDirection,
    create_entity_graph,
    extract_entities_from_text,
)
from neshama.soul.progressive_summarization import (
    ProgressiveSummarizer,
    L0Entry,
    L1Entry,
    L2Entry,
    QualityScore,
    create_progressive_summarizer,
)
from neshama.soul.npc_manager import (
    NPCManager,
    NPCSoul,
    PersonalityProfile,
    get_npc_manager,
    create_npc_manager,
)
from neshama.soul.npc_behavior import (
    NPCBehaviorBridge,
    BehaviorProfile,
    BehaviorModifier,
    BehaviorType,
    DialogueStyle,
    MovementPattern,
    create_behavior_bridge,
)

__all__ = [
    # Emotion
    "EmotionRecognizer",
    "EmotionResponder",
    "EmotionMemory",
    "EmotionCategory",
    "EmotionTag",
    "EmotionPattern",

    # Composite Emotion
    "CompositeEmotion",
    "CompositeEmotionResult",
    "EmotionState",
    "BaseEmotion",
    "create_composite_engine",
    "synthesize_from_emotions",

    # Entity Graph
    "EntityGraph",
    "EntityNode",
    "GraphEdge",
    "EntityType",
    "RelationType",
    "EdgeDirection",
    "create_entity_graph",
    "extract_entities_from_text",

    # Progressive Summarization
    "ProgressiveSummarizer",
    "L0Entry",
    "L1Entry",
    "L2Entry",
    "QualityScore",
    "create_progressive_summarizer",

    # Loader
    "SoulLoader",
    "SoulLoaderConfig",

    # NPC Manager
    "NPCManager",
    "NPCSoul",
    "PersonalityProfile",
    "get_npc_manager",
    "create_npc_manager",

    # NPC Behavior
    "NPCBehaviorBridge",
    "BehaviorProfile",
    "BehaviorModifier",
    "BehaviorType",
    "DialogueStyle",
    "MovementPattern",
    "create_behavior_bridge",
]
