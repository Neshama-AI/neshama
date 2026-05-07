# Storage Manager
"""
Storage manager with factory pattern.

Manages storage backend selection based on configuration.
Provides global singleton access to storage.
"""

import os
import logging
from typing import Optional

from .base import StorageBackend
from .yaml_storage import YamlStorage
from .redis_storage import RedisStorage

logger = logging.getLogger(__name__)

# Environment variable for backend selection
ENV_STORAGE_BACKEND = "NESHAMA_STORAGE_BACKEND"
ENV_REDIS_URL = "NESHAMA_REDIS_URL"

# Backend types
BACKEND_YAML = "yaml"
BACKEND_REDIS = "redis"


class StorageManager:
    """
    Storage backend manager with factory pattern.
    
    Provides unified access to storage with automatic backend
    selection based on environment configuration.
    
    Example:
        >>> # Development (YAML)
        >>> storage = StorageManager.get_instance()
        >>> 
        >>> # Production (Redis)
        >>> os.environ["NESHAMA_STORAGE_BACKEND"] = "redis"
        >>> os.environ["NESHAMA_REDIS_URL"] = "redis://localhost:6379/0"
        >>> storage = StorageManager.get_instance()
        >>> 
        >>> # Direct usage
        >>> storage.set("key", "value")
        >>> value = storage.get("key")
    """
    
    _instance: Optional["StorageManager"] = None
    _lock = None
    
    def __init__(self):
        """Initialize storage manager."""
        self._backend: Optional[StorageBackend] = None
        self._backend_type: Optional[str] = None
        self._initialized = False
    
    @classmethod
    def _get_lock(cls):
        """Get or create class-level lock."""
        if cls._lock is None:
            import threading
            cls._lock = threading.Lock()
        return cls._lock
    
    @classmethod
    def get_instance(cls) -> "StorageManager":
        """
        Get singleton storage manager instance.
        
        Returns:
            The global StorageManager instance
        """
        if cls._instance is None:
            with cls._get_lock():
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        with cls._get_lock():
            if cls._instance is not None:
                cls._instance.close()
            cls._instance = None
    
    def _parse_redis_url(self, url: str) -> dict:
        """
        Parse Redis URL into components.
        
        Args:
            url: Redis URL like redis://localhost:6379/0
            
        Returns:
            Dictionary with host, port, db, password, ssl
        """
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            
            result = {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 6379,
                "db": int(parsed.path.lstrip("/") or "0"),
                "password": parsed.password,
                "ssl": parsed.scheme == "rediss",
            }
            
            return result
        except Exception as e:
            logger.warning(f"Failed to parse Redis URL: {e}")
            return {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": None,
                "ssl": False,
            }
    
    def _init_backend(self) -> None:
        """Initialize the storage backend based on configuration."""
        if self._initialized:
            return
        
        backend_type = os.environ.get(ENV_STORAGE_BACKEND, BACKEND_YAML)
        
        if backend_type == BACKEND_REDIS:
            # Try Redis URL first
            redis_url = os.environ.get(ENV_REDIS_URL)
            
            if redis_url:
                config = self._parse_redis_url(redis_url)
                try:
                    self._backend = RedisStorage(**config)
                    self._backend_type = BACKEND_REDIS
                    logger.info("Initialized Redis storage backend")
                except Exception as e:
                    logger.warning(f"Failed to connect to Redis: {e}, falling back to YAML")
                    backend_type = BACKEND_YAML
            else:
                # Use individual environment variables
                try:
                    self._backend = RedisStorage(
                        host=os.environ.get("NESHAMA_REDIS_HOST", "localhost"),
                        port=int(os.environ.get("NESHAMA_REDIS_PORT", "6379")),
                        db=int(os.environ.get("NESHAMA_REDIS_DB", "0")),
                        password=os.environ.get("NESHAMA_REDIS_PASSWORD"),
                        ssl=os.environ.get("NESHAMA_REDIS_SSL", "").lower() in ("1", "true", "yes"),
                    )
                    self._backend_type = BACKEND_REDIS
                    logger.info("Initialized Redis storage backend")
                except Exception as e:
                    logger.warning(f"Failed to connect to Redis: {e}, falling back to YAML")
                    backend_type = BACKEND_YAML
        
        if backend_type == BACKEND_YAML or self._backend is None:
            # Use YAML storage
            data_dir = os.environ.get("NESHAMA_DATA_DIR", "data/storage")
            self._backend = YamlStorage(data_dir)
            self._backend_type = BACKEND_YAML
            logger.info(f"Initialized YAML storage backend (data_dir={data_dir})")
        
        self._initialized = True
    
    @property
    def backend_type(self) -> str:
        """Get current backend type."""
        self._init_backend()
        return self._backend_type or BACKEND_YAML
    
    def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        self._init_backend()
        return self._backend.get(key)
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair."""
        self._init_backend()
        return self._backend.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete a key."""
        self._init_backend()
        return self._backend.delete(key)
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        self._init_backend()
        return self._backend.exists(key)
    
    def list_keys(self, prefix: str = "") -> list:
        """List all keys with optional prefix."""
        self._init_backend()
        return self._backend.list_keys(prefix)
    
    def batch_get(self, keys: list) -> dict:
        """Get multiple values at once."""
        self._init_backend()
        return self._backend.batch_get(keys)
    
    def batch_set(self, items: dict, ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs at once."""
        self._init_backend()
        return self._backend.batch_set(items, ttl)
    
    def close(self) -> None:
        """Close the storage backend."""
        if self._backend:
            self._backend.close()
            self._backend = None
            self._initialized = False
            logger.info("Storage backend closed")
    
    def health_check(self) -> bool:
        """Check if storage backend is healthy."""
        self._init_backend()
        return self._backend.health_check()
    
    def ping(self) -> bool:
        """Ping the storage backend."""
        self._init_backend()
        return self._backend.ping()


# Global convenience functions
def get_storage() -> StorageBackend:
    """Get the global storage backend."""
    return StorageManager.get_instance()


def get(key: str) -> Optional[str]:
    """Get a value by key."""
    return get_storage().get(key)


def set(key: str, value: str, ttl: Optional[int] = None) -> bool:
    """Set a key-value pair."""
    return get_storage().set(key, value, ttl)


def delete(key: str) -> bool:
    """Delete a key."""
    return get_storage().delete(key)


def exists(key: str) -> bool:
    """Check if a key exists."""
    return get_storage().exists(key)


def list_keys(prefix: str = "") -> list:
    """List all keys with optional prefix."""
    return get_storage().list_keys(prefix)


def batch_get(keys: list) -> dict:
    """Get multiple values at once."""
    return get_storage().batch_get(keys)


def batch_set(items: dict, ttl: Optional[int] = None) -> bool:
    """Set multiple key-value pairs at once."""
    return get_storage().batch_set(items, ttl)
