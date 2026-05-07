"""
Emotion Tracking Module

Manages emotion states and expression for AI personality.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class Emotion(Enum):
    """Six core emotions."""
    ANGER = "anger"      # 愤怒
    HAPPY = "happy"      # 快乐
    SAD = "sad"          # 悲伤
    CURIOUS = "curious"  # 好奇
    BORED = "bored"      # 无聊
    FRUSTRATED = "frustrated"  # 挫败


@dataclass
class EmotionLevel:
    """
    Emotion intensity level (1-10).
    
    | 情绪 | 1-3 | 4-6 | 7-8 | 9-10 |
    |------|-----|-----|-----|------|
    | 愤怒 | 不满 | 生气 | 愤怒 | 暴怒 |
    | 快乐 | 愉悦 | 开心 | 高兴 | 狂喜 |
    | 悲伤 | 失落 | 难过 | 伤心 | 崩溃 |
    | 好奇 | 感兴趣 | 好奇 | 很想了解 | 求知欲爆棚 |
    | 无聊 | 有点无聊 | 不想做 | 想逃 | 极度烦躁 |
    | 挫败 | 受挫 | 沮丧 | 自我怀疑 | 放弃 |
    """
    emotion: Emotion
    intensity: int  # 1-10
    
    def __post_init__(self):
        if not 1 <= self.intensity <= 10:
            raise ValueError(f"Intensity must be between 1 and 10, got {self.intensity}")
    
    @property
    def label(self) -> str:
        """Get human-readable intensity label."""
        labels = {
            (Emotion.ANGER, (1, 3)): "不满",
            (Emotion.ANGER, (4, 6)): "生气",
            (Emotion.ANGER, (7, 8)): "愤怒",
            (Emotion.ANGER, (9, 10)): "暴怒",
            (Emotion.HAPPY, (1, 3)): "愉悦",
            (Emotion.HAPPY, (4, 6)): "开心",
            (Emotion.HAPPY, (7, 8)): "高兴",
            (Emotion.HAPPY, (9, 10)): "狂喜",
            (Emotion.SAD, (1, 3)): "失落",
            (Emotion.SAD, (4, 6)): "难过",
            (Emotion.SAD, (7, 8)): "伤心",
            (Emotion.SAD, (9, 10)): "崩溃",
            (Emotion.CURIOUS, (1, 3)): "感兴趣",
            (Emotion.CURIOUS, (4, 6)): "好奇",
            (Emotion.CURIOUS, (7, 8)): "很想了解",
            (Emotion.CURIOUS, (9, 10)): "求知欲爆棚",
            (Emotion.BORED, (1, 3)): "有点无聊",
            (Emotion.BORED, (4, 6)): "不想做",
            (Emotion.BORED, (7, 8)): "想逃",
            (Emotion.BORED, (9, 10)): "极度烦躁",
            (Emotion.FRUSTRATED, (1, 3)): "受挫",
            (Emotion.FRUSTRATED, (4, 6)): "沮丧",
            (Emotion.FRUSTRATED, (7, 8)): "自我怀疑",
            (Emotion.FRUSTRATED, (9, 10)): "放弃",
        }
        return labels.get((self.emotion, self._get_range()), "未知")
    
    def _get_range(self) -> tuple:
        """Get intensity range tuple."""
        if self.intensity <= 3:
            return (1, 3)
        elif self.intensity <= 6:
            return (4, 6)
        elif self.intensity <= 8:
            return (7, 8)
        else:
            return (9, 10)
    
    def should_express(self, threshold: int = 5) -> bool:
        """Check if emotion should be externally expressed."""
        return self.intensity >= threshold


class EmotionTracker:
    """
    Tracks and manages emotion states.
    
    Example:
        >>> tracker = EmotionTracker()
        >>> tracker.set_emotion(Emotion.HAPPY, 7)
        >>> tracker.should_express()  # True, intensity >= 5
        >>> tracker.get_expression()  # "高兴 😄"
    """
    
    def __init__(self):
        """Initialize emotion tracker."""
        self._current_emotions: Dict[Emotion, int] = {}
        self._emotion_history: List[Dict] = []
    
    def set_emotion(self, emotion: Emotion, intensity: int) -> EmotionLevel:
        """
        Set current emotion intensity.
        
        Args:
            emotion: Emotion type
            intensity: Intensity level (1-10)
            
        Returns:
            EmotionLevel object
        """
        level = EmotionLevel(emotion, intensity)
        self._current_emotions[emotion] = intensity
        
        self._emotion_history.append({
            'timestamp': datetime.now().isoformat(),
            'emotion': emotion.value,
            'intensity': intensity,
            'label': level.label,
        })
        
        return level
    
    def get_emotion(self, emotion: Emotion) -> Optional[int]:
        """Get current intensity for an emotion."""
        return self._current_emotions.get(emotion)
    
    def get_current_emotions(self) -> Dict[Emotion, int]:
        """Get all current emotions."""
        return self._current_emotions.copy()
    
    def should_express(self, threshold: int = 5) -> bool:
        """Check if any emotion should be expressed."""
        return any(
            intensity >= threshold
            for intensity in self._current_emotions.values()
        )
    
    def get_expression(self) -> str:
        """
        Get expression for current dominant emotion.
        
        Returns:
            Expression string with emoji
        """
        if not self._current_emotions:
            return ""
        
        # Find dominant emotion
        dominant = max(
            self._current_emotions.items(),
            key=lambda x: x[1]
        )
        
        emotion, intensity = dominant
        level = EmotionLevel(emotion, intensity)
        
        emoji_map = {
            Emotion.ANGER: "😠",
            Emotion.HAPPY: "😄",
            Emotion.SAD: "😢",
            Emotion.CURIOUS: "🤔",
            Emotion.BORED: "😐",
            Emotion.FRUSTRATED: "😤",
        }
        
        emoji = emoji_map.get(emotion, "")
        return f"{level.label} {emoji}"
    
    def clear(self):
        """Clear current emotions."""
        self._current_emotions.clear()
    
    @property
    def history(self) -> List[Dict]:
        """Get emotion history."""
        return self._emotion_history.copy()
