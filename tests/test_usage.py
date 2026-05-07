# Tests - Usage Tracking
"""
Tests for usage tracking functionality.
Updated for dual-track (hosted/BYOK) model with:
- Hosted conversation tracking
- User key management (BYOK)
- Conversation quota checks
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

from neshama.billing.usage import (
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


class TestResourceType:
    """Test ResourceType enum."""
    
    def test_resource_types(self):
        """Test all resource types exist."""
        assert ResourceType.NPC_COUNT.value == "npc_count"
        assert ResourceType.EMOTION_CALC.value == "emotion_calc"
        assert ResourceType.TTS_CHAR.value == "tts_char"
        assert ResourceType.API_CALL.value == "api_call"
        assert ResourceType.HOSTED_CONVERSATION.value == "hosted_conversation"


class TestUsageTracker:
    """Test UsageTracker class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    @pytest.fixture
    def tracker(self, temp_dir):
        """Create tracker with temporary directory."""
        return UsageTracker(data_dir=temp_dir)
    
    def test_track_npc_usage(self, tracker):
        """Test tracking NPC count usage."""
        tracker.track_usage("session_1", ResourceType.NPC_COUNT, 1)
        
        usage = tracker.get_monthly_usage("session_1")
        assert usage.npc_count == 1
    
    def test_track_emotion_calc(self, tracker):
        """Test tracking emotion calculations."""
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 10)
        
        usage = tracker.get_monthly_usage("session_1")
        assert usage.emotion_calc_count == 10
    
    def test_track_tts_chars(self, tracker):
        """Test tracking TTS character usage."""
        tracker.track_usage("session_1", ResourceType.TTS_CHAR, 500)
        
        usage = tracker.get_monthly_usage("session_1")
        assert usage.tts_char_count == 500
    
    def test_track_api_calls(self, tracker):
        """Test tracking API calls."""
        tracker.track_usage("session_1", ResourceType.API_CALL, 25)
        
        usage = tracker.get_monthly_usage("session_1")
        assert usage.api_call_count == 25
    
    def test_track_hosted_conversations(self, tracker):
        """Test tracking hosted conversations."""
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 1)
        
        usage = tracker.get_monthly_usage("session_1")
        assert usage.hosted_conversation_count == 1
    
    def test_hosted_conversations_accumulate(self, tracker):
        """Test that hosted conversations accumulate."""
        for _ in range(5):
            tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 1)
        
        usage = tracker.get_monthly_usage("session_1")
        assert usage.hosted_conversation_count == 5
    
    def test_accumulated_usage(self, tracker):
        """Test that usage accumulates."""
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 10)
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 15)
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 25)
        
        usage = tracker.get_monthly_usage("session_1")
        assert usage.emotion_calc_count == 50
    
    def test_multiple_sessions(self, tracker):
        """Test tracking multiple sessions separately."""
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 10)
        tracker.track_usage("session_2", ResourceType.EMOTION_CALC, 20)
        tracker.track_usage("session_3", ResourceType.EMOTION_CALC, 30)
        
        assert tracker.get_monthly_usage("session_1").emotion_calc_count == 10
        assert tracker.get_monthly_usage("session_2").emotion_calc_count == 20
        assert tracker.get_monthly_usage("session_3").emotion_calc_count == 30
    
    def test_check_limit_not_reached(self, tracker):
        """Test check_limit_reached when under limit."""
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 100)
        
        result = tracker.check_limit_reached(
            "session_1",
            ResourceType.EMOTION_CALC,
            limit=5000
        )
        assert result is False
    
    def test_check_limit_reached(self, tracker):
        """Test check_limit_reached when at limit."""
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 5000)
        
        result = tracker.check_limit_reached(
            "session_1",
            ResourceType.EMOTION_CALC,
            limit=5000
        )
        assert result is True
    
    def test_check_limit_exceeded(self, tracker):
        """Test check_limit_reached when over limit."""
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 5001)
        
        result = tracker.check_limit_reached(
            "session_1",
            ResourceType.EMOTION_CALC,
            limit=5000
        )
        assert result is True
    
    def test_unlimited_check(self, tracker):
        """Test check with unlimited (-1) limit."""
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 1_000_000)
        
        result = tracker.check_limit_reached(
            "session_1",
            ResourceType.EMOTION_CALC,
            limit=-1
        )
        assert result is False
    
    def test_hosted_conversation_limit_check(self, tracker):
        """Test limit check for hosted conversations."""
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 999)
        
        result = tracker.check_limit_reached(
            "session_1",
            ResourceType.HOSTED_CONVERSATION,
            limit=1000
        )
        assert result is False
        
        # Add one more to hit the limit
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 1)
        result = tracker.check_limit_reached(
            "session_1",
            ResourceType.HOSTED_CONVERSATION,
            limit=1000
        )
        assert result is True
    
    def test_monthly_usage_serialization(self, tracker):
        """Test MonthlyUsage to_dict."""
        tracker.track_usage("session_1", ResourceType.NPC_COUNT, 3)
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 5)
        
        usage = tracker.get_monthly_usage("session_1")
        data = usage.to_dict()
        
        assert data["session_id"] == "session_1"
        assert data["npc_count"] == 3
        assert data["hosted_conversation_count"] == 5
        assert "year_month" in data
        assert "last_updated" in data
    
    def test_get_usage_summary(self, tracker):
        """Test get_usage_summary."""
        tracker.track_usage("session_1", ResourceType.NPC_COUNT, 2)
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 1000)
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 50)
        
        summary = tracker.get_usage_summary(
            "session_1",
            tier_npc_limit=3,
            tier_emotion_limit=5000,
            tier_tts_limit=0,
            tier_api_limit=1000,
            tier_hosted_conversations_limit=1000,
        )
        
        assert summary["usage"]["npc_count"] == 2
        assert summary["usage"]["emotion_calc_count"] == 1000
        assert summary["usage"]["hosted_conversation_count"] == 50
        assert summary["remaining"]["npc_remaining"] == 1
        assert summary["remaining"]["emotion_calc_remaining"] == 4000
        assert summary["remaining"]["hosted_conversations_remaining"] == 950
    
    def test_unlimited_in_summary(self, tracker):
        """Test usage summary with unlimited resources."""
        tracker.track_usage("session_1", ResourceType.NPC_COUNT, 100)
        
        summary = tracker.get_usage_summary(
            "session_1",
            tier_npc_limit=-1,
            tier_emotion_limit=-1,
            tier_tts_limit=-1,
            tier_api_limit=-1,
            tier_hosted_conversations_limit=-1,
        )
        
        assert summary["remaining"]["npc_remaining"] is None
        assert summary["remaining"]["emotion_calc_remaining"] is None
        assert summary["remaining"]["hosted_conversations_remaining"] is None
    
    def test_records_created(self, tracker):
        """Test that usage records are created."""
        tracker.track_usage(
            "session_1",
            ResourceType.EMOTION_CALC,
            10,
            metadata={"source": "test"}
        )
        
        usage = tracker.get_monthly_usage("session_1")
        assert len(usage.records) == 1
        
        record = usage.records[0]
        assert record.resource_type == ResourceType.EMOTION_CALC
        assert record.amount == 10
        assert record.session_id == "session_1"
        assert record.metadata["source"] == "test"
    
    def test_persistence(self, tracker, temp_dir):
        """Test that usage persists across tracker instances."""
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 100)
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 10)
        
        # Create new tracker with same directory
        new_tracker = UsageTracker(data_dir=temp_dir)
        usage = new_tracker.get_monthly_usage("session_1")
        
        assert usage.emotion_calc_count == 100
        assert usage.hosted_conversation_count == 10
    
    def test_reset_monthly(self, tracker):
        """Test monthly reset."""
        tracker.track_usage("session_1", ResourceType.EMOTION_CALC, 100)
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 50)
        tracker.reset_monthly("session_1")
        
        usage = tracker.get_monthly_usage("session_1")
        assert usage.emotion_calc_count == 0
        assert usage.hosted_conversation_count == 0
    
    def test_cleanup_old_data(self, tracker):
        """Test cleanup of old archived data."""
        deleted = tracker.cleanup_old_data(months_to_keep=1)
        assert deleted >= 0


