"""
Neshama Core - Main Engine
===========================

Core dialogue engine that orchestrates all modules for conversation.

Flow:
1. Load/parse user input
2. Retrieve Memory (RAG + context)
3. Get Soul configuration
4. Build Prompt (inject Soul + Memory)
5. Call LLM
6. Generate response
7. Store conversation memory
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EngineConfig:
    """Engine configuration."""
    # Engine identity
    engine_id: str = "default"
    engine_name: str = "Neshama"
    
    # Soul configuration
    soul_config_path: Optional[str] = None
    soul_enabled: bool = True
    
    # Memory configuration
    memory_enabled: bool = True
    memory_storage_path: str = "./memory_data"
    rag_top_k: int = 3
    short_term_capacity: int = 10
    
    # Model configuration
    model_provider: str = "mock"  # Default to mock for MVP
    model_name: str = "mock-model"
    temperature: float = 0.7
    max_tokens: int = 2048
    
    # System prompt
    system_prompt: str = "You are a friendly AI assistant."
    
    # Debug options
    debug: bool = False
    log_prompts: bool = False


@dataclass
class ChatResponse:
    """Chat response."""
    content: str
    session_id: str
    message_id: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=lambda: {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    })
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def __str__(self) -> str:
        return self.content


class NeshamaEngine:
    """
    Neshama Core Dialogue Engine.
    
    Orchestrates Soul, Memory, and Model layers to provide
    complete conversation capabilities.
    
    Example:
        # Basic usage
        engine = NeshamaEngine()
        response = engine.chat("Hello")
        print(response.content)
        
        # With configuration
        config = EngineConfig(
            soul_config_path="./configs/my_soul.yaml",
            model_provider="openai",
            model_name="gpt-4",
            debug=True
        )
        engine = NeshamaEngine(config=config)
        
        # Multi-turn conversation
        session = engine.create_session(user_id="user123")
        response1 = engine.chat("Hello", session_id=session.id)
        response2 = engine.chat("How are you?", session_id=session.id)
    """
    
    def __init__(
        self,
        config: Optional[EngineConfig] = None,
    ):
        """
        Initialize Neshama engine.
        
        Args:
            config: Engine configuration
        """
        self.config = config or EngineConfig()
        self._init_logging()
        
        logger.info(f"Initializing NeshamaEngine: {self.config.engine_id}")
        start_time = time.time()
        
        # Initialize conversation manager
        from neshama.core.conversation import ConversationManager
        self.conversation = ConversationManager()
        
        # Initialize memory if enabled
        if self.config.memory_enabled:
            self._init_memory()
        
        # Initialize soul if enabled
        if self.config.soul_enabled:
            self._init_soul()
        
        # Initialize model adapter
        self._init_model()
        
        elapsed = time.time() - start_time
        logger.info(f"NeshamaEngine initialized in {elapsed:.2f}s")
    
    def _init_logging(self):
        """Initialize logging based on config."""
        if self.config.debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
    
    def _init_memory(self):
        """Initialize memory layer."""
        try:
            from neshama.memory import Memory, MemoryConfig
            
            memory_config = MemoryConfig(
                agent_id=self.config.engine_id,
                storage_path=self.config.memory_storage_path,
                short_term_capacity=self.config.short_term_capacity,
                rag_top_k=self.config.rag_top_k,
            )
            
            self.memory = Memory(config=memory_config)
            logger.info("Memory layer initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize memory: {e}")
            self.memory = None
    
    def _init_soul(self):
        """Initialize soul layer."""
        try:
            from neshama.soul.loader import SoulLoader, SoulLoaderConfig
            
            soul_config = SoulLoaderConfig(
                config_dir="./Neshama/configs",
                default_config_name="default_soul.yaml",
            )
            
            self.soul_loader = SoulLoader(config=soul_config)
            
            # Load soul configuration
            if self.config.soul_config_path:
                self.soul_config = self.soul_loader.load(config_path=self.config.soul_config_path)
            else:
                self.soul_config = self.soul_loader.load()
            
            logger.info("Soul layer initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize soul: {e}")
            self.soul_config = {}
            self.soul_loader = None
    
    def _init_model(self):
        """Initialize model adapter."""
        # For MVP, use mock model
        self.model = MockModelAdapter(
            provider=self.config.model_provider,
            model_name=self.config.model_name,
        )
        logger.info(f"Model adapter initialized: {self.config.model_provider}/{self.config.model_name}")
    
    def create_session(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a new conversation session.
        
        Args:
            user_id: User identifier
            metadata: Session metadata
            
        Returns:
            Session object
        """
        return self.conversation.create_session(user_id=user_id, metadata=metadata)
    
    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Send a chat message and get a response.
        
        Args:
            message: User message
            session_id: Session ID for multi-turn conversation
            user_id: User ID (creates new session if session_id not provided)
            
        Returns:
            ChatResponse object
        """
        start_time = time.time()
        message_id = str(uuid.uuid4())
        
        # Get or create session
        if session_id:
            session = self.conversation.get_session(session_id)
            if not session:
                session = self.conversation.create_session(user_id=user_id)
        else:
            session = self.conversation.create_session(user_id=user_id)
        
        # Add user message to session
        self.conversation.add_message(session.id, "user", message)
        
        # Build context
        context = self._build_context(message, session)
        
        # Call model
        response_text = self.model.generate(
            prompt=context,
            system_prompt=self.config.system_prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        
        # Add assistant response to session
        self.conversation.add_message(session.id, "assistant", response_text)
        
        # Store in memory if enabled
        if self.memory:
            try:
                self.memory.add_turn("user", message)
                self.memory.add_turn("assistant", response_text)
            except Exception as e:
                logger.warning(f"Failed to store in memory: {e}")
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        return ChatResponse(
            content=response_text,
            session_id=session.id,
            message_id=message_id,
            model=self.config.model_name,
            provider=self.config.model_provider,
            latency_ms=latency_ms,
        )
    
    def _build_context(self, message: str, session) -> str:
        """
        Build conversation context.
        
        Args:
            message: Current user message
            session: Session object
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Add soul context if available
        if self.soul_config and self.soul_loader:
            soul_context = self._get_soul_context()
            if soul_context:
                parts.append(f"[Soul Context]\n{soul_context}")
        
        # Add memory context if available
        if self.memory:
            try:
                memory_context = self.memory.get_short_term_context()
                if memory_context:
                    parts.append(f"[Memory Context]\n{memory_context}")
            except Exception as e:
                logger.debug(f"Failed to get memory context: {e}")
        
        # Add conversation history
        history = session.get_history(limit=10)
        if history:
            history_lines = []
            for msg in history[-10:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role}: {msg['content']}")
            parts.append(f"[Conversation History]\n" + "\n".join(history_lines))
        
        # Add current message
        parts.append(f"[Current]\nUser: {message}")
        
        return "\n\n".join(parts)
    
    def _get_soul_context(self) -> str:
        """Get soul configuration context."""
        if not self.soul_config:
            return ""
        
        parts = []
        
        # Identity
        if "identity" in self.soul_config:
            identity = self.soul_config["identity"]
            parts.append(f"Name: {identity.get('name', 'Unknown')}")
            parts.append(f"Tagline: {identity.get('tagline', '')}")
        
        # Characteristics
        if "characteristics" in self.soul_config:
            chars = self.soul_config["characteristics"]
            for key, value in chars.items():
                if isinstance(value, dict):
                    level = value.get("level", 0.5)
                    parts.append(f"{key}: {level:.1f}")
        
        return "\n".join(parts)


