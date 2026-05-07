# Soul Layer - Learning Module
"""
Learning System Module

Contains:
- knowledge.py - Knowledge management
- forgetting.py - Forgetting mechanism
"""

from .knowledge import (
    KnowledgeGraph,
    KnowledgeNode,
    KnowledgeConnection,
    KnowledgeType,
    knowledge_graph,
    add_knowledge,
    retrieve_knowledge
)

from .forgetting import (
    ForgettingMechanism,
    MemoryItem,
    ForgettingConfig,
    ForgettingCurve,
    forgetting_mechanism,
    add_memory,
    access_memory,
    process_forgetting,
    get_memory_stats
)

__all__ = [
    # Knowledge
    "KnowledgeGraph",
    "KnowledgeNode",
    "KnowledgeConnection",
    "KnowledgeType",
    "knowledge_graph",
    "add_knowledge",
    "retrieve_knowledge",
    
    # Forgetting
    "ForgettingMechanism",
    "MemoryItem",
    "ForgettingConfig",
    "ForgettingCurve",
    "forgetting_mechanism",
    "add_memory",
    "access_memory",
    "process_forgetting",
    "get_memory_stats"
]
