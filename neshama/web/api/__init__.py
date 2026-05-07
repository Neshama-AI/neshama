"""
Neshama Web API

API routers for Soul Panel.
"""

from . import soul, emotion, memory, evolution, chat, config
from . import composite_emotion, entity_graph, progressive_summarization
from . import model_marketplace, coding_plans, game
from . import session, ws, rate_limiter, voice
from . import provider
from . import billing
from . import health
from . import gdpr
from . import auth

__all__ = [
    "soul",
    "emotion",
    "memory",
    "evolution",
    "chat",
    "config",
    "composite_emotion",
    "entity_graph",
    "progressive_summarization",
    "model_marketplace",
    "coding_plans",
    "game",
    "session",
    "ws",
    "rate_limiter",
    "voice",
    "provider",
    "billing",
    "health",
    "gdpr",
    "auth",
]
