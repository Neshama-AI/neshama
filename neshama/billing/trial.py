# Billing - Trial Management
"""
Trial mode management for Neshama.

Provides anonymous trial tokens with limited conversation quotas.
Trial tokens expire after 24 hours and can be upgraded to full accounts.

Trial data is stored in data/trials.json (simple file-based storage).
For production, consider migrating to Redis or a database.
"""

import json
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import RLock

logger = logging.getLogger(__name__)

# Default data directory
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRIALS_FILE = DEFAULT_DATA_DIR / "trials.json"

# Default limits
DEFAULT_TRIAL_CONVERSATIONS = 50
DEFAULT_TRIAL_EXPIRY_HOURS = 24


class TrialManager:
    """
    Manages trial accounts and their conversation quotas.
    
    Features:
    - Create trial accounts with temporary tokens
    - Track trial conversation usage
    - Check trial expiry
    - Convert trial to full account (preserving conversation history)
    - Clean up expired trials
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        trial_conversations: int = DEFAULT_TRIAL_CONVERSATIONS,
        trial_expiry_hours: int = DEFAULT_TRIAL_EXPIRY_HOURS,
    ):
        self._data_dir = data_dir or DEFAULT_DATA_DIR
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._trials_file = self._data_dir / "trials.json"
        self._trial_conversations = trial_conversations
        self._trial_expiry_hours = trial_expiry_hours
        self._lock = RLock()
        self._cache: Dict[str, Dict] = {}
    
    def _load_trials(self) -> Dict[str, Dict]:
        """Load trials from file."""
        with self._lock:
            if self._cache:
                return self._cache
            
            if not self._trials_file.exists():
                return {}
            
            try:
                with open(self._trials_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                    return self._cache
            except (json.JSONDecodeError, IOError):
                return {}
    
    def _save_trials(self, trials: Dict[str, Dict]) -> None:
        """Save trials to file."""
        with self._lock:
            self._cache = trials
            with open(self._trials_file, "w", encoding="utf-8") as f:
                json.dump(trials, f, indent=2, ensure_ascii=False)
    
    def create_trial(self) -> Dict[str, Any]:
        """
        Create a new trial account.
        
        Returns:
            Dict with trial_id, trial_token, conversations_limit, expires_at
        """
        trial_id = f"trial_{secrets.token_hex(12)}"
        trial_token = f"nsk_trial_{secrets.token_hex(24)}"
        now = datetime.now()
        expires_at = now + timedelta(hours=self._trial_expiry_hours)
        
        trial_data = {
            "trial_id": trial_id,
            "trial_token": trial_token,
            "conversations_used": 0,
            "conversations_limit": self._trial_conversations,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "upgraded_to": None,
        }
        
        trials = self._load_trials()
        trials[trial_id] = trial_data
        self._save_trials(trials)
        
        logger.info(f"Trial created: {trial_id}, expires {expires_at.isoformat()}")
        
        return {
            "trial_id": trial_id,
            "trial_token": trial_token,
            "remaining_conversations": self._trial_conversations,
            "conversations_limit": self._trial_conversations,
            "expires_at": expires_at.isoformat(),
            "expires_in": f"{self._trial_expiry_hours}h",
        }
    
    def validate_trial(self, trial_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a trial token and return trial data.
        
        Checks:
        - Token exists
        - Not expired
        - Quota not exhausted
        
        Returns:
            Trial data dict, or None if invalid
        """
        trials = self._load_trials()
        
        for tid, trial in trials.items():
            if trial.get("trial_token") == trial_token:
                # Check expiry
                try:
                    expires_at = datetime.fromisoformat(trial["expires_at"])
                    if datetime.now() > expires_at:
                        return None
                except (ValueError, KeyError):
                    return None
                
                # Check if already upgraded
                if trial.get("upgraded_to"):
                    return None
                
                # Check quota
                if trial["conversations_used"] >= trial["conversations_limit"]:
                    return None
                
                return trial
        
        return None
    
    def track_conversation(self, trial_token: str) -> bool:
        """
        Track a trial conversation. Increments usage counter.
        
        Returns:
            True if conversation was tracked, False if quota exhausted or invalid
        """
        trials = self._load_trials()
        
        for tid, trial in trials.items():
            if trial.get("trial_token") == trial_token:
                # Validate first
                validation = self.validate_trial(trial_token)
                if validation is None:
                    return False
                
                # Increment usage
                trials[tid]["conversations_used"] += 1
                self._save_trials(trials)
                
                remaining = trial["conversations_limit"] - trials[tid]["conversations_used"]
                logger.debug(f"Trial conversation tracked: {tid}, remaining: {remaining}")
                
                return True
        
        return False
    
    def get_remaining(self, trial_token: str) -> Optional[int]:
        """Get remaining conversation count for a trial token."""
        trial = self.validate_trial(trial_token)
        if trial is None:
            return None
        return trial["conversations_limit"] - trial["conversations_used"]
    
    def is_expired(self, trial_token: str) -> bool:
        """Check if a trial token has expired."""
        trials = self._load_trials()
        
        for tid, trial in trials.items():
            if trial.get("trial_token") == trial_token:
                try:
                    expires_at = datetime.fromisoformat(trial["expires_at"])
                    return datetime.now() > expires_at
                except (ValueError, KeyError):
                    return True
        
        return True  # Not found = expired
    
    def upgrade_trial(self, trial_token: str, user_id: str) -> bool:
        """
        Upgrade a trial account to a full account.
        Marks the trial as upgraded and links it to the user account.
        
        Args:
            trial_token: The trial token to upgrade
            user_id: The user ID to link to
            
        Returns:
            True if upgrade was successful
        """
        trials = self._load_trials()
        
        for tid, trial in trials.items():
            if trial.get("trial_token") == trial_token:
                if trial.get("upgraded_to"):
                    logger.warning(f"Trial {tid} already upgraded")
                    return False
                
                trials[tid]["upgraded_to"] = user_id
                trials[tid]["upgraded_at"] = datetime.now().isoformat()
                self._save_trials(trials)
                
                logger.info(f"Trial {tid} upgraded to user {user_id}")
                return True
        
        return False
    
    def cleanup_expired(self, max_age_days: int = 7) -> int:
        """
        Clean up expired trial accounts older than max_age_days.
        
        Returns:
            Number of trials cleaned up
        """
        trials = self._load_trials()
        cutoff = datetime.now() - timedelta(days=max_age_days)
        removed = 0
        
        to_remove = []
        for tid, trial in trials.items():
            try:
                expires_at = datetime.fromisoformat(trial["expires_at"])
                if expires_at < cutoff and not trial.get("upgraded_to"):
                    to_remove.append(tid)
            except (ValueError, KeyError):
                to_remove.append(tid)
        
        for tid in to_remove:
            del trials[tid]
            removed += 1
        
        if removed > 0:
            self._save_trials(trials)
            logger.info(f"Cleaned up {removed} expired trials")
        
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get trial statistics."""
        trials = self._load_trials()
        now = datetime.now()
        
        active = 0
        expired = 0
        upgraded = 0
        total_conversations = 0
        
        for trial in trials.values():
            try:
                expires_at = datetime.fromisoformat(trial["expires_at"])
                if trial.get("upgraded_to"):
                    upgraded += 1
                elif now > expires_at:
                    expired += 1
                else:
                    active += 1
            except (ValueError, KeyError):
                expired += 1
            
            total_conversations += trial.get("conversations_used", 0)
        
        return {
            "total_trials": len(trials),
            "active": active,
            "expired": expired,
            "upgraded": upgraded,
            "total_conversations": total_conversations,
        }


# ── Global Instance ───────────────────────────────────────────────────────────

_trial_manager: Optional[TrialManager] = None


def get_trial_manager() -> TrialManager:
    """Get the global TrialManager instance."""
    global _trial_manager
    if _trial_manager is None:
        _trial_manager = TrialManager()
    return _trial_manager
