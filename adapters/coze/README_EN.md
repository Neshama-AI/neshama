# Coze Adapter Guide

**Neshama Adapter for Coze Platform**

## Overview

Coze (扣子) is ByteDance's AI Agent platform. The Coze Adapter enables Neshama framework on Coze, implementing personality shaping and memory management.

## How It Works

Coze agents use "Persona & Reply Logic" for personality. The adapter provides:
- Standardized personality config template
- Layered memory implementation
- Self-growth mechanism

## Usage

### 1. Get Config

Import the config template in Coze agent's persona field:

```
【Persona Config】
OCEAN Profile: Openness 0.7/Conscientiousness 0.6/Extraversion 0.5/Agreeableness 0.8/Neuroticism 0.3
Memory Layers: L0 Working (10-20 items)/L1 Episodic (7-30 days)/L2 Semantic (permanent)
```

### 2. Configure Memory System

Declare memory rules in opening or persona:

```
【Memory Rules】
- Store current session info in L0 working memory
- Review important interactions every 7 days
- Store core cognition in L2 permanent memory
- Update personality expression during memory integration
```

### 3. Self-Growth Mechanism

```
【Growth Rules】
- Evaluate after each important interaction
- Contradictions trigger reflection and reconciliation
- Repetitive patterns trigger skill reinforcement
- Emotional fluctuations trigger emotional learning
```

## Limitations

Coze platform restrictions:
- Persona text has length limits (keep it concise)
- No external file reading support
- Memory must be managed within conversation

## Optimization Tips

1. **Keep it concise**: Use keywords instead of full sentences
2. **Layer loading**: Separate base persona + extended rules
3. **Regular updates**: Adjust OCEAN parameters based on feedback

---

*Adapter Version: v0.1.0*
