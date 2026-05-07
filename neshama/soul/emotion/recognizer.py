# Soul Layer - Emotion Recognition Module
"""
Emotion Recognition: Identify user emotions from input

Features:
- Keyword-based emotion recognition
- Context-based emotion inference
- Compound emotion detection
- Emotion intensity evaluation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import re


class EmotionCategory(Enum):
    """Emotion categories."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    AMBIGUOUS = "ambiguous"


@dataclass
class EmotionTag:
    """Emotion tag with intensity and confidence."""
    category: EmotionCategory
    intensity: float = 0.5        # Intensity 0-1
    confidence: float = 0.5      # Confidence 0-1
    keywords: List[str] = field(default_factory=list)
    context: str = ""             # Trigger context


@dataclass
class EmotionPattern:
    """Emotion pattern definition."""
    name: str
    description: str
    primary_emotions: List[EmotionCategory]
    indicator_keywords: Dict[str, float]  # Keywords and weights
    context_patterns: List[str]           # Context patterns
    intensity_modifiers: Dict[str, float]  # Intensity modifiers


# Global recognizer instance
emotion_recognizer = None


class EmotionRecognizer:
    """Emotion recognizer for detecting emotions from text."""
    
    def __init__(self, config: Dict = None):
        self.emotion_patterns: Dict[EmotionCategory, EmotionPattern] = {}
        self.intensifiers: Dict[str, float] = {}
        self.negators: List[str] = []
        
        if config:
            self.load_config(config)
        else:
            self._init_default_patterns()
    
    def _init_default_patterns(self):
        """Initialize default emotion patterns."""
        
        # Joy/Happiness
        self.emotion_patterns[EmotionCategory.JOY] = EmotionPattern(
            name="joy",
            description="Happy, satisfied, pleased emotions",
            primary_emotions=[EmotionCategory.JOY],
            indicator_keywords={
                "开心": 0.9, "高兴": 0.9, "快乐": 0.9, "喜欢": 0.7,
                "太好了": 0.95, "棒": 0.8, "完美": 0.9, "幸福": 0.9,
                "兴奋": 0.8, "满足": 0.8, "愉悦": 0.8, "happy": 0.7,
                "joy": 0.8, "wonderful": 0.9, "great": 0.7, "love": 0.8,
                "😄": 0.9, "😊": 0.85, "🎉": 0.9, "👍": 0.7
            },
            context_patterns=[],
            intensity_modifiers={"非常": 1.3, "超级": 1.5, "有点": 0.7}
        )
        
        # Sadness
        self.emotion_patterns[EmotionCategory.SADNESS] = EmotionPattern(
            name="sadness",
            description="Sad, lost, depressed emotions",
            primary_emotions=[EmotionCategory.SADNESS],
            indicator_keywords={
                "难过": 0.8, "悲伤": 0.9, "伤心": 0.8, "失落": 0.8,
                "沮丧": 0.7, "郁闷": 0.7, "绝望": 0.9, "痛苦": 0.8,
                "哭": 0.7, "泪": 0.6, "遗憾": 0.6,
                "sad": 0.7, "unhappy": 0.7, "depressed": 0.8, "crying": 0.7,
                "😢": 0.9, "😔": 0.8, "💔": 0.9
            },
            context_patterns=[],
            intensity_modifiers={"非常": 1.3, "特别": 1.4, "有点": 0.6}
        )
        
        # Anger
        self.emotion_patterns[EmotionCategory.ANGER] = EmotionPattern(
            name="anger",
            description="Angry, frustrated, irritated emotions",
            primary_emotions=[EmotionCategory.ANGER],
            indicator_keywords={
                "生气": 0.9, "愤怒": 0.9, "恼火": 0.8, "不爽": 0.7,
                "讨厌": 0.7, "可恶": 0.8, "该死": 0.8, "混蛋": 0.7,
                "气": 0.6, "烦": 0.6, "燥": 0.6, "火": 0.6,
                "angry": 0.8, "mad": 0.7, "furious": 0.9, "hate": 0.8,
                "😠": 0.9, "😤": 0.85, "💢": 0.9
            },
            context_patterns=[],
            intensity_modifiers={"非常": 1.4, "超级": 1.6, "有点": 0.5}
        )
        
        # Fear
        self.emotion_patterns[EmotionCategory.FEAR] = EmotionPattern(
            name="fear",
            description="Fearful, worried, anxious emotions",
            primary_emotions=[EmotionCategory.FEAR],
            indicator_keywords={
                "害怕": 0.9, "恐惧": 0.9, "担心": 0.7, "担忧": 0.7,
                "焦虑": 0.8, "紧张": 0.7, "不安": 0.7, "惶恐": 0.8,
                "怕": 0.6, "慌": 0.6, "惊": 0.6,
                "fear": 0.8, "scared": 0.8, "worried": 0.7, "afraid": 0.8,
                "😰": 0.9, "😨": 0.85, "😟": 0.8
            },
            context_patterns=[],
            intensity_modifiers={"非常": 1.3, "有点": 0.6, "超级": 1.5}
        )
        
        # Surprise
        self.emotion_patterns[EmotionCategory.SURPRISE] = EmotionPattern(
            name="surprise",
            description="Surprised, shocked, amazed emotions",
            primary_emotions=[EmotionCategory.SURPRISE],
            indicator_keywords={
                "惊讶": 0.8, "意外": 0.8, "震惊": 0.9, "吃惊": 0.8,
                "哇": 0.7, "天": 0.6, "没想到": 0.7, "居然": 0.7,
                "surprise": 0.8, "shocked": 0.9, "wow": 0.7, "amazing": 0.7,
                "😮": 0.9, "😲": 0.85, "🤯": 0.9
            },
            context_patterns=[],
            intensity_modifiers={"非常": 1.3, "超级": 1.5, "有点": 0.5}
        )
        
        # Disgust
        self.emotion_patterns[EmotionCategory.DISGUST] = EmotionPattern(
            name="disgust",
            description="Disgusted, repulsed, disdainful emotions",
            primary_emotions=[EmotionCategory.DISGUST],
            indicator_keywords={
                "恶心": 0.9, "厌恶": 0.9, "讨厌": 0.7, "反感": 0.8,
                "不屑": 0.7, "嫌弃": 0.8, "鄙视": 0.7, "烦人": 0.6,
                "disgust": 0.8, "gross": 0.8, "ew": 0.7,
                "😒": 0.8, "🙄": 0.7, "😖": 0.9
            },
            context_patterns=[],
            intensity_modifiers={"非常": 1.4, "超级": 1.5, "有点": 0.5}
        )
        
        # Trust
        self.emotion_patterns[EmotionCategory.TRUST] = EmotionPattern(
            name="trust",
            description="Trusting, believing, confident emotions",
            primary_emotions=[EmotionCategory.TRUST],
            indicator_keywords={
                "相信": 0.8, "信任": 0.9, "依赖": 0.7, "放心": 0.8,
                "相信你": 0.9, "靠谱": 0.8,
                "trust": 0.8, "believe": 0.7, "rely": 0.7,
                "🙏": 0.8, "💪": 0.7
            },
            context_patterns=[],
            intensity_modifiers={"非常": 1.3, "特别": 1.4, "有点": 0.6}
        )
        
        # Anticipation
        self.emotion_patterns[EmotionCategory.ANTICIPATION] = EmotionPattern(
            name="anticipation",
            description="Excited, eager, looking forward to emotions",
            primary_emotions=[EmotionCategory.ANTICIPATION],
            indicator_keywords={
                "期待": 0.9, "希望": 0.8, "盼望": 0.8, "兴奋": 0.9,
                "想要": 0.7, "憧憬": 0.8,
                "excited": 0.8, "hope": 0.7, "looking forward": 0.8,
                "🤩": 0.9, "✨": 0.8, "🌟": 0.7
            },
            context_patterns=[],
            intensity_modifiers={"非常": 1.3, "超级": 1.5, "有点": 0.6}
        )
        
        # Intensifiers
        self.intensifiers = {
            "非常": 1.4,
            "特别": 1.5,
            "极其": 1.6,
            "超级": 1.6,
            "十分": 1.3,
            "相当": 1.2,
            "有点": 0.7,
            "稍微": 0.6,
            "略微": 0.5,
            "very": 1.4,
            "extremely": 1.6,
            "really": 1.3,
            "super": 1.5,
            "a bit": 0.6,
        }
        
        # Negators
        self.negators = ["不", "没", "无", "非", "别", "未", "否", "not", "no", "don't", "doesn't", "didn't"]
    
    def recognize(self, text: str) -> List[EmotionTag]:
        """
        Recognize emotions from text.
        
        Args:
            text: Input text
            
        Returns:
            List of EmotionTag objects sorted by intensity
        """
        if not text:
            return []
        
        text_lower = text.lower()
        results: List[EmotionTag] = []
        
        for category, pattern in self.emotion_patterns.items():
            score = 0.0
            matched_keywords = []
            
            for keyword, weight in pattern.indicator_keywords.items():
                # Check for keyword match (case-insensitive for letters)
                if keyword in text or keyword.lower() in text_lower:
                    score += weight
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # Apply intensifier modifiers
                for intensifier, modifier in self.intensifiers.items():
                    if intensifier in text or intensifier.lower() in text_lower:
                        score *= modifier
                        break
                
                # Check for negators
                for negator in self.negators:
                    if negator in text_lower:
                        score *= 0.3
                        break
                
                # Normalize score
                intensity = min(1.0, score / len(matched_keywords))
                confidence = min(1.0, len(matched_keywords) / 3)
                
                results.append(EmotionTag(
                    category=category,
                    intensity=intensity,
                    confidence=confidence,
                    keywords=matched_keywords,
                    context=text[:100]
                ))
        
        # Sort by intensity
        results.sort(key=lambda x: x.intensity, reverse=True)
        
        return results[:5]  # Return top 5 emotions
    
    def recognize_dominant(self, text: str) -> Optional[EmotionTag]:
        """
        Get the dominant emotion from text.
        
        Args:
            text: Input text
            
        Returns:
            Top EmotionTag or None
        """
        results = self.recognize(text)
        return results[0] if results else None
    
    def load_config(self, config: Dict):
        """Load configuration."""
        self._init_default_patterns()
        
        if "emotions" in config:
            for emotion_name, emotion_config in config["emotions"].items():
                # Update patterns from config
                pass
    
    def add_pattern(self, category: EmotionCategory, pattern: EmotionPattern):
        """Add or update an emotion pattern."""
        self.emotion_patterns[category] = pattern


def recognize_emotion(text: str) -> List[EmotionTag]:
    """Convenience function for emotion recognition."""
    global emotion_recognizer
    if emotion_recognizer is None:
        emotion_recognizer = EmotionRecognizer()
    return emotion_recognizer.recognize(text)
