# Neshama Unity Demo

**让NPC拥有灵魂的演示项目**

---

## 概述

Neshama Demo 是一个完整的 Unity 演示项目，展示了 Neshama NPC 灵魂操作系统的核心功能。

### 核心特性

- 🎭 **情感系统**: 9种情绪实时影响NPC行为
- 💬 **动态对话**: 基于情绪和关系的自然语言生成
- 🤝 **NPC社交**: NPC之间共享信息和记忆
- 📖 **剧情触发**: 根据玩家行为解锁隐藏内容
- 🎮 **开箱即用**: 无需外部模型，使用简单几何体

---

## 快速开始

### 环境要求

- Unity 2022.3.20f1 或更高版本
- TextMeshPro (Unity内置)
- Cinemachine (可选，用于更好的摄像机控制)

### 安装步骤

1. **克隆项目**
   ```bash
   cd Neshama/unity/NeshamaDemo
   ```

2. **打开Unity项目**
   - 启动 Unity Hub
   - 点击 "Open"
   - 选择 `NeshamaDemo` 文件夹

3. **安装依赖**
   - Unity 会自动安装 Package Manager 依赖
   - 如果没有自动安装，手动安装:
     - TextMeshPro
     - Cinemachine

4. **构建Demo场景**
   - 菜单: `Neshama → Build Demo Scene`
   - 或手动创建（见 Assets/Scenes/readme.md）

5. **启动后端服务**
   ```bash
   cd Neshama/neshama
   # 启动后端API (参考后端文档)
   ```

6. **运行Demo**
   - 按 Play 按钮
   - 使用 WASD 移动，鼠标旋转

---

## 控制说明

### 移动控制

| 按键 | 功能 |
|------|------|
| W / S | 前进 / 后退 |
| A / D | 左移 / 右移 |
| 鼠标 | 旋转视角 |
| Shift | 按住奔跑 |

### NPC交互

| 按键 | 功能 |
|------|------|
| E | 与NPC对话 |
| Q | 向NPC送礼 |
| R | 攻击NPC |
| F | 夸赞NPC |

### 快捷事件 (Shift + 数字)

| 快捷键 | 事件 | 效果 |
|--------|------|------|
| Shift+1 | 送礼 | 信任↑ |
| Shift+2 | 攻击 | 愤怒↑ |
| Shift+3 | 帮助 | 信任↑ |
| Shift+4 | 赞美 | 喜悦↑ |
| Shift+5 | 侮辱 | 愤怒↑ |
| Shift+6 | 交易 | 信任↑ |
| Shift+7 | 接任务 | 触发任务 |
| Shift+8 | 完成 | 奖励+信任 |

---

## NPC介绍

### 艾拉 - 酒馆老板娘

**位置**: 酒馆吧台

**性格**: 热情、健谈、关心八卦

**特点**:
- 玩家进入酒馆会主动问候
- Joy > 0.7 时可解锁斟酒动画
- Anger > 0.7 时会赶走玩家
- Sadness > 0.5 时会倾诉烦恼
- Trust > 0.6 时透露酒馆秘密

**触发区域**: 酒馆内部

---

### 凯尔 - 守卫队长

**位置**: 城门口

**性格**: 严肃、警惕、忠于职守

**特点**:
- 玩家靠近城门会检查身份
- Anger > 0.8 时封锁城门
- Trust > 0.7 时提供夜行通行证
- 被攻击会召唤援军
- 守卫城门，阻止可疑玩家

**触发区域**: 城门附近

---

### 神秘的流浪者

**位置**: 酒馆角落 / 游荡

**性格**: 神秘、预言者、洞察人心

**特点**:
- 初次见面有神秘台词
- Trust > 0.6 时透露预言
- Fear > 0.5 时消失并重新出现
- 被侮辱不愤怒但悲伤
- 会在酒馆和城门之间游荡

**触发区域**: 全地图

---

## 项目结构

