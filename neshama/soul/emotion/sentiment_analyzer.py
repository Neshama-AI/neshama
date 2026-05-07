# Soul Layer - Sentiment Analyzer
"""
SentimentAnalyzer - Lightweight rule-based sentiment analysis.

Detects implicit emotional expressions that keyword matching misses.
No external ML dependencies (no numpy/sklearn/etc).

Features:
- Extended Chinese emotion lexicon (50+ words per base emotion)
- Irony/implicit expression pattern detection
- Intensity modifier detection ("太...了" = amplify, "有点" = diminish)
- Sentence pattern analysis (rhetorical questions → anger/scorn, exclamations → strong emotion)
"""

import re
from typing import Dict, List, Optional, Tuple


# Extended emotion lexicon: base_emotion -> list of related words/phrases
EMOTION_LEXICON: Dict[str, List[str]] = {
    "anger": [
        "愤怒", "生气", "恼火", "暴怒", "发怒", "火大", "怒火", "气愤",
        "气死", "怒", "愤", "恼", "恨", "怨", "怒骂", "怒斥", "怒视",
        "可恶", "混蛋", "混账", "卑鄙", "无耻", "岂有此理", "不可理喻",
        "你配吗", "凭什么", "谁给你的脸", "不要脸", "找死", "找打",
        "欠揍", "不知好歹", "得寸进尺", "忍无可忍", "忍够了", "够了",
        "闭嘴", "滚", "滚开", "滚出去", "少废话", "废话少说",
        "别烦我", "烦死了", "讨厌死了", "气死我了", "气死我了",
        "无耻之徒", "卑鄙小人", "畜生", "该死", "去死",
        "你算什么东西", "你以为你是谁", "不自量力", "不知天高地厚",
        "欺人太甚", "太过分了", "太欺负人了", "敢惹我",
    ],
    "sadness": [
        "悲伤", "难过", "伤心", "哀伤", "悲痛", "忧伤", "忧郁", "凄凉",
        "悲", "哀", "凄", "愁", "惘", "怅", "黯然", "伤神", "心碎",
        "心酸", "心寒", "心痛", "心伤", "伤感", "感伤", "痛苦", "苦闷",
        "郁闷", "沮丧", "颓丧", "消沉", "失落", "绝望", "无助",
        "孤独", "寂寞", "凄惨", "凄苦", "悲惨", "凄厉", "凄美",
        "泪", "哭", "泣", "呜咽", "哽咽", "泪流满面", "泪如雨下",
        "痛哭", "嚎啕", "哭泣", "垂泪", "含泪", "落泪", "流泪",
        "心灰意冷", "万念俱灰", "悲痛欲绝", "痛不欲生",
        "黯然神伤", "黯然泪下", "心如刀割", "心如死灰",
    ],
    "fear": [
        "害怕", "恐惧", "惊恐", "恐慌", "畏惧", "惧怕", "胆怯", "心虚",
        "怕", "惧", "怯", "惊", "骇", "慌", "惶", "忐忑",
        "战栗", "颤抖", "发抖", "哆嗦", "惊慌", "慌张", "慌乱",
        "惶恐", "惶惶", "惊骇", "骇然", "骇人", "不寒而栗",
        "毛骨悚然", "心惊肉跳", "胆战心惊", "提心吊胆",
        "惊弓之鸟", "草木皆兵", "如临深渊", "如履薄冰",
        "吓", "惊吓", "恐吓", "威吓", "威胁", "恐", "可怕",
        "恐怖", "恐怖的", "吓人", "吓死", "不敢", "千万别",
        "危险", "小心", "当心", "注意安全", "快逃", "快跑",
    ],
    "joy": [
        "高兴", "开心", "快乐", "欢乐", "愉快", "欣喜", "喜悦", "欢喜",
        "乐", "喜", "欢", "笑", "悦", "畅", "甜", "美",
        "兴奋", "激动", "振奋", "雀跃", "欢呼", "喝彩", "鼓掌",
        "幸福", "甜蜜", "温馨", "美好", "美妙", "灿烂", "辉煌",
        "满意", "满足", "欣慰", "宽慰", "安心", "踏实", "放心",
        "哈哈", "嘻嘻", "呵呵", "太棒了", "太好了", "好极了",
        "棒极了", "妙极了", "太妙了", "真棒", "真好", "厉害",
        "优秀", "出色", "精彩", "完美", "了不起", "了不起",
        "耶", "好耶", "好呀", "太开心了", "乐翻天", "乐不可支",
    ],
    "surprise": [
        "惊讶", "惊奇", "意外", "吃惊", "诧异", "愕然", "惊呆", "震惊",
        "惊", "呀", "啊", "哇", "天哪", "我的天", "不会吧",
        "不可思议", "难以置信", "万万没想到", "出乎意料",
        "没想到", "想不到", "不敢相信", "怎么可能", "怎么会",
        "真的吗", "真假", "什么", "啥", "啥情况", "怎么回事",
        "目瞪口呆", "瞠目结舌", "匪夷所思", "大跌眼镜",
        "居然", "竟然", "怎料", "谁知", "偏偏", "岂料",
        "惊呆了", "吓了一跳", "大吃一惊", "大惊失色",
    ],
    "disgust": [
        "恶心", "厌恶", "反感", "鄙视", "嫌弃", "讨厌", "烦人", "作呕",
        "恶心死了", "令人作呕", "太恶心了", "受不了", "看不下去了",
        "无聊", "乏味", "俗气", "低俗", "下流", "肮脏", "龌龊",
        "不屑", "嗤之以鼻", "不齿", "鄙视", "藐视", "轻蔑",
        "鄙视你", "看不起", "瞧不起", "看不上", "不配",
        "恶心到我了", "倒胃口", "败兴", "扫兴", "大煞风景",
    ],
    "trust": [
        "相信", "信任", "信赖", "放心", "安心", "依靠", "依赖", "托付",
        "真诚", "诚实", "可靠", "靠谱", "守信", "一诺千金",
        "朋友", "伙伴", "战友", "兄弟", "姐妹", "家人", "亲人",
        "交给我", "包在我身上", "我保证", "我发誓", "一定",
        "没问题", "可以的", "信得过", "靠得住", "值得信赖",
        "坦诚", "坦白", "忠厚", "老实", "正直", "善良",
    ],
    "anticipation": [
        "期待", "期望", "盼望", "渴望", "希望", "盼望", "等候", "等待",
        "盼", "望", "期", "等", "候", "想", "盼着", "等着",
        "迫不及待", "急不可待", "翘首以盼", "望眼欲穿",
        "快点", "赶紧", "赶快", "马上", "什么时候", "多久",
        "希望", "但愿", "要是", "如果可以", "好想", "真想",
        "好奇", "想知道", "了解一下", "探个究竟", "一探究竟",
        "兴奋地", "激动地", "期待地", "热切地", "殷切地",
    ],
}

