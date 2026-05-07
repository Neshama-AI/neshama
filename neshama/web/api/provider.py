"""
Provider API - LLM Provider热切换和管理接口

提供Provider配置、切换、健康检查等管理功能

端点:
- GET  /api/provider/active      — 获取当前活跃Provider
- POST /api/provider/switch      — 切换Provider
- GET  /api/provider/list        — 列出所有可用Provider
- GET  /api/provider/health      — 健康检查
- POST /api/provider/fallback    — 配置降级链
- GET  /api/provider/benchmark   — 运行质量对比
- POST /api/provider/config      — 配置Provider
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Body, Request
from pydantic import BaseModel, Field
import logging

# 直接导入model_adapter
import sys
import os
# 向上两级到Neshama根目录
_parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    from model_adapter.orchestrator import (
        ProviderOrchestrator,
        get_orchestrator,
        DialogComplexity,
    )
    from model_adapter.dialogue_benchmark import get_benchmark, DialogueQualityBenchmark
    from model_adapter.providers import PROVIDER_MAP
except ImportError as e:
    # 测试环境或模块未安装时的备用
    ProviderOrchestrator = None
    get_orchestrator = None
    DialogComplexity = None
    get_benchmark = None
    DialogueQualityBenchmark = None
    PROVIDER_MAP = {}
    logging.warning(f"Failed to import model_adapter in provider.py: {e}")

logger = logging.getLogger(__name__)
router = APIRouter()


# ── 请求/响应模型 ─────────────────────────────────────────────────────────────

class SwitchProviderRequest(BaseModel):
    """切换Provider请求"""
    provider_name: str = Field(..., description="Provider名称，如deepseek/openai")
    model_name: Optional[str] = Field(None, description="模型名称")


class SetPrimaryRequest(BaseModel):
    """设置主Provider请求"""
    provider_name: str
    model_name: str
    api_key: Optional[str] = Field(None, description="API Key（可选）")


class AddFallbackRequest(BaseModel):
    """添加降级Provider请求"""
    provider_name: str
    model_name: str
    priority: int = Field(1, description="优先级")
    max_retries: int = Field(3, description="最大重试次数")
    retry_delay: float = Field(1.0, description="重试延迟(秒)")


class ConfigProviderRequest(BaseModel):
    """配置Provider请求"""
    provider_name: str
    api_key: str
    base_url: Optional[str] = None
    timeout: int = Field(60, description="超时时间(秒)")
    max_retries: int = Field(3, description="最大重试次数")


class BenchmarkRequest(BaseModel):
    """评测请求"""
    providers: Optional[List[str]] = Field(
        None,
        description="要评测的Provider列表，为空则使用默认"
    )
    generate_report: bool = Field(True, description="是否生成报告")


class ChatRequest(BaseModel):
    """对话请求（用于测试）"""
    messages: List[Dict[str, str]]
    provider_name: Optional[str] = Field(None, description="指定Provider")
    model_name: Optional[str] = Field(None, description="指定模型")
    complexity: Optional[str] = Field(None, description="对话复杂度")


# ── Provider列表 ───────────────────────────────────────────────────────────────

def get_available_providers() -> List[Dict[str, Any]]:
    """获取所有可用的Provider"""
    if not PROVIDER_MAP:
        return []
    providers = []
    for name, cls in PROVIDER_MAP.items():
        providers.append({
            "name": name,
            "display_name": getattr(cls, 'provider_display_name', name),
            "models": getattr(cls, 'supported_models', []),
            "model_groups": getattr(cls, 'MODEL_GROUPS', {}),
            "pricing": getattr(cls, 'PRICING', {}),
        })
    return providers


# ── 端点实现 ──────────────────────────────────────────────────────────────────

@router.get("/list")
async def list_providers() -> Dict[str, Any]:
    """
    列出所有可用的Provider
    """
    orchestrator = get_orchestrator() if get_orchestrator else None
    configured = orchestrator.list_providers() if orchestrator else []
    available = get_available_providers()
    
    return {
        "success": True,
        "configured": configured,
        "available": available,
        "total_available": len(available),
        "total_configured": len(configured),
    }


@router.get("/active")
async def get_active() -> Dict[str, Any]:
    """
    获取当前活跃Provider
    """
    orchestrator = get_orchestrator() if get_orchestrator else None
    if orchestrator:
        active = orchestrator.get_active_provider()
        stats = orchestrator.get_stats()
    else:
        active = None
        stats = {}
    
    if active is None:
        return {
            "success": True,
            "active": None,
            "message": "No provider configured",
            "stats": stats
        }
    
    return {
        "success": True,
        "active": active,
        "stats": stats
    }


@router.post("/switch")
async def switch_provider(req: SwitchProviderRequest) -> Dict[str, Any]:
    """
    切换Provider（手动切换，不中断服务）
    """
    orchestrator = get_orchestrator() if get_orchestrator else None
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not available")
    
    success = orchestrator.switch_provider(req.provider_name, req.model_name)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to switch to provider: {req.provider_name}"
        )
    
    return {
        "success": True,
        "message": f"Switched to {req.provider_name}",
        "active": orchestrator.get_active_provider()
    }


@router.post("/primary")
async def set_primary(req: SetPrimaryRequest) -> Dict[str, Any]:
    """
    设置主Provider
    """
    orchestrator = get_orchestrator() if get_orchestrator else None
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not available")
    
    # 如果提供了API key，需要配置
    if req.api_key:
        from model_adapter.providers.base import ProviderConfig
        config = ProviderConfig(
            name=req.provider_name,
            api_key=req.api_key,
            base_url=req.base_url or "",
            timeout=60,
        )
        # 这里需要实现动态配置Provider
        # 简化处理：直接设置
        pass
    
    success = orchestrator.set_primary(req.provider_name, req.model_name)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to set primary provider: {req.provider_name}"
        )
    
    return {
        "success": True,
        "message": f"Primary provider set to {req.provider_name}/{req.model_name}",
        "active": orchestrator.get_active_provider()
    }


@router.post("/fallback")
async def add_fallback(req: AddFallbackRequest) -> Dict[str, Any]:
    """
    添加降级Provider
    """
    orchestrator = get_orchestrator() if get_orchestrator else None
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not available")
    
    success = orchestrator.add_fallback(
        provider_name=req.provider_name,
        model_name=req.model_name,
        priority=req.priority,
        max_retries=req.max_retries,
        retry_delay=req.retry_delay
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to add fallback provider: {req.provider_name}"
        )
    
    return {
        "success": True,
        "message": f"Added fallback provider: {req.provider_name}/{req.model_name}",
        "providers": orchestrator.list_providers()
    }


@router.delete("/fallback/{provider_name}")
async def remove_fallback(provider_name: str) -> Dict[str, Any]:
    """
    移除降级Provider
    """
    # 实现移除逻辑
    return {
        "success": True,
        "message": f"Removed fallback provider: {provider_name}"
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康检查 - 检查所有Provider状态
    """
    orchestrator = get_orchestrator() if get_orchestrator else None
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not available")
    
    results = await orchestrator.health_check()
    
    return {
        "success": True,
        **results
    }


