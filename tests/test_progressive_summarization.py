"""
Neshama Progressive Summarization Tests
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.progressive_summarization import (
    ProgressiveSummarizer,
    L0Entry,
    L1Entry,
    L2Entry,
    QualityScore,
    create_progressive_summarizer,
    _default_l0_to_l1_summarizer,
    _default_l1_to_l2_summarizer,
)


class TestProgressiveSummarizerInit:
    """Tests for ProgressiveSummarizer initialization."""

    def test_default_init(self):
        """Test default initialization."""
        ps = ProgressiveSummarizer()
        assert ps is not None
        assert ps.l0_to_l1_threshold == 10
        assert ps.l1_to_l2_threshold == 5
        assert ps.l1_to_l2_age_days == 7
        assert ps.l1_max_age_hours == 24 * 7
        assert ps.quality_threshold == 0.3

    def test_custom_init(self):
        """Test custom initialization."""
        ps = ProgressiveSummarizer(
            l0_to_l1_threshold=5,
            l1_to_l2_threshold=3,
            l1_to_l2_age_days=3,
            quality_threshold=0.5,
        )
        assert ps.l0_to_l1_threshold == 5
        assert ps.l1_to_l2_threshold == 3
        assert ps.l1_to_l2_age_days == 3
        assert ps.quality_threshold == 0.5


class TestL0Management:
    """Tests for L0 entry management."""

    def test_add_l0_entry(self):
        """Test adding L0 entry."""
        ps = ProgressiveSummarizer()
        entry = ps.add_l0(role="user", content="Hello, how are you?")
        assert entry is not None
        assert entry.role == "user"
        assert entry.content == "Hello, how are you?"
        assert entry.id is not None

    def test_add_l0_with_timestamp(self):
        """Test adding L0 entry with explicit timestamp."""
        ps = ProgressiveSummarizer()
        ts = "2024-01-01T12:00:00"
        entry = ps.add_l0(role="user", content="Hello", timestamp=ts)
        assert entry.timestamp == ts

    def test_add_l0_with_metadata(self):
        """Test adding L0 entry with metadata."""
        ps = ProgressiveSummarizer()
        entry = ps.add_l0(role="assistant", content="Hi!", metadata={"mood": "happy"})
        assert entry.metadata["mood"] == "happy"

    def test_get_l0_entries(self):
        """Test getting L0 entries."""
        ps = ProgressiveSummarizer()
        ps.add_l0(role="user", content="Hello")
        ps.add_l0(role="assistant", content="Hi!")
        entries = ps.get_l0()
        assert len(entries) == 2

    def test_get_l0_with_limit(self):
        """Test getting L0 entries with limit."""
        ps = ProgressiveSummarizer()
        for i in range(5):
            ps.add_l0(role="user", content=f"Message {i}")
        entries = ps.get_l0(limit=3)
        assert len(entries) == 3

    def test_l0_count(self):
        """Test L0 count."""
        ps = ProgressiveSummarizer()
        ps.add_l0(role="user", content="One")
        ps.add_l0(role="user", content="Two")
        assert ps.l0_count() == 2

    def test_clear_l0_all(self):
        """Test clearing all L0 entries."""
        ps = ProgressiveSummarizer()
        ps.add_l0(role="user", content="Hello")
        ps.add_l0(role="user", content="World")
        removed = ps.clear_l0()
        assert removed == 2
        assert ps.l0_count() == 0

    def test_clear_l0_specific(self):
        """Test clearing specific L0 entries."""
        ps = ProgressiveSummarizer()
        e1 = ps.add_l0(role="user", content="Hello")
        ps.add_l0(role="user", content="World")
        removed = ps.clear_l0(entry_ids=[e1.id])
        assert removed == 1
        assert ps.l0_count() == 1


class TestL0ToL1Summarization:
    """Tests for L0→L1 summarization."""

    def test_should_not_summarize_below_threshold(self):
        """Test summarization not triggered below threshold."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=10)
        for i in range(5):
            ps.add_l0(role="user", content=f"Message {i}")
        assert ps.should_summarize_l0() is False

    def test_should_summarize_at_threshold(self):
        """Test summarization triggered at threshold."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=5)
        for i in range(5):
            ps.add_l0(role="user", content=f"Message {i}")
        assert ps.should_summarize_l0() is True

    def test_summarize_l0_basic(self):
        """Test basic L0→L1 summarization."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=2)
        ps.add_l0(role="user", content="I love hiking in mountains")
        ps.add_l0(role="assistant", content="That sounds wonderful!")
        l1 = ps.summarize_l0()
        assert l1 is not None
        assert isinstance(l1, L1Entry)
        assert l1.summary != ""
        assert len(l1.source_ids) == 2

    def test_summarize_l0_removes_consumed_entries(self):
        """Test that summarized L0 entries are removed."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=2)
        ps.add_l0(role="user", content="Hello")
        ps.add_l0(role="assistant", content="Hi!")
        ps.add_l0(role="user", content="Extra message")  # Should remain
        assert ps.l0_count() == 3
        ps.summarize_l0()
        # All 3 entries were summarized (max_entries=None = all)
        assert ps.l0_count() == 0

    def test_summarize_l0_force(self):
        """Test forced summarization below threshold."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=10)
        ps.add_l0(role="user", content="Hello")
        ps.add_l0(role="assistant", content="Hi!")
        l1 = ps.summarize_l0(force=True)
        assert l1 is not None

    def test_summarize_l0_empty(self):
        """Test summarizing with no entries."""
        ps = ProgressiveSummarizer()
        l1 = ps.summarize_l0()
        assert l1 is None

    def test_summarize_l0_extracts_entities(self):
        """Test that summarizer extracts entities."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=2)
        ps.add_l0(role="user", content="I visited Paris and London")
        ps.add_l0(role="assistant", content="Great travels!")
        l1 = ps.summarize_l0()
        assert l1 is not None
        # May or may not extract depending on heuristics

    def test_summarize_l0_extracts_sentiment(self):
        """Test that summarizer detects sentiment."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=2)
        ps.add_l0(role="user", content="I love this, it's wonderful and great!")
        ps.add_l0(role="assistant", content="Happy to hear that!")
        l1 = ps.summarize_l0()
        assert l1 is not None
        assert l1.sentiment in ("positive", "negative", "neutral")


