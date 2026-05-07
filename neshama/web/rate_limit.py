# Advanced Rate Limiting with Sliding Window
"""
Advanced rate limiting with sliding window algorithm.

Provides multi-layer rate limiting:
- IP-based limiting (DDoS protection)
- User-based limiting (authenticated users)
- API endpoint differentiation
- Sliding window algorithm for accurate rate limiting

Usage:
    from neshama.web.rate_limit import RateLimitManager, get_rate_limit_manager
    
    manager = get_rate_limit_manager()
    
    # Check and consume
    result = manager.check_request(
        ip="192.168.1.1",
        user_id="user123",
        endpoint="/api/chat",
    )
"""

import asyncio
import logging
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class RateLimitTier(str, Enum):
    """Rate limit tiers for different user levels."""
    ANONYMOUS = "anonymous"
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


# Default rate limits (requests per minute)
DEFAULT_LIMITS: Dict[str, Dict[RateLimitTier, int]] = {
    # IP-based limits (requests per minute)
    "ip": {
        RateLimitTier.ANONYMOUS: 100,
        RateLimitTier.FREE: 200,
        RateLimitTier.BASIC: 500,
        RateLimitTier.PREMIUM: 1000,
        RateLimitTier.ENTERPRISE: 5000,
    },
    # User-based limits (requests per minute)
    "user": {
        RateLimitTier.ANONYMOUS: 0,  # No user limits for anonymous
        RateLimitTier.FREE: 60,
        RateLimitTier.BASIC: 200,
        RateLimitTier.PREMIUM: 500,
        RateLimitTier.ENTERPRISE: 2000,
    },
    # Endpoint-specific limits
    "endpoint": {
        RateLimitTier.ANONYMOUS: 30,
        RateLimitTier.FREE: 60,
        RateLimitTier.BASIC: 150,
        RateLimitTier.PREMIUM: 300,
        RateLimitTier.ENTERPRISE: 1000,
    },
}


