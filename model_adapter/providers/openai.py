"""
OpenAI Provider - 2026 全面升级版
GPT-5, GPT-4.1, o3/o4-mini, Codex 系列模型

文档: https://platform.openai.com/docs/api-reference
支持: Chat Completions API, Responses API, Thinking Mode
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI 提供商 - 2026 全面升级"""
    
    provider_name = "openai"
    provider_display_name = "OpenAI"
    
    # 2026 最新模型列表
    supported_models = [
        # GPT-5 系列
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        # GPT-4.1 系列
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        # GPT-4 系列（保留兼容）
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-4-32k",
        # 推理模型
        "o3",
        "o4-mini",
        # Codex 系列
        "codex-mini-latest",
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["gpt-5", "gpt-4.1", "o3"],
        "standard": ["gpt-5-mini", "gpt-4.1-mini", "gpt-4o", "gpt-4-turbo"],
        "fast": ["gpt-5-nano", "gpt-4.1-nano", "gpt-4o-mini", "o4-mini"],
        "reasoning": ["o3", "o4-mini"],
        "coding": ["codex-mini-latest", "gpt-4.1", "gpt-4.1-mini"],
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        # 默认使用 OpenAI 官方端点
        if not self.config.base_url:
            self.config.base_url = self.DEFAULT_BASE_URL
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _build_headers(self, use_responses_api: bool = False) -> Dict[str, str]:
        """
        构建请求头
        
        Args:
            use_responses_api: 是否使用 Responses API
        """
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        # Responses API 需要不同的认证方式
        if use_responses_api:
            headers["OpenAI-Api-Key"] = self.config.api_key
        
        if self.config.api_version:
            headers["OpenAI-Version"] = self.config.api_version
        
        headers.update(self.config.extra_headers)
        return headers
    
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
            - thinking_mode: 推理模式 (off/basic/medium/high/max)
            - thinking_budget: 思考 token 预算 (用于 o3/o4-mini)
            - include_reasoning: 是否在响应中包含推理内容
        """
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "stream": stream,
            "max_tokens": kwargs.get("max_tokens", self._get_default_max_tokens(model)),
            "temperature": kwargs.get("temperature", kwargs.get("reasoning_temperature", 0.7)),
            "top_p": kwargs.get("top_p", 1.0),
            "n": kwargs.get("n", 1),
            "presence_penalty": kwargs.get("presence_penalty", 0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0),
        }
        
        # 移除 None 值
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # 用户标识
        if "user" in kwargs:
            payload["user"] = kwargs["user"]
        
        # 函数调用
        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]
            if "tool_choice" in kwargs:
                payload["tool_choice"] = kwargs["tool_choice"]
        
        # 响应格式
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]
        
        # ========== 2026 新特性 ==========
        
        # Thinking Mode (o3/o4-mini)
        thinking_mode = kwargs.get("thinking_mode")
        if thinking_mode and model in ["o3", "o4-mini"]:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": kwargs.get("thinking_budget", 10000)
            }
        
        # include_reasoning_in_content (o3/o4-mini)
        if kwargs.get("include_reasoning") and model in ["o3", "o4-mini"]:
            payload["include_reasoning_in_content"] = True
        
        # Modalities (文本+音频)
        if "modalities" in kwargs:
            payload["modalities"] = kwargs["modalities"]
        
        # Parallel tool calls
        if "parallel_tool_calls" in kwargs:
            payload["parallel_tool_calls"] = kwargs["parallel_tool_calls"]
        
        # Store (记忆功能)
        if kwargs.get("store"):
            payload["store"] = True
        
        return payload
    
    def _build_responses_payload(
        self,
        messages: list,
        model: str,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        构建 Responses API 载荷
        
        Responses API 是 OpenAI 2026 的新 API 格式
        文档: https://platform.openai.com/docs/api-reference/responses
        """
        # 转换消息格式
        input_content = []
        for msg in self._format_messages(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            input_content.append({
                "role": role,
                "content": [{"type": "input_text", "text": content}]
            })
        
        payload = {
            "model": model,
            "input": input_content,
            "stream": stream,
        }
        
        # Thinking 配置
        if kwargs.get("thinking_mode") and model in ["o3", "o4-mini"]:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": kwargs.get("thinking_budget", 10000)
            }
        
        # 工具
        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]
        
        # 音频输出
        if "modalities" in kwargs:
            payload["modalities"] = kwargs["modalities"]
        
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
            "gpt-5": 128000,
            "gpt-5-mini": 128000,
            "gpt-5-nano": 64000,
            "gpt-4.1": 128000,
            "gpt-4.1-mini": 128000,
            "gpt-4.1-nano": 64000,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4": 128000,
            "gpt-4-32k": 32768,
            "o3": 200000,
            "o4-mini": 200000,
            "codex-mini-latest": 64000,
        }
        return defaults.get(model, 128000)
    
    async def _make_request(
        self,
        url: str,
        headers: Dict,
        payload: Dict,
        timeout: int,
        stream: bool = False
    ) -> Any:
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
                raise Exception(f"OpenAI API error: {response.status} - {error_msg}")
            
            if stream:
                return response
            else:
                result = await response.json()
                return result
    
    def _parse_response(self, response: Dict, model: str) -> ModelResponse:
        """解析响应"""
        try:
            # 兼容 Responses API 格式
            if "output" in response:
                # Responses API 格式
                output = response.get("output", [])
                content = ""
                for item in output:
                    if item.get("type") == "message":
                        for content_item in item.get("content", []):
                            if content_item.get("type") == "output_text":
                                content += content_item.get("text", "")
                
                # 解析 reasoning (如果包含)
                reasoning = None
                for item in output:
                    if item.get("type") == "reasoning":
                        reasoning = item.get("summary", [])
                
                usage = {
                    "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": response.get("usage", {}).get("output_tokens", 0),
                    "total_tokens": response.get("usage", {}).get("total_tokens", 0),
                }
                if reasoning:
                    usage["reasoning_tokens"] = sum(r.get("tokens", 0) for r in reasoning) if isinstance(reasoning, list) else 0
                
                return ModelResponse(
                    content=content,
                    model=model,
                    provider=self.provider_name,
                    raw_response=response,
                    usage=usage,
                    finish_reason=response.get("status"),
                )
            else:
                # Chat Completions API 格式
                choices = response.get("choices", [])
                
                if not choices:
                    return ModelResponse(
                        content="",
                        model=model,
                        provider=self.provider_name,
                        error="No choices in response"
                    )
                
                choice = choices[0]
                message = choice.get("message", {})
                
                return ModelResponse(
                    content=message.get("content", ""),
                    model=model,
                    provider=self.provider_name,
                    raw_response=response,
                    usage=response.get("usage", {}),
                    finish_reason=choice.get("finish_reason"),
                    tool_calls=message.get("tool_calls")
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
        """解析流式响应 (SSE 格式)"""
        index = 0
        async for line in response.content:
            line = line.decode('utf-8').strip()
            if not line:
                continue
            
            if line.startswith("data: "):
                line = line[6:]
            
            if line == "[DONE]":
                continue
            
            try:
                chunk_data = json.loads(line)
                
                if "error" in chunk_data:
                    raise Exception(f"API Error: {chunk_data['error']}")
                
                # 兼容 Responses API 流式格式
                if "type" in chunk_data:
                    if chunk_data.get("type") == "content_delta":
                        delta = chunk_data.get("delta", "")
                        yield StreamChunk(
                            content=delta,
                            delta=delta,
                            model=model,
                            provider=self.provider_name,
                            index=index,
                            raw_chunk=chunk_data
                        )
                        index += 1
                    elif chunk_data.get("type") == "reasoning_delta":
                        # 推理内容块
                        delta = chunk_data.get("delta", "")
                        # 可以选择是否 yield 推理内容
                        if kwargs.get("include_reasoning", False):
                            yield StreamChunk(
                                content=f"[思考] {delta}",
                                delta=delta,
                                model=model,
                                provider=self.provider_name,
                                index=index,
                                raw_chunk=chunk_data
                            )
                            index += 1
                else:
                    # Chat Completions 格式
                    delta = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    finish_reason = chunk_data.get("choices", [{}])[0].get("finish_reason")
                    
                    if delta:
                        yield StreamChunk(
                            content=delta,
                            delta=delta,
                            model=model,
                            provider=self.provider_name,
                            index=index,
                            finish_reason=finish_reason,
                            raw_chunk=chunk_data
                        )
                        index += 1
                        
            except json.JSONDecodeError:
                continue
    
    async def call(
        self,
        messages,
        model: Optional[str] = None,
        stream: bool = False,
        use_responses_api: bool = False,
        **kwargs
    ) -> Any:
        """
        调用 OpenAI 模型
        
        Args:
            messages: 消息列表
            model: 模型名称
            stream: 是否流式
            use_responses_api: 是否使用 Responses API
            **kwargs: 其他参数
        
        Returns:
            ModelResponse 或 AsyncIterator[StreamChunk]
        """
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "gpt-4o"
        
        messages = self._transform_messages(messages)
        
        # 选择 API 端点
        if use_responses_api:
            url = f"{self.config.base_url.rstrip('/')}/responses"
            headers = self._build_headers(use_responses_api=True)
            payload = self._build_responses_payload(messages, model, stream, **kwargs)
        else:
            url = f"{self.config.base_url.rstrip('/')}/chat/completions"
            headers = self._build_headers()
            payload = self._build_payload(messages, model, stream, **kwargs)
        
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
                        raise Exception(f"OpenAI API error: {response.status} - {error_text}")
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
