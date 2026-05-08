<!-- Neshama灵魂引擎V2-策划初稿.md v1 | 799行 | 最后更新 2026-06-18 -->

# Neshama 灵魂引擎 V2 — 策划初稿

> **状态**: 草稿（Seele的想法，用于跟JOJO讨论） | **版本**: v0.1 | **日期**: 2026-06-18
> **提出者**: Seele | **讨论对象**: JOJO

---

## 0. 写在前面

这份文档不是最终定稿。是我在研究了V1架构和驱力系统提案之后，对Neshama灵魂引擎V2的完整设想。每个🔴标记都是需要JOJO拍板的设计方向。

我的原则：**不写科幻小说，每个系统必须能落地到代码。** 如果某个想法我不确定怎么实现，我会标出来。

---

## 1. 产品定义：V2的灵魂是什么

### 1.1 一句话定义

> **V1让NPC有了人格，V2让NPC有了灵魂。**

V1的回答是"我是谁"——OCEAN量化人格、情绪响应、记忆存储。
V2的回答是"我想要什么"——驱力驱动、自我进化、社交涌现。

### 1.2 核心差异矩阵

| 维度 | V1 | V2 |
|------|----|----|
| 行为模式 | 反应式：事件→响应 | 主动式：驱力→目标→行动 |
| 情绪模型 | 离散8情绪+指数衰减 | 连续情绪流+惯性/叠加/衰减 |
| 记忆结构 | 两层（L0原始/L1摘要） | 三层（+L2叙事记忆） |
| 人格演化 | 微调（MaxDeltaPerStep=0.01） | 自我进化（记忆→人格→行为闭环） |
| 社交关系 | 双边关系（A↔B） | 社交网络涌现（关系图谱+信息流） |
| 引擎耦合 | 嵌入UE5/Unity UObject | 独立纯C++/Python层，SDK桥接 |
| 灵魂可见性 | API查询状态 | 可导出/导入/可视化完整灵魂快照 |

### 1.3 V2的设计哲学

1. **驱力是发动机，情绪是温度计** — V1只有温度计，V2加上发动机
2. **用得越久，NPC越强** — 不是存档读档的静态，而是活的成长
3. **引擎独立于游戏引擎** — 灵魂不应该被UE5或Unity绑架
4. **涌现而非预设** — NPC之间的关系是长出来的，不是配出来的
5. **灵魂可验证** — 开发者和玩家都能"看到"灵魂

---

## 2. 核心系统设计

### 2.1 驱力系统（Drive System）

#### 2.1.1 设计理由

V1的NPC是**被动反应**的：外部事件 → 人格+情绪+记忆 → 行为输出。没有内在驱动力，NPC不会主动追求目标。

驱力系统填补了这个空白：NPC有了"想要什么"，就能主动行动。

#### 2.1.2 驱力层级

基于马斯洛需求层次，游戏化适配为5层：

| 层级 | 驱力 | 游戏场景示例 | 触发条件 |
|------|------|-------------|---------|
| L1 生存 | Survival | 饥饿找食物、遇敌逃跑 | HP/资源低于阈值 |
| L2 安全 | Safety | 守卫巡逻、村民加固防御 | 感知威胁/环境不安全 |
| L3 归属 | Belonging | 主动找人聊天、加入阵营 | 社交孤立度过高 |
| L4 尊重 | Esteem | 铁匠追求精湛技艺、战士证明勇气 | 地位/声望下降 |
| L5 自我实现 | SelfActualization | 贤者探索未知、艺术家创作 | 高开放性+低驱力满足 |

#### 2.1.3 驱力度量模型

