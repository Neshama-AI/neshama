# Neshama 架构

> 灵魂框架实现的技术规格

---

## 系统概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Soul Interface                            │
│                    （灵魂管理与交互的统一 API）                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  OCEAN    │  │  Memory   │  │  Growth   │  │ Reflection│    │
│  │  引擎     │  │  系统     │  │  引擎     │  │  系统     │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                    平台适配层                                    │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│   │  Coze   │  │ Claude  │  │ OpenAI  │  │ Custom  │          │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. Soul Interface

所有灵魂操作的统一入口：

```python
class SoulInterface:
    def __init__(self, config: SoulConfig)
    def interact(self, input: str) -> Response
    def grow(self, experience: Experience) -> None
    def reflect(self) -> ReflectionResult
    def get_identity(self) -> IdentitySnapshot
```

### 2. OCEAN 引擎

数学人格表征：

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

### 3. 记忆系统

五层分级架构：

```
┌──────────────────────────────────────────────────────┐
│                    记忆层级结构                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │            情景记忆层                         │    │
│  │  - 生命叙事记录                               │    │
│  │  - 个人里程碑                                 │    │
│  │  - 定义身份的经历                             │    │
│  └─────────────────────────────────────────────┘    │
│                         ▲                             │
│  ┌─────────────────────────────────────────────┐    │
│  │            长期记忆层                         │    │
│  │  - 语义知识                                   │    │
│  │  - 持久偏好                                   │    │
│  │  - 核心价值观与信念                           │    │
│  └─────────────────────────────────────────────┘    │
│                         ▲                             │
│  ┌─────────────────────────────────────────────┐    │
│  │            工作记忆层                         │    │
│  │  - 活跃处理（7±2 组块）                       │    │
│  │  - 当前任务上下文                             │    │
│  └─────────────────────────────────────────────┘    │
│                         ▲                             │
│  ┌─────────────────────────────────────────────┐    │
│  │            短期记忆层                         │    │
│  │  - 即时上下文（约 20 条目）                   │    │
│  │  - 会话状态                                   │    │
│  └─────────────────────────────────────────────┘    │
│                         ▲                             │
│  ┌─────────────────────────────────────────────┐    │
│  │            感知记忆层                         │    │
│  │  - 原始输入捕获                               │    │
│  │  - 毫秒级保留                                 │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 4. 成长引擎

自主学习机制：

```python
class GrowthEngine:
    def __init__(self, learning_rate: float = 0.01)
    
    def process_experience(self, experience: Experience) -> None
    def update_knowledge(self, insight: Insight) -> None
    def evolve_personality(self, feedback: Feedback) -> OCEANDeltas
    def schedule_reflection(self) -> None
```

### 5. 反思系统

元认知处理：

```python
class ReflectionSystem:
    def __init__(self, ocean: OCEANProfile)
    
    def evaluate_behavior(self, actions: List[Action]) -> Evaluation
    def identify_patterns(self) -> List[Pattern]
    def adjust_personality(self, feedback: Feedback) -> OCEANDeltas
    def consolidate_memory(self) -> MemoryTransfer
```

---

## 平台适配器

### 适配器接口

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

### 支持的平台

| 平台 | 状态 | 功能 |
|------|------|------|
| Coze | ✅ 稳定 | 完整集成 |
| Claude | ✅ 稳定 | 完整集成 |
| OpenAI | ✅ 稳定 | 完整集成 |
| Custom | ✅ 稳定 | 提供 SDK |

---

## 数据流

```
用户输入
    │
    ▼
┌─────────────────┐
│  平台适配器      │
└─────────────────┘
    │
    ▼
┌─────────────────┐     ┌─────────────────┐
│   感知记忆       │────►│   短期记忆       │
└─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   工作记忆       │
                        └─────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  OCEAN 影响     │ │   成长引擎       │ │   反思系统       │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                        ┌─────────────────┐
                        │   响应生成       │
                        └─────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   长期记忆       │ │   情景记忆       │ │   OCEAN 更新    │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
                               │
                               ▼
                         用户响应
```

---

## 配置模式

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
    sensory_ttl: int          # 毫秒
    short_term_ttl: int      # 秒
    working_capacity: int    # 组块数
    long_term_decay: float   # 每日衰减率
  
  growth:
    learning_rate: float
    reflection_interval: int # 分钟
    evolution_rate: float    # 每周期最大变化量
  
  platform:
    adapter: string           # coze|claude|openai|custom
    config: object            # 适配器特定配置
```

---

## 扩展点

### 自定义 OCEAN 影响

```python
class CustomInfluence(OCEANInfluence):
    def modify_response(self, response: Response, profile: OCEANProfile) -> Response:
        # 自定义行为修饰器
        pass
```

### 自定义记忆整合器

```python
class CustomConsolidator(MemoryConsolidator):
    def consolidate(self, short_term: Memory, long_term: Memory) -> TransferResult:
        # 自定义整合逻辑
        pass
```

---

*"架构是灵魂的骨架。Neshama 提供蓝图。"*
