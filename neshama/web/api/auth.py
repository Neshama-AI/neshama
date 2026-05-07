"""
Neshama Auth API

Registration, login, and trial mode endpoints.
Uses simple JWT tokens for authentication — no heavy dependencies.

Endpoints:
- POST /api/auth/register  — Create account (get API key + 1000 free conversations)
- POST /api/auth/login     — Login (get JWT token)
- POST /api/auth/trial     — Anonymous trial (50 free conversations, 24h expiry)
- GET  /api/auth/me        — Get current user info
- POST /api/auth/api-key   — Regenerate API key
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Configuration ─────────────────────────────────────────────────────────────

JWT_SECRET = os.environ.get("NESHAMA_JWT_SECRET", "neshama-dev-jwt-secret-change-in-prod")
FREE_CONVERSATIONS = int(os.environ.get("NESHAMA_FREE_CONVERSATIONS", "1000"))
TRIAL_CONVERSATIONS = int(os.environ.get("NESHAMA_TRIAL_CONVERSATIONS", "50"))
TRIAL_EXPIRY_HOURS = int(os.environ.get("NESHAMA_TRIAL_EXPIRY_HOURS", "24"))

# Storage paths
DATA_DIR = Path(os.environ.get("NESHAMA_DATA_DIR", Path(__file__).parent.parent.parent.parent / "data"))
USERS_FILE = DATA_DIR / "users.json"
TRIALS_FILE = DATA_DIR / "trials.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt. Simple — production should use bcrypt."""
    salt = secrets.token_hex(8)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${hashed}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, hashed = stored.split("$", 1)
        return hmac.compare_digest(
            hashlib.sha256(f"{salt}{password}".encode()).hexdigest(),
            hashed
        )
    except (ValueError, AttributeError):
        return False


def _generate_api_key() -> str:
    """Generate a Neshama API key (nsk_xxx format)."""
    return f"nsk_{secrets.token_hex(24)}"


