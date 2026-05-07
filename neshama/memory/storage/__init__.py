# Memory Layer - Storage Module
"""
Storage Backend Module

Contains:
- file_storage.py - File-based storage
- vector_store.py - Vector storage for embeddings
"""

from .file_storage import FileStorage
from .vector_store import VectorStore

__all__ = [
    "FileStorage",
    "VectorStore",
]
