"""
Neshama Quest System Tests
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.quest_system import (
    DynamicQuestSystem,
    QuestTemplate,
    QuestTrigger,
    QuestCondition,
    QuestReward,
    QuestEmotionalEffect,
    QuestStatus,
    ActiveQuest,
    create_quest_system,
)


class TestQuestSystemInit:
    """Tests for DynamicQuestSystem initialization."""

    def test_default_init(self):
        """Test default initialization with default templates."""
        system = create_quest_system()
        assert system is not None
        assert len(system.list_templates()) >= 5  # Default templates

    def test_custom_templates(self):
        """Test initialization with custom templates."""
        system = create_quest_system()
        
        custom_template = QuestTemplate(
            template_id="custom_test",
            title="自定义任务",
            description="这是一个自定义任务",
            giver_npc="test_npc",
            trigger=QuestTrigger(emotion="joy", threshold=0.6),
            completion_conditions=[
                QuestCondition(
                    condition_type="collect_item",
                    target="test_item",
                    description="收集测试物品",
                )
            ],
        )
        
        result = system.register_template(custom_template)
        assert result is True
        
        retrieved = system.get_template("custom_test")
        assert retrieved is not None
        assert retrieved.title == "自定义任务"


class TestQuestGeneration:
    """Tests for quest generation."""

    def test_generate_quest(self):
        """Test generating a quest from template."""
        system = create_quest_system()
        
        quest = system.generate_quest("angry_lockdown", "tavern_keeper")
        assert quest is not None
        assert quest.template_id == "angry_lockdown"
        assert quest.giver_npc == "tavern_keeper"
        assert quest.status == QuestStatus.AVAILABLE

    def test_generate_with_custom_title(self):
        """Test generating quest with custom title."""
        system = create_quest_system()
        
        quest = system.generate_quest(
            "sad_quest",
            "npc_001",
            params={"title": "帮我找东西", "description": "自定义描述"}
        )
        assert quest is not None
        assert quest.title == "帮我找东西"
        assert quest.description == "自定义描述"

    def test_duplicate_generation_different_npcs(self):
        """Test that same quest can be generated for different NPCs."""
        system = create_quest_system()
        
        quest1 = system.generate_quest("sad_quest", "npc_001")
        quest2 = system.generate_quest("sad_quest", "npc_002")
        
        # Same template can be generated for different NPCs
        assert quest1 is not None
        assert quest2 is not None
        assert quest1.giver_npc == "npc_001"
        assert quest2.giver_npc == "npc_002"
        
    def test_same_quest_same_npc_after_accept(self):
        """Test that same quest can't be generated for same NPC after acceptance."""
        system = create_quest_system()
        
        quest1 = system.generate_quest("sad_quest", "npc_001")
        system.accept_quest(quest1.quest_id)
        
        # Should not be able to generate same quest for same NPC when already active
        quest2 = system.generate_quest("sad_quest", "npc_001")
        assert quest2 is None


class TestQuestTrigger:
    """Tests for quest trigger checking."""

    def test_trigger_conditions_met(self):
        """Test that quest appears when emotion triggers are met."""
        system = create_quest_system()
        
        # anger >= 0.7 should trigger angry_lockdown
        templates = system.check_quest_triggers(
            "tavern_keeper",
            {"anger": 0.8, "joy": 0.2}
        )
        
        template_ids = [t.template_id for t in templates]
        assert "angry_lockdown" in template_ids

    def test_trigger_conditions_not_met(self):
        """Test that quest doesn't appear when emotions are low."""
        system = create_quest_system()
        
        templates = system.check_quest_triggers(
            "tavern_keeper",
            {"anger": 0.3, "joy": 0.2}
        )
        
        template_ids = [t.template_id for t in templates]
        assert "angry_lockdown" not in template_ids

    def test_trust_trigger(self):
        """Test trust-based quest trigger."""
        system = create_quest_system()
        
        # trust >= 0.7 should trigger trust_secret
        templates = system.check_quest_triggers(
            "npc_001",
            {"trust": 0.8, "joy": 0.6}
        )
        
        template_ids = [t.template_id for t in templates]
        assert "trust_secret" in template_ids

    def test_sadness_trigger(self):
        """Test sadness-based quest trigger."""
        system = create_quest_system()
        
        # sadness >= 0.6 should trigger sad_quest
        templates = system.check_quest_triggers(
            "npc_001",
            {"sadness": 0.7}
        )
        
        template_ids = [t.template_id for t in templates]
        assert "sad_quest" in template_ids


