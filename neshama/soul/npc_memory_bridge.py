# Soul Layer - NPC Memory Bridge
"""
NPCMemoryBridge - Connects EntityGraph and Memory systems.

When NPCs interact with entities through game events:
1. Updates the EntityGraph with relationships
2. Stores memories in the Memory system
3. Provides context for dialogue generation

This bridge ensures NPC memories are consistent with their
emotional state and relationship graph.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import threading
import logging

from neshama.soul.entity_graph import (
    EntityGraph, EntityNode, EntityType, RelationType, 
    EdgeDirection, GraphEdge
)
from neshama.soul.emotion.game_event import GameEvent, GameEventType

logger = logging.getLogger(__name__)


# Event to relation mapping rules
EVENT_RELATION_MAPPINGS: Dict[GameEventType, Dict[str, Any]] = {
    GameEventType.PLAYER_ATTACKED: {
        "relation": "hostile",
        "strength_delta": 0.3,
        "trust_delta": -0.2,
    },
    GameEventType.PLAYER_HELPED: {
        "relation": "ally",
        "strength_delta": 0.3,
        "trust_delta": 0.2,
    },
    GameEventType.ITEM_RECEIVED: {
        "relation": "friendly",
        "strength_delta": 0.1,
        "trust_delta": 0.1,
    },
    GameEventType.ITEM_LOST: {
        "relation": "neutral",
        "strength_delta": -0.1,
        "trust_delta": -0.1,
    },
    GameEventType.QUEST_COMPLETED: {
        "relation": "ally",
        "strength_delta": 0.3,
        "trust_delta": 0.3,
    },
    GameEventType.QUEST_FAILED: {
        "relation": "disappointed",
        "strength_delta": -0.2,
        "trust_delta": -0.1,
    },
    GameEventType.NPC_INSULTED: {
        "relation": "hostile",
        "strength_delta": 0.2,
        "trust_delta": -0.3,
    },
    GameEventType.NPC_COMPLIMENTED: {
        "relation": "friendly",
        "strength_delta": 0.2,
        "trust_delta": 0.2,
    },
    GameEventType.GIFT_GIVEN: {
        "relation": "friendly",
        "strength_delta": 0.2,
        "trust_delta": 0.3,
    },
    GameEventType.ENVIRONMENT_CHANGED: {
        "relation": "aware",
        "strength_delta": 0.1,
    },
    GameEventType.RELATIONSHIP_CHANGED: {
        "relation": "connected",
        "strength_delta": 0.2,
    },
    GameEventType.COMBAT_STARTED: {
        "relation": "hostile",
        "strength_delta": 0.2,
    },
    GameEventType.COMBAT_ENDED: {
        "relation": "tense",
        "strength_delta": 0.0,
    },
    GameEventType.DEATH_WITNESSED: {
        "relation": "shaken",
        "strength_delta": 0.2,
    },
    GameEventType.TIME_PASSED: {
        "relation": "neutral",
        "strength_delta": -0.05,
    },
}


class RelationStrength(Enum):
    """Relation strength categories."""
    INTIMATE = "intimate"      # 0.8-1.0
    CLOSE = "close"          # 0.6-0.8
    FRIENDLY = "friendly"     # 0.4-0.6
    NEUTRAL = "neutral"       # 0.2-0.4
    DISTANT = "distant"       # 0.0-0.2
    HOSTILE = "hostile"       # < 0.0


@dataclass
class EntityRelation:
    """NPC's relationship with an entity."""
    entity_id: str
    entity_name: str
    relation_type: str
    strength: float           # 0-1
    trust: float              # 0-1
    last_interaction: str
    interaction_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "relation_type": self.relation_type,
            "strength": round(self.strength, 4),
            "trust": round(self.trust, 4),
            "last_interaction": self.last_interaction,
            "interaction_count": self.interaction_count,
            "strength_category": self._get_strength_category(),
        }
    
    def _get_strength_category(self) -> str:
        if self.strength >= 0.8:
            return "intimate"
        elif self.strength >= 0.6:
            return "close"
        elif self.strength >= 0.4:
            return "friendly"
        elif self.strength >= 0.2:
            return "neutral"
        elif self.strength >= 0.0:
            return "distant"
        else:
            return "hostile"


