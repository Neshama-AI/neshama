"""
Google Gemini Provider - 2026 全面升级版
Gemini 3.1, 2.5, 2.0 系列模型

文档: https://ai.google.dev/docs
支持: Thinking, Grounding (搜索增强), Vision
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List, Union
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """Google Gemini 提供商 - 2026 全面升级"""
    
    provider_name = "gemini"
    provider_display_name = "Google Gemini"
    
    # 2026 最新模型列表
    supported_models = [
        # Gemini 3.1 系列
        "gemini-3.1-pro-preview",
        # Gemini 2.5 系列
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        # Gemini 2.0 系列
        "gemini-2.0-flash",
        "gemini-2.0-flash-thinking",
        # Gemini 1.5 系列 (保留兼容)
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "premium": ["gemini-3.1-pro-preview", "gemini-2.5-pro"],
        "standard": ["gemini-2.5-flash", "gemini-2.0-flash"],
        "fast": ["gemini-2.5-flash-lite"],
        "thinking": ["gemini-2.0-flash-thinking", "gemini-3.1-pro-preview"],
        "vision": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    }
    
    # API 端点格式
    # Google AI Studio 格式
    GENERATIVE_LANGUAGE_API = "https://generativelanguage.googleapis.com/v1beta/models"
    # OpenAI 兼容格式
    OPENAI_COMPATIBLE_API = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    
    def __init__(
        self,
        config: ProviderConfig,
        use_openai_compatible: bool = False
    ):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        self.use_openai_compatible = use_openai_compatible
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _get_api_url(self, model: str, endpoint: str = "generateContent") -> str:
        """
        获取 API URL
        
        Args:
            model: 模型名称
            endpoint: 端点名称 (generateContent, etc.)
        """
        if self.use_openai_compatible:
            return f"{self.OPENAI_COMPATIBLE_API}?key={self.config.api_key}"
        else:
            return f"{self.GENERATIVE_LANGUAGE_API}/{model}:{endpoint}?key={self.config.api_key}"
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Content-Type": "application/json"
        }
        headers.update(self.config.extra_headers)
        return headers
    
    def _transform_messages_to_gemini(self, messages: List[Union[Message, Dict]]) -> tuple:
        """
        转换消息格式为 Gemini 格式
        """
        contents = []
        system_instruction = ""
        
        for msg in messages:
            role = msg.role.value if hasattr(msg, 'role') else msg.get("role", "user")
            content = msg.content if hasattr(msg, 'content') else msg.get("content", "")
            
            if role == "system":
                system_instruction += content + "\n"
            elif role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "assistant":
                contents.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })
        
        return system_instruction.strip() or None, contents
    
    def _build_payload(
        self,
        messages: list,
        model: str,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        构建请求载荷
        
        支持参数:
            - thinking_budget: 思考 token 预算
            - grounding: 搜索增强配置
        """
        system_instruction, contents = self._transform_messages_to_gemini(messages)
        
        generation_config = {
            "maxOutputTokens": kwargs.get("max_tokens", self._get_default_max_tokens(model)),
            "temperature": kwargs.get("temperature", 0.7),
            "topP": kwargs.get("top_p", 0.95),
            "topK": kwargs.get("top_k", 40)
        }
        
        # 停止序列
        if "stop_sequences" in kwargs:
            generation_config["stopSequences"] = kwargs["stop_sequences"]
        
        # 候选数量
        if "candidate_count" in kwargs:
            generation_config["candidateCount"] = kwargs["candidate_count"]
        
        # 思考配置 (Gemini 2.0+)
        if kwargs.get("thinking_budget") and model.startswith("gemini-2"):
            generation_config["thinkingConfig"] = {
                "thinkingBudget": kwargs["thinking_budget"]
            }
        
        payload = {
            "contents": contents,
            "generationConfig": generation_config
        }
        
        # 系统指令
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        # 安全设置
        if "safety_settings" in kwargs:
            payload["safetySettings"] = kwargs["safety_settings"]
        
        # 工具配置 (函数调用)
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]
        
        # ========== 2026 新特性 ==========
        
        # 搜索增强 (Grounding)
        if kwargs.get("grounding"):
            grounding_config = {
                "grounding": {
                    "grounding_sources": kwargs["grounding_sources"] if "grounding_sources" in kwargs else []
                }
            }
            if "search_ engine" in kwargs:
                grounding_config["grounding"]["search_engine"] = kwargs["search_engine"]
            payload.update(grounding_config)
        
        # 思维链 (Chain of Thought)
        if kwargs.get("include_thoughts"):
            payload["generationConfig"]["include_thoughts"] = True
        
        return payload
    
    def _build_openai_compatible_payload(
        self,
        messages: list,
        model: str,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """构建 OpenAI 兼容格式的载荷"""
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            role = msg.role.value if hasattr(msg, 'role') else msg.get("role", "user")
            content = msg.content if hasattr(msg, 'content') else msg.get("content", "")
            formatted_messages.append({"role": role, "content": content})
        
        payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": stream,
            "max_tokens": kwargs.get("max_tokens", self._get_default_max_tokens(model)),
            "temperature": kwargs.get("temperature", 0.7),
        }
        
        # 思考预算
        if kwargs.get("thinking_budget"):
            payload["thinkingBudget"] = kwargs["thinking_budget"]
        
        # 工具
        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]
        
        return payload
    
    def _get_default_max_tokens(self, model: str) -> int:
        """获取模型默认最大 token 数"""
        defaults = {
            "gemini-3.1-pro-preview": 1048576,  # 1M
            "gemini-2.5-pro": 1048576,  # 1M
            "gemini-2.5-flash": 1048576,  # 1M
            "gemini-2.5-flash-lite": 1048576,  # 1M
            "gemini-2.0-flash": 32000,
            "gemini-2.0-flash-thinking": 32000,
            "gemini-1.5-pro": 128000,
            "gemini-1.5-flash": 128000,
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
                raise Exception(f"Gemini API error: {response.status} - {error_msg}")
            
            result = await response.json()
            
            # 检查是否有错误
            if "error" in result:
                raise Exception(f"Gemini API error: {result['error']}")
            
            return result
    
    def _parse_response(self, response: Dict, model: str) -> ModelResponse:
        """解析响应"""
        try:
            candidates = response.get("candidates", [])
            
            if not candidates:
                # 检查 prompt feedback
                prompt_feedback = response.get("promptFeedback", {})
                if prompt_feedback:
                    block_reason = prompt_feedback.get("blockReason", "Unknown")
                    return ModelResponse(
                        content="",
                        model=model,
                        provider=self.provider_name,
                        error=f"Prompt blocked: {block_reason}"
                    )
                return ModelResponse(
                    content="",
                    model=model,
                    provider=self.provider_name,
                    error="No candidates in response"
                )
            
            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            
            text = ""
            for part in parts:
                if "text" in part:
                    text += part["text"]
            
            # 解析 usage
            usage_metadata = response.get("usageMetadata", {})
            usage = {
                "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                "total_tokens": usage_metadata.get("totalTokenCount", 0)
            }
            
            finish_reason = candidate.get("finishReason", "")
            
            # 解析 grounding metadata (如果有)
            grounding_metadata = None
            if "groundingMetadata" in candidate:
                grounding_metadata = candidate["groundingMetadata"]
            
            return ModelResponse(
                content=text,
                model=model,
                provider=self.provider_name,
                raw_response=response,
                usage=usage,
                finish_reason=finish_reason
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
                
                # 检查错误
                if "error" in chunk_data:
                    yield StreamChunk(
                        content="",
                        delta="",
                        model=model,
                        provider=self.provider_name,
                        index=index,
                        raw_chunk={"error": chunk_data["error"]}
                    )
                    continue
                
                candidates = chunk_data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    
                    for part in parts:
                        if "text" in part:
                            delta = part["text"]
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
        """
        调用 Gemini 模型
        
        Args:
            messages: 消息列表
            model: 模型名称
            stream: 是否流式
            **kwargs: 其他参数
        
        Returns:
            ModelResponse 或 AsyncIterator[StreamChunk]
        """
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "gemini-2.5-pro"
        
        messages = self._transform_messages(messages)
        
        # 选择 API 格式
        if self.use_openai_compatible:
            url = self._get_api_url(model)
            headers = {"Content-Type": "application/json"}
            payload = self._build_openai_compatible_payload(messages, model, stream, **kwargs)
        else:
            url = self._get_api_url(model)
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
                        raise Exception(f"Gemini API error: {response.status} - {error_text}")
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
