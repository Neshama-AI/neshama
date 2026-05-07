"""
GDPR API Endpoints

Provides GDPR-compliant data export, deletion, and consent management endpoints.
These endpoints allow users to exercise their rights under GDPR and CCPA.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Header, Body
from pydantic import BaseModel, EmailStr
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gdpr", tags=["GDPR"])


# ============================================
# Pydantic Models
# ============================================

class ConsentType(str, Enum):
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    MARKETING = "marketing"
    DATA_PROCESSING = "data_processing"


class ConsentStatus(BaseModel):
    consent_type: ConsentType
    granted: bool
    timestamp: datetime
    version: str


class UserConsent(BaseModel):
    user_id: str
    consents: list[ConsentStatus]
    last_updated: datetime


class DataExportResponse(BaseModel):
    status: str
    message: str
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class DeletionStatus(BaseModel):
    status: str
    message: str
    scheduled_deletion_at: datetime
    grace_period_days: int = 30


class ConsentUpdateRequest(BaseModel):
    consent_type: ConsentType
    granted: bool
    version: str


class GDPRExportRequest(BaseModel):
    include_npcs: bool = True
    include_chat_history: bool = True
    include_memories: bool = True
    include_emotions: bool = True


# ============================================
# Mock Database Functions (Replace with actual DB)
# ============================================

async def get_user_id_from_token(authorization: str) -> Optional[str]:
    """
    Extract user ID from authorization token.
    In production, this would validate JWT and return user ID.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    # Mock: In production, decode JWT and extract user_id
    # For now, return a mock user ID
    return "mock_user_id_123"


async def get_user_data(user_id: str) -> dict:
    """
    Fetch all user data from the database.
    Replace with actual database queries.
    """
    # Mock implementation - replace with actual DB calls
    return {
        "user_id": user_id,
        "account": {
            "email": "user@example.com",
            "created_at": datetime.now().isoformat(),
            "subscription_status": "active"
        },
        "npcs": [
            {
                "id": "npc_001",
                "name": "Tavern Keeper",
                "personality_config": {
                    "ocean": {"openness": 0.7, "conscientiousness": 0.8}
                },
                "created_at": datetime.now().isoformat()
            }
        ],
        "chat_history": [
            {"npc_id": "npc_001", "messages": [], "exported_at": datetime.now().isoformat()}
        ],
        "memories": [
            {"npc_id": "npc_001", "layer": "L0", "entries": [], "exported_at": datetime.now().isoformat()}
        ],
        "emotions": [
            {"npc_id": "npc_001", "states": [], "exported_at": datetime.now().isoformat()}
        ],
        "exported_at": datetime.now().isoformat()
    }


async def schedule_data_deletion(user_id: str) -> datetime:
    """
    Schedule user data for deletion after 30-day grace period.
    Returns the scheduled deletion date.
    """
    scheduled_date = datetime.now() + timedelta(days=30)
    # In production: Update database record, mark for deletion
    logger.info(f"Scheduled deletion for user {user_id} at {scheduled_date}")
    return scheduled_date


async def cancel_data_deletion(user_id: str) -> bool:
    """
    Cancel scheduled data deletion if within grace period.
    Returns True if cancellation was successful.
    """
    # In production: Remove deletion flag, restore access
    logger.info(f"Cancelled deletion for user {user_id}")
    return True


async def get_user_consents(user_id: str) -> UserConsent:
    """
    Get all consent records for a user.
    """
    now = datetime.now()
    return UserConsent(
        user_id=user_id,
        consents=[
            ConsentStatus(
                consent_type=ConsentType.TERMS_OF_SERVICE,
                granted=True,
                timestamp=now - timedelta(days=30),
                version="1.0"
            ),
            ConsentStatus(
                consent_type=ConsentType.PRIVACY_POLICY,
                granted=True,
                timestamp=now - timedelta(days=30),
                version="1.0"
            ),
            ConsentStatus(
                consent_type=ConsentType.DATA_PROCESSING,
                granted=True,
                timestamp=now - timedelta(days=30),
                version="1.0"
            ),
            ConsentStatus(
                consent_type=ConsentType.MARKETING,
                granted=False,
                timestamp=now - timedelta(days=30),
                version="1.0"
            )
        ],
        last_updated=now
    )


async def update_user_consent(user_id: str, consent_type: ConsentType, granted: bool, version: str) -> ConsentStatus:
    """
    Update a specific consent for a user.
    """
    return ConsentStatus(
        consent_type=consent_type,
        granted=granted,
        timestamp=datetime.now(),
        version=version
    )


# ============================================
# API Endpoints
# ============================================

@router.get("/consent", response_model=UserConsent)
async def get_consent_status(
    authorization: str = Header(..., description="Bearer token"),
) -> UserConsent:
    """
    Get current user's consent status for all consent types.
    
    Returns all consent records including:
    - Terms of Service agreement
    - Privacy Policy agreement
    - Marketing communications opt-in
    - Data processing consent
    """
    user_id = await get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing authorization token")
    
    try:
        return await get_user_consents(user_id)
    except Exception as e:
        logger.error(f"Error fetching consent status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch consent status")


