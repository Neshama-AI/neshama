# Soul Layer - NPC Dialogue Engine
"""
NPCDialogueEngine - Generates dialogues between two NPCs.

Features:
- LLM-based dialogue generation
- Context-aware conversations
- Multi-turn dialogue support
- Dialogue summarization and memory storage

Design:
- Uses LLM for natural dialogue generation
- Constructs rich context from NPC state
- Limits tokens (personality < 200 tokens, history < 500 tokens)
- Each turn tagged with speaker

Example:
    >>> engine = NPCDialogueEngine()
    >>> dialogue = engine.generate_dialogue("alice", "bob", "news", {})
    >>> for turn in dialogue.turns:
    ...     print(f"{turn.speaker}: {turn.content}")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import threading
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)


class DialogueTrigger(Enum):
    """What triggered the dialogue."""
    AUTONOMOUS = "autonomous"         # NPCs initiated themselves
    PLAYER_TRIGGERED = "player_triggered"  # Player caused this
    WORLD_EVENT = "world_event"       # World event triggered it
    INFORMATION_SPREAD = "information_spread"  # Info propagation triggered


@dataclass
class DialogueTurn:
    """A single turn in a dialogue."""
    turn_id: str
    dialogue_id: str
    speaker_id: str       # NPC ID
    speaker_name: str     # Display name
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    emotion_hint: Optional[str] = None  # Suggested emotion for display
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "dialogue_id": self.dialogue_id,
            "speaker_id": self.speaker_id,
            "speaker_name": self.speaker_name,
            "content": self.content,
            "timestamp": self.timestamp,
            "emotion_hint": self.emotion_hint,
        }


@dataclass
class Dialogue:
    """A complete dialogue between two NPCs."""
    dialogue_id: str
    npc_a_id: str
    npc_b_id: str
    npc_a_name: str
    npc_b_name: str
    topic: str
    trigger: DialogueTrigger
    turns: List[DialogueTurn] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    summary: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dialogue_id": self.dialogue_id,
            "npc_a_id": self.npc_a_id,
            "npc_b_id": self.npc_b_id,
            "npc_a_name": self.npc_a_name,
            "npc_b_name": self.npc_b_name,
            "topic": self.topic,
            "trigger": self.trigger.value,
            "turns": [t.to_dict() for t in self.turns],
            "turn_count": len(self.turns),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "summary": self.summary,
            "context": self.context,
        }


@dataclass
class NPCDialogueContext:
    """Context about an NPC for dialogue generation."""
    npc_id: str
    name: str
    personality: Dict[str, float]  # OCEAN
    emotions: Dict[str, float]
    relationship: Optional[Dict[str, Any]]
    known_info: List[str]  # Info snippets they know
    recent_interactions: List[str]  # Recent social events
    session_location: Optional[str] = None
    
    def to_prompt_text(self, max_tokens: int = 200) -> str:
        """Convert to condensed text for prompt (limited tokens)."""
        lines = [f"Name: {self.name}"]
        
        # Personality summary (condensed)
        traits = []
        for trait, value in self.personality.items():
            if value > 0.7:
                traits.append(f"high {trait}")
            elif value < 0.3:
                traits.append(f"low {trait}")
        if traits:
            lines.append(f"Personality: {', '.join(traits[:3])}")
        
        # Emotion summary
        if self.emotions:
            dominant = max(self.emotions.items(), key=lambda x: x[1]) if self.emotions else None
            if dominant and dominant[1] > 0.5:
                lines.append(f"Current emotion: {dominant[0]} ({dominant[1]:.1f})")
        
        # Relationship summary
        if self.relationship:
            rel = self.relationship
            strength = rel.get("strength", 0.5)
            trust = rel.get("trust", 0.5)
            lines.append(f"Relationship: {rel.get('category', 'neutral')} (trust: {trust:.1f})")
        
        # Truncate to token limit
        text = "; ".join(lines)
        if len(text) > max_tokens * 4:  # Rough token estimate
            text = text[:max_tokens * 4] + "..."
        return text


class NPCDialogueEngine:
    """
    Generates dialogues between two NPCs using LLM.
    
    Features:
    - Generate multi-turn dialogues
    - Rich context from NPC states
    - Continue existing dialogues
    - Summarize and store in memory
    
    Example:
        >>> engine = NPCDialogueEngine()
        >>> dialogue = engine.generate_dialogue(
        ...     "alice", "bob",
        ...     "Did you hear about the dragon?",
        ...     {}
        ... )
    """
    
    # Token limits
    MAX_PERSONALITY_TOKENS = 200
    MAX_HISTORY_TOKENS = 500
    MAX_TURNS = 10
    
    # Model settings
    DEFAULT_MODEL = "gpt-4"
    TEMPERATURE = 0.8
    
    def __init__(self, model_adapter=None):
        """
        Initialize NPCDialogueEngine.
        
        Args:
            model_adapter: Optional model adapter for LLM calls
        """
        self._model_adapter = model_adapter
        
        # Dialogue storage: dialogue_id -> Dialogue
        self._dialogues: Dict[str, Dialogue] = {}
        
        # Active dialogue tracking
        self._active_by_npc: Dict[str, Set[str]] = {}  # npc_id -> set of dialogue_ids
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Callbacks for WS notifications
        self._on_dialogue_update: Optional[callable] = None
        
        logger.info("NPCDialogueEngine initialized")
    
    def set_model_adapter(self, adapter):
        """Set model adapter for LLM calls."""
        self._model_adapter = adapter
    
    def set_ws_callback(self, callback: callable):
        """Set WebSocket notification callback."""
        self._on_dialogue_update = callback
    
    def _get_npc_context(
        self,
        npc_id: str,
        social_engine=None,
        information_propagator=None,
    ) -> NPCDialogueContext:
        """Get dialogue context for an NPC."""
        # Get NPC data from manager
        from neshama.soul.npc_manager import get_npc_manager
        
        manager = get_npc_manager()
        soul = manager.get_npc(npc_id)
        
        if not soul:
            # Create minimal context
            return NPCDialogueContext(
                npc_id=npc_id,
                name=npc_id,
                personality={},
                emotions={},
                relationship=None,
                known_info=[],
                recent_interactions=[],
            )
        
        # Get relationship if social engine provided
        relationship = None
        if social_engine:
            rel = social_engine.get_relation(npc_id, npc_id)  # This will be set properly
            if rel:
                relationship = rel.to_dict()
        
        # Get known info if propagator provided
        known_info = []
        if information_propagator:
            knowledge = information_propagator.get_npc_knowledge(npc_id, limit=5)
            known_info = [i["content"][:100] for i in knowledge.known_info]
        
        return NPCDialogueContext(
            npc_id=npc_id,
            name=soul.name,
            personality=soul.personality.to_dict(),
            emotions=soul.current_emotions,
            relationship=relationship,
            known_info=known_info,
            recent_interactions=[],
        )
    
    def _build_system_prompt(self, context_a: NPCDialogueContext, context_b: NPCDialogueContext) -> str:
        """Build system prompt for dialogue generation."""
        return f"""You are generating a natural dialogue between two NPCs in a fantasy game world.

