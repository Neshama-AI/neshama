"""
Neshama Test Suite

Tests for core modules.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.core.ocean import OceanParams, OceanManager
from neshama.core.personality import Personality, PersonalityConfig, Desire


class TestOceanParams:
    """Tests for OceanParams."""
    
    def test_default_initialization(self):
        """Test default OCEAN parameters."""
        params = OceanParams()
        assert params.openness == 0.5
        assert params.conscientiousness == 0.5
        assert params.extraversion == 0.5
        assert params.agreeableness == 0.5
        assert params.neuroticism == 0.5
    
    def test_custom_values(self):
        """Test custom OCEAN values."""
        params = OceanParams(
            openness=0.8,
            conscientiousness=0.7,
            extraversion=0.6,
            agreeableness=0.5,
            neuroticism=0.4
        )
        assert params.openness == 0.8
        assert params.neuroticism == 0.4
    
    def test_validation(self):
        """Test value validation."""
        with pytest.raises(ValueError):
            OceanParams(openness=1.5)  # Out of range
        
        with pytest.raises(ValueError):
            OceanParams(neuroticism=-0.1)  # Out of range
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        params = OceanParams(openness=0.8)
        d = params.to_dict()
        assert isinstance(d, dict)
        assert d['openness'] == 0.8
    
    def test_from_dict(self):
        """Test dictionary loading."""
        data = {
            'openness': 0.9,
            'conscientiousness': 0.7,
            'extraversion': 0.6,
            'agreeableness': 0.5,
            'neuroticism': 0.4
        }
        params = OceanParams.from_dict(data)
        assert params.openness == 0.9
        assert params.neuroticism == 0.4
    
    def test_get_trait_description(self):
        """Test trait descriptions."""
        params = OceanParams(openness=0.8)
        desc = params.get_trait_description('openness')
        assert '高开放性' in desc or 'creative' in desc.lower()
    
    def test_get_summary(self):
        """Test summary generation."""
        params = OceanParams()
        summary = params.get_summary()
        assert 'Openness' in summary or 'openness' in summary


class TestOceanManager:
    """Tests for OceanManager."""
    
    def test_default_initialization(self):
        """Test default manager."""
        manager = OceanManager()
        assert manager.params is not None
    
    def test_preset_loading(self):
        """Test preset loading."""
        manager = OceanManager()
        success = manager.apply_preset('neshama')
        assert success is True
        assert manager.params.openness == 0.75
    
    def test_invalid_preset(self):
        """Test invalid preset."""
        manager = OceanManager()
        success = manager.apply_preset('invalid_preset')
        assert success is False
    
    def test_adjust_trait(self):
        """Test trait adjustment."""
        manager = OceanManager()
        initial = manager.params.openness
        manager.adjust_trait('openness', 0.1)
        assert manager.params.openness == initial + 0.1
    
    def test_adjust_trait_bounds(self):
        """Test trait adjustment respects bounds."""
        manager = OceanManager()
        manager.adjust_trait('openness', 10.0)  # Large delta
        assert manager.params.openness <= 1.0
    
    def test_behavioral_tendencies(self):
        """Test behavioral tendency calculation."""
        manager = OceanManager()
        tendencies = manager.calculate_behavioral_tendency('test')
        assert 'creativity' in tendencies
        assert 'planning' in tendencies
        assert tendencies['creativity'] == manager.params.openness


class TestPersonalityConfig:
    """Tests for PersonalityConfig."""
    
    def test_default_initialization(self):
        """Test default config."""
        ocean = OceanParams()
        config = PersonalityConfig(name="TestBot", ocean=ocean)
        assert config.name == "TestBot"
        assert config.emotion_expression is True
    
    def test_validation(self):
        """Test validation."""
        ocean = OceanParams()
        with pytest.raises(ValueError):
            PersonalityConfig(name="", ocean=ocean)  # Empty name
        
        with pytest.raises(ValueError):
            PersonalityConfig(name="Test", ocean=ocean, directness=1.5)  # Out of range
    
    def test_add_desire(self):
        """Test adding desires."""
        ocean = OceanParams()
        config = PersonalityConfig(name="Test", ocean=ocean)
        config.add_desire("求知欲", "想知道本质", 1)
        assert len(config.desires) == 1
        assert config.desires[0].name == "求知欲"


class TestPersonality:
    """Tests for Personality class."""
    
    def test_from_preset(self):
        """Test creating from preset."""
        personality = Personality.from_preset("TestBot", "neshama")
        assert personality.config.name == "TestBot"
        assert personality.config.ocean.openness == 0.75
    
    def test_add_desire_chain(self):
        """Test desire chaining."""
        personality = Personality("TestBot")
        result = personality.add_desire("Test", "Test desc", 1)
        assert result is personality  # Returns self for chaining
    
    def test_set_response_style(self):
        """Test response style setting."""
        personality = Personality("TestBot")
        personality.set_response_style(directness=0.8, humor=0.6)
        assert personality.config.directness == 0.8
        assert personality.config.humor_level == 0.6
    
    def test_generate_skill_md(self):
        """Test SKILL.md generation."""
        personality = Personality("TestBot")
        skill_md = personality.generate_skill_md()
        assert "TestBot" in skill_md
        assert "OCEAN" in skill_md or "人格参数" in skill_md


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
