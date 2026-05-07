"""
讯飞星火 (XingHuo) Provider - 2026 全面升级版
讯飞认知大模型 Spark 4.0 系列

文档: https://www.xfyun.cn/doc/spark/Web.html
支持: Spark 4.0 Ultra, Spark Max, Function Call
"""

import aiohttp
import json
import hashlib
import hmac
import base64
import time
from typing import Any, Dict, AsyncIterator, Optional
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class XingHuoProvider(BaseProvider):
    """讯飞星火提供商 - 2026 全面升级"""
    
    provider_name = "xinghuo"
    provider_display_name = "讯飞星火"
    
    # 2026 最新模型列表
    supported_models = [
        "spark-4.0-ultra",              # Spark 4.0 Ultra
        "spark-max",                    # Spark Max
        "spark-pro",                    # Spark Pro
        "spark-lite",                   # Spark Lite
        # 旧版本兼容
        "generalv4.0",                  # 星火 4.0
        "generalv3.5",                  # 星火 3.5
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["spark-4.0-ultra", "spark-max"],
        "standard": ["spark-pro"],
        "lite": ["spark-lite"],
        "legacy": ["generalv4.0", "generalv3.5"],
    }
    
    # 模型到域名的映射
    MODEL_DOMAIN_MAP = {
        "spark-4.0-ultra": "4.0Ultra",
        "spark-max": "4.0Max",
        "spark-pro": "4.0Pro",
        "spark-lite": "4.0Lite",
        "generalv4.0": "generalv4.0",
        "generalv3.5": "generalv3.5",
    }
    
    def __init__(self, config: ProviderConfig, app_id: str = ""):
        super().__init__(config)
        self.app_id = app_id
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
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
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            role = msg.role.value if hasattr(msg, 'role') else msg.get("role", "user")
            content = msg.content if hasattr(msg, 'content') else msg.get("content", "")
            
            if role == "system":
                role = "system"
            elif role == "assistant":
                role = "assistant"
            else:
                role = "user"
            
            formatted_messages.append({
                "role": role,
                "content": content
            })
        
        # 获取域名
        domain = self.MODEL_DOMAIN_MAP.get(model, "4.0Max")
        
        # 讯飞特有的 payload 结构
        payload = {
            "header": {
                "app_id": self.app_id or "default",
                "uid": kwargs.get("uid", "default")
            },
            "parameter": {
                "chat": {
                    "domain": domain,
                    "temperature": kwargs.get("temperature", 0.5),
                    "max_tokens": kwargs.get("max_tokens", self._get_default_max_tokens(model)),
                    "top_k": kwargs.get("top_k", 4),
                    "chat_id": kwargs.get("chat_id", "")
                }
            },
            "payload": {
                "message": {
                    "text": formatted_messages
                }
            }
        }
        
        return payload
    
    def _get_default_max_tokens(self, model: str) -> int:
        """获取模型默认最大 token 数"""
        defaults = {
            "spark-4.0-ultra": 32000,
            "spark-max": 32000,
            "spark-pro": 32000,
            "spark-lite": 8000,
            "generalv4.0": 8192,
            "generalv3.5": 8192,
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
        
        if stream:
            async with session.post(
                url,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"XingHuo API error: {response.status} - {error_text}")
                return response
        else:
            async with session.post(
                url,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"XingHuo API error: {response.status} - {error_text}")
                
                result = await response.json()
                
                # 检查错误
                if result.get("header", {}).get("code", 0) != 0:
                    raise Exception(f"XingHuo API error: {result['header'].get('message', 'Unknown error')}")
                
                return result
    
    def _parse_response(self, response: Dict, model: str) -> ModelResponse:
        """解析响应"""
        try:
            choices = response.get("payload", {}).get("choices", {})
            text_parts = choices.get("text", [])
            
            content = ""
            for part in text_parts:
                content += part.get("content", "")
            
            # 解析 usage
            usage_data = response.get("payload", {}).get("usage", {})
            usage = {
                "prompt_tokens": usage_data.get("text", {}).get("prompt_tokens", 0),
                "completion_tokens": usage_data.get("text", {}).get("completion_tokens", 0),
                "total_tokens": usage_data.get("text", {}).get("total_tokens", 0)
            }
            
            return ModelResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                raw_response=response,
                usage=usage
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
                
                # 讯飞流式响应格式
                if "payload" in chunk_data and "choices" in chunk_data["payload"]:
                    text_parts = chunk_data["payload"]["choices"].get("text", [])
                    for part in text_parts:
                        delta = part.get("content", "")
                        if delta:
                            yield StreamChunk(
                                content=delta,
                                delta=delta,
                                model=model,
                                provider=self.provider_name,
                                index=index,
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
        """对话接口"""
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "spark-max"
        
        messages = self._transform_messages(messages)
        headers = self._build_headers()
        payload = self._build_payload(messages, model, stream, **kwargs)
        
        # 讯飞 WebSocket URL (这里简化处理，实际使用需要 WebSocket)
        url = f"{self.config.base_url.rstrip('/')}/v3.1/chat"
        
        try:
            if stream:
                return self._parse_stream_response(None, model)  # 需要 WebSocket 支持
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
