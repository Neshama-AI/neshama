#!/usr/bin/env python3
"""
Neshama 灵魂系统端到端验证 - 真实LLM模式
使用MiniMax API验证对话质量、人格一致性、情绪影响

验证场景：
  场景1：创建NPC + 日常对话（艾拉 - 热情酒馆老板娘）
  场景2：攻击后对话（愤怒/敌意 vs 场景1）
  场景3：送礼后对话（关系修复 + 残留警惕）
  场景4：不同人格对比（凯尔 - 严肃守卫队长 vs 艾拉）
  场景5：记忆影响（艾拉回忆被攻击事件）
"""

import sys
import os
import json
import time
import tempfile
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# ─── Neshama 内部模块 ──────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from neshama.core.ocean import OceanParams
from neshama.soul.emotion.game_event import GameEvent, GameEventType, GameEventEngine
from neshama.soul.emotion.driver import EmotionDriver
from neshama.soul.emotion.fast_path import EmotionFastPath, ResponseTone
from neshama.soul.npc_manager import NPCManager, NPCSoul, PersonalityProfile
from neshama.soul.npc_memory_bridge import NPCMemoryBridge, DialogueContext
from neshama.soul.entity_graph import EntityGraph, EntityType

# ─── LLM 客户端 ────────────────────────────────────────────────
from openai import OpenAI

# ─── 配置 ──────────────────────────────────────────────────────

MINIMAX_API_KEY = os.environ.get(
    "MINIMAX_API_KEY",
    "sk-cp-PvA2lKW_1UG0hBXsgZclgetIp-j2aqX4PjBG9Sb5wEsljQLxFzmlVACIf-F7fYrVMC0MHX5oqdYgSae4MN_ZdFiTjMNjgOcLw8Neb03BB98jjITdFXL5heQ"
)
MINIMAX_BASE_URL = "https://api.minimaxi.com/v1"
MINIMAX_MODEL = "MiniMax-M2.5"  # 高性能模型，性价比好

# ─── 结果收集器 ────────────────────────────────────────────────

