"""
Neshama Web Server

FastAPI server for Soul Panel desktop client.
Production-ready with:
- Graceful shutdown handling
- Health check endpoints
- Rate limiting and concurrency control
- Sentry error tracking
"""

import asyncio
import signal
import threading
import logging
import os
import time
from typing import Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from .api import (
    soul, emotion, memory, evolution, chat, config, 
    composite_emotion, entity_graph, progressive_summarization, 
    model_marketplace, coding_plans, game, provider, health as health_api,
    gdpr, auth,
)

# Import monitoring
from neshama.monitoring import init_sentry, capture_exception

# Import middleware
from .middleware import get_limiter, get_middleware

logger = logging.getLogger(__name__)

# Global shutdown state
_shutdown_initiated = False
_active_requests = 0
_shutdown_lock = threading.Lock()


def get_static_path() -> Path:
    """Get the static files path."""
    return Path(__file__).parent / "static"


class GracefulShutdown:
    """Manages graceful shutdown of the application."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize graceful shutdown manager.
        
        Args:
            timeout: Maximum seconds to wait for requests to complete
        """
        self._timeout = timeout
        self._shutdown_event = asyncio.Event()
        self._background_tasks: list = []
        self._services: list = []
        self._finalizers: list = []
        self._shutdown_initiated = False
        self._shutdown_complete = asyncio.Event()
    
    def register_background_task(self, task):
        """Register a background task for tracking."""
        self._background_tasks.append(task)
    
    def register_service(self, service):
        """Register a service for clean shutdown."""
        self._services.append(service)
    
    def register_finalizer(self, finalizer: callable):
        """
        Register a finalizer function to be called during shutdown.
        
        Args:
            finalizer: A callable that takes no arguments.
        """
        self._finalizers.append(finalizer)
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()
        await self._shutdown_complete.wait()
    
    def initiate_shutdown(self):
        """Initiate graceful shutdown."""
        global _shutdown_initiated
        if self._shutdown_initiated:
            return
        self._shutdown_initiated = True
        _shutdown_initiated = True
        
        logger.info("Graceful shutdown initiated...")
        
        # Stop accepting new requests
        self._shutdown_event.set()
        
        # Wait for active requests to complete
        start_time = time.time()
        while _active_requests > 0:
            elapsed = time.time() - start_time
            if elapsed >= self._timeout:
                logger.warning(
                    f"Shutdown timeout ({self._timeout}s) reached with "
                    f"{_active_requests} active requests"
                )
                break
            logger.info(f"Waiting for {_active_requests} active requests...")
            time.sleep(0.5)
        
        # Cancel background tasks
        for task in self._background_tasks:
            try:
                if hasattr(task, 'cancel'):
                    task.cancel()
            except Exception as e:
                logger.warning(f"Error canceling task: {e}")
        
        # Shutdown services
        for service in self._services:
            try:
                if hasattr(service, 'shutdown'):
                    if asyncio.iscoroutinefunction(service.shutdown):
                        # Run async shutdown in sync context
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.create_task(service.shutdown())
                            else:
                                loop.run_until_complete(service.shutdown())
                        except RuntimeError:
                            pass
                    else:
                        service.shutdown()
                elif hasattr(service, 'close'):
                    service.close()
            except Exception as e:
                logger.warning(f"Error shutting down service: {e}")
        
        # Close storage connections
        try:
            from ...storage import StorageManager
            StorageManager.reset_instance()
        except Exception as e:
            logger.warning(f"Error closing storage: {e}")
        
        # Run finalizers
        for finalizer in self._finalizers:
            try:
                if callable(finalizer):
                    finalizer()
            except Exception as e:
                logger.warning(f"Error running finalizer: {e}")
        
        # Mark shutdown complete
        self._shutdown_complete.set()
        logger.info("Graceful shutdown completed")
    
    async def async_initiate_shutdown(self):
        """Initiate graceful shutdown asynchronously."""
        # Wait for active requests
        start_time = time.time()
        while _active_requests > 0:
            elapsed = time.time() - start_time
            if elapsed >= self._timeout:
                logger.warning(
                    f"Shutdown timeout ({self._timeout}s) reached with "
                    f"{_active_requests} active requests"
                )
                break
            await asyncio.sleep(0.5)
        
        # Run finalizers
        for finalizer in self._finalizers:
            try:
                if asyncio.iscoroutinefunction(finalizer):
                    await finalizer()
                elif callable(finalizer):
                    finalizer()
            except Exception as e:
                logger.warning(f"Error running finalizer: {e}")
        
        # Mark shutdown complete
        self._shutdown_complete.set()
        logger.info("Async graceful shutdown completed")


