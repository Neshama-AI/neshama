"""
Neshama Provider Orchestrator - LLM Provider热切换系统
运行时热切换 + 智能降级 + NPC对话分级

功能:
- 多Provider运行时热切换（不重启）
- 智能降级策略（主Provider失败自动切备用）
- NPC对话分级策略（简单用DeepSeek V3，复杂用GPT-4o mini）
- Provider健康检查和自动恢复
- 线程安全的单例模式
"""

import asyncio
import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union, AsyncIterator
from enum import Enum
from functools import wraps

from .providers.base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk
from .providers import get_provider, DeepSeekProvider, OpenAIProvider, AnthropicProvider

logger = logging.getLogger(__name__)


class DialogComplexity(Enum):
    """对话复杂度等级"""
    SIMPLE = "simple"      # 简单寒暄/日常对话 -> DeepSeek V3
    MODERATE = "moderate"  # 一般剧情对话 -> 中等Provider
    COMPLEX = "complex"    # 复杂剧情/任务对话 -> GPT-4o mini
    NPC2NPC = "npc2npc"    # NPC2NPC自主对话 -> 强制最便宜Provider


class ProviderStatus(Enum):
    """Provider状态"""
    ACTIVE = "active"      # 活跃（当前使用）
    FALLBACK = "fallback"  # 备用（可降级）
    UNAVAILABLE = "unavailable"  # 不可用（失败/维护）
    RECOVERING = "recovering"    # 恢复中（等待健康检查）


@dataclass
class FallbackProvider:
    """降级Provider配置"""
    provider_name: str
    model_name: str
    priority: int = 1  # 优先级，数字越小优先级越高
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟(秒)
    
    def __hash__(self):
        return hash((self.provider_name, self.model_name))


