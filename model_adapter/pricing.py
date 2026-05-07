"""
Neshama Model Adapter - Pricing Module
模型定价信息统一管理 - 2026 全面升级

提供完整的 2026 年定价数据
支持成本估算、最低价查找、模型对比
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型"""
    CHAT = "chat"  # 对话
    CODING = "coding"  # 编程
    REASONING = "reasoning"  # 推理
    VISION = "vision"  # 视觉
    LONG_CONTEXT = "long_context"  # 长上下文
    EMBEDDING = "embedding"  # Embedding
    CHEAP = "cheap"  # 低价优先


@dataclass
class ModelPricing:
    """模型定价信息"""
    model_id: str
    provider: str
    
    # 输入价格 ($/M tokens)
    input_price_per_mtok: float = 0.0
    
    # 输出价格 ($/M tokens)
    output_price_per_mtok: float = 0.0
    
    # 缓存命中价格 ($/M tokens)
    cache_input_price: Optional[float] = None
    
    # 上下文窗口大小
    context_window: int = 128000
    
    # 是否免费
    is_free: bool = False
    
    # 免费额度
    free_rpm: Optional[int] = None  # 每分钟请求数
    free_rpd: Optional[int] = None  # 每天请求数
    free_tokens_per_day: Optional[int] = None  # 每天免费 token 数
    
    # 货币单位
    currency: str = "USD"
    
    # 适用任务类型
    task_types: List[TaskType] = field(default_factory=list)
    
    # 备注
    notes: str = ""
    
    def get_input_price(self) -> float:
        """获取输入价格 ($/M)"""
        if self.is_free:
            return 0.0
        return self.input_price_per_mtok
    
    def get_output_price(self) -> float:
        """获取输出价格 ($/M)"""
        if self.is_free:
            return 0.0
        return self.output_price_per_mtok
    
    def get_cache_price(self) -> float:
        """获取缓存价格 ($/M)"""
        if self.is_free:
            return 0.0
        return self.cache_input_price if self.cache_input_price else self.input_price_per_mtok * 0.1
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, use_cache: bool = False) -> float:
        """
        估算成本
        
        Args:
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            use_cache: 是否使用缓存
        
        Returns:
            成本 ($)
        """
        if self.is_free:
            return 0.0
        
        input_cost = (input_tokens / 1_000_000) * (
            self.get_cache_price() if use_cache else self.input_price_per_mtok
        )
        output_cost = (output_tokens / 1_000_000) * self.output_price_per_mtok
        
        return input_cost + output_cost


