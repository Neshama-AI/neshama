# Neshama SDK - Demo Content README

## 概述

本目录包含 Neshama SDK 的 Blueprint 示例和演示内容。这些 Blueprint 继承自 `NPCSoulComponent`，展示了如何在实际游戏项目中使用 NPC 灵魂系统。

## 快速开始

### 1. 创建 NPC

1. 在 UE5 编辑器中创建一个新的 Actor Blueprint
2. 在 Components 面板中添加 `NPCSoul` 组件
3. 配置 NPC 属性：
   - **NPC ID**: 唯一标识符，如 `tavern_keeper_001`
   - **Preset**: 预设模板，如 `tavern_keeper`, `guard_captain`, `merchant` 等
   - **Display Name**: 显示名称

### 2. 配置连接

在 Project Settings → Neshama SDK 中配置服务器地址：
- **Server URL**: `http://localhost` (默认)
- **Port**: `8420` (默认)

确保 Neshama 服务器已启动并运行。

---

## Blueprint 示例

### BP_TavernKeeper (酒馆老板娘)

**文件**: `Content/BP_TavernKeeper.uasset` (需要创建)

**功能特性**:
- 玩家进入触发区域时发送欢迎事件
- 根据情绪状态切换不同的对话风格
- 支持送礼和互动
- 显示情绪状态的调试信息

**事件绑定**:
```
OnActorBeginOverlap → SendGameEvent(npc_complimented, 0.3)
OnEmotionChanged → UpdateDialogueStyle(NewEmotion)
OnChatResponse → DisplayDialogueUI(Response)
```

**情绪响应示例**:
| 主导情绪 | 对话风格 | 动画状态 |
|---------|---------|---------|
| Joy | 热情友好 | Idle_Happy |
| Anger | 冷淡或讽刺 | Idle_Angry |
| Trust | 信任交谈 | Idle_Neutral |
| Fear | 紧张回避 | Idle_Scared |

---

### BP_GuardCaptain (守卫队长)

**文件**: `Content/BP_GuardCaptain.uasset` (需要创建)

**功能特性**:
- 根据玩家阵营决定交互方式
- 敌对玩家触发戒备事件
- 友方玩家获得任务
- 战斗状态下的行为调整

**事件绑定**:
```
OnActorBeginOverlap → CheckPlayerFaction()
  ├─ 敌对阵营 → SendGameEvent(npc_insulted, 0.6)
  └─ 友方阵营 → SendGameEvent(npc_complimented, 0.3)
  
OnBehaviorChanged → UpdateGuardBehavior(Type, Value)
OnQuestCompleted → SendGameEvent(quest_completed, 1.0)
```

**阵营检测逻辑 (Blueprint)**:
```
1. 获取 Player Controller
2. 获取 Player State
3. 检查 PlayerFaction 变量
4. 根据阵营发送不同事件
```

---

## Blueprint 函数库

### UNPCSoulComponentLibrary

提供 Blueprint 工具函数：

| 函数 | 说明 |
|------|------|
| `Get NPC Soul Component` | 从 Actor 获取 NPCSoulComponent |
| `Has Dominant Emotion` | 检查 NPC 是否有指定主导情绪 |
| `Get Emotion Description` | 获取情绪的友好描述 |
| `Emotion To Debug String` | 将情绪转换为调试字符串 |

**使用示例**:
```
Event BeginPlay:
  └─ Get NPC Soul Component (Self)
      └─ Branch: Is Valid
          ├─ True: Enable Debug Display
          └─ False: Log Error "NPC Soul not found"
```

---

## 创建新的 NPC Blueprint

### 步骤 1: 创建 Actor

```
1. Content Browser → 右键 → Blueprint Class
2. 选择 "Actor" 作为父类
3. 命名，如 "BP_MyNPC"
```

### 步骤 2: 添加组件

```
1. 在 Components 面板点击 "Add" → 搜索 "NPC Soul"
2. 选中 NPCSoul 组件
3. 在 Details 面板设置属性：
   - NPC ID: unique_npc_id
   - Preset: your_preset_name
   - Display Name: 显示名称
   - Auto Connect: True
```

### 步骤 3: 添加触发器

```
1. 添加 Sphere Collision 组件
2. 设置 Collision Preset: OverlapAllDynamic
3. 设置半径（如 200-300 单位）
4. 在 Event Graph 中绑定事件
```