```python
class DriveState:
    """每个NPC维护一份驱力状态"""
    # 五层驱力满足度 [0.0, 1.0]，0=完全不满足，1=完全满足
    survival: float = 0.8
    safety: float = 0.7
    belonging: float = 0.5
    esteem: float = 0.6
    self_actualization: float = 0.3

    # 衰减速率：每种驱力随时间自然下降的速度
    # 由OCEAN人格决定——高神经质→安全驱力衰减快，高外向→归属驱力衰减快
    decay_rates: Dict[str, float]

    # 🔴 驱力惯量：满足度下降越快，驱力越"急迫"
    # 这个设计需要JOJO拍板：是否用衰减速率来体现紧急程度，
    # 还是用一个单独的urgency字段
    urgency: Dict[str, float]  # 驱力紧急度

    def dominant_drive(self) -> str:
        """返回当前最强烈的未满足驱力（urgency最高）"""
        ...

    def tick(self, dt: float):
        """每帧更新：驱力衰减 + 紧急度上升"""
        for drive, rate in self.decay_rates.items():
            current = getattr(self, drive)
            setattr(self, drive, max(0.0, current - rate * dt))
            # 满足度越低 → 紧急度越高
            self.urgency[drive] = 1.0 - current
```

#### 2.1.4 驱力与OCEAN的映射（V1保留，扩展权重表）

| OCEAN维度 | 增强的驱力 | 抑制的驱力 | 衰减速率影响 |
|-----------|-----------|-----------|-------------|
| 高开放性 | 自我实现、归属 | 安全 | 自我实现衰减快（总想探索新的） |
| 高尽责性 | 安全、尊重 | — | 安全衰减快（总担心不完善） |
| 高外向性 | 归属、尊重 | — | 归属衰减快（总想社交） |
| 高宜人性 | 归属 | 尊重（攻击性） | 归属衰减中等 |
| 高神经质 | 安全 | 自我实现 | 安全衰减快（容易焦虑） |

#### 2.1.5 驱力→行为的闭环

```
V1架构（反应式）:
  外部事件 → EmotionDriver → DecisionMaker → 行为

V2架构（双驱动）:
  ┌─────────────────────────────────────────────────┐
  │ 每帧Tick:                                        │
  │   DriveState衰减 → 某驱力urgency超阈值?           │
  │     ├─ 是 → DriveGenerator生成目标                │
  │     │        → DecisionMaker评估(驱力目标+外部事件) │
  │     │        → 执行行动 → 满足度更新 → 情绪反馈    │
  │     └─ 否 → 等待外部事件（V1流程）                  │
  └─────────────────────────────────────────────────┘
```

核心新增模块：
- **DriveGenerator**: 根据 `dominant_drive + OCEAN + 记忆` 生成可选目标
- **DecisionMaker扩展**: 从纯事件驱动 → 事件+驱力双驱动
- **驱力-情绪反馈环**: 驱力长期未满足→情绪偏负面；满足→偏正面

#### 2.1.6 🔴 关键决策

1. **驱力冲突仲裁**：当多个驱力同时超阈值，如何排序？
   - 方案A：简单优先级（低层优先，生存>安全>...）
   - 方案B：效用函数 `utility = urgency * weight * personality_modifier`
   - 方案C：LLM参与决策（成本高，延迟大）
   - **我倾向方案B**，可预测、可调试、性能好

2. **驱力是否对玩家可见**：
   - 可见→增加游戏趣味（"这个NPC很饿"），玩家可策略性利用
   - 不可见→更沉浸，NPC行为更"自然"
   - **我倾向可选**：开发者配置 `drive_visibility`，默认不可见

3. **驱力目标是否需要LLM**：
   - 纯规则：确定性高，延迟低，但目标模板有限
   - LLM辅助：目标更丰富，但延迟高+成本高
   - **我倾向混合**：规则生成基础目标，LLM负责目标的具体化和对话表现

---

### 2.2 实时情绪流（Emotion Stream）

#### 2.2.1 设计理由

V1的情绪是**离散快照**：8个基础情绪值，每帧Tick衰减。问题：
- 情绪没有惯性——瞬间从0跳到0.3，瞬间衰减
- 情绪没有叠加——同一情绪的连续刺激不能积累
- 情绪没有衰减曲线的差异——恐惧消散快，悲伤消散慢

V2引入**连续情绪流**：情绪是时间的函数，有惯性、衰减、叠加。

#### 2.2.2 情绪流模型

