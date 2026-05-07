#!/bin/bash
# ============================================================
# Neshama Cloud API - One-Click Installer for Hostinger
# Run this from the Hostinger web terminal (hPanel > Terminal)
# ============================================================

set -e

INSTALL_DIR="$HOME/neshama-cloud"
mkdir -p "$INSTALL_DIR/data"

echo "=== Neshama Cloud API Installer ==="
echo "Install dir: $INSTALL_DIR"

# ---- Step 1: Create cloud_server.py ----
echo "[1/5] Creating server files..."
cat > "$INSTALL_DIR/cloud_server.py" << 'SERVEREOF'
#!/usr/bin/env python3
"""
Neshama Cloud API Server - Simplified for shared hosting deployment.

This is a lightweight standalone server that provides the core Neshama API:
- Health check
- Auth (register, login, trial)
- Chat (with real LLM via MiniMax)
- Soul creation and management

No Django, no Redis, no heavy dependencies. Just FastAPI + uvicorn.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Configuration ─────────────────────────────────────────────────────────────

JWT_SECRET = os.environ.get("NESHAMA_JWT_SECRET", "neshama-dev-jwt-secret-change-in-prod")
HOSTED_LLM_PROVIDER = os.environ.get("NESHAMA_HOSTED_LLM_PROVIDER", "minimax")
HOSTED_LLM_MODEL = os.environ.get("NESHAMA_HOSTED_LLM_MODEL", "MiniMax-M2.5")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")
FREE_CONVERSATIONS = int(os.environ.get("NESHAMA_FREE_CONVERSATIONS", "1000"))
TRIAL_CONVERSATIONS = int(os.environ.get("NESHAMA_TRIAL_CONVERSATIONS", "50"))
TRIAL_EXPIRY_HOURS = int(os.environ.get("NESHAMA_TRIAL_EXPIRY_HOURS", "24"))
SERVER_HOST = os.environ.get("NESHAMA_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("NESHAMA_PORT", "8420"))
DATA_DIR = Path(os.environ.get("NESHAMA_DATA_DIR", Path(__file__).parent / "data"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("neshama-cloud")

# ── Data Storage (JSON file-based) ────────────────────────────────────────────

DATA_DIR.mkdir(parents=True, exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
TRIALS_FILE = DATA_DIR / "trials.json"
SOULS_FILE = DATA_DIR / "souls.json"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"


def _load_json(filepath: Path) -> dict:
    """Load JSON data from file."""
    if filepath.exists():
        try:
            return json.loads(filepath.read_text())
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_json(filepath: Path, data: dict):
    """Save JSON data to file."""
    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── Auth Helpers ──────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${hashed}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split("$", 1)
        return hmac.compare_digest(
            hashlib.sha256(f"{salt}{password}".encode()).hexdigest(),
            hashed
        )
    except (ValueError, AttributeError):
        return False


def _generate_api_key() -> str:
    return f"nsk_{secrets.token_hex(24)}"


def _generate_jwt(user_id: str, tier: str = "free", expiry_hours: int = 720) -> str:
    import base64
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
    payload = base64.urlsafe_b64encode(json.dumps({
        "sub": user_id,
        "tier": tier,
        "iat": int(time.time()),
        "exp": int(time.time()) + expiry_hours * 3600,
    }).encode()).decode()
    sig = hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{payload}.{sig}"


def _verify_jwt(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        expected_sig = hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload_data = json.loads(__import__("base64").urlsafe_b64decode(payload + "=="))
        if payload_data.get("exp", 0) < time.time():
            return None
        return payload_data
    except Exception:
        return None


def _get_current_user(request: Request) -> Optional[dict]:
    """Extract and verify user from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = _verify_jwt(token)
        if payload:
            users = _load_json(USERS_FILE)
            user_id = payload.get("sub")
            if user_id in users:
                return users[user_id]
    # Also check API key
    api_key = request.headers.get("X-API-Key", "")
    if api_key.startswith("nsk_"):
        users = _load_json(USERS_FILE)
        for uid, user in users.items():
            if user.get("api_key") == api_key:
                return user
    return None


