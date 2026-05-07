# Test Health Checker
"""
Tests for Health Checker.
"""

import time
from unittest.mock import patch, MagicMock

import pytest


class TestHealthChecker:
    """Tests for HealthChecker."""
    
    @pytest.fixture
    def checker(self):
        """Create a health checker for testing."""
        from neshama.monitoring.health import HealthChecker
        return HealthChecker()
    
    def test_initialization(self, checker):
        """Test checker initialization."""
        assert checker._start_time > 0
        assert checker.uptime >= 0
    
    def test_uptime(self, checker):
        """Test uptime calculation."""
        time.sleep(0.1)
        assert checker.uptime >= 0.1
    
    def test_get_version(self, checker):
        """Test version retrieval."""
        version = checker._get_version()
        assert isinstance(version, str)
    
    def test_check_storage(self, checker):
        """Test storage health check."""
        with patch('neshama.monitoring.health.get_storage') as mock_get_storage:
            mock_storage = MagicMock()
            mock_storage.health_check.return_value = True
            mock_storage.backend_type = "yaml"
            mock_get_storage.return_value = mock_storage
            
            result = checker.check_storage()
            
            assert result.name == "storage"
            assert result.status.value in ["healthy", "degraded", "unhealthy"]
            assert result.latency_ms is not None
            assert result.details["backend"] == "yaml"
    
    def test_check_storage_failure(self, checker):
        """Test storage health check failure."""
        with patch('neshama.monitoring.health.get_storage') as mock_get_storage:
            mock_storage = MagicMock()
            mock_storage.health_check.side_effect = Exception("Connection failed")
            mock_get_storage.return_value = mock_storage
            
            result = checker.check_storage()
            
            assert result.name == "storage"
            assert result.status.value == "unhealthy"
            assert "failed" in result.message.lower()
    
    def test_check_memory(self, checker):
        """Test memory health check."""
        with patch('neshama.monitoring.health.psutil') as mock_psutil:
            mock_psutil.virtual_memory.return_value = MagicMock(
                percent=50.0,
                used=8 * 1024**3,
                available=8 * 1024**3,
                total=16 * 1024**3,
            )
            
            result = checker.check_memory()
            
            assert result.name == "memory"
            assert result.status.value == "healthy"
            assert result.details["percent"] == 50.0
    
    def test_check_memory_degraded(self, checker):
        """Test memory health check degraded."""
        with patch('neshama.monitoring.health.psutil') as mock_psutil:
            mock_psutil.virtual_memory.return_value = MagicMock(
                percent=80.0,
                used=12.8 * 1024**3,
                available=3.2 * 1024**3,
                total=16 * 1024**3,
            )
            
            result = checker.check_memory()
            
            assert result.name == "memory"
            assert result.status.value == "degraded"
    
    def test_check_memory_unhealthy(self, checker):
        """Test memory health check unhealthy."""
        with patch('neshama.monitoring.health.psutil') as mock_psutil:
            mock_psutil.virtual_memory.return_value = MagicMock(
                percent=95.0,
                used=15.2 * 1024**3,
                available=0.8 * 1024**3,
                total=16 * 1024**3,
            )
            
            result = checker.check_memory()
            
            assert result.name == "memory"
            assert result.status.value == "unhealthy"
    
    def test_check_cpu(self, checker):
        """Test CPU health check."""
        with patch('neshama.monitoring.health.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 30.0
            mock_psutil.cpu_count.return_value = 4
            
            result = checker.check_cpu()
            
            assert result.name == "cpu"
            assert result.status.value == "healthy"
            assert result.details["percent"] == 30.0
            assert result.details["count"] == 4
    
    def test_check_disk(self, checker):
        """Test disk health check."""
        with patch('neshama.monitoring.health.psutil') as mock_psutil:
            mock_psutil.disk_usage.return_value = MagicMock(
                percent=50.0,
                used=250 * 1024**3,
                free=250 * 1024**3,
                total=500 * 1024**3,
            )
            
            result = checker.check_disk()
            
            assert result.name == "disk"
            assert result.status.value == "healthy"
    
    def test_check_error_rate(self, checker):
        """Test error rate check."""
        result = checker.check_error_rate()
        
        assert result.name == "error_rate"
        assert result.status.value in ["healthy", "degraded", "unhealthy"]
    
    def test_record_error(self, checker):
        """Test recording errors."""
        checker.record_error("test_component")
        
        # Record should be tracked
        with checker._get_error_lock():
            assert "test_component" in checker._error_tracker
    
    def test_full_check(self, checker):
        """Test full health check."""
        with patch('neshama.monitoring.health.get_storage') as mock_storage:
            mock_storage.return_value.health_check.return_value = True
            mock_storage.return_value.backend_type = "yaml"
            
            with patch('neshama.monitoring.health.psutil') as mock_psutil:
                mock_psutil.virtual_memory.return_value = MagicMock(
                    percent=50.0, used=8 * 1024**3,
                    available=8 * 1024**3, total=16 * 1024**3
                )
                mock_psutil.cpu_percent.return_value = 30.0
                mock_psutil.cpu_count.return_value = 4
                mock_psutil.disk_usage.return_value = MagicMock(
                    percent=50.0, used=250 * 1024**3,
                    free=250 * 1024**3, total=500 * 1024**3
                )
                
                report = checker.check()
                
                assert report.status.value in ["healthy", "degraded", "unhealthy"]
                assert report.timestamp is not None
                assert report.uptime_seconds >= 0
                assert report.version is not None
                assert len(report.components) > 0
    
    def test_quick_check(self, checker):
        """Test quick health check."""
        with patch('neshama.monitoring.health.get_storage') as mock_storage:
            mock_storage.return_value.health_check.return_value = True
            
            result = checker.quick_check()
            
            assert "status" in result
            assert result["status"] in ["healthy", "unhealthy"]


class TestHealthStatus:
    """Tests for HealthStatus enum."""
    
    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        from neshama.monitoring.health import HealthStatus
        
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestComponentHealth:
    """Tests for ComponentHealth."""
    
    def test_to_dict(self):
        """Test to_dict conversion."""
        from neshama.monitoring.health import ComponentHealth, HealthStatus
        
        component = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            message="All good",
            latency_ms=1.5,
            details={"key": "value"},
        )
        
        d = component.to_dict()
        assert d["name"] == "test"
        assert d["status"] == "healthy"
        assert d["message"] == "All good"
        assert d["latency_ms"] == 1.5
        assert d["details"] == {"key": "value"}