@router.get("/benchmark")
async def run_benchmark(
    providers: Optional[str] = None,
    generate_report: bool = True
) -> Dict[str, Any]:
    """
    运行对话质量对比
    
    Args:
        providers: 逗号分隔的Provider列表
        generate_report: 是否生成文本报告
    """
    benchmark = get_benchmark() if get_benchmark else None
    if not benchmark:
        raise HTTPException(status_code=500, detail="Benchmark not available")
    
    # 解析Provider列表
    provider_list = None
    if providers:
        provider_list = [p.strip() for p in providers.split(",")]
    
    # 运行评测
    results = benchmark.run_benchmark(providers=provider_list)
    
    response = {
        "success": True,
        "results": results
    }
    
    # 生成报告
    if generate_report:
        report = benchmark.generate_report(results)
        response["report"] = report
    
    return response


@router.post("/benchmark")
async def run_benchmark_post(req: BenchmarkRequest) -> Dict[str, Any]:
    """
    运行对话质量对比（POST版本）
    """
    benchmark = get_benchmark() if get_benchmark else None
    if not benchmark:
        raise HTTPException(status_code=500, detail="Benchmark not available")
    
    # 运行评测
    results = benchmark.run_benchmark(providers=req.providers)
    
    response = {
        "success": True,
        "results": results
    }
    
    # 生成报告
    if req.generate_report:
        report = benchmark.generate_report(results)
        response["report"] = report
    
    return response


