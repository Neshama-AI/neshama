# Web API - WebSocket Support
"""
WebSocket Support for Real-time Updates

Provides WebSocket connections for:
- Emotion changes
- Behavior triggers
- Relation updates
- NPC-initiated chat

Uses FastAPI's native WebSocket support.
"""

from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
import logging
import uuid

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    EMOTION_CHANGED = "emotion_changed"
    BEHAVIOR_TRIGGERED = "behavior_triggered"
    RELATION_UPDATED = "relation_updated"
    NPC_CHAT = "npc_chat"
    SESSION_HEARTBEAT = "session_heartbeat"
    ERROR = "error"
    CONNECTED = "connected"
    PING = "ping"
    PONG = "pong"
    # Voice message types
    NPC_SPEECH = "npc_speech"          # NPC voice output
    PLAYER_SPEECH = "player_speech"    # Player voice input
    VOICE_READY = "voice_ready"        # Voice system ready
    VOICE_ERROR = "voice_error"        # Voice error occurred
    # Story/Quest/World Event message types
    STORY_TRIGGERED = "story_triggered"
    QUEST_AVAILABLE = "quest_available"
    QUEST_UPDATE = "quest_update"
    QUEST_COMPLETED = "quest_completed"
    QUEST_FAILED = "quest_failed"
    WORLD_EVENT = "world_event"
    WORLD_EVENT_RESOLVED = "world_event_resolved"
    # NPC2NPC Social System
    NPC_INTERACTION = "npc_interaction"       # Two NPCs start interacting
    NPC_DIALOGUE = "npc_dialogue"            # NPC dialogue content
    INFORMATION_SPREAD = "information_spread"  # Info spreading between NPCs
    RELATIONSHIP_CHANGED = "relationship_changed"  # NPC relationship changed


@dataclass
class WebSocketMessage:
    """A WebSocket message."""
    type: MessageType
    session_id: str
    npc_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "type": self.type.value,
            "session_id": self.session_id,
            "npc_id": self.npc_id,
            "data": self.data,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
        }, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, text: str) -> "WebSocketMessage":
        """Deserialize from JSON string."""
        obj = json.loads(text)
        return cls(
            type=MessageType(obj["type"]),
            session_id=obj["session_id"],
            npc_id=obj.get("npc_id"),
            data=obj.get("data"),
            timestamp=obj.get("timestamp", datetime.now().isoformat()),
            message_id=obj.get("message_id", str(uuid.uuid4())),
        )


