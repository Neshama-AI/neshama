# Soul Layer - Quest System Module
"""
DynamicQuestSystem - Emotion-driven dynamic quest generation and management.

Generates quests dynamically based on NPC emotional states and relationships.
Quests can affect NPC emotions when completed or failed.

Features:
- Quest template system
- Dynamic quest generation
- Quest progress tracking
- Emotional aftermath of quests
- Quest-to-trigger integration

Quest Templates:
- angry_lockdown: NPC anger triggers lockdown quest
- sad_quest: NPC sadness triggers search quest
- betrayal_revenge: NPC betrayal triggers revenge quest
- trust_secret: High trust unlocks secret quest
- friend_favor: Friend NPC requests help
- multi_npc_conspiracy: Multiple NPCs conspire, player chooses side
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime
from enum import Enum
import uuid
import logging
import threading
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class QuestStatus(Enum):
    """Quest status."""
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestEffectType(Enum):
    """Types of effects when quest completes/fails."""
    EMOTION_MODIFY = "emotion_modify"
    RELATIONSHIP_CHANGE = "relationship_change"
    UNLOCK_QUEST = "unlock_quest"
    UNLOCK_DIALOGUE = "unlock_dialogue"
    SPAWN_NPC = "spawn_npc"
    WORLD_EVENT = "world_event"


@dataclass
class QuestTrigger:
    """Condition for quest to appear."""
    emotion: str
    threshold: float = 0.5
    direction: str = "rising"  # "rising" or "any"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion": self.emotion,
            "threshold": self.threshold,
            "direction": self.direction,
        }


@dataclass
class QuestCondition:
    """Condition for quest completion."""
    condition_type: str  # "talk_to_npc", "kill_npc", "collect_item", "reach_location", "emotion_state"
    target: str
    value: Optional[float] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_type": self.condition_type,
            "target": self.target,
            "value": self.value,
            "description": self.description,
        }


@dataclass
class QuestReward:
    """Quest reward."""
    reward_type: str  # "item", "gold", "reputation", "emotion_modify"
    target: str  # Item ID, faction, emotion name
    value: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reward_type": self.reward_type,
            "target": self.target,
            "value": self.value,
        }


@dataclass
class QuestEmotionalEffect:
    """Effect on NPC emotions after quest completes/fails."""
    emotion: str
    value: float  # Positive = increase, Negative = decrease
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion": self.emotion,
            "value": self.value,
        }


@dataclass
class QuestTemplate:
    """Template for generating quests."""
    template_id: str
    title: str
    description: str
    giver_npc: str  # NPC ID that gives the quest
    trigger: QuestTrigger
    completion_conditions: List[QuestCondition]
    rewards: List[QuestReward] = field(default_factory=list)
    emotional_success: List[QuestEmotionalEffect] = field(default_factory=list)
    emotional_failure: List[QuestEmotionalEffect] = field(default_factory=list)
    related_triggers: List[str] = field(default_factory=list)  # Story triggers this quest might activate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "title": self.title,
            "description": self.description,
            "giver_npc": self.giver_npc,
            "trigger": self.trigger.to_dict(),
            "completion_conditions": [c.to_dict() for c in self.completion_conditions],
            "rewards": [r.to_dict() for r in self.rewards],
            "emotional_success": [e.to_dict() for e in self.emotional_success],
            "emotional_failure": [e.to_dict() for e in self.emotional_failure],
            "related_triggers": self.related_triggers,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestTemplate":
        return cls(
            template_id=data["template_id"],
            title=data["title"],
            description=data["description"],
            giver_npc=data["giver_npc"],
            trigger=QuestTrigger(
                emotion=data["trigger"]["emotion"],
                threshold=data["trigger"].get("threshold", 0.5),
                direction=data["trigger"].get("direction", "rising"),
            ),
            completion_conditions=[
                QuestCondition(
                    condition_type=c["condition_type"],
                    target=c["target"],
                    value=c.get("value"),
                    description=c.get("description", ""),
                )
                for c in data.get("completion_conditions", [])
            ],
            rewards=[
                QuestReward(
                    reward_type=r["reward_type"],
                    target=r["target"],
                    value=r.get("value", 0.0),
                )
                for r in data.get("rewards", [])
            ],
            emotional_success=[
                QuestEmotionalEffect(emotion=e["emotion"], value=e["value"])
                for e in data.get("emotional_success", [])
            ],
            emotional_failure=[
                QuestEmotionalEffect(emotion=e["emotion"], value=e["value"])
                for e in data.get("emotional_failure", [])
            ],
            related_triggers=data.get("related_triggers", []),
        )


@dataclass
class ActiveQuest:
    """An active quest instance."""
    quest_id: str
    template_id: str
    title: str
    description: str
    giver_npc: str
    status: QuestStatus
    progress: Dict[str, Any] = field(default_factory=dict)  # condition_key -> completed
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "quest_id": self.quest_id,
            "template_id": self.template_id,
            "title": self.title,
            "description": self.description,
            "giver_npc": self.giver_npc,
            "status": self.status.value,
            "progress": self.progress,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
        }


class DynamicQuestSystem:
    """
    Dynamic quest system based on NPC emotions.
    
    Manages:
    - Quest templates
    - Available quests
    - Active quests
    - Quest completion/failure effects
    
    Example:
        >>> system = DynamicQuestSystem()
        >>> 
        >>> # Check for available quests based on NPC emotions
        >>> available = system.check_quest_triggers(
        ...     npc_id="tavern_keeper",
        ...     emotion_state={"anger": 0.8}
        ... )
        >>> 
        >>> # Accept a quest
        >>> quest = system.generate_quest("angry_lockdown", "tavern_keeper")
        >>> 
        >>> # Update progress
        >>> system.update_quest_progress(quest.quest_id, {"type": "talk_to_npc", "target": "guard_captain"})
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the quest system.
        
        Args:
            templates_dir: Directory containing quest template YAML files
        """
        # Quest templates
        self._templates: Dict[str, QuestTemplate] = {}
        
        # Available quests (not yet accepted)
        self._available_quests: Dict[str, ActiveQuest] = {}
        
        # Active quests (accepted)
        self._active_quests: Dict[str, ActiveQuest] = {}
        
        # Completed quests
        self._completed_quests: Dict[str, ActiveQuest] = {}
        
        # Failed quests
        self._failed_quests: Dict[str, ActiveQuest] = {}
        
        # Quest-to-emotion callbacks
        self._emotion_callbacks: List[Callable[[str, str, List[QuestEmotionalEffect]], None]] = []
        
        # Callbacks for quest events
        self._callbacks: Dict[str, List[Callable]] = {
            "quest_available": [],
            "quest_accepted": [],
            "quest_progress": [],
            "quest_completed": [],
            "quest_failed": [],
        }
        
        self._lock = threading.Lock()
        
        # Load templates
        if templates_dir:
            self._load_templates(templates_dir)
        else:
            self._load_default_templates()
        
        logger.info(f"DynamicQuestSystem initialized with {len(self._templates)} templates")
    
    def _load_templates(self, templates_dir: Path):
        """Load quest templates from directory."""
        if not templates_dir.exists():
            logger.warning(f"Templates directory not found: {templates_dir}")
            self._load_default_templates()
            return
        
        for yaml_file in templates_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(yaml_file.read_text())
                if data:
                    template = QuestTemplate.from_dict(data)
                    self._templates[template.template_id] = template
                    logger.info(f"Loaded template: {template.template_id}")
            except Exception as e:
                logger.error(f"Failed to load template {yaml_file}: {e}")
    
    def _load_default_templates(self):
        """Load default quest templates."""
        # These are built-in templates that always exist
        self._templates = {
            "angry_lockdown": QuestTemplate(
                template_id="angry_lockdown",
                title="打破封锁",
                description="NPC因愤怒封锁了某个区域，玩家需要安抚NPC或强行通过。",
                giver_npc="",  # Set dynamically
                trigger=QuestTrigger(emotion="anger", threshold=0.7),
                completion_conditions=[
                    QuestCondition(
                        condition_type="emotion_state",
                        target="anger",
                        value=0.4,
                        description="安抚NPC使其愤怒降低",
                    ),
                    QuestCondition(
                        condition_type="alternative_path",
                        target="",
                        description="找到其他方式绕过封锁",
                    ),
                ],
                rewards=[
                    QuestReward(reward_type="reputation", target="town", value=10),
                ],
                emotional_success=[
                    QuestEmotionalEffect(emotion="trust", value=0.2),
                    QuestEmotionalEffect(emotion="joy", value=0.1),
                ],
                emotional_failure=[
                    QuestEmotionalEffect(emotion="anger", value=0.2),
                    QuestEmotionalEffect(emotion="contempt", value=0.1),
                ],
                related_triggers=["anger_lockdown_resolved"],
            ),
            "sad_quest": QuestTemplate(
                template_id="sad_quest",
                title="寻找失落之物",
                description="NPC因悲伤委托玩家寻找遗失的重要物品。",
                giver_npc="",
                trigger=QuestTrigger(emotion="sadness", threshold=0.6),
                completion_conditions=[
                    QuestCondition(
                        condition_type="collect_item",
                        target="lost_item",
                        description="找到NPC遗失的物品",
                    ),
                ],
                rewards=[
                    QuestReward(reward_type="item", target="consolation_gift", value=1),
                    QuestReward(reward_type="gold", target="", value=50),
                ],
                emotional_success=[
                    QuestEmotionalEffect(emotion="joy", value=0.3),
                    QuestEmotionalEffect(emotion="gratitude", value=0.2),
                ],
                emotional_failure=[
                    QuestEmotionalEffect(emotion="sadness", value=0.1),
                ],
                related_triggers=["sadness_relieved"],
            ),
            "betrayal_revenge": QuestTemplate(
                template_id="betrayal_revenge",
                title="复仇任务",
                description="NPC被背叛后委托玩家进行复仇。",
                giver_npc="",
                trigger=QuestTrigger(emotion="anger", threshold=0.6),
                completion_conditions=[
                    QuestCondition(
                        condition_type="defeat_npc",
                        target="target",
                        description="击败背叛者",
                    ),
                ],
                rewards=[
                    QuestReward(reward_type="reputation", target="faction", value=20),
                    QuestReward(reward_type="item", target="revenge_token", value=1),
                ],
                emotional_success=[
                    QuestEmotionalEffect(emotion="satisfaction", value=0.3),
                    QuestEmotionalEffect(emotion="trust", value=0.1),
                ],
                emotional_failure=[
                    QuestEmotionalEffect(emotion="despair", value=0.2),
                    QuestEmotionalEffect(emotion="anger", value=0.1),
                ],
                related_triggers=["betrayal_avenged"],
            ),
            "trust_secret": QuestTemplate(
                template_id="trust_secret",
                title="秘密任务",
                description="NPC信任玩家后透露秘密任务线。",
                giver_npc="",
                trigger=QuestTrigger(emotion="trust", threshold=0.7),
                completion_conditions=[
                    QuestCondition(
                        condition_type="complete_task",
                        target="secret_task",
                        description="完成NPC委托的秘密任务",
                    ),
                ],
                rewards=[
                    QuestReward(reward_type="reputation", target="secret_faction", value=30),
                    QuestReward(reward_type="emotion_modify", target="joy", value=0.2),
                ],
                emotional_success=[
                    QuestEmotionalEffect(emotion="trust", value=0.1),
                    QuestEmotionalEffect(emotion="bond", value=0.2),
                ],
                emotional_failure=[
                    QuestEmotionalEffect(emotion="trust", value=-0.3),
                    QuestEmotionalEffect(emotion="betrayal", value=0.2),
                ],
                related_triggers=["secret_unlocked"],
            ),
            "friend_favor": QuestTemplate(
                template_id="friend_favor",
                title="朋友之请",
                description="友好的NPC请求玩家帮忙。",
                giver_npc="",
                trigger=QuestTrigger(emotion="trust", threshold=0.5),
                completion_conditions=[
                    QuestCondition(
                        condition_type="help_npc",
                        target="friend_npc",
                        description="帮助朋友的NPC",
                    ),
                ],
                rewards=[
                    QuestReward(reward_type="reputation", target="friends", value=15),
                    QuestReward(reward_type="gold", target="", value=30),
                ],
                emotional_success=[
                    QuestEmotionalEffect(emotion="joy", value=0.2),
                    QuestEmotionalEffect(emotion="trust", value=0.1),
                ],
                emotional_failure=[
                    QuestEmotionalEffect(emotion="sadness", value=0.1),
                    QuestEmotionalEffect(emotion="disappointment", value=0.1),
                ],
                related_triggers=["friendship_deepened"],
            ),
            "multi_npc_conspiracy": QuestTemplate(
                template_id="multi_npc_conspiracy",
                title="站队抉择",
                description="多个NPC合谋，玩家需要选择站在哪一边。",
                giver_npc="",
                trigger=QuestTrigger(emotion="anger", threshold=0.5),
                completion_conditions=[
                    QuestCondition(
                        condition_type="choose_side",
                        target="faction",
                        description="选择支持某一派系",
                    ),
                ],
                rewards=[
                    QuestReward(reward_type="reputation", target="chosen_faction", value=40),
                ],
                emotional_success=[
                    QuestEmotionalEffect(emotion="trust", value=0.3),
                ],
                emotional_failure=[
                    QuestEmotionalEffect(emotion="anger", value=0.2),
                    QuestEmotionalEffect(emotion="hostility", value=0.2),
                ],
                related_triggers=["conspiracy_revealed"],
            ),
        }
    
    def register_template(self, template: QuestTemplate) -> bool:
        """Register a quest template."""
        with self._lock:
            if template.template_id in self._templates:
                logger.warning(f"Template {template.template_id} already exists")
                return False
            
            self._templates[template.template_id] = template
            logger.info(f"Registered template: {template.template_id}")
            return True
    
    def get_template(self, template_id: str) -> Optional[QuestTemplate]:
        """Get a quest template."""
        return self._templates.get(template_id)
    
    def list_templates(self) -> List[QuestTemplate]:
        """List all quest templates."""
        return list(self._templates.values())
    
    def check_quest_triggers(
        self,
        npc_id: str,
        emotion_state: Dict[str, float],
    ) -> List[QuestTemplate]:
        """
        Check if any quest should become available for an NPC.
        
        Args:
            npc_id: NPC identifier
            emotion_state: Current emotion state of the NPC
            
        Returns:
            List of newly available quest templates
        """
        available = []
        
        for template in self._templates.values():
            # Skip if already available or active
            if self._is_quest_available(template.template_id, npc_id):
                continue
            
            # Check trigger condition
            trigger = template.trigger
            emotion_value = emotion_state.get(trigger.emotion, 0.0)
            
            if trigger.direction == "rising":
                if emotion_value >= trigger.threshold:
                    available.append(template)
            else:  # "any"
                if emotion_value >= trigger.threshold:
                    available.append(template)
        
        return available
    
    def _is_quest_available(self, template_id: str, npc_id: str) -> bool:
        """Check if quest is already available or active."""
        key = f"{template_id}:{npc_id}"
        
        if key in self._available_quests:
            return True
        
        for quest in self._active_quests.values():
            if quest.template_id == template_id and quest.giver_npc == npc_id:
                return True
        
        return False
    
    def generate_quest(
        self,
        template_id: str,
        npc_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[ActiveQuest]:
        """
        Generate a quest from a template.
        
        Args:
            template_id: Template to use
            npc_id: NPC giving the quest
            params: Optional parameters for customization
            
        Returns:
            Generated quest or None if template not found or quest already exists
        """
        template = self._templates.get(template_id)
        if not template:
            logger.warning(f"Template {template_id} not found")
            return None
        
        # Check if quest already exists for this NPC
        if self._is_quest_available(template_id, npc_id):
            logger.warning(f"Quest {template_id} already available or active for {npc_id}")
            return None
        
        params = params or {}
        quest_id = str(uuid.uuid4())
        
        # Customize title/description if params provided
        title = params.get("title", template.title)
        description = params.get("description", template.description)
        
        quest = ActiveQuest(
            quest_id=quest_id,
            template_id=template_id,
            title=title,
            description=description,
            giver_npc=npc_id,
            status=QuestStatus.AVAILABLE,
            progress={},
        )
        
        # Store as available
        key = quest_id  # Use quest_id as key for easy lookup
        self._available_quests[key] = quest
        
        # Notify callbacks
        for callback in self._callbacks["quest_available"]:
            try:
                callback(quest)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        logger.info(f"Generated quest {quest_id} from template {template_id}")
        return quest
    
    def accept_quest(self, quest_id: str) -> Optional[ActiveQuest]:
        """
        Accept a quest.
        
        Args:
            quest_id: Quest to accept
            
        Returns:
            Accepted quest or None
        """
        with self._lock:
            # Find quest in available
            quest = None
            key = None
            for k, q in self._available_quests.items():
                if q.quest_id == quest_id:
                    quest = q
                    key = k
                    break
            
            if not quest:
                return None
            
            # Move to active
            quest.status = QuestStatus.ACTIVE
            quest.accepted_at = datetime.now()
            del self._available_quests[key]
            self._active_quests[quest_id] = quest
            
            # Notify callbacks
            for callback in self._callbacks["quest_accepted"]:
                try:
                    callback(quest)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            logger.info(f"Quest {quest_id} accepted")
            return quest
    
    def update_quest_progress(
        self,
        quest_id: str,
        event: Dict[str, Any],
    ) -> Optional[ActiveQuest]:
        """
        Update quest progress based on game event.
        
        Args:
            quest_id: Quest to update
            event: Game event that might affect progress
            
        Returns:
            Updated quest or None
        """
        quest = self._active_quests.get(quest_id)
        if not quest:
            return None
        
        template = self._templates.get(quest.template_id)
        if not template:
            return None
        
        event_type = event.get("type")
        event_target = event.get("target")
        
        # Check each completion condition
        all_complete = True
        for condition in template.completion_conditions:
            cond_key = f"{condition.condition_type}:{condition.target}"
            
            if cond_key not in quest.progress:
                # Check if this event completes the condition
                if self._check_condition(condition, event_type, event_target, event):
                    quest.progress[cond_key] = True
                else:
                    all_complete = False
        
        # Notify progress callbacks
        for callback in self._callbacks["quest_progress"]:
            try:
                callback(quest, event)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        # Auto-complete if all conditions met
        if all_complete and quest.progress:
            self.complete_quest(quest_id)
        
        return quest
    
    def _check_condition(
        self,
        condition: QuestCondition,
        event_type: str,
        event_target: str,
        event: Dict[str, Any],
    ) -> bool:
        """Check if an event satisfies a condition."""
        cond_type = condition.condition_type
        
        if cond_type == "talk_to_npc":
            return event_type == "npc_interaction" and event_target == condition.target
        
        elif cond_type == "kill_npc":
            return event_type == "npc_defeated" and event_target == condition.target
        
        elif cond_type == "collect_item":
            return event_type == "item_collected" and event_target == condition.target
        
        elif cond_type == "reach_location":
            return event_type == "location_reached" and event_target == condition.target
        
        elif cond_type == "emotion_state":
            # For emotion conditions, this would be triggered by story engine
            return event_type == "emotion_state" and event_target == condition.target
        
        elif cond_type == "alternative_path":
            return event_type == "alternative_action" and condition.target in event.get("actions", [])
        
        return False
    
    def complete_quest(self, quest_id: str) -> Optional[ActiveQuest]:
        """
        Mark a quest as completed.
        
        Args:
            quest_id: Quest to complete
            
        Returns:
            Completed quest or None
        """
        quest = self._active_quests.get(quest_id)
        if not quest:
            return None
        
        template = self._templates.get(quest.template_id)
        
        with self._lock:
            quest.status = QuestStatus.COMPLETED
            quest.completed_at = datetime.now()
            
            del self._active_quests[quest_id]
            self._completed_quests[quest_id] = quest
        
        # Apply emotional effects
        if template:
            self._apply_emotional_effects(
                quest.giver_npc,
                template.emotional_success
            )
            
            # Notify emotion callbacks
            for callback in self._emotion_callbacks:
                try:
                    callback(quest.giver_npc, "complete", template.emotional_success)
                except Exception as e:
                    logger.error(f"Emotion callback error: {e}")
        
        # Notify callbacks
        for callback in self._callbacks["quest_completed"]:
            try:
                callback(quest)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        logger.info(f"Quest {quest_id} completed")
        return quest
    
    def fail_quest(self, quest_id: str) -> Optional[ActiveQuest]:
        """
        Mark a quest as failed.
        
        Args:
            quest_id: Quest to fail
            
        Returns:
            Failed quest or None
        """
        quest = self._active_quests.get(quest_id)
        if not quest:
            return None
        
        template = self._templates.get(quest.template_id)
        
        with self._lock:
            quest.status = QuestStatus.FAILED
            quest.failed_at = datetime.now()
            
            del self._active_quests[quest_id]
            self._failed_quests[quest_id] = quest
        
        # Apply emotional effects (failure)
        if template:
            self._apply_emotional_effects(
                quest.giver_npc,
                template.emotional_failure
            )
            
            # Notify emotion callbacks
            for callback in self._emotion_callbacks:
                try:
                    callback(quest.giver_npc, "fail", template.emotional_failure)
                except Exception as e:
                    logger.error(f"Emotion callback error: {e}")
        
        # Notify callbacks
        for callback in self._callbacks["quest_failed"]:
            try:
                callback(quest)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        logger.info(f"Quest {quest_id} failed")
        return quest
    
    def _apply_emotional_effects(
        self,
        npc_id: str,
        effects: List[QuestEmotionalEffect],
    ):
        """Apply emotional effects to an NPC (to be integrated with EmotionDriver)."""
        # This will be called by the game engine to modify emotions
        # The actual implementation should call EmotionDriver
        pass
    
    def subscribe_emotion_callback(
        self,
        callback: Callable[[str, str, List[QuestEmotionalEffect]], None],
    ):
        """Subscribe to emotion change callbacks."""
        self._emotion_callbacks.append(callback)
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to quest events."""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def get_available_quests(self, npc_id: Optional[str] = None) -> List[ActiveQuest]:
        """Get available (not yet accepted) quests."""
        if npc_id:
            return [q for q in self._available_quests.values() if q.giver_npc == npc_id]
        return list(self._available_quests.values())
    
    def get_active_quests(self, npc_id: Optional[str] = None) -> List[ActiveQuest]:
        """Get active (accepted) quests."""
        if npc_id:
            return [q for q in self._active_quests.values() if q.giver_npc == npc_id]
        return list(self._active_quests.values())
    
    def get_quest(self, quest_id: str) -> Optional[ActiveQuest]:
        """Get a quest by ID (from any status)."""
        if quest_id in self._available_quests:
            return self._available_quests[quest_id]
        if quest_id in self._active_quests:
            return self._active_quests[quest_id]
        if quest_id in self._completed_quests:
            return self._completed_quests[quest_id]
        if quest_id in self._failed_quests:
            return self._failed_quests[quest_id]
        return None


# Global instance
_global_quest_system: Optional[DynamicQuestSystem] = None


def get_quest_system() -> DynamicQuestSystem:
    """Get the global quest system instance."""
    global _global_quest_system
    if _global_quest_system is None:
        _global_quest_system = DynamicQuestSystem()
    return _global_quest_system


def create_quest_system() -> DynamicQuestSystem:
    """Create a new quest system (for testing)."""
    return DynamicQuestSystem()
