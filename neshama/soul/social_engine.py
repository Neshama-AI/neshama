# Soul Layer - NPC Social Engine
"""
NPCSocialEngine - Manages social relationships between NPCs.

Features:
- NPC-to-NPC social interactions (8 types)
- Social graph management
- Relationship strength tracking
- Information propagation between NPCs
- Autonomous social tick (NPC-initiated interactions)

Design:
- Pure rule-based decision making (no LLM)
- Based on OCEAN personality + emotion state + relationship strength
- Physical distance awareness (same session = can interact)

Example:
    >>> engine = NPCSocialEngine()
    >>> engine.initiate_interaction("npc_alice", "npc_bob", {"topic": "news"})
    >>> graph = engine.get_social_graph("npc_alice")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from enum import Enum
import threading
import uuid
import logging
import random

logger = logging.getLogger(__name__)


class SocialInteractionType(Enum):
    """Types of social interactions between NPCs."""
    GOSSIP = "gossip"           # Share info about third party
    TRADE = "trade"            # Exchange items/info
    ARGUE = "argue"            # Conflict/disagreement
    ALLY = "ally"              # Form alliance
    BETRAY = "betray"          # Break trust
    COMFORT = "comfort"        # Emotional support
    TEACH = "teach"            # Share knowledge
    FLIRT = "flirt"            # Romantic interaction


class RelationshipCategory(Enum):
    """NPC relationship categories."""
    FRIEND = "friend"          # Positive relationship
    ENEMY = "enemy"            # Negative relationship
    NEUTRAL = "neutral"        # No significant relationship
    STRANGER = "stranger"      # Haven't interacted
    ROMANTIC = "romantic"      # Romantic interest
    MENTOR = "mentor"          # Teacher/student
    RIVAL = "rival"            # Competitive relationship


@dataclass
class NPCRelation:
    """Relationship between two NPCs."""
    npc_a_id: str
    npc_b_id: str
    strength: float = 0.5       # 0-1, overall relationship quality
    trust: float = 0.5          # 0-1, trust level
    familiarity: float = 0.0   # 0-1, how well they know each other
    interaction_count: int = 0
    last_interaction: Optional[str] = None
    category: RelationshipCategory = RelationshipCategory.NEUTRAL
    grudge: float = 0.0         # 0-1, grudge level (from BETRAY)
    bond: float = 0.0          # 0-1, emotional bond (from COMFORT)
    romantic_interest: float = 0.0  # 0-1, romantic attraction
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_a_id": self.npc_a_id,
            "npc_b_id": self.npc_b_id,
            "strength": round(self.strength, 4),
            "trust": round(self.trust, 4),
            "familiarity": round(self.familiarity, 4),
            "interaction_count": self.interaction_count,
            "last_interaction": self.last_interaction,
            "category": self.category.value,
            "grudge": round(self.grudge, 4),
            "bond": round(self.bond, 4),
            "romantic_interest": round(self.romantic_interest, 4),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NPCRelation":
        cat = data.get("category", "neutral")
        if isinstance(cat, str):
            try:
                cat = RelationshipCategory(cat)
            except ValueError:
                cat = RelationshipCategory.NEUTRAL
        return cls(
            npc_a_id=data["npc_a_id"],
            npc_b_id=data["npc_b_id"],
            strength=data.get("strength", 0.5),
            trust=data.get("trust", 0.5),
            familiarity=data.get("familiarity", 0.0),
            interaction_count=data.get("interaction_count", 0),
            last_interaction=data.get("last_interaction"),
            category=cat,
            grudge=data.get("grudge", 0.0),
            bond=data.get("bond", 0.0),
            romantic_interest=data.get("romantic_interest", 0.0),
        )


@dataclass
class SocialEvent:
    """Record of a social interaction."""
    event_id: str
    npc_a_id: str
    npc_b_id: str
    interaction_type: SocialInteractionType
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    relationship_delta: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "npc_a_id": self.npc_a_id,
            "npc_b_id": self.npc_b_id,
            "interaction_type": self.interaction_type.value,
            "timestamp": self.timestamp,
            "context": self.context,
            "success": self.success,
            "relationship_delta": self.relationship_delta,
        }


@dataclass
class SocialDecisionContext:
    """Context for making social interaction decisions."""
    npc_personality: Dict[str, float]  # OCEAN scores
    npc_emotions: Dict[str, float]       # Current emotions
    relationship: Optional[NPCRelation]  # Existing relationship
    npc_session_id: Optional[str] = None  # Current session
    physical_distance: float = 1.0       # 0 = same spot, 1 = far away
    time_since_last_interaction: float = 0.0  # Seconds


class NPCSocialEngine:
    """
    Manages social relationships and interactions between NPCs.
    
    Features:
    - Initiate interactions between two NPCs
    - Get social graph for an NPC
    - Get mutual relations between two NPCs
    - Propagate information between NPCs
    - Social tick for autonomous interactions
    
    Example:
        >>> engine = NPCSocialEngine()
        >>> engine.initiate_interaction("alice", "bob", {"topic": "weather"})
        >>> graph = engine.get_social_graph("alice")
    """
    
    # Interaction cooldowns (seconds)
    MIN_INTERACTION_INTERVAL = 30.0  # Minimum time between same pair
    MAX_INTERACTIONS_PER_TICK = 3    # Max new interactions per tick
    
    # Interaction thresholds
    TRUST_THRESHOLD_FOR_DEEP = 0.7   # Trust needed for ALLY/BETRAY
    FAMILIARITY_THRESHOLD = 0.3     # Familiar enough to interact freely
    
    # Relationship bounds
    MAX_STRENGTH = 1.0
    MIN_STRENGTH = -1.0
    MAX_TRUST = 1.0
    MAX_FAMILIARITY = 1.0
    
    def __init__(self):
        """Initialize NPCSocialEngine."""
        # NPC-to-NPC relations: (npc_a_id, npc_b_id) -> NPCRelation
        self._relations: Dict[Tuple[str, str], NPCRelation] = {}
        
        # NPC session membership: npc_id -> session_id
        self._npc_sessions: Dict[str, str] = {}
        
        # NPC profiles cache: npc_id -> personality/emotions
        self._npc_profiles: Dict[str, Dict[str, Any]] = {}
        
        # Social event history
        self._social_events: List[SocialEvent] = []
        self._max_events = 1000
        
        # Last interaction times: (npc_a, npc_b) -> timestamp
        self._last_interactions: Dict[Tuple[str, str], datetime] = {}
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        logger.info("NPCSocialEngine initialized")
    
    def _get_relation_key(self, npc_a: str, npc_b: str) -> Tuple[str, str]:
        """Get normalized relation key (always sorted)."""
        return (min(npc_a, npc_b), max(npc_a, npc_b))
    
    def register_npc(
        self,
        npc_id: str,
        session_id: Optional[str] = None,
        personality: Optional[Dict[str, float]] = None,
        emotions: Optional[Dict[str, float]] = None,
    ):
        """
        Register an NPC with the social engine.
        
        Args:
            npc_id: NPC identifier
            session_id: Current game session
            personality: OCEAN personality scores
            emotions: Current emotion state
        """
        with self._lock:
            self._npc_sessions[npc_id] = session_id
            self._npc_profiles[npc_id] = {
                "personality": personality or {
                    "openness": 0.5, "conscientiousness": 0.5,
                    "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5,
                },
                "emotions": emotions or {},
            }
            logger.debug(f"Registered NPC {npc_id} in session {session_id}")
    
    def update_npc_state(
        self,
        npc_id: str,
        session_id: Optional[str] = None,
        emotions: Optional[Dict[str, float]] = None,
    ):
        """Update NPC state without full re-registration."""
        with self._lock:
            if npc_id in self._npc_profiles:
                if session_id is not None:
                    self._npc_sessions[npc_id] = session_id
                if emotions is not None:
                    self._npc_profiles[npc_id]["emotions"] = emotions
    
    def get_relation(self, npc_a_id: str, npc_b_id: str) -> Optional[NPCRelation]:
        """Get relationship between two NPCs."""
        key = self._get_relation_key(npc_a_id, npc_b_id)
        with self._lock:
            return self._relations.get(key)
    
    def get_or_create_relation(self, npc_a_id: str, npc_b_id: str) -> NPCRelation:
        """Get existing or create new relationship."""
        key = self._get_relation_key(npc_a_id, npc_b_id)
        with self._lock:
            if key not in self._relations:
                self._relations[key] = NPCRelation(
                    npc_a_id=key[0],
                    npc_b_id=key[1],
                )
            return self._relations[key]
    
    def initiate_interaction(
        self,
        npc_a_id: str,
        npc_b_id: str,
        context: Optional[Dict[str, Any]] = None,
        forced_type: Optional[SocialInteractionType] = None,
    ) -> SocialEvent:
        """
        Initiate a social interaction between two NPCs.
        
        Args:
            npc_a_id: Initiator NPC ID
            npc_b_id: Target NPC ID
            context: Additional context (topic, location, etc.)
            forced_type: Force a specific interaction type (for API calls)
            
        Returns:
            SocialEvent with interaction details and relationship changes
        """
        with self._lock:
            # Check cooldown
            key = self._get_relation_key(npc_a_id, npc_b_id)
            last_time = self._last_interactions.get(key)
            if last_time:
                elapsed = (datetime.now() - last_time).total_seconds()
                if elapsed < self.MIN_INTERACTION_INTERVAL:
                    return SocialEvent(
                        event_id=str(uuid.uuid4()),
                        npc_a_id=npc_a_id,
                        npc_b_id=npc_b_id,
                        interaction_type=SocialInteractionType.GOSSIP,
                        success=False,
                        context={"reason": "cooldown", "elapsed": elapsed},
                    )
            
            # Get/create relation
            relation = self.get_or_create_relation(npc_a_id, npc_b_id)
            
            # Get NPC contexts
            npc_a_profile = self._npc_profiles.get(npc_a_id, {})
            npc_b_profile = self._npc_profiles.get(npc_b_id, {})
            
            npc_a_personality = npc_a_profile.get("personality", {})
            npc_a_emotions = npc_a_profile.get("emotions", {})
            npc_b_personality = npc_b_profile.get("personality", {})
            npc_b_emotions = npc_b_profile.get("emotions", {})
            
            # Determine interaction type
            if forced_type:
                interaction_type = forced_type
            else:
                interaction_type = self._decide_interaction_type(
                    npc_a_personality, npc_a_emotions,
                    npc_b_personality, npc_b_emotions,
                    relation,
                )
            
            # Calculate relationship changes
            delta = self._calculate_interaction_effects(
                interaction_type,
                npc_a_personality, npc_b_personality,
                relation,
            )
            
            # Apply changes
            self._apply_relation_delta(relation, delta)
            
            # Update interaction tracking
            relation.interaction_count += 1
            relation.last_interaction = datetime.now().isoformat()
            self._last_interactions[key] = datetime.now()
            
            # Create event
            event = SocialEvent(
                event_id=str(uuid.uuid4()),
                npc_a_id=npc_a_id,
                npc_b_id=npc_b_id,
                interaction_type=interaction_type,
                context=context or {},
                success=True,
                relationship_delta=delta,
            )
            
            # Store event
            self._social_events.append(event)
            if len(self._social_events) > self._max_events:
                self._social_events = self._social_events[-self._max_events:]
            
            logger.info(f"Social event: {npc_a_id} -> {npc_b_id} ({interaction_type.value})")
            return event
    
    def _decide_interaction_type(
        self,
        npc_a_personality: Dict[str, float],
        npc_a_emotions: Dict[str, float],
        npc_b_personality: Dict[str, float],
        npc_b_emotions: Dict[str, float],
        relation: NPCRelation,
    ) -> SocialInteractionType:
        """
        Decide what type of interaction to have based on rule-based logic.
        
        Decision factors:
        - OCEAN personality
        - Current emotions
        - Relationship state
        """
        # High anger -> argue
        anger = npc_a_emotions.get("anger", 0.0) + npc_a_emotions.get("contempt", 0.0)
        if anger > 0.6:
            return SocialInteractionType.ARGUE
        
        # High sadness in target -> comfort
        sadness = npc_b_emotions.get("sadness", 0.0) + npc_b_emotions.get("anxiety", 0.0)
        if sadness > 0.5 and relation.trust > 0.4:
            return SocialInteractionType.COMFORT
        
        # High romantic interest -> flirt
        if relation.romantic_interest > 0.5:
            return SocialInteractionType.FLIRT
        
        # High agreeableness -> gossip or comfort
        if npc_a_personality.get("agreeableness", 0.5) > 0.6:
            if relation.familiarity < self.FAMILIARITY_THRESHOLD:
                return SocialInteractionType.GOSSIP
            return random.choice([SocialInteractionType.COMFORT, SocialInteractionType.GOSSIP])
        
        # Low agreeableness -> argue or trade
        if npc_a_personality.get("agreeableness", 0.5) < 0.4:
            return random.choice([SocialInteractionType.ARGUE, SocialInteractionType.TRADE])
        
        # High extraversion -> initiate social
        if npc_a_personality.get("extraversion", 0.5) > 0.6:
            # Joy leads to flirting or alliance
            joy = npc_a_emotions.get("joy", 0.0) + npc_a_emotions.get("delight", 0.0)
            if joy > 0.5:
                return random.choice([SocialInteractionType.FLIRT, SocialInteractionType.ALLY])
            return SocialInteractionType.GOSSIP
        
        # Trust threshold check for deeper interactions
        if relation.trust > self.TRUST_THRESHOLD_FOR_DEEP:
            return random.choice([SocialInteractionType.ALLY, SocialInteractionType.TEACH])
        
        # Default: gossip for strangers, trade for acquaintances
        if relation.familiarity < 0.1:
            return SocialInteractionType.GOSSIP
        return SocialInteractionType.TRADE
    
    def _calculate_interaction_effects(
        self,
        interaction_type: SocialInteractionType,
        npc_a_personality: Dict[str, float],
        npc_b_personality: Dict[str, float],
        relation: NPCRelation,
    ) -> Dict[str, float]:
        """Calculate relationship delta from an interaction."""
        delta: Dict[str, float] = {}
        
        # Base effects per interaction type
        base_effects = {
            SocialInteractionType.GOSSIP: {
                "strength": 0.05, "familiarity": 0.1,
            },
            SocialInteractionType.TRADE: {
                "strength": 0.1, "trust": 0.1, "familiarity": 0.1,
            },
            SocialInteractionType.ARGUE: {
                "strength": -0.15, "trust": -0.1,
            },
            SocialInteractionType.ALLY: {
                "strength": 0.25, "trust": 0.2, "familiarity": 0.15,
            },
            SocialInteractionType.BETRAY: {
                "strength": -0.5, "trust": -0.6, "grudge": 0.4,
            },
            SocialInteractionType.COMFORT: {
                "strength": 0.1, "bond": 0.15, "familiarity": 0.05,
            },
            SocialInteractionType.TEACH: {
                "strength": 0.1, "trust": 0.1, "familiarity": 0.1,
            },
            SocialInteractionType.FLIRT: {
                "strength": 0.1, "romantic_interest": 0.15, "familiarity": 0.05,
            },
        }
        
        base = base_effects.get(interaction_type, {})
        
        # Personality modifiers
        agreeableness = npc_a_personality.get("agreeableness", 0.5)
        
        # High agreeableness amplifies positive effects, reduces negative
        if interaction_type in [SocialInteractionType.COMFORT, SocialInteractionType.GOSSIP]:
            modifier = 1.0 + (agreeableness - 0.5) * 0.5
        elif interaction_type == SocialInteractionType.ARGUE:
            modifier = 1.0 - (agreeableness - 0.5) * 0.5
        else:
            modifier = 1.0
        
        for key, value in base.items():
            delta[key] = value * modifier
        
        # Relationship state modifiers
        if relation.grudge > 0.3:
            # Grudge makes arguments more likely and interactions harder
            if interaction_type == SocialInteractionType.ARGUE:
                delta["strength"] = delta.get("strength", 0) * 0.5
            elif interaction_type in [SocialInteractionType.ALLY, SocialInteractionType.COMFORT]:
                delta["strength"] = delta.get("strength", 0) * 0.3  # Harder with grudge
        
        return delta
    
    def _apply_relation_delta(self, relation: NPCRelation, delta: Dict[str, float]):
        """Apply relationship delta to a relation."""
        relation.strength = max(
            self.MIN_STRENGTH,
            min(self.MAX_STRENGTH, relation.strength + delta.get("strength", 0))
        )
        relation.trust = max(
            0.0,
            min(self.MAX_TRUST, relation.trust + delta.get("trust", 0))
        )
        relation.familiarity = max(
            0.0,
            min(self.MAX_FAMILIARITY, relation.familiarity + delta.get("familiarity", 0))
        )
        relation.grudge = max(
            0.0,
            min(1.0, relation.grudge + delta.get("grudge", 0))
        )
        relation.bond = max(
            0.0,
            min(1.0, relation.bond + delta.get("bond", 0))
        )
        relation.romantic_interest = max(
            0.0,
            min(1.0, relation.romantic_interest + delta.get("romantic_interest", 0))
        )
        
        # Update category
        self._update_relation_category(relation)
    
    def _update_relation_category(self, relation: NPCRelation):
        """Update relationship category based on current values."""
        if relation.romantic_interest > 0.6 and relation.strength > 0.5:
            relation.category = RelationshipCategory.ROMANTIC
        elif relation.grudge > 0.5:
            relation.category = RelationshipCategory.ENEMY
        elif relation.strength > 0.7:
            relation.category = RelationshipCategory.FRIEND
        elif relation.strength > 0.3:
            relation.category = RelationshipCategory.NEUTRAL
        elif relation.strength < -0.3:
            relation.category = RelationshipCategory.ENEMY
        elif relation.familiarity < 0.1:
            relation.category = RelationshipCategory.STRANGER
        else:
            relation.category = RelationshipCategory.NEUTRAL
    
    def get_social_graph(self, npc_id: str) -> Dict[str, Any]:
        """
        Get social network for an NPC.
        
        Args:
            npc_id: NPC ID to query
            
        Returns:
            Dict with friends, enemies, neutral, and stranger lists
        """
        with self._lock:
            friends = []
            enemies = []
            neutrals = []
            strangers = []
            
            for key, relation in self._relations.items():
                if npc_id not in key:
                    continue
                
                other_id = key[0] if key[1] == npc_id else key[1]
                
                rel_dict = {
                    "npc_id": other_id,
                    **relation.to_dict(),
                }
                
                if relation.category == RelationshipCategory.FRIEND:
                    friends.append(rel_dict)
                elif relation.category == RelationshipCategory.ENEMY:
                    enemies.append(rel_dict)
                elif relation.category == RelationshipCategory.STRANGER:
                    strangers.append(rel_dict)
                else:
                    neutrals.append(rel_dict)
            
            return {
                "npc_id": npc_id,
                "friends": friends,
                "enemies": enemies,
                "neutrals": neutrals,
                "strangers": strangers,
                "friend_count": len(friends),
                "enemy_count": len(enemies),
            }
    
    def get_mutual_relations(self, npc_a_id: str, npc_b_id: str) -> Dict[str, Any]:
        """
        Get complete relationship info between two NPCs.
        
        Args:
            npc_a_id: First NPC ID
            npc_b_id: Second NPC ID
            
        Returns:
            Full relation details
        """
        relation = self.get_relation(npc_a_id, npc_b_id)
        if not relation:
            relation = self.get_or_create_relation(npc_a_id, npc_b_id)
        
        return {
            "npc_a_id": npc_a_id,
            "npc_b_id": npc_b_id,
            "relation": relation.to_dict(),
            "can_interact": self._can_interact(npc_a_id, npc_b_id),
            "suggested_interaction": self._suggest_interaction_type(relation),
        }
    
    def _can_interact(self, npc_a_id: str, npc_b_id: str) -> bool:
        """Check if two NPCs can interact (same session/proximity)."""
        session_a = self._npc_sessions.get(npc_a_id)
        session_b = self._npc_sessions.get(npc_b_id)
        # Can interact if in same session or both unregistered
        return session_a == session_b or session_a is None or session_b is None
    
    def _suggest_interaction_type(self, relation: NPCRelation) -> str:
        """Suggest best interaction type based on relationship."""
        if relation.category == RelationshipCategory.STRANGER:
            return "gossip"
        elif relation.category == RelationshipCategory.FRIEND:
            return "trade"
        elif relation.category == RelationshipCategory.ENEMY:
            if relation.grudge > 0.5:
                return "argue"
            return "trade"
        else:
            return "gossip"
    
    def propagate_information(
        self,
        npc_a_id: str,
        npc_b_id: str,
        info_type: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        Propagate information from one NPC to another.
        
        Args:
            npc_a_id: Source NPC
            npc_b_id: Target NPC
            info_type: Type of information
            content: Information content
            
        Returns:
            Propagation result
        """
        relation = self.get_relation(npc_a_id, npc_b_id)
        if not relation:
            return {"success": False, "reason": "no_relation"}
        
        # Check if they can share info
        if relation.trust < 0.3:
            return {"success": False, "reason": "low_trust"}
        
        # Trust affects info fidelity
        fidelity = relation.trust * relation.familiarity
        
        return {
            "success": True,
            "info_type": info_type,
            "content": content,
            "fidelity": fidelity,
            "shared_with": npc_b_id,
        }
    
    def social_tick(self, session_id: Optional[str] = None) -> List[SocialEvent]:
        """
        Check for and initiate autonomous NPC interactions.
        
        This should be called periodically (e.g., every 10 seconds).
        Only NPCs in the same session can interact autonomously.
        
        Args:
            session_id: Optional session to filter NPCs
            
        Returns:
            List of newly initiated social events
        """
        with self._lock:
            events = []
            
            # Get NPCs in session
            if session_id:
                npcs = [npc for npc, sess in self._npc_sessions.items() if sess == session_id]
            else:
                npcs = list(self._npc_sessions.keys())
            
            if len(npcs) < 2:
                return events
            
            # Limit interactions per tick
            max_new = self.MAX_INTERACTIONS_PER_TICK
            
            for _ in range(max_new):
                if len(events) >= max_new:
                    break
                
                # Pick random pair
                npc_a, npc_b = random.sample(npcs, 2)
                
                # Check cooldown
                key = self._get_relation_key(npc_a, npc_b)
                last_time = self._last_interactions.get(key)
                if last_time:
                    elapsed = (datetime.now() - last_time).total_seconds()
                    if elapsed < self.MIN_INTERACTION_INTERVAL:
                        continue
                
                # Get relation
                relation = self.get_or_create_relation(npc_a, npc_b)
                
                # Check if interaction is worthwhile
                # High extraversion NPCs more likely to initiate
                npc_a_profile = self._npc_profiles.get(npc_a, {})
                extraversion = npc_a_profile.get("personality", {}).get("extraversion", 0.5)
                
                # Random roll based on extraversion
                if random.random() > extraversion * 0.3:
                    continue
                
                # Initiate interaction
                event = self.initiate_interaction(npc_a, npc_b, {"autonomous": True})
                if event.success:
                    events.append(event)
            
            return events
    
    def get_recent_events(
        self,
        npc_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get recent social events, optionally filtered by NPC."""
        events = self._social_events[-limit:]
        
        if npc_id:
            events = [e for e in events if e.npc_a_id == npc_id or e.npc_b_id == npc_id]
        
        return [e.to_dict() for e in events]
    
    def get_all_npcs_in_session(self, session_id: str) -> List[str]:
        """Get all NPC IDs in a session."""
        with self._lock:
            return [
                npc for npc, sess in self._npc_sessions.items()
                if sess == session_id
            ]


# Global instance
_social_engine: Optional[NPCSocialEngine] = None


def get_social_engine() -> NPCSocialEngine:
    """Get the global social engine instance."""
    global _social_engine
    if _social_engine is None:
        _social_engine = NPCSocialEngine()
    return _social_engine