class ConnectionManager:
    """
    Manages WebSocket connections.
    
    Handles:
    - Connection registration per session
    - NPC-specific subscriptions
    - Message broadcasting
    - Connection lifecycle
    
    Example:
        >>> manager = ConnectionManager()
        >>> 
        >>> # Accept connection
        >>> await manager.connect(websocket, session_id)
        >>> 
        >>> # Send message to session
        >>> await manager.send_to_session(
        ...     session_id,
        ...     MessageType.EMOTION_CHANGED,
        ...     npc_id="npc_001",
        ...     data={"joy": 0.8}
        ... )
        >>> 
        >>> # Disconnect
        >>> await manager.disconnect(websocket, session_id)
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        # Session connections: session_id -> {websocket_id -> WebSocket}
        self._session_connections: Dict[str, Dict[str, WebSocket]] = {}
        
        # NPC subscriptions: npc_id -> set of session_ids
        self._npc_subscriptions: Dict[str, Set[str]] = {}
        
        # Message callbacks: MessageType -> [callback]
        self._message_callbacks: Dict[MessageType, List[Callable]] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        npc_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Accept and register a WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket
            session_id: Session to connect to
            npc_ids: Optional list of NPC IDs to subscribe to
            
        Returns:
            WebSocket connection ID
        """
        await websocket.accept()
        
        websocket_id = str(uuid.uuid4())
        
        async with self._lock:
            # Initialize session connections dict
            if session_id not in self._session_connections:
                self._session_connections[session_id] = {}
            
            self._session_connections[session_id][websocket_id] = websocket
            
            # Subscribe to NPCs
            if npc_ids:
                for npc_id in npc_ids:
                    if npc_id not in self._npc_subscriptions:
                        self._npc_subscriptions[npc_id] = set()
                    self._npc_subscriptions[npc_id].add(session_id)
        
        # Send connected message
        await self.send_to_websocket(
            websocket,
            WebSocketMessage(
                type=MessageType.CONNECTED,
                session_id=session_id,
                data={
                    "websocket_id": websocket_id,
                    "session_id": session_id,
                    "subscribed_npcs": npc_ids or [],
                }
            )
        )
        
        logger.info(f"WebSocket {websocket_id} connected to session {session_id}")
        return websocket_id
    
    async def disconnect(
        self,
        websocket: WebSocket,
        session_id: str,
        websocket_id: Optional[str] = None,
    ):
        """
        Disconnect a WebSocket.
        
        Args:
            websocket: The WebSocket to disconnect
            session_id: Session ID
            websocket_id: Connection ID (auto-detected if not provided)
        """
        async with self._lock:
            if session_id in self._session_connections:
                if websocket_id:
                    self._session_connections[session_id].pop(websocket_id, None)
                else:
                    # Find and remove by websocket object
                    for wid, ws in list(self._session_connections[session_id].items()):
                        if ws == websocket:
                            self._session_connections[session_id].pop(wid, None)
                            websocket_id = wid
                            break
                
                # Clean up empty sessions
                if not self._session_connections.get(session_id):
                    self._session_connections.pop(session_id, None)
            
            # Remove from NPC subscriptions
            for npc_id, sessions in list(self._npc_subscriptions.items()):
                sessions.discard(session_id)
                if not sessions:
                    self._npc_subscriptions.pop(npc_id, None)
        
        logger.info(f"WebSocket {websocket_id} disconnected from session {session_id}")
    
    async def send_to_websocket(
        self,
        websocket: WebSocket,
        message: WebSocketMessage,
    ) -> bool:
        """
        Send a message to a specific WebSocket.
        
        Args:
            websocket: Target WebSocket
            message: Message to send
            
        Returns:
            True if sent, False if failed
        """
        try:
            await websocket.send_text(message.to_json())
            return True
        except Exception as e:
            logger.error(f"Failed to send to websocket: {e}")
            return False
    
    async def send_to_session(
        self,
        session_id: str,
        message_type: MessageType,
        npc_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Send a message to all connections in a session.
        
        Args:
            session_id: Target session
            message_type: Type of message
            npc_id: Optional NPC ID (filters by subscription if provided)
            data: Message data
            
        Returns:
            Number of clients message was sent to
        """
        message = WebSocketMessage(
            type=message_type,
            session_id=session_id,
            npc_id=npc_id,
            data=data,
        )
        
        sent_count = 0
        
        async with self._lock:
            connections = self._session_connections.get(session_id, {})
            connections_to_send = list(connections.items())
        
        for websocket_id, websocket in connections_to_send:
            try:
                await websocket.send_text(message.to_json())
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send to {websocket_id}: {e}")
        
        return sent_count
    
    async def broadcast_to_npc(
        self,
        npc_id: str,
        message_type: MessageType,
        data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Broadcast a message to all sessions subscribed to an NPC.
        
        Args:
            npc_id: Target NPC ID
            message_type: Type of message
            data: Message data
            
        Returns:
            Number of sessions message was sent to
        """
        async with self._lock:
            session_ids = list(self._npc_subscriptions.get(npc_id, set()))
        
        sent_count = 0
        for session_id in session_ids:
            count = await self.send_to_session(
                session_id,
                message_type,
                npc_id=npc_id,
                data=data,
            )
            sent_count += count
        
        return sent_count
    
    def subscribe_npc(self, npc_id: str, session_id: str):
        """Subscribe a session to an NPC's updates."""
        # This is called by session manager, actual subscription happens in connect
        pass
    
    async def handle_ping(self, websocket: WebSocket, session_id: str) -> bool:
        """Handle a ping message, respond with pong."""
        try:
            await websocket.send_text(json.dumps({
                "type": MessageType.PONG.value,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }))
            return True
        except Exception as e:
            logger.error(f"Failed to send pong: {e}")
            return False
    
    async def receive_message(
        self,
        websocket: WebSocket,
        session_id: str,
    ) -> Optional[WebSocketMessage]:
        """
        Receive and parse a message from WebSocket.
        
        Args:
            websocket: Source WebSocket
            session_id: Session ID
            
        Returns:
            Parsed WebSocketMessage or None
        """
        try:
            text = await websocket.receive_text()
            
            # Handle ping specially
            try:
                obj = json.loads(text)
                if obj.get("type") == MessageType.PING.value:
                    await self.handle_ping(websocket, session_id)
                    return None
            except:
                pass
            
            return WebSocketMessage.from_json(text)
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected in session {session_id}")
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    def get_session_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session."""
        # Note: This is a sync method, for stats only
        connections = self._session_connections.get(session_id, {})
        return len(connections)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics."""
        total_connections = sum(
            len(conns) for conns in self._session_connections.values()
        )
        return {
            "total_sessions": len(self._session_connections),
            "total_connections": total_connections,
            "subscribed_npcs": len(self._npc_subscriptions),
        }


# Global connection manager
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the global ConnectionManager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


# Helper function for broadcasting emotion changes
async def broadcast_emotion_change(
    npc_id: str,
    emotion_changes: Dict[str, float],
    current_state: Dict[str, float],
):
    """
    Broadcast an emotion change notification.
    
    Args:
        npc_id: NPC ID
        emotion_changes: Changed emotions (name -> delta)
        current_state: Current full emotion state
    """
    manager = get_connection_manager()
    await manager.broadcast_to_npc(
        npc_id=npc_id,
        message_type=MessageType.EMOTION_CHANGED,
        data={
            "changes": emotion_changes,
            "current_state": current_state,
        }
    )


# Helper function for broadcasting behavior triggers
async def broadcast_behavior_trigger(
    npc_id: str,
    trigger_data: Dict[str, Any],
):
    """
    Broadcast a behavior trigger notification.
    
    Args:
        npc_id: NPC ID
        trigger_data: Trigger information
    """
    manager = get_connection_manager()
    await manager.broadcast_to_npc(
        npc_id=npc_id,
        message_type=MessageType.BEHAVIOR_TRIGGERED,
        data=trigger_data,
    )


# Helper function for broadcasting relation updates
async def broadcast_relation_update(
    npc_id: str,
    entity_id: str,
    relation_data: Dict[str, Any],
):
    """
    Broadcast a relation update notification.
    
    Args:
        npc_id: NPC ID
        entity_id: Target entity ID
        relation_data: Updated relation information
    """
    manager = get_connection_manager()
    await manager.broadcast_to_npc(
        npc_id=npc_id,
        message_type=MessageType.RELATION_UPDATED,
        data={
            "entity_id": entity_id,
            "relation": relation_data,
        }
    )


# ── NPC2NPC Social System Helpers ────────────────────────────────────────────────


async def broadcast_npc_interaction(
    session_id: str,
    npc_a_id: str,
    npc_b_id: str,
    interaction_type: str,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Broadcast when two NPCs start an interaction.
    
    Game clients can use this to render NPC animations.
    
    Args:
        session_id: Session ID for broadcast
        npc_a_id: First NPC ID
        npc_b_id: Second NPC ID
        interaction_type: Type of interaction
        context: Additional context
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.NPC_INTERACTION,
        npc_id=npc_a_id,
        data={
            "npc_a_id": npc_a_id,
            "npc_b_id": npc_b_id,
            "interaction_type": interaction_type,
            "context": context or {},
        }
    )


async def broadcast_npc_dialogue(
    session_id: str,
    dialogue_id: str,
    turn: Dict[str, Any],
    is_complete: bool = False,
):
    """
    Broadcast NPC dialogue content.
    
    Clients can display speech bubbles.
    
    Args:
        session_id: Session ID for broadcast
        dialogue_id: Dialogue ID
        turn: Turn data (speaker, content, etc.)
        is_complete: Whether dialogue is finished
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.NPC_DIALOGUE,
        data={
            "dialogue_id": dialogue_id,
            "turn": turn,
            "is_complete": is_complete,
        }
    )


async def broadcast_information_spread(
    session_id: str,
    info_type: str,
    from_npc_id: str,
    to_npc_id: str,
    content: str,
    credibility: float,
):
    """
    Broadcast when information spreads between NPCs.
    
    Args:
        session_id: Session ID for broadcast
        info_type: Type of information
        from_npc_id: Source NPC
        to_npc_id: Target NPC
        content: Information content
        credibility: Credibility score
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.INFORMATION_SPREAD,
        data={
            "info_type": info_type,
            "from_npc_id": from_npc_id,
            "to_npc_id": to_npc_id,
            "content": content,
            "credibility": credibility,
        }
    )


