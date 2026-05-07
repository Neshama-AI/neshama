# Web API - License Endpoints
"""
License API router for SDK license key validation and management.

Public Endpoints:
- POST /api/license/validate   — Validate a license key
- POST /api/license/activate   — Activate (bind) a license to a machine
- POST /api/license/deactivate — Deactivate (unbind) a machine
- GET  /api/license/status     — Query license status
- GET  /api/license/pricing    — Get pricing for a region

Admin Endpoints:
- POST /api/admin/license/generate — Generate a new license key
- GET  /api/admin/license/list     — List all licenses
- POST /api/admin/license/revoke   — Revoke a license

Region Isolation:
  The Host header of each request is used to determine the request region.
  - api.neshama.cn  → cn (China)
  - api.neshama.pw  → global
  License keys with mismatched regions are rejected.
"""

import logging
import os
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel, Field

from neshama.billing.license import (
    validate_license,
    activate_license,
    deactivate_license,
    get_license_status,
    generate_license,
    revoke_license,
    parse_license_key,
    detect_region_from_host,
    check_region_match,
    get_license_store,
    LicenseStore,
    LicenseCache,
    LicenseValidationResult,
    PLAN_CODES,
    PLAN_FEATURES,
    PLAN_NPC_LIMITS,
    MACHINE_LIMITS,
    GRACE_PERIOD_DAYS,
    REGION_CODES,
    REGION_DISPLAY_NAMES,
    REGION_PRICING,
    get_region_pricing,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Admin secret (load from env)
ADMIN_SECRET = os.environ.get("NESHAMA_ADMIN_SECRET", "neshama-admin-secret-change-in-prod")


# ── Helper ────────────────────────────────────────────────────────────────────

def _detect_request_region(request: Request) -> str:
    """Detect the region from the request Host header."""
    host = request.headers.get("host", "")
    return detect_region_from_host(host)


def _verify_admin(request: Request) -> bool:
    """Verify admin access via header."""
    admin_secret = os.environ.get("NESHAMA_ADMIN_SECRET", ADMIN_SECRET)
    auth = request.headers.get("X-Admin-Secret", "")
    return auth == admin_secret


# ── Request/Response Models ───────────────────────────────────────────────────

class ValidateRequest(BaseModel):
    """License validation request."""
    license_key: str = Field(..., min_length=1)
    machine_id: str = Field(..., min_length=8, max_length=128)


class ValidateResponse(BaseModel):
    """License validation response."""
    valid: bool
    plan: str
    max_npcs: int
    features: List[str]
    expires_at: str
    region: str = "global"
    region_match: bool = True
    grace_until: Optional[str] = None
    last_validated_at: Optional[str] = None
    error: Optional[str] = None


class ActivateRequest(BaseModel):
    """License activation request."""
    license_key: str = Field(..., min_length=1)
    machine_id: str = Field(..., min_length=8, max_length=128)


class ActivateResponse(BaseModel):
    """License activation response."""
    success: bool
    message: str
    region: Optional[str] = None


class DeactivateRequest(BaseModel):
    """License deactivation request."""
    license_key: str = Field(..., min_length=1)
    machine_id: str = Field(..., min_length=8, max_length=128)


class DeactivateResponse(BaseModel):
    """License deactivation response."""
    success: bool
    message: str


class StatusResponse(BaseModel):
    """License status response."""
    license_key: str
    plan: str
    region: str
    status: str
    created_at: str
    expires_at: str
    machine_count: int
    machine_limit: int
    machines: List[Dict[str, str]]
    last_validated_at: Optional[str]
    features: List[str]
    max_npcs: int
    pricing: Dict[str, Any]


class PricingItem(BaseModel):
    """Pricing for a single plan."""
    plan: str
    monthly_cents: int
    currency: str
    symbol: str


class PricingResponse(BaseModel):
    """Pricing response for a region."""
    region: str
    plans: List[PricingItem]


# Admin models
class GenerateRequest(BaseModel):
    """Admin: Generate license request."""
    plan: str = Field(..., pattern=r"^(free|indie|studio|enterprise)$")
    region: str = Field(..., pattern=r"^(cn|global)$")
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GenerateResponse(BaseModel):
    """Admin: Generate license response."""
    license_key: str
    plan: str
    region: str
    status: str
    created_at: str
    expires_at: str


class LicenseListItem(BaseModel):
    """Admin: License list item."""
    license_key: str
    plan: str
    region: str
    status: str
    created_at: str
    expires_at: str
    machine_count: int
    last_validated_at: Optional[str]


class LicenseListResponse(BaseModel):
    """Admin: License list response."""
    licenses: List[LicenseListItem]
    total: int


class RevokeRequest(BaseModel):
    """Admin: Revoke license request."""
    license_key: str = Field(..., min_length=1)


class RevokeResponse(BaseModel):
    """Admin: Revoke license response."""
    success: bool
    message: str


# ── Public Endpoints ──────────────────────────────────────────────────────────

@router.post("/validate", response_model=ValidateResponse)
async def validate(req: ValidateRequest, request: Request) -> Dict[str, Any]:
    """
    Validate a license key and return entitlement information.

    The SDK calls this on startup and periodically to confirm the license
    is active and to refresh the grace period timer.

    Region isolation: the request's Host header determines the expected region.
    If the license key's region doesn't match, validation fails with region_match=false.
    """
    request_region = _detect_request_region(request)
    result = validate_license(req.license_key, req.machine_id, request_region=request_region)

    response = result.to_dict()

    # Attach region error message if present
    if not result.valid and hasattr(result, '_region_error'):
        response["error"] = result._region_error
    elif not result.valid:
        response["error"] = "License validation failed"

    return response


@router.post("/activate", response_model=ActivateResponse)
async def activate(req: ActivateRequest, request: Request) -> Dict[str, Any]:
    """
    Activate a license by binding it to a machine fingerprint.

    First activation binds the machine; subsequent validations must
    come from a bound machine. Machine limits apply per plan.

    Region isolation: the license's region must match the request region.
    """
    request_region = _detect_request_region(request)
    success, message = activate_license(
        req.license_key, req.machine_id, request_region=request_region
    )

    response = {"success": success, "message": message}

    # Include region info in response
    parsed = parse_license_key(req.license_key)
    if parsed:
        response["region"] = parsed["region"]

    return response


@router.post("/deactivate", response_model=DeactivateResponse)
async def deactivate(req: DeactivateRequest) -> Dict[str, Any]:
    """
    Deactivate a license by unbinding a machine.

    This frees up a machine slot for the license.
    """
    success, message = deactivate_license(req.license_key, req.machine_id)
    return {"success": success, "message": message}


@router.get("/status", response_model=StatusResponse)
async def status(license_key: str) -> Dict[str, Any]:
    """
    Query the full status of a license.

    Returns plan, region, expiry, bound machines, features, pricing, etc.
    """
    result = get_license_status(license_key)
    if result is None:
        raise HTTPException(status_code=404, detail="License not found")
    return result


@router.get("/pricing", response_model=PricingResponse)
async def pricing(region: str = "global") -> Dict[str, Any]:
    """
    Get pricing information for a specific region.

    Returns prices in the local currency for the given region.
    """
    if region not in REGION_PRICING:
        raise HTTPException(status_code=400, detail=f"Invalid region: {region}. Use 'cn' or 'global'")

    region_info = REGION_PRICING[region]
    plans = []
    for plan_name in ["free", "indie", "studio", "enterprise"]:
        plans.append(PricingItem(
            plan=plan_name,
            monthly_cents=region_info.get(plan_name, 0),
            currency=region_info["currency"],
            symbol=region_info["symbol"],
        ))

    return {
        "region": region,
        "plans": [p.dict() for p in plans],
    }


# ── Admin Endpoints ───────────────────────────────────────────────────────────

@router.post("/admin/generate", response_model=GenerateResponse)
async def admin_generate(req: GenerateRequest, request: Request) -> Dict[str, Any]:
    """
    Generate a new license key (admin only).

    Both plan and region are required. Region is immutable once set.
    """
    if not _verify_admin(request):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        license_key, record = generate_license(
            plan=req.plan,
            region=req.region,
            expires_at=req.expires_at,
            metadata=req.metadata,
        )
        return {
            "license_key": license_key,
            "plan": record.plan,
            "region": record.region,
            "status": record.status,
            "created_at": record.created_at,
            "expires_at": record.expires_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/list", response_model=LicenseListResponse)
async def admin_list(
    request: Request,
    plan: Optional[str] = None,
    region: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List all licenses (admin only).

    Optional filters: plan, region, status.
    """
    if not _verify_admin(request):
        raise HTTPException(status_code=403, detail="Admin access required")

    store = get_license_store()
    records = store.list_all(plan=plan, status=status_filter, region=region)

    items = [
        LicenseListItem(
            license_key=r.license_key,
            plan=r.plan,
            region=r.region,
            status=r.status,
            created_at=r.created_at,
            expires_at=r.expires_at,
            machine_count=len(r.machines),
            last_validated_at=r.last_validated_at,
        )
        for r in records
    ]

    return {
        "licenses": [item.dict() for item in items],
        "total": len(items),
    }


@router.post("/admin/revoke", response_model=RevokeResponse)
async def admin_revoke(req: RevokeRequest, request: Request) -> Dict[str, Any]:
    """
    Revoke a license (admin only).

    Revoked licenses cannot be validated or activated.
    """
    if not _verify_admin(request):
        raise HTTPException(status_code=403, detail="Admin access required")

    success, message = revoke_license(req.license_key)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": success, "message": message}
