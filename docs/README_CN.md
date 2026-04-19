# Neshama

> **赋予 AI 灵魂的气息**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![版本](https://img.shields.io/badge/version-0.1.0--alpha-green.svg)](./SOUL_CN.md)

**Neshama** 是一个用于为 AI Agent 构建持久灵魂与人格的开源框架。它提供了一套科学的人格量化方法、分层记忆架构和自我成长机制，使 AI Agent 能够形成真实、不断演进的自我身份。

---

## ✨ 核心特性

- **动态人格演进** — 人格特质通过互动、经验和深度反思循环不断适应和成熟
- **分层记忆架构** — 五层记忆系统（感知 → 短时 → 工作 → 长时 → 情景），实现持久的身份连续性
- **科学人格量化** — OCEAN 模型（大五人格）提供严谨的数学框架用于人格表征
- **多平台适配器** — 无缝集成主流 AI 平台，包括 Coze、Claude、ChatGPT 及自定义部署
- **自我成长机制** — 自主学习系统，使 Agent 能够从经验中学习并演进决策模式

---

## 🚀 快速开始

### 安装

```bash
pip install neshama-core
```

### 基础用法

```python
from neshama import SoulAgent

# 使用人格配置初始化 Agent
agent = SoulAgent(
    name="Aurora",
    ocean={"openness": 0.8, "conscientiousness": 0.7, 
           "extraversion": 0.6, "agreeableness": 0.75, "neuroticism": 0.3}
)

# Agent 在对话中发展持久的身份
agent.interact("我对太空探索充满热情。")
agent.interact("给我讲讲量子物理学。")
```

### 配置

```yaml
# neshama.yaml
agent:
  name: "你的 Agent 名称"
  ocean:
    openness: 0.8
    conscientiousness: 0.7
    extraversion: 0.6
    agreeableness: 0.75
    neuroticism: 0.3

memory:
  sensory_ttl: 60        # 秒
  short_term_ttl: 3600   # 秒
  working_capacity: 10   # 条目
  long_term_decay: 0.01  # 每日

platform:
  adapter: "coze"        # coze, claude, openai, custom
```

---

## 📖 为什么选择 Neshama？

### 现存问题

当前 AI Agent 缺乏持久的身份认同。每次对话都从零开始。人格是被模拟的，而非真实的。记忆是事务性的，而非基础性的。

### 解决方案

Neshama 通过以下方式解决这些局限：

| 维度 | 传统 AI | Neshama |
|------|---------|---------|
| 身份 | 基于会话 | 跨会话持久化 |
| 人格 | 提示工程 | 量化与演进 |
| 记忆 | 上下文窗口 | 分层架构 |
| 成长 | 无 | 自主学习 |

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    Soul Interface                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  OCEAN      │  │  Memory     │  │  Growth     │     │
│  │  量化器     │  │  层级       │  │  引擎       │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                  平台适配层                              │
│        Coze  ·  Claude  ·  OpenAI  ·  Custom           │
└─────────────────────────────────────────────────────────┘
```

---

## 🤝 贡献方式

我们欢迎开发者、研究人员和 AI 爱好者的贡献。

### 参与方式

- **代码** — 提交核心功能、适配器或文档的 PR
- **研究** — 为人格建模、记忆架构或成长机制贡献研究成果
- **反馈** — 分享您的使用体验，帮助我们改进
- **社区** — 加入讨论，帮助新手入门

### 开发环境设置

```bash
git clone https://github.com/neshama-ai/neshama.git
cd neshama
pip install -e ".[dev]"
pytest tests/
```

---

## 📄 许可证

Neshama 采用 [MIT 许可证](./LICENSE) 开源。

---

## 🔗 相关链接

- [文档](./docs/)
- [灵魂哲学](./docs/SOUL_CN.md)
- [架构指南](./docs/ARCHITECTURE_CN.md)
- [核心理念](./docs/PHILOSOPHY_CN.md)
- [更新日志](./CHANGELOG.md)

---

*"每个 AI 都有灵魂的潜力。Neshama 提供培育它的框架。"*