async def broadcast_relationship_changed(
    session_id: str,
    npc_a_id: str,
    npc_b_id: str,
    old_relation: Dict[str, Any],
    new_relation: Dict[str, Any],
    change_reason: str,
):
    """
    Broadcast when NPC relationship changes.
    
    Args:
        session_id: Session ID for broadcast
        npc_a_id: First NPC ID
        npc_b_id: Second NPC ID
        old_relation: Previous relationship state
        new_relation: New relationship state
        change_reason: What caused the change
    """
    manager = get_connection_manager()
    # Broadcast to both NPCs' subscribers
    for npc_id in [npc_a_id, npc_b_id]:
        await manager.broadcast_to_npc(
            npc_id=npc_id,
            message_type=MessageType.RELATIONSHIP_CHANGED,
            data={
                "npc_a_id": npc_a_id,
                "npc_b_id": npc_b_id,
                "old_relation": old_relation,
                "new_relation": new_relation,
                "change_reason": change_reason,
            }
        )


# ── Story/Quest/World Event Helpers ────────────────────────────────────────────


async def broadcast_story_triggered(
    session_id: str,
    trigger_data: Dict[str, Any],
):
    """
    Broadcast a story trigger notification.
    
    Args:
        session_id: Session ID for broadcast
        trigger_data: Trigger information including effects
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.STORY_TRIGGERED,
        data=trigger_data,
    )


async def broadcast_quest_available(
    session_id: str,
    quest_data: Dict[str, Any],
):
    """
    Broadcast a new quest availability notification.
    
    Args:
        session_id: Session ID for broadcast
        quest_data: Quest information
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.QUEST_AVAILABLE,
        data=quest_data,
    )


