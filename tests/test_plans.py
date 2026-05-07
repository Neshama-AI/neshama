# Tests - Subscription Plans
"""
Tests for subscription plan configurations and limit checks.
Updated for dual-track (hosted/BYOK) model.
"""

import pytest
from neshama.billing.plans import (
    SubscriptionTier,
    PlanConfig,
    LimitsConfig,
    TTSProvider,
    LLMProvider,
    get_plan,
    get_plan_limits,
    check_limit,
    get_all_plans,
    get_tts_provider,
    has_memory_level,
    get_memory_levels,
    get_hosted_conversations_limit,
    is_byok_enabled,
    PLANS,
)


class TestSubscriptionTiers:
    """Test SubscriptionTier enum and conversions."""
    
    def test_tier_values(self):
        """Test that all expected tier values exist."""
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.INDIE.value == "indie"
        assert SubscriptionTier.STUDIO.value == "studio"
        assert SubscriptionTier.ENTERPRISE.value == "enterprise"
    
    def test_from_npc_tier(self):
        """Test conversion from NPC tier names."""
        assert SubscriptionTier.from_npc_tier("free") == SubscriptionTier.FREE
        assert SubscriptionTier.from_npc_tier("basic") == SubscriptionTier.INDIE
        assert SubscriptionTier.from_npc_tier("premium") == SubscriptionTier.STUDIO
        assert SubscriptionTier.from_npc_tier("enterprise") == SubscriptionTier.ENTERPRISE
    
    def test_to_npc_tier(self):
        """Test conversion to NPC tier names."""
        assert SubscriptionTier.FREE.to_npc_tier() == "free"
        assert SubscriptionTier.INDIE.to_npc_tier() == "basic"
        assert SubscriptionTier.STUDIO.to_npc_tier() == "premium"
        assert SubscriptionTier.ENTERPRISE.to_npc_tier() == "enterprise"


class TestLLMProvider:
    """Test LLMProvider enum."""
    
    def test_provider_values(self):
        """Test all BYOK provider values exist."""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.DEEPSEEK.value == "deepseek"
        assert LLMProvider.MINIMAX.value == "minimax"
        assert LLMProvider.ANTHROPIC.value == "anthropic"


class TestPlanConfig:
    """Test plan configurations."""
    
    def test_free_plan_limits(self):
        """Test free tier configuration."""
        plan = PLANS[SubscriptionTier.FREE]
        
        assert plan.npc_limit == 3
        assert plan.emotion_calc_limit == 5_000
        assert plan.monthly_price_cents == 0
        assert plan.tts_provider == TTSProvider.NONE
        assert plan.tts_char_limit == 0
        assert plan.memory_levels == ["L0"]
        # Dual-track fields
        assert plan.hosted_conversations_limit == 1_000
        assert plan.byok_enabled is True
        assert "emotion_engine" in plan.features
        assert "sentiment_analysis" in plan.features
        assert plan.team_member_limit == 1
        assert plan.soul_export_limit == 0
    
    def test_indie_plan_limits(self):
        """Test indie tier configuration."""
        plan = PLANS[SubscriptionTier.INDIE]
        
        assert plan.npc_limit == 10
        assert plan.emotion_calc_limit == 50_000
        assert plan.monthly_price_cents == 1_900  # $19
        assert plan.tts_provider == TTSProvider.AZURE_BASIC
        assert plan.tts_char_limit == 100_000
        assert plan.memory_levels == ["L0", "L1"]
        # Dual-track fields
        assert plan.hosted_conversations_limit == 10_000
        assert plan.byok_enabled is True
        assert "npc2npc_social" in plan.features
        assert "plot_trigger" in plan.features
        assert "relation_graph" in plan.features
    
    def test_studio_plan_limits(self):
        """Test studio tier configuration."""
        plan = PLANS[SubscriptionTier.STUDIO]
        
        assert plan.npc_limit == 50
        assert plan.emotion_calc_limit == 500_000
        assert plan.monthly_price_cents == 7_900  # $79
        assert plan.tts_provider == TTSProvider.AZURE_HD
        assert plan.tts_char_limit == 1_000_000
        assert plan.memory_levels == ["L0", "L1", "L2"]
        # Dual-track fields
        assert plan.hosted_conversations_limit == 100_000
        assert plan.byok_enabled is True
        assert "tts_stt" in plan.features
        assert "team_collaboration" in plan.features
        assert "soul_export" in plan.features
        assert plan.team_member_limit == 3
        assert plan.soul_export_limit == 5
    
    def test_enterprise_plan_limits(self):
        """Test enterprise tier configuration."""
        plan = PLANS[SubscriptionTier.ENTERPRISE]
        
        assert plan.npc_limit == -1  # Unlimited
        assert plan.emotion_calc_limit == -1  # Unlimited
        assert plan.monthly_price_cents == 29_900  # $299
        assert plan.tts_provider == TTSProvider.ELEVENLABS
        assert plan.tts_char_limit == -1  # Unlimited
        assert plan.memory_levels == ["ALL"]
        # Dual-track fields
        assert plan.hosted_conversations_limit == -1  # Unlimited
        assert plan.byok_enabled is True
        assert "private_deploy" in plan.features
        assert "sla_guarantee" in plan.features
        assert plan.team_member_limit == -1  # Unlimited
        assert plan.soul_export_limit == -1  # Unlimited
    
    def test_rate_limits(self):
        """Test rate limits for each tier."""
        # Free tier
        free = PLANS[SubscriptionTier.FREE]
        assert free.rate_limits.event_per_minute == 60
        assert free.rate_limits.chat_per_minute == 20
        assert free.rate_limits.default_per_minute == 30
        
        # Enterprise tier
        enterprise = PLANS[SubscriptionTier.ENTERPRISE]
        assert enterprise.rate_limits.event_per_minute == 2000
        assert enterprise.rate_limits.chat_per_minute == 500
        assert enterprise.rate_limits.default_per_minute == 1000
    
    def test_all_tiers_support_byok(self):
        """Test that all tiers have BYOK enabled."""
        for tier, plan in PLANS.items():
            assert plan.byok_enabled is True, f"Tier {tier.value} should have BYOK enabled"
    
    def test_hosted_conversations_limits(self):
        """Test hosted conversation limits for each tier."""
        assert PLANS[SubscriptionTier.FREE].hosted_conversations_limit == 1_000
        assert PLANS[SubscriptionTier.INDIE].hosted_conversations_limit == 10_000
        assert PLANS[SubscriptionTier.STUDIO].hosted_conversations_limit == 100_000
        assert PLANS[SubscriptionTier.ENTERPRISE].hosted_conversations_limit == -1