CONTEXT:
- {context_a.to_prompt_text(self.MAX_PERSONALITY_TOKENS)}
- {context_b.to_prompt_text(self.MAX_PERSONALITY_TOKENS)}

RULES:
1. Each response should be from ONE speaker only
2. Format: "[SpeakerName]: dialogue content"
3. Keep responses natural and in character
4. Reference their relationship and emotions when appropriate
5. Conversations should feel authentic to NPCs, not like AI outputs
6. Max 2-3 sentences per turn

Generate the dialogue:"""
    
    def _build_dialogue_prompt(
        self,
        context_a: NPCDialogueContext,
        context_b: NPCDialogueContext,
        topic: str,
        history: List[DialogueTurn],
        turn_count: int = 2,
    ) -> str:
        """Build prompt for dialogue generation."""
        prompt_parts = []
        
        # Context summary
        prompt_parts.append(f"Topic: {topic}")
        prompt_parts.append(f"\nNPC A ({context_a.name}): {context_a.to_prompt_text()}")
        prompt_parts.append(f"NPC B ({context_b.name}): {context_b.to_prompt_text()}")
        
        # History (limited)
        if history:
            history_text = []
            for turn in history[-6:]:  # Last 6 turns
                history_text.append(f"{turn.speaker_name}: {turn.content}")
            prompt_parts.append("\nRecent conversation:")
            prompt_parts.append("\n".join(history_text))
        
        prompt_parts.append(f"\nGenerate {turn_count} more exchanges (alternating speakers):")
        
        return "\n".join(prompt_parts)
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for dialogue generation."""
        if self._model_adapter:
            response = await self._model_adapter.generate(
                prompt=prompt,
                model=self.DEFAULT_MODEL,
                temperature=self.TEMPERATURE,
                max_tokens=300,
            )
            return response
        else:
            # Fallback: return placeholder
            return f"[LLM not configured - dialogue placeholder]"
    
    def generate_dialogue(
        self,
        npc_a_id: str,
        npc_b_id: str,
        topic: str,
        context: Optional[Dict[str, Any]] = None,
        trigger: DialogueTrigger = DialogueTrigger.PLAYER_TRIGGERED,
        social_engine=None,
        information_propagator=None,
        max_turns: int = 4,
    ) -> Dialogue:
        """
        Generate a dialogue between two NPCs.
        
        Args:
            npc_a_id: First NPC ID
            npc_b_id: Second NPC ID
            topic: Topic/subject of conversation
            context: Additional context
            trigger: What triggered this dialogue
            social_engine: Optional social engine for relationship context
            information_propagator: Optional propagator for shared knowledge
            max_turns: Maximum turns to generate
            
        Returns:
            Dialogue object with generated turns
        """
        # Get NPC contexts
        context_a = self._get_npc_context(npc_a_id, social_engine, information_propagator)
        context_b = self._get_npc_context(npc_b_id, social_engine, information_propagator)
        
        # Override names if available
        context_a.name = context_a.name or npc_a_id
        context_b.name = context_b.name or npc_b_id
        
        # Create dialogue
        dialogue_id = str(uuid.uuid4())
        dialogue = Dialogue(
            dialogue_id=dialogue_id,
            npc_a_id=npc_a_id,
            npc_b_id=npc_b_id,
            npc_a_name=context_a.name,
            npc_b_name=context_b.name,
            topic=topic,
            trigger=trigger,
            context=context or {},
        )
        
        # Store
        with self._lock:
            self._dialogues[dialogue_id] = dialogue
            self._active_by_npc.setdefault(npc_a_id, set()).add(dialogue_id)
            self._active_by_npc.setdefault(npc_b_id, set()).add(dialogue_id)
        
        # Generate turns using asyncio.run() for compatibility
        try:
            turns = asyncio.run(
                self._generate_turns(dialogue, context_a, context_b, max_turns)
            )
        except RuntimeError:
            # Already in async context, use create_task
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a new event loop in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        turns = pool.submit(
                            asyncio.run,
                            self._generate_turns(dialogue, context_a, context_b, max_turns)
                        ).result()
                else:
                    turns = loop.run_until_complete(
                        self._generate_turns(dialogue, context_a, context_b, max_turns)
                    )
            except Exception:
                # Fallback: return empty turns
                turns = []
        
        dialogue.turns = turns
        dialogue.updated_at = datetime.now().isoformat()
        
        logger.info(f"Generated dialogue {dialogue_id}: {len(turns)} turns")
        return dialogue
    
    async def _generate_turns(
        self,
        dialogue: Dialogue,
        context_a: NPCDialogueContext,
        context_b: NPCDialogueContext,
        max_turns: int,
    ) -> List[DialogueTurn]:
        """Generate dialogue turns asynchronously."""
        turns = []
        
        # Build initial prompt
        prompt = self._build_dialogue_prompt(
            context_a, context_b,
            dialogue.topic,
            [],
            turn_count=min(max_turns, 4),
        )
        
        # Call LLM
        response = await self._call_llm(prompt)
        
        # Parse response into turns
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            
            # Parse "[Speaker]: content" format
            try:
                speaker_part, content = line.split(":", 1)
                speaker_part = speaker_part.strip()
                content = content.strip()
                
                if not content:
                    continue
                
                # Determine which NPC
                if speaker_part.lower() in [context_a.name.lower(), "npc a"]:
                    speaker_id = context_a.npc_id
                    speaker_name = context_a.name
                else:
                    speaker_id = context_b.npc_id
                    speaker_name = context_b.name
                
                turn = DialogueTurn(
                    turn_id=str(uuid.uuid4()),
                    dialogue_id=dialogue.dialogue_id,
                    speaker_id=speaker_id,
                    speaker_name=speaker_name,
                    content=content,
                )
                turns.append(turn)
                
            except ValueError:
                continue
        
        return turns
    
    def continue_dialogue(
        self,
        dialogue_id: str,
        max_turns: int = 2,
        social_engine=None,
        information_propagator=None,
    ) -> Dialogue:
        """
        Continue an existing dialogue.
        
        Args:
            dialogue_id: Dialogue to continue
            max_turns: Number of new turns to add
            social_engine: Optional social engine
            information_propagator: Optional propagator
            
        Returns:
            Updated dialogue
        """
        dialogue = self._dialogues.get(dialogue_id)
        if not dialogue:
            raise ValueError(f"Dialogue {dialogue_id} not found")
        
        # Get NPC contexts
        context_a = self._get_npc_context(dialogue.npc_a_id, social_engine, information_propagator)
        context_b = self._get_npc_context(dialogue.npc_b_id, social_engine, information_propagator)
        
        # Generate more turns
        try:
            turns = asyncio.run(
                self._generate_turns(dialogue, context_a, context_b, max_turns)
            )
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        turns = pool.submit(
                            asyncio.run,
                            self._generate_turns(dialogue, context_a, context_b, max_turns)
                        ).result()
                else:
                    turns = loop.run_until_complete(
                        self._generate_turns(dialogue, context_a, context_b, max_turns)
                    )
            except Exception:
                turns = []
        
        # Add turns
        with self._lock:
            dialogue.turns.extend(turns)
            dialogue.updated_at = datetime.now().isoformat()
        
        logger.info(f"Continued dialogue {dialogue_id}: {len(turns)} new turns")
        return dialogue
    
    def summarize_dialogue(self, dialogue_id: str) -> Optional[str]:
        """
        Summarize a dialogue and store in memory.
        
        Args:
            dialogue_id: Dialogue to summarize
            
        Returns:
            Summary text
        """
        dialogue = self._dialogues.get(dialogue_id)
        if not dialogue:
            return None
        
        # Build summary from turns
        turn_texts = [f"{t.speaker_name}: {t.content}" for t in dialogue.turns]
        summary = f"Conversation between {dialogue.npc_a_name} and {dialogue.npc_b_name} about {dialogue.topic}. "
        summary += " | ".join(turn_texts[:5])  # First 5 exchanges
        
        dialogue.summary = summary
        
        # Could store in NPC memory here
        # For now, just return
        
        return summary
    
    def get_dialogue(self, dialogue_id: str) -> Optional[Dialogue]:
        """Get a dialogue by ID."""
        return self._dialogues.get(dialogue_id)
    
    def get_active_dialogues(self, npc_id: str) -> List[Dialogue]:
        """Get all active dialogues for an NPC."""
        with self._lock:
            dialogue_ids = self._active_by_npc.get(npc_id, set())
            return [
                self._dialogues[did]
                for did in dialogue_ids
                if did in self._dialogues
            ]
    
    def get_dialogue_history(
        self,
        npc_a_id: str,
        npc_b_id: str,
        limit: int = 10,
    ) -> List[Dialogue]:
        """Get dialogue history between two NPCs."""
        dialogues = [
            d for d in self._dialogues.values()
            if (d.npc_a_id == npc_a_id and d.npc_b_id == npc_b_id) or
               (d.npc_a_id == npc_b_id and d.npc_b_id == npc_a_id)
        ]
        
        # Sort by creation time, newest first
        dialogues.sort(key=lambda d: d.created_at, reverse=True)
        return dialogues[:limit]
    
    def get_recent_dialogues(self, limit: int = 20) -> List[Dialogue]:
        """Get most recent dialogues."""
        dialogues = sorted(
            self._dialogues.values(),
            key=lambda d: d.updated_at,
            reverse=True
        )
        return dialogues[:limit]


# Global instance
_dialogue_engine: Optional[NPCDialogueEngine] = None


def get_dialogue_engine() -> NPCDialogueEngine:
    """Get the global dialogue engine instance."""
    global _dialogue_engine
    if _dialogue_engine is None:
        _dialogue_engine = NPCDialogueEngine()
    return _dialogue_engine