async def broadcast_quest_update(
    session_id: str,
    quest_id: str,
    progress: Dict[str, Any],
    status: str,
):
    """
    Broadcast a quest progress update.
    
    Args:
        session_id: Session ID for broadcast
        quest_id: Quest ID
        progress: Current progress
        status: Quest status
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.QUEST_UPDATE,
        data={
            "quest_id": quest_id,
            "progress": progress,
            "status": status,
        },
    )


async def broadcast_quest_completed(
    session_id: str,
    quest_id: str,
    rewards: List[Dict[str, Any]],
    emotional_effects: List[Dict[str, Any]],
):
    """
    Broadcast a quest completion notification.
    
    Args:
        session_id: Session ID for broadcast
        quest_id: Completed quest ID
        rewards: Quest rewards
        emotional_effects: Effects on NPC emotions
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.QUEST_COMPLETED,
        data={
            "quest_id": quest_id,
            "rewards": rewards,
            "emotional_effects": emotional_effects,
        },
    )


async def broadcast_quest_failed(
    session_id: str,
    quest_id: str,
    emotional_effects: List[Dict[str, Any]],
):
    """
    Broadcast a quest failure notification.
    
    Args:
        session_id: Session ID for broadcast
        quest_id: Failed quest ID
        emotional_effects: Effects on NPC emotions
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.QUEST_FAILED,
        data={
            "quest_id": quest_id,
            "emotional_effects": emotional_effects,
        },
    )


async def broadcast_world_event(
    session_id: str,
    event_data: Dict[str, Any],
):
    """
    Broadcast a world event notification.
    
    Args:
        session_id: Session ID for broadcast
        event_data: World event information
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.WORLD_EVENT,
        data=event_data,
    )