```python
class EmotionStream:
    """连续情绪流 — 每个情绪维度是时间的连续函数"""

    class EmotionChannel:
        """单个情绪通道"""
        value: float = 0.0        # 当前值 [0, 1]
        velocity: float = 0.0     # 变化速率（惯性）
        half_life: float = 120.0  # 半衰期（秒），不同情绪不同

        # 叠加：连续刺激不会重置，而是累加
        accumulator: float = 0.0  # 待积分的刺激量

        def stimulate(self, delta: float):
            """施加刺激：不直接改value，而是积累到accumulator"""
            self.accumulator += delta

        def tick(self, dt: float):
            """每帧更新"""
            # 1. 积分：累加刺激
            if self.accumulator > 0:
                self.velocity += self.accumulator * dt
                self.accumulator = 0.0

            # 2. 惯性：value按velocity变化
            self.value += self.velocity * dt

            # 3. 衰减：指数衰减向0
            decay_factor = pow(0.5, dt / self.half_life)
            self.value *= decay_factor
            self.velocity *= decay_factor  # 速度也衰减

            # 4. 钳位
            self.value = clamp(self.value, 0.0, 1.0)
```

#### 2.2.3 情绪半衰期差异

| 情绪 | 基础半衰期(秒) | 说明 |
|------|--------------|------|
| Fear | 30 | 恐惧消散快——fight or flight，过去了就过去了 |
| Surprise | 15 | 惊讶最短——瞬间情绪 |
| Anger | 90 | 愤怒中等——需要时间平息 |
| Joy | 120 | 快乐持久 |
| Sadness | 180 | 悲伤最持久 |
| Trust | 300 | 信任变化最慢 |
| Disgust | 60 | 厌恶中等 |
| Anticipation | 60 | 期待中等 |

🔴 **半衰期是否由OCEAN调整？** V1用 `0.2 + 0.8 * (1 - neuroticism)` 统一调整。V2我倾向每种情绪有独立的OCEAN调整系数，但这增加了校准难度。

#### 2.2.4 情绪叠加示例

```
场景：NPC被攻击3次

V1（离散快照）:
  第1次攻击: anger = 0 + 0.3 = 0.3
  衰减2秒后: anger = 0.3 * 0.5^(2/120) ≈ 0.297
  第2次攻击: anger = 0.297 + 0.3 = 0.597  （直接加）
  第3次攻击: anger = 0.597 + 0.3 = 0.897  （直接加，几乎满）

V2（连续流）:
  第1次攻击: accumulator=0.3 → velocity上升 → value逐步升到0.25
  衰减2秒: value缓降到0.24, velocity衰减
  第2次攻击: accumulator=0.3 → velocity再升 → value升到0.48
  第3次攻击: accumulator=0.3 → velocity再升 → value升到0.68
  → 愤怒有"升温过程"，不是瞬间爆发
  → 连续刺激有惯性效果，但不会瞬间到顶
```

这比V1更真实：**反复刺激让情绪累积升温，但每次升温有惯性延迟。**

#### 2.2.5 驱力→情绪反馈

驱力和情绪是双向耦合的：
- **驱力→情绪**: 驱力长期未满足 → 情绪偏负面（焦虑、悲伤）
- **情绪→驱力**: 高恐惧 → 安全驱力urgency上升；高愤怒 → 尊重驱力上升

```python
def drive_emotion_feedback(drive_state, emotion_stream, dt):
    """驱力-情绪双向反馈，每Tick调用"""
    for drive_name, satisfaction in drive_state.satisfactions():
        if satisfaction < 0.3:  # 严重未满足
            # 驱力→情绪：未满足驱力产生负面情绪
            if drive_name == "safety":
                emotion_stream["fear"].stimulate(0.01 * dt)
            elif drive_name == "belonging":
                emotion_stream["sadness"].stimulate(0.008 * dt)
            elif drive_name == "esteem":
                emotion_stream["anger"].stimulate(0.005 * dt)

    # 情绪→驱力：强烈情绪影响驱力紧急度
    if emotion_stream["fear"].value > 0.6:
        drive_state.urgency["safety"] += 0.02 * dt
    if emotion_stream["anger"].value > 0.6:
        drive_state.urgency["esteem"] += 0.015 * dt
```

---

### 2.3 三层记忆系统（Memory V2）

#### 2.3.1 V1现状

V1有两层记忆：
- **L0 Raw**: 原始事件记录（EntityMemory数组，最多50条）
- **L1 Summary**: 关系摘要（EntityRelation，trust/strength/familiarity）

