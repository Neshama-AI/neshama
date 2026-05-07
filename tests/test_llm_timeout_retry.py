# Tests for LLM HTTP Client timeout and retry fixes
"""
Tests for the enhanced LLMHTTPClient with:
- Configurable connect/read timeouts (10s/30s)
- Timeout retry (1 time)
- 5xx retry (1 time)
- 429 rate limit retry (2s wait, 1 time)
- No retry on other 4xx errors
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import httpx

from neshama.web.connection_pool import LLMHTTPClient, PoolConfig


class TestLLMHTTPClientTimeoutConfig:
    """Tests for timeout configuration."""
    
    def test_default_timeouts(self):
        """Default timeouts should be connect=10s, read=30s."""
        client = LLMHTTPClient()
        assert client._connect_timeout == 10.0
        assert client._read_timeout == 30.0
    
    def test_custom_timeouts(self):
        """Custom timeouts should be applied."""
        client = LLMHTTPClient(connect_timeout=5.0, read_timeout=15.0)
        assert client._connect_timeout == 5.0
        assert client._read_timeout == 15.0
    
    def test_timeout_object_generated(self):
        """_get_timeout should return httpx.Timeout with correct values."""
        client = LLMHTTPClient(connect_timeout=10.0, read_timeout=30.0)
        timeout = client._get_timeout()
        assert isinstance(timeout, httpx.Timeout)
        assert timeout.connect == 10.0
        assert timeout.read == 30.0
        assert timeout.write == 60.0
        assert timeout.pool == 5.0
    
    def test_pool_config_default_read_timeout(self):
        """PoolConfig should have read_timeout=30s for MiniMax latency."""
        config = PoolConfig()
        assert config.read_timeout == 30.0


class TestLLMHTTPClientRetryConfig:
    """Tests for retry configuration constants."""
    
    def test_timeout_retry_limit(self):
        """Timeout should only retry once."""
        assert LLMHTTPClient.TIMEOUT_MAX_RETRIES == 1
    
    def test_server_error_retry_limit(self):
        """5xx errors should only retry once."""
        assert LLMHTTPClient.SERVER_ERROR_MAX_RETRIES == 1
    
    def test_rate_limit_retry_delay(self):
        """429 should wait 2 seconds before retry."""
        assert LLMHTTPClient.RATE_LIMIT_RETRY_DELAY == 2.0


class TestLLMHTTPClientRetryBehavior:
    """Tests for retry behavior with mocked HTTP calls."""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock the HTTP pool."""
        with patch('neshama.web.connection_pool.get_http_pool') as mock_get_pool:
            pool = MagicMock()
            mock_get_pool.return_value = pool
            
            # Mock the session context manager
            mock_session = AsyncMock()
            pool.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            pool.session.return_value.__aexit__ = AsyncMock(return_value=False)
            
            yield pool, mock_session
    
    @pytest.mark.asyncio
    async def test_timeout_retried_once(self, mock_pool):
        """Timeout should be retried exactly once, then raise."""
        pool, mock_session = mock_pool
        
        # All attempts timeout
        mock_session.request = AsyncMock(side_effect=httpx.ReadTimeout("read timeout"))
        
        client = LLMHTTPClient(max_retries=3)
        
        with pytest.raises(httpx.ReadTimeout):
            await client.request("POST", "https://api.example.com/v1/chat")
        
        # Should have been called twice (initial + 1 retry)
        assert mock_session.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_timeout_success_on_retry(self, mock_pool):
        """Timeout followed by success should return the response."""
        pool, mock_session = mock_pool
        
        # First call times out, second succeeds
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        
        mock_session.request = AsyncMock(
            side_effect=[httpx.ReadTimeout("timeout"), mock_response]
        )
        
        client = LLMHTTPClient(max_retries=3)
        result = await client.request("POST", "https://api.example.com/v1/chat")
        
        assert result == mock_response
        assert mock_session.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_5xx_retried_once(self, mock_pool):
        """5xx errors should be retried once (2 total attempts), then raise."""
        pool, mock_session = mock_pool
        
        # All attempts return 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
        )
        
        mock_session.request = AsyncMock(return_value=mock_response)
        
        client = LLMHTTPClient(max_retries=3)
        
        with pytest.raises(httpx.HTTPStatusError):
            await client.request("POST", "https://api.example.com/v1/chat")
        
        # Should have been called twice (initial + 1 retry for 5xx)
        # SERVER_ERROR_MAX_RETRIES=1 means we allow 2 total attempts
        assert mock_session.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_429_retried_with_delay(self, mock_pool):
        """429 should wait RATE_LIMIT_RETRY_DELAY then retry once."""
        pool, mock_session = mock_pool
        
        # First call 429, second succeeds
        mock_429_response = MagicMock()
        mock_429_response.status_code = 429
        mock_429_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Rate Limited", request=MagicMock(), response=mock_429_response
            )
        )
        
        mock_ok_response = MagicMock()
        mock_ok_response.raise_for_status = MagicMock()
        mock_ok_response.status_code = 200
        
        mock_session.request = AsyncMock(
            side_effect=[mock_429_response, mock_ok_response]
        )
        
        client = LLMHTTPClient(max_retries=3)
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await client.request("POST", "https://api.example.com/v1/chat")
            
            # Should have slept for the rate limit delay
            mock_sleep.assert_any_call(LLMHTTPClient.RATE_LIMIT_RETRY_DELAY)
        
        assert result == mock_ok_response
        assert mock_session.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_4xx_no_retry(self, mock_pool):
        """Non-429 4xx errors should not be retried."""
        pool, mock_session = mock_pool
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Bad Request", request=MagicMock(), response=mock_response
            )
        )
        
        mock_session.request = AsyncMock(return_value=mock_response)
        
        client = LLMHTTPClient(max_retries=3)
        
        with pytest.raises(httpx.HTTPStatusError):
            await client.request("POST", "https://api.example.com/v1/chat")
        
        # Should only have been called once (no retry)
        assert mock_session.request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_per_request_timeout_override(self, mock_pool):
        """Per-request timeout kwarg should be used instead of default."""
        pool, mock_session = mock_pool
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        mock_session.request = AsyncMock(return_value=mock_response)
        
        custom_timeout = httpx.Timeout(5.0)  # Use default param style
        client = LLMHTTPClient()
        await client.request("POST", "https://api.example.com/v1/chat", timeout=custom_timeout)
        
        # Verify the custom timeout was passed to session.request
        call_kwargs = mock_session.request.call_args
        assert call_kwargs.kwargs.get('timeout') == custom_timeout
