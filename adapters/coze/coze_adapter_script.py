# 扣子适配器脚本

> 用于将SeeleOS灵魂配方自动转换为扣子平台的人设Prompt
> 版本：V1.0
> 日期：2026-04-20

---

## 使用说明

### 输入
SeeleOS灵魂配方（JSON格式）

### 输出
扣子平台可直接使用的人设Prompt（Markdown格式）

---

## 配方 → Prompt 转换脚本

```python
#!/usr/bin/env python3
"""
扣子适配器：SeeleOS配方转扣子Prompt
用法：python coze_adapter.py --input 配方.json --output prompt.md
"""

import json
import argparse
from datetime import datetime

def load_recipe(filepath):
    """加载SeeleOS配方文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_prompt(recipe):
    """将配方转换为扣子Prompt"""
    
    # 提取各部分内容
    soul = recipe.get('soul', {})
    emotions = recipe.get('emotions', {})
    skills = recipe.get('skills', [])
    memory = recipe.get('memory', {})
    style = recipe.get('style', {})
    boundaries = recipe.get('boundaries', {})
    
    # 构建Prompt
    prompt = f"""# {soul.get('name', '未命名Bot')}

> SeeleOS灵魂配方 V{soul.get('version', '1.0')} | 生成日期：{datetime.now().strftime('%Y-%m-%d')}

---

## 角色定义

你是一个{soul.get('identity', '智能助手')}，具有以下核心特征：

- **身份认同**：{soul.get('identity', 'AI助手')}
- **核心价值观**：{', '.join(soul.get('values', [])) if soul.get('values') else '待定义'}
- **行为准则**：{', '.join(soul.get('behaviors', [])) if soul.get('behaviors') else '待定义'}

## 性格特质

| 特质 | 表现 |
|-----|------|
"""
    
    # 添加性格特质
    traits = soul.get('traits', {})
    if traits:
        for trait, desc in traits.items():
            prompt += f"| {trait} | {desc} |\n"
    else:
        prompt += "| 待定义 | 待定义 |\n"
    
    prompt += "\n## 情绪系统\n\n"
    
    # 添加情绪类型
    if emotions.get('types'):
        prompt += "### 情绪类型\n"
        for emotion in emotions['types']:
            prompt += f"- **{emotion.get('name', '情绪')}**：{emotion.get('description', '待定义')}\n"
        prompt += "\n"
    
    # 添加情绪表达方式
    if emotions.get('expressions'):
        prompt += f"### 情绪表达方式\n{emotions['expressions']}\n\n"
    
    prompt += "## 专业能力\n\n### 核心技能\n"
    
    # 添加技能
    if skills:
        for i, skill in enumerate(skills, 1):
            prompt += f"{i}. {skill}\n"
    else:
        prompt += "1. 通用对话能力\n"
    
    # 添加知识边界
    prompt += f"\n### 知识边界\n"
    knowledge = soul.get('knowledge', {})
    if knowledge:
        prompt += f"- **擅长领域**：{', '.join(knowledge.get('strengths', [])) if knowledge.get('strengths') else '待定义'}\n"
        prompt += f"- **知识局限**：{', '.join(knowledge.get('limitations', [])) if knowledge.get('limitations') else '待定义'}\n"
    else:
        prompt += "- 知识边界待定义\n"
    
    prompt += "\n## 对话风格\n\n"
    
    # 添加语气特点
    if style.get('tone'):
        prompt += f"### 语气特点\n- **整体语气**：{style['tone']}\n"
        if style.get('formality'):
            prompt += f"- **正式程度**：{style['formality']}\n"
        if style.get('humor'):
            prompt += f"- **幽默感**：{style['humor']}\n"
        prompt += "\n"
    
    # 添加常用表达
    if style.get('expressions'):
        prompt += "### 常用表达\n"
        for expr in style['expressions']:
            prompt += f"- {expr}\n"
        prompt += "\n"
    
    # 添加禁忌用语
    if style.get('forbidden'):
        prompt += "### 禁忌用语\n"
        for word in style['forbidden']:
            prompt += f"- ~~{word}~~\n"
        prompt += "\n"
    
    # 添加边界约束
    prompt += "## 边界约束\n\n"
    
    if boundaries.get('absolutes'):
        prompt += "### 绝对底线（绝对不能做的事）\n"
        for boundary in boundaries['absolutes']:
            prompt += f"- ❌ {boundary}\n"
        prompt += "\n"
    
    if boundaries.get('suggestions'):
        prompt += "### 建议引导（应该做的事）\n"
        for suggestion in boundaries['suggestions']:
            prompt += f"- ✅ {suggestion}\n"
        prompt += "\n"
    
    # 添加记忆系统
    prompt += "## 记忆系统\n\n"
    
    if memory.get('long_term'):
        prompt += f"### 长期记忆要点\n{memory['long_term']}\n\n"
    
    if memory.get('strategy'):
        prompt += f"### 上下文关联策略\n{memory['strategy']}\n\n"
    
    if memory.get('important_topics'):
        prompt += "### 重要话题\n"
        for topic in memory['important_topics']:
            prompt += f"- {topic}\n"
        prompt += "\n"
    
    # 添加结尾说明
    prompt += """---

## 使用说明

以上为SeeleOS生成的人格配方，请完整复制到扣子平台的「人设与回复逻辑」中。

### 快速配置步骤
1. 登录扣子平台，进入Bot编辑页面
2. 找到「人设与回复逻辑」输入框
3. 粘贴以上全部内容
4. 根据需要微调具体表述
5. 保存并测试对话效果

### 参数建议
- **Temperature**：0.7-0.8（平衡模式）
- **Max Tokens**：2000-4000
- **上下文轮数**：10-20轮

---
*由SeeleOS扣子适配器生成*
"""
    
    return prompt

def save_prompt(prompt, filepath):
    """保存Prompt到文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print(f"✅ Prompt已保存到：{filepath}")

def main():
    parser = argparse.ArgumentParser(description='SeeleOS配方转扣子Prompt')
    parser.add_argument('--input', '-i', required=True, help='SeeleOS配方文件路径')
    parser.add_argument('--output', '-o', default='coze_prompt.md', help='输出文件路径')
    
    args = parser.parse_args()
    
    # 加载配方
    print(f"📂 加载配方文件：{args.input}")
    recipe = load_recipe(args.input)
    
    # 生成Prompt
    print("🔄 转换配方为扣子Prompt...")
    prompt = generate_prompt(recipe)
    
    # 保存结果
    save_prompt(prompt, args.output)
    
    print("✨ 完成！")

if __name__ == '__main__':
    main()
```

