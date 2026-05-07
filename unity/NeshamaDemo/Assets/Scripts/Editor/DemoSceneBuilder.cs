using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

namespace Neshama.Demo.Editor
{
    /// <summary>
    /// Demo场景构建器 - Editor脚本，用于一键构建Demo场景
    /// 
    /// 自动创建：
    /// - 地面（平面 + 木地板材质）
    /// - 酒馆建筑（简单Box组合：墙壁+屋顶+吧台+桌椅）
    /// - 城门（简单Box组合：城墙+门洞）
    /// - 篝火（点光源）
    /// - 3个NPC GameObject（带NPCSoul组件 + 简单Capsule代替模型）
    /// - 玩家GameObject（带PlayerController + Capsule）
    /// - UI Canvas（对话面板+情绪面板+事件栏）
    /// - Directional Light + Ambient
    /// - NavMesh烘焙占位
    /// </summary>
    public class DemoSceneBuilder : EditorWindow
    {
        #region 菜单入口

        /// <summary>
        /// 添加菜单项
        /// </summary>
        [MenuItem("Neshama/Build Demo Scene")]
        public static void BuildDemoScene()
        {
            // 确认操作
            if (!EditorUtility.DisplayDialog("构建Demo场景", 
                "这将创建完整的Demo场景。\n\n注意：如果场景中已有相关对象，可能会重复创建。\n建议新建一个空场景后再执行。", 
                "继续", "取消"))
            {
                return;
            }

            // 创建场景
            CreateScene();

            EditorUtility.DisplayDialog("构建完成", 
                "Demo场景已创建完成！\n\n按Play开始测试Demo。\n\n控制说明：\n- WASD移动\n- 鼠标旋转\n- Shift+1~8发送事件\n- E对话，Q送礼，R攻击，F夸赞", 
                "确定");
        }

        /// <summary>
        /// 清理场景
        /// </summary>
        [MenuItem("Neshama/Clean Demo Scene")]
        public static void CleanDemoScene()
        {
            if (!EditorUtility.DisplayDialog("清理Demo场景", 
                "这将删除所有Demo相关的GameObject。", 
                "继续", "取消"))
            {
                return;
            }

            CleanScene();

            EditorUtility.DisplayDialog("清理完成", "Demo相关对象已删除。", "确定");
        }

        #endregion

        #region 场景构建

        /// <summary>
        /// 创建完整场景
        /// </summary>
        private static void CreateScene()
        {
            // 创建基础对象
            CreateGround();
            CreateLighting();
            CreateTavern();
            CreateGate();
            CreateCampfire();
            CreatePlayer();
            CreateNPCs();
            CreateSceneManager();
            CreateUIManager();

            // 标记场景为已修改
            UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(
                UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene());
        }

        /// <summary>
        /// 清理场景
        /// </summary>
        private static void CleanScene()
        {
            // 查找并删除所有Demo相关对象
            string[] tagsToClean = { "Player", "Untagged" };

            // 手动删除标记的对象
            string[] namesToDelete = {
                "Ground", "Tavern", "BarCounter", "Gate", "Campfire",
                "Player", "NPC_TavernKeeper", "NPC_GuardCaptain", "NPC_MysticTraveler",
                "DemoSceneManager", "DemoUIManager", "DemoCanvas"
            };

            foreach (string name in namesToDelete)
            {
                var obj = GameObject.Find(name);
                if (obj != null)
                {
                    DestroyImmediate(obj);
                }
            }

            // 删除桌椅
            var tables = GameObject.FindObjectsOfType<Transform>();
            foreach (var t in tables)
            {
                if (t.name.StartsWith("Table_") || t.name.StartsWith("Chair_"))
                {
                    DestroyImmediate(t.gameObject);
                }
            }

            // 标记场景为已修改
            UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(
                UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene());
        }

        #endregion

        #region 基础对象创建

