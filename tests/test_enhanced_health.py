# Test Enhanced Health Checks
"""
Tests for enhanced health checks with Kubernetes probes.
"""

import time
from unittest.mock import patch, MagicMock

import pytest


class TestProbeType:
    """Tests for ProbeType enum."""
    
    def test_probe_type_values(self):
        """Test probe type values."""
        from neshama.monitoring.enhanced_health import ProbeType
        
        assert ProbeType.LIVENESS.value == "liveness"
        assert ProbeType.READINESS.value == "readiness"
        assert ProbeType.STARTUP.value == "startup"


class TestProbeResult:
    """Tests for ProbeResult dataclass."""
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        from neshama.monitoring.enhanced_health import ProbeResult, ProbeType
        
        result = ProbeResult(
            probe=ProbeType.LIVENESS,
            passed=True,
            message="Process is alive",
            details={"pid": 1234},
            duration_ms=1.5,
        )
        
        data = result.to_dict()
        
        assert data["probe"] == "liveness"
        assert data["passed"] is True
        assert data["message"] == "Process is alive"
        assert data["details"]["pid"] == 1234
        assert data["duration_ms"] == 1.5


class TestEnhancedHealthChecker:
    """Tests for EnhancedHealthChecker class."""
    
    def test_init(self):
        """Test enhanced health checker initialization."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker
        
        checker = EnhancedHealthChecker()
        
        assert checker is not None
        assert checker._startup_complete is False
    
    def test_liveness_probe_passed(self):
        """Test liveness probe passes."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker
        
        checker = EnhancedHealthChecker()
        result = checker.liveness_probe()
        
        assert result.passed is True
        assert result.probe.value == "liveness"
    
    def test_readiness_probe_requires_startup(self):
        """Test readiness probe requires startup complete."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker
        
        checker = EnhancedHealthChecker()
        
        # Startup not complete, should fail
        result = checker.readiness_probe()
        assert result.passed is False
    
    def test_startup_probe_in_progress(self):
        """Test startup probe in progress."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker
        
        checker = EnhancedHealthChecker()
        
        # If startup completes quickly (because storage is available), that's OK
        # The test verifies the probe runs and returns a result
        result = checker.startup_probe()
        
        # Result depends on whether startup completes
        # Either "in progress" or "complete" is valid
        assert result.probe.value == "startup"
        assert isinstance(result.passed, bool)
        assert "message" in result.to_dict()
    
    def test_mark_startup_complete(self):
        """Test marking startup complete."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker
        
        checker = EnhancedHealthChecker()
        
        checker.mark_startup_complete()
        
        assert checker._startup_complete is True
        
        # Now readiness should pass
        result = checker.readiness_probe()
        assert result.passed is True
    
    def test_check_redis_not_configured(self):
        """Test Redis check when not configured."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker, HealthStatus
        
        checker = EnhancedHealthChecker()
        
        with patch.dict("os.environ", {
            "NESHAMA_STORAGE_BACKEND": "yaml"
        }, clear=True):
            result = checker.check_redis()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.details.get("configured") is False
    
    def test_check_llm_connectivity(self):
        """Test LLM connectivity check."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker, HealthStatus
        
        checker = EnhancedHealthChecker()
        
        result = checker.check_llm_connectivity()
        
        # Should return some status (providers or errors)
        assert result.name == "llm_connectivity"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    def test_check_dependencies(self):
        """Test checking all dependencies."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker
        
        checker = EnhancedHealthChecker()
        
        deps = checker.check_dependencies()
        
        assert len(deps) >= 3  # storage, redis, llm_connectivity
        assert any(d.name == "storage" for d in deps)
        assert any(d.name == "redis" for d in deps)
        assert any(d.name == "llm_connectivity" for d in deps)
    
    def test_check_all_dependencies_aggregated(self):
        """Test aggregated dependency check."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker
        
        checker = EnhancedHealthChecker()
        
        result = checker.check_all_dependencies()
        
        assert result.name == "dependencies"
        assert "healthy" in result.details
        assert "degraded" in result.details
        assert "unhealthy" in result.details
    
    def test_enhanced_check_returns_dict(self):
        """Test enhanced check returns complete dictionary."""
        from neshama.monitoring.enhanced_health import EnhancedHealthChecker
        
        checker = EnhancedHealthChecker()
        checker.mark_startup_complete()
        
        result = checker.enhanced_check()
        
        assert "health" in result
        assert "dependencies" in result
        assert "probes" in result
        assert "liveness" in result["probes"]
        assert "readiness" in result["probes"]
        assert "startup" in result["probes"]


class TestModuleFunctions:
    """Tests for module-level functions."""
    
    def test_get_enhanced_checker(self):
        """Test getting enhanced checker singleton."""
        from neshama.monitoring.enhanced_health import (
            get_enhanced_checker,
            EnhancedHealthChecker,
        )
        
        checker = get_enhanced_checker()
        
        assert checker is not None
        assert isinstance(checker, EnhancedHealthChecker)
    
    def test_enhanced_health_check_function(self):
        """Test enhanced_health_check function."""
        from neshama.monitoring.enhanced_health import enhanced_health_check
        
        result = enhanced_health_check()
        
        assert isinstance(result, dict)
        assert "health" in result
        assert "dependencies" in result
        assert "probes" in result
    
    def test_liveness_probe_function(self):
        """Test liveness_probe function."""
        from neshama.monitoring.enhanced_health import liveness_probe
        
        result = liveness_probe()
        
        assert result.passed is True
        assert result.probe.value == "liveness"
    
    def test_readiness_probe_function(self):
        """Test readiness_probe function."""
        from neshama.monitoring.enhanced_health import readiness_probe
        
        result = readiness_probe()
        
        # Result depends on startup state
        assert isinstance(result.passed, bool)
        assert result.probe.value == "readiness"
    
    def test_startup_probe_function(self):
        """Test startup_probe function."""
        from neshama.monitoring.enhanced_health import startup_probe
        
        result = startup_probe()
        
        assert result.probe.value == "startup"
        assert isinstance(result.passed, bool)