class TestHealthReport:
    """Tests for HealthReport."""
    
    def test_to_dict(self):
        """Test to_dict conversion."""
        from neshama.monitoring.health import (
            HealthReport, HealthStatus, ComponentHealth
        )
        from datetime import datetime
        
        report = HealthReport(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=100.5,
            version="1.0.0",
            components=[
                ComponentHealth(
                    name="test",
                    status=HealthStatus.HEALTHY,
                )
            ],
        )
        
        d = report.to_dict()
        assert d["status"] == "healthy"
        assert d["uptime_seconds"] == 100.5
        assert d["version"] == "1.0.0"
        assert len(d["components"]) == 1


class TestModuleFunctions:
    """Tests for module-level functions."""
    
    def test_get_checker(self):
        """Test get_checker singleton."""
        from neshama.monitoring.health import get_checker, HealthChecker
        
        checker1 = get_checker()
        checker2 = get_checker()
        
        assert checker1 is checker2
        assert isinstance(checker1, HealthChecker)
    
    def test_health_check_function(self):
        """Test health_check function."""
        from neshama.monitoring.health import health_check
        
        with patch('neshama.monitoring.health.get_storage') as mock_storage:
            mock_storage.return_value.health_check.return_value = True
            mock_storage.return_value.backend_type = "yaml"
            
            with patch('neshama.monitoring.health.psutil') as mock_psutil:
                mock_psutil.virtual_memory.return_value = MagicMock(
                    percent=50.0, used=8 * 1024**3,
                    available=8 * 1024**3, total=16 * 1024**3
                )
                mock_psutil.cpu_percent.return_value = 30.0
                mock_psutil.cpu_count.return_value = 4
                mock_psutil.disk_usage.return_value = MagicMock(
                    percent=50.0, used=250 * 1024**3,
                    free=250 * 1024**3, total=500 * 1024**3
                )
                
                report = health_check()
                assert report.status.value in ["healthy", "degraded", "unhealthy"]
    
    def test_quick_health_check_function(self):
        """Test quick_health_check function."""
        from neshama.monitoring.health import quick_health_check
        
        with patch('neshama.monitoring.health.get_storage') as mock_storage:
            mock_storage.return_value.health_check.return_value = True
            
            result = quick_health_check()
            assert "status" in result
    
    def test_record_error_function(self):
        """Test record_error function."""
        from neshama.monitoring.health import record_error, get_checker
        
        # Clear existing
        checker = get_checker()
        checker._error_tracker.clear()
        
        record_error("test")
        
        assert "test" in checker._error_tracker
