# Test Storage Backend Factory
"""
Tests for storage backend factory.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest


class TestCreateStorageBackend:
    """Tests for create_storage_backend function."""
    
    def test_create_yaml_backend_default(self):
        """Test creating YAML backend by default."""
        from neshama.storage.backend import create_storage_backend, BACKEND_YAML
        
        with tempfile.TemporaryDirectory() as td:
            backend = create_storage_backend(data_dir=td)
            
            assert backend is not None
            assert hasattr(backend, 'get')
            assert hasattr(backend, 'set')
            assert hasattr(backend, 'close')
            
            backend.close()
    
    def test_create_yaml_backend_explicit(self):
        """Test creating YAML backend explicitly."""
        from neshama.storage.backend import create_storage_backend
        
        with tempfile.TemporaryDirectory() as td:
            backend = create_storage_backend("yaml", data_dir=td)
            
            assert backend is not None
            
            backend.close()
    
    def test_create_redis_backend_url(self):
        """Test creating Redis backend with URL."""
        from neshama.storage.backend import create_storage_backend
        
        # This will fail to connect but that's expected without Redis
        with patch.dict(os.environ, {
            "NESHAMA_REDIS_URL": "redis://localhost:6379/0"
        }):
            with pytest.raises(Exception):
                # Redis connection should fail
                create_storage_backend("redis")
    
    def test_create_invalid_backend(self):
        """Test creating invalid backend type."""
        from neshama.storage.backend import create_storage_backend
        
        with pytest.raises(ValueError) as exc_info:
            create_storage_backend("invalid")
        
        assert "Unknown storage backend type" in str(exc_info.value)
    
    def test_create_from_env_variable(self):
        """Test creating backend from environment variable."""
        from neshama.storage.backend import create_storage_backend
        
        with patch.dict(os.environ, {"NESHAMA_STORAGE_BACKEND": "yaml"}):
            with tempfile.TemporaryDirectory() as td:
                # Clear cached storage
                from neshama.storage import StorageManager
                StorageManager.reset_instance()
                
                backend = create_storage_backend(data_dir=td)
                assert backend is not None
                
                backend.close()


class TestBackendAvailability:
    """Tests for backend availability checks."""
    
    def test_yaml_backend_always_available(self):
        """Test that YAML backend is always available."""
        from neshama.storage.backend import is_backend_available, BACKEND_YAML
        
        assert is_backend_available(BACKEND_YAML) is True
    
    def test_redis_backend_availability(self):
        """Test Redis backend availability."""
        from neshama.storage.backend import is_backend_available, BACKEND_REDIS
        
        result = is_backend_available(BACKEND_REDIS)
        # Should be True if redis package is installed
        assert isinstance(result, bool)
    
    def test_invalid_backend_availability(self):
        """Test invalid backend availability."""
        from neshama.storage.backend import is_backend_available
        
        assert is_backend_available("invalid") is False


class TestGetAvailableBackends:
    """Tests for get_available_backends function."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        from neshama.storage.backend import get_available_backends
        
        backends = get_available_backends()
        
        assert isinstance(backends, list)
        assert len(backends) >= 1  # At least YAML should be available
        assert "yaml" in backends


class TestRedisURLParsing:
    """Tests for Redis URL parsing."""
    
    def test_parse_standard_url(self):
        """Test parsing standard Redis URL."""
        from neshama.storage.backend import _parse_redis_url
        
        config = _parse_redis_url("redis://localhost:6379/0")
        
        assert config["host"] == "localhost"
        assert config["port"] == 6379
        assert config["db"] == 0
        assert config["password"] is None
        assert config["ssl"] is False
    
    def test_parse_url_with_password(self):
        """Test parsing Redis URL with password."""
        from neshama.storage.backend import _parse_redis_url
        
        # Test format: redis://:password@host:port/db
        config = _parse_redis_url("redis://:mypassword@localhost:6379/0")
        
        assert config["host"] == "localhost"
        assert config["port"] == 6379
        assert config["password"] == "mypassword"
    
    def test_parse_url_with_password_in_username(self):
        """Test parsing Redis URL with password in username field."""
        from neshama.storage.backend import _parse_redis_url
        
        # Some tools use this format: redis://password@host:port/db
        config = _parse_redis_url("redis://mypassword@localhost:6379/0")
        
        assert config["host"] == "localhost"
        assert config["port"] == 6379
        assert config["password"] == "mypassword"
    
    def test_parse_rediss_url(self):
        """Test parsing Redis SSL URL."""
        from neshama.storage.backend import _parse_redis_url
        
        config = _parse_redis_url("rediss://localhost:6379/0")
        
        assert config["ssl"] is True
    
    def test_parse_invalid_url(self):
        """Test parsing invalid URL."""
        from neshama.storage.backend import _parse_redis_url
        
        # Should return defaults on error
        config = _parse_redis_url("not-a-url")
        
        assert config["host"] == "localhost"
        assert config["port"] == 6379
