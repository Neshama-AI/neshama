"""
Neshama - AI Agent Personality Operating System

Neshama is an open-source AI Agent personality operating system,
giving agents a soul through the OCEAN personality model,
six behavioral systems, and layered memory architecture.
"""

__version__ = "1.0.0"
__author__ = "Neshama Team"

from neshama.core.ocean import OceanParams, OceanManager
from neshama.core.personality import Personality, PersonalityConfig, Desire
from neshama.core.engine import NeshamaEngine, EngineConfig, ChatResponse
from neshama.core.conversation import ConversationManager, Session, Message
from neshama.soul import (
    CompositeEmotion,
    CompositeEmotionResult,
    EmotionState,
    BaseEmotion,
    create_composite_engine,
    synthesize_from_emotions,
    EntityGraph,
    EntityNode,
    GraphEdge,
    EntityType,
    RelationType,
    EdgeDirection,
    create_entity_graph,
    extract_entities_from_text,
    ProgressiveSummarizer,
    L0Entry,
    L1Entry,
    L2Entry,
    QualityScore,
    create_progressive_summarizer,
)

__all__ = [
    # Version
    "__version__",
    
    # OCEAN
    "OceanParams",
    "OceanManager",
    
    # Personality
    "Personality",
    "PersonalityConfig",
    "Desire",
    
    # Engine
    "NeshamaEngine",
    "EngineConfig",
    "ChatResponse",
    
    # Conversation
    "ConversationManager",
    "Session",
    "Message",

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
]
