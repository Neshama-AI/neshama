# YAML Storage Backend
"""
YAML file-based storage implementation.

Stores data as YAML files on the filesystem.
Suitable for development and small-scale deployments.
"""

import os
import fcntl
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import yaml

from .base import StorageBackend


class YamlStorage(StorageBackend):
    """
    YAML file storage backend.
    
    Features:
    - Thread-safe file operations with locking
    - Automatic directory creation
    - TTL support via file metadata
    - Batch operations
    
    File structure:
        data_dir/
            key1.yaml
            key2.yaml
            ...
    
    Each file contains:
        value: <stored value>
        created_at: <timestamp>
        expires_at: <timestamp or null>
    """
    
    def __init__(self, data_dir: str = "data/storage"):
        """
        Initialize YAML storage.
        
        Args:
            data_dir: Directory to store YAML files
        """
        self._data_dir = Path(data_dir)
        self._lock = threading.RLock()
        self._ensure_directory()
    
    def _ensure_directory(self) -> None:
        """Create data directory if it doesn't exist."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a key."""
        # Sanitize key to prevent path traversal
        safe_key = key.replace("/", "_").replace("..", "_")
        return self._data_dir / f"{safe_key}.yaml"
    
    def _read_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """Read and parse a YAML file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    return yaml.safe_load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except FileNotFoundError:
            return None
        except yaml.YAMLError:
            return None
    
    def _write_file(self, path: Path, data: Dict[str, Any]) -> bool:
        """Write data to a YAML file with exclusive lock."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
                    return True
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except OSError:
            return False
    
    def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        with self._lock:
            path = self._get_file_path(key)
            data = self._read_file(path)
            
            if data is None:
                return None
            
            # Check expiration
            expires_at = data.get("expires_at")
            if expires_at:
                if isinstance(expires_at, str):
                    expires_time = datetime.fromisoformat(expires_at)
                else:
                    expires_time = expires_at
                
                if datetime.now() > expires_time:
                    # Expired, delete and return None
                    self.delete(key)
                    return None
            
            return data.get("value")
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair with optional TTL."""
        with self._lock:
            path = self._get_file_path(key)
            
            now = datetime.now()
            data = {
                "value": value,
                "created_at": now.isoformat(),
                "expires_at": None,
            }
            
            if ttl is not None and ttl > 0:
                from datetime import timedelta
                expires = now + timedelta(seconds=ttl)
                data["expires_at"] = expires.isoformat()
            
            return self._write_file(path, data)
    
    def delete(self, key: str) -> bool:
        """Delete a key."""
        with self._lock:
            path = self._get_file_path(key)
            try:
                path.unlink(missing_ok=True)
                return True
            except OSError:
                return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        with self._lock:
            value = self.get(key)
            return value is not None
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix filter."""
        with self._lock:
            self._ensure_directory()
            keys = []
            
            for file_path in self._data_dir.glob("*.yaml"):
                # Convert filename back to key
                key = file_path.stem
                
                # Check prefix
                if prefix and not key.startswith(prefix):
                    continue
                
                # Check if not expired
                data = self._read_file(file_path)
                if data is None:
                    continue
                
                expires_at = data.get("expires_at")
                if expires_at:
                    try:
                        if isinstance(expires_at, str):
                            expires_time = datetime.fromisoformat(expires_at)
                        else:
                            expires_time = expires_at
                        
                        if datetime.now() > expires_time:
                            # Expired, skip
                            continue
                    except (ValueError, TypeError):
                        continue
                
                keys.append(key)
            
            return sorted(keys)
    
    def batch_get(self, keys: List[str]) -> Dict[str, str]:
        """Get multiple values at once."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def batch_set(self, items: Dict[str, str], ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs at once."""
        all_success = True
        for key, value in items.items():
            if not self.set(key, value, ttl):
                all_success = False
        return all_success
    
    def close(self) -> None:
        """Close the storage (no-op for file-based)."""
        pass
    
    def ping(self) -> bool:
        """Check if storage directory is accessible."""
        try:
            self._ensure_directory()
            test_file = self._data_dir / ".health_check"
            test_file.touch()
            test_file.unlink()
            return True
        except OSError:
            return False
    
    def clear_all(self) -> int:
        """
        Clear all stored data.
        
        Returns:
            Number of keys deleted
        """
        with self._lock:
            keys = self.list_keys()
            for key in keys:
                self.delete(key)
            return len(keys)
