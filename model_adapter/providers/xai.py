"""
xAI Provider - 2026 全面升级版
Grok-4.1, Grok-4, Grok-3, Grok-2 系列模型

文档: https://docs.x.ai/api
认证: Bearer Token
特点: 完全 OpenAI 兼容
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class XAIProvider(BaseProvider):
    """xAI Grok 提供商 - 2026 全面升级"""
    
    provider_name = "xai"
    provider_display_name = "xAI (Grok)"
    
    # 2026 最新模型列表
    supported_models = [
        "grok-4.1",                     # Grok-4.1 最新版
        "grok-4",                       # Grok-4
        "grok-3",                       # Grok-3
        "grok-3-beta",                  # Grok-3 Beta
        "grok-2",                       # Grok-2
        "grok-2-mini",                  # Grok-2 Mini
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["grok-4.1", "grok-4"],
        "standard": ["grok-3", "grok-3-beta"],
        "fast": ["grok-2", "grok-2-mini"],
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://api.x.ai/v1"
    
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
            "Content-Type": "application/json"
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
        
        # 函数调用
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]
            if "tool_choice" in kwargs:
                payload["tool_choice"] = kwargs["tool_choice"]
        
        # 响应格式
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]
        
        # xAI 特有参数
        if kwargs.get("user"):
            payload["user"] = kwargs["user"]
        
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
        defaults = {
            "grok-4.1": 256000,
            "grok-4": 256000,
            "grok-3": 131072,
            "grok-3-beta": 131072,
            "grok-2": 131072,
            "grok-2-mini": 131072,
        }
        return defaults.get(model, 131072)
    
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
                raise Exception(f"xAI API error: {response.status} - {error_msg}")
            
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
        """调用 Grok 模型"""
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "grok-4.1"
        
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
                        raise Exception(f"xAI API error: {response.status} - {error_text}")
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
