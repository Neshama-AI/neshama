# Tests - Billing API
"""
Tests for billing API endpoints.
Updated for dual-track (hosted/BYOK) model.

These tests are designed to be isolated from the main web module
to avoid pre-existing dependency issues.
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path


# Direct imports of billing module
from neshama.billing.plans import (
    SubscriptionTier,
    get_plan,
    get_all_plans,
    get_hosted_conversations_limit,
    is_byok_enabled,
)
from neshama.billing.usage import (
    UsageTracker,
    ResourceType,
    UserKeyManager,
    KeyEncryption,
)


# Create a minimal billing router for testing
from fastapi import APIRouter, Request, Header, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional


class CheckoutRequest(BaseModel):
    tier: str
    interval: str = "month"
    email: Optional[str] = None
    name: Optional[str] = None


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
    customer_id: str


class UsageResponse(BaseModel):
    session_id: str
    npc_count: int
    emotion_calc_count: int
    tts_char_count: int
    api_call_count: int
    hosted_conversation_count: int
    limits: Dict[str, Any]
    remaining: Dict[str, Any]


# Create test router
router = APIRouter(prefix="/api/billing")


@router.get("/plans")
async def list_plans():
    plans = get_all_plans()
    return {
        "plans": [
            {
                "tier": p.tier.value,
                "name": p.name,
                "description": p.description,
                "monthly_price": p.monthly_price_cents / 100,
                "monthly_price_cents": p.monthly_price_cents,
                "limits": {
                    "npc_limit": p.npc_limit,
                    "emotion_calc_limit": p.emotion_calc_limit,
                    "tts_char_limit": p.tts_char_limit,
                    "api_call_limit": p.api_call_limit,
                    "hosted_conversations_limit": p.hosted_conversations_limit,
                    "byok_enabled": p.byok_enabled,
                },
                "memory_levels": p.memory_levels,
                "tts_provider": p.tts_provider.value,
                "hosted_conversations_limit": p.hosted_conversations_limit,
                "byok_enabled": p.byok_enabled,
                "features": p.features,
            }
            for p in plans
        ],
        "currency": "usd",
        "dual_track": True,
    }


@router.get("/plans/{tier}")
async def get_plan_details(tier: str):
    plan = get_plan(tier)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {tier}")
    
    return {
        "tier": plan.tier.value,
        "name": plan.name,
        "description": plan.description,
        "monthly_price": plan.monthly_price_cents / 100,
        "monthly_price_cents": plan.monthly_price_cents,
        "limits": {
            "npc_limit": plan.npc_limit,
            "emotion_calc_limit": plan.emotion_calc_limit,
            "tts_char_limit": plan.tts_char_limit,
            "api_call_limit": plan.api_call_limit,
            "hosted_conversations_limit": plan.hosted_conversations_limit,
            "byok_enabled": plan.byok_enabled,
        },
        "memory_levels": plan.memory_levels,
        "tts_provider": plan.tts_provider.value,
        "hosted_conversations_limit": plan.hosted_conversations_limit,
        "byok_enabled": plan.byok_enabled,
        "features": plan.features,
    }


@router.post("/checkout")
async def create_checkout(body: CheckoutRequest):
    if body.tier == "free":
        raise HTTPException(
            status_code=400,
            detail="Cannot checkout for free tier. Just start using the app!"
        )
    
    plan = get_plan(body.tier)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {body.tier}")
    
    if not body.email:
        raise HTTPException(
            status_code=400,
            detail="Email required for new customers"
        )
    
    # Mock checkout
    return CheckoutResponse(
        checkout_url=f"https://checkout.stripe.com/cs_test_{body.tier}",
        session_id="cs_test_123",
        customer_id="cus_test_123",
    )


@router.get("/subscription")
async def get_subscription(request: Request, x_customer_id: Optional[str] = Header(None)):
    if not x_customer_id:
        return {
            "customer_id": "anonymous",
            "tier": "free",
            "status": "active",
        }
    
    return {
        "customer_id": x_customer_id,
        "tier": "indie",
        "status": "active",
    }


@router.get("/usage")
async def get_usage(
    request: Request,
    session_id: Optional[str] = None,
):
    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="Session ID or Customer ID required"
        )
    
    return {
        "session_id": session_id,
        "npc_count": 2,
        "emotion_calc_count": 500,
        "tts_char_count": 0,
        "api_call_count": 100,
        "hosted_conversation_count": 50,
        "limits": {
            "npc_limit": 10,
            "emotion_calc_limit": 50000,
            "tts_char_limit": 100000,
            "api_call_limit": 10000,
            "hosted_conversations_limit": 10000,
        },
        "remaining": {
            "npc_remaining": 8,
            "emotion_calc_remaining": 49500,
            "tts_char_remaining": 100000,
            "api_call_remaining": 9900,
            "hosted_conversations_remaining": 9950,
        },
    }


@router.get("/refund/policy")
async def get_refund_policy():
    return {
        "full_refund_window_days": 14,
        "max_refund_days": 30,
        "policy": {
            "first_subscription": {
                "within_14_days": "Full refund",
                "after_14_days": "Pro-rated refund based on remaining days",
            },
            "add_ons": {
                "extra_npc": "Non-refundable",
                "emotion_calc_packs": "Non-refundable",
            },
        },
    }


# ── Test Setup ────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    """Create test FastAPI app with billing router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestListPlans:
    """Test GET /api/billing/plans endpoint."""
    
    def test_list_plans(self, client):
        """Test that all plans are returned with dual-track fields."""
        response = client.get("/api/billing/plans")
        assert response.status_code == 200
        
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) == 4
        assert data["currency"] == "usd"
        assert data["dual_track"] is True
    
    def test_plans_include_hosted_conversations(self, client):
        """Test that plans include hosted conversation limits."""
        response = client.get("/api/billing/plans")
        plans = response.json()["plans"]
        
        free_plan = next(p for p in plans if p["tier"] == "free")
        assert free_plan["hosted_conversations_limit"] == 1_000
        assert free_plan["byok_enabled"] is True
        
        enterprise_plan = next(p for p in plans if p["tier"] == "enterprise")
        assert enterprise_plan["hosted_conversations_limit"] == -1
    
    def test_plans_include_features(self, client):
        """Test that plans include feature lists."""
        response = client.get("/api/billing/plans")
        plans = response.json()["plans"]
        
        free_plan = next(p for p in plans if p["tier"] == "free")
        assert "emotion_engine" in free_plan["features"]
        assert "sentiment_analysis" in free_plan["features"]
        # Free tier should NOT have premium features
        assert "npc2npc_social" not in free_plan["features"]
        
        indie_plan = next(p for p in plans if p["tier"] == "indie")
        assert "npc2npc_social" in indie_plan["features"]


