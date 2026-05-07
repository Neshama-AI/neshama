# Soul Layer - Inspiration Engine Module
"""
Inspiration and Idea Generation

Features:
- Random inspiration triggers
- Idea brainstorming
- Constraint-based generation
- Divergent thinking support
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import random
import threading


@dataclass
class IdeaSeed:
    """An idea seed for creativity."""
    text: str
    category: str                    # e.g., "metaphor", "analogy", "perspective"
    novelty: float = 0.5              # 0-1, how novel/unique
    utility: float = 0.5              # 0-1, how useful/practical
    constraints: List[str] = field(default_factory=list)
    
    def score(self) -> float:
        """Combined score."""
        return (self.novelty + self.utility) / 2


# Inspiration prompts database
INSPIRATION_PROMPTS = [
    # Metaphors
    "What if {topic} was like a weather system?",
    "How would {topic} behave as a living creature?",
    "What machine does {topic} resemble?",
    "If {topic} was a color, what would it be?",
    
    # Perspectives
    "How would a child describe {topic}?",
    "How would an alien perceive {topic}?",
    "What would {topic} say about itself?",
    "What would a critic say about {topic}?",
    
    # Combinations
    "What if we combined {topic} with space exploration?",
    "How does {topic} connect to music?",
    "What ancient wisdom relates to {topic}?",
    "How would {topic} work in a post-scarcity society?",
    
    # Transformations
    "What if {topic} was 10x larger?",
    "What if {topic} was 100x faster?",
    "What if {topic} worked in reverse?",
    "What if {topic} was invisible?",
    
    # Absurd combinations
    "What would {topic} taste like?",
    "What sound does {topic} make?",
    "If {topic} was a sport, what would the rules be?",
    "What would be the anthem of {topic}?",
]

CREATIVITY_STYLES = {
    "explorer": {
        "novelty_weight": 0.8,
        "utility_weight": 0.2,
        "divergence": 0.9,
    },
    "builder": {
        "novelty_weight": 0.3,
        "utility_weight": 0.7,
        "divergence": 0.4,
    },
    "artist": {
        "novelty_weight": 0.9,
        "utility_weight": 0.1,
        "divergence": 0.95,
    },
    "pragmatist": {
        "novelty_weight": 0.2,
        "utility_weight": 0.8,
        "divergence": 0.2,
    },
}

# Global inspiration engine instance
inspiration_engine = None


class InspirationEngine:
    """
    Inspiration Engine.
    
    Generates creative ideas and inspiration.
    
    Example:
        >>> engine = InspirationEngine()
        >>> ideas = engine.generate("friendship", count=5)
        >>> for idea in ideas:
        ...     print(idea.text)
    """
    
    def __init__(
        self,
        style: str = "explorer",
        custom_prompts: Optional[List[str]] = None,
    ):
        """
        Initialize inspiration engine.
        
        Args:
            style: Creativity style (explorer, builder, artist, pragmatist)
            custom_prompts: Custom inspiration prompts
        """
        self._style = style
        self._prompts = custom_prompts or INSPIRATION_PROMPTS
        self._lock = threading.Lock()
        
        self._style_config = CREATIVITY_STYLES.get(style, CREATIVITY_STYLES["explorer"])
        
        # Track generated ideas to avoid repetition
        self._generated: List[str] = []
    
    def generate(
        self,
        topic: str,
        count: int = 5,
        category: Optional[str] = None,
    ) -> List[IdeaSeed]:
        """
        Generate creative ideas for a topic.
        
        Args:
            topic: Topic to generate ideas about
            count: Number of ideas to generate
            category: Filter by category (optional)
            
        Returns:
            List of IdeaSeed objects
        """
        with self._lock:
            ideas = []
            prompts = self._prompts.copy()
            
            # Shuffle for variety
            random.shuffle(prompts)
            
            for prompt_template in prompts:
                if len(ideas) >= count:
                    break
                
                try:
                    # Fill in topic
                    prompt = prompt_template.format(topic=topic)
                    
                    # Check for repetition
                    if prompt in self._generated:
                        continue
                    
                    # Determine category from prompt
                    if "like" in prompt or "resemble" in prompt:
                        cat = "metaphor"
                    elif "would" in prompt and ("child" in prompt or "alien" in prompt):
                        cat = "perspective"
                    elif "combined" in prompt or "connect" in prompt:
                        cat = "combination"
                    elif "x" in prompt or "reverse" in prompt or "invisible" in prompt:
                        cat = "transformation"
                    elif "taste" in prompt or "sound" in prompt or "sport" in prompt:
                        cat = "absurd"
                    else:
                        cat = "general"
                    
                    # Filter by category if specified
                    if category and cat != category:
                        continue
                    
                    idea = IdeaSeed(
                        text=prompt,
                        category=cat,
                        novelty=self._calculate_novelty(prompt),
                        utility=self._calculate_utility(prompt, topic),
                    )
                    
                    ideas.append(idea)
                    self._generated.append(prompt)
                    
                except KeyError:
                    # Template doesn't have {topic} placeholder
                    continue
            
            # Sort by combined score
            style_cfg = self._style_config
            ideas.sort(
                key=lambda x: (
                    x.novelty * style_cfg["novelty_weight"] +
                    x.utility * style_cfg["utility_weight"]
                ),
                reverse=True
            )
            
            return ideas[:count]
    
    def _calculate_novelty(self, idea: str) -> float:
        """Calculate novelty score for an idea."""
        # Base novelty
        novelty = 0.5
        
        # Boost for absurd/unusual combinations
        unusual_words = ["alien", "invisible", "reverse", "taste", "sound", "sport"]
        if any(word in idea.lower() for word in unusual_words):
            novelty += 0.2
        
        # Boost for perspective-taking
        perspective_words = ["child", "alien", "critic", "itself"]
        if any(word in idea.lower() for word in perspective_words):
            novelty += 0.15
        
        # Reduce for common patterns
        if "what if" not in idea.lower():
            novelty -= 0.1
        
        return max(0.1, min(1.0, novelty))
    
    def _calculate_utility(self, idea: str, topic: str) -> float:
        """Calculate utility score for an idea."""
        # Base utility
        utility = 0.5
        
        # Boost for practical combinations
        practical_words = ["combine", "connect", "work", "society"]
        if any(word in idea.lower() for word in practical_words):
            utility += 0.15
        
        # Reduce for purely absurd
        absurd_words = ["taste", "sound", "sport", "anthem"]
        if any(word in idea.lower() for word in absurd_words):
            utility -= 0.2
        
        return max(0.1, min(1.0, utility))
    
    def set_style(self, style: str):
        """Change creativity style."""
        if style in CREATIVITY_STYLES:
            self._style = style
            self._style_config = CREATIVITY_STYLES[style]
    
    def add_prompt(self, prompt_template: str):
        """Add a custom prompt template."""
        self._prompts.append(prompt_template)
    
    def clear_history(self):
        """Clear generated idea history."""
        self._generated = []


def get_inspiration_engine() -> InspirationEngine:
    """Get or create global inspiration engine instance."""
    global inspiration_engine
    if inspiration_engine is None:
        inspiration_engine = InspirationEngine()
    return inspiration_engine


def generate_ideas(topic: str, count: int = 5, **kwargs) -> List[IdeaSeed]:
    """Convenience function to generate ideas."""
    return get_inspiration_engine().generate(topic, count, **kwargs)
