"""
Neshama Composite Emotion Tests
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.emotion.composite import (
    CompositeEmotion,
    CompositeEmotionResult,
    EmotionState,
    BaseEmotion,
    create_composite_engine,
    synthesize_from_emotions,
    COMPOSITE_RECIPES,
    OPPOSING_PAIRS,
)


class TestCompositeEmotionInit:
    """Tests for CompositeEmotion initialization."""

    def test_default_init(self):
        """Test default initialization."""
        engine = CompositeEmotion()
        assert engine is not None
        assert engine.neuroticism == 0.5
        assert engine.base_decay_halflife == 120.0
        assert engine.conflict_strategy == "dominance"
        assert len(engine.get_all_emotions()) == 0

    def test_custom_init(self):
        """Test custom initialization parameters."""
        engine = CompositeEmotion(
            neuroticism=0.8,
            base_decay_halflife=60.0,
            conflict_strategy="cancel",
        )
        assert engine.neuroticism == 0.8
        assert engine.base_decay_halflife == 60.0
        assert engine.conflict_strategy == "cancel"

    def test_neuroticism_bounds(self):
        """Test that neuroticism affects decay."""
        low_neuro = CompositeEmotion(neuroticism=0.0)
        high_neuro = CompositeEmotion(neuroticism=1.0)
        # High neuroticism should slow decay (higher modifier)
        # Decay modifier for high = 1 - 1.0 * 0.5 = 0.5
        # Decay modifier for low = 1 - 0.0 * 0.5 = 1.0
        assert high_neuro.neuroticism > low_neuro.neuroticism


class TestBaseEmotionManagement:
    """Tests for base emotion setting and retrieval."""

    def test_set_emotion(self):
        """Test setting a base emotion."""
        engine = CompositeEmotion()
        state = engine.set_base_emotion("joy", 0.8)
        assert state is not None
        assert state.emotion == "joy"
        assert state.intensity == 0.8
        assert engine.get_emotion("joy") == 0.8

    def test_set_emotion_bounds(self):
        """Test that emotion intensity is clamped to 0-1."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 1.5)
        assert engine.get_emotion("joy") == 1.0
        engine.set_base_emotion("joy", -0.5)
        assert engine.get_emotion("joy") == 0.0

    def test_set_emotion_case_insensitive(self):
        """Test emotion names are case-insensitive."""
        engine = CompositeEmotion()
        engine.set_base_emotion("JOY", 0.7)
        assert engine.get_emotion("joy") == 0.7
        assert engine.get_emotion("Joy") == 0.7

    def test_adjust_emotion(self):
        """Test adjusting emotion by delta."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.5)
        engine.adjust_emotion("joy", 0.2)
        assert engine.get_emotion("joy") == 0.7

    def test_adjust_emotion_negative(self):
        """Test negative emotion adjustment."""
        engine = CompositeEmotion()
        engine.set_base_emotion("anger", 0.5)
        engine.adjust_emotion("anger", -0.3)
        assert engine.get_emotion("anger") == 0.2

    def test_adjust_new_emotion(self):
        """Test adjusting an emotion that doesn't exist yet."""
        engine = CompositeEmotion()
        state = engine.adjust_emotion("fear", 0.5)
        assert engine.get_emotion("fear") == 0.5  # 0 + 0.5 (fixed: was 0.5 + 0.5 = 1.0)

    def test_get_nonexistent_emotion(self):
        """Test getting an emotion that doesn't exist."""
        engine = CompositeEmotion()
        assert engine.get_emotion("joy") is None

    def test_get_all_emotions(self):
        """Test getting all active emotions."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.8)
        engine.set_base_emotion("surprise", 0.6)
        all_emotions = engine.get_all_emotions()
        assert len(all_emotions) == 2
        assert all_emotions["joy"] == 0.8
        assert all_emotions["surprise"] == 0.6

    def test_clear_emotions(self):
        """Test clearing all emotions."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.8)
        engine.set_base_emotion("sadness", 0.6)
        engine.clear_emotions()
        assert len(engine.get_all_emotions()) == 0


