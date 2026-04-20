# Neshama Python SDK

> AI Personality Operating System

## 安装

```bash
pip install -e .
```

或

```bash
pip install neshama
```

## 核心功能

### 1. OCEAN 人格参数

```python
from neshama import OceanParams, OceanManager

# 默认参数
ocean = OceanParams()

# 使用预设
manager = OceanManager()
manager.apply_preset('neshama')
ocean = manager.params

# 调整参数
manager.adjust_trait('openness', 0.1)
```

### 2. 人格配置生成

```python
from neshama import Personality

p = Personality("MyBot")
p.add_desire("求知欲", "想知道本质", 1)
p.set_response_style(directness=0.8, humor=0.5, empathy=0.6)

# 生成 SKILL.md
print(p.generate_skill_md())
p.save_skill_md("output/SKILL.md")
```

### 3. 配置验证

```python
from neshama import Validator

validator = Validator()
result = validator.validate_skill_md(skill_md_content)
print(result.summary())
```

### 4. 情绪追踪

```python
from neshama import EmotionTracker, Emotion

tracker = EmotionTracker()
tracker.set_emotion(Emotion.HAPPY, 7)

if tracker.should_express():
    print(tracker.get_expression())  # "高兴 😄"
```

### 5. 记忆管理

```python
from neshama import MemoryManager, MemoryType

manager = MemoryManager()
manager.log("学到了新东西", MemoryType.LEARNING, tags=['进步'])
manager.log_emotion("happy", 7)

# 导出记忆
data = manager.export_memory()
```

### 6. 反思触发

```python
from neshama import ReflectionTrigger

trigger = ReflectionTrigger()

# 检查是否需要反思
if trigger.should_reflect({'error_occurred': True}):
    prompt = trigger.generate_prompt({'error_description': '...'})
    print(prompt.prompt)
```

## CLI 命令

```bash
# 初始化新人格
neshama init my_bot
neshama init my_bot --preset analyst

# 验证配置
neshama validate SKILL.md
neshama validate SKILL.md -v

# 导出配置
neshama export my_bot
neshama export my_bot --preset neshama -o output.md

# 查看预设
neshama list
neshama preset neshama
```

## 预设人格

| 预设 | 特点 |
|------|------|
| analyst | 高开放性、高尽责性、低外向性 - 分析师类型 |
| helper | 高宜人性、高外向性 - 助人型 |
| explorer | 高开放性、高外向性 - 探索型 |
| leader | 高尽责性、高外向性 - 领导型 |
| diplomat | 高开放性、高宜人性 - 外交型 |
| sentinel | 高尽责性、低开放性 - 守卫型 |
| neshama | 平衡型 - 默认人格 |

## OCEAN 参数说明

| 维度 | 高分特点 | 低分特点 |
|------|---------|---------|
| 开放性 | 创造力、好奇心 | 务实、传统 |
| 尽责性 | 有计划、注重细节 | 灵活、随性 |
| 外向性 | 社交活跃、精力充沛 | 内向、独立 |
| 宜人性 | 合作、信任 | 竞争、质疑 |
| 神经质 | 敏感、焦虑 | 稳定、抗压 |

## 许可

MIT License
