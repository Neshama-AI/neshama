using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using Neshama.SDK.Models;

namespace Neshama.SDK
{
    /// <summary>
    /// NPC灵魂组件 - 核心MonoBehaviour
    /// 挂载到NPC GameObject上即可使用，自动管理生命周期
    /// 
    /// 使用方式：
    /// 1. 将此组件添加到NPC的GameObject上
    /// 2. 在Inspector中配置npcId和preset
    /// 3. 调用SendEvent、Chat等方法与NPC交互
    /// 4. 监听OnEmotionChanged等事件获取状态变化
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public class NPCSoul : MonoBehaviour
    {
        #region Inspector配置

        [Header("=== NPC身份配置 ===")]
        
        [Tooltip("NPC唯一标识符，在整个游戏中应该唯一")]
        [SerializeField]
        private string npcId = "npc_001";

        [Tooltip("NPC预设模板类型（如 tavern_keeper, guard_captain 等）")]
        [SerializeField]
        private string preset = "default";

        [Tooltip("NPC显示名称")]
        [SerializeField]
        private string npcName = "NPC";

        [Header("=== 连接配置 ===")]
        
        [Tooltip("是否在Awake时自动连接服务器")]
        [SerializeField]
        private bool autoConnect = true;

        [Tooltip("是否在Destroy时自动断开连接")]
        [SerializeField]
        private bool autoDisconnect = true;

        [Tooltip("使用自定义配置")]
        [SerializeField]
        private bool useCustomConfig = false;

        [Tooltip("自定义配置（当UseCustomConfig为true时使用）")]
        [SerializeField]
        private NeshamaConfig customConfig = null;

        [Header("=== 调试配置 ===")]
        
        [Tooltip("是否在场景中显示调试信息")]
        [SerializeField]
        private bool showDebugInfo = false;

        [Tooltip("调试颜色")]
        [SerializeField]
        private Color debugColor = Color.cyan;

        #endregion

        #region 运行时状态

        /// <summary>
        /// Neshama客户端实例
        /// </summary>
        private NeshamaClient _client;

        /// <summary>
        /// 当前NPC档案
        /// </summary>
        private NPCProfile _profile;

        /// <summary>
        /// 当前情绪状态
        /// </summary>
        private EmotionState _currentEmotion;

        /// <summary>
        /// 当前行为建议
        /// </summary>
        private List<BehaviorHint> _currentBehaviors;

        /// <summary>
        /// 是否已连接
        /// </summary>
        private bool _isConnected;

        /// <summary>
        /// NPC创建时间
        /// </summary>
        private float _connectedTime;

        #endregion

        #region 属性访问器

        /// <summary>
        /// 获取NPC ID
        /// </summary>
        public string NpcId => npcId;

        /// <summary>
        /// 获取NPC名称
        /// </summary>
        public string NpcName => npcName;

        /// <summary>
        /// 获取NPC预设
        /// </summary>
        public string Preset => preset;

        /// <summary>
        /// 获取Neshama客户端
        /// </summary>
        public NeshamaClient Client => _client;

        /// <summary>
        /// 获取当前情绪状态
        /// </summary>
        public EmotionState CurrentEmotion => _currentEmotion;

        /// <summary>
        /// 获取当前行为建议
        /// </summary>
        public List<BehaviorHint> CurrentBehaviors => _currentBehaviors;

        /// <summary>
        /// 是否已连接
        /// </summary>
        public bool IsConnected => _isConnected;

        /// <summary>
        /// 获取运行时间
        /// </summary>
        public float RunningTime => Time.time - _connectedTime;

        #endregion

        #region 事件回调

        /// <summary>
        /// 连接状态变化事件
        /// </summary>
        public event Action<bool> OnConnectionStateChanged;

        /// <summary>
        /// 情绪变化事件
        /// </summary>
        public event Action<EmotionState> OnEmotionChanged;

        /// <summary>
        /// 行为变化事件
        /// </summary>
        public event Action<List<BehaviorHint>> OnBehaviorChanged;

        /// <summary>
        /// 对话响应事件
        /// </summary>
        public event Action<ChatResponse> OnChatResponse;

        /// <summary>
        /// 错误事件
        /// </summary>
        public event Action<string> OnError;

        /// <summary>
        /// 日志事件
        /// </summary>
        public event Action<string> OnLog;

        #endregion

        #region Unity生命周期

        /// <summary>
        /// 唤醒时初始化
        /// </summary>
        private void Awake()
        {
            InitializeClient();
            
            if (autoConnect)
            {
                Connect();
            }
        }

        /// <summary>
        /// 销毁时清理
        /// </summary>
        private void OnDestroy()
        {
            if (autoDisconnect)
            {
                Disconnect();
            }
        }

        /// <summary>
        /// 更新调试信息
        /// </summary>
        private void OnGUI()
        {
            if (!showDebugInfo || !Application.isPlaying) return;
            
            // 在屏幕角落显示NPC状态
            string status = $"[{npcName}]\n" +
                           $"Connected: {_isConnected}\n" +
                           $"Emotion: {_currentEmotion?.dominant ?? "N/A"}\n" +
                           $"Time: {RunningTime:F1}s";
            
            GUIStyle style = new GUIStyle(GUI.skin.box)
            {
                alignment = TextAnchor.UpperLeft,
                fontSize = 12
            };
            
            Color originalColor = GUI.backgroundColor;
            GUI.backgroundColor = debugColor;
            
            Rect rect = new Rect(10, 10, 200, 80);
            GUI.Box(rect, status, style);
            
            GUI.backgroundColor = originalColor;
        }

        /// <summary>
        /// 绘制调试Gizmos
        /// </summary>
        private void OnDrawGizmosSelected()
        {
            if (!showDebugInfo) return;
            
            // 绘制NPC头顶指示器
            Vector3 headPos = transform.position + Vector3.up * 2f;
            Gizmos.color = _isConnected ? Color.green : Color.red;
            Gizmos.DrawWireSphere(headPos, 0.2f);
            
            // 绘制情绪强度指示
            if (_currentEmotion != null)
            {
                float anger = _currentEmotion.Anger;
                float joy = _currentEmotion.Joy;
                
                // 红色表示愤怒
                Gizmos.color = new Color(1f, 0f, 0f, anger);
                Gizmos.DrawWireSphere(headPos, 0.3f + anger * 0.3f);
                
                // 绿色表示喜悦
                Gizmos.color = new Color(0f, 1f, 0f, joy);
                Gizmos.DrawWireSphere(headPos, 0.3f + joy * 0.3f);
            }
        }

        #endregion

        #region 初始化方法

        /// <summary>
        /// 初始化客户端
        /// </summary>
        private void InitializeClient()
        {
            // 获取或创建配置
            NeshamaConfig config;
            if (useCustomConfig && customConfig != null)
            {
                config = customConfig;
            }
            else
            {
                config = NeshamaConfig.CreateDefault();
            }

            // 创建客户端
            _client = new NeshamaClient(config, this);

            // 订阅客户端事件
            _client.OnConnectionStateChanged += HandleConnectionStateChanged;
            _client.OnEmotionChanged += HandleEmotionChanged;
            _client.OnBehaviorChanged += HandleBehaviorChanged;
            _client.OnChatResponse += HandleChatResponse;
            _client.OnError += HandleError;
            _client.OnLog += HandleLog;

            Log($"NPCSoul initialized for {npcName}");
        }

        #endregion

        #region 配置方法

        /// <summary>
        /// 配置NPC参数（在连接前调用）
        /// </summary>
        /// <param name="npcId">NPC唯一标识</param>
        /// <param name="npcName">NPC名称</param>
        /// <param name="preset">预设模板</param>
        /// <param name="autoConnect">是否自动连接</param>
        public void Configure(string npcId, string npcName, string preset, bool autoConnect = true)
        {
            this.npcId = npcId;
            this.npcName = npcName;
            this.preset = preset;
            this.autoConnect = autoConnect;
        }

        #endregion

        #region 连接管理

        /// <summary>
        /// 连接到Neshama服务器
        /// </summary>
        /// <returns>连接任务</returns>
        public async Task Connect()
        {
            if (_isConnected)
            {
                Log("Already connected");
                return;
            }

            Log($"Connecting to Neshama server...");
            
            try
            {
                // 首先尝试获取或创建NPC档案
                await EnsureNPCExistsAsync();
                
                // 连接客户端
                await _client.ConnectAsync();
                
                // 获取初始状态
                await RefreshStateAsync();
            }
            catch (Exception ex)
            {
                Log($"Connection failed: {ex.Message}");
                OnError?.Invoke($"Connection failed: {ex.Message}");
            }
        }

        /// <summary>
        /// 确保NPC在服务器上存在
        /// </summary>
        private async Task EnsureNPCExistsAsync()
        {
            try
            {
                // 尝试获取现有档案
                _profile = await _client.GetProfileAsync(npcId);
                
                if (_profile != null)
                {
                    Log($"NPC profile loaded: {_profile.name}");
                }
            }
            catch
            {
                // NPC不存在，创建新的
                Log($"Creating new NPC: {npcName} ({preset})");
                var response = await _client.CreateNPCAsync(npcName, preset);
                
                if (response != null && response.success)
                {
                    _profile = response.profile;
                    npcId = response.npc_id;
                    Log($"NPC created with ID: {npcId}");
                }
                else
                {
                    Log($"Failed to create NPC: {response?.error ?? "Unknown error"}");
                }
            }
        }

        /// <summary>
        /// 刷新NPC状态
        /// </summary>
        private async Task RefreshStateAsync()
        {
            try
            {
                // 获取当前情绪
                _currentEmotion = await _client.GetEmotionAsync(npcId);
                OnEmotionChanged?.Invoke(_currentEmotion);
                
                // 获取行为建议
                _currentBehaviors = (await _client.GetBehaviorHintsAsync(npcId))?.modifiers;
                OnBehaviorChanged?.Invoke(_currentBehaviors);
            }
            catch (Exception ex)
            {
                Log($"Failed to refresh state: {ex.Message}");
            }
        }

        /// <summary>
        /// 断开连接
        /// </summary>
        public void Disconnect()
        {
            if (_client != null)
            {
                _client.Disconnect();
            }
            
            _isConnected = false;
            OnConnectionStateChanged?.Invoke(false);
            
            Log("Disconnected from Neshama server");
        }

        #endregion

        #region 核心交互方法

        /// <summary>
        /// 发送游戏事件
        /// </summary>
        /// <param name="eventType">事件类型</param>
        /// <param name="intensity">事件强度（0-1）</param>
        /// <param name="context">上下文数据</param>
        /// <returns>事件响应</returns>
        public async Task<EventResponse> SendEvent(Enums.GameEventType eventType, 
            float intensity = 1f, Dictionary<string, object> context = null)
        {
            if (!_isConnected)
            {
                Log("Not connected, cannot send event");
                return null;
            }

            Log($"Sending event: {eventType} (intensity={intensity})");
            
            try
            {
                var response = await _client.SendEventAsync(npcId, eventType, intensity, context);
                
                if (response != null)
                {
                    Log($"Event processed. Dominant emotion: {response.emotion_state?.dominant}");
                }
                
                return response;
            }
            catch (Exception ex)
            {
                Log($"Failed to send event: {ex.Message}");
                OnError?.Invoke(ex.Message);
                return null;
            }
        }

        /// <summary>
        /// 发送游戏事件（使用字符串类型）
        /// </summary>
        public async Task<EventResponse> SendEvent(string eventType, 
            float intensity = 1f, Dictionary<string, object> context = null)
        {
            if (!_isConnected)
            {
                Log("Not connected, cannot send event");
                return null;
            }

            var gameEvent = new GameEvent(eventType, intensity, context);
            Log($"Sending event: {eventType} (intensity={intensity})");
            
            try
            {
                var response = await _client.SendEventAsync(npcId, gameEvent);
                return response;
            }
            catch (Exception ex)
            {
                Log($"Failed to send event: {ex.Message}");
                OnError?.Invoke(ex.Message);
                return null;
            }
        }

        /// <summary>
        /// 与NPC对话
        /// </summary>
        /// <param name="message">消息内容</param>
        /// <param name="playerId">玩家ID</param>
        /// <returns>对话响应</returns>
        public async Task<ChatResponse> Chat(string message, string playerId = null)
        {
            if (!_isConnected)
            {
                Log("Not connected, cannot chat");
                return null;
            }

            Log($"Sending chat: {message}");
            
            try
            {
                var response = await _client.ChatAsync(npcId, message, playerId);
                
                if (response != null && response.success)
                {
                    Log($"NPC response: {response.content}");
                }
                else
                {
                    Log($"Chat failed: {response?.error ?? "Unknown error"}");
                }
                
                return response;
            }
            catch (Exception ex)
            {
                Log($"Failed to chat: {ex.Message}");
                OnError?.Invoke(ex.Message);
                return null;
            }
        }

        /// <summary>
        /// 获取当前情绪状态
        /// </summary>
        /// <returns>情绪状态</returns>
        public async Task<EmotionState> GetCurrentEmotion()
        {
            if (!_isConnected)
            {
                Log("Not connected");
                return _currentEmotion;
            }

            try
            {
                _currentEmotion = await _client.GetEmotionAsync(npcId);
                return _currentEmotion;
            }
            catch (Exception ex)
            {
                Log($"Failed to get emotion: {ex.Message}");
                return _currentEmotion;
            }
        }

        /// <summary>
        /// 获取行为建议
        /// </summary>
        /// <returns>行为建议列表</returns>
        public async Task<List<BehaviorHint>> GetBehaviorHints()
        {
            if (!_isConnected)
            {
                Log("Not connected");
                return _currentBehaviors;
            }

            try
            {
                var response = await _client.GetBehaviorHintsAsync(npcId);
                _currentBehaviors = response?.modifiers;
                return _currentBehaviors;
            }
            catch (Exception ex)
            {
                Log($"Failed to get behavior hints: {ex.Message}");
                return _currentBehaviors;
            }
        }

        #endregion

        #region 记忆管理

        /// <summary>
        /// 让NPC记住实体
        /// </summary>
        /// <param name="entityType">实体类型（player, npc, item等）</param>
        /// <param name="entityName">实体名称</param>
        /// <param name="relation">关系类型（ally, enemy, neutral等）</param>
        /// <param name="note">备注信息</param>
        /// <returns>记忆响应</returns>
        public async Task<RememberResponse> RememberEntity(string entityType, 
            string entityName, string relation = null, string note = null)
        {
            if (!_isConnected)
            {
                Log("Not connected");
                return null;
            }

            Log($"NPC remembering: {entityName} ({entityType})");
            
            try
            {
                return await _client.RememberAsync(npcId, entityType, entityName, relation, note);
            }
            catch (Exception ex)
            {
                Log($"Failed to remember: {ex.Message}");
                OnError?.Invoke(ex.Message);
                return null;
            }
        }

        /// <summary>
        /// 获取NPC的记忆
        /// </summary>
        /// <param name="query">查询条件（可选）</param>
        /// <returns>记忆列表</returns>
        public async Task<List<Memory>> GetMemories(string query = null)
        {
            if (!_isConnected)
            {
                Log("Not connected");
                return null;
            }

            try
            {
                var response = await _client.GetMemoryAsync(npcId, query);
                return response?.memories;
            }
            catch (Exception ex)
            {
                Log($"Failed to get memories: {ex.Message}");
                return null;
            }
        }

        #endregion

        #region 关系图谱

        /// <summary>
        /// 获取关系图谱
        /// </summary>
        /// <returns>关系图谱</returns>
        public async Task<RelationGraph> GetRelations()
        {
            if (!_isConnected)
            {
                Log("Not connected");
                return null;
            }

            try
            {
                return await _client.GetRelationsAsync(npcId);
            }
            catch (Exception ex)
            {
                Log($"Failed to get relations: {ex.Message}");
                return null;
            }
        }

        #endregion

        #region 辅助判断方法

        /// <summary>
        /// 判断NPC当前是否愤怒
        /// </summary>
        public bool IsAngry()
        {
            return _currentEmotion != null && _currentEmotion.Anger > 0.5f;
        }

        /// <summary>
        /// 判断NPC当前是否开心
        /// </summary>
        public bool IsHappy()
        {
            return _currentEmotion != null && _currentEmotion.Joy > 0.5f;
        }

        /// <summary>
        /// 判断NPC当前是否恐惧
        /// </summary>
        public bool IsAfraid()
        {
            return _currentEmotion != null && _currentEmotion.Fear > 0.5f;
        }

        /// <summary>
        /// 判断NPC是否愿意与玩家交流
        /// </summary>
        public bool IsWillingToTalk()
        {
            if (_currentBehaviors == null) return true;
            
            foreach (var behavior in _currentBehaviors)
            {
                if (behavior.suggested_actions != null && 
                    behavior.suggested_actions.Contains("refuse_conversation"))
                {
                    return false;
                }
            }
            return true;
        }

        /// <summary>
        /// 获取当前对话风格
        /// </summary>
        public string GetCurrentDialogueStyle()
        {
            if (_currentBehaviors == null) return "neutral";
            
            foreach (var behavior in _currentBehaviors)
            {
                if (behavior.IsDialogueStyleChange())
                {
                    return behavior.value;
                }
            }
            return "neutral";
        }

        /// <summary>
        /// 判断任务是否被锁定
        /// </summary>
        public bool IsQuestLocked()
        {
            if (_currentBehaviors == null) return false;
            
            foreach (var behavior in _currentBehaviors)
            {
                if (behavior.IsQuestLocked())
                {
                    return true;
                }
            }
            return false;
        }

        #endregion

        #region 事件处理器

        private void HandleConnectionStateChanged(bool connected)
        {
            _isConnected = connected;
            _connectedTime = connected ? Time.time : 0;
            
            Log($"Connection state changed: {connected}");
            OnConnectionStateChanged?.Invoke(connected);
        }

        private void HandleEmotionChanged(EmotionState emotion)
        {
            var oldEmotion = _currentEmotion;
            _currentEmotion = emotion;
            
            Log($"Emotion changed: {emotion?.dominant ?? "unknown"}");
            OnEmotionChanged?.Invoke(emotion);
        }

        private void HandleBehaviorChanged(List<BehaviorHint> behaviors)
        {
            _currentBehaviors = behaviors;
            
            Log($"Behavior changed: {behaviors?.Count ?? 0} modifiers");
            OnBehaviorChanged?.Invoke(behaviors);
        }

        private void HandleChatResponse(ChatResponse response)
        {
            Log($"Chat response received");
            OnChatResponse?.Invoke(response);
        }

        private void HandleError(string error)
        {
            Log($"Error: {error}");
            OnError?.Invoke(error);
        }

        private void HandleLog(string message)
        {
            OnLog?.Invoke(message);
        }

        #endregion

        #region 日志

        /// <summary>
        /// 输出日志
        /// </summary>
        private void Log(string message)
        {
            Debug.Log($"[NPCSoul:{npcName}] {message}");
        }

        #endregion
    }
}
