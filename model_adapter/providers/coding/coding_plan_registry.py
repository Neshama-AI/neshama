"""
Coding Plan Registry - 2026 新增
编码套餐统一注册表

管理各厂商编码套餐的 API Key、模型、限制
支持:
  - 智谱 z.ai (GLM-4.7/GLM-5, 5小时窗口限制)
  - 阿里云多模型编码套餐
  - MiniMax 编码套餐
  - OpenAI Codex
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class RestrictionType(Enum):
    """限制类型"""
    INTERACTIVE_CODING_ONLY = "interactive_coding_only"  # 仅交互编码
    NO_BACKEND = "no_backend"  # 禁止后端调用
    NO_AUTOMATION = "no_automation"  # 禁止自动化脚本
    NO_CURL = "no_curl"  # 禁止 curl


class APIStyle(Enum):
    """API 风格"""
    OPENAI_CHAT = "openai_chat"  # OpenAI Chat 格式
    OPENAI_RESPONSES = "openai_responses"  # OpenAI Responses 格式
    ANTHROPIC = "anthropic"  # Anthropic 格式


@dataclass
class ModelCapability:
    """模型能力"""
    name: str
    supports_function_call: bool = True
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_reasoning: bool = False
    context_size: int = 128000


@dataclass
class CodingPlanRestrictions:
    """编码套餐限制"""
    restrictions: List[RestrictionType] = field(default_factory=list)
    max_session_duration_hours: int = 5  # 最大会话时长
    max_requests_per_session: int = 1000  # 每会话最大请求数
    requires_active_editing: bool = True  # 需要活跃编辑


@dataclass
class RateLimit:
    """速率限制"""
    rpm: int = 60  # 每分钟请求数
    rpd: int = 1000  # 每天请求数
    window_minutes: int = 60  # 窗口大小(分钟)


@dataclass
class CodingPlanModel:
    """编码套餐中的模型"""
    name: str
    capabilities: ModelCapability
    base_url: Optional[str] = None
    api_style: APIStyle = APIStyle.OPENAI_CHAT


@dataclass
class CodingPlan:
    """
    编码套餐配置
    
    每个 Coding Plan 记录:
      - provider_name: 提供商名称
      - api_key: API Key
      - base_url: API 端点
      - api_style: API 风格
      - models: 支持的模型列表
      - restrictions: 使用限制
      - rate_limits: 速率限制
    """
    plan_id: str
    plan_name: str
    provider_name: str
    api_key: str
    base_url: str
    api_style: APIStyle
    models: List[CodingPlanModel]
    restrictions: CodingPlanRestrictions
    rate_limits: RateLimit
    
    # 使用统计
    session_start: float = 0
    request_count: int = 0
    last_request_time: float = 0


class CodingPlanViolation(Exception):
    """编码套餐违规异常"""
    def __init__(self, restriction: RestrictionType, message: str):
        self.restriction = restriction
        self.message = message
        super().__init__(f"[Coding Plan Violation] {restriction.value}: {message}")


class CodingPlanRegistry:
    """
    编码套餐注册表
    
    管理所有 Coding Plan 的配置和使用限制
    """
    
    def __init__(self):
        self._plans: Dict[str, CodingPlan] = {}
        self._provider_instances: Dict[str, Any] = {}
        self._restriction_checkers: Dict[RestrictionType, Callable] = {}
        self._register_default_checkers()
    
    def _register_default_checkers(self):
        """注册默认限制检查器"""
        
        def check_interactive_only(ctx: Dict):
            """检查是否仅用于交互编码"""
            if not ctx.get("is_interactive", False):
                raise CodingPlanViolation(
                    RestrictionType.INTERACTIVE_CODING_ONLY,
                    "此套餐仅限交互式编码使用，禁止非交互场景"
                )
        
        def check_no_backend(ctx: Dict):
            """检查是否后端调用"""
            if ctx.get("is_backend", False):
                raise CodingPlanViolation(
                    RestrictionType.NO_BACKEND,
                    "此套餐禁止后端调用"
                )
        
        def check_no_automation(ctx: Dict):
            """检查是否自动化脚本"""
            if ctx.get("is_automated", False):
                raise CodingPlanViolation(
                    RestrictionType.NO_AUTOMATION,
                    "此套餐禁止自动化脚本"
                )
        
        def check_no_curl(ctx: Dict):
            """检查是否 curl 调用"""
            if ctx.get("is_curl", False):
                raise CodingPlanViolation(
                    RestrictionType.NO_CURL,
                    "此套餐禁止使用 curl 调用"
                )
        
        self._restriction_checkers[RestrictionType.INTERACTIVE_CODING_ONLY] = check_interactive_only
        self._restriction_checkers[RestrictionType.NO_BACKEND] = check_no_backend
        self._restriction_checkers[RestrictionType.NO_AUTOMATION] = check_no_automation
        self._restriction_checkers[RestrictionType.NO_CURL] = check_no_curl
    
    def register_plan(self, plan: CodingPlan):
        """注册编码套餐"""
        self._plans[plan.plan_id] = plan
        logger.info(f"[CodingPlanRegistry] Registered plan: {plan.plan_id} ({plan.plan_name})")
    
    def get_plan(self, plan_id: str) -> Optional[CodingPlan]:
        """获取编码套餐"""
        return self._plans.get(plan_id)
    
    def list_plans(self) -> List[CodingPlan]:
        """列出所有套餐"""
        return list(self._plans.values())
    
    def check_restrictions(self, plan_id: str, context: Dict[str, Any] = None):
        """
        检查使用限制
        
        Args:
            plan_id: 套餐 ID
            context: 使用上下文
            
        Raises:
            CodingPlanViolation: 如果违反限制
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return
        
        context = context or {}
        
        # 检查会话时长
        if plan.session_start > 0:
            elapsed_hours = (time.time() - plan.session_start) / 3600
            if elapsed_hours > plan.restrictions.max_session_duration_hours:
                raise CodingPlanViolation(
                    RestrictionType.INTERACTIVE_CODING_ONLY,
                    f"会话已超过 {plan.restrictions.max_session_duration_hours} 小时限制"
                )
        
        # 检查请求数
        if plan.request_count >= plan.restrictions.max_requests_per_session:
            raise CodingPlanViolation(
                RestrictionType.INTERACTIVE_CODING_ONLY,
                f"会话请求数已达上限 {plan.restrictions.max_requests_per_session}"
            )
        
        # 检查速率限制
        if plan.last_request_time > 0:
            elapsed = time.time() - plan.last_request_time
            if elapsed < (60 / plan.rate_limits.rpm):
                raise CodingPlanViolation(
                    RestrictionType.INTERACTIVE_CODING_ONLY,
                    "请求频率超限"
                )
        
        # 执行限制检查
        for restriction in plan.restrictions.restrictions:
            checker = self._restriction_checkers.get(restriction)
            if checker:
                checker(context)
    
    def record_request(self, plan_id: str):
        """记录请求"""
        plan = self._plans.get(plan_id)
        if plan:
            if plan.session_start == 0:
                plan.session_start = time.time()
            plan.request_count += 1
            plan.last_request_time = time.time()
    
    def create_default_plans(self):
        """创建默认编码套餐"""
        
        # 智谱 z.ai 套餐
        zhipu_plan = CodingPlan(
            plan_id="zhipu-za-5h",
            plan_name="智谱 z.ai 套餐 (5小时窗口)",
            provider_name="zhipu",
            api_key="",  # 用户配置
            base_url="https://open.bigmodel.cn/api/paas/v4",
            api_style=APIStyle.OPENAI_CHAT,
            models=[
                CodingPlanModel(
                    name="glm-5",
                    capabilities=ModelCapability(
                        name="glm-5",
                        supports_function_call=True,
                        supports_streaming=True,
                        context_size=256000
                    )
                ),
                CodingPlanModel(
                    name="glm-4.7",
                    capabilities=ModelCapability(
                        name="glm-4.7",
                        supports_function_call=True,
                        supports_streaming=True,
                        context_size=256000
                    )
                ),
            ],
            restrictions=CodingPlanRestrictions(
                restrictions=[RestrictionType.INTERACTIVE_CODING_ONLY],
                max_session_duration_hours=5,
                max_requests_per_session=1000
            ),
            rate_limits=RateLimit(rpm=60, rpd=1000)
        )
        self.register_plan(zhipu_plan)
        
        # 阿里云多模型编码套餐
        ali_plan = CodingPlan(
            plan_id="aliyun-coding-pack",
            plan_name="阿里云多模型编码套餐",
            provider_name="dashscope",
            api_key="",  # 用户配置
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_style=APIStyle.OPENAI_CHAT,
            models=[
                CodingPlanModel(
                    name="qwen3.5-plus",
                    capabilities=ModelCapability(
                        name="qwen3.5-plus",
                        supports_function_call=True,
                        supports_streaming=True,
                        context_size=131072
                    )
                ),
                CodingPlanModel(
                    name="glm-5",
                    capabilities=ModelCapability(
                        name="glm-5",
                        supports_function_call=True,
                        supports_streaming=True,
                        context_size=256000
                    )
                ),
                CodingPlanModel(
                    name="minimax-m2.5",
                    capabilities=ModelCapability(
                        name="minimax-m2.5",
                        supports_function_call=True,
                        supports_streaming=True,
                        context_size=100000
                    )
                ),
                CodingPlanModel(
                    name="kimi-k2.5",
                    capabilities=ModelCapability(
                        name="kimi-k2.5",
                        supports_function_call=True,
                        supports_streaming=True,
                        context_size=128000
                    )
                ),
            ],
            restrictions=CodingPlanRestrictions(
                restrictions=[RestrictionType.INTERACTIVE_CODING_ONLY],
                max_session_duration_hours=8,
                max_requests_per_session=2000
            ),
            rate_limits=RateLimit(rpm=120, rpd=5000)
        )
        self.register_plan(ali_plan)
        
        # MiniMax 编码套餐
        minimax_plan = CodingPlan(
            plan_id="minimax-coding-5h",
            plan_name="MiniMax 编码套餐 (5小时窗口)",
            provider_name="minimax",
            api_key="",  # 用户配置
            base_url="https://api.minimaxi.com/v1",
            api_style=APIStyle.OPENAI_CHAT,
            models=[
                CodingPlanModel(
                    name="minimax-m2.1",
                    capabilities=ModelCapability(
                        name="minimax-m2.1",
                        supports_function_call=True,
                        supports_streaming=True,
                        context_size=100000
                    )
                ),
            ],
            restrictions=CodingPlanRestrictions(
                restrictions=[RestrictionType.INTERACTIVE_CODING_ONLY],
                max_session_duration_hours=5,
                max_requests_per_session=1000
            ),
            rate_limits=RateLimit(rpm=60, rpd=1000)
        )
        self.register_plan(minimax_plan)
        
        # OpenAI Codex (特例：允许通用 API 访问)
        openai_plan = CodingPlan(
            plan_id="openai-codex",
            plan_name="OpenAI Codex",
            provider_name="openai",
            api_key="",  # 用户配置
            base_url="https://api.openai.com/v1",
            api_style=APIStyle.OPENAI_RESPONSES,
            models=[
                CodingPlanModel(
                    name="codex-mini-latest",
                    capabilities=ModelCapability(
                        name="codex-mini-latest",
                        supports_function_call=True,
                        supports_streaming=True,
                        context_size=64000
                    )
                ),
            ],
            restrictions=CodingPlanRestrictions(
                restrictions=[],  # Codex 允许通用 API 访问
                max_session_duration_hours=24,
                max_requests_per_session=10000
            ),
            rate_limits=RateLimit(rpm=500, rpd=10000)
        )
        self.register_plan(openai_plan)
        
        logger.info("[CodingPlanRegistry] Created default plans")


# 全局实例
_coding_plan_registry: Optional[CodingPlanRegistry] = None


def get_coding_plan_registry() -> CodingPlanRegistry:
    """获取编码套餐注册表"""
    global _coding_plan_registry
    if _coding_plan_registry is None:
        _coding_plan_registry = CodingPlanRegistry()
        _coding_plan_registry.create_default_plans()
    return _coding_plan_registry
