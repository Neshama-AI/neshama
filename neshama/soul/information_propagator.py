# Soul Layer - Information Propagator
"""
InformationPropagator - NPC gossip and information sharing system.

Features:
- Information spread between NPCs (player actions, world events, secrets)
- Information distortion (rumors change over time)
- Trust-based propagation
- Information decay and forgetting
- Propagation chain tracking

Design:
This is the core differentiator from Inworld/Convai - when a player does something,
NPCs talk to each other and the information spreads through the social network.

Example:
    >>> propagator = InformationPropagator()
    >>> propagator.spread_information("tavern_keeper", "PLAYER_ACTION", 
    ...     "The adventurer stole from the merchant", ["guard_captain", "blacksmith"])
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import threading
import uuid
import random
import logging

logger = logging.getLogger(__name__)


class InformationType(Enum):
    """Types of information that can spread."""
    PLAYER_ACTION = "player_action"   # Player did something
    WORLD_EVENT = "world_event"      # Something happened in the world
    NPC_SECRET = "npc_secret"         # Private NPC information
    QUEST_INFO = "quest_info"         # Quest-related info
    RUMOR = "rumor"                   # Unverified information


@dataclass
class Information:
    """A piece of information that can spread."""
    info_id: str
    info_type: InformationType
    original_content: str
    current_content: str             # May be distorted
    source_npc_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_spread: Optional[str] = None
    distortion_level: float = 0.0    # 0 = original, 1 = heavily distorted
    credibility: float = 1.0         # Based on source trust
    importance: float = 0.5          # How important this info is
    seen_by: List[str] = field(default_factory=list)  # NPCs who know this
    propagation_count: int = 0
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "info_id": self.info_id,
            "info_type": self.info_type.value,
            "original_content": self.original_content,
            "current_content": self.current_content,
            "source_npc_id": self.source_npc_id,
            "created_at": self.created_at,
            "last_spread": self.last_spread,
            "distortion_level": round(self.distortion_level, 4),
            "credibility": round(self.credibility, 4),
            "importance": round(self.importance, 4),
            "seen_by": self.seen_by,
            "propagation_count": self.propagation_count,
            "tags": self.tags,
        }


@dataclass
class PropagationChain:
    """Chain of NPCs who spread information."""
    info_id: str
    chain: List[Dict[str, str]] = field(default_factory=list)  # [{npc_id, timestamp, action}]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "info_id": self.info_id,
            "chain": self.chain,
        }


@dataclass
class NPCKnowledge:
    """What an NPC knows."""
    npc_id: str
    known_info: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "known_info": self.known_info,
            "last_updated": self.last_updated,
            "info_count": len(self.known_info),
        }


class InformationPropagator:
    """
    Manages information propagation between NPCs.
    
    Features:
    - Spread information from source to targets
    - Track information distortion (rumors change)
    - Trust-based credibility calculation
    - Information decay over time
    - Propagation chain tracking
    
    Example:
        >>> propagator = InformationPropagator()
        >>> result = propagator.spread_information(
        ...     "npc_alice", "PLAYER_ACTION",
        ...     "The adventurer killed the dragon!",
        ...     ["npc_bob", "npc_charlie"]
        ... )
        >>> knowledge = propagator.get_npc_knowledge("npc_bob")
    """
    
    # Propagation settings
    DISTORTION_CHANCE = 0.15          # Per-hop chance of distortion
    DISTORTION_AMOUNT = 0.1           # How much content changes per distortion
    DECAY_RATE = 0.001                # Importance decay per second
    MIN_IMPORTANCE = 0.1              # Below this, info is forgotten
    
    # Credibility settings
    TRUST_DECAY_PER_HOP = 0.1         # Trust decreases per propagation step
    SOURCE_TRUST_MULTIPLIER = 0.5     # How much source trust affects info
    
    def __init__(self):
        """Initialize InformationPropagator."""
        # Information storage: info_id -> Information
        self._information: Dict[str, Information] = {}
        
        # NPC knowledge: npc_id -> list of info_ids
        self._npc_knowledge: Dict[str, Set[str]] = {}
        
        # Propagation chains: info_id -> PropagationChain
        self._propagation_chains: Dict[str, PropagationChain] = {}
        
        # Social engine reference (optional)
        self._social_engine = None
        
        # Emotion update callback (optional): callable(npc_id, emotion_deltas)
        self._emotion_callback = None
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        logger.info("InformationPropagator initialized")
    
    def set_social_engine(self, engine):
        """Set social engine for trust-based propagation."""
        self._social_engine = engine
    
    def set_emotion_callback(self, callback):
        """Set emotion update callback for when NPCs receive information.
        
        Args:
            callback: callable(npc_id: str, emotion_deltas: Dict[str, float])
                      Called when information spreads to an NPC, providing
                      emotion deltas the NPC should experience.
        """
        self._emotion_callback = callback
    
    def _get_trust(self, from_npc: str, to_npc: str) -> float:
        """Get trust level between two NPCs."""
        if self._social_engine:
            relation = self._social_engine.get_relation(from_npc, to_npc)
            if relation:
                return relation.trust
        return 0.5  # Default moderate trust
    
    def spread_information(
        self,
        source_npc_id: str,
        info_type: str,
        content: str,
        targets: List[str],
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        info_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Spread information from source NPC to target NPCs.
        
        Args:
            source_npc_id: Who originally knows/created this info
            info_type: Type of information (from InformationType)
            content: The information content
            targets: List of NPC IDs to spread to
            importance: How important this info is (0-1)
            tags: Optional tags for categorization
            info_id: Optional existing info ID to propagate further
            
        Returns:
            Spread result with details
        """
        with self._lock:
            # Parse info type
            try:
                info_type_enum = InformationType(info_type)
            except ValueError:
                info_type_enum = InformationType.RUMOR
            
            # Create or get information
            if info_id and info_id in self._information:
                info = self._information[info_id]
                # Propagate existing info
                info.last_spread = datetime.now().isoformat()
                info.propagation_count += 1
            else:
                # New information
                info_id = info_id or str(uuid.uuid4())
                info = Information(
                    info_id=info_id,
                    info_type=info_type_enum,
                    original_content=content,
                    current_content=content,
                    source_npc_id=source_npc_id,
                    importance=importance,
                    tags=tags or [],
                )
                self._information[info_id] = info
                self._propagation_chains[info_id] = PropagationChain(info_id=info_id)
                
                # Source knows the info
                self._add_to_npc_knowledge(source_npc_id, info_id)
                
                logger.debug(f"Created info {info_id}: {content[:50]}...")
            
            # Spread to targets
            spread_results = []
            for target_id in targets:
                if target_id == source_npc_id:
                    continue
                
                # Get trust between source and target
                trust = self._get_trust(source_npc_id, target_id)
                
                # Calculate if info actually spreads
                # Higher trust = higher chance of spread
                # Higher importance = higher chance
                spread_chance = (trust * 0.7) + (importance * 0.3)
                
                if random.random() > spread_chance:
                    spread_results.append({
                        "target": target_id,
                        "success": False,
                        "reason": "low_trust",
                    })
                    continue
                
                # Apply distortion if RUMOR type
                final_content = info.current_content
                if info_type_enum == InformationType.RUMOR:
                    final_content, distortion = self._apply_distortion(
                        info.current_content,
                        info.distortion_level,
                        trust,
                    )
                    info.distortion_level = min(1.0, info.distortion_level + distortion)
                    info.current_content = final_content
                
                # Update credibility
                info.credibility = max(0.1, info.credibility - self.TRUST_DECAY_PER_HOP)
                
                # Add to target's knowledge
                self._add_to_npc_knowledge(target_id, info_id)
                
                # Record in propagation chain
                self._propagation_chains[info_id].chain.append({
                    "npc_id": target_id,
                    "timestamp": datetime.now().isoformat(),
                    "action": "received",
                    "from": source_npc_id,
                })
                
                spread_results.append({
                    "target": target_id,
                    "success": True,
                    "content": final_content,
                    "credibility": info.credibility,
                })
                
                # Trigger emotion update for target NPC based on info content
                self._trigger_emotion_reaction(
                    target_id, info_type_enum, final_content,
                    info.credibility, importance, source_npc_id,
                )
                
                logger.debug(f"Spread to {target_id}: {final_content[:50]}...")
            
            return {
                "info_id": info_id,
                "info_type": info_type,
                "spread_to": spread_results,
                "propagation_count": info.propagation_count,
                "total_knowers": len(info.seen_by),
            }
    
    def _apply_distortion(
        self,
        content: str,
        current_distortion: float,
        trust: float,
    ) -> Tuple[str, float]:
        """
        Apply distortion to content (rumors change over time).
        
        Distortion types:
        - Exaggeration: Make it bigger/more dramatic
        - Simplification: Remove details
        - Misattribution: Change who did it
        - Inversion: Change meaning
        """
        # Check if distortion occurs
        distort_chance = self.DISTORTION_CHANCE * (1 - trust)
        if random.random() > distort_chance:
            return content, 0.0
        
        # Distortion types
        distortion_type = random.choice(["exaggerate", "simplify", "misattribute", "partial"])
        
        words = content.split()
        
        if distortion_type == "exaggerate" and len(words) > 5:
            # Add intensifier or dramatic element
            intensifiers = ["apparently", "supposedly", "allegedly", "rumor has it", "I heard that"]
            new_words = random.choice(intensifiers).split() + words[2:]
            return " ".join(new_words[:len(words)]), self.DISTORTION_AMOUNT
        
        elif distortion_type == "simplify" and len(words) > 8:
            # Remove middle details
            keep = words[:3] + words[-3:]
            return " ".join(keep), self.DISTORTION_AMOUNT * 0.5
        
        elif distortion_type == "misattribute" and len(words) > 5:
            # Replace names/pronouns
            new_words = words.copy()
            for i, w in enumerate(new_words):
                if w.lower() in ["he", "she", "they", "him", "her"]:
                    alternatives = ["that person", "someone", "the adventurer", "them"]
                    new_words[i] = random.choice(alternatives)
            return " ".join(new_words), self.DISTORTION_AMOUNT
        
        else:  # partial
            # Change a word to something similar
            new_words = words.copy()
            idx = random.randint(1, len(new_words) - 2)
            new_words[idx] = "[...]"
            return " ".join(new_words), self.DISTORTION_AMOUNT * 0.3
    
    def _add_to_npc_knowledge(self, npc_id: str, info_id: str):
        """Add info to NPC's knowledge base."""
        if npc_id not in self._npc_knowledge:
            self._npc_knowledge[npc_id] = set()
        self._npc_knowledge[npc_id].add(info_id)
        
        if info_id in self._information:
            if npc_id not in self._information[info_id].seen_by:
                self._information[info_id].seen_by.append(npc_id)
    
    def _trigger_emotion_reaction(
        self,
        target_npc_id: str,
        info_type: InformationType,
        content: str,
        credibility: float,
        importance: float,
        source_npc_id: str,
    ):
        """Trigger emotion reaction in target NPC after receiving information.
        
        Uses the emotion callback (if set) to update the target NPC's emotions
        based on the information type and content. The emotion change intensity
        is reduced by 50% compared to direct experience (secondhand information).
        
        Args:
            target_npc_id: The NPC who received the information
            info_type: Type of the information
            content: The information content
            credibility: Credibility of the information
            importance: How important the information is
            source_npc_id: Who shared the information
        """
        if not self._emotion_callback:
            return
        
        content_lower = content.lower()
        emotion_deltas: Dict[str, float] = {}
        
        # Detect event type from content keywords and info type
        # Attack/violence events: trust down, anger up
        attack_keywords = ["attack", "attacked", "hit", "kill", "killed", "fight",
                           "hurt", "stab", "shoot", "暴力", "攻击", "伤害", "杀害"]
        # Help/positive events: trust up
        help_keywords = ["help", "helped", "save", "saved", "protect", "rescue",
                         "heal", "治愈", "帮助", "拯救", "保护"]
        # Trade/neutral events: trust slight up
        trade_keywords = ["trade", "trade", "buy", "sell", "deal", "exchange",
                          "交易", "买卖", "交换"]
        
        # Secondhand information has half the emotional impact
        intensity_factor = credibility * importance * 0.5
        
        is_attack = any(kw in content_lower for kw in attack_keywords)
        is_help = any(kw in content_lower for kw in help_keywords)
        is_trade = any(kw in content_lower for kw in trade_keywords)
        
        if is_attack:
            # Hearing about an attack → trust in attacker drops, anger rises
            emotion_deltas["trust"] = -0.15 * intensity_factor
            emotion_deltas["anger"] = 0.10 * intensity_factor
        elif is_help:
            # Hearing about help → trust in helper rises
            emotion_deltas["trust"] = 0.10 * intensity_factor
            emotion_deltas["joy"] = 0.05 * intensity_factor
        elif is_trade:
            # Hearing about trade → trust slight rise
            emotion_deltas["trust"] = 0.05 * intensity_factor
        elif info_type == InformationType.PLAYER_ACTION:
            # Generic player action: small trust reaction based on importance
            emotion_deltas["trust"] = -0.05 * intensity_factor
        
        if emotion_deltas:
            try:
                self._emotion_callback(target_npc_id, emotion_deltas)
            except Exception as e:
                logger.error(f"Emotion callback error for {target_npc_id}: {e}")
    
    def get_npc_knowledge(
        self,
        npc_id: str,
        info_type: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 50,
    ) -> NPCKnowledge:
        """
        Get all information known by an NPC.
        
        Args:
            npc_id: NPC ID to query
            info_type: Optional filter by information type
            min_importance: Minimum importance threshold
            limit: Maximum number of items to return
            
        Returns:
            NPCKnowledge with all known information
        """
        with self._lock:
            info_ids = self._npc_knowledge.get(npc_id, set())
            
            known_info = []
            for info_id in info_ids:
                info = self._information.get(info_id)
                if not info:
                    continue
                    
                # Filter by type
                if info_type and info.info_type.value != info_type:
                    continue
                
                # Filter by importance
                if info.importance < min_importance:
                    continue
                
                known_info.append({
                    "info_id": info_id,
                    "info_type": info.info_type.value,
                    "content": info.current_content,
                    "original_content": info.original_content if info.distortion_level < 0.3 else None,
                    "credibility": info.credibility,
                    "importance": info.importance,
                    "when_learned": info.last_spread or info.created_at,
                    "tags": info.tags,
                    "is_distorted": info.distortion_level > 0.3,
                })
            
            # Sort by importance and recency
            known_info.sort(key=lambda x: (x["importance"], x["when_learned"]), reverse=True)
            known_info = known_info[:limit]
            
            return NPCKnowledge(
                npc_id=npc_id,
                known_info=known_info,
            )
    
    def get_information_chain(self, info_id: str) -> Optional[PropagationChain]:
        """Get the propagation chain for information."""
        return self._propagation_chains.get(info_id)
    
    def get_info_details(self, info_id: str) -> Optional[Dict[str, Any]]:
        """Get full details about information."""
        info = self._information.get(info_id)
        if not info:
            return None
        
        chain = self._propagation_chains.get(info_id)
        
        return {
            **info.to_dict(),
            "chain": chain.to_dict() if chain else None,
        }
    
    def decay_information(
        self,
        session_id: Optional[str] = None,
        delta_seconds: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Decay information importance over time.
        
        Args:
            session_id: Optional session filter (for efficiency)
            delta_seconds: Time elapsed since last check
            
        Returns:
            Decay statistics
        """
        with self._lock:
            decayed_count = 0
            forgotten_count = 0
            forgotten_ids = []
            
            for info_id, info in list(self._information.items()):
                # Decay importance
                old_importance = info.importance
                info.importance = max(
                    0.0,
                    info.importance - (self.DECAY_RATE * delta_seconds)
                )
                
                if info.importance != old_importance:
                    decayed_count += 1
                
                # Check for forgetting
                if info.importance < self.MIN_IMPORTANCE:
                    # Remove from all NPC knowledge
                    for npc_id in list(self._npc_knowledge.keys()):
                        self._npc_knowledge[npc_id].discard(info_id)
                    
                    # Mark as forgotten
                    self._information.pop(info_id, None)
                    self._propagation_chains.pop(info_id, None)
                    forgotten_count += 1
                    forgotten_ids.append(info_id)
            
            return {
                "delta_seconds": delta_seconds,
                "decayed_count": decayed_count,
                "forgotten_count": forgotten_count,
                "forgotten_ids": forgotten_ids,
                "total_information": len(self._information),
            }
    
    def broadcast_world_event(
        self,
        source_npc_id: str,
        event_type: str,
        event_content: str,
        session_npcs: List[str],
        importance: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Broadcast a world event to all NPCs in a session.
        
        This is the main entry point for game events that should spread.
        
        Args:
            source_npc_id: Who witnessed the event
            event_type: Type of event
            event_content: What happened
            session_npcs: All NPCs in the session
            importance: How significant this is
            
        Returns:
            Broadcast results
        """
        # Create info entry
        info_type = InformationType.WORLD_EVENT
        
        info_id = str(uuid.uuid4())
        info = Information(
            info_id=info_id,
            info_type=info_type,
            original_content=event_content,
            current_content=event_content,
            source_npc_id=source_npc_id,
            importance=importance,
            tags=[event_type],
        )
        
        with self._lock:
            self._information[info_id] = info
            self._propagation_chains[info_id] = PropagationChain(info_id=info_id)
            self._add_to_npc_knowledge(source_npc_id, info_id)
        
        # Spread to others in session (excluding source)
        targets = [npc for npc in session_npcs if npc != source_npc_id]
        
        return self.spread_information(
            source_npc_id=source_npc_id,
            info_type=info_type.value,
            content=event_content,
            targets=targets,
            importance=importance,
            tags=[event_type],
            info_id=info_id,
        )
    
    def spread_player_action(
        self,
        player_id: str,
        action: str,
        source_npc_id: str,
        session_npcs: List[str],
        importance: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Spread player action through NPC network.
        
        This is called when a player does something notable.
        
        Args:
            player_id: Player who performed action
            action: What the player did
            source_npc_id: NPC who witnessed it
            session_npcs: NPCs who might hear about it
            importance: How significant
            
        Returns:
            Spread results
        """
        # Format action for spreading
        content = f"The adventurer {player_id}: {action}"
        
        info_id = str(uuid.uuid4())
        
        info = Information(
            info_id=info_id,
            info_type=InformationType.PLAYER_ACTION,
            original_content=content,
            current_content=content,
            source_npc_id=source_npc_id,
            importance=importance,
            tags=["player_action", player_id],
        )
        
        with self._lock:
            self._information[info_id] = info
            self._propagation_chains[info_id] = PropagationChain(info_id=info_id)
            self._add_to_npc_knowledge(source_npc_id, info_id)
        
        # Spread to nearby NPCs
        targets = [npc for npc in session_npcs if npc != source_npc_id]
        
        return self.spread_information(
            source_npc_id=source_npc_id,
            info_type=InformationType.PLAYER_ACTION.value,
            content=content,
            targets=targets,
            importance=importance,
            tags=["player_action", player_id],
            info_id=info_id,
        )
    
    def get_knowledge_summary(self, npc_id: str) -> Dict[str, Any]:
        """Get a summary of NPC's knowledge."""
        knowledge = self.get_npc_knowledge(npc_id, limit=100)
        
        # Count by type
        type_counts: Dict[str, int] = {}
        for info in knowledge.known_info:
            info_type = info["info_type"]
            type_counts[info_type] = type_counts.get(info_type, 0) + 1
        
        return {
            "npc_id": npc_id,
            "total_known": len(knowledge.known_info),
            "by_type": type_counts,
            "high_importance": len([i for i in knowledge.known_info if i["importance"] > 0.7]),
            "distorted": len([i for i in knowledge.known_info if i["is_distorted"]]),
        }


# Global instance
_propagator: Optional[InformationPropagator] = None


def get_propagator() -> InformationPropagator:
    """Get the global propagator instance."""
    global _propagator
    if _propagator is None:
        _propagator = InformationPropagator()
    return _propagator
