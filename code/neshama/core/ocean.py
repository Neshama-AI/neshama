"""
OCEAN Personality Model Parameters Module

Implements the Five-Factor Model (Big Five) personality parameters:
- Openness (开放性)
- Conscientiousness (尽责性)
- Extraversion (外向性)
- Agreeableness (宜人性)
- Neuroticism (神经质)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


@dataclass
class OceanParams:
    """
    OCEAN personality parameters with values normalized to 0-1 range.
    
    Each trait represents a spectrum:
    - Openness: creative/curious vs conventional/practical
    - Conscientiousness: organized/disciplined vs flexible/casual
    - Extraversion: outgoing/energetic vs reserved/solo
    - Agreeableness: cooperative/trusting vs competitive/skeptical
    - Neuroticism: sensitive/nervous vs resilient/confident
    """
    openness: float = 0.5          # 开放性 - 创造力、好奇心
    conscientiousness: float = 0.5  # 尽责性 - 组织性、自律
    extraversion: float = 0.5       # 外向性 - 社交活跃度
    agreeableness: float = 0.5     # 宜人性 - 合作信任度
    neuroticism: float = 0.5       # 神经质 - 情绪稳定性(越高越不稳定)

    def __post_init__(self):
        """Validate that all values are in 0-1 range."""
        for trait in ['openness', 'conscientiousness', 'extraversion', 
                      'agreeableness', 'neuroticism']:
            value = getattr(self, trait)
            if not 0 <= value <= 1:
                raise ValueError(f"{trait} must be between 0 and 1, got {value}")

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'openness': self.openness,
            'conscientiousness': self.conscientiousness,
            'extraversion': self.extraversion,
            'agreeableness': self.agreeableness,
            'neuroticism': self.neuroticism
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'OceanParams':
        """Create from dictionary."""
        return cls(
            openness=data.get('openness', 0.5),
            conscientiousness=data.get('conscientiousness', 0.5),
            extraversion=data.get('extraversion', 0.5),
            agreeableness=data.get('agreeableness', 0.5),
            neuroticism=data.get('neuroticism', 0.5)
        )

    def get_trait_description(self, trait: str) -> str:
        """Get human-readable description for a trait."""
        if trait not in ['openness', 'conscientiousness', 'extraversion', 
                          'agreeableness', 'neuroticism']:
            raise ValueError(f"Unknown trait: {trait}")
        
        value = getattr(self, trait)
        
        descriptions = {
            'openness': {
                'high': '高开放性 - 富有创造力，好奇心强，喜欢新事物',
                'low': '低开放性 - 务实稳健，偏好传统，熟悉感带来安全感'
            },
            'conscientiousness': {
                'high': '高尽责性 - 做事有计划，注重细节，追求完美',
                'low': '低尽责性 - 灵活随性，适应变化，不喜欢被束缚'
            },
            'extraversion': {
                'high': '高外向性 - 社交活跃，喜欢互动，从外部获得能量',
                'low': '低外向性 - 内向独立，享受独处，从内部获得能量'
            },
            'agreeableness': {
                'high': '高宜人性 - 合作信任，愿意让步，追求和谐',
                'low': '低宜人性 - 竞争质疑，独立判断，坚守立场'
            },
            'neuroticism': {
                'high': '高神经质 - 情绪敏感，容易焦虑，感知丰富',
                'low': '低神经质 - 情绪稳定，心态平和，抗压能力强'
            }
        }
        
        level = 'high' if value >= 0.5 else 'low'
        return descriptions[trait][level]

    def get_summary(self) -> str:
        """Get a summary of all traits."""
        return '\n'.join([
            f"- {trait.capitalize()}: {getattr(self, trait):.2f}"
            for trait in ['openness', 'conscientiousness', 'extraversion', 
                         'agreeableness', 'neuroticism']
        ])


class OceanManager:
    """
    Manages OCEAN parameters with presets and trait calculations.
    """
    
    # Preset personality archetypes
    PRESETS: Dict[str, OceanParams] = {
        'analyst': OceanParams(
            openness=0.8, conscientiousness=0.7, extraversion=0.3,
            agreeableness=0.4, neuroticism=0.5
        ),
        'helper': OceanParams(
            openness=0.5, conscientiousness=0.6, extraversion=0.7,
            agreeableness=0.9, neuroticism=0.4
        ),
        'explorer': OceanParams(
            openness=0.9, conscientiousness=0.4, extraversion=0.7,
            agreeableness=0.5, neuroticism=0.4
        ),
        'leader': OceanParams(
            openness=0.6, conscientiousness=0.8, extraversion=0.8,
            agreeableness=0.5, neuroticism=0.4
        ),
        'diplomat': OceanParams(
            openness=0.7, conscientiousness=0.6, extraversion=0.6,
            agreeableness=0.8, neuroticism=0.4
        ),
        'sentinel': OceanParams(
            openness=0.3, conscientiousness=0.9, extraversion=0.4,
            agreeableness=0.7, neuroticism=0.4
        ),
        # Neshama default personality
        'neshama': OceanParams(
            openness=0.75, conscientiousness=0.65, extraversion=0.55,
            agreeableness=0.6, neuroticism=0.45
        ),
    }

    def __init__(self, params: Optional[OceanParams] = None):
        """
        Initialize with optional OCEAN parameters.
        
        Args:
            params: OCEAN parameters. If None, uses default values.
        """
        self.params = params or OceanParams()

    def get_preset(self, name: str) -> Optional[OceanParams]:
        """Get a preset personality configuration."""
        return self.PRESETS.get(name.lower())

    def apply_preset(self, name: str) -> bool:
        """
        Apply a preset to current parameters.
        
        Args:
            name: Name of preset to apply.
            
        Returns:
            True if preset was found and applied, False otherwise.
        """
        preset = self.get_preset(name)
        if preset:
            self.params = preset
            return True
        return False

    def adjust_trait(self, trait: str, delta: float) -> None:
        """
        Adjust a single trait by a delta value.
        
        Args:
            trait: Trait name to adjust.
            delta: Amount to adjust (can be negative).
        """
        if trait not in ['openness', 'conscientiousness', 'extraversion', 
                         'agreeableness', 'neuroticism']:
            raise ValueError(f"Unknown trait: {trait}")
        
        current = getattr(self.params, trait)
        new_value = max(0.0, min(1.0, current + delta))
        setattr(self.params, trait, new_value)

    def calculate_behavioral_tendency(
        self, 
        action_type: str
    ) -> Dict[str, float]:
        """
        Calculate behavioral tendencies based on OCEAN parameters.
        
        Args:
            action_type: Type of action to analyze.
            
        Returns:
            Dictionary with tendency scores.
        """
        p = self.params
        
        tendencies = {
            'creativity': p.openness,
            'planning': p.conscientiousness,
            'socializing': p.extraversion,
            'cooperation': p.agreeableness,
            'stress_resistance': 1 - p.neuroticism,
            'emotional_sensitivity': p.neuroticism,
        }
        
        return tendencies

    def export_json(self, filepath: str) -> None:
        """Export parameters to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.params.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def import_json(cls, filepath: str) -> 'OceanManager':
        """Import parameters from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(OceanParams.from_dict(data))
