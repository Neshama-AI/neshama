# Health Check API
"""
Health check endpoints for Neshama.

Provides:
- GET /health - Simple health check for load balancers
- GET /health/detailed - Detailed component health
- GET /metrics - Prometheus-format metrics
"""

import time
import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Response

from ...monitoring.health import (
    HealthStatus,
    health_check as _health_check,
    quick_health_check as _quick_health_check,
)
from ...monitoring.enhanced_health import (
    enhanced_health_check as _enhanced_health_check,
    liveness_probe,
    readiness_probe,
    startup_probe,
)
from ..middleware import get_stats, get_metrics as get_rate_limit_metrics
from .rate_limiter import get_metrics_collector

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    """
    Simple health check endpoint.
    
    For use by load balancers and orchestration systems.
    Returns only basic status.
    """
    result = _quick_health_check()
    return result


@router.get("/health/detailed")
async def health_detailed():
    """
    Detailed health check endpoint.
    
    Returns comprehensive health status of all components:
    - Storage backend
    - Memory usage
    - CPU usage
    - Disk usage
    - LLM providers
    - Error rate
    
    Use this for monitoring dashboards and detailed diagnostics.
    """
    report = _health_check()
    return report.to_dict()


@router.get("/metrics")
async def metrics(response: Response):
    """
    Prometheus-format metrics endpoint.
    
    Returns metrics in Prometheus exposition format.
    Suitable for scraping by Prometheus or similar systems.
    """
    # Get health report
    health_report = _health_check()
    
    # Get rate limit metrics
    rate_metrics = get_rate_limit_metrics()
    
    # Get concurrency metrics
    concurrency_stats = get_stats()
    
    # Get rate limiter metrics
    limiter_metrics = get_metrics_collector().get_metrics()
    
    # Build Prometheus-format output
    lines = []
    timestamp = int(time.time() * 1000)
    
    # Neshama info
    lines.append(f"# HELP neshama_info Neshama application info")
    lines.append(f"# TYPE neshama_info gauge")
    lines.append(f'neshama_info{{version="{health_report.version}"}} 1')
    
    # Health status (1 = healthy, 0.5 = degraded, 0 = unhealthy)
    status_value = 1.0
    if health_report.status == HealthStatus.DEGRADED:
        status_value = 0.5
    elif health_report.status == HealthStatus.UNHEALTHY:
        status_value = 0.0
    lines.append(f"# HELP neshama_health_status Overall health status")
    lines.append(f"# TYPE neshama_health_status gauge")
    lines.append(f"neshama_health_status {status_value}")
    
    # Uptime
    lines.append(f"# HELP neshama_uptime_seconds Application uptime")
    lines.append(f"# TYPE neshama_uptime_seconds counter")
    lines.append(f"neshama_uptime_seconds {health_report.uptime_seconds}")
    
    # Component health
    for component in health_report.components:
        status_val = 1.0
        if component.status == HealthStatus.DEGRADED:
            status_val = 0.5
        elif component.status == HealthStatus.UNHEALTHY:
            status_val = 0.0
        lines.append(f"# HELP neshama_component_health Component health status")
        lines.append(f"# TYPE neshama_component_health gauge")
        lines.append(f'neshama_component_health{{component="{component.name}"}} {status_val}')
        
        if component.latency_ms is not None:
            lines.append(f"# HELP neshama_component_latency_ms Component check latency")
            lines.append(f"# TYPE neshama_component_latency_ms gauge")
            lines.append(f'neshama_component_latency_ms{{component="{component.name}"}} {component.latency_ms}')
    
    # Rate limiting metrics
    lines.append(f"# HELP neshama_rate_limit_total Total rate limit checks")
    lines.append(f"# TYPE neshama_rate_limit_total counter")
    lines.append(f"neshama_rate_limit_total {rate_metrics.total_checks}")
    
    lines.append(f"# HELP neshama_rate_limit_allowed Allowed requests")
    lines.append(f"# TYPE neshama_rate_limit_allowed counter")
    lines.append(f"neshama_rate_limit_allowed {rate_metrics.total_allowed}")
    
    lines.append(f"# HELP neshama_rate_limit_rejected Rejected requests")
    lines.append(f"# TYPE neshama_rate_limit_rejected counter")
    lines.append(f"neshama_rate_limit_rejected {rate_metrics.total_rejected}")
    
    lines.append(f"# HELP neshama_rate_limit_ip_blocked IP blocked requests")
    lines.append(f"# TYPE neshama_rate_limit_ip_blocked counter")
    lines.append(f"neshama_rate_limit_ip_blocked {rate_metrics.ip_blocked}")
    
    # Concurrency metrics
    lines.append(f"# HELP neshama_concurrency_current Current concurrent requests")
    lines.append(f"# TYPE neshama_concurrency_current gauge")
    lines.append(f"neshama_concurrency_current {concurrency_stats.current_concurrent}")
    
    lines.append(f"# HELP neshama_concurrency_limit Maximum concurrent requests")
    lines.append(f"# TYPE neshama_concurrency_limit gauge")
    lines.append(f"neshama_concurrency_limit {concurrency_stats.max_concurrent}")
    
    lines.append(f"# HELP neshama_concurrency_rejected Rejected due to concurrency")
    lines.append(f"# TYPE neshama_concurrency_rejected counter")
    lines.append(f"neshama_concurrency_rejected {concurrency_stats.rejected_requests}")
    
    # Extended rate limiter metrics
    lines.append(f"# HELP neshama_requests_total Total requests processed")
    lines.append(f"# TYPE neshama_requests_total counter")
    lines.append(f"neshama_requests_total {limiter_metrics['total_requests']}")
    
    lines.append(f"# HELP neshama_requests_allowed Allowed requests")
    lines.append(f"# TYPE neshama_requests_allowed counter")
    lines.append(f"neshama_requests_allowed {limiter_metrics['allowed_requests']}")
    
    lines.append(f"# HELP neshama_requests_rejected Rejected requests")
    lines.append(f"# TYPE neshama_requests_rejected counter")
    lines.append(f"neshama_requests_rejected {limiter_metrics['rejected_requests']}")
    
    # Memory details (from components)
    for component in health_report.components:
        if component.name == "memory" and component.details:
            mem = component.details
            lines.append(f"# HELP neshama_memory_percent Memory usage percent")
            lines.append(f"# TYPE neshama_memory_percent gauge")
            lines.append(f"neshama_memory_percent {mem.get('percent', 0)}")
            
            lines.append(f"# HELP neshama_memory_used_bytes Memory used in bytes")
            lines.append(f"# TYPE neshama_memory_used_bytes gauge")
            used_gb = mem.get('used_gb', 0)
            lines.append(f"neshama_memory_used_bytes {used_gb * 1024 * 1024 * 1024}")
    
    # CPU details
    for component in health_report.components:
        if component.name == "cpu" and component.details:
            cpu = component.details
            lines.append(f"# HELP neshama_cpu_percent CPU usage percent")
            lines.append(f"# TYPE neshama_cpu_percent gauge")
            lines.append(f"neshama_cpu_percent {cpu.get('percent', 0)}")
    
    # Build final response
    output = "\n".join(lines) + "\n"
    
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return output