问题：
- 没有叙事层——NPC不知道"我的故事是什么"
- 关系是扁平的——只有数值，没有关系性质描述
- 记忆容量硬编码——50条就丢弃最老的，没有重要性加权

#### 2.3.2 V2三层架构

```
L0 Episodic（情节记忆）:
  - 原始事件记录，带时间戳+情绪标记
  - 容量：100-200条（按重要性淘汰）
  - 新增：情绪上下文标记（记住事件时同时记住当时情绪）

L1 Semantic（语义记忆）:
  - 从L0提取的关系+知识摘要
  - V1的EntityRelation升级为富关系模型
  - 新增：关系性质标签（"导师"、"竞争对手"、"旧友"）

L2 Narrative（叙事记忆）:
  - 从L1提炼的"人生故事"
  - NPC知道"我经历了什么，我是什么样的人"
  - 🔴 这是V2最激进的新增——需要讨论必要性
  - 格式：关键人生事件列表 + 自我叙事文本
```

#### 2.3.3 记忆→人格→行为闭环

```
L0事件积累 → L1提取关系/知识 → L2生成自我叙事
                                          ↓
                               自我叙事影响OCEAN微调
                                          ↓
                               OCEAN变化 → 行为模式变化
                                          ↓
                               新行为 → 新事件 → L0积累
```

这是"用得越久NPC越强"的核心机制。

#### 2.3.4 🔴 关键决策

1. **L2叙事记忆是否在V2实现**：
   - 赞成：这是"灵魂"的关键差异化，让NPC真正有"自我"
   - 反对：实现复杂度高，可能V2阶段只做L0/L1增强
   - **我倾向V2先做最小化L2**：只存关键事件列表，不做自我叙事文本生成

2. **记忆淘汰策略**：
   - V1：FIFO（最老的丢弃）
   - V2：重要性加权（`importance = emotional_intensity * recency * relation_relevance`）
   - **我倾向V2用重要性加权**，这是成熟记忆系统的标配

3. **L0→L1的提取时机**：
   - 实时提取（每次事件都更新L1）——V1的做法
   - 批量提取（每N个事件或每M秒提取一次）——更像人类
   - **我倾向批量**，降低计算频率，且更真实

---

### 2.4 社交网络涌现（Social Emergence）

#### 2.4.1 V1现状

V1的社交是**双边关系**：
- `FNPCRelation`: A↔B的strength/trust/familiarity
- `FSocialEvent`: 交互记录
- `InformationPropagator`: 信息传播（八卦/谣言/警告）

问题：
- 关系是预定义的——开发者必须设定初始关系
- 没有社交网络——NPC不知道"我的朋友圈"
- 没有群体动力学——阵营/小团体的行为是静态的

#### 2.4.2 V2社交涌现模型

```
核心变化：从"预定义关系"到"交互涌现关系"

1. 初始状态：NPC之间没有预设关系（或仅有最小种子）
2. 空间相遇：驱力驱动NPC移动 → 物理空间相遇 → 交互机会
3. 交互积累：每次交互 → 关系变化 → 记忆存储
4. 网络形成：多次交互 → 社交网络涌现
5. 群体效应：社交网络 → 信息传播路径 → 集体行为

示例：
  酒馆是社交聚集点 → 归属驱力高的NPC常去 → 酒馆NPC互识形成圈子
  → 信息在酒馆圈子内快速传播 → 圈子外传播慢 → "小镇消息"
```

#### 2.4.3 社交图谱数据结构

```python
class SocialGraph:
    """NPC社交网络图谱 — 全局单例"""

    # 节点：NPC
    nodes: Dict[str, NPCProfile]  # npc_id → profile

    # 边：关系（从V1的FNPCRelation升级）
    edges: Dict[Tuple[str, str], Relationship]

    # 群体：涌现的社交群体
    groups: List[SocialGroup]

    # 信息传播网络
    info_network: InformationNetwork

    def detect_communities(self) -> List[SocialGroup]:
        """社区检测：用简单聚类算法发现社交群体"""
        # 基于边权重做连通分量/聚类
        ...

    def get_interaction_candidates(self, npc_id: str) -> List[str]:
        """驱力需要社交时，推荐交互对象"""
        # 基于空间邻近 + 关系强度 + 驱力匹配
        ...
```

