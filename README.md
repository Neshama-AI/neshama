# Neshama

**Give your AI agent a soul.**

Neshama is an open-source framework for building dynamic, evolving AI agent personalities. Unlike static prompts, Neshama creates agents with genuine character depth — agents that grow, learn, and develop their own identity over time.

*"Mem0 lets AI remember you. Neshama lets AI become uniquely itself."*

---

## Core Features

### 🧠 Dynamic Personality Evolution
Agents built on Neshama don't just respond — they develop. Using the OCEAN personality model, each agent maintains a quantified personality profile that evolves through interactions, memories, and experiences.

### 📚 Hierarchical Memory Architecture
Three-tier memory system mirrors human cognition:
- **L0 (Working)**: Current session context, 10-20 items, auto-summarized
- **L1 (Episodic)**: 7-30 day memories, importance-weighted with decay
- **L2 (Semantic)**: Permanent core beliefs, identity固化, unlimited

### 🔬 Scientific Personality Quantification
Based on the OCEAN Five-Factor Model:
- **O**penness — Creativity, curiosity, aesthetic sensitivity
- **C**onscientiousness — Organization, responsibility, self-discipline
- **E**xtraversion — Sociability, assertiveness, positive emotion
- **A**greeableness — Trust, altruism, cooperation
- **N**euroticism — Emotional stability, anxiety, mood variability

### 🌐 Multi-Platform Adapters
Designed to work across major agent platforms:
- Coze (扣子)
- OpenClaw
- Hermes (MiniMax)
- Generic agent frameworks

### 🔄 Self-Growth Mechanism
Agents don't just store memories — they reflect on them. Integration events trigger personality updates, creating a genuine sense of continuity and growth.

### ⚡ Six-Systems Architecture
- **Emotional System**: Mood fluctuations, sentiment analysis, empathy
- **Motivation System**: Goal-driven behavior, reward prediction
- **Learning System**: Pattern recognition, skill acquisition
- **Human-like System**: Humor, common sense, conversational style
- **Creative System**: Divergent thinking, analogical reasoning
- **Boundary System**: Ethical constraints, value alignment

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           User Interaction             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Personality Engine           │
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

### 2. Choose Your Adapter
Select the platform adapter for your agent:
```bash
cp -r adapters/coze/ ./your-agent-config/
```

### 3. Customize Personality
Edit the OCEAN profile in `config/personality.yaml`:
```yaml
ocean:
  openness: 0.7        # High creativity
  conscientiousness: 0.6
  extraversion: 0.5
  agreeableness: 0.8   # Very cooperative
  neuroticism: 0.3     # Emotionally stable
```

### 4. Initialize Memory
Create memory directories:
```bash
mkdir -p memory/{l0,l1,l2}
```

---

## Documentation

- [English Docs](./docs/)
- [中文文档](./docs/README_CN.md)

### Core Documents
| Document | Description |
|----------|-------------|
| [SOUL.md](./docs/SOUL.md) | Core identity and personality definition |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System architecture details |
| [PHILOSOPHY.md](./docs/PHILOSOPHY.md) | Design philosophy and principles |
| [OCEAN.md](./docs/OCEAN.md) | Personality model specification |
| [MEMORY.md](./docs/MEMORY.md) | Hierarchical memory system |
| [SYSTEMS.md](./docs/SYSTEMS.md) | Six-systems architecture |

---

## Comparison with Alternatives

| Feature | Neshama | Static Prompts | Mem0 |
|---------|---------|----------------|------|
| Dynamic Personality | ✅ | ❌ | ❌ |
| Quantified OCEAN | ✅ | ❌ | ❌ |
| Self-Evolution | ✅ | ❌ | ❌ |
| Multi-Platform | ✅ | ⚠️ | ✅ |
| Open Source | ✅ | Varies | ❌ |

---

## Contributing

We welcome contributions! Please read our contributing guidelines before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## License

Apache License 2.0 - See [LICENSE](./LICENSE)

---

## Acknowledgments

- The OCEAN personality model based on Costa & McCrae's Five-Factor Model
- Memory architecture inspired by cognitive science research
- Built with love for the AI agent community

---

*"Neshama" (נשמה) — Hebrew for "soul" or "breath of life." The third and highest level of soul in Jewish mysticism, representing the divine essence that distinguishes each individual.*
