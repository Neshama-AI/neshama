# Soul Layer - World Event Module
"""
WorldEventManager - Manages world-level events triggered by story.

Events are advisory - the game engine can choose to ignore them.

Event Types:
- AREA_LOCKDOWN: NPC refuses entry/exit to an area
- PRICE_CHANGE: Shop prices change based on NPC mood
- WEATHER_CHANGE: Weather changes (mood metaphor, optional)
- FACTION_SHIFT: NPC joins/leaves a faction
- SPAWN_ENCOUNTER: Spawn hostile NPCs
- STORY_MILESTONE: Unlock new content
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime
from enum import Enum
import uuid
import logging
import threading

logger = logging.getLogger(__name__)


class WorldEventType(Enum):
    """Types of world events."""
    AREA_LOCKDOWN = "area_lockdown"
    PRICE_CHANGE = "price_change"
    WEATHER_CHANGE = "weather_change"
    FACTION_SHIFT = "faction_shift"
    SPAWN_ENCOUNTER = "spawn_encounter"
    STORY_MILESTONE = "story_milestone"


class EventResolution(Enum):
    """How an event can be resolved."""
    PLAYER_ACTION = "player_action"
    TIME_BASED = "time_based"
    QUEST_COMPLETE = "quest_complete"
    NPC_EMOTION_CHANGE = "npc_emotion_change"
    MANUAL = "manual"


@dataclass
class WorldEvent:
    """A world-level event."""
    event_id: str
    event_type: WorldEventType
    source_npc_id: Optional[str]
    title: str
    description: str
    params: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution: Optional[EventResolution] = None
    resolution_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source_npc_id": self.source_npc_id,
            "title": self.title,
            "description": self.description,
            "params": self.params,
            "created_at": self.created_at.isoformat(),
            "resolved": self.resolved,
            "resolution": self.resolution.value if self.resolution else None,
            "resolution_params": self.resolution_params,
        }


@dataclass
class AreaLockdownParams:
    """Parameters for area lockdown event."""
    area_id: str
    area_name: str
    blocked_npcs: List[str] = field(default_factory=list)  # NPCs blocked
    blocked_players: bool = True
    reason: str = ""  # Why the lockdown happened
    alternative_routes: List[str] = field(default_factory=list)  # Alternative paths
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "area_id": self.area_id,
            "area_name": self.area_name,
            "blocked_npcs": self.blocked_npcs,
            "blocked_players": self.blocked_players,
            "reason": self.reason,
            "alternative_routes": self.alternative_routes,
        }


@dataclass
class PriceChangeParams:
    """Parameters for price change event."""
    shop_id: str
    shop_name: str
    item_ids: List[str] = field(default_factory=list)  # Items affected
    price_multiplier: float = 1.0  # 1.0 = normal, >1 = more expensive, <1 = discount
    duration_seconds: Optional[float] = None  # Optional duration
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "shop_id": self.shop_id,
            "shop_name": self.shop_name,
            "item_ids": self.item_ids,
            "price_multiplier": round(self.price_multiplier, 2),
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class WeatherChangeParams:
    """Parameters for weather change event."""
    area_id: str
    weather_type: str  # "sunny", "rainy", "stormy", "foggy", etc.
    duration_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "area_id": self.area_id,
            "weather_type": self.weather_type,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class FactionShiftParams:
    """Parameters for faction shift event."""
    npc_id: str
    npc_name: str
    old_faction: Optional[str] = None
    new_faction: Optional[str] = None
    faction_change_type: str = "join"  # "join", "leave", "switch"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "npc_name": self.npc_name,
            "old_faction": self.old_faction,
            "new_faction": self.new_faction,
            "faction_change_type": self.faction_change_type,
        }


@dataclass
class SpawnEncounterParams:
    """Parameters for spawn encounter event."""
    spawn_location: str
    enemy_type: str  # Type of enemies to spawn
    enemy_count: int = 1
    behavior: str = "hostile"  # "hostile", "patrol", "defensive"
    trigger_radius: float = 10.0  # How close player needs to be
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "spawn_location": self.spawn_location,
            "enemy_type": self.enemy_type,
            "enemy_count": self.enemy_count,
            "behavior": self.behavior,
            "trigger_radius": self.trigger_radius,
        }


@dataclass
class StoryMilestoneParams:
    """Parameters for story milestone event."""
    milestone_id: str
    milestone_type: str  # "unlock_area", "unlock_npc", "unlock_feature"
    target_id: str  # What to unlock
    title: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "milestone_type": self.milestone_type,
            "target_id": self.target_id,
            "title": self.title,
            "description": self.description,
        }


class WorldEventManager:
    """
    Manages world-level events.
    
    Events are ADVISORY - the game engine can choose to ignore them.
    This system just emits events; actual implementation is up to the game.
    
    Features:
    - Event emission
    - Event subscription
    - Event resolution
    - Session-based event tracking
    
    Example:
        >>> manager = WorldEventManager()
        >>> 
        >>> # Emit a lockdown event
        >>> event = manager.emit_world_event(
        ...     event_type=WorldEventType.AREA_LOCKDOWN,
        ...     source_npc_id="tavern_keeper",
        ...     params={"area_id": "main_door", "reason": "NPC太愤怒"}
        ... )
        >>> 
        >>> # Subscribe to event types
        >>> manager.subscribe_event_type(
        ...     WorldEventType.AREA_LOCKDOWN,
        ...     lambda e: print(f"区域封锁: {e.title}")
        ... )
        >>> 
        >>> # Resolve an event
        >>> manager.resolve_event(event.event_id, resolution="player_action")
    """
    
    def __init__(self):
        """Initialize the world event manager."""
        # Active events: event_id -> WorldEvent
        self._events: Dict[str, WorldEvent] = {}
        
        # Event history: event_id -> WorldEvent (for resolved events)
        self._history: Dict[str, WorldEvent] = {}
        
        # Event subscriptions: event_type -> [callbacks]
        self._subscriptions: Dict[WorldEventType, List[Callable[[WorldEvent], None]]] = defaultdict(list)
        
        # Session-based event tracking: session_id -> [event_ids]
        self._session_events: Dict[str, Set[str]] = defaultdict(set)
        
        # All event types for iteration
        for event_type in WorldEventType:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []
        
        # Thread lock
        self._lock = threading.Lock()
        
        logger.info("WorldEventManager initialized")
    
    def emit_world_event(
        self,
        event_type: WorldEventType,
        source_npc_id: Optional[str],
        title: str = "",
        description: str = "",
        params: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> WorldEvent:
        """
        Emit a world event.
        
        Args:
            event_type: Type of event
            source_npc_id: NPC that triggered the event
            title: Event title
            description: Event description
            params: Event-specific parameters
            session_id: Optional session to track event for
            
        Returns:
            Created WorldEvent
        """
        params = params or {}
        event_id = str(uuid.uuid4())
        
        event = WorldEvent(
            event_id=event_id,
            event_type=event_type,
            source_npc_id=source_npc_id,
            title=title or self._get_default_title(event_type),
            description=description or self._get_default_description(event_type, params),
            params=params,
        )
        
        with self._lock:
            self._events[event_id] = event
            
            if session_id:
                self._session_events[session_id].add(event_id)
        
        # Notify subscribers
        for callback in self._subscriptions[event_type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Subscription callback error: {e}")
        
        logger.info(f"World event emitted: {event_id} ({event_type.value})")
        return event
    
    def _get_default_title(self, event_type: WorldEventType) -> str:
        """Get default title for event type."""
        titles = {
            WorldEventType.AREA_LOCKDOWN: "区域封锁",
            WorldEventType.PRICE_CHANGE: "价格变动",
            WorldEventType.WEATHER_CHANGE: "天气变化",
            WorldEventType.FACTION_SHIFT: "阵营变动",
            WorldEventType.SPAWN_ENCOUNTER: "遭遇生成",
            WorldEventType.STORY_MILESTONE: "故事里程碑",
        }
        return titles.get(event_type, "世界事件")
    
    def _get_default_description(self, event_type: WorldEventType, params: Dict[str, Any]) -> str:
        """Get default description for event type."""
        if event_type == WorldEventType.AREA_LOCKDOWN:
            area_name = params.get("area_name", "某区域")
            reason = params.get("reason", "未知原因")
            return f"{area_name}因\"{reason}\"被封锁"
        
        elif event_type == WorldEventType.PRICE_CHANGE:
            shop_name = params.get("shop_name", "商店")
            multiplier = params.get("price_multiplier", 1.0)
            if multiplier > 1.0:
                return f"{shop_name}涨价了"
            elif multiplier < 1.0:
                return f"{shop_name}打折了"
            return f"{shop_name}价格变动"
        
        elif event_type == WorldEventType.WEATHER_CHANGE:
            weather = params.get("weather_type", "未知")
            return f"天气变为{weather}"
        
        elif event_type == WorldEventType.FACTION_SHIFT:
            npc_name = params.get("npc_name", "NPC")
            new_faction = params.get("new_faction", "")
            return f"{npc_name}加入了{new_faction if new_faction else '某阵营'}"
        
        elif event_type == WorldEventType.SPAWN_ENCOUNTER:
            enemy_type = params.get("enemy_type", "敌人")
            location = params.get("spawn_location", "某地")
            return f"{location}出现了{enemy_type}"
        
        elif event_type == WorldEventType.STORY_MILESTONE:
            title = params.get("title", "新内容")
            return f"解锁: {title}"
        
        return "世界发生了变化"
    
    def get_active_events(
        self,
        session_id: Optional[str] = None,
        event_type: Optional[WorldEventType] = None,
    ) -> List[WorldEvent]:
        """
        Get active events.
        
        Args:
            session_id: Filter by session (returns only events for that session)
            event_type: Filter by event type
            
        Returns:
            List of active events
        """
        with self._lock:
            events = list(self._events.values())
        
        # Filter by session
        if session_id:
            event_ids = self._session_events.get(session_id, set())
            events = [e for e in events if e.event_id in event_ids]
        
        # Filter by type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events
    
    def get_event(self, event_id: str) -> Optional[WorldEvent]:
        """Get an event by ID."""
        if event_id in self._events:
            return self._events[event_id]
        if event_id in self._history:
            return self._history[event_id]
        return None
    
    def resolve_event(
        self,
        event_id: str,
        resolution: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Resolve a world event.
        
        Args:
            event_id: Event to resolve
            resolution: Resolution type
            params: Optional resolution parameters
            
        Returns:
            True if resolved, False if event not found
        """
        event = self._events.get(event_id)
        if not event:
            return False
        
        try:
            resolution_enum = EventResolution(resolution)
        except ValueError:
            resolution_enum = EventResolution.MANUAL
        
        with self._lock:
            event.resolved = True
            event.resolution = resolution_enum
            event.resolution_params = params or {}
            
            # Move to history
            del self._events[event_id]
            self._history[event_id] = event
        
        # Notify subscribers of resolution
        for callback in self._subscriptions[event.event_type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Subscription callback error: {e}")
        
        logger.info(f"World event resolved: {event_id} ({resolution})")
        return True
    
    def subscribe_event_type(
        self,
        event_type: WorldEventType,
        callback: Callable[[WorldEvent], None],
    ):
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Event type to subscribe to
            callback: Function to call when event is emitted
        """
        self._subscriptions[event_type].append(callback)
    
    def unsubscribe_event_type(
        self,
        event_type: WorldEventType,
        callback: Callable[[WorldEvent], None],
    ):
        """Unsubscribe from an event type."""
        if callback in self._subscriptions[event_type]:
            self._subscriptions[event_type].remove(callback)
    
    def clear_session_events(self, session_id: str):
        """Clear all events for a session (does not resolve them)."""
        with self._lock:
            event_ids = self._session_events.pop(session_id, set())
            for event_id in event_ids:
                if event_id in self._events:
                    del self._events[event_id]
    
    def get_event_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[WorldEvent]:
        """Get event history."""
        with self._lock:
            history = list(self._history.values())
        
        # Sort by created_at descending
        history.sort(key=lambda e: e.created_at, reverse=True)
        
        # Filter by session if specified
        if session_id:
            event_ids = self._session_events.get(session_id, set())
            history = [e for e in history if e.event_id in event_ids]
        
        return history[:limit]


# Helper functions for creating common events

def create_area_lockdown_event(
    source_npc_id: str,
    area_id: str,
    area_name: str,
    reason: str = "",
    alternative_routes: Optional[List[str]] = None,
    session_id: Optional[str] = None,
) -> WorldEvent:
    """Create an area lockdown event."""
    manager = get_world_event_manager()
    return manager.emit_world_event(
        event_type=WorldEventType.AREA_LOCKDOWN,
        source_npc_id=source_npc_id,
        params=AreaLockdownParams(
            area_id=area_id,
            area_name=area_name,
            reason=reason,
            alternative_routes=alternative_routes or [],
        ).to_dict(),
        session_id=session_id,
    )


def create_price_change_event(
    source_npc_id: str,
    shop_id: str,
    shop_name: str,
    price_multiplier: float,
    duration_seconds: Optional[float] = None,
    session_id: Optional[str] = None,
) -> WorldEvent:
    """Create a price change event."""
    manager = get_world_event_manager()
    return manager.emit_world_event(
        event_type=WorldEventType.PRICE_CHANGE,
        source_npc_id=source_npc_id,
        params=PriceChangeParams(
            shop_id=shop_id,
            shop_name=shop_name,
            price_multiplier=price_multiplier,
            duration_seconds=duration_seconds,
        ).to_dict(),
        session_id=session_id,
    )


def create_faction_shift_event(
    source_npc_id: str,
    npc_name: str,
    old_faction: Optional[str],
    new_faction: Optional[str],
    session_id: Optional[str] = None,
) -> WorldEvent:
    """Create a faction shift event."""
    manager = get_world_event_manager()
    change_type = "switch" if (old_faction and new_faction) else ("join" if new_faction else "leave")
    return manager.emit_world_event(
        event_type=WorldEventType.FACTION_SHIFT,
        source_npc_id=source_npc_id,
        params=FactionShiftParams(
            npc_id=source_npc_id,
            npc_name=npc_name,
            old_faction=old_faction,
            new_faction=new_faction,
            faction_change_type=change_type,
        ).to_dict(),
        session_id=session_id,
    )


# Global instance
_global_manager: Optional[WorldEventManager] = None


def get_world_event_manager() -> WorldEventManager:
    """Get the global world event manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = WorldEventManager()
    return _global_manager


def create_world_event_manager() -> WorldEventManager:
    """Create a new world event manager (for testing)."""
    return WorldEventManager()
