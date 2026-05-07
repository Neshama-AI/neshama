"""
Neshama World Events Tests
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.world_events import (
    WorldEventManager,
    WorldEvent,
    WorldEventType,
    EventResolution,
    AreaLockdownParams,
    PriceChangeParams,
    WeatherChangeParams,
    FactionShiftParams,
    SpawnEncounterParams,
    StoryMilestoneParams,
    create_world_event_manager,
    get_world_event_manager,
)


class TestWorldEventInit:
    """Tests for WorldEventManager initialization."""

    def test_default_init(self):
        """Test default initialization."""
        manager = create_world_event_manager()
        assert manager is not None
        assert len(manager.get_active_events()) == 0


class TestAreaLockdown:
    """Tests for AREA_LOCKDOWN event type."""

    def test_emit_lockdown(self):
        """Test emitting an area lockdown event."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.AREA_LOCKDOWN,
            source_npc_id="tavern_keeper",
            title="酒馆封锁",
            description="老板娘封锁了酒馆",
            params=AreaLockdownParams(
                area_id="tavern_main",
                area_name="酒馆大厅",
                reason="太生气了",
                alternative_routes=["side_door", "window"],
            ).to_dict(),
        )
        
        assert event is not None
        assert event.event_type == WorldEventType.AREA_LOCKDOWN
        assert event.source_npc_id == "tavern_keeper"
        assert event.resolved is False
        assert event.params["area_name"] == "酒馆大厅"

    def test_get_active_lockdowns(self):
        """Test getting active lockdown events."""
        manager = create_world_event_manager()
        
        manager.emit_world_event(
            event_type=WorldEventType.AREA_LOCKDOWN,
            source_npc_id="tavern_keeper",
            params={"area_id": "tavern_main"},
        )
        
        manager.emit_world_event(
            event_type=WorldEventType.AREA_LOCKDOWN,
            source_npc_id="guard_captain",
            params={"area_id": "city_gate"},
        )
        
        events = manager.get_active_events(event_type=WorldEventType.AREA_LOCKDOWN)
        assert len(events) == 2


class TestPriceChange:
    """Tests for PRICE_CHANGE event type."""

    def test_emit_price_increase(self):
        """Test emitting a price increase event."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.PRICE_CHANGE,
            source_npc_id="angry_merchant",
            params=PriceChangeParams(
                shop_id="general_store",
                shop_name="杂货店",
                price_multiplier=1.5,  # 50% more expensive
            ).to_dict(),
        )
        
        assert event is not None
        assert event.params["price_multiplier"] == 1.5

    def test_emit_discount(self):
        """Test emitting a discount event."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.PRICE_CHANGE,
            source_npc_id="happy_merchant",
            params=PriceChangeParams(
                shop_id="general_store",
                shop_name="杂货店",
                price_multiplier=0.7,  # 30% discount
                duration_seconds=3600,  # 1 hour
            ).to_dict(),
        )
        
        assert event is not None
        assert event.params["price_multiplier"] == 0.7
        assert event.params["duration_seconds"] == 3600


class TestWeatherChange:
    """Tests for WEATHER_CHANGE event type."""

    def test_emit_weather_change(self):
        """Test emitting a weather change event."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.WEATHER_CHANGE,
            source_npc_id=None,  # Weather not from NPC
            params=WeatherChangeParams(
                area_id="town",
                weather_type="stormy",
                duration_seconds=1800,
            ).to_dict(),
        )
        
        assert event is not None
        assert event.params["weather_type"] == "stormy"


class TestFactionShift:
    """Tests for FACTION_SHIFT event type."""

    def test_emit_faction_join(self):
        """Test emitting a faction join event."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.FACTION_SHIFT,
            source_npc_id="guard_captain",
            params=FactionShiftParams(
                npc_id="guard_captain",
                npc_name="守卫队长",
                new_faction="royal_guard",
                faction_change_type="join",
            ).to_dict(),
        )
        
        assert event is not None
        assert event.params["new_faction"] == "royal_guard"
        assert event.params["faction_change_type"] == "join"

    def test_emit_faction_switch(self):
        """Test emitting a faction switch event."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.FACTION_SHIFT,
            source_npc_id="mercenary",
            params=FactionShiftParams(
                npc_id="mercenary",
                npc_name="雇佣兵",
                old_faction="bandit_guild",
                new_faction="town_guard",
                faction_change_type="switch",
            ).to_dict(),
        )
        
        assert event is not None
        assert event.params["old_faction"] == "bandit_guild"
        assert event.params["new_faction"] == "town_guard"


class TestSpawnEncounter:
    """Tests for SPAWN_ENCOUNTER event type."""

    def test_emit_spawn_encounter(self):
        """Test emitting a spawn encounter event."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.SPAWN_ENCOUNTER,
            source_npc_id="angry_captain",
            params=SpawnEncounterParams(
                spawn_location="city_entrance",
                enemy_type="patrol_guard",
                enemy_count=3,
                behavior="hostile",
                trigger_radius=15.0,
            ).to_dict(),
        )
        
        assert event is not None
        assert event.params["enemy_count"] == 3
        assert event.params["behavior"] == "hostile"


