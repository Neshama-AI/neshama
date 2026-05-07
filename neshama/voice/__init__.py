# Voice Module
"""
Voice Module - TTS/STT Provider Abstraction Layer

Provides unified voice interfaces for:
- Text-to-Speech (TTS)
- Speech-to-Text (STT)
- Emotion-aware voice synthesis
- Multiple provider support
"""

from .base import VoiceProvider, VoiceInfo, ProviderInfo, EmotionStyle
from .manager import VoiceManager, get_voice_manager

__all__ = [
    "VoiceProvider",
    "VoiceInfo",
    "ProviderInfo",
    "EmotionStyle",
    "VoiceManager",
    "get_voice_manager",
]
