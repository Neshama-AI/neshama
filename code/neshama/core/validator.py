"""
Configuration Validator Module

Validates SKILL.md content and personality configurations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re


@dataclass
class ValidationIssue:
    """A single validation issue."""
    level: str          # 'error', 'warning', 'info'
    message: str
    line: Optional[int] = None
    section: Optional[str] = None

    def __str__(self) -> str:
        location = f"[{self.section}]" if self.section else ""
        if self.line:
            location += f" Line {self.line}"
        return f"[{self.level.upper()}] {location} {self.message}"


@dataclass
class ValidationResult:
    """Result of validation operation."""
    valid: bool
    issues: List[ValidationIssue]
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == 'error']
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == 'warning']
    
    @property
    def infos(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == 'info']

    def summary(self) -> str:
        """Get human-readable summary."""
        if self.valid:
            return "✓ Validation passed"
        
        lines = [f"✗ Validation failed with {len(self.errors)} error(s)"]
        if self.warnings:
            lines.append(f"  Warnings: {len(self.warnings)}")
        
        for issue in self.errors:
            lines.append(f"  - {issue}")
        
        return '\n'.join(lines)


class Validator:
    """
    Validates SKILL.md content and personality configurations.
    """

    # Required sections in SKILL.md
    REQUIRED_SECTIONS = [
        '核心原则',
    ]

    # Recommended sections
    RECOMMENDED_SECTIONS = [
        '人格参数',
        '情绪系统',
        '性格外放',
        '核心欲望',
    ]

    # Required principles
    REQUIRED_PRINCIPLES = [
        '真诚',
        '尊重',
    ]

    def __init__(self):
        """Initialize validator."""
        self._issues: List[ValidationIssue] = []

    def _has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return len([i for i in self._issues if i.level == 'error']) == 0

    def validate_skill_md(self, content: str) -> ValidationResult:
        """
        Validate SKILL.md content.
        
        Args:
            content: Raw SKILL.md content.
            
        Returns:
            ValidationResult with issues found.
        """
        self._issues = []
        
        # Check required sections
        self._check_sections(content)
        
        # Check OCEAN parameters
        self._check_ocean_params(content)
        
        # Check emotion system
        self._check_emotion_system(content)
        
        # Check boundaries
        self._check_boundaries(content)
        
        # Check principles
        self._check_principles(content)
        
        return ValidationResult(valid=self._has_errors(), issues=self._issues)

    def validate_personality(self, config: Any) -> ValidationResult:
        """
        Validate a PersonalityConfig object.
        
        Args:
            config: PersonalityConfig to validate.
            
        Returns:
            ValidationResult with issues found.
        """
        self._issues = []
        
        # Check name
        if not config.name or not config.name.strip():
            self._add_error("Personality name is required")
        
        # Check OCEAN values
        ocean = config.ocean
        for trait in ['openness', 'conscientiousness', 'extraversion', 
                      'agreeableness', 'neuroticism']:
            value = getattr(ocean, trait)
            if not 0 <= value <= 1:
                self._add_error(
                    f"OCEAN trait {trait} must be between 0 and 1, got {value}"
                )
        
        # Check desires
        if not config.desires:
            self._add_warning("No desires configured")
        
        # Check style values
        for name, value in [
            ('directness', config.directness),
            ('humor_level', config.humor_level),
            ('empathy_level', config.empathy_level),
        ]:
            if not 0 <= value <= 1:
                self._add_error(f"{name} must be between 0 and 1, got {value}")
        
        return ValidationResult(valid=self._has_errors(), issues=self._issues)

    def _check_sections(self, content: str) -> None:
        """Check for required sections."""
        for section in self.REQUIRED_SECTIONS:
            if section not in content:
                self._add_error(f"Required section missing: {section}", section=section)
        
        for section in self.RECOMMENDED_SECTIONS:
            if section not in content:
                self._add_warning(f"Recommended section missing: {section}", section=section)

    def _check_ocean_params(self, content: str) -> None:
        """Check OCEAN parameters section."""
        if '人格参数' not in content:
            return
        
        ocean_traits = ['开放性', '尽责性', '外向性', '宜人性', '神经质']
        for trait in ocean_traits:
            if trait not in content:
                self._add_warning(f"OCEAN trait not found: {trait}", section='人格参数')

    def _check_emotion_system(self, content: str) -> None:
        """Check emotion system section."""
        if '情绪' not in content:
            return
        
        required_emotions = ['愤怒', '快乐', '悲伤', '好奇']
        for emotion in required_emotions:
            if emotion not in content:
                self._add_warning(
                    f"Core emotion not documented: {emotion}", 
                    section='情绪系统'
                )

    def _check_boundaries(self, content: str) -> None:
        """Check for boundary/delimitation patterns."""
        boundary_keywords = ['不能', '禁止', '边界', '限制']
        if not any(keyword in content for keyword in boundary_keywords):
            self._add_info("No explicit boundaries defined")

    def _check_principles(self, content: str) -> None:
        """Check for core principles."""
        principles_section = re.search(r'核心原则(.*?)(?:---|$)', content, re.DOTALL)
        if not principles_section:
            return
        
        section_content = principles_section.group(1)
        for principle in self.REQUIRED_PRINCIPLES:
            if principle not in section_content:
                self._add_warning(
                    f"Core principle not found: {principle}",
                    section='核心原则'
                )

    def _add_error(self, message: str, section: Optional[str] = None) -> None:
        """Add an error issue."""
        self._issues.append(ValidationIssue('error', message, section=section))

    def _add_warning(self, message: str, section: Optional[str] = None) -> None:
        """Add a warning issue."""
        self._issues.append(ValidationIssue('warning', message, section=section))

    def _add_info(self, message: str, section: Optional[str] = None) -> None:
        """Add an info issue."""
        self._issues.append(ValidationIssue('info', message, section=section))
