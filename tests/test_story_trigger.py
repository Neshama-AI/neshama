"""
Neshama Story Trigger Tests
"""

import pytest
import sys
import os
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.story_trigger import (
    StoryTriggerEngine,
    StoryTrigger,
    TriggerCondition,
    TriggerConditionType,
    StoryEffect,
    StoryEffectType,
    TriggeredEvent,
    create_story_trigger_engine,
)


class TestStoryTriggerInit:
    """Tests for StoryTriggerEngine initialization."""

    def test_default_init(self):
        """Test default initialization."""
        engine = create_story_trigger_engine()
        assert engine is not None
        assert len(engine.list_triggers()) == 0
        assert len(engine.get_active_events()) == 0

    def test_register_trigger(self):
        """Test registering a trigger."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="test_trigger",
            name="测试触发器",
            description="测试描述",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_THRESHOLD,
                    npc_id="npc_001",
                    emotion="anger",
                    threshold=0.8,
                    direction="rising",
                )
            ],
            effects=[
                StoryEffect(
                    effect_type=StoryEffectType.TRIGGER_WORLD_EVENT,
                    target="test_event",
                )
            ],
        )
        
        result = engine.register_trigger(trigger)
        assert result is True
        
        retrieved = engine.get_trigger("test_trigger")
        assert retrieved is not None
        assert retrieved.trigger_id == "test_trigger"

    def test_duplicate_trigger_id(self):
        """Test that duplicate trigger IDs are rejected."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="dup_trigger",
            name="重复触发器",
            description="",
            conditions=[],
            effects=[],
        )
        
        engine.register_trigger(trigger)
        result = engine.register_trigger(trigger)
        assert result is False

    def test_unregister_trigger(self):
        """Test unregistering a trigger."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="unreg_trigger",
            name="待删除触发器",
            description="",
            conditions=[],
            effects=[],
        )
        
        engine.register_trigger(trigger)
        result = engine.unregister_trigger("unreg_trigger")
        assert result is True
        assert engine.get_trigger("unreg_trigger") is None


class TestEmotionThreshold:
    """Tests for EMOTION_THRESHOLD trigger condition."""

    def test_threshold_rising(self):
        """Test rising threshold triggers correctly."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="anger_threshold",
            name="愤怒阈值触发",
            description="愤怒超过0.8时触发",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_THRESHOLD,
                    npc_id="npc_001",
                    emotion="anger",
                    threshold=0.8,
                    direction="rising",
                )
            ],
            effects=[
                StoryEffect(
                    effect_type=StoryEffectType.TRIGGER_WORLD_EVENT,
                    target="lockdown",
                )
            ],
        )
        engine.register_trigger(trigger)
        
        # Should not trigger - below threshold
        events = engine.check_triggers(
            npc_emotions={"npc_001": {"anger": 0.5}}
        )
        assert len(events) == 0
        
        # Should trigger - at threshold
        events = engine.check_triggers(
            npc_emotions={"npc_001": {"anger": 0.85}}
        )
        assert len(events) == 1
        assert events[0].trigger_id == "anger_threshold"

    def test_threshold_falling(self):
        """Test falling threshold triggers correctly."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="trust_falling",
            name="信任下降触发",
            description="信任降到0.3以下时触发",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_THRESHOLD,
                    npc_id="npc_001",
                    emotion="trust",
                    threshold=0.3,
                    direction="falling",
                )
            ],
            effects=[
                StoryEffect(
                    effect_type=StoryEffectType.TRIGGER_WORLD_EVENT,
                    target="betrayal",
                )
            ],
        )
        engine.register_trigger(trigger)
        
        # Should trigger - trust low
        events = engine.check_triggers(
            npc_emotions={"npc_001": {"trust": 0.2}}
        )
        assert len(events) == 1


class TestEmotionCombo:
    """Tests for EMOTION_COMBO trigger condition."""

    def test_combo_both_required(self):
        """Test that combo requires both emotions."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="joy_trust_combo",
            name="开心信任组合",
            description="joy>0.7 AND trust>0.7时触发",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_COMBO,
                    npc_id="npc_001",
                    emotions={"joy": 0.7, "trust": 0.7},
                )
            ],
            effects=[
                StoryEffect(
                    effect_type=StoryEffectType.UNLOCK_DIALOGUE,
                    target="secret_dialogue",
                )
            ],
        )
        engine.register_trigger(trigger)
        
        # Should not trigger - only one emotion high
        events = engine.check_triggers(
            npc_emotions={"npc_001": {"joy": 0.8, "trust": 0.3}}
        )
        assert len(events) == 0
        
        # Should trigger - both emotions high
        events = engine.check_triggers(
            npc_emotions={"npc_001": {"joy": 0.8, "trust": 0.8}}
        )
        assert len(events) == 1


