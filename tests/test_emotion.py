"""
Neshama Emotion System Tests
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.emotion import (
    EmotionRecognizer,
    EmotionResponder,
    EmotionMemory,
    EmotionCategory,
)
from neshama.tools.emotion import Emotion, EmotionLevel, EmotionTracker


class TestEmotionRecognizer:
    """Tests for EmotionRecognizer."""
    
    def test_initialization(self):
        """Test recognizer initialization."""
        recognizer = EmotionRecognizer()
        assert recognizer is not None
        assert len(recognizer.emotion_patterns) > 0
    
    def test_recognize_joy(self):
        """Test recognizing joy."""
        recognizer = EmotionRecognizer()
        results = recognizer.recognize("I'm so happy today! This is wonderful!")
        assert len(results) > 0
        assert results[0].category == EmotionCategory.JOY
        assert results[0].intensity > 0.5
    
    def test_recognize_sadness(self):
        """Test recognizing sadness."""
        recognizer = EmotionRecognizer()
        results = recognizer.recognize("I feel so sad and depressed")
        assert len(results) > 0
        assert results[0].category == EmotionCategory.SADNESS
    
    def test_recognize_anger(self):
        """Test recognizing anger."""
        recognizer = EmotionRecognizer()
        results = recognizer.recognize("I'm very angry! This is ridiculous!")
        assert len(results) > 0
        assert results[0].category == EmotionCategory.ANGER
    
    def test_recognize_empty(self):
        """Test empty input."""
        recognizer = EmotionRecognizer()
        results = recognizer.recognize("")
        assert len(results) == 0
    
    def test_dominant_emotion(self):
        """Test getting dominant emotion."""
        recognizer = EmotionRecognizer()
        result = recognizer.recognize_dominant("I love this so much!")
        assert result is not None
        assert result.category == EmotionCategory.JOY
    
    def test_chinese_keywords(self):
        """Test Chinese emotion keywords."""
        recognizer = EmotionRecognizer()
        results = recognizer.recognize("我今天很开心！太棒了！")
        assert len(results) > 0
        assert results[0].category == EmotionCategory.JOY
    
    def test_intensity_modifiers(self):
        """Test intensity modifiers."""
        recognizer = EmotionRecognizer()
        
        normal = recognizer.recognize("I'm happy")
        boosted = recognizer.recognize("I'm very happy")
        
        assert boosted[0].intensity > normal[0].intensity


class TestEmotionResponder:
    """Tests for EmotionResponder."""
    
    def test_initialization(self):
        """Test responder initialization."""
        responder = EmotionResponder()
        assert responder is not None
    
    def test_respond_joy(self):
        """Test responding to joy."""
        responder = EmotionResponder()
        response = responder.respond(EmotionCategory.JOY, 0.8)
        assert len(response) > 0
    
    def test_respond_sadness(self):
        """Test responding to sadness."""
        responder = EmotionResponder()
        response = responder.respond(EmotionCategory.SADNESS, 0.7)
        assert len(response) > 0
    
    def test_different_intensities(self):
        """Test different intensity levels."""
        responder = EmotionResponder()
        
        low = responder.respond(EmotionCategory.JOY, 0.3)
        high = responder.respond(EmotionCategory.JOY, 0.9)
        
        # High intensity might have emoji, low might not
        assert isinstance(low, str)
        assert isinstance(high, str)


class TestEmotionTracker:
    """Tests for EmotionTracker (tools layer)."""
    
    def test_initialization(self):
        """Test tracker initialization."""
        tracker = EmotionTracker()
        assert len(tracker.get_current_emotions()) == 0
    
    def test_set_emotion(self):
        """Test setting emotion."""
        tracker = EmotionTracker()
        level = tracker.set_emotion(Emotion.HAPPY, 7)
        assert level.emotion == Emotion.HAPPY
        assert level.intensity == 7
        assert level.label == "高兴"
    
    def test_get_emotion(self):
        """Test getting emotion."""
        tracker = EmotionTracker()
        tracker.set_emotion(Emotion.SAD, 5)
        assert tracker.get_emotion(Emotion.SAD) == 5
    
    def test_should_express(self):
        """Test should express threshold."""
        tracker = EmotionTracker()
        tracker.set_emotion(Emotion.HAPPY, 3)
        assert tracker.should_express() is False
        
        tracker.set_emotion(Emotion.HAPPY, 7)
        assert tracker.should_express() is True
    
    def test_get_expression(self):
        """Test getting expression."""
        tracker = EmotionTracker()
        tracker.set_emotion(Emotion.HAPPY, 7)
        expr = tracker.get_expression()
        assert "高兴" in expr
        assert "😄" in expr
    
    def test_history(self):
        """Test emotion history."""
        tracker = EmotionTracker()
        tracker.set_emotion(Emotion.HAPPY, 5)
        tracker.set_emotion(Emotion.SAD, 3)
        
        history = tracker.history
        assert len(history) == 2


class TestEmotionLevel:
    """Tests for EmotionLevel."""
    
    def test_intensity_levels(self):
        """Test different intensity levels."""
        level = EmotionLevel(Emotion.ANGER, 5)
        assert level.label == "生气"
        
        level = EmotionLevel(Emotion.ANGER, 9)
        assert level.label == "暴怒"
    
    def test_validation(self):
        """Test intensity validation."""
        with pytest.raises(ValueError):
            EmotionLevel(Emotion.HAPPY, 0)  # Too low
        
        with pytest.raises(ValueError):
            EmotionLevel(Emotion.HAPPY, 11)  # Too high
    
    def test_should_express(self):
        """Test expression threshold."""
        level = EmotionLevel(Emotion.HAPPY, 4)
        assert level.should_express() is False
        
        level = EmotionLevel(Emotion.HAPPY, 6)
        assert level.should_express() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