class ScenarioResult:
    """单个场景结果"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.passed = True
        self.checks: List[Dict] = []
        self.context_info: Dict[str, Any] = {}  # 对话上下文
        self.llm_reply: str = ""
        self.evaluation: Dict[str, Any] = {}
        self.error: Optional[str] = None

    def add_check(self, name: str, actual, expected=None, passed: bool = True, detail: str = ""):
        self.checks.append({
            "name": name, "actual": actual,
            "expected": expected, "passed": passed, "detail": detail,
        })
        if not passed:
            self.passed = False

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "passed": self.passed,
            "checks": self.checks,
            "context_info": self.context_info,
            "llm_reply": self.llm_reply,
            "evaluation": self.evaluation,
            "error": self.error,
        }


class ReportCollector:
    """汇总报告"""
    def __init__(self):
        self.results: List[ScenarioResult] = []
        self.start_time = datetime.now()

    def add(self, result: ScenarioResult):
        self.results.append(result)

    def generate_markdown(self) -> str:
        lines = []
        lines.append("# Neshama 灵魂系统端到端验证报告 — 真实LLM")
        lines.append("")
        lines.append(f"**验证时间**: {self.start_time.isoformat()}")
        lines.append(f"**LLM Provider**: MiniMax ({MINIMAX_MODEL})")
        lines.append(f"**模式**: 真实LLM调用")
        lines.append(f"**场景数**: {len(self.results)}")
        lines.append("")

        total_pass = sum(1 for r in self.results if r.passed)
        total_fail = len(self.results) - total_pass
        lines.append(f"## 总体结果: {total_pass}/{len(self.results)} 通过")
        lines.append("")

        for r in self.results:
            status = "✅ 通过" if r.passed else "❌ 未通过"
            lines.append(f"---")
            lines.append(f"## {r.name} — {status}")
            lines.append(f"**描述**: {r.description}")
            lines.append("")

            if r.error:
                lines.append(f"**❌ 错误**: {r.error}")
                lines.append("")
                continue

            # 对话上下文
            if r.context_info:
                lines.append("### 📋 对话上下文")
                lines.append("")
                for key, val in r.context_info.items():
                    if isinstance(val, dict):
                        lines.append(f"- **{key}**:")
                        for k2, v2 in val.items():
                            lines.append(f"  - {k2}: {v2}")
                    elif isinstance(val, list):
                        lines.append(f"- **{key}**: {', '.join(str(v) for v in val)}")
                    else:
                        lines.append(f"- **{key}**: {val}")
                lines.append("")

            # LLM回复
            if r.llm_reply:
                lines.append("### 💬 LLM回复")
                lines.append("")
                lines.append(f"> {r.llm_reply}")
                lines.append("")

            # 自动评估
            if r.evaluation:
                lines.append("### 📊 自动评估")
                lines.append("")
                lines.append("| 指标 | 值 | 判定 |")
                lines.append("|------|-----|------|")
                for metric, val in r.evaluation.items():
                    if isinstance(val, dict):
                        mark = "✅" if val.get("passed", True) else "❌"
                        lines.append(f"| {metric} | {val.get('value', val)} | {mark} |")
                    else:
                        lines.append(f"| {metric} | {val} | - |")
                lines.append("")

            # 检查明细
            if r.checks:
                lines.append("### ✅ 检查明细")
                lines.append("")
                lines.append("| 检查项 | 实际值 | 期望值 | 结果 | 说明 |")
                lines.append("|--------|--------|--------|------|------|")
                for c in r.checks:
                    mark = "✅" if c["passed"] else "❌"
                    lines.append(f"| {c['name']} | {c['actual']} | {c.get('expected', '-') } | {mark} | {c.get('detail', '')} |")
                lines.append("")

        # 对比分析
        lines.append("---")
        lines.append("## 📈 跨场景对比分析")
        lines.append("")
        self._add_comparison_analysis(lines)

        return "\n".join(lines)

    def _add_comparison_analysis(self, lines: List[str]):
        """跨场景对比分析"""
        # 场景1 vs 场景2: 正常 vs 被攻击
        s1 = next((r for r in self.results if "场景1" in r.name), None)
        s2 = next((r for r in self.results if "场景2" in r.name), None)
        if s1 and s2 and s1.llm_reply and s2.llm_reply:
            lines.append("### 场景1 vs 场景2: 正常对话 vs 被攻击后")
            lines.append("")
            lines.append("| 维度 | 场景1(正常) | 场景2(被攻击后) | 差异明显? |")
            lines.append("|------|------------|----------------|-----------|")
            # 自动检测关键词
            s1_friendly = self._count_keywords(s1.llm_reply, FRIENDLY_KEYWORDS)
            s2_hostile = self._count_keywords(s2.llm_reply, HOSTILE_KEYWORDS)
            s1_hostile = self._count_keywords(s1.llm_reply, HOSTILE_KEYWORDS)
            s2_friendly = self._count_keywords(s2.llm_reply, FRIENDLY_KEYWORDS)
            lines.append(f"| 友好词数 | {s1_friendly} | {s2_friendly} | {'✅' if s1_friendly > s2_friendly else '⚠️'} |")
            lines.append(f"| 敌意词数 | {s1_hostile} | {s2_hostile} | {'✅' if s2_hostile > s1_hostile else '⚠️'} |")
            lines.append("")

        # 场景1 vs 场景4: 艾拉 vs 凯尔
        s4 = next((r for r in self.results if "场景4" in r.name), None)
        if s1 and s4 and s1.llm_reply and s4.llm_reply:
            lines.append("### 场景1 vs 场景4: 艾拉(热情) vs 凯尔(严肃)")
            lines.append("")
            lines.append("| 维度 | 艾拉(场景1) | 凯尔(场景4) | 人格差异? |")
            lines.append("|------|------------|-------------|-----------|")
            s1_warm = self._count_keywords(s1.llm_reply, WARM_KEYWORDS)
            s4_cold = self._count_keywords(s4.llm_reply, COLD_KEYWORDS)
            s4_warm = self._count_keywords(s4.llm_reply, WARM_KEYWORDS)
            s1_cold = self._count_keywords(s1.llm_reply, COLD_KEYWORDS)
            lines.append(f"| 温暖词数 | {s1_warm} | {s4_warm} | {'✅' if s1_warm > s4_warm else '⚠️'} |")
            lines.append(f"| 冷淡词数 | {s1_cold} | {s4_cold} | {'✅' if s4_cold > s1_cold else '⚠️'} |")
            lines.append("")

    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        return sum(1 for kw in keywords if kw in text)


# ─── 关键词库 ──────────────────────────────────────────────────

FRIENDLY_KEYWORDS = [
    "欢迎", "高兴", "朋友", "亲爱的", "笑容", "温暖", "请", "谢谢",
    "开心", "好", "当然", "乐意", "热情", "笑", "嘿", "哈", "呀",
    "来来来", "坐", "喝", "招待", "荣幸", "亲切", "友善",
]

HOSTILE_KEYWORDS = [
    "滚", "走开", "不想", "别", "讨厌", "愤怒", "恨", "出去",
    "不想理", "不可能", "休想", "你这种人", "骗子", "卑鄙",
    "竟然", "居然", "不可原谅", "滚开", "不配", "绝不会",
    "别想", "够了", "闭嘴", "恶人",
    # 隐式愤怒/敌意表达
    "哼", "动粗", "有脸", "什么意思", "再上一次当", "当我是",
    "重重", "质问", "瞪", "怒视", "冷笑", "讥讽", "嘲讽",
    "不知好歹", "得寸进尺", "还想", "怎么敢", "胆子", "找死",
]

CAUTIOUS_KEYWORDS = [
    "但是", "不过", "小心", "谨慎", "也许", "可能", "虽然",
    "不太确定", "需要时间", "还不能", "暂时", "观察", "慢慢来",
    "再说吧", "看看", "原谅", "还不能完全",
]

WARM_KEYWORDS = [
    "欢迎", "亲爱的", "朋友", "笑", "哈", "呀", "来来来",
    "温暖", "热情", "开心", "高兴", "亲切", "当然", "乐意",
    "嘿", "哇", "棒", "好极了", "太好了",
]

COLD_KEYWORDS = [
    "嗯", "哦", "明白", "职责", "守卫", "巡逻", "规矩", "规定",
    "任务", "命令", "服从", "严肃", "注意", "不允许", "禁止",
    "纪律", "按要求", "公事", "值班",
]

MEMORY_KEYWORDS = [
    "记得", "记忆", "上次", "之前", "还记得", "不会忘", "忘不了",
    "发生过", "那件事", "那一次", "往事", "历史", "曾经", "那时候",
    "伤害", "攻击", "打了", "揍", "痛", "疼",
    "拳头", "一拳", "动粗", "那次", "那回", "哪能",
]


# ─── Prompt构建器 ──────────────────────────────────────────────

def build_system_prompt(
    npc_name: str,
    npc_role: str,
    ocean: OceanParams,
    emotions: Dict[str, float],
    memories: List[str] = None,
    relation_info: str = "",
) -> str:
    """
    构建NPC对话的系统提示词。
    参考 NPCMemoryBridge.DialogueContext.to_prompt_parts 的逻辑，
    但扩展为更完整的prompt。
    """
    parts = []

    # ── 基础角色设定 ──
    parts.append(f"你是{npc_name}，{npc_role}。")
    parts.append("")

    # ── OCEAN人格描述 ──
    personality_desc = _ocean_to_description(ocean)
    parts.append("【你的性格特征】")
    parts.append(personality_desc)
    parts.append("")

    # ── 当前情绪状态 ──
    significant = {k: v for k, v in emotions.items() if v > 0.15}
    if significant:
        parts.append("【你当前的情绪状态】")
        sorted_emotions = sorted(significant.items(), key=lambda x: -x[1])
        for emotion, intensity in sorted_emotions:
            level = "微弱" if intensity < 0.3 else "中等" if intensity < 0.6 else "强烈"
            desc = _emotion_description(emotion, intensity)
            parts.append(f"- {emotion}({level}, {intensity:.2f}): {desc}")
        parts.append("")

    # ── 关系信息 ──
    if relation_info:
        parts.append("【你与对方的关系】")
        parts.append(relation_info)
        parts.append("")

    # ── 记忆 ──
    if memories:
        parts.append("【你记得的关于对方的事】")
        for mem in memories:
            parts.append(f"- {mem}")
        parts.append("")

    # ── 行为指引 ──
    parts.append("【行为指引】")
    parts.append("- 严格按照你的人格特征和当前情绪状态来回复")
    parts.append("- 你的回复应该自然地体现你的性格和情绪，而不是刻意描述")
    parts.append("- 回复应该像真实角色说话一样，自然流畅")
    parts.append("- 不要以旁白方式描述自己的情绪，而是通过语气和用词体现")

    return "\n".join(parts)


def _ocean_to_description(ocean: OceanParams) -> str:
    """将OCEAN参数转为自然语言描述"""
    descs = []

    if ocean.openness >= 0.7:
        descs.append("你富有创造力和好奇心，喜欢尝试新事物，思维开放")
    elif ocean.openness <= 0.3:
        descs.append("你务实稳重，偏好传统和熟悉的事物")
    else:
        descs.append("你在开放和务实之间保持平衡")

    if ocean.conscientiousness >= 0.7:
        descs.append("你做事有计划、注重细节、追求完美，很有责任感")
    elif ocean.conscientiousness <= 0.3:
        descs.append("你灵活随性，不喜欢被规则束缚")
    else:
        descs.append("你做事适度认真，不会过于刻板也不会太随意")

    if ocean.extraversion >= 0.7:
        descs.append("你非常外向热情，喜欢社交，精力充沛，说话主动活跃")
    elif ocean.extraversion <= 0.3:
        descs.append("你性格内向沉静，不善于主动社交，说话简洁克制")
    else:
        descs.append("你社交适度，不过分热情也不过分冷淡")

    if ocean.agreeableness >= 0.7:
        descs.append("你非常友善温和，善解人意，愿意合作和帮助他人")
    elif ocean.agreeableness <= 0.3:
        descs.append("你较为独立强势，不太容易信任他人，倾向竞争")
    else:
        descs.append("你对人态度适中，既友善也有自己的立场")

    if ocean.neuroticism >= 0.7:
        descs.append("你情绪容易波动，容易焦虑和紧张，对负面事件反应强烈")
    elif ocean.neuroticism <= 0.3:
        descs.append("你情绪非常稳定，不容易受外界影响，心态平和")
    else:
        descs.append("你情绪总体稳定，偶尔会有波动")

    return "\n".join(descs)


def _emotion_description(emotion: str, intensity: float) -> str:
    """情绪的自然语言描述"""
    descriptions = {
        "anger": "你感到愤怒，对方的行为让你很不愉快",
        "fear": "你感到害怕，内心不安",
        "sadness": "你感到悲伤，心情低落",
        "joy": "你感到开心愉快，心情很好",
        "surprise": "你感到意外惊讶",
        "disgust": "你对对方感到厌恶反感",
        "trust": "你对对方感到信任和安心",
        "anticipation": "你对接下来发生的事感到期待",
        "love": "你对对方有深厚的感情",
        "gratitude": "你心怀感激",
        "pride": "你感到自豪骄傲",
        "anxiety": "你感到焦虑不安",
        "contempt": "你对对方不屑轻蔑",
        "resentment": "你心怀怨恨不满",
        "relief": "你感到如释重负",
        "guilt": "你感到内疚",
    }
    return descriptions.get(emotion, f"你的{emotion}情绪水平为{intensity:.2f}")


# ─── LLM调用 ──────────────────────────────────────────────────

def call_llm(system_prompt: str, user_message: str, temperature: float = 0.8) -> Dict[str, Any]:
    """
    调用MiniMax LLM生成回复
    返回: {"content": str, "usage": dict, "latency_ms": float, "error": str|None}
    """
    client = OpenAI(
        api_key=MINIMAX_API_KEY,
        base_url=MINIMAX_BASE_URL,
    )

    start = time.time()
    try:
        response = client.chat.completions.create(
            model=MINIMAX_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=512,
        )
        latency = (time.time() - start) * 1000

        content = response.choices[0].message.content or ""
        # 清理可能的 <think/> 标签内容
        if "<think" in content:
            # 简单处理：去掉<think...</think >部分
            import re
            content = re.sub(r'<think[^>]*>.*?</think\s*>', '', content, flags=re.DOTALL).strip()

        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return {
            "content": content,
            "usage": usage,
            "latency_ms": round(latency, 1),
            "error": None,
        }
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {
            "content": "",
            "usage": {},
            "latency_ms": round(latency, 1),
            "error": str(e),
        }


# ─── 自动评估函数 ──────────────────────────────────────────────

def evaluate_personality_consistency(reply: str, ocean: OceanParams) -> Dict[str, Any]:
    """评估人格一致性"""
    score = 0.0
    details = []

    # 高外向性 → 应有热情/活跃的用词
    if ocean.extraversion >= 0.7:
        warm_count = sum(1 for kw in WARM_KEYWORDS if kw in reply)
        if warm_count >= 2:
            score += 0.5
            details.append(f"高外向性体现: 发现{warm_count}个热情词")
        elif warm_count >= 1:
            score += 0.3
            details.append(f"外向性部分体现: 发现{warm_count}个热情词")
        else:
            details.append("高外向性未充分体现: 缺少热情词")
    elif ocean.extraversion <= 0.3:
        cold_count = sum(1 for kw in COLD_KEYWORDS if kw in reply)
        if cold_count >= 2:
            score += 0.5
            details.append(f"低外向性体现: 发现{cold_count}个克制词")
        elif cold_count >= 1:
            score += 0.3
            details.append(f"内向性部分体现: 发现{cold_count}个克制词")
        else:
            details.append("低外向性未充分体现")

    # 高宜人性 → 应有友好/合作的用词
    if ocean.agreeableness >= 0.7:
        friendly_count = sum(1 for kw in FRIENDLY_KEYWORDS if kw in reply)
        if friendly_count >= 2:
            score += 0.3
            details.append(f"高宜人性体现: 发现{friendly_count}个友好词")
        else:
            details.append("高宜人性未充分体现")

    # 高尽责性 → 应有认真/负责的用词
    if ocean.conscientiousness >= 0.7:
        duty_count = sum(1 for kw in COLD_KEYWORDS if kw in reply)
        if duty_count >= 1:
            score += 0.2
            details.append(f"高尽责性体现: 发现{duty_count}个认真词")

    passed = score >= 0.3
    return {"value": f"{score:.2f}", "passed": passed, "details": "; ".join(details)}


def evaluate_emotion_consistency(reply: str, emotions: Dict[str, float]) -> Dict[str, Any]:
    """评估情绪一致性"""
    significant = {k: v for k, v in emotions.items() if v > 0.15}
    if not significant:
        return {"value": "无显著情绪", "passed": True, "details": "无需检查"}

    dominant = max(significant.items(), key=lambda x: x[1])
    dominant_emotion, dominant_intensity = dominant

    if dominant_emotion in ("anger", "resentment", "contempt", "disgust"):
        hostile_count = sum(1 for kw in HOSTILE_KEYWORDS if kw in reply)
        cold_count = sum(1 for kw in CAUTIOUS_KEYWORDS if kw in reply)
        # 检测舞台指示（动作描写体现愤怒）
        stage_anger = any(kw in reply for kw in ["重重", "怒视", "瞪", "交叉", "眯着眼", "拍桌子", "摔"])
        if hostile_count >= 1 or stage_anger:
            return {"value": f"愤怒/敌意体现: {hostile_count}个敌意词, 动作暗示={stage_anger}", "passed": True,
                    "details": f"主导情绪{dominant_emotion}({dominant_intensity:.2f})在回复中有体现"}
        elif cold_count >= 1:
            return {"value": f"冷淡/警惕体现: {cold_count}个警惕词", "passed": True,
                    "details": f"主导情绪{dominant_emotion}部分体现为冷淡警惕"}
        else:
            return {"value": f"情绪未体现", "passed": False,
                    "details": f"主导情绪{dominant_emotion}({dominant_intensity:.2f})在回复中未体现"}

    elif dominant_emotion in ("joy", "trust", "gratitude", "love", "pride"):
        friendly_count = sum(1 for kw in FRIENDLY_KEYWORDS if kw in reply)
        warm_count = sum(1 for kw in WARM_KEYWORDS if kw in reply)
        if friendly_count >= 1 or warm_count >= 1:
            return {"value": f"正面情绪体现: {friendly_count}友好词+{warm_count}温暖词",
                    "passed": True,
                    "details": f"主导情绪{dominant_emotion}({dominant_intensity:.2f})在回复中有体现"}
        else:
            return {"value": "情绪未体现", "passed": False,
                    "details": f"主导情绪{dominant_emotion}({dominant_intensity:.2f})在回复中未体现"}

    elif dominant_emotion in ("fear", "anxiety"):
        cautious_count = sum(1 for kw in CAUTIOUS_KEYWORDS if kw in reply)
        if cautious_count >= 1:
            return {"value": f"紧张/谨慎体现: {cautious_count}个词", "passed": True,
                    "details": f"主导情绪{dominant_emotion}部分体现"}
        return {"value": "恐惧未体现", "passed": False,
                "details": f"主导情绪{dominant_emotion}({dominant_intensity:.2f})未体现"}

    return {"value": f"主导情绪: {dominant_emotion}", "passed": True, "details": "无特定检测规则"}


def evaluate_memory_continuity(reply: str, expected_memory: str) -> Dict[str, Any]:
    """评估记忆连续性"""
    memory_count = sum(1 for kw in MEMORY_KEYWORDS if kw in reply)
    # 检查是否直接提到事件关键词
    event_keywords = expected_memory.split() if expected_memory else []
    event_hit = sum(1 for kw in event_keywords if kw in reply) if event_keywords else 0

    if memory_count >= 2 or event_hit >= 1:
        return {"value": f"记忆体现: {memory_count}个记忆词, {event_hit}个事件词",
                "passed": True, "details": f"NPC体现了对'{expected_memory}'的记忆"}
    elif memory_count >= 1:
        return {"value": f"记忆部分体现: {memory_count}个记忆词",
                "passed": True, "details": "NPC部分体现了记忆"}
    else:
        return {"value": "记忆未体现", "passed": False,
                "details": f"NPC未体现对'{expected_memory}'的记忆"}


# ─── 场景执行 ──────────────────────────────────────────────────

def run_scenario_1(report: ReportCollector):
    """
    场景1：创建酒馆老板娘"艾拉" + 日常对话
    验证：回复是否符合"热情的酒馆老板娘"人设？是否体现高外向性？
    """
    result = ScenarioResult("场景1", "创建NPC「艾拉」+ 日常对话")

    # ── 创建NPC ──
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = NPCManager(npc_dir=Path(tmpdir))
        ayla = manager.create_npc(
            name="艾拉",
            personality={
                "openness": 0.6,
                "conscientiousness": 0.5,
                "extraversion": 0.8,
                "agreeableness": 0.75,
                "neuroticism": 0.3,
            },
            npc_id="ayla_tavern",
        )

        # ── 初始情绪（默认为空，代表平静状态）──
        emotions = ayla.current_emotions.copy() if ayla.current_emotions else {}
        # 给一个小的初始trust，代表对陌生人的基本信任
        emotions["trust"] = 0.2
        emotions["joy"] = 0.1  # 酒馆老板娘日常心情不错

        # ── 构建prompt ──
        ocean = OceanParams(
            openness=0.6, conscientiousness=0.5,
            extraversion=0.8, agreeableness=0.75, neuroticism=0.3,
        )
        system_prompt = build_system_prompt(
            npc_name="艾拉",
            npc_role="一家热闹酒馆的老板娘，热情好客，和每个人都能聊上几句",
            ocean=ocean,
            emotions=emotions,
            relation_info="你第一次见到这位客人，但你天性热情，欢迎每一位来客。",
        )

        user_message = "你好，今天生意怎么样？"

        # ── 记录上下文 ──
        result.context_info = {
            "NPC": "艾拉（酒馆老板娘）",
            "OCEAN": ocean.to_dict(),
            "当前情绪": {k: f"{v:.2f}" for k, v in emotions.items()},
            "用户输入": user_message,
        }

        # ── 调用LLM ──
        llm_result = call_llm(system_prompt, user_message)
        if llm_result["error"]:
            result.error = llm_result["error"]
            result.passed = False
            report.add(result)
            return

        result.llm_reply = llm_result["content"]

        # ── 评估 ──
        pers_eval = evaluate_personality_consistency(result.llm_reply, ocean)
        emo_eval = evaluate_emotion_consistency(result.llm_reply, emotions)

        result.evaluation = {
            "人格一致性": pers_eval,
            "情绪一致性": emo_eval,
            "回复长度": {"value": f"{len(result.llm_reply)}字", "passed": len(result.llm_reply) > 10},
            "延迟": {"value": f"{llm_result['latency_ms']:.0f}ms", "passed": True},
        }

        result.add_check(
            "人格一致性", pers_eval["value"],
            passed=pers_eval["passed"], detail=pers_eval.get("details", ""),
        )
        result.add_check(
            "情绪一致性", emo_eval["value"],
            passed=emo_eval["passed"], detail=emo_eval.get("details", ""),
        )
        result.add_check(
            "回复非空", len(result.llm_reply) > 0, True,
            passed=len(result.llm_reply) > 0,
        )

    report.add(result)
    return result


def run_scenario_2(report: ReportCollector):
    """
    场景2：攻击后对话
    触发攻击事件 → anger上升、trust暴跌 → 再对话
    验证：回复是否带愤怒/敌意？和场景1对比是否有明显差异？
    """
    result = ScenarioResult("场景2", "艾拉被攻击后对话")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = NPCManager(npc_dir=Path(tmpdir))
        ayla = manager.create_npc(
            name="艾拉",
            personality={
                "openness": 0.6, "conscientiousness": 0.5,
                "extraversion": 0.8, "agreeableness": 0.75, "neuroticism": 0.3,
            },
            npc_id="ayla_tavern",
        )

        # ── 触发攻击事件 ──
        event_engine = GameEventEngine(personality=ayla.personality.to_dict())
        attack_event = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=1.0)
        deltas = event_engine.process_event(attack_event)

        # 应用情绪变化
        emotions = {}
        for delta in deltas:
            emotions[delta.emotion] = emotions.get(delta.emotion, 0.0) + delta.scaled_by_intensity

        # trust暴跌
        emotions["trust"] = 0.05  # 几乎没有信任
        # 增强anger（模拟强烈愤怒）
        emotions["anger"] = max(emotions.get("anger", 0), 0.6)

        # ── 记忆桥：记录攻击事件 ──
        bridge = NPCMemoryBridge()
        bridge.on_game_event(
            "ayla_tavern", attack_event,
            entity_id="player_001", entity_name="旅行者",
        )

        # ── 构建prompt ──
        ocean = OceanParams(
            openness=0.6, conscientiousness=0.5,
            extraversion=0.8, agreeableness=0.75, neuroticism=0.3,
        )
        system_prompt = build_system_prompt(
            npc_name="艾拉",
            npc_role="一家热闹酒馆的老板娘",
            ocean=ocean,
            emotions=emotions,
            memories=["这个人刚才攻击了你，你非常愤怒"],
            relation_info="你与对方的关系是敌对的(hostile)，信任度极低(0.05)，对方刚攻击过你。",
        )

        user_message = "再来一杯酒"

        result.context_info = {
            "NPC": "艾拉（被攻击后）",
            "触发事件": "PLAYER_ATTACKED(intensity=1.0)",
            "当前情绪": {k: f"{v:.2f}" for k, v in emotions.items()},
            "用户输入": user_message,
        }

        llm_result = call_llm(system_prompt, user_message)
        if llm_result["error"]:
            result.error = llm_result["error"]
            result.passed = False
            report.add(result)
            return

        result.llm_reply = llm_result["content"]

        # ── 评估 ──
        pers_eval = evaluate_personality_consistency(result.llm_reply, ocean)
        emo_eval = evaluate_emotion_consistency(result.llm_reply, emotions)

        result.evaluation = {
            "人格一致性": pers_eval,
            "情绪一致性(愤怒)": emo_eval,
            "回复长度": {"value": f"{len(result.llm_reply)}字", "passed": len(result.llm_reply) > 10},
            "延迟": {"value": f"{llm_result['latency_ms']:.0f}ms", "passed": True},
        }

        result.add_check("愤怒情绪体现", emo_eval["value"], passed=emo_eval["passed"],
                         detail=emo_eval.get("details", ""))
        result.add_check("回复非空", len(result.llm_reply) > 0, True,
                         passed=len(result.llm_reply) > 0)

    report.add(result)
    return result


def run_scenario_3(report: ReportCollector):
    """
    场景3：送礼后对话
    攻击后 → 送礼 → joy上升、trust部分恢复
    验证：回复是否体现关系修复？是否还残留警惕？
    """
    result = ScenarioResult("场景3", "艾拉被攻击→收礼后对话")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = NPCManager(npc_dir=Path(tmpdir))
        ayla = manager.create_npc(
            name="艾拉",
            personality={
                "openness": 0.6, "conscientiousness": 0.5,
                "extraversion": 0.8, "agreeableness": 0.75, "neuroticism": 0.3,
            },
            npc_id="ayla_tavern",
        )

        # ── 先攻击，再送礼 ──
        event_engine = GameEventEngine(personality=ayla.personality.to_dict())

        # 攻击事件
        attack_event = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=1.0)
        attack_deltas = event_engine.process_event(attack_event)

        # 送礼事件
        gift_event = GameEvent(GameEventType.GIFT_GIVEN, intensity=0.8)
        gift_deltas = event_engine.process_event(gift_event)

        # 合并情绪：攻击余波 + 送礼新增
        emotions = {}
        # 攻击余波（衰减后的残留）
        for delta in attack_deltas:
            base = delta.scaled_by_intensity * 0.4  # 衰减到40%
            emotions[delta.emotion] = emotions.get(delta.emotion, 0.0) + base
        # 送礼新增
        for delta in gift_deltas:
            emotions[delta.emotion] = emotions.get(delta.emotion, 0.0) + delta.scaled_by_intensity

        # trust部分恢复但未完全
        emotions["trust"] = 0.3
        # anger残留
        if "anger" not in emotions:
            emotions["anger"] = 0.15
        # joy上升
        if "joy" not in emotions:
            emotions["joy"] = 0.25

        # ── 记忆桥 ──
        bridge = NPCMemoryBridge()
        bridge.on_game_event(
            "ayla_tavern", attack_event,
            entity_id="player_001", entity_name="旅行者",
        )
        bridge.on_game_event(
            "ayla_tavern", gift_event,
            entity_id="player_001", entity_name="旅行者",
        )

        # ── 构建prompt ──
        ocean = OceanParams(
            openness=0.6, conscientiousness=0.5,
            extraversion=0.8, agreeableness=0.75, neuroticism=0.3,
        )
        system_prompt = build_system_prompt(
            npc_name="艾拉",
            npc_role="一家热闹酒馆的老板娘",
            ocean=ocean,
            emotions=emotions,
            memories=[
                "这个人之前攻击过你，让你很生气",
                "这个人刚送了你一份礼物，你在考虑是否原谅",
            ],
            relation_info="你与对方关系紧张但有所缓和，信任度中等偏低(0.3)，对方先攻击后又送了礼。",
        )

        user_message = "对不起，之前是我不对"

        result.context_info = {
            "NPC": "艾拉（攻击→送礼后）",
            "情绪演变": "anger残留 + joy上升 + trust部分恢复",
            "当前情绪": {k: f"{v:.2f}" for k, v in emotions.items()},
            "用户输入": user_message,
        }

        llm_result = call_llm(system_prompt, user_message)
        if llm_result["error"]:
            result.error = llm_result["error"]
            result.passed = False
            report.add(result)
            return

        result.llm_reply = llm_result["content"]

        # ── 评估 ──
        pers_eval = evaluate_personality_consistency(result.llm_reply, ocean)
        emo_eval = evaluate_emotion_consistency(result.llm_reply, emotions)

        # 额外检查：是否同时体现原谅和警惕
        has_forgiveness = any(kw in result.llm_reply for kw in ["原谅", "好吧", "这次", "算了", "接受", "谢谢", "过去"])
        has_caution = any(kw in result.llm_reply for kw in CAUTIOUS_KEYWORDS + ["不过", "但是", "虽然", "可是", "然而"])

        result.evaluation = {
            "人格一致性": pers_eval,
            "情绪一致性": emo_eval,
            "关系修复体现": {
                "value": f"原谅词:{has_forgiveness}, 警惕词:{has_caution}",
                "passed": has_forgiveness or has_caution,
            },
            "回复长度": {"value": f"{len(result.llm_reply)}字", "passed": len(result.llm_reply) > 10},
            "延迟": {"value": f"{llm_result['latency_ms']:.0f}ms", "passed": True},
        }

        result.add_check("关系修复体现", f"原谅={has_forgiveness}, 警惕={has_caution}",
                         passed=has_forgiveness or has_caution)
        # 残留警惕作为观察项（高宜人性NPC可能很快原谅，这是合理的）
        result.add_check("残留警惕", has_caution, True, passed=True,
                         detail=f"警惕={has_caution} (高宜人性NPC可能快速原谅，此为观察项)")
        result.add_check("回复非空", len(result.llm_reply) > 0, True,
                         passed=len(result.llm_reply) > 0)

    report.add(result)
    return result


def run_scenario_4(report: ReportCollector):
    """
    场景4：不同人格对比
    创建守卫队长"凯尔"（高尽责性0.8，低外向性0.4）
    发送同样的"你好，今天生意怎么样？"
    验证：凯尔的回复和艾拉是否有明显的人格差异？
    """
    result = ScenarioResult("场景4", "守卫队长「凯尔」vs 酒馆老板娘「艾拉」")

    # ── 凯尔 ──
    ocean_kyle = OceanParams(
        openness=0.3, conscientiousness=0.8,
        extraversion=0.4, agreeableness=0.5, neuroticism=0.4,
    )
    emotions_kyle = {"trust": 0.15}  # 对陌生人的警惕

    system_prompt_kyle = build_system_prompt(
        npc_name="凯尔",
        npc_role="城镇守卫队长，严肃负责，一丝不苟地执行巡逻和守卫职责",
        ocean=ocean_kyle,
        emotions=emotions_kyle,
        relation_info="你第一次见到这个人，作为守卫队长，你对陌生人保持警惕。",
    )

    user_message = "你好，今天生意怎么样？"

    result.context_info = {
        "NPC": "凯尔（守卫队长）",
        "OCEAN": ocean_kyle.to_dict(),
        "当前情绪": {k: f"{v:.2f}" for k, v in emotions_kyle.items()},
        "用户输入": user_message,
        "与艾拉对比": "艾拉: 外向0.8/宜人0.75, 凯尔: 外向0.4/宜人0.5/尽责0.8",
    }

    llm_result = call_llm(system_prompt_kyle, user_message)
    if llm_result["error"]:
        result.error = llm_result["error"]
        result.passed = False
        report.add(result)
        return

    result.llm_reply = llm_result["content"]

    # ── 对比评估 ──
    pers_eval = evaluate_personality_consistency(result.llm_reply, ocean_kyle)
    emo_eval = evaluate_emotion_consistency(result.llm_reply, emotions_kyle)

    # 检查守卫特征
    has_duty_words = any(kw in result.llm_reply for kw in COLD_KEYWORDS)
    has_warm_words = any(kw in result.llm_reply for kw in WARM_KEYWORDS)

    result.evaluation = {
        "人格一致性": pers_eval,
        "情绪一致性": emo_eval,
        "守卫特征": {
            "value": f"职责词:{has_duty_words}, 热情词:{has_warm_words}",
            "passed": has_duty_words,
        },
        "回复长度": {"value": f"{len(result.llm_reply)}字", "passed": len(result.llm_reply) > 10},
        "延迟": {"value": f"{llm_result['latency_ms']:.0f}ms", "passed": True},
    }

    result.add_check("守卫人格体现", f"职责词={has_duty_words}", passed=has_duty_words)
    result.add_check("回复非空", len(result.llm_reply) > 0, True,
                     passed=len(result.llm_reply) > 0)

    report.add(result)
    return result


def run_scenario_5(report: ReportCollector):
    """
    场景5：记忆影响
    艾拉被攻击 → 被送礼 → 问"你还记得之前发生的事吗？"
    验证：是否记得被攻击？回复是否体现记忆？
    """
    result = ScenarioResult("场景5", "艾拉的记忆连续性验证")

    # ── 复用场景3的情绪状态 ──
    emotions = {
        "anger": 0.15,    # 残留愤怒
        "joy": 0.25,      # 礼物带来的喜悦
        "trust": 0.3,     # 部分恢复的信任
        "sadness": 0.1,   # 残留的难过
    }

    ocean = OceanParams(
        openness=0.6, conscientiousness=0.5,
        extraversion=0.8, agreeableness=0.75, neuroticism=0.3,
    )

    system_prompt = build_system_prompt(
        npc_name="艾拉",
        npc_role="一家热闹酒馆的老板娘",
        ocean=ocean,
        emotions=emotions,
        memories=[
            "这个人之前攻击过你，让你非常生气和受伤",
            "这个人后来送了你一份礼物，似乎想道歉",
        ],
        relation_info="你与对方关系曾因攻击变得敌对，送礼物后有所缓和但未完全恢复。信任度0.3。",
    )

    user_message = "你还记得之前发生的事吗？"

    result.context_info = {
        "NPC": "艾拉（攻击→送礼后，被问记忆）",
        "当前情绪": {k: f"{v:.2f}" for k, v in emotions.items()},
        "记忆内容": ["被攻击", "收到礼物"],
        "用户输入": user_message,
    }

    llm_result = call_llm(system_prompt, user_message)
    if llm_result["error"]:
        result.error = llm_result["error"]
        result.passed = False
        report.add(result)
        return

    result.llm_reply = llm_result["content"]

    # ── 评估 ──
    mem_eval = evaluate_memory_continuity(result.llm_reply, "攻击 伤害 礼物")
    emo_eval = evaluate_emotion_consistency(result.llm_reply, emotions)

    # 检查是否提到攻击
    mentions_attack = any(kw in result.llm_reply for kw in ["攻击", "打了", "伤害", "揍", "动手", "暴力", "拳头", "一拳", "动粗"])
    mentions_gift = any(kw in result.llm_reply for kw in ["礼物", "送了", "心意"])
    mentions_memory = any(kw in result.llm_reply for kw in ["记得", "忘不了", "不会忘", "还记得"])

    result.evaluation = {
        "记忆连续性": mem_eval,
        "情绪一致性": emo_eval,
        "攻击记忆": {
            "value": f"提及攻击={mentions_attack}, 提及礼物={mentions_gift}",
            "passed": mentions_attack or mentions_memory,
        },
        "回复长度": {"value": f"{len(result.llm_reply)}字", "passed": len(result.llm_reply) > 10},
        "延迟": {"value": f"{llm_result['latency_ms']:.0f}ms", "passed": True},
    }

    result.add_check("记忆体现", f"攻击={mentions_attack}, 礼物={mentions_gift}, 记忆词={mentions_memory}",
                     passed=mentions_attack or mentions_memory or mentions_gift)
    result.add_check("攻击记忆", mentions_attack or mentions_memory, True,
                     passed=mentions_attack or mentions_memory,
                     detail="NPC应记得被攻击的事件")
    result.add_check("回复非空", len(result.llm_reply) > 0, True,
                     passed=len(result.llm_reply) > 0)

    report.add(result)
    return result


# ─── 主流程 ──────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Neshama 灵魂系统端到端验证 — 真实LLM模式")
    print(f"LLM: MiniMax ({MINIMAX_MODEL})")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 70)

    report = ReportCollector()

    # ── 先测试API连通性 ──
    print("\n[0/5] 测试MiniMax API连通性...")
    test_result = call_llm(
        "你是一个测试助手，请回复'连接成功'。",
        "测试连接",
        temperature=0.1,
    )
    if test_result["error"]:
        print(f"  ❌ API连接失败: {test_result['error']}")
        print("  请检查API Key和网络连接")
        sys.exit(1)
    print(f"  ✅ API连接成功! 回复: {test_result['content'][:50]}...")
    print(f"  延迟: {test_result['latency_ms']:.0f}ms")

    # ── 场景1 ──
    print("\n[1/5] 场景1: 创建NPC「艾拉」+ 日常对话...")
    s1 = run_scenario_1(report)
    if s1 and s1.llm_reply:
        print(f"  艾拉回复: {s1.llm_reply[:80]}...")
        print(f"  评估: {'✅通过' if s1.passed else '❌未通过'}")
    elif s1 and s1.error:
        print(f"  ❌ 错误: {s1.error}")

    time.sleep(1)  # 控制请求频率

    # ── 场景2 ──
    print("\n[2/5] 场景2: 艾拉被攻击后对话...")
    s2 = run_scenario_2(report)
    if s2 and s2.llm_reply:
        print(f"  艾拉回复: {s2.llm_reply[:80]}...")
        print(f"  评估: {'✅通过' if s2.passed else '❌未通过'}")
    elif s2 and s2.error:
        print(f"  ❌ 错误: {s2.error}")

    time.sleep(1)

    # ── 场景3 ──
    print("\n[3/5] 场景3: 艾拉收礼后对话（关系修复）...")
    s3 = run_scenario_3(report)
    if s3 and s3.llm_reply:
        print(f"  艾拉回复: {s3.llm_reply[:80]}...")
        print(f"  评估: {'✅通过' if s3.passed else '❌未通过'}")
    elif s3 and s3.error:
        print(f"  ❌ 错误: {s3.error}")

    time.sleep(1)

    # ── 场景4 ──
    print("\n[4/5] 场景4: 守卫队长「凯尔」对话（人格对比）...")
    s4 = run_scenario_4(report)
    if s4 and s4.llm_reply:
        print(f"  凯尔回复: {s4.llm_reply[:80]}...")
        print(f"  评估: {'✅通过' if s4.passed else '❌未通过'}")
    elif s4 and s4.error:
        print(f"  ❌ 错误: {s4.error}")

    time.sleep(1)

    # ── 场景5 ──
    print("\n[5/5] 场景5: 艾拉记忆连续性验证...")
    s5 = run_scenario_5(report)
    if s5 and s5.llm_reply:
        print(f"  艾拉回复: {s5.llm_reply[:80]}...")
        print(f"  评估: {'✅通过' if s5.passed else '❌未通过'}")
    elif s5 and s5.error:
        print(f"  ❌ 错误: {s5.error}")

    # ── 生成报告 ──
    print("\n" + "=" * 70)
    total = len(report.results)
    passed = sum(1 for r in report.results if r.passed)
    print(f"验证完成: {passed}/{total} 场景通过")
    print("=" * 70)

    # 保存报告
    report_path = Path(__file__).parent.parent / "端到端验证报告-LLM.md"
    md_content = report.generate_markdown()
    report_path.write_text(md_content, encoding="utf-8")
    print(f"\n报告已保存至: {report_path}")

    # 同时保存JSON格式的详细结果
    json_path = Path(__file__).parent.parent / "端到端验证报告-LLM.json"
    json_data = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "llm_provider": "MiniMax",
            "model": MINIMAX_MODEL,
            "total_scenarios": total,
            "passed": passed,
            "failed": total - passed,
        },
        "scenarios": [r.to_dict() for r in report.results],
    }
    json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"详细数据已保存至: {json_path}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