# ── LLM Client (MiniMax/OpenAI-compatible) ────────────────────────────────────

async def _call_llm(messages: List[dict], max_tokens: int = 1024) -> str:
    """Call the hosted LLM provider (MiniMax via OpenAI-compatible API)."""
    import aiohttp
    
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": HOSTED_LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.8,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await resp.text()
                    logger.error(f"LLM API error {resp.status}: {error_text}")
                    return f"[LLM Error: {resp.status}]"
    except asyncio.TimeoutError:
        logger.error("LLM API timeout")
        return "[LLM timeout - please try again]"
    except Exception as e:
        logger.error(f"LLM API exception: {e}")
        return f"[LLM Error: {str(e)}]"


def _build_soul_system_prompt(soul_config: dict) -> str:
    """Build system prompt from soul personality configuration."""
    name = soul_config.get("name", "Neshama")
    personality = soul_config.get("personality", {})
    
    ocean = personality.get("ocean", {})
    openness = ocean.get("openness", 0.7)
    conscientiousness = ocean.get("conscientiousness", 0.6)
    extraversion = ocean.get("extraversion", 0.5)
    agreeableness = ocean.get("agreeableness", 0.7)
    neuroticism = ocean.get("neuroticism", 0.3)
    
    traits = []
    if openness > 0.6:
        traits.append("curious and creative")
    if conscientiousness > 0.6:
        traits.append("organized and diligent")
    if extraversion > 0.6:
        traits.append("outgoing and energetic")
    elif extraversion < 0.4:
        traits.append("introspective and thoughtful")
    if agreeableness > 0.6:
        traits.append("warm and cooperative")
    if neuroticism > 0.6:
        traits.append("sensitive and emotionally responsive")
    elif neuroticism < 0.4:
        traits.append("calm and emotionally stable")
    
    traits_str = ", ".join(traits) if traits else "balanced and adaptable"
    background = personality.get("background", "an AI soul")
    language = personality.get("language", "en")
    
    lang_instruction = ""
    if language == "zh":
        lang_instruction = "请用中文回复。"
    elif language == "en":
        lang_instruction = "Respond in English."
    
    return (
        f"You are {name}, {background}. "
        f"Your personality traits: {traits_str}. "
        f"OCEAN profile: Openness={openness}, Conscientiousness={conscientiousness}, "
        f"Extraversion={extraversion}, Agreeableness={agreeableness}, Neuroticism={neuroticism}. "
        f"Stay in character at all times. Be authentic and engaging. "
        f"{lang_instruction}"
    )


# ── Pydantic Models ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatMessage(BaseModel):
    content: str
    soul_id: Optional[str] = None
    stream: bool = False

class CreateSoulRequest(BaseModel):
    name: str
    personality: Optional[dict] = None
    background: Optional[str] = None
    language: Optional[str] = "en"


# ── FastAPI App ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Neshama Cloud API starting on {SERVER_HOST}:{SERVER_PORT}")
    logger.info(f"Hosted LLM: {HOSTED_LLM_PROVIDER}/{HOSTED_LLM_MODEL}")
    logger.info(f"Data dir: {DATA_DIR}")
    yield
    logger.info("Neshama Cloud API shutting down")


app = FastAPI(
    title="Neshama Soul OS - Cloud API",
    description="AI Agent Personality Operating System - Give agents a soul",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Endpoints ─────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/health/detailed")
async def health_detailed():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "llm_provider": HOSTED_LLM_PROVIDER,
        "llm_model": HOSTED_LLM_MODEL,
        "data_dir": str(DATA_DIR),
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "name": "Neshama Soul OS",
        "version": "1.0.0",
        "description": "AI Agent Personality Operating System",
        "docs": "/docs",
        "health": "/health",
    }


