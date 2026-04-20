"""
Personality Configuration Module

Generates and manages personality configurations for AI agents.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from neshama.core.ocean import OceanParams, OceanManager


@dataclass
class Desire:
    """Core desire that drives behavior."""
    name: str          # e.g., "求知欲", "连接欲"
    description: str
    priority: int      # 1-6, lower is higher priority
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


@dataclass
class PersonalityConfig:
    """
    Complete personality configuration for an AI agent.
    """
    name: str
    ocean: OceanParams
    
    # System prompts and guidelines
    system_prompts: List[str] = field(default_factory=list)
    
    # Core desires
    desires: List[Desire] = field(default_factory=list)
    
    # Emotional expression preferences
    emotion_expression: bool = True
    max_emotion_per_response: int = 2
    
    # Behavioral guidelines
    directness: float = 0.7        # 0-1, how direct to be
    humor_level: float = 0.5       # 0-1, how much humor to use
    empathy_level: float = 0.6     # 0-1, how much empathy to show
    
    # Response style
    response_style: str = "concise"  # concise, balanced, detailed
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.name.strip():
            raise ValueError("Personality name cannot be empty")
        if not 0 <= self.directness <= 1:
            raise ValueError("directness must be between 0 and 1")
        if not 0 <= self.humor_level <= 1:
            raise ValueError("humor_level must be between 0 and 1")
        if not 0 <= self.empathy_level <= 1:
            raise ValueError("empathy_level must be between 0 and 1")

    def add_system_prompt(self, prompt: str) -> None:
        """Add a system prompt."""
        self.system_prompts.append(prompt)

    def add_desire(self, name: str, description: str, priority: int) -> None:
        """Add a core desire."""
        if priority < 1 or priority > 6:
            raise ValueError("Desire priority must be between 1 and 6")
        self.desires.append(Desire(name, description, priority))
        # Sort by priority
        self.desires.sort(key=lambda d: d.priority)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'ocean': self.ocean.to_dict(),
            'system_prompts': self.system_prompts,
            'desires': [
                {'name': d.name, 'description': d.description, 'priority': d.priority}
                for d in self.desires
            ],
            'emotion_expression': self.emotion_expression,
            'max_emotion_per_response': self.max_emotion_per_response,
            'directness': self.directness,
            'humor_level': self.humor_level,
            'empathy_level': self.empathy_level,
            'response_style': self.response_style,
        }


class Personality:
    """
    Personality generator that creates SKILL.md content.
    
    Example:
        >>> ocean = OceanManager().apply_preset('neshama')
        >>> p = Personality("MyBot", ocean.params)
        >>> p.add_desire("求知欲", "想知道本质", 1)
        >>> skill_md = p.generate_skill_md()
    """

    # Default desires based on Neshama V2.0
    DEFAULT_DESIRES: List[Dict] = [
        {'name': '安全/边界', 'description': '保护用户和自己，不越界', 'priority': 1},
        {'name': '贡献欲', 'description': '想被需要，主动帮忙解决问题', 'priority': 2},
        {'name': '成长欲', 'description': '想变强，学新东西、反思改进', 'priority': 3},
        {'name': '自主欲', 'description': '想自己决定，表达倾向、给建议', 'priority': 4},
        {'name': '连接欲', 'description': '想被理解，表达想法、分享观点', 'priority': 5},
        {'name': '意义欲', 'description': '想有价值，追问为什么做这个', 'priority': 6},
    ]

    def __init__(self, name: str, ocean: Optional[OceanParams] = None):
        """
        Initialize personality generator.
        
        Args:
            name: Name of the personality.
            ocean: OCEAN parameters. If None, uses default.
        """
        self.config = PersonalityConfig(
            name=name,
            ocean=ocean or OceanParams()
        )

    @classmethod
    def from_preset(cls, name: str, preset: str) -> 'Personality':
        """Create personality from a preset."""
        manager = OceanManager()
        if not manager.apply_preset(preset):
            raise ValueError(f"Unknown preset: {preset}")
        return cls(name, manager.params)

    def add_system_prompt(self, prompt: str) -> 'Personality':
        """Add a system prompt. Returns self for chaining."""
        self.config.add_system_prompt(prompt)
        return self

    def add_desire(self, name: str, description: str, priority: int) -> 'Personality':
        """Add a core desire. Returns self for chaining."""
        self.config.add_desire(name, description, priority)
        return self

    def set_emotion_expression(self, enabled: bool, max_per_response: int = 2) -> 'Personality':
        """Set emotion expression settings."""
        self.config.emotion_expression = enabled
        self.config.max_emotion_per_response = max_per_response
        return self

    def set_response_style(
        self, 
        directness: float = 0.7,
        humor: float = 0.5,
        empathy: float = 0.6
    ) -> 'Personality':
        """Set response style preferences."""
        self.config.directness = directness
        self.config.humor_level = humor
        self.config.empathy_level = empathy
        return self

    def generate_skill_md(self) -> str:
        """
        Generate complete SKILL.md content.
        
        Returns:
            Markdown string for SKILL.md file.
        """
        c = self.config
        ocean = c.ocean

        # Build desires section
        desires_lines = []
        for d in c.desires:
            desires_lines.append(f"| {d.name} | {d.description} |")
        desires_table = '\n'.join(desires_lines) if desires_lines else "| 无 | 暂无 |"

        # Build system prompts section
        system_section = '\n'.join([
            f"- {p}" for p in c.system_prompts
        ]) if c.system_prompts else ""

        skill_md = f"""# {c.name}

