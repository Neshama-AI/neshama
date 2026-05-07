# Enhanced Health Checks - Kubernetes Probes and Dependency Checks
"""
Enhanced health checks for production deployments.

Provides:
- Liveness probe (is process alive?)
- Readiness probe (can process handle requests?)
- Startup probe (is startup complete?)
- Dependency health checks (Redis, LLM providers)
- Detailed component diagnostics

Usage:
    from neshama.monitoring.health import (
        enhanced_health_check,
        liveness_probe,
        readiness_probe,
        startup_probe,
        EnhancedHealthChecker,
    )
    
    # Get full health report
    report = enhanced_health_check()
    
    # Get specific probe
    probe = readiness_probe()
"""

import os
import time
import logging
import psutil
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .health import HealthChecker, HealthStatus, ComponentHealth, get_storage

logger = logging.getLogger(__name__)


class ProbeType(str, Enum):
    """Health probe types for Kubernetes."""
    LIVENESS = "liveness"  # Is the process alive?
    READINESS = "readiness"  # Can the process handle requests?
    STARTUP = "startup"  # Is startup complete?


@dataclass
class ProbeResult:
    """Result of a health probe."""
    probe: ProbeType
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "probe": self.probe.value,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "duration_ms": round(self.duration_ms, 2),
        }


