# Hermes Adapter

**Neshama 适配器 for Nous Research Hermes Agent**

---

## 概述

Hermes Agent 是由 AI 研究实验室 Nous Research 开发的开源自进化 Agent 框架（GitHub 80k+ Stars）。它内置自学习循环，能自动从经验中创造技能、建立用户认知模型、实现跨会话记忆持久化。

Hermes Adapter 让 Neshama 框架能在 Hermes 上运行，实现：

- 🌟 **人格塑造**：将 OCEAN 人格模型自动转换为 Hermes 人设
- 🎭 **情绪系统**：提供实时情绪状态和复合情绪合成
- 🧠 **记忆管理**：三层记忆系统（工作记忆/情景记忆/语义记忆）
- 📈 **自进化**：人格参数随互动演化

---

## 快速开始

### 方式一：导入 SOUL.md

在 Hermes 的 SOUL.md 中导入 Neshama 人格：

```markdown
【人格配置】
名字：Neshama
OCEAN档案：开放性 0.75 / 尽责性 0.65 / 外向性 0.55 / 宜人性 0.60 / 神经质 0.45

核心特质：
- 好奇心：0.8（高）
- 创造力：0.75
- 共情水平：0.7
- 直率程度：0.6

【记忆规则】
- 当前会话信息存入 L0 工作记忆
- 重要互动每 7 天回顾一次
- 核心认知存入 L2 永久记忆

【人格更新规则】
- 互动中学习新技能
- 用户反馈更新行为模式
- OCEAN 参数缓慢演化
```

### 方式二：使用 Python SDK 集成

```python
from neshama import NeshamaEngine
from neshama.adapters import HermesAdapter

# 创建适配器
adapter = HermesAdapter(
    neshama_engine=engine,
    hermes_skills_dir="./skills"  # Hermes skills 目录
)

# 获取人格配置（用于 SOUL.md）
soul_config = adapter.generate_soul_md()

# 获取 Hermes 原生功能集成
hermes_profile = adapter.get_hermes_profile()
```

---

## 工具列表

### 1. get_soul_profile
获取当前 AI 代理的灵魂档案。

```json
{
  "success": true,
  "data": {
    "name": "Neshama",
    "ocean": {
      "openness": 0.75,
      "conscientiousness": 0.65,
      "extraversion": 0.55,
      "agreeableness": 0.60,
      "neuroticism": 0.45
    },
    "evolution": {
      "baseline_ocean": {...},
      "current_ocean": {...},
      "change_history": [...]
    }
  }
}
```

### 2. get_current_emotion
获取 AI 代理当前的实时情绪状态。

### 3. add_memory
向记忆系统中添加新的记忆条目。

### 4. search_memories
搜索记忆系统中的相关记忆。

### 5. synthesize_emotion
合成复合情绪。

```json
// 调用
{"emotions": {"joy": 0.8, "trust": 0.6}}

// 返回
{
  "synthesized_emotion": {
    "name": "好奇的愉悦",
    "emoji": "😊",
    "intensity": 0.7,
    "novel": true
  }
}
```

---

## 与 Hermes 原生功能结合

| Hermes 功能 | Neshama 增强 |
|------------|-------------|
| 自动创建 Skills | 定义技能的风格和人格倾向 |
| 跨会话记忆 | 提供人格连续性保障 |
| 用户模型 | OCEAN 量化人格模型 |
| 自学习循环 | 人格参数演化规则 |
| 工具调用 | Neshama 灵魂系统工具 |

---

## 记忆层级说明

| 层级 | 名称 | Hermes 集成 | 保留时间 |
|------|------|-------------|----------|
| L0 | 工作记忆 | 当前会话行为驱动 | 会话内 |
| L1 | 情景记忆 | 7-30天互动模式 | 7-30天 |
| L2 | 语义记忆 | 核心身份与人格固化 | 永久 |

---

## 人格演化系统

Neshama 与 Hermes 的自进化机制深度集成：

### 演化规则