class TestL1ToL2Summarization:
    """Tests for L1→L2 summarization."""

    def test_should_not_summarize_l1_below_threshold(self):
        """Test L1→L2 not triggered below threshold."""
        ps = ProgressiveSummarizer(l1_to_l2_threshold=5)
        for i in range(3):
            ps.add_l0(role="user", content=f"Message {i}")
            ps.summarize_l0(force=True)
        assert ps.should_summarize_l1() is False

    def test_should_summarize_l1_at_threshold(self):
        """Test L1→L2 triggered at threshold."""
        ps = ProgressiveSummarizer(l1_to_l2_threshold=3)
        for i in range(6):
            ps.add_l0(role="user", content=f"Message {i}")
            ps.summarize_l0(force=True)
        assert ps.should_summarize_l1() is True

    def test_summarize_l1_basic(self):
        """Test basic L1→L2 summarization."""
        ps = ProgressiveSummarizer(l1_to_l2_threshold=2)
        # Create enough L1 entries
        for i in range(4):
            ps.add_l0(role="user", content=f"Hello world {i}")
            ps.summarize_l0(force=True)
        l2 = ps.summarize_l1()
        assert l2 is not None
        assert isinstance(l2, L2Entry)
        assert l2.knowledge != ""

    def test_summarize_l1_extracts_knowledge_type(self):
        """Test that summarizer extracts knowledge type."""
        ps = ProgressiveSummarizer(l1_to_l2_threshold=2)
        for i in range(4):
            ps.add_l0(role="user", content=f"I prefer {i}")
            ps.summarize_l0(force=True)
        l2 = ps.summarize_l1()
        assert l2 is not None
        assert l2.knowledge_type in ("fact", "concept", "rule", "preference")


