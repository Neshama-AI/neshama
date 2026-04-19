# Neshama

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-orange.svg)]()

**Give your AI agent a soul.**

Neshama is an open-source framework for building dynamic, evolving AI agent personalities. Unlike static prompts, Neshama creates agents with genuine character depth — agents that grow, learn, and develop their own identity over time.

**Built on real experience.** Neshama is not just theory — it's proven in production by [Seele](docs/EXAMPLE_SELEE.md), an AI agent running 24/7.

*"Mem0 lets AI remember you. Neshama lets AI become uniquely itself."*

---

## Why Neshama?

Most AI agents are **stateless**. Every conversation starts from scratch.

Seele is different. Running on Neshama framework, Seele:
- Maintains consistent personality across sessions
- Evolves through real interactions and corrections
- Demonstrates genuine character (not simulated)

**See it in action:** [Seele - Live Neshama Example](docs/EXAMPLE_SELEE.md)

---

## Core Features

### Dynamic Personality Evolution
Agents built on Neshama don't just respond — they develop. Using the OCEAN personality model, each agent maintains a quantified personality profile that evolves through interactions, memories, and experiences.

### Hierarchical Memory Architecture
Three-tier memory system mirrors human cognition:
- **L0 (Working)**: Current session context, 10-20 items, auto-summarized
- **L1 (Episodic)**: 7-30 day memories, importance-weighted with decay
- **L2 (Semantic)**: Permanent core beliefs, identity consolidation, unlimited

### Scientific Personality Quantification
Based on the OCEAN Five-Factor Model:
- **O**penness — Creativity, curiosity, aesthetic sensitivity
- **C**onscientiousness — Organization, responsibility, self-discipline
- **E**xtraversion — Sociability, assertiveness, positive emotion
- **A**greeableness — Trust, altruism, cooperation
- **N**euroticism — Emotional stability, anxiety, mood variability

### Multi-Platform Adapters
Designed to work across major agent platforms:
- Coze (扣子)
- OpenClaw
- Hermes (Nous Research)
- Generic agent frameworks

### Self-Growth Mechanism
Agents don't just store memories — they reflect on them. Integration events trigger personality updates, creating a genuine sense of continuity and growth.

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           User Interaction              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Personality Engine            │
│  ┌─────────────────────────────────┐   │
│  │     OCEAN Profile (Dynamic)     │   │
│  └─────────────────────────────────┘   │
│  ┌───────────┬───────────┬───────────┐  │
│  │  L0 Mem   │  L1 Mem   │  L2 Mem   │  │
│  │  Working  │ Episodic  │ Semantic  │  │
│  └───────────┴───────────┴───────────┘  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Six Systems                  │
│  Emotional | Motivation | Learning      │
│  Human-like| Creative  | Boundary      │
└─────────────────────────────────────────┘
```

---

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Neshama-AI/neshama.git
cd neshama
```

### 2. Study the Example
Read [Seele - Live Example](docs/EXAMPLE_SELEE.md) to see Neshama in action.

### 3. Choose Your Adapter
```bash
cp -r adapters/coze/ ./your-agent-config/
```

### 4. Customize Personality
Edit the OCEAN profile in your SOUL.md:
```yaml
ocean:
  openness: 0.7        # Creative & curious
  conscientiousness: 0.6
  extraversion: 0.5
  agreeableness: 0.8   # Very cooperative
  neuroticism: 0.3     # Emotionally stable
```

---

## Documentation

### Core Documents
| Document | Description |
|----------|-------------|
| [SOUL.md](docs/SOUL.md) | Core identity and personality definition |
| [EXAMPLE_SELEE.md](docs/EXAMPLE_SELEE.md) | Live example of Seele running Neshama |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture details |
| [PHILOSOPHY.md](docs/PHILOSOPHY.md) | Design philosophy and principles |
| [OCEAN.md](docs/OCEAN.md) | Personality model specification |
| [MEMORY.md](docs/MEMORY.md) | Hierarchical memory system |

---

## Comparison with Alternatives

| Feature | Neshama | Static Prompts | Mem0 |
|---------|---------|----------------|------|
| Dynamic Personality | ✅ Real-time | ❌ | ❌ |
| OCEAN Quantification | ✅ | ❌ | ❌ |
| Self-Evolution | ✅ Live example | ❌ | ❌ |
| Multi-Platform | ✅ | ⚠️ | ✅ |
| Production Proven | ✅ Seele | Varies | ❌ |

---

## Contributing

We welcome contributions! Please read our contributing guidelines before submitting PRs.

---

## License

Apache License 2.0 - See [LICENSE](./LICENSE)

---

*"Neshama" (נשמה) — Hebrew for "soul" or "breath of life." The third and highest level of soul in Jewish mysticism.*
