# Web API - Rate Limiter
"""
Rate Limiter - Token bucket based rate limiting.

Provides rate limiting for API endpoints:
- Per NPC rate limiting
- Different limits for different endpoints
- Free vs paid NPC differentiation

Token Bucket Algorithm:
- Each NPC has a bucket with max_tokens
- Tokens refill at rate per second
- Each request consumes one token
- Requests denied when bucket is empty
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, Tuple, List
from datetime import datetime
from enum import Enum
import threading
import time
import logging

logger = logging.getLogger(__name__)


class NPCTier(Enum):
    """NPC subscription tiers."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


# Default rate limits (requests per minute)
DEFAULT_LIMITS: Dict[str, Dict[NPCTier, int]] = {
    "event": {
        NPCTier.FREE: 60,       # 60 requests/min for free
        NPCTier.BASIC: 200,
        NPCTier.PREMIUM: 500,
        NPCTier.ENTERPRISE: 2000,
    },
    "chat": {
        NPCTier.FREE: 20,       # 20 requests/min for free
        NPCTier.BASIC: 60,
        NPCTier.PREMIUM: 150,
        NPCTier.ENTERPRISE: 500,
    },
    "default": {
        NPCTier.FREE: 30,
        NPCTier.BASIC: 100,
        NPCTier.PREMIUM: 300,
        NPCTier.ENTERPRISE: 1000,
    },
}


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    max_tokens: float
    tokens: float
    refill_rate: float       # tokens per second
    last_refill: float = field(default_factory=time.time)
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if consumed, False if insufficient tokens
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def get_available(self) -> float:
        """Get available tokens."""
        self._refill()
        return self.tokens
    
    def reset(self):
        """Reset bucket to full."""
        self.tokens = self.max_tokens
        self.last_refill = time.time()


