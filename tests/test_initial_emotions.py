# Tests for NPC Initial Emotions
"""
Tests for NPC creation with initial emotions from:
1. Preset YAML files
2. Explicit initial_emotions parameter
3. OCEAN personality-derived defaults
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml

from neshama.soul.npc_manager import NPCManager


@pytest.fixture
def temp_npc_dir(tmp_path):
    """Create a temporary NPC data directory with preset files."""
    preset_dir = tmp_path / "presets"
    preset_dir.mkdir()
    
    # Create tavern_keeper preset
    tavern_data = {
        "description": "A friendly tavern keeper",
        "personality": {
            "openness": 0.4,
            "conscientiousness": 0.5,
            "extraversion": 0.8,
            "agreeableness": 0.75,
            "neuroticism": 0.4,
        },
        "initial_emotions": {
            "joy": 0.3,
            "trust": 0.2,
            "anticipation": 0.2,
        },
        "dialogue_style": "friendly",
    }
    (preset_dir / "tavern_keeper.yaml").write_text(
        yaml.dump(tavern_data, default_flow_style=False)
    )
    
    # Create guard_captain preset
    guard_data = {
        "description": "A disciplined guard captain",
        "personality": {
            "openness": 0.3,
            "conscientiousness": 0.9,
            "extraversion": 0.3,
            "agreeableness": 0.4,
            "neuroticism": 0.2,
        },
        "initial_emotions": {
            "trust": 0.15,
            "anticipation": 0.1,
        },
        "dialogue_style": "neutral",
    }
    (preset_dir / "guard_captain.yaml").write_text(
        yaml.dump(guard_data, default_flow_style=False)
    )
    
    # Create a preset WITHOUT initial_emotions
    no_emotions_data = {
        "description": "A simple NPC with no initial emotions",
        "personality": {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.8,  # High extraversion
            "agreeableness": 0.5,
            "neuroticism": 0.5,
        },
    }
    (preset_dir / "no_emotions_preset.yaml").write_text(
        yaml.dump(no_emotions_data, default_flow_style=False)
    )
    
    return tmp_path


@pytest.fixture
def manager(temp_npc_dir):
    """Create NPCManager with temp directory."""
    return NPCManager(npc_dir=temp_npc_dir)


class TestNPCInitialEmotionsFromPreset:
    """Tests for initial emotions loaded from preset YAML."""
    
    def test_tavern_keeper_initial_emotions(self, manager):
        """Tavern keeper preset should have joy=0.3, trust=0.2, anticipation=0.2."""
        soul = manager.create_npc("Tavern Keeper", preset="tavern_keeper", npc_id="test_tk")
        assert soul.current_emotions.get("joy") == 0.3
        assert soul.current_emotions.get("trust") == 0.2
        assert soul.current_emotions.get("anticipation") == 0.2
    
    def test_guard_captain_initial_emotions(self, manager):
        """Guard captain preset should have trust=0.15, anticipation=0.1."""
        soul = manager.create_npc("Guard Captain", preset="guard_captain", npc_id="test_gc")
        assert soul.current_emotions.get("trust") == 0.15
        assert soul.current_emotions.get("anticipation") == 0.1


class TestNPCInitialEmotionsExplicit:
    """Tests for explicitly provided initial_emotions parameter."""
    
    def test_explicit_emotions_override_preset(self, manager):
        """Explicit initial_emotions should override preset values."""
        soul = manager.create_npc(
            "Tavern Keeper",
            preset="tavern_keeper",
            npc_id="test_override",
            initial_emotions={"joy": 0.9, "surprise": 0.5},
        )
        # Explicit overrides preset joy
        assert soul.current_emotions.get("joy") == 0.9
        # Explicit adds new emotion
        assert soul.current_emotions.get("surprise") == 0.5
        # Preset value not in explicit should still be present
        assert "trust" in soul.current_emotions or "anticipation" in soul.current_emotions
    
    def test_explicit_emotions_without_preset(self, manager):
        """Explicit initial_emotions without preset should work."""
        soul = manager.create_npc(
            "Custom NPC",
            npc_id="test_explicit",
            initial_emotions={"joy": 0.5, "fear": 0.3},
        )
        assert soul.current_emotions.get("joy") == 0.5
        assert soul.current_emotions.get("fear") == 0.3


class TestNPCInitialEmotionsDerived:
    """Tests for OCEAN-derived initial emotions when no preset emotions given."""
    
    def test_high_extraversion_derives_joy(self, manager):
        """High extraversion should derive joy baseline."""
        soul = manager.create_npc(
            "Loud Person",
            npc_id="test_ext",
            personality={
                "openness": 0.5,
                "conscientiousness": 0.5,
                "extraversion": 0.9,
                "agreeableness": 0.5,
                "neuroticism": 0.5,
            },
        )
        assert soul.current_emotions.get("joy", 0) > 0
    
    def test_high_neuroticism_derives_fear_sadness(self, manager):
        """High neuroticism should derive fear and sadness baselines."""
        soul = manager.create_npc(
            "Anxious Person",
            npc_id="test_neu",
            personality={
                "openness": 0.5,
                "conscientiousness": 0.5,
                "extraversion": 0.5,
                "agreeableness": 0.5,
                "neuroticism": 0.9,
            },
        )
        assert soul.current_emotions.get("fear", 0) > 0
        assert soul.current_emotions.get("sadness", 0) > 0
    
    def test_high_agreeableness_derives_trust(self, manager):
        """High agreeableness should derive trust baseline."""
        soul = manager.create_npc(
            "Trusting Person",
            npc_id="test_agr",
            personality={
                "openness": 0.5,
                "conscientiousness": 0.5,
                "extraversion": 0.5,
                "agreeableness": 0.9,
                "neuroticism": 0.5,
            },
        )
        assert soul.current_emotions.get("trust", 0) > 0
    
    def test_average_personality_no_derived_emotions(self, manager):
        """Average personality (all 0.5) should derive no initial emotions."""
        soul = manager.create_npc(
            "Average Person",
            npc_id="test_avg",
            personality={
                "openness": 0.5,
                "conscientiousness": 0.5,
                "extraversion": 0.5,
                "agreeableness": 0.5,
                "neuroticism": 0.5,
            },
        )
        # All traits are at 0.5, no derivation threshold met
        assert len(soul.current_emotions) == 0
    
    def test_preset_without_initial_emotions_uses_derived(self, manager):
        """Preset without initial_emotions should fall back to OCEAN-derived."""
        soul = manager.create_npc(
            "NoEmotion NPC",
            preset="no_emotions_preset",
            npc_id="test_noem",
        )
        # Preset has high extraversion (0.8), should derive joy
        assert soul.current_emotions.get("joy", 0) > 0


class TestNPCInitialEmotionsDerivedStatic:
    """Direct tests of _derive_initial_emotions static method."""
    
    def test_derive_high_extraversion(self):
        """High extraversion should produce joy."""
        emotions = NPCManager._derive_initial_emotions({
            "extraversion": 0.9,
            "neuroticism": 0.5,
            "agreeableness": 0.5,
            "openness": 0.5,
        })
        assert "joy" in emotions
        assert emotions["joy"] > 0
    
    def test_derive_high_neuroticism(self):
        """High neuroticism should produce fear and sadness."""
        emotions = NPCManager._derive_initial_emotions({
            "extraversion": 0.5,
            "neuroticism": 0.9,
            "agreeableness": 0.5,
            "openness": 0.5,
        })
        assert "fear" in emotions
        assert "sadness" in emotions
    
    def test_derive_high_agreeableness(self):
        """High agreeableness should produce trust."""
        emotions = NPCManager._derive_initial_emotions({
            "extraversion": 0.5,
            "neuroticism": 0.5,
            "agreeableness": 0.9,
            "openness": 0.5,
        })
        assert "trust" in emotions
    
    def test_derive_high_openness(self):
        """High openness should produce anticipation."""
        emotions = NPCManager._derive_initial_emotions({
            "extraversion": 0.5,
            "neuroticism": 0.5,
            "agreeableness": 0.5,
            "openness": 0.85,
        })
        assert "anticipation" in emotions
    
    def test_derive_low_traits_no_emotions(self):
        """Traits below threshold should not produce emotions."""
        emotions = NPCManager._derive_initial_emotions({
            "extraversion": 0.4,
            "neuroticism": 0.3,
            "agreeableness": 0.4,
            "openness": 0.5,
        })
        assert len(emotions) == 0
    
    def test_derive_multiple_high_traits(self):
        """Multiple high traits should produce multiple emotions."""
        emotions = NPCManager._derive_initial_emotions({
            "extraversion": 0.9,
            "neuroticism": 0.8,
            "agreeableness": 0.8,
            "openness": 0.9,
        })
        assert "joy" in emotions
        assert "fear" in emotions
        assert "trust" in emotions
        assert "anticipation" in emotions


class TestNPCEmotionsPersisted:
    """Tests that initial emotions are persisted to disk."""
    
    def test_emotions_saved_to_yaml(self, manager, temp_npc_dir):
        """Created NPC should have initial emotions in the saved YAML."""
        soul = manager.create_npc(
            "Test",
            npc_id="test_persist",
            initial_emotions={"joy": 0.5},
        )
        
        # Read the saved file
        file_path = temp_npc_dir / "test_persist.yaml"
        assert file_path.exists()
        data = yaml.safe_load(file_path.read_text())
        assert data["current_emotions"].get("joy") == 0.5
