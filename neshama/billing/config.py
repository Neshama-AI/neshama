# Billing - Stripe Configuration
"""
Stripe API configuration.

All sensitive values are loaded from environment variables.
Never hardcode API keys or secrets.

Also includes hosted LLM provider configuration for the dual-track model.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


@dataclass
class StripeConfig:
    """
    Stripe configuration with environment variable support.
    
    Required environment variables:
    - STRIPE_SECRET_KEY: Stripe secret key (sk_live_... or sk_test_...)
    - STRIPE_WEBHOOK_SECRET: Webhook signature verification secret
    - STRIPE_PUBLIC_KEY: Stripe publishable key (pk_live_... or pk_test_...)
    
    Optional:
    - STRIPE_CONNECT_CLIENT_ID: For Stripe Connect (marketplace)
    """
    # API Keys
    secret_key: str
    public_key: str
    webhook_secret: str
    connect_client_id: Optional[str] = None
    
    # Price IDs (from Stripe Dashboard)
    price_indie_monthly: str = "price_indie_monthly"
    price_indie_yearly: str = "price_indie_yearly"
    price_studio_monthly: str = "price_studio_monthly"
    price_studio_yearly: str = "price_studio_yearly"
    price_enterprise_monthly: str = "price_enterprise_monthly"
    price_enterprise_yearly: str = "price_enterprise_yearly"
    
    # Add-on prices
    price_extra_npc: str = "price_extra_npc"  # $1.99/NPC/month
    price_extra_emotion_calc: str = "price_extra_emotion_calc"  # $4.99/10k
    
    # Callbacks
    success_url: str = "https://app.neshama.io/billing/success?session_id={CHECKOUT_SESSION_ID}"
    cancel_url: str = "https://app.neshama.io/billing/cancel"
    
    # Mode
    mode: str = "subscription"  # subscription, payment, or setup
    
    # API Version
    api_version: str = "2023-10-16"
    
    @property
    def is_test_mode(self) -> bool:
        """Check if using test mode keys."""
        return self.secret_key.startswith("sk_test_")
    
    @property
    def is_live_mode(self) -> bool:
        """Check if using live mode keys."""
        return self.secret_key.startswith("sk_live_")


@dataclass
class HostedLLMConfig:
    """
    Configuration for the hosted LLM provider (our side of the dual-track model).
    
    These are the default LLM settings used when the user is in hosted mode
    (not BYOK). The hosted provider costs are covered by us.
    """
    # Default provider for hosted conversations
    default_provider: str = "deepseek"
    # Default model for hosted conversations
    default_model: str = "deepseek-chat"
    # Fallback provider if default fails
    fallback_provider: str = "openai"
    fallback_model: str = "gpt-4o-mini"
    # Maximum tokens per hosted conversation response
    max_response_tokens: int = 1024
    # Whether hosted mode is enabled (can be disabled if costs are too high)
    hosted_mode_enabled: bool = True
    # Cost threshold alert (USD) - warn when monthly hosted cost exceeds this
    cost_alert_threshold: float = 100.0
    
    def to_dict(self) -> dict:
        return {
            "default_provider": self.default_provider,
            "default_model": self.default_model,
            "fallback_provider": self.fallback_provider,
            "fallback_model": self.fallback_model,
            "max_response_tokens": self.max_response_tokens,
            "hosted_mode_enabled": self.hosted_mode_enabled,
            "cost_alert_threshold": self.cost_alert_threshold,
        }


def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    return os.environ.get(key, default)


def get_stripe_config() -> StripeConfig:
    """
    Create StripeConfig from environment variables.
    
    Raises:
        ValueError: If required environment variables are missing
        
    Returns:
        StripeConfig instance
    """
    secret_key = _get_env("STRIPE_SECRET_KEY")
    public_key = _get_env("STRIPE_PUBLIC_KEY")
    webhook_secret = _get_env("STRIPE_WEBHOOK_SECRET")
    
    if not secret_key:
        logger.warning(
            "STRIPE_SECRET_KEY not set. Stripe operations will fail. "
            "Set environment variables for production use."
        )
        # Use test placeholder for development
        secret_key = "sk_test_placeholder"
        public_key = public_key or "pk_test_placeholder"
        webhook_secret = webhook_secret or "whsec_placeholder"
    
    return StripeConfig(
        secret_key=secret_key,
        public_key=public_key,
        webhook_secret=webhook_secret,
        connect_client_id=_get_env("STRIPE_CONNECT_CLIENT_ID"),
        price_indie_monthly=_get_env(
            "STRIPE_PRICE_INDIE_MONTHLY", "price_indie_monthly"
        ),
        price_indie_yearly=_get_env(
            "STRIPE_PRICE_INDIE_YEARLY", "price_indie_yearly"
        ),
        price_studio_monthly=_get_env(
            "STRIPE_PRICE_STUDIO_MONTHLY", "price_studio_monthly"
        ),
        price_studio_yearly=_get_env(
            "STRIPE_PRICE_STUDIO_YEARLY", "price_studio_yearly"
        ),
        price_enterprise_monthly=_get_env(
            "STRIPE_PRICE_ENTERPRISE_MONTHLY", "price_enterprise_monthly"
        ),
        price_enterprise_yearly=_get_env(
            "STRIPE_PRICE_ENTERPRISE_YEARLY", "price_enterprise_yearly"
        ),
        price_extra_npc=_get_env("STRIPE_PRICE_EXTRA_NPC", "price_extra_npc"),
        price_extra_emotion_calc=_get_env(
            "STRIPE_PRICE_EXTRA_EMOTION_CALC", "price_extra_emotion_calc"
        ),
        success_url=_get_env(
            "STRIPE_SUCCESS_URL",
            "https://app.neshama.io/billing/success?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=_get_env(
            "STRIPE_CANCEL_URL",
            "https://app.neshama.io/billing/cancel"
        ),
    )


def get_hosted_llm_config() -> HostedLLMConfig:
    """
    Create HostedLLMConfig from environment variables.
    
    Environment variables:
    - NESHAMA_HOSTED_LLM_PROVIDER: Default provider (default: deepseek)
    - NESHAMA_HOSTED_LLM_MODEL: Default model (default: deepseek-chat)
    - NESHAMA_HOSTED_LLM_FALLBACK_PROVIDER: Fallback provider (default: openai)
    - NESHAMA_HOSTED_LLM_FALLBACK_MODEL: Fallback model (default: gpt-4o-mini)
    - NESHAMA_HOSTED_LLM_MAX_TOKENS: Max response tokens (default: 1024)
    - NESHAMA_HOSTED_MODE_ENABLED: Whether hosted mode is enabled (default: true)
    - NESHAMA_COST_ALERT_THRESHOLD: Cost alert threshold in USD (default: 100.0)
    """
    enabled_str = _get_env("NESHAMA_HOSTED_MODE_ENABLED", "true")
    enabled = enabled_str.lower() in ("true", "1", "yes")
    
    threshold_str = _get_env("NESHAMA_COST_ALERT_THRESHOLD", "100.0")
    try:
        threshold = float(threshold_str)
    except (ValueError, TypeError):
        threshold = 100.0
    
    return HostedLLMConfig(
        default_provider=_get_env("NESHAMA_HOSTED_LLM_PROVIDER", "deepseek"),
        default_model=_get_env("NESHAMA_HOSTED_LLM_MODEL", "deepseek-chat"),
        fallback_provider=_get_env("NESHAMA_HOSTED_LLM_FALLBACK_PROVIDER", "openai"),
        fallback_model=_get_env("NESHAMA_HOSTED_LLM_FALLBACK_MODEL", "gpt-4o-mini"),
        max_response_tokens=int(_get_env("NESHAMA_HOSTED_LLM_MAX_TOKENS", "1024")),
        hosted_mode_enabled=enabled,
        cost_alert_threshold=threshold,
    )


def get_price_id_for_tier(
    tier: str,
    interval: str = "month",
    config: Optional[StripeConfig] = None,
) -> Optional[str]:
    """
    Get Stripe Price ID for a subscription tier.
    
    Args:
        tier: Subscription tier (free, indie, studio, enterprise)
        interval: Billing interval (month or year)
        config: Optional StripeConfig (loads default if not provided)
        
    Returns:
        Stripe Price ID or None for free tier
    """
    if tier == "free":
        return None
    
    if config is None:
        config = get_stripe_config()
    
    price_map = {
        ("indie", "month"): config.price_indie_monthly,
        ("indie", "year"): config.price_indie_yearly,
        ("studio", "month"): config.price_studio_monthly,
        ("studio", "year"): config.price_studio_yearly,
        ("enterprise", "month"): config.price_enterprise_monthly,
        ("enterprise", "year"): config.price_enterprise_yearly,
    }
    
    return price_map.get((tier.lower(), interval))