class TestQuestAccept:
    """Tests for quest acceptance."""

    def test_accept_quest(self):
        """Test accepting a quest."""
        system = create_quest_system()
        
        quest = system.generate_quest("sad_quest", "npc_001")
        assert quest is not None
        
        accepted = system.accept_quest(quest.quest_id)
        assert accepted is not None
        assert accepted.status == QuestStatus.ACTIVE
        assert accepted.accepted_at is not None

    def test_accept_nonexistent_quest(self):
        """Test accepting a quest that doesn't exist."""
        system = create_quest_system()
        
        result = system.accept_quest("nonexistent_id")
        assert result is None

    def test_accept_already_active(self):
        """Test that accepted quest can't be accepted again."""
        system = create_quest_system()
        
        quest = system.generate_quest("sad_quest", "npc_001")
        system.accept_quest(quest.quest_id)
        
        # Try to accept again
        result = system.accept_quest(quest.quest_id)
        assert result is None


class TestQuestProgress:
    """Tests for quest progress updates."""

    def test_update_progress(self):
        """Test updating quest progress."""
        system = create_quest_system()
        
        quest = system.generate_quest("sad_quest", "npc_001")
        system.accept_quest(quest.quest_id)
        
        # Update with collect_item event
        updated = system.update_quest_progress(
            quest.quest_id,
            {"type": "item_collected", "target": "lost_item"}
        )
        
        assert updated is not None
        assert len(updated.progress) > 0

    def test_progress_completes_quest(self):
        """Test that completing conditions auto-completes quest."""
        system = create_quest_system()
        
        quest = system.generate_quest("sad_quest", "npc_001")
        system.accept_quest(quest.quest_id)
        
        # Complete all conditions
        updated = system.update_quest_progress(
            quest.quest_id,
            {"type": "item_collected", "target": "lost_item"}
        )
        
        # Quest should be completed
        final_quest = system.get_quest(quest.quest_id)
        assert final_quest.status == QuestStatus.COMPLETED


class TestQuestCompletion:
    """Tests for quest completion."""

    def test_complete_quest(self):
        """Test manually completing a quest."""
        system = create_quest_system()
        
        quest = system.generate_quest("friend_favor", "npc_001")
        system.accept_quest(quest.quest_id)
        
        completed = system.complete_quest(quest.quest_id)
        assert completed is not None
        assert completed.status == QuestStatus.COMPLETED
        assert completed.completed_at is not None

    def test_complete_nonexistent(self):
        """Test completing a nonexistent quest."""
        system = create_quest_system()
        
        result = system.complete_quest("nonexistent")
        assert result is None


class TestQuestFailure:
    """Tests for quest failure."""

    def test_fail_quest(self):
        """Test failing a quest."""
        system = create_quest_system()
        
        quest = system.generate_quest("betrayal_revenge", "npc_001")
        system.accept_quest(quest.quest_id)
        
        failed = system.fail_quest(quest.quest_id)
        assert failed is not None
        assert failed.status == QuestStatus.FAILED
        assert failed.failed_at is not None

    def test_fail_nonexistent(self):
        """Test failing a nonexistent quest."""
        system = create_quest_system()
        
        result = system.fail_quest("nonexistent")
        assert result is None


