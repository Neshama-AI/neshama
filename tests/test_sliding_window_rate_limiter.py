# Test Enhanced Rate Limiting with Sliding Window
"""
Tests for enhanced rate limiting with sliding window algorithm.
"""

import time
from unittest.mock import patch, MagicMock

import pytest


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter."""
    
    def test_init(self):
        """Test limiter initialization."""
        from neshama.web.rate_limit import SlidingWindowRateLimiter
        
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=100)
        
        assert limiter.window_seconds == 60
        assert limiter.max_requests == 100
    
    def test_check_allows_within_limit(self):
        """Test check allows requests within limit."""
        from neshama.web.rate_limit import SlidingWindowRateLimiter
        
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=10)
        
        allowed, remaining, reset_at = limiter.check()
        
        assert allowed is True
        assert remaining == 10
    
    def test_record_increments_count(self):
        """Test that record increments request count."""
        from neshama.web.rate_limit import SlidingWindowRateLimiter
        
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=10)
        
        limiter.record()
        limiter.record()
        
        allowed, remaining, _ = limiter.check()
        
        assert allowed is True
        assert remaining == 8
    
    def test_check_denies_over_limit(self):
        """Test check denies when over limit."""
        from neshama.web.rate_limit import SlidingWindowRateLimiter
        
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=3)
        
        # Exhaust the limit
        limiter.record()
        limiter.record()
        limiter.record()
        
        allowed, remaining, _ = limiter.check()
        
        assert allowed is False
        assert remaining == 0
    
    def test_check_and_record_atomic(self):
        """Test atomic check and record."""
        from neshama.web.rate_limit import SlidingWindowRateLimiter
        
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=5)
        
        # First request
        allowed, remaining, _ = limiter.check_and_record()
        
        assert allowed is True
        assert remaining == 4
        
        # Exhaust remaining
        for _ in range(4):
            limiter.check_and_record()
        
        # Should be denied
        allowed, remaining, _ = limiter.check_and_record()
        assert allowed is False
    
    def test_reset(self):
        """Test reset clears all timestamps."""
        from neshama.web.rate_limit import SlidingWindowRateLimiter
        
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=10)
        
        limiter.record()
        limiter.record()
        
        limiter.reset()
        
        allowed, remaining, _ = limiter.check()
        assert allowed is True
        assert remaining == 10
    
    def test_get_stats(self):
        """Test getting statistics."""
        from neshama.web.rate_limit import SlidingWindowRateLimiter
        
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=10)
        
        limiter.record()
        limiter.record()
        
        stats = limiter.get_stats()
        
        assert stats["current_count"] == 2
        assert stats["max_requests"] == 10
        assert stats["remaining"] == 8


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        from neshama.web.rate_limit import RateLimitResult
        from datetime import datetime
        
        result = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=50,
            reset_at=time.time() + 60,
            tier="premium",
        )
        
        data = result.to_dict()
        
        assert data["allowed"] is True
        assert data["limit"] == 100
        assert data["remaining"] == 50
        assert data["tier"] == "premium"
        assert "reset_at" in data


class TestRateLimitManager:
    """Tests for RateLimitManager class."""
    
    def test_init(self):
        """Test manager initialization."""
        from neshama.web.rate_limit import RateLimitManager
        
        manager = RateLimitManager()
        
        assert manager is not None
        assert manager._window_seconds == 60
    
    def test_check_request_allows_new_ip(self):
        """Test checking request from new IP."""
        from neshama.web.rate_limit import RateLimitManager
        
        manager = RateLimitManager()
        
        result = manager.check_request(ip="192.168.1.1")
        
        assert result.allowed is True
    
    def test_check_request_blocks_unknown_ip(self):
        """Test that unknown IPs are allowed."""
        from neshama.web.rate_limit import RateLimitManager
        
        manager = RateLimitManager()
        
        result = manager.check_request(ip="unknown")
        
        # Unknown IPs should be allowed (anonymous tier)
        assert result.allowed is True
    
    def test_check_request_blocks_blocked_ip(self):
        """Test that blocked IPs are denied."""
        from neshama.web.rate_limit import RateLimitManager
        
        manager = RateLimitManager()
        manager.block_ip("192.168.1.100")
        
        result = manager.check_request(ip="192.168.1.100")
        
        assert result.allowed is False
    
    def test_record_request_allows(self):
        """Test recording a request."""
        from neshama.web.rate_limit import RateLimitManager
        
        manager = RateLimitManager()
        
        result = manager.record_request(ip="192.168.1.1", endpoint="/api/chat")
        
        assert result.allowed is True
    
    def test_whitelist_allows(self):
        """Test that whitelisted IPs bypass limits."""
        from neshama.web.rate_limit import RateLimitManager
        
        manager = RateLimitManager()
        manager.add_whitelist("192.168.1.200")
        
        result = manager.check_request(ip="192.168.1.200")
        
        assert result.allowed is True
    
    def test_block_and_unblock_ip(self):
        """Test blocking and unblocking IPs."""
        from neshama.web.rate_limit import RateLimitManager
        
        manager = RateLimitManager()
        
        # Block
        manager.block_ip("192.168.1.1")
        result = manager.check_request(ip="192.168.1.1")
        assert result.allowed is False
        
        # Unblock
        manager.unblock_ip("192.168.1.1")
        result = manager.check_request(ip="192.168.1.1")
        assert result.allowed is True
    
    def test_get_metrics(self):
        """Test getting metrics."""
        from neshama.web.rate_limit import RateLimitManager
        
        manager = RateLimitManager()
        
        # Make some requests
        manager.check_request(ip="192.168.1.1")
        manager.check_request(ip="192.168.1.2")
        
        metrics = manager.get_metrics()
        
        assert metrics.total_checks >= 2
        assert metrics.total_allowed >= 2
    
    def test_reset_metrics(self):
        """Test resetting metrics."""
        from neshama.web.rate_limit import RateLimitManager
        
        manager = RateLimitManager()
        manager.check_request(ip="192.168.1.1")
        
        manager.reset_metrics()
        
        metrics = manager.get_metrics()
        assert metrics.total_checks == 0


class TestRateLimitTier:
    """Tests for RateLimitTier enum."""
    
    def test_tier_values(self):
        """Test tier enum values."""
        from neshama.web.rate_limit import RateLimitTier
        
        assert RateLimitTier.ANONYMOUS.value == "anonymous"
        assert RateLimitTier.FREE.value == "free"
        assert RateLimitTier.BASIC.value == "basic"
        assert RateLimitTier.PREMIUM.value == "premium"
        assert RateLimitTier.ENTERPRISE.value == "enterprise"


class TestGlobalManager:
    """Tests for global rate limit manager."""
    
    def test_get_rate_limit_manager(self):
        """Test getting global manager."""
        from neshama.web.rate_limit import get_rate_limit_manager, reset_rate_limit_manager
        
        reset_rate_limit_manager()
        
        manager = get_rate_limit_manager()
        
        assert manager is not None
        
        # Second call returns same instance
        manager2 = get_rate_limit_manager()
        assert manager is manager2
    
    def test_reset_rate_limit_manager(self):
        """Test resetting global manager."""
        from neshama.web.rate_limit import get_rate_limit_manager, reset_rate_limit_manager
        
        manager1 = get_rate_limit_manager()
        reset_rate_limit_manager()
        manager2 = get_rate_limit_manager()
        
        # Should be different instances
        assert manager1 is not manager2


class TestDefaultLimits:
    """Tests for default rate limits."""
    
    def test_default_limits_structure(self):
        """Test default limits have correct structure."""
        from neshama.web.rate_limit import DEFAULT_LIMITS
        
        assert "ip" in DEFAULT_LIMITS
        assert "user" in DEFAULT_LIMITS
        assert "endpoint" in DEFAULT_LIMITS
    
    def test_ip_limits_increase_with_tier(self):
        """Test that IP limits increase with tier."""
        from neshama.web.rate_limit import DEFAULT_LIMITS, RateLimitTier
        
        anonymous = DEFAULT_LIMITS["ip"][RateLimitTier.ANONYMOUS]
        enterprise = DEFAULT_LIMITS["ip"][RateLimitTier.ENTERPRISE]
        
        assert enterprise > anonymous