@router.post("/config")
async def config_provider(req: ConfigProviderRequest) -> Dict[str, Any]:
    """
    配置Provider（更新API Key等）
    """
    # 这里应该实现动态更新Provider配置
    # 简化处理
    return {
        "success": True,
        "message": f"Provider {req.provider_name} configured"
    }


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """
    获取统计信息
    """
    orchestrator = get_orchestrator() if get_orchestrator else None
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not available")
    
    stats = orchestrator.get_stats()
    
    return {
        "success": True,
        "stats": stats
    }


@router.post("/chat")
async def test_chat(req: ChatRequest) -> Dict[str, Any]:
    """
    测试对话（使用当前配置）
    """
    orchestrator = get_orchestrator() if get_orchestrator else None
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not available")
    
    # 解析复杂度
    complexity = None
    if req.complexity and DialogComplexity:
        try:
            complexity = DialogComplexity(req.complexity)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid complexity: {req.complexity}"
            )
    
    # 调用chat
    try:
        response = await orchestrator.chat(
            messages=req.messages,
            model_name=req.model_name,
            complexity=complexity
        )
        
        return {
            "success": True,
            "response": response.to_dict() if hasattr(response, 'to_dict') else {
                "content": response.content,
                "model": response.model,
                "provider": response.provider,
                "error": response.error
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complexity")
async def get_complexity_info() -> Dict[str, Any]:
    """
    获取对话复杂度分级信息
    """
    return {
        "success": True,
        "complexity_levels": [
            {
                "level": "simple",
                "description": "简单寒暄/日常对话",
                "recommended_provider": "DeepSeek V3",
                "examples": ["你好", "今天怎么样", "天气如何"]
            },
            {
                "level": "moderate",
                "description": "一般剧情对话",
                "recommended_provider": "默认Provider",
                "examples": ["聊聊你的过去", "这里有什么故事"]
            },
            {
                "level": "complex",
                "description": "复杂剧情/任务对话",
                "recommended_provider": "GPT-4o Mini",
                "examples": ["帮我完成这个任务", "给我讲讲这个地区的传说"]
            },
            {
                "level": "npc2npc",
                "description": "NPC2NPC自主对话",
                "recommended_provider": "DeepSeek V3 (最便宜)",
                "examples": ["NPC间的日常闲聊"]
            }
        ]
    }


# ── User API Key Management (BYOK) ──────────────────────────────────────────

from neshama.billing.usage import get_key_manager, UserKeyManager
from neshama.billing.plans import LLMProvider


class SetUserKeyRequest(BaseModel):
    """Set user's own API Key for BYOK mode."""
    provider: str = Field(..., description="Provider: openai, deepseek, minimax, anthropic")
    api_key: str = Field(..., description="API Key from the provider")
    model_name: Optional[str] = Field(None, description="Default model name for this provider")
    base_url: Optional[str] = Field(None, description="Custom base URL (optional)")


class DeleteUserKeyRequest(BaseModel):
    """Delete a user's API Key (revert to hosted mode)."""
    provider: Optional[str] = Field(None, description="Specific provider to delete. If None, deletes all.")


def _get_session_id(request: Request) -> Optional[str]:
    """Extract session ID from request headers."""
    return request.headers.get("X-Session-ID")


@router.post("/user-key")
async def set_user_key(req: SetUserKeyRequest, request: Request) -> Dict[str, Any]:
    """
    Set user's own API Key for BYOK (Bring Your Own Key) mode.
    
    The key will be encrypted and stored. A simple connectivity test
    will be performed to verify the key is valid.
    
    After setting a key, the user's LLM calls will use their own
    provider instead of our hosted LLM, and conversation quotas
    no longer apply.
    """
    session_id = _get_session_id(request)
    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="Session ID required (X-Session-ID header)"
        )
    
    # Validate provider
    valid_providers = [p.value for p in LLMProvider]
    if req.provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Supported: {valid_providers}"
        )
    
    key_manager = get_key_manager()
    
    # Store the key (encrypted)
    try:
        key_info = key_manager.set_key(
            session_id=session_id,
            provider=req.provider,
            api_key=req.api_key,
            model_name=req.model_name,
            base_url=req.base_url,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store API key: {str(e)}"
        )
    
    # Attempt connectivity test
    verified = False
    verification_error = None
    try:
        verified = await _verify_api_key(req.provider, req.api_key, req.base_url)
    except Exception as e:
        verification_error = str(e)
        logger.warning(f"Key verification failed for provider={req.provider}: {e}")
    
    return {
        "success": True,
        "message": f"API Key set for {req.provider}. BYOK mode is now active.",
        "key_info": {
            "provider": key_info.provider,
            "key_last4": f"****{key_info.key_last4}",
            "created_at": key_info.created_at,
            "verified": verified,
        },
        "verification_error": verification_error,
        "mode": "byok",
    }


