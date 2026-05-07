# Health Checker
"""
Health check system for Neshama.

Provides health check endpoints for:
- Load balancers
- Monitoring systems
- Orchestration platforms (Kubernetes, etc.)

Health check levels:
- Simple: Basic server status
- Detailed: Component-level status
- Metrics: Prometheus-formatted metrics
"""

import os
import gc
import time
import logging
import psutil
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..storage import get_storage, StorageManager

logger = logging.getLogger(__name__)

# Health status
class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "status": self.status.value,
        }
        if self.message:
            result["message"] = self.message
        if self.latency_ms is not None:
            result["latency_ms"] = round(self.latency_ms, 2)
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class HealthReport:
    """Complete health report."""
    status: HealthStatus
    timestamp: str
    uptime_seconds: float
    version: str
    components: List[ComponentHealth]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "version": self.version,
            "components": [c.to_dict() for c in self.components],
        }


class HealthChecker:
    """
    Health checker for Neshama components.
    
    Provides:
    - Storage backend connectivity
    - Memory usage monitoring
    - Error rate tracking
    - Component-specific checks
    
    Example:
        >>> checker = HealthChecker()
        >>> report = checker.check()
        >>> print(f"Status: {report.status}")
    """
    
    def __init__(self):
        """Initialize health checker."""
        self._start_time = time.time()
        self._error_tracker: Dict[str, List[float]] = {}
        self._error_lock = None
    
    def _get_error_lock(self):
        """Get error tracker lock."""
        if self._error_lock is None:
            import threading
            self._error_lock = threading.Lock()
        return self._error_lock
    
    @property
    def uptime(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self._start_time
    
    def _get_version(self) -> str:
        """Get application version."""
        try:
            from neshama import __version__
            return __version__
        except Exception:
            return "unknown"
    
    def check_storage(self) -> ComponentHealth:
        """
        Check storage backend health.
        
        Returns:
            ComponentHealth for storage
        """
        start = time.time()
        
        try:
            storage = get_storage()
            is_healthy = storage.health_check()
            latency = (time.time() - start) * 1000
            
            if is_healthy:
                return ComponentHealth(
                    name="storage",
                    status=HealthStatus.HEALTHY,
                    message="Storage backend is healthy",
                    latency_ms=latency,
                    details={"backend": storage.backend_type},
                )
            else:
                return ComponentHealth(
                    name="storage",
                    status=HealthStatus.UNHEALTHY,
                    message="Storage backend is not responding",
                    latency_ms=latency,
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name="storage",
                status=HealthStatus.UNHEALTHY,
                message=f"Storage check failed: {str(e)}",
                latency_ms=latency,
            )
    
    def check_memory(self) -> ComponentHealth:
        """
        Check memory usage.
        
        Returns:
            ComponentHealth for memory
        """
        try:
            memory = psutil.virtual_memory()
            
            # Determine status based on usage
            if memory.percent < 70:
                status = HealthStatus.HEALTHY
            elif memory.percent < 85:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name="memory",
                status=status,
                message=f"Memory usage at {memory.percent:.1f}%",
                details={
                    "percent": memory.percent,
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2),
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}",
            )
    
    def check_cpu(self) -> ComponentHealth:
        """
        Check CPU usage.
        
        Returns:
            ComponentHealth for CPU
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            # Determine status
            if cpu_percent < 70:
                status = HealthStatus.HEALTHY
            elif cpu_percent < 90:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name="cpu",
                status=status,
                message=f"CPU usage at {cpu_percent:.1f}%",
                details={
                    "percent": cpu_percent,
                    "count": cpu_count,
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="cpu",
                status=HealthStatus.UNHEALTHY,
                message=f"CPU check failed: {str(e)}",
            )
    
    def check_disk(self) -> ComponentHealth:
        """
        Check disk usage.
        
        Returns:
            ComponentHealth for disk
        """
        try:
            disk = psutil.disk_usage("/")
            
            if disk.percent < 80:
                status = HealthStatus.HEALTHY
            elif disk.percent < 90:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name="disk",
                status=status,
                message=f"Disk usage at {disk.percent:.1f}%",
                details={
                    "percent": disk.percent,
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "total_gb": round(disk.total / (1024**3), 2),
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk check failed: {str(e)}",
            )
    
    def check_llm_providers(self) -> ComponentHealth:
        """
        Check LLM provider connectivity.
        
        Returns:
            ComponentHealth for LLM providers
        """
        # This is a lightweight check - just verify we can import the providers
        start = time.time()
        
        try:
            # Check if LLM provider module exists
            from neshama.voice import llm
            
            # Try to get configured providers
            providers = []
            try:
                # This is a placeholder - actual implementation would
                # check configured providers from config
                providers = ["openai", "anthropic"]  # Placeholder
            except Exception:
                pass
            
            latency = (time.time() - start) * 1000
            
            return ComponentHealth(
                name="llm_providers",
                status=HealthStatus.HEALTHY,
                message="LLM providers module accessible",
                latency_ms=latency,
                details={"configured_providers": providers},
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name="llm_providers",
                status=HealthStatus.DEGRADED,
                message=f"LLM providers module error: {str(e)}",
                latency_ms=latency,
            )
    
    def check_error_rate(self, window_minutes: int = 60) -> ComponentHealth:
        """
        Check error rate over a time window.
        
        Args:
            window_minutes: Time window in minutes
            
        Returns:
            ComponentHealth for error rate
        """
        try:
            with self._get_error_lock():
                now = time.time()
                cutoff = now - (window_minutes * 60)
                
                # Count errors in window
                error_count = 0
                for component, timestamps in self._error_tracker.items():
                    # Filter to window
                    recent = [t for t in timestamps if t >= cutoff]
                    self._error_tracker[component] = recent
                    error_count += len(recent)
            
            # Calculate error rate threshold
            # For now, use 5% of requests as threshold (requests ~= uptime * expected_rpm)
            expected_requests = self.uptime / 60 * 100  # Rough estimate
            error_threshold = max(10, expected_requests * 0.05)  # At least 10 errors
            
            if error_count <= error_threshold:
                status = HealthStatus.HEALTHY
            elif error_count <= error_threshold * 2:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name="error_rate",
                status=status,
                message=f"{error_count} errors in last {window_minutes} minutes",
                details={
                    "error_count": error_count,
                    "window_minutes": window_minutes,
                    "threshold": error_threshold,
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="error_rate",
                status=HealthStatus.HEALTHY,
                message=f"Error tracking unavailable: {str(e)}",
            )
    
    def record_error(self, component: str) -> None:
        """
        Record an error for rate tracking.
        
        Args:
            component: Component name where error occurred
        """
        with self._get_error_lock():
            if component not in self._error_tracker:
                self._error_tracker[component] = []
            self._error_tracker[component].append(time.time())
    
    def check(self) -> HealthReport:
        """
        Perform complete health check.
        
        Returns:
            HealthReport with all component statuses
        """
        components = [
            self.check_storage(),
            self.check_memory(),
            self.check_cpu(),
            self.check_disk(),
            self.check_llm_providers(),
            self.check_error_rate(),
        ]
        
        # Determine overall status
        statuses = [c.status for c in components]
        
        if HealthStatus.UNHEALTHY in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        return HealthReport(
            status=overall,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=self.uptime,
            version=self._get_version(),
            components=components,
        )
    
    def quick_check(self) -> Dict[str, str]:
        """
        Perform quick health check (for load balancer).
        
        Returns:
            Simple dict with status
        """
        try:
            storage = get_storage()
            if storage.health_check():
                return {"status": "healthy"}
            else:
                return {"status": "unhealthy", "reason": "storage_unavailable"}
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}


# Global singleton
_checker: Optional[HealthChecker] = None


def get_checker() -> HealthChecker:
    """Get the health checker singleton."""
    global _checker
    if _checker is None:
        _checker = HealthChecker()
    return _checker


def health_check() -> HealthReport:
    """Perform full health check."""
    return get_checker().check()


def quick_health_check() -> Dict[str, str]:
    """Perform quick health check."""
    return get_checker().quick_check()


def record_error(component: str) -> None:
    """Record an error for rate tracking."""
    get_checker().record_error(component)
