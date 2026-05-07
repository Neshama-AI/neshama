"""
Anthropic Provider - 2026 全面升级版
Claude 4.6, 4.5, 4 系列模型

文档: https://docs.anthropic.com/claude/reference
支持: Extended Thinking, Tool Use, Vision
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude 提供商 - 2026 全面升级"""
    
    provider_name = "anthropic"
    provider_display_name = "Anthropic (Claude)"
    
    # 2026 最新模型列表
    supported_models = [
        # Claude 4.6 系列 (2026 最新)
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        # Claude 4 系列
        "claude-opus-4",
        "claude-sonnet-4",
        "claude-haiku-4",
        # Claude 3.5 系列 (保留兼容)
        "claude-3-5-sonnet",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["claude-opus-4-6", "claude-opus-4"],
        "standard": ["claude-sonnet-4-6", "claude-sonnet-4", "claude-3-5-sonnet"],
        "fast": ["claude-haiku-4-5", "claude-haiku-4", "claude-3-haiku"],
        "reasoning": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-opus-4", "claude-sonnet-4"],
    }
    
    # 模型别名映射
    MODEL_ALIASES = {
        "claude-opus-4-6": "claude-opus-4-6-20250514",
        "claude-sonnet-4-6": "claude-sonnet-4-6-20250514",
        "claude-haiku-4-5": "claude-haiku-4-5-20250620",
        "claude-opus-4": "claude-opus-4-20250514",
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        "claude-haiku-4": "claude-haiku-4-20250514",
        "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
    ANTHROPIC_VERSION = "2023-06-01"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        if not self.config.base_url:
            self.config.base_url = self.DEFAULT_BASE_URL
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _normalize_model(self, model: str) -> str:
        """规范化模型名称"""
        return self.MODEL_ALIASES.get(model, model)
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": self.ANTHROPIC_VERSION,
            "anthropic-dangerous-direct-browser-access": "true"
        }
        headers.update(self.config.extra_headers)
        return headers
    
    def _transform_messages_to_anthropic(self, messages: list) -> tuple:
        """
        转换消息格式为 Anthropic 格式
        
        Returns:
            (system_prompt, transformed_messages)
        """
        system_prompt = ""
        transformed = []
        
        for msg in messages:
            role = msg.role.value if hasattr(msg, 'role') else msg.get("role")
            content = msg.content if hasattr(msg, 'content') else msg.get("content", "")
            
            if role == "system":
                system_prompt += content + "\n"
            else:
                # Anthropic 只支持 user 和 assistant
                if role == "function":
                    role = "user"  # 转换为 user 角色
                transformed.append({
                    "role": role,
                    "content": content
                })
        
        return system_prompt.strip(), transformed
    
    def _build_payload(
        self,
        messages: list,
        model: str,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        构建请求载荷
        
        支持参数:
            - thinking: Extended thinking 配置
            - thinking_tokens: 思考 token 预算
            - system: 系统提示
        """
        system, transformed_messages = self._transform_messages_to_anthropic(messages)
        
        # 获取 max_tokens
        max_tokens = kwargs.pop("max_tokens", kwargs.pop("max_output_tokens", 4096))
        
        payload = {
            "model": self._normalize_model(model),
            "messages": transformed_messages,
            "stream": stream,
            "max_tokens": max_tokens,
        }
        
        # 系统提示
        if system:
            payload["system"] = system
        elif kwargs.get("system"):
            payload["system"] = kwargs["system"]
        
        # 温度
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        
        # Top P
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        
        # Top K
        if "top_k" in kwargs:
            payload["top_k"] = kwargs["top_k"]
        
        # ========== 2026 新特性 ==========
        
        # Extended Thinking (Claude 4 系列)
        if kwargs.get("thinking") and model.startswith("claude-opus-4") or model.startswith("claude-sonnet-4"):
            thinking_config = {
                "type": "enabled",
                "budget_tokens": kwargs.get("thinking_tokens", 10000)
            }
            # 排除内容类型
            if "thinking_excluded_content_types" in kwargs:
                thinking_config["thinking_excluded_content_types"] = kwargs["thinking_excluded_content_types"]
            payload["thinking"] = thinking_config
        
        # Beta 头信息 (用于访问预览功能)
        beta_headers = kwargs.get("beta_header")
        if beta_headers:
            pass  # 通过 extra_headers 传递
        
        # Anthropic 的工具使用
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]
        
        # Metadata
        if "metadata" in kwargs:
            payload["metadata"] = kwargs["metadata"]
        
        # Stop sequences
        if "stop_sequences" in kwargs:
            payload["stop_sequences"] = kwargs["stop_sequences"]
        
        return payload
    
    def _format_messages(self, messages) -> list:
        """格式化消息"""
        formatted = []
        for msg in messages:
            if isinstance(msg, Message):
                formatted.append(msg.to_dict())
            elif isinstance(msg, dict):
                formatted.append(msg)
            elif isinstance(msg, str):
                formatted.append({"role": "user", "content": msg})
        return formatted
    
    def _get_default_max_tokens(self, model: str) -> int:
        """获取模型默认最大 token 数"""
        defaults = {
            "claude-opus-4-6": 200000,
            "claude-sonnet-4-6": 200000,
            "claude-haiku-4-5": 200000,
            "claude-opus-4": 200000,
            "claude-sonnet-4": 200000,
            "claude-haiku-4": 200000,
            "claude-3-5-sonnet": 8192,
            "claude-3-opus": 4096,
            "claude-3-sonnet": 4096,
            "claude-3-haiku": 4096,
        }
        return defaults.get(model, 4096)
    
    async def _make_request(
        self,
        url: str,
        headers: Dict,
        payload: Dict,
        timeout: int
    ) -> Dict:
        """发送 HTTP 请求"""
        session = await self._get_session()
        
        async with session.post(
            url,
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                try:
                    error_json = json.loads(error_text)
                    error_msg = error_json.get("error", {}).get("message", error_text)
                except:
                    error_msg = error_text
                raise Exception(f"Anthropic API error: {response.status} - {error_msg}")
            
            result = await response.json()
            return result
    
    def _parse_response(self, response: Dict, model: str) -> ModelResponse:
        """解析响应"""
        try:
            content = response.get("content", [])
            text = ""
            tool_calls = []
            
            for block in content:
                if block.get("type") == "text":
                    text += block.get("text", "")
                elif block.get("type") == "tool_use":
                    tool_calls.append({
                        "id": block.get("id"),
                        "name": block.get("name"),
                        "input": block.get("input", {})
                    })
            
            # 解析 thinking block (如果有)
            thinking_content = None
            if "thinking" in response:
                thinking_content = response.get("thinking", {}).get("content", "")
            
            usage = {
                "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                "output_tokens": response.get("usage", {}).get("output_tokens", 0),
            }
            usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
            
            # 添加思考 token (如果有)
            if thinking_content:
                usage["thinking_tokens"] = response.get("usage", {}).get("thinking_tokens", 0)
            
            return ModelResponse(
                content=text,
                model=model,
                provider=self.provider_name,
                raw_response=response,
                usage=usage,
                finish_reason=response.get("stop_reason"),
                tool_calls=tool_calls if tool_calls else None
            )
        except Exception as e:
            return ModelResponse(
                content="",
                model=model,
                provider=self.provider_name,
                raw_response=response,
                error=f"Parse error: {str(e)}"
            )
    
    async def _parse_stream_response(
        self,
        response: aiohttp.ClientResponse,
        model: str
    ) -> AsyncIterator[StreamChunk]:
        """解析流式响应"""
        index = 0
        async for line in response.content:
            line = line.decode('utf-8').strip()
            
            if not line or line.startswith(":") or line.startswith("event:"):
                continue
            
            if line.startswith("data: "):
                line = line[6:]
            
            if line == "[DONE]":
                continue
            
            try:
                chunk_data = json.loads(line)
                
                event_type = chunk_data.get("type")
                
                if event_type == "content_block_delta":
                    delta_type = chunk_data.get("delta", {}).get("type")
                    if delta_type == "text_delta":
                        delta = chunk_data.get("delta", {}).get("text", "")
                        yield StreamChunk(
                            content=delta,
                            delta=delta,
                            model=model,
                            provider=self.provider_name,
                            index=index,
                            raw_chunk=chunk_data
                        )
                        index += 1
                    elif delta_type == "thinking_delta":
                        # Thinking 内容 (可以通过参数控制是否返回)
                        pass
                
                elif event_type == "message_delta":
                    finish_reason = chunk_data.get("delta", {}).get("stop_reason")
                    if finish_reason:
                        yield StreamChunk(
                            content="",
                            delta="",
                            model=model,
                            provider=self.provider_name,
                            index=index,
                            finish_reason=finish_reason,
                            raw_chunk=chunk_data
                        )
                        
            except json.JSONDecodeError:
                continue
    
    async def call(
        self,
        messages,
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """
        调用 Claude 模型
        
        Args:
            messages: 消息列表
            model: 模型名称
            stream: 是否流式
            **kwargs: 其他参数
        
        Returns:
            ModelResponse 或 AsyncIterator[StreamChunk]
        """
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "claude-sonnet-4-6"
        
        messages = self._transform_messages(messages)
        headers = self._build_headers()
        payload = self._build_payload(messages, model, stream, **kwargs)
        
        url = f"{self.config.base_url.rstrip('/')}/messages"
        
        try:
            if stream:
                session = await self._get_session()
                async with session.post(
                    url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Anthropic API error: {response.status} - {error_text}")
                    return self._parse_stream_response(response, model)
            else:
                result = await self._make_request(url, headers, payload, self.config.timeout)
                self._record_success()
                latency_ms = (time.time() - start_time) * 1000
                response = self._parse_response(result, model)
                response.latency_ms = latency_ms
                return response
                
        except Exception as e:
            self._record_failure(str(e))
            latency_ms = (time.time() - start_time) * 1000
            return ModelResponse(
                content="", model=model, provider=self.provider_name,
                latency_ms=latency_ms, error=str(e)
            )
    
    async def call_stream(self, messages, model: Optional[str] = None, **kwargs):
        """流式调用"""
        return self.call(messages, model, stream=True, **kwargs)
