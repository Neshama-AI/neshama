# NeshamaSDK Demo Prefabs

## 说明

本目录用于存放Demo场景所需的Prefab文件。由于Unity的Prefab是二进制格式，无法直接通过文本创建。

## 如何创建Prefab

### TavernKeeper Prefab

1. 在Unity中创建一个空GameObject，命名为 "TavernKeeper"
2. 添加以下组件：
   - `NPCSoul` (来自 NeshamaSDK)
   - `Collider` (设置为触发器，半径约2米)
   - `TavernKeeperAI` (来自 NeshamaSDK/Samples/TavernDemo)
   - 可选：`Animator`, `Renderer` 等视觉组件

3. 配置 `NPCSoul` 组件：
   - NPC Id: "tavern_keeper_001" (或其他唯一ID)
   - Preset: "tavern_keeper"
   - NPC Name: "酒馆老板娘"
   - Auto Connect: ✓

4. 配置 `TavernKeeperAI` 组件：
   - NPC Name: "酒馆老板娘"
   - Preset: "tavern_keeper"
   - Trigger Radius: 2f
   - Default Greeting: "欢迎光临！"
   - Angry Greeting: "哼，是你啊..."
   - Happy Greeting: "哦，亲爱的朋友来了！"

5. 将GameObject拖入Project窗口创建Prefab

### GuardCaptain Prefab

1. 创建一个空GameObject，命名为 "GuardCaptain"
2. 添加以下组件：
   - `NPCSoul` (来自 NeshamaSDK)
   - `Collider` (用于检测敌人)
   - `UnityEngine.AI.NavMeshAgent` (用于巡逻和追击)
   - `GuardCaptainAI` (来自 NeshamaSDK/Samples/TavernDemo)
   - 可选：`Animator`, `Renderer` 等视觉组件

3. 配置 `NPCSoul` 组件：
   - NPC Id: "guard_captain_001"
   - Preset: "guard_captain"
   - NPC Name: "守卫队长"
   - Auto Connect: ✓

4. 配置 `GuardCaptainAI` 组件：
   - NPC Name: "守卫队长"
   - Preset: "guard_captain"
   - Alert Radius: 10f
   - Enemy Detection Radius: 15f
   - Alert Threshold: 0.6f
   - Default Salute: "职责所在！"

5. 将GameObject拖入Project窗口创建Prefab

## 场景设置

### 酒馆Demo场景设置

1. 创建地面平面 (Plane)
2. 创建酒馆建筑结构（墙壁、吧台、桌子等）
3. 放置 TavernKeeper Prefab 在吧台后面
4. 创建玩家对象（需要有 "Player" 标签）
5. 创建UI Canvas用于显示对话
6. 设置NavMesh（如果使用导航）

### 守卫Demo场景设置

1. 创建城堡/城镇地面
2. 放置 GuardCaptain Prefab 在城门附近
3. 创建敌人预制件（需要有 "Enemy" 标签）
4. 设置NavMesh区域
5. 创建任务UI系统

## 测试流程

1. 确保后端API服务正在运行 (localhost:8420)
2. 打开Demo场景
3. 运行游戏
4. 观察NPC连接状态
5. 与NPC交互测试功能