@dataclass
class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.
    
    Uses a sliding window algorithm to accurately track
    request rates over a configurable time window.
    
    Features:
    - Accurate rate limiting without burst issues
    - Configurable window size
    - Per-entity tracking
    
    Example:
        >>> limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=100)
        >>> 
        >>> # Check if request is allowed
        >>> allowed, remaining, reset = limiter.check()
        >>> if allowed:
        ...     limiter.record()
    """
    
    window_seconds: int = 60  # Sliding window size
    max_requests: int = 100  # Max requests in window
    
    def __post_init__(self):
        """Initialize the rate limiter."""
        self._timestamps: List[float] = []
        self._lock = threading.RLock()
        self._cleanup()
    
    def _cleanup(self) -> None:
        """Remove expired timestamps outside the window."""
        cutoff = time.time() - self.window_seconds
        self._timestamps = [ts for ts in self._timestamps if ts > cutoff]
    
    def check(self) -> Tuple[bool, int, float]:
        """
        Check if a request is allowed.
        
        Returns:
            Tuple of (allowed, remaining_requests, reset_timestamp).
        """
        with self._lock:
            self._cleanup()
            
            current_count = len(self._timestamps)
            remaining = max(0, self.max_requests - current_count)
            allowed = current_count < self.max_requests
            
            # Calculate reset time
            if self._timestamps:
                oldest = min(self._timestamps)
                reset_at = oldest + self.window_seconds
            else:
                reset_at = time.time() + self.window_seconds
            
            return allowed, remaining, reset_at
    
    def record(self) -> bool:
        """
        Record a request.
        
        Returns:
            True if recorded, False if rate limited.
        """
        with self._lock:
            allowed, _, _ = self.check()
            if allowed:
                self._timestamps.append(time.time())
                return True
            return False
    
    def check_and_record(self) -> Tuple[bool, int, float]:
        """
        Atomically check and record a request.
        
        Returns:
            Tuple of (allowed, remaining_requests, reset_timestamp).
        """
        with self._lock:
            allowed, remaining, reset_at = self.check()
            if allowed:
                self._timestamps.append(time.time())
                remaining = max(0, remaining - 1)
            return allowed, remaining, reset_at
    
    def reset(self) -> None:
        """Reset the rate limiter."""
        with self._lock:
            self._timestamps.clear()
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        with self._lock:
            self._cleanup()
            return {
                "current_count": len(self._timestamps),
                "max_requests": self.max_requests,
                "remaining": max(0, self.max_requests - len(self._timestamps)),
                "window_seconds": self.window_seconds,
            }


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: float
    retry_after: Optional[float] = None
    tier: str = RateLimitTier.ANONYMOUS.value
    
    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_at": datetime.fromtimestamp(self.reset_at).isoformat(),
            "retry_after": self.retry_after,
            "tier": self.tier,
        }


@dataclass
class RateLimitMetrics:
    """Rate limiting metrics."""
    total_checks: int = 0
    total_allowed: int = 0
    total_rejected: int = 0
    ip_rejected: int = 0
    user_rejected: int = 0
    endpoint_rejected: int = 0
    unique_ips: int = 0
    unique_users: int = 0
    blocked_ips: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict:
        return {
            "total_checks": self.total_checks,
            "total_allowed": self.total_allowed,
            "total_rejected": self.total_rejected,
            "ip_rejected": self.ip_rejected,
            "user_rejected": self.user_rejected,
            "endpoint_rejected": self.endpoint_rejected,
            "unique_ips": self.unique_ips,
            "unique_users": self.unique_users,
            "blocked_ips_count": len(self.blocked_ips),
        }


class RateLimitManager:
    """
    Multi-layer rate limit manager.
    
    Features:
    - IP-based rate limiting
    - User-based rate limiting
    - Endpoint-differentiated rate limiting
    - Sliding window algorithm
    - Whitelist support
    - Block list support
    
    Example:
        >>> manager = RateLimitManager()
        >>> 
        >>> # Check request
        >>> result = manager.check_request(
        ...     ip="192.168.1.1",
        ...     user_id="user123",
        ...     endpoint="/api/chat",
        ... )
        >>> 
        >>> if not result.allowed:
        ...     raise HTTPException(status_code=429, detail="Rate limited")
    """
    
    def __init__(
        self,
        window_seconds: int = 60,
        whitelist_ips: Optional[Set[str]] = None,
        blocked_ips: Optional[Set[str]] = None,
    ):
        """
        Initialize rate limit manager.
        
        Args:
            window_seconds: Sliding window size in seconds.
            whitelist_ips: Set of IPs to whitelist.
            blocked_ips: Set of IPs to block entirely.
        """
        self._window_seconds = window_seconds
        self._whitelist_ips = whitelist_ips or set()
        self._blocked_ips = blocked_ips or set()
        
        # Rate limiters
        self._ip_limiters: Dict[str, SlidingWindowRateLimiter] = {}
        self._user_limiters: Dict[str, SlidingWindowRateLimiter] = {}
        self._endpoint_limiters: Dict[str, Dict[str, SlidingWindowRateLimiter]] = defaultdict(dict)
        
        # Metrics
        self._metrics = RateLimitMetrics()
        
        # Lock
        self._lock = threading.RLock()
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def _get_ip_limiter(self, ip: str, tier: RateLimitTier) -> SlidingWindowRateLimiter:
        """Get or create IP rate limiter."""
        tier_limit = DEFAULT_LIMITS["ip"].get(tier, DEFAULT_LIMITS["ip"][RateLimitTier.ANONYMOUS])
        
        with self._lock:
            if ip not in self._ip_limiters:
                self._ip_limiters[ip] = SlidingWindowRateLimiter(
                    window_seconds=self._window_seconds,
                    max_requests=tier_limit,
                )
            return self._ip_limiters[ip]
    
    def _get_user_limiter(self, user_id: str, tier: RateLimitTier) -> SlidingWindowRateLimiter:
        """Get or create user rate limiter."""
        tier_limit = DEFAULT_LIMITS["user"].get(tier, 0)
        if tier_limit == 0:
            # Return a dummy limiter that always allows
            return SlidingWindowRateLimiter(window_seconds=1, max_requests=999999)
        
        with self._lock:
            if user_id not in self._user_limiters:
                self._user_limiters[user_id] = SlidingWindowRateLimiter(
                    window_seconds=self._window_seconds,
                    max_requests=tier_limit,
                )
            return self._user_limiters[user_id]
    
    def _get_endpoint_limiter(
        self, ip: str, endpoint: str, tier: RateLimitTier
    ) -> SlidingWindowRateLimiter:
        """Get or create endpoint rate limiter."""
        tier_limit = DEFAULT_LIMITS["endpoint"].get(tier, DEFAULT_LIMITS["endpoint"][RateLimitTier.ANONYMOUS])
        
        with self._lock:
            if endpoint not in self._endpoint_limiters[ip]:
                self._endpoint_limiters[ip][endpoint] = SlidingWindowRateLimiter(
                    window_seconds=self._window_seconds,
                    max_requests=tier_limit,
                )
            return self._endpoint_limiters[ip][endpoint]
    
    def _get_tier(self, user_id: Optional[str] = None) -> RateLimitTier:
        """Determine tier based on user ID."""
        if not user_id:
            return RateLimitTier.ANONYMOUS
        
        # Placeholder: In production, look up tier from database
        if user_id.startswith("enterprise_"):
            return RateLimitTier.ENTERPRISE
        elif user_id.startswith("premium_"):
            return RateLimitTier.PREMIUM
        elif user_id.startswith("basic_"):
            return RateLimitTier.BASIC
        elif user_id.startswith("free_"):
            return RateLimitTier.FREE
        
        return RateLimitTier.FREE
    
    def check_request(
        self,
        ip: str,
        user_id: Optional[str] = None,
        endpoint: str = "default",
    ) -> RateLimitResult:
        """
        Check if a request is allowed.
        
        Args:
            ip: Client IP address.
            user_id: Optional user ID.
            endpoint: API endpoint identifier.
        
        Returns:
            RateLimitResult with allowed status and metadata.
        """
        # Check block list
        if ip in self._blocked_ips:
            self._metrics.total_checks += 1
            self._metrics.total_rejected += 1
            self._metrics.ip_rejected += 1
            self._metrics.blocked_ips.add(ip)
            return RateLimitResult(
                allowed=False,
                limit=0,
                remaining=0,
                reset_at=time.time() + 3600,
                retry_after=3600,
                tier=RateLimitTier.ANONYMOUS.value,
            )
        
        # Check whitelist
        if ip in self._whitelist_ips:
            self._metrics.total_checks += 1
            self._metrics.total_allowed += 1
            return RateLimitResult(
                allowed=True,
                limit=0,
                remaining=999999,
                reset_at=time.time() + 3600,
                tier=RateLimitTier.ENTERPRISE.value,
            )
        
        tier = self._get_tier(user_id)
        
        # IP check
        ip_limiter = self._get_ip_limiter(ip, tier)
        ip_allowed, ip_remaining, ip_reset = ip_limiter.check()
        
        if not ip_allowed:
            self._metrics.total_checks += 1
            self._metrics.total_rejected += 1
            self._metrics.ip_rejected += 1
            self._metrics.unique_ips = max(self._metrics.unique_ips, len(self._ip_limiters))
            return RateLimitResult(
                allowed=False,
                limit=ip_limiter.max_requests,
                remaining=0,
                reset_at=ip_reset,
                retry_after=ip_reset - time.time(),
                tier=tier.value,
            )
        
        # User check (if authenticated)
        if user_id:
            user_limiter = self._get_user_limiter(user_id, tier)
            user_allowed, user_remaining, user_reset = user_limiter.check()
            
            if not user_allowed:
                self._metrics.total_checks += 1
                self._metrics.total_rejected += 1
                self._metrics.user_rejected += 1
                self._metrics.unique_users = max(self._metrics.unique_users, len(self._user_limiters))
                return RateLimitResult(
                    allowed=False,
                    limit=user_limiter.max_requests,
                    remaining=0,
                    reset_at=user_reset,
                    retry_after=user_reset - time.time(),
                    tier=tier.value,
                )
        
        # Endpoint check
        endpoint_limiter = self._get_endpoint_limiter(ip, endpoint, tier)
        endpoint_allowed, endpoint_remaining, endpoint_reset = endpoint_limiter.check()
        
        if not endpoint_allowed:
            self._metrics.total_checks += 1
            self._metrics.total_rejected += 1
            self._metrics.endpoint_rejected += 1
            return RateLimitResult(
                allowed=False,
                limit=endpoint_limiter.max_requests,
                remaining=0,
                reset_at=endpoint_reset,
                retry_after=endpoint_reset - time.time(),
                tier=tier.value,
            )
        
        # All checks passed
        self._metrics.total_checks += 1
        self._metrics.total_allowed += 1
        self._metrics.unique_ips = max(self._metrics.unique_ips, len(self._ip_limiters))
        if user_id:
            self._metrics.unique_users = max(self._metrics.unique_users, len(self._user_limiters))
        
        return RateLimitResult(
            allowed=True,
            limit=endpoint_limiter.max_requests,
            remaining=endpoint_remaining,
            reset_at=endpoint_reset,
            tier=tier.value,
        )
    
    def record_request(
        self,
        ip: str,
        user_id: Optional[str] = None,
        endpoint: str = "default",
    ) -> RateLimitResult:
        """
        Record a request and check limits atomically.
        
        Args:
            ip: Client IP address.
            user_id: Optional user ID.
            endpoint: API endpoint identifier.
        
        Returns:
            RateLimitResult with allowed status and metadata.
        """
        tier = self._get_tier(user_id)
        
        # IP check and record
        ip_limiter = self._get_ip_limiter(ip, tier)
        ip_allowed, ip_remaining, ip_reset = ip_limiter.check_and_record()
        
        if not ip_allowed:
            return RateLimitResult(
                allowed=False,
                limit=ip_limiter.max_requests,
                remaining=0,
                reset_at=ip_reset,
                retry_after=ip_reset - time.time(),
                tier=tier.value,
            )
        
        # User check (if authenticated)
        if user_id:
            user_limiter = self._get_user_limiter(user_id, tier)
            user_allowed, user_remaining, user_reset = user_limiter.check_and_record()
            
            if not user_allowed:
                return RateLimitResult(
                    allowed=False,
                    limit=user_limiter.max_requests,
                    remaining=0,
                    reset_at=user_reset,
                    retry_after=user_reset - time.time(),
                    tier=tier.value,
                )
        
        # Endpoint check and record
        endpoint_limiter = self._get_endpoint_limiter(ip, endpoint, tier)
        endpoint_allowed, endpoint_remaining, endpoint_reset = endpoint_limiter.check_and_record()
        
        if not endpoint_allowed:
            return RateLimitResult(
                allowed=False,
                limit=endpoint_limiter.max_requests,
                remaining=0,
                reset_at=endpoint_reset,
                retry_after=endpoint_reset - time.time(),
                tier=tier.value,
            )
        
        return RateLimitResult(
            allowed=True,
            limit=endpoint_limiter.max_requests,
            remaining=endpoint_remaining,
            reset_at=endpoint_reset,
            tier=tier.value,
        )
    
    def block_ip(self, ip: str) -> None:
        """Block an IP address."""
        with self._lock:
            self._blocked_ips.add(ip)
            if ip in self._ip_limiters:
                self._ip_limiters[ip].reset()
    
    def unblock_ip(self, ip: str) -> None:
        """Unblock an IP address."""
        with self._lock:
            self._blocked_ips.discard(ip)
    
    def add_whitelist(self, ip: str) -> None:
        """Add an IP to the whitelist."""
        self._whitelist_ips.add(ip)
    
    def remove_whitelist(self, ip: str) -> None:
        """Remove an IP from the whitelist."""
        self._whitelist_ips.discard(ip)
    
    def get_metrics(self) -> RateLimitMetrics:
        """Get rate limiting metrics."""
        return self._metrics
    
    def reset_metrics(self) -> None:
        """Reset metrics."""
        self._metrics = RateLimitMetrics()
    
    async def cleanup_loop(self, interval: int = 300) -> None:
        """
        Periodic cleanup of old rate limiters.
        
        Args:
            interval: Cleanup interval in seconds.
        """
        while True:
            await asyncio.sleep(interval)
            
            with self._lock:
                # Remove old IP limiters (not used recently)
                cutoff = time.time() - 3600  # 1 hour
                to_remove = []
                
                for ip, limiter in self._ip_limiters.items():
                    if not limiter._timestamps or max(limiter._timestamps) < cutoff:
                        to_remove.append(ip)
                
                for ip in to_remove:
                    del self._ip_limiters[ip]
                
                # Remove old user limiters
                to_remove = []
                for user_id, limiter in self._user_limiters.items():
                    if not limiter._timestamps or max(limiter._timestamps) < cutoff:
                        to_remove.append(user_id)
                
                for user_id in to_remove:
                    del self._user_limiters[user_id]
                
                # Clear endpoint limiters
                self._endpoint_limiters.clear()
                
                logger.debug(f"Rate limit cleanup: removed {len(to_remove)} IP limiters, {len(to_remove)} user limiters")
    
    def shutdown(self) -> None:
        """Shutdown the rate limit manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()


# Global rate limit manager instance
_rate_limit_manager: Optional[RateLimitManager] = None
_manager_lock = threading.Lock()


def get_rate_limit_manager() -> RateLimitManager:
    """Get the global rate limit manager instance."""
    global _rate_limit_manager
    
    with _manager_lock:
        if _rate_limit_manager is None:
            _rate_limit_manager = RateLimitManager()
        return _rate_limit_manager


def reset_rate_limit_manager() -> None:
    """Reset the global rate limit manager (for testing)."""
    global _rate_limit_manager
    
    with _manager_lock:
        if _rate_limit_manager is not None:
            _rate_limit_manager.shutdown()
            _rate_limit_manager = None
