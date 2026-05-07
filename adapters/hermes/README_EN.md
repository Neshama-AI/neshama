# Hermes Adapter

**Neshama Adapter for Nous Research Hermes Agent**

## Overview

Hermes Agent is an open-source self-improving AI agent framework built by AI research lab Nous Research (80k+ GitHub Stars). It features a built-in learning loop that creates skills from experience, builds user models, and maintains cross-session memory.

MiniMax's MaxHermes is a cloud product built on Hermes Agent.

## Usage

### 1. Get Config

Import Neshama persona in Hermes's SOUL.md:

```
【Persona Config】
OCEAN Profile: Openness 0.7/Conscientiousness 0.6/Extraversion 0.5/Agreeableness 0.8/Neuroticism 0.3
```

### 2. Memory System

Hermes has built-in memory. Neshama adds personality layer:

```
【Persona Rules】
- L0 Working: Current session behavior drive
- L1 Episodic: 7-30 day interaction patterns
- L2 Semantic: Core identity & personality solidification
- Personality Update: OCEAN evolves with interactions
```

### 3. Integration with Native Features

- Hermes auto-creates Skills → Neshama defines skill style
- Hermes cross-session memory → Neshama provides personality continuity
- Hermes user modeling → Neshama provides OCEAN quantified personality

---

*Adapter Version: v0.1.0*