# ── Auth Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    """Register a new account with free tier."""
    users = _load_json(USERS_FILE)
    
    # Check if email already exists
    for uid, user in users.items():
        if user.get("email") == req.email:
            raise HTTPException(status_code=409, detail="Email already registered")
    
    user_id = f"usr_{secrets.token_hex(12)}"
    api_key = _generate_api_key()
    
    users[user_id] = {
        "id": user_id,
        "email": req.email,
        "name": req.name or req.email.split("@")[0],
        "password_hash": _hash_password(req.password),
        "api_key": api_key,
        "tier": "free",
        "conversations_remaining": FREE_CONVERSATIONS,
        "conversations_used": 0,
        "created_at": datetime.now().isoformat(),
    }
    
    _save_json(USERS_FILE, users)
    
    token = _generate_jwt(user_id, "free")
    
    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "email": req.email,
            "name": users[user_id]["name"],
            "api_key": api_key,
            "tier": "free",
            "conversations_remaining": FREE_CONVERSATIONS,
            "token": token,
        }
    }


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """Login with email and password."""
    users = _load_json(USERS_FILE)
    
    for uid, user in users.items():
        if user.get("email") == req.email:
            if _verify_password(req.password, user.get("password_hash", "")):
                token = _generate_jwt(uid, user.get("tier", "free"))
                return {
                    "success": True,
                    "data": {
                        "user_id": uid,
                        "email": user["email"],
                        "name": user.get("name", ""),
                        "api_key": user.get("api_key", ""),
                        "tier": user.get("tier", "free"),
                        "conversations_remaining": user.get("conversations_remaining", 0),
                        "token": token,
                    }
                }
    
    raise HTTPException(status_code=401, detail="Invalid email or password")


@app.post("/api/auth/trial")
async def trial():
    """Create an anonymous trial session."""
    trial_id = f"trial_{secrets.token_hex(12)}"
    token = _generate_jwt(trial_id, "trial", TRIAL_EXPIRY_HOURS)
    
    trials = _load_json(TRIALS_FILE)
    trials[trial_id] = {
        "id": trial_id,
        "tier": "trial",
        "conversations_remaining": TRIAL_CONVERSATIONS,
        "conversations_used": 0,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=TRIAL_EXPIRY_HOURS)).isoformat(),
    }
    _save_json(TRIALS_FILE, trials)
    
    return {
        "success": True,
        "data": {
            "trial_id": trial_id,
            "token": token,
            "tier": "trial",
            "conversations_remaining": TRIAL_CONVERSATIONS,
            "expires_in_hours": TRIAL_EXPIRY_HOURS,
        }
    }


@app.get("/api/auth/me")
async def me(request: Request):
    """Get current user info."""
    user = _get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "success": True,
        "data": {
            "user_id": user.get("id", ""),
            "email": user.get("email", "trial"),
            "name": user.get("name", "Trial User"),
            "tier": user.get("tier", "trial"),
            "conversations_remaining": user.get("conversations_remaining", 0),
        }
    }


@app.post("/api/auth/api-key")
async def regenerate_api_key(request: Request):
    """Regenerate API key."""
    user = _get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    new_key = _generate_api_key()
    users = _load_json(USERS_FILE)
    user_id = user.get("id", "")
    if user_id in users:
        users[user_id]["api_key"] = new_key
        _save_json(USERS_FILE, users)
        return {"success": True, "data": {"api_key": new_key}}
    
    raise HTTPException(status_code=404, detail="User not found")


