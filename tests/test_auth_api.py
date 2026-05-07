"""
Tests for Neshama Auth API and Trial Mode

Covers:
- POST /api/auth/register — Account creation
- POST /api/auth/login — Login
- POST /api/auth/trial — Anonymous trial
- GET  /api/auth/me — User info
- POST /api/auth/api-key — Regenerate API key
- Trial token validation and quota tracking
"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        yield data_dir


@pytest.fixture
def client(temp_data_dir):
    """Create a test client with temporary data directory."""
    # Patch data paths before importing
    import neshama.web.api.auth as auth_module
    
    original_users = auth_module.USERS_FILE
    original_trials = auth_module.TRIALS_FILE
    original_data = auth_module.DATA_DIR
    
    auth_module.DATA_DIR = temp_data_dir
    auth_module.USERS_FILE = temp_data_dir / "users.json"
    auth_module.TRIALS_FILE = temp_data_dir / "trials.json"
    
    from neshama.web.server import create_app
    app = create_app()
    test_client = TestClient(app)
    
    yield test_client
    
    # Restore
    auth_module.DATA_DIR = original_data
    auth_module.USERS_FILE = original_users
    auth_module.TRIALS_FILE = original_trials


# ── Registration Tests ────────────────────────────────────────────────────────

class TestRegister:
    def test_register_success(self, client):
        """Test successful registration."""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "name": "TestUser"
        })
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["user_id"].startswith("usr_")
        assert "api_key" in data
        assert data["api_key"].startswith("nsk_")
        assert data["tier"] == "free"
        assert "token" in data

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email."""
        # First registration
        client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "password123",
            "name": "User1"
        })
        
        # Duplicate email
        response = client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "password456",
            "name": "User2"
        })
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]

    def test_register_short_password(self, client):
        """Test registration with short password."""
        response = client.post("/api/auth/register", json={
            "email": "short@example.com",
            "password": "12345",
            "name": "TestUser"
        })
        assert response.status_code == 400
        assert "6 characters" in response.json()["detail"]

    def test_register_empty_name(self, client):
        """Test registration with empty name."""
        response = client.post("/api/auth/register", json={
            "email": "empty@example.com",
            "password": "password123",
            "name": ""
        })
        assert response.status_code == 400

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
            "name": "TestUser"
        })
        assert response.status_code == 422  # Validation error


# ── Login Tests ───────────────────────────────────────────────────────────────

class TestLogin:
    def _register_user(self, client, email="login@example.com", password="password123", name="LoginUser"):
        return client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "name": name
        })

    def test_login_success(self, client):
        """Test successful login."""
        self._register_user(client)
        
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "api_key" in data
        assert data["api_key"].startswith("nsk_")
        assert "token" in data

    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        self._register_user(client)
        
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "password123"
        })
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ── Trial Tests ───────────────────────────────────────────────────────────────

