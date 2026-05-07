"""
Neshama NPC Behavior Bridge Tests
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.npc_behavior import (
    NPCBehaviorBridge,
    BehaviorProfile,
    BehaviorModifier,
    BehaviorType,
    DialogueStyle,
    MovementPattern,
    QuestModifier,
    create_behavior_bridge,
)


class TestBehaviorTypes:
    """Tests for behavior enums."""

    def test_behavior_types_exist(self):
        """All behavior types should be defined."""
        types = [e.value for e in BehaviorType]
        assert "dialogue_style_change" in types
        assert "quest_availability_change" in types
        assert "faction_shift" in types
        assert "shop_price_change" in types
        assert "movement_pattern_change" in types

    def test_dialogue_styles_exist(self):
        """All dialogue styles should be defined."""
        styles = [e.value for e in DialogueStyle]
        assert "friendly" in styles
        assert "hostile" in styles
        assert "neutral" in styles
        assert "cautious" in styles

    def test_movement_patterns_exist(self):
        """All movement patterns should be defined."""
        patterns = [e.value for e in MovementPattern]
        assert "normal" in patterns
        assert "fleeing" in patterns
        assert "aggressive_patrol" in patterns


class TestBehaviorModifier:
    """Tests for BehaviorModifier dataclass."""

    def test_create_modifier(self):
        """Test basic modifier creation."""
        modifier = BehaviorModifier(
            behavior_type=BehaviorType.INFO_SHARING,
            modifier_value=0.5,
        )
        assert modifier.behavior_type == BehaviorType.INFO_SHARING
        assert modifier.modifier_value == 0.5
        assert modifier.enabled is True

    def test_modifier_to_dict(self):
        """Test modifier serialization."""
        modifier = BehaviorModifier(
            behavior_type=BehaviorType.SHOP_PRICE_CHANGE,
            modifier_value=0.1,
            priority=5,
            description="Happy merchant",
        )
        d = modifier.to_dict()
        
        assert d["behavior_type"] == "shop_price_change"
        assert d["modifier_value"] == 0.1
        assert d["priority"] == 5


class TestBehaviorProfile:
    """Tests for BehaviorProfile dataclass."""

    def test_default_profile(self):
        """Test default profile values."""
        profile = BehaviorProfile()
        
        assert profile.dialogue_style == DialogueStyle.NEUTRAL
        assert profile.movement_pattern == MovementPattern.NORMAL
        assert profile.quest_modifier == QuestModifier.AVAILABLE
        assert profile.shop_price_multiplier == 1.0
        assert profile.will_talk is True
        assert profile.will_share_secrets is False

    def test_profile_to_dict(self):
        """Test profile serialization."""
        profile = BehaviorProfile()
        profile.dialogue_style = DialogueStyle.FRIENDLY
        profile.will_share_secrets = True
        
        d = profile.to_dict()
        
        assert d["dialogue_style"] == "friendly"
        assert d["will_share_secrets"] is True
        assert "modifiers" in d


class TestNPCBehaviorBridgeInit:
    """Tests for NPCBehaviorBridge initialization."""

    def test_default_init(self):
        """Test default initialization."""
        bridge = NPCBehaviorBridge()
        assert bridge._personality is not None
        assert len(bridge._thresholds) > 0

    def test_custom_personality(self):
        """Test with custom personality."""
        personality = {
            "openness": 0.8,
            "extraversion": 0.9,
        }
        bridge = NPCBehaviorBridge(personality=personality)
        assert bridge._personality["extraversion"] == 0.9


class TestGenerateBehavior:
    """Tests for generate_behavior()."""

    def test_empty_emotions(self):
        """Test with no emotions."""
        bridge = NPCBehaviorBridge()
        profile = bridge.generate_behavior({})
        
        assert isinstance(profile, BehaviorProfile)
        assert profile.dialogue_style == DialogueStyle.NEUTRAL

    def test_high_anger(self):
        """Test behavior with high anger."""
        bridge = NPCBehaviorBridge()
        emotions = {"anger": 0.8, "fear": 0.2, "joy": 0.1}
        
        profile = bridge.generate_behavior(emotions)
        
        # Should be hostile
        assert profile.dialogue_style == DialogueStyle.AGGRESSIVE
        
        # Should not share info
        assert profile.will_share_secrets is False

    def test_high_fear(self):
        """Test behavior with high fear."""
        bridge = NPCBehaviorBridge()
        emotions = {"fear": 0.7, "anger": 0.1}
        
        profile = bridge.generate_behavior(emotions)
        
        # Should be fleeing or defensive
        assert profile.movement_pattern in [
            MovementPattern.FLEEING,
            MovementPattern.DEFENSIVE,
        ]
        
        # May not talk
        assert profile.will_talk is False

    def test_high_joy(self):
        """Test behavior with high joy."""
        bridge = NPCBehaviorBridge()
        emotions = {"joy": 0.7, "trust": 0.5}
        
        profile = bridge.generate_behavior(emotions)
        
        # Should be friendly/excited
        assert profile.dialogue_style == DialogueStyle.EXCITED
        
        # May share info based on trust
        assert profile.will_talk is True

    def test_high_trust(self):
        """Test behavior with high trust."""
        bridge = NPCBehaviorBridge()
        emotions = {"trust": 0.8, "joy": 0.3}
        
        profile = bridge.generate_behavior(emotions)
        
        # Should share secrets
        assert profile.will_share_secrets is True

    def test_high_sadness(self):
        """Test behavior with high sadness."""
        bridge = NPCBehaviorBridge()
        emotions = {"sadness": 0.7, "fear": 0.2}
        
        profile = bridge.generate_behavior(emotions)
        
        # Should be gloomy or cautious
        assert profile.dialogue_style in [
            DialogueStyle.GLOOMY,
            DialogueStyle.CAUTIOUS,
        ]

    def test_shop_price_with_joy(self):
        """Test shop discount with joy."""
        bridge = NPCBehaviorBridge()
        emotions = {"joy": 0.8}
        
        profile = bridge.generate_behavior(emotions)
        
        # Should get discount
        assert profile.shop_price_multiplier < 1.0

    def test_shop_price_with_anger(self):
        """Test shop markup with anger."""
        bridge = NPCBehaviorBridge()
        emotions = {"anger": 0.7}
        
        profile = bridge.generate_behavior(emotions)
        
        # Should have markup
        assert profile.shop_price_multiplier > 1.0

    def test_faction_shift_positive(self):
        """Test positive faction shift with positive emotions."""
        bridge = NPCBehaviorBridge()
        emotions = {"joy": 0.6, "trust": 0.6}
        
        profile = bridge.generate_behavior(emotions)
        
        # Should be positive
        assert profile.faction_point_modifier > 0

    def test_faction_shift_negative(self):
        """Test negative faction shift with negative emotions."""
        bridge = NPCBehaviorBridge()
        emotions = {"anger": 0.6, "disgust": 0.5}
        
        profile = bridge.generate_behavior(emotions)
        
        # Should be negative
        assert profile.faction_point_modifier < 0

    def test_quest_locked_with_high_anger(self):
        """Test quest locked when very angry."""
        bridge = NPCBehaviorBridge()
        emotions = {"anger": 0.8}
        
        profile = bridge.generate_behavior(emotions)
        
        assert profile.quest_modifier == QuestModifier.LOCKED


class TestPersonalityModifiers:
    """Tests for personality effect on behavior."""

    def test_high_agreeableness_more_tolerant(self):
        """Test high agreeableness makes NPC more tolerant."""
        bridge_agreeable = NPCBehaviorBridge(
            personality={"agreeableness": 0.9}
        )
        emotions = {"anger": 0.5}
        
        profile = bridge_agreeable.generate_behavior(emotions)
        
        # Should still be willing to talk
        assert profile.will_talk is True

    def test_high_neuroticism_more_reactive(self):
        """Test high neuroticism increases reactions."""
        bridge_low_neuro = NPCBehaviorBridge(
            personality={"neuroticism": 0.2}
        )
        bridge_high_neuro = NPCBehaviorBridge(
            personality={"neuroticism": 0.8}
        )
        
        emotions = {"fear": 0.4}
        
        profile_low = bridge_low_neuro.generate_behavior(emotions)
        profile_high = bridge_high_neuro.generate_behavior(emotions)
        
        # High neuroticism should have more modifiers
        assert len(profile_high.modifiers) >= len(profile_low.modifiers)


class TestGetTriggeredBehaviors:
    """Tests for get_triggered_behaviors()."""

    def test_get_specific_behavior_type(self):
        """Test getting behaviors of a specific type."""
        bridge = NPCBehaviorBridge()
        emotions = {"anger": 0.8}
        
        modifiers = bridge.get_triggered_behaviors(
            emotions,
            BehaviorType.INTERACTION_ALLOWED
        )
        
        assert len(modifiers) > 0
        assert all(m.behavior_type == BehaviorType.INTERACTION_ALLOWED for m in modifiers)


class TestFactoryFunction:
    """Tests for factory function."""

    def test_create_behavior_bridge(self):
        """Test factory function."""
        bridge = create_behavior_bridge()
        assert isinstance(bridge, NPCBehaviorBridge)

    def test_create_with_personality(self):
        """Test factory with personality."""
        personality = {"extraversion": 0.9}
        bridge = create_behavior_bridge(personality=personality)
        assert bridge._personality["extraversion"] == 0.9