# Intensity modifiers: patterns that amplify or diminish emotion
INTENSITY_MODIFIERS: List[Tuple[re.Pattern, float]] = [
    # Amplifiers (multiplier > 1)
    (re.compile(r"太[^\s]{1,6}了"), 1.5),         # 太...了
    (re.compile(r"特别[^\s]{1,4}"), 1.4),          # 特别...
    (re.compile(r"非常[^\s]{1,4}"), 1.4),          # 非常...
    (re.compile(r"极其[^\s]{1,4}"), 1.6),          # 极其...
    (re.compile(r"超级[^\s]{1,4}"), 1.5),          # 超级...
    (re.compile(r"真的[^\s]{1,4}"), 1.3),          # 真的...
    (re.compile(r"真是[^\s]{1,4}"), 1.3),          # 真是...
    (re.compile(r"十分[^\s]{1,4}"), 1.3),          # 十分...
    (re.compile(r"无比[^\s]{1,4}"), 1.5),          # 无比...
    (re.compile(r"死我了"), 1.6),                   # ...死我了
    (re.compile(r"极了"), 1.5),                     # ...极了
    (re.compile(r"要命"), 1.4),                     # ...要命
    (re.compile(r"得要死"), 1.5),                   # ...得要死
    (re.compile(r"不得了"), 1.4),                   # ...不得了
    # Diminishers (multiplier < 1)
    (re.compile(r"有点[^\s]{1,4}"), 0.6),          # 有点...
    (re.compile(r"稍微[^\s]{1,4}"), 0.5),          # 稍微...
    (re.compile(r"略微[^\s]{1,4}"), 0.5),          # 略微...
    (re.compile(r"有些[^\s]{1,4}"), 0.6),          # 有些...
    (re.compile(r"一点[^\s]{0,2}"), 0.5),          # 一点...
]

# Irony/sarcasm patterns: rhetorical question + negation = likely sarcasm
IRONY_PATTERNS: List[re.Pattern] = [
    re.compile(r"难道.{0,10}吗[？?]"),            # 难道...吗？
    re.compile(r"不是.{0,10}吗[？?]"),             # 不是...吗？
    re.compile(r"你觉得.{0,6}可能吗[？?]"),         # 你觉得...可能吗？
    re.compile(r"你也配[？?]?$"),                    # 你也配？
    re.compile(r"谁.{0,6}你了[？?]"),              # 谁...你了？
    re.compile(r"什么.{0,6}啊[？?]"),              # 什么...啊？
]

# Sentence pattern indicators
_EXCLAMATION_PATTERN = re.compile(r'[！!]{1,3}\s*$')
_QUESTION_PATTERN = re.compile(r'[？?]{1,3}\s*$')
_RHETORICAL_QUESTION_PATTERN = re.compile(r'[？?]{2,}\s*$')


