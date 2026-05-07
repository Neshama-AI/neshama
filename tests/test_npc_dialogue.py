"""
Neshama NPC Dialogue Engine Tests
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.npc_dialogue import (
    NPCDialogueEngine, DialogueTrigger, DialogueTurn, Dialogue,
    NPCDialogueContext,
)


class TestDialogueTrigger:
    """Tests for DialogueTrigger enum."""
    
    def test_all_triggers_exist(self):
        """Test that all triggers are defined."""
        assert DialogueTrigger.AUTONOMOUS.value == "autonomous"
        assert DialogueTrigger.PLAYER_TRIGGERED.value == "player_triggered"
        assert DialogueTrigger.WORLD_EVENT.value == "world_event"
        assert DialogueTrigger.INFORMATION_SPREAD.value == "information_spread"


class TestDialogueTurn:
    """Tests for DialogueTurn dataclass."""
    
    def test_create_turn(self):
        """Test creating a dialogue turn."""
        turn = DialogueTurn(
            turn_id="turn_001",
            dialogue_id="dialogue_001",
            speaker_id="npc_001",
            speaker_name="Alice",
            content="Hello, how are you?",
        )
        
        assert turn.turn_id == "turn_001"
        assert turn.speaker_name == "Alice"
        assert turn.emotion_hint is None
    
    def test_to_dict(self):
        """Test turn serialization."""
        turn = DialogueTurn(
            turn_id="turn_001",
            dialogue_id="dialogue_001",
            speaker_id="npc_001",
            speaker_name="Bob",
            content="I'm doing well!",
            emotion_hint="joy",
        )
        
        data = turn.to_dict()
        
        assert data["turn_id"] == "turn_001"
        assert data["speaker_name"] == "Bob"
        assert data["emotion_hint"] == "joy"


class TestDialogue:
    """Tests for Dialogue dataclass."""
    
    def test_create_dialogue(self):
        """Test creating a dialogue."""
        dialogue = Dialogue(
            dialogue_id="dialogue_001",
            npc_a_id="npc_001",
            npc_b_id="npc_002",
            npc_a_name="Alice",
            npc_b_name="Bob",
            topic="The weather",
            trigger=DialogueTrigger.PLAYER_TRIGGERED,
        )
        
        assert dialogue.dialogue_id == "dialogue_001"
        assert dialogue.npc_a_name == "Alice"
        assert len(dialogue.turns) == 0
        assert dialogue.summary is None
    
    def test_add_turns(self):
        """Test adding turns to dialogue."""
        dialogue = Dialogue(
            dialogue_id="dialogue_001",
            npc_a_id="npc_001",
            npc_b_id="npc_002",
            npc_a_name="Alice",
            npc_b_name="Bob",
            topic="News",
            trigger=DialogueTrigger.AUTONOMOUS,
        )
        
        turn1 = DialogueTurn(
            turn_id="turn_001",
            dialogue_id="dialogue_001",
            speaker_id="npc_001",
            speaker_name="Alice",
            content="Did you hear?",
        )
        
        turn2 = DialogueTurn(
            turn_id="turn_002",
            dialogue_id="dialogue_001",
            speaker_id="npc_002",
            speaker_name="Bob",
            content="About what?",
        )
        
        dialogue.turns.append(turn1)
        dialogue.turns.append(turn2)
        
        assert len(dialogue.turns) == 2
        # turn_count is computed in to_dict(), not a direct attribute
        assert dialogue.to_dict()["turn_count"] == 2
    
    def test_to_dict(self):
        """Test dialogue serialization."""
        dialogue = Dialogue(
            dialogue_id="dialogue_001",
            npc_a_id="npc_001",
            npc_b_id="npc_002",
            npc_a_name="Alice",
            npc_b_name="Bob",
            topic="The dragon",
            trigger=DialogueTrigger.WORLD_EVENT,
        )
        dialogue.summary = "They discussed the dragon sighting."
        
        data = dialogue.to_dict()
        
        assert data["dialogue_id"] == "dialogue_001"
        assert data["npc_a_name"] == "Alice"
        assert data["trigger"] == "world_event"
        assert data["summary"] is not None


class TestNPCDialogueContext:
    """Tests for NPCDialogueContext."""
    
    def test_create_context(self):
        """Test creating dialogue context."""
        context = NPCDialogueContext(
            npc_id="npc_001",
            name="Alice",
            personality={"extraversion": 0.8, "agreeableness": 0.6},
            emotions={"joy": 0.7, "trust": 0.5},
            relationship={"strength": 0.7, "trust": 0.6},
            known_info=["Dragon spotted!", "Merchant arrived."],
            recent_interactions=["gossiped with Bob", "heard about the dragon"],
        )
        
        assert context.npc_id == "npc_001"
        assert context.name == "Alice"
    
    def test_to_prompt_text(self):
        """Test conversion to prompt text."""
        context = NPCDialogueContext(
            npc_id="npc_001",
            name="Alice",
            personality={
                "extraversion": 0.9,  # High
                "agreeableness": 0.3,  # Low
                "openness": 0.5,
            },
            emotions={"joy": 0.8},  # High
            relationship={"strength": 0.7, "trust": 0.6, "category": "friend"},
            known_info=["News about the dragon."],
            recent_interactions=[],
        )
        
        text = context.to_prompt_text(max_tokens=500)
        
        assert "Alice" in text
        assert "Name:" in text
        assert "Personality:" in text


class TestNPCDialogueEngine:
    """Tests for NPCDialogueEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create fresh engine for each test."""
        return NPCDialogueEngine()
    
    def test_init(self, engine):
        """Test engine initialization."""
        assert len(engine._dialogues) == 0
        assert engine._on_dialogue_update is None
    
    def test_set_model_adapter(self, engine):
        """Test setting model adapter."""
        mock_adapter = Mock()
        engine.set_model_adapter(mock_adapter)
        
        assert engine._model_adapter is mock_adapter
    
    def test_set_ws_callback(self, engine):
        """Test setting WS callback."""
        callback = Mock()
        engine.set_ws_callback(callback)
        
        assert engine._on_dialogue_update is callback
    
    def test_generate_dialogue_creates_entry(self, engine):
        """Test that generate dialogue creates entry."""
        with patch.object(engine, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Alice: Hello! | Bob: Hi there!"
            
            # Mock NPC context retrieval
            with patch.object(engine, '_get_npc_context') as mock_context:
                mock_context.side_effect = lambda npc_id, *args: NPCDialogueContext(
                    npc_id=npc_id,
                    name=f"NPC_{npc_id}",
                    personality={},
                    emotions={},
                    relationship=None,
                    known_info=[],
                    recent_interactions=[],
                )
                
                dialogue = engine.generate_dialogue(
                    npc_a_id="npc_001",
                    npc_b_id="npc_002",
                    topic="Greetings",
                )
                
                assert dialogue.dialogue_id is not None
                assert dialogue.npc_a_id == "npc_001"
                assert dialogue.npc_b_id == "npc_002"
                assert dialogue.topic == "Greetings"
    
    def test_generate_dialogue_stores_turns(self, engine):
        """Test that dialogue generates turns."""
        with patch.object(engine, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Alice: How's the weather? | Bob: It's sunny today."
            
            with patch.object(engine, '_get_npc_context') as mock_context:
                mock_context.side_effect = lambda npc_id, *args: NPCDialogueContext(
                    npc_id=npc_id,
                    name=f"NPC_{npc_id}",
                    personality={},
                    emotions={},
                    relationship=None,
                    known_info=[],
                    recent_interactions=[],
                )
                
                dialogue = engine.generate_dialogue(
                    npc_a_id="npc_001",
                    npc_b_id="npc_002",
                    topic="Weather",
                )
                
                assert dialogue.dialogue_id in engine._dialogues
    
    def test_get_dialogue(self, engine):
        """Test getting dialogue by ID."""
        with patch.object(engine, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Alice: Hello!"
            
            with patch.object(engine, '_get_npc_context') as mock_context:
                mock_context.side_effect = lambda npc_id, *args: NPCDialogueContext(
                    npc_id=npc_id,
                    name=f"NPC_{npc_id}",
                    personality={},
                    emotions={},
                    relationship=None,
                    known_info=[],
                    recent_interactions=[],
                )
                
                dialogue = engine.generate_dialogue(
                    npc_a_id="npc_001",
                    npc_b_id="npc_002",
                    topic="Test",
                )
                
                retrieved = engine.get_dialogue(dialogue.dialogue_id)
                
                assert retrieved is not None
                assert retrieved.dialogue_id == dialogue.dialogue_id
    
    def test_get_dialogue_not_found(self, engine):
        """Test getting non-existent dialogue."""
        result = engine.get_dialogue("nonexistent")
        
        assert result is None
    
    def test_continue_dialogue(self, engine):
        """Test continuing a dialogue."""
        with patch.object(engine, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Alice: Hello!"
            
            with patch.object(engine, '_get_npc_context') as mock_context:
                mock_context.side_effect = lambda npc_id, *args: NPCDialogueContext(
                    npc_id=npc_id,
                    name=f"NPC_{npc_id}",
                    personality={},
                    emotions={},
                    relationship=None,
                    known_info=[],
                    recent_interactions=[],
                )
                
                dialogue = engine.generate_dialogue(
                    npc_a_id="npc_001",
                    npc_b_id="npc_002",
                    topic="Test",
                )
                
                continued = engine.continue_dialogue(dialogue.dialogue_id)
                
                assert continued.dialogue_id == dialogue.dialogue_id
    
    def test_continue_dialogue_not_found(self, engine):
        """Test continuing non-existent dialogue."""
        with pytest.raises(ValueError):
            engine.continue_dialogue("nonexistent")
    
    def test_summarize_dialogue(self, engine):
        """Test summarizing dialogue."""
        with patch.object(engine, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Alice: Hello! | Bob: Hi!"
            
            with patch.object(engine, '_get_npc_context') as mock_context:
                mock_context.side_effect = lambda npc_id, *args: NPCDialogueContext(
                    npc_id=npc_id,
                    name=f"NPC_{npc_id}",
                    personality={},
                    emotions={},
                    relationship=None,
                    known_info=[],
                    recent_interactions=[],
                )
                
                dialogue = engine.generate_dialogue(
                    npc_a_id="npc_001",
                    npc_b_id="npc_002",
                    topic="Test",
                )
                
                summary = engine.summarize_dialogue(dialogue.dialogue_id)
                
                assert summary is not None
                # Names are NPC_{npc_id} from the mock
                assert "NPC_npc_001" in summary
                assert "NPC_npc_002" in summary
    
    def test_summarize_dialogue_not_found(self, engine):
        """Test summarizing non-existent dialogue."""
        result = engine.summarize_dialogue("nonexistent")
        
        assert result is None
    
    def test_get_active_dialogues(self, engine):
        """Test getting active dialogues for NPC."""
        with patch.object(engine, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Alice: Hello!"
            
            with patch.object(engine, '_get_npc_context') as mock_context:
                mock_context.side_effect = lambda npc_id, *args: NPCDialogueContext(
                    npc_id=npc_id,
                    name=f"NPC_{npc_id}",
                    personality={},
                    emotions={},
                    relationship=None,
                    known_info=[],
                    recent_interactions=[],
                )
                
                dialogue = engine.generate_dialogue(
                    npc_a_id="npc_001",
                    npc_b_id="npc_002",
                    topic="Test",
                )
                
                active = engine.get_active_dialogues("npc_001")
                
                assert len(active) >= 1
    
    def test_get_dialogue_history(self, engine):
        """Test getting dialogue history between NPCs."""
        with patch.object(engine, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Alice: Hello!"
            
            with patch.object(engine, '_get_npc_context') as mock_context:
                mock_context.side_effect = lambda npc_id, *args: NPCDialogueContext(
                    npc_id=npc_id,
                    name=f"NPC_{npc_id}",
                    personality={},
                    emotions={},
                    relationship=None,
                    known_info=[],
                    recent_interactions=[],
                )
                
                engine.generate_dialogue(
                    npc_a_id="npc_001",
                    npc_b_id="npc_002",
                    topic="Test",
                )
                
                history = engine.get_dialogue_history("npc_001", "npc_002")
                
                assert len(history) >= 1
    
    def test_get_recent_dialogues(self, engine):
        """Test getting recent dialogues."""
        with patch.object(engine, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Hello!"
            
            with patch.object(engine, '_get_npc_context') as mock_context:
                mock_context.side_effect = lambda npc_id, *args: NPCDialogueContext(
                    npc_id=npc_id,
                    name=f"NPC_{npc_id}",
                    personality={},
                    emotions={},
                    relationship=None,
                    known_info=[],
                    recent_interactions=[],
                )
                
                # Create multiple dialogues
                for i in range(3):
                    engine.generate_dialogue(
                        npc_a_id=f"npc_00{i}",
                        npc_b_id=f"npc_01{i}",
                        topic=f"Topic {i}",
                    )
                
                recent = engine.get_recent_dialogues(limit=5)
                
                assert len(recent) >= 3


class TestDialoguePromptBuilding:
    """Tests for dialogue prompt building."""
    
    @pytest.fixture
    def engine(self):
        return NPCDialogueEngine()
    
    def test_build_system_prompt(self, engine):
        """Test building system prompt."""
        context_a = NPCDialogueContext(
            npc_id="npc_001",
            name="Alice",
            personality={"extraversion": 0.8},
            emotions={},
            relationship=None,
            known_info=[],
            recent_interactions=[],
        )
        
        context_b = NPCDialogueContext(
            npc_id="npc_002",
            name="Bob",
            personality={"agreeableness": 0.6},
            emotions={},
            relationship=None,
            known_info=[],
            recent_interactions=[],
        )
        
        prompt = engine._build_system_prompt(context_a, context_b)
        
        assert "Alice" in prompt
        assert "Bob" in prompt
        assert "NPC" in prompt
    
    def test_build_dialogue_prompt(self, engine):
        """Test building dialogue prompt."""
        context_a = NPCDialogueContext(
            npc_id="npc_001",
            name="Alice",
            personality={},
            emotions={},
            relationship=None,
            known_info=[],
            recent_interactions=[],
        )
        
        context_b = NPCDialogueContext(
            npc_id="npc_002",
            name="Bob",
            personality={},
            emotions={},
            relationship=None,
            known_info=[],
            recent_interactions=[],
        )
        
        prompt = engine._build_dialogue_prompt(
            context_a, context_b,
            topic="The festival",
            history=[],
            turn_count=2,
        )
        
        assert "The festival" in prompt
        assert "Alice" in prompt
        assert "Bob" in prompt
    
    def test_build_dialogue_prompt_with_history(self, engine):
        """Test building prompt with conversation history."""
        context_a = NPCDialogueContext(
            npc_id="npc_001",
            name="Alice",
            personality={},
            emotions={},
            relationship=None,
            known_info=[],
            recent_interactions=[],
        )
        
        context_b = NPCDialogueContext(
            npc_id="npc_002",
            name="Bob",
            personality={},
            emotions={},
            relationship=None,
            known_info=[],
            recent_interactions=[],
        )
        
        history = [
            DialogueTurn(
                turn_id="t1",
                dialogue_id="d1",
                speaker_id="npc_001",
                speaker_name="Alice",
                content="Hello!",
            ),
            DialogueTurn(
                turn_id="t2",
                dialogue_id="d1",
                speaker_id="npc_002",
                speaker_name="Bob",
                content="Hi there!",
            ),
        ]
        
        prompt = engine._build_dialogue_prompt(
            context_a, context_b,
            topic="Greetings",
            history=history,
            turn_count=2,
        )
        
        assert "Hello!" in prompt
        assert "Hi there!" in prompt
        assert "Recent conversation" in prompt


class TestGlobalInstance:
    """Tests for global instance management."""
    
    def test_get_dialogue_engine(self):
        """Test getting global instance."""
        from neshama.soul.npc_dialogue import get_dialogue_engine
        
        engine1 = get_dialogue_engine()
        engine2 = get_dialogue_engine()
        
        assert engine1 is engine2
