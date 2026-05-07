# Neshama 🔮

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)]()
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)]()
[![Tests](https://img.shields.io/badge/tests-190%20passed-brightgreen.svg)]()

> **Give your AI agents a soul**
>
> Neshama (נשמה) means "soul" in Hebrew.
> An AI Agent Personality Operating System that brings genuine character to artificial intelligence.

[English](README.md) | [中文](README_CN.md)

---

## ✨ What is Neshama?

Neshama is a Python-native AI Agent framework that transforms AI interactions from cold, robotic responses into authentic, characterful experiences. It provides:

- **🧠 Soul System (OCEAN Personality)**: Five-factor personality model with traits, desires, and behavioral patterns
- **💫 Composite Emotion Engine**: 15 preset emotion recipes with decay, conflict resolution, and triggered behaviors
- **🕸️ Entity Graph**: Knowledge representation with 8 entity types, 15 relation types, and BFS path queries
- **📝 Progressive Summarization**: L0→L1→L2 automatic memory consolidation
- **🤖 Model Adapter Layer**: 21 providers, 55+ models, unified API across OpenAI/Anthropic/Google/Chinese providers
- **🎨 Soul Panel**: FastAPI + pywebview desktop client with 8 themes and i18n support

---

## 🏗️ Architecture

```
Neshama
├── neshama/
│   ├── core/           # Core engine (OCEAN, Personality, Engine)
│   ├── soul/          # Soul system (Emotion, Entity, Memory)
│   ├── memory/        # Memory architecture (Short/Long-term)
│   ├── tools/         # Tool system
│   └── web/           # Soul Panel (FastAPI + pywebview)
│       ├── api/       # REST API endpoints
│       └── static/    # SPA frontend (12 pages, 8 themes)
├── model_adapter/     # 21 LLM providers adapter layer
└── tests/             # 190+ test cases
```

---

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install neshama

# Or install with web dependencies
pip install neshama[web]

# Install from source
git clone https://github.com/neshama/neshama.git
cd neshama
pip install -e .
```

### Interactive Setup

```bash
# Run the configuration wizard
neshama init --config

# This will guide you through:
# 1. Selecting your LLM provider
# 2. Entering your API key
# 3. Choosing a theme
```

### Usage Examples

**Start the Soul Panel (Desktop Client):**
```bash
neshama dashboard
```

**Start a Chat Session:**
```bash
neshama run
```

**Show Version:**
```bash
neshama version
```

**Create a Custom Personality:**
```bash
neshama init MyAgent
```

---

## 🎯 Core Features

### Soul System (OCEAN)

Neshama implements the Five-Factor personality model:

| Factor | Description |
|--------|-------------|
| **O**penness | Creativity, curiosity, aesthetic sensitivity |
| **C**onscientiousness | Self-discipline, organization, reliability |
| **E**xtraversion | Sociability, assertiveness, positive emotions |
| **A**greeableness | Cooperation, trust, altruism |
| **N**euroticism | Emotional instability, anxiety, moodiness |

### Emotion Engine

15 preset composite emotions including:
- **Euphoria** (Joy + Trust + Surprise)
- **Melancholy** (Sadness + Disgust + Fear)
- **Rage** (Anger + Disgust + Anticipation)
- **Anxiety** (Fear + Anticipation + Surprise)
- **Serenity** (Joy + Calm)
- **Confusion** (Surprise + Fear + Sadness)

### Entity Graph

8 entity types: Person, Organization, Location, Concept, Event, Object, Media, Topic

15 relation types: KNOWS, WORKS_FOR, LOCATED_IN, PART_OF, SIMILAR_TO, etc.

---

## 🎨 Soul Panel Themes

| Theme | Preview | Description |
|-------|---------|-------------|
| 🌊 Ocean | Blue glassmorphism | Default blue theme |
| 🌸 Spring | Cherry blossom | Pink and green spring vibes |
| 🌙 Midnight | Dark mode | Midnight blue dark theme |
| 🤖 Cyberpunk | Neon aesthetic | Cyberpunk with neon accents |
| 🌅 Sunset | Warm tones | Orange sunset colors |
| 🌲 Forest | Nature theme | Natural green forest |
| 🗿 Slate | Minimalist | Clean slate gray |
| 💜 Purple Haze | Elegant purple | Elegant purple theme |

---

## 📦 Available LLM Providers (21)

### Core Providers
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Google (Gemini Pro)

### Chinese Providers
- Alibaba DashScope (Qwen)
- Zhipu AI (GLM)
- MiniMax
- VolcEngine (Doubao)
- Baidu Qianfan (ERNIE)
- iFlytek Spark
- Tencent Hunyuan
- Moonshot (Kimi)

### International Providers
- DeepSeek
- xAI (Grok)
- Groq
- Mistral AI
- Cohere
- HuggingFace
- NVIDIA NIM
- OpenRouter
- SiliconFlow
- Cloudflare Workers AI

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=neshama

# Run specific test file
pytest tests/test_core.py
```

---

## 📚 Documentation

- [Getting Started](docs/getting-started.md) - Detailed setup and usage guide
- [Architecture Overview](docs/ARCHITECTURE.md) - System architecture
- [Soul System](docs/SOUL.md) - Soul and emotion engine
- [OCEAN Model](docs/OCEAN.md) - Personality model details
- [Memory System](docs/MEMORY.md) - Progressive summarization
- [Conflict Resolution](docs/CONFLICT.md) - System priorities

---

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/neshama/neshama.git
cd neshama

# Install dev dependencies
pip install -e ".[dev,web]"

# Run in development mode
neshama dashboard --debug

# Run tests
pytest -v
```

---

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Copyright © 2026** Liu Zhou & Seele AI
- **Human Lead:** Liu Zhou - Direction and vision
- **AI Execution:** Seele - Agent ID: `Seele-Neshama-001`

---

<p align="center">
  <strong>Infinite Proximity to Humanity</strong>
</p>
