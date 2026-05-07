# Soul Layer - Creativity Module
"""
Creativity System Module

Contains:
- inspiration.py - Inspiration and idea generation
- style.py - Creative style management
"""

from .inspiration import (
    InspirationEngine,
    IdeaSeed,
    inspiration_engine,
    generate_ideas,
)
from .style import (
    CreativeStyle,
    StyleProfile,
    creative_style,
)

__all__ = [
    # Inspiration
    "InspirationEngine",
    "IdeaSeed",
    "inspiration_engine",
    "generate_ideas",
    
    # Style
    "CreativeStyle",
    "StyleProfile",
    "creative_style",
]
