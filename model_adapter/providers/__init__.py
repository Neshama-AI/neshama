"""
Neshama Model Adapter - Providers
模型提供商模块 - 2026 全面升级

包含所有 21 个 Provider 的导入
"""

from typing import Optional, List
from .base import (
    BaseProvider,
    ProviderConfig,
    Message,
    MessageRole,
    ModelResponse,
    StreamChunk
)

# ==================== 核心 Providers ====================

# OpenAI & 兼容
from .openai import OpenAIProvider

# Anthropic Claude
from .anthropic import AnthropicProvider

# Google Gemini
from .gemini import GeminiProvider

# ==================== 国产 Providers ====================

# 阿里云百炼 (通义千问)
from .dashscope import DashScopeProvider

# 智谱 GLM
from .zhipu import ZhipuProvider

# MiniMax
from .minimax import MiniMaxProvider

# 火山引擎 (豆包)
from .volcengine import VolcEngineProvider

# 百度千帆 (文心一言)
from .qianfan import QianFanProvider

# 讯飞星火
from .xinghuo import XingHuoProvider

# 腾讯混元
from .hunyuan import HunyuanProvider

# Moonshot/Kimi
from .moonshot import MoonshotProvider

# ==================== 新增国际 Providers ====================

# DeepSeek
from .deepseek import DeepSeekProvider

# xAI (Grok)
from .xai import XAIProvider

# Groq
from .groq import GroqProvider

# Mistral
from .mistral import MistralProvider

# Cohere
from .cohere import CohereProvider

# HuggingFace
from .huggingface import HuggingFaceProvider

# NVIDIA NIM
from .nvidia import NVIDIAProvider

# ==================== 聚合网关 ====================

# OpenRouter
from .openrouter import OpenRouterProvider

# SiliconFlow (国内聚合)
from .siliconflow import SiliconFlowProvider

# Cloudflare Workers AI
from .cloudflare import CloudflareProvider

__all__ = [
    # Base
    "BaseProvider",
    "ProviderConfig",
    "Message",
    "MessageRole",
    "ModelResponse",
    "StreamChunk",
    
    # Core Providers
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    
    # Chinese Providers
    "DashScopeProvider",
    "ZhipuProvider",
    "MiniMaxProvider",
    "VolcEngineProvider",
    "QianFanProvider",
    "XingHuoProvider",
    "HunyuanProvider",
    "MoonshotProvider",
    
    # International Providers
    "DeepSeekProvider",
    "XAIProvider",
    "GroqProvider",
    "MistralProvider",
    "CohereProvider",
    "HuggingFaceProvider",
    "NVIDIAProvider",
    
    # Aggregation Gateways
    "OpenRouterProvider",
    "SiliconFlowProvider",
    "CloudflareProvider",
]

# Provider 映射表
PROVIDER_MAP = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "dashscope": DashScopeProvider,
    "zhipu": ZhipuProvider,
    "minimax": MiniMaxProvider,
    "volcengine": VolcEngineProvider,
    "qianfan": QianFanProvider,
    "xinghuo": XingHuoProvider,
    "hunyuan": HunyuanProvider,
    "moonshot": MoonshotProvider,
    "deepseek": DeepSeekProvider,
    "xai": XAIProvider,
    "groq": GroqProvider,
    "mistral": MistralProvider,
    "cohere": CohereProvider,
    "huggingface": HuggingFaceProvider,
    "nvidia": NVIDIAProvider,
    "openrouter": OpenRouterProvider,
    "siliconflow": SiliconFlowProvider,
    "cloudflare": CloudflareProvider,
}


def get_provider(provider_name: str) -> Optional[type]:
    """获取 Provider 类"""
    return PROVIDER_MAP.get(provider_name)


def list_providers() -> List[str]:
    """列出所有 Provider"""
    return list(PROVIDER_MAP.keys())
