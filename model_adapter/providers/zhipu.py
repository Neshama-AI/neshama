"""
智谱 GLM (ZhipuAI) Provider - 2026 全面升级版
GLM-5, GLM-4.7 系列模型

文档: https://open.bigmodel.cn/dev/api
支持: GLM-5, GLM-4.7, Function Call, Vision
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class ZhipuProvider(BaseProvider):
    """智谱GLM提供商 - 2026 全面升级"""
    
    provider_name = "zhipu"
    provider_display_name = "智谱GLM"
    
    # 2026 最新模型列表
    supported_models = [
        # GLM-5 系列 (最新)
        "glm-5",                        # GLM-5 标准版
        # GLM-4.7 系列
        "glm-4.7",                      # GLM-4.7
        # GLM-4 系列
        "glm-4-plus",                   # GLM-4 Plus
        "glm-4-flash",                  # GLM-4 Flash (快速版)
        "glm-4-long",                   # GLM-4 长文本版
        "glm-4v",                       # GLM-4V 视觉版
        "glm-4v-plus",                  # GLM-4V Plus
        # GLM-3 系列 (保留兼容)
        "glm-3-turbo",                  # GLM-3 Turbo
        # Embedding
        "embedding-3",                   # Embedding v3
        "embedding-2",                  # Embedding v2
        # 其他
        "cogview-3",                    # 图像生成
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["glm-5", "glm-4.7", "glm-4-plus"],
        "standard": ["glm-4-flash", "glm-4"],
        "long": ["glm-4-long"],
        "vision": ["glm-4v", "glm-4v-plus"],
        "turbo": ["glm-3-turbo"],
        "embedding": ["embedding-3", "embedding-2"],
        "image": ["cogview-3"],
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
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
            "Content-Type": "application/json",
            "Accept": "application/json"
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
            "max_tokens": kwargs.get("max_tokens", self._get_default_max_tokens(model)),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": stream
        }
        
        # 智谱特有参数
        if kwargs.get("do_sample"):
            payload["do_sample"] = kwargs["do_sample"]
        
        if "top_k" in kwargs:
            payload["top_k"] = kwargs["top_k"]
        
        # 增量输出 (流式)
        if stream and "incremental" in kwargs:
            payload["incremental"] = kwargs["incremental"]
        
        # 工具调用
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]
        
        # 工具选择
        if "tool_choice" in kwargs:
            payload["tool_choice"] = kwargs["tool_choice"]
        
        # 请求 ID
        if "request_id" in kwargs:
            payload["request_id"] = kwargs["request_id"]
        
        # 对话 ID (用于多轮对话)
        if "conversation_id" in kwargs:
            payload["conversation_id"] = kwargs["conversation_id"]
        
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
            "glm-5": 256000,
            "glm-4.7": 256000,
            "glm-4-plus": 128000,
            "glm-4-flash": 32000,
            "glm-4-long": 128000,
            "glm-4v": 4096,
            "glm-4v-plus": 4096,
            "glm-3-turbo": 128000,
        }
        return defaults.get(model, 8192)
    
    async def _make_request(
        self,
        url: str,
        headers: Dict,
        payload: Dict,
        timeout: int
    ) -> Dict:
        """发送 HTTP 请求"""
        session = await self._get_session()
        
        try:
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
                        error_msg = error_json.get("error", {}).get("message", error_text)
                    except:
                        error_msg = error_text
                    raise Exception(f"[Zhipu Error] {error_msg}")
                
                result = await response.json()
                
                if "error" in result:
                    raise Exception(f"[Zhipu Error] {result['error'].get('message', 'Unknown')}")
                
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Zhipu request failed: {e}")
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
            logger.error(f"Failed to parse Zhipu response: {e}")
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
                
                # 增量模式格式
                if "choices" in chunk_data:
                    choice = chunk_data["choices"][0]
                    delta = choice.get("delta", {}).get("content", "")
                    finish_reason = choice.get("finish_reason")
                    
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
                else:
                    # 非增量模式
                    content = chunk_data.get("content", "")
                    if content:
                        yield StreamChunk(
                            content=content,
                            delta=content,
                            model=model,
                            provider=self.provider_name,
                            index=index,
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
            model = self.supported_models[0] if self.supported_models else "glm-4-plus"
        
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
                        raise Exception(f"Zhipu API error: {response.status} - {error_text}")
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
