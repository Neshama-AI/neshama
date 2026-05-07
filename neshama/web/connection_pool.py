# HTTP Connection Pool
"""
HTTP connection pool for LLM API calls.

Provides connection pooling and reuse for HTTP clients:
- LLM provider API calls (OpenAI, Anthropic, etc.)
- Reusable connections
- Connection limits
- Keep-alive support

Usage:
    from neshama.web.connection_pool import HTTPConnectionPool, get_http_pool
    
    pool = get_http_pool()
    async with pool.get_session() as session:
        async with session.get(url) as response:
            data = await response.json()
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


# Global HTTP connection pool
_http_pool: Optional["HTTPConnectionPool"] = None
_pool_lock = threading.Lock()


@dataclass
class PoolConfig:
    """HTTP connection pool configuration."""
    max_connections: int = 100  # Max total connections
    max_keepalive_connections: int = 20  # Max idle connections
    keepalive_expiry: int = 30  # Seconds before idle connections expire
    connect_timeout: float = 10.0  # Connection timeout
    read_timeout: float = 30.0  # Read timeout (reduced for MiniMax latency handling)
    write_timeout: float = 60.0  # Write timeout
    pool_timeout: float = 5.0  # Timeout for getting connection from pool


@dataclass
class PoolStats:
    """HTTP connection pool statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    active_requests: int = 0
    total_connections: int = 0
    active_connections: int = 0


