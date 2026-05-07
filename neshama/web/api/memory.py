"""
Memory API - Three-layer memory management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import random
import uuid

from fastapi import APIRouter, HTTPException

from .cache import get_memory_cache, invalidate_memory_cache

router = APIRouter()

# Mock memory data
MOCK_MEMORY = {
    "L0": [  # Working memory (short-term)
        {"id": "w1", "content": "User is working on a Python project", "timestamp": datetime.now().isoformat(), "importance": 0.8},
        {"id": "w2", "content": "Discussing AI agent architecture", "timestamp": datetime.now().isoformat(), "importance": 0.7},
        {"id": "w3", "content": "User mentioned preference for concise explanations", "timestamp": datetime.now().isoformat(), "importance": 0.6}
    ],
    "L1": [  # Episodic memory (contextual)
        {"id": "e1", "content": "Session on 2024-01-15: User learned about OCEAN model", "timestamp": "2024-01-15T10:30:00", "importance": 0.9, "context": "Learning session"},
        {"id": "e2", "content": "Session on 2024-01-14: Creative writing practice", "timestamp": "2024-01-14T15:00:00", "importance": 0.7, "context": "Creative exercise"},
        {"id": "e3", "content": "User asked about memory systems", "timestamp": "2024-01-13T09:00:00", "importance": 0.8, "context": "Technical discussion"}
    ],
    "L2": [  # Semantic memory (knowledge)
        {"id": "s1", "content": "Python best practices for AI applications", "timestamp": "2024-01-10", "importance": 0.9, "source": "Learning"},
        {"id": "s2", "content": "User prefers morning productivity", "timestamp": "2024-01-08", "importance": 0.7, "source": "Observation"},
        {"id": "s3", "content": "Design patterns for agent systems", "timestamp": "2024-01-05", "importance": 0.8, "source": "Research"}
    ]
}

LAYER_NAMES = {
    "L0": "Working Memory",
    "L1": "Episodic Memory", 
    "L2": "Semantic Memory"
}

LAYER_DESCRIPTIONS = {
    "L0": "Current conversation context and immediate information",
    "L1": "Personal experiences and contextual episodes",
    "L2": "General knowledge, facts, and learned concepts"
}

# 缓存键和TTL
CACHE_KEY_STATS = "memory_stats"
CACHE_KEY_LAYERS = "memory_layers"
CACHE_TTL = 10  # 10秒缓存


@router.get("/layers")
async def get_memory_layers():
    """Get all memory layers with stats (cached for 10 seconds)."""
    cache = get_memory_cache()
    
    # 尝试从缓存获取
    cached_data = cache.get(CACHE_KEY_LAYERS)
    if cached_data is not None:
        return {
            "success": True,
            "data": cached_data,
            "cached": True
        }
    
    # 生成新数据
    data = {
        "layers": [
            {
                "id": layer,
                "name": LAYER_NAMES[layer],
                "description": LAYER_DESCRIPTIONS[layer],
                "count": len(memories)
            }
            for layer, memories in MOCK_MEMORY.items()
        ]
    }
    
    # 存入缓存
    cache.set(CACHE_KEY_LAYERS, data, CACHE_TTL)
    
    return {
        "success": True,
        "data": data,
        "cached": False
    }


@router.get("/{layer}")
async def get_memory_layer(layer: str, search: Optional[str] = None, limit: int = 50):
    """Get memories from a specific layer."""
    if layer not in MOCK_MEMORY:
        raise HTTPException(status_code=404, detail=f"Memory layer '{layer}' not found")
    
    memories = MOCK_MEMORY[layer]
    
    # Filter by search term
    if search:
        search_lower = search.lower()
        memories = [m for m in memories if search_lower in m.get("content", "").lower()]
    
    # Limit results
    memories = memories[:limit]
    
    return {
        "success": True,
        "data": {
            "layer": layer,
            "name": LAYER_NAMES[layer],
            "memories": memories,
            "total": len(MOCK_MEMORY[layer])
        }
    }


@router.post("/{layer}")
async def add_memory(layer: str, memory_item: Dict[str, Any]):
    """Add a new memory to a layer."""
    if layer not in MOCK_MEMORY:
        raise HTTPException(status_code=404, detail=f"Memory layer '{layer}' not found")
    
    required_fields = ["content"]
    for field in required_fields:
        if field not in memory_item:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    new_memory = {
        "id": str(uuid.uuid4())[:8],
        "content": memory_item["content"],
        "timestamp": datetime.now().isoformat(),
        "importance": memory_item.get("importance", 0.5),
        "context": memory_item.get("context"),
        "source": memory_item.get("source")
    }
    
    MOCK_MEMORY[layer].insert(0, new_memory)
    
    # 使缓存失效
    invalidate_memory_cache()
    
    return {
        "success": True,
        "data": new_memory,
        "message": "Memory added successfully"
    }


@router.delete("/{layer}/{memory_id}")
async def delete_memory(layer: str, memory_id: str):
    """Delete a memory from a layer."""
    if layer not in MOCK_MEMORY:
        raise HTTPException(status_code=404, detail=f"Memory layer '{layer}' not found")
    
    original_length = len(MOCK_MEMORY[layer])
    MOCK_MEMORY[layer] = [m for m in MOCK_MEMORY[layer] if m["id"] != memory_id]
    
    if len(MOCK_MEMORY[layer]) == original_length:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    
    # 使缓存失效
    invalidate_memory_cache()
    
    return {
        "success": True,
        "message": "Memory deleted successfully"
    }


@router.put("/{layer}/{memory_id}")
async def update_memory(layer: str, memory_id: str, updates: Dict[str, Any]):
    """Update a memory in a layer."""
    if layer not in MOCK_MEMORY:
        raise HTTPException(status_code=404, detail=f"Memory layer '{layer}' not found")
    
    for memory in MOCK_MEMORY[layer]:
        if memory["id"] == memory_id:
            memory.update({k: v for k, v in updates.items() if k != "id"})
            memory["updated_at"] = datetime.now().isoformat()
            
            # 使缓存失效
            invalidate_memory_cache()
            
            return {
                "success": True,
                "data": memory,
                "message": "Memory updated successfully"
            }
    
    raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")


@router.get("/stats/overview")
async def get_memory_stats():
    """
    Get overall memory statistics.
    
    Cached for 10 seconds to reduce database/query load.
    Statistics are less time-sensitive than individual memory access.
    """
    cache = get_memory_cache()
    
    # 尝试从缓存获取
    cached_data = cache.get(CACHE_KEY_STATS)
    if cached_data is not None:
        return {
            "success": True,
            "data": cached_data,
            "cached": True
        }
    
    # 生成新数据
    stats = {
        "total_memories": sum(len(memories) for memories in MOCK_MEMORY.values()),
        "by_layer": {
            layer: len(memories) for layer, memories in MOCK_MEMORY.items()
        },
        "recent_additions": 12,
        "knowledge_topics": 8,
        "last_updated": datetime.now().isoformat()
    }
    
    # 存入缓存
    cache.set(CACHE_KEY_STATS, stats, CACHE_TTL)
    
    return {
        "success": True,
        "data": stats,
        "cached": False
    }
