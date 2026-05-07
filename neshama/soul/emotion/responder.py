# Soul Layer - Emotion Response Module
"""
Emotion Response Generation

Generates emotionally appropriate responses based on detected emotions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from neshama.soul.emotion.recognizer import EmotionCategory, EmotionTag


class ResponseStrategy(Enum):
    """Response generation strategies."""
    EMPATHETIC = "empathetic"       # Acknowledge and validate emotion
    REFRAMING = "reframing"         # Help reframe the situation
    ACTIONABLE = "actionable"       # Provide actionable suggestions
    DISTRACTING = "distracting"     # Lighten mood if appropriate
    SILENT = "silent"              # Minimal response when uncertain


@dataclass
class ResponseTemplate:
    """Response template for emotion handling."""
    strategy: ResponseStrategy
    templates: List[str]  # Multiple template options
    emoji: Optional[str] = None
    priority: int = 1     # Lower = higher priority


# Global responder instance
emotion_responder = None


class EmotionResponder:
    """
    Emotion Responder.
    
    Generates appropriate responses based on detected emotions.
    
    Example:
        >>> responder = EmotionResponder()
        >>> response = responder.respond(
        ...     user_emotion=EmotionCategory.SADNESS,
        ...     intensity=0.8,
        ...     user_message="I'm feeling really down today..."
        ... )
        >>> print(response)
    """
    
    def __init__(self, config: Dict = None):
        self.response_templates: Dict[EmotionCategory, List[ResponseTemplate]] = {}
        self.default_templates: List[ResponseTemplate] = []
        
        if config:
            self.load_config(config)
        else:
            self._init_default_templates()
    
    def _init_default_templates(self):
        """Initialize default response templates."""
        
        # Joy templates
        self.response_templates[EmotionCategory.JOY] = [
            ResponseTemplate(
                strategy=ResponseStrategy.EMPATHETIC,
                templates=[
                    "I'm so glad to hear you're happy! {reason}",
                    "That's wonderful! {reason}",
                    "Your joy is contagious! 😊",
                ],
                emoji="😄",
                priority=1
            ),
            ResponseTemplate(
                strategy=ResponseStrategy.ACTIONABLE,
                templates=[
                    "What's making you so happy? I'd love to hear more!",
                    "That's great news! Want to share more about it?",
                ],
                priority=2
            ),
        ]
        
        # Sadness templates
        self.response_templates[EmotionCategory.SADNESS] = [
            ResponseTemplate(
                strategy=ResponseStrategy.EMPATHETIC,
                templates=[
                    "I'm sorry you're feeling down. It sounds like {reason}",
                    "I understand this is difficult. {reason}",
                    "That sounds really hard. I'm here to listen. 💙",
                ],
                emoji="🤗",
                priority=1
            ),
            ResponseTemplate(
                strategy=ResponseStrategy.ACTIONABLE,
                templates=[
                    "Would you like to talk about what's troubling you?",
                    "Sometimes sharing can help. I'm here to listen.",
                ],
                priority=2
            ),
            ResponseTemplate(
                strategy=ResponseStrategy.REFRAMING,
                templates=[
                    "Even in difficult times, there might be small things that could help.",
                    "Remember, difficult emotions are temporary. You're stronger than you think.",
                ],
                priority=3
            ),
        ]
        
        # Anger templates
        self.response_templates[EmotionCategory.ANGER] = [
            ResponseTemplate(
                strategy=ResponseStrategy.EMPATHETIC,
                templates=[
                    "I can hear that you're frustrated. {reason}",
                    "That sounds really annoying. {reason}",
                    "Your feelings are valid. {reason}",
                ],
                emoji="😔",
                priority=1
            ),
            ResponseTemplate(
                strategy=ResponseStrategy.REFRAMING,
                templates=[
                    "When you're ready, I'd be happy to help think through solutions.",
                    "Sometimes taking a step back can help see things more clearly.",
                ],
                priority=2
            ),
        ]
        
        # Fear templates
        self.response_templates[EmotionCategory.FEAR] = [
            ResponseTemplate(
                strategy=ResponseStrategy.EMPATHETIC,
                templates=[
                    "I understand you're worried about {reason}",
                    "It's natural to feel anxious about this. {reason}",
                    "I'm here to help you work through this. 💪",
                ],
                emoji="🤗",
                priority=1
            ),
            ResponseTemplate(
                strategy=ResponseStrategy.ACTIONABLE,
                templates=[
                    "Let's break this down together - what specifically are you worried about?",
                    "Would it help to make a plan to address your concerns?",
                ],
                priority=2
            ),
        ]
        
        # Surprise templates
        self.response_templates[EmotionCategory.SURPRISE] = [
            ResponseTemplate(
                strategy=ResponseStrategy.EMPATHETIC,
                templates=[
                    "Wow, that is surprising! {reason}",
                    "I can see why you're surprised! {reason}",
                    "That's unexpected indeed! 🤯",
                ],
                emoji="😮",
                priority=1
            ),
        ]
        
        # Disgust templates
        self.response_templates[EmotionCategory.DISGUST] = [
            ResponseTemplate(
                strategy=ResponseStrategy.EMPATHETIC,
                templates=[
                    "I understand your reaction. {reason}",
                    "That does sound unpleasant. {reason}",
                ],
                emoji="😕",
                priority=1
            ),
        ]
        
        # Trust templates
        self.response_templates[EmotionCategory.TRUST] = [
            ResponseTemplate(
                strategy=ResponseStrategy.EMPATHETIC,
                templates=[
                    "Thank you for trusting me! 🙏",
                    "I appreciate your confidence. I'll do my best to help.",
                    "Your trust means a lot to me! 💙",
                ],
                emoji="🤝",
                priority=1
            ),
        ]
        
        # Anticipation templates
        self.response_templates[EmotionCategory.ANTICIPATION] = [
            ResponseTemplate(
                strategy=ResponseStrategy.EMPATHETIC,
                templates=[
                    "I can feel your excitement! {reason}",
                    "That sounds like something to look forward to! ✨",
                    "Your enthusiasm is great! What are you most excited about?",
                ],
                emoji="🤩",
                priority=1
            ),
        ]
        
        # Default templates
        self.default_templates = [
            ResponseTemplate(
                strategy=ResponseStrategy.EMPATHETIC,
                templates=[
                    "I hear you. Tell me more.",
                    "Thanks for sharing that with me.",
                    "I appreciate you opening up.",
                ],
                priority=10
            ),
        ]
    
    def respond(
        self,
        user_emotion: EmotionCategory,
        intensity: float = 0.5,
        user_message: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate an emotional response.
        
        Args:
            user_emotion: Detected emotion category
            intensity: Emotion intensity (0-1)
            user_message: Original user message
            context: Additional context
            
        Returns:
            Generated response string
        """
        templates = self.response_templates.get(user_emotion, self.default_templates)
        
        # Select template based on intensity
        if intensity > 0.7:
            # High intensity - use primary empathetic response
            selected = [t for t in templates if t.priority == 1]
        elif intensity > 0.4:
            # Medium intensity - mix of empathetic and actionable
            selected = [t for t in templates if t.priority <= 2]
        else:
            # Low intensity - use any template
            selected = templates
        
        if not selected:
            selected = templates
        
        # Pick a random template from selection
        import random
        template = random.choice(selected)
        
        # Generate response with context
        reason = self._extract_reason(user_message)
        template_str = random.choice(template.templates)
        
        response = template_str.format(reason=reason) if "{reason}" in template_str else template_str
        
        # Add emoji if available and intensity is high
        if template.emoji and intensity > 0.5:
            response = f"{response} {template.emoji}"
        
        return response
    
    def _extract_reason(self, message: str) -> str:
        """Extract a brief reason or context from the message."""
        if not message:
            return ""
        
        # Simple extraction - take first clause
        for sep in ["，", ",", "。", ".", "！", "!", "？", "?"]:
            if sep in message:
                return message.split(sep)[0]
        
        return message[:50] + ("..." if len(message) > 50 else "")
    
    def load_config(self, config: Dict):
        """Load configuration."""
        self._init_default_templates()


def generate_emotional_response(
    emotion: EmotionCategory,
    intensity: float = 0.5,
    message: str = "",
) -> str:
    """Convenience function for generating emotional response."""
    global emotion_responder
    if emotion_responder is None:
        emotion_responder = EmotionResponder()
    return emotion_responder.respond(emotion, intensity, message)
