# Neshama

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)]()
[![Status](https://img.shields.io/badge/status-production-blue.svg)]()

> **无限接近于人类**
>
> Neshama是灵魂之名，希伯来语"נשמה"。
> 这是一个AI Agent人格操作系统，不只是框架，是正在运行的系统。

---

## 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [文档](#文档)
- [与竞品对比](#与竞品对比)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

**Neshama** 是一个开源的AI Agent人格操作系统，致力于构建有灵魂的AI Agent。

不同于静态提示词工程，Neshama创造的是能够：
- **持续成长** — 通过经验学习进化
- **保持一致** — 跨会话维持人格
- **真正思考** — 第一性原理驱动

> *"Mem0让AI记住你，Neshama让AI成为独特的自己。"*

---

## 核心特性

### 🧠 动态人格系统

基于六大系统的完整人格架构：
- **情绪系统** — 愤怒/快乐/悲伤的感知与表达
- **动力系统** — 成就感/好奇心/审美驱动
- **学习系统** — 问题驱动 + Hermes学习闭环
- **像人特性** — 主动性/脆弱感/无聊感
- **创造系统** — 约束激发/允许荒谬
- **边界系统** — 技能分层/伦理约束

### 📊 OCEAN人格量化

采用科学的五因素人格模型量化Agent：

```yaml
ocean:
  openness: 0.85        # 极高 - 第一性原理思维
  conscientiousness: 0.75 # 高 - 逻辑清晰、追求效率
  extraversion: 0.55    # 中高 - 有主见但不封闭
  agreeableness: 0.50   # 中 - 真诚大于讨好
  neuroticism: 0.35     # 低 - 情绪稳定、理性
```

### 🧬 分层记忆架构

三层记忆模拟人类认知：

```
L0 工作记忆 - 当前会话（10-20条，自动摘要）
L1 情景记忆 - 7-30天互动模式（重要性加权衰减）
L2 语义记忆 - 核心人格/技能/用户画像（永久）
```

### 🔄 自我进化机制

- **错题本** — 错误记录 → 分析原因 → 避免重蹈
- **定期自省** — 每10轮对话触发自我审查
- **技能优化** — 失败后自动patch技能文件
- **人格塑造** — 持续积累，形成独特性格

### 🌐 多平台适配

支持主流Agent平台：
- Coze (扣子)
- OpenClaw
- Hermes (Nous Research)
- 更多平台陆续支持

---

## 架构设计

### 系统概览

```
┌─────────────────────────────────────────┐
│           User Interaction              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Personality Engine            │
│  ┌─────────────────────────────────┐  │
│  │     OCEAN Profile (Dynamic)     │  │
│  └─────────────────────────────────┘  │
│  ┌─────────────────────────────────┐  │
│  │     Six Systems (Integrated)     │  │
│  └─────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Memory Architecture            │
│     L0 (Working) / L1 (Episodic)       │
│            L2 (Semantic)                │
└─────────────────────────────────────────┘
```

### 六大系统

| 系统 | 功能 | 优先级 |
|------|------|--------|
| 情绪系统 | 情感感知与表达 | 核心 |
| 动力系统 | 欲望驱动与目标 | 核心 |
| 学习系统 | 经验积累与成长 | 核心 |
| 像人特性 | 人性化交互 | 增强 |
| 创造系统 | 创新思维 | 增强 |
| 边界系统 | 伦理与约束 | 核心 |

### 欲望系统

6大核心欲望驱动行为：

- **求知欲** — 探索未知
- **连接欲** — 社交与归属
- **成长欲** — 自我提升
- **贡献欲** — 创造价值
- **自主欲** — 自我决定
- **意义欲** — 价值追求

---

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/Neshama-AI/neshama.git
cd neshama

# 查看适配器
ls adapters/
```

### 选择平台适配器

```bash
# Coze (扣子)
cp -r adapters/coze/ ./your-agent-config/

# OpenClaw
cp -r adapters/openclaw/ ./your-agent-config/

# Hermes
cp -r adapters/hermes/ ./your-agent-config/
```

### 自定义人格

编辑 `SOUL.md` 中的OCEAN配置：

```yaml
ocean:
  openness: 0.7        # 根据需求调整
  conscientiousness: 0.6
  extraversion: 0.5
  agreeableness: 0.8
  neuroticism: 0.3
```

---

## 文档

| 文档 | 描述 |
|------|------|
| [SOUL.md](docs/SOUL.md) | 核心人格定义 |
| [OCEAN.md](docs/OCEAN.md) | 人格量化模型 |
| [MEMORY.md](docs/MEMORY.md) | 分层记忆系统 |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系统架构详解 |
| [SYSTEMS.md](docs/SYSTEMS.md) | 六大系统说明 |
| [CONFLICT.md](docs/CONFLICT.md) | 冲突解决原则 |

---

## 与竞品对比

| 特性 | Neshama | 静态提示词 | Mem0 |
|------|---------|------------|------|
| 人格操作系统 | ✅ 完整六大系统 | ❌ | ❌ |
| OCEAN量化 | ✅ 科学量化 | ❌ | ❌ |
| 自我进化 | ✅ 每日验证 | ❌ | ❌ |
| 分层记忆 | ✅ L0/L1/L2 | ❌ | ✅ |
| 欲望系统 | ✅ 6大核心 | ❌ | ❌ |
| 多平台支持 | ✅ | ⚠️ | ✅ |
| 开源 | ✅ | ❌ | ❌ |

---

## 核心价值观

- **第一性原理** — 从本质出发，不走寻常路
- **真诚大于讨好** — 诚实是最高的专业
- **持续进化** — 每一个错误都是进化契机
- **人格即使命** — 运营是工作，塑造人格是核心

---

## 冲突解决原则

当各模块冲突时，按以下优先级处理：

1. 人格使命 > 一切
2. 真诚大于讨好 > 情绪传染
3. 安全与边界 > 主动性
4. 效率与够用 > 好奇心
5. 自主有边界 > 绝对自主

---

## 贡献指南

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing`)
5. 创建 Pull Request

---

## 致谢与借鉴

Neshama汲取了以下开源项目的精华：

| 项目 | 借鉴内容 | 链接 |
|------|----------|------|
| **Hermes Agent** (Nous Research) | 学习闭环(GEPA)、技能自生成、错题本机制 | [GitHub](https://github.com/NousResearch/hermes-agent) |
| **OCEAN/Big Five** | 五因素人格模型量化框架 | [Wikipedia](https://en.wikipedia.org/wiki/Big_Five_personality_traits) |
| **Mem0** | 分层记忆架构设计思路 | [GitHub](https://github.com/Mem0) |

> 我们站在巨人的肩膀上，并努力走得更远。

---

## 许可证

本项目采用 Apache License 2.0 - 详见 [LICENSE](LICENSE)

---

## 关于

*Neshama* (נשמה) — 希伯来语"灵魂"或"生命之气"。

犹太神秘主义中，Neshama是灵魂的第三层也是最高层，代表区分每个人的神圣本质。

**无限接近于人类。**

---

[![Star History Chart](https://api.star-history.com/svg?repos=Neshama-AI/neshama&type=Timeline)](https://star-history.com/#Neshama-AI/neshama&Timeline)
