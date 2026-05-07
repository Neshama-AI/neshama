# Soul Layer - Creative Style Module
"""
Creative Style Management

Features:
- Style profiles with parameters
- Style adaptation based on context
- Multiple creative dimensions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class CreativeDimension(Enum):
    """Dimensions of creativity."""
    NOVELTY = "novelty"            # Originality and uniqueness
    UTILITY = "utility"            # Practical value and usefulness
    EXPRESSION = "expression"      # Emotional expression level
    COMPLEXITY = "complexity"       # Structural complexity
    ABSTRACTION = "abstraction"    # Level of abstraction


@dataclass
class StyleProfile:
    """A creative style profile."""
    name: str
    description: str
    
    # Dimension weights (0-1)
    novelty: float = 0.5
    utility: float = 0.5
    expression: float = 0.5
    complexity: float = 0.5
    abstraction: float = 0.5
    
    # Behavioral parameters
    risk_taking: float = 0.5       # How risky/unconventional
    flexibility: float = 0.5       # How flexible in approach
    persistence: float = 0.5       # How persistent in exploring
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "dimensions": {
                "novelty": self.novelty,
                "utility": self.utility,
                "expression": self.expression,
                "complexity": self.complexity,
                "abstraction": self.abstraction,
            },
            "behavioral": {
                "risk_taking": self.risk_taking,
                "flexibility": self.flexibility,
                "persistence": self.persistence,
            }
        }


# Predefined creative styles
CREATIVE_STYLES = {
    "analytical": StyleProfile(
        name="Analytical",
        description="Deep, systematic, and methodical",
        novelty=0.4,
        utility=0.8,
        expression=0.3,
        complexity=0.8,
        abstraction=0.6,
        risk_taking=0.2,
        flexibility=0.4,
        persistence=0.9,
    ),
    "creative": StyleProfile(
        name="Creative",
        description="Highly original and expressive",
        novelty=0.9,
        utility=0.5,
        expression=0.8,
        complexity=0.6,
        abstraction=0.7,
        risk_taking=0.8,
        flexibility=0.9,
        persistence=0.5,
    ),
    "practical": StyleProfile(
        name="Practical",
        description="Focused on real-world application",
        novelty=0.3,
        utility=0.9,
        expression=0.4,
        complexity=0.4,
        abstraction=0.3,
        risk_taking=0.2,
        flexibility=0.3,
        persistence=0.7,
    ),
    "visionary": StyleProfile(
        name="Visionary",
        description="Future-oriented and transformative",
        novelty=0.95,
        utility=0.6,
        expression=0.7,
        complexity=0.7,
        abstraction=0.9,
        risk_taking=0.9,
        flexibility=0.8,
        persistence=0.6,
    ),
    "balanced": StyleProfile(
        name="Balanced",
        description="Well-rounded and adaptive",
        novelty=0.5,
        utility=0.5,
        expression=0.5,
        complexity=0.5,
        abstraction=0.5,
        risk_taking=0.5,
        flexibility=0.5,
        persistence=0.5,
    ),
}


# Global creative style instance
creative_style = None


class CreativeStyle:
    """
    Creative Style Manager.
    
    Manages creative style profiles and adaptations.
    
    Example:
        >>> style = CreativeStyle()
        >>> profile = style.get_profile("creative")
        >>> style.adapt_for_context("brainstorming")
    """
    
    def __init__(self, default_style: str = "balanced"):
        """
        Initialize creative style manager.
        
        Args:
            default_style: Default style name
        """
        self._styles = CREATIVE_STYLES.copy()
        self._current_style = default_style
        self._context_adaptations: Dict[str, Dict[str, float]] = {}
        
        # Initialize context adaptations
        self._init_context_adaptations()
    
    def _init_context_adaptations(self):
        """Initialize context-based style adaptations."""
        self._context_adaptations = {
            "brainstorming": {
                "novelty": 0.3,  # Boost novelty
                "flexibility": 0.3,
                "risk_taking": 0.3,
            },
            "problem_solving": {
                "utility": 0.3,
                "persistence": 0.2,
                "complexity": 0.2,
            },
            "writing": {
                "expression": 0.3,
                "abstraction": 0.2,
            },
            "analysis": {
                "complexity": 0.2,
                "utility": 0.2,
                "novelty": -0.1,
            },
            "playful": {
                "novelty": 0.2,
                "expression": 0.2,
                "risk_taking": 0.2,
            },
        }
    
    def get_profile(self, style_name: Optional[str] = None) -> StyleProfile:
        """
        Get a style profile.
        
        Args:
            style_name: Style name (uses current if None)
            
        Returns:
            StyleProfile
        """
        name = style_name or self._current_style
        return self._styles.get(name, self._styles["balanced"])
    
    def set_style(self, style_name: str) -> bool:
        """
        Set current style.
        
        Args:
            style_name: Style name
            
        Returns:
            True if successful
        """
        if style_name in self._styles:
            self._current_style = style_name
            return True
        return False
    
    def adapt_for_context(
        self,
        context: str,
        temporary: bool = True,
    ) -> StyleProfile:
        """
        Adapt current style for a specific context.
        
        Args:
            context: Context name
            temporary: If True, returns modified profile without saving
            
        Returns:
            Modified StyleProfile
        """
        base = self.get_profile()
        adaptations = self._context_adaptations.get(context, {})
        
        if not adaptations:
            return base
        
        # Create modified profile
        adapted = StyleProfile(
            name=base.name + f" ({context})",
            description=f"{base.description} - adapted for {context}",
            novelty=max(0, min(1, base.novelty + adaptations.get("novelty", 0))),
            utility=max(0, min(1, base.utility + adaptations.get("utility", 0))),
            expression=max(0, min(1, base.expression + adaptations.get("expression", 0))),
            complexity=max(0, min(1, base.complexity + adaptations.get("complexity", 0))),
            abstraction=max(0, min(1, base.abstraction + adaptations.get("abstraction", 0))),
            risk_taking=max(0, min(1, base.risk_taking + adaptations.get("risk_taking", 0))),
            flexibility=max(0, min(1, base.flexibility + adaptations.get("flexibility", 0))),
            persistence=max(0, min(1, base.persistence + adaptations.get("persistence", 0))),
        )
        
        return adapted
    
    def create_custom_style(
        self,
        name: str,
        description: str,
        **dimensions
    ) -> StyleProfile:
        """
        Create a custom style profile.
        
        Args:
            name: Style name
            description: Style description
            **dimensions: Dimension values
            
        Returns:
            Created StyleProfile
        """
        profile = StyleProfile(
            name=name,
            description=description,
            novelty=dimensions.get("novelty", 0.5),
            utility=dimensions.get("utility", 0.5),
            expression=dimensions.get("expression", 0.5),
            complexity=dimensions.get("complexity", 0.5),
            abstraction=dimensions.get("abstraction", 0.5),
            risk_taking=dimensions.get("risk_taking", 0.5),
            flexibility=dimensions.get("flexibility", 0.5),
            persistence=dimensions.get("persistence", 0.5),
        )
        
        self._styles[name] = profile
        return profile
    
    def blend_styles(
        self,
        style1: str,
        style2: str,
        weight1: float = 0.5,
    ) -> StyleProfile:
        """
        Blend two styles together.
        
        Args:
            style1: First style name
            style2: Second style name
            weight1: Weight for first style (1-weight1 for second)
            
        Returns:
            Blended StyleProfile
        """
        s1 = self.get_profile(style1)
        s2 = self.get_profile(style2)
        w2 = 1 - weight1
        
        return StyleProfile(
            name=f"Blend: {s1.name} + {s2.name}",
            description=f"Blended style from {s1.name} and {s2.name}",
            novelty=s1.novelty * weight1 + s2.novelty * w2,
            utility=s1.utility * weight1 + s2.utility * w2,
            expression=s1.expression * weight1 + s2.expression * w2,
            complexity=s1.complexity * weight1 + s2.complexity * w2,
            abstraction=s1.abstraction * weight1 + s2.abstraction * w2,
            risk_taking=s1.risk_taking * weight1 + s2.risk_taking * w2,
            flexibility=s1.flexibility * weight1 + s2.flexibility * w2,
            persistence=s1.persistence * weight1 + s2.persistence * w2,
        )
    
    def list_styles(self) -> List[str]:
        """List all available style names."""
        return list(self._styles.keys())


def get_creative_style() -> CreativeStyle:
    """Get or create global creative style instance."""
    global creative_style
    if creative_style is None:
        creative_style = CreativeStyle()
    return creative_style