@router.post("/consent", response_model=ConsentStatus)
async def update_consent(
    request: ConsentUpdateRequest,
    authorization: str = Header(..., description="Bearer token"),
) -> ConsentStatus:
    """
    Update user's consent for a specific type.
    
    Users can update their consent preferences at any time.
    Note: Some consents may be required for service provision.
    """
    user_id = await get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing authorization token")
    
    try:
        return await update_user_consent(
            user_id, 
            request.consent_type, 
            request.granted, 
            request.version
        )
    except Exception as e:
        logger.error(f"Error updating consent: {e}")
        raise HTTPException(status_code=500, detail="Failed to update consent")


@router.post("/export", response_model=DataExportResponse)
async def export_user_data(
    request: GDPRExportRequest = None,
    authorization: str = Header(..., description="Bearer token"),
) -> DataExportResponse:
    """
    Export all user data in a portable format.
    
    GDPR Article 20 - Right to Data Portability
    
    Includes:
    - NPC personality configurations
    - Chat history
    - Memory data
    - Emotion states
    
    The export will be available as a downloadable JSON file.
    """
    user_id = await get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing authorization token")
    
    if request is None:
        request = GDPRExportRequest()
    
    try:
        # Fetch user data
        user_data = await get_user_data(user_id)
        
        # Filter data based on request
        export_data = {
            "user_id": user_data["user_id"],
            "account": user_data["account"],
            "exported_at": datetime.now().isoformat(),
            "data_included": {
                "npcs": request.include_npcs,
                "chat_history": request.include_chat_history,
                "memories": request.include_memories,
                "emotions": request.include_emotions
            }
        }
        
        if request.include_npcs:
            export_data["npcs"] = user_data.get("npcs", [])
        
        if request.include_chat_history:
            export_data["chat_history"] = user_data.get("chat_history", [])
        
        if request.include_memories:
            export_data["memories"] = user_data.get("memories", [])
        
        if request.include_emotions:
            export_data["emotions"] = user_data.get("emotions", [])
        
        # In production: Save to secure storage, generate download URL
        # For now, return mock response
        expires_at = datetime.now() + timedelta(hours=24)
        
        logger.info(f"Data export generated for user {user_id}")
        
        return DataExportResponse(
            status="success",
            message="Your data export is being prepared. You will receive a download link shortly.",
            download_url=f"/api/gdpr/download/{user_id}",  # Mock URL
            expires_at=expires_at
        )
        
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate data export")


@router.delete("/delete-account", response_model=DeletionStatus)
async def delete_account(
    confirmation: str = Body(..., embed=True, description="Type 'DELETE' to confirm"),
    authorization: str = Header(..., description="Bearer token"),
) -> DeletionStatus:
    """
    Request deletion of user account and all associated data.
    
    GDPR Article 17 - Right to Erasure ("Right to be Forgotten")
    
    IMPORTANT:
    - After deletion, data will be retained for 30 days (grace period)
    - During grace period, account can be restored
    - After 30 days, all data will be permanently deleted
    
    WARNING: This action cannot be easily undone!
    """
    user_id = await get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing authorization token")
    
    if confirmation.upper() != "DELETE":
        raise HTTPException(
            status_code=400, 
            detail="Please type 'DELETE' in the confirmation field to confirm account deletion"
        )
    
    try:
        scheduled_deletion = await schedule_data_deletion(user_id)
        
        logger.info(f"Account deletion requested for user {user_id}, scheduled for {scheduled_deletion}")
        
        return DeletionStatus(
            status="scheduled",
            message=(
                "Your account has been scheduled for deletion. "
                "You have 30 days to cancel this request if you change your mind. "
                "Contact support@neshama.ai to restore your account."
            ),
            scheduled_deletion_at=scheduled_deletion,
            grace_period_days=30
        )
        
    except Exception as e:
        logger.error(f"Error scheduling account deletion: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule account deletion")


@router.post("/cancel-deletion", response_model=dict)
async def cancel_deletion(
    authorization: str = Header(..., description="Bearer token"),
) -> dict:
    """
    Cancel scheduled account deletion during grace period.
    
    Restores user access and removes the scheduled deletion.
    """
    user_id = await get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing authorization token")
    
    try:
        success = await cancel_data_deletion(user_id)
        
        if success:
            return {
                "status": "restored",
                "message": "Your account deletion has been cancelled. Your account is now active."
            }
        else:
            raise HTTPException(status_code=404, detail="No pending deletion found for this account")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling deletion: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel deletion")


# ============================================
# Health Check Endpoint
# ============================================

@router.get("/health")
async def gdpr_health_check():
    """
    Health check endpoint for GDPR service.
    """
    return {
        "status": "healthy",
        "service": "gdpr-api",
        "timestamp": datetime.now().isoformat()
    }
