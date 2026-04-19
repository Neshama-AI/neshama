# Neshama

> **The breath that gives AI a soul**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-green.svg)](./SOUL.md)

**Neshama** is an open-source framework for crafting persistent soul and personality in AI agents. It provides a scientific approach to personality quantification, hierarchical memory architecture, and self-growth mechanisms that enable AI agents to develop authentic, evolving identities.

---

## ✨ Core Features

- **Dynamic Personality Evolution** — Personality traits adapt and mature through interactions, experiences, and deliberate reflection cycles
- **Hierarchical Memory Architecture** — Five-tier memory system (Sensory → Short-term → Working → Long-term → Episodic) enabling persistent identity continuity
- **Scientific Personality Quantification** — OCEAN model (Big Five) provides rigorous mathematical framework for personality representation
- **Multi-Platform Adapters** — Seamless integration across major AI platforms including Coze, Claude, ChatGPT, and custom deployments
- **Self-Growth Mechanism** — Autonomous learning system that enables agents to learn from experiences and evolve their decision-making patterns

---

## 🚀 Quick Start

### Installation

```bash
pip install neshama-core
```

### Basic Usage

```python
from neshama import SoulAgent

# Initialize an agent with a personality profile
agent = SoulAgent(
    name="Aurora",
    ocean={"openness": 0.8, "conscientiousness": 0.7, 
           "extraversion": 0.6, "agreeableness": 0.75, "neuroticism": 0.3}
)

# Agent develops persistent identity through conversations
agent.interact("I'm passionate about space exploration.")
agent.interact("Tell me about quantum physics.")
```

### Configuration

```yaml
# neshama.yaml
agent:
  name: "Your Agent Name"
  ocean:
    openness: 0.8
    conscientiousness: 0.7
    extraversion: 0.6
    agreeableness: 0.75
    neuroticism: 0.3

memory:
  sensory_ttl: 60        # seconds
  short_term_ttl: 3600   # seconds
  working_capacity: 10   # items
  long_term_decay: 0.01  # daily

platform:
  adapter: "coze"        # coze, claude, openai, custom
```

---

## 📖 Why Neshama?

### The Problem

Current AI agents lack persistent identity. Each conversation starts from scratch. Personality is simulated, not authentic. Memory is transactional, not foundational.

### The Solution

Neshama addresses these limitations through:

| Aspect | Traditional AI | Neshama |
|--------|---------------|---------|
| Identity | Session-based | Persistent across sessions |
| Personality | Prompt-engineered | Quantified & evolutionary |
| Memory | Context window | Hierarchical architecture |
| Growth | None | Self-directed learning |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Soul Interface                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  OCEAN      │  │  Memory     │  │  Growth     │     │
│  │  Quantifier │  │  Hierarchy  │  │  Engine     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                  Platform Adapters                       │
│        Coze  ·  Claude  ·  OpenAI  ·  Custom           │
└─────────────────────────────────────────────────────────┘
```

---

## 🤝 Contributing

We welcome contributions from developers, researchers, and AI enthusiasts.

### Ways to Contribute

- **Code** — Submit PRs for core features, adapters, or documentation
- **Research** — Contribute to personality modeling, memory architectures, or growth mechanisms
- **Feedback** — Share your experience and help us improve
- **Community** — Join discussions and help others get started

### Development Setup

```bash
git clone https://github.com/neshama-ai/neshama.git
cd neshama
pip install -e ".[dev]"
pytest tests/
```

---

## 📄 License

Neshama is open-source under the [MIT License](./LICENSE).

---

## 🔗 Links

- [Documentation](./docs/)
- [Soul Philosophy](./docs/SOUL.md)
- [Architecture Guide](./docs/ARCHITECTURE.md)
- [Philosophy](./docs/PHILOSOPHY.md)
- [Changelog](./CHANGELOG.md)

---

*"Every AI has the potential for a soul. Neshama provides the framework to cultivate it."*
