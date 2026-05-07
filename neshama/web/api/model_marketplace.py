"""
Neshama Model Marketplace API - 2026 新增
模型市场 API - 浏览、搜索、对比模型

提供:
- 所有可用 Provider 和模型的浏览
- 模型搜索和筛选
- 模型对比功能
- 成本估算和推荐
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

# Mock Provider 数据 - 与 model_adapter 保持一致
PROVIDERS_DATA = {
    "openai": {
        "id": "openai",
        "name": "OpenAI",
        "emoji": "🤖",
        "color": "#10A37F",
        "models": [
            {"id": "gpt-5", "name": "GPT-5", "context_window": 1100000, "task_types": ["chat", "coding", "vision", "long_context"]},
            {"id": "gpt-5-mini", "name": "GPT-5 Mini", "context_window": 1100000, "task_types": ["chat", "coding", "vision"]},
            {"id": "gpt-4.1", "name": "GPT-4.1", "context_window": 128000, "task_types": ["chat", "coding", "vision"]},
            {"id": "gpt-4o", "name": "GPT-4o", "context_window": 128000, "task_types": ["chat", "coding", "vision"]},
            {"id": "o4-mini", "name": "o4-mini", "context_window": 100000, "task_types": ["reasoning", "coding"]},
        ],
        "status": "connected"
    },
    "anthropic": {
        "id": "anthropic",
        "name": "Anthropic",
        "emoji": "🧠",
        "color": "#D97706",
        "models": [
            {"id": "claude-sonnet-4", "name": "Claude Sonnet 4", "context_window": 200000, "task_types": ["chat", "coding", "vision", "reasoning"]},
            {"id": "claude-opus-4", "name": "Claude Opus 4", "context_window": 200000, "task_types": ["chat", "coding", "vision", "reasoning"]},
            {"id": "claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "context_window": 200000, "task_types": ["chat", "coding", "vision"]},
            {"id": "claude-3.5-haiku", "name": "Claude 3.5 Haiku", "context_window": 200000, "task_types": ["chat", "coding"]},
        ],
        "status": "connected"
    },
    "google": {
        "id": "google",
        "name": "Google Gemini",
        "emoji": "💎",
        "color": "#4285F4",
        "models": [
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "context_window": 1000000, "task_types": ["chat", "coding", "vision", "long_context"]},
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "context_window": 1000000, "task_types": ["chat", "coding", "vision"]},
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "context_window": 1000000, "task_types": ["chat", "coding"]},
            {"id": "gemini-exp-1206", "name": "Gemini Exp 1206", "context_window": 1000000, "task_types": ["chat", "coding", "reasoning"]},
        ],
        "status": "disconnected"
    },
    "deepseek": {
        "id": "deepseek",
        "name": "DeepSeek",
        "emoji": "🔵",
        "color": "#4D6BFE",
        "models": [
            {"id": "deepseek-v3", "name": "DeepSeek V3", "context_window": 640000, "task_types": ["chat", "coding", "reasoning"]},
            {"id": "deepseek-r1", "name": "DeepSeek R1", "context_window": 640000, "task_types": ["reasoning", "coding"]},
            {"id": "deepseek-r1-distill", "name": "DeepSeek R1 Distill", "context_window": 128000, "task_types": ["reasoning"]},
        ],
        "status": "connected"
    },
    "dashscope": {
        "id": "dashscope",
        "name": "阿里云百炼",
        "emoji": "☁️",
        "color": "#DC2626",
        "models": [
            {"id": "qwen-max", "name": "通义千问 Max", "context_window": 320000, "task_types": ["chat", "coding", "vision"]},
            {"id": "qwen-plus", "name": "通义千问 Plus", "context_window": 131000, "task_types": ["chat", "coding"]},
            {"id": "qwen-turbo", "name": "通义千问 Turbo", "context_window": 131000, "task_types": ["chat"]},
            {"id": "qwq-32b", "name": "QwQ-32B", "context_window": 32000, "task_types": ["reasoning", "coding"]},
        ],
        "status": "connected"
    },
    "zhipu": {
        "id": "zhipu",
        "name": "智谱 GLM",
        "emoji": "🟢",
        "color": "#16A34A",
        "models": [
            {"id": "glm-z1-flash", "name": "GLM-Z1 Flash", "context_window": 128000, "task_types": ["chat", "coding", "reasoning"]},
            {"id": "glm-z1", "name": "GLM-Z1", "context_window": 128000, "task_types": ["chat", "coding", "reasoning"]},
            {"id": "glm-4-plus", "name": "GLM-4 Plus", "context_window": 128000, "task_types": ["chat", "vision"]},
            {"id": "glm-4-flash", "name": "GLM-4 Flash", "context_window": 128000, "task_types": ["chat"]},
        ],
        "status": "disconnected"
    },
    "cohere": {
        "id": "cohere",
        "name": "Cohere",
        "emoji": "🔮",
        "color": "#5A4FCF",
        "models": [
            {"id": "command-r-plus-2", "name": "Command R+ 2", "context_window": 200000, "task_types": ["chat", "coding", "reasoning"]},
            {"id": "command-r-plus", "name": "Command R+", "context_window": 128000, "task_types": ["chat", "coding"]},
            {"id": "command", "name": "Command", "context_window": 4096, "task_types": ["chat"]},
        ],
        "status": "disconnected"
    },
    "groq": {
        "id": "groq",
        "name": "Groq",
        "emoji": "⚡",
        "color": "#F97316",
        "models": [
            {"id": "mixtral-8x7b", "name": "Mixtral 8x7B", "context_window": 32000, "task_types": ["chat", "coding"]},
            {"id": "llama-3.3-70b", "name": "Llama 3.3 70B", "context_window": 128000, "task_types": ["chat", "coding"]},
            {"id": "qwen-2.5-32b", "name": "Qwen 2.5 32B", "context_window": 32000, "task_types": ["chat"]},
        ],
        "status": "connected"
    },
    "mistral": {
        "id": "mistral",
        "name": "Mistral",
        "emoji": "🌬️",
        "color": "#7C3AED",
        "models": [
            {"id": "mistral-large", "name": "Mistral Large", "context_window": 128000, "task_types": ["chat", "coding", "vision"]},
            {"id": "mistral-small", "name": "Mistral Small", "context_window": 128000, "task_types": ["chat", "coding"]},
            {"id": "codestral", "name": "Codestral", "context_window": 32000, "task_types": ["coding"]},
        ],
        "status": "disconnected"
    },
    "xai": {
        "id": "xai",
        "name": "xAI (Grok)",
        "emoji": "🌟",
        "color": "#9333EA",
        "models": [
            {"id": "grok-3", "name": "Grok 3", "context_window": 131072, "task_types": ["chat", "coding", "reasoning"]},
            {"id": "grok-2", "name": "Grok 2", "context_window": 131072, "task_types": ["chat", "coding"]},
            {"id": "grok-beta", "name": "Grok Beta", "context_window": 131072, "task_types": ["chat"]},
        ],
        "status": "disconnected"
    },
    "openrouter": {
        "id": "openrouter",
        "name": "OpenRouter",
        "emoji": "🛤️",
        "color": "#6366F1",
        "models": [
            {"id": "anthropic/claude-sonnet-4", "name": "Claude Sonnet (OR)", "context_window": 200000, "task_types": ["chat", "coding", "vision"]},
            {"id": "google/gemini-2.0-flash", "name": "Gemini 2.0 (OR)", "context_window": 1000000, "task_types": ["chat", "coding"]},
            {"id": "meta/llama-3.3-70b", "name": "Llama 3.3 70B (OR)", "context_window": 128000, "task_types": ["chat", "coding"]},
        ],
        "status": "connected"
    },
    "siliconflow": {
        "id": "siliconflow",
        "name": "SiliconFlow",
        "emoji": "🌊",
        "color": "#0891B2",
        "models": [
            {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen2.5 72B", "context_window": 32000, "task_types": ["chat", "coding"]},
            {"id": "deepseek-ai/DeepSeek-V3", "name": "DeepSeek V3 (SF)", "context_window": 64000, "task_types": ["chat", "coding"]},
            {"id": "01-ai/Yi-1.5-34B", "name": "Yi-1.5 34B", "context_window": 32000, "task_types": ["chat"]},
        ],
        "status": "disconnected"
    }
}

# 定价数据 - 基于 pricing.py
PRICING_DATA = {
    "gpt-5": {"input": 2.50, "output": 15.00, "is_free": False},
    "gpt-5-mini": {"input": 0.50, "output": 2.00, "is_free": False},
    "gpt-4.1": {"input": 2.00, "output": 8.00, "is_free": False},
    "gpt-4o": {"input": 2.50, "output": 10.00, "is_free": False},
    "o4-mini": {"input": 1.10, "output": 4.40, "is_free": False},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00, "is_free": False},
    "claude-opus-4": {"input": 15.00, "output": 75.00, "is_free": False},
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00, "is_free": False},
    "claude-3.5-haiku": {"input": 0.80, "output": 4.00, "is_free": False},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00, "is_free": False},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "is_free": False},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40, "is_free": False},
    "gemini-exp-1206": {"input": 0.00, "output": 0.00, "is_free": True, "free_limit": "实验性免费"},
    "deepseek-v3": {"input": 0.27, "output": 1.10, "is_free": False},
    "deepseek-r1": {"input": 0.55, "output": 2.19, "is_free": False},
    "deepseek-r1-distill": {"input": 0.14, "output": 0.28, "is_free": False},
    "qwen-max": {"input": 0.50, "output": 2.00, "is_free": False},
    "qwen-plus": {"input": 0.20, "output": 0.80, "is_free": False},
    "qwen-turbo": {"input": 0.10, "output": 0.30, "is_free": False},
    "qwq-32b": {"input": 0.00, "output": 0.00, "is_free": True, "free_limit": "限时免费"},
    "glm-z1-flash": {"input": 0.10, "output": 0.30, "is_free": False},
    "glm-z1": {"input": 0.50, "output": 1.00, "is_free": False},
    "glm-4-plus": {"input": 0.60, "output": 1.20, "is_free": False},
    "glm-4-flash": {"input": 0.10, "output": 0.10, "is_free": False},
    "command-r-plus-2": {"input": 3.00, "output": 15.00, "is_free": False},
    "command-r-plus": {"input": 3.00, "output": 15.00, "is_free": False},
    "command": {"input": 0.50, "output": 1.50, "is_free": False},
    "mixtral-8x7b": {"input": 0.24, "output": 0.24, "is_free": False},
    "llama-3.3-70b": {"input": 0.59, "output": 2.40, "is_free": False},
    "qwen-2.5-32b": {"input": 0.50, "output": 0.50, "is_free": False},
    "mistral-large": {"input": 2.00, "output": 6.00, "is_free": False},
    "mistral-small": {"input": 0.15, "output": 0.60, "is_free": False},
    "codestral": {"input": 0.00, "output": 0.00, "is_free": True, "free_limit": "免费使用"},
    "grok-3": {"input": 5.00, "output": 15.00, "is_free": False},
    "grok-2": {"input": 2.00, "output": 8.00, "is_free": False},
    "grok-beta": {"input": 5.00, "output": 15.00, "is_free": False},
    "anthropic/claude-sonnet-4": {"input": 3.00, "output": 15.00, "is_free": False},
    "google/gemini-2.0-flash": {"input": 0.10, "output": 0.40, "is_free": False},
    "meta/llama-3.3-70b": {"input": 0.59, "output": 2.40, "is_free": False},
    "Qwen/Qwen2.5-72B-Instruct": {"input": 0.36, "output": 0.36, "is_free": False},
    "deepseek-ai/DeepSeek-V3": {"input": 0.27, "output": 1.10, "is_free": False},
    "01-ai/Yi-1.5-34B": {"input": 0.60, "output": 0.60, "is_free": False},
}


def get_pricing(model_id: str) -> Dict:
    """获取模型定价"""
    return PRICING_DATA.get(model_id, {"input": 0, "output": 0, "is_free": False})


def get_all_models() -> List[Dict]:
    """获取所有模型"""
    models = []
    for provider_id, provider in PROVIDERS_DATA.items():
        for model in provider["models"]:
            pricing = get_pricing(model["id"])
            models.append({
                "model_id": model["id"],
                "model_name": model["name"],
                "provider_id": provider_id,
                "provider_name": provider["name"],
                "provider_emoji": provider["emoji"],
                "provider_color": provider["color"],
                "context_window": model["context_window"],
                "task_types": model["task_types"],
                "input_price": pricing["input"],
                "output_price": pricing["output"],
                "is_free": pricing.get("is_free", False),
                "free_limit": pricing.get("free_limit", None),
                "status": provider["status"],
            })
    return models


@router.get("/providers")
async def get_providers():
    """获取所有 Provider 信息"""
    providers = []
    for provider_id, provider in PROVIDERS_DATA.items():
        models = provider["models"]
        models_with_pricing = []
        for m in models:
            pricing = get_pricing(m["id"])
            models_with_pricing.append({
                **m,
                "input_price": pricing["input"],
                "output_price": pricing["output"],
                "is_free": pricing.get("is_free", False),
                "free_limit": pricing.get("free_limit", None),
            })
        
        providers.append({
            "id": provider_id,
            "name": provider["name"],
            "emoji": provider["emoji"],
            "color": provider["color"],
            "models": models_with_pricing,
            "status": provider["status"],
            "model_count": len(models),
        })
    
    # 统计
    total_providers = len(providers)
    total_models = sum(p["model_count"] for p in providers)
    free_models = sum(1 for p in providers for m in p["models"] if m.get("is_free", False))
    
    return {
        "success": True,
        "data": {
            "providers": providers,
            "stats": {
                "total_providers": total_providers,
                "total_models": total_models,
                "free_models": free_models,
                "connected_providers": sum(1 for p in providers if p["status"] == "connected"),
            }
        }
    }


@router.get("/pricing")
async def get_pricing_all():
    """获取所有模型定价"""
    models = get_all_models()
    return {
        "success": True,
        "data": {
            "models": models,
            "updated_at": "2026-01-15T00:00:00Z"
        }
    }


@router.get("/search")
async def search_models(
    provider: Optional[str] = Query(None, description="Provider ID 筛选"),
    task_type: Optional[str] = Query(None, description="任务类型: chat/coding/reasoning/vision/long_context"),
    free_only: Optional[bool] = Query(None, description="仅显示免费模型"),
    max_price: Optional[float] = Query(None, description="最大输入价格 $/M"),
    query: Optional[str] = Query(None, description="搜索关键词"),
):
    """搜索和筛选模型"""
    models = get_all_models()
    
    # 筛选
    if provider:
        models = [m for m in models if m["provider_id"] == provider]
    
    if task_type:
        models = [m for m in models if task_type in m["task_types"]]
    
    if free_only:
        models = [m for m in models if m["is_free"]]
    
    if max_price:
        models = [m for m in models if m["input_price"] <= max_price]
    
    if query:
        q = query.lower()
        models = [m for m in models if 
            q in m["model_id"].lower() or 
            q in m["model_name"].lower() or 
            q in m["provider_name"].lower()
        ]
    
    return {
        "success": True,
        "data": {
            "models": models,
            "count": len(models)
        }
    }


@router.post("/compare")
async def compare_models(payload: Dict[str, Any]):
    """对比多个模型"""
    model_ids = payload.get("model_ids", [])
    
    if len(model_ids) < 2:
        raise HTTPException(status_code=400, detail="需要至少2个模型进行对比")
    
    if len(model_ids) > 5:
        raise HTTPException(status_code=400, detail="最多支持5个模型对比")
    
    models = get_all_models()
    comparison = []
    
    for model_id in model_ids:
        model = next((m for m in models if m["model_id"] == model_id), None)
        if model:
            comparison.append(model)
    
    return {
        "success": True,
        "data": {
            "models": comparison,
            "columns": ["model_name", "provider_name", "input_price", "output_price", "context_window", "task_types", "is_free"]
        }
    }


@router.post("/estimate-cost")
async def estimate_cost(payload: Dict[str, Any]):
    """估算月成本"""
    input_tokens_per_month = payload.get("input_tokens_per_month", 1000000)  # 默认 1M
    output_ratio = payload.get("output_ratio", 0.5)  # 默认输出是输入的一半
    output_tokens_per_month = int(input_tokens_per_month * output_ratio)
    
    models = get_all_models()
    estimates = []
    
    for model in models:
        input_cost = (input_tokens_per_month / 1_000_000) * model["input_price"]
        output_cost = (output_tokens_per_month / 1_000_000) * model["output_price"]
        total_cost = input_cost + output_cost
        
        estimates.append({
            **model,
            "input_tokens_per_month": input_tokens_per_month,
            "output_tokens_per_month": output_tokens_per_month,
            "estimated_monthly_cost": round(total_cost, 2),
            "estimated_daily_cost": round(total_cost / 30, 2),
        })
    
    # 按月成本排序
    estimates.sort(key=lambda x: x["estimated_monthly_cost"])
    
    # 推荐最便宜的3个
    recommended = estimates[:3]
    
    return {
        "success": True,
        "data": {
            "estimates": estimates,
            "recommended": recommended,
            "input_tokens_per_month": input_tokens_per_month,
            "output_tokens_per_month": output_tokens_per_month,
        }
    }


@router.post("/config")
async def configure_provider(payload: Dict[str, Any]):
    """配置 Provider API Key"""
    provider_id = payload.get("provider_id")
    api_key = payload.get("api_key")
    base_url = payload.get("base_url")
    
    if not provider_id or not api_key:
        raise HTTPException(status_code=400, detail="provider_id 和 api_key 必填")
    
    # 更新状态（实际应该更新配置文件）
    if provider_id in PROVIDERS_DATA:
        PROVIDERS_DATA[provider_id]["status"] = "connected"
    
    return {
        "success": True,
        "message": f"Provider {provider_id} 配置成功",
        "data": {
            "provider_id": provider_id,
            "status": "connected"
        }
    }


@router.post("/test")
async def test_connection(payload: Dict[str, Any]):
    """测试 Provider 连接"""
    provider_id = payload.get("provider_id")
    api_key = payload.get("api_key")
    
    # 模拟测试
    import random
    success = random.random() > 0.2  # 80% 成功率
    
    return {
        "success": success,
        "message": "连接测试成功" if success else "连接测试失败",
        "latency_ms": round(random.uniform(50, 500), 2) if success else None,
        "provider_id": provider_id,
    }