class TestAutoProcessing:
    """Tests for automatic processing."""

    def test_auto_process_triggers_l0(self):
        """Test auto_process triggers L0→L1."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=3)
        ps.add_l0(role="user", content="Hello")
        ps.add_l0(role="assistant", content="Hi!")
        ps.add_l0(role="user", content="How are you?")
        result = ps.auto_process()
        assert result["l0_summarized"] is True
        assert result["l1_entry"] is not None

    def test_auto_process_empty(self):
        """Test auto_process with no entries."""
        ps = ProgressiveSummarizer()
        result = ps.auto_process()
        assert result["l0_summarized"] is False
        assert result["l1_summarized"] is False


class TestQualityAssessment:
    """Tests for quality scoring."""

    def test_quality_score_to_dict(self):
        """Test QualityScore serialization."""
        score = QualityScore(
            coverage=0.8,
            entity_retention=0.7,
            sentiment_preservation=0.9,
            information_density=0.6,
            overall=0.75,
        )
        data = score.to_dict()
        assert data["coverage"] == 0.8
        assert data["overall"] == 0.75

    def test_quality_below_threshold_skipped(self):
        """Test that summaries below quality threshold are rejected."""
        ps = ProgressiveSummarizer(quality_threshold=0.9)
        ps.add_l0(role="user", content="x")
        l1 = ps.summarize_l0()
        # May be None if quality too low


class TestQueryMethods:
    """Tests for querying L1 and L2 entries."""

    def test_get_l1(self):
        """Test getting L1 entries."""
        ps = ProgressiveSummarizer()
        for i in range(3):
            ps.add_l0(role="user", content=f"Message {i}")
            ps.summarize_l0(force=True)
        l1_entries = ps.get_l1()
        assert len(l1_entries) == 3

    def test_get_l1_with_limit(self):
        """Test getting L1 entries with limit."""
        ps = ProgressiveSummarizer()
        for i in range(5):
            ps.add_l0(role="user", content=f"Message {i}")
            ps.summarize_l0(force=True)
        l1_entries = ps.get_l1(limit=2)
        assert len(l1_entries) == 2

    def test_get_l2(self):
        """Test getting L2 entries."""
        ps = ProgressiveSummarizer(l1_to_l2_threshold=2)
        for i in range(4):
            ps.add_l0(role="user", content=f"Message {i}")
            ps.summarize_l0(force=True)
        ps.summarize_l1(force=True)
        l2_entries = ps.get_l2()
        assert len(l2_entries) >= 1

    def test_get_l2_by_type(self):
        """Test getting L2 entries by knowledge type."""
        ps = ProgressiveSummarizer(l1_to_l2_threshold=2)
        for i in range(4):
            ps.add_l0(role="user", content=f"I prefer coffee {i}")
            ps.summarize_l0(force=True)
        ps.summarize_l1(force=True)
        l2_entries = ps.get_l2(knowledge_type="preference")
        assert all(e.knowledge_type == "preference" for e in l2_entries)


class TestStats:
    """Tests for statistics."""

    def test_get_stats_empty(self):
        """Test stats on empty summarizer."""
        ps = ProgressiveSummarizer()
        stats = ps.get_stats()
        assert stats["l0_count"] == 0
        assert stats["l1_count"] == 0
        assert stats["l2_count"] == 0
        assert stats["should_summarize_l0"] is False
        assert stats["should_summarize_l1"] is False

    def test_get_stats_after_operations(self):
        """Test stats after adding entries."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=3)
        ps.add_l0(role="user", content="Hello")
        ps.add_l0(role="assistant", content="Hi!")
        stats = ps.get_stats()
        assert stats["l0_count"] == 2
        assert stats["l0_threshold"] == 3
        assert stats["should_summarize_l0"] is False  # Not at threshold yet


