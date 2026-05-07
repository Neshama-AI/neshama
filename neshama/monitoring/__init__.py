# Monitoring Module
"""
Monitoring module for Neshama.

Provides monitoring and observability:
- Sentry error tracking
- Health checks (basic and enhanced)
- Metrics collection
- Kubernetes probe support

Usage:
    from neshama.monitoring import init_sentry, health_check
    
    # Initialize Sentry (optional)
    init_sentry()
    
    # Check health
    report = health_check()
    print(f"Status: {report.status}")
    
    # Enhanced health checks with Kubernetes probes
    from neshama.monitoring import (
        enhanced_health_check,
        liveness_probe,
        readiness_probe,
        startup_probe,
    )
    
    # Full health report
    report = enhanced_health_check()
    
    # Specific probes
    if readiness_probe().passed:
        print("Ready to serve traffic")
"""

from .sentry import SentryIntegration, init_sentry, capture_exception, capture_message
from .health import (
    HealthChecker,
    HealthStatus,
    HealthReport,
    ComponentHealth,
    health_check,
    quick_health_check,
    record_error,
    get_checker,
)

# Import enhanced health checks
from .enhanced_health import (
    EnhancedHealthChecker,
    ProbeType,
    ProbeResult,
    enhanced_health_check,
    liveness_probe,
    readiness_probe,
    startup_probe,
    get_enhanced_checker,
)

# Import rate limiter metrics collector
# Note: This is imported from web.api.rate_limiter to avoid circular imports
def _get_metrics_collector():
    from neshama.web.api.rate_limiter import get_metrics_collector as _get
    return _get()

__all__ = [
    # Sentry
    "SentryIntegration",
    "init_sentry",
    "capture_exception",
    "capture_message",
    # Health (basic)
    "HealthChecker",
    "HealthStatus",
    "HealthReport",
    "ComponentHealth",
    "health_check",
    "quick_health_check",
    "record_error",
    "get_checker",
    # Health (enhanced)
    "EnhancedHealthChecker",
    "ProbeType",
    "ProbeResult",
    "enhanced_health_check",
    "liveness_probe",
    "readiness_probe",
    "startup_probe",
    "get_enhanced_checker",
]
