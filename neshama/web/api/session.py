# Session Management
"""
Session management for game clients and NPC registration.

Provides:
- Game session creation and lifecycle management
- NPC registration per session
- Heartbeat tracking
- Session metadata storage
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """A game session."""
    session_id: str
    game_id: str
    client_id: str
    created_at: datetime
    last_heartbeat: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_alive(self, timeout_seconds: int = 300) -> bool:
        """
        Check if the session is still alive.
        
        Args:
            timeout_seconds: Timeout threshold in seconds.
            
        Returns:
            True if session is alive, False otherwise.
        """
        # Handle both datetime and string timestamps
        if isinstance(self.last_heartbeat, str):
            last_hb = datetime.fromisoformat(self.last_heartbeat)
        else:
            last_hb = self.last_heartbeat
        
        elapsed = (datetime.now() - last_hb).total_seconds()
        return elapsed < timeout_seconds
    
    def to_dict(self, npc_count: int = None) -> Dict:
        # Handle both datetime and string timestamps
        created = self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        last_hb = self.last_heartbeat.isoformat() if isinstance(self.last_heartbeat, datetime) else self.last_heartbeat
        
        return {
            "session_id": self.session_id,
            "game_id": self.game_id,
            "client_id": self.client_id,
            "created_at": created,
            "last_heartbeat": last_hb,
            "metadata": self.metadata,
            "is_alive": self.is_alive(),
            "npc_count": npc_count if npc_count is not None else 0,
        }


@dataclass
class NPCRegistration:
    """An NPC registration to a session."""
    npc_id: str
    session_id: str
    registered_at: datetime
    
    def to_dict(self) -> Dict:
        return {
            "npc_id": self.npc_id,
            "session_id": self.session_id,
            "registered_at": self.registered_at.isoformat(),
        }


class SessionManager:
    """
    Session manager for game clients.
    
    Features:
    - Session creation with unique IDs
    - Heartbeat tracking
    - NPC registration per session
    - Automatic session cleanup
    
    Example:
        >>> manager = SessionManager()
        >>> 
        >>> # Create session
        >>> session = manager.create_session("game_001", "client_abc")
        >>> 
        >>> # Register NPC
        >>> manager.register_npc("npc_001", session.session_id)
        >>> 
        >>> # Heartbeat
        >>> manager.heartbeat(session.session_id)
    """
    
    def __init__(self, session_timeout: int = 300):
        """
        Initialize session manager.
        
        Args:
            session_timeout: Session timeout in seconds (default 5 minutes)
        """
        self._sessions: Dict[str, Session] = {}
        self._client_sessions: Dict[str, List[str]] = {}  # client_id -> [session_ids]
        self._npc_sessions: Dict[str, str] = {}  # npc_id -> session_id
        self._session_timeout = session_timeout
        self._lock = threading.RLock()
    
    def create_session(
        self,
        game_id: str,
        client_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """
        Create a new session.
        
        Args:
            game_id: The game ID
            client_id: The client ID
            metadata: Optional session metadata
            
        Returns:
            The created Session
        """
        with self._lock:
            now = datetime.now()
            session_id = str(uuid.uuid4())
            
            session = Session(
                session_id=session_id,
                game_id=game_id,
                client_id=client_id,
                created_at=now,
                last_heartbeat=now,
                metadata=metadata or {},
            )
            
            self._sessions[session_id] = session
            
            # Track client's sessions
            if client_id not in self._client_sessions:
                self._client_sessions[client_id] = []
            self._client_sessions[client_id].append(session_id)
            
            logger.debug(f"Created session {session_id} for client {client_id}")
            
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        with self._lock:
            session = self._sessions.get(session_id)
            
            if session:
                # Check timeout
                elapsed = (datetime.now() - session.last_heartbeat).total_seconds()
                if elapsed > self._session_timeout:
                    self._remove_session(session_id)
                    return None
            
            return session
    
    def get_client_sessions(self, client_id: str) -> List[Session]:
        """Get all sessions for a client."""
        with self._lock:
            session_ids = self._client_sessions.get(client_id, [])
            sessions = []
            
            for session_id in session_ids:
                session = self.get_session(session_id)
                if session:
                    sessions.append(session)
            
            return sessions
    
    def heartbeat(self, session_id: str) -> bool:
        """
        Update session heartbeat.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if updated, False if session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            
            if not session:
                return False
            
            session.last_heartbeat = datetime.now()
            return True
    
    def register_npc(self, npc_id: str, session_id: str) -> Optional[NPCRegistration]:
        """
        Register an NPC to a session.
        
        Args:
            npc_id: The NPC ID
            session_id: The session ID
            
        Returns:
            The registration, or None if session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            
            if not session:
                return None
            
            # Unregister from previous session if any
            if npc_id in self._npc_sessions:
                old_session_id = self._npc_sessions[npc_id]
                if old_session_id != session_id:
                    logger.debug(f"NPC {npc_id} moving from session {old_session_id} to {session_id}")
            
            registration = NPCRegistration(
                npc_id=npc_id,
                session_id=session_id,
                registered_at=datetime.now(),
            )
            
            self._npc_sessions[npc_id] = session_id
            
            return registration
    
    def unregister_npc(self, npc_id: str) -> bool:
        """
        Unregister an NPC.
        
        Args:
            npc_id: The NPC ID
            
        Returns:
            True if unregistered, False if not found
        """
        with self._lock:
            if npc_id in self._npc_sessions:
                del self._npc_sessions[npc_id]
                return True
            return False
    
    def get_npc_session(self, npc_id: str) -> Optional[str]:
        """Get the session ID for an NPC."""
        with self._lock:
            return self._npc_sessions.get(npc_id)
    
    def get_session_npcs(self, session_id: str) -> List[str]:
        """Get all NPC IDs registered to a session."""
        with self._lock:
            return [
                npc_id for npc_id, sid in self._npc_sessions.items()
                if sid == session_id
            ]
    
    def _remove_session(self, session_id: str):
        """Remove a session (internal)."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            
            # Remove from client's sessions
            client_id = session.client_id
            if client_id in self._client_sessions:
                self._client_sessions[client_id] = [
                    sid for sid in self._client_sessions[client_id]
                    if sid != session_id
                ]
            
            # Remove NPC registrations
            npcs_to_remove = [
                npc_id for npc_id, sid in self._npc_sessions.items()
                if sid == session_id
            ]
            for npc_id in npcs_to_remove:
                del self._npc_sessions[npc_id]
            
            # Remove session
            del self._sessions[session_id]
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        with self._lock:
            now = datetime.now()
            expired = []
            
            for session_id, session in self._sessions.items():
                # Handle both datetime and string timestamps
                if isinstance(session.last_heartbeat, str):
                    last_hb = datetime.fromisoformat(session.last_heartbeat)
                else:
                    last_hb = session.last_heartbeat
                
                elapsed = (now - last_hb).total_seconds()
                if elapsed > self._session_timeout:
                    expired.append(session_id)
            
            for session_id in expired:
                self._remove_session(session_id)
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")
            
            return len(expired)
    
    def get_stats(self) -> Dict:
        """Get session statistics."""
        with self._lock:
            # Count alive sessions
            alive_sessions = [s for s in self._sessions.values() if s.is_alive()]
            alive_npcs = sum(
                1 for npc_id, session_id in self._npc_sessions.items()
                if session_id in self._sessions and self._sessions[session_id].is_alive()
            )
            
            return {
                "total_sessions": len(self._sessions),
                "active_sessions": len(alive_sessions),
                "active_npcs": alive_npcs,
                "total_npc_registrations": len(self._npc_sessions),
                "total_clients": len(self._client_sessions),
            }
    
    def get_active_sessions(self) -> List[Session]:
        """Get all active (alive) sessions."""
        with self._lock:
            return [s for s in self._sessions.values() if s.is_alive()]
    
    def get_session_with_npc_count(self, session_id: str) -> Optional[Dict]:
        """
        Get session data with NPC count.
        
        Args:
            session_id: The session ID.
            
        Returns:
            Session dict with npc_count, or None if not found.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            
            # Count NPCs in this session
            npc_count = sum(
                1 for npc_id, sid in self._npc_sessions.items()
                if sid == session_id
            )
            
            return session.to_dict(npc_count=npc_count)


# Global session manager instance
_session_manager: Optional[SessionManager] = None
_manager_lock = threading.Lock()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    
    with _manager_lock:
        if _session_manager is None:
            _session_manager = SessionManager()
        return _session_manager


def reset_session_manager() -> None:
    """Reset the global session manager (for testing)."""
    global _session_manager
    
    with _manager_lock:
        if _session_manager is not None:
            _session_manager = None
