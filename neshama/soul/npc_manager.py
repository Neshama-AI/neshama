# Soul Layer - NPC Manager
"""
NPCManager - Manages multiple NPC soul instances.

Handles CRUD operations for NPC souls with:
- Emotion state management
- Personality profiles
- Entity graph for relationships
- Memory storage
- YAML-based persistence
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import uuid
import yaml
import logging

logger = logging.getLogger(__name__)

# Default NPC data directory
DEFAULT_NPC_DIR = Path(__file__).parent.parent.parent / "npc_data"


@dataclass
class PersonalityProfile:
    """OCEAN personality profile for an NPC."""
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "openness": round(self.openness, 2),
            "conscientiousness": round(self.conscientiousness, 2),
            "extraversion": round(self.extraversion, 2),
            "agreeableness": round(self.agreeableness, 2),
            "neuroticism": round(self.neuroticism, 2),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "PersonalityProfile":
        return cls(
            openness=data.get("openness", 0.5),
            conscientiousness=data.get("conscientiousness", 0.5),
            extraversion=data.get("extraversion", 0.5),
            agreeableness=data.get("agreeableness", 0.5),
            neuroticism=data.get("neuroticism", 0.5),
        )


@dataclass
class NPCSoul:
    """
    Complete soul state for an NPC.
    
    Contains all emotional and memory data for a game NPC.
    """
    npc_id: str
    name: str
    personality: PersonalityProfile
    current_emotions: Dict[str, float] = field(default_factory=dict)
    composite_emotion: Optional[str] = None
    composite_intensity: float = 0.0
    entity_graph_id: Optional[str] = None
    memory_ids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "personality": self.personality.to_dict(),
            "current_emotions": {k: round(v, 4) for k, v in self.current_emotions.items()},
            "composite_emotion": self.composite_emotion,
            "composite_intensity": round(self.composite_intensity, 4),
            "entity_graph_id": self.entity_graph_id,
            "memory_ids": self.memory_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPCSoul":
        """Create from dict."""
        return cls(
            npc_id=data["npc_id"],
            name=data["name"],
            personality=PersonalityProfile.from_dict(data.get("personality", {})),
            current_emotions=data.get("current_emotions", {}),
            composite_emotion=data.get("composite_emotion"),
            composite_intensity=data.get("composite_intensity", 0.0),
            entity_graph_id=data.get("entity_graph_id"),
            memory_ids=data.get("memory_ids", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )


class NPCManager:
    """
    Manager for NPC soul instances.
    
    Handles creation, retrieval, updating, and deletion of NPC souls.
    Persists to YAML files in npc_data directory.
    
    Example:
        >>> manager = NPCManager()
        >>> npc = manager.create_npc("tavern_keeper")
        >>> manager.process_event(npc.npc_id, event)
        >>> profile = manager.get_behavior(npc.npc_id)
    """
    
    def __init__(self, npc_dir: Optional[Path] = None):
        """
        Initialize NPC Manager.
        
        Args:
            npc_dir: Directory for NPC data files (defaults to npc_data/)
        """
        self._npc_dir = npc_dir or DEFAULT_NPC_DIR
        self._npc_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of NPC souls
        self._souls: Dict[str, NPCSoul] = {}
        
        # Fast path instances per NPC
        self._fast_paths: Dict[str, Any] = {}
        
        # Behavior bridge instances per NPC
        self._behavior_bridges: Dict[str, Any] = {}
        
        # Entity graphs per NPC
        self._entity_graphs: Dict[str, Any] = {}
        
        # Load existing NPCs
        self._load_existing()
    
    def _load_existing(self):
        """Load all existing NPCs from disk."""
        for yaml_file in self._npc_dir.glob("*.yaml"):
            if yaml_file.name == "presets":
                continue
            try:
                data = yaml.safe_load(yaml_file.read_text())
                if data:
                    soul = NPCSoul.from_dict(data)
                    self._souls[soul.npc_id] = soul
                    logger.info(f"Loaded NPC: {soul.name} ({soul.npc_id})")
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
    
    def _get_file_path(self, npc_id: str) -> Path:
        """Get file path for NPC."""
        return self._npc_dir / f"{npc_id}.yaml"
    
    def _save_npc(self, soul: NPCSoul):
        """Save NPC soul to disk."""
        soul.updated_at = datetime.now().isoformat()
        file_path = self._get_file_path(soul.npc_id)
        file_path.write_text(yaml.dump(soul.to_dict(), default_flow_style=False))
    
    def create_npc(
        self,
        name: str,
        personality: Optional[Dict[str, float]] = None,
        preset: Optional[str] = None,
        npc_id: Optional[str] = None,
        initial_emotions: Optional[Dict[str, float]] = None,
    ) -> NPCSoul:
        """
        Create a new NPC soul.
        
        Args:
            name: Display name for the NPC
            personality: OCEAN personality scores (0-1 for each trait)
            preset: Use a preset configuration (tavern_keeper, guard_captain)
            npc_id: Optional custom ID (defaults to UUID)
            initial_emotions: Optional initial emotion values (0-1)
            
        Returns:
            Created NPCSoul
        """
        # Generate ID
        new_id = npc_id or str(uuid.uuid4())
        
        # Check for existing
        if new_id in self._souls:
            raise ValueError(f"NPC with ID {new_id} already exists")
        
        # Load preset if specified
        preset_emotions: Dict[str, float] = {}
        if preset:
            preset_data = self._load_preset(preset)
            personality = preset_data["personality"]
            preset_emotions = preset_data.get("initial_emotions", {})
        
        # Default personality if not provided
        if personality is None:
            personality = {
                "openness": 0.5,
                "conscientiousness": 0.5,
                "extraversion": 0.5,
                "agreeableness": 0.5,
                "neuroticism": 0.5,
            }
        
        # Determine initial emotions:
        # 1. Explicit initial_emotions parameter takes highest priority
        # 2. Then preset initial_emotions
        # 3. Then OCEAN-derived initial emotions as fallback
        resolved_emotions: Dict[str, float] = {}
        if not initial_emotions and not preset_emotions:
            resolved_emotions = self._derive_initial_emotions(personality)
        else:
            if preset_emotions:
                resolved_emotions.update(preset_emotions)
            if initial_emotions:
                resolved_emotions.update(initial_emotions)
        
        # Create soul
        soul = NPCSoul(
            npc_id=new_id,
            name=name,
            personality=PersonalityProfile.from_dict(personality),
            current_emotions=resolved_emotions,
        )
        
        # Initialize components
        self._init_components(soul)
        
        # Set initial emotions in the fast path engine
        if resolved_emotions:
            fast_path = self._fast_paths.get(new_id)
            if fast_path:
                for emotion, value in resolved_emotions.items():
                    fast_path._emotion_engine.adjust_emotion(emotion, value)
        
        # Save and cache
        self._souls[new_id] = soul
        self._save_npc(soul)
        
        logger.info(f"Created NPC: {name} ({new_id}) with emotions: {resolved_emotions}")
        return soul
    
    def _init_components(self, soul: NPCSoul):
        """Initialize fast path and behavior bridge for an NPC."""
        from neshama.soul.emotion.fast_path import EmotionFastPath
        from neshama.soul.npc_behavior import NPCBehaviorBridge
        from neshama.soul.entity_graph import EntityGraph
        
        personality = soul.personality.to_dict()
        
        # Fast path
        self._fast_paths[soul.npc_id] = EmotionFastPath(
            neuroticism=personality["neuroticism"],
            personality=personality,
        )
        
        # Behavior bridge
        self._behavior_bridges[soul.npc_id] = NPCBehaviorBridge(
            personality=personality,
        )
        
        # Entity graph
        self._entity_graphs[soul.npc_id] = EntityGraph()
    
    def _load_preset(self, preset_name: str) -> Dict[str, Any]:
        """Load a preset configuration.
        
        Returns dict with 'personality' and optionally 'initial_emotions'.
        """
        preset_dir = self._npc_dir / "presets"
        preset_file = preset_dir / f"{preset_name}.yaml"
        
        if not preset_file.exists():
            raise ValueError(f"Preset '{preset_name}' not found")
        
        data = yaml.safe_load(preset_file.read_text())
        return {
            "personality": data.get("personality", {}),
            "initial_emotions": data.get("initial_emotions", {}),
        }
    
    @staticmethod
    def _derive_initial_emotions(personality: Dict[str, float]) -> Dict[str, float]:
        """Derive initial emotion baselines from OCEAN personality when preset doesn't specify them.
        
        Rules:
        - High extraversion → joy baseline high
        - High neuroticism → fear/sadness baseline high
        - High agreeableness → trust baseline high
        """
        emotions: Dict[str, float] = {}
        
        ext = personality.get("extraversion", 0.5)
        neu = personality.get("neuroticism", 0.5)
        agr = personality.get("agreeableness", 0.5)
        opn = personality.get("openness", 0.5)
        
        # Extraversion → joy
        if ext > 0.6:
            emotions["joy"] = round((ext - 0.5) * 0.6, 2)  # 0.06-0.3
        
        # Neuroticism → fear and sadness
        if neu > 0.6:
            emotions["fear"] = round((neu - 0.5) * 0.4, 2)  # 0.04-0.2
            emotions["sadness"] = round((neu - 0.5) * 0.3, 2)  # 0.03-0.15
        
        # Agreeableness → trust
        if agr > 0.6:
            emotions["trust"] = round((agr - 0.5) * 0.5, 2)  # 0.05-0.25
        
        # Openness → anticipation
        if opn > 0.7:
            emotions["anticipation"] = round((opn - 0.5) * 0.4, 2)  # 0.08-0.2
        
        return emotions
    
    def get_npc(self, npc_id: str) -> Optional[NPCSoul]:
        """Get an NPC soul by ID."""
        return self._souls.get(npc_id)
    
    def list_npcs(self) -> List[NPCSoul]:
        """List all NPCs."""
        return list(self._souls.values())
    
    def delete_npc(self, npc_id: str) -> bool:
        """Delete an NPC."""
        if npc_id not in self._souls:
            return False
        
        # Remove from cache
        del self._souls[npc_id]
        
        # Remove components
        self._fast_paths.pop(npc_id, None)
        self._behavior_bridges.pop(npc_id, None)
        self._entity_graphs.pop(npc_id, None)
        
        # Remove file
        file_path = self._get_file_path(npc_id)
        if file_path.exists():
            file_path.unlink()
        
        logger.info(f"Deleted NPC: {npc_id}")
        return True
    
    def process_event(self, npc_id: str, event) -> Dict[str, Any]:
        """
        Process a game event for an NPC.
        
        Args:
            npc_id: NPC ID
            event: GameEvent from game_event.py
            
        Returns:
            FastPathResult as dict
        """
        if npc_id not in self._souls:
            raise ValueError(f"NPC {npc_id} not found")
        
        fast_path = self._fast_paths.get(npc_id)
        if not fast_path:
            self._init_components(self._souls[npc_id])
            fast_path = self._fast_paths[npc_id]
        
        # Process event
        result = fast_path.process(event)
        
        # Update soul state
        soul = self._souls[npc_id]
        soul.current_emotions = result.emotion_state
        soul.composite_emotion = result.composite_emotion
        soul.composite_intensity = result.composite_intensity
        self._save_npc(soul)
        
        return result.to_dict()
    
    def get_emotion_state(self, npc_id: str) -> Dict[str, Any]:
        """Get current emotion state for an NPC."""
        if npc_id not in self._souls:
            raise ValueError(f"NPC {npc_id} not found")
        
        fast_path = self._fast_paths.get(npc_id)
        if fast_path:
            return fast_path.get_current_state()
        
        soul = self._souls[npc_id]
        return {
            "emotion_state": soul.current_emotions,
            "composite_emotion": soul.composite_emotion,
            "composite_intensity": soul.composite_intensity,
        }
    
    def get_behavior(self, npc_id: str) -> Dict[str, Any]:
        """Get behavior profile for an NPC."""
        if npc_id not in self._souls:
            raise ValueError(f"NPC {npc_id} not found")
        
        soul = self._souls[npc_id]
        
        bridge = self._behavior_bridges.get(npc_id)
        if not bridge:
            self._init_components(soul)
            bridge = self._behavior_bridges[npc_id]
        
        # Get current emotions
        emotion_state = soul.current_emotions
        if not emotion_state and self._fast_paths.get(npc_id):
            emotion_state = self._fast_paths[npc_id].get_current_state()["emotion_state"]
        
        profile = bridge.generate_behavior(emotion_state)
        return profile.to_dict()
    
    def get_profile(self, npc_id: str) -> Dict[str, Any]:
        """Get full NPC profile."""
        soul = self.get_npc(npc_id)
        if not soul:
            raise ValueError(f"NPC {npc_id} not found")
        return soul.to_dict()
    
    def get_entity_graph(self, npc_id: str) -> Optional[Any]:
        """Get entity graph for an NPC."""
        if npc_id not in self._entity_graphs:
            self._init_components(self._souls.get(npc_id))
        return self._entity_graphs.get(npc_id)
    
    def add_relation(
        self,
        npc_id: str,
        entity_id: str,
        relation_type: str,
        weight: float = 0.5,
    ):
        """Add a relationship to NPC's entity graph."""
        from neshama.soul.entity_graph import EntityType
        graph = self.get_entity_graph(npc_id)
        if graph:
            # Add the target entity to the graph (using entity_id as both name and ID)
            graph.add_entity(
                name=entity_id,
                entity_type=EntityType.CUSTOM,
                entity_id=entity_id,
            )
            # Add the NPC itself as a source entity (if not exists)
            graph.add_entity(
                name=npc_id,
                entity_type=EntityType.CUSTOM,
                entity_id=npc_id,
            )
            # Convert string relation_type to RelationType enum
            from neshama.soul.entity_graph import RelationType as RT
            try:
                rel_type = RT(relation_type)
            except ValueError:
                rel_type = RT.CUSTOM
            # Add relation from NPC to entity
            graph.add_relation(npc_id, entity_id, rel_type, weight=weight)
    
    def get_relations(self, npc_id: str) -> List[Dict[str, Any]]:
        """Get all relations for an NPC."""
        graph = self.get_entity_graph(npc_id)
        if not graph:
            return []
        
        edges = graph.get_relations()
        relations = []
        for edge in edges:
            relations.append({
                "from": edge.source_id,
                "to": edge.target_id,
                "relation_type": edge.relation_type.value,
                "weight": edge.weight,
            })
        return relations
    
    def tick(self, npc_id: str, delta_seconds: float):
        """Apply time-based emotion decay."""
        fast_path = self._fast_paths.get(npc_id)
        if fast_path:
            fast_path.tick(delta_seconds)
            # Sync decayed emotions back to soul
            soul = self._souls.get(npc_id)
            if soul:
                state = fast_path.get_current_state()
                soul.current_emotions = state.get("emotion_state", {})
                soul.composite_emotion = state.get("composite_emotion")
                soul.composite_intensity = state.get("composite_intensity", 0.0)
                self._save_npc(soul)
    
    def clear_emotions(self, npc_id: str):
        """Clear all emotions for an NPC."""
        fast_path = self._fast_paths.get(npc_id)
        if fast_path:
            fast_path.clear()
        
        soul = self._souls.get(npc_id)
        if soul:
            soul.current_emotions = {}
            soul.composite_emotion = None
            soul.composite_intensity = 0.0
            self._save_npc(soul)
    
    def list_presets(self) -> List[str]:
        """List available NPC presets."""
        preset_dir = self._npc_dir / "presets"
        if not preset_dir.exists():
            return []
        return [p.stem for p in preset_dir.glob("*.yaml")]
    
    def get_preset_info(self, preset_name: str) -> Dict[str, Any]:
        """Get information about a preset."""
        preset_dir = self._npc_dir / "presets"
        preset_file = preset_dir / f"{preset_name}.yaml"
        
        if not preset_file.exists():
            raise ValueError(f"Preset '{preset_name}' not found")
        
        data = yaml.safe_load(preset_file.read_text())
        return {
            "name": preset_name,
            "description": data.get("description", ""),
            "personality": data.get("personality", {}),
            "initial_emotions": data.get("initial_emotions", {}),
            "dialogue_style": data.get("dialogue_style", ""),
        }


# Global NPC manager instance
_npc_manager: Optional[NPCManager] = None


def get_npc_manager() -> NPCManager:
    """Get or create the global NPC manager instance."""
    global _npc_manager
    if _npc_manager is None:
        _npc_manager = NPCManager()
    return _npc_manager


def create_npc_manager(npc_dir: Optional[Path] = None) -> NPCManager:
    """Create a new NPC manager."""
    global _npc_manager
    _npc_manager = NPCManager(npc_dir=npc_dir)
    return _npc_manager
