"""
Emotion API - Current and historical emotion data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

from fastapi import APIRouter, HTTPException

from .cache import get_emotion_cache, invalidate_emotion_cache

router = APIRouter()

# Mock emotion data
EMOTION_CATEGORIES = ["joy", "sadness", "anger", "fear", "surprise", "disgust", "trust", "anticipation"]

EMOTION_EMOJI = {
    "joy": "😊",
    "sadness": "😢",
    "anger": "😠",
    "fear": "😨",
    "surprise": "😲",
    "disgust": "😒",
    "trust": "🤝",
    "anticipation": "🤔"
}

EMOTION_COLORS = {
    "joy": "#FFD700",
    "sadness": "#4A90D9",
    "anger": "#FF4444",
    "fear": "#9B59B6",
    "surprise": "#E67E22",
    "disgust": "#27AE60",
    "trust": "#3498DB",
    "anticipation": "#F39C12"
}

# 情绪状态缓存键
CACHE_KEY_CURRENT = "emotion_current"
CACHE_TTL = 5  # 5秒缓存


def generate_mock_current_emotion():
    """Generate mock current emotion state."""
    primary = random.choice(EMOTION_CATEGORIES)
    secondary = random.choice([c for c in EMOTION_CATEGORIES if c != primary])
    
    return {
        "primary": {
            "category": primary,
            "intensity": round(random.uniform(0.3, 0.9), 2),
            "emoji": EMOTION_EMOJI[primary],
            "color": EMOTION_COLORS[primary],
            "description": f"Currently experiencing {primary}"
        },
        "secondary": {
            "category": secondary,
            "intensity": round(random.uniform(0.1, 0.5), 2),
            "emoji": EMOTION_EMOJI[secondary],
            "color": EMOTION_COLORS[secondary]
        },
        "valence": round(random.uniform(-0.5, 0.8), 2),  # -1 negative to +1 positive
        "arousal": round(random.uniform(0.2, 0.9), 2),  # 0 calm to 1 excited
        "timestamp": datetime.now().isoformat()
    }


def generate_mock_emotion_history(hours: int = 24, points: int = 48):
    """Generate mock emotion history."""
    history = []
    now = datetime.now()
    interval = timedelta(hours=hours) / points
    
    current_emotion = random.choice(EMOTION_CATEGORIES)
    
    for i in range(points):
        timestamp = now - (interval * (points - i - 1))
        
        # Occasionally change emotion
        if random.random() < 0.1:
            current_emotion = random.choice(EMOTION_CATEGORIES)
        
        intensity = round(random.uniform(0.2, 0.8), 2)
        
        history.append({
            "timestamp": timestamp.isoformat(),
            "category": current_emotion,
            "intensity": intensity,
            "emoji": EMOTION_EMOJI[current_emotion],
            "color": EMOTION_COLORS[current_emotion],
            "valence": round(random.uniform(-0.5, 0.8), 2),
            "arousal": round(random.uniform(0.2, 0.9), 2)
        })
    
    return history


def generate_mock_emotion_events():
    """Generate mock emotion trigger events."""
    events = [
        {"time": "2h ago", "event": "User asked about creative writing", "emotion": "anticipation", "intensity": 0.7},
        {"time": "4h ago", "event": "Shared a joke with user", "emotion": "joy", "intensity": 0.8},
        {"time": "6h ago", "event": "Discussed complex topic", "emotion": "trust", "intensity": 0.6},
        {"time": "8h ago", "event": "User expressed frustration", "emotion": "sadness", "intensity": 0.4},
        {"time": "12h ago", "event": "Explained difficult concept", "emotion": "satisfaction", "intensity": 0.7}
    ]
    return events


@router.get("/current")
async def get_current_emotion():
    """
    Get current emotion state.
    
    Cached for 5 seconds to reduce API calls while maintaining
    near real-time updates for the dashboard.
    """
    cache = get_emotion_cache()
    
    # 尝试从缓存获取
    cached_data = cache.get(CACHE_KEY_CURRENT)
    if cached_data is not None:
        return {
            "success": True,
            "data": cached_data,
            "cached": True
        }
    
    # 生成新数据
    emotion_data = generate_mock_current_emotion()
    
    # 存入缓存
    cache.set(CACHE_KEY_CURRENT, emotion_data, CACHE_TTL)
    
    return {
        "success": True,
        "data": emotion_data,
        "cached": False
    }


@router.post("/current")
async def update_emotion_state(emotion_data: Dict[str, Any]):
    """
    Update the current emotion state.
    
    When emotion is updated, invalidate the cache so
    next request gets fresh data.
    """
    # 验证情绪数据
    category = emotion_data.get("category")
    intensity = emotion_data.get("intensity", 0.5)
    
    if category and category not in EMOTION_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid emotion category. Must be one of: {EMOTION_CATEGORIES}"
        )
    
    if not 0 <= intensity <= 1:
        raise HTTPException(
            status_code=400,
            detail="Intensity must be between 0 and 1"
        )
    
    # 更新缓存
    invalidate_emotion_cache()
    
    return {
        "success": True,
        "message": "Emotion state updated",
        "data": emotion_data
    }


@router.get("/history")
async def get_emotion_history(hours: int = 24):
    """Get emotion history over time."""
    if hours < 1 or hours > 168:
        raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
    
    return {
        "success": True,
        "data": {
            "history": generate_mock_emotion_history(hours),
            "events": generate_mock_emotion_events(),
            "stats": {
                "avg_intensity": round(random.uniform(0.4, 0.6), 2),
                "dominant_emotion": random.choice(EMOTION_CATEGORIES),
                "emotion_variance": round(random.uniform(0.1, 0.3), 2),
                "peak_times": ["10:00", "14:00", "20:00"]
            }
        }
    }


@router.get("/categories")
async def get_emotion_categories():
    """Get all emotion categories with metadata."""
    return {
        "success": True,
        "data": {
            "categories": [
                {
                    "id": cat,
                    "name": cat.capitalize(),
                    "emoji": EMOTION_EMOJI[cat],
                    "color": EMOTION_COLORS[cat],
                    "valence": random.uniform(-0.5, 0.5),
                    "arousal": random.uniform(0.2, 0.9)
                }
                for cat in EMOTION_CATEGORIES
            ]
        }
    }
