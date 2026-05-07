"""
Neshama Model Adapter Layer - Router - 2026 全面升级
模型路由与负载均衡

新增功能:
- 按任务类型自动路由 (coding/chat/reasoning/long-context)
- 按成本路由 (cheapest/best_quality/balanced)
- 健康检查和自动故障转移
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Any, AsyncIterator, Set
from dataclasses import dataclass, field
from enum import Enum
from .providers.base import BaseProvider, ModelResponse, StreamChunk, Message
from .pricing import PricingRegistry, TaskType, get_pricing_registry


class RouterStrategy(Enum):
    """路由策略"""
    PRIORITY = "priority"       # 按优先级
    ROUND_ROBIN = "round_robin" # 轮询
    WEIGHTED = "weighted"       # 加权轮询
    FAILOVER = "failover"       # 故障转移
    RANDOM = "random"           # 随机
    CHEAPEST = "cheapest"       # 最低价
    BEST_QUALITY = "best_quality"  # 最高质量
    BALANCED = "balanced"       # 平衡 (质量+价格)


@dataclass
class ProviderEndpoint:
    """Provider 端点"""
    provider: BaseProvider
    model: str
    priority: int = 100
    weight: int = 1
    enabled: bool = True
    consecutive_failures: int = 0
    last_failure_time: float = 0
    request_count: int = 0
    
    @property
    def health_score(self) -> float:
        """计算健康分数"""
        base_score = self.provider.health_score
        failure_penalty = min(0.5, self.consecutive_failures * 0.15)
        return max(0, base_score - failure_penalty)
    
    @property
    def is_available(self) -> bool:
        """是否可用"""
        if not self.enabled:
            return False
        if self.consecutive_failures >= 3:
            if time.time() - self.last_failure_time < 60:
                return False
        return self.health_score > 0.3


class ModelRouter:
    """
    模型路由器 - 2026 全面升级
    
    支持:
    - 多种路由策略
    - 任务类型自动路由
    - 成本感知路由
    - 健康检查和故障转移
    """
    
    def __init__(
        self,
        strategy: RouterStrategy = RouterStrategy.PRIORITY,
        failover_enabled: bool = True,
        max_consecutive_failures: int = 3,
        pricing_registry: Optional[PricingRegistry] = None
    ):
        self.strategy = strategy
        self.failover_enabled = failover_enabled
        self.max_consecutive_failures = max_consecutive_failures
        self.pricing_registry = pricing_registry or get_pricing_registry()
        
        # model_name -> endpoints
        self._endpoints: Dict[str, List[ProviderEndpoint]] = {}
        # model_name -> counter
        self._round_robin_counters: Dict[str, int] = {}
        # 任务类型 -> 模型列表映射
        self._task_type_models: Dict[TaskType, List[str]] = {}
        
        self._lock = asyncio.Lock()
        
        # 注册默认任务类型映射
        self._register_default_task_mappings()
    
    def _register_default_task_mappings(self):
        """注册默认任务类型映射"""
        self._task_type_models = {
            TaskType.CODING: [
                "deepseek-chat", "deepseek-v4-flash", "deepseek-reasoner",
                "qwen3.5-plus", "qwen-turbo", "glm-5", "glm-4.7",
                "gpt-4.1", "gpt-4.1-mini", "claude-sonnet-4-6",
                "claude-haiku-4-5", "kimi-k2.5", "moonshot-v1-128k",
            ],
            TaskType.REASONING: [
                "deepseek-reasoner", "deepseek-chat",
                "o3", "o4-mini",
                "claude-opus-4-6", "claude-sonnet-4-6",
                "gemini-2.5-pro", "qwq-32b",
            ],
            TaskType.VISION: [
                "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini",
                "claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5",
                "gemini-2.5-pro", "gemini-2.5-flash",
                "doubao-1.5-pro", "doubao-vision-pro",
            ],
            TaskType.LONG_CONTEXT: [
                "gpt-5", "gpt-5-mini", "gpt-4.1", "gpt-4o",
                "claude-opus-4-6", "claude-sonnet-4-6",
                "gemini-2.5-pro", "gemini-3.1-pro-preview",
                "deepseek-v4-pro", "deepseek-chat",
                "glm-5", "glm-4.7", "glm-4-long",
                "qwen3-max", "qwen3.5-plus", "qwen-long",
                "kimi-k2.5", "moonshot-v1-128k",
            ],
            TaskType.CHAT: [
                # 所有模型都支持 chat，这里列出常用的
                "deepseek-chat", "deepseek-v4-flash",
                "qwen3.5-plus", "qwen-turbo",
                "glm-4-plus", "glm-4-flash",
                "gpt-4o-mini", "gpt-4.1-mini",
                "claude-haiku-4-5",
            ],
            TaskType.CHEAP: [
                # 按价格排序
                "qwen-turbo", "glm-4-flash", "hunyuan-lite",
                "gpt-4o-mini", "gemini-2.5-flash-lite",
                "doubao-1.5-lite", "deepseek-v4-flash",
                "minimax-m2.1", "ernie-lite-8k",
            ],
        }
    
    def register_provider(
        self,
        provider: BaseProvider,
        model: str,
        priority: int = 100,
        weight: int = 1
    ):
        """注册 Provider"""
        endpoint = ProviderEndpoint(
            provider=provider,
            model=model,
            priority=priority,
            weight=weight
        )
        
        if model not in self._endpoints:
            self._endpoints[model] = []
            self._round_robin_counters[model] = 0
        
        for i, ep in enumerate(self._endpoints[model]):
            if ep.provider.provider_name == provider.provider_name:
                self._endpoints[model][i] = endpoint
                return
        
        self._endpoints[model].append(endpoint)
    
    def unregister_provider(self, model: str, provider_name: str):
        """取消注册 Provider"""
        if model in self._endpoints:
            self._endpoints[model] = [
                ep for ep in self._endpoints[model]
                if ep.provider.provider_name != provider_name
            ]
    
    def get_endpoints(self, model: str) -> List[ProviderEndpoint]:
        """获取可用的端点列表"""
        if model not in self._endpoints:
            return []
        return [ep for ep in self._endpoints[model] if ep.is_available]
    
    def get_models_for_task(self, task_type: TaskType) -> List[str]:
        """获取适合特定任务的模型列表"""
        return self._task_type_models.get(task_type, [])
    
    async def _select_endpoint_by_task(
        self,
        task_type: TaskType,
        prefer_cheapest: bool = False
    ) -> Optional[ProviderEndpoint]:
        """根据任务类型选择端点"""
        models = self.get_models_for_task(task_type)
        
        if not models:
            return None
        
        candidates = []
        for model in models:
            for ep in self.get_endpoints(model):
                candidates.append((model, ep))
        
        if not candidates:
            return None
        
        if prefer_cheapest:
            # 按价格排序
            candidates.sort(
                key=lambda x: self.pricing_registry.get_pricing(x[0]) or float('inf')
            )
        
        # 返回最健康的端点
        candidates.sort(key=lambda x: x[1].health_score, reverse=True)
        return candidates[0][1] if candidates else None
    
    async def _select_endpoint_by_strategy(
        self,
        model: str
    ) -> Optional[ProviderEndpoint]:
        """根据策略选择端点"""
        endpoints = self.get_endpoints(model)
        if not endpoints:
            return None
        
        if self.strategy == RouterStrategy.PRIORITY:
            return min(endpoints, key=lambda x: x.priority)
        
        elif self.strategy == RouterStrategy.ROUND_ROBIN:
            async with self._lock:
                counter = self._round_robin_counters.get(model, 0)
                index = counter % len(endpoints)
                self._round_robin_counters[model] = counter + 1
            return endpoints[index]
        
        elif self.strategy == RouterStrategy.WEIGHTED:
            total_weight = sum(ep.weight for ep in endpoints)
            if total_weight == 0:
                return random.choice(endpoints)
            rand = random.uniform(0, total_weight)
            cumulative = 0
            for ep in endpoints:
                cumulative += ep.weight
                if rand <= cumulative:
                    return ep
            return endpoints[-1]
        
        elif self.strategy == RouterStrategy.RANDOM:
            return random.choice(endpoints)
        
        elif self.strategy == RouterStrategy.CHEAPEST:
            # 选择最便宜的模型
            pricing = self.pricing_registry.get_pricing(model)
            if pricing and pricing.is_free:
                return endpoints[0]  # 免费优先
            
            # 需要考虑不同 endpoint 可能使用不同模型
            candidates_with_price = []
            for ep in endpoints:
                ep_model_pricing = self.pricing_registry.get_pricing(ep.model)
                if ep_model_pricing:
                    candidates_with_price.append((ep, ep_model_pricing.input_price_per_mtok))
            
            if candidates_with_price:
                return min(candidates_with_price, key=lambda x: x[1])[0]
            
            return endpoints[0]
        
        else:
            return endpoints[0]
    
    async def _select_endpoint(
        self,
        model: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        prefer_cheapest: bool = False
    ) -> Optional[ProviderEndpoint]:
        """选择最佳端点"""
        if task_type:
            return await self._select_endpoint_by_task(task_type, prefer_cheapest)
        
        if model:
            return await self._select_endpoint_by_strategy(model)
        
        # 如果都没有，返回任何可用的端点
        for eps in self._endpoints.values():
            for ep in eps:
                if ep.is_available:
                    return ep
        
        return None
    
    async def _call_single(
        self,
        messages: Any,
        model: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        prefer_cheapest: bool = False,
        **kwargs
    ) -> ModelResponse:
        """单次调用 (非流式)"""
        tried_endpoints = []
        
        while True:
            endpoint = await self._select_endpoint(model, task_type, prefer_cheapest)
            
            if endpoint is None:
                return ModelResponse(
                    content="",
                    model=model or "unknown",
                    provider="router",
                    error="No available endpoints"
                )
            
            if endpoint in tried_endpoints:
                break
            
            tried_endpoints.append(endpoint)
            
            try:
                response = await endpoint.provider.call(
                    messages,
                    endpoint.model,
                    **kwargs
                )
                
                if response.error:
                    raise Exception(response.error)
                
                endpoint.consecutive_failures = 0
                endpoint.request_count += 1
                return response
                    
            except Exception as e:
                endpoint.consecutive_failures += 1
                endpoint.last_failure_time = time.time()
                
                if self.failover_enabled and len(tried_endpoints) < len(self.get_endpoints(model or "")):
                    continue
                
                return ModelResponse(
                    content="",
                    model=model or endpoint.model,
                    provider="router",
                    error=f"All endpoints failed. Last error: {str(e)}"
                )
    
    async def call(
        self,
        messages: Any,
        model: Optional[str] = None,
        stream: bool = False,
        task_type: Optional[TaskType] = None,
        prefer_cheapest: bool = False,
        **kwargs
    ) -> Any:
        """
        路由调用
        
        Args:
            messages: 消息
            model: 模型名称 (可选)
            stream: 是否流式
            task_type: 任务类型 (可选)
            prefer_cheapest: 是否优先选择最便宜的
            **kwargs: 额外参数
        
        Returns:
            ModelResponse 或 AsyncIterator[StreamChunk]
        """
        if stream:
            return self._call_stream(messages, model, task_type, prefer_cheapest, **kwargs)
        else:
            return await self._call_single(messages, model, task_type, prefer_cheapest, **kwargs)
    
    async def _call_stream(
        self,
        messages: Any,
        model: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        prefer_cheapest: bool = False,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """流式调用"""
        tried_endpoints = []
        
        while True:
            endpoint = await self._select_endpoint(model, task_type, prefer_cheapest)
            
            if endpoint is None:
                yield StreamChunk(
                    content="",
                    delta="",
                    model=model or "unknown",
                    provider="router",
                    raw_chunk={"error": "No available endpoints"}
                )
                return
            
            if endpoint in tried_endpoints:
                yield StreamChunk(
                    content="",
                    delta="",
                    model=model or endpoint.model,
                    provider="router",
                    raw_chunk={"error": "All endpoints failed"}
                )
                return
            
            tried_endpoints.append(endpoint)
            success = False
            
            try:
                async for chunk in endpoint.provider.call_stream(
                    messages,
                    endpoint.model,
                    **kwargs
                ):
                    if isinstance(chunk, StreamChunk) and chunk.raw_chunk.get("error"):
                        raise Exception(chunk.raw_chunk["error"])
                    success = True
                    yield chunk
                
                if success:
                    endpoint.consecutive_failures = 0
                    return
                    
            except Exception as e:
                endpoint.consecutive_failures += 1
                endpoint.last_failure_time = time.time()
                
                if self.failover_enabled and len(tried_endpoints) < len(self.get_endpoints(model or "")):
                    continue
                
                yield StreamChunk(
                    content="",
                    delta="",
                    model=model or endpoint.model,
                    provider="router",
                    raw_chunk={"error": f"All endpoints failed. Last error: {str(e)}"}
                )
                return
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取所有端点的健康状态"""
        status = {}
        
        for model, endpoints in self._endpoints.items():
            status[model] = {
                "endpoints": [
                    {
                        "provider": ep.provider.provider_name,
                        "model": ep.model,
                        "health_score": ep.health_score,
                        "is_available": ep.is_available,
                        "consecutive_failures": ep.consecutive_failures,
                        "request_count": ep.request_count
                    }
                    for ep in endpoints
                ],
                "available_count": sum(1 for ep in endpoints if ep.is_available)
            }
        
        return status
    
    def get_stats(self) -> Dict[str, Any]:
        """获取路由统计"""
        total_requests = sum(
            ep.request_count
            for endpoints in self._endpoints.values()
            for ep in endpoints
        )
        
        total_failures = sum(
            ep.consecutive_failures
            for endpoints in self._endpoints.values()
            for ep in endpoints
        )
        
        return {
            "total_models": len(self._endpoints),
            "total_endpoints": sum(len(eps) for eps in self._endpoints.values()),
            "total_requests": total_requests,
            "total_failures": total_failures,
            "strategy": self.strategy.value,
            "failover_enabled": self.failover_enabled
        }