@router.get("/status")
async def status():
    """
    Combined status endpoint.
    
    Returns a summary of system status including:
    - Health check summary
    - Key metrics
    - Version info
    """
    health_report = _health_check()
    rate_metrics = get_rate_limit_metrics()
    limiter_metrics = get_metrics_collector().get_metrics()
    concurrency_stats = get_stats()
    
    return {
        "status": health_report.status.value,
        "version": health_report.version,
        "uptime_seconds": round(health_report.uptime_seconds, 2),
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "requests": {
                "total": limiter_metrics["total_requests"],
                "allowed": limiter_metrics["allowed_requests"],
                "rejected": limiter_metrics["rejected_requests"],
                "rejection_rate": limiter_metrics["rejection_rate"],
            },
            "rate_limiting": {
                "total_checks": rate_metrics.total_checks,
                "allowed": rate_metrics.total_allowed,
                "rejected": rate_metrics.total_rejected,
                "ip_blocked": rate_metrics.ip_blocked,
            },
            "concurrency": {
                "current": concurrency_stats.current_concurrent,
                "max": concurrency_stats.max_concurrent,
                "rejected": concurrency_stats.rejected_requests,
            },
        },
        "components": {
            c.name: {
                "status": c.status.value,
                "message": c.message,
            }
            for c in health_report.components
        },
    }


# Kubernetes Probe Endpoints

@router.get("/health/liveness")
async def probe_liveness():
    """
    Kubernetes liveness probe.
    
    Returns 200 if the process is alive.
    Returns 503 if the process is not alive.
    
    Use this for Kubernetes liveness checks.
    """
    result = liveness_probe()
    
    if result.passed:
        return {
            "status": "alive",
            "message": result.message,
            "details": result.details,
        }
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_alive",
                "message": result.message,
                "details": result.details,
            }
        )


@router.get("/health/readiness")
async def probe_readiness():
    """
    Kubernetes readiness probe.
    
    Returns 200 if the process is ready to receive traffic.
    Returns 503 if the process is not ready.
    
    Use this for Kubernetes readiness checks.
    """
    result = readiness_probe()
    
    if result.passed:
        return {
            "status": "ready",
            "message": result.message,
            "details": result.details,
        }
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "message": result.message,
                "details": result.details,
            }
        )


@router.get("/health/startup")
async def probe_startup():
    """
    Kubernetes startup probe.
    
    Returns 200 if startup is complete.
    Returns 503 if startup is still in progress or failed.
    
    Use this for Kubernetes startup checks.
    """
    result = startup_probe()
    
    if result.passed:
        return {
            "status": "started",
            "message": result.message,
            "details": result.details,
        }
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={
                "status": "starting",
                "message": result.message,
                "details": result.details,
            }
        )


@router.get("/health/enhanced")
async def health_enhanced():
    """
    Enhanced health check with all components and probes.
    
    Returns comprehensive health status including:
    - Basic health report
    - Dependency checks
    - Kubernetes probe results
    
    Use this for detailed diagnostics and monitoring.
    """
    return _enhanced_health_check()