# Global shutdown manager
_shutdown_manager: Optional[GracefulShutdown] = None


def get_shutdown_manager() -> GracefulShutdown:
    """Get the global shutdown manager."""
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = GracefulShutdown(timeout=30)
    return _shutdown_manager


def _setup_signal_handlers(loop: asyncio.AbstractEventLoop):
    """Setup signal handlers for graceful shutdown."""
    shutdown_mgr = get_shutdown_manager()
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        shutdown_mgr.initiate_shutdown()
    
    def async_signal_handler():
        shutdown_mgr.initiate_shutdown()
    
    # Handle SIGTERM (container orchestrators)
    if hasattr(signal, 'SIGTERM'):
        try:
            loop.add_signal_handler(
                signal.SIGTERM,
                async_signal_handler
            )
            logger.info("SIGTERM handler registered")
        except (NotImplementedError, OSError):
            # Windows doesn't support add_signal_handler
            pass
    
    # Handle SIGINT (Ctrl+C)
    try:
        loop.add_signal_handler(
            signal.SIGINT,
            async_signal_handler
        )
        logger.info("SIGINT handler registered")
    except (NotImplementedError, OSError):
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Neshama Soul Panel starting...")
    
    # Initialize Sentry (optional)
    init_sentry()
    
    # Get shutdown manager and register services
    shutdown_mgr = get_shutdown_manager()
    
    # Register storage for cleanup
    try:
        from ...storage import StorageManager
        storage = StorageManager.get_instance()
        shutdown_mgr.register_service(storage)
    except Exception as e:
        logger.warning(f"Could not register storage: {e}")
    
    # Register HTTP connection pool for cleanup
    try:
        from .connection_pool import get_http_pool, reset_http_pool
        http_pool = get_http_pool()
        shutdown_mgr.register_finalizer(reset_http_pool)
    except Exception as e:
        logger.warning(f"Could not register HTTP pool: {e}")
    
    # Register enhanced health checker to mark startup complete
    try:
        from ...monitoring import get_enhanced_checker
        health_checker = get_enhanced_checker()
        shutdown_mgr.register_finalizer(lambda: health_checker.mark_startup_complete())
    except Exception as e:
        logger.warning(f"Could not register health checker: {e}")
    
    # Register rate limit manager cleanup
    try:
        from .api.session import reset_rate_limit_manager
        shutdown_mgr.register_finalizer(reset_rate_limit_manager)
    except Exception as e:
        logger.warning(f"Could not register rate limit cleanup: {e}")
    
    # Mark startup complete
    try:
        from ...monitoring import get_enhanced_checker
        get_enhanced_checker().mark_startup_complete()
    except Exception:
        pass
    
    logger.info("Neshama Soul Panel ready")
    
    yield
    
    # Shutdown
    logger.info("Neshama Soul Panel shutting down...")
    
    # Async shutdown for connection pools
    try:
        from .connection_pool import get_http_pool
        http_pool = get_http_pool()
        await http_pool.async_close()
    except Exception as e:
        logger.warning(f"Error closing HTTP pool: {e}")
    
    # Sync shutdown
    shutdown_mgr.initiate_shutdown()


async def request_start_hook(request: Request):
    """Called when a request starts."""
    global _active_requests
    with _shutdown_lock:
        _active_requests += 1


