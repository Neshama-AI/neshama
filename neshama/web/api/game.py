# Web API - Game API Router
"""
Game API - Endpoints for game integration.

Provides game-specific endpoints for:
- Pushing game events to NPCs
- Getting emotion states
- Getting behavior modifiers
- NPC chat with LLM + emotion context (with hosted/BYOK quota checks)
- NPC CRUD operations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Body, Request

from neshama.soul.emotion.game_event import GameEvent, GameEventType, GameEventEngine
from neshama.soul.npc_manager import get_npc_manager, NPCSoul
from neshama.soul.response_formatter import ResponseFormatter, FormatMode
from neshama.soul.emotion.sentiment_analyzer import SentimentAnalyzer

router = APIRouter()

# Module-level instances
_response_formatter = ResponseFormatter()


def _format_llm_response(raw_response: str) -> Dict[str, str]:
    """
    Format an LLM response by cleaning/converting stage directions.
    
    Args:
        raw_response: Raw LLM response text
        
    Returns:
        Dict with 'clean' and 'convert' formatted versions
    """
    return _response_formatter.format_all(raw_response)


def _get_manager():
    """Get the NPC manager instance."""
    return get_npc_manager()


# ── Event Endpoint ──────────────────────────────────────────────────────────

@router.post("/npc/{npc_id}/event")
async def push_game_event(
    npc_id: str,
    event_type: str,
    intensity: float = 1.0,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Push a game event to an NPC, triggering emotion calculation.
    
    This is the fast path endpoint - uses pure rule-based calculation,
    no LLM calls. Target response time: <50ms.
    
    Args:
        npc_id: UUID of the NPC
        event_type: One of the 15 game event types
        intensity: Event intensity (0-1)
        context: Optional event context
        
    Returns:
        EmotionFastPath result with emotion state and response hints
    """
    manager = _get_manager()
    
    # Validate NPC exists
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    # Parse event type
    try:
        event_enum = GameEventType(event_type)
    except ValueError:
        valid_types = [e.value for e in GameEventType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Valid types: {valid_types}"
        )
    
    # Validate intensity
    if not 0 <= intensity <= 1:
        raise HTTPException(status_code=400, detail="intensity must be between 0 and 1")
    
    # Create event
    event = GameEvent(
        event_type=event_enum,
        intensity=intensity,
        context=context,
    )
    
    # Process event
    result = manager.process_event(npc_id, event)
    
    return {
        "success": True,
        "data": result,
    }


@router.get("/npc/{npc_id}/event/info")
async def get_event_info(event_type: str):
    """Get information about what emotions a given event type affects."""
    try:
        event_enum = GameEventType(event_type)
    except ValueError:
        valid_types = [e.value for e in GameEventType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Valid types: {valid_types}"
        )
    
    engine = GameEventEngine()
    info = engine.get_event_info(event_enum)
    
    return {
        "success": True,
        "data": info,
    }


@router.get("/events")
async def list_all_events():
    """List all supported game event types."""
    engine = GameEventEngine()
    events = engine.list_all_events()
    
    return {
        "success": True,
        "data": {
            "events": events,
            "count": len(events),
        }
    }


@router.get("/events/{event_type}")
async def get_event_info_by_type(event_type: str):
    """Get information about what emotions a given event type affects."""
    try:
        event_enum = GameEventType(event_type)
    except ValueError:
        valid_types = [e.value for e in GameEventType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Valid types: {valid_types}"
        )
    
    engine = GameEventEngine()
    info = engine.get_event_info(event_enum)
    
    return {
        "success": True,
        "data": info,
    }


# ── Emotion State Endpoints ───────────────────────────────────────────────────

@router.get("/npc/{npc_id}/emotion")
async def get_emotion_state(npc_id: str):
    """
    Get the current emotion state of an NPC.
    
    Returns the current emotion vector and composite emotion.
    """
    manager = _get_manager()
    
    soul = manager.get_npc(npc_id)
    if not soul:
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    state = manager.get_emotion_state(npc_id)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "emotion_state": state["emotion_state"],
            "composite_emotion": state["composite_emotion"],
            "composite_intensity": state["composite_intensity"],
            "dominant_emotion": _get_dominant(state["emotion_state"]),
        },
    }


@router.post("/npc/{npc_id}/emotion/clear")
async def clear_emotions(npc_id: str):
    """Clear all emotions for an NPC."""
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    manager.clear_emotions(npc_id)
    
    return {
        "success": True,
        "data": {"npc_id": npc_id, "cleared": True},
    }


@router.post("/npc/{npc_id}/emotion/tick")
async def tick_emotions(npc_id: str, delta_seconds: float):
    """Apply time-based emotion decay."""
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    if delta_seconds < 0:
        raise HTTPException(status_code=400, detail="delta_seconds must be non-negative")
    
    manager.tick(npc_id, delta_seconds)
    
    state = manager.get_emotion_state(npc_id)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "delta_seconds": delta_seconds,
            "emotion_state": state["emotion_state"],
        },
    }


def _get_dominant(emotions: Dict[str, float]) -> Optional[str]:
    """Get the dominant emotion from state."""
    if not emotions:
        return None
    return max(emotions.items(), key=lambda x: x[1])[0]


# ── Behavior Endpoints ────────────────────────────────────────────────────────

@router.get("/npc/{npc_id}/behavior")
async def get_behavior(npc_id: str):
    """
    Get the current behavior profile for an NPC.
    
    Returns Unity-friendly behavior modifiers including:
    - Dialogue style
    - Movement pattern
    - Quest availability
    - Shop price modifier
    - Faction point modifier
    """
    manager = _get_manager()
    
    soul = manager.get_npc(npc_id)
    if not soul:
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    behavior = manager.get_behavior(npc_id)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            **behavior,
        },
    }


# ── NPC CRUD Endpoints ────────────────────────────────────────────────────────

