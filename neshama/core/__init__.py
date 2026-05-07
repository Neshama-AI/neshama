"""
Neshama Core Module

Core components for the Neshama personality operating system.
"""

from neshama.core.ocean import OceanParams, OceanManager
from neshama.core.personality import Personality, PersonalityConfig, Desire
from neshama.core.engine import NeshamaEngine, EngineConfig, ChatResponse
from neshama.core.conversation import ConversationManager, Session, Message

__all__ = [
    "OceanParams",
    "OceanManager",
    "Personality",
    "PersonalityConfig",
    "Desire",
    "NeshamaEngine",
    "EngineConfig",
    "ChatResponse",
    "ConversationManager",
    "Session",
    "Message",
]
