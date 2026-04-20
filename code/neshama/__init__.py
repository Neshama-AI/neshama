"""
Neshama Python SDK - AI Personality Operating System
"""

__version__ = "0.1.0"
__author__ = "Neshama Team"

from neshama.core.ocean import OceanParams, OceanManager
from neshama.core.personality import Personality, PersonalityConfig
from neshama.core.validator import Validator, ValidationResult
from neshama.tools.emotion import EmotionTracker, Emotion, EmotionLevel
from neshama.tools.memory import MemoryManager
from neshama.tools.reflection import ReflectionTrigger, ReflectionType

__all__ = [
    # Core
    "OceanParams",
    "OceanManager",
    "Personality",
    "PersonalityConfig",
    "Validator",
    "ValidationResult",
    # Tools
    "EmotionTracker",
    "Emotion",
    "EmotionLevel",
    "MemoryManager",
    "ReflectionTrigger",
    "ReflectionType",
]
