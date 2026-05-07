# Memory Layer - File Storage
"""
File-based Storage Backend

Simple file-based storage for memory persistence.
"""

import json
import os
from typing import Dict, Any, Optional, List
import threading
from datetime import datetime


class FileStorage:
    """
    File-based Storage Backend.
    
    Example:
        >>> storage = FileStorage(base_path="./data")
        >>> storage.write("key1", {"data": "value"})
        >>> data = storage.read("key1")
    """
    
    def __init__(
        self,
        base_path: str = "./memory_data",
        auto_flush: bool = True,
    ):
        """
        Initialize file storage.
        
        Args:
            base_path: Base directory for storage
            auto_flush: Whether to auto-flush writes
        """
        self._base_path = base_path
        self._auto_flush = auto_flush
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        
        # Ensure base path exists
        os.makedirs(base_path, exist_ok=True)
    
    def write(
        self,
        key: str,
        data: Any,
        file_path: Optional[str] = None,
    ) -> bool:
        """
        Write data to storage.
        
        Args:
            key: Storage key
            data: Data to store
            file_path: Custom file path (optional)
            
        Returns:
            True if successful
        """
        with self._lock:
            try:
                path = file_path or self._get_path(key)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self._cache[key] = data
                return True
            except Exception:
                return False
    
    def read(
        self,
        key: str,
        default: Any = None,
        file_path: Optional[str] = None,
    ) -> Any:
        """
        Read data from storage.
        
        Args:
            key: Storage key
            default: Default value if not found
            file_path: Custom file path (optional)
            
        Returns:
            Stored data or default
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]
        
        try:
            path = file_path or self._get_path(key)
            
            if not os.path.exists(path):
                return default
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._cache[key] = data
            return data
        except Exception:
            return default
    
    def delete(self, key: str) -> bool:
        """
        Delete data from storage.
        
        Args:
            key: Storage key
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            try:
                path = self._get_path(key)
                
                if os.path.exists(path):
                    os.remove(path)
                
                if key in self._cache:
                    del self._cache[key]
                
                return True
            except Exception:
                return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if key in self._cache:
            return True
        
        path = self._get_path(key)
        return os.path.exists(path)
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """
        List all keys with optional prefix filter.
        
        Args:
            prefix: Key prefix filter
            
        Returns:
            List of keys
        """
        keys = list(self._cache.keys())
        
        try:
            for filename in os.listdir(self._base_path):
                if filename.endswith('.json'):
                    key = filename[:-5]  # Remove .json
                    if prefix and not key.startswith(prefix):
                        continue
                    if key not in keys:
                        keys.append(key)
        except Exception:
            pass
        
        return keys
    
    def clear(self, prefix: str = "") -> int:
        """
        Clear storage.
        
        Args:
            prefix: Only clear keys with this prefix
            
        Returns:
            Number of keys cleared
        """
        with self._lock:
            keys = self.list_keys(prefix)
            count = 0
            
            for key in keys:
                if self.delete(key):
                    count += 1
            
            return count
    
    def _get_path(self, key: str) -> str:
        """Get file path for a key."""
        # Sanitize key for filesystem
        safe_key = key.replace('/', '_').replace('\\', '_')
        return os.path.join(self._base_path, f"{safe_key}.json")
    
    @property
    def base_path(self) -> str:
        """Get base path."""
        return self._base_path
