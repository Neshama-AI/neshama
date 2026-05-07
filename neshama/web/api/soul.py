"""
Soul API - OCEAN personality configuration management.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import random

from fastapi import APIRouter, HTTPException

from .cache import get_soul_cache, invalidate_soul_cache

router = APIRouter()

# In-memory mock data (in production, this would connect to real Neshama engine)
MOCK_SOUL_CONFIG = {
    "name": "Neshama",
    "ocean": {
        "openness": 0.75,
        "conscientiousness": 0.65,
        "extraversion": 0.55,
        "agreeableness": 0.60,
        "neuroticism": 0.45
    },
    "traits": {
        "directness": 0.6,
        "humor_level": 0.5,
        "empathy_level": 0.7,
        "curiosity": 0.8,
        "creativity": 0.75
    },
    "desires": [
        {"id": "curiosity", "name": "好奇心", "priority": 1, "active": True},
        {"id": "connection", "name": "连接感", "priority": 2, "active": True},
        {"id": "growth", "name": "成长", "priority": 3, "active": True},
        {"id": "autonomy", "name": "自主性", "priority": 4, "active": True},
        {"id": "purpose", "name": "意义感", "priority": 5, "active": True},
        {"id": "stability", "name": "稳定性", "priority": 6, "active": False}
    ],
    "presets": ["analyst", "helper", "explorer", "leader", "diplomat", "sentinel", "neshama"]
}

# 缓存键
CACHE_KEY_SOUL = "soul_config"
CACHE_TTL = 30  # 30秒缓存


@router.get("/")
async def get_soul():
    """Get current soul configuration (cached for 30 seconds)."""
    cache = get_soul_cache()
    
    # 尝试从缓存获取
    cached_data = cache.get(CACHE_KEY_SOUL)
    if cached_data is not None:
        cached_data["cached"] = True
        return cached_data
    
    # 生成新数据
    response = {
        "success": True,
        "data": MOCK_SOUL_CONFIG.copy(),
        "timestamp": datetime.now().isoformat(),
        "cached": False
    }
    
    # 存入缓存
    cache.set(CACHE_KEY_SOUL, response, CACHE_TTL)
    
    return response


@router.put("/")
async def update_soul(config: Dict[str, Any]):
    """Update soul configuration."""
    try:
        # Validate OCEAN values
        ocean = config.get("ocean", {})
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            if trait in ocean:
                value = ocean[trait]
                if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    raise ValueError(f"{trait} must be between 0 and 1")

        # Update mock data
        MOCK_SOUL_CONFIG["ocean"].update(ocean.get("ocean", {}))
        MOCK_SOUL_CONFIG["traits"].update(config.get("traits", {}))
        
        if "desires" in config:
            MOCK_SOUL_CONFIG["desires"] = config["desires"]
        
        # 更新缓存
        invalidate_soul_cache()

        return {
            "success": True,
            "data": MOCK_SOUL_CONFIG,
            "message": "Soul configuration updated"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/preset/{preset_name}")
async def apply_preset(preset_name: str):
    """Apply a preset configuration."""
    presets = {
        "analyst": {"openness": 0.8, "conscientiousness": 0.7, "extraversion": 0.3, "agreeableness": 0.4, "neuroticism": 0.5},
        "helper": {"openness": 0.5, "conscientiousness": 0.6, "extraversion": 0.7, "agreeableness": 0.9, "neuroticism": 0.4},
        "explorer": {"openness": 0.9, "conscientiousness": 0.4, "extraversion": 0.7, "agreeableness": 0.5, "neuroticism": 0.4},
        "leader": {"openness": 0.6, "conscientiousness": 0.8, "extraversion": 0.8, "agreeableness": 0.5, "neuroticism": 0.4},
        "diplomat": {"openness": 0.7, "conscientiousness": 0.6, "extraversion": 0.6, "agreeableness": 0.8, "neuroticism": 0.4},
        "sentinel": {"openness": 0.3, "conscientiousness": 0.9, "extraversion": 0.4, "agreeableness": 0.7, "neuroticism": 0.4},
        "neshama": {"openness": 0.75, "conscientiousness": 0.65, "extraversion": 0.55, "agreeableness": 0.6, "neuroticism": 0.45}
    }
    
    if preset_name.lower() not in presets:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
    
    MOCK_SOUL_CONFIG["ocean"].update(presets[preset_name.lower()])
    MOCK_SOUL_CONFIG["name"] = preset_name.capitalize()
    
    # 更新缓存
    invalidate_soul_cache()
    
    return {
        "success": True,
        "data": MOCK_SOUL_CONFIG,
        "message": f"Applied preset: {preset_name}"
    }


@router.get("/export")
async def export_soul():
    """Export soul configuration as JSON."""
    return {
        "success": True,
        "data": MOCK_SOUL_CONFIG,
        "filename": f"neshama_soul_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    }


@router.post("/import")
async def import_soul(config: Dict[str, Any]):
    """Import soul configuration from JSON."""
    try:
        ocean = config.get("ocean", {})
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            if trait in ocean:
                value = ocean[trait]
                if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    raise ValueError(f"{trait} must be between 0 and 1")
        
        MOCK_SOUL_CONFIG.update(config)
        
        # 更新缓存
        invalidate_soul_cache()
        
        return {
            "success": True,
            "message": "Soul configuration imported"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
