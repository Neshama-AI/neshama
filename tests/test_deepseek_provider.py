"""
DeepSeek Provider 测试
测试DeepSeek API调用（mock）
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

# 设置路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_adapter.providers.deepseek import DeepSeekProvider
from model_adapter.providers.base import ProviderConfig, Message, MessageRole, ModelResponse


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def config():
    """创建测试配置"""
    return ProviderConfig(
        name="deepseek",
        api_key="test-api-key",
        base_url="https://api.deepseek.com",
        timeout=60,
    )


@pytest.fixture
def provider(config):
    """创建DeepSeek Provider实例"""
    return DeepSeekProvider(config)


@pytest.fixture
def mock_session():
    """创建mock session"""
    session = AsyncMock()
    return session


# ── 测试用例 ──────────────────────────────────────────────────────────────────

class TestDeepSeekProviderInit:
    """测试初始化"""
    
    def test_init(self, config):
        """基本初始化"""
        provider = DeepSeekProvider(config)
        
        assert provider.provider_name == "deepseek"
        assert provider.provider_display_name == "DeepSeek"
        assert provider.config.api_key == "test-api-key"
        assert provider.config.base_url == "https://api.deepseek.com"
    
    def test_default_base_url(self, config):
        """默认base_url"""
        config.base_url = ""
        provider = DeepSeekProvider(config)
        
        assert provider.config.base_url == "https://api.deepseek.com"
    
    def test_supported_models(self, provider):
        """支持的模型"""
        assert "deepseek-chat" in provider.supported_models
        assert "deepseek-v3" in provider.supported_models
        assert "deepseek-reasoner" in provider.supported_models
        assert "deepseek-r1" in provider.supported_models
    
    def test_model_groups(self, provider):
        """模型分组"""
        assert "cheap" in provider.MODEL_GROUPS
        assert "reasoning" in provider.MODEL_GROUPS
        assert "deepseek-chat" in provider.MODEL_GROUPS["cheap"]


class TestNormalizeModel:
    """测试模型名称规范化"""
    
    def test_normalize_chat(self, provider):
        """规范化deepseek-chat"""
        result = provider._normalize_model("deepseek-chat")
        assert result == "deepseek-chat"
    
    def test_normalize_v3(self, provider):
        """规范化deepseek-v3"""
        result = provider._normalize_model("deepseek-v3")
        assert result == "deepseek-chat"
    
    def test_normalize_reasoner(self, provider):
        """规范化deepseek-reasoner"""
        result = provider._normalize_model("deepseek-reasoner")
        assert result == "deepseek-reasoner"
    
    def test_normalize_r1(self, provider):
        """规范化deepseek-r1"""
        result = provider._normalize_model("deepseek-r1")
        assert result == "deepseek-reasoner"


class TestBuildHeaders:
    """测试构建请求头"""
    
    def test_basic_headers(self, provider):
        """基本请求头"""
        headers = provider._build_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-api-key"
        assert headers["Content-Type"] == "application/json"
    
    def test_anthropic_headers(self, provider):
        """Anthropic兼容请求头"""
        headers = provider._build_headers(use_anthropic_api=True)
        
        assert "anthropic-version" in headers
        assert headers["anthropic-version"] == "2023-06-01"


class TestBuildPayload:
    """测试构建请求载荷"""
    
    def test_basic_payload(self, provider):
        """基本载荷"""
        messages = [
            Message(role=MessageRole.USER, content="Hello")
        ]
        payload = provider._build_payload(messages, "deepseek-chat")
        
        assert payload["model"] == "deepseek-chat"
        assert "messages" in payload
        assert payload["stream"] is False
    
    def test_payload_with_temperature(self, provider):
        """带温度参数"""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        payload = provider._build_payload(
            messages,
            "deepseek-chat",
            temperature=0.8
        )
        
        assert payload["temperature"] == 0.8
    
    def test_payload_with_max_tokens(self, provider):
        """带最大token参数"""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        payload = provider._build_payload(
            messages,
            "deepseek-chat",
            max_tokens=100
        )
        
        assert payload["max_tokens"] == 100
    
    def test_payload_with_fim(self, provider):
        """FIM补全"""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        payload = provider._build_payload(
            messages,
            "deepseek-chat",
            fim={"prompt": "prefix", "suffix": "suffix"}
        )
        
        assert "fim" in payload
        assert payload["fim"]["prompt"] == "prefix"
        assert payload["fim"]["suffix"] == "suffix"


class TestBuildAnthropicPayload:
    """测试Anthropic兼容载荷"""
    
    def test_basic_anthropic_payload(self, provider):
        """基本Anthropic载荷"""
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are helpful"),
            Message(role=MessageRole.USER, content="Hello")
        ]
        payload = provider._build_anthropic_payload(messages, "deepseek-reasoner")
        
        assert "system" in payload
        # system可能包含换行符
        assert "You are helpful" in payload["system"]
        assert len(payload["messages"]) == 1


class TestFormatMessages:
    """测试消息格式化"""
    
    def test_format_message_objects(self, provider):
        """格式化Message对象"""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there")
        ]
        formatted = provider._format_messages(messages)
        
        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Hello"
    
    def test_format_dict_messages(self, provider):
        """格式化字典消息"""
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        formatted = provider._format_messages(messages)
        
        assert len(formatted) == 1
        assert formatted[0]["content"] == "Hello"
    
    def test_format_string_message(self, provider):
        """格式化字符串消息 - 注意: base.py的_transform_messages将字符串转为列表"""
        # DeepSeekProvider._format_messages只处理Message对象和dict
        # 字符串消息应该通过_transform_messages处理
        formatted = provider._transform_messages("Hello")
        
        assert len(formatted) == 1
        assert formatted[0].role == MessageRole.USER
        assert formatted[0].content == "Hello"


class TestParseResponse:
    """测试响应解析"""
    
    def test_parse_openai_format(self, provider):
        """解析OpenAI格式响应"""
        response = {
            "choices": [{
                "message": {"content": "Hello, how can I help?"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18
            }
        }
        
        result = provider._parse_response(response, "deepseek-chat")
        
        assert result.content == "Hello, how can I help?"
        assert result.model == "deepseek-chat"
        assert result.provider == "deepseek"
        assert result.finish_reason == "stop"
        assert result.usage["total_tokens"] == 18
    
    def test_parse_anthropic_format(self, provider):
        """解析Anthropic格式响应"""
        response = {
            "content": [
                {"type": "text", "text": "Here is my response."}
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 15
            }
        }
        
        result = provider._parse_response(response, "deepseek-reasoner")
        
        assert result.content == "Here is my response."
        assert result.finish_reason == "end_turn"
    
    def test_parse_with_reasoning_content(self, provider):
        """解析带reasoning_content的响应"""
        response = {
            "choices": [{
                "message": {
                    "content": "The answer is 42.",
                    "reasoning_content": "Let me think step by step..."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        
        result = provider._parse_response(response, "deepseek-reasoner")
        
        assert result.usage["reasoning_content_length"] == len("Let me think step by step...")
    
    def test_parse_empty_choices(self, provider):
        """解析空choices"""
        response = {"choices": []}
        
        result = provider._parse_response(response, "deepseek-chat")
        
        assert result.error == "No choices in response"


class TestPricing:
    """测试定价"""
    
    def test_v3_pricing(self, provider):
        """V3定价"""
        pricing = provider.PRICING["deepseek-chat"]
        
        assert pricing["input"] == 0.27
        assert pricing["output"] == 1.10
        assert pricing["cache"] == 0.027
    
    def test_r1_pricing(self, provider):
        """R1定价"""
        pricing = provider.PRICING["deepseek-reasoner"]
        
        assert pricing["input"] == 0.27
        assert pricing["output"] == 1.10


class TestDefaultMaxTokens:
    """测试默认最大token"""
    
    def test_chat_default(self, provider):
        """对话模型默认token"""
        max_tokens = provider._get_default_max_tokens("deepseek-chat")
        assert max_tokens == 128000
    
    def test_reasoner_default(self, provider):
        """推理模型默认token"""
        max_tokens = provider._get_default_max_tokens("deepseek-reasoner")
        assert max_tokens == 128000
    
    def test_v4_default(self, provider):
        """V4默认token"""
        max_tokens = provider._get_default_max_tokens("deepseek-v4-pro")
        assert max_tokens == 1000000


class TestCall:
    """测试call方法"""
    
    @pytest.mark.asyncio
    @patch.object(DeepSeekProvider, '_get_session')
    async def test_call_basic(self, mock_get_session, provider):
        """基本调用测试（验证mock设置）"""
        # 创建一个简单的mock响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {"content": "Test response"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 2,
                "total_tokens": 7
            }
        })
        
        mock_session = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_ctx)
        mock_get_session.return_value = mock_session
        
        messages = [Message(role=MessageRole.USER, content="Hello")]
        result = await provider.call(messages, "deepseek-chat")
        
        # 验证调用结果
        assert result is not None
        assert hasattr(result, 'content')


# ── 运行测试 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
