"""
阿里云百炼 (DashScope) Provider - 2026 全面升级版
通义千问 Qwen3, Qwen2.5 系列模型

文档: https://help.aliyun.com/zh/dashscope/
支持: Qwen3-Max, Qwen3.5+, QWQ-32B, Vision
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class DashScopeProvider(BaseProvider):
    """阿里云百炼提供商 - 2026 全面升级"""
    
    provider_name = "dashscope"
    provider_display_name = "阿里云百炼 (通义千问)"
    
    # 2026 最新模型列表
    supported_models = [
        # Qwen3 系列 (最新)
        "qwen3-max",                    # Qwen3 超大规模模型
        "qwen3.5-plus",                # Qwen3.5 增强版
        "qwen3-turbo",                  # Qwen3 快速版
        # Qwen2.5 系列
        "qwen-plus",                    # Qwen2.5 Plus
        "qwen-max",                     # Qwen2.5 Max (保留兼容)
        "qwen-turbo",                   # Qwen2.5 Turbo
        # Qwen-VL 系列 (视觉)
        "qwen-vl-ocr",                  # Qwen-VL OCR 版本
        "qwen-vl-plus",                 # Qwen-VL Plus
        "qwen-vl-max",                  # Qwen-VL Max
        # Qwen-Long 系列 (长文本)
        "qwen-long",                    # 长文本模型
        # QWQ 系列 (思考模型)
        "qwq-32b",                      # QWQ 32B 思考模型
        # Qwen-Coder 系列 (编程)
        "qwen-coder-plus",              # 编程增强版
        "qwen-coder",                   # 编程版
        # Embedding & Rerank
        "text-embedding-v4",            # Embedding v4
        "text-embedding-v3",            # Embedding v3
        "gte-rerank",                   # 重排序模型
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["qwen3-max", "qwen3.5-plus", "qwen-max", "qwen-plus"],
        "fast": ["qwen3-turbo", "qwen-turbo"],
        "vision": ["qwen-vl-ocr", "qwen-vl-plus", "qwen-vl-max"],
        "long": ["qwen-long"],
        "thinking": ["qwq-32b"],
        "coding": ["qwen-coder-plus", "qwen-coder"],
        "embedding": ["text-embedding-v4", "text-embedding-v3"],
        "rerank": ["gte-rerank"],
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
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
        formatted_messages = self._format_messages(messages)
        
        parameters = {
            "result_format": "message",
            "max_tokens": kwargs.get("max_tokens", self._get_default_max_tokens(model)),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.8),
            "top_k": kwargs.get("top_k", 50),
            "repetition_penalty": kwargs.get("repetition_penalty", 1.1)
        }
        
        # 流式输出配置
        if stream:
            parameters["incremental_output"] = kwargs.get("incremental_output", True)
        
        # 思考过程配置 (qwq 模型)
        if model == "qwq-32b" or model.startswith("qwen3"):
            parameters["thinking_depth"] = kwargs.get("thinking_depth", 16)
        
        # Qwen 特有参数
        if kwargs.get("guided_json"):
            parameters["guided_json"] = kwargs["guided_json"]
        
        payload = {
            "model": model,
            "input": {
                "messages": formatted_messages
            },
            "parameters": parameters
        }
        
        # 处理函数调用
        if "tools" in kwargs and kwargs["tools"]:
            payload["parameters"]["tools"] = kwargs["tools"]
        
        return payload
    
    def _format_messages(self, messages) -> List[Dict]:
        """格式化消息"""
        formatted = []
        
        for msg in messages:
            if isinstance(msg, Message):
                formatted.append(msg.to_dict())
            elif isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                formatted_msg = {
                    "role": role,
                    "content": content
                }
                
                if "tool_calls" in msg:
                    formatted_msg["tool_calls"] = msg["tool_calls"]
                if "tool_call_id" in msg:
                    formatted_msg["tool_call_id"] = msg["tool_call_id"]
                if "name" in msg:
                    formatted_msg["name"] = msg["name"]
                
                formatted.append(formatted_msg)
            elif isinstance(msg, str):
                formatted.append({
                    "role": "user",
                    "content": msg
                })
        
        return formatted
    
    def _get_default_max_tokens(self, model: str) -> int:
        """获取模型默认最大 token 数"""
        defaults = {
            "qwen3-max": 131072,
            "qwen3.5-plus": 131072,
            "qwen3-turbo": 131072,
            "qwen-plus": 32768,
            "qwen-max": 8192,
            "qwen-turbo": 8192,
            "qwen-vl-ocr": 8192,
            "qwen-vl-plus": 8192,
            "qwen-vl-max": 8192,
            "qwen-long": 1048576,
            "qwq-32b": 32768,
            "qwen-coder-plus": 8192,
            "qwen-coder": 8192,
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
                        error_code = error_json.get("error", {}).get("code", response.status)
                        error_msg = error_json.get("error", {}).get("message", error_text)
                    except:
                        error_code = response.status
                        error_msg = error_text
                    
                    raise self._create_error(error_code, error_msg, response.status)
                
                result = await response.json()
                
                if "error" in result:
                    raise self._create_error(
                        result["error"].get("code", "API_ERROR"),
                        result["error"].get("message", "Unknown error"),
                        response.status
                    )
                
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"DashScope request failed: {e}")
            raise
    
    def _create_error(self, code: Any, message: str, status: int) -> Exception:
        """创建统一错误"""
        error_messages = {
            401: "API密钥无效或已过期",
            403: "没有权限访问该模型",
            429: "请求频率超限，请降低调用频率",
            500: "服务器内部错误",
            503: "服务暂时不可用",
            "InvalidParameter": "参数无效",
            "UnsupportedModel": "不支持的模型",
            "TokenExpired": "Token已过期",
        }
        
        description = error_messages.get(code, error_messages.get(status, message))
        return Exception(f"[DashScope Error {code}] {description}")
    
    def _parse_response(self, response: Dict, model: str) -> ModelResponse:
        """解析响应"""
        try:
            output = response.get("output", {})
            choices = output.get("choices", [])
            
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
            
            # 处理思考过程 (qwq 模型)
            reasoning_content = None
            if model == "qwq-32b" and "reasoning_content" in message:
                reasoning_content = message.get("reasoning_content")
            
            usage = self._parse_usage(response.get("usage", {}))
            
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
            logger.error(f"Failed to parse DashScope response: {e}")
            return ModelResponse(
                content="",
                model=model,
                provider=self.provider_name,
                raw_response=response,
                error=f"Parse error: {str(e)}"
            )
    
    def _parse_usage(self, usage: Dict) -> Dict[str, int]:
        """解析 usage"""
        return {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }
    
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
                yield StreamChunk(
                    content="",
                    delta="",
                    model=model,
                    provider=self.provider_name,
                    index=index,
                    finish_reason="stop",
                    raw_chunk=None
                )
                break
            
            try:
                chunk_data = json.loads(line)
                
                output = chunk_data.get("output", {})
                delta = output.get("delta", "")
                finish_reason = output.get("finish_reason")
                
                output_index = chunk_data.get("output", {}).get("output_index", index)
                
                tool_calls = None
                if "tool_calls" in output:
                    tool_calls = output["tool_calls"]
                
                yield StreamChunk(
                    content=delta,
                    delta=delta,
                    model=model,
                    provider=self.provider_name,
                    index=output_index,
                    finish_reason=finish_reason,
                    raw_chunk=chunk_data
                )
                
                if finish_reason:
                    break
                    
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
        """
        对话接口
        """
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "qwen-plus"
        
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
                        raise Exception(f"DashScope API error: {response.status} - {error_text}")
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
