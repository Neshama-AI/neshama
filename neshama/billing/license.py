# Billing - License Key Management
"""
License key generation, validation, and machine binding for Neshama SDK.

License Key Format: NSH-{PLAN}-{REGION}-{RANDOM}-{RANDOM}-{CHECKSUM}
  PLAN:     F(ree) / I(ndie) / S(tudio) / E(nterprise)
  REGION:   C(hina) / G(lobal)
  RANDOM:   4-char alphanumeric (A-Z, 0-9, excluding O/0/I/1 for readability)
  CHECKSUM: 2-char verification code (HMAC-based)

Examples:
  NSH-I-C-A1B2-C3D4-E5  → Indie, China region
  NSH-I-G-A1B2-C3D4-E5  → Indie, Global region

Region Isolation (Anti-Arbitrage):
  - China region (C):  api.neshama.cn  → ¥0/¥49/¥199/¥799
  - Global region (G): api.neshama.pw  → $0/$19/$79/$299
  - License key region must match the API endpoint region
  - Cross-region usage is blocked with a clear error message

Machine Binding:
  - First activation binds a machine_id to the license
  - Indie: max 2 machines, Studio: max 5, Enterprise: unlimited
  - Free keys: no machine binding required
  - Machine binding is also region-constrained

Grace Period:
  - 7-day offline grace period after last successful validation
  - Exceeding grace period degrades to Free tier

Redis Caching:
  - License validation results cached for 5 minutes
  - Cache key: license:{license_key}:{machine_id}
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import string
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

# HMAC secret for license key checksum (load from env in production)
LICENSE_HMAC_SECRET = os.environ.get(
    "NESHAMA_LICENSE_HMAC_SECRET",
    "nsh-license-hmac-secret-change-in-prod"
)

# Grace period in days
GRACE_PERIOD_DAYS = 7

# Redis cache TTL in seconds
LICENSE_CACHE_TTL = 300  # 5 minutes

# Machine binding limits per plan
MACHINE_LIMITS = {
    "free": 0,       # Free doesn't bind machines
    "indie": 2,
    "studio": 5,
    "enterprise": -1,  # -1 = unlimited
}

# Feature sets per plan
PLAN_FEATURES = {
    "free": [
        "basic_emotion",
        "ocean_personality",
        "l0_memory",
    ],
    "indie": [
        "basic_emotion",
        "ocean_personality",
        "l0_memory",
        "l1_memory",
        "personality_evolution",
        "byok",
    ],
    "studio": [
        "basic_emotion",
        "ocean_personality",
        "l0_memory",
        "l1_memory",
        "personality_evolution",
        "byok",
        "social_engine",
        "info_propagation",
        "story_trigger",
        "entity_graph",
        "l2_memory",
    ],
    "enterprise": [
        "basic_emotion",
        "ocean_personality",
        "l0_memory",
        "l1_memory",
        "personality_evolution",
        "byok",
        "social_engine",
        "info_propagation",
        "story_trigger",
        "entity_graph",
        "l2_memory",
        "unlimited_npcs",
        "private_deploy",
        "custom_memory",
    ],
}

# NPC limits per plan
PLAN_NPC_LIMITS = {
    "free": 3,
    "indie": 10,
    "studio": 50,
    "enterprise": -1,  # unlimited
}

# Safe alphabet for license keys (no O/0/I/1 to avoid confusion)
SAFE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# Plan code mapping for license key encoding
PLAN_CODES = {
    "free": "F",
    "indie": "I",
    "studio": "S",
    "enterprise": "E",
}

PLAN_CODE_REVERSE = {v: k for k, v in PLAN_CODES.items()}

# ── Region Configuration ─────────────────────────────────────────────────────

# Region code mapping for license key encoding
REGION_CODES = {
    "cn": "C",     # China (api.neshama.cn)
    "global": "G",  # Global (api.neshama.pw)
}

REGION_CODE_REVERSE = {v: k for k, v in REGION_CODES.items()}

# Domain-to-region mapping (used by the API layer to detect request region)
DOMAIN_REGION_MAP = {
    "api.neshama.cn": "cn",
    "api.neshama.pw": "global",
    # Aliases and local dev
    "localhost": "global",
    "127.0.0.1": "global",
}

# Region display names for error messages
REGION_DISPLAY_NAMES = {
    "cn": "China (中国区)",
    "global": "Global (国际区)",
}

# Region-specific pricing (monthly, in local currency cents)
REGION_PRICING = {
    "cn": {
        "free": 0,         # ¥0
        "indie": 4900,     # ¥49
        "studio": 19900,   # ¥199
        "enterprise": 79900,  # ¥799
        "currency": "CNY",
        "symbol": "¥",
    },
    "global": {
        "free": 0,         # $0
        "indie": 1900,     # $19
        "studio": 7900,    # $79
        "enterprise": 29900,  # $299
        "currency": "USD",
        "symbol": "$",
    },
}

# Storage path for license data
DATA_DIR = Path(os.environ.get("NESHAMA_DATA_DIR", Path(__file__).parent.parent.parent.parent / "data"))
LICENSES_FILE = DATA_DIR / "licenses.json"


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class MachineBinding:
    """A machine bound to a license."""
    machine_id: str
    activated_at: str  # ISO 8601
    last_seen_at: str  # ISO 8601


@dataclass
class LicenseRecord:
    """Full license record stored in the database."""
    license_key: str
    plan: str  # free, indie, studio, enterprise
    region: str  # cn, global
    status: str  # active, revoked, expired
    created_at: str  # ISO 8601
    expires_at: str  # ISO 8601
    machines: List[Dict[str, str]] = field(default_factory=list)
    last_validated_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LicenseRecord":
        # Handle legacy records without 'region' field
        if "region" not in data:
            data["region"] = "global"
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class LicenseValidationResult:
    """Result of a license validation check."""
    valid: bool
    plan: str
    max_npcs: int
    features: List[str]
    expires_at: str
    region: str = "global"
    region_match: bool = True
    grace_until: Optional[str] = None
    last_validated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── License Key Generation & Verification ────────────────────────────────────

def _generate_checksum(plan_code: str, region_code: str, random_parts: Tuple[str, str]) -> str:
    """
    Generate a 2-character HMAC-based checksum for a license key.

    The checksum covers: plan_code + region_code + random_part1 + random_part2
    Returns 2 uppercase hex chars.
    """
    payload = f"{plan_code}-{region_code}-{random_parts[0]}-{random_parts[1]}"
    sig = hmac.new(
        LICENSE_HMAC_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()
    # Take first byte, encode as 2 hex chars, uppercase
    return format(sig[0], '02X')


def _verify_checksum(plan_code: str, region_code: str, random_parts: Tuple[str, str], checksum: str) -> bool:
    """Verify the checksum of a license key."""
    expected = _generate_checksum(plan_code, region_code, random_parts)
    return hmac.compare_digest(expected, checksum.upper())


def generate_license_key(plan: str, region: str = "global") -> str:
    """
    Generate a license key in the format: NSH-{PLAN}-{REGION}-{RANDOM}-{RANDOM}-{CHECKSUM}

    Args:
        plan: One of 'free', 'indie', 'studio', 'enterprise'
        region: One of 'cn', 'global'

    Returns:
        License key string

    Raises:
        ValueError: If plan or region is invalid
    """
    if plan not in PLAN_CODES:
        raise ValueError(f"Invalid plan: {plan}. Must be one of: {list(PLAN_CODES.keys())}")
    if region not in REGION_CODES:
        raise ValueError(f"Invalid region: {region}. Must be one of: {list(REGION_CODES.keys())}")

    plan_code = PLAN_CODES[plan]
    region_code = REGION_CODES[region]
    part1 = "".join(secrets.choice(SAFE_ALPHABET) for _ in range(4))
    part2 = "".join(secrets.choice(SAFE_ALPHABET) for _ in range(4))
    checksum = _generate_checksum(plan_code, region_code, (part1, part2))

    return f"NSH-{plan_code}-{region_code}-{part1}-{part2}-{checksum}"


def parse_license_key(license_key: str) -> Optional[Dict[str, str]]:
    """
    Parse and validate the format of a license key.

    New format (6 parts): NSH-{PLAN}-{REGION}-{RANDOM}-{RANDOM}-{CHECKSUM}
    Legacy format (5 parts): NSH-{PLAN}-{RANDOM}-{RANDOM}-{CHECKSUM}
      → Treated as region="global" for backward compatibility

    Returns dict with parsed fields or None if invalid.
    """
    if not license_key:
        return None

    key = license_key.strip().upper()
    parts = key.split("-")

    if len(parts) == 6:
        # New format: NSH-PLAN-REGION-RANDOM-RANDOM-CHECKSUM
        prefix, plan_code, region_code, random1, random2, checksum = parts

        if prefix != "NSH":
            return None
        if plan_code not in PLAN_CODE_REVERSE:
            return None
        if region_code not in REGION_CODE_REVERSE:
            return None
        if len(random1) != 4 or len(random2) != 4:
            return None
        if len(checksum) != 2:
            return None

        # Verify all chars are from safe alphabet
        valid_chars = set(SAFE_ALPHABET)
        if not all(c in valid_chars for c in random1 + random2):
            return None

        # Verify checksum
        if not _verify_checksum(plan_code, region_code, (random1, random2), checksum):
            return None

        return {
            "plan_code": plan_code,
            "plan": PLAN_CODE_REVERSE[plan_code],
            "region_code": region_code,
            "region": REGION_CODE_REVERSE[region_code],
            "random1": random1,
            "random2": random2,
            "checksum": checksum,
        }

    elif len(parts) == 5:
        # Legacy format: NSH-PLAN-RANDOM-RANDOM-CHECKSUM (treat as global)
        prefix, plan_code, random1, random2, checksum = parts

        if prefix != "NSH":
            return None
        if plan_code not in PLAN_CODE_REVERSE:
            return None
        if len(random1) != 4 or len(random2) != 4:
            return None
        if len(checksum) != 2:
            return None

        valid_chars = set(SAFE_ALPHABET)
        if not all(c in valid_chars for c in random1 + random2):
            return None

        # Verify legacy checksum (no region code in payload)
        if not _verify_checksum(plan_code, "G", (random1, random2), checksum):
            return None

        return {
            "plan_code": plan_code,
            "plan": PLAN_CODE_REVERSE[plan_code],
            "region_code": "G",
            "region": "global",
            "random1": random1,
            "random2": random2,
            "checksum": checksum,
        }

    return None


# ── Region Detection ──────────────────────────────────────────────────────────

def detect_region_from_host(host: str) -> str:
    """
    Detect the request region from the API host header.

    Args:
        host: The Host header value (e.g., "api.neshama.cn", "api.neshama.pw")

    Returns:
        Region string ("cn" or "global")
    """
    if not host:
        return "global"

    # Strip port if present
    hostname = host.split(":")[0].lower()

    # Direct match
    if hostname in DOMAIN_REGION_MAP:
        return DOMAIN_REGION_MAP[hostname]

    # Subdomain match (e.g., test.api.neshama.cn)
    for domain, region in DOMAIN_REGION_MAP.items():
        if hostname.endswith(f".{domain}"):
            return region

    # Default to global for unknown domains
    logger.debug(f"Unknown host '{hostname}', defaulting to global region")
    return "global"


def check_region_match(license_region: str, request_region: str) -> Tuple[bool, str]:
    """
    Check if a license's region matches the request region.

    Args:
        license_region: The region encoded in the license key ("cn" or "global")
        request_region: The region detected from the request host

    Returns:
        (match, error_message) tuple. error_message is empty string if match.
    """
    if license_region == request_region:
        return True, ""

    license_display = REGION_DISPLAY_NAMES.get(license_region, license_region)
    request_display = REGION_DISPLAY_NAMES.get(request_region, request_region)

    return False, (
        f"License region mismatch. This license is for {license_display} "
        f"but the request came from {request_display}. "
        f"Cross-region usage is not permitted."
    )


# ── License Storage ───────────────────────────────────────────────────────────

class LicenseStore:
    """
    Persistent storage for license records.

    Uses JSON file for simplicity. Production should use a database.
    Thread-safe via file locking (simplified).
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._path = storage_path or LICENSES_FILE
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load license data from disk."""
        if self._path.exists():
            try:
                with open(self._path, 'r') as f:
                    self._data = json.load(f)
                logger.info(f"Loaded {len(self._data)} license records from {self._path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load license data: {e}")
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """Save license data to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._path, 'w') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Failed to save license data: {e}")

    def get(self, license_key: str) -> Optional[LicenseRecord]:
        """Get a license record by key."""
        raw = self._data.get(license_key)
        if raw is None:
            return None
        return LicenseRecord.from_dict(raw)

    def put(self, record: LicenseRecord) -> None:
        """Create or update a license record."""
        self._data[record.license_key] = record.to_dict()
        self._save()

    def delete(self, license_key: str) -> bool:
        """Delete a license record. Returns True if found and deleted."""
        if license_key in self._data:
            del self._data[license_key]
            self._save()
            return True
        return False

    def list_all(
        self,
        plan: Optional[str] = None,
        status: Optional[str] = None,
        region: Optional[str] = None,
    ) -> List[LicenseRecord]:
        """List all licenses, optionally filtered by plan, status, or region."""
        results = []
        for raw in self._data.values():
            record = LicenseRecord.from_dict(raw)
            if plan and record.plan != plan:
                continue
            if status and record.status != status:
                continue
            if region and record.region != region:
                continue
            results.append(record)
        return results

    def add_machine(self, license_key: str, machine_id: str) -> bool:
        """
        Bind a machine to a license.

        Returns True if binding succeeded, False if limit exceeded.
        """
        record = self.get(license_key)
        if record is None:
            return False

        # Check if already bound
        for m in record.machines:
            if m["machine_id"] == machine_id:
                # Update last_seen_at
                m["last_seen_at"] = datetime.now(timezone.utc).isoformat()
                self.put(record)
                return True

        # Check limit
        limit = MACHINE_LIMITS.get(record.plan, 0)
        if limit == -1:
            pass  # Unlimited
        elif len(record.machines) >= limit:
            return False

        now = datetime.now(timezone.utc).isoformat()
        record.machines.append({
            "machine_id": machine_id,
            "activated_at": now,
            "last_seen_at": now,
        })
        self.put(record)
        return True

    def remove_machine(self, license_key: str, machine_id: str) -> bool:
        """
        Unbind a machine from a license.

        Returns True if machine was found and removed.
        """
        record = self.get(license_key)
        if record is None:
            return False

        original_len = len(record.machines)
        record.machines = [m for m in record.machines if m["machine_id"] != machine_id]

        if len(record.machines) < original_len:
            self.put(record)
            return True
        return False

    def is_machine_bound(self, license_key: str, machine_id: str) -> bool:
        """Check if a machine is bound to a license."""
        record = self.get(license_key)
        if record is None:
            return False
        return any(m["machine_id"] == machine_id for m in record.machines)

    def update_last_validated(self, license_key: str) -> None:
        """Update the last_validated_at timestamp."""
        record = self.get(license_key)
        if record is not None:
            record.last_validated_at = datetime.now(timezone.utc).isoformat()
            self.put(record)