class TestEmotionalAftermath:
    """Tests for emotional effects of quest completion/failure."""

    def test_emotion_callback_on_complete(self):
        """Test that emotion callback is triggered on completion."""
        system = create_quest_system()
        
        callback_results = []
        def callback(npc_id, action, effects):
            callback_results.append((npc_id, action, effects))
        
        system.subscribe_emotion_callback(callback)
        
        quest = system.generate_quest("sad_quest", "npc_001")
        system.accept_quest(quest.quest_id)
        system.complete_quest(quest.quest_id)
        
        assert len(callback_results) == 1
        npc_id, action, effects = callback_results[0]
        assert npc_id == "npc_001"
        assert action == "complete"
        assert len(effects) > 0

    def test_emotion_callback_on_fail(self):
        """Test that emotion callback is triggered on failure."""
        system = create_quest_system()
        
        callback_results = []
        def callback(npc_id, action, effects):
            callback_results.append((npc_id, action, effects))
        
        system.subscribe_emotion_callback(callback)
        
        quest = system.generate_quest("sad_quest", "npc_001")
        system.accept_quest(quest.quest_id)
        system.fail_quest(quest.quest_id)
        
        assert len(callback_results) == 1
        npc_id, action, effects = callback_results[0]
        assert npc_id == "npc_001"
        assert action == "fail"


class TestQuestQueries:
    """Tests for quest queries."""

    def test_get_available_quests(self):
        """Test getting available quests."""
        system = create_quest_system()
        
        system.generate_quest("sad_quest", "npc_001")
        system.generate_quest("angry_lockdown", "npc_002")
        
        available = system.get_available_quests()
        assert len(available) == 2

    def test_get_available_quests_by_npc(self):
        """Test filtering available quests by NPC."""
        system = create_quest_system()
        
        system.generate_quest("sad_quest", "npc_001")
        system.generate_quest("angry_lockdown", "npc_002")
        
        available = system.get_available_quests(npc_id="npc_001")
        assert len(available) == 1
        assert available[0].giver_npc == "npc_001"

    def test_get_active_quests(self):
        """Test getting active quests."""
        system = create_quest_system()
        
        quest1 = system.generate_quest("sad_quest", "npc_001")
        quest2 = system.generate_quest("angry_lockdown", "npc_002")
        system.accept_quest(quest1.quest_id)
        
        active = system.get_active_quests()
        assert len(active) == 1
        assert active[0].quest_id == quest1.quest_id

    def test_get_quest_any_status(self):
        """Test getting quest by ID regardless of status."""
        system = create_quest_system()
        
        quest = system.generate_quest("sad_quest", "npc_001")
        system.accept_quest(quest.quest_id)
        system.complete_quest(quest.quest_id)
        
        # Quest is now completed, but should still be retrievable
        retrieved = system.get_quest(quest.quest_id)
        assert retrieved is not None
        assert retrieved.status == QuestStatus.COMPLETED


class TestQuestSubscriptions:
    """Tests for quest event subscriptions."""

    def test_quest_available_callback(self):
        """Test quest_available callback."""
        system = create_quest_system()
        
        results = []
        def callback(quest):
            results.append(quest)
        
        system.subscribe("quest_available", callback)
        
        system.generate_quest("sad_quest", "npc_001")
        
        assert len(results) == 1

    def test_quest_accepted_callback(self):
        """Test quest_accepted callback."""
        system = create_quest_system()
        
        results = []
        def callback(quest):
            results.append(quest)
        
        system.subscribe("quest_accepted", callback)
        
        quest = system.generate_quest("sad_quest", "npc_001")
        system.accept_quest(quest.quest_id)
        
        assert len(results) == 1

    def test_quest_completed_callback(self):
        """Test quest_completed callback."""
        system = create_quest_system()
        
        results = []
        def callback(quest):
            results.append(quest)
        
        system.subscribe("quest_completed", callback)
        
        quest = system.generate_quest("sad_quest", "npc_001")
        system.accept_quest(quest.quest_id)
        system.complete_quest(quest.quest_id)
        
        assert len(results) == 1
