# Soul Layer - NPC Behavior Bridge
"""
NPCBehaviorBridge - Maps emotions to game behaviors.

Converts emotion states into actionable behavior modifiers
that Unity C# can directly consume.

Features:
- Emotion intensity threshold triggers
- Multiple behavior types
- Faction and relationship modifiers
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum


class BehaviorType(Enum):
    """Types of behavior modifications."""
    DIALOGUE_STYLE_CHANGE = "dialogue_style_change"
    QUEST_AVAILABILITY_CHANGE = "quest_availability_change"
    FACTION_SHIFT = "faction_shift"
    SHOP_PRICE_CHANGE = "shop_price_change"
    MOVEMENT_PATTERN_CHANGE = "movement_pattern_change"
    INTERACTION_ALLOWED = "interaction_allowed"
    INFO_SHARING = "info_sharing"
    GIFT_REACTION = "gift_reaction"


class DialogueStyle(Enum):
    """Dialogue style options."""
    FRIENDLY = "friendly"
    HOSTILE = "hostile"
    NEUTRAL = "neutral"
    CAUTIOUS = "cautious"
    AGGRESSIVE = "aggressive"
    SUBMISSIVE = "submissive"
    EXCITED = "excited"
    GLOOMY = "gloomy"


class QuestModifier(Enum):
    """Quest availability modifiers."""
    AVAILABLE = "available"
    AVAILABLE_WITH_CONDITION = "available_with_condition"
    LOCKED = "locked"
    COMPLETED = "completed"
    FAILED = "failed"


class MovementPattern(Enum):
    """Movement pattern options."""
    NORMAL = "normal"
    AGGRESSIVE_PATROL = "aggressive_patrol"
    DEFENSIVE = "defensive"
    FLEEING = "fleeing"
    EXCITED = "excited"
    HIDING = "hiding"


@dataclass
class BehaviorModifier:
    """
    A single behavior modification from emotion state.
    
    Unity C# friendly - flat structure, no deep nesting.
    
    Attributes:
        behavior_type: Type of behavior modification
        modifier_value: Numeric modifier (for prices, faction points, etc.)
        enabled: Whether this behavior is enabled
        conditions: Optional conditions for this behavior
        priority: Priority order (higher = more important)
    """
    behavior_type: BehaviorType
    modifier_value: float = 0.0
    enabled: bool = True
    conditions: Optional[Dict[str, Any]] = None
    priority: int = 0
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Unity-friendly dict."""
        return {
            "behavior_type": self.behavior_type.value,
            "modifier_value": round(self.modifier_value, 2),
            "enabled": self.enabled,
            "conditions": self.conditions,
            "priority": self.priority,
            "description": self.description,
        }


