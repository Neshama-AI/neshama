"""
Cohere Provider - 2026 全面升级版
Command A, Command R+, Command R 系列模型

文档: https://docs.cohere.com/
认证: Bearer Token
特点: 免费 20 RPM
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class CohereProvider(BaseProvider):
    """Cohere 提供商 - 2026 全面升级"""
    
    provider_name = "cohere"
    provider_display_name = "Cohere"
    
    # 2026 最新模型列表
    supported_models = [
        # Command A 系列 (最新)
        "command-a",                     # Command A
        # Command R+ 系列
        "command-r-plus-08-2024",        # Command R+ 08-2024
        "command-r-plus",                # Command R+ 通用
        # Command R 系列
        "command-r-08-2024",             # Command R 08-2024
        "command-r",                      # Command R 通用
        # Command 系列 (旧版)
        "command",                        # Command
        "command-light",                  # Command Light
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["command-a", "command-r-plus-08-2024", "command-r-plus"],
        "standard": ["command-r-08-2024", "command-r"],
        "legacy": ["command", "command-light"],
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://api.cohere.ai/v1"
    
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
        # 转换消息格式
        formatted_messages = self._format_messages(messages)
        
        payload = {
            "model": model,
            "message": formatted_messages[-1].get("content") if formatted_messages else "",
            "chat_history": formatted_messages[:-1] if len(formatted_messages) > 1 else [],
            "stream": stream,
            "max_tokens": kwargs.get("max_tokens", self._get_default_max_tokens(model)),
            "temperature": kwargs.get("temperature", 0.7),
        }
        
        # 移除 None 值
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # 前置消息 (Preamble)
        if kwargs.get("preamble"):
            payload["preamble"] = kwargs["preamble"]
        
        # 搜索工具
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        
        # 文档 (用于 RAG)
        if kwargs.get("documents"):
            payload["documents"] = kwargs["documents"]
        
        # 导管 (Conduits)
        if kwargs.get("conduits"):
            payload["conduits"] = kwargs["conduits"]
        
        return payload
    
    def _format_messages(self, messages) -> List[Dict]:
        """格式化消息"""
        formatted = []
        for msg in messages:
            if isinstance(msg, Message):
                role = msg.role.value if hasattr(msg, 'role') else msg.get("role", "user")
                # Cohere 使用 "USER" 和 "CHATBOT" 角色
                if role == "assistant":
                    role = "CHATBOT"
                elif role == "system":
                    role = "SYSTEM"
                else:
                    role = "USER"
                formatted.append({
                    "role": role,
                    "content": msg.content if hasattr(msg, 'content') else msg.get("content", "")
                })
            elif isinstance(msg, dict):
                formatted.append(msg)
            elif isinstance(msg, str):
                formatted.append({"role": "USER", "content": msg})
        return formatted
    
    def _get_default_max_tokens(self, model: str) -> int:
        """获取模型默认最大 token 数"""
        defaults = {
            "command-a": 128000,
            "command-r-plus-08-2024": 128000,
            "command-r-plus": 128000,
            "command-r-08-2024": 128000,
            "command-r": 128000,
            "command": 4096,
            "command-light": 4096,
        }
        return defaults.get(model, 4096)
    
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
                    error_msg = error_json.get("message", error_text)
                except:
                    error_msg = error_text
                raise Exception(f"Cohere API error: {response.status} - {error_msg}")
            
            if stream:
                return response
            return await response.json()
    
    def _parse_response(self, response: Dict, model: str) -> ModelResponse:
        """解析响应"""
        try:
            content = response.get("text", "")
            
            # 解析 tool calls (如果有)
            tool_calls = None
            if "tool_calls" in response:
                tool_calls = response["tool_calls"]
            
            # 解析 citations (如果有)
            citations = None
            if "citations" in response:
                citations = response["citations"]
            
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
                finish_reason=response.get("finish_reason"),
                tool_calls=tool_calls
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
            
            try:
                chunk_data = json.loads(line)
                
                event_type = chunk_data.get("event_type")
                
                if event_type == "text-generation":
                    delta = chunk_data.get("text", "")
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
                        
                elif event_type == "stream-end":
                    finish_reason = chunk_data.get("finish_reason")
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
        """调用 Cohere 模型"""
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "command-a"
        
        messages = self._transform_messages(messages)
        url = f"{self.config.base_url.rstrip('/')}/chat"
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
                        raise Exception(f"Cohere API error: {response.status} - {error_text}")
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