@router.post("/npc")
async def create_npc(
    name: str,
    personality: Optional[Dict[str, float]] = None,
    preset: Optional[str] = None,
    npc_id: Optional[str] = None,
):
    """
    Create a new NPC soul.
    
    Args:
        name: Display name for the NPC
        personality: OCEAN scores (openness, conscientiousness, extraversion, agreeableness, neuroticism)
        preset: Use a preset configuration (tavern_keeper, guard_captain)
        npc_id: Optional custom ID (defaults to UUID)
    """
    manager = _get_manager()
    
    try:
        soul = manager.create_npc(
            name=name,
            personality=personality,
            preset=preset,
            npc_id=npc_id,
        )
        return {
            "success": True,
            "data": soul.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/npc/{npc_id}/profile")
async def get_profile(npc_id: str):
    """Get full NPC profile including personality and current state."""
    manager = _get_manager()
    
    try:
        profile = manager.get_profile(npc_id)
        return {
            "success": True,
            "data": profile,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/npc")
async def list_npcs():
    """List all NPCs."""
    manager = _get_manager()
    npcs = manager.list_npcs()
    
    return {
        "success": True,
        "data": {
            "npcs": [npc.to_dict() for npc in npcs],
            "count": len(npcs),
        }
    }


@router.delete("/npc/{npc_id}")
async def delete_npc(npc_id: str):
    """Delete an NPC."""
    manager = _get_manager()
    
    deleted = manager.delete_npc(npc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    return {
        "success": True,
        "data": {"npc_id": npc_id, "deleted": True},
    }


# ── Memory & Relations Endpoints ──────────────────────────────────────────────

@router.get("/npc/{npc_id}/memory")
async def get_memory(npc_id: str, entity_id: Optional[str] = None):
    """
    Get NPC's memory about a specific entity or all memories.
    
    Args:
        npc_id: NPC UUID
        entity_id: Optional specific entity to query
    """
    manager = _get_manager()
    
    soul = manager.get_npc(npc_id)
    if not soul:
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    # For now, return entity graph relations
    relations = manager.get_relations(npc_id)
    
    if entity_id:
        relations = [r for r in relations if r["from"] == entity_id or r["to"] == entity_id]
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "entity_id": entity_id,
            "relations": relations,
            "memory_ids": soul.memory_ids,
        },
    }


@router.post("/npc/{npc_id}/remember")
async def remember(
    npc_id: str,
    entity_id: str,
    relation_type: str,
    weight: float = 0.5,
):
    """
    Make an NPC remember an entity/relationship.
    
    Args:
        npc_id: NPC UUID
        entity_id: ID of the entity to remember
        relation_type: Type of relationship
        weight: Relationship strength (0-1)
    """
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    if not 0 <= weight <= 1:
        raise HTTPException(status_code=400, detail="weight must be between 0 and 1")
    
    manager.add_relation(npc_id, entity_id, relation_type, weight)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "entity_id": entity_id,
            "relation_type": relation_type,
            "weight": weight,
        },
    }


@router.get("/npc/{npc_id}/relations")
async def get_relations(npc_id: str):
    """Get all relations for an NPC."""
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    relations = manager.get_relations(npc_id)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "relations": relations,
            "count": len(relations),
        },
    }


# ── Preset Endpoints ──────────────────────────────────────────────────────────

@router.get("/presets")
async def list_presets():
    """List available NPC presets."""
    manager = _get_manager()
    presets = manager.list_presets()
    
    return {
        "success": True,
        "data": {
            "presets": presets,
            "count": len(presets),
        }
    }