@dataclass
class EntityMemory:
    """A memory entry about an entity interaction."""
    memory_id: str
    entity_id: str
    entity_name: str
    event_type: str
    description: str
    timestamp: str
    emotional_context: Dict[str, float]
    trust_at_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "event_type": self.event_type,
            "description": self.description,
            "timestamp": self.timestamp,
            "emotional_context": {k: round(v, 4) for k, v in self.emotional_context.items()},
            "trust_at_time": round(self.trust_at_time, 4),
        }


@dataclass
class DialogueContext:
    """Context for NPC dialogue generation."""
    npc_id: str
    player_id: str
    player_name: str
    relation: EntityRelation
    recent_memories: List[EntityMemory]
    emotional_state: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "relation": self.relation.to_dict(),
            "recent_memories": [m.to_dict() for m in self.recent_memories],
            "emotional_state": {k: round(v, 4) for k, v in self.emotional_state.items()},
        }
    
    def to_prompt_parts(self, max_memories: int = 3) -> List[str]:
        """Convert to prompt injection strings."""
        parts = []
        
        # Relation description
        parts.append(f"你与{self.player_name}的关系是{self.relation.relation_type}，强度{self.relation.strength:.2f}，信任度{self.relation.trust:.2f}")
        
        # Recent memories (limit to most recent)
        if self.recent_memories:
            memories_desc = "、".join([
                f"{m.event_type}({m.description[:20]}...)" 
                for m in self.recent_memories[:max_memories]
            ])
            parts.append(f"你最近与{self.player_name}的交互：{memories_desc}")
        
        # Emotional state (only significant emotions)
        significant = {k: v for k, v in self.emotional_state.items() if v > 0.2}
        if significant:
            emotions_desc = "、".join([f"{k}({v:.2f})" for k, v in sorted(significant.items(), key=lambda x: -x[1])])
            parts.append(f"你当前情绪：{emotions_desc}")
        
        return parts


