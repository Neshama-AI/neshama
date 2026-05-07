# Storage Backend Factory
"""
Storage backend factory and abstraction layer.

This module provides the factory for creating storage backends
based on environment configuration.

Usage:
    from neshama.storage.backend import create_storage_backend
    
    # Create based on environment
    backend = create_storage_backend()
    
    # Or specify explicitly
    backend = create_storage_backend("redis")
"""

import os
import logging
from typing import Optional

from .base import StorageBackend
from .yaml_storage import YamlStorage
from .redis_storage import RedisStorage

logger = logging.getLogger(__name__)

# Environment variables
ENV_STORAGE_BACKEND = "NESHAMA_STORAGE_BACKEND"
ENV_REDIS_URL = "NESHAMA_REDIS_URL"
ENV_REDIS_HOST = "NESHAMA_REDIS_HOST"
ENV_REDIS_PORT = "NESHAMA_REDIS_PORT"
ENV_REDIS_DB = "NESHAMA_REDIS_DB"
ENV_REDIS_PASSWORD = "NESHAMA_REDIS_PASSWORD"
ENV_REDIS_SSL = "NESHAMA_REDIS_SSL"
ENV_DATA_DIR = "NESHAMA_DATA_DIR"

# Backend types
BACKEND_YAML = "yaml"
BACKEND_REDIS = "redis"


def create_storage_backend(
    backend_type: Optional[str] = None,
    redis_url: Optional[str] = None,
    data_dir: Optional[str] = None,
) -> StorageBackend:
    """
    Create a storage backend based on configuration.
    
    Args:
        backend_type: Override backend type ("yaml" or "redis").
                     If None, uses environment variable or defaults to "yaml".
        redis_url: Redis connection URL (e.g., "redis://localhost:6379/0").
                  Overrides individual host/port/db settings.
        data_dir: Directory for YAML storage data files.
    
    Returns:
        A StorageBackend instance (YamlStorage or RedisStorage).
    
    Raises:
        ValueError: If backend_type is not recognized.
    
    Example:
        >>> # Auto-detect from environment
        >>> backend = create_storage_backend()
        >>> 
        >>> # Explicit Redis backend
        >>> backend = create_storage_backend(
        ...     backend_type="redis",
        ...     redis_url="redis://localhost:6379/0"
        ... )
        >>> 
        >>> # Explicit YAML backend
        >>> backend = create_storage_backend(
        ...     backend_type="yaml",
        ...     data_dir="custom/data/path"
        ... )
    """
    # Determine backend type
    if backend_type is None:
        backend_type = os.environ.get(ENV_STORAGE_BACKEND, BACKEND_YAML).lower()
    
    if backend_type == BACKEND_REDIS:
        return _create_redis_backend(redis_url)
    elif backend_type == BACKEND_YAML:
        return _create_yaml_backend(data_dir)
    else:
        raise ValueError(
            f"Unknown storage backend type: {backend_type}. "
            f"Valid options: {BACKEND_YAML}, {BACKEND_REDIS}"
        )


def _create_redis_backend(redis_url: Optional[str] = None) -> RedisStorage:
    """
    Create a Redis storage backend.
    
    Args:
        redis_url: Redis connection URL.
    
    Returns:
        RedisStorage instance.
    
    Note:
        If Redis connection fails, this function will raise an exception.
        The StorageManager class provides automatic fallback to YAML.
    """
    if redis_url:
        config = _parse_redis_url(redis_url)
        return RedisStorage(**config)
    
    # Use individual environment variables
    return RedisStorage(
        host=os.environ.get(ENV_REDIS_HOST, "localhost"),
        port=int(os.environ.get(ENV_REDIS_PORT, "6379")),
        db=int(os.environ.get(ENV_REDIS_DB, "0")),
        password=os.environ.get(ENV_REDIS_PASSWORD),
        ssl=os.environ.get(ENV_REDIS_SSL, "").lower() in ("1", "true", "yes"),
    )


def _create_yaml_backend(data_dir: Optional[str] = None) -> YamlStorage:
    """
    Create a YAML storage backend.
    
    Args:
        data_dir: Directory for YAML data files.
    
    Returns:
        YamlStorage instance.
    """
    if data_dir is None:
        data_dir = os.environ.get(ENV_DATA_DIR, "data/storage")
    
    return YamlStorage(data_dir=data_dir)


def _parse_redis_url(url: str) -> dict:
    """
    Parse a Redis URL into connection parameters.
    
    Args:
        url: Redis URL in format: redis[s]://[password@]host[:port][/db]
              Or: redis[s]://[:password@]host[:port][/db]
    
    Returns:
        Dictionary with host, port, db, password, ssl.
    
    Example:
        >>> config = _parse_redis_url("redis://localhost:6379/0")
        >>> print(config)
        {'host': 'localhost', 'port': 6379, 'db': 0, 'password': None, 'ssl': False}
        
        >>> config = _parse_redis_url("redis://:password@localhost:6379/0")
        >>> print(config)
        {'host': 'localhost', 'port': 6379, 'db': 0, 'password': 'password', 'ssl': False}
    """
    try:
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        # Handle password
        password = parsed.password
        if not password:
            # Try to extract from username (for formats like redis://password@host)
            # This handles the common case where password is in the "username" field
            if parsed.username and parsed.username != "":
                # Check if it looks like a password (not a typical username)
                password = parsed.username
        
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 6379,
            "db": int(parsed.path.lstrip("/") or "0"),
            "password": password,
            "ssl": parsed.scheme == "rediss",
        }
    except Exception as e:
        logger.warning(f"Failed to parse Redis URL: {e}, using defaults")
        return {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None,
            "ssl": False,
        }


def get_available_backends() -> list[str]:
    """
    Get list of available storage backend types.
    
    Returns:
        List of backend type strings.
    """
    backends = [BACKEND_YAML]  # YAML is always available
    
    # Check if Redis is available
    try:
        import redis
        backends.append(BACKEND_REDIS)
    except ImportError:
        logger.debug("redis package not available")
    
    return backends


def is_backend_available(backend_type: str) -> bool:
    """
    Check if a storage backend type is available.
    
    Args:
        backend_type: Backend type to check.
    
    Returns:
        True if the backend is available, False otherwise.
    """
    if backend_type == BACKEND_YAML:
        return True
    
    if backend_type == BACKEND_REDIS:
        try:
            import redis
            return True
        except ImportError:
            return False
    
    return False
