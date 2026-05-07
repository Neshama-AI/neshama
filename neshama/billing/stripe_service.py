# Billing - Stripe Service
"""
Stripe payment service integration.

Handles all Stripe API operations:
- Customer creation and management
- Checkout session creation
- Subscription management
- Portal access
- Webhook handling

All Stripe operations are mocked for testing.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import json
import hashlib
import time

logger = logging.getLogger(__name__)


class SubscriptionStatus(str, Enum):
    """Stripe subscription status values."""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    UNPAID = "unpaid"
    PAUSED = "paused"


@dataclass
class CustomerInfo:
    """Stripe customer information."""
    customer_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class SubscriptionInfo:
    """Stripe subscription information."""
    subscription_id: str
    customer_id: str
    status: SubscriptionStatus
    tier: str  # free, indie, studio, enterprise
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool = False
    cancel_at: Optional[str] = None
    trial_end: Optional[str] = None
    default_payment_method: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "customer_id": self.customer_id,
            "status": self.status.value,
            "tier": self.tier,
            "current_period_start": self.current_period_start,
            "current_period_end": self.current_period_end,
            "cancel_at_period_end": self.cancel_at_period_end,
            "cancel_at": self.cancel_at,
            "trial_end": self.trial_end,
            "default_payment_method": self.default_payment_method,
            "items": self.items,
            "metadata": self.metadata,
        }
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.PAST_DUE,  # Still active during grace period
        )
    
    @property
    def days_until_renewal(self) -> int:
        """Days until subscription renews."""
        end = datetime.fromisoformat(self.current_period_end)
        delta = end - datetime.now()
        return max(0, delta.days)


@dataclass
class CheckoutSessionInfo:
    """Stripe checkout session information."""
    session_id: str
    url: str
    customer_id: str
    subscription_id: Optional[str] = None
    payment_status: str = "unpaid"
    status: str = "open"
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "url": self.url,
            "customer_id": self.customer_id,
            "subscription_id": self.subscription_id,
            "payment_status": self.payment_status,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class RefundInfo:
    """Refund information."""
    refund_id: str
    amount_cents: int
    status: str
    reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class WebhookEventType(str, Enum):
    """Stripe webhook event types we handle."""
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    CUSTOMER_SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    CUSTOMER_SUBSCRIPTION_DELETED = "customer.subscription.deleted"
    INVOICE_PAYMENT_SUCCEEDED = "invoice.payment_succeeded"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"


@dataclass
class WebhookEvent:
    """Parsed webhook event."""
    event_id: str
    event_type: str
    data: Dict[str, Any]
    created_at: int  # Unix timestamp
    
    @classmethod
    def from_stripe_event(cls, payload: Dict[str, Any]) -> "WebhookEvent":
        return cls(
            event_id=payload.get("id", ""),
            event_type=payload.get("type", ""),
            data=payload.get("data", {}).get("object", {}),
            created_at=payload.get("created", int(time.time())),
        )


class StripeService:
    """
    Stripe API integration service.
    
    All methods are designed to be mockable for testing.
    In production, replace mock implementations with real Stripe SDK calls.
    
    Example:
        >>> service = StripeService()
        >>> 
        >>> # Create customer
        >>> customer = service.create_customer("user@example.com", "John Doe")
        >>> 
        >>> # Create checkout session
        >>> session = service.create_checkout_session(
        ...     customer_id=customer.customer_id,
        ...     price_id="price_studio_monthly"
        ... )
        >>> print(f"Checkout URL: {session.url}")
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        mock: bool = True,
    ):
        """
        Initialize StripeService.
        
        Args:
            secret_key: Stripe secret key (reads from env if not provided)
            webhook_secret: Webhook signature secret
            mock: If True, use mock implementations for testing
        """
        self._mock = mock
        self._secret_key = secret_key
        self._webhook_secret = webhook_secret
        
        # Mock data storage
        self._mock_customers: Dict[str, CustomerInfo] = {}
        self._mock_subscriptions: Dict[str, SubscriptionInfo] = {}
        self._mock_sessions: Dict[str, CheckoutSessionInfo] = {}
        self._webhook_handlers: Dict[str, List[Callable]] = {}
        
        logger.info(f"StripeService initialized (mock={mock})")
    
    def _generate_id(self, prefix: str) -> str:
        """Generate a mock Stripe ID."""
        timestamp = str(int(time.time() * 1000))
        hash_input = f"{prefix}_{timestamp}_{self._secret_key or ''}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:16]
        return f"{prefix}_{hash_value}"
    
    def _call_mock(self, operation: str, *args, **kwargs):
        """Call mock implementation."""
        mock_method = getattr(self, f"_mock_{operation}", None)
        if mock_method:
            return mock_method(*args, **kwargs)
        raise NotImplementedError(f"Mock for {operation} not implemented")
    
    # ── Customer Operations ────────────────────────────────────────────────────
    
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> CustomerInfo:
        """
        Create a Stripe customer.
        
        Args:
            email: Customer email address
            name: Customer name
            metadata: Optional metadata dict
            
        Returns:
            CustomerInfo with customer_id
        """
        if self._mock:
            return self._mock_create_customer(email, name, metadata)
        
        # Real Stripe implementation would go here
        # from stripe import Customer
        # customer = Customer.create(
        #     email=email,
        #     name=name,
        #     metadata=metadata or {},
        #     api_key=self._secret_key,
        # )
        # return CustomerInfo(
        #     customer_id=customer.id,
        #     email=customer.email,
        #     name=customer.name,
        #     created_at=datetime.fromtimestamp(customer.created).isoformat(),
        #     metadata=customer.metadata,
        # )
        raise NotImplementedError("Real Stripe implementation not provided")
    
    def _mock_create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> CustomerInfo:
        """Mock customer creation."""
        customer_id = self._generate_id("cus")
        customer = CustomerInfo(
            customer_id=customer_id,
            email=email,
            name=name,
            metadata=metadata or {},
        )
        self._mock_customers[customer_id] = customer
        logger.debug(f"Mock created customer: {customer_id}")
        return customer
    
    def get_customer(self, customer_id: str) -> Optional[CustomerInfo]:
        """
        Get customer information.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            CustomerInfo or None if not found
        """
        if self._mock:
            return self._mock_customers.get(customer_id)
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    def update_customer(
        self,
        customer_id: str,
        **kwargs,
    ) -> CustomerInfo:
        """
        Update customer information.
        
        Args:
            customer_id: Customer to update
            **kwargs: Fields to update (email, name, metadata, etc.)
            
        Returns:
            Updated CustomerInfo
        """
        if self._mock:
            customer = self._mock_customers.get(customer_id)
            if customer:
                if "email" in kwargs:
                    customer.email = kwargs["email"]
                if "name" in kwargs:
                    customer.name = kwargs["name"]
                if "metadata" in kwargs:
                    customer.metadata.update(kwargs["metadata"])
            return customer
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    # ── Checkout Session Operations ──────────────────────────────────────────
    
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        allow_promotion_codes: bool = True,
        billing_cycle_anchor: Optional[int] = None,
    ) -> CheckoutSessionInfo:
        """
        Create a Stripe Checkout session.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Price ID from Stripe Dashboard
            success_url: URL after successful payment
            cancel_url: URL after cancellation
            metadata: Optional metadata
            allow_promotion_codes: Whether to allow promo codes
            billing_cycle_anchor: Unix timestamp for billing start
            
        Returns:
            CheckoutSessionInfo with session URL
        """
        if self._mock:
            return self._mock_create_checkout_session(
                customer_id, price_id, success_url, cancel_url, metadata
            )
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    def _mock_create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> CheckoutSessionInfo:
        """Mock checkout session creation."""
        session_id = self._generate_id("cs")
        checkout_url = f"https://checkout.stripe.com/pay/{session_id}"
        
        session = CheckoutSessionInfo(
            session_id=session_id,
            url=checkout_url,
            customer_id=customer_id,
            metadata=metadata or {},
        )
        self._mock_sessions[session_id] = session
        logger.debug(f"Mock created checkout session: {session_id}")
        return session
    
    def get_checkout_session(self, session_id: str) -> Optional[CheckoutSessionInfo]:
        """Get checkout session by ID."""
        if self._mock:
            return self._mock_sessions.get(session_id)
        raise NotImplementedError("Real Stripe implementation not provided")
    
    # ── Subscription Operations ──────────────────────────────────────────────
    
    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, str]] = None,
        trial_period_days: Optional[int] = None,
        default_payment_method_id: Optional[str] = None,
    ) -> SubscriptionInfo:
        """
        Create a new subscription.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Price ID for the subscription
            metadata: Optional metadata
            trial_period_days: Days of trial (optional)
            default_payment_method_id: Payment method to use
            
        Returns:
            SubscriptionInfo
        """
        if self._mock:
            return self._mock_create_subscription(
                customer_id, price_id, metadata, trial_period_days
            )
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    def _mock_create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, str]] = None,
        trial_period_days: Optional[int] = None,
    ) -> SubscriptionInfo:
        """Mock subscription creation."""
        subscription_id = self._generate_id("sub")
        now = datetime.now()
        period_end = now
        
        if trial_period_days:
            period_end = now + timedelta(days=trial_period_days)
        else:
            period_end = now + timedelta(days=30)  # Monthly
        
        # Determine tier from price_id
        tier = "free"
        if "indie" in price_id:
            tier = "indie"
        elif "studio" in price_id:
            tier = "studio"
        elif "enterprise" in price_id:
            tier = "enterprise"
        
        subscription = SubscriptionInfo(
            subscription_id=subscription_id,
            customer_id=customer_id,
            status=SubscriptionStatus.TRIALING if trial_period_days else SubscriptionStatus.ACTIVE,
            tier=tier,
            current_period_start=now.isoformat(),
            current_period_end=period_end.isoformat(),
            trial_end=period_end.isoformat() if trial_period_days else None,
            items=[{"price_id": price_id}],
            metadata=metadata or {},
        )
        self._mock_subscriptions[subscription_id] = subscription
        logger.debug(f"Mock created subscription: {subscription_id}")
        return subscription
    
    def get_subscription(self, customer_id: str) -> Optional[SubscriptionInfo]:
        """
        Get current subscription for a customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            SubscriptionInfo or None
        """
        if self._mock:
            for sub in self._mock_subscriptions.values():
                if sub.customer_id == customer_id and sub.is_active:
                    return sub
            return None
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    def get_subscription_by_id(self, subscription_id: str) -> Optional[SubscriptionInfo]:
        """Get subscription by subscription ID."""
        if self._mock:
            return self._mock_subscriptions.get(subscription_id)
        raise NotImplementedError("Real Stripe implementation not provided")
    
    def update_subscription(
        self,
        subscription_id: str,
        new_price_id: Optional[str] = None,
        prorate: bool = True,
        metadata: Optional[Dict[str, str]] = None,
    ) -> SubscriptionInfo:
        """
        Update subscription (change plan).
        
        Args:
            subscription_id: Subscription to update
            new_price_id: New price ID (for upgrade/downgrade)
            prorate: Whether to prorate charges
            metadata: Optional metadata updates
            
        Returns:
            Updated SubscriptionInfo
        """
        if self._mock:
            sub = self._mock_subscriptions.get(subscription_id)
            if sub and new_price_id:
                # Update tier based on new price
                if "indie" in new_price_id:
                    sub.tier = "indie"
                elif "studio" in new_price_id:
                    sub.tier = "studio"
                elif "enterprise" in new_price_id:
                    sub.tier = "enterprise"
                sub.items = [{"price_id": new_price_id}]
            if sub and metadata:
                sub.metadata.update(metadata)
            return sub
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True,
        reason: Optional[str] = None,
    ) -> SubscriptionInfo:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Subscription to cancel
            cancel_at_period_end: If True, cancel at end of period
                                   If False, cancel immediately
            reason: Optional cancellation reason
            
        Returns:
            Updated SubscriptionInfo
        """
        if self._mock:
            sub = self._mock_subscriptions.get(subscription_id)
            if sub:
                if cancel_at_period_end:
                    sub.cancel_at_period_end = True
                    sub.cancel_at = sub.current_period_end
                else:
                    sub.status = SubscriptionStatus.CANCELED
                if reason:
                    sub.metadata["cancel_reason"] = reason
            return sub
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    def reactivate_subscription(self, subscription_id: str) -> SubscriptionInfo:
        """
        Reactivate a canceled subscription.
        
        Args:
            subscription_id: Subscription to reactivate
            
        Returns:
            Updated SubscriptionInfo
        """
        if self._mock:
            sub = self._mock_subscriptions.get(subscription_id)
            if sub:
                sub.cancel_at_period_end = False
                sub.cancel_at = None
                sub.status = SubscriptionStatus.ACTIVE
            return sub
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    # ── Customer Portal ────────────────────────────────────────────────────────
    
    def create_portal_session(
        self,
        customer_id: str,
        return_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Create a customer portal session.
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal
            
        Returns:
            Dict with portal_url
        """
        if self._mock:
            portal_url = f"https://billing.stripe.com/session/{customer_id}"
            return {"url": portal_url}
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    # ── Refund Operations ─────────────────────────────────────────────────────
    
    def create_refund(
        self,
        payment_intent_id: str,
        amount_cents: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> RefundInfo:
        """
        Create a refund.
        
        Args:
            payment_intent_id: Payment intent to refund
            amount_cents: Amount to refund (None = full refund)
            reason: Reason for refund
            
        Returns:
            RefundInfo
        """
        if self._mock:
            refund_id = self._generate_id("re")
            return RefundInfo(
                refund_id=refund_id,
                amount_cents=amount_cents or 0,
                status="succeeded",
                reason=reason,
            )
        
        raise NotImplementedError("Real Stripe implementation not provided")
    
    # ── Webhook Handling ──────────────────────────────────────────────────────
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> Dict[str, Any]:
        """
        Verify webhook signature and return event data.
        
        Args:
            payload: Raw request body
            signature: Stripe-Signature header value
            
        Returns:
            Parsed event dict
            
        Raises:
            ValueError: If signature verification fails
        """
        if self._mock:
            # In mock mode, just parse JSON
            return json.loads(payload)
        
        # Real implementation would use stripe.Webhook.construct_event
        raise NotImplementedError("Real Stripe implementation not provided")
    
    def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Handle a webhook event.
        
        Dispatches to registered handlers based on event type.
        
        Args:
            event: WebhookEvent to process
            
        Returns:
            Dict with processing result
        """
        logger.info(f"Handling webhook event: {event.event_type}")
        
        handlers = self._webhook_handlers.get(event.event_type, [])
        
        results = []
        for handler in handlers:
            try:
                result = handler(event)
                results.append({"success": True, "result": result})
            except Exception as e:
                logger.error(f"Webhook handler error: {e}")
                results.append({"success": False, "error": str(e)})
        
        # Default handling based on event type
        if event.event_type == WebhookEventType.CHECKOUT_SESSION_COMPLETED.value:
            return self._handle_checkout_completed(event)
        elif event.event_type == WebhookEventType.CUSTOMER_SUBSCRIPTION_UPDATED.value:
            return self._handle_subscription_updated(event)
        elif event.event_type == WebhookEventType.CUSTOMER_SUBSCRIPTION_DELETED.value:
            return self._handle_subscription_deleted(event)
        elif event.event_type == WebhookEventType.INVOICE_PAYMENT_SUCCEEDED.value:
            return self._handle_payment_succeeded(event)
        elif event.event_type == WebhookEventType.INVOICE_PAYMENT_FAILED.value:
            return self._handle_payment_failed(event)
        
        return {"processed": True, "handlers": len(results)}
    
    def register_webhook_handler(
        self,
        event_type: str,
        handler: Callable[[WebhookEvent], Any],
    ) -> None:
        """Register a webhook handler."""
        if event_type not in self._webhook_handlers:
            self._webhook_handlers[event_type] = []
        self._webhook_handlers[event_type].append(handler)
    
    def _handle_checkout_completed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle checkout.session.completed event."""
        session_id = event.data.get("id")
        customer_id = event.data.get("customer")
        subscription_id = event.data.get("subscription")
        
        logger.info(
            f"Checkout completed: session={session_id}, "
            f"customer={customer_id}, subscription={subscription_id}"
        )
        
        return {
            "event_type": "checkout.session.completed",
            "session_id": session_id,
            "customer_id": customer_id,
            "subscription_id": subscription_id,
        }
    
    def _handle_subscription_updated(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle customer.subscription.updated event."""
        sub_id = event.data.get("id")
        status = event.data.get("status")
        
        logger.info(f"Subscription updated: {sub_id} -> {status}")
        
        # Update mock subscription
        if self._mock and sub_id in self._mock_subscriptions:
            sub = self._mock_subscriptions[sub_id]
            sub.status = SubscriptionStatus(status)
        
        return {
            "event_type": "customer.subscription.updated",
            "subscription_id": sub_id,
            "status": status,
        }
    
    def _handle_subscription_deleted(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle customer.subscription.deleted event."""
        sub_id = event.data.get("id")
        
        logger.info(f"Subscription deleted: {sub_id}")
        
        # Update mock subscription
        if self._mock and sub_id in self._mock_subscriptions:
            self._mock_subscriptions[sub_id].status = SubscriptionStatus.CANCELED
        
        return {
            "event_type": "customer.subscription.deleted",
            "subscription_id": sub_id,
        }
    
    def _handle_payment_succeeded(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle invoice.payment_succeeded event."""
        customer_id = event.data.get("customer")
        
        logger.info(f"Payment succeeded for customer: {customer_id}")
        
        return {
            "event_type": "invoice.payment_succeeded",
            "customer_id": customer_id,
        }
    
    def _handle_payment_failed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle invoice.payment_failed event."""
        customer_id = event.data.get("customer")
        
        logger.warning(f"Payment failed for customer: {customer_id}")
        
        return {
            "event_type": "invoice.payment_failed",
            "customer_id": customer_id,
        }
    
    # ── Mock Helpers ───────────────────────────────────────────────────────────
    
    def set_mock_subscription(
        self,
        customer_id: str,
        tier: str = "free",
        status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
    ) -> SubscriptionInfo:
        """Helper to set up mock subscription for testing."""
        price_map = {
            "free": None,
            "indie": "price_indie_monthly",
            "studio": "price_studio_monthly",
            "enterprise": "price_enterprise_monthly",
        }
        
        if tier == "free":
            return None
        
        return self._mock_create_subscription(
            customer_id=customer_id,
            price_id=price_map.get(tier, "price_indie_monthly"),
        )


# Import timedelta for mock methods
from datetime import timedelta

# ── Global instance ───────────────────────────────────────────────────────────

_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get the global StripeService instance."""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService(mock=True)
    return _stripe_service