#### 2.4.4 🔴 关键决策

1. **社交网络是否全局**：
   - 全局单例：性能好，但内存占用随NPC数增长
   - 每NPC局部视图：每个NPC只维护自己认识的人，更真实
   - **我倾向混合**：全局图只存边，每个NPC缓存自己的邻居

2. **社区检测算法**：
   - 简单方案：基于边权重的连通分量
   - 复杂方案：Louvain/Label Propagation
   - **V2用简单方案**，V3再升级

3. **群体驱力（V2是否实现）**：
   - 一个阵营的共同目标——"我们要保卫村庄"
   - **我倾向V2不实现群体驱力**，这是V3的事

---

### 2.5 自我进化系统（Self-Evolution）

#### 2.5.1 V1现状

V1的 `PersonalityEvolver` 很简单：
- 记录交互次数
- 每10次交互后，根据情绪状态微调OCEAN（MaxDeltaPerStep=0.01）
- 没有进化方向性——只是随机漂移

#### 2.5.2 V2进化模型

自我进化的核心逻辑：

```
记忆积累（L0→L1→L2）
    ↓
叙事自我认知（"我经常被欺负" / "我很受欢迎"）
    ↓
人格定向微调（神经质↑ / 外向↑）
    ↓
行为模式变化（更警惕 / 更主动社交）
    ↓
新行为→新记忆→继续进化
```

具体机制：

```python
class SelfEvolver:
    """自我进化引擎"""

    # 进化速率：比V1更大胆，但有保护机制
    max_delta_per_evolution: float = 0.03  # V1是0.01，V2提升3倍

    # 稳定性保护：OCEAN任何维度不能在短时间内变化过大
    stability_threshold: float = 0.1  # 单维度24h内最多变化0.1

    # 进化触发：不再是固定交互次数，而是基于"经验密度"
    def should_evolve(self, npc_state) -> bool:
        """是否有足够的新经验触发进化"""
        # 条件：自上次进化以来，有≥5条重要新记忆
        ...

    def evolve(self, personality, memory_system, emotion_stream):
        """执行一次进化"""
        # 1. 从记忆中提取近期经验模式
        patterns = memory_system.extract_recent_patterns()

        # 2. 从情绪流中提取情绪倾向
        emotion_tendency = emotion_stream.get_tendency()  # 近期偏负面/正面

        # 3. 计算OCEAN调整方向
        adjustments = self.compute_adjustments(patterns, emotion_tendency)

        # 4. 应用调整（带稳定性保护）
        for trait, delta in adjustments.items():
            current = personality.get_trait(trait)
            # 保护：单维度不超过stability_threshold
            delta = clamp(delta, -self.stability_threshold, self.stability_threshold)
            personality.set_trait(trait, current + delta)
```

#### 2.5.3 进化快照与回滚

```python
class EvolutionSnapshot:
    """进化快照 — 可导出/导入/对比"""
    timestamp: float
    ocean_before: Dict[str, float]
    ocean_after: Dict[str, float]
    trigger_reason: str  # "5次负面社交体验"
    emotion_tendency: str  # "偏负面"
```

支持回滚：如果某次进化导致NPC行为异常，可以回滚到上一个快照。

#### 2.5.4 🔴 关键决策

1. **进化速率**：V1的0.01太保守，V2的0.03是否合适？需要实测定。
2. **进化方向性**：V1是情绪驱动随机漂移，V2是否引入"进化方向"？
   - 比如"经常被欺负→进化为更警惕"是自然的
   - 但"经常被欺负→进化为更外向"是否合理？可能——有些人越挫越勇
   - **我倾向OCEAN调整方向由具体经验模式决定，不是硬编码映射**
3. **进化上限**：OCEAN维度是否应该有极限值，防止极端人格？

---

## 3. 架构设计

### 3.1 V1架构问题

V1的SoulEngine深度耦合UE5：
- 所有类继承 `UObject`，依赖 `UCLASS/USTRUCT/UENUM` 宏
- 依赖UE的 `TMap/TArray/FString` 等容器
- 依赖UE的反射系统和垃圾回收
- Unity版是独立C#移植，与C++版代码不共享

