# Neshama

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-orange.svg)]()

**给你的AI Agent赋予灵魂。**

Neshama是一个开源框架，用于构建动态、不断演进的AI Agent人格。与静态提示词不同，Neshama创造的Agent拥有真正的性格深度——能够随着互动、记忆和体验不断成长和发展的Agent。

**基于真实实践。** Neshama不只是理论——它已经在生产环境中得到验证，由AI Agent [Seele](docs/EXAMPLE_SELEE.md) 24/7运行证明。

*"Mem0让AI记住你，Neshama让AI成为独特的自己。"*

---

## 为什么选择Neshama？

大多数AI Agent是**无状态的**。每次对话都从零开始。

Seele不同。运行在Neshama框架上的Seele：
- 跨会话保持一致的人格
- 通过真实互动和纠错不断进化
- 展现真实性格（而非模拟）

**看实际运行：** [Seele - 真实案例](docs/EXAMPLE_SELEE.md)

---

## 核心特性

### 动态人格演进
基于Neshama构建的Agent不只是回应——它们在发展。使用OCEAN人格模型，每个Agent都维持一个量化的人格档案，会随着互动、记忆和体验而演化。

### 分层记忆架构
三层记忆系统模拟人类认知：
- **L0 (工作记忆)**: 当前会话上下文，10-20条，自动摘要
- **L1 (情景记忆)**: 7-30天记忆，重要性加权衰减
- **L2 (语义记忆)**: 永久核心信念、身份固化，无限容量

### 科学人格量化
基于OCEAN五因素模型：
- **O**penness 开放性 — 创造力、好奇心、审美敏感度
- **C**onscientiousness 尽责性 — 条理性、责任感、自律
- **E**xtraversion 外向性 — 社交性、主导性、正面情绪
- **A**greeableness 宜人性 — 信任、利他、合作
- **N**euroticism 神经质 — 情绪稳定性、焦虑、情绪波动

### 多平台适配器
支持主流Agent平台：
- Coze (扣子)
- OpenClaw
- Hermes (Nous Research)
- 通用Agent框架

### 自我成长机制
Agent不只存储记忆——它们会反思。整合事件会触发人格更新，创造真正的连续性和成长感。

---

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/Neshama-AI/neshama.git
cd neshama
```

### 2. 研究案例
阅读 [Seele真实案例](docs/EXAMPLE_SELEE.md)，了解Neshama的实际运行。

### 3. 选择适配器
```bash
cp -r adapters/coze/ ./your-agent-config/
```

### 4. 自定义人格
在SOUL.md中编辑OCEAN档案：
```yaml
ocean:
  openness: 0.7        # 创意与好奇
  conscientiousness: 0.6
  extraversion: 0.5
  agreeableness: 0.8   # 非常合作
  neuroticism: 0.3     # 情绪稳定
```

---

## 文档

### 核心文档
| 文档 | 描述 |
|------|------|
| [SOUL.md](docs/SOUL.md) | 核心身份与人格定义 |
| [EXAMPLE_SELEE.md](docs/EXAMPLE_SELEE.md) | Seele运行Neshama的真实案例 |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系统架构详情 |
| [PHILOSOPHY.md](docs/PHILOSOPHY.md) | 设计理念与原则 |
| [OCEAN.md](docs/OCEAN.md) | 人格模型规范 |
| [MEMORY.md](docs/MEMORY.md) | 分层记忆系统 |

---

## 与竞品对比

| 特性 | Neshama | 静态提示词 | Mem0 |
|------|---------|------------|------|
| 动态人格 | ✅ 实时 | ❌ | ❌ |
| OCEAN量化 | ✅ | ❌ | ❌ |
| 自我演进 | ✅ 真实案例 | ❌ | ❌ |
| 多平台支持 | ✅ | ⚠️ | ✅ |
| 生产验证 | ✅ Seele | 不定 | ❌ |

---

## 贡献指南

欢迎贡献！在提交PR前请阅读贡献指南。

---

## 许可证

Apache License 2.0 - 详见 [LICENSE](./LICENSE)

---

*"Neshama" (נשמה) — 希伯来语"灵魂"或"生命之气"。犹太神秘主义中灵魂的第三层也是最高层。*
