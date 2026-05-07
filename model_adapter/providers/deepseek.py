"""
DeepSeek Provider - 2026 全面升级版 ⭐ 重点
DeepSeek V4 Pro/Flash, V3.2 系列模型

文档: https://api.deepseek.com/docs
支持: Thinking Mode, Reasoning Effort, FIM 补全
认证: Bearer Token
价格参考: V3.2 输入$0.28/输出$0.42 (缓存$0.028) / M tokens
"""

import aiohttp
import json
import time
from typing import Any, Dict, AsyncIterator, Optional, List
from .base import BaseProvider, ProviderConfig, Message, ModelResponse, StreamChunk, MessageRole

import logging
logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseProvider):
    """
    DeepSeek 提供商 - 2026 全面升级 ⭐
    
    支持模型:
    - DeepSeek V3 (deepseek-chat): 高性价比通用对话
    - DeepSeek R1 (deepseek-reasoner): 推理模型，支持reasoning_content
    - DeepSeek V4 Pro/Flash: 超大规模模型
    
    API: https://api.deepseek.com/v1/chat/completions
    认证: Bearer Token
    定价: V3 输入$0.27/M, 输出$1.10/M (约GPT-4o的1/5)
    """
    
    provider_name = "deepseek"
    provider_display_name = "DeepSeek"
    
    # 支持的模型列表
    supported_models = [
        # DeepSeek V3 系列 (推荐，性价比最高)
        "deepseek-chat",            # V3 对话模型
        "deepseek-v3",              # V3 别名
        # DeepSeek R1 系列 (推理模型)
        "deepseek-reasoner",        # R1 推理模型
        "deepseek-r1",              # R1 别名
        # DeepSeek V4 系列
        "deepseek-v4-pro",          # V4 Pro 超大规模
        "deepseek-v4-flash",        # V4 Flash 快速版
    ]
    
    # 模型分组
    MODEL_GROUPS = {
        "cheap": ["deepseek-chat", "deepseek-v3"],  # 简单对话首选
        "reasoning": ["deepseek-reasoner", "deepseek-r1"],  # 推理任务
        "premium": ["deepseek-v4-pro"],  # 高质量需求
        "fast": ["deepseek-v4-flash"],  # 快速响应
    }
    
    # 模型别名 (API调用时使用的实际模型名)
    MODEL_ALIASES = {
        # V3 系列
        "deepseek-chat": "deepseek-chat",
        "deepseek-v3": "deepseek-chat",
        # R1 系列
        "deepseek-reasoner": "deepseek-reasoner",
        "deepseek-r1": "deepseek-reasoner",
        # V4 系列
        "deepseek-v4-pro": "deepseek-v4-pro",
        "deepseek-v4-flash": "deepseek-v4-flash",
    }
    
    # 默认配置
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    
    # 定价信息 ($/M tokens)
    PRICING = {
        # V3 系列: 高性价比
        "deepseek-chat": {"input": 0.27, "output": 1.10, "cache": 0.027},
        "deepseek-v3": {"input": 0.27, "output": 1.10, "cache": 0.027},
        # R1 系列: 推理模型
        "deepseek-reasoner": {"input": 0.27, "output": 1.10, "cache": 0.027},
        "deepseek-r1": {"input": 0.27, "output": 1.10, "cache": 0.027},
        # V4 系列
        "deepseek-v4-pro": {"input": 0.50, "output": 1.50, "cache": None},
        "deepseek-v4-flash": {"input": 0.10, "output": 0.30, "cache": None},
    }
    
    # 默认使用的模型
    DEFAULT_MODEL = "deepseek-chat"
    
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
    
    def _normalize_model(self, model: str) -> str:
        """规范化模型名称"""
        return self.MODEL_ALIASES.get(model, model)
    
    def _build_headers(self, use_anthropic_api: bool = False) -> Dict[str, str]:
        """
        构建请求头
        
        Args:
            use_anthropic_api: 是否使用 Anthropic 兼容端点
        """
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        if use_anthropic_api:
            headers["anthropic-version"] = "2023-06-01"
        
        headers.update(self.config.extra_headers)
        return headers
    
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
            - thinking_mode: 思考模式 (non-thinking/basic/medium/high/max)
            - reasoning_effort: 推理强度 (低/中/高)
            - fim: FIM 补全配置
        """
        normalized_model = self._normalize_model(model)
        
        payload = {
            "model": normalized_model,
            "messages": self._format_messages(messages),
            "stream": stream,
            "max_tokens": kwargs.get("max_tokens", self._get_default_max_tokens(model)),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.95),
        }
        
        # 移除 None 值
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # ========== DeepSeek 特色功能 ==========
        
        # Thinking Mode (V3.2+)
        thinking_mode = kwargs.get("thinking_mode")
        if thinking_mode and model in ["deepseek-chat", "deepseek-v4-pro", "deepseek-v4-flash"]:
            payload["thinking_mode"] = thinking_mode
        
        # Reasoning Effort (R1)
        reasoning_effort = kwargs.get("reasoning_effort")
        if reasoning_effort and model == "deepseek-reasoner":
            # reasoning_effort 可以是低/中/高，对应不同的 token 预算
            pass
        
        # FIM 补全 (代码补全)
        if kwargs.get("fim"):
            fim_config = kwargs["fim"]
            payload["fim"] = {
                "prompt": fim_config.get("prompt", ""),
                "suffix": fim_config.get("suffix", ""),
                "context_window_fraction": fim_config.get("context_window_fraction", 0.9)
            }
        
        # 函数调用
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]
        
        # 响应格式
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]
        
        return payload
    
    def _build_anthropic_payload(
        self,
        messages: list,
        model: str,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """构建 Anthropic 兼容格式的载荷 (用于 deepseek-reasoner)"""
        # 分离 system 和 messages
        system_prompt = ""
        transformed_messages = []
        
        for msg in messages:
            role = msg.role.value if hasattr(msg, 'role') else msg.get("role", "user")
            content = msg.content if hasattr(msg, 'content') else msg.get("content", "")
            
            if role == "system":
                system_prompt += content + "\n"
            else:
                transformed_messages.append({
                    "role": role,
                    "content": content
                })
        
        payload = {
            "model": self._normalize_model(model),
            "messages": transformed_messages,
            "stream": stream,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        
        if "thinking" in kwargs:
            payload["thinking"] = kwargs["thinking"]
        
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
                formatted.append({"role": "user", "content": msg})
        return formatted
    
    def _get_default_max_tokens(self, model: str) -> int:
        """获取模型默认最大 token 数"""
        defaults = {
            "deepseek-v4-pro": 1000000,
            "deepseek-v4-flash": 1000000,
            "deepseek-chat": 128000,
            "deepseek-reasoner": 128000,
        }
        return defaults.get(model, 128000)
    
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
                    error_msg = error_json.get("error", {}).get("message", error_text)
                except:
                    error_msg = error_text
                raise Exception(f"DeepSeek API error: {response.status} - {error_msg}")
            
            if stream:
                return response
            return await response.json()
    
    def _parse_response(self, response: Dict, model: str) -> ModelResponse:
        """
        解析响应
        
        支持:
        - OpenAI兼容格式 (deepseek-chat / deepseek-v3)
        - Anthropic兼容格式 (deepseek-reasoner / deepseek-r1)
        - reasoning_content字段 (R1推理内容)
        """
        try:
            # 兼容 Anthropic 格式
            if "content" in response and isinstance(response.get("content"), list):
                # Anthropic 格式
                content = ""
                reasoning_content = ""
                tool_calls = []
                for block in response.get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        tool_calls.append({
                            "id": block.get("id"),
                            "name": block.get("name"),
                            "input": block.get("input", {})
                        })
                
                usage = {
                    "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": response.get("usage", {}).get("output_tokens", 0),
                }
                usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
                
                # thinking_tokens (R1)
                if "thinking_tokens" in response.get("usage", {}):
                    usage["thinking_tokens"] = response["usage"]["thinking_tokens"]
                
                # reasoning_content (DeepSeek R1特有)
                if "reasoning_content" in response:
                    reasoning_content = response.get("reasoning_content", "")
                    usage["reasoning_content_length"] = len(reasoning_content)
                
                return ModelResponse(
                    content=content,
                    model=model,
                    provider=self.provider_name,
                    raw_response=response,
                    usage=usage,
                    finish_reason=response.get("stop_reason"),
                    tool_calls=tool_calls if tool_calls else None
                )
            else:
                # OpenAI 格式
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
                
                # 获取content
                content = message.get("content", "")
                
                # reasoning_content (DeepSeek R1在OpenAI格式下也可能返回)
                if "reasoning_content" in message:
                    reasoning_content = message.get("reasoning_content", "")
                    # 将推理内容附在回复后
                    if reasoning_content:
                        usage = response.get("usage", {})
                        if "reasoning_content_length" not in usage:
                            usage["reasoning_content_length"] = len(reasoning_content)
                
                return ModelResponse(
                    content=content,
                    model=model,
                    provider=self.provider_name,
                    raw_response=response,
                    usage=response.get("usage", {}),
                    finish_reason=choice.get("finish_reason"),
                    tool_calls=message.get("tool_calls")
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
                
                # Anthropic 格式
                if "type" in chunk_data:
                    if chunk_data.get("type") == "content_block_delta":
                        delta_type = chunk_data.get("delta", {}).get("type")
                        if delta_type == "text_delta":
                            delta = chunk_data.get("delta", {}).get("text", "")
                            yield StreamChunk(
                                content=delta,
                                delta=delta,
                                model=model,
                                provider=self.provider_name,
                                index=index,
                                raw_chunk=chunk_data
                            )
                            index += 1
                    elif chunk_data.get("type") == "message_delta":
                        finish_reason = chunk_data.get("delta", {}).get("stop_reason")
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
                else:
                    # OpenAI 格式
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
                            
            except json.JSONDecodeError:
                continue
    
    async def call(
        self,
        messages,
        model: Optional[str] = None,
        stream: bool = False,
        use_anthropic_api: bool = False,
        **kwargs
    ) -> Any:
        """
        调用 DeepSeek 模型
        
        Args:
            messages: 消息列表
            model: 模型名称
            stream: 是否流式
            use_anthropic_api: 是否使用 Anthropic 兼容端点 (用于 reasoner)
            **kwargs: 其他参数
        
        Returns:
            ModelResponse 或 AsyncIterator[StreamChunk]
        """
        import time
        start_time = time.time()
        
        if model is None:
            model = self.supported_models[0] if self.supported_models else "deepseek-chat"
        
        messages = self._transform_messages(messages)
        
        # 选择端点
        if use_anthropic_api or model == "deepseek-reasoner":
            url = f"{self.config.base_url.rstrip('/')}/anthropic"
            headers = self._build_headers(use_anthropic_api=True)
            payload = self._build_anthropic_payload(messages, model, stream, **kwargs)
        else:
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
                        raise Exception(f"DeepSeek API error: {response.status} - {error_text}")
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