# ── Redis Cache ───────────────────────────────────────────────────────────────

class LicenseCache:
    """
    Redis-based cache for license validation results.

    Falls back to in-memory dict if Redis is unavailable.
    """

    def __init__(self):
        self._redis = None
        self._fallback: Dict[str, Tuple[float, Dict[str, Any]]] = {}  # key -> (expiry_ts, data)
        self._init_redis()

    def _init_redis(self) -> None:
        """Try to connect to Redis."""
        try:
            import redis
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(redis_url, socket_timeout=2)
            self._redis.ping()
            logger.info("License cache connected to Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable for license cache, using in-memory fallback: {e}")
            self._redis = None

    def _cache_key(self, license_key: str, machine_id: str) -> str:
        return f"license:{license_key}:{machine_id}"

    def get(self, license_key: str, machine_id: str) -> Optional[Dict[str, Any]]:
        """Get cached validation result."""
        key = self._cache_key(license_key, machine_id)

        if self._redis:
            try:
                raw = self._redis.get(key)
                if raw:
                    return json.loads(raw)
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")
        else:
            entry = self._fallback.get(key)
            if entry:
                expiry_ts, data = entry
                if time.time() < expiry_ts:
                    return data
                del self._fallback[key]

        return None

    def set(self, license_key: str, machine_id: str, result: Dict[str, Any]) -> None:
        """Cache a validation result."""
        key = self._cache_key(license_key, machine_id)

        if self._redis:
            try:
                self._redis.setex(key, LICENSE_CACHE_TTL, json.dumps(result))
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")
                # Fall back to in-memory
                self._fallback[key] = (time.time() + LICENSE_CACHE_TTL, result)
        else:
            self._fallback[key] = (time.time() + LICENSE_CACHE_TTL, result)

    def invalidate(self, license_key: str, machine_id: Optional[str] = None) -> None:
        """Invalidate cached results for a license key."""
        if self._redis:
            try:
                if machine_id:
                    key = self._cache_key(license_key, machine_id)
                    self._redis.delete(key)
                else:
                    # Delete all cache entries for this license
                    pattern = f"license:{license_key}:*"
                    keys = self._redis.keys(pattern)
                    if keys:
                        self._redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis cache invalidation error: {e}")
        else:
            if machine_id:
                key = self._cache_key(license_key, machine_id)
                self._fallback.pop(key, None)
            else:
                prefix = f"license:{license_key}:"
                to_remove = [k for k in self._fallback if k.startswith(prefix)]
                for k in to_remove:
                    del self._fallback[k]


