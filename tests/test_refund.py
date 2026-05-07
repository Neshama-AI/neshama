# Tests - Refund Service
"""
Tests for refund processing and policy enforcement.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from neshama.billing.refund import (
    RefundService,
    RefundStatus,
    RefundType,
    RefundRequest,
    RefundResult,
    REFUND_WINDOW_DAYS,
    MAX_REFUND_DAYS,
)


class TestRefundService:
    """Test RefundService class."""
    
    @pytest.fixture
    def mock_stripe(self):
        """Create mock Stripe service."""
        stripe = MagicMock()
        stripe.get_subscription_by_id.return_value = MagicMock(
            subscription_id="sub_123",
            customer_id="cus_123",
            tier="indie",
            current_period_start=(datetime.now() - timedelta(days=5)).isoformat(),
            current_period_end=(datetime.now() + timedelta(days=25)).isoformat(),
        )
        stripe.get_subscription.return_value = MagicMock(
            subscription_id="sub_123",
            customer_id="cus_123",
            tier="indie",
        )
        return stripe
    
    @pytest.fixture
    def service(self, mock_stripe):
        """Create RefundService with mocked Stripe."""
        return RefundService(stripe_service=mock_stripe)
    
    # ── Policy Constants ───────────────────────────────────────────────────────
    
    def test_refund_window_days(self):
        """Test refund window constant."""
        assert REFUND_WINDOW_DAYS == 14
    
    def test_max_refund_days(self):
        """Test max refund days constant."""
        assert MAX_REFUND_DAYS == 30
    
    # ── Eligibility Tests ──────────────────────────────────────────────────────
    
    def test_validate_eligibility_within_window(self, service, mock_stripe):
        """Test eligibility within 14-day window."""
        # Set up subscription created 5 days ago
        mock_stripe.get_subscription_by_id.return_value = MagicMock(
            subscription_id="sub_123",
            customer_id="cus_123",
            tier="indie",
            current_period_start=(datetime.now() - timedelta(days=5)).isoformat(),
            current_period_end=(datetime.now() + timedelta(days=25)).isoformat(),
        )
        mock_stripe.get_subscription.return_value = mock_stripe.get_subscription_by_id.return_value
        
        eligibility = service.validate_refund_eligibility("cus_123")
        
        assert eligibility["eligible"] is True
        assert eligibility["refund_type"] == "full"
        assert eligibility["estimated_amount"] == 19.0  # Full $19
    
    def test_validate_eligibility_after_window(self, service, mock_stripe):
        """Test eligibility after 14-day window (pro-rated)."""
        mock_stripe.get_subscription_by_id.return_value = MagicMock(
            subscription_id="sub_123",
            customer_id="cus_123",
            tier="indie",
            current_period_start=(datetime.now() - timedelta(days=20)).isoformat(),
            current_period_end=(datetime.now() + timedelta(days=10)).isoformat(),
        )
        mock_stripe.get_subscription.return_value = mock_stripe.get_subscription_by_id.return_value
        
        eligibility = service.validate_refund_eligibility("cus_123")
        
        assert eligibility["eligible"] is True
        assert eligibility["refund_type"] == "pro_rated"
        # Pro-rated based on remaining days
    
    def test_validate_eligibility_no_subscription(self, service, mock_stripe):
        """Test eligibility with no subscription."""
        mock_stripe.get_subscription.return_value = None
        
        eligibility = service.validate_refund_eligibility("cus_123")
        
        assert eligibility["eligible"] is False
        assert "No active subscription" in eligibility["reason"]
    
    def test_validate_eligibility_already_refunded(self, service):
        """Test eligibility when refund already in progress."""
        # Create a pending refund request
        service._requests["refreq_123"] = RefundRequest(
            request_id="refreq_123",
            customer_id="cus_123",
            subscription_id="sub_123",
            refund_type=RefundType.FULL,
            requested_amount_cents=1900,
            reason="Test",
            status=RefundStatus.PENDING,
        )
        
        eligibility = service.validate_refund_eligibility("cus_123")
        
        assert eligibility["eligible"] is False
        assert "already in progress" in eligibility["reason"]
    
    def test_validate_eligibility_too_old(self, service, mock_stripe):
        """Test eligibility when subscription too old."""
        mock_stripe.get_subscription_by_id.return_value = MagicMock(
            subscription_id="sub_123",
            customer_id="cus_123",
            tier="indie",
            current_period_start=(datetime.now() - timedelta(days=45)).isoformat(),
            current_period_end=(datetime.now() + timedelta(days=1)).isoformat(),
        )
        mock_stripe.get_subscription.return_value = mock_stripe.get_subscription_by_id.return_value
        
        eligibility = service.validate_refund_eligibility("cus_123")
        
        assert eligibility["eligible"] is False
        assert "days old" in eligibility["reason"]
    
    # ── Refund Request Tests ───────────────────────────────────────────────────
    
    def test_request_refund(self, service):
        """Test creating refund request."""
        request = service.request_refund(
            customer_id="cus_123",
            reason="Not satisfied"
        )
        
        assert request.request_id.startswith("refreq_")
        assert request.customer_id == "cus_123"
        assert request.reason == "Not satisfied"
        assert request.status == RefundStatus.PENDING
    
    def test_request_refund_with_notes(self, service):
        """Test creating refund request with notes."""
        request = service.request_refund(
            customer_id="cus_123",
            reason="Not satisfied",
            notes="Please process quickly"
        )
        
        assert request.notes == "Please process quickly"
    
    def test_request_refund_no_subscription(self, service, mock_stripe):
        """Test refund request with no subscription raises error."""
        mock_stripe.get_subscription.return_value = None
        
        with pytest.raises(ValueError, match="No active subscription"):
            service.request_refund(
                customer_id="cus_123",
                reason="Test"
            )
    
    # ── Approval Tests ─────────────────────────────────────────────────────────
    
    def test_approve_refund(self, service):
        """Test approving refund request."""
        request = service.request_refund(
            customer_id="cus_123",
            reason="Test"
        )
        
        approved = service.approve_refund(request.request_id, reviewed_by="admin")
        
        assert approved.status == RefundStatus.APPROVED
        assert approved.reviewed_by == "admin"
        assert approved.reviewed_at is not None
    
    def test_approve_nonexistent_request(self, service):
        """Test approving non-existent request raises error."""
        with pytest.raises(ValueError, match="not found"):
            service.approve_refund("refreq_nonexistent")
    
    def test_approve_already_processed(self, service):
        """Test approving already processed request raises error."""
        request = service.request_refund(
            customer_id="cus_123",
            reason="Test"
        )
        service.approve_refund(request.request_id)
        
        with pytest.raises(ValueError, match="already processed"):
            service.approve_refund(request.request_id)
    
    # ── Processing Tests ──────────────────────────────────────────────────────
    
    def test_process_refund(self, service):
        """Test processing approved refund."""
        request = service.request_refund(
            customer_id="cus_123",
            reason="Test"
        )
        service.approve_refund(request.request_id)
        
        result = service.process_refund(request.request_id)
        
        assert result.refund_id.startswith("re_")
        assert result.request_id == request.request_id
        assert result.customer_id == "cus_123"
        assert result.status == RefundStatus.COMPLETED
        assert result.stripe_refund_id is not None
    
    def test_process_unapproved_request(self, service):
        """Test processing unapproved request raises error."""
        request = service.request_refund(
            customer_id="cus_123",
            reason="Test"
        )
        
        with pytest.raises(ValueError, match="not approved"):
            service.process_refund(request.request_id)
    
    # ── Rejection Tests ────────────────────────────────────────────────────────
    
    def test_reject_refund(self, service):
        """Test rejecting refund request."""
        request = service.request_refund(
            customer_id="cus_123",
            reason="Test"
        )
        
        rejected = service.reject_refund(
            request.request_id,
            reason="Does not meet criteria"
        )
        
        assert rejected.status == RefundStatus.REJECTED
        assert "Does not meet criteria" in rejected.notes
    
    # ── Downgrade Tests ─────────────────────────────────────────────────────────
    
    def test_downgrade_to_free(self, service, mock_stripe):
        """Test downgrading customer to free tier."""
        service.downgrade_to_free("cus_123")
        
        mock_stripe.cancel_subscription.assert_called_once()
    
    # ── Policy Tests ───────────────────────────────────────────────────────────
    
    def test_get_refund_policy(self, service):
        """Test getting refund policy details."""
        policy = service.get_refund_policy()
        
        assert policy["full_refund_window_days"] == 14
        assert policy["max_refund_days"] == 30
        assert "policy" in policy
        assert "exceptions" in policy
    
    # ── History Tests ──────────────────────────────────────────────────────────
    
    def test_get_customer_refund_history(self, service):
        """Test getting customer refund history."""
        # Create some refunds
        service.request_refund(customer_id="cus_123", reason="Test 1")
        service.request_refund(customer_id="cus_123", reason="Test 2")
        
        history = service.get_customer_refund_history("cus_123")
        
        assert len(history) == 2
    
    def test_get_refund_history_empty(self, service):
        """Test refund history for customer with no refunds."""
        history = service.get_customer_refund_history("cus_nonexistent")
        
        assert len(history) == 0


class TestRefundRequest:
    """Test RefundRequest dataclass."""
    
    def test_to_dict(self):
        """Test serialization."""
        request = RefundRequest(
            request_id="refreq_123",
            customer_id="cus_123",
            subscription_id="sub_123",
            refund_type=RefundType.FULL,
            requested_amount_cents=1900,
            reason="Not satisfied",
            status=RefundStatus.PENDING,
        )
        
        data = request.to_dict()
        
        assert data["request_id"] == "refreq_123"
        assert data["refund_type"] == "full"
        assert data["requested_amount_cents"] == 1900
        assert data["status"] == "pending"


class TestRefundResult:
    """Test RefundResult dataclass."""
    
    def test_to_dict(self):
        """Test serialization."""
        result = RefundResult(
            refund_id="re_123",
            request_id="refreq_123",
            customer_id="cus_123",
            subscription_id="sub_123",
            refund_amount_cents=1900,
            status=RefundStatus.COMPLETED,
            stripe_refund_id="re_stripe_123",
        )
        
        data = result.to_dict()
        
        assert data["refund_id"] == "re_123"
        assert data["refund_amount_cents"] == 1900
        assert data["refund_amount"] == 19.0
        assert data["status"] == "completed"


class TestRefundType:
    """Test RefundType enum."""
    
    def test_values(self):
        """Test all refund type values."""
        assert RefundType.FULL.value == "full"
        assert RefundType.PRO_RATED.value == "pro_rated"
        assert RefundType.PARTIAL.value == "partial"


class TestRefundStatus:
    """Test RefundStatus enum."""
    
    def test_values(self):
        """Test all refund status values."""
        assert RefundStatus.PENDING.value == "pending"
        assert RefundStatus.APPROVED.value == "approved"
        assert RefundStatus.PROCESSING.value == "processing"
        assert RefundStatus.COMPLETED.value == "completed"
        assert RefundStatus.REJECTED.value == "rejected"
        assert RefundStatus.FAILED.value == "failed"
