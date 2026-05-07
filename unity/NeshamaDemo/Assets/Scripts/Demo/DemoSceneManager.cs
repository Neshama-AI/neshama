using System;
using System.Collections.Generic;
using UnityEngine;
using Neshama.SDK;
using Neshama.SDK.Models;
using Neshama.SDK.Enums;

namespace Neshama.Demo
{
    /// <summary>
    /// Demo场景管理器 - 负责场景初始化和全局管理
    /// 
    /// 功能：
    /// - 连接Neshama服务器
    /// - 创建和管理3个Demo NPC
    /// - 设置酒馆场景环境（光照、摄像机）
    /// - 全局事件监听（WebSocket情绪变化通知）
    /// </summary>
    public class DemoSceneManager : MonoBehaviour
    {
        #region 单例

        private static DemoSceneManager _instance;
        public static DemoSceneManager Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = FindObjectOfType<DemoSceneManager>();
                }
                return _instance;
            }
        }

        #endregion

        #region 配置

        [Header("=== 服务器配置 ===")]
        [Tooltip("Neshama服务器地址")]
        [SerializeField] private string serverUrl = "http://localhost:8420";

        [Tooltip("玩家ID")]
        [SerializeField] private string playerId = "demo_player";

        [Header("=== NPC预设配置 ===")]
        [Tooltip("酒馆老板娘预设")]
        [SerializeField] private string tavernKeeperPreset = "tavern_keeper";

        [Tooltip("守卫队长预设")]
        [SerializeField] private string guardCaptainPreset = "guard_captain";

        [Tooltip("神秘旅人预设")]
        [SerializeField] private string mysticTravelerPreset = "mystic_traveler";

        [Header("=== 场景配置 ===")]
        [Tooltip("是否自动创建NPC")]
        [SerializeField] private bool autoCreateNPCs = true;

        [Tooltip("是否启用WebSocket实时通知")]
        [SerializeField] private bool enableWebSocket = true;

        [Tooltip("是否显示调试信息")]
        [SerializeField] private bool showDebugInfo = true;

        #endregion

        #region 运行时数据

        /// <summary>
        /// 所有注册的NPC列表
        /// </summary>
        private List<NPCSoul> _registeredNPCs = new List<NPCSoul>();

        /// <summary>
        /// Neshama客户端实例
        /// </summary>
        private NeshamaClient _neshamaClient;

        /// <summary>
        /// 是否已初始化
        /// </summary>
        private bool _isInitialized = false;

        /// <summary>
        /// 初始化完成回调
        /// </summary>
        public event Action OnInitializationComplete;

        #endregion

        #region Unity生命周期

        /// <summary>
        /// 唤醒时初始化
        /// </summary>
        private void Awake()
        {
            // 单例设置
            if (_instance != null && _instance != this)
            {
                Destroy(gameObject);
                return;
            }
            _instance = this;

            // 初始化客户端
            InitializeClient();
        }

        /// <summary>
        /// 启动时完成场景设置
        /// </summary>
        private void Start()
        {
            // 设置场景环境
            SetupSceneEnvironment();

            // 创建NPC
            if (autoCreateNPCs)
            {
                CreateDemoNPCs();
            }

            // 注册全局事件监听
            RegisterGlobalEventListeners();

            _isInitialized = true;
            OnInitializationComplete?.Invoke();

            if (showDebugInfo)
            {
                Debug.Log("[DemoSceneManager] 场景初始化完成！");
            }
        }

        /// <summary>
        /// 销毁时清理
        /// </summary>
        private void OnDestroy()
        {
            if (_instance == this)
            {
                _instance = null;
            }

            // 断开服务器连接
            _neshamaClient?.Disconnect();
        }

        #endregion

        #region 初始化

        /// <summary>
        /// 初始化Neshama客户端
        /// </summary>
        private void InitializeClient()
        {
            var config = new NeshamaConfig
            {
                BaseUrl = serverUrl,
                DefaultPlayerId = playerId,
                DebugMode = showDebugInfo,
                AutoConnect = true
            };

            _neshamaClient = new NeshamaClient(config, this);

            // 监听连接状态
            _neshamaClient.OnConnectionStateChanged += (connected) =>
            {
                if (showDebugInfo)
                {
                    Debug.Log($"[DemoSceneManager] 服务器连接状态: {(connected ? "已连接" : "未连接")}");
                }
            };

            // 监听错误
            _neshamaClient.OnError += (error) =>
            {
                Debug.LogWarning($"[DemoSceneManager] 错误: {error}");
            };

            // 尝试连接
            _ = _neshamaClient.ConnectAsync();
        }

        /// <summary>
        /// 设置场景环境（光照、摄像机等）
        /// </summary>
        private void SetupSceneEnvironment()
        {
            // 设置光照 - 暖色酒馆氛围
            var directionalLight = FindObjectOfType<Light>();
            if (directionalLight != null)
            {
                directionalLight.color = new Color(1f, 0.95f, 0.85f);
                directionalLight.intensity = 0.8f;
                directionalLight.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            }

            // 设置环境光
            RenderSettings.ambientLight = new Color(0.4f, 0.35f, 0.3f);
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.6f, 0.5f, 0.4f);
            RenderSettings.fogDensity = 0.02f;

            if (showDebugInfo)
            {
                Debug.Log("[DemoSceneManager] 场景环境设置完成");
            }
        }

        #endregion

        #region NPC管理

        /// <summary>
        /// 创建Demo NPC
        /// </summary>
        private void CreateDemoNPCs()
        {
            // 查找场景中的NPC Spawn点
            Transform tavernKeeperSpawn = GameObject.Find("NPCSpawn_TavernKeeper")?.transform;
            Transform guardCaptainSpawn = GameObject.Find("NPCSpawn_GuardCaptain")?.transform;
            Transform mysticTravelerSpawn = GameObject.Find("NPCSpawn_MysticTraveler")?.transform;

            // 如果没有Spawn点，使用默认位置
            if (tavernKeeperSpawn == null)
            {
                tavernKeeperSpawn = CreateDefaultSpawn("NPCSpawn_TavernKeeper", new Vector3(0, 0, 0));
            }
            if (guardCaptainSpawn == null)
            {
                guardCaptainSpawn = CreateDefaultSpawn("NPCSpawn_GuardCaptain", new Vector3(8, 0, 0));
            }
            if (mysticTravelerSpawn == null)
            {
                mysticTravelerSpawn = CreateDefaultSpawn("NPCSpawn_MysticTraveler", new Vector3(-4, 0, 3));
            }

            // 创建酒馆老板娘
            CreateNPC("艾拉", "tavern_keeper", tavernKeeperPreset, tavernKeeperSpawn.position, tavernKeeperSpawn.rotation);

            // 创建守卫队长
            CreateNPC("凯尔", "guard_captain", guardCaptainPreset, guardCaptainSpawn.position, guardCaptainSpawn.rotation);

            // 创建神秘旅人
            CreateNPC("神秘的流浪者", "mystic_traveler", mysticTravelerPreset, mysticTravelerSpawn.position, mysticTravelerSpawn.rotation);

            if (showDebugInfo)
            {
                Debug.Log($"[DemoSceneManager] 已创建 {_registeredNPCs.Count} 个NPC");
            }
        }

        /// <summary>
        /// 创建默认Spawn点
        /// </summary>
        private Transform CreateDefaultSpawn(string name, Vector3 position)
        {
            var go = new GameObject(name);
            go.transform.position = position;
            go.hideFlags = HideFlags.HideInHierarchy;
            return go.transform;
        }

        /// <summary>
        /// 创建单个NPC
        /// </summary>
        public NPCSoul CreateNPC(string npcName, string npcId, string preset, Vector3 position, Quaternion rotation)
        {
            // 创建NPC GameObject（使用Capsule作为简单模型）
            var npcObj = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            npcObj.name = $"NPC_{npcId}";
            npcObj.transform.position = position;
            npcObj.transform.rotation = rotation;

            // 移除默认碰撞体，使用触发区
            var defaultCollider = npcObj.GetComponent<Collider>();
            if (defaultCollider != null)
            {
                Destroy(defaultCollider);
            }

            // 添加碰撞体
            var collider = npcObj.AddComponent<CapsuleCollider>();
            collider.height = 2f;
            collider.center = new Vector3(0, 1f, 0);

            // 添加NPCSoul组件
            var npcSoul = npcObj.AddComponent<NPCSoul>();
            npcSoul.SetNpcId(npcId);
            npcSoul.SetNpcName(npcName);
            npcSoul.SetPreset(preset);
            npcSoul.AutoConnect = true;
            npcSoul.ShowDebugInfo = showDebugInfo;

            // 注册到列表
            _registeredNPCs.Add(npcSoul);

            // 监听NPC事件
            npcSoul.OnEmotionChanged += (emotion) =>
            {
                OnNPCEmotionChanged(npcSoul, emotion);
            };

            npcSoul.OnError += (error) =>
            {
                Debug.LogWarning($"[{npcName}] 错误: {error}");
            };

            if (showDebugInfo)
            {
                Debug.Log($"[DemoSceneManager] 创建NPC: {npcName} (ID: {npcId})");
            }

            return npcSoul;
        }

        /// <summary>
        /// 根据ID获取NPC
        /// </summary>
        public NPCSoul GetNPC(string npcId)
        {
            return _registeredNPCs.Find(npc => npc.NpcId == npcId);
        }

        /// <summary>
        /// 获取所有NPC
        /// </summary>
        public List<NPCSoul> GetAllNPCs()
        {
            return new List<NPCSoul>(_registeredNPCs);
        }

        #endregion

        #region 事件处理

        /// <summary>
        /// 注册全局事件监听
        /// </summary>
        private void RegisterGlobalEventListeners()
        {
            // 监听所有NPC的情绪变化
            foreach (var npc in _registeredNPCs)
            {
                npc.OnEmotionChanged += (emotion) =>
                {
                    BroadcastSocialEvent(npc, emotion);
                };
            }
        }

        /// <summary>
        /// NPC情绪变化回调
        /// </summary>
        private void OnNPCEmotionChanged(NPCSoul npc, EmotionState emotion)
        {
            if (showDebugInfo)
            {
                Debug.Log($"[{npc.NpcName}] 情绪变化: {emotion.dominant} (强度: {emotion.GetHighestValue():F2})");
            }

            // 触发剧情条件检查
            CheckStoryTriggers(npc, emotion);
        }

        /// <summary>
        /// 广播社交事件（NPC间的 gossip）
        /// </summary>
        private void BroadcastSocialEvent(NPCSoul sourceNPC, EmotionState emotion)
        {
            if (!enableWebSocket) return;

            // 通知其他NPC
            foreach (var npc in _registeredNPCs)
            {
                if (npc != sourceNPC && emotion.IsNegative())
                {
                    // 如果一个NPC不高兴，可能影响其他NPC对这个玩家的态度
                    // 这里可以扩展为实际的gossip系统
                    if (showDebugInfo)
                    {
                        Debug.Log($"[{npc.NpcName}] 听说了关于你的消息...");
                    }
                }
            }
        }

        /// <summary>
        /// 检查剧情触发条件
        /// </summary>
        private void CheckStoryTriggers(NPCSoul npc, EmotionState emotion)
        {
            // 守卫队长愤怒 > 0.8 -> 城门戒严
            if (npc.NpcId == "guard_captain" && emotion.Anger > 0.8f)
            {
                TriggerStoryEvent("城门戒严！守卫变得更加警惕。");
            }

            // 酒馆老板娘快乐 > 0.7 -> 解锁特殊对话
            if (npc.NpcId == "tavern_keeper" && emotion.Joy > 0.7f)
            {
                TriggerStoryEvent("艾拉看起来心情很好，也许可以问问她一些私密的事情...");
            }
        }

        /// <summary>
        /// 触发剧情事件
        /// </summary>
        public void TriggerStoryEvent(string message)
        {
            if (showDebugInfo)
            {
                Debug.Log($"[剧情] {message}");
            }

            // 通知UI显示剧情提示
            DemoUIManager.Instance?.ShowStoryNotification(message);
        }

        #endregion

        #region 公共方法

        /// <summary>
        /// 向服务器发送全局事件
        /// </summary>
        public void SendGlobalEvent(GameEventType eventType, float intensity)
        {
            // 向所有NPC发送事件
            foreach (var npc in _registeredNPCs)
            {
                npc.SendEvent(eventType, intensity);
            }
        }

        /// <summary>
        /// 获取Neshama客户端
        /// </summary>
        public NeshamaClient GetClient()
        {
            return _neshamaClient;
        }

        /// <summary>
        /// 获取玩家ID
        /// </summary>
        public string GetPlayerId()
        {
            return playerId;
        }

        /// <summary>
        /// 检查是否初始化完成
        /// </summary>
        public bool IsInitialized()
        {
            return _isInitialized;
        }

        #endregion
    }

    /// <summary>
    /// NPCSoul扩展方法（用于Demo中的便捷配置）
    /// </summary>
    public static class NPCSoulExtensions
    {
        /// <summary>
        /// 设置NPC ID
        /// </summary>
        public static void SetNpcId(this NPCSoul npcSoul, string npcId)
        {
            // 通过反射设置私有字段（Demo用途）
            var field = typeof(NPCSoul).GetField("npcId", 
                System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            field?.SetValue(npcSoul, npcId);
        }

        /// <summary>
        /// 设置NPC名称
        /// </summary>
        public static void SetNpcName(this NPCSoul npcSoul, string npcName)
        {
            var field = typeof(NPCSoul).GetField("npcName", 
                System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            field?.SetValue(npcSoul, npcName);
        }

        /// <summary>
        /// 设置预设
        /// </summary>
        public static void SetPreset(this NPCSoul npcSoul, string preset)
        {
            var field = typeof(NPCSoul).GetField("preset", 
                System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            field?.SetValue(npcSoul, preset);
        }

        /// <summary>
        /// 设置是否显示调试信息
        /// </summary>
        public static void SetShowDebugInfo(this NPCSoul npcSoul, bool show)
        {
            var field = typeof(NPCSoul).GetField("showDebugInfo", 
                System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            field?.SetValue(npcSoul, show);
        }
    }

    /// <summary>
    /// Demo专用属性别名（方便Inspector配置）
    /// </summary>
    public class DemoConfig
    {
        // 由于无法直接修改NPCSoul的序列化字段
        // Demo中使用这些扩展属性进行配置
    }
}