@dataclass
class ProviderState:
    """Provider运行时状态"""
    provider: BaseProvider
    model_name: str
    status: ProviderStatus = ProviderStatus.ACTIVE
    consecutive_failures: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    total_requests: int = 0
    failed_requests: int = 0
    
    @property
    def failure_rate(self) -> float:
        """计算失败率"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    @property
    def is_healthy(self) -> bool:
        """检查是否健康"""
        return self.consecutive_failures < 3 and self.status != ProviderStatus.UNAVAILABLE


class ProviderOrchestrator:
    """
    Provider编排器 - 全局单例，线程安全
    
    特性:
    - 运行时热切换（不重启服务）
    - 自动降级（主Provider失败自动切备用）
    - 自动恢复（主Provider恢复后自动切回）
    - NPC对话分级（根据复杂度选择Provider）
    - 健康检查（定时检查所有Provider）
    """
    
    _instance: Optional['ProviderOrchestrator'] = None
    _lock = threading.RLock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        timeout: float = 5.0,
        recovery_delay: float = 30.0,
        max_consecutive_failures: int = 3,
        health_check_interval: float = 60.0,
        enable_auto_recovery: bool = True
    ):
        """
        初始化编排器
        
        Args:
            timeout: 请求超时时间(秒)
            recovery_delay: 主Provider恢复后延迟切换时间(秒)，避免抖动
            max_consecutive_failures: 最大连续失败次数
            health_check_interval: 健康检查间隔(秒)
            enable_auto_recovery: 是否启用自动恢复
        """
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.timeout = timeout
        self.recovery_delay = recovery_delay
        self.max_consecutive_failures = max_consecutive_failures
        self.health_check_interval = health_check_interval
        self.enable_auto_recovery = enable_auto_recovery
        
        # Provider状态管理
        self._primary_state: Optional[ProviderState] = None
        self._fallback_states: List[ProviderState] = []
        self._fallback_priorities: Dict[str, FallbackProvider] = {}
        
        # 线程锁
        self._state_lock = threading.RLock()
        self._provider_lock = threading.RLock()
        
        # 默认配置
        self._default_configs: Dict[str, ProviderConfig] = {}
        
        # 对话复杂度评估器
        self._complexity_keywords = {
            DialogComplexity.SIMPLE: [
                "你好", "早上好", "晚安", "天气", "吃了吗", "最近", "怎么样",
                "hi", "hello", "hey", "good morning", "good night"
            ],
            DialogComplexity.COMPLEX: [
                "任务", "委托", "剧情", "故事", "敌人", "战斗", "boss",
                "quest", "mission", "story", "plot", "battle", "fight"
            ]
        }
        
        # 规则引擎fallback回复
        self._fallback_responses = [
            "让我想想...",
            "这个嘛，我需要再考虑一下。",
            "你说的有道理，让我想想该怎么回答。",
            "嗯...这个话题挺有意思的。",
            "抱歉，我现在有点困惑，能再说一遍吗？",
        ]
        
        # 统计信息
        self._stats = {
            "total_requests": 0,
            "failed_requests": 0,
            "fallback_count": 0,
            "switch_count": 0,
            "start_time": time.time()
        }
        
        logger.info("ProviderOrchestrator initialized (singleton)")
    
    @classmethod
    def get_instance(cls) -> 'ProviderOrchestrator':
        """获取单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例（主要用于测试）"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._initialized = False
            cls._instance = None
    
    # ── Provider配置管理 ──────────────────────────────────────────────────────
    
    def set_primary(self, provider_name: str, model_name: str, **config_kwargs) -> bool:
        """
        设置主Provider
        
        Args:
            provider_name: Provider名称（如"deepseek", "openai"）
            model_name: 模型名称（如"deepseek-chat", "gpt-4o-mini"）
            **config_kwargs: 额外配置参数
            
        Returns:
            是否设置成功
        """
        with self._state_lock:
            try:
                # 创建Provider
                provider = get_provider(provider_name)
                if provider is None:
                    logger.error(f"Provider not found: {provider_name}")
                    return False
                
                # 创建状态
                state = ProviderState(
                    provider=provider,
                    model_name=model_name,
                    status=ProviderStatus.ACTIVE,
                    last_success_time=time.time()
                )
                
                # 更新配置
                self._primary_state = state
                
                # 记录切换
                self._stats["switch_count"] += 1
                logger.info(f"Primary provider set: {provider_name}/{model_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to set primary provider: {e}")
                return False
    
    def add_fallback(
        self,
        provider_name: str,
        model_name: str,
        priority: int = 1,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> bool:
        """
        添加降级Provider
        
        Args:
            provider_name: Provider名称
            model_name: 模型名称
            priority: 优先级（数字越小优先级越高）
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            
        Returns:
            是否添加成功
        """
        with self._state_lock:
            try:
                # 获取Provider
                provider = get_provider(provider_name)
                if provider is None:
                    logger.error(f"Provider not found: {provider_name}")
                    return False
                
                # 创建状态
                state = ProviderState(
                    provider=provider,
                    model_name=model_name,
                    status=ProviderStatus.FALLBACK
                )
                
                # 添加到fallback列表
                self._fallback_states.append(state)
                
                # 记录优先级
                key = f"{provider_name}:{model_name}"
                self._fallback_priorities[key] = FallbackProvider(
                    provider_name=provider_name,
                    model_name=model_name,
                    priority=priority,
                    max_retries=max_retries,
                    retry_delay=retry_delay
                )
                
                # 按优先级排序
                self._fallback_states.sort(
                    key=lambda s: self._fallback_priorities.get(
                        f"{s.provider.provider_name}:{s.model_name}",
                        FallbackProvider(provider_name="", model_name="", priority=999)
                    ).priority
                )
                
                logger.info(f"Fallback provider added: {provider_name}/{model_name} (priority={priority})")
                return True
                
            except Exception as e:
                logger.error(f"Failed to add fallback provider: {e}")
                return False
    
    def switch_provider(self, provider_name: str, model_name: Optional[str] = None) -> bool:
        """
        手动切换Provider（不中断服务）
        
        Args:
            provider_name: Provider名称
            model_name: 模型名称（可选，不提供则使用默认模型）
            
        Returns:
            是否切换成功
        """
        with self._state_lock:
            try:
                # 获取Provider
                provider = get_provider(provider_name)
                if provider is None:
                    logger.error(f"Provider not found: {provider_name}")
                    return False
                
                # 确定模型名
                if model_name is None:
                    model_name = provider.supported_models[0] if provider.supported_models else ""
                
                # 如果当前有主Provider，将其转为fallback
                if self._primary_state is not None:
                    old_primary = self._primary_state
                    old_primary.status = ProviderStatus.FALLBACK
                    if old_primary not in self._fallback_states:
                        self._fallback_states.insert(0, old_primary)
                
                # 设置新主Provider
                new_state = ProviderState(
                    provider=provider,
                    model_name=model_name,
                    status=ProviderStatus.ACTIVE,
                    last_success_time=time.time()
                )
                self._primary_state = new_state
                
                # 记录切换
                self._stats["switch_count"] += 1
                logger.info(f"Provider switched to: {provider_name}/{model_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to switch provider: {e}")
                return False
    
    # ── 对话复杂度评估 ─────────────────────────────────────────────────────────
    
    def evaluate_complexity(self, messages: Union[List[Message], List[Dict], str]) -> DialogComplexity:
        """
        评估对话复杂度
        
        Args:
            messages: 消息列表或字符串
            
        Returns:
            对话复杂度等级
        """
        # 提取文本内容
        if isinstance(messages, str):
            text = messages.lower()
        else:
            text = " ".join([
                m.content if hasattr(m, 'content') else m.get('content', '')
                for m in messages
            ]).lower()
        
        # 检查是否NPC2NPC对话
        if any(m.name in text for m in messages if hasattr(m, 'name') and m.name):
            return DialogComplexity.NPC2NPC
        
        # 检查复杂度关键词
        simple_score = sum(1 for kw in self._complexity_keywords[DialogComplexity.SIMPLE] if kw.lower() in text)
        complex_score = sum(1 for kw in self._complexity_keywords[DialogComplexity.COMPLEX] if kw.lower() in text)
        
        if complex_score >= 2:
            return DialogComplexity.COMPLEX
        elif simple_score >= 2:
            return DialogComplexity.SIMPLE
        elif complex_score == 1:
            return DialogComplexity.MODERATE
        else:
            return DialogComplexity.MODERATE
    
    def _select_provider_for_complexity(self, complexity: DialogComplexity) -> Optional[ProviderState]:
        """
        根据复杂度选择Provider
        
        Args:
            complexity: 对话复杂度
            
        Returns:
            选中的Provider状态
        """
        if complexity == DialogComplexity.SIMPLE or complexity == DialogComplexity.NPC2NPC:
            # 简单对话 -> 找最便宜的Provider（DeepSeek V3）
            for state in self._fallback_states:
                if state.provider.provider_name == "deepseek":
                    return state
            # 如果没有DeepSeek，找其他便宜的
            for state in self._fallback_states:
                if state.is_healthy:
                    return state
                    
        elif complexity == DialogComplexity.COMPLEX:
            # 复杂对话 -> 找质量好的Provider
            for state in self._fallback_states:
                if state.provider.provider_name in ["openai", "anthropic"]:
                    if state.is_healthy:
                        return state
            # 如果没有，返回主Provider
            return self._primary_state
            
        else:  # MODERATE
            # 中等复杂度 -> 主Provider或第一个健康的fallback
            if self._primary_state and self._primary_state.is_healthy:
                return self._primary_state
            for state in self._fallback_states:
                if state.is_healthy:
                    return state
        
        return self._primary_state
    
    # ── 对话调用 ───────────────────────────────────────────────────────────────
    
    async def chat(
        self,
        messages: Union[List[Message], List[Dict], str],
        model_name: Optional[str] = None,
        complexity: Optional[DialogComplexity] = None,
        **kwargs
    ) -> ModelResponse:
        """
        调用当前活跃Provider，失败自动降级
        
        Args:
            messages: 消息列表
            model_name: 指定模型（可选）
            complexity: 指定复杂度（可选）
            **kwargs: 额外参数
            
        Returns:
            ModelResponse
        """
        with self._state_lock:
            self._stats["total_requests"] += 1
            
            # 评估复杂度
            if complexity is None:
                complexity = self.evaluate_complexity(messages)
            
            # 根据复杂度选择Provider
            active_state = self._select_provider_for_complexity(complexity)
            if active_state is None:
                return self._create_error_response("No available provider")
            
            target_model = model_name or active_state.model_name
            
            # 调用Provider
            return await self._call_with_fallback(
                active_state,
                messages,
                target_model,
                **kwargs
            )
    
    async def _call_with_fallback(
        self,
        initial_state: ProviderState,
        messages: Union[List[Message], List[Dict], str],
        model_name: str,
        **kwargs
    ) -> ModelResponse:
        """
        带降级的调用
        
        Args:
            initial_state: 初始Provider状态
            messages: 消息列表
            model_name: 模型名称
            **kwargs: 额外参数
            
        Returns:
            ModelResponse
        """
        # 首先尝试初始Provider
        states_to_try = [initial_state] + [
            s for s in self._fallback_states
            if s != initial_state and s.is_healthy
        ]
        
        last_error = None
        
        for state in states_to_try:
            try:
                # 获取fallback配置
                key = f"{state.provider.provider_name}:{state.model_name}"
                fb_config = self._fallback_priorities.get(key)
                max_retries = fb_config.max_retries if fb_config else self.max_consecutive_failures
                retry_delay = fb_config.retry_delay if fb_config else 1.0
                
                # 重试逻辑
                for attempt in range(max_retries):
                    try:
                        # Apply timeout to provider calls for MiniMax latency handling
                        try:
                            response = await asyncio.wait_for(
                                state.provider.call(
                                    messages,
                                    model=model_name if model_name else state.model_name,
                                    **kwargs
                                ),
                                timeout=self.timeout * 6  # 30s default timeout for LLM calls
                            )
                        except asyncio.TimeoutError:
                            raise TimeoutError(
                                f"Provider {state.provider.provider_name} timed out "
                                f"after {self.timeout * 6}s on attempt {attempt + 1}"
                            )
                        
                        # 成功
                        state.consecutive_failures = 0
                        state.last_success_time = time.time()
                        state.total_requests += 1
                        
                        # 如果不是主Provider且成功了，记录降级
                        if state != self._primary_state:
                            self._stats["fallback_count"] += 1
                            logger.info(f"Fallback succeeded: {state.provider.provider_name}")
                        
                        return response
                        
                    except Exception as e:
                        last_error = str(e)
                        logger.warning(
                            f"Provider {state.provider.provider_name} attempt {attempt + 1} failed: {e}"
                        )
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                
                # 所有重试都失败
                state.consecutive_failures += 1
                state.failed_requests += 1
                state.last_failure_time = time.time()
                
                # 如果失败次数过多，标记为不可用
                if state.consecutive_failures >= self.max_consecutive_failures:
                    state.status = ProviderStatus.UNAVAILABLE
                    logger.warning(
                        f"Provider {state.provider.provider_name} marked unavailable "
                        f"(failures={state.consecutive_failures})"
                    )
                
                # 尝试下一个Provider
                self._stats["failed_requests"] += 1
                self._stats["fallback_count"] += 1
                continue
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error with provider {state.provider.provider_name}: {e}")
                continue
        
        # 所有Provider都失败
        logger.error("All providers failed, using fallback response")
        return self._create_fallback_response()
    
    def _create_error_response(self, error_msg: str) -> ModelResponse:
        """创建错误响应"""
        return ModelResponse(
            content="",
            model="",
            provider="orchestrator",
            error=error_msg
        )
    
    def _create_fallback_response(self) -> ModelResponse:
        """创建规则引擎fallback响应"""
        import random
        return ModelResponse(
            content=random.choice(self._fallback_responses),
            model="rule-engine",
            provider="orchestrator",
            finish_reason="fallback"
        )
    
    # ── 健康检查和恢复 ─────────────────────────────────────────────────────────
    
    async def health_check(self) -> Dict[str, Any]:
        """
        检查所有Provider健康状态
        
        Returns:
            健康检查结果
        """
        results = {
            "primary": None,
            "fallbacks": [],
            "summary": {
                "total": 0,
                "healthy": 0,
                "unhealthy": 0
            }
        }
        
        with self._state_lock:
            # 检查主Provider
            if self._primary_state:
                is_healthy = self._primary_state.is_healthy
                results["primary"] = {
                    "provider": self._primary_state.provider.provider_name,
                    "model": self._primary_state.model_name,
                    "status": self._primary_state.status.value,
                    "is_healthy": is_healthy,
                    "consecutive_failures": self._primary_state.consecutive_failures,
                    "failure_rate": self._primary_state.failure_rate,
                    "total_requests": self._primary_state.total_requests
                }
                results["summary"]["total"] += 1
                if is_healthy:
                    results["summary"]["healthy"] += 1
                else:
                    results["summary"]["unhealthy"] += 1
                
                # 检查是否需要自动恢复
                if (self.enable_auto_recovery and
                    self._primary_state.status == ProviderStatus.UNAVAILABLE and
                    time.time() - self._primary_state.last_failure_time > self.recovery_delay):
                    
                    # 尝试恢复
                    self._primary_state.status = ProviderStatus.RECOVERING
                    logger.info(f"Primary provider recovering: {self._primary_state.provider.provider_name}")
            
            # 检查fallback Providers
            for state in self._fallback_states:
                is_healthy = state.is_healthy
                results["fallbacks"].append({
                    "provider": state.provider.provider_name,
                    "model": state.model_name,
                    "status": state.status.value,
                    "is_healthy": is_healthy,
                    "consecutive_failures": state.consecutive_failures,
                    "failure_rate": state.failure_rate,
                    "total_requests": state.total_requests
                })
                results["summary"]["total"] += 1
                if is_healthy:
                    results["summary"]["healthy"] += 1
                else:
                    results["summary"]["unhealthy"] += 1
        
        return results
    
    async def auto_recovery_check(self):
        """自动恢复检查（定时任务）"""
        with self._state_lock:
            if not self.enable_auto_recovery:
                return
            
            # 检查主Provider是否可以恢复
            if (self._primary_state and
                self._primary_state.status == ProviderStatus.RECOVERING):
                
                elapsed = time.time() - self._primary_state.last_failure_time
                if elapsed >= self.recovery_delay:
                    # 重置为active
                    self._primary_state.status = ProviderStatus.ACTIVE
                    self._primary_state.consecutive_failures = 0
                    logger.info(
                        f"Primary provider recovered: {self._primary_state.provider.provider_name}"
                    )
    
    # ── 信息查询 ───────────────────────────────────────────────────────────────
    
    def get_active_provider(self) -> Optional[Dict[str, Any]]:
        """获取当前活跃Provider信息"""
        with self._state_lock:
            if self._primary_state:
                return {
                    "provider": self._primary_state.provider.provider_name,
                    "model": self._primary_state.model_name,
                    "status": self._primary_state.status.value,
                    "is_healthy": self._primary_state.is_healthy
                }
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._state_lock:
            uptime = time.time() - self._stats["start_time"]
            return {
                **self._stats,
                "uptime_seconds": uptime,
                "success_rate": (
                    (self._stats["total_requests"] - self._stats["failed_requests"]) /
                    self._stats["total_requests"]
                    if self._stats["total_requests"] > 0 else 1.0
                )
            }
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """列出所有配置的Provider"""
        with self._state_lock:
            providers = []
            
            if self._primary_state:
                providers.append({
                    "provider": self._primary_state.provider.provider_name,
                    "model": self._primary_state.model_name,
                    "role": "primary",
                    "status": self._primary_state.status.value,
                    "is_healthy": self._primary_state.is_healthy
                })
            
            for state in self._fallback_states:
                key = f"{state.provider.provider_name}:{state.model_name}"
                fb_config = self._fallback_priorities.get(key)
                providers.append({
                    "provider": state.provider.provider_name,
                    "model": state.model_name,
                    "role": "fallback",
                    "priority": fb_config.priority if fb_config else 999,
                    "status": state.status.value,
                    "is_healthy": state.is_healthy
                })
            
            return providers


# ── 全局单例访问函数 ──────────────────────────────────────────────────────────

_orchestrator_instance: Optional[ProviderOrchestrator] = None


def get_orchestrator() -> ProviderOrchestrator:
    """获取全局编排器实例"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ProviderOrchestrator.get_instance()
    return _orchestrator_instance


def reset_orchestrator():
    """重置编排器（主要用于测试）"""
    global _orchestrator_instance
    _orchestrator_instance = None
    ProviderOrchestrator.reset_instance()
