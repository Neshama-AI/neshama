# Billing - Subscription Plans
"""
Subscription plan definitions for Neshama.

Defines four subscription tiers with dual-track LLM billing:
- Hosted mode (default): We cover LLM costs, conversation quota per month
- BYOK mode: User brings their own API Key, unlimited conversations

Tiers:
- Free: 3 NPCs, 1000 hosted conversations/month, BYOK unlimited
- Indie ($19/mo): 10 NPCs, 10000 hosted conversations/month, BYOK unlimited
- Studio ($79/mo): 50 NPCs, 100000 hosted conversations/month, BYOK unlimited
- Enterprise ($299/mo): Unlimited NPCs, unlimited hosted conversations, BYOK unlimited
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tier identifiers."""
    FREE = "free"
    INDIE = "indie"
    STUDIO = "studio"
    ENTERPRISE = "enterprise"
    
    @classmethod
    def from_npc_tier(cls, tier_name: str) -> "SubscriptionTier":
        """Convert NPC tier name to subscription tier."""
        mapping = {
            "free": cls.FREE,
            "basic": cls.INDIE,  # Map BASIC to INDIE
            "premium": cls.STUDIO,  # Map PREMIUM to STUDIO
            "enterprise": cls.ENTERPRISE,
        }
        return mapping.get(tier_name.lower(), cls.FREE)
    
    def to_npc_tier(self) -> str:
        """Convert subscription tier to NPC tier name."""
        mapping = {
            self.FREE: "free",
            self.INDIE: "basic",
            self.STUDIO: "premium",
            self.ENTERPRISE: "enterprise",
        }
        return mapping[self]


class TTSProvider(str, Enum):
    """TTS provider options."""
    NONE = "none"
    AZURE_BASIC = "azure_basic"
    AZURE_HD = "azure_hd"
    ELEVENLABS = "elevenlabs"


class LLMProvider(str, Enum):
    """Supported LLM providers for BYOK mode."""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    MINIMAX = "minimax"
    ANTHROPIC = "anthropic"


@dataclass
class RateLimitsConfig:
    """Rate limits for API endpoints."""
    event_per_minute: int
    chat_per_minute: int
    default_per_minute: int


@dataclass
class LimitsConfig:
    """Resource limits for a subscription tier."""
    npc_limit: int
    emotion_calc_limit: int
    tts_char_limit: int  # Monthly TTS character limit
    api_call_limit: int
    rate_limits: RateLimitsConfig
    hosted_conversations_limit: int  # Monthly hosted (our LLM) conversation limit (-1 = unlimited)
    byok_enabled: bool = True  # All tiers support BYOK
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_limit": self.npc_limit,
            "emotion_calc_limit": self.emotion_calc_limit,
            "tts_char_limit": self.tts_char_limit,
            "api_call_limit": self.api_call_limit,
            "rate_limits": {
                "event_per_minute": self.rate_limits.event_per_minute,
                "chat_per_minute": self.rate_limits.chat_per_minute,
                "default_per_minute": self.rate_limits.default_per_minute,
            },
            "hosted_conversations_limit": self.hosted_conversations_limit,
            "byok_enabled": self.byok_enabled,
        }


