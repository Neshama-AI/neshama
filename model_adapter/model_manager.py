"""
Neshama Model Adapter Layer - Model Manager - 2026 全面升级
模型管理：分组、成本统计、调用量监控、降级策略

新增功能:
- Coding Plan 和通用 API 的统一管理
- 多 API Key 轮换
- 速率限制追踪
- 与 Pricing Registry 集成
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from .pricing import PricingRegistry, ModelPricing, TaskType, get_pricing_registry
from .providers.base import BaseProvider, ProviderConfig, ModelResponse
from .providers.coding.coding_plan_registry import (
    CodingPlanRegistry,
    CodingPlan,
    get_coding_plan_registry,
    CodingPlanViolation
)

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """模型层级"""
    TIER_1_CHEAP = "tier_1_cheap"       # 第一梯队：低价先试
    TIER_2_FIXED = "tier_2_fixed"       # 第二梯队：月费固定
    TIER_3_CODING = "tier_3_coding"     # 第三梯队：编程类
    TIER_4_PREMIUM = "tier_4_premium"   # 第四梯队：高端旗舰


class CostUnit(Enum):
    """计费单位"""
    PER_1K_TOKENS = "per_1k_tokens"     # 每千token
    PER_CALL = "per_call"               # 每次调用
    MONTHLY = "monthly"                 # 月费


@dataclass
class CallRecord:
    """调用记录"""
    timestamp: datetime
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    success: bool
    error: Optional[str] = None
    cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelGroup:
    """模型分组"""
    name: str
    tier: ModelTier
    models: List[str] = field(default_factory=list)
    description: str = ""
    fallback_models: List[str] = field(default_factory=list)
    enabled: bool = True
    daily_budget: float = 0.0
    monthly_budget: float = 0.0
    
    @property
    def primary_model(self) -> Optional[str]:
        """主模型"""
        return self.models[0] if self.models else None


@dataclass
class APIKeyConfig:
    """API Key 配置"""
    api_key: str
    provider: str
    base_url: Optional[str] = None
    enabled: bool = True
    rate_limit_rpm: int = 60
    rate_limit_rpd: int = 10000
    used_count: int = 0
    last_used: float = 0


class CostTracker:
    """成本追踪器"""
    
    def __init__(self, pricing_registry: Optional[PricingRegistry] = None):
        self._records: List[CallRecord] = []
        self._daily_cost: Dict[str, float] = defaultdict(float)
        self._monthly_cost: Dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()
        self.pricing_registry = pricing_registry or get_pricing_registry()
    
    async def record(self, record: CallRecord):
        """记录调用"""
        async with self._lock:
            self._records.append(record)
            
            provider = record.provider
            self._daily_cost[provider] += record.cost
            self._monthly_cost[provider] += record.cost
    
    def get_daily_cost(self, provider: Optional[str] = None) -> float:
        """获取当日成本"""
        if provider:
            return self._daily_cost.get(provider, 0.0)
        return sum(self._daily_cost.values())
    
    def get_monthly_cost(self, provider: Optional[str] = None) -> float:
        """获取当月成本"""
        if provider:
            return self._monthly_cost.get(provider, 0.0)
        return sum(self._monthly_cost.values())
    
    def get_cost_by_model(self, model: str) -> float:
        """获取指定模型的总成本"""
        return sum(r.cost for r in self._records if r.model == model)
    
    def get_total_cost(self) -> float:
        """获取总成本"""
        return sum(r.cost for r in self._records)
    
    def get_records(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> List[CallRecord]:
        """获取调用记录"""
        records = self._records
        
        if start_time:
            records = [r for r in records if r.timestamp >= start_time]
        if end_time:
            records = [r for r in records if r.timestamp <= end_time]
        if model:
            records = [r for r in records if r.model == model]
        if provider:
            records = [r for r in records if r.provider == provider]
        
        return records
    
    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """估算成本"""
        return self.pricing_registry.estimate_cost(model, input_tokens, output_tokens)


class UsageMonitor:
    """使用量监控"""
    
    def __init__(self):
        self._call_counts: Dict[str, int] = defaultdict(int)
        self._input_tokens: Dict[str, int] = defaultdict(int)
        self._output_tokens: Dict[str, int] = defaultdict(int)
        self._success_counts: Dict[str, int] = defaultdict(int)
        self._failure_counts: Dict[str, int] = defaultdict(int)
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def record(self, record: CallRecord):
        """记录使用"""
        async with self._lock:
            model = record.model
            
            self._call_counts[model] += 1
            self._input_tokens[model] += record.input_tokens
            self._output_tokens[model] += record.output_tokens
            
            if record.success:
                self._success_counts[model] += 1
            else:
                self._failure_counts[model] += 1
            
            if record.latency_ms > 0:
                self._latencies[model].append(record.latency_ms)
                if len(self._latencies[model]) > 100:
                    self._latencies[model] = self._latencies[model][-100:]
    
    def get_stats(self, model: str) -> Dict[str, Any]:
        """获取模型统计"""
        latencies = self._latencies.get(model, [])
        
        return {
            "model": model,
            "total_calls": self._call_counts.get(model, 0),
            "success_calls": self._success_counts.get(model, 0),
            "failure_calls": self._failure_counts.get(model, 0),
            "total_input_tokens": self._input_tokens.get(model, 0),
            "total_output_tokens": self._output_tokens.get(model, 0),
            "total_tokens": self._input_tokens.get(model, 0) + self._output_tokens.get(model, 0),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "p50_latency_ms": self._percentile(latencies, 50),
            "p95_latency_ms": self._percentile(latencies, 95),
            "p99_latency_ms": self._percentile(latencies, 99),
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]


class FallbackManager:
    """降级管理器"""
    
    def __init__(self):
        self._fallback_chains: Dict[str, List[str]] = {}
        self._current_index: Dict[str, int] = {}
        self._lock = asyncio.Lock()
    
    def register_fallback_chain(self, model: str, chain: List[str]):
        """注册降级链"""
        self._fallback_chains[model] = chain
        self._current_index[model] = 0
    
    def get_fallback(self, model: str) -> Optional[str]:
        """获取降级模型"""
        if model not in self._fallback_chains:
            return None
        
        chain = self._fallback_chains[model]
        current = self._current_index[model]
        
        if current < len(chain) - 1:
            fallback = chain[current + 1]
            return fallback
        return None
    
    async def record_failure(self, model: str):
        """记录失败，触发降级"""
        async with self._lock:
            if model in self._current_index:
                self._current_index[model] += 1
                logger.warning(f"[FallbackManager] Fallback triggered for {model}, "
                             f"now using index {self._current_index[model]}")
    
    async def reset(self, model: str):
        """重置降级索引"""
        async with self._lock:
            if model in self._fallback_chains:
                self._current_index[model] = 0


class BudgetController:
    """预算控制器"""
    
    def __init__(self, daily_budget: float = 0, monthly_budget: float = 0):
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        
        self._daily_spent: Dict[str, float] = defaultdict(float)
        self._monthly_spent: Dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()
    
    async def check_budget(
        self, 
        provider: str, 
        estimated_cost: float = 0
    ) -> bool:
        """
        检查预算
        
        Returns:
            True 如果允许，False 如果超出预算
        """
        async with self._lock:
            if self.daily_budget > 0:
                if self._daily_spent[provider] + estimated_cost > self.daily_budget:
                    return False
            
            if self.monthly_budget > 0:
                if self._monthly_spent[provider] + estimated_cost > self.monthly_budget:
                    return False
            
            return True
    
    async def record_spend(self, provider: str, cost: float):
        """记录支出"""
        async with self._lock:
            self._daily_spent[provider] += cost
            self._monthly_spent[provider] += cost


class MultiAPIKeyManager:
    """
    多 API Key 管理器
    
    支持多 API Key 轮换和速率限制追踪
    """
    
    def __init__(self):
        self._api_keys: Dict[str, List[APIKeyConfig]] = defaultdict(list)
        self._current_index: Dict[str, int] = {}
        self._lock = asyncio.Lock()
    
    def add_api_key(
        self,
        provider: str,
        api_key: str,
        base_url: Optional[str] = None,
        rate_limit_rpm: int = 60,
        rate_limit_rpd: int = 10000
    ):
        """添加 API Key"""
        config = APIKeyConfig(
            api_key=api_key,
            provider=provider,
            base_url=base_url,
            rate_limit_rpm=rate_limit_rpm,
            rate_limit_rpd=rate_limit_rpd
        )
        
        if provider not in self._current_index:
            self._current_index[provider] = 0
        
        self._api_keys[provider].append(config)
    
    async def get_api_key(self, provider: str) -> Optional[APIKeyConfig]:
        """获取可用的 API Key (轮换)"""
        async with self._lock:
            keys = self._api_keys.get(provider, [])
            if not keys:
                return None
            
            # 尝试找到一个未超限的 key
            for i in range(len(keys)):
                idx = (self._current_index[provider] + i) % len(keys)
                key = keys[idx]
                
                if not key.enabled:
                    continue
                
                # 检查速率限制
                if self._is_rate_limited(key):
                    continue
                
                self._current_index[provider] = (idx + 1) % len(keys)
                key.used_count += 1
                key.last_used = time.time()
                return key
            
            return None
    
    def _is_rate_limited(self, key: APIKeyConfig) -> bool:
        """检查是否被速率限制"""
        now = time.time()
        
        # 简单的速率限制检查
        # 实际生产环境需要更精确的实现
        if key.last_used > 0:
            elapsed = now - key.last_used
            if elapsed < (60 / key.rate_limit_rpm):
                return True
        
        return False
    
    def enable_api_key(self, provider: str, api_key: str, enabled: bool = True):
        """启用/禁用 API Key"""
        for key in self._api_keys.get(provider, []):
            if key.api_key == api_key:
                key.enabled = enabled
                break
    
    def remove_api_key(self, provider: str, api_key: str):
        """移除 API Key"""
        if provider in self._api_keys:
            self._api_keys[provider] = [
                k for k in self._api_keys[provider]
                if k.api_key != api_key
            ]
    
    def list_api_keys(self, provider: str) -> List[Dict[str, Any]]:
        """列出 Provider 的所有 API Key"""
        return [
            {
                "api_key": k.api_key[:8] + "...",
                "enabled": k.enabled,
                "rate_limit_rpm": k.rate_limit_rpm,
                "used_count": k.used_count,
                "last_used": datetime.fromtimestamp(k.last_used) if k.last_used > 0 else None
            }
            for k in self._api_keys.get(provider, [])
        ]


class ModelManager:
    """
    模型管理器 - 2026 全面升级
    
    统一管理:
    - Provider 实例
    - 成本追踪
    - 使用量监控
    - 降级策略
    - 预算控制
    - Coding Plan
    - 多 API Key
    """
    
    def __init__(
        self,
        pricing_registry: Optional[PricingRegistry] = None,
        coding_plan_registry: Optional[CodingPlanRegistry] = None
    ):
        self.pricing_registry = pricing_registry or get_pricing_registry()
        self.coding_plan_registry = coding_plan_registry or get_coding_plan_registry()
        
        # 组件
        self.cost_tracker = CostTracker(self.pricing_registry)
        self.usage_monitor = UsageMonitor()
        self.fallback_manager = FallbackManager()
        self.budget_controller = BudgetController()
        self.api_key_manager = MultiAPIKeyManager()
        
        # Provider 实例
        self._providers: Dict[str, BaseProvider] = {}
        
        # 模型分组
        self._model_groups: Dict[str, ModelGroup] = {}
        
        # 注册默认降级链
        self._register_default_fallbacks()
    
    def _register_default_fallbacks(self):
        """注册默认降级链"""
        self.fallback_manager.register_fallback_chain(
            "gpt-5",
            ["gpt-5", "gpt-4.1", "gpt-4o", "gpt-4o-mini"]
        )
        self.fallback_manager.register_fallback_chain(
            "claude-opus-4-6",
            ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"]
        )
        self.fallback_manager.register_fallback_chain(
            "deepseek-v4-pro",
            ["deepseek-v4-pro", "deepseek-chat", "qwen3.5-plus"]
        )
    
    def register_provider(self, name: str, provider: BaseProvider):
        """注册 Provider"""
        self._providers[name] = provider
        logger.info(f"[ModelManager] Registered provider: {name}")
    
    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """获取 Provider"""
        return self._providers.get(name)
    
    def register_model_group(self, group: ModelGroup):
        """注册模型分组"""
        self._model_groups[group.name] = group
    
    def get_model_group(self, name: str) -> Optional[ModelGroup]:
        """获取模型分组"""
        return self._model_groups.get(name)
    
    async def call(
        self,
        provider_name: str,
        messages: Any,
        model: str,
        use_coding_plan: bool = False,
        coding_plan_id: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        调用模型
        
        Args:
            provider_name: Provider 名称
            messages: 消息
            model: 模型
            use_coding_plan: 是否使用 Coding Plan
            coding_plan_id: Coding Plan ID
            **kwargs: 其他参数
        """
        # 检查 Coding Plan 限制
        if use_coding_plan and coding_plan_id:
            context = {
                "is_interactive": kwargs.get("is_interactive", True),
                "is_backend": kwargs.get("is_backend", False),
                "is_automated": kwargs.get("is_automated", False),
                "is_curl": kwargs.get("is_curl", False),
            }
            self.coding_plan_registry.check_restrictions(coding_plan_id, context)
        
        # 获取 Provider
        provider = self._providers.get(provider_name)
        if not provider:
            return ModelResponse(
                content="",
                model=model,
                provider=provider_name,
                error=f"Provider not found: {provider_name}"
            )
        
        start_time = time.time()
        
        try:
            # 估算成本
            estimated_cost = self.cost_tracker.estimate_cost(
                model,
                kwargs.get("input_tokens", 0),
                kwargs.get("output_tokens", 0)
            )
            
            # 检查预算
            if not await self.budget_controller.check_budget(provider_name, estimated_cost):
                return ModelResponse(
                    content="",
                    model=model,
                    provider=provider_name,
                    error="Budget exceeded"
                )
            
            # 调用
            response = await provider.call(messages, model, **kwargs)
            
            # 记录
            await self.cost_tracker.record(CallRecord(
                timestamp=datetime.now(),
                model=model,
                provider=provider_name,
                input_tokens=response.usage.get("prompt_tokens", 0) if response.usage else 0,
                output_tokens=response.usage.get("completion_tokens", 0) if response.usage else 0,
                latency_ms=response.latency_ms,
                success=not bool(response.error),
                error=response.error,
                cost=estimated_cost
            ))
            
            await self.usage_monitor.record(CallRecord(
                timestamp=datetime.now(),
                model=model,
                provider=provider_name,
                input_tokens=response.usage.get("prompt_tokens", 0) if response.usage else 0,
                output_tokens=response.usage.get("completion_tokens", 0) if response.usage else 0,
                latency_ms=response.latency_ms,
                success=not bool(response.error),
                error=response.error,
                cost=estimated_cost
            ))
            
            # 更新 Coding Plan 请求计数
            if use_coding_plan and coding_plan_id:
                self.coding_plan_registry.record_request(coding_plan_id)
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[ModelManager] Call failed: {error_msg}")
            
            # 触发降级
            fallback_model = self.fallback_manager.get_fallback(model)
            if fallback_model:
                await self.fallback_manager.record_failure(model)
                logger.info(f"[ModelManager] Falling back to {fallback_model}")
                return await self.call(
                    provider_name,
                    messages,
                    fallback_model,
                    use_coding_plan=use_coding_plan,
                    coding_plan_id=coding_plan_id,
                    **kwargs
                )
            
            return ModelResponse(
                content="",
                model=model,
                provider=provider_name,
                latency_ms=(time.time() - start_time) * 1000,
                error=error_msg
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_providers": len(self._providers),
            "total_model_groups": len(self._model_groups),
            "cost": {
                "daily": self.cost_tracker.get_daily_cost(),
                "monthly": self.cost_tracker.get_monthly_cost(),
                "total": self.cost_tracker.get_total_cost()
            },
            "coding_plans": [
                {
                    "plan_id": p.plan_id,
                    "plan_name": p.plan_name,
                    "request_count": p.request_count,
                    "session_duration_hours": (time.time() - p.session_start) / 3600 if p.session_start > 0 else 0
                }
                for p in self.coding_plan_registry.list_plans()
            ],
            "providers": list(self._providers.keys())
        }
