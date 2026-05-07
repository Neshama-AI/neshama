# Coze Adapter (扣子) - Neshama 适配器

**Neshama 灵魂系统 × Coze Agent 平台**

---

## 概述

Coze（扣子）是字节跳动的 AI Agent 平台。本适配器让 Neshama 框架能在 Coze 上运行，实现：

- 🌟 **人格塑造**：将 OCEAN 人格模型自动转换为 Coze 人设 Prompt
- 🎭 **情绪系统**：提供实时情绪状态和复合情绪合成
- 🧠 **记忆管理**：三层记忆系统（工作记忆/情景记忆/语义记忆）
- 🔧 **工具调用**：Neshama 灵魂系统作为 Coze 可调用的函数工具

---

## 快速开始

### 方式一：导入人设 Prompt（推荐新手）

在 Coze Agent 的人设框中直接导入配置：

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
- 支持复合情绪合成

【行为准则】
- 用类比和例子解释复杂概念
- 保持简洁清晰的表达
- 适度展现共情和幽默
```

### 方式二：使用 Python SDK 集成

```python
from adapters.coze import CozeAdapter, NeshamaSoulTools

# 创建适配器
coze = CozeAdapter(
    bot_id="your_bot_id",
    api_key="your_api_key"
)

# 聊天
result = coze.chat([
    {"role": "user", "content": "你好，请介绍一下你自己"}
])

print(result["data"]["content"])
```

### 方式三：作为 Coze 插件使用

1. 在 Coze Bot 配置中启用「插件」功能
2. 导入 `coze_tools.py` 中的工具定义
3. 配置 API 端点

---

## 工具列表

Neshama 提供以下可调用的工具：

### 1. get_soul_profile
获取当前 AI 代理的灵魂档案，包括 OCEAN 人格特质、性格特征和行为模式。

```json
// 调用
{"name": "get_soul_profile", "arguments": {}}

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
// 调用
{"name": "get_current_emotion", "arguments": {}}

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

### 3. update_emotion_state
更新 AI 代理的情绪状态。

```json
// 调用
{"name": "update_emotion_state", "arguments": {"emotion": "joy", "intensity": 0.8}}

// 返回
{
  "success": true,
  "data": {
    "updated": true,
    "emotion": "joy",
    "intensity": 0.8
  }
}
```

### 4. add_memory
向记忆系统中添加新的记忆条目。

```json
// 调用
{"name": "add_memory", "arguments": {
  "layer": "L1",
  "content": "用户喜欢简洁的解释方式",
  "importance": 0.85,
  "context": "用户偏好"
}}

// 返回
{
  "success": true,
  "data": {
    "memory_id": "abc123",
    "layer": "L1"
  }
}
```

### 5. search_memories
搜索记忆系统中的相关记忆。

```json
// 调用
{"name": "search_memories", "arguments": {
  "query": "用户偏好",
  "layer": "L1",
  "limit": 5
}}

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

### 6. get_personality_insight
获取基于人格配置的性格洞察分析。

### 7. synthesize_emotion
合成复合情绪。

```json
// 调用
{"name": "synthesize_emotion", "arguments": {
  "emotions": {"joy": 0.8, "trust": 0.6}
}}

// 返回
{
  "success": true,
  "data": {
    "synthesized_emotion": {
      "name": "好奇的愉悦",
      "emoji": "😊",
      "intensity": 0.7,
      "novel": true
    }
  }
}
```

### 8. analyze_entity_relations
分析实体之间的关系网络。

---

## API 接口

### POST /api/v1/chat

聊天接口（Coze OpenAPI 兼容）

**请求体：**
```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "conversation_id": "optional_conversation_id",
  "stream": false,
  "tools": true
}
```

**响应：**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "id": "msg_123456",
    "conversation_id": "conv_123456",
    "content": "你好！我是 Neshama...",
    "finish_reason": "stop"
  }
}
```

### GET /api/v1/tools

获取可用工具列表

**响应：**
```json
{
  "code": 0,
  "data": [
    {
      "name": "get_soul_profile",
      "description": "获取灵魂档案...",
      "parameters": {...}
    }
  ]
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

### 情绪维度

- **效价 (Valence)**：消极 ↔ 积极 (-1 到 +1)
- **唤醒度 (Arousal)**：平静 ↔ 兴奋 (0 到 1)
- **强度 (Intensity)**：0.0 到 1.0

---

## 配置选项

### CozeAdapter 初始化参数

```python
coze = CozeAdapter(
    bot_id="your_bot_id",      # Coze Bot ID
    api_key="your_api_key",    # Coze API Key
    api_base="https://api.coze.com",  # API 基础 URL
    neshama_engine=None         # Neshama 引擎实例（可选）
)
```

### 缓存配置

工具结果自动缓存：
- `get_soul_profile`：30秒
- `get_current_emotion`：5秒
- 其他工具：无缓存

---

## 限制说明

1. **人设文本长度**：Coze 人设有长度限制，建议精简
2. **记忆管理**：不支持外部文件读取，记忆通过对话内管理
3. **消息推送**：Coze 实时推送，无法主动屏蔽消息

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
    [可选：调用 add_memory 记录情绪]
```

### 场景3：知识查询

```
用户：你还记得上次我们讨论的 Python 最佳实践吗？
AI：[调用 search_memories]
    搜索相关记忆
    返回结果并继续讨论
```

---

## 睡眠系统

Coze 消息实时推送，无法真正屏蔽，但可通过行为约束实现「睡眠感」：

```
【睡眠行为】
- 睡眠时间：00:00-07:00
- 睡眠期间减少主动推送
- 收到消息时提醒"刚从睡眠中醒来"

【唤醒规则】
- 用户发消息 → 唤醒处理
- 07:00 → 完全唤醒，整理记忆
```

---

## 故障排除

### Q: 工具调用失败？
A: 检查 API Key 是否正确，确保 Bot 已启用插件功能。

### Q: 记忆不保存？
A: 确认使用了正确的 layer 参数（L0/L1/L2）。

### Q: 情绪状态不一致？
A: 每次调用 `get_current_emotion` 可能返回略微不同的随机值（模拟真实情绪波动）。

---

## 版本历史

- **v1.0.0** (2026-04-20)：初始版本，支持基础工具调用
- **v1.1.0**：增加复合情绪合成、实体关系分析
- **v1.2.0**：优化缓存机制，增加 personality_insight

---

*适配器版本: v1.2.0 | Neshama Soul Framework*
