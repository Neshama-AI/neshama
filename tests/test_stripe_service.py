# Tests - Stripe Service
"""
Tests for Stripe service integration.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from neshama.billing.stripe_service import (
    StripeService,
    SubscriptionStatus,
    SubscriptionInfo,
    CustomerInfo,
    CheckoutSessionInfo,
    WebhookEvent,
    WebhookEventType,
    RefundInfo,
)


class TestStripeService:
    """Test StripeService class."""
    
    @pytest.fixture
    def service(self):
        """Create StripeService in mock mode."""
        return StripeService(mock=True)
    
    # ── Customer Tests ─────────────────────────────────────────────────────────
    
    def test_create_customer(self, service):
        """Test customer creation."""
        customer = service.create_customer(
            email="test@example.com",
            name="Test User",
            metadata={"source": "test"}
        )
        
        assert customer.customer_id is not None
        assert customer.customer_id.startswith("cus_")
        assert customer.email == "test@example.com"
        assert customer.name == "Test User"
        assert customer.metadata["source"] == "test"
    
    def test_get_customer(self, service):
        """Test getting existing customer."""
        created = service.create_customer(email="test@example.com")
        
        retrieved = service.get_customer(created.customer_id)
        
        assert retrieved is not None
        assert retrieved.customer_id == created.customer_id
        assert retrieved.email == "test@example.com"
    
    def test_get_nonexistent_customer(self, service):
        """Test getting non-existent customer returns None."""
        result = service.get_customer("cus_nonexistent")
        assert result is None
    
    def test_update_customer(self, service):
        """Test customer update."""
        customer = service.create_customer(email="test@example.com")
        
        updated = service.update_customer(
            customer.customer_id,
            email="new@example.com",
            name="New Name"
        )
        
        assert updated.email == "new@example.com"
        assert updated.name == "New Name"
    
    # ── Checkout Session Tests ─────────────────────────────────────────────────
    
    def test_create_checkout_session(self, service):
        """Test checkout session creation."""
        customer = service.create_customer(email="test@example.com")
        
        session = service.create_checkout_session(
            customer_id=customer.customer_id,
            price_id="price_test"
        )
        
        assert session.session_id is not None
        assert session.session_id.startswith("cs_")
        assert session.customer_id == customer.customer_id
        assert session.url.startswith("https://checkout.stripe.com")
    
    def test_get_checkout_session(self, service):
        """Test getting checkout session."""
        customer = service.create_customer(email="test@example.com")
        created = service.create_checkout_session(
            customer_id=customer.customer_id,
            price_id="price_test"
        )
        
        retrieved = service.get_checkout_session(created.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == created.session_id
    
    # ── Subscription Tests ──────────────────────────────────────────────────────
    
    def test_create_subscription_indie(self, service):
        """Test subscription creation for indie tier."""
        customer = service.create_customer(email="test@example.com")
        
        subscription = service.create_subscription(
            customer_id=customer.customer_id,
            price_id="price_indie_monthly"
        )
        
        assert subscription.subscription_id.startswith("sub_")
        assert subscription.customer_id == customer.customer_id
        assert subscription.tier == "indie"
        assert subscription.status == SubscriptionStatus.ACTIVE
    
    def test_create_subscription_studio(self, service):
        """Test subscription creation for studio tier."""
        customer = service.create_customer(email="test@example.com")
        
        subscription = service.create_subscription(
            customer_id=customer.customer_id,
            price_id="price_studio_monthly"
        )
        
        assert subscription.tier == "studio"
    
    def test_create_subscription_with_trial(self, service):
        """Test subscription creation with trial period."""
        customer = service.create_customer(email="test@example.com")
        
        subscription = service.create_subscription(
            customer_id=customer.customer_id,
            price_id="price_indie_monthly",
            trial_period_days=14
        )
        
        assert subscription.status == SubscriptionStatus.TRIALING
        assert subscription.trial_end is not None
    
    def test_get_subscription(self, service):
        """Test getting subscription for customer."""
        customer = service.create_customer(email="test@example.com")
        created = service.create_subscription(
            customer_id=customer.customer_id,
            price_id="price_indie_monthly"
        )
        
        subscription = service.get_subscription(customer.customer_id)
        
        assert subscription is not None
        assert subscription.subscription_id == created.subscription_id
    
    def test_get_subscription_no_subscription(self, service):
        """Test getting subscription when none exists."""
        customer = service.create_customer(email="test@example.com")
        
        subscription = service.get_subscription(customer.customer_id)
        
        assert subscription is None
    
    def test_update_subscription(self, service):
        """Test subscription upgrade."""
        customer = service.create_customer(email="test@example.com")
        subscription = service.create_subscription(
            customer_id=customer.customer_id,
            price_id="price_indie_monthly"
        )
        
        updated = service.update_subscription(
            subscription.subscription_id,
            new_price_id="price_studio_monthly"
        )
        
        assert updated.tier == "studio"
    
    def test_cancel_subscription_at_period_end(self, service):
        """Test canceling subscription at period end."""
        customer = service.create_customer(email="test@example.com")
        subscription = service.create_subscription(
            customer_id=customer.customer_id,
            price_id="price_indie_monthly"
        )
        
        canceled = service.cancel_subscription(
            subscription.subscription_id,
            cancel_at_period_end=True
        )
        
        assert canceled.cancel_at_period_end is True
        assert canceled.cancel_at == canceled.current_period_end
    
    def test_cancel_subscription_immediately(self, service):
        """Test canceling subscription immediately."""
        customer = service.create_customer(email="test@example.com")
        subscription = service.create_subscription(
            customer_id=customer.customer_id,
            price_id="price_indie_monthly"
        )
        
        canceled = service.cancel_subscription(
            subscription.subscription_id,
            cancel_at_period_end=False
        )
        
        assert canceled.status == SubscriptionStatus.CANCELED
    
    def test_reactivate_subscription(self, service):
        """Test reactivating canceled subscription."""
        customer = service.create_customer(email="test@example.com")
        subscription = service.create_subscription(
            customer_id=customer.customer_id,
            price_id="price_indie_monthly"
        )
        
        # Cancel first
        service.cancel_subscription(
            subscription.subscription_id,
            cancel_at_period_end=True
        )
        
        # Reactivate
        reactivated = service.reactivate_subscription(subscription.subscription_id)
        
        assert reactivated.cancel_at_period_end is False
        assert reactivated.status == SubscriptionStatus.ACTIVE
    
    # ── Portal Tests ────────────────────────────────────────────────────────────
    
    def test_create_portal_session(self, service):
        """Test creating customer portal session."""
        customer = service.create_customer(email="test@example.com")
        
        result = service.create_portal_session(
            customer_id=customer.customer_id,
            return_url="https://example.com/return"
        )
        
        assert "url" in result
        assert customer.customer_id in result["url"]
    
    # ── Refund Tests ───────────────────────────────────────────────────────────
    
    def test_create_refund(self, service):
        """Test creating a refund."""
        refund = service.create_refund(
            payment_intent_id="pi_test",
            amount_cents=1900,
            reason="Customer request"
        )
        
        assert refund.refund_id.startswith("re_")
        assert refund.amount_cents == 1900
        assert refund.status == "succeeded"
        assert refund.reason == "Customer request"
    
    # ── Webhook Tests ──────────────────────────────────────────────────────────
    
    def test_verify_webhook_signature(self, service):
        """Test webhook signature verification (mock mode)."""
        payload = json.dumps({
            "id": "evt_test",
            "type": "checkout.session.completed",
            "data": {"object": {}}
        }).encode()
        
        result = service.verify_webhook_signature(
            payload,
            "test_signature"
        )
        
        assert result["id"] == "evt_test"
        assert result["type"] == "checkout.session.completed"
    
    def test_handle_checkout_completed(self, service):
        """Test handling checkout completed webhook."""
        event = WebhookEvent(
            event_id="evt_1",
            event_type=WebhookEventType.CHECKOUT_SESSION_COMPLETED.value,
            data={
                "id": "cs_test",
                "customer": "cus_test",
                "subscription": "sub_test"
            },
            created_at=int(datetime.now().timestamp())
        )
        
        result = service.handle_webhook(event)
        
        assert result["event_type"] == "checkout.session.completed"
        assert result["session_id"] == "cs_test"
        assert result["customer_id"] == "cus_test"
    
    def test_handle_subscription_deleted(self, service):
        """Test handling subscription deleted webhook."""
        event = WebhookEvent(
            event_id="evt_1",
            event_type=WebhookEventType.CUSTOMER_SUBSCRIPTION_DELETED.value,
            data={"id": "sub_test"},
            created_at=int(datetime.now().timestamp())
        )
        
        result = service.handle_webhook(event)
        
        assert result["event_type"] == "customer.subscription.deleted"
        assert result["subscription_id"] == "sub_test"
    
    def test_register_webhook_handler(self, service):
        """Test registering custom webhook handler."""
        called = []
        
        def handler(event):
            called.append(event)
            return "handled"
        
        service.register_webhook_handler(
            WebhookEventType.CHECKOUT_SESSION_COMPLETED.value,
            handler
        )
        
        event = WebhookEvent(
            event_id="evt_1",
            event_type=WebhookEventType.CHECKOUT_SESSION_COMPLETED.value,
            data={},
            created_at=int(datetime.now().timestamp())
        )
        
        result = service.handle_webhook(event)
        
        assert len(called) == 1
        assert called[0].event_id == "evt_1"


class TestSubscriptionInfo:
    """Test SubscriptionInfo dataclass."""
    
    def test_is_active(self):
        """Test is_active property."""
        active = SubscriptionInfo(
            subscription_id="sub_1",
            customer_id="cus_1",
            status=SubscriptionStatus.ACTIVE,
            tier="indie",
            current_period_start=datetime.now().isoformat(),
            current_period_end=(datetime.now() + timedelta(days=30)).isoformat(),
        )
        assert active.is_active is True
        
        canceled = SubscriptionInfo(
            subscription_id="sub_1",
            customer_id="cus_1",
            status=SubscriptionStatus.CANCELED,
            tier="indie",
            current_period_start=datetime.now().isoformat(),
            current_period_end=(datetime.now() + timedelta(days=30)).isoformat(),
        )
        assert canceled.is_active is False
    
    def test_days_until_renewal(self):
        """Test days_until_renewal calculation."""
        info = SubscriptionInfo(
            subscription_id="sub_1",
            customer_id="cus_1",
            status=SubscriptionStatus.ACTIVE,
            tier="indie",
            current_period_start=datetime.now().isoformat(),
            current_period_end=(datetime.now() + timedelta(days=15)).isoformat(),
        )
        
        assert 14 <= info.days_until_renewal <= 15
    
    def test_to_dict(self):
        """Test serialization."""
        info = SubscriptionInfo(
            subscription_id="sub_1",
            customer_id="cus_1",
            status=SubscriptionStatus.ACTIVE,
            tier="indie",
            current_period_start=datetime.now().isoformat(),
            current_period_end=(datetime.now() + timedelta(days=30)).isoformat(),
        )
        
        data = info.to_dict()
        
        assert data["subscription_id"] == "sub_1"
        assert data["tier"] == "indie"
        assert data["status"] == "active"


class TestCustomerInfo:
    """Test CustomerInfo dataclass."""
    
    def test_to_dict(self):
        """Test serialization."""
        customer = CustomerInfo(
            customer_id="cus_1",
            email="test@example.com",
            name="Test User",
            metadata={"key": "value"}
        )
        
        data = customer.to_dict()
        
        assert data["customer_id"] == "cus_1"
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["metadata"]["key"] == "value"


class TestCheckoutSessionInfo:
    """Test CheckoutSessionInfo dataclass."""
    
    def test_to_dict(self):
        """Test serialization."""
        session = CheckoutSessionInfo(
            session_id="cs_1",
            url="https://checkout.stripe.com/cs_test",
            customer_id="cus_1",
            subscription_id="sub_1"
        )
        
        data = session.to_dict()
        
        assert data["session_id"] == "cs_1"
        assert data["url"] == "https://checkout.stripe.com/cs_test"
        assert data["customer_id"] == "cus_1"
        assert data["subscription_id"] == "sub_1"


class TestWebhookEvent:
    """Test WebhookEvent dataclass."""
    
    def test_from_stripe_event(self):
        """Test creation from Stripe event payload."""
        payload = {
            "id": "evt_123",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_123"}},
            "created": 1700000000
        }
        
        event = WebhookEvent.from_stripe_event(payload)
        
        assert event.event_id == "evt_123"
        assert event.event_type == "checkout.session.completed"
        assert event.data["id"] == "cs_123"
        assert event.created_at == 1700000000


class TestSubscriptionStatus:
    """Test SubscriptionStatus enum."""
    
    def test_all_statuses(self):
        """Test all status values exist."""
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.PAST_DUE.value == "past_due"
        assert SubscriptionStatus.CANCELED.value == "canceled"
        assert SubscriptionStatus.INCOMPLETE.value == "incomplete"
        assert SubscriptionStatus.TRIALING.value == "trialing"
        assert SubscriptionStatus.UNPAID.value == "unpaid"