class MockModelAdapter:
    """
    Mock model adapter for testing/MVP.
    
    Provides simple echo/rule-based responses without requiring
    actual LLM API calls.
    """
    
    def __init__(self, provider: str, model_name: str):
        self.provider = provider
        self.model_name = model_name
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a mock response.
        
        For MVP, this provides simple rule-based responses.
        Replace with actual LLM integration for production.
        """
        # Simple rule-based responses for testing
        user_msg = ""
        if "[Current]" in prompt:
            parts = prompt.split("[Current]")
            if len(parts) > 1:
                current = parts[1].strip()
                if "User:" in current:
                    user_msg = current.split("User:")[1].strip()
        
        # Basic responses based on keywords
        user_lower = user_msg.lower()
        
        if any(g in user_lower for g in ["hello", "hi", "你好", "嗨"]):
            return "Hello! I'm Neshama, your AI companion. How can I help you today?"
        
        elif any(g in user_lower for g in ["how are you", "怎么样", "好吗"]):
            return "I'm doing great, thanks for asking! I'm here and ready to help. What's on your mind?"
        
        elif any(g in user_lower for g in ["who are you", "你是谁", "name"]):
            return "I'm Neshama, an AI personality system with emotions, drives, and memory. Think of me as an AI with a soul! 😊"
        
        elif any(g in user_lower for g in ["thank", "谢谢", "thanks"]):
            return "You're welcome! Is there anything else I can help you with?"
        
        elif any(g in user_lower for g in ["bye", "goodbye", "再见", "拜拜"]):
            return "Goodbye! Take care! 👋"
        
        elif "?" in user_msg or "？" in user_msg:
            return f"That's an interesting question about '{user_msg[:30]}...'. As an AI, I don't have personal opinions, but I'm here to help you explore different perspectives!"
        
        else:
            return f"I understand you said: '{user_msg[:50]}...' Let me think about that. Could you tell me more about what you're looking for?"
