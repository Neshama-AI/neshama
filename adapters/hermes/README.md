# Hermes Adapter

**Neshama适配器 for Nous Research Hermes Agent**

## 概述

Hermes Agent是由AI研究实验室Nous Research开发的开源自进化Agent框架（GitHub 80k+ Stars）。它内置自学习循环，能自动从经验中创造技能、建立用户认知模型、实现跨会话记忆持久化。

MiniMax的MaxHermes是基于Hermes Agent打造的云端产品。

## 使用方法

### 1. 获取配置

在Hermes的SOUL.md中导入Neshama人格：

```
【人格配置】
OCEAN档案：开放性0.7/尽责性0.6/外向性0.5/宜人性0.8/神经质0.3
```

### 2. 记忆系统

Hermes已有内置记忆系统，Neshama提供人格层面的增强：

```
【人格规则】
- L0工作记忆：当前会话行为驱动
- L1情景记忆：7-30天互动模式
- L2语义记忆：核心身份与人格固化
- 人格更新：OCEAN档案随互动演化
```

### 3. 与Hermes原生功能结合

- Hermes自动创建Skills → Neshama定义技能的风格
- Hermes跨会话记忆 → Neshama提供人格连续性
- Hermes用户模型 → Neshama提供OCEAN量化人格

---

*适配器版本: v0.1.0*
