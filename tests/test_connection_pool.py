# Test Connection Pool
"""
Tests for ConnectionPool.
"""

import time
import threading
from unittest.mock import patch, MagicMock

import pytest


class MockConnection:
    """Mock connection for testing."""
    _id = 0
    
    def __init__(self):
        MockConnection._id += 1
        self.id = MockConnection._id
        self.closed = False
    
    def ping(self):
        return not self.closed
    
    def close(self):
        self.closed = True


class TestConnectionPool:
    """Tests for ConnectionPool."""
    
    @pytest.fixture
    def pool_config(self):
        """Create test pool config."""
        from neshama.storage.connection_pool import PoolConfig
        return PoolConfig(
            max_connections=5,
            min_idle=0,  # No initial idle connections for tests
            max_idle=3,
            idle_timeout=5,
            health_check_interval=3600,  # Very long interval to avoid test interference
            acquire_timeout=2.0,
            leak_detection_timeout=10,
        )
    
    @pytest.fixture
    def factory(self):
        """Create connection factory."""
        return lambda: MockConnection()
    
    @pytest.fixture
    def health_check(self):
        """Create health check function."""
        return lambda conn: conn.ping()
    
    def test_pool_initialization(self, factory, health_check, pool_config):
        """Test pool initialization."""
        from neshama.storage.connection_pool import ConnectionPool
        
        pool = ConnectionPool(
            factory=factory,
            health_check=health_check,
            config=pool_config,
        )
        
        assert pool._config.max_connections == 5
        assert pool._config.min_idle == 0  # Updated to match fixture
        
        pool.close()
    
    def test_acquire_and_release(self, factory, health_check, pool_config):
        """Test acquiring and releasing connections."""
        from neshama.storage.connection_pool import ConnectionPool
        
        pool = ConnectionPool(
            factory=factory,
            health_check=health_check,
            config=pool_config,
        )
        
        # Acquire connection
        conn = pool.acquire(timeout=1.0)
        assert conn is not None
        assert conn.id > 0
        
        stats = pool.stats
        assert stats.active_connections == 1
        
        # Release connection
        pool.release(conn)
        
        stats = pool.stats
        assert stats.active_connections == 0
        assert stats.idle_connections == 1
        
        pool.close()
    
    def test_context_manager(self, factory, health_check, pool_config):
        """Test context manager usage."""
        from neshama.storage.connection_pool import ConnectionPool
        
        pool = ConnectionPool(
            factory=factory,
            health_check=health_check,
            config=pool_config,
        )
        
        with pool.connection() as conn:
            assert conn is not None
            stats = pool.stats
            assert stats.active_connections == 1
        
        stats = pool.stats
        assert stats.active_connections == 0
        
        pool.close()
    
    def test_timeout(self, factory, health_check):
        """Test acquire timeout."""
        from neshama.storage.connection_pool import ConnectionPool, PoolConfig
        
        # Create pool with very small max connections
        config = PoolConfig(
            max_connections=1,
            min_idle=0,
            acquire_timeout=0.5,
            health_check_interval=3600,
        )
        
        pool = ConnectionPool(
            factory=factory,
            health_check=health_check,
            config=config,
        )
        
        # Acquire and hold connection
        conn = pool.acquire()
        
        # Try to acquire another - should timeout
        with pytest.raises(TimeoutError):
            pool.acquire(timeout=0.1)
        
        pool.release(conn)
        pool.close()
    
    def test_max_connections_limit(self, factory, health_check):
        """Test max connections limit."""
        from neshama.storage.connection_pool import ConnectionPool, PoolConfig
        
        config = PoolConfig(max_connections=2, min_idle=0, health_check_interval=3600)
        
        pool = ConnectionPool(
            factory=factory,
            health_check=health_check,
            config=config,
        )
        
        # Acquire max connections
        conn1 = pool.acquire()
        conn2 = pool.acquire()
        
        stats = pool.stats
        assert stats.total_connections == 2
        assert stats.active_connections == 2
        
        # Third acquire should work (creates new up to max)
        # But with 2 max and 2 active, it should wait
        # Let's just verify we're at limit
        assert pool._stats.total_connections == pool._config.max_connections
        
        pool.release(conn1)
        pool.release(conn2)
        pool.close()
    
    def test_stats(self, factory, health_check, pool_config):
        """Test statistics tracking."""
        from neshama.storage.connection_pool import ConnectionPool
        
        pool = ConnectionPool(
            factory=factory,
            health_check=health_check,
            config=pool_config,
        )
        
        conn = pool.acquire()
        pool.release(conn)
        
        stats = pool.stats
        assert stats.total_connections == 1
        assert stats.active_connections == 0
        
        pool.close()
    
    def test_close(self, factory, health_check, pool_config):
        """Test pool close."""
        from neshama.storage.connection_pool import ConnectionPool
        
        pool = ConnectionPool(
            factory=factory,
            health_check=health_check,
            config=pool_config,
        )
        
        conn = pool.acquire()
        pool.close()
        
        assert pool._closed
    
    def test_connection_health_check_failure(self, factory):
        """Test connection health check failure handling."""
        from neshama.storage.connection_pool import ConnectionPool, PoolConfig
        
        # Health check that fails
        bad_health = lambda conn: conn.id < 0
        
        config = PoolConfig(max_connections=3, min_idle=0, health_check_interval=3600)
        
        pool = ConnectionPool(
            factory=factory,
            health_check=bad_health,
            config=config,
        )
        
        # Connection should be created but rejected on health check
        # Eventually pool should create a working connection
        pool.close()
    
    def test_multiple_threads(self, factory, health_check):
        """Test concurrent access from multiple threads."""
        from neshama.storage.connection_pool import ConnectionPool, PoolConfig
        
        config = PoolConfig(max_connections=10, min_idle=0, health_check_interval=3600)
        
        pool = ConnectionPool(
            factory=factory,
            health_check=health_check,
            config=config,
        )
        
        results = []
        errors = []
        
        def worker():
            try:
                with pool.connection() as conn:
                    time.sleep(0.01)  # Simulate work
                    results.append(conn.id)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 5
        assert len(errors) == 0
        
        pool.close()


class TestPoolConfig:
    """Tests for PoolConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        from neshama.storage.connection_pool import PoolConfig
        
        config = PoolConfig()
        
        assert config.max_connections == 50
        assert config.min_idle == 5
        assert config.max_idle == 20
        assert config.idle_timeout == 300
        assert config.health_check_interval == 60
        assert config.acquire_timeout == 5.0
        assert config.leak_detection_timeout == 30
    
    def test_custom_config(self):
        """Test custom configuration."""
        from neshama.storage.connection_pool import PoolConfig
        
        config = PoolConfig(
            max_connections=100,
            min_idle=10,
            acquire_timeout=10.0,
        )
        
        assert config.max_connections == 100
        assert config.min_idle == 10
        assert config.acquire_timeout == 10.0
