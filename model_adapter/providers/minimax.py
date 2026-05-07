"""
MiniMax Provider - 2026 全面升级版
MiniMax M2, M1 系列模型

文档: https://www.minimaxi.com/document
支持: M2.7, M2.5, M2.1, Function Call
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class MiniMaxProvider(BaseProvider):
    """MiniMax 提供商 - 2026 全面升级"""
    
    provider_name = "minimax"
    provider_display_name = "MiniMax"
    
    # 2026 最新模型列表
    supported_models = [
        # MiniMax M 系列 (最新)
        "minimax-m2.7",                 # M2.7 超大规模
        "minimax-m2.5",                 # M2.5 增强版
        "minimax-m2.1",                 # M2.1 标准版
        # MiniMax 文本系列
        "MiniMax-Text-01",              # 文本模型 01
        "MiniMax-Text-02",              # 文本模型 02
        # MiniMax Embedding
        "MiniMax-Embedding-01",         # Embedding 模型
        # 角色扮演
        "RolePlay-01",                  # 角色扮演
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["minimax-m2.7", "minimax-m2.5", "MiniMax-Text-02"],
        "standard": ["minimax-m2.1", "MiniMax-Text-01"],
        "embedding": ["MiniMax-Embedding-01"],
        "roleplay": ["RolePlay-01"],
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://api.minimaxi.com/v1"
    
    def __init__(self, config: ProviderConfig, group_id: str = ""):
        super().__init__(config)
        self.group_id = group_id
        self._session: Optional[aiohttp.ClientSession] = None
        if not self.config.base_url:
            self.config.base_url = self.DEFAULT_BASE_URL
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout, connect=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.group_id:
            headers["MiniMax-Group-Id"] = self.group_id
        
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
            "top_p": kwargs.get("top_p", 0.95)
        }
        
        # Token 采样控制
        if "min_tokens" in kwargs:
            payload["min_tokens"] = kwargs["min_tokens"]
        
        # 屏蔽词
        if "屏蔽词列表" in kwargs:
            payload["屏蔽词列表"] = kwargs["屏蔽词列表"]
        
        # 角色设定
        if "role_meta" in kwargs:
            payload["role_meta"] = kwargs["role_meta"]
        
        # 状态信息
        if "status_info" in kwargs:
            payload["status_info"] = kwargs["status_info"]
        
        # 参考信息
        if "reference_info" in kwargs:
            payload["reference_info"] = kwargs["reference_info"]
        
        # 函数调用
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]
        
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
            "minimax-m2.7": 100000,
            "minimax-m2.5": 100000,
            "minimax-m2.1": 100000,
            "MiniMax-Text-01": 32768,
            "MiniMax-Text-02": 32768,
            "RolePlay-01": 16384,
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
                        try:
                            error_json = json.loads(error_text)
                            error_msg = error_json.get("base_resp", {}).get("status_msg", error_text)
                        except:
                            error_msg = error_text
                        raise Exception(f"[MiniMax Error] {error_msg}")
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
                        try:
                            error_json = json.loads(error_text)
                            error_msg = error_json.get("base_resp", {}).get("status_msg", error_text)
                        except:
                            error_msg = error_text
                        raise Exception(f"[MiniMax Error] {error_msg}")
                    
                    result = await response.json()
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"MiniMax request failed: {e}")
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
            logger.error(f"Failed to parse MiniMax response: {e}")
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
            model = self.supported_models[0] if self.supported_models else "minimax-m2.5"
        
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
                        raise Exception(f"MiniMax API error: {response.status} - {error_text}")
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