class TestGetPlan:
    """Test get_plan function."""
    
    def test_get_valid_plan(self):
        """Test getting valid plans."""
        assert get_plan("free") is not None
        assert get_plan("indie") is not None
        assert get_plan("studio") is not None
        assert get_plan("enterprise") is not None
    
    def test_get_valid_plan_case_insensitive(self):
        """Test case insensitivity."""
        assert get_plan("FREE") is not None
        assert get_plan("Indie") is not None
        assert get_plan("STUDIO") is not None
    
    def test_get_invalid_plan(self):
        """Test getting invalid plan returns None."""
        assert get_plan("nonexistent") is None
        assert get_plan("") is None
        assert get_plan("pro") is None


class TestGetPlanLimits:
    """Test get_plan_limits function."""
    
    def test_free_limits(self):
        """Test free tier limits."""
        limits = get_plan_limits("free")
        
        assert limits is not None
        assert limits.npc_limit == 3
        assert limits.emotion_calc_limit == 5_000
        assert limits.hosted_conversations_limit == 1_000
        assert limits.byok_enabled is True
    
    def test_indie_limits(self):
        """Test indie tier limits."""
        limits = get_plan_limits("indie")
        
        assert limits is not None
        assert limits.npc_limit == 10
        assert limits.emotion_calc_limit == 50_000
        assert limits.hosted_conversations_limit == 10_000
    
    def test_invalid_tier_returns_none(self):
        """Test invalid tier returns None."""
        assert get_plan_limits("invalid") is None


class TestCheckLimit:
    """Test check_limit function."""
    
    def test_free_npc_limit(self):
        """Test NPC limit check for free tier."""
        within, limit = check_limit("free", "npc", 2)
        assert within is True
        assert limit == 3
        
        within, limit = check_limit("free", "npc", 3)
        assert within is False
        assert limit == 3
    
    def test_indie_emotion_limit(self):
        """Test emotion calc limit for indie tier."""
        within, limit = check_limit("indie", "emotion_calc", 49_999)
        assert within is True
        assert limit == 50_000
        
        within, limit = check_limit("indie", "emotion_calc", 50_000)
        assert within is False
    
    def test_hosted_conversations_limit(self):
        """Test hosted conversations limit check."""
        # Free tier: 1000 limit
        within, limit = check_limit("free", "hosted_conversations", 500)
        assert within is True
        assert limit == 1_000
        
        within, limit = check_limit("free", "hosted_conversations", 1_000)
        assert within is False
        assert limit == 1_000
        
        # Enterprise: unlimited
        within, limit = check_limit("enterprise", "hosted_conversations", 1_000_000)
        assert within is True
        assert limit == -1
    
    def test_enterprise_unlimited(self):
        """Test enterprise tier has unlimited resources."""
        within, limit = check_limit("enterprise", "npc", 1000)
        assert within is True
        assert limit == -1
        
        within, limit = check_limit("enterprise", "emotion_calc", 1_000_000)
        assert within is True
        assert limit == -1
    
    def test_invalid_resource_type(self):
        """Test invalid resource type."""
        within, limit = check_limit("free", "invalid", 0)
        assert within is True  # Defaults to unlimited on error
        assert limit == -1


class TestHostedConversationsLimit:
    """Test get_hosted_conversations_limit function."""
    
    def test_free_limit(self):
        assert get_hosted_conversations_limit("free") == 1_000
    
    def test_indie_limit(self):
        assert get_hosted_conversations_limit("indie") == 10_000
    
    def test_studio_limit(self):
        assert get_hosted_conversations_limit("studio") == 100_000
    
    def test_enterprise_unlimited(self):
        assert get_hosted_conversations_limit("enterprise") == -1
    
    def test_invalid_tier(self):
        assert get_hosted_conversations_limit("invalid") == 0