@router.get("/presets/{preset_name}")
async def get_preset(preset_name: str):
    """Get information about a preset."""
    manager = _get_manager()
    
    try:
        info = manager.get_preset_info(preset_name)
        return {
            "success": True,
            "data": info,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Chat Endpoint (with emotion context) ─────────────────────────────────────

@router.post("/npc/{npc_id}/chat")
async def chat_with_npc(
    npc_id: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    request: Request = None,
):
    """
    Chat with an NPC using LLM with emotion context injected.
    
    This endpoint uses the LLM path but injects:
    - Current emotion state
    - Personality profile
    - Entity graph context
    - Behavior modifiers
    
    Dual-track LLM billing:
    - BYOK users: Use their own API Key, no quota check
    - Hosted users: Use our LLM provider, quota check applies
    
    When hosted quota is exceeded:
    - Returns quota_exceeded error with suggestions
    - Falls back to rule-engine response (no LLM call) rather than hard error
    
    Response includes formatted_response with cleaned/converted stage directions
    and sentiment analysis of the player's input.
    """
    manager = _get_manager()
    
    soul = manager.get_npc(npc_id)
    if not soul:
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    # ── Determine LLM mode (hosted vs BYOK) ──────────────────────────────
    session_id = None
    tier_name = "free"
    llm_mode = "hosted"
    byok_user = False
    
    if request:
        session_id = request.headers.get("X-Session-ID") or request.query_params.get("session_id")
        tier_name = request.headers.get("X-Subscription-Tier", "free")
    
    if session_id:
        from neshama.billing.usage import is_byok as check_is_byok, check_conversation_quota, get_usage_tracker, ResourceType
        from neshama.billing.plans import get_hosted_conversations_limit
        
        byok_user = check_is_byok(session_id)
        
        # Check conversation quota
        quota_result = check_conversation_quota(session_id, tier_name, byok_user)
        
        if not quota_result["allowed"]:
            # Quota exceeded for hosted mode
            # Instead of hard error, fall back to rule-engine response
            emotion_state = manager.get_emotion_state(npc_id)
            behavior = manager.get_behavior(npc_id)
            sentiment_analyzer = SentimentAnalyzer()
            sentiment_result = sentiment_analyzer.analyze(message)
            
            return {
                "success": True,
                "data": {
                    "npc_id": npc_id,
                    "npc_name": soul.name,
                    "message_received": message,
                    "formatted_response": {
                        "clean": None,
                        "convert": None,
                        "note": "Rule-engine fallback (hosted quota exceeded)",
                    },
                    "emotion_context": emotion_state,
                    "behavior_context": behavior,
                    "sentiment": sentiment_result.to_dict(),
                    "llm_mode": "fallback_rule_engine",
                    "quota": {
                        "mode": "hosted",
                        "remaining": 0,
                        "limit": quota_result["limit"],
                        "error": "quota_exceeded",
                        "suggestions": quota_result["suggestions"],
                    },
                },
            }
        
        # Track hosted conversation usage (only for non-BYOK)
        if not byok_user:
            get_usage_tracker().track_usage(
                session_id, ResourceType.HOSTED_CONVERSATION, 1,
                metadata={"npc_id": npc_id}
            )
        
        llm_mode = "byok" if byok_user else "hosted"
    
    # Get emotion context
    emotion_state = manager.get_emotion_state(npc_id)
    behavior = manager.get_behavior(npc_id)
    relations = manager.get_relations(npc_id)
    
    # Build context for LLM
    system_context = {
        "npc_name": soul.name,
        "personality": soul.personality.to_dict(),
        "emotion_state": emotion_state,
        "behavior": behavior,
        "relations": relations,
        "dialogue_style": behavior.get("dialogue_style", "neutral"),
    }
    
    # Analyze player input sentiment
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_result = sentiment_analyzer.analyze(message)
    
    # Return context for actual LLM call
    # In production, this would call an LLM with the context
    # The formatted_response field will be populated when LLM response is available
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "npc_name": soul.name,
            "message_received": message,
            "emotion_context": emotion_state,
            "behavior_context": behavior,
            "system_context": system_context,
            "formatted_response": {
                "clean": None,
                "convert": None,
                "note": "Will be populated when LLM response is available",
            },
            "sentiment": sentiment_result.to_dict(),
            "llm_mode": llm_mode,
            "note": "LLM integration pending - use system_context for prompt injection",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MVP-1: Session Management Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

from .session import get_session_manager


@router.post("/session")
async def create_session(
    game_id: str,
    client_id: str,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Create a new game session.
    
    Args:
        game_id: Game identifier
        client_id: Client identifier
        metadata: Optional session metadata
        
    Returns:
        Session information with session_id
    """
    session_manager = get_session_manager()
    session = session_manager.create_session(game_id, client_id, metadata)
    
    return {
        "success": True,
        "data": session.to_dict(),
    }


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get session information.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Session details
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return {
        "success": True,
        "data": session.to_dict(),
    }


@router.post("/session/{session_id}/heartbeat")
async def session_heartbeat(session_id: str):
    """
    Update session heartbeat.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Success status
    """
    session_manager = get_session_manager()
    updated = session_manager.heartbeat(session_id)
    
    if not updated:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return {
        "success": True,
        "data": {"session_id": session_id, "heartbeat_updated": True},
    }


@router.post("/session/{session_id}/npc/{npc_id}/register")
async def register_npc_to_session(
    session_id: str,
    npc_id: str,
):
    """
    Register an NPC to a session.
    
    Args:
        session_id: Session UUID
        npc_id: NPC UUID
        
    Returns:
        Registration confirmation
    """
    session_manager = get_session_manager()
    registration = session_manager.register_npc(npc_id, session_id)
    
    if not registration:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return {
        "success": True,
        "data": registration.to_dict(),
    }


@router.get("/session/{session_id}/npcs")
async def get_session_npcs(session_id: str):
    """
    Get all NPCs registered to a session.
    
    Args:
        session_id: Session UUID
        
    Returns:
        List of NPC IDs
    """
    session_manager = get_session_manager()
    npcs = session_manager.get_session_npcs(session_id)
    
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "npcs": npcs,
            "count": len(npcs),
        },
    }


@router.delete("/session/{session_id}/npc/{npc_id}")
async def unregister_npc_from_session(session_id: str, npc_id: str):
    """
    Unregister an NPC from a session.
    
    Args:
        session_id: Session UUID
        npc_id: NPC UUID
        
    Returns:
        Unregistration confirmation
    """
    session_manager = get_session_manager()
    unregistered = session_manager.unregister_npc(npc_id)
    
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "npc_id": npc_id,
            "unregistered": unregistered,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MVP-1: Emotion Trajectory Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

from neshama.soul.emotion.driver_service import get_driver_service


@router.get("/npc/{npc_id}/trajectory")
async def get_emotion_trajectory(
    npc_id: str,
    duration: float = 60.0,
    steps: int = 10,
):
    """
    Get predicted emotion trajectory for an NPC.
    
    Args:
        npc_id: NPC UUID
        duration: Duration to predict (seconds)
        steps: Number of trajectory points
        
    Returns:
        Trajectory data with emotion predictions over time
    """
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    driver_service = get_driver_service()
    
    # Register NPC if not already
    soul = manager.get_npc(npc_id)
    if soul:
        driver_service.register_npc(
            npc_id,
            personality_neuroticism=soul.personality.neuroticism,
            initial_emotions=soul.current_emotions,
        )
    
    trajectory = driver_service.get_trajectory(npc_id, duration, steps)
    
    if trajectory is None:
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not in driver service")
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "duration_seconds": duration,
            "steps": steps,
            "trajectory": trajectory,
        },
    }


@router.get("/npc/{npc_id}/triggers")
async def get_active_triggers(
    npc_id: str,
    min_threshold: float = 0.5,
):
    """
    Get active behavior triggers for an NPC.
    
    Args:
        npc_id: NPC UUID
        min_threshold: Minimum emotion value to consider active
        
    Returns:
        List of active triggers
    """
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    driver_service = get_driver_service()
    triggers = driver_service.get_active_triggers(npc_id, min_threshold)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "min_threshold": min_threshold,
            "triggers": triggers,
            "count": len(triggers),
        },
    }


@router.post("/npc/{npc_id}/emotion/set")
async def set_emotion_value(
    npc_id: str,
    emotion: str,
    value: float,
    baseline: Optional[float] = None,
):
    """
    Set a specific emotion value for an NPC.
    
    Args:
        npc_id: NPC UUID
        emotion: Emotion name
        value: Target value (0-1)
        baseline: Optional baseline (defaults to value)
        
    Returns:
        Updated emotion state
    """
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    if not 0 <= value <= 1:
        raise HTTPException(status_code=400, detail="value must be between 0 and 1")
    
    driver_service = get_driver_service()
    driver = driver_service.register_npc(npc_id)
    driver.set_emotion(emotion, value, baseline)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "emotion": emotion,
            "value": value,
            "baseline": baseline,
            "current_state": driver.get_all_emotions(),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MVP-1: Rate Limiting Integration
# ═══════════════════════════════════════════════════════════════════════════════

from .rate_limiter import get_rate_limiter, NPCTier


@router.get("/npc/{npc_id}/rate-limit")
async def get_rate_limit_info(
    npc_id: str,
    endpoint: str = "default",
):
    """
    Get rate limit information for an NPC.
    
    Args:
        npc_id: NPC UUID
        endpoint: Endpoint type (event, chat, default)
        
    Returns:
        Rate limit status and remaining requests
    """
    rate_limiter = get_rate_limiter()
    info = rate_limiter.get_info(npc_id, endpoint)
    
    return {
        "success": True,
        "data": info.to_dict(),
    }


@router.post("/npc/{npc_id}/rate-limit/tier")
async def set_npc_tier(
    npc_id: str,
    tier: str,
):
    """
    Set the rate limit tier for an NPC.
    
    Args:
        npc_id: NPC UUID
        tier: Tier name (free, basic, premium, enterprise)
        
    Returns:
        Updated tier confirmation
    """
    try:
        tier_enum = NPCTier(tier.lower())
    except ValueError:
        valid_tiers = [t.value for t in NPCTier]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier. Valid tiers: {valid_tiers}"
        )
    
    rate_limiter = get_rate_limiter()
    rate_limiter.set_tier(npc_id, tier_enum)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "tier": tier_enum.value,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MVP-1: NPC Memory Bridge Integration
# ═══════════════════════════════════════════════════════════════════════════════

from neshama.soul.npc_memory_bridge import get_memory_bridge, EntityType


@router.post("/npc/{npc_id}/memory/event")
async def process_memory_event(
    npc_id: str,
    event_type: str,
    entity_id: str,
    entity_name: str,
    intensity: float = 1.0,
    context: Optional[Dict[str, Any]] = None,
    entity_type: str = "person",
):
    """
    Process a game event and update NPC memory.
    
    This endpoint integrates with the NPCMemoryBridge to:
    - Update entity graph relationships
    - Store memory entries
    - Trigger emotion changes
    
    Args:
        npc_id: NPC UUID
        event_type: Game event type
        entity_id: Target entity ID
        entity_name: Target entity name
        intensity: Event intensity (0-1)
        context: Optional event context
        entity_type: Type of entity (person, place, object, etc.)
        
    Returns:
        Memory and relation update results
    """
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    # Parse event type
    try:
        event_enum = GameEventType(event_type)
    except ValueError:
        valid_types = [e.value for e in GameEventType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Valid types: {valid_types}"
        )
    
    # Parse entity type
    try:
        ent_type = EntityType(entity_type)
    except ValueError:
        ent_type = EntityType.CUSTOM
    
    # Create event
    event = GameEvent(
        event_type=event_enum,
        intensity=intensity,
        context=context,
    )
    
    # Process with memory bridge
    bridge = get_memory_bridge()
    bridge.on_game_event(
        npc_id=npc_id,
        event=event,
        entity_id=entity_id,
        entity_name=entity_name,
        entity_type=ent_type,
    )
    
    # Also process with NPC manager for emotion updates
    result = manager.process_event(npc_id, event)
    
    # Get updated relation
    relation = bridge.get_relation(npc_id, entity_id)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "entity_id": entity_id,
            "event_type": event_type,
            "relation": relation.to_dict() if relation else None,
            "emotion_result": result,
        },
    }


@router.get("/npc/{npc_id}/memory/context/{player_id}")
async def get_dialogue_context(
    npc_id: str,
    player_id: str,
    player_name: Optional[str] = None,
):
    """
    Get dialogue context for NPC-player interaction.
    
    Returns memory and relationship context for LLM prompt injection.
    
    Args:
        npc_id: NPC UUID
        player_id: Player UUID
        player_name: Optional player display name
        
    Returns:
        Dialogue context with relation and recent memories
    """
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    bridge = get_memory_bridge()
    
    # Get emotional state if available
    emotional_state = {}
    try:
        driver_service = get_driver_service()
        emotional_state = driver_service.get_all_emotions(npc_id) or {}
    except Exception:
        pass
    
    context = bridge.get_dialogue_context(
        npc_id=npc_id,
        player_id=player_id,
        player_name=player_name,
        emotional_state=emotional_state,
        max_memories=5,
    )
    
    if not context:
        return {
            "success": True,
            "data": {
                "npc_id": npc_id,
                "player_id": player_id,
                "has_context": False,
                "note": "No existing relation with this entity",
            },
        }
    
    return {
        "success": True,
        "data": {
            **context.to_dict(),
            "has_context": True,
        },
    }


@router.get("/npc/{npc_id}/relations/{entity_id}")
async def get_entity_relation(
    npc_id: str,
    entity_id: str,
):
    """
    Get NPC's relation with a specific entity.
    
    Args:
        npc_id: NPC UUID
        entity_id: Target entity UUID
        
    Returns:
        Relation details
    """
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    bridge = get_memory_bridge()
    relation = bridge.get_relation(npc_id, entity_id)
    
    if not relation:
        raise HTTPException(status_code=404, detail=f"No relation found for entity {entity_id}")
    
    return {
        "success": True,
        "data": relation.to_dict(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MVP-1: Service Stats Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/stats")
async def get_service_stats():
    """
    Get service statistics.
    
    Returns:
        Stats for all MVP-1 services
    """
    session_manager = get_session_manager()
    driver_service = get_driver_service()
    rate_limiter = get_rate_limiter()
    
    return {
        "success": True,
        "data": {
            "sessions": session_manager.get_stats(),
            "emotion_drivers": driver_service.get_stats(),
            "rate_limiter": rate_limiter.get_stats(),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MVP-2: NPC2NPC Social System Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

from neshama.soul.social_engine import (
    get_social_engine, SocialInteractionType, NPCRelation,
)
from neshama.soul.information_propagator import (
    get_propagator, InformationType,
)
from neshama.soul.npc_dialogue import (
    get_dialogue_engine, DialogueTrigger,
)


def _get_social_engine():
    """Get social engine instance."""
    return get_social_engine()


def _get_propagator():
    """Get information propagator instance."""
    return get_propagator()


def _get_dialogue_engine():
    """Get dialogue engine instance."""
    return get_dialogue_engine()


# ── NPC Interaction Endpoints ────────────────────────────────────────────────────


@router.post("/npc/{npc_a_id}/interact/{npc_b_id}")
async def trigger_npc_interaction(
    npc_a_id: str,
    npc_b_id: str,
    interaction_type: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
):
    """
    Trigger an interaction between two NPCs.
    
    This endpoint initiates a social interaction, optionally generating
    a dialogue. The interaction type can be specified or auto-determined.
    
    Args:
        npc_a_id: Initiator NPC ID
        npc_b_id: Target NPC ID
        interaction_type: Optional specific type (gossip/trade/argue/ally/etc)
        context: Additional context for the interaction
        session_id: Session for WebSocket broadcast
        
    Returns:
        Interaction result with relationship changes
    """
    engine = _get_social_engine()
    
    # Validate NPCs exist
    manager = _get_manager()
    if not manager.get_npc(npc_a_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_a_id} not found")
    if not manager.get_npc(npc_b_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_b_id} not found")
    
    # Parse interaction type
    forced_type = None
    if interaction_type:
        try:
            forced_type = SocialInteractionType(interaction_type)
        except ValueError:
            valid = [t.value for t in SocialInteractionType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interaction_type. Valid: {valid}"
            )
    
    # Initiate interaction
    event = engine.initiate_interaction(
        npc_a_id=npc_a_id,
        npc_b_id=npc_b_id,
        context=context,
        forced_type=forced_type,
    )
    
    # Broadcast via WebSocket if session provided
    if session_id:
        from .ws import broadcast_npc_interaction
        try:
            await broadcast_npc_interaction(
                session_id=session_id,
                npc_a_id=npc_a_id,
                npc_b_id=npc_b_id,
                interaction_type=event.interaction_type.value,
                context=event.context,
            )
        except Exception:
            pass  # Don't fail if WS broadcast fails
    
    # Get updated relationship
    relation = engine.get_relation(npc_a_id, npc_b_id)
    
    return {
        "success": True,
        "data": {
            "event": event.to_dict(),
            "relationship": relation.to_dict() if relation else None,
            "suggested_dialogue": event.success,
        },
    }


@router.get("/npc/{npc_id}/social-graph")
async def get_npc_social_graph(npc_id: str):
    """
    Get social network for an NPC.
    
    Returns lists of friends, enemies, neutrals, and strangers.
    
    Args:
        npc_id: NPC ID to query
        
    Returns:
        Social graph with categorized relationships
    """
    engine = _get_social_engine()
    
    graph = engine.get_social_graph(npc_id)
    
    return {
        "success": True,
        "data": graph,
    }


@router.get("/npc/{npc_id}/relations/{other_id}/mutual")
async def get_mutual_relation(npc_id: str, other_id: str):
    """
    Get complete relationship info between two NPCs.
    
    Args:
        npc_id: First NPC ID
        other_id: Second NPC ID
        
    Returns:
        Full relationship details and interaction suggestions
    """
    engine = _get_social_engine()
    manager = _get_manager()
    
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    if not manager.get_npc(other_id):
        raise HTTPException(status_code=404, detail=f"NPC {other_id} not found")
    
    mutual = engine.get_mutual_relations(npc_id, other_id)
    
    return {
        "success": True,
        "data": mutual,
    }


# ── Information Propagation Endpoints ───────────────────────────────────────────


@router.get("/npc/{npc_id}/knowledge")
async def get_npc_knowledge(
    npc_id: str,
    info_type: Optional[str] = None,
    min_importance: float = 0.0,
):
    """
    Get all information known by an NPC.
    
    Args:
        npc_id: NPC ID to query
        info_type: Optional filter by info type
        min_importance: Minimum importance threshold
        
    Returns:
        NPC's knowledge base
    """
    manager = _get_manager()
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    propagator = _get_propagator()
    knowledge = propagator.get_npc_knowledge(
        npc_id=npc_id,
        info_type=info_type,
        min_importance=min_importance,
    )
    
    return {
        "success": True,
        "data": knowledge.to_dict(),
    }


@router.post("/npc/{npc_id}/spread-info")
async def spread_information(
    npc_id: str,
    info_type: str = Body(...),
    content: str = Body(...),
    targets: List[str] = Body(...),
    importance: float = Body(0.5),
    tags: Optional[List[str]] = Body(None),
):
    """
    Have an NPC spread information to other NPCs.
    
    Args:
        npc_id: Source NPC ID
        info_type: Type of information
        content: Information content
        targets: List of NPC IDs to spread to
        importance: How important (0-1)
        tags: Optional tags
        
    Returns:
        Spread results
    """
    manager = _get_manager()
    if not manager.get_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")
    
    # Validate targets
    for target_id in targets:
        if not manager.get_npc(target_id):
            raise HTTPException(
                status_code=404,
                detail=f"Target NPC {target_id} not found"
            )
    
    # Validate info type
    try:
        InformationType(info_type)
    except ValueError:
        valid = [t.value for t in InformationType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid info_type. Valid: {valid}"
        )
    
    propagator = _get_propagator()
    result = propagator.spread_information(
        source_npc_id=npc_id,
        info_type=info_type,
        content=content,
        targets=targets,
        importance=importance,
        tags=tags,
    )
    
    return {
        "success": True,
        "data": result,
    }


@router.get("/information/{info_id}")
async def get_information_details(info_id: str):
    """
    Get details about spread information.
    
    Args:
        info_id: Information ID
        
    Returns:
        Info details and propagation chain
    """
    propagator = _get_propagator()
    details = propagator.get_info_details(info_id)
    
    if not details:
        raise HTTPException(status_code=404, detail=f"Info {info_id} not found")
    
    return {
        "success": True,
        "data": details,
    }


# ── NPC Dialogue Endpoints ───────────────────────────────────────────────────────


@router.post("/npc/{npc_a_id}/dialogue/{npc_b_id}")
async def generate_npc_dialogue(
    npc_a_id: str,
    npc_b_id: str,
    topic: str,
    trigger: str = "player_triggered",
    context: Optional[Dict[str, Any]] = None,
    max_turns: int = 4,
):
    """
    Generate a dialogue between two NPCs.
    
    This endpoint uses LLM to generate natural conversation.
    
    Args:
        npc_a_id: First NPC ID
        npc_b_id: Second NPC ID
        topic: Conversation topic/subject
        trigger: What triggered this (autonomous/player_triggered/world_event)
        context: Additional context
        max_turns: Maximum dialogue turns
        
    Returns:
        Generated dialogue with turns
    """
    manager = _get_manager()
    if not manager.get_npc(npc_a_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_a_id} not found")
    if not manager.get_npc(npc_b_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_b_id} not found")
    
    # Parse trigger
    try:
        trigger_enum = DialogueTrigger(trigger)
    except ValueError:
        trigger_enum = DialogueTrigger.PLAYER_TRIGGERED
    
    # Get engines
    social_engine = _get_social_engine()
    propagator = _get_propagator()
    dialogue_engine = _get_dialogue_engine()
    
    # Register NPCs with social engine if not already
    soul_a = manager.get_npc(npc_a_id)
    soul_b = manager.get_npc(npc_b_id)
    
    social_engine.register_npc(
        npc_id=npc_a_id,
        personality=soul_a.personality.to_dict(),
        emotions=soul_a.current_emotions,
    )
    social_engine.register_npc(
        npc_id=npc_b_id,
        personality=soul_b.personality.to_dict(),
        emotions=soul_b.current_emotions,
    )
    
    # Generate dialogue
    dialogue = dialogue_engine.generate_dialogue(
        npc_a_id=npc_a_id,
        npc_b_id=npc_b_id,
        topic=topic,
        context=context,
        trigger=trigger_enum,
        social_engine=social_engine,
        information_propagator=propagator,
        max_turns=max_turns,
    )
    
    return {
        "success": True,
        "data": dialogue.to_dict(),
    }


@router.post("/dialogue/{dialogue_id}/continue")
async def continue_npc_dialogue(
    dialogue_id: str,
    max_turns: int = 2,
):
    """
    Continue an existing dialogue.
    
    Args:
        dialogue_id: Dialogue to continue
        max_turns: Number of new turns
        
    Returns:
        Updated dialogue
    """
    dialogue_engine = _get_dialogue_engine()
    
    try:
        dialogue = dialogue_engine.continue_dialogue(
            dialogue_id=dialogue_id,
            max_turns=max_turns,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "success": True,
        "data": dialogue.to_dict(),
    }


@router.post("/dialogue/{dialogue_id}/summarize")
async def summarize_dialogue(dialogue_id: str):
    """
    Summarize a dialogue and store in NPC memory.
    
    Args:
        dialogue_id: Dialogue to summarize
        
    Returns:
        Summary text
    """
    dialogue_engine = _get_dialogue_engine()
    
    summary = dialogue_engine.summarize_dialogue(dialogue_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail=f"Dialogue {dialogue_id} not found")
    
    return {
        "success": True,
        "data": {
            "dialogue_id": dialogue_id,
            "summary": summary,
        },
    }


# ── Social Events Endpoints ──────────────────────────────────────────────────────


@router.get("/social/events")
async def get_social_events(
    npc_id: Optional[str] = None,
    limit: int = 20,
):
    """
    Get recent social events.
    
    Args:
        npc_id: Optional filter by NPC
        limit: Max events to return
        
    Returns:
        List of recent social events
    """
    engine = _get_social_engine()
    
    events = engine.get_recent_events(npc_id=npc_id, limit=limit)
    
    return {
        "success": True,
        "data": {
            "events": events,
            "count": len(events),
        },
    }


@router.post("/social/tick")
async def social_system_tick(
    session_id: Optional[str] = None,
):
    """
    Trigger autonomous social tick.
    
    This checks for NPCs that should initiate social interactions.
    Should be called periodically (e.g., every 10 seconds).
    
    Args:
        session_id: Optional session filter
        
    Returns:
        New events generated
    """
    engine = _get_social_engine()
    
    events = engine.social_tick(session_id=session_id)
    
    return {
        "success": True,
        "data": {
            "events": [e.to_dict() for e in events],
            "count": len(events),
        },
    }


@router.post("/information/decay")
async def decay_information(
    delta_seconds: float = 10.0,
):
    """
    Decay information importance over time.
    
    Args:
        delta_seconds: Time elapsed since last check
        
    Returns:
        Decay statistics
    """
    propagator = _get_propagator()
    
    result = propagator.decay_information(delta_seconds=delta_seconds)
    
    return {
        "success": True,
        "data": result,
    }


# ── Social System Stats ────────────────────────────────────────────────────────


@router.get("/social/stats")
async def get_social_stats():
    """
    Get social system statistics.
    
    Returns:
        Stats for social engine and propagator
    """
    engine = _get_social_engine()
    propagator = _get_propagator()
    
    return {
        "success": True,
        "data": {
            "relations_count": len(engine._relations),
            "social_events_count": len(engine._social_events),
            "information_count": len(propagator._information),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MVP-2: Story Trigger Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

from neshama.soul.story_trigger import (
    get_story_trigger_engine,
    StoryTrigger,
    TriggerCondition,
    TriggerConditionType,
    StoryEffect,
    StoryEffectType,
)


def _get_story_engine():
    """Get the story trigger engine instance."""
    return get_story_trigger_engine()


@router.get("/story/triggers")
async def list_story_triggers():
    """
    List all registered story triggers.
    
    Returns:
        List of all story triggers
    """
    engine = _get_story_engine()
    triggers = engine.list_triggers()
    
    return {
        "success": True,
        "data": {
            "triggers": [t.to_dict() for t in triggers],
            "count": len(triggers),
        },
    }


@router.post("/story/trigger")
async def register_story_trigger(
    trigger_id: str,
    name: str,
    description: str = "",
    cooldown: float = 60.0,
    priority: int = 0,
    one_shot: bool = False,
    conditions: List[Dict[str, Any]] = Body(default=[]),
    effects: List[Dict[str, Any]] = Body(default=[]),
):
    """
    Register a new story trigger.
    
    Args:
        trigger_id: Unique trigger ID
        name: Trigger name
        description: Trigger description
        cooldown: Cooldown in seconds
        priority: Priority (higher = checked first)
        one_shot: Fire only once
        conditions: List of trigger conditions
        effects: List of effects when triggered
        
    Returns:
        Registered trigger info
    """
    engine = _get_story_engine()
    
    # Parse conditions
    parsed_conditions = []
    for cond in conditions:
        cond_type = TriggerConditionType(cond.get("condition_type"))
        condition = TriggerCondition(
            condition_type=cond_type,
            npc_id=cond.get("npc_id"),
            emotion=cond.get("emotion"),
            threshold=cond.get("threshold"),
            direction=cond.get("direction"),
            change_magnitude=cond.get("change_magnitude"),
            emotions=cond.get("emotions"),
            relationship_type=cond.get("relationship_type"),
            relationship_target=cond.get("relationship_target"),
            duration_seconds=cond.get("duration_seconds"),
        )
        parsed_conditions.append(condition)
    
    # Parse effects
    parsed_effects = []
    for eff in effects:
        effect_type = StoryEffectType(eff.get("effect_type"))
        effect = StoryEffect(
            effect_type=effect_type,
            target=eff.get("target", ""),
            params=eff.get("params", {}),
        )
        parsed_effects.append(effect)
    
    trigger = StoryTrigger(
        trigger_id=trigger_id,
        name=name,
        description=description,
        conditions=parsed_conditions,
        effects=parsed_effects,
        cooldown=cooldown,
        priority=priority,
        one_shot=one_shot,
    )
    
    engine.register_trigger(trigger)
    
    return {
        "success": True,
        "data": trigger.to_dict(),
    }


@router.post("/story/trigger/{trigger_id}/activate")
async def activate_trigger(
    trigger_id: str,
    npc_emotions: Dict[str, Dict[str, float]],
    npc_relationships: Optional[Dict[str, Dict[str, str]]] = None,
):
    """
    Manually activate a trigger.
    
    Args:
        trigger_id: Trigger to activate
        npc_emotions: Current NPC emotions
        npc_relationships: Current NPC relationships
        
    Returns:
        Triggered events
    """
    engine = _get_story_engine()
    
    trigger = engine.get_trigger(trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail=f"Trigger {trigger_id} not found")
    
    events = engine.check_triggers(npc_emotions, npc_relationships)
    
    return {
        "success": True,
        "data": {
            "trigger_id": trigger_id,
            "triggered": len(events) > 0,
            "events": [e.to_dict() for e in events],
        },
    }


@router.get("/story/active")
async def get_active_story_events():
    """
    Get currently active story events.
    
    Returns:
        List of active triggered events
    """
    engine = _get_story_engine()
    events = engine.get_active_events()
    
    return {
        "success": True,
        "data": {
            "events": [e.to_dict() for e in events],
            "count": len(events),
        },
    }


@router.post("/story/check")
async def check_all_triggers(
    npc_emotions: Dict[str, Dict[str, float]],
    npc_relationships: Optional[Dict[str, Dict[str, str]]] = None,
):
    """
    Check all triggers against current state.
    
    Args:
        npc_emotions: Current NPC emotions
        npc_relationships: Current NPC relationships
        
    Returns:
        All triggered events
    """
    engine = _get_story_engine()
    events = engine.check_triggers(npc_emotions, npc_relationships)
    
    return {
        "success": True,
        "data": {
            "events": [e.to_dict() for e in events],
            "count": len(events),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MVP-2: Quest System Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

from neshama.soul.quest_system import (
    get_quest_system,
    QuestStatus,
)


def _get_quest_system():
    """Get the quest system instance."""
    return get_quest_system()


@router.get("/quest/templates")
async def list_quest_templates():
    """
    List all quest templates.
    
    Returns:
        List of quest templates
    """
    system = _get_quest_system()
    templates = system.list_templates()
    
    return {
        "success": True,
        "data": {
            "templates": [t.to_dict() for t in templates],
            "count": len(templates),
        },
    }


@router.get("/quest/available")
async def get_available_quests(npc_id: Optional[str] = None):
    """
    Get available (not yet accepted) quests.
    
    Args:
        npc_id: Optional filter by NPC
        
    Returns:
        List of available quests
    """
    system = _get_quest_system()
    quests = system.get_available_quests(npc_id)
    
    return {
        "success": True,
        "data": {
            "quests": [q.to_dict() for q in quests],
            "count": len(quests),
        },
    }


@router.get("/quest/active")
async def get_active_quests(npc_id: Optional[str] = None):
    """
    Get active (accepted) quests.
    
    Args:
        npc_id: Optional filter by NPC
        
    Returns:
        List of active quests
    """
    system = _get_quest_system()
    quests = system.get_active_quests(npc_id)
    
    return {
        "success": True,
        "data": {
            "quests": [q.to_dict() for q in quests],
            "count": len(quests),
        },
    }


@router.get("/quest/{quest_id}")
async def get_quest(quest_id: str):
    """
    Get quest details.
    
    Args:
        quest_id: Quest ID
        
    Returns:
        Quest details
    """
    system = _get_quest_system()
    quest = system.get_quest(quest_id)
    
    if not quest:
        raise HTTPException(status_code=404, detail=f"Quest {quest_id} not found")
    
    return {
        "success": True,
        "data": quest.to_dict(),
    }


@router.post("/quest/generate")
async def generate_quest(
    template_id: str,
    npc_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    Generate a quest from template.
    
    Args:
        template_id: Template to use
        npc_id: NPC giving the quest
        title: Optional custom title
        description: Optional custom description
        
    Returns:
        Generated quest
    """
    system = _get_quest_system()
    
    params = {}
    if title:
        params["title"] = title
    if description:
        params["description"] = description
    
    quest = system.generate_quest(template_id, npc_id, params)
    
    if not quest:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    return {
        "success": True,
        "data": quest.to_dict(),
    }


@router.post("/quest/{quest_id}/accept")
async def accept_quest(quest_id: str):
    """
    Accept a quest.
    
    Args:
        quest_id: Quest to accept
        
    Returns:
        Accepted quest
    """
    system = _get_quest_system()
    quest = system.accept_quest(quest_id)
    
    if not quest:
        raise HTTPException(status_code=404, detail=f"Quest {quest_id} not found or already accepted")
    
    return {
        "success": True,
        "data": quest.to_dict(),
    }


@router.post("/quest/{quest_id}/progress")
async def update_quest_progress(
    quest_id: str,
    event_type: str,
    event_target: str,
    additional_data: Optional[Dict[str, Any]] = None,
):
    """
    Update quest progress.
    
    Args:
        quest_id: Quest to update
        event_type: Type of event
        event_target: Event target
        additional_data: Additional event data
        
    Returns:
        Updated quest
    """
    system = _get_quest_system()
    
    event = {
        "type": event_type,
        "target": event_target,
    }
    if additional_data:
        event.update(additional_data)
    
    quest = system.update_quest_progress(quest_id, event)
    
    if not quest:
        raise HTTPException(status_code=404, detail=f"Quest {quest_id} not found or not active")
    
    return {
        "success": True,
        "data": quest.to_dict(),
    }


@router.post("/quest/{quest_id}/complete")
async def complete_quest(quest_id: str):
    """
    Mark a quest as completed.
    
    Args:
        quest_id: Quest to complete
        
    Returns:
        Completed quest
    """
    system = _get_quest_system()
    quest = system.complete_quest(quest_id)
    
    if not quest:
        raise HTTPException(status_code=404, detail=f"Quest {quest_id} not found or not active")
    
    return {
        "success": True,
        "data": quest.to_dict(),
    }


@router.post("/quest/{quest_id}/fail")
async def fail_quest(quest_id: str):
    """
    Mark a quest as failed.
    
    Args:
        quest_id: Quest to fail
        
    Returns:
        Failed quest
    """
    system = _get_quest_system()
    quest = system.fail_quest(quest_id)
    
    if not quest:
        raise HTTPException(status_code=404, detail=f"Quest {quest_id} not found or not active")
    
    return {
        "success": True,
        "data": quest.to_dict(),
    }


@router.post("/quest/check-triggers")
async def check_quest_triggers(
    npc_id: str,
    emotion_state: Optional[Dict[str, float]] = None,
):
    """
    Check if any quests should become available for an NPC.
    
    Args:
        npc_id: NPC ID
        emotion_state: Current emotion state
        
    Returns:
        Newly available quests
    """
    if emotion_state is None:
        emotion_state = {}
    system = _get_quest_system()
    templates = system.check_quest_triggers(npc_id, emotion_state)
    
    return {
        "success": True,
        "data": {
            "npc_id": npc_id,
            "available_templates": [t.to_dict() for t in templates],
            "count": len(templates),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MVP-2: World Event Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

from neshama.soul.world_events import (
    get_world_event_manager,
    WorldEventType,
    EventResolution,
)


def _get_world_manager():
    """Get the world event manager instance."""
    return get_world_event_manager()


@router.get("/world/events")
async def get_world_events(
    session_id: Optional[str] = None,
    event_type: Optional[str] = None,
):
    """
    Get active world events.
    
    Args:
        session_id: Optional session filter
        event_type: Optional event type filter
        
    Returns:
        List of active world events
    """
    manager = _get_world_manager()
    
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = WorldEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event_type. Valid types: {[e.value for e in WorldEventType]}"
            )
    
    events = manager.get_active_events(session_id, event_type_enum)
    
    return {
        "success": True,
        "data": {
            "events": [e.to_dict() for e in events],
            "count": len(events),
        },
    }


@router.get("/world/events/{event_id}")
async def get_world_event(event_id: str):
    """
    Get world event details.
    
    Args:
        event_id: Event ID
        
    Returns:
        Event details
    """
    manager = _get_world_manager()
    event = manager.get_event(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    
    return {
        "success": True,
        "data": event.to_dict(),
    }


@router.post("/world/events")
async def emit_world_event(
    event_type: str,
    source_npc_id: Optional[str] = None,
    title: str = "",
    description: str = "",
    params: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
):
    """
    Emit a world event.
    
    Args:
        event_type: Type of event
        source_npc_id: NPC that triggered the event
        title: Event title
        description: Event description
        params: Event parameters
        session_id: Session ID
        
    Returns:
        Created event
    """
    manager = _get_world_manager()
    
    try:
        event_type_enum = WorldEventType(event_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Valid types: {[e.value for e in WorldEventType]}"
        )
    
    event = manager.emit_world_event(
        event_type=event_type_enum,
        source_npc_id=source_npc_id,
        title=title,
        description=description,
        params=params,
        session_id=session_id,
    )
    
    return {
        "success": True,
        "data": event.to_dict(),
    }


@router.post("/world/events/{event_id}/resolve")
async def resolve_world_event(
    event_id: str,
    resolution: str,
    params: Optional[Dict[str, Any]] = None,
):
    """
    Resolve a world event.
    
    Args:
        event_id: Event to resolve
        resolution: Resolution type
        params: Resolution parameters
        
    Returns:
        Resolution confirmation
    """
    manager = _get_world_manager()
    
    resolved = manager.resolve_event(event_id, resolution, params)
    
    if not resolved:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    
    return {
        "success": True,
        "data": {
            "event_id": event_id,
            "resolved": True,
            "resolution": resolution,
        },
    }


@router.get("/world/events/{event_id}/history")
async def get_event_history(
    event_id: str,
    session_id: Optional[str] = None,
):
    """
    Get event history.
    
    Args:
        event_id: Event ID to get history for
        session_id: Optional session filter
        
    Returns:
        Event history
    """
    manager = _get_world_manager()
    event = manager.get_event(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    
    history = manager.get_event_history(session_id)
    
    return {
        "success": True,
        "data": {
            "event_id": event_id,
            "history": [e.to_dict() for e in history if e.event_id == event_id],
        },
    }