@dataclass
class PlanConfig:
    """Complete plan configuration."""
    tier: SubscriptionTier
    name: str
    description: str
    monthly_price_cents: int  # Price in cents (0 for free)
    yearly_price_cents: int  # Yearly price in cents
    npc_limit: int
    emotion_calc_limit: int
    memory_levels: List[str]  # e.g., ["L0"], ["L0", "L1"], ["L0", "L1", "L2"], ["ALL"]
    tts_provider: TTSProvider
    tts_char_limit: int
    api_call_limit: int
    rate_limits: RateLimitsConfig
    hosted_conversations_limit: int  # Monthly hosted conversation limit (-1 = unlimited)
    byok_enabled: bool = True  # All tiers support BYOK
    features: List[str] = field(default_factory=list)  # Feature list for display
    team_member_limit: int = 1  # Team collaboration member limit (-1 = unlimited)
    soul_export_limit: int = 0  # Soul exports per month (-1 = unlimited)
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None
    extra_npc_price_id: Optional[str] = None
    extra_emotion_calc_price_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses."""
        return {
            "tier": self.tier.value,
            "name": self.name,
            "description": self.description,
            "monthly_price": self.monthly_price_cents / 100,
            "monthly_price_cents": self.monthly_price_cents,
            "yearly_price": self.yearly_price_cents / 100,
            "yearly_price_cents": self.yearly_price_cents,
            "limits": LimitsConfig(
                npc_limit=self.npc_limit,
                emotion_calc_limit=self.emotion_calc_limit,
                tts_char_limit=self.tts_char_limit,
                api_call_limit=self.api_call_limit,
                rate_limits=self.rate_limits,
                hosted_conversations_limit=self.hosted_conversations_limit,
                byok_enabled=self.byok_enabled,
            ).to_dict(),
            "memory_levels": self.memory_levels,
            "tts_provider": self.tts_provider.value,
            "features": self.features,
            "team_member_limit": self.team_member_limit,
            "soul_export_limit": self.soul_export_limit,
        }


# ── Plan Definitions ──────────────────────────────────────────────────────────

PLANS: Dict[SubscriptionTier, PlanConfig] = {
    SubscriptionTier.FREE: PlanConfig(
        tier=SubscriptionTier.FREE,
        name="Free",
        description="Get started with 3 NPC souls. Perfect for trying Neshama. Bring your own API Key for unlimited conversations!",
        monthly_price_cents=0,
        yearly_price_cents=0,
        npc_limit=3,
        emotion_calc_limit=5_000,
        memory_levels=["L0"],  # Only short-term memory
        tts_provider=TTSProvider.NONE,
        tts_char_limit=0,
        api_call_limit=1_000,
        rate_limits=RateLimitsConfig(
            event_per_minute=60,
            chat_per_minute=20,
            default_per_minute=30,
        ),
        hosted_conversations_limit=1_000,  # ~$2-5 LLM cost/month
        byok_enabled=True,
        features=[
            "emotion_engine",      # Emotion engine
            "memory_system",       # Memory system
            "behavior_mapping",    # Behavior mapping
            "sentiment_analysis",  # Sentiment analysis
        ],
        team_member_limit=1,
        soul_export_limit=0,
    ),
    SubscriptionTier.INDIE: PlanConfig(
        tier=SubscriptionTier.INDIE,
        name="Indie",
        description="10 NPC souls for indie developers and small studios. Enhanced social and narrative features.",
        monthly_price_cents=1_900,  # $19
        yearly_price_cents=1_900 * 10,  # ~10 months
        npc_limit=10,
        emotion_calc_limit=50_000,
        memory_levels=["L0", "L1"],  # Short-term + episodic
        tts_provider=TTSProvider.AZURE_BASIC,
        tts_char_limit=100_000,
        api_call_limit=10_000,
        rate_limits=RateLimitsConfig(
            event_per_minute=200,
            chat_per_minute=60,
            default_per_minute=100,
        ),
        hosted_conversations_limit=10_000,
        byok_enabled=True,
        features=[
            "emotion_engine",
            "memory_system",
            "behavior_mapping",
            "sentiment_analysis",
            "npc2npc_social",      # NPC2NPC social interaction
            "plot_trigger",        # Plot trigger system
            "relation_graph",      # Relationship graph
        ],
        team_member_limit=1,
        soul_export_limit=0,
        stripe_price_id_monthly="price_indie_monthly",
        stripe_price_id_yearly="price_indie_yearly",
        extra_npc_price_id="price_extra_npc_indie",
        extra_emotion_calc_price_id="price_extra_emotion_indie",
    ),
    SubscriptionTier.STUDIO: PlanConfig(
        tier=SubscriptionTier.STUDIO,
        name="Studio",
        description="50 NPC souls with full feature set for professional game studios. Team collaboration included.",
        monthly_price_cents=7_900,  # $79
        yearly_price_cents=7_900 * 10,  # ~10 months
        npc_limit=50,
        emotion_calc_limit=500_000,
        memory_levels=["L0", "L1", "L2"],  # + semantic memory
        tts_provider=TTSProvider.AZURE_HD,
        tts_char_limit=1_000_000,
        api_call_limit=100_000,
        rate_limits=RateLimitsConfig(
            event_per_minute=500,
            chat_per_minute=150,
            default_per_minute=300,
        ),
        hosted_conversations_limit=100_000,
        byok_enabled=True,
        features=[
            "emotion_engine",
            "memory_system",
            "behavior_mapping",
            "sentiment_analysis",
            "npc2npc_social",
            "plot_trigger",
            "relation_graph",
            "tts_stt",            # TTS/STT
            "sentiment_enhanced",  # Enhanced sentiment analysis
            "template_market",    # Template marketplace
            "team_collaboration", # Team collaboration
            "soul_export",        # Soul export (YAML/JSON)
        ],
        team_member_limit=3,
        soul_export_limit=5,  # 5 soul exports per month
        stripe_price_id_monthly="price_studio_monthly",
        stripe_price_id_yearly="price_studio_yearly",
        extra_npc_price_id="price_extra_npc_studio",
        extra_emotion_calc_price_id="price_extra_emotion_studio",
    ),
    SubscriptionTier.ENTERPRISE: PlanConfig(
        tier=SubscriptionTier.ENTERPRISE,
        name="Enterprise",
        description="Unlimited everything with dedicated support, SLA guarantees, and private deployment options.",
        monthly_price_cents=29_900,  # $299
        yearly_price_cents=29_900 * 10,  # ~10 months
        npc_limit=-1,  # Unlimited (-1 means unlimited)
        emotion_calc_limit=-1,
        memory_levels=["ALL"],  # All memory levels
        tts_provider=TTSProvider.ELEVENLABS,
        tts_char_limit=-1,  # Unlimited
        api_call_limit=-1,
        rate_limits=RateLimitsConfig(
            event_per_minute=2000,
            chat_per_minute=500,
            default_per_minute=1000,
        ),
        hosted_conversations_limit=-1,  # Unlimited hosted conversations
        byok_enabled=True,
        features=[
            "emotion_engine",
            "memory_system",
            "behavior_mapping",
            "sentiment_analysis",
            "npc2npc_social",
            "plot_trigger",
            "relation_graph",
            "tts_stt",
            "sentiment_enhanced",
            "template_market",
            "team_collaboration",
            "soul_export",
            "private_deploy",     # Private deployment support
            "sla_guarantee",      # SLA guarantee
        ],
        team_member_limit=-1,  # Unlimited team members
        soul_export_limit=-1,  # Unlimited soul exports
        stripe_price_id_monthly="price_enterprise_monthly",
        stripe_price_id_yearly="price_enterprise_yearly",
    ),
}


def get_plan(tier_name: str) -> Optional[PlanConfig]:
    """
    Get plan configuration by tier name.
    
    Args:
        tier_name: Tier name (free, indie, studio, enterprise)
        
    Returns:
        PlanConfig or None if not found
    """
    try:
        tier = SubscriptionTier(tier_name.lower())
        return PLANS.get(tier)
    except ValueError:
        logger.warning(f"Unknown tier name: {tier_name}")
        return None


def get_plan_limits(tier_name: str) -> Optional[LimitsConfig]:
    """
    Get resource limits for a tier.
    
    Args:
        tier_name: Tier name
        
    Returns:
        LimitsConfig or None if tier not found
    """
    plan = get_plan(tier_name)
    if not plan:
        return None
    
    return LimitsConfig(
        npc_limit=plan.npc_limit,
        emotion_calc_limit=plan.emotion_calc_limit,
        tts_char_limit=plan.tts_char_limit,
        api_call_limit=plan.api_call_limit,
        rate_limits=plan.rate_limits,
        hosted_conversations_limit=plan.hosted_conversations_limit,
        byok_enabled=plan.byok_enabled,
    )


def check_limit(
    tier_name: str,
    resource_type: str,
    current_usage: int,
) -> tuple[bool, Optional[int]]:
    """
    Check if current usage exceeds the limit for a resource type.
    
    Args:
        tier_name: Subscription tier
        resource_type: One of "npc", "emotion_calc", "tts_char", "api_call", "hosted_conversations"
        current_usage: Current usage amount
        
    Returns:
        Tuple of (within_limit, limit_value)
        - (True, limit) if within limit
        - (False, limit) if exceeded
        - (True, -1) if unlimited
    """
    limits = get_plan_limits(tier_name)
    if not limits:
        return True, -1  # Default to unlimited on error
    
    resource_map = {
        "npc": limits.npc_limit,
        "emotion_calc": limits.emotion_calc_limit,
        "tts_char": limits.tts_char_limit,
        "api_call": limits.api_call_limit,
        "hosted_conversations": limits.hosted_conversations_limit,
    }
    
    limit = resource_map.get(resource_type, -1)
    
    if limit == -1:  # Unlimited
        return True, -1
    
    return current_usage < limit, limit


def get_hosted_conversations_limit(tier_name: str) -> int:
    """
    Get the hosted conversations limit for a tier.
    
    Returns -1 for unlimited.
    """
    plan = get_plan(tier_name)
    if not plan:
        return 0
    return plan.hosted_conversations_limit


def is_byok_enabled(tier_name: str) -> bool:
    """Check if BYOK is enabled for a tier. All tiers support BYOK."""
    plan = get_plan(tier_name)
    if not plan:
        return True  # Default to enabled
    return plan.byok_enabled


def get_all_plans() -> List[PlanConfig]:
    """Get all available plans."""
    return list(PLANS.values())


def get_tts_provider(tier_name: str) -> TTSProvider:
    """Get TTS provider for a tier."""
    plan = get_plan(tier_name)
    if not plan:
        return TTSProvider.NONE
    return plan.tts_provider


def has_memory_level(tier_name: str, level: str) -> bool:
    """Check if tier has access to a specific memory level."""
    plan = get_plan(tier_name)
    if not plan:
        return level == "L0"  # Default to L0
    
    if "ALL" in plan.memory_levels:
        return True
    
    return level in plan.memory_levels


def get_memory_levels(tier_name: str) -> List[str]:
    """Get available memory levels for a tier."""
    plan = get_plan(tier_name)
    if not plan:
        return ["L0"]
    return plan.memory_levels
