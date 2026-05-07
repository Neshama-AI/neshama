"""
Composite Emotion API - Web endpoints for composite emotion engine.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException

router = APIRouter()

# Module-level engine instance for stateful API
_engine_instances: Dict[str, Dict] = {}


def get_or_create_engine(soul_id: str, neuroticism: float = 0.5) -> Dict[str, Any]:
    """Get or create a composite emotion engine instance."""
    if soul_id not in _engine_instances:
        from neshama.soul.emotion.composite import CompositeEmotion
        _engine_instances[soul_id] = {
            "engine": CompositeEmotion(neuroticism=neuroticism),
            "neuroticism": neuroticism,
            "created_at": datetime.now().isoformat(),
        }
    return _engine_instances[soul_id]


@router.post("/engine")
async def create_engine(soul_id: str, neuroticism: float = 0.5):
    """Create a new composite emotion engine."""
    if not 0 <= neuroticism <= 1:
        raise HTTPException(status_code=400, detail="neuroticism must be between 0 and 1")

    data = get_or_create_engine(soul_id, neuroticism)
    return {
        "success": True,
        "data": {
            "soul_id": soul_id,
            "neuroticism": data["neuroticism"],
            "created_at": data["created_at"],
        }
    }


@router.post("/emotions")
async def set_emotion(
    soul_id: str,
    emotion: str,
    intensity: float,
    neuroticism: Optional[float] = None,
):
    """Set a base emotion intensity."""
    data = get_or_create_engine(soul_id, neuroticism or data.get("neuroticism", 0.5))
    engine = data["engine"]
    state = engine.set_base_emotion(emotion, intensity)
    return {
        "success": True,
        "data": {
            "emotion": state.emotion,
            "intensity": round(state.intensity, 4),
            "timestamp": state.timestamp.isoformat(),
        }
    }


@router.post("/emotions/adjust")
async def adjust_emotion(
    soul_id: str,
    emotion: str,
    delta: float,
    neuroticism: Optional[float] = None,
):
    """Adjust an existing emotion by a delta."""
    data = get_or_create_engine(soul_id, neuroticism or data.get("neuroticism", 0.5))
    engine = data["engine"]
    state = engine.adjust_emotion(emotion, delta)
    return {
        "success": True,
        "data": {
            "emotion": state.emotion,
            "intensity": round(state.intensity, 4),
            "timestamp": state.timestamp.isoformat(),
        }
    }


@router.get("/emotions")
async def get_emotions(soul_id: str):
    """Get all active base emotions."""
    if soul_id not in _engine_instances:
        return {"success": True, "data": {"emotions": {}, "composite": None}}
    engine = _engine_instances[soul_id]["engine"]
    return {
        "success": True,
        "data": {
            "emotions": {k: round(v, 4) for k, v in engine.get_all_emotions().items()},
        }
    }


@router.post("/synthesize")
async def synthesize(soul_id: str, neuroticism: Optional[float] = None):
    """Synthesize composite emotion from active base emotions."""
    data = get_or_create_engine(soul_id, neuroticism or data.get("neuroticism", 0.5))
    engine = data["engine"]
    result = engine.synthesize()
    return {
        "success": True,
        "data": {
            "name": result.name,
            "intensity": round(result.intensity, 4),
            "components": {k: round(v, 4) for k, v in result.components.items()},
            "is_novel": result.is_novel,
        }
    }


@router.post("/tick")
async def tick(soul_id: str, delta_seconds: float, neuroticism: Optional[float] = None):
    """Advance time for emotion decay."""
    data = get_or_create_engine(soul_id, neuroticism or data.get("neuroticism", 0.5))
    engine = data["engine"]
    engine.tick(delta_seconds=delta_seconds)
    return {
        "success": True,
        "data": {
            "emotions": {k: round(v, 4) for k, v in engine.get_all_emotions().items()},
        }
    }


@router.post("/clear")
async def clear_emotions(soul_id: str):
    """Clear all active emotions."""
    if soul_id not in _engine_instances:
        return {"success": True, "data": {"cleared": 0}}
    engine = _engine_instances[soul_id]["engine"]
    count = len(engine.get_all_emotions())
    engine.clear_emotions()
    return {"success": True, "data": {"cleared": count}}


@router.get("/triggered")
async def get_triggered(soul_id: str, threshold: float = 0.7):
    """Get list of emotions above threshold."""
    if soul_id not in _engine_instances:
        return {"success": True, "data": {"triggered": []}}
    engine = _engine_instances[soul_id]["engine"]
    triggered = engine.get_triggered_emotions(threshold)
    return {"success": True, "data": {"triggered": triggered}}


@router.get("/state")
async def get_state(soul_id: str):
    """Get full engine state for display."""
    if soul_id not in _engine_instances:
        return {"success": True, "data": None}
    engine = _engine_instances[soul_id]["engine"]
    state = engine.to_dict()
    return {"success": True, "data": state}
