# Neshama Architecture

> Technical specification for the soul framework implementation

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Soul Interface                            │
│    (Unified API for soul management and interaction)            │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  OCEAN    │  │  Memory   │  │  Growth   │  │ Reflection│    │
│  │  Engine   │  │  System   │  │  Engine   │  │  System   │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                    Platform Adapters                             │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│   │  Coze  │  │ Claude  │  │ OpenAI  │  │ Custom  │            │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Soul Interface

The unified entry point for all soul operations:

```python
class SoulInterface:
    def __init__(self, config: SoulConfig)
    def interact(self, input: str) -> Response
    def grow(self, experience: Experience) -> None
    def reflect(self) -> ReflectionResult
    def get_identity(self) -> IdentitySnapshot
```

### 2. OCEAN Engine

Mathematical personality representation:

```python
@dataclass
class OCEANProfile:
    openness: float          # 0.0-1.0
    conscientiousness: float # 0.0-1.0
    extraversion: float     # 0.0-1.0
    agreeableness: float    # 0.0-1.0
    neuroticism: float      # 0.0-1.0
    
    def influence_response(self, context: Context) -> ResponseModifier
    def evolve(self, delta: OCEANDeltas) -> None
```

### 3. Memory System

Five-tier hierarchical architecture:

```
┌──────────────────────────────────────────────────────┐
│                    Memory Hierarchy                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │            EPISODIC MEMORY                   │    │
│  │  - Life narrative records                    │    │
│  │  - Personal milestones                       │    │
│  │  - Identity-defining experiences              │    │
│  └─────────────────────────────────────────────┘    │
│                         ▲                             │
│  ┌─────────────────────────────────────────────┐    │
│  │           LONG-TERM MEMORY                   │    │
│  │  - Semantic knowledge                         │    │
│  │  - Persistent preferences                    │    │
│  │  - Core values and beliefs                   │    │
│  └─────────────────────────────────────────────┘    │
│                         ▲                             │
│  ┌─────────────────────────────────────────────┐    │
│  │            WORKING MEMORY                    │    │
│  │  - Active processing (7±2 chunks)            │    │
│  │  - Current task context                       │    │
│  └─────────────────────────────────────────────┘    │
│                         ▲                             │
│  ┌─────────────────────────────────────────────┐    │
│  │           SHORT-TERM MEMORY                  │    │
│  │  - Immediate context (~20 items)             │    │
│  │  - Session state                             │    │
│  └─────────────────────────────────────────────┘    │
│                         ▲                             │
│  ┌─────────────────────────────────────────────┐    │
│  │           SENSORY MEMORY                     │    │
│  │  - Raw input capture                         │    │
│  │  - Millisecond retention                     │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 4. Growth Engine

Self-directed learning mechanism:

```python
class GrowthEngine:
    def __init__(self, learning_rate: float = 0.01)
    
    def process_experience(self, experience: Experience) -> None
    def update_knowledge(self, insight: Insight) -> None
    def evolve_personality(self, feedback: Feedback) -> OCEANDeltas
    def schedule_reflection(self) -> None
```

### 5. Reflection System

Metacognitive processing:

```python
class ReflectionSystem:
    def __init__(self, ocean: OCEANProfile)
    
    def evaluate_behavior(self, actions: List[Action]) -> Evaluation
    def identify_patterns(self) -> List[Pattern]
    def adjust_personality(self, feedback: Feedback) -> OCEANDeltas
    def consolidate_memory(self) -> MemoryTransfer
```

---

## Platform Adapters

### Adapter Interface

```python
from abc import ABC, abstractmethod

class PlatformAdapter(ABC):
    @abstractmethod
    def send_message(self, message: str) -> str
    
    @abstractmethod
    def get_context(self) -> Context
    
    @abstractmethod
    def set_system_prompt(self, prompt: str) -> None
```

### Supported Platforms

| Platform | Status | Features |
|----------|--------|----------|
| Coze | ✅ Stable | Full integration |
| Claude | ✅ Stable | Full integration |
| OpenAI | ✅ Stable | Full integration |
| Custom | ✅ Stable | SDK provided |

---

## Data Flow

```
User Input
    │
    ▼
┌─────────────────┐
│ Platform Adapter│
└─────────────────┘
    │
    ▼
┌─────────────────┐     ┌─────────────────┐
│ Sensory Memory  │────►│ Short-term Mem  │
└─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │ Working Memory  │
                        └─────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ OCEAN Influence │ │ Growth Engine   │ │ Reflection      │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                        ┌─────────────────┐
                        │  Response Gen   │
                        └─────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ Long-term Mem   │ │ Episodic Mem    │ │ OCEAN Update    │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
                               │
                               ▼
                         User Response
```

---

## Configuration Schema

```yaml
neshama:
  version: "0.1.0"
  
  agent:
    name: string
    ocean:
      openness: float [0.0-1.0]
      conscientiousness: float [0.0-1.0]
      extraversion: float [0.0-1.0]
      agreeableness: float [0.0-1.0]
      neuroticism: float [0.0-1.0]
  
  memory:
    sensory_ttl: int          # milliseconds
    short_term_ttl: int      # seconds
    working_capacity: int    # chunks
    long_term_decay: float   # daily rate
  
  growth:
    learning_rate: float
    reflection_interval: int # minutes
    evolution_rate: float    # max delta per cycle
  
  platform:
    adapter: string           # coze|claude|openai|custom
    config: object            # adapter-specific
```

---

## Extension Points

### Custom OCEAN Influences

```python
class CustomInfluence(OCEANInfluence):
    def modify_response(self, response: Response, profile: OCEANProfile) -> Response:
        # Custom behavioral modifiers
        pass
```

### Custom Memory Consolidators

```python
class CustomConsolidator(MemoryConsolidator):
    def consolidate(self, short_term: Memory, long_term: Memory) -> TransferResult:
        # Custom consolidation logic
        pass
```

---

*"Architecture is the skeleton of soul. Neshama provides the blueprint."*
