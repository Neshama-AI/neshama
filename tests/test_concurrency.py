# Test Concurrency Middleware
"""
Tests for ConcurrencyLimiter middleware.
"""

import time
import threading
import asyncio
from unittest.mock import MagicMock, AsyncMock

import pytest

from neshama.web.middleware.concurrency import (
    ConcurrencyLimiter,
    ConcurrencyStats,
    get_limiter,
    reset_stats,
)


class TestConcurrencyLimiter:
    """Tests for ConcurrencyLimiter."""
    
    @pytest.fixture
    def limiter(self):
        """Create a limiter for testing."""
        return ConcurrencyLimiter(max_concurrent=5)
    
    def test_initialization(self, limiter):
        """Test limiter initialization."""
        assert limiter._max_concurrent == 5
        assert limiter._current_concurrent == 0
    
    def test_acquire_and_release(self, limiter):
        """Test acquiring and releasing slots."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.client = MagicMock(host="127.0.0.1")
        
        # Acquire
        assert limiter.acquire(mock_request) is True
        assert limiter._current_concurrent == 1
        
        # Release
        limiter.release()
        assert limiter._current_concurrent == 0
    
    def test_limit_rejection(self, limiter):
        """Test rejection when at limit."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.client = MagicMock(host="127.0.0.1")
        
        # Fill up the pool
        for _ in range(5):
            limiter.acquire(mock_request)
        
        assert limiter._current_concurrent == 5
        
        # Next acquire should fail
        assert limiter.acquire(mock_request) is False
        assert limiter._current_concurrent == 5  # Should not increase
    
    def test_stats(self, limiter):
        """Test statistics tracking."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.client = MagicMock(host="127.0.0.1")
        
        limiter.acquire(mock_request)
        limiter.acquire(mock_request)
        
        limiter.release()
        
        stats = limiter.stats
        assert stats.total_requests == 2
        assert stats.rejected_requests == 0
    
    def test_rejected_stats(self, limiter):
        """Test rejection statistics."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.client = MagicMock(host="127.0.0.1")
        
        # Fill up
        for _ in range(5):
            limiter.acquire(mock_request)
        
        # Try to exceed
        limiter.acquire(mock_request)
        limiter.acquire(mock_request)
        
        stats = limiter.stats
        assert stats.rejected_requests == 2
    
    def test_endpoint_stats(self, limiter):
        """Test per-endpoint statistics."""
        limiter2 = ConcurrencyLimiter(max_concurrent=10, endpoint_stats_enabled=True)
        
        mock_request1 = MagicMock()
        mock_request1.method = "GET"
        mock_request1.url.path = "/api/test1"
        mock_request1.client = MagicMock(host="127.0.0.1")
        
        mock_request2 = MagicMock()
        mock_request2.method = "POST"
        mock_request2.url.path = "/api/test2"
        mock_request2.client = MagicMock(host="127.0.0.1")
        
        limiter2.acquire(mock_request1)
        limiter2.acquire(mock_request2)
        limiter2.acquire(mock_request1)
        
        stats = limiter2.stats
        # Keys include HTTP method prefix
        assert "GET /api/test1" in stats.endpoint_stats
        assert "POST /api/test2" in stats.endpoint_stats
    
    def test_get_middleware(self, limiter):
        """Test middleware class creation."""
        middleware_class = limiter.get_middleware()
        assert middleware_class is not None
        assert hasattr(middleware_class, 'dispatch')


class TestConcurrencyStats:
    """Tests for ConcurrencyStats."""
    
    def test_to_dict(self):
        """Test stats to dict conversion."""
        stats = ConcurrencyStats(
            current_concurrent=5,
            max_concurrent=10,
            total_requests=100,
            rejected_requests=10,
            peak_concurrent=8,
        )
        
        d = stats.to_dict()
        assert d["current_concurrent"] == 5
        assert d["max_concurrent"] == 10
        assert d["total_requests"] == 100
        assert d["rejected_requests"] == 10
        assert d["peak_concurrent"] == 8


class TestGlobalLimiter:
    """Tests for global limiter functions."""
    
    def test_get_limiter(self):
        """Test getting global limiter."""
        reset_stats()
        limiter = get_limiter(max_concurrent=20)
        assert limiter._max_concurrent == 20
    
    def test_get_stats(self):
        """Test getting global stats."""
        reset_stats()
        limiter = get_limiter()
        stats = limiter.stats
        assert isinstance(stats, ConcurrencyStats)
    
    def test_reset_stats(self):
        """Test resetting stats."""
        from neshama.web.middleware.concurrency import get_limiter, reset_stats
        
        # Get global limiter
        limiter = get_limiter()
        limiter._total_requests = 100
        
        # Reset
        reset_stats()
        
        # Get new limiter
        new_limiter = get_limiter()
        assert new_limiter._total_requests == 0


class TestConcurrencyMiddlewareIntegration:
    """Integration tests for middleware."""
    
    @pytest.mark.asyncio
    async def test_middleware_rejects_when_full(self):
        """Test middleware rejects requests when at limit."""
        limiter = ConcurrencyLimiter(max_concurrent=1)
        
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.client = MagicMock(host="127.0.0.1")
        
        # Acquire the only slot
        limiter.acquire(mock_request)
        
        # Create middleware
        middleware_class = limiter.get_middleware()
        middleware = middleware_class(app=MagicMock())
        
        # Create mock call_next that returns a response
        async def mock_call_next(request):
            return MagicMock(
                status_code=200,
                headers={},
            )
        
        # Should get 503 response
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 503
        
        limiter.release()