        /// <summary>
        /// 创建地面
        /// </summary>
        private static void CreateGround()
        {
            // 检查是否已存在
            if (GameObject.Find("Ground") != null) return;

            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Ground";

            // 设置位置和大小
            ground.transform.position = new Vector3(0, 0, 0);
            ground.transform.localScale = new Vector3(4, 1, 4);

            // 创建木地板材质
            var material = new Material(Shader.Find("Standard"));
            material.color = new Color(0.4f, 0.3f, 0.2f);
            material.name = "WoodFloor";

            var renderer = ground.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material = material;
            }

            Debug.Log("[DemoSceneBuilder] 地面创建完成");
        }

        /// <summary>
        /// 创建光照
        /// </summary>
        private static void CreateLighting()
        {
            // 创建方向光
            var directionalLight = GameObject.Find("Directional Light");
            if (directionalLight == null)
            {
                var lightGO = new GameObject("Directional Light");
                var light = lightGO.AddComponent<Light>();
                light.type = LightType.Directional;
                light.color = new Color(1f, 0.95f, 0.85f);
                light.intensity = 0.8f;
                lightGO.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            }

            // 设置环境光
            RenderSettings.ambientLight = new Color(0.4f, 0.35f, 0.3f);
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.6f, 0.5f, 0.4f);
            RenderSettings.fogDensity = 0.02f;

