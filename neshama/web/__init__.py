"""
Neshama Web Module

Desktop client management panel for Neshama Soul.
"""

__version__ = "1.0.0"

from .server import create_app, start_server

__all__ = ["create_app", "start_server"]
