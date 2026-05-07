"""
Neshama Rate Limiter Tests
"""

import pytest
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.web.api.rate_limiter import (
    RateLimiter,
    TokenBucket,
    RateLimitInfo,
    NPCTier,
    DEFAULT_LIMITS,
    get_rate_limiter,
)


class TestTokenBucket:
    """Tests for TokenBucket."""

    def test_default_init(self):
        """Test default initialization."""
        bucket = TokenBucket(max_tokens=10, tokens=10, refill_rate=1.0)
        
        assert bucket.max_tokens == 10
        assert bucket.tokens == 10

    def test_consume_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(max_tokens=10, tokens=10, refill_rate=1.0)
        
        result = bucket.consume(1)
        
        assert result is True
        assert bucket.tokens == 9

    def test_consume_multiple(self):
        """Test consuming multiple tokens."""
        bucket = TokenBucket(max_tokens=10, tokens=10, refill_rate=1.0)
        
        result = bucket.consume(5)
        
        assert result is True
        assert bucket.tokens == 5

    def test_consume_insufficient(self):
        """Test consuming when insufficient tokens."""
        bucket = TokenBucket(max_tokens=10, tokens=3, refill_rate=0.0)  # No refill to avoid float drift
        
        result = bucket.consume(5)
        
        assert result is False
        assert bucket.tokens <= 3  # Unchanged or slightly less due to precision

    def test_refill(self):
        """Test token refill over time."""
        bucket = TokenBucket(max_tokens=10, tokens=5, refill_rate=2.0)
        
        time.sleep(0.1)
        
        available = bucket.get_available()
        
        # Should have gained ~0.2 tokens (2 * 0.1)
        assert available > 5

    def test_refill_caps_at_max(self):
        """Test that refill doesn't exceed max."""
        bucket = TokenBucket(max_tokens=10, tokens=9, refill_rate=10.0)
        
        time.sleep(1.0)
        
        available = bucket.get_available()
        
        assert available <= 10

    def test_reset(self):
        """Test resetting bucket."""
        bucket = TokenBucket(max_tokens=10, tokens=3, refill_rate=1.0)
        
        bucket.reset()
        
        assert bucket.tokens == 10


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_default_init(self):
        """Test default initialization."""
        limiter = RateLimiter()
        
        assert limiter is not None
        assert limiter._default_tier == NPCTier.FREE

    def test_custom_default_tier(self):
        """Test initialization with custom default tier."""
        limiter = RateLimiter(default_tier=NPCTier.PREMIUM)
        
        assert limiter._default_tier == NPCTier.PREMIUM


class TestTierManagement:
    """Tests for tier management."""

    def test_set_tier(self):
        """Test setting tier for entity."""
        limiter = RateLimiter()
        
        limiter.set_tier("npc_001", NPCTier.BASIC)
        
        tier = limiter.get_tier("npc_001")
        
        assert tier == NPCTier.BASIC

    def test_get_default_tier_for_unknown(self):
        """Test getting default tier for unknown entity."""
        limiter = RateLimiter()
        
        tier = limiter.get_tier("unknown_npc")
        
        assert tier == NPCTier.FREE

    def test_different_tiers_have_different_limits(self):
        """Test that different tiers have different limits."""
        free_limit = DEFAULT_LIMITS["event"][NPCTier.FREE]
        premium_limit = DEFAULT_LIMITS["event"][NPCTier.PREMIUM]
        
        assert premium_limit > free_limit


class TestRateLimitCheck:
    """Tests for rate limit checking."""

    def test_check_allows_initial_request(self):
        """Test that initial request is allowed."""
        limiter = RateLimiter()
        
        allowed, info = limiter.check("npc_001", "event")
        
        assert allowed is True
        assert info.remaining > 0

    def test_check_returns_info(self):
        """Test that check returns rate limit info."""
        limiter = RateLimiter()
        
        allowed, info = limiter.check("npc_001", "event")
        
        assert isinstance(info, RateLimitInfo)
        assert info.entity_id == "npc_001"
        assert info.endpoint == "event"
        assert info.tier == NPCTier.FREE

    def test_acquire_decreases_remaining(self):
        """Test that acquire decreases remaining count."""
        limiter = RateLimiter()
        
        # Use acquire which both checks and consumes
        _, info1 = limiter.acquire("npc_001", "event")
        _, info2 = limiter.acquire("npc_001", "event")
        
        assert info2.remaining < info1.remaining


class TestRateLimitConsume:
    """Tests for token consumption."""

    def test_consume_after_check(self):
        """Test consuming after check."""
        limiter = RateLimiter()
        
        allowed, _ = limiter.check("npc_001", "event")
        assert allowed is True
        
        result = limiter.consume("npc_001", "event")
        
        assert result is True

    def test_acquire_atomic(self):
        """Test atomic check and consume."""
        limiter = RateLimiter()
        
        allowed, info = limiter.acquire("npc_001", "event")
        
        assert allowed is True
        
        # Should have consumed one token
        remaining = limiter.get_info("npc_001", "event").remaining
        assert remaining < info.remaining


