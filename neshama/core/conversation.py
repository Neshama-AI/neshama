"""
Neshama Core - Conversation Manager
===================================

Manages multi-turn conversations and session states.

Features:
- Session management
- Multi-turn conversation context
- History maintenance
- Session timeout handling
"""

import logging
import threading
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Conversation message."""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class Session:
    """
    Session object.
    
    Manages state and history for a single conversation session.
    """
    id: str = ""  # Empty string triggers auto-generation in __post_init__
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Configuration
    max_history: int = 50  # Maximum history messages
    timeout_minutes: int = 30  # Session timeout
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to the session.
        
        Args:
            role: Message role ("user" | "assistant")
            content: Message content
            metadata: Additional metadata
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Trim excess history
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        logger.debug(f"Session {self.id}: Added {role} message")
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get conversation history.
        
        Args:
            limit: Limit number of messages returned (last N)
            
        Returns:
            List of messages
        """
        history = [msg.to_dict() for msg in self.messages]
        
        # Exclude system messages (handled separately in prompt construction)
        history = [m for m in history if m["role"] != "system"]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_context(self, include_recent: int = 10) -> str:
        """
        Get conversation context text.
        
        Args:
            include_recent: Include last N messages
            
        Returns:
            Formatted conversation context
        """
        recent = self.messages[-include_recent:] if include_recent else self.messages
        
        parts = []
        for msg in recent:
            if msg.role == "user":
                parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                parts.append(f"Assistant: {msg.content}")
        
        return "\n".join(parts)
    
    def is_expired(self) -> bool:
        """Check if session has timed out."""
        elapsed = datetime.now() - self.updated_at
        return elapsed > timedelta(minutes=self.timeout_minutes)
    
    def touch(self):
        """Update session timestamp."""
        self.updated_at = datetime.now()
    
    def clear_history(self):
        """Clear conversation history."""
        self.messages = []
        self.updated_at = datetime.now()


class ConversationManager:
    """
    Conversation Manager.
    
    Manages multiple sessions and provides conversation capabilities.
    
    Example:
        >>> cm = ConversationManager()
        >>> session = cm.create_session(user_id="user123")
        >>> cm.add_message(session.id, "user", "Hello!")
        >>> cm.add_message(session.id, "assistant", "Hi there!")
        >>> history = cm.get_history(session.id)
    """
    
    def __init__(
        self,
        max_sessions: int = 100,
        default_max_history: int = 50,
        default_timeout_minutes: int = 30,
    ):
        """
        Initialize conversation manager.
        
        Args:
            max_sessions: Maximum number of active sessions
            default_max_history: Default max history per session
            default_timeout_minutes: Default session timeout
        """
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.RLock()
        self._max_sessions = max_sessions
        self._default_max_history = default_max_history
        self._default_timeout = default_timeout_minutes
        
        logger.info("ConversationManager initialized")
    
    def create_session(
        self,
        user_id: Optional[str] = None,
        max_history: Optional[int] = None,
        timeout_minutes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """
        Create a new session.
        
        Args:
            user_id: User identifier
            max_history: Max history for this session
            timeout_minutes: Timeout for this session
            metadata: Session metadata
            
        Returns:
            Created Session object
        """
        with self._lock:
            # Cleanup expired sessions if at capacity
            if len(self._sessions) >= self._max_sessions:
                self._cleanup_expired()
            
            session = Session(
                user_id=user_id,
                max_history=max_history or self._default_max_history,
                timeout_minutes=timeout_minutes or self._default_timeout,
                metadata=metadata or {},
            )
            
            self._sessions[session.id] = session
            logger.info(f"Created session {session.id} for user {user_id}")
            
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object or None if not found
        """
        return self._sessions.get(session_id)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a message to a session.
        
        Args:
            session_id: Session identifier
            role: Message role ("user" | "assistant" | "system")
            content: Message content
            metadata: Additional metadata
            
        Returns:
            True if message added, False if session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return False
            
            session.add_message(role, content, metadata)
            return True
    
    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Limit number of messages
            
        Returns:
            List of message dictionaries
        """
        session = self._sessions.get(session_id)
        if not session:
            return []
        
        return session.get_history(limit)
    
    def get_context(
        self,
        session_id: str,
        include_recent: int = 10,
    ) -> str:
        """
        Get formatted conversation context.
        
        Args:
            session_id: Session identifier
            include_recent: Include last N messages
            
        Returns:
            Formatted context string
        """
        session = self._sessions.get(session_id)
        if not session:
            return ""
        
        return session.get_context(include_recent)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session {session_id}")
                return True
            return False
    
    def _cleanup_expired(self) -> int:
        """
        Remove expired sessions.
        
        Returns:
            Number of sessions removed
        """
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]
        
        for sid in expired:
            del self._sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    @property
    def session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)
