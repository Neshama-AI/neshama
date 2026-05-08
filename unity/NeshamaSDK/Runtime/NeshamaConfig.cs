using System;
using UnityEngine;

namespace Neshama.SDK
{
    /// <summary>
    /// Neshama SDK 配置类
    /// 用于配置SDK连接参数，可通过ProjectSettings持久化
    /// </summary>
    [Serializable]
    public class NeshamaConfig : ScriptableObject
    {
        /// <summary>
        /// 服务器模式：Cloud（云端托管）或 Local（本地部署）
        /// </summary>
        public enum ServerMode
        {
            /// <summary>云端托管模式（默认，免部署）</summary>
            Cloud,
            /// <summary>本地部署模式（需要自己启动后端）</summary>
            Local
        }

        /// <summary>
        /// 云端API地址
        /// </summary>
        private const string CLOUD_BASE_URL = "https://api.neshama.pw";

        /// <summary>
        /// 本地开发API地址
        /// </summary>
        private const string LOCAL_BASE_URL = "http://localhost:8420";

        /// <summary>
        /// 服务器模式
        /// </summary>
        [SerializeField]
        private ServerMode serverMode = ServerMode.Cloud;

        /// <summary>
        /// 服务器基础地址
        /// </summary>
        [SerializeField]
        private string baseUrl = CLOUD_BASE_URL;

        /// <summary>
        /// API Key（从注册或试用获得）
        /// </summary>
        [SerializeField]
        private string apiKey = "";

        /// <summary>
        /// 试用模式（无需API Key，自动获取临时Token）
        /// </summary>
        [SerializeField]
        private bool trialMode = false;

        /// <summary>
        /// 试用Token（自动获取，无需手动填写）
        /// </summary>
        [SerializeField]
        private string trialToken = "";

        /// <summary>
        /// 请求超时时间（秒）
        /// </summary>
        [SerializeField]
        private int timeoutSeconds = 30;

        /// <summary>
        /// 是否启用调试模式
        /// </summary>
        [SerializeField]
        private bool debugMode = false;

        /// <summary>
        /// 最大重试次数
        /// </summary>
        [SerializeField]
        private int maxRetries = 3;

        /// <summary>
        /// 重试间隔时间（秒）
        /// </summary>
        [SerializeField]
        private float retryDelaySeconds = 1f;

        /// <summary>
        /// 是否在Awake时自动连接
        /// </summary>
        [SerializeField]
        private bool autoConnect = true;

        /// <summary>
        /// 默认玩家ID（用于测试）
        /// </summary>
        [SerializeField]
        private string defaultPlayerId = "player_001";

        /// <summary>
        /// API路径前缀
        /// </summary>
        [SerializeField]
        private string apiPrefix = "/api/game";

        /// <summary>
        /// 心跳间隔时间（秒）
        /// </summary>
        [SerializeField]
        private float heartbeatInterval = 30f;

        /// <summary>
        /// 默认NPC预设
        /// </summary>
        [SerializeField]
        private string defaultPreset = "default";

        /// <summary>
        /// 日志级别
        /// </summary>
        [SerializeField]
        private LogLevel logLevel = LogLevel.Info;

        // ── 属性访问器 ──────────────────────────────────────────

        /// <summary>服务器模式</summary>
        public ServerMode CurrentServerMode
        {
            get => serverMode;
            set
            {
                serverMode = value;
                // 自动切换baseUrl
                baseUrl = value == ServerMode.Cloud ? CLOUD_BASE_URL : LOCAL_BASE_URL;
            }
        }

        /// <summary>服务器基础地址</summary>
        public string BaseUrl
        {
            get => baseUrl;
            set => baseUrl = value;
        }

        /// <summary>API Key</summary>
        public string ApiKey
        {
            get => apiKey;
            set => apiKey = value ?? "";
        }

        /// <summary>试用模式</summary>
        public bool TrialMode
        {
            get => trialMode;
            set => trialMode = value;
        }

        /// <summary>试用Token</summary>
        public string TrialToken
        {
            get => trialToken;
            set => trialToken = value ?? "";
        }

        public int TimeoutSeconds
        {
            get => timeoutSeconds;
            set => timeoutSeconds = Mathf.Max(1, value);
        }

        public bool DebugMode
        {
            get => debugMode;
            set => debugMode = value;
        }

