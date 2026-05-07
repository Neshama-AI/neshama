# Billing - Refund Service
"""
Refund processing and policy enforcement.

Refund policy:
- First subscription: 14-day full refund window
- After 14 days: Pro-rated refund based on remaining days
- Add-ons (extra NPCs, emotion calc packs): Non-refundable
- Refunds processed within 5-10 business days
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from .config import get_stripe_config
from .stripe_service import StripeService, SubscriptionStatus, SubscriptionInfo

logger = logging.getLogger(__name__)


class RefundStatus(str, Enum):
    """Refund request status."""
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class RefundType(str, Enum):
    """Type of refund."""
    FULL = "full"  # Within 14-day window
    PRO_RATED = "pro_rated"  # After 14 days, based on remaining days
    PARTIAL = "partial"  # Specific amount


@dataclass
class RefundRequest:
    """Refund request details."""
    request_id: str
    customer_id: str
    subscription_id: str
    refund_type: RefundType
    requested_amount_cents: int
    reason: str
    requested_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: RefundStatus = RefundStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "customer_id": self.customer_id,
            "subscription_id": self.subscription_id,
            "refund_type": self.refund_type.value,
            "requested_amount_cents": self.requested_amount_cents,
            "reason": self.reason,
            "requested_at": self.requested_at,
            "status": self.status.value,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
            "notes": self.notes,
        }


@dataclass
class RefundResult:
    """Result of refund processing."""
    refund_id: str
    request_id: str
    customer_id: str
    subscription_id: str
    refund_amount_cents: int
    status: RefundStatus
    stripe_refund_id: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "refund_id": self.refund_id,
            "request_id": self.request_id,
            "customer_id": self.customer_id,
            "subscription_id": self.subscription_id,
            "refund_amount_cents": self.refund_amount_cents,
            "refund_amount": self.refund_amount_cents / 100,
            "status": self.status.value,
            "stripe_refund_id": self.stripe_refund_id,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
        }


# Refund policy constants
REFUND_WINDOW_DAYS = 14  # Full refund within 14 days
MAX_REFUND_DAYS = 30  # Pro-rated refund up to 30 days


class RefundService:
    """
    Service for processing refunds according to policy.
    
    Refund Policy:
    1. First subscription only
    2. 14-day full refund window from first payment
    3. After 14 days: Pro-rated based on remaining subscription days
    4. Add-ons are non-refundable
    5. Refunds processed within 5-10 business days
    
    Example:
        >>> service = RefundService()
        >>> 
        >>> # Calculate refund amount
        >>> amount = service.calculate_refund_amount("sub_123")
        >>> print(f"Refund amount: ${amount}")
        >>> 
        >>> # Request refund
        >>> request = service.request_refund(
        ...     customer_id="cus_123",
        ...     reason="Not satisfied with product"
        ... )
    """
    
    def __init__(self, stripe_service: Optional[StripeService] = None):
        """
        Initialize RefundService.
        
        Args:
            stripe_service: Optional StripeService instance
        """
        self._stripe = stripe_service or StripeService(mock=True)
        self._requests: Dict[str, RefundRequest] = {}
        self._results: Dict[str, RefundResult] = {}
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return f"refreq_{uuid.uuid4().hex[:16]}"
    
    def calculate_refund_amount(
        self,
        subscription_id: str,
        add_on_amount_cents: int = 0,
    ) -> float:
        """
        Calculate refund amount based on policy.
        
        Args:
            subscription_id: Stripe subscription ID
            add_on_amount_cents: Amount spent on add-ons (non-refundable)
            
        Returns:
            Refund amount in dollars
        """
        subscription = self._stripe.get_subscription_by_id(subscription_id)
        
        if not subscription:
            logger.warning(f"Subscription not found: {subscription_id}")
            return 0.0
        
        # Determine if within full refund window
        start_date = datetime.fromisoformat(subscription.current_period_start)
        days_since_start = (datetime.now() - start_date).days
        
        if days_since_start <= REFUND_WINDOW_DAYS:
            # Full refund
            refund_cents = self._get_subscription_price_cents(subscription)
        else:
            # Pro-rated refund
            refund_cents = self._calculate_pro_rated_refund(subscription)
        
        # Subtract non-refundable add-ons
        refund_cents = max(0, refund_cents - add_on_amount_cents)
        
        # Convert to dollars with proper decimal handling
        return Decimal(refund_cents) / Decimal(100)
    
    def _get_subscription_price_cents(self, subscription: SubscriptionInfo) -> int:
        """Get subscription price in cents."""
        # This would typically come from Stripe
        tier_prices = {
            "free": 0,
            "indie": 1900,  # $19
            "studio": 9900,  # $99
            "enterprise": 0,  # Custom pricing, not refundable
        }
        return tier_prices.get(subscription.tier, 0)
    
    def _calculate_pro_rated_refund(self, subscription: SubscriptionInfo) -> int:
        """Calculate pro-rated refund based on remaining days."""
        start = datetime.fromisoformat(subscription.current_period_start)
        end = datetime.fromisoformat(subscription.current_period_end)
        
        total_days = (end - start).days
        remaining_days = (end - datetime.now()).days
        
        if remaining_days <= 0 or total_days <= 0:
            return 0
        
        # Get subscription price
        price_cents = self._get_subscription_price_cents(subscription)
        
        # Calculate pro-rated amount
        daily_rate = Decimal(price_cents) / Decimal(total_days)
        refund = (daily_rate * Decimal(remaining_days)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        
        return int(refund)
    
    def get_refund_type(
        self,
        subscription_id: str,
    ) -> RefundType:
        """
        Determine refund type based on policy.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            RefundType enum value
        """
        subscription = self._stripe.get_subscription_by_id(subscription_id)
        
        if not subscription:
            return RefundType.PARTIAL
        
        start_date = datetime.fromisoformat(subscription.current_period_start)
        days_since_start = (datetime.now() - start_date).days
        
        if days_since_start <= REFUND_WINDOW_DAYS:
            return RefundType.FULL
        elif days_since_start <= MAX_REFUND_DAYS:
            return RefundType.PRO_RATED
        else:
            return RefundType.PARTIAL
    
    def request_refund(
        self,
        customer_id: str,
        reason: str,
        subscription_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> RefundRequest:
        """
        Request a refund.
        
        Args:
            customer_id: Stripe customer ID
            reason: Reason for refund request
            subscription_id: Specific subscription to refund (uses current if None)
            notes: Optional additional notes
            
        Returns:
            RefundRequest object
        """
        # Get subscription
        if not subscription_id:
            subscription = self._stripe.get_subscription(customer_id)
            if not subscription:
                raise ValueError("No active subscription found")
            subscription_id = subscription.subscription_id
        
        subscription = self._stripe.get_subscription_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        # Calculate refund amount
        refund_amount = self.calculate_refund_amount(subscription_id)
        refund_type = self.get_refund_type(subscription_id)
        
        # Create request
        request = RefundRequest(
            request_id=self._generate_request_id(),
            customer_id=customer_id,
            subscription_id=subscription_id,
            refund_type=refund_type,
            requested_amount_cents=int(refund_amount * 100),
            reason=reason,
            notes=notes,
        )
        
        self._requests[request.request_id] = request
        logger.info(
            f"Refund requested: {request.request_id}, "
            f"amount=${refund_amount}, type={refund_type.value}"
        )
        
        return request
    
    def approve_refund(
        self,
        request_id: str,
        reviewed_by: str = "system",
    ) -> RefundRequest:
        """
        Approve a refund request.
        
        Args:
            request_id: Request to approve
            reviewed_by: Who approved the request
            
        Returns:
            Updated RefundRequest
        """
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Refund request not found: {request_id}")
        
        if request.status != RefundStatus.PENDING:
            raise ValueError(f"Request already processed: {request.status.value}")
        
        request.status = RefundStatus.APPROVED
        request.reviewed_by = reviewed_by
        request.reviewed_at = datetime.now().isoformat()
        
        return request
    
    def process_refund(
        self,
        refund_id: str,
    ) -> RefundResult:
        """
        Process an approved refund.
        
        Args:
            refund_id: Refund request ID to process
            
        Returns:
            RefundResult with processing details
        """
        request = self._requests.get(refund_id)
        if not request:
            raise ValueError(f"Refund request not found: {refund_id}")
        
        if request.status != RefundStatus.APPROVED:
            raise ValueError(f"Request not approved: {request.status.value}")
        
        # Update status
        request.status = RefundStatus.PROCESSING
        
        # Process through Stripe (mocked)
        try:
            # In real implementation:
            # stripe.Refund.create(
            #     payment_intent=subscription.latest_invoice.payment_intent,
            #     amount=request.requested_amount_cents,
            # )
            
            result = RefundResult(
                refund_id=f"re_{refund_id}",
                request_id=request.request_id,
                customer_id=request.customer_id,
                subscription_id=request.subscription_id,
                refund_amount_cents=request.requested_amount_cents,
                status=RefundStatus.COMPLETED,
                stripe_refund_id=f"re_stripe_{request.request_id}",
                completed_at=datetime.now().isoformat(),
            )
            
            self._results[result.refund_id] = result
            request.status = RefundStatus.COMPLETED
            
            logger.info(f"Refund completed: {result.refund_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Refund processing failed: {e}")
            request.status = RefundStatus.FAILED
            
            return RefundResult(
                refund_id=f"re_{refund_id}",
                request_id=request.request_id,
                customer_id=request.customer_id,
                subscription_id=request.subscription_id,
                refund_amount_cents=request.requested_amount_cents,
                status=RefundStatus.FAILED,
                error_message=str(e),
            )
    
    def reject_refund(
        self,
        request_id: str,
        reason: str,
        reviewed_by: str = "system",
    ) -> RefundRequest:
        """
        Reject a refund request.
        
        Args:
            request_id: Request to reject
            reason: Reason for rejection
            reviewed_by: Who rejected
            
        Returns:
            Updated RefundRequest
        """
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Refund request not found: {request_id}")
        
        request.status = RefundStatus.REJECTED
        request.reviewed_by = reviewed_by
        request.reviewed_at = datetime.now().isoformat()
        request.notes = f"Rejected: {reason}"
        
        return request
    
    def downgrade_to_free(
        self,
        customer_id: str,
        reason: str = "refund_completed",
    ) -> None:
        """
        Downgrade customer to free tier after refund.
        
        Args:
            customer_id: Customer to downgrade
            reason: Reason for downgrade
        """
        subscription = self._stripe.get_subscription(customer_id)
        
        if subscription:
            # Cancel at period end or immediately
            self._stripe.cancel_subscription(
                subscription.subscription_id,
                cancel_at_period_end=False,
                reason=reason,
            )
        
        logger.info(f"Customer {customer_id} downgraded to free tier")
    
    def get_refund_policy(self) -> Dict[str, Any]:
        """
        Get refund policy details.
        
        Returns:
            Dict with policy information
        """
        return {
            "full_refund_window_days": REFUND_WINDOW_DAYS,
            "max_refund_days": MAX_REFUND_DAYS,
            "policy": {
                "first_subscription": {
                    "within_14_days": "Full refund",
                    "after_14_days": "Pro-rated refund based on remaining days",
                },
                "add_ons": {
                    "extra_npc": "Non-refundable",
                    "emotion_calc_packs": "Non-refundable",
                },
                "processing_time": "5-10 business days",
            },
            "exceptions": [
                "Enterprise custom pricing - case by case",
                "Fraudulent claims - no refund",
                "Terms of service violations - no refund",
            ],
        }
    
    def get_customer_refund_history(
        self,
        customer_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get refund history for a customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            List of refund records
        """
        history = []
        
        for request in self._requests.values():
            if request.customer_id == customer_id:
                history.append(request.to_dict())
        
        for result in self._results.values():
            if result.customer_id == customer_id:
                history.append(result.to_dict())
        
        return sorted(history, key=lambda x: x.get("requested_at", ""), reverse=True)
    
    def validate_refund_eligibility(
        self,
        customer_id: str,
        subscription_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check if customer is eligible for refund.
        
        Args:
            customer_id: Stripe customer ID
            subscription_id: Optional specific subscription
            
        Returns:
            Dict with eligibility status and reason
        """
        subscription = self._stripe.get_subscription(
            subscription_id if subscription_id else customer_id
        )
        
        if not subscription:
            return {
                "eligible": False,
                "reason": "No active subscription found",
            }
        
        # Check for existing refunds
        for request in self._requests.values():
            if (request.customer_id == customer_id and 
                request.subscription_id == subscription.subscription_id and
                request.status in (RefundStatus.PENDING, RefundStatus.PROCESSING)):
                return {
                    "eligible": False,
                    "reason": "Refund already in progress",
                    "request_id": request.request_id,
                }
        
        # Check subscription age
        start_date = datetime.fromisoformat(subscription.current_period_start)
        days_since_start = (datetime.now() - start_date).days
        
        if days_since_start > MAX_REFUND_DAYS:
            return {
                "eligible": False,
                "reason": f"Subscription is {days_since_start} days old (max {MAX_REFUND_DAYS} days)",
            }
        
        # Eligible
        refund_type = self.get_refund_type(subscription.subscription_id)
        estimated_amount = self.calculate_refund_amount(subscription.subscription_id)
        
        return {
            "eligible": True,
            "refund_type": refund_type.value,
            "estimated_amount": estimated_amount,
            "days_since_start": days_since_start,
            "subscription_id": subscription.subscription_id,
        }
