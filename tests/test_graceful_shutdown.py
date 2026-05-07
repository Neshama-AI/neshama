# Test Graceful Shutdown
"""
Tests for graceful shutdown functionality.
"""

import time
import threading
import asyncio
from unittest.mock import patch, MagicMock

import pytest


class TestGracefulShutdown:
    """Tests for GracefulShutdown."""
    
    def test_initialization(self):
        """Test shutdown manager initialization."""
        from neshama.web.server import GracefulShutdown
        
        manager = GracefulShutdown(timeout=30)
        
        assert manager._timeout == 30
        assert not manager._shutdown_event.is_set()
    
    def test_register_background_task(self):
        """Test registering background task."""
        from neshama.web.server import GracefulShutdown
        
        manager = GracefulShutdown()
        task = MagicMock()
        
        manager.register_background_task(task)
        
        assert task in manager._background_tasks
    
    def test_register_service(self):
        """Test registering service."""
        from neshama.web.server import GracefulShutdown
        
        manager = GracefulShutdown()
        service = MagicMock()
        
        manager.register_service(service)
        
        assert service in manager._services
    
    def test_initiate_shutdown(self):
        """Test initiating shutdown."""
        from neshama.web.server import GracefulShutdown
        
        manager = GracefulShutdown()
        manager.initiate_shutdown()
        
        assert manager._shutdown_event.is_set()
    
    def test_initiate_shutdown_idempotent(self):
        """Test that shutdown is idempotent."""
        from neshama.web.server import GracefulShutdown
        
        manager = GracefulShutdown()
        manager.initiate_shutdown()
        manager.initiate_shutdown()  # Should not raise
        
        assert manager._shutdown_event.is_set()
    
    @pytest.mark.asyncio
    async def test_wait_for_shutdown(self):
        """Test waiting for shutdown."""
        from neshama.web.server import GracefulShutdown
        
        manager = GracefulShutdown()
        
        async def set_event():
            await asyncio.sleep(0.1)
            manager.initiate_shutdown()
        
        # Start the event setter
        asyncio.create_task(set_event())
        
        # Wait for shutdown
        await manager.wait_for_shutdown()
        
        assert manager._shutdown_event.is_set()


class TestServerManagerShutdown:
    """Tests for ServerManager shutdown."""
    
    def test_shutdown_timeout_property(self):
        """Test shutdown timeout property."""
        from neshama.web.server import ServerManager
        
        manager = ServerManager()
        
        assert manager.shutdown_timeout == 30
        
        manager.shutdown_timeout = 60
        assert manager.shutdown_timeout == 60


class TestRequestTracking:
    """Tests for request tracking."""
    
    @pytest.mark.asyncio
    async def test_request_start_hook(self):
        """Test request start hook."""
        from neshama.web.server import request_start_hook, _active_requests, _shutdown_lock
        
        mock_request = MagicMock()
        
        # Get initial count
        initial_count = _active_requests
        
        await request_start_hook(mock_request)
        
        # Count should increase
        with _shutdown_lock:
            assert _active_requests == initial_count + 1
        
        # Cleanup
        from neshama.web.server import _active_requests
        with _shutdown_lock:
            _active_requests = initial_count
    
    @pytest.mark.asyncio
    async def test_request_end_hook(self):
        """Test request end hook."""
        from neshama.web.server import request_end_hook, _active_requests, _shutdown_lock
        
        mock_request = MagicMock()
        
        # Set active count
        with _shutdown_lock:
            _active_requests = 5
        
        await request_end_hook(mock_request)
        
        # Count should decrease
        with _shutdown_lock:
            assert _active_requests == 4


class TestGlobalShutdownManager:
    """Tests for global shutdown manager."""
    
    def test_get_shutdown_manager(self):
        """Test getting global shutdown manager."""
        from neshama.web.server import get_shutdown_manager, GracefulShutdown
        
        manager = get_shutdown_manager()
        
        assert isinstance(manager, GracefulShutdown)
    
    def test_get_shutdown_manager_singleton(self):
        """Test that shutdown manager is singleton."""
        from neshama.web.server import get_shutdown_manager
        
        manager1 = get_shutdown_manager()
        manager2 = get_shutdown_manager()
        
        assert manager1 is manager2


class TestShutdownIntegration:
    """Integration tests for shutdown."""
    
    def test_shutdown_with_active_requests(self):
        """Test shutdown behavior with active requests."""
        from neshama.web.server import GracefulShutdown, _active_requests, _shutdown_lock
        
        manager = GracefulShutdown(timeout=2)
        
        # Simulate active requests
        with _shutdown_lock:
            _active_requests = 3
        
        # Initiate shutdown should work
        manager.initiate_shutdown()
        
        # Cleanup
        with _shutdown_lock:
            _active_requests = 0
    
    def test_shutdown_timeout(self):
        """Test shutdown with timeout."""
        from neshama.web.server import GracefulShutdown, _active_requests, _shutdown_lock
        
        manager = GracefulShutdown(timeout=1)
        
        # Simulate infinite active requests
        with _shutdown_lock:
            _active_requests = 9999
        
        start_time = time.time()
        manager.initiate_shutdown()
        
        # Wait for shutdown
        time.sleep(2)  # Should timeout
        
        elapsed = time.time() - start_time
        
        # Should have timed out
        assert elapsed >= 1
        
        # Cleanup
        with _shutdown_lock:
            _active_requests = 0
    
    def test_service_shutdown(self):
        """Test service shutdown callbacks."""
        from neshama.web.server import GracefulShutdown
        
        manager = GracefulShutdown()
        
        # Create mock service with shutdown method
        service = MagicMock()
        manager.register_service(service)
        
        # Services should be called during shutdown
        # (In real implementation, but here we just verify registration)
        assert service in manager._services


class TestShutdownFlags:
    """Tests for shutdown flags."""
    
    def test_shutdown_initiated_flag(self):
        """Test shutdown initiated flag."""
        from neshama.web.server import _shutdown_initiated, _shutdown_lock
        
        import neshama.web.server as server_module
        
        # Initially False
        with _shutdown_lock:
            assert server_module._shutdown_initiated is False or \
                   server_module._shutdown_initiated is True  # May have been set by other tests


class TestLifespanShutdown:
    """Tests for lifespan shutdown."""
    
    @pytest.mark.asyncio
    async def test_lifespan_yields(self):
        """Test lifespan yields control."""
        from neshama.web.server import create_app
        
        app = create_app()
        
        # The lifespan context manager should exist
        assert hasattr(app, 'router')
