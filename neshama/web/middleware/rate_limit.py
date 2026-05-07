# Rate Limit Middleware
"""
Enhanced rate limiting middleware for FastAPI.

Provides multi-layer rate limiting:
- IP-based (DDoS protection)
- API Key-based (per-user quotas)
- Endpoint-based (per-NPC limits)

Features:
- Token bucket algorithm
- Burst traffic allowance
- Standardized 429 responses
- Metrics exposure
- Whitelist support
"""

import time
import hashlib
import logging
from typing import Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..api.rate_limiter import RateLimiter, NPCTier

logger = logging.getLogger(__name__)


# Configuration
DEFAULT_IP_LIMIT = 1000  # requests per minute
DEFAULT_API_KEY_LIMIT = 500  # requests per minute
DEFAULT_ENDPOINT_LIMIT = 60  # requests per minute (for free tier)
BURST_MULTIPLIER = 1.5
BURST_DURATION = 5  # seconds


@dataclass
class RateLimitResponse:
    """Rate limit response data."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: Optional[str] = None
    retry_after: Optional[float] = None
    tier: str = "anonymous"
    
    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_at": self.reset_at,
            "retry_after": self.retry_after,
            "tier": self.tier,
        }


@dataclass
class RateLimitMetrics:
    """Rate limiting metrics."""
    total_checks: int = 0
    total_allowed: int = 0
    total_rejected: int = 0
    ip_blocked: int = 0
    api_key_blocked: int = 0
    endpoint_blocked: int = 0
    whitelist_allowed: int = 0
    ip_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    api_key_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)


class RateLimitMiddleware:
    """
    Multi-layer rate limiting middleware.
    
    Rate limiting layers (in order):
    1. IP whitelist check
    2. IP-based global limit (DDoS protection)
    3. API Key based limit (registered users)
    4. Endpoint-based limit (per-NPC)
    
    Features:
    - Token bucket with burst allowance
    - Configurable limits per tier
    - Whitelist support
    - Detailed metrics
    - Standardized responses
    
    Example:
        >>> middleware = RateLimitMiddleware()
        >>> app.add_middleware(middleware.get_middleware())
    """
    
    def __init__(
        self,
        ip_limit: int = DEFAULT_IP_LIMIT,
        api_key_limit: int = DEFAULT_API_KEY_LIMIT,
        endpoint_limiter: Optional[RateLimiter] = None,
        whitelist_paths: Optional[List[str]] = None,
        whitelist_ips: Optional[Set[str]] = None,
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            ip_limit: Global IP rate limit (requests/minute)
            api_key_limit: Per API key limit (requests/minute)
            endpoint_limiter: Existing endpoint rate limiter
            whitelist_paths: Paths that bypass rate limiting
            whitelist_ips: IPs that bypass rate limiting
        """
        self._ip_limit = ip_limit
        self._api_key_limit = api_key_limit
        self._endpoint_limiter = endpoint_limiter
        
        # Whitelists
        self._whitelist_paths: Set[str] = set(whitelist_paths or [
            "/health",
            "/health/detailed",
            "/api/billing/webhook",
            "/metrics",
        ])
        self._whitelist_ips: Set[str] = whitelist_ips or set()
        
        # IP tracking: ip -> (tokens, last_update, burst_end)
        self._ip_buckets: Dict[str, Tuple[float, float, float]] = {}
        
        # API Key tracking: api_key -> (tokens, last_update, burst_end)
        self._api_key_buckets: Dict[str, Tuple[float, float, float]] = {}
        
        # Metrics
        self._metrics = RateLimitMetrics()
        
        # Lock
        self._lock = None
    
    def _get_lock(self):
        """Get or create lock."""
        if self._lock is None:
            import threading
            self._lock = threading.RLock()
        return self._lock
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check forwarded headers first
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request."""
        # Check header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        
        # Check query param
        if not api_key:
            api_key = request.query_params.get("api_key")
        
        # Normalize
        if api_key:
            if api_key.startswith("Bearer "):
                api_key = api_key[7:]
            return api_key
        
        return None
    
    def _get_tier(self, api_key: Optional[str]) -> str:
        """
        Get tier for API key.
        
        This would normally look up the tier from a database or cache.
        For now, use placeholder logic.
        """
        if not api_key:
            return "anonymous"
        
        # Placeholder: In production, look up tier from storage
        # For now, treat keys starting with "premium_" as premium
        if api_key.startswith("premium_"):
            return "premium"
        elif api_key.startswith("basic_"):
            return "basic"
        
        return "registered"
    
    def _check_ip_limit(self, ip: str, tokens: int = 1) -> Tuple[bool, RateLimitResponse]:
        """
        Check IP rate limit.
        
        Args:
            ip: Client IP
            tokens: Tokens to consume
            
        Returns:
            Tuple of (allowed, response)
        """
        with self._get_lock():
            now = time.time()
            refill_rate = self._ip_limit / 60.0  # per second
            
            if ip not in self._ip_buckets:
                self._ip_buckets[ip] = (float(self._ip_limit), now, now + BURST_DURATION)
            
            bucket_tokens, last_update, burst_end = self._ip_buckets[ip]
            
            # Calculate refill
            elapsed = now - last_update
            bucket_tokens = min(
                float(self._ip_limit),
                bucket_tokens + elapsed * refill_rate
            )
            
            # Apply burst allowance
            max_tokens = float(self._ip_limit)
            if now < burst_end:
                max_tokens = float(self._ip_limit) * BURST_MULTIPLIER
            
            # Check limit
            if bucket_tokens >= tokens:
                bucket_tokens -= tokens
                allowed = True
            else:
                allowed = False
            
            # Calculate retry after
            if not allowed:
                deficit = tokens - bucket_tokens
                retry_after = deficit / refill_rate if refill_rate > 0 else 60
            else:
                retry_after = None
            
            # Update bucket
            self._ip_buckets[ip] = (bucket_tokens, now, burst_end)
            
            # Update metrics
            self._metrics.total_checks += 1
            if allowed:
                self._metrics.total_allowed += 1
            else:
                self._metrics.total_rejected += 1
                self._metrics.ip_blocked += 1
            
            # Track IP stats
            if ip not in self._metrics.ip_stats:
                self._metrics.ip_stats[ip] = {"requests": 0, "blocked": 0}
            self._metrics.ip_stats[ip]["requests"] += 1
            if not allowed:
                self._metrics.ip_stats[ip]["blocked"] += 1
            
            # Calculate reset time
            tokens_to_full = max_tokens - bucket_tokens
            reset_at = datetime.fromtimestamp(
                now + (tokens_to_full / refill_rate if refill_rate > 0 else 60)
            ).isoformat()
            
            return allowed, RateLimitResponse(
                allowed=allowed,
                limit=int(max_tokens),
                remaining=int(bucket_tokens),
                reset_at=reset_at,
                retry_after=retry_after,
                tier="ip_limited",
            )
    
    def _check_api_key_limit(
        self, api_key: Optional[str], tokens: int = 1
    ) -> Tuple[bool, RateLimitResponse]:
        """
        Check API key rate limit.
        
        Args:
            api_key: API key
            tokens: Tokens to consume
            
        Returns:
            Tuple of (allowed, response)
        """
        if not api_key:
            return True, RateLimitResponse(allowed=True, limit=0, remaining=0, tier="anonymous")
        
        with self._get_lock():
            now = time.time()
            
            # Get tier-based limit
            tier = self._get_tier(api_key)
            limit = self._get_limit_for_tier(tier, "default")
            refill_rate = limit / 60.0
            
            # Normalize API key for storage
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            
            if key_hash not in self._api_key_buckets:
                self._api_key_buckets[key_hash] = (float(limit), now, now + BURST_DURATION)
            
            bucket_tokens, last_update, burst_end = self._api_key_buckets[key_hash]
            
            # Calculate refill
            elapsed = now - last_update
            bucket_tokens = min(float(limit), bucket_tokens + elapsed * refill_rate)
            
            # Apply burst
            max_tokens = float(limit)
            if now < burst_end:
                max_tokens = float(limit) * BURST_MULTIPLIER
            
            # Check
            if bucket_tokens >= tokens:
                bucket_tokens -= tokens
                allowed = True
            else:
                allowed = False
            
            # Retry after
            if not allowed:
                deficit = tokens - bucket_tokens
                retry_after = deficit / refill_rate if refill_rate > 0 else 60
            else:
                retry_after = None
            
            # Update
            self._api_key_buckets[key_hash] = (bucket_tokens, now, burst_end)
            
            # Metrics
            self._metrics.total_checks += 1
            if allowed:
                self._metrics.total_allowed += 1
            else:
                self._metrics.total_rejected += 1
                self._metrics.api_key_blocked += 1
            
            # Track
            if api_key not in self._metrics.api_key_stats:
                self._metrics.api_key_stats[api_key] = {"requests": 0, "blocked": 0}
            self._metrics.api_key_stats[api_key]["requests"] += 1
            if not allowed:
                self._metrics.api_key_stats[api_key]["blocked"] += 1
            
            # Reset time
            tokens_to_full = max_tokens - bucket_tokens
            reset_at = datetime.fromtimestamp(
                now + (tokens_to_full / refill_rate if refill_rate > 0 else 60)
            ).isoformat()
            
            return allowed, RateLimitResponse(
                allowed=allowed,
                limit=int(max_tokens),
                remaining=int(bucket_tokens),
                reset_at=reset_at,
                retry_after=retry_after,
                tier=tier,
            )
    
    def _get_limit_for_tier(self, tier: str, endpoint: str) -> int:
        """Get rate limit for a tier and endpoint."""
        tier_obj = NPCTier.FREE
        if tier == "premium":
            tier_obj = NPCTier.PREMIUM
        elif tier == "basic":
            tier_obj = NPCTier.BASIC
        elif tier == "enterprise":
            tier_obj = NPCTier.ENTERPRISE
        
        from ..api.rate_limiter import DEFAULT_LIMITS
        if endpoint in DEFAULT_LIMITS:
            return DEFAULT_LIMITS[endpoint].get(tier_obj, 30)
        return DEFAULT_LIMITS["default"].get(tier_obj, 30)
    
    def _is_whitelisted(self, request: Request) -> bool:
        """Check if request path or IP is whitelisted."""
        path = request.url.path
        
        # Check path whitelist
        for wl_path in self._whitelist_paths:
            if path.startswith(wl_path):
                return True
        
        # Check IP whitelist
        ip = self._get_client_ip(request)
        if ip in self._whitelist_ips:
            return True
        
        return False
    
    def check_request(self, request: Request) -> Tuple[bool, RateLimitResponse, int]:
        """
        Check if a request should be allowed.
        
        Args:
            request: The incoming request
            
        Returns:
            Tuple of (allowed, response, blocking_layer)
            blocking_layer: 0=allowed, 1=IP, 2=API Key, 3=Endpoint
        """
        # Check whitelist
        if self._is_whitelisted(request):
            self._metrics.whitelist_allowed += 1
            return True, RateLimitResponse(allowed=True, limit=0, remaining=0), 0
        
        # Get request identifiers
        ip = self._get_client_ip(request)
        api_key = self._get_api_key(request)
        
        # Layer 1: IP rate limit
        allowed, response = self._check_ip_limit(ip)
        if not allowed:
            return False, response, 1
        
        # Layer 2: API Key rate limit
        allowed, response = self._check_api_key_limit(api_key)
        if not allowed:
            return False, response, 2
        
        # Layer 3: Endpoint rate limit (if limiter provided)
        if self._endpoint_limiter and api_key:
            allowed, info = self._endpoint_limiter.acquire(api_key, "default")
            if not allowed:
                self._metrics.total_rejected += 1
                self._metrics.endpoint_blocked += 1
                return False, RateLimitResponse(
                    allowed=False,
                    limit=info.limit_per_minute,
                    remaining=info.remaining,
                    retry_after=info.retry_after,
                    tier=info.tier.value,
                ), 3
        
        return True, response, 0
    
    @property
    def metrics(self) -> RateLimitMetrics:
        """Get current metrics."""
        return self._metrics
    
    def get_middleware(self) -> type:
        """Get the FastAPI middleware class."""
        return self._create_middleware_class()
    
    def _create_middleware_class(self) -> type:
        """Create a middleware class."""
        middleware = self
        
        class RateLimitMiddlewareClass(BaseHTTPMiddleware):
            """Middleware that enforces rate limits."""
            
            async def dispatch(
                self, request: Request, call_next: Callable
            ) -> Response:
                # Check rate limit
                allowed, response, layer = middleware.check_request(request)
                
                if not allowed:
                    layer_name = ["", "IP", "API Key", "Endpoint"][layer]
                    logger.warning(
                        f"Rate limit exceeded ({layer_name}): "
                        f"{request.method} {request.url.path}"
                    )
                    
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Too Many Requests",
                            "message": f"Rate limit exceeded at {layer_name} level",
                            "limit": response.limit,
                            "remaining": response.remaining,
                            "retry_after": response.retry_after,
                            "tier": response.tier,
                        },
                        headers={
                            "Retry-After": str(int(response.retry_after or 60)),
                            "X-RateLimit-Limit": str(response.limit),
                            "X-RateLimit-Remaining": str(response.remaining),
                            "X-RateLimit-Reset": response.reset_at or "",
                        },
                    )
                
                # Process request
                response = await call_next(request)
                
                # Add rate limit headers to response
                if hasattr(response, "headers") and hasattr(response, "limit"):
                    response.headers["X-RateLimit-Limit"] = str(response.limit)
                    response.headers["X-RateLimit-Remaining"] = str(response.remaining)
                
                return response
        
        return RateLimitMiddlewareClass
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        with self._get_lock():
            self._metrics = RateLimitMetrics()
            self._ip_buckets.clear()
            self._api_key_buckets.clear()


# Global middleware instance
_middleware: Optional[RateLimitMiddleware] = None


def get_middleware(
    ip_limit: int = DEFAULT_IP_LIMIT,
    api_key_limit: int = DEFAULT_API_KEY_LIMIT,
    endpoint_limiter: Optional[RateLimiter] = None,
) -> RateLimitMiddleware:
    """Get or create the global rate limit middleware."""
    global _middleware
    if _middleware is None:
        _middleware = RateLimitMiddleware(
            ip_limit=ip_limit,
            api_key_limit=api_key_limit,
            endpoint_limiter=endpoint_limiter,
        )
    return _middleware


def get_metrics() -> RateLimitMetrics:
    """Get rate limiting metrics."""
    return get_middleware().metrics
