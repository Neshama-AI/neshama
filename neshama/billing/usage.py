# Billing - Usage Tracking
"""
Usage tracking for Neshama subscription resources.

Tracks per-session/monthly usage of:
- NPC count
- Emotion calculations
- TTS character usage
- API calls
- Hosted conversations (LLM calls under our provider)

Also provides BYOK detection logic:
- is_byok(session_id): Check if user has configured their own API Key
- check_conversation_quota: BYOK users bypass conversation quota checks

Data is stored in JSON files under billing_data/, organized by month.
User API Keys (for BYOK) are stored encrypted in billing_data/user_keys/.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import threading
import logging
import os
import base64

logger = logging.getLogger(__name__)

# Default billing data directory
DEFAULT_BILLING_DIR = Path(__file__).parent.parent.parent / "billing_data"

# Default user keys directory (encrypted)
DEFAULT_KEYS_DIR = DEFAULT_BILLING_DIR / "user_keys"


class ResourceType(str, Enum):
    """Types of tracked resources."""
    NPC_COUNT = "npc_count"
    EMOTION_CALC = "emotion_calc"
    TTS_CHAR = "tts_char"
    API_CALL = "api_call"
    HOSTED_CONVERSATION = "hosted_conversation"


@dataclass
class UsageRecord:
    """Single usage record."""
    timestamp: str
    resource_type: ResourceType
    amount: int
    session_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonthlyUsage:
    """Monthly usage summary for a session."""
    session_id: str
    year_month: str  # Format: "2024-01"
    npc_count: int = 0
    emotion_calc_count: int = 0
    tts_char_count: int = 0
    api_call_count: int = 0
    hosted_conversation_count: int = 0  # Conversations using our LLM
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    records: List[UsageRecord] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "year_month": self.year_month,
            "npc_count": self.npc_count,
            "emotion_calc_count": self.emotion_calc_count,
            "tts_char_count": self.tts_char_count,
            "api_call_count": self.api_call_count,
            "hosted_conversation_count": self.hosted_conversation_count,
            "last_updated": self.last_updated,
        }
    
    def get_total_api_calls(self) -> int:
        """Get total API calls (emotion calcs + TTS + direct API + hosted conversations)."""
        return self.emotion_calc_count + self.tts_char_count // 100 + self.api_call_count + self.hosted_conversation_count


# ── API Key Encryption ────────────────────────────────────────────────────────

class KeyEncryption:
    """
    Simple Fernet-compatible encryption for user API Keys.
    Uses the cryptography library's Fernet if available,
    falls back to a simple XOR-based scheme for development.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize encryption with a secret key.
        
        Args:
            secret_key: Encryption key. Falls back to NESHAMA_KEY_ENCRYPTION_SECRET
                       env var, then to a dev default.
        """
        self._secret = secret_key or os.environ.get(
            "NESHAMA_KEY_ENCRYPTION_SECRET", ""
        )
        self._fernet = None
        
        if self._secret:
            try:
                from cryptography.fernet import Fernet
                import hashlib
                # Derive a valid Fernet key from the secret
                key = base64.urlsafe_b64encode(
                    hashlib.sha256(self._secret.encode()).digest()
                )
                self._fernet = Fernet(key)
            except ImportError:
                logger.warning(
                    "cryptography library not installed. "
                    "API Key encryption will use simple XOR fallback. "
                    "Install with: pip install cryptography"
                )
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        if self._fernet:
            return self._fernet.encrypt(plaintext.encode()).decode()
        
        # Fallback: simple XOR + base64 (NOT secure, development only)
        key_bytes = self._secret.encode() if self._secret else b"neshama_dev_key"
        data = plaintext.encode()
        xored = bytes(
            data[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(data))
        )
        return base64.urlsafe_b64encode(xored).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64-encoded ciphertext and return plaintext."""
        if self._fernet:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        
        # Fallback: simple XOR + base64
        key_bytes = self._secret.encode() if self._secret else b"neshama_dev_key"
        data = base64.urlsafe_b64decode(ciphertext.encode())
        xored = bytes(
            data[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(data))
        )
        return xored.decode()


# ── User Key Manager ──────────────────────────────────────────────────────────

