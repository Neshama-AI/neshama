"""
HuggingFace Provider - 2026 全面升级版
海量开源模型

文档: https://huggingface.co/docs/inference-endpoints/
认证: Bearer Token
特点: 海量开源模型选择
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseProvider):
    """HuggingFace 提供商 - 2026 全面升级"""
    
    provider_name = "huggingface"
    provider_display_name = "HuggingFace"
    
    # 常用模型列表
    supported_models = [
        # LLaMA 系列
        "meta-llama/Llama-3.3-70B-Instruct",
        "meta-llama/Llama-3.1-8B-Instruct",
        "meta-llama/Llama-3-70B-Instruct",
        # Mistral
        "mistralai/Mistral-7B-Instruct-v0.3",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        # Gemma
        "google/gemma-2-27b-it",
        "google/gemma-2-9b-it",
        # Qwen
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        # DeepSeek
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-R1",
        # 其他
        "mistralai/Mistral-Nemo-Instruct-12B",
        "anthropics/claude-3.5-sonnet",
        "microsoft/Phi-3-mini-4k-instruct",
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "llama": ["meta-llama/Llama-3.3-70B-Instruct", "meta-llama/Llama-3.1-8B-Instruct", "meta-llama/Llama-3-70B-Instruct"],
        "mistral": ["mistralai/Mistral-7B-Instruct-v0.3", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
        "gemma": ["google/gemma-2-27b-it", "google/gemma-2-9b-it"],
        "qwen": ["Qwen/Qwen2.5-72B-Instruct", "Qwen/Qwen2.5-7B-Instruct"],
        "deepseek": ["deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1"],
        "phi": ["microsoft/Phi-3-mini-4k-instruct"],
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://api-inference.huggingface.co/v1"
    
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
        """构建请求载荷 (TGI 格式)"""
        # 转换消息格式
        formatted_messages = self._format_messages(messages)
        
        # HuggingFace 使用 inputs 格式
        last_message = formatted_messages[-1] if formatted_messages else {"role": "user", "content": ""}
        
        payload = {
            "inputs": last_message.get("content", ""),
            "parameters": {
                "max_new_tokens": kwargs.get("max_tokens", kwargs.get("max_new_tokens", 512)),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.95),
                "return_full_text": False,
            },
            "stream": stream,
        }
        
        # 添加 chat_history (如果有多条消息)
        if len(formatted_messages) > 1:
            payload["parameters"]["chat_history"] = formatted_messages[:-1]
        
        # 停止词
        if "stop" in kwargs:
            payload["parameters"]["stop"] = kwargs["stop"]
        
        # 生成参数
        if "top_k" in kwargs:
            payload["parameters"]["top_k"] = kwargs["top_k"]
        
        if "repetition_penalty" in kwargs:
            payload["parameters"]["repetition_penalty"] = kwargs["repetition_penalty"]
        
        return payload
    
    def _format_messages(self, messages) -> List[Dict]:
        """格式化消息"""
        formatted = []
        for msg in messages:
            if isinstance(msg, Message):
                role = msg.role.value if hasattr(msg, 'role') else msg.get("role", "user")
                formatted.append({
                    "role": role,
                    "content": msg.content if hasattr(msg, 'content') else msg.get("content", "")
                })
            elif isinstance(msg, dict):
                formatted.append(msg)
            elif isinstance(msg, str):
                formatted.append({"role": "user", "content": msg})
        return formatted
    
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
                    error_msg = error_json.get("error", str(error_text))
                except:
                    error_msg = error_text
                raise Exception(f"HuggingFace API error: {response.status} - {error_msg}")
            
            if stream:
                return response
            return await response.json()
    
    def _parse_response(self, response: Any, model: str) -> ModelResponse:
        """解析响应"""
        try:
            # TGI 格式响应
            if isinstance(response, list):
                content = response[0].get("generated_text", "") if response else ""
            elif isinstance(response, dict):
                content = response.get("generated_text", "")
            else:
                content = str(response)
            
            return ModelResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                raw_response=response,
                usage={}  # HuggingFace 不总是返回 usage
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
                
                if "error" in chunk_data:
                    raise Exception(f"API Error: {chunk_data['error']}")
                
                # TGI 流式响应格式
                if "token" in chunk_data:
                    delta = chunk_data["token"].get("text", "")
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
        """调用 HuggingFace 模型"""
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "meta-llama/Llama-3.1-8B-Instruct"
        
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
                        raise Exception(f"HuggingFace API error: {response.status} - {error_text}")
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