```
NeshamaDemo/
├── Assets/
│   ├── Scenes/
│   │   └── readme.md           # 场景创建指南
│   ├── Scripts/
│   │   ├── Demo/
│   │   │   ├── DemoSceneManager.cs      # 场景管理
│   │   │   ├── PlayerController.cs      # 玩家控制
│   │   │   ├── InteractionSystem.cs     # 交互系统
│   │   │   ├── NPCTavernKeeper.cs       # 酒馆老板娘AI
│   │   │   ├── NPCGuardCaptain.cs       # 守卫队长AI
│   │   │   ├── NPCMysticTraveler.cs     # 神秘旅人AI
│   │   │   └── DemoUIManager.cs         # UI管理
│   │   └── Editor/
│   │       └── DemoSceneBuilder.cs     # 场景构建器
│   ├── Prefabs/
│   │   └── readme.md           # 预制件说明
│   ├── UI/
│   │   └── readme.md           # UI说明
│   └── DemoSettings/
│       └── NeshamaDemoConfig.cs # 配置文件
├── Packages/
│   └── manifest.json            # Unity包配置
└── ProjectSettings/
    └── ProjectVersion.txt        # Unity版本
```

---

## 配置

### 服务器配置

编辑 `Assets/DemoSettings/NeshamaDemoConfig.asset`:

```
Server URL: http://localhost:8420
Player ID: demo_player
Auto Connect: true
Enable WebSocket: true
```

### NPC预设

可在 Inspector 中修改每个 NPC 的预设:
- `tavern_keeper`
- `guard_captain`
- `mystic_traveler`

---

## 扩展指南

### 添加新NPC

1. 创建新的AI控制器脚本，继承 `MonoBehaviour`
2. 添加 `NPCSoul` 组件
3. 实现情绪响应逻辑
4. 添加巡逻路径

示例:
```csharp
public class MyCustomNPC : MonoBehaviour
{
    public NPCSoul npcSoul;
    
    void Start()
    {
        npcSoul.OnEmotionChanged += OnEmotionChanged;
    }
    
    void OnEmotionChanged(EmotionState emotion)
    {
        // 根据情绪执行行为
        if (emotion.Anger > 0.8f)
        {
            // 愤怒行为
        }
    }
}
```

### 自定义对话流

```csharp
// 获取对话响应
var response = await npcSoul.ChatAsync("你好");
// response.Text 包含NPC的回复
// response.Emotion 包含回复时的情绪状态
```

### 添加新事件类型

在 `GameEventType` 枚举中添加新事件:
```csharp
public enum GameEventType
{
    // ... 现有事件 ...
    custom_event_1,
    custom_event_2,
}
```

---

## 故障排除

### 连接失败

1. 检查服务器是否运行: `curl http://localhost:8420/health`
2. 检查防火墙设置
3. 确认 Server URL 配置正确

### NPC不响应

1. 检查 Console 日志
2. 确认 NPC 在交互范围内
3. 检查是否有交互冷却

### UI不显示

1. 确认 DemoUIManager 存在
2. 检查 Canvas 渲染模式
3. 查看 Console 错误信息

---

## 开发指南

### 调试模式

启用调试可以获得更多信息:
```csharp
// 在 DemoSceneManager 中
showDebugInfo = true;
```

### 日志输出

所有日志以 `[NPC名称]` 前缀:
```
[艾拉] 情绪变化: anger
[凯尔] 封锁了城门！
[神秘的流浪者] 揭示了真名: 艾瑟琳
```

---

## 技术支持

- 文档: [docs.neshama.game](https://docs.neshama.game)
- 问题反馈: [github.com/neshama/issues](https://github.com/neshama/issues)
- Discord: [discord.gg/neshama](https://discord.gg/neshama)

---

## 许可

本项目使用 MIT 许可证。详见 LICENSE 文件。

---

## 致谢

- Unity Technologies - Unity Engine
- TextMeshPro - 高级文字渲染
- Cinemachine - 智能摄像机系统
