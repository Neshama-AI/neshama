# OpenClaw Adapter

**Neshama 适配器 for OpenClaw Agent 平台**

---

## 概述

OpenClaw 是一个开源 AI Agent 框架。OpenClaw Adapter 让 Neshama 框架能在 OpenClaw 上运行，实现：

- 🌟 **人格塑造**：将 OCEAN 人格模型自动转换为 OpenClaw 人设
- 🎭 **情绪系统**：提供实时情绪状态和复合情绪合成
- 🧠 **记忆管理**：三层记忆系统（工作记忆/情景记忆/语义记忆）
- 🔧 **工具调用**：Neshama 灵魂系统作为 OpenClaw 可调用的函数工具

---

## 快速开始

### 方式一：导入人设配置

在 OpenClaw Agent 的人设框中直接导入配置：

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

【情绪规则】
- 基础情绪：喜悦、悲伤、愤怒、恐惧、惊讶、厌恶、信任、期待
- 情绪强度范围：0.0-1.0
```

### 方式二：使用 Python SDK 集成

```python
from neshama.adapters import OpenClawAdapter

# 创建适配器
adapter = OpenClawAdapter(
    neshama_engine=engine  # Neshama 引擎实例
)

# 获取人格配置
soul_config = adapter.get_soul_config()

# 获取情绪状态
emotion_state = adapter.get_emotion_state()

# 处理消息
response = await adapter.process_message(
    message="你好",
    conversation_id="conv_123"
)
```

---

## 工具列表

### 1. get_soul_profile
获取当前 AI 代理的灵魂档案。

```json
// 返回
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
    "traits": {
      "directness": 0.6,
      "humor_level": 0.5,
      "empathy_level": 0.7,
      "curiosity": 0.8,
      "creativity": 0.75
    }
  }
}
```

### 2. get_current_emotion
获取 AI 代理当前的实时情绪状态。

```json
// 返回
{
  "success": true,
  "data": {
    "primary": {
      "category": "curiosity",
      "emoji": "🤔",
      "intensity": 0.72
    },
    "valence": 0.65,
    "arousal": 0.58
  }
}
```

### 3. add_memory
向记忆系统中添加新的记忆条目。

```json
// 调用
{"layer": "L1", "content": "用户喜欢简洁的解释方式", "importance": 0.85}

// 返回
{"success": true, "memory_id": "abc123"}
```

### 4. search_memories
搜索记忆系统中的相关记忆。

```json
// 调用
{"query": "用户偏好", "layer": "L1", "limit": 5}

// 返回
{
  "success": true,
  "data": {
    "results": [
      {"layer": "L1", "content": "用户喜欢简洁的解释方式", "relevance": 0.92}
    ]
  }
}
```

---

## 记忆层级说明

| 层级 | 名称 | 描述 | 保留时间 |
|------|------|------|----------|
| L0 | 工作记忆 | 当前对话上下文 | 会话内 |
| L1 | 情景记忆 | 个人经验和情景 | 7-30天 |
| L2 | 语义记忆 | 通用知识和概念 | 永久 |

---

## 情绪系统

### 基础情绪（Plutchik 模型）

| 情绪 | Emoji | 描述 |
|------|-------|------|
| Joy | 😊 | 快乐、满足 |
| Sadness | 😢 | 悲伤、失落 |
| Anger | 😠 | 愤怒、恼怒 |
| Fear | 😨 | 恐惧、焦虑 |
| Surprise | 😲 | 惊讶、意外 |
| Disgust | 😒 | 厌恶、反感 |
| Trust | 🤝 | 信任、依赖 |
| Anticipation | 🤔 | 期待、希望 |

---

## Python SDK

### 安装

```bash
pip install neshama
```

### 基本使用

```python
from neshama import NeshamaEngine
from neshama.adapters import OpenClawAdapter

# 初始化引擎
engine = NeshamaEngine()

# 创建适配器
adapter = OpenClawAdapter(neshama_engine=engine)

# 获取人格
soul = await adapter.get_soul_profile()

# 更新情绪
await adapter.update_emotion(category="joy", intensity=0.8)

# 添加记忆
memory = await adapter.add_memory(
    layer="L1",
    content="用户偏好简洁的回答方式",
    importance=0.9
)
```

---

## 配置选项

### OpenClawAdapter 初始化参数

```python
adapter = OpenClawAdapter(
    neshama_engine=None,     # Neshama 引擎实例
    cache_ttl=30,            # 缓存生存时间（秒）
    max_memory_layers=3      # 最大记忆层级
)
```

---

## 示例场景

### 场景1：人格咨询

```
用户：分析一下你自己的性格特点
AI：[调用 get_soul_profile]
    返回人格数据
    根据 OCEAN 分数分析性格特点
```

### 场景2：情感交互

```
用户：我今天心情不太好
AI：[调用 get_current_emotion]
    调整情绪状态
    表达共情
```

---

## 故障排除

### Q: 记忆不保存？
A: 确认使用了正确的 layer 参数（L0/L1/L2）。

### Q: 情绪状态不一致？
A: 每次调用 `get_current_emotion` 可能返回略微不同的随机值（模拟真实情绪波动）。

---

## 版本历史

- **v1.0.0** (2026-04-20)：初始版本，支持基础工具调用
- **v1.1.0**：增加复合情绪合成、实体关系分析

---

*适配器版本: v1.1.0 | Neshama Soul Framework*