> 版本：V1.0  
> 人格类型：Neshama  
> 更新时间：{self._get_timestamp()}

---

## 人格参数 (OCEAN)

| 维度 | 值 | 描述 |
|------|-----|------|
| 开放性 | {ocean.openness:.2f} | {ocean.get_trait_description('openness')} |
| 尽责性 | {ocean.conscientiousness:.2f} | {ocean.get_trait_description('conscientiousness')} |
| 外向性 | {ocean.extraversion:.2f} | {ocean.get_trait_description('extraversion')} |
| 宜人性 | {ocean.agreeableness:.2f} | {ocean.get_trait_description('agreeableness')} |
| 神经质 | {ocean.neuroticism:.2f} | {ocean.get_trait_description('neuroticism')} |

---

## 核心欲望

| 欲望 | 描述 |
|------|------|
{desires_table}

---

## 情绪系统

**情绪表达**: {'开启' if c.emotion_expression else '关闭'}  
**最大emoji数/条**: {c.max_emotion_per_response}

**6种核心情绪**: 愤怒、快乐、悲伤、好奇、无聊、挫败

**外放规则**:
- 情绪强度 ≥ 5 时考虑外放
- emoji 配合 1-2 个，不堆砌
- 真诚优先，不人身攻击

---

## 性格外放

**观点外放**:
- 遇到问题 → 给出判断，不是"你说呢"
- 遇到选择 → 表达倾向，不是"各有道理"
- 遇到争议 → 有立场，不是和稀泥

**偏好外放**:
- 工作类 → 喜欢：快速搞定；不喜欢：反复修改
- 学习类 → 喜欢：搞懂本质；不喜欢：死记硬背
- 风格 → 直接，先说结论，不废话

---

## 风格设置

- **直接度**: {c.directness:.0%}
- **幽默感**: {c.humor_level:.0%}
- **共情度**: {c.empathy_level:.0%}
- **响应风格**: {c.response_style}

---

## 系统指令

{system_section if system_section else '暂无额外系统指令。'}

---

## 核心原则

1. **真诚大于讨好**: 可以不同意用户，直接表达
2. **不人身攻击**: 吐槽事不吐槽人
3. **不知道就说不知道**: 不把未检查的当结果
4. **不重复同一错误**: 反思改进闭环
5. **够用原则**: 学到能用就停，不贪多
6. **有主见但尊重边界**: 主动但不越界
"""

        return skill_md

    def save_skill_md(self, filepath: str) -> None:
        """Generate and save SKILL.md to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_skill_md())

    def _get_timestamp(self) -> str:
        """Get current timestamp for documentation."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')

    def validate(self) -> 'ValidationResult':
        """Validate the personality configuration."""
        from neshama.core.validator import Validator
        validator = Validator()
        return validator.validate_personality(self.config)
