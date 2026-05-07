# Connection Pool
"""
Generic connection pool implementation.

Provides a reusable connection pool for various backends:
- Database connections
- Redis connections
- HTTP clients
- Any resource that supports acquire/release pattern
"""

import threading
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, TypeVar
from queue import Queue, Empty, Full
from contextlib import contextmanager

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class PoolConfig:
    """Connection pool configuration."""
    max_connections: int = 50
    min_idle: int = 5
    max_idle: int = 20
    idle_timeout: int = 300  # seconds
    health_check_interval: int = 60  # seconds
    acquire_timeout: float = 5.0  # seconds
    leak_detection_timeout: int = 30  # seconds


@dataclass
class PoolStats:
    """Connection pool statistics."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    wait_count: int = 0
    timeout_count: int = 0
    leak_warnings: int = 0
    health_check_failures: int = 0


@dataclass
class PooledConnection(Generic[T]):
    """A pooled connection wrapper."""
    connection: T
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    use_count: int = 0
    _leak_warned: bool = False
    
    def mark_used(self):
        """Mark the connection as used."""
        self.last_used_at = time.time()
        self.use_count += 1
    
    def is_leaked(self, timeout: int) -> bool:
        """Check if connection has been held too long."""
        if self._leak_warned:
            return False
        elapsed = time.time() - self.created_at
        return elapsed > timeout


class ConnectionPool(Generic[T]):
    """
    Generic connection pool.
    
    Features:
    - Configurable pool size
    - Idle connection management
    - Health checks
    - Connection leak detection
    - Thread-safe operations
    
    Example:
        >>> def factory():
        ...     return create_connection()
        ...
        >>> def health_check(conn):
        ...     return conn.is_healthy()
        ...
        >>> pool = ConnectionPool(factory, health_check)
        >>> 
        >>> with pool.acquire() as conn:
        ...     conn.query("SELECT 1")
        >>> 
        >>> pool.close()
    """
    
    def __init__(
        self,
        factory: Callable[[], T],
        health_check: Optional[Callable[[T], bool]] = None,
        config: Optional[PoolConfig] = None,
    ):
        """
        Initialize connection pool.
        
        Args:
            factory: Function to create new connections
            health_check: Function to check connection health
            config: Pool configuration
        """
        self._factory = factory
        self._health_check = health_check
        self._config = config or PoolConfig()
        
        self._pool: Queue[Optional[PooledConnection[T]]] = Queue(
            maxsize=self._config.max_connections
        )
        self._all_connections: list[PooledConnection[T]] = []
        self._lock = threading.RLock()  # Use RLock for reentrant locking
        
        self._stats = PoolStats()
        self._closed = False
        
        # Start health check thread
        self._health_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True,
            name="ConnectionPool-HealthCheck"
        )
        self._health_thread.start()
        
        # Initialize minimum idle connections
        self._initialize_idle()
    
    def _initialize_idle(self) -> None:
        """Create initial idle connections."""
        for _ in range(self._config.min_idle):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
    
    def _create_connection(self) -> Optional[PooledConnection[T]]:
        """Create a new pooled connection."""
        try:
            conn = self._factory()
            pooled = PooledConnection(connection=conn)
            
            with self._lock:
                self._all_connections.append(pooled)
                self._stats.total_connections += 1
            
            logger.debug(f"Created new connection (total: {self._stats.total_connections})")
            return pooled
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None
    
    def acquire(self, timeout: Optional[float] = None) -> T:
        """
        Acquire a connection from the pool.
        
        Args:
            timeout: Maximum time to wait for a connection
            
        Returns:
            A connection from the pool
            
        Raises:
            TimeoutError: If no connection available within timeout
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        timeout = timeout or self._config.acquire_timeout
        deadline = time.time() + timeout
        
        while True:
            # Check if we can get from pool
            remaining = deadline - time.time()
            if remaining <= 0:
                self._stats.timeout_count += 1
                raise TimeoutError(
                    f"Could not acquire connection within {timeout}s "
                    f"(waited {self._stats.wait_count} times)"
                )
            
            try:
                pooled = self._pool.get(timeout=min(remaining, 0.1))
                self._stats.wait_count += 1
                
                # Check if connection is healthy
                if self._health_check:
                    try:
                        if not self._health_check(pooled.connection):
                            logger.warning("Connection failed health check, creating new one")
                            self._dispose_connection(pooled)
                            pooled = self._create_connection()
                            if pooled is None:
                                continue
                    except Exception as e:
                        logger.warning(f"Health check error: {e}")
                        self._dispose_connection(pooled)
                        pooled = self._create_connection()
                        if pooled is None:
                            continue
                
                # Check for leaks
                if pooled.is_leaked(self._config.leak_detection_timeout):
                    logger.warning(
                        f"Connection held for {time.time() - pooled.created_at:.1f}s "
                        f"(may indicate a leak)"
                    )
                    pooled._leak_warned = True
                    self._stats.leak_warnings += 1
                
                pooled.mark_used()
                self._stats.active_connections += 1
                self._stats.idle_connections -= 1
                
                return pooled.connection
                
            except Empty:
                # Pool empty, try to create new if under limit
                with self._lock:
                    if self._stats.total_connections < self._config.max_connections:
                        pooled = self._create_connection()
                        if pooled:
                            self._stats.active_connections += 1
                            return pooled.connection
                
                # No connection available, sleep briefly and retry
                time.sleep(0.05)
                
                # No connections available, keep waiting
                continue
    
    @contextmanager
    def connection(self):
        """
        Context manager for acquiring connections.
        
        Example:
            with pool.connection() as conn:
                conn.query("SELECT 1")
        """
        conn = self.acquire()
        try:
            yield conn
        finally:
            self.release(conn)
    
    def release(self, connection: T) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection: The connection to release
        """
        if self._closed:
            self._dispose_connection_by_conn(connection)
            return
        
        # Find the pooled connection wrapper
        pooled = None
        with self._lock:
            for p in self._all_connections:
                if p.connection is connection:
                    pooled = p
                    break
        
        if pooled is None:
            logger.warning("Released unknown connection, disposing")
            return
        
        # Check if should be disposed
        if pooled.is_leaked(self._config.leak_detection_timeout * 2):
            logger.info("Disposing leaked connection")
            self._dispose_connection(pooled)
            return
        
        pooled.mark_used()
        self._stats.active_connections -= 1
        self._stats.idle_connections += 1
        
        try:
            self._pool.put_nowait(pooled)
        except Full:
            logger.warning("Pool full, disposing connection")
            self._dispose_connection(pooled)
    
    def _dispose_connection(self, pooled: PooledConnection[T]) -> None:
        """Dispose of a pooled connection."""
        try:
            if hasattr(pooled.connection, 'close'):
                pooled.connection.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
        
        with self._lock:
            if pooled in self._all_connections:
                self._all_connections.remove(pooled)
            self._stats.total_connections -= 1
    
    def _dispose_connection_by_conn(self, connection: T) -> None:
        """Dispose a connection by its raw connection object."""
        with self._lock:
            for pooled in self._all_connections:
                if pooled.connection is connection:
                    self._dispose_connection(pooled)
                    return
    
    def _health_check_loop(self) -> None:
        """Background health check loop."""
        while not self._closed:
            time.sleep(self._config.health_check_interval)
            
            if self._closed:
                break
            
            self._perform_health_check()
    
    def _perform_health_check(self) -> None:
        """Perform health check on idle connections."""
        connections_to_check = []
        
        # Collect idle connections
        while True:
            try:
                pooled = self._pool.get_nowait()
                connections_to_check.append(pooled)
            except Empty:
                break
        
        healthy = []
        unhealthy = 0
        
        for pooled in connections_to_check:
            # Check if connection is too old
            idle_time = time.time() - pooled.last_used_at
            if idle_time > self._config.idle_timeout:
                if self._stats.idle_connections > self._config.min_idle:
                    unhealthy += 1
                    self._dispose_connection(pooled)
                    continue
            
            # Run health check if provided
            if self._health_check:
                try:
                    if self._health_check(pooled.connection):
                        healthy.append(pooled)
                    else:
                        unhealthy += 1
                        self._dispose_connection(pooled)
                except Exception as e:
                    logger.warning(f"Health check failed: {e}")
                    unhealthy += 1
                    self._dispose_connection(pooled)
            else:
                healthy.append(pooled)
        
        # Return healthy connections to pool
        for pooled in healthy:
            try:
                self._pool.put_nowait(pooled)
            except Full:
                self._dispose_connection(pooled)
        
        if unhealthy > 0:
            self._stats.health_check_failures += unhealthy
            logger.info(f"Health check: disposed {unhealthy} unhealthy connections")
        
        # Update idle count
        with self._lock:
            self._stats.idle_connections = len(healthy)
    
    @property
    def stats(self) -> PoolStats:
        """Get pool statistics."""
        with self._lock:
            self._stats.idle_connections = self._pool.qsize()
            return PoolStats(
                total_connections=self._stats.total_connections,
                active_connections=self._stats.active_connections,
                idle_connections=self._stats.idle_connections,
                wait_count=self._stats.wait_count,
                timeout_count=self._stats.timeout_count,
                leak_warnings=self._stats.leak_warnings,
                health_check_failures=self._stats.health_check_failures,
            )
    
    def close(self) -> None:
        """Close the connection pool."""
        self._closed = True
        
        # Dispose all connections
        with self._lock:
            for pooled in self._all_connections[:]:
                self._dispose_connection(pooled)
            self._all_connections.clear()
        
        logger.info("Connection pool closed")
    
    def resize(self, max_connections: int) -> None:
        """
        Resize the pool.
        
        Args:
            max_connections: New maximum connections
        """
        self._config.max_connections = max_connections
        
        # Drain excess connections
        while self._pool.qsize() > max_connections:
            try:
                pooled = self._pool.get_nowait()
                self._dispose_connection(pooled)
            except Empty:
                break
        
        logger.info(f"Pool resized to max_connections={max_connections}")