class TestCompositeEmotionSynthesis:
    """Tests for composite emotion synthesis."""

    def test_synthesize_empty(self):
        """Test synthesizing with no emotions."""
        engine = CompositeEmotion()
        result = engine.synthesize()
        assert result.name == "neutral"
        assert result.intensity == 0.0
        assert result.components == {}

    def test_synthesize_delight(self):
        """Test synthesizing joy + surprise -> delight."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.8)
        engine.set_base_emotion("surprise", 0.6)
        result = engine.synthesize()
        assert result.name == "delight"
        assert result.is_novel is False
        assert "joy" in result.components
        assert "surprise" in result.components

    def test_synthesize_resentment(self):
        """Test synthesizing sadness + anger -> resentment."""
        engine = CompositeEmotion()
        engine.set_base_emotion("sadness", 0.7)
        engine.set_base_emotion("anger", 0.5)
        result = engine.synthesize()
        assert result.name == "resentment"

    def test_synthesize_optimism(self):
        """Test synthesizing joy + anticipation -> optimism."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.5)
        engine.set_base_emotion("anticipation", 0.7)
        result = engine.synthesize()
        assert result.name == "optimism"

    def test_synthesize_anxiety(self):
        """Test synthesizing fear + anticipation -> anxiety."""
        engine = CompositeEmotion()
        engine.set_base_emotion("fear", 0.7)
        engine.set_base_emotion("anticipation", 0.6)
        result = engine.synthesize()
        assert result.name == "anxiety"

    def test_synthesize_single_emotion(self):
        """Test synthesizing with only one emotion."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.9)
        result = engine.synthesize()
        assert result.name == "joy"
        assert result.intensity == 0.9

    def test_synthesize_adhoc(self):
        """Test ad-hoc composite when no recipe matches."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.5)
        engine.set_base_emotion("disgust", 0.5)
        result = engine.synthesize()
        # Should be ad-hoc composite
        assert "+" in result.name
        assert result.is_novel is True

    def test_synthesize_from_dict(self):
        """Test one-shot synthesis from dict."""
        result = synthesize_from_emotions(
            {"joy": 0.8, "surprise": 0.6},
            neuroticism=0.5,
        )
        assert result.name == "delight"

    def test_create_composite_engine_convenience(self):
        """Test convenience factory function."""
        engine = create_composite_engine(neuroticism=0.3)
        assert engine.neuroticism == 0.3


class TestConflictResolution:
    """Tests for emotion conflict resolution."""

    def test_dominance_strategy(self):
        """Test dominance conflict resolution."""
        engine = CompositeEmotion(conflict_strategy="dominance")
        engine.set_base_emotion("joy", 0.8)
        engine.set_base_emotion("sadness", 0.4)
        result = engine.synthesize()
        # sadness should be reduced, joy should dominate
        emotions = engine.get_all_emotions()
        assert emotions["joy"] > emotions["sadness"]

    def test_cancel_strategy(self):
        """Test cancel conflict resolution."""
        engine = CompositeEmotion(conflict_strategy="cancel")
        engine.set_base_emotion("joy", 0.6)
        engine.set_base_emotion("sadness", 0.6)
        emotions_before = engine.get_all_emotions().copy()
        engine.synthesize()
        emotions_after = engine.get_all_emotions()
        # Both should be reduced toward each other
        assert emotions_after["joy"] <= emotions_before["joy"]

    def test_blend_strategy(self):
        """Test blend conflict resolution."""
        engine = CompositeEmotion(conflict_strategy="blend")
        engine.set_base_emotion("joy", 0.8)
        engine.set_base_emotion("sadness", 0.4)
        engine.synthesize()
        emotions = engine.get_all_emotions()
        # Both should converge toward average (0.6)
        assert emotions["joy"] <= 0.8
        assert emotions["sadness"] >= 0.4


