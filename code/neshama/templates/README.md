# Neshama Python SDK

> AI Personality Operating System

## 安装

```bash
pip install neshama
```

## 快速开始

```python
from neshama import Personality, OceanManager

# 从预设创建
p = Personality.from_preset("MyBot", "neshama")
p.save_skill_md("MyBot/SKILL.md")

# 自定义配置
p = Personality("CustomBot")
p.config.ocean.openness = 0.8
p.config.ocean.extraversion = 0.6
p.add_desire("求知欲", "想知道本质", 1)
print(p.generate_skill_md())
```

## CLI 使用

```bash
# 创建新人格
neshama init my_bot

# 使用预设
neshama init my_bot --preset analyst

# 验证配置
neshama validate SKILL.md

# 查看预设
neshama list
neshama preset neshama
```

## 核心模块

- `ocean.py` - OCEAN人格参数管理
- `personality.py` - 人格配置生成
- `validator.py` - SKILL.md验证
- `emotion.py` - 情绪追踪
- `memory.py` - 记忆管理
- `reflection.py` - 反思触发

## 许可

MIT License