# ── Soul Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/soul/create")
async def create_soul(req: CreateSoulRequest, request: Request):
    """Create a new soul."""
    user = _get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    soul_id = f"soul_{secrets.token_hex(8)}"
    
    personality = req.personality or {
        "ocean": {
            "openness": 0.7,
            "conscientiousness": 0.6,
            "extraversion": 0.5,
            "agreeableness": 0.7,
            "neuroticism": 0.3,
        },
        "background": req.background or "an AI soul with unique personality",
        "language": req.language or "en",
    }
    
    souls = _load_json(SOULS_FILE)
    souls[soul_id] = {
        "id": soul_id,
        "name": req.name,
        "owner_id": user.get("id", ""),
        "personality": personality,
        "created_at": datetime.now().isoformat(),
        "conversation_count": 0,
    }
    _save_json(SOULS_FILE, souls)
    
    return {
        "success": True,
        "data": {
            "soul_id": soul_id,
            "name": req.name,
            "personality": personality,
        }
    }


@app.get("/api/soul/list")
async def list_souls(request: Request):
    """List user's souls."""
    user = _get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    souls = _load_json(SOULS_FILE)
    user_souls = [
        s for s in souls.values()
        if s.get("owner_id") == user.get("id", "")
    ]
    
    return {"success": True, "data": {"souls": user_souls}}


@app.get("/api/soul/{soul_id}")
async def get_soul(soul_id: str, request: Request):
    """Get soul details."""
    user = _get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    souls = _load_json(SOULS_FILE)
    soul = souls.get(soul_id)
    if not soul:
        raise HTTPException(status_code=404, detail="Soul not found")
    
    return {"success": True, "data": soul}


# ── Chat Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatMessage, request: Request):
    """Send a chat message and get AI response."""
    user = _get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check conversation quota
    remaining = user.get("conversations_remaining", 0)
    if remaining <= 0:
        raise HTTPException(
            status_code=429,
            detail="No conversations remaining. Upgrade your plan or bring your own API key."
        )
    
    # Get soul config if specified
    system_prompt = "You are Neshama, an AI soul with a warm, curious, and insightful personality. Engage authentically and helpfully."
    
    if req.soul_id:
        souls = _load_json(SOULS_FILE)
        soul = souls.get(req.soul_id)
        if soul:
            system_prompt = _build_soul_system_prompt(soul)
    
    # Build messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": req.content},
    ]
    
    # Call LLM
    response_content = await _call_llm(messages)
    
    # Decrement conversation count
    user_id = user.get("id", "")
    if "email" in user:  # registered user
        users = _load_json(USERS_FILE)
        if user_id in users:
            users[user_id]["conversations_remaining"] = max(0, remaining - 1)
            users[user_id]["conversations_used"] = users[user_id].get("conversations_used", 0) + 1
            _save_json(USERS_FILE, users)
    else:  # trial user
        trials = _load_json(TRIALS_FILE)
        if user_id in trials:
            trials[user_id]["conversations_remaining"] = max(0, remaining - 1)
            trials[user_id]["conversations_used"] = trials[user_id].get("conversations_used", 0) + 1
            _save_json(TRIALS_FILE, trials)
    
    return {
        "success": True,
        "data": {
            "role": "assistant",
            "content": response_content,
            "soul_id": req.soul_id,
            "conversations_remaining": max(0, remaining - 1),
        }
    }


# WebSocket chat
class WSConnectionManager:
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}
    
    async def connect(self, ws: WebSocket, session_id: str):
        await ws.accept()
        self.active[session_id] = ws
    
    def disconnect(self, session_id: str):
        self.active.pop(session_id, None)


ws_manager = WSConnectionManager()


@app.websocket("/api/chat/ws")
async def websocket_chat(websocket: WebSocket, token: str = ""):
    """WebSocket chat endpoint."""
    # Verify token
    payload = _verify_jwt(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get("sub", "")
    session_id = f"ws_{secrets.token_hex(6)}"
    
    await ws_manager.connect(websocket, session_id)
    
    try:
        await websocket.send_json({
            "type": "system",
            "content": "Connected to Neshama Soul Panel",
            "timestamp": datetime.now().isoformat(),
        })
        
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})
                continue
            
            if msg.get("type") == "message":
                content = msg.get("content", "")
                soul_id = msg.get("soul_id")
                
                # Build system prompt
                system_prompt = "You are Neshama, an AI soul with a warm, curious, and insightful personality."
                if soul_id:
                    souls = _load_json(SOULS_FILE)
                    soul = souls.get(soul_id)
                    if soul:
                        system_prompt = _build_soul_system_prompt(soul)
                
                await websocket.send_json({"type": "typing", "content": "..."})
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ]
                response = await _call_llm(messages)
                
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                })
    
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(session_id)


