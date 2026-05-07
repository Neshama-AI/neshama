# Storage Module
"""
Storage module for Neshama.

Provides abstract and concrete storage backends:
- YAML file storage (development)
- Redis storage (production)

Usage:
    from neshama.storage import get_storage, StorageManager
    
    # Global instance
    storage = get_storage()
    storage.set("key", "value")
    value = storage.get("key")
    
    # Or use convenience functions
    from neshama.storage import set, get, delete
    
    set("key", "value")
    value = get("key")
"""

from .base import StorageBackend
from .yaml_storage import YamlStorage
from .redis_storage import RedisStorage
from .manager import StorageManager, get_storage
from .backend import (
    create_storage_backend,
    get_available_backends,
    is_backend_available,
)

__all__ = [
    "StorageBackend",
    "YamlStorage", 
    "RedisStorage",
    "StorageManager",
    "get_storage",
    "create_storage_backend",
    "get_available_backends",
    "is_backend_available",
]
