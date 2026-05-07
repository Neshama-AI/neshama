# NeshamaDemo Scenes 文件夹

此文件夹包含 Demo 场景文件。

## 场景文件

由于 Unity 场景文件（.unity）是二进制格式，无法直接创建。

### 自动构建场景

请使用菜单 **Neshama → Build Demo Scene** 自动构建完整场景。

### 手动创建步骤

如果 Editor 脚本无法使用，请按以下步骤手动创建场景：

---

## 场景结构

```
DemoScene
├── Lighting
│   └── Directional Light (创建 → 灯光 → 方向光)
├── Ground
│   └── Plane (创建 → 3D Object → Plane)
│       - Position: (0, 0, 0)
│       - Scale: (4, 1, 4)
│       - Material: WoodFloor (木地板材质)
├── Tavern (空对象作为父级)
│   ├── BackWall (立方体)
│   │   - Position: (0, 2.5, -5)
│   │   - Scale: (12, 5, 0.5)
│   ├── LeftWall (立方体)
│   │   - Position: (-5.5, 2.5, 0)
│   │   - Scale: (0.5, 5, 10)
│   ├── RightWall (立方体)
│   │   - Position: (5.5, 2.5, 0)
│   │   - Scale: (0.5, 5, 10)
│   ├── Roof (立方体)
│   │   - Position: (0, 5.5, -2.5)
│   │   - Scale: (12, 0.3, 5.5)
│   ├── BarCounter (立方体)
│   │   - Position: (0, 0.6, -3)
│   │   - Scale: (4, 1.2, 1.5)
│   ├── Table_1, Table_2, Table_3 (立方体)
│   │   - Position: 各不相同，分布在酒馆内
│   │   - Scale: (1.5, 0.1, 1.5)
│   └── Chair_* (立方体)
│       - 每张桌子配2把椅子
├── Gate (空对象作为父级)
│   ├── GateWallLeft (立方体)
│   │   - Position: (8, 2.5, 0)
│   │   - Scale: (4, 5, 2)
│   ├── GateWallRight (立方体)
│   │   - Position: (8, 2.5, 0) [偏移不同]
│   │   - Scale: (4, 5, 2)
│   └── GateArch (立方体，无碰撞体)
│       - Position: (8, 2, 0)
│       - Scale: (2, 4, 2.1)
├── Campfire (空对象作为父级)
│   ├── FireBase (圆柱体)
│   │   - Position: (0, 0.1, -7)
│   └── FireLight (点光源)
│       - Position: (0, 1, -7)
│       - Color: 暖橙色
│       - Intensity: 1.5
│       - Range: 10
├── Player
│   - 胶囊体 (创建 → 3D Object → Capsule)
│   - 添加组件:
│     - CharacterController
│     - PlayerController
│     - InteractionSystem
│   - Tag: Player
│   - Position: (0, 1, 5)
├── NPC_TavernKeeper
│   - 胶囊体
│   - 添加组件:
│     - NPCSoul
│     - NPCTavernKeeper
│   - Position: (0, 1, -2)
│   - Material: 暖肤色
├── NPC_GuardCaptain
│   - 胶囊体
│   - 添加组件:
│     - NPCSoul
│     - NPCGuardCaptain
│   - Position: (8, 1, 0)
│   - Material: 冷灰色
├── NPC_MysticTraveler
│   - 胶囊体
│   - 添加组件:
│     - NPCSoul
│     - NPCMysticTraveler
│   - Position: (-4, 1, 3)
│   - Material: 淡紫色
├── DemoSceneManager
│   - 空对象
│   - 添加组件: DemoSceneManager
├── DemoUIManager
│   - 空对象
│   - 添加组件: DemoUIManager
└── NPCSpawn_* (空对象，隐藏)
    - 作为 NPC 出生点标记
```

---

## 材质创建

### 木地板材质
```
1. 资源 → 创建 → 材质
2. 名称: WoodFloor
3. Surface Type: Opaque
4. Base Map: 自定义或使用棕色
5. Metallic: 0
6. Smoothness: 0.3
```

### 墙壁材质
```
颜色: RGB(89, 64, 51) - 深棕色
```

### NPC材质
```
酒馆老板娘: RGB(255, 230, 204) - 暖肤色
守卫队长: RGB(179, 204, 230) - 冷灰色
神秘旅人: RGB(204, 179, 230) - 淡紫色
```

---

## 组件配置

### PlayerController
- Move Speed: 5
- Rotation Speed: 10
- Run Speed Multiplier: 2
- Interaction Distance: 3

### NPCSoul (每个NPC)
- Auto Connect: ✓
- Show Debug Info: ✓
- NpcId: 根据NPC类型设置
- Preset: tavern_keeper / guard_captain / mystic_traveler

### DemoSceneManager
- Server URL: http://localhost:8420
- Player ID: demo_player
- Auto Create NPCs: ✓
- Enable WebSocket: ✓
- Show Debug Info: ✓

---

## 快捷操作

1. **构建完整场景**: 菜单 → Neshama → Build Demo Scene
2. **清理场景**: 菜单 → Neshama → Clean Demo Scene
3. **保存场景**: Ctrl + S

---

## 截图标注指南

场景构建完成后，建议截图并标注以下关键位置：

1. **全景图**: 展示整个酒馆和城门区域
2. **酒馆老板娘特写**: 标注她的位置和交互区域
3. **守卫队长位置**: 标注城门口巡逻区域
4. **神秘旅人位置**: 标注酒馆角落位置
5. **UI界面**: 对话面板、情绪面板示例
