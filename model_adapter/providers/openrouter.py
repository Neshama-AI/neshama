"""
OpenRouter Provider - 2026 全面升级版 ⭐ 聚合网关
聚合所有主流模型的统一入口

文档: https://openrouter.ai/docs
认证: Bearer Token
特点: 一个接口走天下，自动路由到各后端，国内可直连，免费 50 次/天
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseProvider):
    """OpenRouter 提供商 - 2026 全面升级 ⭐ 聚合网关"""
    
    provider_name = "openrouter"
    provider_display_name = "OpenRouter (聚合网关)"
    
    # 2026 最新常用模型列表 (OpenRouter 聚合所有模型)
    supported_models = [
        # OpenAI
        "openai/gpt-4.1",
        "openai/gpt-4.1-mini",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        # Anthropic
        "anthropic/claude-sonnet-4-6",
        "anthropic/claude-haiku-4-5",
        "anthropic/claude-opus-4-6",
        # Google
        "google/gemini-2.5-pro",
        "google/gemini-2.5-flash",
        "google/gemini-2.0-flash",
        # DeepSeek
        "deepseek/deepseek-v4-pro",
        "deepseek/deepseek-chat",
        # Meta/LLaMA
        "meta-llama/llama-4-scout",
        "meta-llama/llama-4-maverick",
        "meta-llama/llama-3.3-70b-instruct",
        # Qwen
        "qwen/qwen3.5-plus",
        "qwen/qwen2.5-72b-instruct",
        # Mistral
        "mistralai/mistral-large",
        "mistralai/codestral",
        # 其他
        "x-ai/grok-4.1",
        "cohere/command-a",
        "perplexity/sonar-pro",
    ]
    
    # 模型分组 (按来源)
    MODEL_GROUPS = {
        "openai": ["openai/gpt-4.1", "openai/gpt-4.1-mini", "openai/gpt-4o", "openai/gpt-4o-mini"],
        "anthropic": ["anthropic/claude-sonnet-4-6", "anthropic/claude-haiku-4-5", "anthropic/claude-opus-4-6"],
        "google": ["google/gemini-2.5-pro", "google/gemini-2.5-flash", "google/gemini-2.0-flash"],
        "deepseek": ["deepseek/deepseek-v4-pro", "deepseek/deepseek-chat"],
        "llama": ["meta-llama/llama-4-scout", "meta-llama/llama-4-maverick", "meta-llama/llama-3.3-70b-instruct"],
        "qwen": ["qwen/qwen3.5-plus", "qwen/qwen2.5-72b-instruct"],
        "mistral": ["mistralai/mistral-large", "mistralai/codestral"],
        "xai": ["x-ai/grok-4.1"],
        "cohere": ["cohere/command-a"],
        "perplexity": ["perplexity/sonar-pro"],
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    
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
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://neshama.ai",  # OpenRouter 推荐
            "X-Title": "Neshama AI Agent"
        }
        headers.update(self.config.extra_headers)
        return headers
    
    def _build_payload(
        self,
        messages: list,
        model: str,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """构建请求载荷"""
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "stream": stream,
            "max_tokens": kwargs.get("max_tokens", self._get_default_max_tokens(model)),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 1.0),
        }
        
        # 移除 None 值
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # n
        if "n" in kwargs:
            payload["n"] = kwargs["n"]
        
        # 停止词
        if "stop" in kwargs:
            payload["stop"] = kwargs["stop"]
        
        # 函数调用
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]
            if "tool_choice" in kwargs:
                payload["tool_choice"] = kwargs["tool_choice"]
        
        # 路由优化
        if kwargs.get("route"):
            payload["route"] = kwargs["route"]  # e.g., "fallback", "smart"
        
        # Provider 偏好
        if kwargs.get("provider"):
            payload["provider"] = kwargs["provider"]
        
        # 变换 (Transformations)
        if kwargs.get("transforms"):
            payload["transforms"] = kwargs["transforms"]
        
        # 模型别名
        if kwargs.get("model_alias"):
            payload["model_alias"] = kwargs["model_alias"]
        
        return payload
    
    def _format_messages(self, messages) -> List[Dict]:
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
        # 默认 128K
        return 128000
    
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
                raise Exception(f"OpenRouter API error: {response.status} - {error_msg}")
            
            if stream:
                return response
            return await response.json()
    
    def _parse_response(self, response: Dict, model: str) -> ModelResponse:
        """解析响应"""
        try:
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
            
            # 解析 OpenRouter 特有的 provider 和 usage
            provider = response.get("provider", {}).get("name", self.provider_name)
            
            return ModelResponse(
                content=message.get("content", ""),
                model=model,
                provider=provider,
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
        """解析流式响应"""
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
        **kwargs
    ) -> Any:
        """调用 OpenRouter (聚合网关)"""
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "openai/gpt-4o"
        
        messages = self._transform_messages(messages)
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
                        raise Exception(f"OpenRouter API error: {response.status} - {error_text}")
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
