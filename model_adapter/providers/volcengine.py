"""
火山引擎方舟 (VolcEngine) Provider - 2026 全面升级版
豆包 Doubao 1.5 系列模型

文档: https://www.volcengine.com/docs/82379/1099475
支持: Doubao 1.5 Pro/Lite, Vision
"""

import aiohttp
import json
import hashlib
import hmac
import time
import base64
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class VolcEngineProvider(BaseProvider):
    """火山引擎方舟提供商 - 2026 全面升级"""
    
    provider_name = "volcengine"
    provider_display_name = "火山引擎方舟 (豆包)"
    
    # 2026 最新模型列表
    supported_models = [
        # Doubao 1.5 系列
        "doubao-1.5-pro",               # Doubao 1.5 Pro
        "doubao-1.5-lite",              # Doubao 1.5 Lite
        "doubao-1.5-thinking-pro",      # Doubao 1.5 思考版
        # Doubao Pro/Lite 系列 (保留兼容)
        "doubao-pro",                   # 标准版
        "doubao-lite",                  # 轻量版
        # Doubao-Vision 系列
        "doubao-vision-pro",            # 视觉理解 Pro
        "doubao-vision",                # 视觉版
        # Embedding
        "doubao-embedding",             # Embedding
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["doubao-1.5-pro", "doubao-pro"],
        "fast": ["doubao-1.5-lite", "doubao-lite"],
        "thinking": ["doubao-1.5-thinking-pro"],
        "vision": ["doubao-vision-pro", "doubao-vision"],
        "embedding": ["doubao-embedding"],
    }
    
    def __init__(
        self,
        config: ProviderConfig,
        account_id: str = "",
        secret_key: str = ""
    ):
        super().__init__(config)
        self.account_id = account_id
        self.secret_key = secret_key
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout, connect=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _generate_sign(self, timestamp: str) -> str:
        """生成签名 (TC3-HMAC-SHA256)"""
        if not self.secret_key:
            return ""
        
        secret = self.secret_key.encode('utf-8')
        message = f"ARC3\n{timestamp}\n".encode('utf-8')
        
        sign = base64.b64encode(
            hmac.new(secret, message, hashlib.sha256).digest()
        ).decode('utf-8')
        
        return sign
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        timestamp = str(int(time.time()))
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Date": timestamp,
            "X-Api-Key": self.config.api_key,
        }
        
        if self.secret_key:
            headers["X-Signature"] = self._generate_sign(timestamp)
        
        if self.account_id:
            headers["X-Account-Id"] = self.account_id
        
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
            "top_p": kwargs.get("top_p", 0.8),
        }
        
        # 停止词
        if "stop" in kwargs:
            payload["stop"] = kwargs["stop"]
        
        # 频率惩罚
        if "frequency_penalty" in kwargs:
            payload["frequency_penalty"] = kwargs["frequency_penalty"]
        
        # 存在惩罚
        if "presence_penalty" in kwargs:
            payload["presence_penalty"] = kwargs["presence_penalty"]
        
        # 响应格式
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]
        
        # 函数调用
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]
        
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
                formatted.append({
                    "role": "user",
                    "content": msg
                })
        
        return formatted
    
    def _get_default_max_tokens(self, model: str) -> int:
        """获取模型默认最大 token 数"""
        defaults = {
            "doubao-1.5-pro": 200000,
            "doubao-1.5-lite": 200000,
            "doubao-1.5-thinking-pro": 200000,
            "doubao-pro": 8192,
            "doubao-lite": 8192,
            "doubao-vision-pro": 8000,
            "doubao-vision": 8000,
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
                        raise Exception(f"[VolcEngine Error] {error_text}")
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
                        raise Exception(f"[VolcEngine Error] {error_text}")
                    
                    result = await response.json()
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"VolcEngine request failed: {e}")
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
            logger.error(f"Failed to parse VolcEngine response: {e}")
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
            model = self.supported_models[0] if self.supported_models else "doubao-1.5-pro"
        
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
                        raise Exception(f"VolcEngine API error: {response.status} - {error_text}")
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
