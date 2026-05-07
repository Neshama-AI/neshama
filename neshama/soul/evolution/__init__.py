# Soul Layer - Evolution Module
"""
Personality Evolution Engine

Manages gradual personality changes in agents.
"""

from .engine import (
    EvolutionEngine,
    PersonalityTrait,
    EvolutionRule,
    EvolutionTrigger,
    EvolutionDirection,
    evolution_engine,
)

__all__ = [
    "EvolutionEngine",
    "PersonalityTrait",
    "EvolutionRule",
    "EvolutionTrigger",
    "EvolutionDirection",
    "evolution_engine",
]