class TestIsByokEnabled:
    """Test is_byok_enabled function."""
    
    def test_all_tiers_enabled(self):
        """All tiers should have BYOK enabled."""
        for tier in ["free", "indie", "studio", "enterprise"]:
            assert is_byok_enabled(tier) is True
    
    def test_invalid_tier_defaults_to_enabled(self):
        assert is_byok_enabled("invalid") is True


class TestGetAllPlans:
    """Test get_all_plans function."""
    
    def test_returns_all_plans(self):
        """Test that all plans are returned."""
        plans = get_all_plans()
        
        assert len(plans) == 4
        
        tiers = [p.tier for p in plans]
        assert SubscriptionTier.FREE in tiers
        assert SubscriptionTier.INDIE in tiers
        assert SubscriptionTier.STUDIO in tiers
        assert SubscriptionTier.ENTERPRISE in tiers


class TestTTSProvider:
    """Test TTS provider functions."""
    
    def test_get_tts_provider(self):
        """Test getting TTS provider for each tier."""
        assert get_tts_provider("free") == TTSProvider.NONE
        assert get_tts_provider("indie") == TTSProvider.AZURE_BASIC
        assert get_tts_provider("studio") == TTSProvider.AZURE_HD
        assert get_tts_provider("enterprise") == TTSProvider.ELEVENLABS
    
    def test_invalid_tier_tts(self):
        """Test invalid tier returns NONE."""
        assert get_tts_provider("invalid") == TTSProvider.NONE


class TestMemoryLevels:
    """Test memory level access functions."""
    
    def test_free_memory_levels(self):
        """Test free tier has only L0."""
        assert has_memory_level("free", "L0") is True
        assert has_memory_level("free", "L1") is False
        assert has_memory_level("free", "L2") is False
        assert get_memory_levels("free") == ["L0"]
    
    def test_indie_memory_levels(self):
        """Test indie tier has L0 and L1."""
        assert has_memory_level("indie", "L0") is True
        assert has_memory_level("indie", "L1") is True
        assert has_memory_level("indie", "L2") is False
        assert get_memory_levels("indie") == ["L0", "L1"]
    
    def test_studio_memory_levels(self):
        """Test studio tier has L0, L1, and L2."""
        assert has_memory_level("studio", "L0") is True
        assert has_memory_level("studio", "L1") is True
        assert has_memory_level("studio", "L2") is True
        assert get_memory_levels("studio") == ["L0", "L1", "L2"]
    
    def test_enterprise_memory_levels(self):
        """Test enterprise tier has ALL."""
        assert has_memory_level("enterprise", "L0") is True
        assert has_memory_level("enterprise", "L1") is True
        assert has_memory_level("enterprise", "L2") is True
        assert has_memory_level("enterprise", "L3") is True
        assert get_memory_levels("enterprise") == ["ALL"]
    
    def test_invalid_tier_memory(self):
        """Test invalid tier defaults to L0."""
        assert has_memory_level("invalid", "L0") is True
        assert get_memory_levels("invalid") == ["L0"]


class TestPlanToDict:
    """Test plan serialization."""
    
    def test_plan_serialization(self):
        """Test that plan can be serialized to dict."""
        plan = get_plan("indie")
        assert plan is not None
        
        data = plan.to_dict()
        
        assert data["tier"] == "indie"
        assert data["name"] == "Indie"
        assert data["monthly_price"] == 19.0
        assert data["monthly_price_cents"] == 1900
        assert "limits" in data
        assert "memory_levels" in data
        assert "tts_provider" in data
        assert "features" in data
        # hosted_conversations_limit and byok_enabled are in limits sub-dict
        assert "hosted_conversations_limit" in data["limits"]
        assert "byok_enabled" in data["limits"]
        assert data["limits"]["byok_enabled"] is True
    
    def test_plan_serialization_includes_features(self):
        """Test that features are serialized."""
        plan = get_plan("studio")
        data = plan.to_dict()
        
        assert "features" in data
        assert "tts_stt" in data["features"]
        assert "team_collaboration" in data["features"]


class TestLimitsConfig:
    """Test LimitsConfig serialization."""
    
    def test_limits_to_dict(self):
        """Test limits serialization."""
        limits = get_plan_limits("indie")
        assert limits is not None
        
        data = limits.to_dict()
        
        assert "npc_limit" in data
        assert "emotion_calc_limit" in data
        assert "tts_char_limit" in data
        assert "api_call_limit" in data
        assert "rate_limits" in data
        assert "hosted_conversations_limit" in data
        assert "byok_enabled" in data
    
    def test_limits_include_hosted_conversations(self):
        """Test that hosted conversations limit is in limits dict."""
        limits = get_plan_limits("free")
        data = limits.to_dict()
        
        assert data["hosted_conversations_limit"] == 1_000
        assert data["byok_enabled"] is True
