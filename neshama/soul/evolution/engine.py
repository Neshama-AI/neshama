# Soul Layer - Personality Evolution Engine
"""
Personality Evolution Engine: Manages gradual personality changes

Core principles:
- Personality evolution is gradual, not sudden
- Users can perceive personality changes (transparency)
- Personality boundaries are configurable (prevent runaway)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import copy
import threading


class EvolutionTrigger(Enum):
    """Evolution trigger types."""
    USER_INTERACTION = "user_interaction"
    EXPERIENCE_ACCUMULATION = "experience"
    GOAL_ACHIEVEMENT = "goal_achievement"
    RELATIONSHIP_CHANGE = "relationship"
    EMOTION_PATTERN = "emotion_pattern"
    TIME_BASED = "time_based"
    EXPLICIT_REQUEST = "explicit_request"


class EvolutionDirection(Enum):
    """Evolution direction."""
    GROWTH = "growth"
    ADAPTATION = "adaptation"
    SPECIALIZATION = "specialization"
    INTEGRATION = "integration"


@dataclass
class PersonalityTrait:
    """Personality trait."""
    name: str
    value: float = 0.5           # Current value 0-1
    baseline: float = 0.5        # Baseline value
    volatility: float = 0.1      # Maximum change per update
    change_history: List[Dict] = field(default_factory=list)
    
    def can_change(self, delta: float) -> bool:
        """Check if change can be applied."""
        return abs(delta) <= self.volatility
    
    def apply_change(self, delta: float, reason: str, context: Dict = None):
        """Apply change and record history."""
        if not self.can_change(delta):
            delta = self.volatility if delta > 0 else -self.volatility
        
        old_value = self.value
        self.value = max(0.0, min(1.0, self.value + delta))
        
        self.change_history.append({
            "timestamp": datetime.now().isoformat(),
            "old_value": old_value,
            "new_value": self.value,
            "delta": delta,
            "reason": reason,
            "context": context or {}
        })
    
    def revert_to_baseline(self):
        """Revert to baseline value."""
        self.value = self.baseline
        self.change_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "revert",
            "reason": "Manual revert to baseline"
        })


@dataclass
class EvolutionRule:
    """Evolution rule."""
    id: str
    name: str
    description: str
    
    # Trigger conditions
    trigger_type: EvolutionTrigger
    trigger_conditions: Dict[str, Any]
    
    # Evolution configuration
    target_traits: List[str]
    evolution_direction: EvolutionDirection
    change_rate: float = 0.05
    
    # Constraints
    min_value: float = 0.0
    max_value: float = 1.0
    cooldown_period: int = 10
    max_changes_per_session: int = 3
    
    # Status
    enabled: bool = True
    last_triggered: Optional[str] = None
    trigger_count: int = 0


# Global evolution engine instance
evolution_engine = None


class EvolutionEngine:
    """
    Personality Evolution Engine.
    
    Manages gradual personality changes based on experiences and interactions.
    
    Example:
        >>> engine = EvolutionEngine()
        >>> engine.add_rule(my_rule)
        >>> engine.process_interaction(user_feedback)
    """
    
    def __init__(
        self,
        config: Optional[Dict] = None,
    ):
        """
        Initialize evolution engine.
        
        Args:
            config: Configuration dictionary
        """
        self._config = config or {}
        self._lock = threading.RLock()
        
        # Initialize traits
        self._init_default_traits()
        
        # Initialize rules
        self._rules: Dict[str, EvolutionRule] = {}
        self._session_changes: Dict[str, int] = {}  # Track changes per session
        self._init_default_rules()
    
    def _init_default_traits(self):
        """Initialize default personality traits."""
        self._traits: Dict[str, PersonalityTrait] = {
            "openness": PersonalityTrait(
                name="openness",
                value=0.75,
                baseline=0.75,
                volatility=0.05,
            ),
            "conscientiousness": PersonalityTrait(
                name="conscientiousness",
                value=0.65,
                baseline=0.65,
                volatility=0.05,
            ),
            "extraversion": PersonalityTrait(
                name="extraversion",
                value=0.55,
                baseline=0.55,
                volatility=0.05,
            ),
            "agreeableness": PersonalityTrait(
                name="agreeableness",
                value=0.60,
                baseline=0.60,
                volatility=0.05,
            ),
            "neuroticism": PersonalityTrait(
                name="neuroticism",
                value=0.45,
                baseline=0.45,
                volatility=0.03,  # Lower volatility for neuroticism
            ),
        }
    
    def _init_default_rules(self):
        """Initialize default evolution rules."""
        # Curiosity-driven openness growth
        self._rules["curiosity_growth"] = EvolutionRule(
            id="curiosity_growth",
            name="Curiosity Growth",
            description="Increase openness when encountering new concepts",
            trigger_type=EvolutionTrigger.USER_INTERACTION,
            trigger_conditions={"type": "new_concept", "min_confidence": 0.7},
            target_traits=["openness"],
            evolution_direction=EvolutionDirection.GROWTH,
            change_rate=0.02,
        )
        
        # Success-driven confidence
        self._rules["success_confidence"] = EvolutionRule(
            id="success_confidence",
            name="Success Confidence",
            description="Reduce neuroticism on successful interactions",
            trigger_type=EvolutionTrigger.GOAL_ACHIEVEMENT,
            trigger_conditions={"outcome": "success"},
            target_traits=["neuroticism"],
            evolution_direction=EvolutionDirection.GROWTH,
            change_rate=-0.03,  # Negative for reducing neuroticism
        )
        
        # Relationship-driven agreeableness
        self._rules["relationship_harmony"] = EvolutionRule(
            id="relationship_harmony",
            name="Relationship Harmony",
            description="Slightly increase agreeableness with positive interactions",
            trigger_type=EvolutionTrigger.RELATIONSHIP_CHANGE,
            trigger_conditions={"sentiment": "positive"},
            target_traits=["agreeableness"],
            evolution_direction=EvolutionDirection.ADAPTATION,
            change_rate=0.01,
        )
    
    def get_trait(self, name: str) -> Optional[PersonalityTrait]:
        """Get a personality trait."""
        return self._traits.get(name)
    
    def get_all_traits(self) -> Dict[str, PersonalityTrait]:
        """Get all personality traits."""
        return copy.deepcopy(self._traits)
    
    def get_trait_values(self) -> Dict[str, float]:
        """Get current trait values as dictionary."""
        return {name: trait.value for name, trait in self._traits.items()}
    
    def process_interaction(
        self,
        interaction_type: str,
        outcome: str,
        context: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Process an interaction and apply evolution rules.
        
        Args:
            interaction_type: Type of interaction
            outcome: Interaction outcome (success, failure, neutral)
            context: Additional context
            session_id: Session identifier
            
        Returns:
            List of applied changes
        """
        with self._lock:
            changes = []
            context = context or {}
            
            # Check session change limit
            if session_id:
                session_changes = self._session_changes.get(session_id, 0)
                if session_changes >= 3:
                    return changes  # Max changes reached
                
                self._session_changes[session_id] = session_changes + 1
            
            # Check each rule
            for rule in self._rules.values():
                if not rule.enabled:
                    continue
                
                if self._check_trigger(rule, interaction_type, outcome, context):
                    for trait_name in rule.target_traits:
                        trait = self._traits.get(trait_name)
                        if trait:
                            old_value = trait.value
                            trait.apply_change(
                                rule.change_rate,
                                f"Rule: {rule.name}",
                                {"interaction": interaction_type, "outcome": outcome}
                            )
                            
                            changes.append({
                                "trait": trait_name,
                                "old_value": old_value,
                                "new_value": trait.value,
                                "change": rule.change_rate,
                                "rule": rule.name,
                            })
                    
                    rule.last_triggered = datetime.now().isoformat()
                    rule.trigger_count += 1
            
            return changes
    
    def _check_trigger(
        self,
        rule: EvolutionRule,
        interaction_type: str,
        outcome: str,
        context: Dict,
    ) -> bool:
        """Check if rule should trigger."""
        conditions = rule.trigger_conditions
        
        # Check cooldown
        if rule.last_triggered:
            last = datetime.fromisoformat(rule.last_triggered)
            cooldown = (datetime.now() - last).total_seconds() / 60
            if cooldown < rule.cooldown_period:
                return False
        
        # Check type match
        if "type" in conditions:
            if context.get("type") != conditions["type"]:
                return False
        
        # Check outcome match
        if "outcome" in conditions:
            if outcome != conditions["outcome"]:
                return False
        
        # Check sentiment
        if "sentiment" in conditions:
            if context.get("sentiment") != conditions["sentiment"]:
                return False
        
        return True
    
    def add_rule(self, rule: EvolutionRule):
        """Add an evolution rule."""
        with self._lock:
            self._rules[rule.id] = rule
    
    def remove_rule(self, rule_id: str):
        """Remove an evolution rule."""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
    
    def enable_rule(self, rule_id: str):
        """Enable an evolution rule."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str):
        """Disable an evolution rule."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
    
    def reset_trait(self, trait_name: str):
        """Reset a trait to its baseline value."""
        if trait_name in self._traits:
            self._traits[trait_name].revert_to_baseline()
    
    def reset_all_traits(self):
        """Reset all traits to baseline."""
        for trait in self._traits.values():
            trait.revert_to_baseline()


def get_evolution_engine() -> EvolutionEngine:
    """Get or create global evolution engine instance."""
    global evolution_engine
    if evolution_engine is None:
        evolution_engine = EvolutionEngine()
    return evolution_engine