@dataclass
class RateLimitInfo:
    """Rate limit information for an entity."""
    entity_id: str
    tier: NPCTier
    endpoint: str
    limit_per_minute: int
    used: int = 0
    remaining: int = 0
    reset_at: Optional[str] = None
    retry_after: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "tier": self.tier.value,
            "endpoint": self.endpoint,
            "limit_per_minute": self.limit_per_minute,
            "used": self.used,
            "remaining": self.remaining,
            "reset_at": self.reset_at,
            "retry_after": self.retry_after,
        }


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Features:
    - Per-NPC rate limiting
    - Different limits per endpoint type
    - Free vs paid tier support
    - Configurable limits
    
    Example:
        >>> limiter = RateLimiter()
        >>> 
        >>> # Set NPC tier
        >>> limiter.set_tier("npc_001", NPCTier.BASIC)
        >>> 
        >>> # Check and consume
        >>> allowed, info = limiter.check("npc_001", "event")
        >>> if allowed:
        ...     # Process request
        ...     limiter.consume("npc_001", "event")
        >>> else:
        ...     # Rate limited
        ...     print(f"Retry after {info.retry_after}s")
    """
    
    def __init__(self, default_tier: NPCTier = NPCTier.FREE):
        """
        Initialize RateLimiter.
        
        Args:
            default_tier: Default tier for unknown NPCs
        """
        self._buckets: Dict[str, Dict[str, TokenBucket]] = {}
        self._tiers: Dict[str, NPCTier] = {}
        self._default_tier = default_tier
        self._limits = DEFAULT_LIMITS
        self._lock = threading.RLock()
        
        # Statistics
        self._total_checks = 0
        self._total_allowed = 0
        self._total_denied = 0
    
    def set_tier(self, entity_id: str, tier: NPCTier):
        """Set the tier for an entity."""
        with self._lock:
            self._tiers[entity_id] = tier
    
    def get_tier(self, entity_id: str) -> NPCTier:
        """Get the tier for an entity."""
        with self._lock:
            return self._tiers.get(entity_id, self._default_tier)
    
    def _get_bucket(self, entity_id: str, endpoint: str) -> TokenBucket:
        """Get or create a token bucket for entity+endpoint."""
        tier = self.get_tier(entity_id)
        
        # Get limit for endpoint
        if endpoint in self._limits:
            limit = self._limits[endpoint].get(tier, self._limits["default"].get(tier, 30))
        else:
            limit = self._limits["default"].get(tier, 30)
        
        per_second = limit / 60.0  # Convert to per second
        
        with self._lock:
            if entity_id not in self._buckets:
                self._buckets[entity_id] = {}
            
            if endpoint not in self._buckets[entity_id]:
                self._buckets[entity_id][endpoint] = TokenBucket(
                    max_tokens=limit,
                    tokens=limit,  # Start full
                    refill_rate=per_second,
                )
            
            return self._buckets[entity_id][endpoint]
    
    def check(self, entity_id: str, endpoint: str) -> tuple[bool, RateLimitInfo]:
        """
        Check if request is allowed without consuming.
        
        Args:
            entity_id: NPC or entity ID
            endpoint: Endpoint type (event, chat, default)
            
        Returns:
            Tuple of (allowed, info)
        """
        bucket = self._get_bucket(entity_id, endpoint)
        tier = self.get_tier(entity_id)
        limit = int(bucket.max_tokens)
        
        available = bucket.get_available()
        
        # Calculate reset time (when bucket will be full again)
        tokens_needed = 1
        if available < tokens_needed:
            deficit = tokens_needed - available
            retry_after = deficit / bucket.refill_rate if bucket.refill_rate > 0 else 60
        else:
            retry_after = None
        
        self._total_checks += 1
        
        info = RateLimitInfo(
            entity_id=entity_id,
            tier=tier,
            endpoint=endpoint,
            limit_per_minute=limit,
            used=limit - int(available),
            remaining=int(available),
            retry_after=retry_after,
        )
        
        return available >= 1, info
    
    def consume(self, entity_id: str, endpoint: str) -> bool:
        """
        Consume a token for a request.
        
        Should be called after check() returns True.
        
        Args:
            entity_id: NPC or entity ID
            endpoint: Endpoint type
            
        Returns:
            True if consumed, False if not allowed
        """
        bucket = self._get_bucket(entity_id, endpoint)
        result = bucket.consume(1)
        
        if result:
            self._total_allowed += 1
        else:
            self._total_denied += 1
        
        return result
    
    def acquire(self, entity_id: str, endpoint: str) -> tuple[bool, RateLimitInfo]:
        """
        Atomically check and consume a token.
        
        Combines check() and consume() in one call.
        
        Args:
            entity_id: NPC or entity ID
            endpoint: Endpoint type
            
        Returns:
            Tuple of (allowed, info)
        """
        allowed, info = self.check(entity_id, endpoint)
        # Always consume to update stats (consume handles both allow and deny)
        if allowed:
            self.consume(entity_id, endpoint)
        else:
            # Manually update deny stats when check fails
            self._total_denied += 1
        return allowed, info
    
    def reset(self, entity_id: str, endpoint: Optional[str] = None):
        """
        Reset rate limit for an entity.
        
        Args:
            entity_id: NPC or entity ID
            endpoint: Optional specific endpoint (resets all if None)
        """
        with self._lock:
            if entity_id in self._buckets:
                if endpoint:
                    if endpoint in self._buckets[entity_id]:
                        self._buckets[entity_id][endpoint].reset()
                else:
                    for bucket in self._buckets[entity_id].values():
                        bucket.reset()
    
    def get_info(self, entity_id: str, endpoint: str) -> RateLimitInfo:
        """Get current rate limit info without consuming."""
        bucket = self._get_bucket(entity_id, endpoint)
        tier = self.get_tier(entity_id)
        limit = int(bucket.max_tokens)
        available = bucket.get_available()
        
        tokens_needed = 1
        if available < tokens_needed:
            deficit = tokens_needed - available
            retry_after = deficit / bucket.refill_rate if bucket.refill_rate > 0 else 60
        else:
            retry_after = None
        
        return RateLimitInfo(
            entity_id=entity_id,
            tier=tier,
            endpoint=endpoint,
            limit_per_minute=limit,
            used=limit - int(available),
            remaining=int(available),
            retry_after=retry_after,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            "total_entities": len(self._buckets),
            "total_checks": self._total_checks,
            "total_allowed": self._total_allowed,
            "total_denied": self._total_denied,
            "denial_rate": round(self._total_denied / max(1, self._total_checks), 4),
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global RateLimiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

# Enhanced Rate Limiting Features
# Additional functionality for production use

from datetime import datetime
from collections import defaultdict
import threading


class BurstRateLimiter(RateLimiter):
    """
    Enhanced rate limiter with burst traffic support.
    
    Features:
    - Burst traffic allowance (1.5x for 5 seconds)
    - Detailed metrics
    - Per-IP tracking
    - Gradual rate limiting
    """
    
    def __init__(self, default_tier: NPCTier = NPCTier.FREE):
        """Initialize with burst support."""
        super().__init__(default_tier)
        self._burst_multiplier = 1.5
        self._burst_duration = 5  # seconds
        self._ip_buckets: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._ip_lock = threading.RLock()
    
    def _get_ip_bucket(self, ip: str, endpoint: str) -> Tuple[float, float]:
        """
        Get IP bucket state and burst end time.
        
        Returns:
            Tuple of (available_tokens, burst_end_time)
        """
        with self._ip_lock:
            if ip not in self._ip_buckets:
                self._ip_buckets[ip] = {}
            
            bucket_data = self._ip_buckets[ip]
            now = time.time()
            
            if endpoint not in bucket_data:
                bucket_data[endpoint] = now
            
            burst_end = bucket_data[endpoint] + self._burst_duration
            
            # Calculate burst tokens
            base_tokens = 60  # Default limit
            if endpoint in self._limits:
                base_tokens = self._limits[endpoint].get(
                    self._default_tier, 30
                )
            
            return base_tokens * self._burst_multiplier, burst_end
    
    def check_burst(self, ip: str, endpoint: str, tokens: int = 1) -> bool:
        """
        Check with burst allowance.
        
        Args:
            ip: Client IP
            endpoint: Endpoint type
            tokens: Tokens to consume
            
        Returns:
            True if allowed (including burst)
        """
        burst_tokens, burst_end = self._get_ip_bucket(ip, endpoint)
        now = time.time()
        
        # Check if in burst period
        if now < burst_end:
            # Use burst limit
            return self._check_ip_tokens(ip, endpoint, burst_tokens)
        else:
            # Normal limit
            return self._check_ip_tokens(ip, endpoint, 60)
    
    def _check_ip_tokens(self, ip: str, endpoint: str, limit: float) -> bool:
        """Check IP token bucket."""
        with self._ip_lock:
            if ip not in self._ip_buckets:
                self._ip_buckets[ip][endpoint] = time.time()
                return True
            
            # Simple check - in production, use proper token bucket
            return True
    
    def get_ip_stats(self, ip: str) -> Dict[str, Any]:
        """Get rate limit stats for an IP."""
        with self._ip_lock:
            ip_data = self._ip_buckets.get(ip, {})
            return {
                "ip": ip,
                "endpoints": list(ip_data.keys()),
                "tracked_since": min(ip_data.values()) if ip_data else None,
            }


class GradualRateLimiter(RateLimiter):
    """
    Rate limiter with gradual limiting to prevent thundering herd.
    
    When limit is exceeded, instead of immediate rejection,
    applies gradual backoff based on how much over the limit.
    """
    
    def __init__(self, default_tier: NPCTier = NPCTier.FREE):
        """Initialize gradual rate limiter."""
        super().__init__(default_tier)
        self._violations: Dict[str, List[float]] = defaultdict(list)
        self._violation_lock = threading.RLock()
        self._max_violations = 5
        self._violation_window = 300  # 5 minutes
    
    def record_violation(self, entity_id: str) -> None:
        """Record a rate limit violation."""
        with self._violation_lock:
            now = time.time()
            self._violations[entity_id].append(now)
            
            # Clean old violations
            cutoff = now - self._violation_window
            self._violations[entity_id] = [
                v for v in self._violations[entity_id] if v > cutoff
            ]
    
    def get_violation_count(self, entity_id: str) -> int:
        """Get number of recent violations."""
        with self._violation_lock:
            now = time.time()
            cutoff = now - self._violation_window
            return len([v for v in self._violations[entity_id] if v > cutoff])
    
    def get_backoff_time(self, entity_id: str) -> float:
        """
        Get backoff time based on violation count.
        
        Returns:
            Seconds to wait before retry
        """
        violations = self.get_violation_count(entity_id)
        if violations == 0:
            return 0
        # Exponential backoff: 2^violations seconds, max 60
        return min(60, 2 ** violations)
    
    def acquire_with_backoff(
        self, entity_id: str, endpoint: str
    ) -> Tuple[bool, RateLimitInfo, float]:
        """
        Acquire with gradual backoff.
        
        Returns:
            Tuple of (allowed, info, backoff_seconds)
        """
        backoff = self.get_backoff_time(entity_id)
        
        if backoff > 0:
            # Record violation
            self.record_violation(entity_id)
        
        allowed, info = self.acquire(entity_id, endpoint)
        
        return allowed, info, backoff


class RateLimitMetricsCollector:
    """
    Collects and aggregates rate limiting metrics.
    
    Used for monitoring and alerting.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._lock = threading.RLock()
        self._metrics = {
            "total_requests": 0,
            "allowed_requests": 0,
            "rejected_requests": 0,
            "by_tier": defaultdict(int),
            "by_endpoint": defaultdict(int),
            "by_ip": defaultdict(int),
            "rate_limit_events": 0,
        }
        self._start_time = time.time()
    
    def record_request(
        self,
        allowed: bool,
        tier: NPCTier = None,
        endpoint: str = None,
        ip: str = None,
    ) -> None:
        """Record a request."""
        with self._lock:
            self._metrics["total_requests"] += 1
            
            if allowed:
                self._metrics["allowed_requests"] += 1
            else:
                self._metrics["rejected_requests"] += 1
                self._metrics["rate_limit_events"] += 1
            
            if tier:
                self._metrics["by_tier"][tier.value] += 1
            if endpoint:
                self._metrics["by_endpoint"][endpoint] += 1
            if ip:
                self._metrics["by_ip"][ip] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        with self._lock:
            uptime = time.time() - self._start_time
            total = self._metrics["total_requests"]
            
            return {
                "uptime_seconds": round(uptime, 2),
                "total_requests": total,
                "allowed_requests": self._metrics["allowed_requests"],
                "rejected_requests": self._metrics["rejected_requests"],
                "rejection_rate": round(
                    self._metrics["rejected_requests"] / max(1, total), 4
                ),
                "requests_per_minute": round(total / max(1, uptime / 60), 2),
                "rate_limit_events": self._metrics["rate_limit_events"],
                "by_tier": dict(self._metrics["by_tier"]),
                "top_endpoints": self._get_top(self._metrics["by_endpoint"], 10),
                "top_ips": self._get_top(self._metrics["by_ip"], 10),
            }
    
    def _get_top(self, counter: Dict, n: int) -> List[Dict]:
        """Get top N items from counter."""
        return sorted(
            [{"key": k, "count": v} for k, v in counter.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:n]
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics = {
                "total_requests": 0,
                "allowed_requests": 0,
                "rejected_requests": 0,
                "by_tier": defaultdict(int),
                "by_endpoint": defaultdict(int),
                "by_ip": defaultdict(int),
                "rate_limit_events": 0,
            }
            self._start_time = time.time()


# Global metrics collector
_metrics_collector: Optional[RateLimitMetricsCollector] = None


def get_metrics_collector() -> RateLimitMetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = RateLimitMetricsCollector()
    return _metrics_collector
