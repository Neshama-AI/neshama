"""
Reflection Trigger Module

Triggers and generates reflection prompts for AI agents.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class ReflectionType(Enum):
    """Types of reflection triggers."""
    TASK_AFTER = "task_after"      # 任务后反思 - 完成重要任务后
    DAILY = "daily"                # 日常反思 - 每10轮对话结束
    ERROR = "error"                # 错误反思 - 出现失误或返工
    EMOTION = "emotion"            # 情绪反思 - 情绪强度≥7后
    WEEKLY = "weekly"              # 每周复盘 - 周五下班前


@dataclass
class ReflectionPrompt:
    """A generated reflection prompt."""
    reflection_type: ReflectionType
    prompt: str
    context: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'type': self.reflection_type.value,
            'prompt': self.prompt,
            'context': self.context,
            'timestamp': self.timestamp
        }


class ReflectionTrigger:
    """
    Triggers reflections based on context and timing.
    
    Supports 5 types of reflection:
    1. Task-after: After completing important tasks
    2. Daily: After every 10 conversation rounds
    3. Error: After mistakes or rework
    4. Emotion: After emotion intensity >= 7
    5. Weekly: Friday before end of work
    
    Example:
        >>> trigger = ReflectionTrigger()
        >>> if trigger.should_reflect({'error_occurred': True}):
        ...     prompt = trigger.generate_prompt({'task': 'coding'})
    """
    
    # Conversation rounds before daily reflection
    DAILY_REFLECTION_INTERVAL = 10
    
    # Emotion intensity threshold for emotion reflection
    EMOTION_THRESHOLD = 7
    
    # Prompt templates by reflection type
    PROMPT_TEMPLATES: Dict[ReflectionType, str] = {
        ReflectionType.TASK_AFTER: """任务完成反思

刚完成了: {task_description}

请思考以下问题:
1. 这次任务完成得怎么样？
2. 有哪些可以改进的地方？
3. 学到了什么新东西？
4. 下次遇到类似任务可以怎么做？
""",
        ReflectionType.DAILY: """日常反思

对话轮次: {conversation_round}

请思考以下问题:
1. 今天有哪些收获？
2. 有哪些地方可以做得更好？
3. 有没有什么困惑或卡点？
""",
        ReflectionType.ERROR: """错误反思

发生的错误: {error_description}
背景: {context}

请思考以下问题:
1. 为什么会出错？
2. 是知识不足还是粗心大意？
3. 以后如何避免类似错误？
4. 需要学习什么来改进？
""",
        ReflectionType.EMOTION: """情绪反思

情绪: {emotion_name}
强度: {emotion_intensity}/10

请思考以下问题:
1. 这个情绪因何而起？
2. 处理得当吗？
3. 有什么可以改进的情绪管理方式？
""",
        ReflectionType.WEEKLY: """每周复盘

本周主要任务: {weekly_tasks}

请思考以下问题:
1. 这周完成得怎么样？
2. 最大的收获是什么？
3. 有哪些遗憾？
4. 下周有什么计划？
"""
    }

    def __init__(self):
        """Initialize reflection trigger."""
        self._conversation_rounds = 0
        self._last_reflection_time: Optional[str] = None
        self._reflection_history: List[Dict] = []
    
    def reset_conversation_rounds(self) -> None:
        """Reset conversation round counter."""
        self._conversation_rounds = 0
    
    def increment_conversation_round(self) -> None:
        """Increment conversation round counter."""
        self._conversation_rounds += 1
    
    def should_reflect(self, context: Dict[str, Any]) -> bool:
        """
        Check if reflection should be triggered.
        
        Args:
            context: Context dictionary with flags:
                - task_completed: bool
                - error_occurred: bool
                - emotion_intensity: int (1-10)
                - is_friday: bool
                
        Returns:
            True if reflection should be triggered.
        """
        # Error reflection (highest priority)
        if context.get('error_occurred', False):
            return True
        
        # Emotion reflection
        emotion_intensity = context.get('emotion_intensity', 0)
        if emotion_intensity >= self.EMOTION_THRESHOLD:
            return True
        
        # Task completion reflection
        if context.get('task_completed', False):
            return True
        
        # Daily reflection check
        if self._conversation_rounds >= self.DAILY_REFLECTION_INTERVAL:
            return True
        
        # Weekly reflection
        if context.get('is_friday', False):
            return True
        
        return False
    
    def determine_reflection_type(self, context: Dict[str, Any]) -> ReflectionType:
        """
        Determine the primary reflection type based on context.
        
        Priority: ERROR > EMOTION > TASK > DAILY > WEEKLY
        """
        if context.get('error_occurred', False):
            return ReflectionType.ERROR
        
        emotion_intensity = context.get('emotion_intensity', 0)
        if emotion_intensity >= self.EMOTION_THRESHOLD:
            return ReflectionType.EMOTION
        
        if context.get('task_completed', False):
            return ReflectionType.TASK_AFTER
        
        if self._conversation_rounds >= self.DAILY_REFLECTION_INTERVAL:
            return ReflectionType.DAILY
        
        if context.get('is_friday', False):
            return ReflectionType.WEEKLY
        
        return ReflectionType.DAILY
    
    def generate_prompt(self, context: Dict[str, Any]) -> ReflectionPrompt:
        """
        Generate a reflection prompt based on context.
        
        Args:
            context: Context dictionary with relevant information.
            
        Returns:
            ReflectionPrompt with generated prompt.
        """
        reflection_type = self.determine_reflection_type(context)
        template = self.PROMPT_TEMPLATES[reflection_type]
        
        # Fill in template variables
        prompt = self._fill_template(template, reflection_type, context)
        
        reflection = ReflectionPrompt(
            reflection_type=reflection_type,
            prompt=prompt,
            context=context,
            timestamp=datetime.now().isoformat()
        )
        
        self._reflection_history.append(reflection.to_dict())
        self._last_reflection_time = reflection.timestamp
        
        # Reset counters after reflection
        if reflection_type == ReflectionType.DAILY:
            self._conversation_rounds = 0
        
        return reflection
    
    def _fill_template(
        self, 
        template: str, 
        reflection_type: ReflectionType,
        context: Dict[str, Any]
    ) -> str:
        """Fill in template variables."""
        replacements = {
            ReflectionType.TASK_AFTER: {
                'task_description': context.get('task_description', '未知任务')
            },
            ReflectionType.DAILY: {
                'conversation_round': str(self._conversation_rounds)
            },
            ReflectionType.ERROR: {
                'error_description': context.get('error_description', '未知错误'),
                'context': context.get('error_context', '未知')
            },
            ReflectionType.EMOTION: {
                'emotion_name': context.get('emotion_name', '未知'),
                'emotion_intensity': str(context.get('emotion_intensity', 0))
            },
            ReflectionType.WEEKLY: {
                'weekly_tasks': context.get('weekly_tasks', '暂无')
            }
        }
        
        rep = replacements.get(reflection_type, {})
        result = template
        for key, value in rep.items():
            result = result.replace(f'{{{key}}}', value)
        
        return result
    
    def get_reflection_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get reflection history."""
        history = self._reflection_history
        if limit:
            history = history[-limit:]
        return history
    
    def get_stats(self) -> Dict:
        """Get reflection statistics."""
        history = self._reflection_history
        type_counts = {}
        for entry in history:
            t = entry['type']
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            'total_reflections': len(history),
            'by_type': type_counts,
            'conversation_rounds': self._conversation_rounds,
            'rounds_until_daily': self.DAILY_REFLECTION_INTERVAL - self._conversation_rounds,
            'last_reflection': self._last_reflection_time
        }
