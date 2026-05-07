# Redis Storage Backend
"""
Redis-based storage implementation.

Stores data in Redis with connection pooling.
Suitable for production deployments.
"""

import logging
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from .base import StorageBackend

logger = logging.getLogger(__name__)


class RedisStorage(StorageBackend):
    """
    Redis storage backend.
    
    Features:
    - Connection pooling (max_connections=50)
    - Automatic reconnection
    - TTL support
    - Pipeline for batch operations
    - Thread-safe
    
    Requires redis-py package.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ssl: bool = False,
        max_connections: int = 50,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        socket_keepalive: bool = True,
        retry_on_timeout: bool = True,
    ):
        """
        Initialize Redis storage.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
            ssl: Use SSL connection
            max_connections: Maximum connections in pool
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout
            socket_keepalive: Enable TCP keepalive
            retry_on_timeout: Retry on timeout errors
        """
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._max_connections = max_connections
        self._socket_timeout = socket_timeout
        self._socket_connect_timeout = socket_connect_timeout
        self._socket_keepalive = socket_keepalive
        self._retry_on_timeout = retry_on_timeout
        
        self._pool = None
        self._client = None
        self._connect()
    
    def _connect(self) -> None:
        """Create connection pool and Redis client."""
        try:
            import redis
        except ImportError:
            raise ImportError(
                "redis package is required for RedisStorage. "
                "Install with: pip install redis"
            )
        
        self._pool = redis.ConnectionPool(
            host=self._host,
            port=self._port,
            db=self._db,
            password=self._password,
            ssl=self._ssl,
            max_connections=self._max_connections,
            socket_timeout=self._socket_timeout,
            socket_connect_timeout=self._socket_connect_timeout,
            socket_keepalive=self._socket_keepalive,
            retry_on_timeout=self._retry_on_timeout,
            decode_responses=True,
        )
        
        self._client = redis.Redis(connection_pool=self._pool)
        
        # Test connection
        self._client.ping()
        logger.info(
            f"Redis connected: {self._host}:{self._port}/{self._db}"
        )
    
    def _ensure_connection(self) -> None:
        """Ensure Redis connection is active, reconnect if needed."""
        try:
            self._client.ping()
        except Exception as e:
            logger.warning(f"Redis connection lost, reconnecting: {e}")
            self._connect()
    
    def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        self._ensure_connection()
        try:
            value = self._client.get(key)
            return value
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair with optional TTL."""
        self._ensure_connection()
        try:
            if ttl is not None and ttl > 0:
                return self._client.setex(key, ttl, value)
            else:
                return self._client.set(key, value)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key."""
        self._ensure_connection()
        try:
            return self._client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        self._ensure_connection()
        try:
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix filter."""
        self._ensure_connection()
        try:
            if prefix:
                pattern = f"{prefix}*"
            else:
                pattern = "*"
            
            # Use SCAN for production-safe iteration
            keys = []
            cursor = 0
            while True:
                cursor, batch = self._client.scan(cursor, match=pattern, count=100)
                keys.extend(batch)
                if cursor == 0:
                    break
            
            return sorted(keys)
        except Exception as e:
            logger.error(f"Redis list_keys error: {e}")
            return []
    
    def batch_get(self, keys: List[str]) -> Dict[str, str]:
        """Get multiple values at once using pipeline."""
        self._ensure_connection()
        if not keys:
            return {}
        
        try:
            pipe = self._client.pipeline()
            for key in keys:
                pipe.get(key)
            
            results = pipe.execute()
            
            return {
                key: value
                for key, value in zip(keys, results)
                if value is not None
            }
        except Exception as e:
            logger.error(f"Redis batch_get error: {e}")
            return {}
    
    def batch_set(self, items: Dict[str, str], ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs at once using pipeline."""
        self._ensure_connection()
        if not items:
            return True
        
        try:
            pipe = self._client.pipeline()
            
            for key, value in items.items():
                if ttl is not None and ttl > 0:
                    pipe.setex(key, ttl, value)
                else:
                    pipe.set(key, value)
            
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis batch_set error: {e}")
            return False
    
    def close(self) -> None:
        """Close the Redis connection pool."""
        if self._pool:
            self._pool.disconnect()
            self._pool = None
            self._client = None
            logger.info("Redis connection closed")
    
    def ping(self) -> bool:
        """Check if Redis is reachable."""
        try:
            self._ensure_connection()
            return self._client.ping()
        except Exception:
            return False
    
    @contextmanager
    def pipeline(self):
        """
        Context manager for Redis pipeline.
        
        Example:
            with storage.pipeline() as pipe:
                pipe.set("key1", "value1")
                pipe.set("key2", "value2")
                results = pipe.execute()
        """
        self._ensure_connection()
        pipe = self._client.pipeline()
        try:
            yield pipe
        finally:
            pipe.reset()
    
    def get_info(self) -> Dict[str, Any]:
        """Get Redis server info."""
        self._ensure_connection()
        try:
            return self._client.info()
        except Exception as e:
            logger.error(f"Redis info error: {e}")
            return {}
    
    @property
    def connection_count(self) -> int:
        """Get current number of connections in pool."""
        if self._pool:
            return len(self._pool._in_use_connections) + len(self._pool._available_connections)
        return 0