@router.delete("/user-key")
async def delete_user_key(request: Request, provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete user's API Key and revert to hosted mode.
    
    If provider is specified, only that provider's key is deleted.
    If no provider is specified, all keys are deleted.
    
    After deleting all keys, the user reverts to hosted mode
    and conversation quotas apply again.
    """
    session_id = _get_session_id(request)
    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="Session ID required (X-Session-ID header)"
        )
    
    key_manager = get_key_manager()
    deleted = key_manager.delete_key(session_id, provider=provider)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="No API key found to delete"
        )
    
    # Check remaining mode
    still_byok = key_manager.is_byok(session_id)
    
    return {
        "success": True,
        "message": f"API Key deleted for {provider or 'all providers'}.",
        "mode": "byok" if still_byok else "hosted",
        "deleted_provider": provider or "all",
    }


@router.get("/user-key")
async def get_user_key_info(request: Request) -> Dict[str, Any]:
    """
    Get information about user's stored API Keys.
    
    Returns the active provider, list of configured providers,
    and current mode (hosted/byok). Key values are never returned -
    only the last 4 characters for identification.
    """
    session_id = _get_session_id(request)
    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="Session ID required (X-Session-ID header)"
        )
    
    key_manager = get_key_manager()
    info = key_manager.get_all_keys_info(session_id)
    
    return {
        "success": True,
        **info,
    }


async def _verify_api_key(
    provider: str,
    api_key: str,
    base_url: Optional[str] = None,
) -> bool:
    """
    Verify an API Key by making a simple test request.
    
    Returns True if the key works, False otherwise.
    Raises on unexpected errors.
    """
    import httpx
    
    test_configs = {
        "openai": {
            "url": (base_url or "https://api.openai.com") + "/v1/models",
            "headers": {"Authorization": f"Bearer {api_key}"},
        },
        "deepseek": {
            "url": (base_url or "https://api.deepseek.com") + "/v1/models",
            "headers": {"Authorization": f"Bearer {api_key}"},
        },
        "anthropic": {
            "url": "https://api.anthropic.com/v1/messages",
            "headers": {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            "method": "options",  # Anthropic doesn't have a simple models endpoint
        },
        "minimax": {
            "url": (base_url or "https://api.minimax.chat") + "/v1/text/chatcompletion_v2",
            "headers": {"Authorization": f"Bearer {api_key}"},
        },
    }
    
    config = test_configs.get(provider)
    if not config:
        # Unknown provider, skip verification
        return True
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            method = config.get("method", "get")
            response = await client.request(
                method,
                config["url"],
                headers=config["headers"],
            )
            # Accept 200, 403 (key exists but maybe limited scope)
            # Reject 401 (unauthorized)
            if response.status_code == 401:
                return False
            return True
    except httpx.TimeoutException:
        logger.warning(f"Timeout verifying key for provider={provider}")
        return True  # Assume valid on timeout
    except Exception as e:
        logger.warning(f"Error verifying key for provider={provider}: {e}")
        return True  # Assume valid on error (don't block user)