class TestEmotionChange:
    """Tests for EMOTION_CHANGE trigger condition."""

    def test_change_detected(self):
        """Test that significant changes are detected."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="trust_drop",
            name="信任急剧下降",
            description="信任下降超过0.4时触发",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_CHANGE,
                    npc_id="npc_001",
                    emotion="trust",
                    change_magnitude=0.4,
                    direction="falling",
                )
            ],
            effects=[
                StoryEffect(
                    effect_type=StoryEffectType.MODIFY_NPC,
                    target="npc_001",
                    params={"dialogue_style": "hostile"},
                )
            ],
        )
        engine.register_trigger(trigger)
        
        # First call - initializes snapshot, no trigger
        events1 = engine.check_triggers(
            npc_emotions={"npc_001": {"trust": 0.8}}
        )
        # No trigger on first call (snapshot initialized)
        
        # Second call - change detected
        events2 = engine.check_triggers(
            npc_emotions={"npc_001": {"trust": 0.3}}
        )
        # Should trigger due to significant change
        assert len(events2) == 1


class TestMultiNpc:
    """Tests for MULTI_NPC_CONDITION trigger condition."""

    def test_multi_npc_anger(self):
        """Test multiple NPCs with high anger."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="town_alert",
            name="全镇警戒",
            description="两个NPC愤怒超过0.6时触发",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.MULTI_NPC_CONDITION,
                    emotion="anger",
                    threshold=0.6,
                )
            ],
            effects=[
                StoryEffect(
                    effect_type=StoryEffectType.TRIGGER_WORLD_EVENT,
                    target="town_lockdown",
                )
            ],
        )
        engine.register_trigger(trigger)
        
        # Should not trigger - only one NPC angry
        events = engine.check_triggers(
            npc_emotions={
                "npc_001": {"anger": 0.7},
                "npc_002": {"anger": 0.3},
            }
        )
        assert len(events) == 0
        
        # Should trigger - two NPCs angry
        events = engine.check_triggers(
            npc_emotions={
                "npc_001": {"anger": 0.7},
                "npc_002": {"anger": 0.8},
            }
        )
        assert len(events) == 1


class TestTimeBased:
    """Tests for TIME_BASED trigger condition."""

    def test_time_based_trigger(self):
        """Test time-based condition."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="prolonged_sadness",
            name="持续悲伤",
            description="悲伤超过0.6持续5秒时触发",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.TIME_BASED,
                    npc_id="npc_001",
                    emotion="sadness",
                    threshold=0.6,
                    duration_seconds=5.0,
                )
            ],
            effects=[
                StoryEffect(
                    effect_type=StoryEffectType.MODIFY_NPC,
                    target="npc_001",
                    params={"will_talk": False},
                )
            ],
        )
        engine.register_trigger(trigger)
        
        # First check - emotion above threshold, starts tracking
        events1 = engine.check_triggers(
            npc_emotions={"npc_001": {"sadness": 0.7}}
        )
        # Time hasn't elapsed yet
        
        # Emotion drops - resets tracking
        engine.check_triggers(
            npc_emotions={"npc_001": {"sadness": 0.3}}
        )
        
        # Emotion rises again - new tracking starts
        events2 = engine.check_triggers(
            npc_emotions={"npc_001": {"sadness": 0.8}}
        )


class TestCooldown:
    """Tests for trigger cooldown."""

    def test_cooldown_prevents_retrigger(self):
        """Test that cooldown prevents immediate retriggering."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="cooldown_test",
            name="冷却测试",
            description="带冷却的触发器",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_THRESHOLD,
                    npc_id="npc_001",
                    emotion="anger",
                    threshold=0.5,
                    direction="rising",
                )
            ],
            effects=[
                StoryEffect(
                    effect_type=StoryEffectType.TRIGGER_WORLD_EVENT,
                    target="test",
                )
            ],
            cooldown=10.0,  # 10 second cooldown
        )
        engine.register_trigger(trigger)
        
        # First trigger
        events1 = engine.check_triggers(
            npc_emotions={"npc_001": {"anger": 0.9}}
        )
        assert len(events1) == 1
        
        # Immediate recheck - should not trigger due to cooldown
        events2 = engine.check_triggers(
            npc_emotions={"npc_001": {"anger": 0.9}}
        )
        assert len(events2) == 0