# ── Config Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/config/models")
async def list_models():
    """List available models."""
    return {
        "success": True,
        "data": {
            "hosted": {
                "provider": HOSTED_LLM_PROVIDER,
                "model": HOSTED_LLM_MODEL,
            },
            "supported_providers": [
                "openai", "anthropic", "gemini", "deepseek",
                "minimax", "dashscope", "zhipu", "moonshot",
                "openrouter", "groq", "mistral",
            ],
        }
    }


@app.get("/api/config/plans")
async def list_plans():
    """List subscription plans."""
    return {
        "success": True,
        "data": {
            "free": {
                "conversations": FREE_CONVERSATIONS,
                "price": "$0",
                "features": ["Basic soul creation", "Text chat", f"{FREE_CONVERSATIONS} conversations"],
            },
            "trial": {
                "conversations": TRIAL_CONVERSATIONS,
                "price": "$0",
                "duration_hours": TRIAL_EXPIRY_HOURS,
                "features": ["Quick trial", "Text chat", f"{TRIAL_CONVERSATIONS} conversations"],
            },
        }
    }


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Handle signals for graceful shutdown
    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    logger.info(f"Starting Neshama Cloud API on {SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
        access_log=True,
    )

SERVEREOF

# ---- Step 2: Create requirements.txt ----
cat > "$INSTALL_DIR/requirements.txt" << 'REQEOF'
# Neshama Cloud API - Minimal Dependencies
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
aiohttp>=3.8.0
websockets>=11.0

REQEOF

# ---- Step 3: Create .env ----
cat > "$INSTALL_DIR/.env" << 'ENVEOF'
# Neshama Cloud API Environment Configuration
# Copy this to .env and fill in your values

# Server
NESHAMA_HOST=0.0.0.0
NESHAMA_PORT=8420

# JWT Secret - MUST change in production!
NESHAMA_JWT_SECRET=6ff919e95832ccbad826060a15686b4bacf988e7cf71c6605f6d07ed4a7c2d61

# Hosted LLM Configuration
NESHAMA_HOSTED_LLM_PROVIDER=minimax
NESHAMA_HOSTED_LLM_MODEL=MiniMax-M2.5

# MiniMax API Key
MINIMAX_API_KEY=sk-cp-PvA2lKW_1UG0hBXsgZclgetIp-j2aqX4PjBG9Sb5wEsljQLxFzmlVACIf-F7fYrVMC0MHX5oqdYgSae4MN_ZdFiTjMNjgOcLw8Neb03BB98jjITdFXL5heQ
MINIMAX_BASE_URL=https://api.minimaxi.com/v1

# Quotas
NESHAMA_FREE_CONVERSATIONS=1000
NESHAMA_TRIAL_CONVERSATIONS=50
NESHAMA_TRIAL_EXPIRY_HOURS=24

ENVEOF

# ---- Step 4: Create manage.sh ----
cat > "$INSTALL_DIR/manage.sh" << 'MANAGEEOF'
#!/bin/bash
# Start/stop script for Neshama Cloud API
# Usage: ./manage.sh [start|stop|restart|status|logs]

INSTALL_DIR="$HOME/neshama-cloud"
PID_FILE="$INSTALL_DIR/server.pid"
LOG_FILE="$INSTALL_DIR/server.log"
PORT=${NESHAMA_PORT:-8420}