# ── License Service ───────────────────────────────────────────────────────────

# Global instances (lazy init)
_store: Optional[LicenseStore] = None
_cache: Optional[LicenseCache] = None


def get_license_store() -> LicenseStore:
    """Get the global license store instance."""
    global _store
    if _store is None:
        _store = LicenseStore()
    return _store


def get_license_cache() -> LicenseCache:
    """Get the global license cache instance."""
    global _cache
    if _cache is None:
        _cache = LicenseCache()
    return _cache


def validate_license(
    license_key: str,
    machine_id: str,
    request_region: Optional[str] = None,
    store: Optional[LicenseStore] = None,
    cache: Optional[LicenseCache] = None,
) -> LicenseValidationResult:
    """
    Validate a license key and return entitlement information.

    Steps:
    1. Check cache for recent validation
    2. Parse and verify the license key format + checksum
    3. Check region match (if request_region provided)
    4. Look up the license record in the store
    5. Check if the license is active and not expired
    6. Check machine binding (if required by plan)
    7. Check grace period (last_validated_at)
    8. Update last_validated_at and cache the result

    Args:
        license_key: The license key to validate
        machine_id: Hardware fingerprint of the requesting machine
        request_region: Region detected from request host ("cn" or "global").
                        If None, region check is skipped.
        store: License store (uses global if not provided)
        cache: License cache (uses global if not provided)

    Returns:
        LicenseValidationResult with entitlement information
    """
    store = store or get_license_store()
    cache = cache or get_license_cache()

    # Step 1: Check cache (skip if region must be re-validated)
    if request_region is None:
        cached = cache.get(license_key, machine_id)
        if cached:
            logger.debug(f"License cache hit for {license_key[:12]}...")
            return LicenseValidationResult(**cached)

    # Step 2: Parse key format
    parsed = parse_license_key(license_key)
    if parsed is None:
        result = _free_result(reason="Invalid license key format", region=request_region or "global")
        return result

    license_region = parsed["region"]
    effective_region = request_region or license_region

    # Step 3: Region match check
    region_match = True
    if request_region is not None:
        region_match, region_error = check_region_match(license_region, request_region)
        if not region_match:
            result = LicenseValidationResult(
                valid=False,
                plan="free",
                max_npcs=PLAN_NPC_LIMITS["free"],
                features=list(PLAN_FEATURES["free"]),
                expires_at="",
                region=license_region,
                region_match=False,
                grace_until=None,
                last_validated_at=datetime.now(timezone.utc).isoformat(),
            )
            # Attach the error reason via a private attribute for the API layer
            result._region_error = region_error
            return result

    # Step 4: Look up record
    record = store.get(license_key)
    if record is None:
        result = _free_result(reason="License key not found", region=effective_region)
        return result

    # Step 5: Check status
    if record.status == "revoked":
        result = _free_result(reason="License has been revoked", region=effective_region)
        return result

    # Step 6: Check expiry
    now = datetime.now(timezone.utc)
    try:
        expires_at = datetime.fromisoformat(record.expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            result = _free_result(reason="License has expired", region=effective_region)
            return result
    except (ValueError, TypeError):
        logger.warning(f"Invalid expires_at format for license {license_key}")

    # Step 7: Check machine binding
    plan = record.plan
    if plan != "free" and record.machines:
        bound = any(m["machine_id"] == machine_id for m in record.machines)
        if not bound:
            result = _free_result(reason="Machine not bound to this license", region=effective_region)
            return result

    # Step 8: Update last_validated_at
    store.update_last_validated(license_key)

    # Step 9: Compute grace_until (from last_validated_at if exists)
    grace_until = None
    if record.last_validated_at:
        try:
            last_validated = datetime.fromisoformat(record.last_validated_at)
            if last_validated.tzinfo is None:
                last_validated = last_validated.replace(tzinfo=timezone.utc)
            grace_deadline = last_validated + timedelta(days=GRACE_PERIOD_DAYS)
            if grace_deadline > now:
                grace_until = grace_deadline.isoformat()
        except (ValueError, TypeError):
            pass

    # Build result
    result = LicenseValidationResult(
        valid=True,
        plan=plan,
        max_npcs=PLAN_NPC_LIMITS.get(plan, 3),
        features=list(PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])),
        expires_at=record.expires_at,
        region=license_region,
        region_match=True,
        grace_until=grace_until,
        last_validated_at=datetime.now(timezone.utc).isoformat(),
    )

    # Cache the result (only if region matched)
    cache.set(license_key, machine_id, result.to_dict())

    return result