### 步骤 4: 实现交互逻辑

```blueprint
// 玩家进入触发区
OnComponentBeginOverlap (SphereCollision, OtherActor):
  ├─ SendGameEvent(PlayerEntered, 1.0, {})
  └─ Delay(0.5s):
      └─ Chat("Hello!", "")
      
// 情绪变化响应
OnEmotionChanged (EmotionState):
  ├─ Switch on EmotionState.Dominant:
  │   ├─ Joy: → Set Animation (Happy)
  │   ├─ Anger: → Set Animation (Angry)
  │   └─ Default: → Set Animation (Neutral)
  └─ UpdateDialogueUI()
  
// 对话响应
OnChatResponseBP (Response):
  └─ Create Dialog Widget with Response
```

---

## 事件类型参考

| 枚举值 | 说明 | 典型影响 |
|--------|------|---------|
| `PlayerEntered` | 玩家进入 | 触发问候 |
| `PlayerLeft` | 玩家离开 | 触发告别 |
| `PlayerAttacked` | 玩家攻击 | 愤怒上升 |
| `NPCHealed` | NPC被治愈 | 信任上升 |
| `NPCDamaged` | NPC受伤 | 恐惧/愤怒上升 |
| `NPCComplimented` | NPC被赞美 | 喜悦上升 |
| `NPCInsulted` | NPC被侮辱 | 愤怒/厌恶上升 |
| `GiftGiven` | 收到礼物 | 喜悦/信任上升 |
| `NPCHelped` | 被玩家帮助 | 信任上升 |
| `TradeCompleted` | 交易完成 | 信任上升 |
| `CombatStarted` | 战斗开始 | 恐惧/愤怒上升 |
| `CombatEnded` | 战斗结束 | 情绪稳定 |
| `QuestCompleted` | 任务完成 | 喜悦/信任上升 |
| `QuestAccepted` | 接受任务 | 期待上升 |
| `QuestFailed` | 任务失败 | 失望/羞愧 |

---

## 行为建议类型

| 类型 | 值示例 | 效果 |
|------|--------|------|
| `dialogue_style_change` | `hostile`, `friendly`, `cold` | 改变对话语气 |
| `quest_availability_change` | `locked`, `unlocked` | 解锁/锁定任务 |
| `shop_price_modifier` | `+10%`, `-20%` | 调整商店价格 |
| `movement_speed_change` | `1.5x`, `0.8x` | 改变移动速度 |
| `ai_behavior_change` | `aggressive`, `passive` | 改变AI行为模式 |

---

## 调试技巧

### 1. 启用调试显示

在 NPCSoulComponent 属性中勾选 `Show Debug Info`，会在场景中显示：
- NPC 名称
- 当前主导情绪
- 连接状态

### 2. 使用 Details 面板测试

在 Editor 中选中带 NPCSoul 组件的 Actor：
1. 打开 Details 面板
2. 展开 "NPC Soul" 部分
3. 使用 Quick Test 按钮发送测试事件
4. 观察情绪条变化

### 3. 控制台命令

```bash
// 手动连接
Neshama.Connect

// 手动发送事件
Neshama.SendEvent npc_id=tavern_keeper type=npc_complimented intensity=0.5

// 打印当前状态
Neshama.PrintStatus
```

---

## 常见问题

### Q: NPC 无法连接服务器

**检查项**:
1. 服务器是否运行在 `http://localhost:8420`
2. 检查 `ServerUrl` 和 `Port` 配置
3. 确认防火墙允许本地连接
4. 查看 Output Log 中的错误信息

### Q: 情绪没有变化

**检查项**:
1. 确认调用了 `SendGameEvent`
2. 检查事件强度值是否合理 (0-1)
3. 查看服务器日志是否有错误

### Q: Blueprint 事件不触发

**检查项**:
1. 确认正确绑定了事件（使用 `OnEmotionChanged` 等）
2. 检查组件是否正确添加到 Actor
3. 确认 `bAutoConnect` 为 true

---

## 进一步学习

- 参考 `../Source/NeshamaSDK/` 中的 C++ 源码
- 阅读 API 文档了解完整的接口
- 查看 Unity SDK 对比实现 (`../../unity/NeshamaSDK/`)
