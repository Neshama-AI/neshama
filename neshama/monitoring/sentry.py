# Sentry Integration
"""
Sentry error monitoring integration.

Provides automatic error tracking and monitoring:
- Unhandled exceptions
- API 5xx errors
- LLM Provider failures
- Data storage errors

Features:
- Optional dependency (silent skip if not configured)
- Configurable sampling rate
- Rich context attachment
- Ignore rules for noise
"""

import os
import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Sentry integration state
_sentry_initialized = False
_sentry_client = None

# Environment variables
ENV_SENTRY_DSN = "SENTRY_DSN"
ENV_SENTRY_SAMPLE_RATE = "SENTRY_SAMPLE_RATE"
ENV_SENTRY_ENVIRONMENT = "SENTRY_ENVIRONMENT"
ENV_SENTRY_TRACES_SAMPLE_RATE = "SENTRY_TRACES_SAMPLE_RATE"


class SentryIntegration:
    """
    Sentry SDK integration for Neshama.
    
    Features:
    - Optional dependency (fails silently if not installed)
    - Automatic error capture
    - Custom context attachment
    - Configurable sampling
    - Ignore rules for expected errors
    
    Example:
        >>> sentry = SentryIntegration()
        >>> sentry.init()
        >>> 
        >>> # Capture with context
        >>> sentry.capture_exception(
        ...     exc_info,
        ...     context={"session_id": "abc", "npc_id": "npc_001"}
        ... )
    """
    
    def __init__(self):
        """Initialize Sentry integration."""
        self._dsn: Optional[str] = None
        self._sample_rate: float = 1.0
        self._environment: Optional[str] = None
        self._traces_sample_rate: float = 0.2
        self._initialized = False
    
    @property
    def is_configured(self) -> bool:
        """Check if Sentry DSN is configured."""
        return bool(os.environ.get(ENV_SENTRY_DSN))
    
    @property
    def is_initialized(self) -> bool:
        """Check if Sentry client is initialized."""
        return self._initialized and _sentry_initialized
    
    def _check_sentry_available(self) -> bool:
        """Check if sentry-sdk is available."""
        try:
            import sentry_sdk
            return True
        except ImportError:
            return False
    
    def init(self) -> bool:
        """
        Initialize Sentry SDK.
        
        Returns:
            True if initialized, False if skipped
        """
        if self._initialized:
            return True
        
        # Check if DSN is configured
        self._dsn = os.environ.get(ENV_SENTRY_DSN)
        if not self._dsn:
            logger.debug("Sentry DSN not configured, skipping initialization")
            return False
        
        # Check if sentry-sdk is installed
        if not self._check_sentry_available():
            logger.warning(
                "sentry-sdk not installed. "
                "Install with: pip install sentry-sdk"
            )
            return False
        
        # Load configuration
        self._sample_rate = float(
            os.environ.get(ENV_SENTRY_SAMPLE_RATE, "1.0")
        )
        self._environment = os.environ.get(
            ENV_SENTRY_ENVIRONMENT,
            os.environ.get("ENV", "production")
        )
        self._traces_sample_rate = float(
            os.environ.get(ENV_SENTRY_TRACES_SAMPLE_RATE, "0.2")
        )
        
        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            
            # Configure integrations
            integrations = [
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.WARNING,
                ),
                FastApiIntegration(
                    transaction_style="endpoint",
                ),
            ]
            
            # Initialize Sentry
            sentry_sdk.init(
                dsn=self._dsn,
                environment=self._environment,
                release=self._get_release(),
                sample_rate=self._sample_rate,
                traces_sample_rate=self._traces_sample_rate,
                integrations=integrations,
                # Ignore expected errors
                ignore_errors=[
                    "HTTPException",
                    "ClientError",
                    "RequestError",
                    # Rate limiting is expected
                    "429",
                    "RateLimitError",
                    # Validation errors
                    "ValidationError",
                    "PydanticValidationError",
                ],
                # Don't send personal data
                send_default_pii=False,
                # Attach breadcrumbs
                max_breadcrumbs=50,
            )
            
            global _sentry_initialized, _sentry_client
            _sentry_initialized = True
            _sentry_client = sentry_sdk
            self._initialized = True
            
            logger.info(
                f"Sentry initialized (environment={self._environment}, "
                f"sample_rate={self._sample_rate})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            return False
    
    def _get_release(self) -> Optional[str]:
        """Get application version/release."""
        try:
            from neshama import __version__
            return __version__
        except Exception:
            return None
    
    def capture_exception(
        self,
        exc_info: Any = None,
        context: Optional[Dict[str, Any]] = None,
        hint: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Capture an exception with optional context.
        
        Args:
            exc_info: Exception info tuple (type, value, traceback)
            context: Additional context to attach
            hint: Sentry hint for processing
            
        Returns:
            Event ID if captured, None otherwise
        """
        if not self.is_initialized:
            return None
        
        try:
            import sentry_sdk
            
            # Add context
            if context:
                with sentry_sdk.configure_scope() as scope:
                    for key, value in context.items():
                        if value is not None:
                            scope.set_context(key, self._serialize_context(value))
            
            # Capture exception
            event_id = sentry_sdk.capture_exception(exc_info, hint=hint)
            return event_id
            
        except Exception as e:
            logger.warning(f"Failed to capture exception to Sentry: {e}")
            return None
    
    def capture_message(
        self,
        message: str,
        level: str = "info",
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Capture a message.
        
        Args:
            message: The message to capture
            level: Log level (debug, info, warning, error)
            context: Additional context to attach
            
        Returns:
            Event ID if captured, None otherwise
        """
        if not self.is_initialized:
            return None
        
        try:
            import sentry_sdk
            
            # Add context
            if context:
                with sentry_sdk.configure_scope() as scope:
                    for key, value in context.items():
                        if value is not None:
                            scope.set_context(key, self._serialize_context(value))
            
            # Capture message
            event_id = sentry_sdk.capture_message(message, level=level)
            return event_id
            
        except Exception as e:
            logger.warning(f"Failed to capture message to Sentry: {e}")
            return None
    
    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a breadcrumb to the current transaction.
        
        Args:
            message: Breadcrumb message
            category: Breadcrumb category
            level: Breadcrumb level
            data: Additional data
        """
        if not self.is_initialized:
            return
        
        try:
            import sentry_sdk
            
            sentry_sdk.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=data or {},
            )
        except Exception as e:
            logger.warning(f"Failed to add breadcrumb: {e}")
    
    def set_context(self, name: str, data: Dict[str, Any]) -> None:
        """
        Set context for the current scope.
        
        Args:
            name: Context name
            data: Context data
        """
        if not self.is_initialized:
            return
        
        try:
            import sentry_sdk
            
            with sentry_sdk.configure_scope() as scope:
                scope.set_context(name, self._serialize_context(data))
        except Exception as e:
            logger.warning(f"Failed to set context: {e}")
    
    def set_user(self, user_id: str, **kwargs) -> None:
        """
        Set user context.
        
        Args:
            user_id: User identifier
            **kwargs: Additional user data
        """
        if not self.is_initialized:
            return
        
        try:
            import sentry_sdk
            
            user_data = {"id": user_id, **kwargs}
            sentry_sdk.set_user(user_data)
        except Exception as e:
            logger.warning(f"Failed to set user: {e}")
    
    def set_tag(self, key: str, value: str) -> None:
        """
        Set a tag.
        
        Args:
            key: Tag key
            value: Tag value
        """
        if not self.is_initialized:
            return
        
        try:
            import sentry_sdk
            sentry_sdk.set_tag(key, value)
        except Exception as e:
            logger.warning(f"Failed to set tag: {e}")
    
    def _serialize_context(self, data: Any) -> Dict[str, Any]:
        """Serialize context data for Sentry."""
        if isinstance(data, dict):
            return {
                key: self._serialize_context(value)
                for key, value in data.items()
                if value is not None
            }
        elif isinstance(data, (list, tuple)):
            return [self._serialize_context(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            try:
                return str(data)
            except Exception:
                return repr(data)


# Module-level singleton
_integration: Optional[SentryIntegration] = None


def get_integration() -> SentryIntegration:
    """Get the Sentry integration singleton."""
    global _integration
    if _integration is None:
        _integration = SentryIntegration()
    return _integration


def init_sentry() -> bool:
    """Initialize Sentry integration."""
    return get_integration().init()


def capture_exception(
    exc_info: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Capture an exception."""
    return get_integration().capture_exception(exc_info, context)


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Capture a message."""
    return get_integration().capture_message(message, level, context)