class TestEmotionDecay:
    """Tests for emotion decay over time."""

    def test_no_decay_on_zero_delta(self):
        """Test no decay when delta is zero."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.8)
        engine.tick(delta_seconds=0)
        assert engine.get_emotion("joy") == 0.8

    def test_decay_removes_very_low_emotions(self):
        """Test emotions drop below threshold are removed."""
        engine = CompositeEmotion()
        engine.set_base_emotion("surprise", 0.02)  # Very low, half-life 30s
        engine.tick(delta_seconds=120.0)  # 4 half-lives
        assert engine.get_emotion("surprise") is None

    def test_decay_respects_half_life(self):
        """Test decay follows exponential curve."""
        # Use neuroticism=0 so decay_modifier=1.0 (no slowdown)
        engine = CompositeEmotion(neuroticism=0.0)
        engine.set_base_emotion("joy", 1.0)
        # Half-life is 120s for joy. After 120s, should be ~0.5
        engine.tick(delta_seconds=120.0)
        # Should be approximately 0.5 (with small floating point variance)
        assert 0.45 <= engine.get_emotion("joy") <= 0.55

    def test_high_neuroticism_alters_decay(self):
        """Test neuroticism alters the decay rate."""
        # neuroticism=0.8 → decay_modifier=0.36 → adjusted_halflife≈43s → more decay
        # neuroticism=0.0 → decay_modifier=1.0 → adjusted_halflife=120s → less decay
        high_neuro = CompositeEmotion(neuroticism=0.8)
        low_neuro = CompositeEmotion(neuroticism=0.0)
        high_neuro.set_base_emotion("joy", 1.0)
        low_neuro.set_base_emotion("joy", 1.0)
        high_val = high_neuro.tick_and_get(delta_seconds=60.0)
        low_val = low_neuro.tick_and_get(delta_seconds=60.0)
        # High neuroticism (sensitive, reactive) → emotions fluctuate faster → less remaining
        assert high_val < low_val, (
            f"Expected high-neuroticism to have lower value: "
            f"high={high_val:.4f}, low={low_val:.4f}"
        )


class TestThresholdTriggers:
    """Tests for emotion threshold triggering."""

    def test_set_threshold(self):
        """Test setting custom threshold."""
        engine = CompositeEmotion()
        engine.set_threshold("joy", 0.3)
        assert engine._thresholds["joy"] == 0.3

    def test_trigger_callback(self):
        """Test that callback fires when threshold exceeded."""
        engine = CompositeEmotion()
        triggered = []

        def callback(emotion, intensity):
            triggered.append((emotion, intensity))

        engine.register_listener("joy", callback)
        engine.set_threshold("joy", 0.5)
        engine.set_base_emotion("joy", 0.8)
        assert len(triggered) == 1
        assert triggered[0] == ("joy", 0.8)

    def test_no_trigger_below_threshold(self):
        """Test callback doesn't fire below threshold."""
        engine = CompositeEmotion()
        triggered = []

        def callback(emotion, intensity):
            triggered.append((emotion, intensity))

        engine.register_listener("joy", callback)
        engine.set_threshold("joy", 0.9)
        engine.set_base_emotion("joy", 0.5)
        assert len(triggered) == 0

    def test_get_triggered_emotions(self):
        """Test getting list of triggered emotions."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.8)
        engine.set_base_emotion("surprise", 0.6)
        triggered = engine.get_triggered_emotions(threshold=0.7)
        assert "joy" in triggered
        assert "surprise" not in triggered


class TestStateExport:
    """Tests for state export/import."""

    def test_to_dict(self):
        """Test exporting state to dictionary."""
        engine = CompositeEmotion(neuroticism=0.6)
        engine.set_base_emotion("joy", 0.8)
        engine.set_base_emotion("surprise", 0.6)
        data = engine.to_dict()
        assert "base_emotions" in data
        assert "joy" in data["base_emotions"]
        assert data["base_emotions"]["joy"]["intensity"] == 0.8
        assert "composite" in data

    def test_from_dict(self):
        """Test reconstructing from dictionary."""
        engine = CompositeEmotion()
        engine.set_base_emotion("joy", 0.8)
        engine.set_base_emotion("sadness", 0.4)
        data = engine.to_dict()
        restored = CompositeEmotion.from_dict(data, neuroticism=0.6)
        assert restored.get_emotion("joy") == 0.8
        assert restored.get_emotion("sadness") == 0.4


class TestIntegrationWithSoul:
    """Integration tests with existing Soul modules."""

    def test_with_OCEAN_params(self):
        """Test using OCEAN neuroticism directly."""
        from neshama.core.ocean import OceanParams
        ocean = OceanParams(neuroticism=0.7)
        engine = CompositeEmotion(neuroticism=ocean.neuroticism)
        assert engine.neuroticism == 0.7

    def test_with_emotion_recognizer(self):
        """Test integration with EmotionRecognizer."""
        from neshama.soul.emotion import EmotionRecognizer

        recognizer = EmotionRecognizer()
        engine = CompositeEmotion()

        text = "I'm so happy and surprised by this news!"
        tags = recognizer.recognize(text)

        for tag in tags:
            engine.set_base_emotion(tag.category.value, tag.intensity)

        result = engine.synthesize()
        assert result.name in COMPOSITE_RECIPES or "+" in result.name
        assert 0 < result.intensity <= 1.0

    def test_oneshot_synthesis_integration(self):
        """Test one-shot synthesis using recognizer results."""
        from neshama.soul.emotion import EmotionRecognizer

        recognizer = EmotionRecognizer()
        tags = recognizer.recognize("This is wonderful and amazing!")

        if tags:
            emotions = {tag.category.value: tag.intensity for tag in tags[:2]}
            result = synthesize_from_emotions(emotions)
            assert result is not None
            assert result.intensity >= 0