async def request_end_hook(request: Request):
    """Called when a request ends."""
    global _active_requests
    with _shutdown_lock:
        _active_requests = max(0, _active_requests - 1)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Neshama Soul Panel",
        description="Desktop client for Neshama AI Agent Personality System",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Add request tracking middleware
    @app.middleware("http")
    async def track_requests(request: Request, call_next):
        await request_start_hook(request)
        try:
            response = await call_next(request)
            return response
        finally:
            await request_end_hook(request)
    
    # Add error handling middleware
    @app.middleware("http")
    async def error_handling_middleware(request: Request, call_next):
        try:
            response = await call_next(request)
            # Track 5xx errors
            if response.status_code >= 500:
                from ...monitoring import record_error
                record_error("api_5xx")
                capture_exception(
                    context={
                        "request": {
                            "method": request.method,
                            "path": str(request.url.path),
                            "status_code": response.status_code,
                        }
                    }
                )
            return response
        except Exception as e:
            # Capture unhandled exceptions
            from ...monitoring import record_error
            record_error("api_exception")
            capture_exception(
                exc_info=True,
                context={
                    "request": {
                        "method": request.method,
                        "path": str(request.url.path),
                    }
                }
            )
            raise
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add concurrency limiter middleware
    try:
        concurrency_limiter = get_limiter(max_concurrent=100)
        app.add_middleware(concurrency_limiter.get_middleware())
    except Exception as e:
        logger.warning(f"Could not add concurrency limiter: {e}")
    
    # Add rate limit middleware
    try:
        rate_limit_middleware = get_middleware()
        app.add_middleware(rate_limit_middleware.get_middleware())
    except Exception as e:
        logger.warning(f"Could not add rate limit middleware: {e}")
    
    # Mount static files
    static_path = get_static_path()
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Include API routers
    app.include_router(soul.router, prefix="/api/soul", tags=["Soul"])
    app.include_router(emotion.router, prefix="/api/emotion", tags=["Emotion"])
    app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
    app.include_router(evolution.router, prefix="/api/evolution", tags=["Evolution"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(config.router, prefix="/api/config", tags=["Config"])
    app.include_router(composite_emotion.router, prefix="/api/composite-emotion", tags=["Composite Emotion"])
    app.include_router(entity_graph.router, prefix="/api/entity-graph", tags=["Entity Graph"])
    app.include_router(progressive_summarization.router, prefix="/api/summarization", tags=["Progressive Summarization"])
    app.include_router(model_marketplace.router, prefix="/api/models", tags=["Model Marketplace"])
    app.include_router(coding_plans.router, prefix="/api/coding-plans", tags=["Coding Plans"])
    app.include_router(game.router, prefix="/api/game", tags=["Game NPC"])
    app.include_router(provider.router, prefix="/api/provider", tags=["Provider Management"])
    app.include_router(health_api.router, tags=["Health"])
    app.include_router(gdpr.router, prefix="/api/gdpr", tags=["GDPR"])
    app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
    
    # SPA fallback
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA for all non-API routes."""
        index_path = static_path / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text())
        raise HTTPException(status_code=404, detail="Soul Panel not found")
    
    @app.get("/")
    async def root():
        """Serve the SPA root."""
        index_path = static_path / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text())
        raise HTTPException(status_code=404, detail="Soul Panel not found")
    
    return app


def start_server(host: str = "127.0.0.1", port: int = 8420, debug: bool = False):
    """Start the FastAPI server."""
    app = create_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info",
    )


class ServerManager:
    """Manages the FastAPI server lifecycle."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8420):
        self.host = host
        self.port = port
        self._server = None
        self._thread: Optional[threading.Thread] = None
        self._shutdown_event = asyncio.Event()
        self._shutdown_manager = GracefulShutdown(timeout=30)

    def start(self, background: bool = False):
        """Start the server."""
        if background:
            self._thread = threading.Thread(
                target=self._run_server,
                daemon=True,
                name="NeshamaServer"
            )
            self._thread.start()
            logger.info(f"Server starting in background on {self.host}:{self.port}")
        else:
            self._run_server()

    def _run_server(self):
        """Run the server (blocking)."""
        import uvicorn
        uvicorn.run(
            "neshama.web.server:create_app",
            factory=True,
            host=self.host,
            port=self.port,
            log_level="info",
        )

    def stop(self):
        """Stop the server."""
        self._shutdown_manager.initiate_shutdown()
        self._shutdown_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Server stopped")
    
    async def _async_stop(self):
        """Stop the server asynchronously."""
        self._shutdown_manager.initiate_shutdown()
        self._shutdown_event.set()

    @property
    def url(self) -> str:
        """Get the server URL."""
        return f"http://{self.host}:{self.port}"
    
    @property
    def shutdown_timeout(self) -> int:
        """Get shutdown timeout in seconds."""
        return self._shutdown_manager._timeout
    
    @shutdown_timeout.setter
    def shutdown_timeout(self, value: int):
        """Set shutdown timeout in seconds."""
        self._shutdown_manager._timeout = value


def launch_pywebview(url: str, title: str = "Neshama Soul Panel", width: int = 1280, height: int = 800):
    """Launch pywebview window."""
    try:
        import webview
    except ImportError:
        logger.error("pywebview not installed. Install with: pip install pywebview")
        raise

    window = webview.create_window(
        title=title,
        url=url,
        width=width,
        height=height,
        min_size=(800, 600),
        resizable=True,
        js_api=None,
    )

    webview.start(debug=False)