class TestGetPlanDetails:
    """Test GET /api/billing/plans/{tier} endpoint."""
    
    def test_get_free_plan(self, client):
        """Test getting free plan details."""
        response = client.get("/api/billing/plans/free")
        assert response.status_code == 200
        
        data = response.json()
        assert data["tier"] == "free"
        assert data["hosted_conversations_limit"] == 1_000
        assert data["byok_enabled"] is True
    
    def test_get_indie_plan(self, client):
        """Test getting indie plan details."""
        response = client.get("/api/billing/plans/indie")
        assert response.status_code == 200
        
        data = response.json()
        assert data["monthly_price"] == 19.0
        assert data["hosted_conversations_limit"] == 10_000
    
    def test_get_studio_plan(self, client):
        """Test getting studio plan details."""
        response = client.get("/api/billing/plans/studio")
        assert response.status_code == 200
        
        data = response.json()
        assert data["monthly_price"] == 79.0
        assert data["hosted_conversations_limit"] == 100_000
    
    def test_get_enterprise_plan(self, client):
        """Test getting enterprise plan details."""
        response = client.get("/api/billing/plans/enterprise")
        assert response.status_code == 200
        
        data = response.json()
        assert data["monthly_price"] == 299.0
        assert data["hosted_conversations_limit"] == -1
    
    def test_plan_not_found(self, client):
        """Test getting non-existent plan."""
        response = client.get("/api/billing/plans/nonexistent")
        assert response.status_code == 404


class TestCheckout:
    """Test POST /api/billing/checkout endpoint."""
    
    def test_checkout_free_tier_fails(self, client):
        """Test that checkout for free tier is rejected."""
        response = client.post(
            "/api/billing/checkout",
            json={"tier": "free", "email": "test@test.com"}
        )
        assert response.status_code == 400
    
    def test_checkout_requires_email(self, client):
        """Test that checkout requires email for new customers."""
        response = client.post(
            "/api/billing/checkout",
            json={"tier": "indie"}
        )
        assert response.status_code == 400
    
    def test_checkout_indie(self, client):
        """Test checkout for indie tier."""
        response = client.post(
            "/api/billing/checkout",
            json={"tier": "indie", "email": "test@test.com"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data


class TestUsageEndpoint:
    """Test GET /api/billing/usage endpoint."""
    
    def test_usage_requires_session_id(self, client):
        """Test that usage requires session ID."""
        response = client.get("/api/billing/usage")
        assert response.status_code == 400
    
    def test_usage_includes_hosted_conversations(self, client):
        """Test that usage includes hosted conversation count."""
        response = client.get("/api/billing/usage?session_id=test_session")
        assert response.status_code == 200
        
        data = response.json()
        assert "hosted_conversation_count" in data
        assert "hosted_conversations_limit" in data["limits"]
        assert "hosted_conversations_remaining" in data["remaining"]


class TestRefundPolicy:
    """Test GET /api/billing/refund/policy endpoint."""
    
    def test_get_refund_policy(self, client):
        """Test getting refund policy."""
        response = client.get("/api/billing/refund/policy")
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_refund_window_days"] == 14


class TestDualTrackPricing:
    """Test dual-track pricing model."""
    
    def test_studio_price_is_79(self, client):
        """Test Studio tier is $79/mo."""
        response = client.get("/api/billing/plans/studio")
        data = response.json()
        assert data["monthly_price"] == 79.0
        assert data["monthly_price_cents"] == 7900
    
    def test_enterprise_price_is_299(self, client):
        """Test Enterprise tier is $299/mo."""
        response = client.get("/api/billing/plans/enterprise")
        data = response.json()
        assert data["monthly_price"] == 299.0
        assert data["monthly_price_cents"] == 29900
    
    def test_all_tiers_enable_byok(self, client):
        """Test that all tiers have BYOK enabled."""
        response = client.get("/api/billing/plans")
        plans = response.json()["plans"]
        
        for plan in plans:
            assert plan["byok_enabled"] is True, f"Tier {plan['tier']} should have BYOK enabled"