def _generate_jwt(user_id: str, tier: str = "free", expiry_hours: int = 720) -> str:
    """
    Generate a simple JWT-like token.
    Format: base64(header).base64(payload).base64(signature)
    No external JWT library needed.
    """
    import base64

    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
    
    payload_data = {
        "sub": user_id,
        "tier": tier,
        "iat": int(time.time()),
        "exp": int(time.time()) + expiry_hours * 3600,
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode()
    
    signature = hmac.new(
        JWT_SECRET.encode(),
        f"{header}.{payload}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{header}.{payload}.{signature}"


def _verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token. Returns payload or None."""
    try:
        import base64
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature = parts
        
        # Verify signature
        expected_sig = hmac.new(
            JWT_SECRET.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # Decode payload
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
        
        # Check expiry
        if payload.get("exp", 0) < time.time():
            return None
        
        return payload
    except Exception:
        return None


def _load_json(filepath: Path) -> Dict:
    """Load JSON file safely."""
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_json(filepath: Path, data: Dict) -> None:
    """Save JSON file safely."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _get_auth_user(request: Request) -> Optional[Dict[str, Any]]:
    """Extract authenticated user from request Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        # Try JWT first
        payload = _verify_jwt(token)
        if payload:
            users = _load_json(USERS_FILE)
            user_id = payload.get("sub")
            if user_id in users:
                return users[user_id]
        # Try API key
        users = _load_json(USERS_FILE)
        for uid, user in users.items():
            if user.get("api_key") == token:
                return user
    return None


# ── Request/Response Models ───────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ApiKeyResponse(BaseModel):
    api_key: str

class AuthResponse(BaseModel):
    user_id: str
    api_key: str
    tier: str
    token: Optional[str] = None

class TrialResponse(BaseModel):
    trial_token: str
    remaining_conversations: int
    expires_in: str

class UserInfoResponse(BaseModel):
    user_id: str
    email: str
    name: str
    tier: str
    api_key_last4: str
    conversations_used: int
    conversations_limit: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, summary="Register new account")
async def register(req: RegisterRequest):
    """
    Register a new Neshama account.
    
    - Creates user with Free tier subscription
    - Automatically assigns 1000 free hosted conversations per month
    - Returns API key for SDK configuration
    """
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    if len(req.name) < 1 or len(req.name) > 50:
        raise HTTPException(status_code=400, detail="Name must be 1-50 characters")
    
    users = _load_json(USERS_FILE)
    
    # Check if email already exists
    for uid, user in users.items():
        if user.get("email") == req.email:
            raise HTTPException(status_code=409, detail="Email already registered")
    
    # Create user
    user_id = f"usr_{secrets.token_hex(12)}"
    api_key = _generate_api_key()
    
    users[user_id] = {
        "user_id": user_id,
        "email": req.email,
        "name": req.name,
        "password_hash": _hash_password(req.password),
        "api_key": api_key,
        "tier": "free",
        "conversations_used": 0,
        "conversations_limit": FREE_CONVERSATIONS,
        "created_at": datetime.now().isoformat(),
        "is_trial": False,
    }
    
    _save_json(USERS_FILE, users)
    
    # Generate JWT token
    token = _generate_jwt(user_id, "free")
    
    logger.info(f"New user registered: {user_id} ({req.email})")
    
    return AuthResponse(
        user_id=user_id,
        api_key=api_key,
        tier="free",
        token=token,
    )


@router.post("/login", response_model=AuthResponse, summary="Login")
async def login(req: LoginRequest):
    """
    Login with email and password.
    
    Returns JWT token and API key.
    """
    users = _load_json(USERS_FILE)
    
    for uid, user in users.items():
        if user.get("email") == req.email:
            if not _verify_password(req.password, user.get("password_hash", "")):
                raise HTTPException(status_code=401, detail="Invalid password")
            
            token = _generate_jwt(uid, user.get("tier", "free"))
            
            return AuthResponse(
                user_id=uid,
                api_key=user["api_key"],
                tier=user.get("tier", "free"),
                token=token,
            )
    
    raise HTTPException(status_code=404, detail="User not found")


@router.post("/trial", response_model=TrialResponse, summary="Start anonymous trial")
async def start_trial():
    """
    Start an anonymous trial — no registration, no email required.
    
    - Automatically creates a temporary account
    - Assigns 50 free conversations
    - Trial token expires in 24 hours
    - After using all conversations, prompts to register for more
    """
    trials = _load_json(TRIALS_FILE)
    
    # Create trial account
    trial_id = f"trial_{secrets.token_hex(12)}"
    trial_token = _generate_api_key()  # Use same format for simplicity
    
    trials[trial_id] = {
        "trial_id": trial_id,
        "trial_token": trial_token,
        "conversations_used": 0,
        "conversations_limit": TRIAL_CONVERSATIONS,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=TRIAL_EXPIRY_HOURS)).isoformat(),
    }
    
    _save_json(TRIALS_FILE, trials)
    
    logger.info(f"New trial started: {trial_id}")
    
    return TrialResponse(
        trial_token=trial_token,
        remaining_conversations=TRIAL_CONVERSATIONS,
        expires_in=f"{TRIAL_EXPIRY_HOURS}h",
    )


@router.get("/me", response_model=UserInfoResponse, summary="Get current user info")
async def get_me(request: Request):
    """Get current authenticated user information."""
    user = _get_auth_user(request)
    
    if not user:
        # Check trial tokens
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            trials = _load_json(TRIALS_FILE)
            for tid, trial in trials.items():
                if trial.get("trial_token") == token:
                    # Check expiry
                    expires_at = datetime.fromisoformat(trial["expires_at"])
                    if datetime.now() > expires_at:
                        raise HTTPException(status_code=401, detail="Trial expired")
                    
                    remaining = trial["conversations_limit"] - trial["conversations_used"]
                    return UserInfoResponse(
                        user_id=tid,
                        email="trial@neshama.ai",
                        name="Trial User",
                        tier="trial",
                        api_key_last4=token[-4:],
                        conversations_used=trial["conversations_used"],
                        conversations_limit=trial["conversations_limit"],
                    )
        
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    api_key = user.get("api_key", "")
    remaining = user.get("conversations_limit", FREE_CONVERSATIONS) - user.get("conversations_used", 0)
    
    return UserInfoResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        tier=user.get("tier", "free"),
        api_key_last4=api_key[-4:] if len(api_key) >= 4 else api_key,
        conversations_used=user.get("conversations_used", 0),
        conversations_limit=user.get("conversations_limit", FREE_CONVERSATIONS),
    )


@router.post("/api-key", response_model=ApiKeyResponse, summary="Regenerate API key")
async def regenerate_api_key(request: Request):
    """Regenerate the API key for the current user."""
    user = _get_auth_user(request)
    
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    users = _load_json(USERS_FILE)
    user_id = user["user_id"]
    
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_key = _generate_api_key()
    users[user_id]["api_key"] = new_key
    _save_json(USERS_FILE, users)
    
    logger.info(f"API key regenerated for user: {user_id}")
    
    return ApiKeyResponse(api_key=new_key)


# ── Trial Validation Helper ───────────────────────────────────────────────────

def validate_trial_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a trial token and return trial data.
    Used by the billing middleware to check trial quotas.
    """
    trials = _load_json(TRIALS_FILE)
    
    for tid, trial in trials.items():
        if trial.get("trial_token") == token:
            # Check expiry
            try:
                expires_at = datetime.fromisoformat(trial["expires_at"])
                if datetime.now() > expires_at:
                    return None
            except (ValueError, KeyError):
                return None
            
            # Check quota
            if trial["conversations_used"] >= trial["conversations_limit"]:
                return None
            
            return trial
    
    return None


def increment_trial_usage(token: str) -> bool:
    """Increment trial conversation count. Returns True if successful."""
    trials = _load_json(TRIALS_FILE)
    
    for tid, trial in trials.items():
        if trial.get("trial_token") == token:
            if trial["conversations_used"] >= trial["conversations_limit"]:
                return False
            
            trials[tid]["conversations_used"] += 1
            _save_json(TRIALS_FILE, trials)
            return True
    
    return False
