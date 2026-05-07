# Tests - License API
"""
Comprehensive tests for the Neshama License system.

Covers:
- License key generation and parsing (with region)
- Region isolation / anti-arbitrage
- License validation (valid, invalid, expired, revoked, region mismatch)
- Machine activation / deactivation / binding limits
- Grace period
- Feature checking
- Redis caching (with in-memory fallback)
- Admin endpoints (generate, list, revoke)
- Pricing by region
"""

import json
import os
import tempfile
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from neshama.billing.license import (
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
    get_region_pricing,
    PLAN_CODES,
    PLAN_FEATURES,
    PLAN_NPC_LIMITS,
    MACHINE_LIMITS,
    GRACE_PERIOD_DAYS,
    REGION_CODES,
    REGION_CODE_REVERSE,
    REGION_DISPLAY_NAMES,
    REGION_PRICING,
    DOMAIN_REGION_MAP,
    SAFE_ALPHABET,
    _generate_checksum,
    _verify_checksum,
    _free_result,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test license storage."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def store(temp_dir):
    """Create a LicenseStore with a temporary file."""
    return LicenseStore(storage_path=temp_dir / "test_licenses.json")


@pytest.fixture
def cache():
    """Create a LicenseCache (will use in-memory fallback in tests)."""
    return LicenseCache()


def _future_expires(days=365):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past_expires(days=1):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# ══════════════════════════════════════════════════════════════════════════════
# 1. License Key Generation & Parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestLicenseKeyGeneration:
    """Tests for license key generation with region support."""

    def test_generate_indie_global_key(self):
        key = generate_license_key("indie", "global")
        parts = key.split("-")
        assert parts[0] == "NSH"
        assert parts[1] == "I"
        assert parts[2] == "G"
        assert len(parts[3]) == 4
        assert len(parts[4]) == 4
        assert len(parts[5]) == 2

    def test_generate_indie_china_key(self):
        key = generate_license_key("indie", "cn")
        parts = key.split("-")
        assert parts[0] == "NSH"
        assert parts[1] == "I"
        assert parts[2] == "C"
        assert len(parts[3]) == 4
        assert len(parts[4]) == 4
        assert len(parts[5]) == 2

    def test_generate_all_plans_all_regions(self):
        for plan in PLAN_CODES:
            for region in REGION_CODES:
                key = generate_license_key(plan, region)
                parsed = parse_license_key(key)
                assert parsed is not None, f"Failed to parse key for {plan}/{region}: {key}"
                assert parsed["plan"] == plan
                assert parsed["region"] == region

    def test_generate_invalid_plan_raises(self):
        with pytest.raises(ValueError, match="Invalid plan"):
            generate_license_key("premium")

    def test_generate_invalid_region_raises(self):
        with pytest.raises(ValueError, match="Invalid region"):
            generate_license_key("indie", "eu")

    def test_keys_are_unique(self):
        keys = {generate_license_key("indie", "global") for _ in range(100)}
        assert len(keys) == 100  # All keys are unique

    def test_safe_alphabet_no_confusing_chars(self):
        """No O, 0, I, 1 in generated keys."""
        for _ in range(50):
            key = generate_license_key("studio", "global")
            random_part = key.split("-")[3] + key.split("-")[4]
            for c in random_part:
                assert c not in "O0I1", f"Confusing char '{c}' found in key {key}"


class TestLicenseKeyParsing:
    """Tests for license key parsing with region support."""

    def test_parse_valid_global_key(self):
        key = generate_license_key("enterprise", "global")
        parsed = parse_license_key(key)
        assert parsed is not None
        assert parsed["plan"] == "enterprise"
        assert parsed["region"] == "global"
        assert parsed["region_code"] == "G"

    def test_parse_valid_china_key(self):
        key = generate_license_key("studio", "cn")
        parsed = parse_license_key(key)
        assert parsed is not None
        assert parsed["plan"] == "studio"
        assert parsed["region"] == "cn"
        assert parsed["region_code"] == "C"

    def test_parse_empty_key(self):
        assert parse_license_key("") is None
        assert parse_license_key(None) is None

    def test_parse_garbage_key(self):
        assert parse_license_key("NOT-A-VALID-KEY") is None

    def test_parse_tampered_checksum(self):
        key = generate_license_key("indie", "global")
        parts = key.split("-")
        # Corrupt the checksum
        parts[-1] = "ZZ"
        tampered = "-".join(parts)
        assert parse_license_key(tampered) is None

    def test_parse_tampered_plan(self):
        key = generate_license_key("indie", "global")
        parts = key.split("-")
        parts[1] = "X"  # Invalid plan code
        tampered = "-".join(parts)
        assert parse_license_key(tampered) is None

    def test_parse_tampered_region(self):
        key = generate_license_key("indie", "global")
        parts = key.split("-")
        parts[2] = "X"  # Invalid region code
        tampered = "-".join(parts)
        assert parse_license_key(tampered) is None

    def test_case_insensitive_parsing(self):
        key = generate_license_key("indie", "global")
        assert parse_license_key(key.lower()) is not None


# ══════════════════════════════════════════════════════════════════════════════
# 2. Checksum Verification
# ══════════════════════════════════════════════════════════════════════════════

class TestChecksum:
    """Tests for HMAC-based checksum generation and verification."""

    def test_checksum_deterministic(self):
        cs1 = _generate_checksum("I", "G", ("A1B2", "C3D4"))
        cs2 = _generate_checksum("I", "G", ("A1B2", "C3D4"))
        assert cs1 == cs2

    def test_checksum_different_plan(self):
        cs1 = _generate_checksum("I", "G", ("A1B2", "C3D4"))
        cs2 = _generate_checksum("S", "G", ("A1B2", "C3D4"))
        assert cs1 != cs2

    def test_checksum_different_region(self):
        """Region affects checksum — this is the anti-tampering mechanism."""
        cs1 = _generate_checksum("I", "C", ("A1B2", "C3D4"))
        cs2 = _generate_checksum("I", "G", ("A1B2", "C3D4"))
        assert cs1 != cs2

    def test_verify_valid_checksum(self):
        cs = _generate_checksum("I", "G", ("A1B2", "C3D4"))
        assert _verify_checksum("I", "G", ("A1B2", "C3D4"), cs) is True

    def test_verify_invalid_checksum(self):
        assert _verify_checksum("I", "G", ("A1B2", "C3D4"), "XX") is False


# ══════════════════════════════════════════════════════════════════════════════
# 3. Region Detection & Isolation
# ══════════════════════════════════════════════════════════════════════════════

class TestRegionDetection:
    """Tests for region detection from Host header."""

    def test_detect_cn_from_host(self):
        assert detect_region_from_host("api.neshama.cn") == "cn"

    def test_detect_global_from_host(self):
        assert detect_region_from_host("api.neshama.pw") == "global"

    def test_detect_cn_with_port(self):
        assert detect_region_from_host("api.neshama.cn:8420") == "cn"

    def test_detect_global_with_port(self):
        assert detect_region_from_host("api.neshama.pw:443") == "global"

    def test_detect_localhost(self):
        assert detect_region_from_host("localhost") == "global"

    def test_detect_127(self):
        assert detect_region_from_host("127.0.0.1") == "global"

    def test_detect_unknown_domain(self):
        assert detect_region_from_host("custom.server.com") == "global"

    def test_detect_empty_host(self):
        assert detect_region_from_host("") == "global"

    def test_detect_none_host(self):
        assert detect_region_from_host(None) == "global"

    def test_detect_subdomain_of_cn(self):
        assert detect_region_from_host("test.api.neshama.cn") == "cn"


class TestRegionMatch:
    """Tests for region matching / anti-arbitrage."""

    def test_cn_matches_cn(self):
        match, error = check_region_match("cn", "cn")
        assert match is True
        assert error == ""

    def test_global_matches_global(self):
        match, error = check_region_match("global", "global")
        assert match is True
        assert error == ""

    def test_cn_does_not_match_global(self):
        match, error = check_region_match("cn", "global")
        assert match is False
        assert "China" in error or "中国区" in error
        assert "mismatch" in error.lower() or "not permitted" in error.lower()

    def test_global_does_not_match_cn(self):
        match, error = check_region_match("global", "cn")
        assert match is False
        assert "Global" in error or "国际区" in error


# ══════════════════════════════════════════════════════════════════════════════
# 4. License Store
# ══════════════════════════════════════════════════════════════════════════════

class TestLicenseStore:
    """Tests for LicenseStore CRUD operations."""

    def test_put_and_get(self, store):
        record = LicenseRecord(
            license_key="NSH-I-G-TEST-TEST-AB",
            plan="indie",
            region="global",
            status="active",
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=_future_expires(),
        )
        store.put(record)
        retrieved = store.get("NSH-I-G-TEST-TEST-AB")
        assert retrieved is not None
        assert retrieved.plan == "indie"
        assert retrieved.region == "global"

    def test_get_nonexistent(self, store):
        assert store.get("NSH-I-G-NOPE-NOPE-AB") is None

    def test_delete(self, store):
        record = LicenseRecord(
            license_key="NSH-I-G-TEST-TEST-AB",
            plan="indie",
            region="global",
            status="active",
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=_future_expires(),
        )
        store.put(record)
        assert store.delete("NSH-I-G-TEST-TEST-AB") is True
        assert store.get("NSH-I-G-TEST-TEST-AB") is None

    def test_delete_nonexistent(self, store):
        assert store.delete("NSH-I-G-NOPE-NOPE-AB") is False

    def test_list_all(self, store):
        for plan in ["free", "indie", "studio", "enterprise"]:
            key = generate_license_key(plan, "global")
            record = LicenseRecord(
                license_key=key,
                plan=plan,
                region="global",
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
                expires_at=_future_expires(),
            )
            store.put(record)
        all_licenses = store.list_all()
        assert len(all_licenses) >= 4

    def test_list_filter_by_plan(self, store):
        for plan in ["free", "indie", "studio"]:
            key = generate_license_key(plan, "global")
            record = LicenseRecord(
                license_key=key,
                plan=plan,
                region="global",
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
                expires_at=_future_expires(),
            )
            store.put(record)
        indie_only = store.list_all(plan="indie")
        assert all(r.plan == "indie" for r in indie_only)

    def test_list_filter_by_region(self, store):
        for region in ["cn", "global"]:
            key = generate_license_key("indie", region)
            record = LicenseRecord(
                license_key=key,
                plan="indie",
                region=region,
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
                expires_at=_future_expires(),
            )
            store.put(record)
        cn_only = store.list_all(region="cn")
        assert all(r.region == "cn" for r in cn_only)

    def test_legacy_record_without_region(self, store):
        """Records without region field should default to 'global'."""
        # Manually insert a legacy record
        store._data["NSH-I-TEST-TEST-AB"] = {
            "license_key": "NSH-I-TEST-TEST-AB",
            "plan": "indie",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": _future_expires(),
            "machines": [],
            "last_validated_at": None,
            "metadata": {},
        }
        store._save()
        store._load()
        record = store.get("NSH-I-TEST-TEST-AB")
        assert record is not None
        assert record.region == "global"  # Default for legacy records


# ══════════════════════════════════════════════════════════════════════════════
# 5. Machine Binding
# ══════════════════════════════════════════════════════════════════════════════

class TestMachineBinding:
    """Tests for machine activation/deactivation with binding limits."""

    def _make_license(self, store, plan="indie", region="global"):
        key = generate_license_key(plan, region)
        record = LicenseRecord(
            license_key=key,
            plan=plan,
            region=region,
            status="active",
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=_future_expires(),
        )
        store.put(record)
        return key

    def test_bind_first_machine(self, store):
        key = self._make_license(store, "indie")
        assert store.add_machine(key, "machine_001") is True
        record = store.get(key)
        assert len(record.machines) == 1
        assert record.machines[0]["machine_id"] == "machine_001"

    def test_bind_same_machine_twice_updates_last_seen(self, store):
        key = self._make_license(store, "indie")
        assert store.add_machine(key, "machine_001") is True
        assert store.add_machine(key, "machine_001") is True  # No duplicate
        record = store.get(key)
        assert len(record.machines) == 1

    def test_indie_max_2_machines(self, store):
        key = self._make_license(store, "indie")
        assert store.add_machine(key, "machine_001") is True
        assert store.add_machine(key, "machine_002") is True
        assert store.add_machine(key, "machine_003") is False  # Exceeds limit

    def test_studio_max_5_machines(self, store):
        key = self._make_license(store, "studio")
        for i in range(5):
            assert store.add_machine(key, f"machine_{i:03d}") is True
        assert store.add_machine(key, "machine_005") is False  # Exceeds limit

    def test_enterprise_unlimited_machines(self, store):
        key = self._make_license(store, "enterprise")
        for i in range(20):
            assert store.add_machine(key, f"machine_{i:03d}") is True

    def test_unbind_machine(self, store):
        key = self._make_license(store, "indie")
        store.add_machine(key, "machine_001")
        store.add_machine(key, "machine_002")
        assert store.remove_machine(key, "machine_001") is True
        record = store.get(key)
        assert len(record.machines) == 1
        assert record.machines[0]["machine_id"] == "machine_002"

    def test_unbind_frees_slot(self, store):
        key = self._make_license(store, "indie")
        store.add_machine(key, "machine_001")
        store.add_machine(key, "machine_002")
        store.remove_machine(key, "machine_001")
        # Now we have 1 slot free again
        assert store.add_machine(key, "machine_003") is True

    def test_unbind_nonexistent_machine(self, store):
        key = self._make_license(store, "indie")
        assert store.remove_machine(key, "ghost_machine") is False


# ══════════════════════════════════════════════════════════════════════════════
# 6. License Validation
# ══════════════════════════════════════════════════════════════════════════════

class TestLicenseValidation:
    """Tests for the validate_license function."""

    def _create_and_store(self, store, plan="indie", region="global", expires_at=None):
        key = generate_license_key(plan, region)
        record = LicenseRecord(
            license_key=key,
            plan=plan,
            region=region,
            status="active",
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=expires_at or _future_expires(),
        )
        store.put(record)
        return key

    def test_validate_valid_license(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        result = validate_license(key, "machine_001", store=store, cache=cache)
        assert result.valid is True
        assert result.plan == "indie"
        assert result.region == "global"
        assert result.region_match is True
        assert result.max_npcs == 10

    def test_validate_china_license(self, store, cache):
        key = self._create_and_store(store, "studio", "cn")
        result = validate_license(key, "machine_001", request_region="cn", store=store, cache=cache)
        assert result.valid is True
        assert result.plan == "studio"
        assert result.region == "cn"
        assert result.region_match is True

    def test_validate_region_mismatch(self, store, cache):
        """China license used on global endpoint → rejected."""
        key = self._create_and_store(store, "indie", "cn")
        result = validate_license(key, "machine_001", request_region="global", store=store, cache=cache)
        assert result.valid is False
        assert result.region == "cn"
        assert result.region_match is False
        assert hasattr(result, '_region_error')
        assert "mismatch" in result._region_error.lower() or "not permitted" in result._region_error.lower()

    def test_validate_global_on_cn_endpoint(self, store, cache):
        """Global license used on China endpoint → rejected."""
        key = self._create_and_store(store, "indie", "global")
        result = validate_license(key, "machine_001", request_region="cn", store=store, cache=cache)
        assert result.valid is False
        assert result.region_match is False

    def test_validate_invalid_key_format(self, store, cache):
        result = validate_license("GARBAGE-KEY", "machine_001", store=store, cache=cache)
        assert result.valid is False
        assert result.plan == "free"

    def test_validate_nonexistent_key(self, store, cache):
        key = generate_license_key("indie", "global")
        result = validate_license(key, "machine_001", store=store, cache=cache)
        assert result.valid is False

    def test_validate_revoked_license(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        record = store.get(key)
        record.status = "revoked"
        store.put(record)
        result = validate_license(key, "machine_001", store=store, cache=cache)
        assert result.valid is False

    def test_validate_expired_license(self, store, cache):
        key = self._create_and_store(store, "indie", "global", expires_at=_past_expires())
        result = validate_license(key, "machine_001", store=store, cache=cache)
        assert result.valid is False

    def test_validate_free_plan_no_machine_binding(self, store, cache):
        """Free plan doesn't require machine binding."""
        key = self._create_and_store(store, "free", "global")
        result = validate_license(key, "any_machine", store=store, cache=cache)
        assert result.valid is True
        assert result.max_npcs == 3

    def test_validate_with_bound_machine(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        store.add_machine(key, "machine_001")
        result = validate_license(key, "machine_001", store=store, cache=cache)
        assert result.valid is True

    def test_validate_with_unbound_machine(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        store.add_machine(key, "machine_001")
        # Try to validate from a different machine
        result = validate_license(key, "machine_999", store=store, cache=cache)
        assert result.valid is False

    def test_validate_no_region_check_when_region_none(self, store, cache):
        """When request_region is None, region check is skipped."""
        key = self._create_and_store(store, "indie", "cn")
        result = validate_license(key, "machine_001", request_region=None, store=store, cache=cache)
        # Should succeed because no region check was performed
        assert result.valid is True

    def test_validate_enterprise_features(self, store, cache):
        key = self._create_and_store(store, "enterprise", "global")
        result = validate_license(key, "machine_001", store=store, cache=cache)
        assert result.valid is True
        assert "private_deploy" in result.features
        assert "custom_memory" in result.features
        assert result.max_npcs == -1  # unlimited


# ══════════════════════════════════════════════════════════════════════════════
# 7. License Activation & Deactivation
# ══════════════════════════════════════════════════════════════════════════════

class TestActivation:
    """Tests for activate_license and deactivate_license."""

    def _create_and_store(self, store, plan="indie", region="global"):
        key = generate_license_key(plan, region)
        record = LicenseRecord(
            license_key=key,
            plan=plan,
            region=region,
            status="active",
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=_future_expires(),
        )
        store.put(record)
        return key

    def test_activate_success(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        success, msg = activate_license(key, "machine_001", store=store, cache=cache)
        assert success is True
        assert "success" in msg.lower()

    def test_activate_region_mismatch(self, store, cache):
        key = self._create_and_store(store, "indie", "cn")
        success, msg = activate_license(key, "machine_001", request_region="global", store=store, cache=cache)
        assert success is False
        assert "mismatch" in msg.lower() or "not permitted" in msg.lower()

    def test_activate_expired_license(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        record = store.get(key)
        record.expires_at = _past_expires()
        store.put(record)
        success, msg = activate_license(key, "machine_001", store=store, cache=cache)
        assert success is False
        assert "expired" in msg.lower()

    def test_activate_revoked_license(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        record = store.get(key)
        record.status = "revoked"
        store.put(record)
        success, msg = activate_license(key, "machine_001", store=store, cache=cache)
        assert success is False

    def test_activate_free_plan(self, store, cache):
        key = self._create_and_store(store, "free", "global")
        success, msg = activate_license(key, "machine_001", store=store, cache=cache)
        assert success is True
        assert "not require" in msg.lower()

    def test_activate_machine_limit(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        activate_license(key, "machine_001", store=store, cache=cache)
        activate_license(key, "machine_002", store=store, cache=cache)
        success, msg = activate_license(key, "machine_003", store=store, cache=cache)
        assert success is False
        assert "limit" in msg.lower()

    def test_deactivate_success(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        activate_license(key, "machine_001", store=store, cache=cache)
        success, msg = deactivate_license(key, "machine_001", store=store, cache=cache)
        assert success is True

    def test_deactivate_not_bound(self, store, cache):
        key = self._create_and_store(store, "indie", "global")
        success, msg = deactivate_license(key, "ghost_machine", store=store, cache=cache)
        assert success is False


# ══════════════════════════════════════════════════════════════════════════════
# 8. Grace Period
# ══════════════════════════════════════════════════════════════════════════════

class TestGracePeriod:
    """Tests for offline grace period logic."""

    def test_within_grace_period(self):
        recent = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        within_grace, grace_until = check_grace_period(
            "any-key", last_validated_at=recent
        )
        assert within_grace is True
        assert grace_until is not None

    def test_exceeded_grace_period(self):
        old = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        within_grace, grace_until = check_grace_period(
            "any-key", last_validated_at=old
        )
        assert within_grace is False
        assert grace_until is None

    def test_exactly_7_days_boundary(self):
        """7 days ago should be exactly at the boundary."""
        exactly_7 = (datetime.now(timezone.utc) - timedelta(days=7, seconds=1)).isoformat()
        within_grace, _ = check_grace_period("any-key", last_validated_at=exactly_7)
        assert within_grace is False

    def test_just_under_7_days(self):
        almost = (datetime.now(timezone.utc) - timedelta(days=6, hours=23)).isoformat()
        within_grace, _ = check_grace_period("any-key", last_validated_at=almost)
        assert within_grace is True

    def test_invalid_timestamp(self):
        within_grace, _ = check_grace_period("any-key", last_validated_at="not-a-date")
        assert within_grace is False


# ══════════════════════════════════════════════════════════════════════════════
# 9. Feature Checking
# ══════════════════════════════════════════════════════════════════════════════

class TestFeatureChecking:
    """Tests for feature availability by plan."""

    def test_free_features(self):
        assert check_feature("basic_emotion", "free") is True
        assert check_feature("ocean_personality", "free") is True
        assert check_feature("l0_memory", "free") is True

    def test_free_no_advanced_features(self):
        assert check_feature("social_engine", "free") is False
        assert check_feature("l1_memory", "free") is False
        assert check_feature("byok", "free") is False

    def test_indie_features(self):
        assert check_feature("l1_memory", "indie") is True
        assert check_feature("personality_evolution", "indie") is True
        assert check_feature("byok", "indie") is True
        assert check_feature("social_engine", "indie") is False

    def test_studio_features(self):
        assert check_feature("social_engine", "studio") is True
        assert check_feature("info_propagation", "studio") is True
        assert check_feature("story_trigger", "studio") is True
        assert check_feature("entity_graph", "studio") is True
        assert check_feature("l2_memory", "studio") is True
        assert check_feature("private_deploy", "studio") is False

    def test_enterprise_features(self):
        assert check_feature("unlimited_npcs", "enterprise") is True
        assert check_feature("private_deploy", "enterprise") is True
        assert check_feature("custom_memory", "enterprise") is True

    def test_unknown_feature(self):
        assert check_feature("teleportation", "enterprise") is False


# ══════════════════════════════════════════════════════════════════════════════
# 10. License Generation (Service)
# ══════════════════════════════════════════════════════════════════════════════

class TestLicenseGeneration:
    """Tests for the generate_license service function."""

    def test_generate_global_license(self, store):
        key, record = generate_license("indie", "global", store=store)
        assert key.startswith("NSH-I-G-")
        assert record.plan == "indie"
        assert record.region == "global"
        assert record.status == "active"

    def test_generate_china_license(self, store):
        key, record = generate_license("studio", "cn", store=store)
        assert key.startswith("NSH-S-C-")
        assert record.plan == "studio"
        assert record.region == "cn"

    def test_generate_without_region_raises(self, store):
        """Region is now required."""
        with pytest.raises(ValueError, match="Invalid region"):
            generate_license("indie", "eu", store=store)

    def test_generate_with_custom_expiry(self, store):
        custom_expiry = "2028-12-31T23:59:59+00:00"
        key, record = generate_license("enterprise", "global", expires_at=custom_expiry, store=store)
        assert record.expires_at == custom_expiry

    def test_generated_key_stored_and_retrievable(self, store):
        key, _ = generate_license("indie", "global", store=store)
        retrieved = store.get(key)
        assert retrieved is not None
        assert retrieved.license_key == key


# ══════════════════════════════════════════════════════════════════════════════
# 11. License Revocation
# ══════════════════════════════════════════════════════════════════════════════

class TestRevocation:
    """Tests for the revoke_license function."""

    def test_revoke_active_license(self, store, cache):
        key, _ = generate_license("indie", "global", store=store)
        success, msg = revoke_license(key, store=store, cache=cache)
        assert success is True
        record = store.get(key)
        assert record.status == "revoked"

    def test_revoke_already_revoked(self, store, cache):
        key, _ = generate_license("indie", "global", store=store)
        revoke_license(key, store=store, cache=cache)
        success, msg = revoke_license(key, store=store, cache=cache)
        assert success is False
        assert "already" in msg.lower()

    def test_revoke_nonexistent(self, store, cache):
        success, msg = revoke_license("NSH-I-G-NOPE-NOPE-AB", store=store, cache=cache)
        assert success is False
        assert "not found" in msg.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 12. License Status
# ══════════════════════════════════════════════════════════════════════════════

class TestLicenseStatus:
    """Tests for the get_license_status function."""

    def test_status_returns_region_and_pricing(self, store):
        key, _ = generate_license("indie", "cn", store=store)
        status = get_license_status(key, store=store)
        assert status is not None
        assert status["region"] == "cn"
        assert status["pricing"]["currency"] == "CNY"
        assert status["pricing"]["symbol"] == "¥"
        assert status["pricing"]["monthly"] == 4900

    def test_status_global_pricing(self, store):
        key, _ = generate_license("indie", "global", store=store)
        status = get_license_status(key, store=store)
        assert status["pricing"]["currency"] == "USD"
        assert status["pricing"]["symbol"] == "$"
        assert status["pricing"]["monthly"] == 1900

    def test_status_not_found(self, store):
        status = get_license_status("NSH-I-G-NOPE-NOPE-AB", store=store)
        assert status is None


# ══════════════════════════════════════════════════════════════════════════════
# 13. Caching
# ══════════════════════════════════════════════════════════════════════════════

class TestCaching:
    """Tests for the LicenseCache (in-memory fallback)."""

    def test_cache_set_and_get(self):
        c = LicenseCache()
        c.set("key1", "mid1", {"valid": True, "plan": "indie"})
        result = c.get("key1", "mid1")
        assert result is not None
        assert result["valid"] is True

    def test_cache_miss(self):
        c = LicenseCache()
        assert c.get("nokey", "nomid") is None

    def test_cache_invalidate(self):
        c = LicenseCache()
        c.set("key1", "mid1", {"valid": True})
        c.invalidate("key1", "mid1")
        assert c.get("key1", "mid1") is None

    def test_cache_invalidate_all_for_key(self):
        c = LicenseCache()
        c.set("key1", "mid1", {"valid": True})
        c.set("key1", "mid2", {"valid": True})
        c.invalidate("key1")
        assert c.get("key1", "mid1") is None
        assert c.get("key1", "mid2") is None

    def test_cache_ttl_expiry(self):
        c = LicenseCache()
        # Manually set with past expiry
        c._fallback["license:k:m"] = (time.time() - 1, {"valid": True})
        assert c.get("k", "m") is None


# ══════════════════════════════════════════════════════════════════════════════
# 14. Region Pricing
# ══════════════════════════════════════════════════════════════════════════════

class TestRegionPricing:
    """Tests for region-specific pricing."""

    def test_china_pricing(self):
        pricing = get_region_pricing("cn")
        assert pricing["currency"] == "CNY"
        assert pricing["symbol"] == "¥"
        assert pricing["free"] == 0
        assert pricing["indie"] == 4900
        assert pricing["studio"] == 19900
        assert pricing["enterprise"] == 79900

    def test_global_pricing(self):
        pricing = get_region_pricing("global")
        assert pricing["currency"] == "USD"
        assert pricing["symbol"] == "$"
        assert pricing["free"] == 0
        assert pricing["indie"] == 1900
        assert pricing["studio"] == 7900
        assert pricing["enterprise"] == 29900

    def test_unknown_region_defaults_to_global(self):
        pricing = get_region_pricing("eu")
        assert pricing["currency"] == "USD"


# ══════════════════════════════════════════════════════════════════════════════
# 15. Free Result Helper
# ══════════════════════════════════════════════════════════════════════════════

class TestFreeResult:
    """Tests for the _free_result helper."""

    def test_free_result_defaults(self):
        result = _free_result("some reason")
        assert result.valid is False
        assert result.plan == "free"
        assert result.max_npcs == 3
        assert "basic_emotion" in result.features
        assert result.grace_until is not None

    def test_free_result_with_region(self):
        result = _free_result(region="cn")
        assert result.region == "cn"
        assert result.region_match is False


# ══════════════════════════════════════════════════════════════════════════════
# 16. Integration: Full License Lifecycle
# ══════════════════════════════════════════════════════════════════════════════

class TestFullLifecycle:
    """End-to-end tests for the complete license lifecycle."""

    def test_generate_activate_validate_deactivate(self, store, cache):
        # 1. Generate
        key, record = generate_license("studio", "global", store=store)
        assert record.status == "active"

        # 2. Activate (bind machine)
        success, msg = activate_license(key, "machine_abc", request_region="global", store=store, cache=cache)
        assert success is True

        # 3. Validate from bound machine
        result = validate_license(key, "machine_abc", request_region="global", store=store, cache=cache)
        assert result.valid is True
        assert result.plan == "studio"
        assert "social_engine" in result.features

        # 4. Validate from unbound machine fails
        result2 = validate_license(key, "machine_xyz", request_region="global", store=store, cache=cache)
        assert result2.valid is False

        # 5. Deactivate
        success2, msg2 = deactivate_license(key, "machine_abc", store=store, cache=cache)
        assert success2 is True

        # 6. Re-activate on different machine
        success3, msg3 = activate_license(key, "machine_xyz", request_region="global", store=store, cache=cache)
        assert success3 is True

    def test_cross_region_blocked(self, store, cache):
        """Full lifecycle test for cross-region blocking."""
        # Generate a China license
        key, _ = generate_license("indie", "cn", store=store)

        # Try to activate on Global endpoint → blocked
        success, msg = activate_license(key, "machine_001", request_region="global", store=store, cache=cache)
        assert success is False
        assert "mismatch" in msg.lower() or "not permitted" in msg.lower()

        # Validate on Global endpoint → region mismatch
        result = validate_license(key, "machine_001", request_region="global", store=store, cache=cache)
        assert result.valid is False
        assert result.region_match is False

        # Activate on CN endpoint → success
        success2, msg2 = activate_license(key, "machine_001", request_region="cn", store=store, cache=cache)
        assert success2 is True

        # Validate on CN endpoint → success
        result2 = validate_license(key, "machine_001", request_region="cn", store=store, cache=cache)
        assert result2.valid is True
        assert result2.region_match is True
