# Storage Backend - Abstract Interface
"""
Abstract storage interface for Neshama.

Provides a unified API for data storage:
- YAML file backend (development)
- Redis backend (production)

This abstraction allows seamless switching between backends
based on environment configuration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageBackend(ABC):
    """
    Abstract storage backend interface.
    
    All storage implementations must inherit from this class
    and implement the following methods.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Get a value by key.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The value if found, None otherwise
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Set a key-value pair.
        
        Args:
            key: The key
            value: The value to store
            ttl: Optional time-to-live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a key.
        
        Args:
            key: The key to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: The key to check
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """
        List all keys with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of matching keys
        """
        pass
    
    @abstractmethod
    def batch_get(self, keys: List[str]) -> Dict[str, str]:
        """
        Get multiple values at once.
        
        Args:
            keys: List of keys to retrieve
            
        Returns:
            Dictionary of key-value pairs for found keys
        """
        pass
    
    @abstractmethod
    def batch_set(self, items: Dict[str, str], ttl: Optional[int] = None) -> bool:
        """
        Set multiple key-value pairs at once.
        
        Args:
            items: Dictionary of key-value pairs
            ttl: Optional time-to-live in seconds
            
        Returns:
            True if all successful, False otherwise
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the storage connection."""
        pass
    
    def health_check(self) -> bool:
        """
        Check if the storage backend is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            return self.ping()
        except Exception:
            return False
    
    @abstractmethod
    def ping(self) -> bool:
        """
        Ping the storage backend to check connectivity.
        
        Returns:
            True if reachable, False otherwise
        """
        pass