class TestMonthlyUsage:
    """Test MonthlyUsage dataclass."""
    
    def test_default_values(self):
        """Test default values for MonthlyUsage."""
        usage = MonthlyUsage(
            session_id="test",
            year_month="2024-01"
        )
        
        assert usage.npc_count == 0
        assert usage.emotion_calc_count == 0
        assert usage.tts_char_count == 0
        assert usage.api_call_count == 0
        assert usage.hosted_conversation_count == 0
    
    def test_get_total_api_calls(self):
        """Test get_total_api_calls calculation."""
        usage = MonthlyUsage(
            session_id="test",
            year_month="2024-01",
            emotion_calc_count=100,
            tts_char_count=1000,
            api_call_count=50,
            hosted_conversation_count=30,
        )
        
        total = usage.get_total_api_calls()
        # emotion_calc_count + tts_char_count//100 + api_call_count + hosted_conversation_count
        assert total == 100 + 10 + 50 + 30


class TestConversationQuota:
    """Test conversation quota checking logic."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    @pytest.fixture
    def tracker(self, temp_dir):
        """Create tracker with temporary directory."""
        return UsageTracker(data_dir=temp_dir)
    
    def test_byok_user_always_allowed(self, tracker):
        """BYOK users should always pass quota check."""
        result = tracker.check_conversation_quota(
            "session_1", "free", is_byok=True
        )
        
        assert result["allowed"] is True
        assert result["mode"] == "byok"
        assert result["remaining"] is None
        assert result["limit"] == -1
    
    def test_hosted_user_under_limit(self, tracker):
        """Hosted user with usage under limit should be allowed."""
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 500)
        
        result = tracker.check_conversation_quota(
            "session_1", "free", is_byok=False
        )
        
        assert result["allowed"] is True
        assert result["mode"] == "hosted"
        assert result["remaining"] == 500  # 1000 - 500
        assert result["limit"] == 1_000
    
    def test_hosted_user_at_limit(self, tracker):
        """Hosted user who hits limit should be blocked."""
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 1_000)
        
        result = tracker.check_conversation_quota(
            "session_1", "free", is_byok=False
        )
        
        assert result["allowed"] is False
        assert result["mode"] == "hosted"
        assert result["remaining"] == 0
        assert result["error"] == "quota_exceeded"
        assert "switch_to_byok" in result["suggestions"]
        assert "upgrade_tier" in result["suggestions"]
    
    def test_enterprise_unlimited_hosted(self, tracker):
        """Enterprise tier should have unlimited hosted conversations."""
        tracker.track_usage("session_1", ResourceType.HOSTED_CONVERSATION, 1_000_000)
        
        result = tracker.check_conversation_quota(
            "session_1", "enterprise", is_byok=False
        )
        
        assert result["allowed"] is True
        assert result["limit"] == -1
        assert result["remaining"] is None


class TestKeyEncryption:
    """Test KeyEncryption class."""
    
    def test_encrypt_decrypt_cycle(self):
        """Test that encrypt/decrypt is reversible."""
        enc = KeyEncryption(secret_key="test_secret_key")
        plaintext = "sk-test-1234567890abcdef"
        
        ciphertext = enc.encrypt(plaintext)
        assert ciphertext != plaintext
        
        decrypted = enc.decrypt(ciphertext)
        assert decrypted == plaintext
    
    def test_different_keys_produce_different_ciphertext(self):
        """Different secrets should produce different ciphertext."""
        enc1 = KeyEncryption(secret_key="secret1")
        enc2 = KeyEncryption(secret_key="secret2")
        
        plaintext = "sk-test-1234567890"
        
        ct1 = enc1.encrypt(plaintext)
        ct2 = enc2.encrypt(plaintext)
        
        assert ct1 != ct2
    
    def test_empty_secret_fallback(self):
        """Test with no secret (dev fallback)."""
        enc = KeyEncryption(secret_key="")
        plaintext = "sk-test-key"
        
        ciphertext = enc.encrypt(plaintext)
        decrypted = enc.decrypt(ciphertext)
        assert decrypted == plaintext


class TestUserKeyManager:
    """Test UserKeyManager for BYOK key storage."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    @pytest.fixture
    def key_manager(self, temp_dir):
        """Create key manager with temporary directory."""
        keys_dir = temp_dir / "user_keys"
        keys_dir.mkdir(parents=True, exist_ok=True)
        encryption = KeyEncryption(secret_key="test_encryption_key")
        return UserKeyManager(keys_dir=keys_dir, encryption=encryption)
    
    def test_set_and_get_key(self, key_manager):
        """Test setting and retrieving a key."""
        key_info = key_manager.set_key(
            session_id="session_1",
            provider="openai",
            api_key="sk-test-1234567890",
        )
        
        assert key_info.provider == "openai"
        assert key_info.key_last4 == "7890"
        assert key_info.verified is True
        
        # Retrieve the key
        key_data = key_manager.get_key("session_1")
        assert key_data is not None
        assert key_data["provider"] == "openai"
        assert key_data["api_key"] == "sk-test-1234567890"
        assert key_data["key_last4"] == "7890"
    
    def test_set_multiple_providers(self, key_manager):
        """Test setting keys for multiple providers."""
        key_manager.set_key("session_1", "openai", "sk-openai-key1234")
        key_manager.set_key("session_1", "deepseek", "sk-deepseek-key5678")
        
        # Active should be the last one set (deepseek)
        info = key_manager.get_all_keys_info("session_1")
        assert info["active_provider"] == "deepseek"
        assert info["mode"] == "byok"
        assert len(info["providers"]) == 2
        
        # Get specific provider
        key_data = key_manager.get_key("session_1", "openai")
        assert key_data["api_key"] == "sk-openai-key1234"
    
    def test_is_byok(self, key_manager):
        """Test is_byok detection."""
        assert key_manager.is_byok("session_1") is False
        
        key_manager.set_key("session_1", "openai", "sk-test-key")
        assert key_manager.is_byok("session_1") is True
    
    def test_delete_specific_provider(self, key_manager):
        """Test deleting a specific provider's key."""
        key_manager.set_key("session_1", "openai", "sk-openai-key")
        key_manager.set_key("session_1", "deepseek", "sk-deepseek-key")
        
        # Delete openai, deepseek should remain active
        deleted = key_manager.delete_key("session_1", provider="openai")
        assert deleted is True
        
        info = key_manager.get_all_keys_info("session_1")
        assert info["active_provider"] == "deepseek"
        assert len(info["providers"]) == 1
    
    def test_delete_all_keys(self, key_manager):
        """Test deleting all keys (revert to hosted)."""
        key_manager.set_key("session_1", "openai", "sk-test-key")
        
        deleted = key_manager.delete_key("session_1")  # No provider = delete all
        assert deleted is True
        
        # Should be in hosted mode now
        info = key_manager.get_all_keys_info("session_1")
        assert info["mode"] == "hosted"
        assert key_manager.is_byok("session_1") is False
    
    def test_get_all_keys_info_no_keys(self, key_manager):
        """Test get_all_keys_info when no keys are configured."""
        info = key_manager.get_all_keys_info("session_1")
        
        assert info["mode"] == "hosted"
        assert info["active_provider"] is None
        assert info["providers"] == []
    
    def test_key_last4_display(self, key_manager):
        """Test that key_last4 only shows last 4 characters."""
        key_manager.set_key("session_1", "openai", "sk-very-long-api-key-1234")
        
        key_data = key_manager.get_key("session_1")
        assert key_data["key_last4"] == "1234"
        
        # Full key should still be retrievable
        assert key_data["api_key"] == "sk-very-long-api-key-1234"
    
    def test_set_key_with_model_and_base_url(self, key_manager):
        """Test setting a key with model name and base URL."""
        key_manager.set_key(
            "session_1",
            "deepseek",
            "sk-deepseek-key",
            model_name="deepseek-chat",
            base_url="https://custom.api.deepseek.com"
        )
        
        key_data = key_manager.get_key("session_1")
        assert key_data["model_name"] == "deepseek-chat"
        assert key_data["base_url"] == "https://custom.api.deepseek.com"
    
    def test_delete_nonexistent_key(self, key_manager):
        """Test deleting a key that doesn't exist."""
        deleted = key_manager.delete_key("nonexistent_session")
        assert deleted is False


class TestGlobalFunctions:
    """Test module-level convenience functions."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_track_usage_function(self, temp_dir):
        """Test track_usage convenience function."""
        with patch('neshama.billing.usage._tracker', UsageTracker(data_dir=temp_dir)):
            track_usage("session_1", ResourceType.EMOTION_CALC, 10)
            
            usage = get_monthly_usage("session_1")
            assert usage.emotion_calc_count == 10
    
    def test_check_limit_reached_function(self, temp_dir):
        """Test check_limit_reached convenience function."""
        tracker = UsageTracker(data_dir=temp_dir)
        tracker.track_usage("session_1", ResourceType.NPC_COUNT, 5)
        
        with patch('neshama.billing.usage._tracker', tracker):
            result = check_limit_reached("session_1", ResourceType.NPC_COUNT, 10)
            assert result is False
            
            result = check_limit_reached("session_1", ResourceType.NPC_COUNT, 5)
            assert result is True