class SentimentResult:
    """Result of sentiment analysis."""
    
    def __init__(
        self,
        scores: Dict[str, float],
        dominant_emotion: str,
        is_irony: bool = False,
        intensity_multiplier: float = 1.0,
    ):
        self.scores = scores
        self.dominant_emotion = dominant_emotion
        self.is_irony = is_irony
        self.intensity_multiplier = intensity_multiplier
    
    def to_dict(self) -> Dict:
        return {
            "scores": {k: round(v, 4) for k, v in self.scores.items()},
            "dominant_emotion": self.dominant_emotion,
            "is_irony": self.is_irony,
            "intensity_multiplier": round(self.intensity_multiplier, 2),
        }


class SentimentAnalyzer:
    """
    Lightweight rule-based sentiment analyzer.
    
    No external ML dependencies. Uses extended lexicon + pattern rules.
    
    Example:
        >>> analyzer = SentimentAnalyzer()
        >>> result = analyzer.analyze("你配吗？")
        >>> print(result.dominant_emotion)  # "anger"
        >>> result = analyzer.analyze("太好了！")
        >>> print(result.dominant_emotion)  # "joy"
    """
    
    def __init__(self):
        """Initialize the sentiment analyzer."""
        # Build reverse lookup: word -> (emotion, base_score)
        self._word_to_emotion: Dict[str, List[Tuple[str, float]]] = {}
        for emotion, words in EMOTION_LEXICON.items():
            for word in words:
                if word not in self._word_to_emotion:
                    self._word_to_emotion[word] = []
                # Longer words get higher base score (more specific)
                base_score = min(0.3 + len(word) * 0.05, 0.8)
                self._word_to_emotion[word].append((emotion, base_score))
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze text for sentiment/emotion content.
        
        Args:
            text: Input text to analyze
            
        Returns:
            SentimentResult with emotion scores and metadata
        """
        if not text or not text.strip():
            return SentimentResult(
                scores={},
                dominant_emotion="neutral",
            )
        
        text = text.strip()
        
        # Step 1: Lexicon-based scoring
        scores = self._lexicon_score(text)
        
        # Step 2: Detect intensity modifiers
        intensity = self._detect_intensity(text)
        
        # Step 3: Apply intensity to all scores
        for emotion in scores:
            scores[emotion] *= intensity
        
        # Step 4: Detect irony
        is_irony = self._detect_irony(text)
        
        # Step 5: Sentence pattern adjustments
        scores = self._apply_sentence_patterns(text, scores)
        
        # Step 6: If irony detected, boost anger/disgust
        if is_irony:
            scores["anger"] = scores.get("anger", 0.0) + 0.3
            scores["disgust"] = scores.get("disgust", 0.0) + 0.2
        
        # Clamp all scores
        scores = {k: max(0.0, min(1.0, v)) for k, v in scores.items()}
        
        # Find dominant emotion
        if scores:
            dominant = max(scores.items(), key=lambda x: x[1])
            dominant_emotion = dominant[0] if dominant[1] > 0.05 else "neutral"
        else:
            dominant_emotion = "neutral"
        
        return SentimentResult(
            scores=scores,
            dominant_emotion=dominant_emotion,
            is_irony=is_irony,
            intensity_multiplier=intensity,
        )
    
    def _lexicon_score(self, text: str) -> Dict[str, float]:
        """Score text using emotion lexicon."""
        scores: Dict[str, float] = {}
        
        for word, emotion_scores in self._word_to_emotion.items():
            if word in text:
                for emotion, base_score in emotion_scores:
                    if emotion not in scores:
                        scores[emotion] = 0.0
                    # Use max rather than sum to avoid over-accumulation
                    scores[emotion] = max(scores[emotion], base_score)
        
        return scores
    
    def _detect_intensity(self, text: str) -> float:
        """Detect intensity modifiers in text."""
        multiplier = 1.0
        
        for pattern, mod in INTENSITY_MODIFIERS:
            if pattern.search(text):
                if mod > 1.0:
                    multiplier = max(multiplier, mod)
                else:
                    # Diminisher only applies if no amplifier found
                    if multiplier <= 1.0:
                        multiplier = min(multiplier, mod)
        
        return multiplier
    
    def _detect_irony(self, text: str) -> bool:
        """Detect irony/sarcasm patterns."""
        for pattern in IRONY_PATTERNS:
            if pattern.search(text):
                return True
        return False
    
    def _apply_sentence_patterns(
        self, text: str, scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Adjust scores based on sentence patterns."""
        # Exclamation marks amplify existing emotions
        if _EXCLAMATION_PATTERN.search(text):
            for emotion in scores:
                scores[emotion] *= 1.3
        
        # Rhetorical questions (multiple question marks) boost anger/disgust
        if _RHETORICAL_QUESTION_PATTERN.search(text):
            scores["anger"] = scores.get("anger", 0.0) + 0.2
            scores["disgust"] = scores.get("disgust", 0.0) + 0.1
        
        # Single question mark - mild anticipation
        elif _QUESTION_PATTERN.search(text):
            scores["anticipation"] = scores.get("anticipation", 0.0) + 0.05
        
        return scores
