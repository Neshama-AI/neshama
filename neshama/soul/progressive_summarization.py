# Soul Layer - Progressive Summarization Module
"""
Progressive Summarization

Automatically condenses memory layers from raw conversation to semantic knowledge.

Layers:
- L0: Raw conversation turns (ShortTermMemory)
- L1: Episodic summaries (key events, facts, feelings)
- L2: Semantic knowledge (generalized facts, concepts)

Transitions:
- L0→L1: When L0 has > threshold entries, summarize conversation fragments
- L1→L2: When L1 entries are old or accumulated, abstract to knowledge

Quality:
- Key information retention score
- Entity/keyword coverage
- Sentiment preservation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
import hashlib
import threading
import uuid


@dataclass
class L0Entry:
    """Raw L0 conversation turn."""
    id: str
    role: str          # "user" | "assistant" | "system"
    content: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "L0Entry":
        return cls(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class L1Entry:
    """L1 episodic summary of a group of L0 entries."""
    id: str
    summary: str        # Natural language summary
    source_ids: List[str]  # IDs of L0 entries this summarizes
    entities: List[str] = field(default_factory=list)  # Named entities
    sentiment: str = "neutral"  # "positive" | "negative" | "neutral"
    importance: float = 0.5
    keywords: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "source_ids": self.source_ids,
            "entities": self.entities,
            "sentiment": self.sentiment,
            "importance": self.importance,
            "keywords": self.keywords,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "L1Entry":
        return cls(
            id=data["id"],
            summary=data["summary"],
            source_ids=data.get("source_ids", []),
            entities=data.get("entities", []),
            sentiment=data.get("sentiment", "neutral"),
            importance=data.get("importance", 0.5),
            keywords=data.get("keywords", []),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class L2Entry:
    """L2 semantic knowledge extracted from L1 entries."""
    id: str
    knowledge: str      # Generalized knowledge statement
    source_ids: List[str]  # IDs of L1 entries this abstracts
    knowledge_type: str = "fact"  # "fact" | "concept" | "rule" | "preference"
    confidence: float = 0.5
    entities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "knowledge": self.knowledge,
            "source_ids": self.source_ids,
            "knowledge_type": self.knowledge_type,
            "confidence": self.confidence,
            "entities": self.entities,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "L2Entry":
        return cls(
            id=data["id"],
            knowledge=data["knowledge"],
            source_ids=data.get("source_ids", []),
            knowledge_type=data.get("knowledge_type", "fact"),
            confidence=data.get("confidence", 0.5),
            entities=data.get("entities", []),
            tags=data.get("tags", []),
            usage_count=data.get("usage_count", 0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_accessed=data.get("last_accessed", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class QualityScore:
    """Quality assessment for a summary."""
    coverage: float          # 0-1, how much source content is covered
    entity_retention: float  # 0-1, named entity preservation
    sentiment_preservation: float  # 0-1, sentiment match
    information_density: float  # 0-1, conciseness vs completeness
    overall: float           # 0-1, weighted composite

    def to_dict(self) -> Dict[str, float]:
        return {
            "coverage": round(self.coverage, 4),
            "entity_retention": round(self.entity_retention, 4),
            "sentiment_preservation": round(self.sentiment_preservation, 4),
            "information_density": round(self.information_density, 4),
            "overall": round(self.overall, 4),
        }


# ── Default summarizer (rule-based, no external API needed) ──────────────────

def _default_l0_to_l1_summarizer(
    entries: List[L0Entry],
) -> Tuple[str, List[str], List[str]]:
    """
    Default L0→L1 summarizer using simple extraction heuristics.

    Returns:
        (summary_text, entities, sentiment)
    """
    if not entries:
        return "", [], "neutral"

    # Concatenate content
    all_content = " ".join(e.content for e in entries)

    # Simple entity extraction (capitalized words and specific patterns)
    import re
    entities = []
    # Look for capitalized multi-word phrases
    capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*", all_content)
    entities.extend(capitalized[:10])  # cap at 10
    # Quoted strings
    quoted = re.findall(r'"([^"]*)"', all_content)
    entities.extend(quoted[:5])

    # Simple sentiment: check keyword counts
    positive_words = ["good", "great", "happy", "love", "like", "best", "nice", "开心", "好", "喜欢", "棒", "赞"]
    negative_words = ["bad", "sad", "hate", "angry", "worst", "terrible", "难过", "讨厌", "生气", "差", "烂"]
    pos_count = sum(1 for w in positive_words if w.lower() in all_content.lower())
    neg_count = sum(1 for w in negative_words if w.lower() in all_content.lower())

    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Simple extractive summary: first and last non-system turns
    user_entries = [e for e in entries if e.role == "user"]
    assistant_entries = [e for e in entries if e.role == "assistant"]

    summary_parts = []
    if user_entries:
        summary_parts.append(f"User: {user_entries[0].content[:100]}")
    if len(user_entries) > 1:
        summary_parts.append(f"User (follow-up): {user_entries[-1].content[:80]}")
    if assistant_entries:
        summary_parts.append(f"Assistant: {assistant_entries[0].content[:100]}")

    summary = " | ".join(summary_parts) if summary_parts else all_content[:150]

    # Deduplicate entities
    entities = list(dict.fromkeys(entities))
    return summary, entities, sentiment


def _default_l1_to_l2_summarizer(
    entries: List[L1Entry],
) -> Tuple[str, str, List[str]]:
    """
    Default L1→L2 summarizer: abstract episodic summaries into knowledge.

    Returns:
        (knowledge_statement, knowledge_type, entities)
    """
    if not entries:
        return "", "fact", []

    # Aggregate entities
    all_entities = []
    for e in entries:
        all_entities.extend(e.entities)
    all_entities = list(dict.fromkeys(all_entities))[:10]

    # Determine dominant sentiment
    sentiments = [e.sentiment for e in entries]
    dominant = max(set(sentiments), key=sentiments.count) if sentiments else "neutral"

    # Build knowledge statement from first summary
    first = entries[0]
    knowledge = f"During interaction: {first.summary[:200]}"
    if len(entries) > 1:
        knowledge += f" (related to {len(entries)-1} other similar events)"

    # Infer knowledge type from content
    knowledge_type = "fact"
    content_lower = first.summary.lower()
    if any(w in content_lower for w in ["prefer", "like", "want", "喜欢", "想要", "希望"]):
        knowledge_type = "preference"
    elif any(w in content_lower for w in ["always", "never", "must", "should", "总是", "应该"]):
        knowledge_type = "rule"
    elif any(w in content_lower for w in ["what is", "define", "概念", "是什么"]):
        knowledge_type = "concept"

    return knowledge, knowledge_type, all_entities


# ── Progressive Summarizer ─────────────────────────────────────────────────────

class ProgressiveSummarizer:
    """
    Progressive Summarization Engine.

    Condenses memory from raw conversation (L0) through episodic (L1) to
    semantic knowledge (L2), automatically triggered by thresholds.

    Example:
        >>> summarizer = ProgressiveSummarizer(
        ...     l0_to_l1_threshold=10,   # Summarize when L0 has 10+ entries
        ...     l1_to_l2_age_days=7,    # Summarize L1 entries older than 7 days
        ... )
        >>>
        >>> # Add L0 entries
        >>> summarizer.add_l0(role="user", content="I love hiking")
        >>> summarizer.add_l0(role="assistant", content="That's great!")
        >>>
        >>> # Trigger summarization if threshold reached
        >>> if summarizer.should_summarize_l0():
        ...     result = summarizer.summarize_l0()
        >>>     print(result.summary)
    """

    def __init__(
        self,
        l0_to_l1_threshold: int = 10,
        l1_to_l2_threshold: int = 5,
        l1_to_l2_age_days: int = 7,
        l1_max_age_hours: int = 24 * 7,
        summarizer_l0_to_l1: Optional[Callable] = None,
        summarizer_l1_to_l2: Optional[Callable] = None,
        quality_threshold: float = 0.3,
    ):
        """
        Initialize ProgressiveSummarizer.

        Args:
            l0_to_l1_threshold: Number of L0 entries before auto-L0→L1
            l1_to_l2_threshold: Number of L1 entries before L1→L2
            l1_to_l2_age_days: L1 entries older than this trigger L1→L2
            l1_max_age_hours: Maximum age in hours before L1 is forced to L2
            summarizer_l0_to_l1: Custom summarizer function
            summarizer_l1_to_l2: Custom summarizer function
            quality_threshold: Minimum quality score to accept summary
        """
        self.l0_to_l1_threshold = l0_to_l1_threshold
        self.l1_to_l2_threshold = l1_to_l2_threshold
        self.l1_to_l2_age_days = l1_to_l2_age_days
        self.l1_max_age_hours = l1_max_age_hours
        self.quality_threshold = quality_threshold

        self._l0_entries: List[L0Entry] = []
        self._l1_entries: List[L1Entry] = []
        self._l2_entries: List[L2Entry] = []
        self._l0_summarizer = summarizer_l0_to_l1 or _default_l0_to_l1_summarizer
        self._l1_summarizer = summarizer_l1_to_l2 or _default_l1_to_l2_summarizer
        self._lock = threading.RLock()

    # ── L0 Management ─────────────────────────────────────────────────────────

    def add_l0(
        self,
        role: str,
        content: str,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> L0Entry:
        """Add a raw L0 conversation turn."""
        entry = L0Entry(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=timestamp or datetime.now().isoformat(),
            metadata=metadata or {},
        )
        with self._lock:
            self._l0_entries.append(entry)
        return entry

    def get_l0(self, limit: Optional[int] = None) -> List[L0Entry]:
        """Get L0 entries."""
        with self._lock:
            if limit:
                return list(self._l0_entries[-limit:])
            return list(self._l0_entries)

    def clear_l0(self, entry_ids: Optional[List[str]] = None) -> int:
        """
        Clear L0 entries. If entry_ids provided, remove only those.

        Returns:
            Number of entries removed
        """
        with self._lock:
            if entry_ids:
                before = len(self._l0_entries)
                self._l0_entries = [
                    e for e in self._l0_entries if e.id not in entry_ids
                ]
                return before - len(self._l0_entries)
            else:
                count = len(self._l0_entries)
                self._l0_entries.clear()
                return count

    def l0_count(self) -> int:
        """Count L0 entries."""
        with self._lock:
            return len(self._l0_entries)

    # ── L0 → L1 ───────────────────────────────────────────────────────────────

    def should_summarize_l0(self) -> bool:
        """Check if L0 should be summarized (threshold reached)."""
        return self.l0_count() >= self.l0_to_l1_threshold

    def summarize_l0(
        self,
        max_entries: Optional[int] = None,
        force: bool = False,
    ) -> Optional[L1Entry]:
        """
        Summarize L0 entries into L1 episodic summary.

        Args:
            max_entries: Max L0 entries to include (oldest first). None = all.
            force: If True, summarize even if below threshold.

        Returns:
            Created L1Entry, or None if nothing to summarize.
        """
        with self._lock:
            if not force and not self.should_summarize_l0():
                return None

            if not self._l0_entries:
                return None

            # Take entries to summarize
            entries_to_summarize = self._l0_entries[:max_entries]
            source_ids = [e.id for e in entries_to_summarize]

            # Call summarizer
            summary_text, entities, sentiment = self._l0_summarizer(entries_to_summarize)

            # Quality assessment
            quality = self._assess_quality_l0(entries_to_summarize, summary_text, entities)

            if quality.overall < self.quality_threshold and not force:
                return None

            # Extract keywords
            keywords = self._extract_keywords(entries_to_summarize)

            l1_entry = L1Entry(
                id=str(uuid.uuid4()),
                summary=summary_text,
                source_ids=source_ids,
                entities=entities,
                sentiment=sentiment,
                importance=quality.overall,
                keywords=keywords,
            )

            self._l1_entries.append(l1_entry)

            # Remove summarized L0 entries
            consumed_ids = set(source_ids)
            self._l0_entries = [e for e in self._l0_entries if e.id not in consumed_ids]

            return l1_entry

    # ── L1 → L2 ───────────────────────────────────────────────────────────────

    def should_summarize_l1(self) -> bool:
        """Check if L1 should be summarized to L2."""
        with self._lock:
            if len(self._l1_entries) >= self.l1_to_l2_threshold:
                return True
            # Check age
            for entry in self._l1_entries:
                ts = datetime.fromisoformat(entry.timestamp)
                age_hours = (datetime.now() - ts).total_seconds() / 3600
                if age_hours >= self.l1_max_age_hours:
                    return True
            return False

    def summarize_l1(
        self,
        max_entries: Optional[int] = None,
        force: bool = False,
    ) -> Optional[L2Entry]:
        """
        Summarize L1 episodic entries into L2 semantic knowledge.

        Args:
            max_entries: Max L1 entries to include. None = all.
            force: If True, summarize even if conditions not met.

        Returns:
            Created L2Entry, or None if nothing to summarize.
        """
        with self._lock:
            if not force and not self.should_summarize_l1():
                return None

            if not self._l1_entries:
                return None

            entries_to_summarize = self._l1_entries[:max_entries or len(self._l1_entries)]
            source_ids = [e.id for e in entries_to_summarize]

            # Call L1→L2 summarizer
            knowledge, ktype, entities = self._l1_summarizer(entries_to_summarize)

            # Quality
            quality = self._assess_quality_l1(entries_to_summarize, knowledge)

            if quality.overall < self.quality_threshold and not force:
                return None

            # Tags from keywords
            tags = []
            for entry in entries_to_summarize:
                tags.extend(entry.keywords[:3])
            tags = list(dict.fromkeys(tags))[:10]

            l2_entry = L2Entry(
                id=str(uuid.uuid4()),
                knowledge=knowledge,
                source_ids=source_ids,
                knowledge_type=ktype,
                confidence=quality.overall,
                entities=entities,
                tags=tags,
            )

            self._l2_entries.append(l2_entry)

            # Remove summarized L1 entries
            consumed = set(source_ids)
            self._l1_entries = [e for e in self._l1_entries if e.id not in consumed]

            return l2_entry

    # ── Auto Summarization ────────────────────────────────────────────────────

    def auto_process(self) -> Dict[str, Any]:
        """
        Run automatic summarization for both L0→L1 and L1→L2.

        Returns:
            Summary of what was processed
        """
        results = {
            "l0_summarized": False,
            "l1_summarized": False,
            "l1_entry": None,
            "l2_entry": None,
        }

        if self.should_summarize_l0():
            l1 = self.summarize_l0()
            if l1:
                results["l0_summarized"] = True
                results["l1_entry"] = l1.to_dict()

        if self.should_summarize_l1():
            l2 = self.summarize_l1()
            if l2:
                results["l1_summarized"] = True
                results["l2_entry"] = l2.to_dict()

        return results

    # ── Quality Assessment ─────────────────────────────────────────────────────

    def _assess_quality_l0(
        self,
        entries: List[L0Entry],
        summary: str,
        entities: List[str],
    ) -> QualityScore:
        """Assess quality of L0→L1 summary."""
        if not entries:
            return QualityScore(0, 0, 0, 0, 0)

        # Coverage: how much source text length is captured
        source_len = sum(len(e.content) for e in entries)
        summary_len = len(summary)
        coverage = min(1.0, summary_len / max(source_len, 1) * 3)  # Allow 3x compression

        # Entity retention: how many entities appear in summary
        source_entities = set(e.content for e in entries)
        retained = sum(1 for ent in entities if ent in summary)
        entity_retention = min(1.0, retained / max(len(entities), 1))

        # Sentiment preservation (simple check)
        sentiment_keywords = {
            "positive": ["good", "great", "happy", "love", "like", "开心", "好", "喜欢", "棒"],
            "negative": ["bad", "sad", "hate", "angry", "worst", "terrible", "难过", "讨厌", "生气"],
        }
        source_lower = " ".join(e.content.lower() for e in entries)
        summary_lower = summary.lower()
        source_pos = sum(1 for w in sentiment_keywords["positive"] if w in source_lower)
        source_neg = sum(1 for w in sentiment_keywords["negative"] if w in source_lower)
        summary_pos = sum(1 for w in sentiment_keywords["positive"] if w in summary_lower)
        summary_neg = sum(1 for w in sentiment_keywords["negative"] if w in summary_lower)

        if (source_pos + source_neg) == 0:
            sentiment_preservation = 1.0
        else:
            sent_diff = abs((source_pos - source_neg) - (summary_pos - summary_neg))
            sentiment_preservation = max(0, 1.0 - sent_diff / 2)

        # Information density: concise but complete
        # Ideal summary length is ~20% of source for extractive
        ideal_ratio = 0.2
        actual_ratio = summary_len / max(source_len, 1)
        info_density = 1.0 - abs(actual_ratio - ideal_ratio)
        info_density = max(0, min(1, info_density))

        overall = (
            coverage * 0.25 +
            entity_retention * 0.25 +
            sentiment_preservation * 0.2 +
            info_density * 0.3
        )

        return QualityScore(
            coverage=coverage,
            entity_retention=entity_retention,
            sentiment_preservation=sentiment_preservation,
            information_density=info_density,
            overall=overall,
        )

    def _assess_quality_l1(self, entries: List[L1Entry], knowledge: str) -> QualityScore:
        """Assess quality of L1→L2 summary."""
        if not entries:
            return QualityScore(0, 0, 0, 0, 0)

        # For L1→L2, coverage measures how many L1 entries are abstracted
        coverage = min(1.0, len(entries) / max(self.l1_to_l2_threshold, 1))

        # Entity retention: aggregated entities
        all_entities = []
        for e in entries:
            all_entities.extend(e.entities)
        unique_entities = set(all_entities)
        entity_retention = min(1.0, len(unique_entities) / max(len(all_entities), 1))

        # Sentiment preservation
        sentiments = [e.sentiment for e in entries]
        dominant = max(set(sentiments), key=sentiments.count) if sentiments else "neutral"
        sentiment_preservation = 1.0 if dominant in knowledge.lower() else 0.5

        # Information density
        info_density = min(1.0, len(knowledge) / 500)  # 500 chars is good density

        overall = (
            coverage * 0.3 +
            entity_retention * 0.2 +
            sentiment_preservation * 0.2 +
            info_density * 0.3
        )

        return QualityScore(
            coverage=coverage,
            entity_retention=entity_retention,
            sentiment_preservation=sentiment_preservation,
            information_density=info_density,
            overall=overall,
        )

    def _extract_keywords(self, entries: List[L0Entry]) -> List[str]:
        """Extract top keywords from L0 entries."""
        import re
        # Collect words 3+ chars, filter stopwords
        stopwords = {
            "the", "and", "is", "in", "to", "of", "a", "that", "this", "it",
            "我", "的", "是", "在", "了", "和", "也", "都", "有", "就", "不",
            "not", "but", "with", "for", "on", "at", "by", "or", "an", "so",
        }
        text = " ".join(e.content for e in entries)
        words = re.findall(r"\b[a-zA-Z\u4e00-\u9fff]{3,}\b", text.lower())
        freq: Dict[str, int] = {}
        for w in words:
            if w not in stopwords:
                freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:20]]

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_l1(self, limit: Optional[int] = None) -> List[L1Entry]:
        """Get L1 entries."""
        with self._lock:
            entries = sorted(self._l1_entries, key=lambda e: e.timestamp, reverse=True)
            return entries[:limit] if limit else entries

    def get_l2(
        self,
        knowledge_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[L2Entry]:
        """Get L2 entries."""
        with self._lock:
            entries = self._l2_entries
            if knowledge_type:
                entries = [e for e in entries if e.knowledge_type == knowledge_type]
            entries = sorted(entries, key=lambda e: e.last_accessed, reverse=True)
            return entries[:limit] if limit else entries

    def get_stats(self) -> Dict[str, Any]:
        """Get layer statistics."""
        with self._lock:
            return {
                "l0_count": len(self._l0_entries),
                "l1_count": len(self._l1_entries),
                "l2_count": len(self._l2_entries),
                "l0_threshold": self.l0_to_l1_threshold,
                "l1_threshold": self.l1_to_l2_threshold,
                "should_summarize_l0": self.should_summarize_l0(),
                "should_summarize_l1": self.should_summarize_l1(),
            }

    def to_dict(self) -> Dict[str, Any]:
        """Export all layers."""
        with self._lock:
            return {
                "l0": [e.to_dict() for e in self._l0_entries],
                "l1": [e.to_dict() for e in self._l1_entries],
                "l2": [e.to_dict() for e in self._l2_entries],
                "stats": self.get_stats(),
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressiveSummarizer":
        """Reconstruct from dictionary."""
        ps = cls()
        for entry_data in data.get("l0", []):
            ps._l0_entries.append(L0Entry.from_dict(entry_data))
        for entry_data in data.get("l1", []):
            ps._l1_entries.append(L1Entry.from_dict(entry_data))
        for entry_data in data.get("l2", []):
            ps._l2_entries.append(L2Entry.from_dict(entry_data))
        return ps


# ── Convenience ────────────────────────────────────────────────────────────────

def create_progressive_summarizer(**kwargs) -> ProgressiveSummarizer:
    """Create a configured ProgressiveSummarizer."""
    return ProgressiveSummarizer(**kwargs)