        public int MaxRetries
        {
            get => maxRetries;
            set => maxRetries = Mathf.Max(0, value);
        }

        public float RetryDelaySeconds
        {
            get => retryDelaySeconds;
            set => retryDelaySeconds = Mathf.Max(0.1f, value);
        }

        public bool AutoConnect
        {
            get => autoConnect;
            set => autoConnect = value;
        }

        public string DefaultPlayerId
        {
            get => defaultPlayerId;
            set => defaultPlayerId = value ?? "player_001";
        }

        public string ApiPrefix
        {
            get => apiPrefix;
            set => apiPrefix = value ?? "/api/game";
        }

        public float HeartbeatInterval
        {
            get => heartbeatInterval;
            set => heartbeatInterval = Mathf.Max(1f, value);
        }

        public string DefaultPreset
        {
            get => defaultPreset;
            set => defaultPreset = value ?? "default";
        }

        public LogLevel LogLevelValue
        {
            get => logLevel;
            set => logLevel = value;
        }

        /// <summary>
        /// 获取认证头
        /// </summary>
        public string GetAuthHeader()
        {
            if (trialMode && !string.IsNullOrEmpty(trialToken))
            {
                return $"Bearer {trialToken}";
            }
            if (!string.IsNullOrEmpty(apiKey))
            {
                return $"Bearer {apiKey}";
            }
            return "";
        }

        /// <summary>
        /// 是否已配置认证信息
        /// </summary>
        public bool HasAuth()
        {
            return !string.IsNullOrEmpty(apiKey) || (trialMode && !string.IsNullOrEmpty(trialToken));
        }

        /// <summary>
        /// 获取完整的API基础URL
        /// </summary>
        public string GetFullApiBaseUrl()
        {
            return $"{baseUrl.TrimEnd('/')}{apiPrefix}";
        }

        /// <summary>
        /// 构建完整的API URL
        /// </summary>
        /// <param name="endpoint">API端点（如 /npc/{npc_id}/emotion）</param>
        /// <returns>完整的URL</returns>
        public string BuildUrl(string endpoint)
        {
            return $"{GetFullApiBaseUrl()}{endpoint}";
        }

        /// <summary>
        /// 创建默认配置
        /// </summary>
        public static NeshamaConfig CreateDefault()
        {
            return ScriptableObject.CreateInstance<NeshamaConfig>();
        }

        /// <summary>
        /// 日志级别枚举
        /// </summary>
        public enum LogLevel
        {
            /// <summary>调试信息</summary>
            Debug,
            /// <summary>一般信息</summary>
            Info,
            /// <summary>警告信息</summary>
            Warning,
            /// <summary>错误信息</summary>
            Error
        }

        /// <summary>
        /// 输出日志
        /// </summary>
        public void Log(string message, LogLevel level = LogLevel.Info)
        {
            if (!debugMode && level == LogLevel.Debug) return;
            
            var logMessage = $"[Neshama] [{level}] {message}";
            switch (level)
            {
                case LogLevel.Debug:
                    Debug.Log(logMessage);
                    break;
                case LogLevel.Info:
                    Debug.Log(logMessage);
                    break;
                case LogLevel.Warning:
                    Debug.LogWarning(logMessage);
                    break;
                case LogLevel.Error:
                    Debug.LogError(logMessage);
                    break;
            }
        }

        /// <summary>
        /// 验证配置是否有效
        /// </summary>
        /// <returns>配置是否有效</returns>
        public bool IsValid()
        {
            if (string.IsNullOrEmpty(baseUrl))
            {
                Log("BaseUrl is required", LogLevel.Error);
                return false;
            }
            
            if (!baseUrl.StartsWith("http://") && !baseUrl.StartsWith("https://"))
            {
                Log("BaseUrl must start with http:// or https://", LogLevel.Error);
                return false;
            }
            
            if (timeoutSeconds <= 0)
            {
                Log("TimeoutSeconds must be greater than 0", LogLevel.Error);
                return false;
            }
            
            return true;
        }

        public override string ToString()
        {
            var authStatus = HasAuth() ? "Auth: Yes" : "Auth: No";
            return $"NeshamaConfig: Mode={serverMode}, BaseUrl={baseUrl}, Timeout={timeoutSeconds}s, {authStatus}";
        }
    }
}
