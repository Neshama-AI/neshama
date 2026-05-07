# Billing - Subscription Middleware
"""
FastAPI middleware for subscription-based resource enforcement.

Checks each request for:
- NPC creation limits
- Emotion calculation limits
- TTS usage quotas
- Memory level access
- API rate limits

Returns 429 Too Many Requests when limits are exceeded.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any, List
from enum import Enum

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .plans import (
    get_plan,
    get_plan_limits,
    SubscriptionTier,
    check_limit,
    has_memory_level,
    get_memory_levels,
    TTSProvider,
    get_tts_provider,
)
from .usage import (
    UsageTracker,
    ResourceType,
    get_usage_tracker,
)
from .stripe_service import StripeService, get_stripe_service

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        resource_type: str,
        current_usage: int,
        limit: int,
        message: Optional[str] = None,
    ):
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.limit = limit
        self.message = message or f"{resource_type} limit exceeded"
        super().__init__(self.message)


@dataclass
class SubscriptionContext:
    """Context about a user's subscription."""
    customer_id: Optional[str] = None
    session_id: Optional[str] = None
    tier: SubscriptionTier = SubscriptionTier.FREE
    npc_count: int = 0
    emotion_calc_count: int = 0
    tts_char_count: int = 0
    api_call_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "session_id": self.session_id,
            "tier": self.tier.value,
            "npc_count": self.npc_count,
            "emotion_calc_count": self.emotion_calc_count,
            "tts_char_count": self.tts_char_count,
            "api_call_count": self.api_call_count,
        }


class SubscriptionMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for subscription enforcement.
    
    Applies to specific endpoints based on resource type.
    Supports both per-session and per-customer limits.
    
    Example:
        >>> app.add_middleware(
        ...     SubscriptionMiddleware,
        ...     stripe_service=stripe_service,
        ...     usage_tracker=usage_tracker,
        ... )
    """
    
    # Endpoints that require resource checks
    NPC_CREATION_PATHS = [
        "/api/game/npc",
        "/api/soul/npc",
    ]
    
    EMOTION_CALC_PATHS = [
        "/api/game/npc/{npc_id}/event",
        "/api/emotion/calculate",
    ]
    
    TTS_PATHS = [
        "/api/voice/tts",
        "/api/voice/speak",
    ]
    
    MEMORY_PATHS = [
        "/api/memory/store",
        "/api/memory/l1",
        "/api/memory/l2",
    ]
    
    def __init__(
        self,
        app,
        stripe_service: Optional[StripeService] = None,
        usage_tracker: Optional[UsageTracker] = None,
        bypass_paths: Optional[List[str]] = None,
    ):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI app
            stripe_service: Stripe service instance
            usage_tracker: Usage tracker instance
            bypass_paths: Paths to skip middleware (e.g., health checks)
        """
        super().__init__(app)
        self._stripe = stripe_service or get_stripe_service()
        self._usage = usage_tracker or get_usage_tracker()
        self._bypass_paths = bypass_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/billing/webhook",  # Webhooks have their own auth
        ]
        
        # Cache for customer tiers (simple in-memory cache)
        self._tier_cache: Dict[str, tuple[SubscriptionTier, float]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    def _get_tier_from_cache(self, customer_id: str) -> Optional[SubscriptionTier]:
        """Get cached tier if valid."""
        if customer_id in self._tier_cache:
            tier, cached_at = self._tier_cache[customer_id]
            import time
            if time.time() - cached_at < self._cache_ttl:
                return tier
            del self._tier_cache[customer_id]
        return None
    
    def _set_tier_cache(self, customer_id: str, tier: SubscriptionTier):
        """Cache tier."""
        import time
        self._tier_cache[customer_id] = (tier, time.time())
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request with subscription checks."""
        path = request.url.path
        
        # Bypass certain paths
        for bypass in self._bypass_paths:
            if path.startswith(bypass):
                return await call_next(request)
        
        # Extract identifiers
        session_id = self._get_session_id(request)
        customer_id = self._get_customer_id(request)
        
        # Get subscription context
        context = await self._get_subscription_context(session_id, customer_id)
        
        # Store context in request state for downstream handlers
        request.state.subscription_context = context
        
        # Apply resource checks based on endpoint
        try:
            # NPC creation check
            if self._is_npc_creation(request):
                self._check_npc_limit(context, session_id)
            
            # Emotion calculation check
            elif self._is_emotion_calc(request):
                self._check_emotion_limit(context, session_id)
            
            # TTS check
            elif self._is_tts_request(request):
                self._check_tts_limit(context, session_id)
            
            # Memory level check
            elif self._is_memory_request(request):
                self._check_memory_access(request, context)
            
        except RateLimitExceeded as e:
            return self._create_limit_response(e, context)
        
        # Process request
        response = await call_next(request)
        
        # Track usage after successful request
        await self._track_request_usage(request, session_id, context)
        
        return response
    
    def _get_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from request."""
        # Try query param
        session_id = request.query_params.get("session_id")
        if session_id:
            return session_id
        
        # Try header
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            return session_id
        
        # Try cookie
        session_id = request.cookies.get("session_id")
        if session_id:
            return session_id
        
        return None
    
    def _get_customer_id(self, request: Request) -> Optional[str]:
        """Extract customer ID from request."""
        # Try header
        customer_id = request.headers.get("X-Customer-ID")
        if customer_id:
            return customer_id
        
        # Try auth token/session (would be extracted from JWT in production)
        auth = request.headers.get("Authorization")
        if auth:
            # In production, decode JWT and extract customer_id
            pass
        
        return None
    
    async def _get_subscription_context(
        self,
        session_id: Optional[str],
        customer_id: Optional[str],
    ) -> SubscriptionContext:
        """Build subscription context for request."""
        context = SubscriptionContext(
            session_id=session_id,
            customer_id=customer_id,
        )
        
        # Default to free tier
        context.tier = SubscriptionTier.FREE
        
        # Get tier from customer subscription
        if customer_id:
            # Check cache first
            cached_tier = self._get_tier_from_cache(customer_id)
            if cached_tier:
                context.tier = cached_tier
            else:
                subscription = self._stripe.get_subscription(customer_id)
                if subscription:
                    try:
                        context.tier = SubscriptionTier(subscription.tier)
                        self._set_tier_cache(customer_id, context.tier)
                    except ValueError:
                        context.tier = SubscriptionTier.FREE
        
        # Get current usage
        if session_id:
            usage = self._usage.get_monthly_usage(session_id)
            context.npc_count = usage.npc_count
            context.emotion_calc_count = usage.emotion_calc_count
            context.tts_char_count = usage.tts_char_count
            context.api_call_count = usage.api_call_count
        
        return context
    
    def _is_npc_creation(self, request: Request) -> bool:
        """Check if request is creating an NPC."""
        return (
            request.method == "POST" and
            any(path in request.url.path for path in self.NPC_CREATION_PATHS)
        )
    
    def _is_emotion_calc(self, request: Request) -> bool:
        """Check if request is an emotion calculation."""
        return any(
            request.url.path.startswith(path)
            for path in self.EMOTION_CALC_PATHS
        )
    
    def _is_tts_request(self, request: Request) -> bool:
        """Check if request is TTS."""
        return any(
            path in request.url.path
            for path in self.TTS_PATHS
        )
    
    def _is_memory_request(self, request: Request) -> bool:
        """Check if request is accessing memory."""
        return (
            request.method in ("POST", "GET") and
            any(path in request.url.path for path in self.MEMORY_PATHS)
        )
    
    def _check_npc_limit(
        self,
        context: SubscriptionContext,
        session_id: Optional[str],
    ):
        """Check NPC creation limit."""
        plan = get_plan(context.tier.value)
        if not plan:
            return
        
        if session_id:
            if self._usage.check_limit_reached(
                session_id,
                ResourceType.NPC_COUNT,
                plan.npc_limit,
            ):
                raise RateLimitExceeded(
                    resource_type="npc",
                    current_usage=context.npc_count,
                    limit=plan.npc_limit,
                    message=f"NPC limit reached ({plan.npc_limit}). Upgrade to create more NPCs.",
                )
    
    def _check_emotion_limit(
        self,
        context: SubscriptionContext,
        session_id: Optional[str],
    ):
        """Check emotion calculation limit."""
        plan = get_plan(context.tier.value)
        if not plan:
            return
        
        if session_id:
            if self._usage.check_limit_reached(
                session_id,
                ResourceType.EMOTION_CALC,
                plan.emotion_calc_limit,
            ):
                raise RateLimitExceeded(
                    resource_type="emotion_calc",
                    current_usage=context.emotion_calc_count,
                    limit=plan.emotion_calc_limit,
                    message=f"Emotion calculation limit reached. Upgrade for more.",
                )
    
    def _check_tts_limit(
        self,
        context: SubscriptionContext,
        session_id: Optional[str],
    ):
        """Check TTS character limit."""
        plan = get_plan(context.tier.value)
        if not plan:
            return
        
        # Check if tier has TTS access
        if plan.tts_provider == TTSProvider.NONE:
            raise RateLimitExceeded(
                resource_type="tts",
                current_usage=0,
                limit=0,
                message="TTS not available on Free tier. Upgrade to Indie or higher.",
            )
        
        if session_id:
            if self._usage.check_limit_reached(
                session_id,
                ResourceType.TTS_CHAR,
                plan.tts_char_limit,
            ):
                raise RateLimitExceeded(
                    resource_type="tts_char",
                    current_usage=context.tts_char_count,
                    limit=plan.tts_char_limit,
                    message="TTS character limit reached. Upgrade or purchase additional characters.",
                )
    
    def _check_memory_access(
        self,
        request: Request,
        context: SubscriptionContext,
    ):
        """Check memory level access."""
        # Determine requested memory level from path
        if "/api/memory/l1" in request.url.path:
            required_level = "L1"
        elif "/api/memory/l2" in request.url.path:
            required_level = "L2"
        elif "/api/memory/store" in request.url.path:
            # Check request body for memory level
            required_level = self._get_memory_level_from_body(request)
        else:
            return
        
        if required_level and not has_memory_level(context.tier.value, required_level):
            available_levels = get_memory_levels(context.tier.value)
            raise RateLimitExceeded(
                resource_type="memory",
                current_usage=0,
                limit=0,
                message=f"Memory level {required_level} not available on {context.tier.value.title()} tier. Available: {', '.join(available_levels)}",
            )
    
    async def _get_memory_level_from_body(self, request: Request) -> Optional[str]:
        """Extract memory level from request body."""
        try:
            body = await request.body()
            if body:
                import json
                data = json.loads(body)
                return data.get("level") or data.get("memory_level")
        except Exception:
            pass
        return None
    
    def _create_limit_response(
        self,
        error: RateLimitExceeded,
        context: SubscriptionContext,
    ) -> JSONResponse:
        """Create 429 response for limit exceeded."""
        upgrade_url = f"/api/billing/plans"
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "limit_exceeded",
                "resource_type": error.resource_type,
                "current_usage": error.current_usage,
                "limit": error.limit,
                "message": error.message,
                "tier": context.tier.value,
                "upgrade_url": upgrade_url,
                "retry_after": 60,  # Suggest retry after 60 seconds
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Resource": error.resource_type,
                "X-RateLimit-Limit": str(error.limit),
                "X-RateLimit-Remaining": str(max(0, error.limit - error.current_usage)),
            },
        )
    
    async def _track_request_usage(
        self,
        request: Request,
        session_id: Optional[str],
        context: SubscriptionContext,
    ):
        """Track API call usage after successful request."""
        if not session_id:
            return
        
        # Track API calls
        self._usage.track_usage(
            session_id,
            ResourceType.API_CALL,
            1,
            metadata={"path": request.url.path, "method": request.method},
        )
        
        # Track emotion calculations
        if self._is_emotion_calc(request):
            self._usage.track_usage(
                session_id,
                ResourceType.EMOTION_CALC,
                1,
            )
        
        # Track TTS characters (would need to extract from response)
        # This would typically be done in a response middleware
    
    def invalidate_cache(self, customer_id: str):
        """Invalidate tier cache for a customer."""
        if customer_id in self._tier_cache:
            del self._tier_cache[customer_id]


# ── Utility functions ─────────────────────────────────────────────────────────

def get_subscription_context(request: Request) -> Optional[SubscriptionContext]:
    """Get subscription context from request state."""
    return getattr(request.state, "subscription_context", None)


def require_subscription(
    request: Request,
    min_tier: SubscriptionTier = SubscriptionTier.INDIE,
) -> SubscriptionContext:
    """
    Require minimum subscription tier.
    
    Raises HTTPException if not met.
    """
    context = get_subscription_context(request)
    
    if not context:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Authentication required")
    
    tier_order = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.INDIE: 1,
        SubscriptionTier.STUDIO: 2,
        SubscriptionTier.ENTERPRISE: 3,
    }
    
    if tier_order.get(context.tier, 0) < tier_order.get(min_tier, 0):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail=f"This feature requires {min_tier.value.title()} tier or higher",
        )
    
    return context