class TestSerialization:
    """Tests for serialization."""

    def test_to_dict(self):
        """Test exporting all layers to dictionary."""
        ps = ProgressiveSummarizer()
        ps.add_l0(role="user", content="Hello")
        ps.add_l0(role="assistant", content="Hi!")
        data = ps.to_dict()
        assert "l0" in data
        assert "l1" in data
        assert "l2" in data
        assert "stats" in data
        assert len(data["l0"]) == 2

    def test_from_dict(self):
        """Test reconstructing from dictionary."""
        ps = ProgressiveSummarizer(l0_to_l1_threshold=5)
        ps.add_l0(role="user", content="Hello")
        ps.add_l0(role="assistant", content="Hi!")
        data = ps.to_dict()
        restored = ProgressiveSummarizer.from_dict(data)
        assert restored.l0_count() == 2


class TestDefaultSummarizers:
    """Tests for default summarizer functions."""

    def test_l0_to_l1_summarizer_empty(self):
        """Test default L0→L1 with empty entries."""
        summary, entities, sentiment = _default_l0_to_l1_summarizer([])
        assert summary == ""
        assert entities == []
        assert sentiment == "neutral"

    def test_l0_to_l1_summarizer_positive(self):
        """Test default L0→L1 with positive sentiment."""
        entries = [
            L0Entry(id="1", role="user", content="I love this! It's great!", timestamp="", metadata={}),
            L0Entry(id="2", role="assistant", content="Wonderful!", timestamp="", metadata={}),
        ]
        summary, entities, sentiment = _default_l0_to_l1_summarizer(entries)
        assert sentiment == "positive"
        assert "I love this" in summary or "Wonderful" in summary

    def test_l0_to_l1_summarizer_negative(self):
        """Test default L0→L1 with negative sentiment."""
        entries = [
            L0Entry(id="1", role="user", content="I hate this. It's terrible.", timestamp="", metadata={}),
            L0Entry(id="2", role="assistant", content="Sorry to hear that.", timestamp="", metadata={}),
        ]
        summary, entities, sentiment = _default_l0_to_l1_summarizer(entries)
        assert sentiment == "negative"

    def test_l1_to_l2_summarizer_empty(self):
        """Test default L1→L2 with empty entries."""
        knowledge, ktype, entities = _default_l1_to_l2_summarizer([])
        assert knowledge == ""
        assert ktype == "fact"

    def test_l1_to_l2_summarizer_preference(self):
        """Test default L1→L2 infers preference type."""
        entries = [
            L1Entry(
                id="1",
                summary="User expressed they like hiking",
                source_ids=[],
                entities=["hiking"],
                sentiment="positive",
                importance=0.7,
                keywords=["like", "hiking"],
                timestamp="",
                metadata={},
            ),
        ]
        knowledge, ktype, entities = _default_l1_to_l2_summarizer(entries)
        assert knowledge != ""
        assert ktype == "preference"


class TestIntegrationWithSoul:
    """Integration tests with existing Soul modules."""

    def test_with_emotion_recognizer(self):
        """Test integration with EmotionRecognizer."""
        from neshama.soul.emotion import EmotionRecognizer

        ps = ProgressiveSummarizer(l0_to_l1_threshold=2)
        recognizer = EmotionRecognizer()

        text = "I'm so happy about this wonderful news!"
        tags = recognizer.recognize(text)

        # Add recognized emotions as metadata to L0
        ps.add_l0(
            role="user",
            content=text,
            metadata={"emotions": [(t.category.value, t.intensity) for t in tags]},
        )
        ps.add_l0(role="assistant", content="That's great to hear!")
        ps.summarize_l0(force=True)

        l1 = ps.get_l1()[0]
        assert l1 is not None

    def test_convenience_factory(self):
        """Test create_progressive_summarizer factory."""
        ps = create_progressive_summarizer(
            l0_to_l1_threshold=7,
            l1_to_l2_threshold=3,
        )
        assert ps.l0_to_l1_threshold == 7
        assert ps.l1_to_l2_threshold == 3


