using UnityEngine;

namespace Neshama.Demo
{
    /// <summary>
    /// Demo配置文件 - ScriptableObject格式
    /// 用于在Unity Editor中配置Demo运行时参数
    /// </summary>
    [CreateAssetMenu(fileName = "NeshamaDemoConfig", menuName = "Neshama/Demo Configuration")]
    public class NeshamaDemoConfig : ScriptableObject
    {
        #region 服务器配置

        [Header("=== 服务器配置 ===")]
        
        [Tooltip("Neshama服务器地址")]
        [SerializeField]
        private string serverUrl = "http://localhost:8420";

        [Tooltip("API路径前缀")]
        [SerializeField]
        private string apiPrefix = "/api/game";

        [Tooltip("请求超时时间（秒）")]
        [SerializeField]
        private int timeoutSeconds = 30;

        [Tooltip("心跳间隔时间（秒）")]
        [SerializeField]
        private float heartbeatInterval = 30f;

        [Tooltip("最大重试次数")]
        [SerializeField]
        private int maxRetries = 3;

        #endregion

        #region 玩家配置

        [Header("=== 玩家配置 ===")]

        [Tooltip("玩家ID")]
        [SerializeField]
        private string playerId = "demo_player";

        [Tooltip("玩家名称")]
        [SerializeField]
        private string playerName = "冒险者";

        #endregion

        #region NPC配置

        [Header("=== NPC配置 ===")]

        [Tooltip("是否自动创建NPC")]
        [SerializeField]
        private bool autoCreateNPCs = true;

        [Tooltip("酒馆老板娘预设")]
        [SerializeField]
        private string tavernKeeperPreset = "tavern_keeper";

        [Tooltip("守卫队长预设")]
        [SerializeField]
        private string guardCaptainPreset = "guard_captain";

        [Tooltip("神秘旅人预设")]
        [SerializeField]
        private string mysticTravelerPreset = "mystic_traveler";

        [Tooltip("NPC交互触发距离")]
        [SerializeField]
        private float npcInteractionDistance = 3f;

        [Tooltip("NPC交互冷却时间")]
        [SerializeField]
        private float npcInteractionCooldown = 5f;

        #endregion

        #region 连接配置

        [Header("=== 连接配置 ===")]

        [Tooltip("是否在Awake时自动连接")]
        [SerializeField]
        private bool autoConnect = true;

        [Tooltip("是否启用WebSocket实时通知")]
        [SerializeField]
        private bool enableWebSocket = true;

        [Tooltip("是否自动重连")]
        [SerializeField]
        private bool autoReconnect = true;

        [Tooltip("重连间隔时间（秒）")]
        [SerializeField]
        private float reconnectInterval = 5f;

        #endregion

        #region 调试配置

        [Header("=== 调试配置 ===")]

        [Tooltip("是否显示调试信息")]
        [SerializeField]
        private bool showDebugInfo = true;

        [Tooltip("是否显示情绪面板")]
        [SerializeField]
        private bool showEmotionPanel = true;

        [Tooltip("是否显示快捷事件栏")]
        [SerializeField]
        private bool showQuickEventBar = true;

        [Tooltip("日志级别")]
        [SerializeField]
        private LogLevel debugLogLevel = LogLevel.Info;

        #endregion

        #region Demo引导配置

        [Header("=== Demo引导配置 ===")]

        [Tooltip("是否启用Demo引导模式")]
        [SerializeField]
        private bool enableGuidedMode = true;

        [Tooltip("是否显示控制说明")]
        [SerializeField]
        private bool showControlsHelp = true;

        [Tooltip("是否显示首次见面提示")]
        [SerializeField]
        private bool showFirstMeetTips = true;

        [Tooltip("引导提示延迟时间（秒）")]
        [SerializeField]
        private float tipDisplayDelay = 2f;

        #endregion

        #region 场景配置

        [Header("=== 场景配置 ===")]

        [Tooltip("酒馆位置")]
        [SerializeField]
        private Vector3 tavernPosition = new Vector3(0, 0, 0);

        [Tooltip("城门位置")]
        [SerializeField]
        private Vector3 gatePosition = new Vector3(8, 0, 0);

        [Tooltip("玩家初始位置")]
        [SerializeField]
        private Vector3 playerStartPosition = new Vector3(0, 1, 5);

        #endregion

        #region 属性访问器

        public string ServerUrl => serverUrl;
        public string ApiPrefix => apiPrefix;
        public int TimeoutSeconds => timeoutSeconds;
        public float HeartbeatInterval => heartbeatInterval;
        public int MaxRetries => maxRetries;

        public string PlayerId => playerId;
        public string PlayerName => playerName;

        public bool AutoCreateNPCs => autoCreateNPCs;
        public string TavernKeeperPreset => tavernKeeperPreset;
        public string GuardCaptainPreset => guardCaptainPreset;
        public string MysticTravelerPreset => mysticTravelerPreset;
        public float NpcInteractionDistance => npcInteractionDistance;
        public float NpcInteractionCooldown => npcInteractionCooldown;

        public bool AutoConnect => autoConnect;
        public bool EnableWebSocket => enableWebSocket;
        public bool AutoReconnect => autoReconnect;
        public float ReconnectInterval => reconnectInterval;

        public bool ShowDebugInfo => showDebugInfo;
        public bool ShowEmotionPanel => showEmotionPanel;
        public bool ShowQuickEventBar => showQuickEventBar;
        public LogLevel DebugLogLevel => debugLogLevel;

        public bool EnableGuidedMode => enableGuidedMode;
        public bool ShowControlsHelp => showControlsHelp;
        public bool ShowFirstMeetTips => showFirstMeetTips;
        public float TipDisplayDelay => tipDisplayDelay;

        public Vector3 TavernPosition => tavernPosition;
        public Vector3 GatePosition => gatePosition;
        public Vector3 PlayerStartPosition => playerStartPosition;

        #endregion

        #region 日志级别

        public enum LogLevel
        {
            Debug,
            Info,
            Warning,
            Error
        }

        #endregion

        #region 静态实例

        /// <summary>
        /// 获取默认配置
        /// </summary>
        public static NeshamaDemoConfig GetDefaultConfig()
        {
            var config = CreateInstance<NeshamaDemoConfig>();
            return config;
        }

        /// <summary>
        /// 从资源加载配置
        /// </summary>
        public static NeshamaDemoConfig LoadConfig()
        {
            var configs = UnityEngine.Resources.LoadAll<NeshamaDemoConfig>("DemoSettings");
            if (configs.Length > 0)
            {
                return configs[0];
            }
            return GetDefaultConfig();
        }

        #endregion

        #region 验证

        /// <summary>
        /// 验证配置是否有效
        /// </summary>
        public bool Validate()
        {
            if (string.IsNullOrEmpty(serverUrl))
            {
                Debug.LogError("[NeshamaDemoConfig] 服务器地址不能为空");
                return false;
            }

            if (string.IsNullOrEmpty(playerId))
            {
                Debug.LogError("[NeshamaDemoConfig] 玩家ID不能为空");
                return false;
            }

            if (timeoutSeconds < 1)
            {
                Debug.LogWarning("[NeshamaDemoConfig] 超时时间过短，已调整为默认值");
                timeoutSeconds = 30;
            }

            return true;
        }

        #endregion
    }
}
