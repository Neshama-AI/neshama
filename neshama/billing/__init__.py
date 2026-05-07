# Billing Module - Stripe Payment Integration
"""
Billing module for Neshama subscription management.

Provides:
- Subscription plan definitions (Free/Indie/Studio/Enterprise) with dual-track LLM billing
- Usage tracking for resources (NPCs, emotion calcs, TTS, API calls, hosted conversations)
- BYOK (Bring Your Own Key) management for user-provided LLM API Keys
- Stripe integration for payment processing
- Refund handling with policy enforcement
- Subscription middleware for resource enforcement

Dual-Track Model:
- Hosted mode: We cover LLM costs, conversation quota per month
- BYOK mode: User brings their own API Key, unlimited conversations
"""

from .plans import (
    SubscriptionTier,
    PlanConfig,
    LimitsConfig,
    TTSProvider,
    LLMProvider,
    get_plan,
    get_plan_limits,
    get_all_plans,
    check_limit,
    get_tts_provider,
    has_memory_level,
    get_memory_levels,
    get_hosted_conversations_limit,
    is_byok_enabled,
    PLANS,
)
from .usage import (
    UsageTracker,
    MonthlyUsage,
    ResourceType,
    UsageRecord,
    UserKeyManager,
    UserKeyInfo,
    KeyEncryption,
    track_usage,
    get_monthly_usage,
    check_limit_reached,
    get_usage_tracker,
    get_key_manager,
    is_byok,
    check_conversation_quota,
)
from .config import StripeConfig, get_stripe_config, get_price_id_for_tier, HostedLLMConfig, get_hosted_llm_config
from .stripe_service import (
    StripeService,
    SubscriptionInfo,
    CustomerInfo,
    CheckoutSessionInfo,
    SubscriptionStatus,
    WebhookEvent,
    WebhookEventType,
)
from .refund import (
    RefundService,
    RefundRequest,
    RefundResult,
    RefundStatus,
)