@dataclass
class BehaviorProfile:
    """
    Complete behavior profile for an NPC based on emotion state.
    
    Contains all behavior modifiers that should be active.
    """
    modifiers: List[BehaviorModifier] = field(default_factory=list)
    dialogue_style: DialogueStyle = DialogueStyle.NEUTRAL
    movement_pattern: MovementPattern = MovementPattern.NORMAL
    quest_modifier: QuestModifier = QuestModifier.AVAILABLE
    shop_price_multiplier: float = 1.0
    faction_point_modifier: float = 0.0
    will_talk: bool = True
    will_share_secrets: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Unity-friendly flat dict."""
        return {
            "dialogue_style": self.dialogue_style.value,
            "movement_pattern": self.movement_pattern.value,
            "quest_modifier": self.quest_modifier.value,
            "shop_price_multiplier": round(self.shop_price_multiplier, 2),
            "faction_point_modifier": round(self.faction_point_modifier, 2),
            "will_talk": self.will_talk,
            "will_share_secrets": self.will_share_secrets,
            "modifier_count": len(self.modifiers),
            "modifiers": [m.to_dict() for m in self.modifiers],
        }


# Emotion threshold configurations
# Format: (emotion, threshold, BehaviorType, modifier_value)
EMOTION_THRESHOLD_CONFIGS: List[tuple] = [
    # High anger thresholds
    ("anger", 0.7, BehaviorType.INTERACTION_ALLOWED, -0.3),
    ("anger", 0.8, BehaviorType.INFO_SHARING, -1.0),
    
    # High fear thresholds
    ("fear", 0.6, BehaviorType.MOVEMENT_PATTERN_CHANGE, 0.0),  # fleeing
    ("fear", 0.7, BehaviorType.INTERACTION_ALLOWED, -0.4),
    ("fear", 0.8, BehaviorType.DIALOGUE_STYLE_CHANGE, -0.5),  # submissive
    
    # High joy thresholds
    ("joy", 0.6, BehaviorType.QUEST_AVAILABILITY_CHANGE, 0.3),
    ("joy", 0.7, BehaviorType.SHOP_PRICE_CHANGE, -0.1),  # 10% discount
    ("joy", 0.8, BehaviorType.INFO_SHARING, 0.5),
    
    # High trust thresholds
    ("trust", 0.6, BehaviorType.INFO_SHARING, 0.4),
    ("trust", 0.8, BehaviorType.QUEST_AVAILABILITY_CHANGE, 0.5),
    ("trust", 0.8, BehaviorType.GIFT_REACTION, 0.5),
    
    # High sadness thresholds
    ("sadness", 0.5, BehaviorType.DIALOGUE_STYLE_CHANGE, -0.3),
    ("sadness", 0.7, BehaviorType.QUEST_AVAILABILITY_CHANGE, -0.2),
    ("sadness", 0.8, BehaviorType.MOVEMENT_PATTERN_CHANGE, 0.0),  # hiding
    
    # High disgust thresholds
    ("disgust", 0.5, BehaviorType.INTERACTION_ALLOWED, -0.3),
    ("disgust", 0.7, BehaviorType.SHOP_PRICE_CHANGE, 0.2),  # 20% markup
    ("disgust", 0.8, BehaviorType.INFO_SHARING, -0.8),
]


class NPCBehaviorBridge:
    """
    Bridge from emotion state to game behavior.
    
    Converts emotion intensities into actionable behavior modifiers.
    Pure rule-based, no LLM calls.
    
    Example:
        >>> bridge = NPCBehaviorBridge()
        >>> emotions = {"anger": 0.8, "fear": 0.3, "joy": 0.1}
        >>> profile = bridge.generate_behavior(emotions)
        >>> print(profile.will_talk)  # False or reduced
    """
    
    def __init__(
        self,
        thresholds: Optional[List[tuple]] = None,
        personality: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize the behavior bridge.
        
        Args:
            thresholds: Custom emotion threshold configs
            personality: OCEAN personality for modifier adjustments
        """
        self._thresholds = thresholds or EMOTION_THRESHOLD_CONFIGS
        self._personality = personality or {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5,
        }
    
    def generate_behavior(
        self,
        emotion_state: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> BehaviorProfile:
        """
        Generate behavior profile from emotion state.
        
        Args:
            emotion_state: Dict of emotion -> intensity (0-1)
            context: Optional context (player reputation, etc.)
            
        Returns:
            BehaviorProfile with all active modifiers
        """
        profile = BehaviorProfile()
        context = context or {}
        
        # Apply personality modifiers
        base_thresholds = self._apply_personality_modifiers()
        
        # Check each threshold
        for emotion, threshold, behavior_type, base_modifier in base_thresholds:
            intensity = emotion_state.get(emotion, 0.0)
            
            if intensity >= threshold:
                modifier = self._create_modifier(
                    behavior_type=behavior_type,
                    emotion=emotion,
                    intensity=intensity,
                    threshold=threshold,
                    base_modifier=base_modifier,
                    context=context,
                )
                profile.modifiers.append(modifier)
        
        # Derive aggregate behaviors
        self._derive_dialogue_style(profile, emotion_state)
        self._derive_movement_pattern(profile, emotion_state)
        self._derive_quest_modifier(profile, emotion_state)
        self._derive_shop_price(profile, emotion_state)
        self._derive_faction_shift(profile, emotion_state)
        self._derive_interaction_flags(profile, emotion_state)
        
        return profile
    
    def _apply_personality_modifiers(self) -> List[tuple]:
        """Apply OCEAN personality to threshold configs."""
        modified = []
        
        for emotion, threshold, behavior_type, base_modifier in self._thresholds:
            threshold_mod = threshold
            
            # High agreeableness = more tolerant, lower thresholds for positive behaviors
            if behavior_type in [BehaviorType.INFO_SHARING, BehaviorType.QUEST_AVAILABILITY_CHANGE]:
                agreeableness = self._personality.get("agreeableness", 0.5)
                if agreeableness > 0.6:
                    threshold_mod = threshold * (1.0 - (agreeableness - 0.6) * 0.3)
            
            # High neuroticism = lower thresholds for fear/anger responses
            if behavior_type in [BehaviorType.MOVEMENT_PATTERN_CHANGE, BehaviorType.INTERACTION_ALLOWED]:
                neuroticism = self._personality.get("neuroticism", 0.5)
                if neuroticism > 0.6:
                    threshold_mod = threshold * (1.0 - (neuroticism - 0.6) * 0.2)
            
            modified.append((emotion, threshold_mod, behavior_type, base_modifier))
        
        return modified
    
    def _create_modifier(
        self,
        behavior_type: BehaviorType,
        emotion: str,
        intensity: float,
        threshold: float,
        base_modifier: float,
        context: Dict[str, Any],
    ) -> BehaviorModifier:
        """Create a behavior modifier from threshold breach."""
        # Scale modifier by how much over threshold
        overflow = intensity - threshold
        scaled_modifier = base_modifier * (1 + overflow)
        
        descriptions = {
            BehaviorType.INTERACTION_ALLOWED: f"Emotion {emotion} ({intensity:.2f}) affects willingness to interact",
            BehaviorType.INFO_SHARING: f"Emotion {emotion} ({intensity:.2f}) affects information sharing",
            BehaviorType.QUEST_AVAILABILITY_CHANGE: f"Emotion {emotion} ({intensity:.2f}) affects quest availability",
            BehaviorType.SHOP_PRICE_CHANGE: f"Emotion {emotion} ({intensity:.2f}) affects shop pricing",
            BehaviorType.MOVEMENT_PATTERN_CHANGE: f"Emotion {emotion} ({intensity:.2f}) affects movement",
            BehaviorType.FACTION_SHIFT: f"Emotion {emotion} ({intensity:.2f}) affects faction standing",
            BehaviorType.GIFT_REACTION: f"Emotion {emotion} ({intensity:.2f}) affects gift reception",
            BehaviorType.DIALOGUE_STYLE_CHANGE: f"Emotion {emotion} ({intensity:.2f}) affects dialogue",
        }
        
        return BehaviorModifier(
            behavior_type=behavior_type,
            modifier_value=round(scaled_modifier, 4),
            enabled=True,
            priority=int(intensity * 10),
            description=descriptions.get(behavior_type, ""),
        )
    
    def _derive_dialogue_style(
        self,
        profile: BehaviorProfile,
        emotion_state: Dict[str, float],
    ):
        """Derive dialogue style from emotions."""
        anger = emotion_state.get("anger", 0.0)
        fear = emotion_state.get("fear", 0.0)
        joy = emotion_state.get("joy", 0.0)
        sadness = emotion_state.get("sadness", 0.0)
        
        if anger > 0.5:
            profile.dialogue_style = DialogueStyle.AGGRESSIVE
        elif fear > 0.5:
            profile.dialogue_style = DialogueStyle.SUBMISSIVE
        elif joy > 0.5:
            profile.dialogue_style = DialogueStyle.EXCITED
        elif sadness > 0.4:
            profile.dialogue_style = DialogueStyle.GLOOMY
        elif anger > 0.3 or fear > 0.3:
            profile.dialogue_style = DialogueStyle.CAUTIOUS
        else:
            profile.dialogue_style = DialogueStyle.NEUTRAL
    
    def _derive_movement_pattern(
        self,
        profile: BehaviorProfile,
        emotion_state: Dict[str, float],
    ):
        """Derive movement pattern from emotions."""
        fear = emotion_state.get("fear", 0.0)
        anger = emotion_state.get("anger", 0.0)
        joy = emotion_state.get("joy", 0.0)
        sadness = emotion_state.get("sadness", 0.0)
        
        if fear > 0.6:
            profile.movement_pattern = MovementPattern.FLEEING
        elif sadness > 0.6:
            profile.movement_pattern = MovementPattern.HIDING
        elif anger > 0.6:
            profile.movement_pattern = MovementPattern.AGGRESSIVE_PATROL
        elif fear > 0.4 or anger > 0.4:
            profile.movement_pattern = MovementPattern.DEFENSIVE
        elif joy > 0.5:
            profile.movement_pattern = MovementPattern.EXCITED
        else:
            profile.movement_pattern = MovementPattern.NORMAL
    
    def _derive_quest_modifier(
        self,
        profile: BehaviorProfile,
        emotion_state: Dict[str, float],
    ):
        """Derive quest availability from emotions."""
        anger = emotion_state.get("anger", 0.0)
        trust = emotion_state.get("trust", 0.0)
        sadness = emotion_state.get("sadness", 0.0)
        
        if anger > 0.7:
            profile.quest_modifier = QuestModifier.LOCKED
        elif trust > 0.7:
            profile.quest_modifier = QuestModifier.AVAILABLE
        elif sadness > 0.5:
            profile.quest_modifier = QuestModifier.AVAILABLE_WITH_CONDITION
        else:
            profile.quest_modifier = QuestModifier.AVAILABLE
    
    def _derive_shop_price(
        self,
        profile: BehaviorProfile,
        emotion_state: Dict[str, float],
    ):
        """Derive shop price modifier from emotions."""
        joy = emotion_state.get("joy", 0.0)
        trust = emotion_state.get("trust", 0.0)
        anger = emotion_state.get("anger", 0.0)
        disgust = emotion_state.get("disgust", 0.0)
        
        # Base multiplier
        multiplier = 1.0
        
        # Positive emotions = discount
        if joy > 0.5:
            multiplier -= 0.1 * joy
        if trust > 0.5:
            multiplier -= 0.1 * trust
        
        # Negative emotions = markup
        if anger > 0.4:
            multiplier += 0.15 * anger
        if disgust > 0.4:
            multiplier += 0.2 * disgust
        
        profile.shop_price_multiplier = max(0.5, min(2.0, multiplier))
    
    def _derive_faction_shift(
        self,
        profile: BehaviorProfile,
        emotion_state: Dict[str, float],
    ):
        """Derive faction point change from emotions."""
        anger = emotion_state.get("anger", 0.0)
        disgust = emotion_state.get("disgust", 0.0)
        trust = emotion_state.get("trust", 0.0)
        joy = emotion_state.get("joy", 0.0)
        
        # Positive emotions = gain faction points
        shift = 0.0
        if trust > 0.4:
            shift += 0.1 * trust
        if joy > 0.4:
            shift += 0.1 * joy
        
        # Negative emotions = lose faction points
        if anger > 0.4:
            shift -= 0.15 * anger
        if disgust > 0.4:
            shift -= 0.1 * disgust
        
        profile.faction_point_modifier = max(-1.0, min(1.0, shift))
    
    def _derive_interaction_flags(
        self,
        profile: BehaviorProfile,
        emotion_state: Dict[str, float],
    ):
        """Derive interaction flags from emotions."""
        anger = emotion_state.get("anger", 0.0)
        fear = emotion_state.get("fear", 0.0)
        disgust = emotion_state.get("disgust", 0.0)
        trust = emotion_state.get("trust", 0.0)
        
        # Will talk
        if anger > 0.8 or fear > 0.8 or disgust > 0.8:
            profile.will_talk = False
        elif anger > 0.5 or fear > 0.6 or disgust > 0.5:
            profile.will_talk = False  # May talk but reluctantly
        else:
            profile.will_talk = True
        
        # Will share secrets
        if trust > 0.7:
            profile.will_share_secrets = True
        elif anger > 0.3 or fear > 0.4:
            profile.will_share_secrets = False
        else:
            profile.will_share_secrets = False
    
    def get_triggered_behaviors(
        self,
        emotion_state: Dict[str, float],
        behavior_type: BehaviorType,
    ) -> List[BehaviorModifier]:
        """Get all triggered behaviors of a specific type."""
        profile = self.generate_behavior(emotion_state)
        return [m for m in profile.modifiers if m.behavior_type == behavior_type]


def create_behavior_bridge(
    personality: Optional[Dict[str, float]] = None,
) -> NPCBehaviorBridge:
    """Factory function to create an NPCBehaviorBridge."""
    return NPCBehaviorBridge(personality=personality)