@dataclass
class UserKeyInfo:
    """Information about a user's stored API Key."""
    provider: str          # e.g., "openai", "deepseek", "minimax", "anthropic"
    key_last4: str         # Last 4 chars of the key for display
    created_at: str
    verified: bool = True  # Whether the key passed verification


class UserKeyManager:
    """
    Manages user-provided API Keys for BYOK mode.
    
    Keys are stored encrypted in billing_data/user_keys/{session_id}.json
    """
    
    def __init__(
        self,
        keys_dir: Optional[Path] = None,
        encryption: Optional[KeyEncryption] = None,
    ):
        self._keys_dir = keys_dir or DEFAULT_KEYS_DIR
        self._keys_dir.mkdir(parents=True, exist_ok=True)
        self._encryption = encryption or KeyEncryption()
        self._lock = threading.RLock()
        self._cache: Dict[str, Dict[str, Any]] = {}  # session_id -> key data
    
    def _get_file_path(self, session_id: str) -> Path:
        """Get file path for user's key data."""
        return self._keys_dir / f"{session_id}.json"
    
    def set_key(
        self,
        session_id: str,
        provider: str,
        api_key: str,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> UserKeyInfo:
        """
        Store a user's API Key (encrypted).
        
        Args:
            session_id: Session identifier
            provider: Provider name (openai, deepseek, minimax, anthropic)
            api_key: The API Key to store
            model_name: Optional default model name
            base_url: Optional custom base URL
            
        Returns:
            UserKeyInfo with last4 for display
        """
        with self._lock:
            encrypted_key = self._encryption.encrypt(api_key)
            key_last4 = api_key[-4:] if len(api_key) >= 4 else api_key
            
            key_data = {
                "provider": provider,
                "encrypted_key": encrypted_key,
                "key_last4": key_last4,
                "model_name": model_name or "",
                "base_url": base_url or "",
                "created_at": datetime.now().isoformat(),
                "verified": True,
            }
            
            # Save to file
            file_path = self._get_file_path(session_id)
            # Load existing keys to preserve multiple provider entries
            existing = {}
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        existing = json.load(f)
                except (json.JSONDecodeError, IOError):
                    existing = {}
            
            # Store under "providers" dict keyed by provider name
            if "providers" not in existing:
                existing["providers"] = {}
            existing["providers"][provider] = key_data
            existing["active_provider"] = provider
            existing["updated_at"] = datetime.now().isoformat()
            
            with open(file_path, "w") as f:
                json.dump(existing, f, indent=2)
            
            # Update cache
            self._cache[session_id] = existing
            
            logger.info(
                f"Stored BYOK key for session={session_id}, "
                f"provider={provider}, last4=****{key_last4}"
            )
            
            return UserKeyInfo(
                provider=provider,
                key_last4=key_last4,
                created_at=key_data["created_at"],
                verified=True,
            )
    
    def get_key(self, session_id: str, provider: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get decrypted key info for a session.
        
        Args:
            session_id: Session identifier
            provider: Optional specific provider. If None, uses active provider.
            
        Returns:
            Dict with provider, api_key (decrypted), model_name, base_url, etc.
            None if no key configured.
        """
        with self._lock:
            data = self._load_key_data(session_id)
            if not data or "providers" not in data:
                return None
            
            provider_name = provider or data.get("active_provider")
            if not provider_name or provider_name not in data["providers"]:
                return None
            
            key_entry = data["providers"][provider_name]
            
            try:
                decrypted_key = self._encryption.decrypt(key_entry["encrypted_key"])
            except Exception as e:
                logger.error(f"Failed to decrypt key for session={session_id}: {e}")
                return None
            
            return {
                "provider": provider_name,
                "api_key": decrypted_key,
                "model_name": key_entry.get("model_name", ""),
                "base_url": key_entry.get("base_url", ""),
                "key_last4": key_entry.get("key_last4", ""),
                "created_at": key_entry.get("created_at", ""),
                "verified": key_entry.get("verified", False),
            }
    
    def delete_key(self, session_id: str, provider: Optional[str] = None) -> bool:
        """
        Delete a stored API Key.
        
        Args:
            session_id: Session identifier
            provider: Specific provider to delete. If None, deletes all keys
                      and reverts to hosted mode.
            
        Returns:
            True if key was deleted
        """
        with self._lock:
            data = self._load_key_data(session_id)
            if not data or "providers" not in data:
                return False
            
            if provider:
                if provider not in data["providers"]:
                    return False
                del data["providers"][provider]
                
                # If we deleted the active provider, switch to another or clear
                if data.get("active_provider") == provider:
                    remaining = list(data["providers"].keys())
                    data["active_provider"] = remaining[0] if remaining else None
            else:
                # Delete all keys - revert to hosted mode
                data["providers"] = {}
                data["active_provider"] = None
            
            data["updated_at"] = datetime.now().isoformat()
            
            file_path = self._get_file_path(session_id)
            if not data["providers"]:
                # No more keys, remove the file
                if file_path.exists():
                    file_path.unlink()
                if session_id in self._cache:
                    del self._cache[session_id]
            else:
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)
                self._cache[session_id] = data
            
            logger.info(f"Deleted BYOK key for session={session_id}, provider={provider or 'all'}")
            return True
    
    def get_all_keys_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get info about all stored keys (without decrypting).
        
        Returns:
            Dict with active_provider and list of provider key infos (last4 only)
        """
        with self._lock:
            data = self._load_key_data(session_id)
            if not data or "providers" not in data:
                return {
                    "active_provider": None,
                    "providers": [],
                    "mode": "hosted",
                }
            
            providers = []
            for name, entry in data["providers"].items():
                providers.append({
                    "provider": name,
                    "key_last4": entry.get("key_last4", ""),
                    "model_name": entry.get("model_name", ""),
                    "created_at": entry.get("created_at", ""),
                    "verified": entry.get("verified", False),
                })
            
            active = data.get("active_provider")
            
            return {
                "active_provider": active,
                "providers": providers,
                "mode": "byok" if active else "hosted",
            }
    
    def is_byok(self, session_id: str) -> bool:
        """
        Check if a session has BYOK mode active (user has configured their own API Key).
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if user has an active BYOK key configured
        """
        info = self.get_all_keys_info(session_id)
        return info["mode"] == "byok" and info["active_provider"] is not None
    
    def get_active_provider(self, session_id: str) -> Optional[str]:
        """Get the active provider name for a session (BYOK mode)."""
        info = self.get_all_keys_info(session_id)
        return info.get("active_provider")
    
    def _load_key_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load key data from disk or cache."""
        if session_id in self._cache:
            return self._cache[session_id]
        
        file_path = self._get_file_path(session_id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            self._cache[session_id] = data
            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading key data for session={session_id}: {e}")
            return None


# ── Usage Tracker ──────────────────────────────────────────────────────────────

class UsageTracker:
    """
    Tracks resource usage per session.
    
    Stores data in JSON files organized by month.
    Thread-safe for concurrent access.
    
    Example:
        >>> tracker = UsageTracker()
        >>> 
        >>> # Track emotion calculation
        >>> tracker.track_usage("session_123", ResourceType.EMOTION_CALC, 1)
        >>> 
        >>> # Track hosted conversation
        >>> tracker.track_usage("session_123", ResourceType.HOSTED_CONVERSATION, 1)
        >>> 
        >>> # Check if limit reached
        >>> if tracker.check_limit_reached("session_123", ResourceType.EMOTION_CALC):
        ...     print("Limit reached!")
        >>> 
        >>> # Get current monthly usage
        >>> usage = tracker.get_monthly_usage("session_123")
        >>> print(f"Hosted conversations: {usage.hosted_conversation_count}")
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize UsageTracker.
        
        Args:
            data_dir: Directory for usage data files. Defaults to billing_data/
        """
        self._data_dir = data_dir or DEFAULT_BILLING_DIR
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._memory_cache: Dict[str, MonthlyUsage] = {}
    
    def _get_current_month(self) -> str:
        """Get current year-month string."""
        return datetime.now().strftime("%Y-%m")
    
    def _get_file_path(self, session_id: str, year_month: Optional[str] = None) -> Path:
        """Get file path for session's monthly data."""
        if year_month is None:
            year_month = self._get_current_month()
        return self._data_dir / f"{session_id}_{year_month}.json"
    
    def _load_monthly_usage(
        self,
        session_id: str,
        year_month: Optional[str] = None,
    ) -> MonthlyUsage:
        """Load monthly usage from disk or create new."""
        if year_month is None:
            year_month = self._get_current_month()
        
        cache_key = f"{session_id}_{year_month}"
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]
        
        file_path = self._get_file_path(session_id, year_month)
        
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    records = [
                        UsageRecord(
                            timestamp=r["timestamp"],
                            resource_type=ResourceType(r["resource_type"]),
                            amount=r["amount"],
                            session_id=r["session_id"],
                            metadata=r.get("metadata", {}),
                        )
                        for r in data.get("records", [])
                    ]
                    usage = MonthlyUsage(
                        session_id=data["session_id"],
                        year_month=data["year_month"],
                        npc_count=data.get("npc_count", 0),
                        emotion_calc_count=data.get("emotion_calc_count", 0),
                        tts_char_count=data.get("tts_char_count", 0),
                        api_call_count=data.get("api_call_count", 0),
                        hosted_conversation_count=data.get("hosted_conversation_count", 0),
                        last_updated=data.get("last_updated", datetime.now().isoformat()),
                        records=records,
                    )
                    self._memory_cache[cache_key] = usage
                    return usage
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Error loading usage file {file_path}: {e}")
        
        # Create new usage record
        return MonthlyUsage(
            session_id=session_id,
            year_month=year_month,
        )
    
    def _save_monthly_usage(self, usage: MonthlyUsage) -> None:
        """Save monthly usage to disk."""
        file_path = self._get_file_path(usage.session_id, usage.year_month)
        
        # Update cache
        cache_key = f"{usage.session_id}_{usage.year_month}"
        self._memory_cache[cache_key] = usage
        
        # Save to file
        with open(file_path, "w") as f:
            json.dump({
                "session_id": usage.session_id,
                "year_month": usage.year_month,
                "npc_count": usage.npc_count,
                "emotion_calc_count": usage.emotion_calc_count,
                "tts_char_count": usage.tts_char_count,
                "api_call_count": usage.api_call_count,
                "hosted_conversation_count": usage.hosted_conversation_count,
                "last_updated": usage.last_updated,
                "records": [
                    {
                        "timestamp": r.timestamp,
                        "resource_type": r.resource_type.value,
                        "amount": r.amount,
                        "session_id": r.session_id,
                        "metadata": r.metadata,
                    }
                    for r in usage.records
                ],
            }, f, indent=2)
    
    def track_usage(
        self,
        session_id: str,
        resource_type: ResourceType,
        amount: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track resource usage.
        
        Args:
            session_id: Session identifier
            resource_type: Type of resource used
            amount: Amount consumed (usually 1)
            metadata: Optional additional data
        """
        with self._lock:
            usage = self._load_monthly_usage(session_id)
            
            # Create record
            record = UsageRecord(
                timestamp=datetime.now().isoformat(),
                resource_type=resource_type,
                amount=amount,
                session_id=session_id,
                metadata=metadata or {},
            )
            usage.records.append(record)
            
            # Update counts
            usage.last_updated = datetime.now().isoformat()
            
            if resource_type == ResourceType.NPC_COUNT:
                usage.npc_count += amount
            elif resource_type == ResourceType.EMOTION_CALC:
                usage.emotion_calc_count += amount
            elif resource_type == ResourceType.TTS_CHAR:
                usage.tts_char_count += amount
            elif resource_type == ResourceType.API_CALL:
                usage.api_call_count += amount
            elif resource_type == ResourceType.HOSTED_CONVERSATION:
                usage.hosted_conversation_count += amount
            
            self._save_monthly_usage(usage)
            resource_type_value = resource_type.value if hasattr(resource_type, 'value') else str(resource_type)
            logger.debug(
                f"Tracked usage: session={session_id}, "
                f"type={resource_type_value}, amount={amount}"
            )
    
    def get_monthly_usage(
        self,
        session_id: str,
        year_month: Optional[str] = None,
    ) -> MonthlyUsage:
        """
        Get monthly usage for a session.
        
        Args:
            session_id: Session identifier
            year_month: Optional specific month (defaults to current)
            
        Returns:
            MonthlyUsage object
        """
        with self._lock:
            return self._load_monthly_usage(session_id, year_month)
    
    def check_limit_reached(
        self,
        session_id: str,
        resource_type: ResourceType,
        limit: int,
    ) -> bool:
        """
        Check if resource usage has reached a limit.
        
        Args:
            session_id: Session identifier
            resource_type: Type of resource
            limit: Maximum allowed (-1 for unlimited)
            
        Returns:
            True if limit reached/exceeded, False if within limit
        """
        if limit == -1:  # Unlimited
            return False
        
        with self._lock:
            usage = self.get_monthly_usage(session_id)
            
            if resource_type == ResourceType.NPC_COUNT:
                current = usage.npc_count
            elif resource_type == ResourceType.EMOTION_CALC:
                current = usage.emotion_calc_count
            elif resource_type == ResourceType.TTS_CHAR:
                current = usage.tts_char_count
            elif resource_type == ResourceType.API_CALL:
                current = usage.api_call_count
            elif resource_type == ResourceType.HOSTED_CONVERSATION:
                current = usage.hosted_conversation_count
            else:
                return False
            
            return current >= limit
    
    def check_conversation_quota(
        self,
        session_id: str,
        tier_name: str,
        is_byok: bool = False,
    ) -> Dict[str, Any]:
        """
        Check if the user can make another conversation.
        
        BYOK users always pass this check.
        Hosted users are checked against their tier's conversation limit.
        
        Args:
            session_id: Session identifier
            tier_name: Subscription tier name
            is_byok: Whether the user has BYOK mode active
            
        Returns:
            Dict with:
            - allowed: bool - Whether the conversation is allowed
            - mode: str - "byok" or "hosted"
            - remaining: Optional[int] - Remaining hosted conversations (None if unlimited)
            - limit: int - The hosted conversation limit (-1 for unlimited)
            - error: Optional[str] - Error message if not allowed
            - suggestions: List[str] - Suggestions if quota exceeded
        """
        from neshama.billing.plans import get_hosted_conversations_limit
        
        # BYOK users bypass all conversation quotas
        if is_byok:
            return {
                "allowed": True,
                "mode": "byok",
                "remaining": None,
                "limit": -1,
                "error": None,
                "suggestions": [],
            }
        
        limit = get_hosted_conversations_limit(tier_name)
        
        # Unlimited hosted conversations
        if limit == -1:
            return {
                "allowed": True,
                "mode": "hosted",
                "remaining": None,
                "limit": -1,
                "error": None,
                "suggestions": [],
            }
        
        # Check current usage
        with self._lock:
            usage = self.get_monthly_usage(session_id)
            current = usage.hosted_conversation_count
        
        remaining = max(0, limit - current)
        allowed = current < limit
        
        result: Dict[str, Any] = {
            "allowed": allowed,
            "mode": "hosted",
            "remaining": remaining,
            "limit": limit,
            "error": None,
            "suggestions": [],
        }
        
        if not allowed:
            result["error"] = "quota_exceeded"
            result["suggestions"] = [
                "switch_to_byok",  # Switch to BYOK mode (bring your own API Key)
                "upgrade_tier",    # Upgrade subscription tier
            ]
        
        return result
    
    def reset_monthly(self, session_id: str) -> None:
        """
        Reset monthly usage for a session.
        
        Called when moving to a new month.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            # Clear current month
            year_month = self._get_current_month()
            cache_key = f"{session_id}_{year_month}"
            
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
            
            # Archive current file
            file_path = self._get_file_path(session_id, year_month)
            if file_path.exists():
                archive_path = file_path.with_suffix(".archived.json")
                file_path.rename(archive_path)
            
            logger.info(f"Reset monthly usage for session {session_id}")
    
    def get_usage_summary(
        self,
        session_id: str,
        tier_npc_limit: int,
        tier_emotion_limit: int,
        tier_tts_limit: int,
        tier_api_limit: int,
        tier_hosted_conversations_limit: int = -1,
    ) -> Dict[str, Any]:
        """
        Get complete usage summary with limits.
        
        Args:
            session_id: Session identifier
            tier_npc_limit: NPC limit from subscription tier (-1 for unlimited)
            tier_emotion_limit: Emotion calc limit (-1 for unlimited)
            tier_tts_limit: TTS char limit (-1 for unlimited)
            tier_api_limit: API call limit (-1 for unlimited)
            tier_hosted_conversations_limit: Hosted conversation limit (-1 for unlimited)
            
        Returns:
            Dict with usage and remaining amounts
        """
        usage = self.get_monthly_usage(session_id)
        
        def remaining(current: int, limit: int) -> Optional[int]:
            if limit == -1:
                return None  # Unlimited
            return max(0, limit - current)
        
        return {
            "session_id": session_id,
            "year_month": usage.year_month,
            "usage": {
                "npc_count": usage.npc_count,
                "emotion_calc_count": usage.emotion_calc_count,
                "tts_char_count": usage.tts_char_count,
                "api_call_count": usage.api_call_count,
                "hosted_conversation_count": usage.hosted_conversation_count,
            },
            "limits": {
                "npc_limit": tier_npc_limit,
                "emotion_calc_limit": tier_emotion_limit,
                "tts_char_limit": tier_tts_limit,
                "api_call_limit": tier_api_limit,
                "hosted_conversations_limit": tier_hosted_conversations_limit,
            },
            "remaining": {
                "npc_remaining": remaining(usage.npc_count, tier_npc_limit),
                "emotion_calc_remaining": remaining(usage.emotion_calc_count, tier_emotion_limit),
                "tts_char_remaining": remaining(usage.tts_char_count, tier_tts_limit),
                "api_call_remaining": remaining(usage.api_call_count, tier_api_limit),
                "hosted_conversations_remaining": remaining(usage.hosted_conversation_count, tier_hosted_conversations_limit),
            },
            "last_updated": usage.last_updated,
        }
    
    def cleanup_old_data(self, months_to_keep: int = 3) -> int:
        """
        Clean up archived usage data older than specified months.
        
        Args:
            months_to_keep: Number of months to retain
            
        Returns:
            Number of files deleted
        """
        with self._lock:
            cutoff = datetime.now() - timedelta(days=30 * months_to_keep)
            deleted = 0
            
            for file_path in self._data_dir.glob("*.archived.json"):
                try:
                    stat = file_path.stat()
                    if datetime.fromtimestamp(stat.st_mtime) < cutoff:
                        file_path.unlink()
                        deleted += 1
                except OSError as e:
                    logger.warning(f"Error cleaning up {file_path}: {e}")
            
            return deleted


# ── Global instances ───────────────────────────────────────────────────────────

_tracker: Optional[UsageTracker] = None
_key_manager: Optional[UserKeyManager] = None


def get_usage_tracker() -> UsageTracker:
    """Get the global UsageTracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker


def get_key_manager() -> UserKeyManager:
    """Get the global UserKeyManager instance."""
    global _key_manager
    if _key_manager is None:
        _key_manager = UserKeyManager()
    return _key_manager


def track_usage(
    session_id: str,
    resource_type: ResourceType,
    amount: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Convenience function to track usage."""
    get_usage_tracker().track_usage(session_id, resource_type, amount, metadata)


def get_monthly_usage(
    session_id: str,
    year_month: Optional[str] = None,
) -> MonthlyUsage:
    """Convenience function to get monthly usage."""
    return get_usage_tracker().get_monthly_usage(session_id, year_month)


def check_limit_reached(
    session_id: str,
    resource_type: ResourceType,
    limit: int,
) -> bool:
    """Convenience function to check limit."""
    return get_usage_tracker().check_limit_reached(session_id, resource_type, limit)


def is_byok(session_id: str) -> bool:
    """
    Check if a session has BYOK mode active.
    
    Convenience function that delegates to UserKeyManager.
    """
    return get_key_manager().is_byok(session_id)


def check_conversation_quota(
    session_id: str,
    tier_name: str,
    is_byok_mode: bool = False,
) -> Dict[str, Any]:
    """
    Check conversation quota for a session.
    
    Convenience function that delegates to UsageTracker.
    """
    return get_usage_tracker().check_conversation_quota(
        session_id, tier_name, is_byok_mode
    )