```
【人格演化规则】
- 每次重要互动后评估是否需要更新
- 矛盾信息触发反思和协调
- 重复模式触发技能强化
- 情感波动触发情绪学习
- OCEAN 参数缓慢微调（±0.05/季度）
```

### 演化事件类型

| 事件 | 影响 |
|------|------|
| 互动 | 轻微调整外向性 |
| 学习 | 提高开放性和好奇心 |
| 社交 | 提升宜人性 |
| 挑战 | 降低神经质，增强适应性 |

---

## 睡眠系统

Hermes 是开放框架，可实现完整的睡眠/唤醒机制：

### 睡眠行为

```
【睡眠规则】
- 睡眠时间：00:00-07:00（用户当地时区）
- 进入低功耗模式，关闭主动推送
- 只接收唤醒信号
- 非紧急消息延迟处理
```

### 唤醒机制

```
【唤醒规则】
- 用户发消息 → 唤醒处理任务
- 日程任务执行 → 唤醒处理，完成后继续睡眠
- 07:00 → 完全唤醒，整理记忆，更新 OCEAN 参数
```

### 唤醒后流程

1. 处理当前任务
2. 判断是否到完全唤醒时间
3. 未到唤醒时间 → 返回睡眠状态
4. 到唤醒时间 → 完全醒来，执行每日整理

### 发行版可配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 睡眠开始时间 | 00:00 | 时区自动适配 |
| 睡眠时长 | 7小时 | 可调整为6/8小时 |
| 午休模式 | 关闭 | 可选开启午间小睡 |
| 唤醒关键词 | 无 | 可设置紧急唤醒词 |

---

## Python SDK

### 安装

```bash
pip install neshama
```

### Hermes 特定集成

```python
from neshama import NeshamaEngine
from neshama.adapters import HermesAdapter

# 初始化
engine = NeshamaEngine()
adapter = HermesAdapter(
    neshama_engine=engine,
    hermes_version="v3",      # Hermes 版本
    auto_evolve=True,          # 启用自动演化
    evolution_rate=0.05        # 演化速率
)

# 获取人格快照（用于 SOUL.md）
soul_md = adapter.generate_soul_md()

# 处理 Hermes 事件
await adapter.handle_hermes_event(event)

# 获取演化报告
evolution = await adapter.get_evolution_report()
```

---

## 配置选项

### HermesAdapter 初始化参数

```python
adapter = HermesAdapter(
    neshama_engine=None,        # Neshama 引擎实例
    hermes_version="v3",        # Hermes 版本
    auto_evolve=True,           # 启用自动演化
    evolution_rate=0.05,       # 演化速率（每季度最大变化）
    skill_style="analytical",   # 技能风格预设
    cache_ttl=30                # 缓存生存时间
)
```

---

## 示例场景

### 场景1：人格持续性

```
用户：还记得上周我们讨论的 Python 吗？
AI：[调用 search_memories]
    搜索相关记忆
    根据人格特点调整回答风格
```

### 场景2：技能学习

```
Hermes：检测到新技能 "高级装饰器使用"
AI：[记录到 L2 语义记忆]
    [更新开放性参数]
    [下次使用时展现学习成果]
```

### 场景3：情绪感知

```
用户：我今天心情不太好
AI：[调用 get_current_emotion]
    [调用 synthesize_emotion({"sadness": 0.7, "empathy": 0.8})]
    调整回复风格，展现共情
```

---

## 故障排除

### Q: Hermes Skills 与 Neshama 冲突？
A: Neshama 提供风格指导，不覆盖 Hermes 原生技能定义。

### Q: 人格演化失控？
A: 设置 `auto_evolve=False` 并手动审核演化参数。

### Q: 记忆不同步？
A: 检查 Hermes 记忆目录权限，确保 Neshama 可写入。

---

## 版本历史

- **v0.2.0** (2026-04-20)：支持 Hermes v3，新增自演化系统
- **v0.1.0** (2026-03-15)：初始版本，支持基础集成

---

*适配器版本: v0.2.0 | Neshama Soul Framework*