class TestTrial:
    def test_trial_success(self, client):
        """Test successful trial creation."""
        response = client.post("/api/auth/trial")
        assert response.status_code == 200
        data = response.json()
        assert "trial_token" in data
        assert data["trial_token"].startswith("nsk_")
        assert data["remaining_conversations"] == 50
        assert "24h" in data["expires_in"]

    def test_trial_me_endpoint(self, client):
        """Test /me endpoint with trial token."""
        # Create trial
        trial_resp = client.post("/api/auth/trial")
        trial_token = trial_resp.json()["trial_token"]
        
        # Get trial info
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {trial_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "trial"
        assert data["conversations_limit"] == 50
        assert data["conversations_used"] == 0


# ── User Info Tests ───────────────────────────────────────────────────────────

class TestUserInfo:
    def test_me_with_api_key(self, client):
        """Test /me endpoint with API key."""
        # Register
        reg_resp = client.post("/api/auth/register", json={
            "email": "me@example.com",
            "password": "password123",
            "name": "MeUser"
        })
        api_key = reg_resp.json()["api_key"]
        
        # Get user info
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {api_key}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["name"] == "MeUser"
        assert data["tier"] == "free"
        assert data["api_key_last4"] == api_key[-4:]

    def test_me_with_jwt_token(self, client):
        """Test /me endpoint with JWT token."""
        reg_resp = client.post("/api/auth/register", json={
            "email": "jwt@example.com",
            "password": "password123",
            "name": "JWTUser"
        })
        jwt_token = reg_resp.json()["token"]
        
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {jwt_token}"
        })
        assert response.status_code == 200

    def test_me_unauthorized(self, client):
        """Test /me without authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


# ── API Key Regeneration Tests ────────────────────────────────────────────────

class TestApiKeyRegeneration:
    def test_regenerate_api_key(self, client):
        """Test API key regeneration."""
        # Register
        reg_resp = client.post("/api/auth/register", json={
            "email": "regen@example.com",
            "password": "password123",
            "name": "RegenUser"
        })
        old_key = reg_resp.json()["api_key"]
        jwt_token = reg_resp.json()["token"]
        
        # Regenerate
        response = client.post("/api/auth/api-key", headers={
            "Authorization": f"Bearer {jwt_token}"
        })
        assert response.status_code == 200
        new_key = response.json()["api_key"]
        assert new_key != old_key
        assert new_key.startswith("nsk_")

    def test_regenerate_unauthorized(self, client):
        """Test API key regeneration without auth."""
        response = client.post("/api/auth/api-key")
        assert response.status_code == 401


# ── Trial Manager Unit Tests ─────────────────────────────────────────────────

class TestTrialManager:
    def test_create_trial(self, temp_data_dir):
        """Test TrialManager trial creation."""
        from neshama.billing.trial import TrialManager
        
        manager = TrialManager(data_dir=temp_data_dir)
        result = manager.create_trial()
        
        assert "trial_id" in result
        assert "trial_token" in result
        assert result["remaining_conversations"] == 50
        assert result["trial_token"].startswith("nsk_trial_")

    def test_validate_trial(self, temp_data_dir):
        """Test trial validation."""
        from neshama.billing.trial import TrialManager
        
        manager = TrialManager(data_dir=temp_data_dir)
        result = manager.create_trial()
        token = result["trial_token"]
        
        # Should be valid
        trial = manager.validate_trial(token)
        assert trial is not None
        assert trial["conversations_used"] == 0

    def test_track_conversation(self, temp_data_dir):
        """Test conversation tracking."""
        from neshama.billing.trial import TrialManager
        
        manager = TrialManager(data_dir=temp_data_dir)
        result = manager.create_trial()
        token = result["trial_token"]
        
        # Track 50 conversations
        for i in range(50):
            assert manager.track_conversation(token) is True
        
        # 51st should fail
        assert manager.track_conversation(token) is False

    def test_get_remaining(self, temp_data_dir):
        """Test remaining conversation count."""
        from neshama.billing.trial import TrialManager
        
        manager = TrialManager(data_dir=temp_data_dir)
        result = manager.create_trial()
        token = result["trial_token"]
        
        assert manager.get_remaining(token) == 50
        manager.track_conversation(token)
        assert manager.get_remaining(token) == 49

    def test_upgrade_trial(self, temp_data_dir):
        """Test trial upgrade to full account."""
        from neshama.billing.trial import TrialManager
        
        manager = TrialManager(data_dir=temp_data_dir)
        result = manager.create_trial()
        token = result["trial_token"]
        
        # Upgrade
        assert manager.upgrade_trial(token, "usr_12345") is True
        
        # Should no longer validate
        assert manager.validate_trial(token) is None

    def test_cleanup_expired(self, temp_data_dir):
        """Test expired trial cleanup."""
        from neshama.billing.trial import TrialManager
        
        manager = TrialManager(data_dir=temp_data_dir)
        result = manager.create_trial()
        
        # Manually expire the trial
        trials = manager._load_trials()
        for tid, trial in trials.items():
            trial["expires_at"] = (datetime.now() - timedelta(days=8)).isoformat()
        manager._save_trials(trials)
        
        # Cleanup
        removed = manager.cleanup_expired(max_age_days=7)
        assert removed >= 1

    def test_get_stats(self, temp_data_dir):
        """Test trial statistics."""
        from neshama.billing.trial import TrialManager
        
        manager = TrialManager(data_dir=temp_data_dir)
        manager.create_trial()
        manager.create_trial()
        
        stats = manager.get_stats()
        assert stats["total_trials"] == 2
        assert stats["active"] == 2


# ── JWT Token Tests ──────────────────────────────────────────────────────────

class TestJWTTokens:
    def test_jwt_generation_and_verification(self):
        """Test JWT token generation and verification."""
        from neshama.web.api.auth import _generate_jwt, _verify_jwt
        
        token = _generate_jwt("usr_test123", "free", expiry_hours=1)
        payload = _verify_jwt(token)
        
        assert payload is not None
        assert payload["sub"] == "usr_test123"
        assert payload["tier"] == "free"

    def test_jwt_expired(self):
        """Test expired JWT token."""
        from neshama.web.api.auth import _generate_jwt, _verify_jwt
        
        # Create token that's already expired
        token = _generate_jwt("usr_expired", "free", expiry_hours=-1)
        payload = _verify_jwt(token)
        
        assert payload is None

    def test_jwt_invalid_signature(self):
        """Test JWT with invalid signature."""
        from neshama.web.api.auth import _verify_jwt
        
        # Tampered token
        fake_token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c3JfaGFja2VkIn0.fakesignature"
        payload = _verify_jwt(fake_token)
        
        assert payload is None


# ── Password Hashing Tests ───────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_and_verify(self):
        """Test password hashing and verification."""
        from neshama.web.api.auth import _hash_password, _verify_password
        
        hashed = _hash_password("mypassword123")
        assert _verify_password("mypassword123", hashed) is True
        assert _verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)."""
        from neshama.web.api.auth import _hash_password
        
        hash1 = _hash_password("samepassword")
        hash2 = _hash_password("samepassword")
        assert hash1 != hash2  # Different salts


# ── API Key Format Tests ─────────────────────────────────────────────────────

class TestApiKeyFormat:
    def test_api_key_format(self):
        """Test API key generation format."""
        from neshama.web.api.auth import _generate_api_key
        
        key = _generate_api_key()
        assert key.startswith("nsk_")
        assert len(key) > 10  # Should be long enough
