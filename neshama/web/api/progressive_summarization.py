"""
Progressive Summarization API - Web endpoints for memory summarization.
"""

from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException

router = APIRouter()

# Module-level summarizer instances
_summarizer_instances: Dict[str, Dict[str, Any]] = {}


def get_or_create_summarizer(
    summarizer_id: str,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
) -> Dict[str, Any]:
    """Get or create a summarizer instance."""
    if summarizer_id not in _summarizer_instances:
        from neshama.soul.progressive_summarization import ProgressiveSummarizer
        _summarizer_instances[summarizer_id] = {
            "summarizer": ProgressiveSummarizer(
                l0_to_l1_threshold=l0_threshold,
                l1_to_l2_threshold=l1_threshold,
                l1_to_l2_age_days=l1_age_days,
            ),
        }
    return _summarizer_instances[summarizer_id]


@router.post("/create")
async def create_summarizer(
    summarizer_id: str,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Create a new progressive summarizer."""
    data = get_or_create_summarizer(
        summarizer_id,
        l0_threshold=l0_threshold,
        l1_threshold=l1_threshold,
        l1_age_days=l1_age_days,
    )
    return {
        "success": True,
        "data": {
            "summarizer_id": summarizer_id,
            "l0_threshold": l0_threshold,
            "l1_threshold": l1_threshold,
            "l1_age_days": l1_age_days,
        }
    }


@router.post("/l0/add")
async def add_l0_entry(
    summarizer_id: str,
    role: str,
    content: str,
    timestamp: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Add a raw L0 conversation turn."""
    data = get_or_create_summarizer(summarizer_id, l0_threshold, l1_threshold, l1_age_days)
    summarizer = data["summarizer"]
    entry = summarizer.add_l0(role=role, content=content, timestamp=timestamp, metadata=metadata)
    return {
        "success": True,
        "data": {
            "entry": entry.to_dict(),
            "l0_count": summarizer.l0_count(),
            "should_summarize": summarizer.should_summarize_l0(),
        }
    }


@router.get("/l0")
async def get_l0_entries(
    summarizer_id: str,
    limit: Optional[int] = None,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Get L0 entries."""
    data = get_or_create_summarizer(summarizer_id, l0_threshold, l1_threshold, l1_age_days)
    summarizer = data["summarizer"]
    entries = summarizer.get_l0(limit=limit)
    return {
        "success": True,
        "data": {
            "entries": [e.to_dict() for e in entries],
            "count": len(entries),
        }
    }


@router.post("/summarize-l0")
async def summarize_l0(
    summarizer_id: str,
    force: bool = False,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Summarize L0 entries to L1 episodic summary."""
    data = get_or_create_summarizer(summarizer_id, l0_threshold, l1_threshold, l1_age_days)
    summarizer = data["summarizer"]
    result = summarizer.summarize_l0(force=force)
    if result is None:
        return {
            "success": True,
            "data": {"summarized": False, "reason": "below_threshold or no entries"},
        }
    return {
        "success": True,
        "data": {
            "summarized": True,
            "l1_entry": result.to_dict(),
            "remaining_l0": summarizer.l0_count(),
        }
    }


@router.post("/summarize-l1")
async def summarize_l1(
    summarizer_id: str,
    force: bool = False,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Summarize L1 entries to L2 semantic knowledge."""
    data = get_or_create_summarizer(summarizer_id, l0_threshold, l1_threshold, l1_age_days)
    summarizer = data["summarizer"]
    result = summarizer.summarize_l1(force=force)
    if result is None:
        return {
            "success": True,
            "data": {"summarized": False, "reason": "below_threshold or no entries"},
        }
    return {
        "success": True,
        "data": {
            "summarized": True,
            "l2_entry": result.to_dict(),
        }
    }


@router.post("/auto-process")
async def auto_process(
    summarizer_id: str,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Run automatic summarization for both layers."""
    data = get_or_create_summarizer(summarizer_id, l0_threshold, l1_threshold, l1_age_days)
    summarizer = data["summarizer"]
    result = summarizer.auto_process()
    return {"success": True, "data": result}


@router.get("/l1")
async def get_l1_entries(
    summarizer_id: str,
    limit: Optional[int] = None,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Get L1 episodic entries."""
    data = get_or_create_summarizer(summarizer_id, l0_threshold, l1_threshold, l1_age_days)
    summarizer = data["summarizer"]
    entries = summarizer.get_l1(limit=limit)
    return {
        "success": True,
        "data": {
            "entries": [e.to_dict() for e in entries],
            "count": len(entries),
        }
    }


@router.get("/l2")
async def get_l2_entries(
    summarizer_id: str,
    knowledge_type: Optional[str] = None,
    limit: Optional[int] = None,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Get L2 semantic knowledge entries."""
    data = get_or_create_summarizer(summarizer_id, l0_threshold, l1_threshold, l1_age_days)
    summarizer = data["summarizer"]
    entries = summarizer.get_l2(knowledge_type=knowledge_type, limit=limit)
    return {
        "success": True,
        "data": {
            "entries": [e.to_dict() for e in entries],
            "count": len(entries),
        }
    }


@router.get("/stats")
async def get_stats(
    summarizer_id: str,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Get summarizer statistics."""
    data = get_or_create_summarizer(summarizer_id, l0_threshold, l1_threshold, l1_age_days)
    summarizer = data["summarizer"]
    return {"success": True, "data": summarizer.get_stats()}


@router.get("/state")
async def get_state(
    summarizer_id: str,
    l0_threshold: int = 10,
    l1_threshold: int = 5,
    l1_age_days: int = 7,
):
    """Get full summarizer state."""
    data = get_or_create_summarizer(summarizer_id, l0_threshold, l1_threshold, l1_age_days)
    summarizer = data["summarizer"]
    return {"success": True, "data": summarizer.to_dict()}
