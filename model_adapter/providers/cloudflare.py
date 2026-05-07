"""
Cloudflare Workers AI Provider - 2026 全面升级版
Cloudflare 边缘 AI 推理

文档: https://developers.cloudflare.com/workers-ai/
认证: Bearer Token (Cloudflare API Token)
特点: 免费 10,000 Neurons/天, 边缘部署
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class CloudflareProvider(BaseProvider):
    """Cloudflare Workers AI 提供商 - 2026 全面升级"""
    
    provider_name = "cloudflare"
    provider_display_name = "Cloudflare Workers AI"
    
    # 常用模型列表
    supported_models = [
        # LLaMA 系列
        "@cf/meta/llama-3.3-70b-instruct-f",
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/meta/llama-3-8b-instruct-hf-lora",
        # Mistral
        "@cf/mistralai/mistral-7b-instruct-v0.1",
        "@cf/mistralai/mistral-7b-instruct-v0.2",
        # Gemma
        "@cf/google/gemma-7b-instruct",
        "@cf/google/gemma-2-7b-instruct",
        # DeepSeek
        "@cf/deepseek-ai/deepseek-v3",
        # 其他
        "@cf/qwen/qwen1.5-14b-chat",
        "@cf/tiiuae/falcon-7b-instruct",
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "llama": ["@cf/meta/llama-3.3-70b-instruct-f", "@cf/meta/llama-3.1-8b-instruct", "@cf/meta/llama-3-8b-instruct-hf-lora"],
        "mistral": ["@cf/mistralai/mistral-7b-instruct-v0.1", "@cf/mistralai/mistral-7b-instruct-v0.2"],
        "gemma": ["@cf/google/gemma-7b-instruct", "@cf/google/gemma-2-7b-instruct"],
        "deepseek": ["@cf/deepseek-ai/deepseek-v3"],
        "qwen": ["@cf/qwen/qwen1.5-14b-chat"],
        "falcon": ["@cf/tiiuae/falcon-7b-instruct"],
    }
    
    def __init__(
        self,
        config: ProviderConfig,
        account_id: str = ""
    ):
        super().__init__(config)
        self.account_id = account_id
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _get_base_url(self) -> str:
        """获取基础 URL"""
        if self.config.base_url:
            return self.config.base_url
        if self.account_id:
            return f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/v1"
        raise ValueError("account_id or base_url must be provided")
    
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
            "messages": formatted_messages,
            "stream": stream,
        }
        
        # max_tokens
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        
        # temperature
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        
        # top_p
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        
        # 停止词
        if "stop" in kwargs:
            payload["stop"] = kwargs["stop"]
        
        # LLM 特定参数
        if "top_k" in kwargs:
            payload["top_k"] = kwargs["top_k"]
        
        return payload
    
    def _format_messages(self, messages) -> List[Dict]:
        """格式化消息"""
        formatted = []
        for msg in messages:
            if isinstance(msg, Message):
                role = msg.role.value if hasattr(msg, 'role') else msg.get("role", "user")
                # Cloudflare 使用 system/user/assistant
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
                raise Exception(f"Cloudflare API error: {response.status} - {error_msg}")
            
            if stream:
                return response
            return await response.json()
    
    def _parse_response(self, response: Dict, model: str) -> ModelResponse:
        """解析响应"""
        try:
            content = response.get("result", {}).get("response", "")
            
            usage = {
                "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": response.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": response.get("usage", {}).get("prompt_tokens", 0) + response.get("usage", {}).get("completion_tokens", 0)
            }
            
            # 解析 Neurons (Cloudflare 特有)
            if "ms" in response:
                usage["latency_ms"] = response["ms"]
            
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
                
                if "error" in chunk_data:
                    raise Exception(f"API Error: {chunk_data['error']}")
                
                # Cloudflare 流式响应格式
                delta = chunk_data.get("response", "")
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
        """调用 Cloudflare Workers AI"""
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "@cf/meta/llama-3.1-8b-instruct"
        
        messages = self._transform_messages(messages)
        base_url = self._get_base_url()
        url = f"{base_url.rstrip('/')}/chat/completions"
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
                        raise Exception(f"Cloudflare API error: {response.status} - {error_text}")
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