class NPCMemoryBridge:
    """
    Bridge between EntityGraph and Memory systems.
    
    Handles:
    - Game event → EntityGraph updates
    - Game event → Memory storage
    - Dialogue context generation
    
    Example:
        >>> bridge = NPCMemoryBridge()
        >>> 
        >>> # Process a game event
        >>> event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        >>> bridge.on_game_event("npc_001", event, entity_id="player_001", entity_name="Hero")
        >>> 
        >>> # Get dialogue context
        >>> ctx = bridge.get_dialogue_context("npc_001", "player_001")
        >>> prompt_parts = ctx.to_prompt_parts()
    """
    
    def __init__(self):
        """Initialize the bridge."""
        self._lock = threading.RLock()
        
        # NPC's entity graphs: npc_id -> EntityGraph
        self._npc_graphs: Dict[str, EntityGraph] = {}
        
        # NPC's entity relations: npc_id -> {entity_id -> EntityRelation}
        self._relations: Dict[str, Dict[str, EntityRelation]] = {}
        
        # NPC's memories: npc_id -> [EntityMemory]
        self._memories: Dict[str, List[EntityMemory]] = {}
        
        # Memory ID counter
        self._memory_counter = 0
        
        # Relation decay rate (per second)
        self._decay_rate = 0.001  # 0.1% per second
    
    def _get_or_create_npc_graph(self, npc_id: str) -> EntityGraph:
        """Get or create an EntityGraph for an NPC."""
        with self._lock:
            if npc_id not in self._npc_graphs:
                self._npc_graphs[npc_id] = EntityGraph()
                self._relations[npc_id] = {}
                self._memories[npc_id] = []
            return self._npc_graphs[npc_id]
    
    def on_game_event(
        self,
        npc_id: str,
        event: GameEvent,
        entity_id: str,
        entity_name: str,
        entity_type: EntityType = EntityType.PERSON,
    ) -> Optional[DialogueContext]:
        """
        Process a game event and update entity graph + memory.
        
        Args:
            npc_id: NPC identifier
            event: The game event
            entity_id: Target entity ID (e.g., player ID)
            entity_name: Target entity name
            entity_type: Type of entity
            
        Returns:
            Updated DialogueContext or None on error
        """
        with self._lock:
            graph = self._get_or_create_npc_graph(npc_id)
            
            # Get mapping for this event type
            mapping = EVENT_RELATION_MAPPINGS.get(event.event_type)
            if not mapping:
                logger.warning(f"No mapping for event type: {event.event_type}")
                return None
            
            # Get or create entity node
            entity_node = graph.get_entity(entity_id)
            if not entity_node:
                entity_node = graph.add_entity(
                    name=entity_name,
                    entity_type=entity_type,
                    description=f"{entity_type.value} encountered by NPC",
                )
                entity_node.id = entity_id
            else:
                # Update name if changed
                entity_node.name = entity_name
            
            # Get or create NPC node
            npc_node = graph.get_entity(npc_id)
            if not npc_node:
                npc_node = graph.add_entity(
                    name=npc_id,
                    entity_type=EntityType.PERSON,
                    description="NPC with soul",
                )
                npc_node.id = npc_id
            
            # Get current relation or create new
            if npc_id not in self._relations:
                self._relations[npc_id] = {}
            
            relation = self._relations[npc_id].get(entity_id)
            
            # Calculate new values
            strength_delta = mapping.get("strength_delta", 0.0) * event.intensity
            trust_delta = mapping.get("trust_delta", 0.0) * event.intensity
            
            if relation:
                new_strength = max(-1.0, min(1.0, relation.strength + strength_delta))
                new_trust = max(0.0, min(1.0, relation.trust + trust_delta))
                
                relation.strength = new_strength
                relation.trust = new_trust
                relation.relation_type = mapping["relation"]
                relation.last_interaction = datetime.now().isoformat()
                relation.interaction_count += 1
            else:
                relation = EntityRelation(
                    entity_id=entity_id,
                    entity_name=entity_name,
                    relation_type=mapping["relation"],
                    strength=max(0.0, min(1.0, 0.3 + strength_delta)),
                    trust=max(0.0, min(1.0, 0.3 + trust_delta)),
                    last_interaction=datetime.now().isoformat(),
                    interaction_count=1,
                )
                self._relations[npc_id][entity_id] = relation
            
            # Create/update graph edge
            try:
                existing_edge = None
                for edge in graph.get_edges_from(npc_id):
                    if edge.target_id == entity_id:
                        existing_edge = edge
                        break
                
                if existing_edge:
                    existing_edge.weight = max(0.0, min(1.0, existing_edge.weight + strength_delta * 0.5))
                else:
                    graph.add_edge(
                        source_id=npc_id,
                        target_id=entity_id,
                        relation_type=RelationType.CUSTOM,
                        weight=max(0.0, min(1.0, 0.3 + strength_delta)),
                        description=f"Relationship: {mapping['relation']}",
                    )
            except Exception as e:
                logger.error(f"Error updating graph edge: {e}")
            
            # Create memory entry
            self._memory_counter += 1
            memory = EntityMemory(
                memory_id=f"mem_{self._memory_counter}",
                entity_id=entity_id,
                entity_name=entity_name,
                event_type=event.event_type.value,
                description=self._generate_memory_description(event, entity_name, mapping),
                timestamp=datetime.now().isoformat(),
                emotional_context={},  # Would be filled by caller
                trust_at_time=relation.trust,
            )
            self._memories[npc_id].append(memory)
            
            # Keep only recent memories (last 50)
            if len(self._memories[npc_id]) > 50:
                self._memories[npc_id] = self._memories[npc_id][-50:]
            
            return None  # Caller should get context separately
    
    def _generate_memory_description(
        self, 
        event: GameEvent, 
        entity_name: str,
        mapping: Dict[str, Any],
    ) -> str:
        """Generate a human-readable memory description."""
        event_desc = {
            GameEventType.PLAYER_ATTACKED: f"被{entity_name}攻击",
            GameEventType.PLAYER_HELPED: f"被{entity_name}帮助",
            GameEventType.ITEM_RECEIVED: f"从{entity_name}处收到物品",
            GameEventType.ITEM_LOST: f"被{entity_name}夺走物品",
            GameEventType.QUEST_COMPLETED: f"与{entity_name}完成任务",
            GameEventType.QUEST_FAILED: f"与{entity_name}任务失败",
            GameEventType.NPC_INSULTED: f"被{entity_name}侮辱",
            GameEventType.NPC_COMPLIMENTED: f"被{entity_name}称赞",
            GameEventType.GIFT_GIVEN: f"收到{entity_name}的礼物",
            GameEventType.ENVIRONMENT_CHANGED: f"环境发生变化",
            GameEventType.RELATIONSHIP_CHANGED: f"与{entity_name}关系改变",
            GameEventType.COMBAT_STARTED: f"与{entity_name}开始战斗",
            GameEventType.COMBAT_ENDED: f"与{entity_name}结束战斗",
            GameEventType.DEATH_WITNESSED: f"目睹{entity_name}死亡",
            GameEventType.TIME_PASSED: f"时间流逝",
        }
        
        base = event_desc.get(event.event_type, f"与{entity_name}发生未知事件")
        
        if event.context:
            if isinstance(event.context, dict):
                extra = event.context.get("description", "")
                if extra:
                    return f"{base}：{extra}"
        
        return base
    
    def get_dialogue_context(
        self,
        npc_id: str,
        player_id: str,
        player_name: Optional[str] = None,
        emotional_state: Optional[Dict[str, float]] = None,
        max_memories: int = 5,
    ) -> Optional[DialogueContext]:
        """
        Get dialogue context for NPC-player interaction.
        
        Args:
            npc_id: NPC identifier
            player_id: Player identifier
            player_name: Player display name (optional)
            emotional_state: Current NPC emotional state (optional)
            max_memories: Maximum recent memories to include
            
        Returns:
            DialogueContext or None if no relation exists
        """
        with self._lock:
            if npc_id not in self._relations:
                return None
            
            relation = self._relations[npc_id].get(player_id)
            if not relation:
                return None
            
            # Get recent memories about this entity
            memories = [
                m for m in self._memories.get(npc_id, [])
                if m.entity_id == player_id
            ][-max_memories:]
            
            return DialogueContext(
                npc_id=npc_id,
                player_id=player_id,
                player_name=player_name or relation.entity_name,
                relation=relation,
                recent_memories=memories,
                emotional_state=emotional_state or {},
            )
    
    def get_entity_memories(
        self,
        npc_id: str,
        entity_id: str,
        max_count: int = 10,
    ) -> List[EntityMemory]:
        """
        Get all memories an NPC has about an entity.
        
        Args:
            npc_id: NPC identifier
            entity_id: Entity identifier
            max_count: Maximum memories to return
            
        Returns:
            List of EntityMemory objects (most recent first)
        """
        with self._lock:
            memories = self._memories.get(npc_id, [])
            entity_memories = [
                m for m in memories
                if m.entity_id == entity_id
            ]
            return entity_memories[-max_count:][::-1]  # Most recent first
    
    def get_relation(self, npc_id: str, entity_id: str) -> Optional[EntityRelation]:
        """Get NPC's relation with an entity."""
        with self._lock:
            return self._relations.get(npc_id, {}).get(entity_id)
    
    def get_all_relations(self, npc_id: str) -> List[EntityRelation]:
        """Get all relations for an NPC."""
        with self._lock:
            return list(self._relations.get(npc_id, {}).values())
    
    def decay_relations(self, npc_id: str, delta_seconds: float):
        """
        Decay relations over time.
        
        Relations weaken if no interaction for a long time.
        
        Args:
            npc_id: NPC identifier
            delta_seconds: Time elapsed
        """
        with self._lock:
            if npc_id not in self._relations:
                return
            
            for relation in self._relations[npc_id].values():
                # Decay strength slightly
                decay_factor = 1.0 - (self._decay_rate * delta_seconds * 0.1)
                relation.strength *= decay_factor
                
                # Trust decays slower
                trust_decay = 1.0 - (self._decay_rate * delta_seconds * 0.05)
                relation.trust *= trust_decay
    
    def update_emotional_context(
        self,
        npc_id: str,
        memory_id: str,
        emotional_context: Dict[str, float],
    ):
        """Update emotional context for a memory entry."""
        with self._lock:
            for memory in self._memories.get(npc_id, []):
                if memory.memory_id == memory_id:
                    memory.emotional_context = emotional_context
                    break
    
    def get_graph(self, npc_id: str) -> Optional[EntityGraph]:
        """Get NPC's entity graph."""
        with self._lock:
            return self._npc_graphs.get(npc_id)
    
    def clear_npc(self, npc_id: str):
        """Clear all data for an NPC."""
        with self._lock:
            self._npc_graphs.pop(npc_id, None)
            self._relations.pop(npc_id, None)
            self._memories.pop(npc_id, None)


# Global bridge instance
_bridge_instance: Optional[NPCMemoryBridge] = None
_bridge_lock = threading.Lock()


def get_memory_bridge() -> NPCMemoryBridge:
    """Get the global NPCMemoryBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        with _bridge_lock:
            if _bridge_instance is None:
                _bridge_instance = NPCMemoryBridge()
    return _bridge_instance
