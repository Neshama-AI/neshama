"""
Neshama Coding Plans API - 2026 新增
编码套餐管理 API

提供:
- 编码套餐的 CRUD 操作
- 使用限制管理
- 速率限制追踪
- 连接测试
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Mock Coding Plans 存储
CODING_PLANS = {
    "plan_001": {
        "plan_id": "plan_001",
        "plan_name": "GLM-4.7 智谱套餐",
        "provider_name": "zhipu",
        "api_style": "openai_chat",
        "models": [
            {"name": "glm-4.7", "capabilities": {"supports_function_call": True, "supports_streaming": True, "supports_vision": False, "supports_reasoning": False, "context_size": 128000}},
            {"name": "glm-4-plus", "capabilities": {"supports_function_call": True, "supports_streaming": True, "supports_vision": True, "supports_reasoning": False, "context_size": 128000}},
        ],
        "restrictions": {
            "max_session_duration_hours": 5,
            "max_requests_per_session": 1000,
            "requires_active_editing": True,
            "restriction_list": ["interactive_coding_only", "no_backend"],
        },
        "rate_limits": {"rpm": 60, "rpd": 1000, "window_minutes": 60},
        "enabled": True,
        "configured": True,
        "session_stats": {"request_count": 156, "last_request": "2026-01-14T15:30:00Z"},
    },
    "plan_002": {
        "plan_id": "plan_002",
        "plan_name": "通义千问 Coding",
        "provider_name": "dashscope",
        "api_style": "openai_chat",
        "models": [
            {"name": "qwq-32b", "capabilities": {"supports_function_call": False, "supports_streaming": True, "supports_vision": False, "supports_reasoning": True, "context_size": 32000}},
            {"name": "qwen-plus", "capabilities": {"supports_function_call": True, "supports_streaming": True, "supports_vision": True, "supports_reasoning": False, "context_size": 131000}},
        ],
        "restrictions": {
            "max_session_duration_hours": 8,
            "max_requests_per_session": 500,
            "requires_active_editing": False,
            "restriction_list": ["interactive_coding_only"],
        },
        "rate_limits": {"rpm": 120, "rpd": 5000, "window_minutes": 60},
        "enabled": True,
        "configured": True,
        "session_stats": {"request_count": 89, "last_request": "2026-01-14T14:20:00Z"},
    },
    "plan_003": {
        "plan_id": "plan_003",
        "plan_name": "MiniMax 编程套餐",
        "provider_name": "minimax",
        "api_style": "openai_chat",
        "models": [
            {"name": "MiniMax-Text-01", "capabilities": {"supports_function_call": True, "supports_streaming": True, "supports_vision": False, "supports_reasoning": True, "context_size": 1000000}},
        ],
        "restrictions": {
            "max_session_duration_hours": 24,
            "max_requests_per_session": 2000,
            "requires_active_editing": False,
            "restriction_list": ["no_automation"],
        },
        "rate_limits": {"rpm": 60, "rpd": 10000, "window_minutes": 60},
        "enabled": False,
        "configured": False,
        "session_stats": {"request_count": 0, "last_request": None},
    },
}


class CodingPlanCreate(BaseModel):
    plan_name: str
    provider_name: str
    api_key: str
    base_url: Optional[str] = None
    api_style: str = "openai_chat"
    models: List[str] = []
    enabled: bool = True


class CodingPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_style: Optional[str] = None
    models: Optional[List[str]] = None
    enabled: Optional[bool] = None


@router.get("/")
async def get_coding_plans():
    """获取所有编码套餐"""
    plans = list(CODING_PLANS.values())
    
    return {
        "success": True,
        "data": {
            "plans": plans,
            "total": len(plans),
            "enabled_count": sum(1 for p in plans if p["enabled"]),
            "configured_count": sum(1 for p in plans if p["configured"]),
        }
    }


@router.post("/")
async def create_coding_plan(payload: CodingPlanCreate):
    """创建新编码套餐"""
    import uuid
    
    plan_id = f"plan_{uuid.uuid4().hex[:8]}"
    
    # 获取模型能力信息
    model_capabilities = []
    for model_name in payload.models:
        model_capabilities.append({
            "name": model_name,
            "capabilities": {
                "supports_function_call": True,
                "supports_streaming": True,
                "supports_vision": False,
                "supports_reasoning": False,
                "context_size": 128000,
            }
        })
    
    new_plan = {
        "plan_id": plan_id,
        "plan_name": payload.plan_name,
        "provider_name": payload.provider_name,
        "api_style": payload.api_style,
        "models": model_capabilities,
        "restrictions": {
            "max_session_duration_hours": 5,
            "max_requests_per_session": 1000,
            "requires_active_editing": True,
            "restriction_list": ["interactive_coding_only"],
        },
        "rate_limits": {"rpm": 60, "rpd": 1000, "window_minutes": 60},
        "enabled": payload.enabled,
        "configured": len(payload.api_key) > 0,
        "session_stats": {"request_count": 0, "last_request": None},
    }
    
    CODING_PLANS[plan_id] = new_plan
    
    return {
        "success": True,
        "data": new_plan,
        "message": "编码套餐创建成功"
    }


@router.get("/{plan_id}")
async def get_coding_plan(plan_id: str):
    """获取单个编码套餐"""
    plan = CODING_PLANS.get(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="编码套餐不存在")
    
    return {
        "success": True,
        "data": plan
    }


@router.put("/{plan_id}")
async def update_coding_plan(plan_id: str, payload: CodingPlanUpdate):
    """更新编码套餐"""
    plan = CODING_PLANS.get(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="编码套餐不存在")
    
    # 更新字段
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "models" and value:
            # 更新模型能力
            plan["models"] = [
                {
                    "name": m,
                    "capabilities": {
                        "supports_function_call": True,
                        "supports_streaming": True,
                        "supports_vision": False,
                        "supports_reasoning": False,
                        "context_size": 128000,
                    }
                }
                for m in value
            ]
        elif key == "api_key":
            plan["configured"] = len(value) > 0 if value else plan["configured"]
        elif hasattr(plan, key) or key in plan:
            plan[key] = value
    
    CODING_PLANS[plan_id] = plan
    
    return {
        "success": True,
        "data": plan,
        "message": "编码套餐更新成功"
    }


@router.delete("/{plan_id}")
async def delete_coding_plan(plan_id: str):
    """删除编码套餐"""
    if plan_id not in CODING_PLANS:
        raise HTTPException(status_code=404, detail="编码套餐不存在")
    
    del CODING_PLANS[plan_id]
    
    return {
        "success": True,
        "message": "编码套餐已删除"
    }


@router.post("/{plan_id}/test")
async def test_coding_plan(plan_id: str):
    """测试编码套餐连接"""
    plan = CODING_PLANS.get(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="编码套餐不存在")
    
    if not plan.get("configured"):
        return {
            "success": False,
            "message": "套餐未配置 API Key",
            "latency_ms": None,
        }
    
    # 模拟测试
    import random
    success = random.random() > 0.1  # 90% 成功率
    
    return {
        "success": success,
        "message": "连接测试成功" if success else "连接测试失败",
        "latency_ms": round(random.uniform(80, 400), 2) if success else None,
        "plan_id": plan_id,
    }


@router.post("/{plan_id}/toggle")
async def toggle_coding_plan(plan_id: str):
    """启用/禁用编码套餐"""
    plan = CODING_PLANS.get(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="编码套餐不存在")
    
    plan["enabled"] = not plan["enabled"]
    CODING_PLANS[plan_id] = plan
    
    return {
        "success": True,
        "data": plan,
        "message": f"套餐已{'启用' if plan['enabled'] else '禁用'}",
    }


@router.get("/{plan_id}/stats")
async def get_plan_stats(plan_id: str):
    """获取套餐使用统计"""
    plan = CODING_PLANS.get(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="编码套餐不存在")
    
    stats = plan.get("session_stats", {"request_count": 0, "last_request": None})
    
    return {
        "success": True,
        "data": {
            "plan_id": plan_id,
            "plan_name": plan["plan_name"],
            "request_count": stats.get("request_count", 0),
            "last_request": stats.get("last_request"),
            "rate_limits": plan.get("rate_limits", {}),
            "daily_limit": plan.get("rate_limits", {}).get("rpd", 0),
            "used_today": stats.get("request_count", 0),
            "remaining_today": max(0, plan.get("rate_limits", {}).get("rpd", 0) - stats.get("request_count", 0)),
        }
    }
