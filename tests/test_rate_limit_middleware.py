# Test Rate Limit Middleware
"""
Tests for RateLimitMiddleware.
"""

import time
from unittest.mock import MagicMock

import pytest

from neshama.web.middleware.rate_limit import (
    RateLimitMiddleware,
    RateLimitResponse,
    RateLimitMetrics,
    get_middleware,
    DEFAULT_IP_LIMIT,
    DEFAULT_API_KEY_LIMIT,
)


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware for testing."""
        return RateLimitMiddleware(
            ip_limit=100,
            api_key_limit=50,
        )
    
    def test_initialization(self, middleware):
        """Test middleware initialization."""
        assert middleware._ip_limit == 100
        assert middleware._api_key_limit == 50
        assert middleware._whitelist_paths is not None
    
    def test_get_client_ip_direct(self, middleware):
        """Test getting client IP directly."""
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.query_params = {}
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_forwarded(self, middleware):
        """Test getting client IP from forwarded header."""
        mock_request = MagicMock()
        mock_request.headers = {
            "X-Forwarded-For": "10.0.0.1, 10.0.0.2"
        }
        mock_request.query_params = {}
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "10.0.0.1"
    
    def test_get_client_ip_real_ip(self, middleware):
        """Test getting client IP from X-Real-IP header."""
        mock_request = MagicMock()
        mock_request.headers = {
            "X-Real-IP": "10.0.0.5"
        }
        mock_request.query_params = {}
        mock_request.client = None
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "10.0.0.5"
    
    def test_get_api_key_header(self, middleware):
        """Test getting API key from header."""
        mock_request = MagicMock()
        mock_request.headers = {
            "X-API-Key": "test_key_123"
        }
        mock_request.query_params = {}
        
        key = middleware._get_api_key(mock_request)
        assert key == "test_key_123"
    
    def test_get_api_key_bearer(self, middleware):
        """Test getting API key from Authorization header."""
        mock_request = MagicMock()
        mock_request.headers = {
            "Authorization": "Bearer my_token"
        }
        mock_request.query_params = {}
        
        key = middleware._get_api_key(mock_request)
        assert key == "my_token"
    
    def test_get_api_key_query(self, middleware):
        """Test getting API key from query params."""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.query_params = {
            "api_key": "query_key_456"
        }
        
        key = middleware._get_api_key(mock_request)
        assert key == "query_key_456"
    
    def test_get_api_key_none(self, middleware):
        """Test getting API key when not present."""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.query_params = {}
        
        key = middleware._get_api_key(mock_request)
        assert key is None
    
    def test_get_tier_anonymous(self, middleware):
        """Test getting tier for anonymous user."""
        tier = middleware._get_tier(None)
        assert tier == "anonymous"
    
    def test_get_tier_premium(self, middleware):
        """Test getting tier for premium user."""
        tier = middleware._get_tier("premium_user_key")
        assert tier == "premium"
    
    def test_get_tier_basic(self, middleware):
        """Test getting tier for basic user."""
        tier = middleware._get_tier("basic_user_key")
        assert tier == "basic"
    
    def test_get_tier_registered(self, middleware):
        """Test getting tier for registered user."""
        tier = middleware._get_tier("regular_key")
        assert tier == "registered"
    
    def test_is_whitelisted_path(self, middleware):
        """Test path whitelisting."""
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_request.client.host = "192.168.1.1"
        
        assert middleware._is_whitelisted(mock_request) is True
    
    def test_is_whitelisted_ip(self, middleware):
        """Test IP whitelisting."""
        middleware._whitelist_ips = {"192.168.1.100"}
        
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.headers.get = MagicMock(return_value=None)  # No forwarded headers
        mock_request.client.host = "192.168.1.100"
        
        assert middleware._is_whitelisted(mock_request) is True
    
    def test_is_not_whitelisted(self, middleware):
        """Test non-whitelisted request."""
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.client.host = "192.168.1.1"
        
        assert middleware._is_whitelisted(mock_request) is False
    
    def test_check_ip_limit_first_request(self, middleware):
        """Test IP limit for first request."""
        allowed, response = middleware._check_ip_limit("192.168.1.1")
        
        assert allowed is True
        assert response.allowed is True
        assert response.limit > 0
        assert response.remaining > 0
    
    def test_check_ip_limit_exhausted(self, middleware):
        """Test IP limit when exhausted."""
        # Create middleware with very low limit
        mw = RateLimitMiddleware(ip_limit=5)
        
        # Exhaust the limit
        for _ in range(5):
            mw._check_ip_limit("192.168.1.1")
        
        # Next should fail
        allowed, response = mw._check_ip_limit("192.168.1.1")
        
        assert allowed is False
        assert response.allowed is False
        assert response.retry_after is not None
        assert response.retry_after > 0
    
    def test_check_api_key_limit(self, middleware):
        """Test API key limit check."""
        allowed, response = middleware._check_api_key_limit("test_key")
        
        assert allowed is True
        assert response.tier in ["registered", "premium", "basic"]
    
    def test_check_request_whitelisted(self, middleware):
        """Test checking whitelisted request."""
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.query_params = {}
        
        allowed, response, layer = middleware.check_request(mock_request)
        
        assert allowed is True
        assert response.allowed is True
        assert layer == 0
    
    def test_check_request_ip_limit(self, middleware):
        """Test checking request with IP limit."""
        # Exhaust IP limit
        for _ in range(middleware._ip_limit):
            middleware._check_ip_limit("192.168.1.1")
        
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.query_params = {}
        
        allowed, response, layer = middleware.check_request(mock_request)
        
        assert allowed is False
        assert layer == 1  # IP layer blocked
    
    def test_metrics(self, middleware):
        """Test metrics tracking."""
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.query_params = {}
        
        # Make some requests
        middleware.check_request(mock_request)
        middleware.check_request(mock_request)
        
        metrics = middleware.metrics
        assert metrics.total_checks >= 2
    
    def test_reset_metrics(self, middleware):
        """Test resetting metrics."""
        middleware._metrics.total_checks = 100
        
        middleware.reset_metrics()
        
        assert middleware._metrics.total_checks == 0
    
    def test_get_middleware_class(self, middleware):
        """Test getting middleware class."""
        cls = middleware.get_middleware()
        assert cls is not None
        assert hasattr(cls, 'dispatch')


class TestRateLimitResponse:
    """Tests for RateLimitResponse."""
    
    def test_to_dict(self):
        """Test to_dict conversion."""
        response = RateLimitResponse(
            allowed=True,
            limit=100,
            remaining=99,
            reset_at="2024-01-01T12:00:00",
            retry_after=None,
            tier="registered",
        )
        
        d = response.to_dict()
        assert d["allowed"] is True
        assert d["limit"] == 100
        assert d["remaining"] == 99
        assert d["reset_at"] == "2024-01-01T12:00:00"
        assert d["tier"] == "registered"


class TestRateLimitMetrics:
    """Tests for RateLimitMetrics."""
    
    def test_defaults(self):
        """Test default metrics."""
        metrics = RateLimitMetrics()
        
        assert metrics.total_checks == 0
        assert metrics.total_allowed == 0
        assert metrics.total_rejected == 0
        assert metrics.ip_blocked == 0
        assert metrics.api_key_blocked == 0
        assert metrics.endpoint_blocked == 0


class TestConstants:
    """Tests for constants."""
    
    def test_default_limits(self):
        """Test default limit constants."""
        assert DEFAULT_IP_LIMIT > 0
        assert DEFAULT_API_KEY_LIMIT > 0
        assert DEFAULT_IP_LIMIT >= DEFAULT_API_KEY_LIMIT


class TestGlobalMiddleware:
    """Tests for global middleware functions."""
    
    def test_get_middleware_function(self):
        """Test get_middleware function."""
        middleware = get_middleware(ip_limit=200)
        assert middleware._ip_limit == 200