            Debug.Log("[DemoSceneBuilder] 光照设置完成");
        }

        #endregion

        #region 酒馆创建

        /// <summary>
        /// 创建酒馆
        /// </summary>
        private static void CreateTavern()
        {
            // 检查是否已存在
            if (GameObject.Find("Tavern") != null) return;

            var tavern = new GameObject("Tavern");
            tavern.transform.position = new Vector3(0, 0, 0);

            // 创建墙壁
            CreateWall(tavern.transform, new Vector3(0, 2.5f, -5), new Vector3(12, 5, 0.5f), "BackWall");
            CreateWall(tavern.transform, new Vector3(-5.5f, 2.5f, 0), new Vector3(0.5f, 5, 10), "LeftWall");
            CreateWall(tavern.transform, new Vector3(5.5f, 2.5f, 0), new Vector3(0.5f, 5, 10), "RightWall");

            // 创建屋顶
            CreateWall(tavern.transform, new Vector3(0, 5.5f, -2.5f), new Vector3(12, 0.3f, 5.5f), "Roof");

            // 创建吧台
            CreateBarCounter(tavern.transform);

            // 创建桌椅
            CreateTablesAndChairs(tavern.transform);

            Debug.Log("[DemoSceneBuilder] 酒馆创建完成");
        }

        /// <summary>
        /// 创建墙壁
        /// </summary>
        private static void CreateWall(Transform parent, Vector3 position, Vector3 scale, string name)
        {
            var wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
            wall.name = name;
            wall.transform.SetParent(parent);
            wall.transform.position = position;
            wall.transform.localScale = scale;

            // 设置材质
            var material = new Material(Shader.Find("Standard"));
            material.color = new Color(0.35f, 0.25f, 0.2f);
            var renderer = wall.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material = material;
            }
        }

        /// <summary>
        /// 创建吧台
        /// </summary>
        private static void CreateBarCounter(Transform parent)
        {
            var bar = GameObject.CreatePrimitive(PrimitiveType.Cube);
            bar.name = "BarCounter";
            bar.transform.SetParent(parent);
            bar.transform.position = new Vector3(0, 0.6f, -3);
            bar.transform.localScale = new Vector3(4, 1.2f, 1.5f);

            // 设置材质
            var material = new Material(Shader.Find("Standard"));
            material.color = new Color(0.3f, 0.2f, 0.15f);
            var renderer = bar.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material = material;
            }
        }

        /// <summary>
        /// 创建桌椅
        /// </summary>
        private static void CreateTablesAndChairs(Transform parent)
        {
            // 创建3组桌椅
            Vector3[] tablePositions = {
                new Vector3(-3, 0, 2),
                new Vector3(0, 0, 2),
                new Vector3(3, 0, 2)
            };

            for (int i = 0; i < tablePositions.Length; i++)
            {
                // 桌子
                var table = GameObject.CreatePrimitive(PrimitiveType.Cube);
                table.name = $"Table_{i + 1}";
                table.transform.SetParent(parent);
                table.transform.position = tablePositions[i] + new Vector3(0, 0.4f, 0);
                table.transform.localScale = new Vector3(1.5f, 0.1f, 1.5f);

                var tableMaterial = new Material(Shader.Find("Standard"));
                tableMaterial.color = new Color(0.5f, 0.35f, 0.25f);
                var tableRenderer = table.GetComponent<Renderer>();
                if (tableRenderer != null)
                {
                    tableRenderer.material = tableMaterial;
                }

                // 桌子腿
                var leg = GameObject.CreatePrimitive(PrimitiveType.Cube);
                leg.name = $"TableLeg_{i + 1}";
                leg.transform.SetParent(parent);
                leg.transform.position = tablePositions[i] + new Vector3(0, 0.2f, 0);
                leg.transform.localScale = new Vector3(0.1f, 0.4f, 0.1f);
                leg.GetComponent<Renderer>().material = tableMaterial;

                // 椅子（2把）
                for (int j = 0; j < 2; j++)
                {
                    var chair = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    chair.name = $"Chair_{i + 1}_{j + 1}";
                    chair.transform.SetParent(parent);

                    float offset = j == 0 ? -1.2f : 1.2f;
                    chair.transform.position = tablePositions[i] + new Vector3(offset, 0.25f, 0);
                    chair.transform.localScale = new Vector3(0.5f, 0.5f, 0.5f);

                    var chairMaterial = new Material(Shader.Find("Standard"));
                    chairMaterial.color = new Color(0.4f, 0.3f, 0.2f);
                    var chairRenderer = chair.GetComponent<Renderer>();
                    if (chairRenderer != null)
                    {
                        chairRenderer.material = chairMaterial;
                    }
                }
            }
        }

        #endregion

        #region 城门创建

        /// <summary>
        /// 创建城门
        /// </summary>
        private static void CreateGate()
        {
            // 检查是否已存在
            if (GameObject.Find("Gate") != null) return;

            var gate = new GameObject("Gate");
            gate.transform.position = new Vector3(8, 0, 0);

            // 创建城墙
            var wall1 = GameObject.CreatePrimitive(PrimitiveType.Cube);
            wall1.name = "GateWallLeft";
            wall1.transform.SetParent(gate.transform);
            wall1.transform.position = new Vector3(-3, 2.5f, 0);
            wall1.transform.localScale = new Vector3(4, 5, 2);

            var wall2 = GameObject.CreatePrimitive(PrimitiveType.Cube);
            wall2.name = "GateWallRight";
            wall2.transform.SetParent(gate.transform);
            wall2.transform.position = new Vector3(3, 2.5f, 0);
            wall2.transform.localScale = new Vector3(4, 5, 2);

            // 创建门洞
            var arch = GameObject.CreatePrimitive(PrimitiveType.Cube);
            arch.name = "GateArch";
            arch.transform.SetParent(gate.transform);
            arch.transform.position = new Vector3(0, 2, 0);
            arch.transform.localScale = new Vector3(2, 4, 2.1f);

            // 移除门洞碰撞体（允许通过）
            var archCollider = arch.GetComponent<Collider>();
            if (archCollider != null)
            {
                DestroyImmediate(archCollider);
            }

            // 城墙材质
            var material = new Material(Shader.Find("Standard"));
            material.color = new Color(0.3f, 0.3f, 0.35f);

            var walls = new[] { wall1, wall2 };
            foreach (var wall in walls)
            {
                var renderer = wall.GetComponent<Renderer>();
                if (renderer != null)
                {
                    renderer.material = material;
                }
            }

            Debug.Log("[DemoSceneBuilder] 城门创建完成");
        }

        #endregion

        #region 篝火创建

        /// <summary>
        /// 创建篝火
        /// </summary>
        private static void CreateCampfire()
        {
            // 检查是否已存在
            if (GameObject.Find("Campfire") != null) return;

            var campfire = new GameObject("Campfire");
            campfire.transform.position = new Vector3(0, 0, -7);

            // 创建火堆底座
            var baseObj = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            baseObj.name = "FireBase";
            baseObj.transform.SetParent(campfire.transform);
            baseObj.transform.position = new Vector3(0, 0.1f, 0);
            baseObj.transform.localScale = new Vector3(1, 0.2f, 1);

            var baseMaterial = new Material(Shader.Find("Standard"));
            baseMaterial.color = new Color(0.3f, 0.25f, 0.2f);
            baseObj.GetComponent<Renderer>().material = baseMaterial;

            // 创建点光源
            var fireLight = new GameObject("FireLight");
            fireLight.transform.SetParent(campfire.transform);
            fireLight.transform.position = new Vector3(0, 1f, 0);

            var light = fireLight.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = new Color(1f, 0.6f, 0.2f);
            light.intensity = 1.5f;
            light.range = 10f;

            Debug.Log("[DemoSceneBuilder] 篝火创建完成");
        }

        #endregion

        #region 玩家创建

        /// <summary>
        /// 创建玩家
        /// </summary>
        private static void CreatePlayer()
        {
            // 检查是否已存在
            if (GameObject.Find("Player") != null) return;

            // 创建玩家对象
            var player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            player.name = "Player";
            player.tag = "Player";

            // 设置位置
            player.transform.position = new Vector3(0, 1, 5);

            // 移除碰撞体，使用CharacterController
            var collider = player.GetComponent<Collider>();
            if (collider != null)
            {
                DestroyImmediate(collider);
            }

            // 添加CharacterController
            var controller = player.AddComponent<CharacterController>();
            controller.height = 2f;
            controller.radius = 0.3f;
            controller.center = new Vector3(0, 1f, 0);

            // 设置材质
            var material = new Material(Shader.Find("Standard"));
            material.color = new Color(0.3f, 0.7f, 0.9f);
            player.GetComponent<Renderer>().material = material;

            // 添加PlayerController
            var playerController = player.AddComponent<Demo.PlayerController>();
            playerController.moveSpeed = 5f;
            playerController.rotationSpeed = 10f;

            // 添加InteractionSystem
            player.AddComponent<Demo.InteractionSystem>();

            Debug.Log("[DemoSceneBuilder] 玩家创建完成");
        }

        #endregion

        #region NPC创建

        /// <summary>
        /// 创建NPC
        /// </summary>
        private static void CreateNPCs()
        {
            CreateTavernKeeper();
            CreateGuardCaptain();
            CreateMysticTraveler();

            Debug.Log("[DemoSceneBuilder] NPC创建完成");
        }

        /// <summary>
        /// 创建酒馆老板娘
        /// </summary>
        private static void CreateTavernKeeper()
        {
            if (GameObject.Find("NPC_TavernKeeper") != null) return;

            var npc = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            npc.name = "NPC_TavernKeeper";
            npc.transform.position = new Vector3(0, 1, -2);

            // 移除碰撞体
            var collider = npc.GetComponent<Collider>();
            if (collider != null)
            {
                DestroyImmediate(collider);
            }

            // 设置材质
            var material = new Material(Shader.Find("Standard"));
            material.color = new Color(1f, 0.9f, 0.8f);
            npc.GetComponent<Renderer>().material = material;

            // 添加NPCSoul组件
            var npcSoul = npc.AddComponent<Neshama.SDK.NPCSoul>();

            // 添加AI控制器
            var ai = npc.AddComponent<Demo.NPCTavernKeeper>();
            ai.npcName = "艾拉";
            ai.preset = "tavern_keeper";

            // 创建Spawn点
            var spawn = new GameObject("NPCSpawn_TavernKeeper");
            spawn.transform.position = new Vector3(0, 0, -2);
            spawn.hideFlags = HideFlags.HideInHierarchy;
        }

        /// <summary>
        /// 创建守卫队长
        /// </summary>
        private static void CreateGuardCaptain()
        {
            if (GameObject.Find("NPC_GuardCaptain") != null) return;

            var npc = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            npc.name = "NPC_GuardCaptain";
            npc.transform.position = new Vector3(8, 1, 0);

            // 移除碰撞体
            var collider = npc.GetComponent<Collider>();
            if (collider != null)
            {
                DestroyImmediate(collider);
            }

            // 设置材质
            var material = new Material(Shader.Find("Standard"));
            material.color = new Color(0.7f, 0.8f, 0.9f);
            npc.GetComponent<Renderer>().material = material;

            // 添加NPCSoul组件
            npc.AddComponent<Neshama.SDK.NPCSoul>();

            // 添加AI控制器
            var ai = npc.AddComponent<Demo.NPCGuardCaptain>();
            ai.npcName = "凯尔";
            ai.preset = "guard_captain";

            // 创建Spawn点
            var spawn = new GameObject("NPCSpawn_GuardCaptain");
            spawn.transform.position = new Vector3(8, 0, 0);
            spawn.hideFlags = HideFlags.HideInHierarchy;
        }

        /// <summary>
        /// 创建神秘旅人
        /// </summary>
        private static void CreateMysticTraveler()
        {
            if (GameObject.Find("NPC_MysticTraveler") != null) return;

            var npc = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            npc.name = "NPC_MysticTraveler";
            npc.transform.position = new Vector3(-4, 1, 3);

            // 移除碰撞体
            var collider = npc.GetComponent<Collider>();
            if (collider != null)
            {
                DestroyImmediate(collider);
            }

            // 设置材质
            var material = new Material(Shader.Find("Standard"));
            material.color = new Color(0.8f, 0.7f, 0.9f);
            npc.GetComponent<Renderer>().material = material;

            // 添加NPCSoul组件
            npc.AddComponent<Neshama.SDK.NPCSoul>();

            // 添加AI控制器
            var ai = npc.AddComponent<Demo.NPCMysticTraveler>();
            ai.npcName = "神秘的流浪者";
            ai.preset = "mystic_traveler";

            // 创建Spawn点
            var spawn = new GameObject("NPCSpawn_MysticTraveler");
            spawn.transform.position = new Vector3(-4, 0, 3);
            spawn.hideFlags = HideFlags.HideInHierarchy;
        }

        #endregion

        #region 管理器创建

        /// <summary>
        /// 创建场景管理器
        /// </summary>
        private static void CreateSceneManager()
        {
            if (GameObject.Find("DemoSceneManager") != null) return;

            var manager = new GameObject("DemoSceneManager");
            manager.AddComponent<Demo.DemoSceneManager>();

            Debug.Log("[DemoSceneBuilder] 场景管理器创建完成");
        }

        /// <summary>
        /// 创建UI管理器
        /// </summary>
        private static void CreateUIManager()
        {
            if (GameObject.Find("DemoUIManager") != null) return;

            var manager = new GameObject("DemoUIManager");
            manager.AddComponent<Demo.DemoUIManager>();

            Debug.Log("[DemoSceneBuilder] UI管理器创建完成");
        }

        #endregion

        #region 辅助方法

        /// <summary>
        /// 创建材质
        /// </summary>
        private static Material CreateMaterial(Color color)
        {
            var material = new Material(Shader.Find("Standard"));
            material.color = color;
            return material;
        }

        #endregion
    }
}
