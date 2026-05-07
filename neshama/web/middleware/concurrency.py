# Concurrency Limiter Middleware
"""
Concurrency limiting middleware for FastAPI.

Limits the number of concurrent requests being processed.
Protects against overload and resource exhaustion.
"""

import time
import threading
import logging
from typing import Callable, Dict, Optional
from dataclasses import dataclass, field

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class ConcurrencyStats:
    """Concurrency statistics."""
    current_concurrent: int = 0
    max_concurrent: int = 0
    total_requests: int = 0
    rejected_requests: int = 0
    peak_concurrent: int = 0
    endpoint_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "current_concurrent": self.current_concurrent,
            "max_concurrent": self.max_concurrent,
            "total_requests": self.total_requests,
            "rejected_requests": self.rejected_requests,
            "peak_concurrent": self.peak_concurrent,
            "endpoint_stats": self.endpoint_stats,
        }


class ConcurrencyLimiter:
    """
    Concurrency limiter for FastAPI.
    
    Features:
    - Configurable max concurrent requests
    - Per-endpoint statistics
    - Graceful rejection with 503 + Retry-After
    - Thread-safe operations
    
    Example:
        >>> limiter = ConcurrencyLimiter(max_concurrent=100)
        >>> app.add_middleware(limiter.get_middleware())
    """
    
    def __init__(
        self,
        max_concurrent: int = 100,
        max_queue_size: int = 0,
        endpoint_stats_enabled: bool = True,
    ):
        """
        Initialize concurrency limiter.
        
        Args:
            max_concurrent: Maximum concurrent requests
            max_queue_size: Max requests to queue (0 = no queue)
            endpoint_stats_enabled: Track per-endpoint stats
        """
        self._max_concurrent = max_concurrent
        self._max_queue_size = max_queue_size
        self._endpoint_stats_enabled = endpoint_stats_enabled
        
        self._current_concurrent = 0
        self._total_requests = 0
        self._rejected_requests = 0
        self._peak_concurrent = 0
        self._endpoint_stats: Dict[str, Dict[str, int]] = {}
        self._lock = threading.RLock()
        
        # Queue for waiting requests (stores timestamps)
        self._queue: list = []
        self._queue_lock = threading.RLock()
    
    @property
    def stats(self) -> ConcurrencyStats:
        """Get current statistics."""
        with self._lock:
            return ConcurrencyStats(
                current_concurrent=self._current_concurrent,
                max_concurrent=self._max_concurrent,
                total_requests=self._total_requests,
                rejected_requests=self._rejected_requests,
                peak_concurrent=self._peak_concurrent,
                endpoint_stats=dict(self._endpoint_stats),
            )
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Get a normalized endpoint key for tracking."""
        return f"{request.method} {request.url.path}"
    
    def _update_endpoint_stats(self, endpoint: str, success: bool) -> None:
        """Update endpoint statistics."""
        if not self._endpoint_stats_enabled:
            return
        
        with self._lock:
            if endpoint not in self._endpoint_stats:
                self._endpoint_stats[endpoint] = {
                    "requests": 0,
                    "completed": 0,
                    "rejected": 0,
                }
            
            stats = self._endpoint_stats[endpoint]
            stats["requests"] += 1
            if success:
                stats["completed"] += 1
            else:
                stats["rejected"] += 1
    
    def acquire(self, request: Request) -> bool:
        """
        Try to acquire a concurrency slot.
        
        Args:
            request: The incoming request
            
        Returns:
            True if acquired, False if rejected
        """
        endpoint = self._get_endpoint_key(request)
        
        with self._lock:
            self._total_requests += 1
            
            if self._current_concurrent >= self._max_concurrent:
                self._rejected_requests += 1
                self._update_endpoint_stats(endpoint, success=False)
                return False
            
            self._current_concurrent += 1
            self._peak_concurrent = max(self._peak_concurrent, self._current_concurrent)
            self._update_endpoint_stats(endpoint, success=True)
            return True
    
    def release(self) -> None:
        """Release a concurrency slot."""
        with self._lock:
            self._current_concurrent = max(0, self._current_concurrent - 1)
    
    def get_retry_after(self) -> int:
        """
        Get suggested retry-after value in seconds.
        
        Returns:
            Retry after seconds
        """
        # Simple heuristic: base on how many slots are free
        with self._lock:
            available = self._max_concurrent - self._current_concurrent
            if available > 0:
                return 1
            return 5
    
    def get_middleware(self) -> type:
        """Get the FastAPI middleware class."""
        return self._create_middleware_class()
    
    def _create_middleware_class(self) -> type:
        """Create a middleware class that uses this limiter."""
        limiter = self
        
        class ConcurrencyLimiterMiddleware(BaseHTTPMiddleware):
            """Middleware that limits concurrent requests."""
            
            async def dispatch(
                self, request: Request, call_next: Callable
            ) -> Response:
                # Check if we can process this request
                if not limiter.acquire(request):
                    retry_after = limiter.get_retry_after()
                    logger.warning(
                        f"Concurrency limit reached, rejecting request: "
                        f"{request.method} {request.url.path}"
                    )
                    return JSONResponse(
                        status_code=503,
                        content={
                            "error": "Service temporarily unavailable",
                            "message": "Server is at maximum capacity",
                            "retry_after": retry_after,
                        },
                        headers={
                            "Retry-After": str(retry_after),
                            "X-Concurrency-Limit": str(limiter.stats.max_concurrent),
                        },
                    )
                
                try:
                    response = await call_next(request)
                    
                    # Add concurrency headers to response
                    response.headers["X-Concurrency-Current"] = str(
                        limiter.stats.current_concurrent
                    )
                    response.headers["X-Concurrency-Limit"] = str(
                        limiter.stats.max_concurrent
                    )
                    
                    return response
                finally:
                    limiter.release()
        
        return ConcurrencyLimiterMiddleware


# Global limiter instance
_limiter: Optional[ConcurrencyLimiter] = None


def get_limiter(
    max_concurrent: int = 100,
    endpoint_stats_enabled: bool = True,
) -> ConcurrencyLimiter:
    """
    Get or create the global concurrency limiter.
    
    Args:
        max_concurrent: Maximum concurrent requests
        endpoint_stats_enabled: Track per-endpoint stats
        
    Returns:
        The ConcurrencyLimiter instance
    """
    global _limiter
    if _limiter is None:
        _limiter = ConcurrencyLimiter(
            max_concurrent=max_concurrent,
            endpoint_stats_enabled=endpoint_stats_enabled,
        )
    return _limiter


def get_stats() -> ConcurrencyStats:
    """Get concurrency statistics."""
    return get_limiter().stats


def reset_stats() -> None:
    """Reset statistics."""
    global _limiter
    if _limiter:
        _limiter = None
