# Web API - Billing Endpoints
"""
Billing API router for subscription management.

Provides endpoints for:
- Getting available plans
- Creating checkout sessions
- Managing subscriptions
- Viewing usage
- Handling webhooks
- Processing refunds
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Header, Body
from pydantic import BaseModel, EmailStr

from neshama.billing import (
    SubscriptionTier,
    get_plan,
    get_plan_limits,
    get_all_plans,
    get_tts_provider,
    has_memory_level,
    get_memory_levels,
    LimitsConfig,
    get_hosted_conversations_limit,
    is_byok_enabled,
)
from neshama.billing.config import get_stripe_config, get_price_id_for_tier, get_hosted_llm_config
from neshama.billing.stripe_service import (
    StripeService,
    SubscriptionInfo,
    CustomerInfo,
    WebhookEvent,
)
from neshama.billing.usage import (
    UsageTracker,
    ResourceType,
    get_monthly_usage,
    get_key_manager,
    is_byok,
    check_conversation_quota,
)
from neshama.billing.refund import RefundService, RefundRequest, RefundResult

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request/Response Models ───────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    """Checkout session request."""
    tier: str  # free, indie, studio, enterprise
    interval: str = "month"  # month or year
    email: Optional[str] = None
    name: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str
    customer_id: str


class SubscriptionResponse(BaseModel):
    """Subscription information response."""
    customer_id: str
    tier: str
    status: str
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool
    days_until_renewal: int
    is_active: bool


class PortalRequest(BaseModel):
    """Customer portal request."""
    return_url: Optional[str] = None


class PortalResponse(BaseModel):
    """Customer portal response."""
    portal_url: str


class UpgradeRequest(BaseModel):
    """Subscription upgrade request."""
    new_tier: str  # indie, studio, enterprise
    interval: str = "month"


class RefundRequestModel(BaseModel):
    """Refund request."""
    reason: str
    notes: Optional[str] = None


class UsageResponse(BaseModel):
    """Usage information response."""
    session_id: str
    npc_count: int
    emotion_calc_count: int
    tts_char_count: int
    api_call_count: int
    hosted_conversation_count: int
    limits: Dict[str, Any]
    remaining: Dict[str, Any]


class PlanResponse(BaseModel):
    """Plan information response."""
    tier: str
    name: str
    description: str
    monthly_price: float
    yearly_price: float
    limits: Dict[str, Any]
    memory_levels: list
    tts_provider: str
    hosted_conversations_limit: int
    byok_enabled: bool
    features: list
    team_member_limit: int
    soul_export_limit: int


# ── Service instances ─────────────────────────────────────────────────────────

def _get_stripe_service() -> StripeService:
    """Get or create StripeService instance."""
    return StripeService(mock=True)


def _get_usage_tracker() -> UsageTracker:
    """Get or create UsageTracker instance."""
    return UsageTracker()


def _get_refund_service() -> RefundService:
    """Get or create RefundService instance."""
    return RefundService()


def _get_customer_id(request: Request) -> Optional[str]:
    """Extract customer ID from request."""
    return request.headers.get("X-Customer-ID")


def _get_session_id(request: Request) -> Optional[str]:
    """Extract session ID from request."""
    session_id = request.query_params.get("session_id")
    if session_id:
        return session_id
    return request.headers.get("X-Session-ID")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/plans")
async def list_plans() -> Dict[str, Any]:
    """
    Get all available subscription plans.
    
    Returns pricing, limits, and features for each tier,
    including dual-track (hosted/BYOK) conversation quotas.
    """
    plans = get_all_plans()
    
    return {
        "plans": [
            {
                "tier": p.tier.value,
                "name": p.name,
                "description": p.description,
                "monthly_price": p.monthly_price_cents / 100,
                "monthly_price_cents": p.monthly_price_cents,
                "yearly_price": p.yearly_price_cents / 100,
                "yearly_price_cents": p.yearly_price_cents,
                "limits": LimitsConfig(
                    npc_limit=p.npc_limit,
                    emotion_calc_limit=p.emotion_calc_limit,
                    tts_char_limit=p.tts_char_limit,
                    api_call_limit=p.api_call_limit,
                    rate_limits=p.rate_limits,
                    hosted_conversations_limit=p.hosted_conversations_limit,
                    byok_enabled=p.byok_enabled,
                ).to_dict(),
                "memory_levels": p.memory_levels,
                "tts_provider": p.tts_provider.value,
                "hosted_conversations_limit": p.hosted_conversations_limit,
                "byok_enabled": p.byok_enabled,
                "features": p.features,
                "team_member_limit": p.team_member_limit,
                "soul_export_limit": p.soul_export_limit,
            }
            for p in plans
        ],
        "currency": "usd",
        "dual_track": True,
    }


@router.get("/plans/{tier}")
async def get_plan_details(tier: str) -> Dict[str, Any]:
    """
    Get details for a specific plan.
    
    Args:
        tier: Plan tier (free, indie, studio, enterprise)
    """
    plan = get_plan(tier)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {tier}")
    
    return {
        "tier": plan.tier.value,
        "name": plan.name,
        "description": plan.description,
        "monthly_price": plan.monthly_price_cents / 100,
        "monthly_price_cents": plan.monthly_price_cents,
        "limits": LimitsConfig(
            npc_limit=plan.npc_limit,
            emotion_calc_limit=plan.emotion_calc_limit,
            tts_char_limit=plan.tts_char_limit,
            api_call_limit=plan.api_call_limit,
            rate_limits=plan.rate_limits,
            hosted_conversations_limit=plan.hosted_conversations_limit,
            byok_enabled=plan.byok_enabled,
        ).to_dict(),
        "memory_levels": plan.memory_levels,
        "tts_provider": plan.tts_provider.value,
        "hosted_conversations_limit": plan.hosted_conversations_limit,
        "byok_enabled": plan.byok_enabled,
        "features": plan.features,
        "team_member_limit": plan.team_member_limit,
        "soul_export_limit": plan.soul_export_limit,
    }


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: Request,
    body: CheckoutRequest,
) -> CheckoutResponse:
    """
    Create a Stripe checkout session.
    
    For new customers, creates a customer account first.
    Returns checkout URL for payment.
    """
    stripe = _get_stripe_service()
    
    # Validate tier
    if body.tier == "free":
        raise HTTPException(
            status_code=400,
            detail="Cannot checkout for free tier. Just start using the app!"
        )
    
    plan = get_plan(body.tier)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {body.tier}")
    
    # Get customer ID from request or create new
    customer_id = _get_customer_id(request)
    
    if not customer_id:
        if not body.email:
            raise HTTPException(
                status_code=400,
                detail="Email required for new customers"
            )
        
        # Create new customer
        customer = stripe.create_customer(
            email=body.email,
            name=body.name,
            metadata={"source": "web_checkout"},
        )
        customer_id = customer.customer_id
    
    # Get price ID
    price_id = get_price_id_for_tier(body.tier, body.interval)
    
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail=f"No price configured for {body.tier}/{body.interval}"
        )
    
    # Create checkout session
    config = get_stripe_config()
    session = stripe.create_checkout_session(
        customer_id=customer_id,
        price_id=price_id,
        success_url=config.success_url,
        cancel_url=config.cancel_url,
        metadata={"tier": body.tier, "interval": body.interval},
    )
    
    return CheckoutResponse(
        checkout_url=session.url,
        session_id=session.session_id,
        customer_id=customer_id,
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(request: Request) -> SubscriptionResponse:
    """
    Get current subscription information.
    """
    customer_id = _get_customer_id(request)
    
    if not customer_id:
        # Return free tier for unauthenticated users
        return SubscriptionResponse(
            customer_id="anonymous",
            tier="free",
            status="active",
            current_period_start=datetime.now().isoformat(),
            current_period_end=datetime.now().isoformat(),
            cancel_at_period_end=False,
            days_until_renewal=0,
            is_active=True,
        )
    
    stripe = _get_stripe_service()
    subscription = stripe.get_subscription(customer_id)
    
    if not subscription:
        return SubscriptionResponse(
            customer_id=customer_id,
            tier="free",
            status="none",
            current_period_start=datetime.now().isoformat(),
            current_period_end=datetime.now().isoformat(),
            cancel_at_period_end=False,
            days_until_renewal=0,
            is_active=True,
        )
    
    return SubscriptionResponse(
        customer_id=subscription.customer_id,
        tier=subscription.tier,
        status=subscription.status.value,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        days_until_renewal=subscription.days_until_renewal,
        is_active=subscription.is_active,
    )


@router.post("/portal", response_model=PortalResponse)
async def create_portal(request: Request, body: PortalRequest) -> PortalResponse:
    """
    Create a Stripe customer portal session.
    
    Allows customers to manage their subscription, payment methods, etc.
    """
    customer_id = _get_customer_id(request)
    
    if not customer_id:
        raise HTTPException(
            status_code=400,
            detail="Customer ID required. Please log in."
        )
    
    stripe = _get_stripe_service()
    result = stripe.create_portal_session(
        customer_id=customer_id,
        return_url=body.return_url,
    )
    
    return PortalResponse(portal_url=result["url"])


@router.post("/cancel")
async def cancel_subscription(request: Request) -> Dict[str, Any]:
    """
    Cancel subscription.
    
    Subscription remains active until end of current period.
    """
    customer_id = _get_customer_id(request)
    
    if not customer_id:
        raise HTTPException(
            status_code=400,
            detail="Customer ID required"
        )
    
    stripe = _get_stripe_service()
    subscription = stripe.get_subscription(customer_id)
    
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="No active subscription found"
        )
    
    updated = stripe.cancel_subscription(
        subscription.subscription_id,
        cancel_at_period_end=True,
    )
    
    return {
        "success": True,
        "subscription_id": updated.subscription_id,
        "cancel_at": updated.cancel_at,
        "message": f"Subscription will cancel at end of period ({updated.current_period_end})",
    }


@router.post("/upgrade")
async def upgrade_subscription(
    request: Request,
    body: UpgradeRequest,
) -> Dict[str, Any]:
    """
    Upgrade subscription to a higher tier.
    
    Prorated charges may apply.
    """
    customer_id = _get_customer_id(request)
    
    if not customer_id:
        raise HTTPException(
            status_code=400,
            detail="Customer ID required"
        )
    
    stripe = _get_stripe_service()
    subscription = stripe.get_subscription(customer_id)
    
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="No active subscription found"
        )
    
    # Get new price
    price_id = get_price_id_for_tier(body.new_tier, body.interval)
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: {body.new_tier}"
        )
    
    # Update subscription
    updated = stripe.update_subscription(
        subscription.subscription_id,
        new_price_id=price_id,
    )
    
    return {
        "success": True,
        "subscription_id": updated.subscription_id,
        "new_tier": updated.tier,
        "message": f"Upgraded to {updated.tier.title()}",
    }


@router.post("/refund")
async def request_refund(
    request: Request,
    body: RefundRequestModel,
) -> Dict[str, Any]:
    """
    Request a refund.
    
    Returns eligibility status and estimated refund amount.
    """
    customer_id = _get_customer_id(request)
    
    if not customer_id:
        raise HTTPException(
            status_code=400,
            detail="Customer ID required"
        )
    
    refund_service = _get_refund_service()
    
    # Check eligibility
    eligibility = refund_service.validate_refund_eligibility(customer_id)
    
    if not eligibility["eligible"]:
        raise HTTPException(
            status_code=400,
            detail=eligibility["reason"],
        )
    
    # Create refund request
    refund_request = refund_service.request_refund(
        customer_id=customer_id,
        reason=body.reason,
        notes=body.notes,
    )
    
    # Auto-approve and process for demo
    refund_service.approve_refund(refund_request.request_id)
    result = refund_service.process_refund(refund_request.request_id)
    
    # Downgrade to free
    refund_service.downgrade_to_free(customer_id)
    
    return {
        "success": True,
        "request_id": refund_request.request_id,
        "refund_id": result.refund_id,
        "amount": result.refund_amount_cents / 100,
        "status": result.status.value,
    }


@router.get("/refund/policy")
async def get_refund_policy() -> Dict[str, Any]:
    """
    Get refund policy details.
    """
    refund_service = _get_refund_service()
    return refund_service.get_refund_policy()


@router.get("/usage")
async def get_usage(request: Request) -> UsageResponse:
    """
    Get current resource usage for a session.
    """
    session_id = _get_session_id(request)
    customer_id = _get_customer_id(request)
    
    if not session_id and not customer_id:
        raise HTTPException(
            status_code=400,
            detail="Session ID or Customer ID required"
        )
    
    usage_tracker = _get_usage_tracker()
    stripe = _get_stripe_service()
    
    # Get tier
    tier = "free"
    if customer_id:
        subscription = stripe.get_subscription(customer_id)
        if subscription:
            tier = subscription.tier
    
    plan = get_plan(tier)
    
    # Get usage
    if session_id:
        usage = usage_tracker.get_monthly_usage(session_id)
    else:
        usage = usage_tracker.get_monthly_usage(customer_id)
    
    def remaining(current: int, limit: int) -> Optional[int]:
        if limit == -1:
            return None
        return max(0, limit - current)
    
    return UsageResponse(
        session_id=session_id or customer_id or "unknown",
        npc_count=usage.npc_count,
        emotion_calc_count=usage.emotion_calc_count,
        tts_char_count=usage.tts_char_count,
        api_call_count=usage.api_call_count,
        limits={
            "npc_limit": plan.npc_limit if plan else 3,
            "emotion_calc_limit": plan.emotion_calc_limit if plan else 5000,
            "tts_char_limit": plan.tts_char_limit if plan else 0,
            "api_call_limit": plan.api_call_limit if plan else 1000,
        },
        remaining={
            "npc_remaining": remaining(
                usage.npc_count, plan.npc_limit if plan else 3
            ),
            "emotion_calc_remaining": remaining(
                usage.emotion_calc_count, plan.emotion_calc_limit if plan else 5000
            ),
            "tts_char_remaining": remaining(
                usage.tts_char_count, plan.tts_char_limit if plan else 0
            ),
            "api_call_remaining": remaining(
                usage.api_call_count, plan.api_call_limit if plan else 1000
            ),
        },
    )


@router.post("/webhook")
async def handle_webhook(request: Request) -> Dict[str, Any]:
    """
    Handle Stripe webhook events.
    
    This endpoint does not require authentication.
    Stripe signature verification is handled internally.
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Get signature header
    signature = request.headers.get("Stripe-Signature", "")
    
    stripe = _get_stripe_service()
    
    try:
        event_data = stripe.verify_webhook_signature(body, signature)
        event = WebhookEvent.from_stripe_event(event_data)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(
            status_code=400,
            detail="Webhook signature verification failed"
        )
    
    # Process event
    result = stripe.handle_webhook(event)
    
    logger.info(f"Webhook processed: {event.event_type} -> {result}")
    
    return {"received": True, "event_type": event.event_type, "result": result}


@router.get("/eligibility")
async def check_eligibility(request: Request) -> Dict[str, Any]:
    """
    Check refund eligibility for current customer.
    """
    customer_id = _get_customer_id(request)
    
    if not customer_id:
        return {
            "eligible": False,
            "reason": "Customer ID required",
        }
    
    refund_service = _get_refund_service()
    return refund_service.validate_refund_eligibility(customer_id)
