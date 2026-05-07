# Tests - Subscription Middleware
"""
Tests for subscription middleware.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from starlette.responses import JSONResponse

from neshama.billing.middleware import (
    SubscriptionMiddleware,
    SubscriptionContext,
    RateLimitExceeded,
    get_subscription_context,
    require_subscription,
    SubscriptionTier,
)


class TestSubscriptionContext:
    """Test SubscriptionContext dataclass."""
    
    def test_default_values(self):
        """Test default context values."""
        ctx = SubscriptionContext()
        
        assert ctx.customer_id is None
        assert ctx.session_id is None
        assert ctx.tier == SubscriptionTier.FREE
        assert ctx.npc_count == 0
    
    def test_to_dict(self):
        """Test serialization."""
        ctx = SubscriptionContext(
            customer_id="cus_123",
            session_id="session_123",
            tier=SubscriptionTier.INDIE,
            npc_count=5,
            emotion_calc_count=1000,
        )
        
        data = ctx.to_dict()
        
        assert data["customer_id"] == "cus_123"
        assert data["session_id"] == "session_123"
        assert data["tier"] == "indie"
        assert data["npc_count"] == 5


class TestRateLimitExceeded:
    """Test RateLimitExceeded exception."""
    
    def test_exception_attributes(self):
        """Test exception has correct attributes."""
        exc = RateLimitExceeded(
            resource_type="npc",
            current_usage=5,
            limit=3,
            message="NPC limit reached"
        )
        
        assert exc.resource_type == "npc"
        assert exc.current_usage == 5
        assert exc.limit == 3
        assert exc.message == "NPC limit reached"
    
    def test_exception_message(self):
        """Test exception message."""
        exc = RateLimitExceeded(
            resource_type="emotion_calc",
            current_usage=100,
            limit=50
        )
        
        assert "emotion_calc" in str(exc)


class TestSubscriptionMiddleware:
    """Test SubscriptionMiddleware."""
    
    @pytest.fixture
    def mock_stripe(self):
        """Create mock Stripe service."""
        mock = MagicMock()
        mock.get_subscription.return_value = MagicMock(
            customer_id="cus_123",
            subscription_id="sub_123",
            tier="indie",
        )
        return mock
    
    @pytest.fixture
    def mock_tracker(self):
        """Create mock usage tracker."""
        mock = MagicMock()
        mock.get_monthly_usage.return_value = MagicMock(
            npc_count=2,
            emotion_calc_count=500,
            tts_char_count=0,
            api_call_count=100,
        )
        mock.check_limit_reached.return_value = False
        return mock
    
    @pytest.fixture
    def app(self, mock_stripe, mock_tracker):
        """Create test FastAPI app with middleware."""
        app = FastAPI()
        
        app.add_middleware(
            SubscriptionMiddleware,
            stripe_service=mock_stripe,
            usage_tracker=mock_tracker,
        )
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            ctx = get_subscription_context(request)
            return {"tier": ctx.tier.value if ctx else "unknown"}
        
        @app.post("/api/game/npc")
        async def create_npc(request: Request):
            return {"success": True}
        
        @app.post("/api/game/npc/{npc_id}/event")
        async def push_event(npc_id: str):
            return {"success": True}
        
        @app.post("/api/voice/tts")
        async def tts_request():
            return {"success": True}
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_bypass_health_check(self, client, mock_stripe, mock_tracker):
        """Test that health endpoint bypasses middleware."""
        response = client.get("/health")
        
        assert response.status_code == 200
        # Middleware should not call stripe/usage for bypassed paths
        mock_stripe.get_subscription.assert_not_called()
    
    def test_context_added_to_request(self, client, mock_stripe, mock_tracker):
        """Test that context is added to request state."""
        response = client.get(
            "/test",
            headers={"X-Customer-ID": "cus_123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have determined tier
        assert "tier" in data
    
    def test_tier_from_customer(self, client, mock_stripe, mock_tracker):
        """Test tier determination from customer."""
        response = client.get(
            "/test",
            headers={"X-Customer-ID": "cus_123"}
        )
        
        assert response.status_code == 200
        mock_stripe.get_subscription.assert_called_with("cus_123")
    
    def test_session_from_header(self, client, mock_stripe, mock_tracker):
        """Test session ID from header."""
        response = client.get(
            "/test",
            headers={"X-Session-ID": "session_123"}
        )
        
        assert response.status_code == 200
        mock_tracker.get_monthly_usage.assert_called_with("session_123")
    
    def test_session_from_query(self, client, mock_stripe, mock_tracker):
        """Test session ID from query param."""
        response = client.get(
            "/test?session_id=session_456"
        )
        
        assert response.status_code == 200
        mock_tracker.get_monthly_usage.assert_called_with("session_456")


class TestMiddlewareNPCLimit:
    """Test NPC creation limit enforcement."""
    
    @pytest.fixture
    def mock_stripe(self):
        """Create mock Stripe service."""
        mock = MagicMock()
        mock.get_subscription.return_value = MagicMock(
            customer_id="cus_123",
            subscription_id="sub_123",
            tier="free",  # Free tier has 3 NPC limit
        )
        return mock
    
    @pytest.fixture
    def mock_tracker(self):
        """Create mock usage tracker that simulates limit reached."""
        mock = MagicMock()
        mock.get_monthly_usage.return_value = MagicMock(
            npc_count=3,  # At limit
            emotion_calc_count=0,
            tts_char_count=0,
            api_call_count=0,
        )
        mock.check_limit_reached.return_value = True  # Limit reached!
        return mock
    
    @pytest.fixture
    def app(self, mock_stripe, mock_tracker):
        """Create test app."""
        app = FastAPI()
        
        app.add_middleware(
            SubscriptionMiddleware,
            stripe_service=mock_stripe,
            usage_tracker=mock_tracker,
        )
        
        @app.post("/api/game/npc")
        async def create_npc():
            return {"success": True}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_npc_limit_exceeded(self, client):
        """Test that NPC creation is blocked when limit reached."""
        response = client.post(
            "/api/game/npc",
            headers={"X-Customer-ID": "cus_123", "X-Session-ID": "session_123"}
        )
        
        assert response.status_code == 429
        data = response.json()
        
        assert data["error"] == "limit_exceeded"
        assert data["resource_type"] == "npc"
        assert "limit" in data


class TestMiddlewareTTSLimit:
    """Test TTS limit enforcement."""
    
    @pytest.fixture
    def mock_stripe(self):
        """Create mock Stripe service for free tier."""
        mock = MagicMock()
        mock.get_subscription.return_value = None  # Free tier
        return mock
    
    @pytest.fixture
    def app(self, mock_stripe):
        """Create test app."""
        app = FastAPI()
        
        app.add_middleware(
            SubscriptionMiddleware,
            stripe_service=mock_stripe,
            usage_tracker=MagicMock(),
        )
        
        @app.post("/api/voice/tts")
        async def tts_request():
            return {"success": True}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_tts_blocked_on_free_tier(self, client):
        """Test that TTS is blocked on free tier."""
        response = client.post(
            "/api/voice/tts",
            headers={"X-Customer-ID": "cus_123"}
        )
        
        assert response.status_code == 429
        data = response.json()
        
        assert data["error"] == "limit_exceeded"
        assert data["resource_type"] == "tts"
        assert "Free tier" in data["message"]


class TestMiddlewareMemoryAccess:
    """Test memory level access enforcement."""
    
    @pytest.fixture
    def mock_stripe(self):
        """Create mock Stripe service for indie tier."""
        mock = MagicMock()
        mock.get_subscription.return_value = MagicMock(
            customer_id="cus_123",
            subscription_id="sub_123",
            tier="indie",  # Has L0, L1
        )
        return mock
    
    @pytest.fixture
    def mock_tracker(self):
        """Create mock usage tracker."""
        mock = MagicMock()
        mock.get_monthly_usage.return_value = MagicMock(
            npc_count=0,
            emotion_calc_count=0,
            tts_char_count=0,
            api_call_count=0,
        )
        mock.check_limit_reached.return_value = False
        return mock
    
    @pytest.fixture
    def app(self, mock_stripe, mock_tracker):
        """Create test app."""
        app = FastAPI()
        
        app.add_middleware(
            SubscriptionMiddleware,
            stripe_service=mock_stripe,
            usage_tracker=mock_tracker,
        )
        
        @app.post("/api/memory/l2")
        async def memory_l2():
            return {"success": True}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_l2_blocked_on_indie(self, client):
        """Test that L2 memory is blocked on indie tier."""
        response = client.post(
            "/api/memory/l2",
            headers={"X-Customer-ID": "cus_123"}
        )
        
        assert response.status_code == 429
        data = response.json()
        
        assert data["error"] == "limit_exceeded"
        assert data["resource_type"] == "memory"
        assert "L2" in data["message"]


class TestGetSubscriptionContext:
    """Test get_subscription_context helper."""
    
    def test_no_context(self):
        """Test when no context is set."""
        # Create mock request without state
        request = MagicMock(spec=Request)
        request.state = MagicMock(spec=[])
        
        # Should return None
        result = get_subscription_context(request)
        assert result is None


class TestRequireSubscription:
    """Test require_subscription helper."""
    
    def test_no_context_raises(self):
        """Test that missing context raises HTTPException."""
        request = MagicMock(spec=Request)
        request.state = MagicMock(spec=[])
        
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            require_subscription(request)
        
        assert exc_info.value.status_code == 401
    
    def test_tier_too_low_raises(self):
        """Test that insufficient tier raises HTTPException."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.subscription_context = SubscriptionContext(
            tier=SubscriptionTier.FREE
        )
        
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            require_subscription(request, min_tier=SubscriptionTier.INDIE)
        
        assert exc_info.value.status_code == 403
        assert "Indie" in exc_info.value.detail
    
    def test_sufficient_tier(self):
        """Test that sufficient tier passes."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.subscription_context = SubscriptionContext(
            tier=SubscriptionTier.STUDIO
        )
        
        result = require_subscription(request, min_tier=SubscriptionTier.INDIE)
        
        assert result.tier == SubscriptionTier.STUDIO