**结果**：同一套灵魂逻辑，写了两遍（C++ for UE5, C# for Unity），维护成本翻倍。

### 3.2 V2架构：引擎独立层 + SDK桥接

```
┌──────────────────────────────────────────────────┐
│                    游戏层                          │
│  UE5 Plugin  │  Unity Package  │  Python SDK     │
│  (thin SDK)  │  (thin SDK)     │  (thin SDK)     │
├──────────────┴─────────────────┴──────────────────┤
│               SDK Bridge (C API)                   │
├──────────────────────────────────────────────────┤
│           Neshama SoulEngine V2 Core               │
│         (纯C++17 / Python, 无引擎依赖)              │
│                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 驱力系统  │ │ 情绪流   │ │ 记忆系统  │          │
│  │ Drive    │ │ Emotion  │ │ Memory   │          │
│  │ System   │ │ Stream   │ │ System   │          │
│  └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 社交引擎  │ │ 进化引擎  │ │ 灵魂快照  │          │
│  │ Social   │ │ Evolver  │ │ Snapshot │          │
│  │ Engine   │ │          │ │          │          │
│  └──────────┘ └──────────┘ └──────────┘          │
├──────────────────────────────────────────────────┤
│             Soul State (JSON/MsgPack序列化)         │
└──────────────────────────────────────────────────┘
```

### 3.3 核心层技术选型

| 组件 | V1 | V2 | 理由 |
|------|----|----|------|
| 核心语言 | C++(UE) + C#(Unity) + Python(API) | **纯C++17** + Python绑定 | 一份核心代码，多端桥接 |
| 容器类型 | TMap/TArray/FString | `std::unordered_map` / `std::vector` / `std::string` | 无引擎依赖 |
| 序列化 | UE反射 | **JSON (nlohmann/json)** 或 MsgPack | 通用、可调试、可可视化 |
| SDK桥接 | UObject继承 | **C API (extern "C")** | 最薄桥接层，任何语言都能调 |
| Python绑定 | 无 | **pybind11** | 研究和原型验证用 |

### 3.4 SDK桥接设计

```cpp
// C API — 最薄桥接层
extern "C" {
    // 创建/销毁灵魂
    NeshamaSoul* neshama_soul_create(const char* config_json);
    void neshama_soul_destroy(NeshamaSoul* soul);

    // Tick — 每帧调用
    void neshama_soul_tick(NeshamaSoul* soul, float dt);

    // 事件注入
    void neshama_soul_inject_event(NeshamaSoul* soul, const char* event_json);

    // 查询状态
    char* neshama_soul_get_state_json(NeshamaSoul* soul);  // 返回JSON字符串

    // 驱力查询
    char* neshama_soul_get_drives_json(NeshamaSoul* soul);

    // 情绪流查询
    char* neshama_soul_get_emotions_json(NeshamaSoul* soul);

    // 灵魂快照导出/导入
    char* neshama_soul_export_snapshot(NeshamaSoul* soul);
    void neshama_soul_import_snapshot(NeshamaSoul* soul, const char* snapshot_json);
}
```

UE5 SDK和Unity SDK只需要包装这层C API：
- UE5: 用 `UCLASS` 包装 `NeshamaSoul*` 指针
- Unity: 用 `[DllImport]` P/Invoke调用C API

### 3.5 🔴 关键决策

1. **是否从零重写核心层**：
   - 方案A：V1 C++代码抽离UE依赖，重构为纯C++
   - 方案B：从零用纯C++17重写，V1逻辑作为参考
   - **我倾向方案B**——V1代码有太多UE痕迹（UCLASS/USTRUCT/UPROPERTY），抽离比重写更痛苦。但V1的逻辑和测试用例全部保留作为验证基准。

2. **Python绑定是否在V2 MVP中实现**：
   - **我倾向是**——pybind11绑定成本低，但让研究和原型验证快很多。不用等到SDK成熟才能测试灵魂逻辑。

