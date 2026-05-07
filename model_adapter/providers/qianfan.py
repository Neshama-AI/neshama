"""
百度千帆 (QianFan) Provider - 2026 全面升级版
文心一言 ERNIE 4.5, ERNIE Speed/Lite 系列

文档: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clntutve
支持: ERNIE 4.5, Function Call
"""

import aiohttp
import json
import hashlib
import hmac
import time
import base64
from typing import Any, Dict, AsyncIterator, Optional, List
from urllib.parse import urlencode
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class QianFanProvider(BaseProvider):
    """百度千帆提供商 - 2026 全面升级"""
    
    provider_name = "qianfan"
    provider_display_name = "百度千帆 (文心一言)"
    
    # 2026 最新模型列表
    supported_models = [
        # ERNIE 4.5 系列
        "ernie-4.5",                    # ERNIE 4.5 标准版
        "ernie-4.5-8k",                 # ERNIE 4.5 8K
        # ERNIE Speed/Lite 系列
        "ernie-speed-128k",            # 高速版 128K
        "ernie-speed-32k",             # 高速版 32K
        "ernie-lite-8k",               # 轻量版 8K
        "ernie-lite-4k",               # 轻量版 4K
        # ERNIE 4.0 系列 (保留兼容)
        "ernie-4.0-8k-latest",         # ERNIE 4.0 最新版
        "ernie-4.0-8k",                # ERNIE 4.0 标准版
        # Embedding
        "embedding-v1",                 # Embedding v1
        "bge-large-zh",                # BGE 中文大模型
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["ernie-4.5", "ernie-4.5-8k", "ernie-4.0-8k-latest", "ernie-4.0-8k"],
        "fast": ["ernie-speed-128k", "ernie-speed-32k"],
        "lite": ["ernie-lite-8k", "ernie-lite-4k"],
        "embedding": ["embedding-v1", "bge-large-zh"],
    }
    
    def __init__(
        self,
        config: ProviderConfig,
        access_key: str = "",
        secret_key: str = ""
    ):
        super().__init__(config)
        self.access_key = access_key
        self.secret_key = secret_key
        self._session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None
        self._token_expires_at: float = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout, connect=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def _get_access_token(self) -> str:
        """获取 Access Token"""
        if self._token and time.time() < self._token_expires_at - 300:
            return self._token
        
        if self.access_key:
            self._token = self.access_key
            return self._token
        
        self._token = self.config.api_key
        return self._token
    
    def _build_headers(self, auth_token: str = "") -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        elif self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
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
            "messages": self._format_messages(messages),
            "stream": stream,
        }
        
        # max_tokens
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        elif "max_output_tokens" in kwargs:
            payload["max_output_tokens"] = kwargs["max_output_tokens"]
        else:
            payload["max_output_tokens"] = self._get_default_max_tokens(model)
        
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        
        # 惩罚参数
        if "penalty_score" in kwargs:
            payload["penalty_score"] = kwargs["penalty_score"]
        
        # 停止词
        if "stop" in kwargs:
            payload["stop"] = kwargs["stop"]
        
        # 函数调用
        if "tools" in kwargs and kwargs["tools"]:
            payload["functions"] = kwargs["tools"]
        
        # Response format
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]
        
        return payload
    
    def _format_messages(self, messages) -> List[Dict]:
        """格式化消息"""
        formatted = []
        
        for msg in messages:
            if isinstance(msg, Message):
                msg_dict = msg.to_dict()
                msg_dict = {k: v for k, v in msg_dict.items() if v is not None}
                formatted.append(msg_dict)
            elif isinstance(msg, dict):
                formatted.append(msg)
            elif isinstance(msg, str):
                formatted.append({
                    "role": "user",
                    "content": msg
                })
        
        return formatted
    
    def _get_default_max_tokens(self, model: str) -> int:
        """获取模型默认最大 token 数"""
        defaults = {
            "ernie-4.5": 32000,
            "ernie-4.5-8k": 8000,
            "ernie-speed-128k": 128000,
            "ernie-speed-32k": 32000,
            "ernie-lite-8k": 8000,
            "ernie-lite-4k": 4000,
            "ernie-4.0-8k-latest": 8000,
            "ernie-4.0-8k": 8000,
        }
        return defaults.get(model, 8192)
    
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
        
        try:
            if stream:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"[QianFan Error] {error_text}")
                    return response
            else:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"[QianFan Error] {error_text}")
                    
                    result = await response.json()
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"QianFan request failed: {e}")
            raise
    
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
            
            content = message.get("content", "")
            
            usage = {
                "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": response.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": response.get("usage", {}).get("total_tokens", 0)
            }
            
            return ModelResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                raw_response=response,
                usage=usage,
                finish_reason=choice.get("finish_reason"),
                tool_calls=message.get("tool_calls")
            )
            
        except Exception as e:
            logger.error(f"Failed to parse QianFan response: {e}")
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
                
                choices = chunk_data.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {}).get("content", "")
                    finish_reason = choices[0].get("finish_reason")
                    
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
                        
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse stream chunk: {e}")
                continue
    
    async def call(
        self,
        messages,
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """对话接口"""
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "ernie-4.5"
        
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
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"QianFan API error: {response.status} - {error_text}")
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