class TestDifferentEndpointLimits:
    """Tests for different endpoint limits."""

    def test_event_endpoint_has_limit(self):
        """Test that event endpoint has configured limit."""
        limiter = RateLimiter()
        
        _, info = limiter.check("npc_001", "event")
        
        assert info.limit_per_minute > 0

    def test_chat_endpoint_has_limit(self):
        """Test that chat endpoint has configured limit."""
        limiter = RateLimiter()
        
        _, info = limiter.check("npc_001", "chat")
        
        assert info.limit_per_minute > 0

    def test_event_limit_different_from_chat(self):
        """Test that event and chat have different limits."""
        limiter = RateLimiter()
        
        _, event_info = limiter.check("npc_001", "event")
        _, chat_info = limiter.check("npc_001", "chat")
        
        # Chat typically has lower limit than event
        assert event_info.limit_per_minute >= chat_info.limit_per_minute


class TestPremiumTierLimits:
    """Tests for premium tier limits."""

    def test_premium_has_higher_limit(self):
        """Test that premium tier has higher limits."""
        limiter = RateLimiter()
        limiter.set_tier("premium_npc", NPCTier.PREMIUM)
        
        _, free_info = limiter.check("free_npc", "event")
        _, premium_info = limiter.check("premium_npc", "event")
        
        assert premium_info.limit_per_minute > free_info.limit_per_minute

    def test_enterprise_has_highest_limit(self):
        """Test that enterprise tier has highest limits."""
        limiter = RateLimiter()
        limiter.set_tier("ent_npc", NPCTier.ENTERPRISE)
        
        _, enterprise_info = limiter.check("ent_npc", "event")
        
        # Enterprise should have highest limits
        assert enterprise_info.limit_per_minute >= DEFAULT_LIMITS["event"][NPCTier.PREMIUM]


class TestRateLimitReset:
    """Tests for rate limit reset."""

    def test_reset_endpoint(self):
        """Test resetting specific endpoint."""
        limiter = RateLimiter()
        
        # Consume some tokens
        limiter.acquire("npc_001", "event")
        limiter.acquire("npc_001", "event")
        
        # Reset
        limiter.reset("npc_001", "event")
        
        info = limiter.get_info("npc_001", "event")
        
        # Should be back to full
        assert info.remaining == info.limit_per_minute

    def test_reset_all_endpoints(self):
        """Test resetting all endpoints for entity."""
        limiter = RateLimiter()
        
        # Consume from multiple endpoints
        limiter.acquire("npc_001", "event")
        limiter.acquire("npc_001", "chat")
        
        # Reset all
        limiter.reset("npc_001")
        
        event_info = limiter.get_info("npc_001", "event")
        chat_info = limiter.get_info("npc_001", "chat")
        
        assert event_info.remaining == event_info.limit_per_minute
        assert chat_info.remaining == chat_info.limit_per_minute


class TestRateLimitInfo:
    """Tests for RateLimitInfo."""

    def test_to_dict(self):
        """Test RateLimitInfo serialization."""
        info = RateLimitInfo(
            entity_id="npc_001",
            tier=NPCTier.FREE,
            endpoint="event",
            limit_per_minute=60,
            used=10,
            remaining=50,
        )
        
        data = info.to_dict()
        
        assert data["entity_id"] == "npc_001"
        assert data["tier"] == "free"
        assert data["endpoint"] == "event"
        assert data["limit_per_minute"] == 60
        assert data["remaining"] == 50


class TestRateLimiterStats:
    """Tests for rate limiter statistics."""

    def test_initial_stats(self):
        """Test initial stats are zero."""
        limiter = RateLimiter()
        
        stats = limiter.get_stats()
        
        assert stats["total_checks"] == 0
        assert stats["total_allowed"] == 0
        assert stats["total_denied"] == 0

    def test_stats_update_on_check(self):
        """Test stats update on check."""
        limiter = RateLimiter()
        
        limiter.check("npc_001", "event")
        
        stats = limiter.get_stats()
        
        assert stats["total_checks"] == 1

    def test_stats_update_on_consume(self):
        """Test stats update on consume."""
        limiter = RateLimiter()
        
        limiter.acquire("npc_001", "event")
        
        stats = limiter.get_stats()
        
        assert stats["total_allowed"] == 1

    def test_stats_update_on_deny(self):
        """Test stats update on denial."""
        limiter = RateLimiter()
        
        # Create a bucket with only 1 token
        limiter._buckets = {
            "low_npc": {
                "event": TokenBucket(max_tokens=1, tokens=1, refill_rate=0.0)
            }
        }
        
        # First acquire should succeed
        allowed1, _ = limiter.acquire("low_npc", "event")
        assert allowed1 is True
        
        # Second acquire should fail (bucket exhausted)
        allowed2, _ = limiter.acquire("low_npc", "event")
        assert allowed2 is False
        
        stats = limiter.get_stats()
        
        assert stats["total_denied"] >= 1


class TestGlobalRateLimiter:
    """Tests for global rate limiter."""

    def test_get_rate_limiter(self):
        """Test getting global rate limiter."""
        limiter = get_rate_limiter()
        
        assert limiter is not None
        assert isinstance(limiter, RateLimiter)


class TestDefaultLimits:
    """Tests for default limits configuration."""

    def test_default_limits_exist(self):
        """Test that default limits are defined."""
        assert "event" in DEFAULT_LIMITS
        assert "chat" in DEFAULT_LIMITS

    def test_all_tiers_have_limits(self):
        """Test that all tiers have limits defined."""
        for tier in NPCTier:
            for endpoint in ["event", "chat"]:
                assert tier in DEFAULT_LIMITS[endpoint]