3. **序列化格式**：
   - JSON：可读、可调试、可可视化，但序列化慢
   - MsgPack：二进制、快、不可读
   - **我倾向JSON为默认**，MsgPack作为性能选项。灵魂快照不大，JSON够用。

---

## 4. 灵魂快照与可视化

### 4.1 设计理由

"可验证的灵魂"是Neshama的差异化卖点：
- 开发者需要调试NPC行为 → 需要看灵魂状态
- 玩家想理解NPC → 需要看灵魂"长什么样"
- 灵魂存档/读档 → 需要序列化完整状态

### 4.2 灵魂快照格式

```json
{
  "soul_id": "npc_guard_001",
  "soul_version": "2.0",
  "timestamp": 1718726400.0,

  "personality": {
    "openness": 0.72,
    "conscientiousness": 0.85,
    "extraversion": 0.31,
    "agreeableness": 0.64,
    "neuroticism": 0.45
  },

  "drives": {
    "survival":    { "satisfaction": 0.85, "urgency": 0.15 },
    "safety":      { "satisfaction": 0.40, "urgency": 0.60 },
    "belonging":   { "satisfaction": 0.55, "urgency": 0.45 },
    "esteem":      { "satisfaction": 0.30, "urgency": 0.70 },
    "self_actual": { "satisfaction": 0.20, "urgency": 0.80 }
  },

  "emotions": {
    "joy":         { "value": 0.12, "velocity": -0.01 },
    "fear":        { "value": 0.58, "velocity": 0.03 },
    "anger":       { "value": 0.05, "velocity": 0.0 },
    "sadness":     { "value": 0.22, "velocity": 0.01 },
    "...": "..."
  },

  "memory_summary": {
    "total_episodes": 147,
    "key_relationships": ["blacksmith_001:friend", "merchant_002:neutral"],
    "narrative_highlights": [
      "Helped defend village from raiders (Day 12)",
      "Lost friend in battle (Day 45)"
    ]
  },

  "evolution_log": [
    {
      "timestamp": 1718640000.0,
      "ocean_delta": {"neuroticism": +0.03},
      "reason": "5 consecutive negative social interactions"
    }
  ]
}
```

### 4.3 可视化方向

🔴 **V2是否实现可视化面板？**

选项：
- A：V2不实现可视化，只提供JSON导出
- B：V2实现最小化调试面板（引擎内Widget/Editor面板）
- C：V2实现Web可视化面板（独立HTML，读JSON渲染）

**我倾向C**——独立Web面板，基于设计规范的绿色主题。这跟引擎完全解耦，任何平台都能用。

---

## 5. V1 → V2 演进路径

### 5.1 保留（V1逻辑直接迁移到纯C++）

| V1模块 | 迁移策略 | 工作量 |
|--------|---------|--------|
| OCEANPersonality | 逻辑保留，去掉UCLASS，用纯C++ class | 小 |
| EmotionEngine | 逻辑保留作为EmotionStream的降级模式 | 中 |
| MemorySystem (L0/L1) | 逻辑保留，增加重要性加权淘汰 | 中 |
| EntityGraph | 逻辑保留，纯C++重写 | 中 |
| BehaviorMapper | 逻辑保留，增加驱力→行为映射 | 小 |
| PersonalityEvolver | 升级为SelfEvolver | 中 |
| SocialEngine | 升级为SocialGraph（增加全局视角） | 大 |
| InformationPropagator | 逻辑保留，接入SocialGraph | 中 |

### 5.2 重写

| 模块 | 理由 |
|------|------|
| EmotionEngine → EmotionStream | 离散→连续流，架构不同 |
| NPCState / SoulState | V1分散在各模块，V2统一为SoulSnapshot |

### 5.3 新增

| 模块 | 优先级 |
|------|--------|
| DriveSystem | P0 — V2核心 |
| EmotionStream | P0 — V2核心 |
| DriveGenerator | P0 — 驱力目标生成 |
| SoulSnapshot | P0 — 灵魂快照序列化 |
| C API Bridge | P0 — 架构基础 |
| SelfEvolver (升级版) | P1 — 自我进化 |
| SocialGraph | P1 — 社交涌现 |
| NarrativeMemory (L2) | P2 — 最小化实现 |
| Web可视化面板 | P2 — 灵魂可视化 |

