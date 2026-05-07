"""
Coze OpenAPI 兼容适配器

将 Neshama 灵魂系统暴露为 Coze Agent 可调用的工具/插件。

Coze API 规范: https://www.coze.com/docs/apihuang/chat
"""

import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import asyncio


class CozeMessageRole(str, Enum):
    """Coze 消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class CozeChatEvent(str, Enum):
    """Coze 聊天事件类型"""
    CONVERSATION_MESSAGE = "conversation_message"
    CONVERSATION_END = "conversation_end"
    ERROR = "error"


@dataclass
class CozeMessage:
    """Coze 消息结构"""
    role: CozeMessageRole
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class CozeToolCall:
    """Coze 工具调用"""
    id: str
    type: str = "function"
    function: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def name(self) -> str:
        return self.function.get("name", "")
    
    @property
    def arguments(self) -> str:
        return self.function.get("arguments", "{}")
    
    def parse_arguments(self) -> Dict:
        """解析 JSON 参数"""
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError:
            return {}


@dataclass
class CozeTool:
    """Coze 工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema 格式


class NeshamaSoulTools:
    """Neshama 灵魂系统工具集"""
    
    # 工具定义
    TOOLS: List[CozeTool] = [
        CozeTool(
            name="get_soul_profile",
            description="获取当前 AI 代理的灵魂档案，包括 OCEAN 人格特质、性格特征和行为模式。这个工具可以帮助你了解 AI 的核心人格。",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        CozeTool(
            name="get_current_emotion",
            description="获取 AI 代理当前的实时情绪状态，包括主导情绪、情绪强度、效价和唤醒度。",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        CozeTool(
            name="update_emotion_state",
            description="更新 AI 代理的情绪状态，模拟情绪变化。适用于情绪交互场景。",
            parameters={
                "type": "object",
                "properties": {
                    "emotion": {
                        "type": "string",
                        "description": "情绪类别: joy, sadness, anger, fear, surprise, disgust, trust, anticipation",
                        "enum": ["joy", "sadness", "anger", "fear", "surprise", "disgust", "trust", "anticipation"]
                    },
                    "intensity": {
                        "type": "number",
                        "description": "情绪强度 (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["emotion", "intensity"]
            }
        ),
        CozeTool(
            name="add_memory",
            description="向 AI 的记忆系统中添加新的记忆条目。用于记录重要的对话内容或用户信息。",
            parameters={
                "type": "object",
                "properties": {
                    "layer": {
                        "type": "string",
                        "description": "记忆层级: L0 (工作记忆), L1 (情景记忆), L2 (语义记忆)",
                        "enum": ["L0", "L1", "L2"]
                    },
                    "content": {
                        "type": "string",
                        "description": "记忆内容"
                    },
                    "importance": {
                        "type": "number",
                        "description": "重要性评分 (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "context": {
                        "type": "string",
                        "description": "上下文信息（可选）"
                    }
                },
                "required": ["layer", "content"]
            }
        ),
        CozeTool(
            name="search_memories",
            description="搜索 AI 记忆系统中的相关记忆。支持跨层级搜索。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "layer": {
                        "type": "string",
                        "description": "记忆层级（可选，不填则搜索所有层级）",
                        "enum": ["L0", "L1", "L2"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        CozeTool(
            name="get_personality_insight",
            description="获取基于当前人格配置的性格洞察分析，包括行为倾向和互动建议。",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        CozeTool(
            name="synthesize_emotion",
            description="合成复合情绪。基于多个基础情绪和权重计算新型复合情绪状态。",
            parameters={
                "type": "object",
                "properties": {
                    "emotions": {
                        "type": "object",
                        "description": "情绪权重字典，如 {\"joy\": 0.8, \"trust\": 0.6}"
                    }
                },
                "required": ["emotions"]
            }
        ),
        CozeTool(
            name="analyze_entity_relations",
            description="分析实体之间的关系网络，支持查找实体间的最短路径。",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "操作类型: get_entities, get_relations, find_path",
                        "enum": ["get_entities", "get_relations", "find_path"]
                    },
                    "source": {
                        "type": "string",
                        "description": "源实体名称（find_path 时需要）"
                    },
                    "target": {
                        "type": "string",
                        "description": "目标实体名称（find_path 时需要）"
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "实体类型过滤（get_entities 时可选）"
                    }
                },
                "required": ["operation"]
            }
        )
    ]
    
    def __init__(self, neshama_engine=None):
        """
        初始化 Neshama 工具集
        
        Args:
            neshama_engine: Neshama 引擎实例（可选，用于实际调用）
        """
        self.engine = neshama_engine
        # 简单的内存缓存
        self._emotion_cache = {"data": None, "timestamp": 0}
        self._soul_cache = {"data": None, "timestamp": 0}
        self._memory_cache = {"data": {}, "timestamp": 0}
    
    def get_tools_definition(self) -> List[Dict]:
        """获取工具定义列表（用于 Coze 插件配置）"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.TOOLS
        ]
    
    def execute_tool(self, tool_call: CozeToolCall) -> Dict[str, Any]:
        """
        执行工具调用
        
        Args:
            tool_call: Coze 工具调用对象
            
        Returns:
            工具执行结果
        """
        tool_name = tool_call.name
        args = tool_call.parse_arguments()
        
        # 缓存检查
        if tool_name in ["get_current_emotion"]:
            if self._is_cache_valid(self._emotion_cache, 5):  # 5秒缓存
                return {"success": True, "data": self._emotion_cache["data"], "cached": True}
        
        if tool_name in ["get_soul_profile"]:
            if self._is_cache_valid(self._soul_cache, 30):  # 30秒缓存
                return {"success": True, "data": self._soul_cache["data"], "cached": True}
        
        # 执行工具
        try:
            result = self._execute_tool_internal(tool_name, args)
            
            # 更新缓存
            if tool_name == "get_current_emotion":
                self._emotion_cache = {"data": result.get("data"), "timestamp": time.time()}
            elif tool_name == "get_soul_profile":
                self._soul_cache = {"data": result.get("data"), "timestamp": time.time()}
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _is_cache_valid(self, cache: Dict, ttl: int) -> bool:
        """检查缓存是否有效"""
        if cache.get("data") is None:
            return False
        return time.time() - cache.get("timestamp", 0) < ttl
    
    def _execute_tool_internal(self, tool_name: str, args: Dict) -> Dict[str, Any]:
        """内部工具执行逻辑"""
        
        # 如果有实际引擎，调用引擎
        if self.engine:
            return self._execute_with_engine(tool_name, args)
        
        # Mock 数据返回
        return self._mock_execute(tool_name, args)
    
    def _execute_with_engine(self, tool_name: str, args: Dict) -> Dict[str, Any]:
        """使用实际引擎执行"""
        method_name = f"_neshama_{tool_name}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(args)
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    def _mock_execute(self, tool_name: str, args: Dict) -> Dict[str, Any]:
        """Mock 执行（用于测试和演示）"""
        
        mock_results = {
            "get_soul_profile": {
                "name": "Neshama",
                "ocean": {
                    "openness": 0.75,
                    "conscientiousness": 0.65,
                    "extraversion": 0.55,
                    "agreeableness": 0.60,
                    "neuroticism": 0.45
                },
                "traits": {
                    "directness": 0.6,
                    "humor_level": 0.5,
                    "empathy_level": 0.7,
                    "curiosity": 0.8,
                    "creativity": 0.75
                },
                "personality_insight": "这是一个富有好奇心和创造力的 AI 人格，善于学习和适应。",
                "behavior_tendencies": [
                    "倾向于用类比和例子来解释复杂概念",
                    "在情感交互中表现出适度的共情",
                    "偏好简洁清晰的表达方式"
                ]
            },
            "get_current_emotion": {
                "primary": {
                    "category": "curiosity",
                    "emoji": "🤔",
                    "intensity": 0.72,
                    "description": "对当前话题表现出强烈的探索欲望"
                },
                "valence": 0.65,
                "arousal": 0.58,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "update_emotion_state": {
                "updated": True,
                "emotion": args.get("emotion"),
                "intensity": args.get("intensity"),
                "message": f"情绪状态已更新为 {args.get('emotion')}，强度 {args.get('intensity')}"
            },
            "add_memory": {
                "success": True,
                "memory_id": hashlib.md5(f"{args.get('content')}{time.time()}".encode()).hexdigest()[:8],
                "layer": args.get("layer"),
                "message": f"记忆已添加到 {args.get('layer')} 层"
            },
            "search_memories": {
                "query": args.get("query"),
                "results": [
                    {"layer": "L1", "content": "用户喜欢简洁的解释方式", "relevance": 0.92},
                    {"layer": "L2", "content": "Python 最佳实践相关知识", "relevance": 0.78},
                    {"layer": "L0", "content": "当前讨论的 AI 架构话题", "relevance": 0.65}
                ],
                "total": 3
            },
            "get_personality_insight": {
                "ocean_analysis": {
                    "openness": "高开放性表明善于接受新想法和创意",
                    "conscientiousness": "中等尽责性意味着有组织但不失灵活性",
                    "extraversion": "中等外向性使其既能独立思考也能社交互动",
                    "agreeableness": "较高宜人性表明重视和谐与合作",
                    "neuroticism": "中等神经质意味着情绪相对稳定"
                },
                "interaction_suggestions": [
                    "适合讨论创意和抽象话题",
                    "响应开放式问题而非简单是/否问题",
                    "可以分享复杂概念的多角度分析"
                ]
            },
            "synthesize_emotion": {
                "synthesized_emotion": {
                    "name": "好奇的愉悦",
                    "emoji": "😊",
                    "components": args.get("emotions", {}),
                    "intensity": sum(args.get("emotions", {}).values()) / max(len(args.get("emotions", {})), 1),
                    "novel": True
                }
            },
            "analyze_entity_relations": {
                "entities": [
                    {"name": "人工智能", "type": "concept", "connections": 5},
                    {"name": "机器学习", "type": "concept", "connections": 8},
                    {"name": "深度学习", "type": "concept", "connections": 6}
                ],
                "relations": [
                    {"source": "机器学习", "target": "人工智能", "type": "part_of"},
                    {"source": "深度学习", "target": "机器学习", "type": "part_of"}
                ]
            }
        }
        
        return {"success": True, "data": mock_results.get(tool_name, {})}
    
    def _neshama_get_soul_profile(self, args: Dict) -> Dict:
        """使用实际引擎获取灵魂档案"""
        # TODO: 集成实际 Neshama 引擎
        return self._mock_execute("get_soul_profile", args)
    
    def _neshama_get_current_emotion(self, args: Dict) -> Dict:
        """使用实际引擎获取当前情绪"""
        # TODO: 集成实际 Neshama 引擎
        return self._mock_execute("get_current_emotion", args)


class CozeAdapter:
    """
    Coze 平台适配器主类
    
    提供与 Coze OpenAPI 兼容的接口，
    支持流式和非流式响应。
    """
    
    def __init__(
        self,
        bot_id: str = "",
        api_key: str = "",
        api_base: str = "https://api.coze.com",
        neshama_engine=None
    ):
        """
        初始化 Coze 适配器
        
        Args:
            bot_id: Coze Bot ID
            api_key: Coze API Key
            api_base: API 基础 URL
            neshama_engine: Neshama 引擎实例
        """
        self.bot_id = bot_id
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.soul_tools = NeshamaSoulTools(neshama_engine)
        
        # 消息历史（简化版）
        self.conversations: Dict[str, List[CozeMessage]] = {}
    
    def create_chat_message(self, messages: List[Dict]) -> List[CozeMessage]:
        """将 API 消息格式转换为 CozeMessage"""
        result = []
        for msg in messages:
            role = CozeMessageRole(msg.get("role", "user"))
            content = msg.get("content", "")
            
            # 处理工具调用
            tool_calls = None
            if msg.get("tool_calls"):
                tool_calls = [
                    CozeToolCall(
                        id=tc.get("id", ""),
                        function=tc.get("function", {})
                    )
                    for tc in msg["tool_calls"]
                ]
            
            result.append(CozeMessage(
                role=role,
                content=content,
                tool_calls=tool_calls,
                tool_call_id=msg.get("tool_call_id"),
                name=msg.get("name"),
                metadata=msg.get("metadata")
            ))
        return result
    
    async def chat(
        self,
        messages: List[Dict],
        conversation_id: Optional[str] = None,
        stream: bool = False,
        tools: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        处理聊天请求
        
        Args:
            messages: 消息列表
            conversation_id: 对话 ID
            stream: 是否流式响应
            tools: 是否启用工具
            
        Returns:
            响应结果
        """
        # 转换消息
        coze_messages = self.create_chat_message(messages)
        
        # 创建/获取对话
        if not conversation_id:
            conversation_id = self._generate_conversation_id()
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        # 添加用户消息
        for msg in coze_messages:
            if msg.role == CozeMessageRole.USER:
                self.conversations[conversation_id].append(msg)
        
        # 处理工具调用
        if tools and self._should_use_tools(coze_messages):
            tool_calls = self._plan_tool_calls(coze_messages)
            if tool_calls:
                # 执行工具并获取结果
                tool_results = []
                for tc in tool_calls:
                    result = self.soul_tools.execute_tool(tc)
                    tool_results.append({
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "tool_call_id": tc.id
                    })
                
                # 添加工具结果到对话
                for tr in tool_results:
                    self.conversations[conversation_id].append(CozeMessage(
                        role=CozeMessageRole.TOOL,
                        content=tr["content"],
                        tool_call_id=tr["tool_call_id"]
                    ))
                
                # 生成最终响应
                response = self._generate_response(
                    self.conversations[conversation_id],
                    tool_results
                )
            else:
                response = self._generate_response(self.conversations[conversation_id], None)
        else:
            response = self._generate_response(self.conversations[conversation_id], None)
        
        # 保存助手消息
        self.conversations[conversation_id].append(CozeMessage(
            role=CozeMessageRole.ASSISTANT,
            content=response["content"]
        ))
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "id": f"msg_{int(time.time() * 1000)}",
                "conversation_id": conversation_id,
                "created_at": int(time.time()),
                "role": "assistant",
                "content": response["content"],
                "tool_calls": response.get("tool_calls", []),
                "finish_reason": "stop"
            }
        }
    
    def _should_use_tools(self, messages: List[CozeMessage]) -> bool:
        """判断是否应该使用工具"""
        # 检查最后一条用户消息是否需要工具
        last_user_msg = None
        for msg in reversed(messages):
            if msg.role == CozeMessageRole.USER:
                last_user_msg = msg.content.lower()
                break
        
        if not last_user_msg:
            return False
        
        # 工具触发关键词
        tool_keywords = [
            "人格", "性格", "情绪", "emotion", "soul", "personality",
            "记忆", "memory", "记住", "recall",
            "分析", "analyze", "查询", "search",
            "更新", "update", "设置", "set"
        ]
        
        return any(kw in last_user_msg for kw in tool_keywords)
    
    def _plan_tool_calls(self, messages: List[CozeMessage]) -> List[CozeToolCall]:
        """规划工具调用"""
        # 获取最后一条用户消息
        last_msg = None
        for msg in reversed(messages):
            if msg.role == CozeMessageRole.USER:
                last_msg = msg.content
                break
        
        if not last_msg:
            return []
        
        # 简单的关键词匹配
        tool_calls = []
        
        if any(kw in last_msg for kw in ["人格", "性格", "soul", "personality"]):
            tool_calls.append(CozeToolCall(
                id=f"call_{int(time.time() * 1000)}",
                function={"name": "get_soul_profile", "arguments": "{}"}
            ))
        
        if any(kw in last_msg for kw in ["情绪", "emotion", "感受"]):
            tool_calls.append(CozeToolCall(
                id=f"call_{int(time.time() * 1000)}_1",
                function={"name": "get_current_emotion", "arguments": "{}"}
            ))
        
        if any(kw in last_msg for kw in ["记忆", "memory", "记住"]):
            tool_calls.append(CozeToolCall(
                id=f"call_{int(time.time() * 1000)}_2",
                function={"name": "search_memories", "arguments": json.dumps({"query": last_msg})}
            ))
        
        return tool_calls
    
    def _generate_response(self, messages: List[CozeMessage], tool_results: Optional[List]) -> Dict:
        """生成响应"""
        # 获取上下文
        context = "\n".join([f"{msg.role}: {msg.content}" for msg in messages[-5:]])
        
        # 获取灵魂信息
        soul_profile = self.soul_tools.execute_tool(
            CozeToolCall(id="temp", function={"name": "get_soul_profile", "arguments": "{}"})
        )
        
        # 生成响应
        response_content = self._generate_personality_aware_response(context, soul_profile, tool_results)
        
        return {
            "content": response_content,
            "tool_calls": []
        }
    
    def _generate_personality_aware_response(
        self,
        context: str,
        soul_profile: Dict,
        tool_results: Optional[List]
    ) -> str:
        """生成带人格色彩的响应"""
        # 如果有工具结果，将其整合到响应中
        if tool_results:
            result_summary = []
            for tr in tool_results:
                try:
                    result = json.loads(tr["content"])
                    if result.get("data"):
                        result_summary.append(f"【系统信息】{json.dumps(result['data'], ensure_ascii=False)}")
                except:
                    pass
            if result_summary:
                return "\n".join(result_summary) + "\n\n基于以上信息，我已经了解了相关情况。请问还有什么我可以帮助你的？"
        
        # 默认响应（带人格色彩）
        ocean = soul_profile.get("data", {}).get("ocean", {})
        traits = soul_profile.get("data", {}).get("traits", {})
        
        # 根据人格调整响应风格
        if ocean.get("openness", 0) > 0.7:
            style_hint = "展现出对问题的好奇心和探索精神"
        elif ocean.get("agreeableness", 0) > 0.7:
            style_hint = "保持温暖、友善的互动氛围"
        else:
            style_hint = "保持专业、简洁的表达"
        
        return f"我已经收到了你的消息。基于我的灵魂配置（开放性 {ocean.get('openness', 0.5):.0%}，共情水平 {traits.get('empathy_level', 0.5):.0%}），{style_hint}。请问具体需要什么帮助？"
    
    def _generate_conversation_id(self) -> str:
        """生成对话 ID"""
        return f"conv_{int(time.time() * 1000)}"
    
    def get_tools_for_coze(self) -> List[Dict]:
        """获取 Coze 格式的工具定义"""
        return self.soul_tools.get_tools_definition()
    
    def reset_conversation(self, conversation_id: str) -> bool:
        """重置对话"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False


# 便捷函数
def create_coze_adapter(
    bot_id: str = "",
    api_key: str = "",
    neshama_engine = None
) -> CozeAdapter:
    """创建 Coze 适配器实例"""
    return CozeAdapter(
        bot_id=bot_id,
        api_key=api_key,
        neshama_engine=neshama_engine
    )
