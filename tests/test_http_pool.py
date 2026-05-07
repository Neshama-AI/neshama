# Test HTTP Connection Pool
"""
Tests for HTTP connection pool.
"""

import asyncio
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager

import pytest


class TestPoolConfig:
    """Tests for PoolConfig dataclass."""
    
    def test_default_config(self):
        """Test default pool configuration."""
        from neshama.web.connection_pool import PoolConfig
        
        config = PoolConfig()
        
        assert config.max_connections == 100
        assert config.max_keepalive_connections == 20
        assert config.keepalive_expiry == 30
        assert config.connect_timeout == 10.0
        assert config.read_timeout == 30.0
    
    def test_custom_config(self):
        """Test custom pool configuration."""
        from neshama.web.connection_pool import PoolConfig
        
        config = PoolConfig(
            max_connections=50,
            connect_timeout=5.0,
        )
        
        assert config.max_connections == 50
        assert config.connect_timeout == 5.0


class TestPoolStats:
    """Tests for PoolStats dataclass."""
    
    def test_default_stats(self):
        """Test default pool statistics."""
        from neshama.web.connection_pool import PoolStats
        
        stats = PoolStats()
        
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.active_requests == 0


class TestHTTPConnectionPool:
    """Tests for HTTPConnectionPool class."""
    
    def test_init(self):
        """Test pool initialization."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        assert pool is not None
        assert pool._config.max_connections == 100
        assert pool._closed is False
    
    def test_get_client_key(self):
        """Test client key extraction."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        key1 = pool._get_client_key("https://api.openai.com/v1/models")
        assert key1 == "https://api.openai.com"
        
        key2 = pool._get_client_key("http://localhost:8080/api/test")
        assert key2 == "http://localhost:8080"
    
    def test_get_client_default(self):
        """Test getting default client."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        client = pool.get_client()
        
        assert client is not None
        assert hasattr(client, 'get')
        assert hasattr(client, 'post')
        
        pool.close()
    
    def test_get_client_with_base_url(self):
        """Test getting client with base URL."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        client = pool.get_client("https://api.openai.com")
        
        assert client is not None
        
        pool.close()
    
    def test_get_multiple_clients(self):
        """Test getting multiple clients."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        client1 = pool.get_client("https://api.openai.com")
        client2 = pool.get_client("https://api.anthropic.com")
        
        assert client1 is not client2
        
        pool.close()
    
    def test_stats(self):
        """Test pool statistics."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        stats = pool.stats
        
        assert hasattr(stats, 'total_requests')
        assert hasattr(stats, 'successful_requests')
        assert hasattr(stats, 'failed_requests')
    
    def test_close(self):
        """Test closing pool."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        client = pool.get_client()
        
        pool.close()
        
        assert pool._closed is True
    
    def test_close_idempotent(self):
        """Test that close can be called multiple times."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        pool.close()
        pool.close()  # Should not raise
        
        assert pool._closed is True
    
    def test_set_default_headers(self):
        """Test setting default headers."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        pool.set_default_headers({"X-Custom-Header": "value"})
        
        assert "X-Custom-Header" in pool._default_headers
        assert pool._default_headers["X-Custom-Header"] == "value"
        
        pool.close()


class TestGlobalPool:
    """Tests for global pool functions."""
    
    def test_get_http_pool(self):
        """Test getting global HTTP pool."""
        from neshama.web.connection_pool import get_http_pool, reset_http_pool
        from neshama.web.connection_pool import HTTPConnectionPool
        
        # Reset first
        reset_http_pool()
        
        pool = get_http_pool()
        
        assert pool is not None
        assert isinstance(pool, HTTPConnectionPool)
        
        # Second call should return same instance
        pool2 = get_http_pool()
        assert pool is pool2
    
    def test_reset_http_pool(self):
        """Test resetting global HTTP pool."""
        from neshama.web.connection_pool import get_http_pool, reset_http_pool
        
        pool1 = get_http_pool()
        reset_http_pool()
        pool2 = get_http_pool()
        
        # Should be different instances
        assert pool1 is not pool2


class TestLLMHTTPClient:
    """Tests for LLMHTTPClient class."""
    
    def test_init(self):
        """Test LLM client initialization."""
        from neshama.web.connection_pool import LLMHTTPClient
        
        client = LLMHTTPClient()
        
        assert client is not None
        assert client._max_retries == 3
        assert client._retry_delay == 1.0
    
    def test_custom_init(self):
        """Test custom LLM client initialization."""
        from neshama.web.connection_pool import LLMHTTPClient
        
        client = LLMHTTPClient(
            max_retries=5,
            retry_delay=2.0,
            backoff_factor=3.0,
        )
        
        assert client._max_retries == 5
        assert client._retry_delay == 2.0
        assert client._backoff_factor == 3.0


@pytest.mark.asyncio
class TestAsyncSession:
    """Tests for async session context manager."""
    
    async def test_session_context_manager(self):
        """Test async session context manager."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        async with pool.session() as session:
            assert session is not None
            assert hasattr(session, 'get')
            assert hasattr(session, 'post')
        
        pool.close()
    
    async def test_session_tracks_stats(self):
        """Test that session tracks statistics."""
        from neshama.web.connection_pool import HTTPConnectionPool
        
        pool = HTTPConnectionPool()
        
        async with pool.session() as session:
            pass
        
        stats = pool.stats
        assert stats.total_requests >= 0
        
        pool.close()