class TestStoryMilestone:
    """Tests for STORY_MILESTONE event type."""

    def test_emit_unlock_area(self):
        """Test emitting a milestone to unlock area."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.STORY_MILESTONE,
            source_npc_id="quest_giver",
            params=StoryMilestoneParams(
                milestone_id="secret_cave_unlocked",
                milestone_type="unlock_area",
                target_id="secret_cave",
                title="秘密洞穴",
                description="发现了通往秘密洞穴的路",
            ).to_dict(),
        )
        
        assert event is not None
        assert event.params["milestone_type"] == "unlock_area"
        assert event.params["target_id"] == "secret_cave"


class TestEventSubscription:
    """Tests for event subscriptions."""

    def test_subscribe_to_event_type(self):
        """Test subscribing to event type."""
        manager = create_world_event_manager()
        
        received = []
        def callback(event):
            received.append(event)
        
        manager.subscribe_event_type(WorldEventType.AREA_LOCKDOWN, callback)
        
        manager.emit_world_event(
            event_type=WorldEventType.AREA_LOCKDOWN,
            source_npc_id="test_npc",
            params={"area_id": "test"},
        )
        
        assert len(received) == 1
        assert received[0].event_type == WorldEventType.AREA_LOCKDOWN

    def test_subscribe_to_all_types(self):
        """Test subscribing captures all event types."""
        manager = create_world_event_manager()
        
        received = []
        def callback(event):
            received.append(event)
        
        # Subscribe to specific type
        manager.subscribe_event_type(WorldEventType.AREA_LOCKDOWN, callback)
        
        # Emit different event types
        manager.emit_world_event(
            event_type=WorldEventType.AREA_LOCKDOWN,
            source_npc_id="npc1",
            params={},
        )
        manager.emit_world_event(
            event_type=WorldEventType.PRICE_CHANGE,
            source_npc_id="npc2",
            params={},
        )
        
        # Only lockdown events should be received
        assert len(received) == 1
        assert received[0].event_type == WorldEventType.AREA_LOCKDOWN


class TestEventResolution:
    """Tests for event resolution."""

    def test_resolve_event(self):
        """Test resolving an event."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.AREA_LOCKDOWN,
            source_npc_id="tavern_keeper",
            params={"area_id": "tavern"},
        )
        
        resolved = manager.resolve_event(
            event.event_id,
            resolution="player_action",
            params={"method": "persuasion"},
        )
        
        assert resolved is True
        
        # Event should no longer be active
        active = manager.get_active_events()
        assert len(active) == 0
        
        # But should be in history
        retrieved = manager.get_event(event.event_id)
        assert retrieved is not None
        assert retrieved.resolved is True
        assert retrieved.resolution == EventResolution.PLAYER_ACTION

    def test_resolve_nonexistent(self):
        """Test resolving a nonexistent event."""
        manager = create_world_event_manager()
        
        result = manager.resolve_event("nonexistent_id", "manual")
        assert result is False


class TestSessionTracking:
    """Tests for session-based event tracking."""

    def test_events_tracked_by_session(self):
        """Test that events are tracked by session."""
        manager = create_world_event_manager()
        
        manager.emit_world_event(
            event_type=WorldEventType.AREA_LOCKDOWN,
            source_npc_id="npc1",
            params={},
            session_id="session_001",
        )
        manager.emit_world_event(
            event_type=WorldEventType.PRICE_CHANGE,
            source_npc_id="npc2",
            params={},
            session_id="session_002",
        )
        
        # Get events for session 001
        session_001_events = manager.get_active_events(session_id="session_001")
        assert len(session_001_events) == 1
        assert session_001_events[0].source_npc_id == "npc1"

    def test_clear_session_events(self):
        """Test clearing session events."""
        manager = create_world_event_manager()
        
        event = manager.emit_world_event(
            event_type=WorldEventType.AREA_LOCKDOWN,
            source_npc_id="npc1",
            params={},
            session_id="session_001",
        )
        
        manager.clear_session_events("session_001")
        
        events = manager.get_active_events(session_id="session_001")
        assert len(events) == 0


class TestEventHistory:
    """Tests for event history."""

    def test_event_history(self):
        """Test event history retrieval."""
        manager = create_world_event_manager()
        
        # Emit and resolve events
        for i in range(5):
            event = manager.emit_world_event(
                event_type=WorldEventType.AREA_LOCKDOWN,
                source_npc_id=f"npc_{i}",
                params={},
            )
            manager.resolve_event(event.event_id, "manual")
        
        history = manager.get_event_history(limit=3)
        assert len(history) == 3  # Limited to 3
        
        # Should be sorted by most recent first
        for i in range(len(history) - 1):
            assert history[i].created_at >= history[i + 1].created_at


class TestGlobalInstance:
    """Tests for global manager instance."""

    def test_global_instance(self):
        """Test that global instance is accessible."""
        manager = get_world_event_manager()
        assert manager is not None
        
        # Should be the same instance
        manager2 = get_world_event_manager()
        assert manager is manager2