class PricingRegistry:
    """
    定价注册表
    
    统一管理所有模型的定价信息
    """
    
    def __init__(self):
        self._pricing: Dict[str, ModelPricing] = {}
        self._register_all_pricing()
    
    def _register_all_pricing(self):
        """注册所有模型定价"""
        
        # ==================== 国际模型 ====================
        
        # OpenAI
        self.register(ModelPricing(
            model_id="gpt-5",
            provider="openai",
            input_price_per_mtok=2.50,
            output_price_per_mtok=15.00,
            context_window=1100000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="gpt-5-mini",
            provider="openai",
            input_price_per_mtok=0.50,
            output_price_per_mtok=2.00,
            context_window=1100000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="gpt-5-nano",
            provider="openai",
            input_price_per_mtok=0.15,
            output_price_per_mtok=0.60,
            context_window=640000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="gpt-4.1",
            provider="openai",
            input_price_per_mtok=2.00,
            output_price_per_mtok=8.00,
            context_window=1000000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="gpt-4.1-mini",
            provider="openai",
            input_price_per_mtok=0.40,
            output_price_per_mtok=1.60,
            context_window=1000000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="gpt-4.1-nano",
            provider="openai",
            input_price_per_mtok=0.10,
            output_price_per_mtok=0.40,
            context_window=640000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="gpt-4o",
            provider="openai",
            input_price_per_mtok=2.50,
            output_price_per_mtok=10.00,
            context_window=128000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION]
        ))
        
        self.register(ModelPricing(
            model_id="gpt-4o-mini",
            provider="openai",
            input_price_per_mtok=0.15,
            output_price_per_mtok=0.60,
            context_window=128000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION]
        ))
        
        self.register(ModelPricing(
            model_id="o3",
            provider="openai",
            input_price_per_mtok=10.00,
            output_price_per_mtok=40.00,
            context_window=200000,
            task_types=[TaskType.REASONING, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="o4-mini",
            provider="openai",
            input_price_per_mtok=1.10,
            output_price_per_mtok=4.40,
            context_window=200000,
            task_types=[TaskType.REASONING, TaskType.CODING]
        ))
        
        # Anthropic
        self.register(ModelPricing(
            model_id="claude-opus-4-6",
            provider="anthropic",
            input_price_per_mtok=5.00,
            output_price_per_mtok=25.00,
            context_window=1000000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.REASONING, TaskType.VISION, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="claude-sonnet-4-6",
            provider="anthropic",
            input_price_per_mtok=3.00,
            output_price_per_mtok=15.00,
            context_window=1000000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.REASONING, TaskType.VISION, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="claude-haiku-4-5",
            provider="anthropic",
            input_price_per_mtok=1.00,
            output_price_per_mtok=5.00,
            context_window=200000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="claude-opus-4",
            provider="anthropic",
            input_price_per_mtok=4.00,
            output_price_per_mtok=20.00,
            context_window=200000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.REASONING, TaskType.VISION]
        ))
        
        self.register(ModelPricing(
            model_id="claude-sonnet-4",
            provider="anthropic",
            input_price_per_mtok=2.00,
            output_price_per_mtok=10.00,
            context_window=200000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.REASONING, TaskType.VISION]
        ))
        
        self.register(ModelPricing(
            model_id="claude-haiku-4",
            provider="anthropic",
            input_price_per_mtok=0.80,
            output_price_per_mtok=4.00,
            context_window=200000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        # Google Gemini
        self.register(ModelPricing(
            model_id="gemini-3.1-pro-preview",
            provider="gemini",
            input_price_per_mtok=1.25,
            output_price_per_mtok=10.00,
            context_window=1048576,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="gemini-2.5-pro",
            provider="gemini",
            input_price_per_mtok=1.25,
            output_price_per_mtok=10.00,
            context_window=1000000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="gemini-2.5-flash",
            provider="gemini",
            input_price_per_mtok=0.30,
            output_price_per_mtok=2.50,
            context_window=1000000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="gemini-2.5-flash-lite",
            provider="gemini",
            input_price_per_mtok=0.10,
            output_price_per_mtok=0.40,
            context_window=1000000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="gemini-2.0-flash",
            provider="gemini",
            input_price_per_mtok=0.15,
            output_price_per_mtok=0.60,
            context_window=32000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        # xAI Grok
        self.register(ModelPricing(
            model_id="grok-4",
            provider="xai",
            input_price_per_mtok=3.00,
            output_price_per_mtok=15.00,
            context_window=256000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION]
        ))
        
        self.register(ModelPricing(
            model_id="grok-3",
            provider="xai",
            input_price_per_mtok=2.00,
            output_price_per_mtok=10.00,
            context_window=131072,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="grok-4.1",
            provider="xai",
            input_price_per_mtok=3.00,
            output_price_per_mtok=15.00,
            context_window=256000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION]
        ))
        
        # DeepSeek V3 / R1 系列
        # V3定价：输入$0.27/M，输出$1.10/M (约GPT-4o的1/5)
        self.register(ModelPricing(
            model_id="deepseek-v3",
            provider="deepseek",
            input_price_per_mtok=0.27,
            output_price_per_mtok=1.10,
            cache_input_price=0.027,
            context_window=128000,
            task_types=[TaskType.CHAT, TaskType.CHEAP],
            notes="DeepSeek V3，高性价比中文模型"
        ))
        
        self.register(ModelPricing(
            model_id="deepseek-chat",  # deepseek-v3的别名
            provider="deepseek",
            input_price_per_mtok=0.27,
            output_price_per_mtok=1.10,
            cache_input_price=0.027,
            context_window=128000,
            task_types=[TaskType.CHAT, TaskType.CHEAP],
            notes="DeepSeek V3 别名"
        ))
        
        # DeepSeek R1 (推理模型)
        self.register(ModelPricing(
            model_id="deepseek-r1",
            provider="deepseek",
            input_price_per_mtok=0.27,
            output_price_per_mtok=1.10,
            cache_input_price=0.027,
            context_window=128000,
            task_types=[TaskType.REASONING, TaskType.CHEAP],
            notes="DeepSeek R1 推理模型，支持reasoning_content"
        ))
        
        self.register(ModelPricing(
            model_id="deepseek-reasoner",  # R1的API名称
            provider="deepseek",
            input_price_per_mtok=0.27,
            output_price_per_mtok=1.10,
            cache_input_price=0.027,
            context_window=128000,
            task_types=[TaskType.REASONING, TaskType.CHEAP],
            notes="DeepSeek R1 别名，支持reasoning_content"
        ))
        
        # DeepSeek V4 系列
        self.register(ModelPricing(
            model_id="deepseek-v4-pro",
            provider="deepseek",
            input_price_per_mtok=0.50,
            output_price_per_mtok=1.50,
            context_window=1000000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="deepseek-v4-flash",
            provider="deepseek",
            input_price_per_mtok=0.10,
            output_price_per_mtok=0.30,
            context_window=1000000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        # Mistral
        self.register(ModelPricing(
            model_id="mistral-large-latest",
            provider="mistral",
            input_price_per_mtok=2.00,
            output_price_per_mtok=6.00,
            context_window=128000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        # Groq (免费额度)
        self.register(ModelPricing(
            model_id="llama-4-scout-17b-16e-instruct",
            provider="groq",
            is_free=True,
            free_rpm=30,
            free_rpd=1440,
            context_window=10000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="llama-3.3-70b-versatile",
            provider="groq",
            is_free=True,
            free_rpm=30,
            free_rpd=1440,
            context_window=32768,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        # ==================== 国产模型 (元/M Token) ====================
        # 换算: ¥1 ≈ $0.14
        
        # 阿里云百炼
        self.register(ModelPricing(
            model_id="qwen3-max",
            provider="dashscope",
            input_price_per_mtok=0.33,  # ¥2.4/1M -> $0.33
            output_price_per_mtok=1.32,  # ¥9.6/1M -> $1.32
            context_window=131072,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="qwen3.5-plus",
            provider="dashscope",
            input_price_per_mtok=0.14,  # ¥1.0/1M -> $0.14
            output_price_per_mtok=0.55,  # ¥4.0/1M -> $0.55
            context_window=131072,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="qwen-turbo",
            provider="dashscope",
            input_price_per_mtok=0.05,  # ¥0.37/1M -> $0.05
            output_price_per_mtok=0.20,  # ¥1.47/1M -> $0.20
            context_window=131072,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="qwq-32b",
            provider="dashscope",
            input_price_per_mtok=0.05,  # ¥0.37/1M
            output_price_per_mtok=0.20,
            context_window=32768,
            task_types=[TaskType.REASONING]
        ))
        
        # 智谱 GLM
        self.register(ModelPricing(
            model_id="glm-5",
            provider="zhipu",
            input_price_per_mtok=0.50,
            output_price_per_mtok=1.50,
            context_window=256000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="glm-4.7",
            provider="zhipu",
            input_price_per_mtok=0.30,
            output_price_per_mtok=0.90,
            context_window=256000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="glm-4-plus",
            provider="zhipu",
            input_price_per_mtok=0.14,  # ¥1.0/1M
            output_price_per_mtok=0.55,  # ¥4.0/1M
            context_window=128000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="glm-4-flash",
            provider="zhipu",
            input_price_per_mtok=0.03,  # ¥0.2/1M
            output_price_per_mtok=0.10,  # ¥0.7/1M
            context_window=32000,
            task_types=[TaskType.CHAT]
        ))
        
        self.register(ModelPricing(
            model_id="glm-4-long",
            provider="zhipu",
            input_price_per_mtok=0.07,  # ¥0.5/1M
            output_price_per_mtok=0.14,  # ¥1.0/1M
            context_window=128000,
            task_types=[TaskType.LONG_CONTEXT]
        ))
        
        # MiniMax
        self.register(ModelPricing(
            model_id="minimax-m2.7",
            provider="minimax",
            input_price_per_mtok=0.50,
            output_price_per_mtok=1.50,
            context_window=100000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="minimax-m2.5",
            provider="minimax",
            input_price_per_mtok=0.28,
            output_price_per_mtok=0.42,
            context_window=100000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="minimax-m2.1",
            provider="minimax",
            input_price_per_mtok=0.10,
            output_price_per_mtok=0.30,
            context_window=100000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        # 火山引擎 (豆包)
        self.register(ModelPricing(
            model_id="doubao-1.5-pro",
            provider="volcengine",
            input_price_per_mtok=0.10,  # ¥0.8/1M -> $0.11
            output_price_per_mtok=0.20,  # ¥1.5/1M -> $0.21
            context_window=200000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.VISION]
        ))
        
        self.register(ModelPricing(
            model_id="doubao-1.5-lite",
            provider="volcengine",
            input_price_per_mtok=0.08,  # ¥0.6/1M -> $0.08
            output_price_per_mtok=0.17,  # ¥1.2/1M -> $0.17
            context_window=200000,
            task_types=[TaskType.CHAT]
        ))
        
        # 百度千帆
        self.register(ModelPricing(
            model_id="ernie-4.5",
            provider="qianfan",
            input_price_per_mtok=0.55,  # ¥4.0/1M
            output_price_per_mtok=0.55,  # ¥4.0/1M
            context_window=32000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="ernie-speed-128k",
            provider="qianfan",
            input_price_per_mtok=0.07,  # ¥0.5/1M
            output_price_per_mtok=0.14,  # ¥1.0/1M
            context_window=128000,
            task_types=[TaskType.CHAT]
        ))
        
        self.register(ModelPricing(
            model_id="ernie-lite-8k",
            provider="qianfan",
            input_price_per_mtok=0.03,  # ¥0.2/1M
            output_price_per_mtok=0.06,  # ¥0.4/1M
            context_window=8000,
            task_types=[TaskType.CHAT]
        ))
        
        # 腾讯混元
        self.register(ModelPricing(
            model_id="hunyuan-2.0-instruct",
            provider="hunyuan",
            input_price_per_mtok=0.44,  # ¥3.18/1M
            output_price_per_mtok=1.10,  # ¥7.95/1M
            context_window=32000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        self.register(ModelPricing(
            model_id="hunyuan-2.0-think",
            provider="hunyuan",
            input_price_per_mtok=0.55,  # ¥3.98/1M
            output_price_per_mtok=2.20,  # ¥15.9/1M
            context_window=32000,
            task_types=[TaskType.REASONING]
        ))
        
        self.register(ModelPricing(
            model_id="hunyuan-lite",
            provider="hunyuan",
            input_price_per_mtok=0.03,  # ¥0.2/1M
            output_price_per_mtok=0.06,  # ¥0.4/1M
            context_window=8000,
            task_types=[TaskType.CHAT]
        ))
        
        # Moonshot (Kimi)
        self.register(ModelPricing(
            model_id="kimi-k2.5",
            provider="moonshot",
            input_price_per_mtok=0.30,
            output_price_per_mtok=0.90,
            context_window=128000,
            task_types=[TaskType.CHAT, TaskType.CODING, TaskType.LONG_CONTEXT]
        ))
        
        self.register(ModelPricing(
            model_id="moonshot-v1-128k",
            provider="moonshot",
            input_price_per_mtok=0.14,  # ¥1.0/1M
            output_price_per_mtok=0.55,  # ¥4.0/1M
            context_window=128000,
            task_types=[TaskType.CHAT, TaskType.LONG_CONTEXT]
        ))
        
        # OpenRouter (聚合网关)
        self.register(ModelPricing(
            model_id="openrouter/*",
            provider="openrouter",
            input_price_per_mtok=0.50,  # 动态，根据实际路由
            output_price_per_mtok=1.50,
            is_free=True,
            free_rpd=50,  # 免费 50 次/天
            context_window=128000,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        # SiliconFlow (国内聚合)
        self.register(ModelPricing(
            model_id="siliconflow/*",
            provider="siliconflow",
            is_free=True,
            free_rpm=100,
            context_window=32768,
            task_types=[TaskType.CHAT, TaskType.CODING]
        ))
        
        logger.info(f"[PricingRegistry] Registered {len(self._pricing)} model prices")
    
    def register(self, pricing: ModelPricing):
        """注册模型定价"""
        self._pricing[pricing.model_id] = pricing
    
    def get_pricing(self, model_id: str) -> Optional[ModelPricing]:
        """获取模型定价"""
        return self._pricing.get(model_id)
    
    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """
        估算成本
        
        Args:
            model_id: 模型 ID
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
        
        Returns:
            成本 ($)
        """
        pricing = self._pricing.get(model_id)
        if not pricing:
            logger.warning(f"[PricingRegistry] Unknown model: {model_id}")
            return 0.0
        
        return pricing.estimate_cost(input_tokens, output_tokens)
    
    def find_cheapest(
        self,
        task_type: TaskType,
        min_context: int = 0,
        max_budget: Optional[float] = None
    ) -> List[Tuple[str, ModelPricing]]:
        """
        查找最低价模型
        
        Args:
            task_type: 任务类型
            min_context: 最小上下文大小
            max_budget: 最大预算 (可选)
        
        Returns:
            按价格排序的模型列表
        """
        candidates = []
        
        for model_id, pricing in self._pricing.items():
            if pricing.is_free:
                continue
            
            # 检查任务类型
            if task_type not in pricing.task_types and task_type != TaskType.CHEAP:
                continue
            
            # 检查上下文大小
            if pricing.context_window < min_context:
                continue
            
            candidates.append((model_id, pricing))
        
        # 按输入价格排序
        candidates.sort(key=lambda x: x[1].input_price_per_mtok)
        
        return candidates
    
    def compare_models(self, model_ids: List[str]) -> Dict[str, Any]:
        """
        对比多个模型
        
        Args:
            model_ids: 模型 ID 列表
        
        Returns:
            对比结果
        """
        results = []
        
        for model_id in model_ids:
            pricing = self._pricing.get(model_id)
            if pricing:
                results.append({
                    "model_id": model_id,
                    "provider": pricing.provider,
                    "input_price": pricing.get_input_price(),
                    "output_price": pricing.get_output_price(),
                    "context_window": pricing.context_window,
                    "is_free": pricing.is_free,
                    "task_types": [t.value for t in pricing.task_types],
                    "notes": pricing.notes
                })
        
        return {
            "models": results,
            "cheapest_input": min(results, key=lambda x: x["input_price"])["model_id"] if results else None,
            "cheapest_output": min(results, key=lambda x: x["output_price"])["model_id"] if results else None,
            "largest_context": max(results, key=lambda x: x["context_window"])["model_id"] if results else None,
        }
    
    def list_all_providers(self) -> List[str]:
        """列出所有提供商"""
        return list(set(p.provider for p in self._pricing.values()))
    
    def list_models_by_provider(self, provider: str) -> List[str]:
        """列出提供商的所有模型"""
        return [m for m, p in self._pricing.items() if p.provider == provider]


# 全局实例
_pricing_registry: Optional[PricingRegistry] = None


def get_pricing_registry() -> PricingRegistry:
    """获取定价注册表"""
    global _pricing_registry
    if _pricing_registry is None:
        _pricing_registry = PricingRegistry()
    return _pricing_registry