class TestOneShot:
    """Tests for one-shot triggers."""

    def test_one_shot_fires_once(self):
        """Test that one-shot triggers fire only once."""
        engine = create_story_trigger_engine()
        trigger = StoryTrigger(
            trigger_id="one_shot_test",
            name="一次性触发器",
            description="只触发一次的触发器",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_THRESHOLD,
                    npc_id="npc_001",
                    emotion="joy",
                    threshold=0.5,
                    direction="rising",
                )
            ],
            effects=[
                StoryEffect(
                    effect_type=StoryEffectType.TRIGGER_WORLD_EVENT,
                    target="milestone",
                )
            ],
            one_shot=True,
        )
        engine.register_trigger(trigger)
        
        # First trigger
        events1 = engine.check_triggers(
            npc_emotions={"npc_001": {"joy": 0.8}}
        )
        assert len(events1) == 1
        
        # Second trigger - should not fire
        events2 = engine.check_triggers(
            npc_emotions={"npc_001": {"joy": 0.9}}
        )
        assert len(events2) == 0


class TestPriority:
    """Tests for trigger priority."""

    def test_higher_priority_first(self):
        """Test that higher priority triggers are checked first."""
        engine = create_story_trigger_engine()
        
        # Low priority trigger
        low_trigger = StoryTrigger(
            trigger_id="low_priority",
            name="低优先级",
            description="",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_THRESHOLD,
                    npc_id="npc_001",
                    emotion="anger",
                    threshold=0.3,
                    direction="rising",
                )
            ],
            effects=[StoryEffect(effect_type=StoryEffectType.SEND_NOTIFICATION, target="low")],
            priority=1,
        )
        
        # High priority trigger
        high_trigger = StoryTrigger(
            trigger_id="high_priority",
            name="高优先级",
            description="",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_THRESHOLD,
                    npc_id="npc_001",
                    emotion="anger",
                    threshold=0.3,
                    direction="rising",
                )
            ],
            effects=[StoryEffect(effect_type=StoryEffectType.SEND_NOTIFICATION, target="high")],
            priority=10,
        )
        
        engine.register_trigger(low_trigger)
        engine.register_trigger(high_trigger)
        
        events = engine.check_triggers(
            npc_emotions={"npc_001": {"anger": 0.8}}
        )
        
        # Both should trigger, but high_priority should be first
        assert len(events) == 2
        assert events[0].effects[0].target == "high"


class TestCallbacks:
    """Tests for trigger callbacks."""

    def test_callback_called(self):
        """Test that callbacks are called when triggers fire."""
        engine = create_story_trigger_engine()
        
        callback_called = []
        def callback(event):
            callback_called.append(event)
        
        engine.subscribe(callback)
        
        trigger = StoryTrigger(
            trigger_id="callback_test",
            name="回调测试",
            description="",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_THRESHOLD,
                    npc_id="npc_001",
                    emotion="anger",
                    threshold=0.5,
                    direction="rising",
                )
            ],
            effects=[StoryEffect(effect_type=StoryEffectType.SEND_NOTIFICATION, target="test")],
        )
        engine.register_trigger(trigger)
        
        engine.check_triggers(
            npc_emotions={"npc_001": {"anger": 0.9}}
        )
        
        assert len(callback_called) == 1


class TestDisabledTrigger:
    """Tests for disabled triggers."""

    def test_disabled_trigger_not_checked(self):
        """Test that disabled triggers don't fire."""
        engine = create_story_trigger_engine()
        
        trigger = StoryTrigger(
            trigger_id="disabled_test",
            name="禁用测试",
            description="",
            conditions=[
                TriggerCondition(
                    condition_type=TriggerConditionType.EMOTION_THRESHOLD,
                    npc_id="npc_001",
                    emotion="anger",
                    threshold=0.5,
                    direction="rising",
                )
            ],
            effects=[StoryEffect(effect_type=StoryEffectType.SEND_NOTIFICATION, target="test")],
            enabled=False,  # Disabled
        )
        engine.register_trigger(trigger)
        
        events = engine.check_triggers(
            npc_emotions={"npc_001": {"anger": 0.9}}
        )
        
        assert len(events) == 0
