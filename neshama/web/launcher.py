"""
Neshama Soul Panel Launcher

Launches the Soul Panel desktop client using pywebview.
"""

import logging
import sys
import threading
import time

logger = logging.getLogger(__name__)


def launch_desktop(url: str, title: str = "Neshama Soul Panel", width: int = 1280, height: int = 800):
    """
    Launch pywebview desktop window.
    
    Args:
        url: URL to load in the window
        title: Window title
        width: Window width
        height: Window height
    """
    try:
        import webview
    except ImportError:
        logger.error("pywebview is not installed.")
        logger.error("Please install it with: pip install pywebview")
        logger.error("Or install Neshama with web extras: pip install neshama[web]")
        sys.exit(1)
    
    logger.info(f"Launching Soul Panel at {url}")
    
    # Create window
    window = webview.create_window(
        title=title,
        url=url,
        width=width,
        height=height,
        min_size=(800, 600),
        resizable=True,
        text_select_enabled=True,
    )
    
    # Start webview
    webview.start(debug=False)
    
    logger.info("Soul Panel closed")


def launch_with_server(
    host: str = "127.0.0.1",
    port: int = 8420,
    title: str = "Neshama Soul Panel",
    width: int = 1280,
    height: int = 800,
    debug: bool = False
):
    """
    Start FastAPI server and launch pywebview window.
    
    Args:
        host: Server host
        port: Server port
        title: Window title
        width: Window width
        height: Window height
        debug: Enable debug mode (browser instead of window)
    """
    if debug:
        # Open in browser instead
        import webbrowser
        import uvicorn
        
        # Start server in background thread
        server_thread = threading.Thread(
            target=lambda: uvicorn.run(
                "neshama.web.server:create_app",
                host=host,
                port=port,
                log_level="info",
            ),
            daemon=True
        )
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Open browser
        url = f"http://{host}:{port}"
        logger.info(f"Opening Soul Panel in browser: {url}")
        webbrowser.open(url)
        
        # Keep main thread alive
        try:
            while server_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Server stopped")
        
    else:
        # Start server and launch pywebview
        from neshama.web.server import ServerManager
        
        # Create server manager
        server = ServerManager(host=host, port=port)
        
        # Start server in background
        server.start(background=True)
        
        # Wait for server to start
        time.sleep(2)
        
        # Launch desktop window
        launch_desktop(
            url=server.url,
            title=title,
            width=width,
            height=height
        )
        
        # Stop server when window closes
        server.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    launch_with_server()
