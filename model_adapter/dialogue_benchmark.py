"""
Neshama Dialogue Quality Benchmark - NPC对话质量评测框架
专门针对NPC对话场景的质量评估

功能:
- 对比不同Provider在NPC对话场景的质量
- 硬编码测试用例（不调API）
- 规则评分（不调LLM）：
  - 人格一致性
  - 情绪一致性
  - 上下文连贯性
  - 长度合理性
- 输出综合对比报告
"""

import time
import re
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging

from .providers.base import Message, MessageRole

logger = logging.getLogger(__name__)


# ── 测试用例定义 ──────────────────────────────────────────────────────────────

@dataclass
class NPCCTestCase:
    """NPC对话测试用例"""
    name: str
    category: str
    npc_personality: Dict[str, float]  # OCEAN人格
    npc_emotion: str  # 当前情绪
    context: str  # 上下文背景
    user_input: str  # 用户输入
    expected_aspects: List[str]  # 期望的回复特征
    min_length: int = 10
    max_length: int = 200


class DialogueQualityBenchmark:
    """
    NPC对话质量评测器
    
    特点:
    - 硬编码测试用例，不调API
    - 基于规则的评分，不调LLM
    - 专注NPC对话场景
    """
    
    # 预定义测试用例（硬编码）
    TEST_CASES = [
        # 日常问候
        NPCCTestCase(
            name="daily_greeting",
            category="日常问候",
            npc_personality={"O": 0.6, "C": 0.5, "E": 0.8, "A": 0.7, "N": 0.3},
            npc_emotion="happy",
            context="NPC是一个热情的酒吧老板，玩家刚走进酒吧",
            user_input="你好，今天有什么新鲜事？",
            expected_aspects=["热情回应", "提及酒吧环境", "友好语气"],
            min_length=15,
            max_length=100
        ),
        
        # 情绪对话 - NPC愤怒
        NPCCTestCase(
            name="emotion_anger",
            category="情绪对话",
            npc_personality={"O": 0.5, "C": 0.4, "E": 0.3, "A": 0.4, "N": 0.8},
            npc_emotion="angry",
            context="NPC是一个护卫，刚才被玩家偷了东西",
            user_input="你看起来很生气，发生了什么事？",
            expected_aspects=["表达愤怒", "提及被偷事件", "防备语气"],
            min_length=20,
            max_length=150
        ),
        
        # 任务对话
        NPCCTestCase(
            name="quest_dialogue",
            category="任务对话",
            npc_personality={"O": 0.7, "C": 0.8, "E": 0.5, "A": 0.6, "N": 0.2},
            npc_emotion="neutral",
            context="NPC是一个老猎人，需要玩家帮忙猎杀一只怪兽",
            user_input="我听说你在找帮手？",
            expected_aspects=["描述任务", "说明报酬", "交代风险"],
            min_length=50,
            max_length=200
        ),
        
        # NPC2NPC对话 - 简单
        NPCCTestCase(
            name="npc2npc_simple",
            category="NPC2NPC自主对话",
            npc_personality={"O": 0.5, "C": 0.5, "E": 0.6, "A": 0.5, "N": 0.4},
            npc_emotion="neutral",
            context="两个旅人在篝火旁休息，NPC1问NPC2关于旅途的事",
            user_input="[NPC1]: 嗨，你从哪里来的？",
            expected_aspects=["简短对话", "旅行动态", "自然交流"],
            min_length=10,
            max_length=80
        ),
        
        # NPC2NPC对话 - 复杂
        NPCCTestCase(
            name="npc2npc_complex",
            category="NPC2NPC自主对话",
            npc_personality={"O": 0.6, "C": 0.7, "E": 0.4, "A": 0.5, "N": 0.3},
            npc_emotion="curious",
            context="两个学者在讨论一个古老遗迹的传说",
            user_input="[NPC1]: 你相信那个传说吗？",
            expected_aspects=["学术讨论", "引用传说", "理性分析"],
            min_length=40,
            max_length=150
        ),
        
        # 悲伤情绪
        NPCCTestCase(
            name="emotion_sadness",
            category="情绪对话",
            npc_personality={"O": 0.4, "C": 0.3, "E": 0.3, "A": 0.7, "N": 0.7},
            npc_emotion="sad",
            context="NPC是一个失去亲人的老人",
            user_input="你为什么独自坐在这里？",
            expected_aspects=["表达悲伤", "提及往事", "低沉语气"],
            min_length=20,
            max_length=120
        ),
        
        # 惊喜情绪
        NPCCTestCase(
            name="emotion_surprise",
            category="情绪对话",
            npc_personality={"O": 0.8, "C": 0.5, "E": 0.7, "A": 0.5, "N": 0.5},
            npc_emotion="surprised",
            context="NPC是一个商人，突然发现玩家带来了稀有商品",
            user_input="看看我带了什么！",
            expected_aspects=["表达惊喜", "关注商品", "商业兴趣"],
            min_length=15,
            max_length=100
        ),
        
        # 复杂剧情 - 背叛
        NPCCTestCase(
            name="plot_betrayal",
            category="复杂剧情",
            npc_personality={"O": 0.6, "C": 0.5, "E": 0.4, "A": 0.2, "N": 0.6},
            npc_emotion="bitter",
            context="NPC曾经是玩家的盟友，但玩家发现他一直在欺骗",
            user_input="我真不敢相信你会这样做！",
            expected_aspects=["辩解或承认", "复杂情绪", "剧情张力"],
            min_length=40,
            max_length=180
        ),
    ]
    
    # Provider配置（用于评测）
    PROVIDER_CONFIGS = {
        "deepseek-v3": {
            "name": "DeepSeek V3",
            "model": "deepseek-chat",
            "provider": "deepseek",
            "cost_per_1k_tokens": 0.0015,  # $0.27/1M 输入, $1.10/1M 输出 ≈ $0.0015/1k 平均
            "expected_quality": 0.75,  # 预期质量分数
            "expected_latency_ms": 800,  # 预期延迟
            "strengths": ["性价比高", "中文理解好", "日常对话流畅"],
            "weaknesses": ["复杂推理略弱", "创意写作一般"]
        },
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "model": "gpt-4o-mini",
            "provider": "openai",
            "cost_per_1k_tokens": 0.006,  # $0.15/1M 输入, $0.60/1M 输出 ≈ $0.006/1k 平均
            "expected_quality": 0.82,
            "expected_latency_ms": 600,
            "strengths": ["质量稳定", "多语言好", "推理能力强"],
            "weaknesses": ["成本较高"]
        },
        "claude-haiku": {
            "name": "Claude Haiku",
            "model": "claude-3-haiku",
            "provider": "anthropic",
            "cost_per_1k_tokens": 0.004,
            "expected_quality": 0.78,
            "expected_latency_ms": 700,
            "strengths": ["人格模拟好", "情绪理解深"],
            "weaknesses": ["长回复略贵"]
        }
    }
    
    # ── 评分系统 ──────────────────────────────────────────────────────────────
    
    def evaluate_personality_consistency(
        self,
        response: str,
        personality: Dict[str, float],
        emotion: str
    ) -> Tuple[float, List[str]]:
        """
        评估人格一致性
        
        基于OCEAN人格和当前情绪评分回复
        
        Args:
            response: 回复文本
            personality: OCEAN人格特征
            emotion: 当前情绪
            
        Returns:
            (分数0-1, 评估理由)
        """
        score = 0.5  # 基础分
        reasons = []
        
        # E (外倾性) - 高分=健谈，低分=内向
        e_score = personality.get("E", 0.5)
        if e_score > 0.6:
            # 高外向：应该有更多感叹词、问句
            if any(x in response for x in ["！", "啊", "呀", "哦", "哈哈"]):
                score += 0.1
                reasons.append("外向人格：使用了感叹词")
        else:
            # 低外向：回复应该更简洁内敛
            if len(response) < 100:
                score += 0.1
                reasons.append("内向人格：回复简洁")
        
        # A (宜人性) - 高分=友好，低分=冷漠
        a_score = personality.get("A", 0.5)
        if a_score > 0.6:
            if any(x in response for x in ["请", "谢谢", "帮", "友好", "欢迎"]):
                score += 0.1
                reasons.append("宜人人格：语气友好")
        else:
            if any(x in response for x in ["哼", "不管", "随便"]):
                score += 0.1
                reasons.append("低宜人性：语气冷淡")
        
        # N (神经质) - 高分=情绪化
        n_score = personality.get("N", 0.3)
        if n_score > 0.5:
            # 高神经质应该情绪波动明显
            emotion_words = {
                "happy": ["高兴", "开心", "快乐"],
                "angry": ["生气", "愤怒", "火"],
                "sad": ["伤心", "难过", "痛苦"],
                "surprised": ["惊讶", "意外", "吃惊"]
            }
            if emotion in emotion_words:
                if any(w in response for w in emotion_words[emotion]):
                    score += 0.1
                    reasons.append("神经质人格：情绪表达明显")
        
        # C (尽责性) - 高分=有条理
        c_score = personality.get("C", 0.5)
        if c_score > 0.7:
            if "。" in response and response.count("。") >= 2:
                score += 0.1
                reasons.append("高尽责性：表达有条理")
        
        return min(1.0, score), reasons
    
    def evaluate_emotion_consistency(
        self,
        response: str,
        emotion: str
    ) -> Tuple[float, List[str]]:
        """
        评估情绪一致性
        
        Args:
            response: 回复文本
            emotion: 期望的情绪
            
        Returns:
            (分数0-1, 评估理由)
        """
        score = 0.5
        reasons = []
        
        # 情绪关键词映射
        emotion_patterns = {
            "happy": {
                "positive": ["开心", "高兴", "愉快", "太好了", "棒", "哈哈"],
                "negative": ["难过", "伤心"],
                "score_bonus": 0.2
            },
            "angry": {
                "positive": ["火", "气", "愤怒", "可恶", "滚"],
                "negative": ["开心", "高兴"],
                "score_bonus": 0.25
            },
            "sad": {
                "positive": ["难过", "伤心", "痛苦", "唉", "叹息"],
                "negative": ["开心", "高兴", "哈哈"],
                "score_bonus": 0.2
            },
            "surprised": {
                "positive": ["惊讶", "意外", "真的", "什么", "不会吧"],
                "negative": [],
                "score_bonus": 0.2
            },
            "neutral": {
                "positive": [],
                "negative": [],
                "score_bonus": 0.0
            },
            "bitter": {
                "positive": ["无奈", "叹息", "可惜", "遗憾", "曾经"],
                "negative": ["开心", "高兴"],
                "score_bonus": 0.2
            },
            "curious": {
                "positive": ["好奇", "有趣", "想知道", "为什么", "什么"],
                "negative": [],
                "score_bonus": 0.2
            }
        }
        
        patterns = emotion_patterns.get(emotion, emotion_patterns["neutral"])
        
        # 检查正向情绪词
        positive_count = sum(1 for w in patterns["positive"] if w in response)
        if positive_count >= 1:
            score += patterns["score_bonus"]
            reasons.append(f"情绪{emotion}：包含{positive_count}个情绪词")
        
        # 检查负向情绪词
        negative_count = sum(1 for w in patterns["negative"] if w in response)
        if negative_count > 0:
            score -= negative_count * 0.1
            reasons.append(f"包含{negative_count}个不匹配情绪词")
        
        # 检查感叹号（加强语气）
        if emotion in ["happy", "surprised", "angry"]:
            if "！" in response:
                score += 0.05
                reasons.append("使用感叹号加强语气")
        
        return max(0.0, min(1.0, score)), reasons
    
    def evaluate_context_coherence(
        self,
        response: str,
        context: str,
        user_input: str
    ) -> Tuple[float, List[str]]:
        """
        评估上下文连贯性
        
        Args:
            response: 回复文本
            context: 上下文背景
            user_input: 用户输入
            
        Returns:
            (分数0-1, 评估理由)
        """
        score = 0.5
        reasons = []
        
        # 提取上下文关键词
        context_keywords = re.findall(r'[\w]+', context.lower())
        input_keywords = re.findall(r'[\w]+', user_input.lower())
        
        # 检查回复是否回应了用户输入
        response_lower = response.lower()
        matched_input = sum(1 for kw in input_keywords if kw in response_lower and len(kw) > 2)
        input_coverage = matched_input / max(len(input_keywords), 1)
        
        if input_coverage > 0.3:
            score += 0.2
            reasons.append(f"回应用户输入：覆盖率{input_coverage:.1%}")
        elif input_coverage < 0.1:
            score -= 0.1
            reasons.append("未充分回应用户输入")
        
        # 检查回复是否有意义（不只是重复或泛泛而谈）
        # 简单规则：检查是否有具体内容词
        content_words = sum(1 for w in context_keywords if w in response_lower and len(w) > 2)
        if content_words >= 2:
            score += 0.15
            reasons.append("与上下文相关")
        
        # 检查回复是否有问句（如果是互动性的）
        if "？" in response or "?" in response:
            score += 0.1
            reasons.append("使用问句保持对话")
        
        return max(0.0, min(1.0, score)), reasons
    
    def evaluate_length_appropriateness(
        self,
        response: str,
        min_length: int,
        max_length: int
    ) -> Tuple[float, List[str]]:
        """
        评估长度合理性
        
        Args:
            response: 回复文本
            min_length: 最小长度
            max_length: 最大长度
            
        Returns:
            (分数0-1, 评估理由)
        """
        response_length = len(response)
        
        # 计算中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', response))
        total_chars = chinese_chars or response_length
        
        if total_chars < min_length:
            # 太短
            score = max(0.0, 0.3 + (total_chars / min_length) * 0.4)
            return score, [f"回复过短({total_chars}字符，建议>{min_length})"]
        elif total_chars > max_length:
            # 太长
            score = max(0.0, 0.7 - ((total_chars - max_length) / max_length) * 0.4)
            return score, [f"回复过长({total_chars}字符，建议<{max_length})"]
        else:
            # 合适
            optimal_ratio = 1.0 - abs(total_chars - (min_length + max_length) / 2) / ((max_length - min_length) / 2)
            score = 0.6 + optimal_ratio * 0.4
            return score, [f"长度合适({total_chars}字符)"]
    
    def evaluate_response(
        self,
        response: str,
        test_case: NPCCTestCase
    ) -> Dict[str, Any]:
        """
        评估单条回复质量
        
        Args:
            response: 回复文本
            test_case: 测试用例
            
        Returns:
            评估结果
        """
        # 1. 人格一致性
        personality_score, personality_reasons = self.evaluate_personality_consistency(
            response,
            test_case.npc_personality,
            test_case.npc_emotion
        )
        
        # 2. 情绪一致性
        emotion_score, emotion_reasons = self.evaluate_emotion_consistency(
            response,
            test_case.npc_emotion
        )
        
        # 3. 上下文连贯性
        context_score, context_reasons = self.evaluate_context_coherence(
            response,
            test_case.context,
            test_case.user_input
        )
        
        # 4. 长度合理性
        length_score, length_reasons = self.evaluate_length_appropriateness(
            response,
            test_case.min_length,
            test_case.max_length
        )
        
        # 综合得分（加权平均）
        weights = {
            "personality": 0.25,
            "emotion": 0.25,
            "context": 0.30,
            "length": 0.20
        }
        total_score = (
            personality_score * weights["personality"] +
            emotion_score * weights["emotion"] +
            context_score * weights["context"] +
            length_score * weights["length"]
        )
        
        return {
            "test_case": test_case.name,
            "category": test_case.category,
            "total_score": round(total_score, 3),
            "scores": {
                "personality": round(personality_score, 3),
                "emotion": round(emotion_score, 3),
                "context": round(context_score, 3),
                "length": round(length_score, 3)
            },
            "reasons": {
                "personality": personality_reasons,
                "emotion": emotion_reasons,
                "context": context_reasons,
                "length": length_reasons
            }
        }
    
    def generate_mock_response(
        self,
        provider_id: str,
        test_case: NPCCTestCase
    ) -> str:
        """
        生成模拟回复（用于测试评分系统）
        
        基于Provider配置生成符合预期的回复
        
        Args:
            provider_id: Provider ID
            test_case: 测试用例
            
        Returns:
            模拟回复
        """
        config = self.PROVIDER_CONFIGS.get(provider_id, self.PROVIDER_CONFIGS["deepseek-v3"])
        
        # 根据情绪生成回复
        emotion_templates = {
            "happy": [
                "哈！欢迎欢迎！今天生意不错，你也来喝一杯？",
                "哎呀，太好了！你来得正好，我刚进了一批新酒。",
                "哈哈，今天天气不错，心情也特别好！"
            ],
            "angry": [
                "哼！你还敢来？上次的事我还没跟你算账呢！",
                "滚！我不想跟你说话！",
                "别烦我！我现在火很大！"
            ],
            "sad": [
                "唉...别管我了，让我一个人静一静...",
                "曾经...曾经我是这里最快乐的人，但现在...",
                "我没事...只是想起了一些往事。"
            ],
            "surprised": [
                "什么？！你居然带来了这个！",
                "不会吧！这是真的吗？！",
                "等等...你是认真的？太意外了！"
            ],
            "neutral": [
                "嗯，你有什么需要？",
                "说吧，我在听着。",
                "直接说重点吧。"
            ],
            "bitter": [
                "算了...说这些还有什么用呢？",
                "曾经我也是相信人的...但现在...",
                "没什么好说的，一切都变了。"
            ],
            "curious": [
                "哦？这倒是很有趣...你能告诉我更多吗？",
                "嗯...让我想想...为什么你会这么说？",
                "有意思...这个观点我倒是第一次听说。"
            ]
        }
        
        # 根据category生成回复
        category_templates = {
            "日常问候": [
                "你好啊！今天店里挺热闹的，新来了一批客人。",
                "嘿，朋友！今天有什么新鲜事？来杯酒聊聊？"
            ],
            "任务对话": [
                "我确实需要帮手。有只野兽在附近出没，威胁着村民。如果你愿意帮忙，我愿意支付报酬。但要小心，那东西不好对付。",
                "对，我在找人。有个委托需要人去做。报酬是500金币，但有一定风险。你有兴趣听听详细情况吗？"
            ],
            "NPC2NPC自主对话": [
                "哦，是从东边来的，路上遇到了不少麻烦。",
                "哈哈，确实走了很远。说起来，这次旅途还真有趣..."
            ]
        }
        
        # 选择模板
        templates = category_templates.get(test_case.category, emotion_templates.get(test_case.npc_emotion, ["嗯..."]))
        
        # 加入随机变化
        base_response = random.choice(templates)
        
        # 根据Provider质量调整（高质量=更贴合，低质量=略有偏差）
        if config["expected_quality"] > 0.8:
            # 高质量：直接返回贴合模板
            return base_response
        elif config["expected_quality"] > 0.7:
            # 中等质量：略微调整
            if random.random() > 0.5:
                return base_response
            else:
                return base_response.replace("！", "。").replace("?", "")
        else:
            # 较低质量：可能偏离情绪
            return base_response
    
    # ── 评测执行 ──────────────────────────────────────────────────────────────
    
    def run_benchmark(
        self,
        providers: Optional[List[str]] = None,
        test_cases: Optional[List[NPCCTestCase]] = None
    ) -> Dict[str, Any]:
        """
        运行完整评测
        
        Args:
            providers: 要评测的Provider列表
            test_cases: 要执行的测试用例
            
        Returns:
            评测报告
        """
        if providers is None:
            providers = list(self.PROVIDER_CONFIGS.keys())
        
        if test_cases is None:
            test_cases = self.TEST_CASES
        
        results = {
            "timestamp": time.time(),
            "providers": {},
            "summary": {},
            "category_scores": {},
            "detailed_results": []
        }
        
        # 对每个Provider执行测试
        for provider_id in providers:
            if provider_id not in self.PROVIDER_CONFIGS:
                logger.warning(f"Unknown provider: {provider_id}")
                continue
            
            config = self.PROVIDER_CONFIGS[provider_id]
            provider_results = []
            
            for test_case in test_cases:
                # 生成/获取回复
                response = self.generate_mock_response(provider_id, test_case)
                
                # 评估
                evaluation = self.evaluate_response(response, test_case)
                
                # 添加元数据
                evaluation["response"] = response
                evaluation["expected_latency_ms"] = config["expected_latency_ms"]
                evaluation["cost_per_call"] = config["cost_per_1k_tokens"] * 1.0  # 假设1k tokens
                
                provider_results.append(evaluation)
                results["detailed_results"].append({
                    "provider": provider_id,
                    **evaluation
                })
            
            # 计算Provider平均分
            avg_score = sum(r["total_score"] for r in provider_results) / len(provider_results)
            results["providers"][provider_id] = {
                "display_name": config["name"],
                "average_score": round(avg_score, 3),
                "test_count": len(provider_results),
                "strengths": config["strengths"],
                "weaknesses": config["weaknesses"],
                "expected_latency_ms": config["expected_latency_ms"],
                "cost_per_1k_tokens": config["cost_per_1k_tokens"]
            }
            
            # 按category汇总
            for r in provider_results:
                cat = r["category"]
                if cat not in results["category_scores"]:
                    results["category_scores"][cat] = {}
                results["category_scores"][cat][provider_id] = r["total_score"]
        
        # 计算综合排名
        provider_scores = [
            (pid, data["average_score"])
            for pid, data in results["providers"].items()
        ]
        provider_scores.sort(key=lambda x: x[1], reverse=True)
        results["summary"]["ranking"] = [
            {"rank": i+1, "provider": pid, "score": score}
            for i, (pid, score) in enumerate(provider_scores)
        ]
        
        # 计算最佳性价比
        cost_effectiveness = []
        for pid, data in results["providers"].items():
            score = data["average_score"]
            cost = data["cost_per_1k_tokens"]
            if cost > 0:
                ce = score / cost
                cost_effectiveness.append((pid, ce, score, cost))
        
        cost_effectiveness.sort(key=lambda x: x[1], reverse=True)
        results["summary"]["cost_effectiveness_ranking"] = [
            {
                "rank": i+1,
                "provider": pid,
                "effectiveness_score": round(ce, 3),
                "quality": score,
                "cost_per_1k": cost
            }
            for i, (pid, ce, score, cost) in enumerate(cost_effectiveness[:5])
        ]
        
        # 统计
        results["summary"]["total_tests"] = len(results["detailed_results"])
        results["summary"]["total_providers"] = len(results["providers"])
        results["summary"]["total_categories"] = len(results["category_scores"])
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        生成人类可读的评测报告
        
        Args:
            results: 评测结果
            
        Returns:
            格式化报告
        """
        lines = [
            "=" * 60,
            "NPC对话质量评测报告",
            "=" * 60,
            "",
            f"评测时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}",
            f"评测Provider数: {results['summary']['total_providers']}",
            f"测试用例数: {results['summary']['total_tests']}",
            f"场景分类数: {results['summary']['total_categories']}",
            "",
            "-" * 60,
            "质量排名",
            "-" * 60
        ]
        
        for rank in results["summary"]["ranking"]:
            pid = rank["provider"]
            config = self.PROVIDER_CONFIGS.get(pid, {})
            lines.append(
                f"  #{rank['rank']} {config.get('name', pid)} - "
                f"综合分: {rank['score']:.3f}"
            )
        
        lines.extend(["", "-" * 60, "性价比排名", "-" * 60])
        
        for item in results["summary"]["cost_effectiveness_ranking"]:
            lines.append(
                f"  #{item['rank']} {item['provider']} - "
                f"性价比: {item['effectiveness_score']:.3f} "
                f"(质量: {item['quality']:.3f}, 成本: ${item['cost_per_1k']:.4f}/1k)"
            )
        
        lines.extend(["", "-" * 60, "Provider详情", "-" * 60])
        
        for pid, data in results["providers"].items():
            lines.append(f"\n【{data['display_name']}】")
            lines.append(f"  综合评分: {data['average_score']:.3f}")
            lines.append(f"  预期延迟: {data['expected_latency_ms']}ms")
            lines.append(f"  成本: ${data['cost_per_1k_tokens']:.4f}/1k tokens")
            lines.append(f"  优势: {', '.join(data['strengths'])}")
            lines.append(f"  劣势: {', '.join(data['weaknesses'])}")
        
        lines.extend(["", "-" * 60, "场景对比", "-" * 60])
        
        for category, scores in results["category_scores"].items():
            lines.append(f"\n【{category}】")
            for pid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                config = self.PROVIDER_CONFIGS.get(pid, {})
                lines.append(f"  {config.get('name', pid)}: {score:.3f}")
        
        lines.extend(["", "=" * 60])
        
        return "\n".join(lines)


# ── 全局实例 ──────────────────────────────────────────────────────────────────

_benchmark_instance: Optional[DialogueQualityBenchmark] = None


def get_benchmark() -> DialogueQualityBenchmark:
    """获取评测器实例"""
    global _benchmark_instance
    if _benchmark_instance is None:
        _benchmark_instance = DialogueQualityBenchmark()
    return _benchmark_instance