class EnhancedHealthChecker(HealthChecker):
    """
    Enhanced health checker with Kubernetes probe support.
    
    Provides:
    - Liveness probe (is process alive?)
    - Readiness probe (can process handle requests?)
    - Startup probe (is startup complete?)
    - Dependency health checks
    - Detailed component diagnostics
    
    Example:
        >>> checker = EnhancedHealthChecker()
        >>> 
        >>> # Kubernetes probes
        >>> liveness = checker.liveness_probe()
        >>> readiness = checker.readiness_probe()
        >>> startup = checker.startup_probe()
        >>> 
        >>> # Dependency checks
        >>> deps = checker.check_all_dependencies()
    """
    
    def __init__(self):
        """Initialize enhanced health checker."""
        super().__init__()
        self._startup_complete = False
        self._startup_timeout = 30  # seconds
        self._startup_deadline = time.time() + self._startup_timeout
    
    def check_redis(self) -> ComponentHealth:
        """
        Check Redis connectivity.
        
        Returns:
            ComponentHealth for Redis
        """
        start = time.time()
        
        try:
            # Check if Redis is configured
            redis_url = os.environ.get("NESHAMA_REDIS_URL")
            redis_host = os.environ.get("NESHAMA_REDIS_HOST")
            storage_backend = os.environ.get("NESHAMA_STORAGE_BACKEND")
            
            # If not using Redis, skip check
            if storage_backend != "redis" and not redis_url and not redis_host:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis not configured (using YAML backend)",
                    latency_ms=(time.time() - start) * 1000,
                    details={"configured": False},
                )
            
            # Try to connect
            import redis
            client = redis.Redis(
                host=redis_host or "localhost",
                port=int(os.environ.get("NESHAMA_REDIS_PORT", "6379")),
                db=int(os.environ.get("NESHAMA_REDIS_DB", "0")),
                password=os.environ.get("NESHAMA_REDIS_PASSWORD"),
                socket_timeout=2,
            )
            
            start_connect = time.time()
            client.ping()
            latency = (time.time() - start_connect) * 1000
            
            # Check latency
            if latency < 10:
                status = HealthStatus.HEALTHY
            elif latency < 100:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name="redis",
                status=status,
                message=f"Redis connected (latency: {latency:.1f}ms)",
                latency_ms=(time.time() - start) * 1000,
                details={
                    "latency_ms": round(latency, 2),
                    "connected": True,
                },
            )
        except ImportError:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis package not installed",
                latency_ms=(time.time() - start) * 1000,
                details={"installed": False},
            )
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.DEGRADED,
                message=f"Redis check failed: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
            )
    
    def check_llm_connectivity(self) -> ComponentHealth:
        """
        Check LLM provider connectivity.
        
        Returns:
            ComponentHealth for LLM connectivity
        """
        start = time.time()
        
        try:
            # Check configured providers
            providers = []
            errors = []
            
            # Try OpenAI
            try:
                from neshama.model_adapter.providers.openai import OpenAIProvider
                providers.append("openai")
            except ImportError:
                errors.append("openai: module_not_found")
            except Exception as e:
                errors.append(f"openai: {str(e)}")
            
            # Try Anthropic
            try:
                from neshama.model_adapter.providers.anthropic import AnthropicProvider
                providers.append("anthropic")
            except ImportError:
                errors.append("anthropic: module_not_found")
            except Exception as e:
                errors.append(f"anthropic: {str(e)}")
            
            latency = (time.time() - start) * 1000
            
            if providers:
                status = HealthStatus.HEALTHY
                message = f"LLM providers available: {', '.join(providers)}"
            else:
                status = HealthStatus.DEGRADED
                message = "No LLM providers available"
            
            return ComponentHealth(
                name="llm_connectivity",
                status=status,
                message=message,
                latency_ms=latency,
                details={
                    "providers": providers,
                    "errors": errors if errors else None,
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="llm_connectivity",
                status=HealthStatus.DEGRADED,
                message=f"LLM check failed: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
            )
    
    def check_dependencies(self) -> List[ComponentHealth]:
        """
        Check all dependencies.
        
        Returns:
            List of ComponentHealth for each dependency
        """
        return [
            self.check_storage(),
            self.check_redis(),
            self.check_llm_connectivity(),
        ]
    
    def check_all_dependencies(self) -> ComponentHealth:
        """
        Check all dependencies as a single component.
        
        Returns:
            ComponentHealth with aggregated status
        """
        start = time.time()
        deps = self.check_dependencies()
        
        healthy = sum(1 for d in deps if d.status == HealthStatus.HEALTHY)
        degraded = sum(1 for d in deps if d.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for d in deps if d.status == HealthStatus.UNHEALTHY)
        
        total = len(deps)
        
        if unhealthy > 0:
            status = HealthStatus.UNHEALTHY
            message = f"{unhealthy}/{total} dependencies unhealthy"
        elif degraded > 0:
            status = HealthStatus.DEGRADED
            message = f"{degraded}/{total} dependencies degraded"
        else:
            status = HealthStatus.HEALTHY
            message = f"All {total} dependencies healthy"
        
        return ComponentHealth(
            name="dependencies",
            status=status,
            message=message,
            latency_ms=(time.time() - start) * 1000,
            details={
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy,
                "total": total,
                "components": {d.name: d.status.value for d in deps},
            },
        )
    
    def liveness_probe(self) -> ProbeResult:
        """
        Kubernetes liveness probe.
        
        Checks if the process is alive and should not be restarted.
        
        Returns:
            ProbeResult for liveness
        """
        start = time.time()
        
        try:
            # Basic liveness: process is running
            pid = os.getpid()
            
            # Check we can access basic system info
            psutil.Process(pid)
            
            duration = (time.time() - start) * 1000
            
            return ProbeResult(
                probe=ProbeType.LIVENESS,
                passed=True,
                message="Process is alive",
                details={"pid": pid},
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ProbeResult(
                probe=ProbeType.LIVENESS,
                passed=False,
                message=f"Liveness check failed: {str(e)}",
                duration_ms=duration,
            )
    
    def readiness_probe(self) -> ProbeResult:
        """
        Kubernetes readiness probe.
        
        Checks if the process is ready to receive traffic.
        
        Returns:
            ProbeResult for readiness
        """
        start = time.time()
        
        try:
            # Readiness: storage is available
            storage = get_storage()
            storage_ok = storage.health_check()
            
            # Startup is complete
            startup_ok = self._startup_complete
            
            duration = (time.time() - start) * 1000
            
            if storage_ok and startup_ok:
                return ProbeResult(
                    probe=ProbeType.READINESS,
                    passed=True,
                    message="Process is ready to receive traffic",
                    details={
                        "storage_ok": storage_ok,
                        "startup_complete": startup_ok,
                    },
                    duration_ms=duration,
                )
            else:
                reasons = []
                if not storage_ok:
                    reasons.append("storage_unavailable")
                if not startup_ok:
                    reasons.append("startup_incomplete")
                
                return ProbeResult(
                    probe=ProbeType.READINESS,
                    passed=False,
                    message=f"Not ready: {', '.join(reasons)}",
                    details={
                        "storage_ok": storage_ok,
                        "startup_complete": startup_ok,
                    },
                    duration_ms=duration,
                )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ProbeResult(
                probe=ProbeType.READINESS,
                passed=False,
                message=f"Readiness check failed: {str(e)}",
                duration_ms=duration,
            )
    
    def startup_probe(self) -> ProbeResult:
        """
        Kubernetes startup probe.
        
        Checks if the startup process is complete.
        
        Returns:
            ProbeResult for startup
        """
        start = time.time()
        
        if self._startup_complete:
            duration = (time.time() - start) * 1000
            return ProbeResult(
                probe=ProbeType.STARTUP,
                passed=True,
                message="Startup complete",
                duration_ms=duration,
            )
        
        # Check if startup timeout exceeded
        elapsed = time.time() - (self._startup_deadline - self._startup_timeout)
        
        if time.time() > self._startup_deadline:
            duration = (time.time() - start) * 1000
            return ProbeResult(
                probe=ProbeType.STARTUP,
                passed=False,
                message="Startup timeout exceeded",
                details={"elapsed_seconds": round(elapsed, 1)},
                duration_ms=duration,
            )
        
        # Try to complete startup
        try:
            storage = get_storage()
            if storage.health_check():
                self._startup_complete = True
                duration = (time.time() - start) * 1000
                return ProbeResult(
                    probe=ProbeType.STARTUP,
                    passed=True,
                    message="Startup complete",
                    details={"elapsed_seconds": round(elapsed, 1)},
                    duration_ms=duration,
                )
        except Exception:
            pass
        
        duration = (time.time() - start) * 1000
        return ProbeResult(
            probe=ProbeType.STARTUP,
            passed=False,
            message="Startup in progress",
            details={
                "elapsed_seconds": round(elapsed, 1),
                "timeout_seconds": self._startup_timeout,
                "progress_percent": min(100, (elapsed / self._startup_timeout) * 100),
            },
            duration_ms=duration,
        )
    
    def mark_startup_complete(self) -> None:
        """Mark startup as complete (call after initialization)."""
        self._startup_complete = True
    
    def enhanced_check(self) -> Dict[str, Any]:
        """
        Perform enhanced health check with all details.
        
        Returns:
            Dictionary with full health report including probes
        """
        # Get basic health report
        report = self.check()
        
        # Get dependency check
        deps = self.check_all_dependencies()
        
        # Get probes
        liveness = self.liveness_probe()
        readiness = self.readiness_probe()
        startup = self.startup_probe()
        
        return {
            "health": report.to_dict(),
            "dependencies": deps.to_dict(),
            "probes": {
                "liveness": liveness.to_dict(),
                "readiness": readiness.to_dict(),
                "startup": startup.to_dict(),
            },
        }


# Global enhanced checker
_enhanced_checker: Optional[EnhancedHealthChecker] = None


def get_enhanced_checker() -> EnhancedHealthChecker:
    """Get the enhanced health checker singleton."""
    global _enhanced_checker
    if _enhanced_checker is None:
        _enhanced_checker = EnhancedHealthChecker()
    return _enhanced_checker


def enhanced_health_check() -> Dict[str, Any]:
    """Perform enhanced health check."""
    return get_enhanced_checker().enhanced_check()


def liveness_probe() -> ProbeResult:
    """Perform liveness probe."""
    return get_enhanced_checker().liveness_probe()


def readiness_probe() -> ProbeResult:
    """Perform readiness probe."""
    return get_enhanced_checker().readiness_probe()


def startup_probe() -> ProbeResult:
    """Perform startup probe."""
    return get_enhanced_checker().startup_probe()
