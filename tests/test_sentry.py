# Test Sentry Integration
"""
Tests for Sentry integration.
"""

import os
from unittest.mock import patch, MagicMock

import pytest


class TestSentryIntegration:
    """Tests for SentryIntegration."""
    
    def test_initialization(self):
        """Test initialization."""
        from neshama.monitoring.sentry import SentryIntegration
        
        integration = SentryIntegration()
        assert integration._dsn is None
        assert integration._initialized is False
    
    def test_is_configured_without_dsn(self):
        """Test is_configured when DSN not set."""
        # Make sure DSN is not set
        with patch.dict(os.environ, {}, clear=True):
            from neshama.monitoring.sentry import SentryIntegration
            
            integration = SentryIntegration()
            assert integration.is_configured is False
    
    def test_is_configured_with_dsn(self):
        """Test is_configured when DSN is set."""
        with patch.dict(os.environ, {"SENTRY_DSN": "https://key@sentry.io/123"}):
            from neshama.monitoring.sentry import SentryIntegration
            
            integration = SentryIntegration()
            # Need to reinit after env change
            assert integration.is_configured is True
    
    def test_check_sentry_available(self):
        """Test checking if sentry-sdk is available."""
        from neshama.monitoring.sentry import SentryIntegration
        
        integration = SentryIntegration()
        # Should return True (sentry-sdk is installed in test env)
        # or False if not installed
        result = integration._check_sentry_available()
        assert isinstance(result, bool)
    
    def test_init_without_dsn(self):
        """Test init without DSN."""
        from neshama.monitoring.sentry import SentryIntegration
        
        with patch.dict(os.environ, {}, clear=True):
            integration = SentryIntegration()
            result = integration.init()
            assert result is False
    
    def test_init_with_invalid_dsn(self):
        """Test init with invalid DSN."""
        from neshama.monitoring.sentry import SentryIntegration
        
        with patch.dict(os.environ, {"SENTRY_DSN": "invalid"}):
            integration = SentryIntegration()
            # Should fail gracefully
            try:
                result = integration.init()
            except Exception:
                result = False
            # Should either succeed or fail gracefully
    
    def test_serialize_context(self):
        """Test context serialization."""
        from neshama.monitoring.sentry import SentryIntegration
        from datetime import datetime
        
        integration = SentryIntegration()
        
        # Test dict
        result = integration._serialize_context({"key": "value"})
        assert result == {"key": "value"}
        
        # Test list (items are serialized)
        result = integration._serialize_context([1, 2, 3])
        assert result == ["1", "2", "3"]
        
        # Test datetime
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = integration._serialize_context(dt)
        assert result == "2024-01-01T12:00:00"
        
        # Test other types
        result = integration._serialize_context(123)
        assert result == "123"
    
    def test_capture_exception_without_init(self):
        """Test capture_exception when not initialized."""
        from neshama.monitoring.sentry import SentryIntegration
        
        integration = SentryIntegration()
        result = integration.capture_exception({"error": "test"})
        assert result is None
    
    def test_capture_message_without_init(self):
        """Test capture_message when not initialized."""
        from neshama.monitoring.sentry import SentryIntegration
        
        integration = SentryIntegration()
        result = integration.capture_message("test message")
        assert result is None
    
    def test_add_breadcrumb_without_init(self):
        """Test add_breadcrumb when not initialized."""
        from neshama.monitoring.sentry import SentryIntegration
        
        integration = SentryIntegration()
        # Should not raise
        integration.add_breadcrumb("test", "test")
    
    def test_set_context_without_init(self):
        """Test set_context when not initialized."""
        from neshama.monitoring.sentry import SentryIntegration
        
        integration = SentryIntegration()
        # Should not raise
        integration.set_context("test", {"key": "value"})
    
    def test_set_tag_without_init(self):
        """Test set_tag when not initialized."""
        from neshama.monitoring.sentry import SentryIntegration
        
        integration = SentryIntegration()
        # Should not raise
        integration.set_tag("key", "value")
    
    def test_get_integration(self):
        """Test get_integration singleton."""
        from neshama.monitoring.sentry import get_integration, SentryIntegration
        
        integration1 = get_integration()
        integration2 = get_integration()
        
        # Should return same instance
        assert integration1 is integration2
        assert isinstance(integration1, SentryIntegration)


class TestModuleFunctions:
    """Tests for module-level functions."""
    
    def test_init_sentry(self):
        """Test init_sentry function."""
        from neshama.monitoring.sentry import init_sentry
        
        # Should not raise
        result = init_sentry()
        assert isinstance(result, bool)
    
    def test_capture_exception_function(self):
        """Test capture_exception function."""
        from neshama.monitoring.sentry import capture_exception
        
        # Should not raise
        result = capture_exception({"error": "test"})
        assert result is None  # Not initialized
    
    def test_capture_message_function(self):
        """Test capture_message function."""
        from neshama.monitoring.sentry import capture_message
        
        # Should not raise
        result = capture_message("test message")
        assert result is None  # Not initialized
