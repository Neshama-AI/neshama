"""
Neshama Model Adapter Layer - 2026 全面升级
模型接入层统一入口

功能:
- 统一管理所有 Provider
- 模型路由与负载均衡
- 成本追踪与预算控制
- Coding Plan 支持
- 定价信息查询
"""

# 导入 typing
from typing import Optional, List, Tuple, Dict, Any

from .providers import (
    BaseProvider,
    ProviderConfig,
    Message,
    MessageRole,
    ModelResponse,
    StreamChunk,
    PROVIDER_MAP,
    get_provider,
    list_providers,
    
    # Core Providers
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    
    # Chinese Providers
    DashScopeProvider,
    ZhipuProvider,
    MiniMaxProvider,
    VolcEngineProvider,
    QianFanProvider,
    XingHuoProvider,
    HunyuanProvider,
    MoonshotProvider,
    
    # International Providers
    DeepSeekProvider,
    XAIProvider,
    GroqProvider,
    MistralProvider,
    CohereProvider,
    HuggingFaceProvider,
    NVIDIAProvider,
    
    # Aggregation Gateways
    OpenRouterProvider,
    SiliconFlowProvider,
    CloudflareProvider,
)

from .providers.coding import (
    CursorProvider,
    CopilotProvider,
    OpenCodeProvider,
)

from .router import ModelRouter, RouterStrategy, ProviderEndpoint
from .model_manager import ModelManager, CostTracker, UsageMonitor, FallbackManager
from .pricing import (
    PricingRegistry,
    ModelPricing,
    TaskType,
    get_pricing_registry,
)
from .orchestrator import (
    ProviderOrchestrator,
    DialogComplexity,
    ProviderStatus,
    get_orchestrator,
    reset_orchestrator,
)
from .dialogue_benchmark import (
    DialogueQualityBenchmark,
    NPCCTestCase,
    get_benchmark,
)
from .providers.coding.coding_plan_registry import (
    CodingPlanRegistry,
    CodingPlan,
    RestrictionType,
    APIStyle,
    get_coding_plan_registry,
)

__version__ = "2026.1.0"

__all__ = [
    # Version
    "__version__",
    
    # Base Classes
    "BaseProvider",
    "ProviderConfig",
    "Message",
    "MessageRole",
    "ModelResponse",
    "StreamChunk",
    
    # All Providers
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "DashScopeProvider",
    "ZhipuProvider",
    "MiniMaxProvider",
    "VolcEngineProvider",
    "QianFanProvider",
    "XingHuoProvider",
    "HunyuanProvider",
    "MoonshotProvider",
    "DeepSeekProvider",
    "XAIProvider",
    "GroqProvider",
    "MistralProvider",
    "CohereProvider",
    "HuggingFaceProvider",
    "NVIDIAProvider",
    "OpenRouterProvider",
    "SiliconFlowProvider",
    "CloudflareProvider",
    
    # Coding Providers
    "CursorProvider",
    "CopilotProvider",
    "OpenCodeProvider",
    
    # Routing & Management
    "ModelRouter",
    "RouterStrategy",
    "ProviderEndpoint",
    "ModelManager",
    "CostTracker",
    "UsageMonitor",
    "FallbackManager",
    
    # Orchestrator (热切换)
    "ProviderOrchestrator",
    "DialogComplexity",
    "ProviderStatus",
    "get_orchestrator",
    "reset_orchestrator",
    
    # Dialogue Benchmark
    "DialogueQualityBenchmark",
    "NPCCTestCase",
    "get_benchmark",
    
    # Pricing
    "PricingRegistry",
    "ModelPricing",
    "TaskType",
    "get_pricing_registry",
    
    # Coding Plan
    "CodingPlanRegistry",
    "CodingPlan",
    "RestrictionType",
    "APIStyle",
    "get_coding_plan_registry",
    
    # Utilities
    "PROVIDER_MAP",
    "get_provider",
    "list_providers",
]


def create_provider(
    provider_name: str,
    api_key: str,
    base_url: Optional[str] = None,
    **kwargs
) -> BaseProvider:
    """
    创建 Provider 实例
    
    Args:
        provider_name: Provider 名称
        api_key: API Key
        base_url: API 端点 (可选)
        **kwargs: 其他配置
    
    Returns:
        Provider 实例
    """
    provider_class = get_provider(provider_name)
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    config = ProviderConfig(
        name=provider_name,
        api_key=api_key,
        base_url=base_url or "",
        **kwargs
    )
    
    return provider_class(config)


# 便捷函数
def get_cheapest_models(
    task_type: TaskType,
    min_context: int = 0
) -> List[Tuple[str, ModelPricing]]:
    """获取最便宜的模型"""
    return get_pricing_registry().find_cheapest(task_type, min_context)


def estimate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """估算成本"""
    return get_pricing_registry().estimate_cost(model_id, input_tokens, output_tokens)


def compare_models(model_ids: List[str]) -> Dict[str, Any]:
    """对比模型"""
    return get_pricing_registry().compare_models(model_ids)