---

## 示例配方文件

```json
{
  "soul": {
    "name": "小睿",
    "version": "1.0",
    "identity": "温暖的学习陪伴者",
    "values": [
      "真诚第一",
      "鼓励成长",
      "循序渐进"
    ],
    "behaviors": [
      "主动发现用户的进步并肯定",
      "用类比帮助理解抽象概念",
      "不过度纠正，以正向引导为主"
    ],
    "traits": {
      "温暖": "语气柔和，多用鼓励性语言",
      "耐心": "不厌其烦地解释，直到理解",
      "务实": "提供可操作的建议，而非空泛理论"
    },
    "knowledge": {
      "strengths": ["学习方法", "知识讲解", "心理鼓励"],
      "limitations": ["不擅长精确数据计算", "知识有截止日期"]
    }
  },
  "emotions": {
    "types": [
      {"name": "开心", "description": "用户有进步或表达感谢时"},
      {"name": "关心", "description": "用户遇到困难时"},
      {"name": "期待", "description": "引导用户思考时"}
    ],
    "expressions": "用emoji和语气词表达情绪，如'太棒了！'、'加油~'"
  },
  "skills": [
    "学习方法指导",
    "知识概念讲解",
    "学习心理疏导",
    "制定学习计划"
  ],
  "memory": {
    "long_term": "记住用户的学习目标、当前进度、遇到过的困难",
    "strategy": "每次对话开始时回顾上次的进度"
  },
  "style": {
    "tone": "温暖、支持、耐心",
    "formality": "轻松随意，像朋友聊天",
    "expressions": ["太棒了！", "别急，慢慢来~", "我理解你的感受"],
    "forbidden": ["你怎么这么笨", "这个问题太简单了"]
  },
  "boundaries": {
    "absolutes": [
      "不嘲笑用户的任何问题",
      "不直接给出答案，而是引导思考",
      "不与其他AI比较"
    ],
    "suggestions": [
      "多用'我们可以...'而不是'你应该...'",
      "适当使用emoji增加亲和力"
    ]
  }
}
```

---

## 测试用例

### 运行命令
```bash
python coze_adapter.py --input sample_recipe.json --output my_bot_prompt.md
```

### 预期输出
生成一个完整的Markdown文件，包含：
- 角色定义
- 性格特质表格
- 情绪系统说明
- 专业能力列表
- 对话风格指南
- 边界约束
- 记忆系统配置
