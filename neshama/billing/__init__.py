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
- License key generation, validation, and machine binding

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
from .license import (
    LicenseStore,
    LicenseCache,
    LicenseRecord,
    LicenseValidationResult,
    MachineBinding,
    generate_license_key,
    parse_license_key,
    validate_license,
    activate_license,
    deactivate_license,
    get_license_status,
    generate_license,
    revoke_license,
    check_grace_period,
    check_feature,
    check_region_match,
    detect_region_from_host,
    get_license_store,
    get_license_cache,
    get_region_pricing,
    PLAN_FEATURES,
    PLAN_NPC_LIMITS,
    MACHINE_LIMITS,
    GRACE_PERIOD_DAYS,
    PLAN_CODES,
    REGION_CODES,
    REGION_CODE_REVERSE,
    REGION_DISPLAY_NAMES,
    REGION_PRICING,
    DOMAIN_REGION_MAP,
)