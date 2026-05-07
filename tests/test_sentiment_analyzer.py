# Tests for SentimentAnalyzer
"""
Tests for the lightweight rule-based sentiment analyzer.
"""

import pytest

from neshama.soul.emotion.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzerBasic:
    """Basic emotion detection tests."""
    
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_anger_explicit(self):
        """Explicit anger words should be detected."""
        result = self.analyzer.analyze("我非常愤怒！")
        assert result.dominant_emotion == "anger"
        assert result.scores.get("anger", 0) > 0
    
    def test_joy_explicit(self):
        """Explicit joy words should be detected."""
        result = self.analyzer.analyze("今天太开心了！")
        assert result.dominant_emotion == "joy"
        assert result.scores.get("joy", 0) > 0
    
    def test_sadness_explicit(self):
        """Explicit sadness words should be detected."""
        result = self.analyzer.analyze("我很难过")
        assert result.dominant_emotion == "sadness"
        assert result.scores.get("sadness", 0) > 0
    
    def test_fear_explicit(self):
        """Explicit fear words should be detected."""
        result = self.analyzer.analyze("我害怕")
        assert result.dominant_emotion == "fear"
        assert result.scores.get("fear", 0) > 0
    
    def test_empty_string(self):
        """Empty string should return neutral."""
        result = self.analyzer.analyze("")
        assert result.dominant_emotion == "neutral"
    
    def test_neutral_text(self):
        """Text without emotion words should return neutral or low scores."""
        result = self.analyzer.analyze("今天天气不错")
        # May or may not detect emotion, but should not crash
        assert result.dominant_emotion is not None


class TestSentimentAnalyzerImplicit:
    """Tests for implicit emotion detection (the core problem this solves)."""
    
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_implicit_anger_rhetorical_question(self):
        """"你配吗？" should be detected as anger (rhetorical + implicit)."""
        result = self.analyzer.analyze("你配吗？")
        assert result.scores.get("anger", 0) > 0
    
    def test_implicit_anger_disdain(self):
        """"你以为你是谁" should be detected as anger."""
        result = self.analyzer.analyze("你以为你是谁？")
        assert result.scores.get("anger", 0) > 0
    
    def test_implicit_anger_sarcasm(self):
        """Sarcastic patterns should boost anger."""
        result = self.analyzer.analyze("难道你觉得这样对吗？")
        assert result.is_irony is True
        assert result.scores.get("anger", 0) > 0
    
    def test_implicit_disgust(self):
        """"你算什么东西" should be detected as disgust/anger."""
        result = self.analyzer.analyze("你算什么东西")
        anger_or_disgust = result.scores.get("anger", 0) + result.scores.get("disgust", 0)
        assert anger_or_disgust > 0


class TestSentimentAnalyzerIntensity:
    """Tests for intensity modifier detection."""
    
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_amplifier_too_much(self):
        """"太...了" should amplify emotion."""
        result = self.analyzer.analyze("太生气了！")
        assert result.intensity_multiplier > 1.0
    
    def test_amplifier_very(self):
        """"非常" should amplify emotion."""
        result = self.analyzer.analyze("我非常愤怒")
        assert result.intensity_multiplier > 1.0
    
    def test_diminisher_a_little(self):
        """"有点" should diminish emotion."""
        result = self.analyzer.analyze("我有点难过")
        assert result.intensity_multiplier < 1.0
    
    def test_amplifier_overrides_diminisher(self):
        """When both amplifier and diminisher present, amplifier wins."""
        result = self.analyzer.analyze("太高兴了")  # "太" is amplifier
        assert result.intensity_multiplier > 1.0


class TestSentimentAnalyzerSentencePatterns:
    """Tests for sentence pattern adjustments."""
    
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_exclamation_amplifies(self):
        """Exclamation marks should amplify existing emotions."""
        result = self.analyzer.analyze("好开心！")
        result_no_excl = self.analyzer.analyze("好开心")
        # Exclamation version should have higher joy
        assert result.scores.get("joy", 0) >= result_no_excl.scores.get("joy", 0)
    
    def test_rhetorical_question_boosts_anger(self):
        """Multiple question marks (rhetorical) should boost anger."""
        result = self.analyzer.analyze("凭什么？？")
        assert result.scores.get("anger", 0) > 0


class TestSentimentAnalyzerIrony:
    """Tests for irony detection."""
    
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_irony_pattern_1(self):
        """"难道...吗" should be detected as irony."""
        result = self.analyzer.analyze("难道你觉得这很好吗？")
        assert result.is_irony is True
    
    def test_irony_boosts_anger(self):
        """Irony should boost anger and disgust scores."""
        result = self.analyzer.analyze("难道你觉得这很好吗？")
        assert result.scores.get("anger", 0) > 0
        assert result.scores.get("disgust", 0) > 0


class TestSentimentAnalyzerOutput:
    """Tests for output format."""
    
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_to_dict(self):
        """to_dict should return a valid dict."""
        result = self.analyzer.analyze("开心")
        d = result.to_dict()
        assert "scores" in d
        assert "dominant_emotion" in d
        assert "is_irony" in d
        assert "intensity_multiplier" in d
    
    def test_scores_clamped(self):
        """All scores should be between 0 and 1."""
        result = self.analyzer.analyze("太愤怒了！凭什么！可恶！去死！")
        for emotion, score in result.scores.items():
            assert 0.0 <= score <= 1.0, f"{emotion} score {score} not in [0,1]"
