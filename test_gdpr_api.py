"""
GDPR API Tests

Tests for GDPR-compliant data export, deletion, and consent management endpoints.
Run with: pytest test_gdpr_api.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

# Import the GDPR router and models
import sys
sys.path.insert(0, ".")

from neshama.web.api.gdpr import (
    router,
    ConsentType,
    ConsentStatus,
    UserConsent,
    DataExportResponse,
    DeletionStatus,
    ConsentUpdateRequest,
    GDPRExportRequest,
    get_user_id_from_token,
    get_user_data,
    schedule_data_deletion,
    cancel_data_deletion,
    get_user_consents,
    update_user_consent,
)


# ============================================
# Mock Fixtures
# ============================================

@pytest.fixture
def mock_user_id():
    """Mock user ID for testing."""
    return "test_user_123"


@pytest.fixture
def mock_authorization():
    """Mock authorization header."""
    return "Bearer test_token_abc"


@pytest.fixture
def mock_user_data(mock_user_id):
    """Mock user data for export."""
    return {
        "user_id": mock_user_id,
        "account": {
            "email": "test@example.com",
            "created_at": datetime.now().isoformat(),
            "subscription_status": "active"
        },
        "npcs": [
            {
                "id": "npc_001",
                "name": "Test NPC",
                "personality_config": {
                    "ocean": {"openness": 0.7, "conscientiousness": 0.8}
                }
            }
        ],
        "chat_history": [{"npc_id": "npc_001", "messages": ["Hello", "World"]}],
        "memories": [{"npc_id": "npc_001", "layer": "L0", "entries": ["Test memory"]}],
        "emotions": [{"npc_id": "npc_001", "states": [{"joy": 0.8}]}]
    }


# ============================================
# Unit Tests - Helper Functions
# ============================================

class TestHelperFunctions:
    """Test helper functions used by GDPR endpoints."""

    @pytest.mark.asyncio
    async def test_get_user_id_from_valid_token(self, mock_authorization):
        """Test extracting user ID from valid authorization token."""
        with patch('neshama.web.api.gdpr.get_user_id_from_token') as mock:
            mock.return_value = "test_user_123"
            result = await get_user_id_from_token(mock_authorization)
            assert result == "test_user_123"

    @pytest.mark.asyncio
    async def test_get_user_id_from_invalid_token(self):
        """Test that invalid token returns None."""
        result = await get_user_id_from_token("InvalidToken")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_id_from_missing_header(self):
        """Test that missing authorization returns None."""
        result = await get_user_id_from_token("")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_id_from_none_header(self):
        """Test that None authorization returns None."""
        result = await get_user_id_from_token(None)
        assert result is None


# ============================================
# Unit Tests - Data Export
# ============================================

class TestDataExport:
    """Test data export functionality."""

    @pytest.mark.asyncio
    async def test_get_user_data_returns_all_fields(self, mock_user_id, mock_user_data):
        """Test that get_user_data returns all expected fields."""
        with patch('neshama.web.api.gdpr.get_user_data') as mock:
            mock.return_value = mock_user_data
            result = await get_user_data(mock_user_id)
            
            assert "user_id" in result
            assert "account" in result
            assert "npcs" in result
            assert "chat_history" in result
            assert "memories" in result
            assert "emotions" in result

    @pytest.mark.asyncio
    async def test_schedule_data_deletion_returns_future_date(self, mock_user_id):
        """Test that scheduled deletion returns a date in the future."""
        with patch('neshama.web.api.gdpr.schedule_data_deletion') as mock:
            mock.return_value = datetime.now() + timedelta(days=30)
            result = await schedule_data_deletion(mock_user_id)
            
            assert result > datetime.now()
            # Should be approximately 30 days from now
            delta = result - datetime.now()
            assert 29 <= delta.days <= 31


# ============================================
# Unit Tests - Consent Management
# ============================================

class TestConsentManagement:
    """Test consent management functionality."""

    @pytest.mark.asyncio
    async def test_get_user_consents_returns_all_types(self, mock_user_id):
        """Test that get_user_consents returns all consent types."""
        result = await get_user_consents(mock_user_id)
        
        assert result.user_id == mock_user_id
        assert len(result.consents) == 4  # TOS, Privacy, Marketing, Data Processing
        
        consent_types = [c.consent_type for c in result.consents]
        assert ConsentType.TERMS_OF_SERVICE in consent_types
        assert ConsentType.PRIVACY_POLICY in consent_types
        assert ConsentType.MARKETING in consent_types
        assert ConsentType.DATA_PROCESSING in consent_types

    @pytest.mark.asyncio
    async def test_update_user_consent_returns_status(self, mock_user_id):
        """Test that update_user_consent returns updated status."""
        result = await update_user_consent(
            mock_user_id,
            ConsentType.MARKETING,
            True,
            "1.0"
        )
        
        assert result.consent_type == ConsentType.MARKETING
        assert result.granted is True
        assert result.version == "1.0"
        assert isinstance(result.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_consent_status_model(self):
        """Test ConsentStatus model initialization."""
        now = datetime.now()
        status = ConsentStatus(
            consent_type=ConsentType.TERMS_OF_SERVICE,
            granted=True,
            timestamp=now,
            version="1.0"
        )
        
        assert status.consent_type == ConsentType.TERMS_OF_SERVICE
        assert status.granted is True
        assert status.timestamp == now
        assert status.version == "1.0"

    @pytest.mark.asyncio
    async def test_user_consent_model(self, mock_user_id):
        """Test UserConsent model initialization."""
        now = datetime.now()
        consent = UserConsent(
            user_id=mock_user_id,
            consents=[
                ConsentStatus(
                    consent_type=ConsentType.TERMS_OF_SERVICE,
                    granted=True,
                    timestamp=now,
                    version="1.0"
                )
            ],
            last_updated=now
        )
        
        assert consent.user_id == mock_user_id
        assert len(consent.consents) == 1
        assert consent.last_updated == now


# ============================================
# Unit Tests - Account Deletion
# ============================================

class TestAccountDeletion:
    """Test account deletion functionality."""

    @pytest.mark.asyncio
    async def test_cancel_deletion_returns_true(self, mock_user_id):
        """Test that cancel_deletion returns True on success."""
        result = await cancel_data_deletion(mock_user_id)
        assert result is True


# ============================================
# Unit Tests - Model Validation
# ============================================

class TestModels:
    """Test Pydantic models."""

    def test_consent_update_request_valid(self):
        """Test valid ConsentUpdateRequest."""
        request = ConsentUpdateRequest(
            consent_type=ConsentType.TERMS_OF_SERVICE,
            granted=True,
            version="1.0"
        )
        
        assert request.consent_type == ConsentType.TERMS_OF_SERVICE
        assert request.granted is True
        assert request.version == "1.0"

    def test_consent_update_request_marketing_opt_out(self):
        """Test marketing opt-out request."""
        request = ConsentUpdateRequest(
            consent_type=ConsentType.MARKETING,
            granted=False,
            version="1.0"
        )
        
        assert request.consent_type == ConsentType.MARKETING
        assert request.granted is False

    def test_gdpr_export_request_defaults(self):
        """Test GDPRExportRequest with default values."""
        request = GDPRExportRequest()
        
        assert request.include_npcs is True
        assert request.include_chat_history is True
        assert request.include_memories is True
        assert request.include_emotions is True

    def test_gdpr_export_request_selective(self):
        """Test GDPRExportRequest with selective export."""
        request = GDPRExportRequest(
            include_npcs=True,
            include_chat_history=False,
            include_memories=True,
            include_emotions=False
        )
        
        assert request.include_npcs is True
        assert request.include_chat_history is False
        assert request.include_memories is True
        assert request.include_emotions is False

    def test_data_export_response(self):
        """Test DataExportResponse model."""
        expires_at = datetime.now() + timedelta(hours=24)
        response = DataExportResponse(
            status="success",
            message="Export complete",
            download_url="/api/gdpr/download/123",
            expires_at=expires_at
        )
        
        assert response.status == "success"
        assert response.download_url == "/api/gdpr/download/123"
        assert response.expires_at == expires_at

    def test_deletion_status(self):
        """Test DeletionStatus model."""
        scheduled = datetime.now() + timedelta(days=30)
        status = DeletionStatus(
            status="scheduled",
            message="Deletion scheduled",
            scheduled_deletion_at=scheduled,
            grace_period_days=30
        )
        
        assert status.status == "scheduled"
        assert status.scheduled_deletion_at == scheduled
        assert status.grace_period_days == 30


# ============================================
# Unit Tests - ConsentType Enum
# ============================================

class TestConsentType:
    """Test ConsentType enum values."""

    def test_consent_types_exist(self):
        """Test all expected consent types exist."""
        assert ConsentType.TERMS_OF_SERVICE.value == "terms_of_service"
        assert ConsentType.PRIVACY_POLICY.value == "privacy_policy"
        assert ConsentType.MARKETING.value == "marketing"
        assert ConsentType.DATA_PROCESSING.value == "data_processing"

    def test_consent_type_count(self):
        """Test total number of consent types."""
        assert len(ConsentType) == 4


# ============================================
# Integration Tests (Mock FastAPI App)
# ============================================

class TestGDPREndpoints:
    """Integration tests for GDPR API endpoints."""

    @pytest.fixture
    def test_app(self):
        """Create test FastAPI app with GDPR router."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_health_endpoint(self, client):
        """Test GDPR health check endpoint."""
        response = client.get("/api/gdpr/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "gdpr-api"
        assert "timestamp" in data

    def test_get_consent_without_auth_fails(self, client):
        """Test that getting consent without auth returns 401."""
        response = client.get("/api/gdpr/consent")
        
        assert response.status_code == 422  # Missing required header

    def test_update_consent_without_auth_fails(self, client):
        """Test that updating consent without auth returns 422."""
        response = client.post(
            "/api/gdpr/consent",
            json={
                "consent_type": "terms_of_service",
                "granted": True,
                "version": "1.0"
            }
        )
        
        assert response.status_code == 422  # Missing required header

    def test_delete_account_without_confirmation_fails(self, client):
        """Test that deletion without 'DELETE' confirmation fails."""
        response = client.request(
            "DELETE",
            "/api/gdpr/delete-account",
            headers={"authorization": "Bearer test_token"},
            json={"confirmation": "maybe" }
        )
        
        # Should fail because confirmation is not "DELETE"
        assert response.status_code == 400


# ============================================
# Edge Cases
# ============================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_consent_type_string_values(self):
        """Test consent type string values match expected."""
        assert ConsentType.TERMS_OF_SERVICE.value != ConsentType.PRIVACY_POLICY.value
        assert ConsentType.MARKETING.value != ConsentType.DATA_PROCESSING.value

    def test_deletion_status_grace_period_default(self):
        """Test deletion status has correct default grace period."""
        scheduled = datetime.now() + timedelta(days=30)
        status = DeletionStatus(
            status="scheduled",
            message="Test",
            scheduled_deletion_at=scheduled
        )
        
        assert status.grace_period_days == 30  # Default value

    @pytest.mark.asyncio
    async def test_schedule_deletion_date_calculation(self, mock_user_id):
        """Test that scheduled deletion is approximately 30 days from now."""
        with patch('neshama.web.api.gdpr.schedule_data_deletion') as mock:
            mock.return_value = datetime.now() + timedelta(days=30)
            result = await schedule_data_deletion(mock_user_id)
            
            delta = result - datetime.now()
            assert 29 <= delta.days <= 31


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