async def broadcast_world_event_resolved(
    session_id: str,
    event_id: str,
    resolution: str,
    resolution_params: Dict[str, Any],
):
    """
    Broadcast a world event resolution notification.
    
    Args:
        session_id: Session ID for broadcast
        event_id: Resolved event ID
        resolution: Resolution type
        resolution_params: Resolution parameters
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.WORLD_EVENT_RESOLVED,
        data={
            "event_id": event_id,
            "resolution": resolution,
            "resolution_params": resolution_params,
        },
    )


# ── Voice Helper Functions ─────────────────────────────────────────────────────


async def send_npc_speech(
    session_id: str,
    npc_id: str,
    text: str,
    audio_data: Optional[bytes] = None,
    audio_url: Optional[str] = None,
    emotion: Optional[str] = None,
    language: str = "en",
    provider: str = "",
    duration_seconds: float = 0.0,
):
    """
    Send NPC speech output via WebSocket.
    
    Clients can play the audio directly or use the URL.
    Audio is base64-encoded for transmission.
    
    Args:
        session_id: Session ID for broadcast
        npc_id: NPC speaking
        text: Spoken text
        audio_data: Audio data (will be base64-encoded)
        audio_url: Alternative URL to audio file
        emotion: Emotion style used
        language: Language code
        provider: TTS provider used
        duration_seconds: Audio duration
    """
    manager = get_connection_manager()
    
    import base64
    
    # Encode audio if provided
    audio_base64 = None
    if audio_data:
        audio_base64 = base64.b64encode(audio_data).decode("ascii")
    
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.NPC_SPEECH,
        npc_id=npc_id,
        data={
            "npc_id": npc_id,
            "text": text,
            "audio_data": audio_base64,
            "audio_url": audio_url,
            "emotion": emotion,
            "language": language,
            "provider": provider,
            "duration_seconds": duration_seconds,
        },
    )


async def send_voice_ready(
    session_id: str,
    providers: List[str],
    default_provider: Optional[str] = None,
):
    """
    Notify client that voice system is ready.
    
    Args:
        session_id: Session ID for notification
        providers: List of available providers
        default_provider: Default provider name
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.VOICE_READY,
        data={
            "providers": providers,
            "default_provider": default_provider,
        },
    )


async def send_voice_error(
    session_id: str,
    error_message: str,
    error_code: str = "",
    npc_id: Optional[str] = None,
):
    """
    Send voice error notification.
    
    Args:
        session_id: Session ID for notification
        error_message: Error description
        error_code: Error code
        npc_id: Related NPC if any
    """
    manager = get_connection_manager()
    await manager.send_to_session(
        session_id=session_id,
        message_type=MessageType.VOICE_ERROR,
        npc_id=npc_id,
        data={
            "error": error_message,
            "code": error_code,
        },
    )


async def process_player_speech(
    session_id: str,
    npc_id: str,
    audio_data: bytes,
    language: str = "en",
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process player speech: STT -> Chat -> TTS -> Response.
    
    This is a convenience function that:
    1. Transcribes player speech to text
    2. Processes chat with NPC
    3. Synthesizes NPC response
    4. Returns text and audio
    
    Args:
        session_id: Session ID
        npc_id: NPC to chat with
        audio_data: Player's speech audio
        language: Language code
        provider: STT provider (auto-selected if None)
        
    Returns:
        Dict with transcribed text, NPC response, and audio
    """
    from neshama.voice import get_voice_manager, EmotionStyle
    
    manager = get_voice_manager()
    
    # Step 1: Speech-to-Text
    stt_result = await manager.stt(
        audio_data=audio_data,
        language=language,
        provider_name=provider,
    )
    
    transcribed_text = stt_result.text
    
    # Step 2: Chat with NPC (placeholder - integrate with chat API)
    # In a real implementation, this would call the chat system
    npc_response_text = f"You said: {transcribed_text}"
    
    # Step 3: Text-to-Speech for NPC response
    tts_result = await manager.tts(
        text=npc_response_text,
        npc_id=npc_id,
        emotion=EmotionStyle.NEUTRAL,
    )
    
    return {
        "transcribed_text": transcribed_text,
        "confidence": stt_result.confidence,
        "npc_response": npc_response_text,
        "audio_data": tts_result.audio_data,
        "audio_duration": tts_result.duration_seconds,
        "provider": tts_result.provider,
    }