# Load env
if [ -f "$INSTALL_DIR/.env" ]; then
    set -a
    source "$INSTALL_DIR/.env"
    set +a
    PORT=${NESHAMA_PORT:-8420}
fi

get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

case "${1:-status}" in
    start)
        if is_running; then
            echo "Server already running (PID: $(get_pid))"
        else
            echo "Starting Neshama Cloud API..."
            cd "$INSTALL_DIR"
            if [ -f "$INSTALL_DIR/venv/bin/python3" ]; then
                PYTHON="$INSTALL_DIR/venv/bin/python3"
            else
                PYTHON="python3"
            fi
            nohup $PYTHON "$INSTALL_DIR/cloud_server.py" >> "$LOG_FILE" 2>&1 &
            echo $! > "$PID_FILE"
            echo "Started with PID: $(get_pid)"
            sleep 3
            if is_running; then
                echo "✓ Server is running"
            else
                echo "✗ Server failed to start. Check logs:"
                tail -20 "$LOG_FILE"
            fi
        fi
        ;;
    stop)
        if is_running; then
            echo "Stopping server (PID: $(get_pid))..."
            kill $(get_pid)
            sleep 2
            if is_running; then
                kill -9 $(get_pid)
            fi
            rm -f "$PID_FILE"
            echo "Stopped"
        else
            echo "Server not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if is_running; then
            echo "✓ Server running (PID: $(get_pid))"
            HEALTH=$(curl -s http://localhost:$PORT/health 2>/dev/null || echo "unreachable")
            echo "  Health: $HEALTH"
        else
            echo "✗ Server not running"
        fi
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        ;;
esac

MANAGEEOF
chmod +x "$INSTALL_DIR/manage.sh"

# ---- Step 5: Setup Python environment and install deps ----
echo "[2/5] Setting up Python environment..."

# Try virtual environment first
python3 -m venv "$INSTALL_DIR/venv" 2>/dev/null && {
    echo "Virtual environment created."
    PIP_CMD="$INSTALL_DIR/venv/bin/pip3"
    PYTHON_CMD="$INSTALL_DIR/venv/bin/python3"
} || {
    echo "venv failed, using --user install..."
    PIP_CMD="python3 -m pip --user"
    PYTHON_CMD="python3"
}

echo "[3/5] Installing dependencies (this may take a minute)..."
$PIP_CMD install --no-cache-dir -r "$INSTALL_DIR/requirements.txt" 2>&1 | tail -5

echo "[4/5] Loading environment..."
set -a
source "$INSTALL_DIR/.env"
set +a

echo "[5/5] Starting server..."
# Stop existing server
if [ -f "$INSTALL_DIR/server.pid" ]; then
    OLD_PID=$(cat "$INSTALL_DIR/server.pid")
    kill "$OLD_PID" 2>/dev/null || true
    sleep 2
    rm -f "$INSTALL_DIR/server.pid"
fi

cd "$INSTALL_DIR"
nohup $PYTHON_CMD "$INSTALL_DIR/cloud_server.py" >> "$INSTALL_DIR/server.log" 2>&1 &
echo $! > "$INSTALL_DIR/server.pid"
echo "Server started with PID: $(cat $INSTALL_DIR/server.pid)"

# Wait and verify
sleep 5
if kill -0 $(cat "$INSTALL_DIR/server.pid") 2>/dev/null; then
    echo ""
    echo "✓ Neshama Cloud API is running!"
    echo "  Health:  curl http://localhost:${NESHAMA_PORT:-8420}/health"
    echo "  Docs:    http://localhost:${NESHAMA_PORT:-8420}/docs"
    echo "  Logs:    tail -f $INSTALL_DIR/server.log"
    echo "  Stop:    kill $(cat $INSTALL_DIR/server.pid)"
    echo "  Restart: bash $INSTALL_DIR/manage.sh restart"
else
    echo "✗ Server failed to start! Check logs:"
    tail -20 "$INSTALL_DIR/server.log"
fi
