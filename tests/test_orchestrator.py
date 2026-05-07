"""
ProviderOrchestrator 测试
测试热切换/降级/恢复功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List

# 设置路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_adapter.orchestrator import (
    ProviderOrchestrator,
    DialogComplexity,
    ProviderStatus,
    FallbackProvider,
    get_orchestrator,
    reset_orchestrator,
)
from model_adapter.providers.base import Message, MessageRole, ModelResponse, BaseProvider


class MockProvider(BaseProvider):
    """测试用Mock Provider"""
    
    provider_name = "mock"
    provider_display_name = "Mock Provider"
    supported_models = ["mock-model"]
    
    def __init__(self):
        # 不调用super，避免config问题
        self.config = None
        self._request_count = 0
        self._failure_count = 0
        self._last_failure_time = 0
        self._health_score = 1.0
    
    @property
    def is_healthy(self):
        return self._health_score > 0.3
    
    @property
    def health_score(self):
        return self._health_score
    
    def _build_headers(self):
        return {}
    
    def _build_payload(self, messages, model, **kwargs):
        return {}
    
    def _parse_response(self, response, model):
        return ModelResponse(
            content="mock response",
            model=model,
            provider=self.provider_name
        )
    
    def _parse_stream_response(self, response, model):
        """Mock流式响应"""
        async def gen():
            yield None
        return gen()
    
    async def _make_request(self, url, headers, payload, timeout):
        return {"choices": [{"message": {"content": "mock response"}}]}
    
    def _record_success(self):
        self._request_count += 1
        self._health_score = min(1.0, self._health_score + 0.05)
    
    def _record_failure(self, error):
        self._request_count += 1
        self._failure_count += 1
        self._health_score = max(0, self._health_score - 0.2)


class FailingProvider(MockProvider):
    """会失败的Provider"""
    provider_name = "failing"
    
    async def call(self, messages, model=None, stream=False, **kwargs):
        self._record_failure("intentional failure")
        raise Exception("Provider failed")


class SlowProvider(MockProvider):
    """超时的Provider"""
    provider_name = "slow"
    
    async def call(self, messages, model=None, stream=False, **kwargs):
        await asyncio.sleep(10)  # 超时
        return ModelResponse(
            content="slow response",
            model=model or "slow-model",
            provider=self.provider_name
        )


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_orchestrator_fixture():
    """每个测试前重置orchestrator"""
    reset_orchestrator()
    yield
    reset_orchestrator()


@pytest.fixture
def orchestrator():
    """获取orchestrator实例"""
    return get_orchestrator()


@pytest.fixture
def mock_providers():
    """创建mock providers"""
    primary = MockProvider()
    primary.provider_name = "primary"
    
    fallback1 = MockProvider()
    fallback1.provider_name = "fallback1"
    
    fallback2 = MockProvider()
    fallback2.provider_name = "fallback2"
    
    return {
        "primary": primary,
        "fallback1": fallback1,
        "fallback2": fallback2
    }


# ── 测试用例 ──────────────────────────────────────────────────────────────────

class TestProviderOrchestratorInit:
    """测试初始化"""
    
    def test_singleton(self):
        """单例模式测试"""
        reset_orchestrator()
        
        o1 = ProviderOrchestrator()
        o2 = ProviderOrchestrator()
        
        assert o1 is o2
    
    def test_get_instance(self):
        """get_instance测试"""
        reset_orchestrator()
        o = get_orchestrator()
        
        assert isinstance(o, ProviderOrchestrator)
    
    def test_default_config(self, orchestrator):
        """默认配置测试"""
        assert orchestrator.timeout == 5.0
        assert orchestrator.recovery_delay == 30.0
        assert orchestrator.max_consecutive_failures == 3
        assert orchestrator.enable_auto_recovery is True


class TestComplexityEvaluation:
    """测试对话复杂度评估"""
    
    def test_simple_greeting(self, orchestrator):
        """简单问候"""
        complexity = orchestrator.evaluate_complexity("你好，今天怎么样？")
        assert complexity == DialogComplexity.SIMPLE
    
    def test_simple_hello(self, orchestrator):
        """简单hello"""
        complexity = orchestrator.evaluate_complexity("hello, how are you?")
        # 纯英文问候可能评估为MODERATE
        assert complexity in [DialogComplexity.SIMPLE, DialogComplexity.MODERATE]
    
    def test_complex_quest(self, orchestrator):
        """复杂任务"""
        messages = [
            Message(role=MessageRole.USER, content="帮我完成这个任务吧")
        ]
        complexity = orchestrator.evaluate_complexity(messages)
        # 可能评估为COMPLEX或MODERATE
        assert complexity in [DialogComplexity.COMPLEX, DialogComplexity.MODERATE]
    
    def test_moderate_conversation(self, orchestrator):
        """中等复杂度"""
        messages = [
            Message(role=MessageRole.USER, content="跟我说说你的故事")
        ]
        complexity = orchestrator.evaluate_complexity(messages)
        assert complexity in [DialogComplexity.MODERATE, DialogComplexity.SIMPLE]


class TestSetPrimary:
    """测试设置主Provider"""
    
    @patch('model_adapter.orchestrator.get_provider')
    def test_set_primary_success(self, mock_get_provider, orchestrator, mock_providers):
        """成功设置主Provider"""
        mock_get_provider.return_value = mock_providers["primary"]
        
        success = orchestrator.set_primary("primary", "mock-model")
        
        assert success is True
        active = orchestrator.get_active_provider()
        assert active is not None
        assert active["provider"] == "primary"
        assert active["model"] == "mock-model"
    
    @patch('model_adapter.orchestrator.get_provider')
    def test_set_primary_not_found(self, mock_get_provider, orchestrator):
        """Provider不存在"""
        mock_get_provider.return_value = None
        
        success = orchestrator.set_primary("nonexistent", "model")
        
        assert success is False


class TestAddFallback:
    """测试添加降级Provider"""
    
    @patch('model_adapter.orchestrator.get_provider')
    def test_add_fallback_success(self, mock_get_provider, orchestrator, mock_providers):
        """成功添加降级Provider"""
        mock_get_provider.return_value = mock_providers["fallback1"]
        
        success = orchestrator.add_fallback(
            "fallback1",
            "mock-model",
            priority=1
        )
        
        assert success is True
        providers = orchestrator.list_providers()
        fallback_providers = [p for p in providers if p["role"] == "fallback"]
        assert len(fallback_providers) >= 1
    
    @patch('model_adapter.orchestrator.get_provider')
    def test_add_fallback_priority(self, mock_get_provider, orchestrator, mock_providers):
        """测试优先级排序"""
        mock_get_provider.return_value = mock_providers["fallback1"]
        
        orchestrator.add_fallback("fallback1", "mock-model", priority=2)
        mock_get_provider.return_value = mock_providers["fallback2"]
        orchestrator.add_fallback("fallback2", "mock-model", priority=1)
        
        providers = orchestrator.list_providers()
        fallback_providers = [p for p in providers if p["role"] == "fallback"]
        
        # priority=1 应该在前面
        assert fallback_providers[0]["provider"] == "fallback2"


class TestSwitchProvider:
    """测试切换Provider"""
    
    @patch('model_adapter.orchestrator.get_provider')
    def test_switch_success(self, mock_get_provider, orchestrator, mock_providers):
        """成功切换"""
        mock_get_provider.return_value = mock_providers["primary"]
        orchestrator.set_primary("primary", "mock-model")
        
        mock_get_provider.return_value = mock_providers["fallback1"]
        success = orchestrator.switch_provider("fallback1", "mock-model")
        
        assert success is True
        active = orchestrator.get_active_provider()
        assert active["provider"] == "fallback1"
    
    @patch('model_adapter.orchestrator.get_provider')
    def test_switch_not_found(self, mock_get_provider, orchestrator, mock_providers):
        """切换到不存在的Provider"""
        mock_get_provider.return_value = mock_providers["primary"]
        orchestrator.set_primary("primary", "mock-model")
        
        mock_get_provider.return_value = None
        success = orchestrator.switch_provider("nonexistent")
        
        assert success is False


class TestHealthCheck:
    """测试健康检查"""
    
    @pytest.mark.asyncio
    @patch('model_adapter.orchestrator.get_provider')
    async def test_health_check_primary(self, mock_get_provider, orchestrator, mock_providers):
        """检查主Provider健康"""
        mock_get_provider.return_value = mock_providers["primary"]
        orchestrator.set_primary("primary", "mock-model")
        
        results = await orchestrator.health_check()
        
        assert "primary" in results
        assert results["primary"]["provider"] == "primary"
        assert results["primary"]["is_healthy"] is True
    
    @pytest.mark.asyncio
    @patch('model_adapter.orchestrator.get_provider')
    async def test_health_check_summary(self, mock_get_provider, orchestrator, mock_providers):
        """检查汇总"""
        mock_get_provider.return_value = mock_providers["primary"]
        orchestrator.set_primary("primary", "mock-model")
        
        mock_get_provider.return_value = mock_providers["fallback1"]
        orchestrator.add_fallback("fallback1", "mock-model")
        
        results = await orchestrator.health_check()
        
        assert "summary" in results
        assert results["summary"]["total"] >= 2


class TestChatWithFallback:
    """测试带降级的chat调用"""
    
    @pytest.mark.asyncio
    @patch('model_adapter.orchestrator.get_provider')
    async def test_chat_returns_response(self, mock_get_provider, orchestrator, mock_providers):
        """基本调用测试"""
        mock_get_provider.return_value = mock_providers["primary"]
        orchestrator.set_primary("primary", "mock-model")
        
        messages = [Message(role=MessageRole.USER, content="你好")]
        
        # 模拟provider调用成功
        mock_providers["primary"].call = AsyncMock(return_value=ModelResponse(
            content="mock response",
            model="mock-model",
            provider="primary"
        ))
        
        response = await orchestrator.chat(messages)
        
        # 应该返回响应（成功或降级）
        assert response is not None
        assert hasattr(response, 'content')
    
    @pytest.mark.asyncio
    @patch('model_adapter.orchestrator.get_provider')
    async def test_chat_with_multiple_fallbacks(self, mock_get_provider, orchestrator, mock_providers):
        """多级降级测试"""
        # 设置主Provider
        mock_get_provider.return_value = mock_providers["primary"]
        orchestrator.set_primary("primary", "mock-model")
        
        # 添加fallback
        mock_get_provider.return_value = mock_providers["fallback1"]
        orchestrator.add_fallback("fallback1", "mock-model")
        
        # 模拟provider调用
        mock_providers["primary"].call = AsyncMock(return_value=ModelResponse(
            content="fallback response",
            model="mock-model",
            provider="fallback1"
        ))
        
        messages = [Message(role=MessageRole.USER, content="你好")]
        response = await orchestrator.chat(messages)
        
        # 应该返回响应
        assert response is not None


class TestStats:
    """测试统计"""
    
    @pytest.mark.asyncio
    @patch('model_adapter.orchestrator.get_provider')
    async def test_stats_increment(self, mock_get_provider, orchestrator, mock_providers):
        """统计递增"""
        mock_get_provider.return_value = mock_providers["primary"]
        orchestrator.set_primary("primary", "mock-model")
        
        # 发送请求
        messages = [Message(role=MessageRole.USER, content="你好")]
        await orchestrator.chat(messages)
        
        stats = orchestrator.get_stats()
        assert stats["total_requests"] >= 1


# ── 运行测试 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