class HTTPConnectionPool:
    """
    HTTP connection pool for LLM API calls.
    
    Features:
    - Connection reuse across requests
    - Per-host connection limiting
    - Keep-alive connection management
    - Automatic cleanup of expired connections
    - Thread-safe operations
    
    Example:
        >>> pool = HTTPConnectionPool()
        >>> 
        >>> # Sync usage
        >>> with pool.get_client() as client:
        ...     response = client.get("https://api.openai.com/v1/models")
        ... 
        >>> # Async usage
        >>> async with pool.get_async_client() as client:
        ...     response = await client.get("https://api.anthropic.com/v1/messages")
    """
    
    def __init__(self, config: Optional[PoolConfig] = None):
        """
        Initialize HTTP connection pool.
        
        Args:
            config: Pool configuration.
        """
        self._config = config or PoolConfig()
        self._clients: Dict[str, httpx.Client] = {}
        self._async_clients: Dict[str, httpx.AsyncClient] = {}
        self._client_lock = threading.Lock()
        self._stats = PoolStats()
        self._closed = False
        
        # Default headers for all requests
        self._default_headers: Dict[str, str] = {
            "User-Agent": "Neshama/1.0",
            "Accept": "application/json",
        }
    
    def _get_client_key(self, url: str) -> str:
        """Get the client key (host) for a URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _create_client(self) -> httpx.Client:
        """Create a new HTTP client with connection pooling."""
        limits = httpx.Limits(
            max_connections=self._config.max_connections,
            max_keepalive_connections=self._config.max_keepalive_connections,
            keepalive_expiry=self._config.keepalive_expiry,
        )
        
        return httpx.Client(
            limits=limits,
            timeout=httpx.Timeout(
                connect=self._config.connect_timeout,
                read=self._config.read_timeout,
                write=self._config.write_timeout,
                pool=self._config.pool_timeout,
            ),
            headers=self._default_headers,
        )
    
    def _create_async_client(self) -> httpx.AsyncClient:
        """Create a new async HTTP client with connection pooling."""
        limits = httpx.Limits(
            max_connections=self._config.max_connections,
            max_keepalive_connections=self._config.max_keepalive_connections,
            keepalive_expiry=self._config.keepalive_expiry,
        )
        
        return httpx.AsyncClient(
            limits=limits,
            timeout=httpx.Timeout(
                connect=self._config.connect_timeout,
                read=self._config.read_timeout,
                write=self._config.write_timeout,
                pool=self._config.pool_timeout,
            ),
            headers=self._default_headers,
        )
    
    def get_client(self, base_url: Optional[str] = None) -> httpx.Client:
        """
        Get or create an HTTP client for the given base URL.
        
        Args:
            base_url: Optional base URL to scope the client.
        
        Returns:
            httpx.Client instance.
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        key = base_url or "_default_"
        
        with self._client_lock:
            if key not in self._clients:
                if base_url:
                    self._clients[key] = httpx.Client(base_url=base_url)
                else:
                    self._clients[key] = self._create_client()
                self._stats.total_connections += 1
        
        return self._clients[key]
    
    async def get_async_client(self, base_url: Optional[str] = None) -> httpx.AsyncClient:
        """
        Get or create an async HTTP client for the given base URL.
        
        Args:
            base_url: Optional base URL to scope the client.
        
        Returns:
            httpx.AsyncClient instance.
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        key = base_url or "_default_"
        
        if key not in self._async_clients:
            if base_url:
                self._async_clients[key] = httpx.AsyncClient(base_url=base_url)
            else:
                self._async_clients[key] = self._create_async_client()
            self._stats.total_connections += 1
        
        return self._async_clients[key]
    
    @asynccontextmanager
    async def session(self, base_url: Optional[str] = None):
        """
        Async context manager for an HTTP session.
        
        Args:
            base_url: Optional base URL.
        
        Yields:
            httpx.AsyncClient instance.
        """
        client = await self.get_async_client(base_url)
        self._stats.active_requests += 1
        self._stats.total_requests += 1
        
        try:
            yield client
            self._stats.successful_requests += 1
        except Exception as e:
            self._stats.failed_requests += 1
            raise
        finally:
            self._stats.active_requests -= 1
    
    @property
    def stats(self) -> PoolStats:
        """Get pool statistics."""
        return self._stats
    
    def close(self) -> None:
        """Close all HTTP clients in the pool."""
        if self._closed:
            return
        
        self._closed = True
        
        with self._client_lock:
            for client in self._clients.values():
                try:
                    client.close()
                except Exception as e:
                    logger.warning(f"Error closing HTTP client: {e}")
            self._clients.clear()
        
        # Note: Async clients should be closed via async_close()
    
    async def async_close(self) -> None:
        """Close all async HTTP clients."""
        if self._closed:
            return
        
        self._closed = True
        
        for client in self._async_clients.values():
            try:
                await client.aclose()
            except Exception as e:
                logger.warning(f"Error closing async HTTP client: {e}")
        self._async_clients.clear()
    
    def set_default_headers(self, headers: Dict[str, str]) -> None:
        """
        Set default headers for all HTTP requests.
        
        Args:
            headers: Dictionary of headers.
        """
        self._default_headers.update(headers)


def get_http_pool(config: Optional[PoolConfig] = None) -> HTTPConnectionPool:
    """
    Get the global HTTP connection pool instance.
    
    Args:
        config: Optional pool configuration.
    
    Returns:
        HTTPConnectionPool instance.
    """
    global _http_pool
    
    with _pool_lock:
        if _http_pool is None:
            _http_pool = HTTPConnectionPool(config)
        return _http_pool


def reset_http_pool() -> None:
    """Reset the global HTTP connection pool (for testing)."""
    global _http_pool
    
    with _pool_lock:
        if _http_pool is not None:
            _http_pool.close()
            _http_pool = None


class LLMHTTPClient:
    """
    Specialized HTTP client for LLM API calls.
    
    Features:
    - Per-provider connection pools
    - Automatic retry with backoff
    - Timeout handling with configurable connect/read timeouts
    - Rate-limit-aware retry (429 waits before retry)
    - Request/response logging
    - Error handling
    
    Example:
        >>> client = LLMHTTPClient()
        >>> 
        >>> # OpenAI-style API
        >>> response = await client.post(
        ...     "https://api.openai.com/v1/chat/completions",
        ...     json={"model": "gpt-4", "messages": [...]}
        ... )
        >>> 
        >>> # Anthropic-style API
        >>> response = await client.post(
        ...     "https://api.anthropic.com/v1/messages",
        ...     json={"model": "claude-3", "messages": [...]}
        ... )
    """
    
    # Retry configuration per error type
    TIMEOUT_MAX_RETRIES = 1       # Timeout: retry once
    SERVER_ERROR_MAX_RETRIES = 1  # 5xx: retry once
    RATE_LIMIT_RETRY_DELAY = 2.0  # 429: wait 2s then retry once
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        connect_timeout: float = 10.0,
        read_timeout: float = 30.0,
    ):
        """
        Initialize LLM HTTP client.
        
        Args:
            max_retries: Maximum number of retries for failed requests.
            retry_delay: Initial delay between retries (seconds).
            backoff_factor: Multiplier for delay after each retry.
            connect_timeout: Connection timeout in seconds (default 10s).
            read_timeout: Read timeout in seconds (default 30s for MiniMax latency).
        """
        self._pool = get_http_pool()
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._backoff_factor = backoff_factor
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
    
    def _get_timeout(self) -> httpx.Timeout:
        """Get httpx.Timeout with configured connect/read timeouts."""
        return httpx.Timeout(
            connect=self._connect_timeout,
            read=self._read_timeout,
            write=60.0,
            pool=5.0,
        )
    
    async def request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """
        Make an HTTP request with retry logic.
        
        Retry strategy:
        - Timeout (ConnectTimeout/ReadTimeout): retry 1 time
        - 5xx server error: retry 1 time
        - 429 rate limit: wait 2s, then retry 1 time
        - 4xx client error (not 429): no retry, raise immediately
        
        Args:
            method: HTTP method (GET, POST, etc.).
            url: Request URL.
            **kwargs: Additional arguments for httpx.
        
        Returns:
            httpx.Response instance.
        
        Raises:
            httpx.HTTPStatusError: After all retries exhausted.
            httpx.TimeoutException: After timeout retries exhausted.
        """
        # Determine max retries based on error category tracking
        attempt = 0
        delay = self._retry_delay
        max_attempts = self._max_retries + 1
        
        while attempt < max_attempts:
            try:
                # Use per-request timeout override
                timeout = kwargs.pop("timeout", self._get_timeout())
                async with self._pool.session() as session:
                    response = await session.request(method, url, timeout=timeout, **kwargs)
                    response.raise_for_status()
                    return response
                    
            except httpx.TimeoutException as e:
                attempt += 1
                # Timeout: only retry once
                if attempt > self.TIMEOUT_MAX_RETRIES:
                    logger.error(
                        f"Request timed out after {attempt} attempts: {url} "
                        f"(connect={self._connect_timeout}s, read={self._read_timeout}s)"
                    )
                    raise
                
                logger.warning(
                    f"Request timed out (attempt {attempt}/{self.TIMEOUT_MAX_RETRIES + 1}): "
                    f"{type(e).__name__} for {url}. Retrying..."
                )
                # No delay on timeout retry - the timeout itself already cost time
                
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                
                # 429 rate limit: wait and retry once
                if status_code == 429:
                    attempt += 1
                    if attempt > 1:  # Only one 429 retry
                        raise
                    logger.warning(
                        f"Rate limited (429) for {url}. "
                        f"Retrying in {self.RATE_LIMIT_RETRY_DELAY}s..."
                    )
                    await asyncio.sleep(self.RATE_LIMIT_RETRY_DELAY)
                    continue
                
                # 5xx server error: retry once
                if status_code >= 500:
                    attempt += 1
                    if attempt > self.SERVER_ERROR_MAX_RETRIES:
                        raise
                    logger.warning(
                        f"Server error {status_code} (attempt {attempt}): {url}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= self._backoff_factor
                    continue
                
                # Other 4xx client errors: no retry
                raise
                
            except httpx.RequestError as e:
                attempt += 1
                if attempt > self.TIMEOUT_MAX_RETRIES + 1:
                    raise
                
                logger.warning(
                    f"Request error (attempt {attempt}): {type(e).__name__} for {url}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                delay *= self._backoff_factor
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make a GET request."""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make a POST request."""
        return await self.request("POST", url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Make a PUT request."""
        return await self.request("PUT", url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Make a DELETE request."""
        return await self.request("DELETE", url, **kwargs)


def get_llm_client() -> LLMHTTPClient:
    """
    Get an LLM HTTP client instance.
    
    Returns:
        LLMHTTPClient instance.
    """
    return LLMHTTPClient()
