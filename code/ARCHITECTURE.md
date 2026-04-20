# Neshama Python SDK 架构设计

> 版本：V0.1 | 更新：2026-04-20

---

## 定位

轻量级Python工具包，用于：
1. 生成人格配置文件（SKILL.md）
2. 验证人格配置正确性
3. 管理OCEAN人格参数
4. 辅助记忆和反思

**不是**：重型框架、Agent运行时

---

## 目录结构

```
neshama/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── personality.py      # 人格配置生成
│   ├── ocean.py            # OCEAN参数管理
│   └── validator.py        # 配置验证
├── tools/
│   ├── __init__.py
│   ├── memory.py           # 记忆辅助
│   ├── reflection.py       # 反思触发器
│   └── emotion.py          # 情绪追踪
├── cli.py                  # 命令行工具
└── templates/              # 模板文件
    └── base_skill.md
```

---

## 核心模块

### 1. personality.py - 人格配置

```python
class Personality:
    def __init__(self, name: str, ocean: OceanParams)
    def add_system(self, system: str)
    def generate_skill_md() -> str
    def validate() -> ValidationResult
```

### 2. ocean.py - OCEAN参数

```python
@dataclass
class OceanParams:
    openness: float          # 0-1
    conscientiousness: float # 0-1
    extraversion: float      # 0-1
    agreeableness: float     # 0-1
    neuroticism: float       # 0-1
```

### 3. validator.py - 配置验证

```python
def validate_skill_md(content: str) -> ValidationResult
def check_emotion_system(content: str) -> bool
def check_boundaries(content: str) -> bool
```

### 4. memory.py - 记忆辅助

```python
class MemoryManager:
    def log_emotion(self, emotion: str, intensity: int)
    def log_reflection(self, content: str)
    def export_memory() -> dict
```

### 5. reflection.py - 反思触发

```python
class ReflectionTrigger:
    def should_reflect(self, context: dict) -> bool
    def generate_prompt(self, context: dict) -> str
```

### 6. cli.py - 命令行

```bash
neshama init <name>          # 创建新人格
neshama validate <file>      # 验证配置
neshama export <name>         # 导出SKILL.md
neshama reflect               # 触发反思
```

---

## 安装使用

```bash
pip install neshama

# 创建新人格
neshama init my_bot

# 验证配置
neshama validate skill.md

# 导出扣子配置
neshama export my_bot --platform coze
```

---

## 依赖

- Python >= 3.9
- pydantic (参数验证)
- click (CLI)
- markdown (MD生成)

---

## TODO

- [ ] 核心模块实现
- [ ] CLI工具
- [ ] 单元测试
- [ ] PyPI发布
- [ ] 文档