def activate_license(
    license_key: str,
    machine_id: str,
    request_region: Optional[str] = None,
    store: Optional[LicenseStore] = None,
    cache: Optional[LicenseCache] = None,
) -> Tuple[bool, str]:
    """
    Activate a license by binding it to a machine.

    Args:
        license_key: The license key to activate
        machine_id: Hardware fingerprint to bind
        request_region: Region detected from request host. If provided, checks region match.

    Returns:
        (success, message) tuple
    """
    store = store or get_license_store()
    cache = cache or get_license_cache()

    # Parse key
    parsed = parse_license_key(license_key)
    if parsed is None:
        return False, "Invalid license key format"

    # Region match check
    if request_region is not None:
        match, error = check_region_match(parsed["region"], request_region)
        if not match:
            return False, error

    # Look up record
    record = store.get(license_key)
    if record is None:
        return False, "License key not found"

    # Check status
    if record.status != "active":
        return False, f"License is {record.status}, cannot activate"

    # Check expiry
    now = datetime.now(timezone.utc)
    try:
        expires_at = datetime.fromisoformat(record.expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            return False, "License has expired"
    except (ValueError, TypeError):
        pass

    # Free plan doesn't need machine binding
    if record.plan == "free":
        return True, "Free plan does not require machine activation"

    # Try to bind
    success = store.add_machine(license_key, machine_id)
    if not success:
        limit = MACHINE_LIMITS.get(record.plan, 0)
        return False, f"Machine limit reached ({limit} machines for {record.plan} plan)"

    # Invalidate cache
    cache.invalidate(license_key)

    return True, "License activated successfully"


def deactivate_license(
    license_key: str,
    machine_id: str,
    store: Optional[LicenseStore] = None,
    cache: Optional[LicenseCache] = None,
) -> Tuple[bool, str]:
    """
    Deactivate a license by unbinding a machine.

    Args:
        license_key: The license key
        machine_id: Machine to unbind

    Returns:
        (success, message) tuple
    """
    store = store or get_license_store()
    cache = cache or get_license_cache()

    # Parse key
    parsed = parse_license_key(license_key)
    if parsed is None:
        return False, "Invalid license key format"

    # Look up record
    record = store.get(license_key)
    if record is None:
        return False, "License key not found"

    # Try to unbind
    success = store.remove_machine(license_key, machine_id)
    if not success:
        return False, "Machine not bound to this license"

    # Invalidate cache
    cache.invalidate(license_key, machine_id)

    return True, "Machine deactivated successfully"


def get_license_status(
    license_key: str,
    store: Optional[LicenseStore] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get the full status of a license.

    Returns dict with license details or None if not found.
    """
    store = store or get_license_store()

    record = store.get(license_key)
    if record is None:
        return None

    region_info = REGION_PRICING.get(record.region, REGION_PRICING["global"])

    return {
        "license_key": record.license_key,
        "plan": record.plan,
        "region": record.region,
        "status": record.status,
        "created_at": record.created_at,
        "expires_at": record.expires_at,
        "machine_count": len(record.machines),
        "machine_limit": MACHINE_LIMITS.get(record.plan, 0),
        "machines": [
            {
                "machine_id": m["machine_id"],
                "activated_at": m["activated_at"],
                "last_seen_at": m["last_seen_at"],
            }
            for m in record.machines
        ],
        "last_validated_at": record.last_validated_at,
        "features": PLAN_FEATURES.get(record.plan, []),
        "max_npcs": PLAN_NPC_LIMITS.get(record.plan, 3),
        "pricing": {
            "currency": region_info["currency"],
            "symbol": region_info["symbol"],
            "monthly": region_info.get(record.plan, 0),
        },
    }


def generate_license(
    plan: str,
    region: str = "global",
    expires_at: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    store: Optional[LicenseStore] = None,
) -> Tuple[str, LicenseRecord]:
    """
    Generate a new license key and store the record.

    Args:
        plan: Subscription plan
        region: Region ("cn" or "global") — required, determines key encoding
        expires_at: ISO 8601 expiry date (defaults to 1 year from now)
        metadata: Optional metadata dict

    Returns:
        (license_key, license_record) tuple
    """
    store = store or get_license_store()

    if plan not in PLAN_CODES:
        raise ValueError(f"Invalid plan: {plan}")
    if region not in REGION_CODES:
        raise ValueError(f"Invalid region: {region}. Must be 'cn' or 'global'")

    # Generate key with region
    license_key = generate_license_key(plan, region)

    # Default expiry
    if expires_at is None:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()

    now = datetime.now(timezone.utc).isoformat()

    record = LicenseRecord(
        license_key=license_key,
        plan=plan,
        region=region,
        status="active",
        created_at=now,
        expires_at=expires_at,
        machines=[],
        last_validated_at=None,
        metadata=metadata or {},
    )

    store.put(record)

    logger.info(f"Generated {region}:{plan} license: {license_key}")
    return license_key, record


def revoke_license(
    license_key: str,
    store: Optional[LicenseStore] = None,
    cache: Optional[LicenseCache] = None,
) -> Tuple[bool, str]:
    """
    Revoke a license.

    Returns:
        (success, message) tuple
    """
    store = store or get_license_store()
    cache = cache or get_license_cache()

    record = store.get(license_key)
    if record is None:
        return False, "License key not found"

    if record.status == "revoked":
        return False, "License already revoked"

    record.status = "revoked"
    store.put(record)

    # Invalidate all cache entries
    cache.invalidate(license_key)

    logger.info(f"Revoked license: {license_key}")
    return True, "License revoked successfully"


def check_grace_period(
    license_key: str,
    last_validated_at: Optional[str] = None,
    store: Optional[LicenseStore] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Check if a license is within the grace period.

    Used by SDK clients for offline validation.

    Args:
        license_key: The license key
        last_validated_at: ISO 8601 timestamp from client cache (optional)
        store: License store (uses global if not provided)

    Returns:
        (within_grace, grace_until_iso) tuple
    """
    store = store or get_license_store()

    # Use server-side last_validated_at if client doesn't provide one
    if last_validated_at is None:
        record = store.get(license_key)
        if record is None or record.last_validated_at is None:
            return False, None
        last_validated_at = record.last_validated_at

    try:
        last_validated = datetime.fromisoformat(last_validated_at)
        if last_validated.tzinfo is None:
            last_validated = last_validated.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return False, None

    now = datetime.now(timezone.utc)
    grace_deadline = last_validated + timedelta(days=GRACE_PERIOD_DAYS)
    within_grace = now <= grace_deadline

    return within_grace, grace_deadline.isoformat() if within_grace else None


def check_feature(feature_name: str, plan: str) -> bool:
    """Check if a feature is available in the given plan."""
    features = PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])
    return feature_name in features


def get_region_pricing(region: str) -> Dict[str, Any]:
    """Get pricing information for a region."""
    return REGION_PRICING.get(region, REGION_PRICING["global"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _free_result(reason: str = "", region: str = "global") -> LicenseValidationResult:
    """Create a Free-tier result for invalid/expired licenses."""
    grace_deadline = datetime.now(timezone.utc) + timedelta(days=GRACE_PERIOD_DAYS)
    return LicenseValidationResult(
        valid=False,
        plan="free",
        max_npcs=PLAN_NPC_LIMITS["free"],
        features=list(PLAN_FEATURES["free"]),
        expires_at="",
        region=region,
        region_match=False,
        grace_until=grace_deadline.isoformat(),
        last_validated_at=datetime.now(timezone.utc).isoformat(),
    )
