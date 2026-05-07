# Test Storage Module
"""
Tests for storage backends.
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from neshama.storage.base import StorageBackend
from neshama.storage.yaml_storage import YamlStorage
from neshama.storage.manager import StorageManager


class TestYamlStorage:
    """Tests for YAML storage backend."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as td:
            yield td
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create a YamlStorage instance for testing."""
        return YamlStorage(data_dir=temp_dir)
    
    def test_set_and_get(self, storage):
        """Test basic set and get operations."""
        assert storage.set("key1", "value1")
        assert storage.get("key1") == "value1"
    
    def test_get_nonexistent(self, storage):
        """Test getting a nonexistent key."""
        assert storage.get("nonexistent") is None
    
    def test_delete(self, storage):
        """Test deleting a key."""
        storage.set("key1", "value1")
        assert storage.get("key1") == "value1"
        
        assert storage.delete("key1")
        assert storage.get("key1") is None
    
    def test_delete_nonexistent(self, storage):
        """Test deleting a nonexistent key."""
        # unlink with missing_ok=True returns True, so we just verify no exception
        assert storage.delete("nonexistent") is True
    
    def test_exists(self, storage):
        """Test exists operation."""
        storage.set("key1", "value1")
        assert storage.exists("key1")
        assert not storage.exists("key2")
    
    def test_ttl(self, storage):
        """Test TTL functionality."""
        storage.set("key1", "value1", ttl=1)
        assert storage.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert storage.get("key1") is None
    
    def test_list_keys(self, storage):
        """Test listing keys."""
        storage.set("key1", "value1")
        storage.set("key2", "value2")
        storage.set("prefix_key1", "value3")
        
        keys = storage.list_keys()
        assert set(keys) == {"key1", "key2", "prefix_key1"}
        
        prefixed = storage.list_keys("prefix")
        assert prefixed == ["prefix_key1"]
    
    def test_batch_set_and_get(self, storage):
        """Test batch operations."""
        items = {
            "batch1": "value1",
            "batch2": "value2",
            "batch3": "value3",
        }
        
        assert storage.batch_set(items)
        
        result = storage.batch_get(["batch1", "batch2", "nonexistent"])
        assert result == {"batch1": "value1", "batch2": "value2"}
    
    def test_ping(self, storage):
        """Test ping functionality."""
        assert storage.ping()
    
    def test_close(self, storage):
        """Test close operation."""
        storage.close()  # Should not raise


class TestStorageManager:
    """Tests for StorageManager."""
    
    def test_yaml_backend_default(self):
        """Test default YAML backend."""
        StorageManager.reset_instance()
        manager = StorageManager.get_instance()
        
        # Should default to YAML
        assert manager.backend_type == "yaml"
        
        StorageManager.reset_instance()
    
    def test_explicit_yaml_backend(self):
        """Test explicit YAML backend selection."""
        os.environ["NESHAMA_STORAGE_BACKEND"] = "yaml"
        StorageManager.reset_instance()
        
        manager = StorageManager.get_instance()
        assert manager.backend_type == "yaml"
        
        StorageManager.reset_instance()
        del os.environ["NESHAMA_STORAGE_BACKEND"]
    
    def test_redis_fallback_to_yaml(self):
        """Test Redis fallback to YAML when unavailable."""
        os.environ["NESHAMA_STORAGE_BACKEND"] = "redis"
        StorageManager.reset_instance()
        
        manager = StorageManager.get_instance()
        # Should fall back to YAML when Redis unavailable
        assert manager.backend_type == "yaml"
        
        StorageManager.reset_instance()
        del os.environ["NESHAMA_STORAGE_BACKEND"]
    
    def test_redis_backend_with_mock(self):
        """Test Redis backend with mock."""
        os.environ["NESHAMA_STORAGE_BACKEND"] = "redis"
        os.environ["NESHAMA_REDIS_HOST"] = "localhost"
        
        StorageManager.reset_instance()
        
        # This should fail to connect and fall back
        manager = StorageManager.get_instance()
        
        StorageManager.reset_instance()
        del os.environ["NESHAMA_STORAGE_BACKEND"]
        del os.environ["NESHAMA_REDIS_HOST"]
    
    def test_basic_operations(self):
        """Test basic storage operations."""
        StorageManager.reset_instance()
        
        manager = StorageManager.get_instance()
        
        # Basic operations
        manager.set("test_key", "test_value")
        assert manager.get("test_key") == "test_value"
        assert manager.exists("test_key")
        manager.delete("test_key")
        assert not manager.exists("test_key")
        
        StorageManager.reset_instance()
    
    def test_health_check(self):
        """Test health check."""
        StorageManager.reset_instance()
        
        manager = StorageManager.get_instance()
        assert manager.health_check()
        
        StorageManager.reset_instance()


class TestStorageBackendInterface:
    """Tests to verify StorageBackend interface compliance."""
    
    def test_yaml_storage_implements_interface(self):
        """Verify YamlStorage implements StorageBackend."""
        with tempfile.TemporaryDirectory() as td:
            storage = YamlStorage(data_dir=td)
            
            # Verify all required methods exist
            assert hasattr(storage, 'get')
            assert hasattr(storage, 'set')
            assert hasattr(storage, 'delete')
            assert hasattr(storage, 'exists')
            assert hasattr(storage, 'list_keys')
            assert hasattr(storage, 'batch_get')
            assert hasattr(storage, 'batch_set')
            assert hasattr(storage, 'close')
            assert hasattr(storage, 'health_check')
            assert hasattr(storage, 'ping')
    
    def test_yaml_storage_is_storage_backend(self):
        """Verify YamlStorage is a StorageBackend."""
        with tempfile.TemporaryDirectory() as td:
            storage = YamlStorage(data_dir=td)
            assert isinstance(storage, StorageBackend)
