# Middleware Module
"""
Web middleware for Neshama.

Provides middleware components:
- Concurrency limiting
- Rate limiting
- Request logging
- Error handling

Usage:
    from neshama.web.middleware import get_limiter, get_middleware
    
    # Add middleware to app
    app.add_middleware(get_limiter().get_middleware())
    app.add_middleware(get_middleware().get_middleware())
"""

from .concurrency import (
    ConcurrencyLimiter,
    ConcurrencyStats,
    get_limiter,
    get_stats,
    reset_stats,
)
from .rate_limit import (
    RateLimitMiddleware,
    RateLimitResponse,
    RateLimitMetrics,
    get_middleware,
    get_metrics,
    DEFAULT_IP_LIMIT,
    DEFAULT_API_KEY_LIMIT,
)

__all__ = [
    # Concurrency
    "ConcurrencyLimiter",
    "ConcurrencyStats",
    "get_limiter",
    "get_stats",
    "reset_stats",
    # Rate Limiting
    "RateLimitMiddleware",
    "RateLimitResponse",
    "RateLimitMetrics",
    "get_middleware",
    "get_metrics",
    "DEFAULT_IP_LIMIT",
    "DEFAULT_API_KEY_LIMIT",
]
