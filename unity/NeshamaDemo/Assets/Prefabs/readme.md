# NeshamaDemo Prefabs 文件夹

此文件夹用于存放预制件（Prefab）资源。

## 目录结构

```
Prefabs/
├── NPC/
│   ├── TavernKeeper.prefab    - 酒馆老板娘预制件
│   ├── GuardCaptain.prefab    - 守卫队长预制件
│   └── MysticTraveler.prefab  - 神秘旅人预制件
├── UI/
│   ├── DialoguePanel.prefab   - 对话面板预制件
│   ├── EmotionPanel.prefab    - 情绪面板预制件
│   └── Notification.prefab   - 通知提示预制件
└── Environment/
    ├── Table.prefab           - 桌椅预制件
    └── Barrel.prefab          - 酒桶装饰预制件
```

## 使用说明

### NPC预制件

NPC预制件包含完整的NPC配置：
- **NPCSoul组件**: 连接Neshama服务器
- **AI控制器**: NPCTavernKeeper / NPCGuardCaptain / NPCMysticTraveler
- **胶囊体模型**: 简单人形表示
- **碰撞体**: 用于交互检测

### 创建NPC预制件

1. 在场景中创建NPC（使用DemoSceneBuilder）
2. 在Hierarchy中选中NPC
3. 拖拽到Prefabs/NPC文件夹
4. 预制件已创建

### UI预制件

UI预制件包含完整的UI配置：
- **Canvas**: 自动创建的UI Canvas
- **Panel**: 面板容器
- **Text**: 文本组件
- **Button**: 按钮组件
- **事件绑定**: 与DemoUIManager通信

## 预制件变体

可以为不同的游戏场景创建预制件变体：

1. **TavernKeeper_Day**: 白天版本的酒馆老板娘
2. **TavernKeeper_Night**: 夜晚版本，情绪更紧张
3. **GuardCaptain_Alert**: 警戒状态的守卫
4. **GuardCaptain_Relaxed**: 放松状态的守卫

## 注意事项

- 预制件使用简单几何体，无外部模型依赖
- 所有材质使用Standard Shader
- 颜色配置存储在材质中，可自定义