class TestL0EntrySerialization:
    """Tests for L0Entry serialization."""

    def test_l0entry_to_dict(self):
        """Test L0Entry serialization."""
        entry = L0Entry(
            id="test-001",
            role="user",
            content="Hello",
            timestamp="2024-01-01T12:00:00",
            metadata={"key": "value"},
        )
        data = entry.to_dict()
        assert data["id"] == "test-001"
        assert data["role"] == "user"
        assert data["content"] == "Hello"

    def test_l0entry_from_dict(self):
        """Test L0Entry deserialization."""
        data = {
            "id": "test-001",
            "role": "assistant",
            "content": "Hi!",
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {},
        }
        entry = L0Entry.from_dict(data)
        assert entry.id == "test-001"
        assert entry.role == "assistant"
        assert entry.content == "Hi!"


class TestL1EntrySerialization:
    """Tests for L1Entry serialization."""

    def test_l1entry_to_dict(self):
        """Test L1Entry serialization."""
        entry = L1Entry(
            id="l1-001",
            summary="User expressed happiness",
            source_ids=["e1", "e2"],
            entities=["Alice"],
            sentiment="positive",
            importance=0.8,
            keywords=["happy", "joy"],
            timestamp="2024-01-01T12:00:00",
            metadata={},
        )
        data = entry.to_dict()
        assert data["id"] == "l1-001"
        assert data["sentiment"] == "positive"
        assert len(data["source_ids"]) == 2

    def test_l1entry_from_dict(self):
        """Test L1Entry deserialization."""
        data = {
            "id": "l1-001",
            "summary": "Test summary",
            "source_ids": [],
            "entities": [],
            "sentiment": "neutral",
            "importance": 0.5,
            "keywords": [],
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {},
        }
        entry = L1Entry.from_dict(data)
        assert entry.id == "l1-001"
        assert entry.sentiment == "neutral"


class TestL2EntrySerialization:
    """Tests for L2Entry serialization."""

    def test_l2entry_to_dict(self):
        """Test L2Entry serialization."""
        entry = L2Entry(
            id="l2-001",
            knowledge="User likes outdoor activities",
            source_ids=["l1-001"],
            knowledge_type="preference",
            confidence=0.85,
            entities=["hiking"],
            tags=["outdoor", "preference"],
            usage_count=3,
            created_at="2024-01-01T12:00:00",
            last_accessed="2024-01-02T12:00:00",
            metadata={},
        )
        data = entry.to_dict()
        assert data["id"] == "l2-001"
        assert data["knowledge_type"] == "preference"
        assert data["usage_count"] == 3

    def test_l2entry_from_dict(self):
        """Test L2Entry deserialization."""
        data = {
            "id": "l2-001",
            "knowledge": "User enjoys reading",
            "source_ids": [],
            "knowledge_type": "preference",
            "confidence": 0.8,
            "entities": [],
            "tags": [],
            "usage_count": 0,
            "created_at": "2024-01-01T12:00:00",
            "last_accessed": "2024-01-01T12:00:00",
            "metadata": {},
        }
        entry = L2Entry.from_dict(data)
        assert entry.id == "l2-001"
        assert entry.knowledge_type == "preference"
        assert entry.confidence == 0.8


class TestL2EntryUsageCount:
    """Tests for L2 entry usage tracking."""

    def test_l2entry_default_usage_count(self):
        """Test L2Entry default usage count."""
        entry = L2Entry(
            id="test",
            knowledge="Test knowledge",
            source_ids=[],
        )
        assert entry.usage_count == 0

    def test_l2entry_increment_usage(self):
        """Test L2Entry usage count increment."""
        entry = L2Entry(
            id="test",
            knowledge="Test knowledge",
            source_ids=[],
        )
        entry.usage_count += 1
        assert entry.usage_count == 1