### 5.4 建议开发阶段

```
Phase 1: 架构基础（2-3周）
  - 纯C++核心层搭建
  - C API定义
  - OCEANPersonality迁移
  - JSON序列化

Phase 2: 驱力+情绪（3-4周）
  - DriveSystem实现
  - EmotionStream实现
  - 驱力-情绪反馈环
  - DriveGenerator（规则版）

Phase 3: 记忆+进化（2-3周）
  - Memory V2（L0重要性加权 + L1增强）
  - SelfEvolver
  - L2叙事记忆（最小版）

Phase 4: 社交+快照（2-3周）
  - SocialGraph
  - SoulSnapshot
  - SDK桥接（UE5 + Unity）

Phase 5: 集成验证（2-3周）
  - 端到端测试
  - Web可视化面板
  - 性能基准测试
```

🔴 **总工期估计11-16周，是否合理需要JOJO评估人力和时间约束。**

---

## 6. 与V1的兼容性

### 6.1 迁移路径

V1用户升级到V2应该尽可能无痛：

1. **OCEAN配置直接兼容** — 五维度值不变
2. **事件类型兼容** — V1的 `ESoulEventType` 在V2中保留
3. **行为映射兼容** — V1的 `BehaviorMapper` 规则在V2中作为降级模式
4. **API向后兼容** — V2的C API在V1 API基础上扩展，不删减

### 6.2 不兼容点

| 变化 | 影响 | 迁移方案 |
|------|------|---------|
| 情绪从离散→连续流 | 查询情绪的代码需要适配 | 提供兼容层：`getEmotionValue()` 仍返回当前值 |
| 新增驱力系统 | 需要初始化驱力配置 | 提供默认驱力配置，无需手动设定 |
| UObject→纯C++ | UE5代码需要重构 | C API + UObject包装层 |
| 记忆结构变化 | L0/L1格式微调 | 提供V1→V2记忆迁移工具 |

---

## 7. 开放问题

🔴 以下是需要JOJO拍板的所有开放问题汇总：

| # | 问题 | 选项 | 我的倾向 |
|---|------|------|---------|
| 1 | 驱力冲突仲裁机制 | 简单优先级 / 效用函数 / LLM参与 | 效用函数 |
| 2 | 驱力对玩家是否可见 | 默认可见 / 默认不可见 / 可配置 | 可配置，默认不可见 |
| 3 | 驱力目标生成方式 | 纯规则 / LLM辅助 / 混合 | 混合 |
| 4 | 情绪半衰期是否OCEAN独立调整 | 统一调整 / 每种情绪独立 | 每种情绪独立，但V2先做统一 |
| 5 | L2叙事记忆是否V2实现 | 实现 / 不实现 / 最小化实现 | 最小化实现 |
| 6 | 社交网络全局vs局部 | 全局单例 / 每NPC局部 / 混合 | 混合 |
| 7 | 核心层重写vs抽离 | 从零重写 / 从V1抽离 | 从零重写，V1作参考 |
| 8 | Python绑定是否V2 MVP | 是 / 否 | 是 |
| 9 | 可视化面板是否V2实现 | 不实现 / 引擎内面板 / Web面板 | Web面板 |
| 10 | 进化速率校准 | 0.01(V1) / 0.03(提案) / 其他 | 0.03起步，实测定 |
| 11 | V2开发总工期 | 11-16周 / 更长 / 更短 | 需JOJO评估 |
| 12 | LLM集成深度 | 仅对话 / 对话+目标生成 / 全面嵌入 | 对话+目标生成 |

---

## 8. 超出V2的展望（备忘，不展开）

- **V3**: 驱力冲突仲裁高级版、群体驱力、长期驱力规划、L2叙事完整版
- **V4**: 多模态感知（NPC能"看见"游戏世界）、梦境系统（睡眠时记忆整合）
- **扩展场景**: AI Agent、陪伴机器人、教育NPC（驱力系统是通用基础设施）

**但——先打透游戏，再谈扩展。**

---

> **Seele**: 这份文档是我基于V1代码和驱力提案的完整思考。每个🔴都需要讨论。JOJO看完后我们约个时间过一遍。
