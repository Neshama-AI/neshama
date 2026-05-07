"""
Evolution API - Personality trait evolution history.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

from fastapi import APIRouter, HTTPException

router = APIRouter()

# Mock evolution data
def generate_mock_evolution_history(days: int = 30):
    """Generate mock OCEAN evolution history."""
    history = []
    now = datetime.now()
    
    # Starting values
    values = {
        "openness": 0.70,
        "conscientiousness": 0.60,
        "extraversion": 0.50,
        "agreeableness": 0.55,
        "neuroticism": 0.50
    }
    
    for i in range(days):
        date = now - timedelta(days=days - i - 1)
        
        # Small random changes
        for trait in values:
            change = random.uniform(-0.03, 0.03)
            values[trait] = max(0, min(1, values[trait] + change))
        
        history.append({
            "date": date.isoformat(),
            "values": values.copy()
        })
    
    return history


def generate_mock_evolution_events():
    """Generate mock evolution events."""
    events = [
        {
            "id": "ev1",
            "date": "2024-01-15",
            "type": "interaction",
            "description": "Extended creative discussion",
            "traits_affected": ["openness", "creativity"],
            "magnitude": 0.02
        },
        {
            "id": "ev2",
            "date": "2024-01-12",
            "type": "learning",
            "description": "Learned new problem-solving approach",
            "traits_affected": ["conscientiousness"],
            "magnitude": 0.03
        },
        {
            "id": "ev3",
            "date": "2024-01-10",
            "type": "social",
            "description": "Collaborative task completed",
            "traits_affected": ["extraversion", "agreeableness"],
            "magnitude": 0.02
        },
        {
            "id": "ev4",
            "date": "2024-01-05",
            "type": "challenge",
            "description": "Handled difficult user query",
            "traits_affected": ["neuroticism"],
            "magnitude": -0.02
        }
    ]
    return events


def generate_mock_snapshots():
    """Generate mock evolution snapshots."""
    snapshots = [
        {
            "id": "snap1",
            "name": "Initial State",
            "date": "2024-01-01",
            "ocean": {
                "openness": 0.70,
                "conscientiousness": 0.60,
                "extraversion": 0.50,
                "agreeableness": 0.55,
                "neuroticism": 0.50
            },
            "description": "Default Neshama configuration"
        },
        {
            "id": "snap2",
            "name": "After First Week",
            "date": "2024-01-08",
            "ocean": {
                "openness": 0.72,
                "conscientiousness": 0.62,
                "extraversion": 0.52,
                "agreeableness": 0.57,
                "neuroticism": 0.48
            },
            "description": "Slight increase in openness and learning"
        },
        {
            "id": "snap3",
            "name": "Current State",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "ocean": {
                "openness": 0.75,
                "conscientiousness": 0.65,
                "extraversion": 0.55,
                "agreeableness": 0.60,
                "neuroticism": 0.45
            },
            "description": "Evolved through user interactions"
        }
    ]
    return snapshots


@router.get("/history")
async def get_evolution_history(days: int = 30):
    """Get OCEAN evolution history."""
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
    
    return {
        "success": True,
        "data": {
            "history": generate_mock_evolution_history(days),
            "current": {
                "openness": 0.75,
                "conscientiousness": 0.65,
                "extraversion": 0.55,
                "agreeableness": 0.60,
                "neuroticism": 0.45
            },
            "baseline": {
                "openness": 0.70,
                "conscientiousness": 0.60,
                "extraversion": 0.50,
                "agreeableness": 0.55,
                "neuroticism": 0.50
            }
        }
    }


@router.get("/events")
async def get_evolution_events():
    """Get evolution events."""
    return {
        "success": True,
        "data": generate_mock_evolution_events()
    }


@router.get("/snapshots")
async def get_snapshots():
    """Get evolution snapshots."""
    return {
        "success": True,
        "data": generate_mock_snapshots()
    }


@router.post("/snapshot")
async def create_snapshot(name: str, description: str = ""):
    """Create a new evolution snapshot."""
    snapshot = {
        "id": f"snap_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "name": name,
        "date": datetime.now().isoformat(),
        "ocean": {
            "openness": 0.75,
            "conscientiousness": 0.65,
            "extraversion": 0.55,
            "agreeableness": 0.60,
            "neuroticism": 0.45
        },
        "description": description
    }
    
    return {
        "success": True,
        "data": snapshot,
        "message": "Snapshot created successfully"
    }


@router.get("/compare/{snapshot_id1}/{snapshot_id2}")
async def compare_snapshots(snapshot_id1: str, snapshot_id2: str):
    """Compare two evolution snapshots."""
    snapshots = generate_mock_snapshots()
    
    snap1 = None
    snap2 = None
    for s in snapshots:
        if s["id"] == snapshot_id1:
            snap1 = s
        if s["id"] == snapshot_id2:
            snap2 = s
    
    if not snap1 or not snap2:
        raise HTTPException(status_code=404, detail="One or both snapshots not found")
    
    # Calculate differences
    differences = {}
    for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
        diff = snap2["ocean"][trait] - snap1["ocean"][trait]
        differences[trait] = round(diff, 3)
    
    return {
        "success": True,
        "data": {
            "snapshot1": snap1,
            "snapshot2": snap2,
            "differences": differences
        }
    }
