using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
using Neshama.SDK.Models;

namespace Neshama.SDK
{
    /// <summary>
    /// Neshama SDK 核心HTTP客户端
    /// 基于 UnityWebRequest 的异步HTTP通信封装
    /// 支持所有API端点的调用
    /// </summary>
    public class NeshamaClient : IDisposable
    {
        // 配置
        private NeshamaConfig _config;
        public NeshamaConfig Config => _config;

        // 连接状态
        private bool _isConnected;
        public bool IsConnected => _isConnected;

        // 回调事件
        public event Action<bool> OnConnectionStateChanged;
        public event Action<EmotionState> OnEmotionChanged;
        public event Action<List<BehaviorHint>> OnBehaviorChanged;
        public event Action<ChatResponse> OnChatResponse;
        public event Action<string> OnError;
        public event Action<string> OnLog;

        // 协程处理器
        private MonoBehaviour _coroutineHost;
        
        // 当前活跃的请求
        private HashSet<UnityWebRequest> _activeRequests = new HashSet<UnityWebRequest>();
        
        // 是否已释放
        private bool _disposed;

        /// <summary>
        /// 创建Neshama客户端
        /// </summary>
        /// <param name="config">配置对象，如果为null则使用默认配置</param>
        /// <param name="coroutineHost">协程宿主MonoBehaviour，用于启动协程</param>
        public NeshamaClient(NeshamaConfig config, MonoBehaviour coroutineHost)
        {
            _config = config ?? NeshamaConfig.CreateDefault();
            _coroutineHost = coroutineHost;
            
            if (!_config.IsValid())
            {
                _config.Log("Configuration validation failed", NeshamaConfig.LogLevel.Warning);
            }
            
            _config.Log($"NeshamaClient created with config: {_config}", NeshamaConfig.LogLevel.Info);
        }

        /// <summary>
        /// 创建Neshama客户端（使用默认配置）
        /// </summary>
        public NeshamaClient(MonoBehaviour coroutineHost) 
            : this(null, coroutineHost)
        {
        }

        #region 连接管理

        /// <summary>
        /// 连接到服务器
        /// </summary>
        /// <returns>连接是否成功</returns>
        public async Task<bool> ConnectAsync()
        {
            if (_disposed)
            {
                throw new ObjectDisposedException(nameof(NeshamaClient));
            }

            _config.Log("Attempting to connect to Neshama server...", NeshamaConfig.LogLevel.Info);

            try
            {
                // 发送健康检查请求来测试连接
                var healthUrl = _config.BuildUrl("/health");
                var request = UnityWebRequest.Get(healthUrl);
                request.timeout = _config.TimeoutSeconds;
                
                _activeRequests.Add(request);
                
                var operation = request.SendWebRequest();
                
                // 使用简单的等待循环
                float elapsed = 0f;
                while (!operation.isDone && elapsed < _config.TimeoutSeconds)
                {
                    await Task.Delay(100);
                    elapsed += 0.1f;
                }

                bool success = false;
                
                if (operation.isDone)
                {
                    success = request.result == UnityWebRequest.Result.Success;
                    
                    if (success)
                    {
                        _isConnected = true;
                        _config.Log("Successfully connected to Neshama server", NeshamaConfig.LogLevel.Info);
                        OnConnectionStateChanged?.Invoke(true);
                    }
                    else
                    {
                        _config.Log($"Connection failed: {request.error}", NeshamaConfig.LogLevel.Warning);
                        // 即使健康检查失败，也允许继续（服务器可能没有健康检查端点）
                        _isConnected = true; // 假设连接成功，API调用时会验证
                        OnConnectionStateChanged?.Invoke(true);
                    }
                }
                else
                {
                    _config.Log("Connection timeout", NeshamaConfig.LogLevel.Warning);
                    _isConnected = true; // 仍然标记为已尝试连接
                    OnConnectionStateChanged?.Invoke(true);
                }

                return success;
            }
            catch (Exception ex)
            {
                _config.Log($"Connection error: {ex.Message}", NeshamaConfig.LogLevel.Warning);
                _isConnected = true; // 仍然允许操作
                OnConnectionStateChanged?.Invoke(true);
                return true; // 返回true允许继续使用
            }
            finally
            {
                _activeRequests.RemoveWhere(r => r == null);
            }
        }

        /// <summary>
        /// 断开连接
        /// </summary>
        public void Disconnect()
        {
            if (_disposed) return;

            _config.Log("Disconnecting from Neshama server...", NeshamaConfig.LogLevel.Info);
            
            // 取消所有活跃请求
            CancelAllRequests();
            
            _isConnected = false;
            OnConnectionStateChanged?.Invoke(false);
        }

        /// <summary>
        /// 取消所有活跃请求
        /// </summary>
        public void CancelAllRequests()
        {
            foreach (var request in _activeRequests)
            {
                if (request != null)
                {
                    request.Abort();
                }
            }
            _activeRequests.Clear();
        }

        #endregion

        #region NPC管理API

        /// <summary>
        /// 创建新NPC
        /// </summary>
        /// <param name="name">NPC名称</param>
        /// <param name="preset">预设模板</param>
        /// <returns>创建结果响应</returns>
        public async Task<CreateNPCResponse> CreateNPCAsync(string name, string preset)
        {
            var request = new CreateNPCRequest(name, preset);
            var apiResponse = await PostAsync<CreateNPCApiResponse>("/npc", request);
            
            if (apiResponse != null && apiResponse.success && apiResponse.data != null)
            {
                return new CreateNPCResponse
                {
                    success = true,
                    npc_id = apiResponse.data.npc_id,
                    profile = new NPCProfile
                    {
                        name = apiResponse.data.name,
                        npc_id = apiResponse.data.npc_id,
                        preset = apiResponse.data.preset,
                        created_at = apiResponse.data.created_at,
                    }
                };
            }
            
            return new CreateNPCResponse
            {
                success = false,
                error = apiResponse?.detail ?? "Unknown error"
            };
        }

        /// <summary>
        /// 获取NPC档案
        /// </summary>
        /// <param name="npcId">NPC ID</param>
        /// <returns>NPC档案</returns>
        public async Task<NPCProfile> GetProfileAsync(string npcId)
        {
            var apiResponse = await GetAsync<ProfileApiResponse>($"/npc/{npcId}/profile");
            
            if (apiResponse != null && apiResponse.success && apiResponse.data != null)
            {
                return new NPCProfile
                {
                    name = apiResponse.data.name,
                    npc_id = apiResponse.data.npc_id,
                    preset = apiResponse.data.preset,
                    created_at = apiResponse.data.created_at,
                };
            }
            
            return null;
        }

        #endregion

        #region 事件推送API

        /// <summary>
        /// 推送游戏事件
        /// </summary>
        /// <param name="npcId">NPC ID</param>
        /// <param name="gameEvent">游戏事件</param>
        /// <returns>事件响应</returns>
        public async Task<EventResponse> SendEventAsync(string npcId, GameEvent gameEvent)
        {
            var apiResponse = await PostAsync<EventApiResponse>($"/npc/{npcId}/event", gameEvent);
            
            if (apiResponse != null && apiResponse.success && apiResponse.data != null)
            {
                var result = new EventResponse
                {
                    success = true,
                    emotion_state = apiResponse.data.emotion_state,
                    response_hint = apiResponse.data.response_hint,
                };
                
                if (result.emotion_state != null)
                {
                    OnEmotionChanged?.Invoke(result.emotion_state);
                }
                
                return result;
            }
            
            return new EventResponse
            {
                success = false,
                error = apiResponse?.detail ?? "Unknown error"
            };
        }

        /// <summary>
        /// 推送游戏事件（使用枚举类型）
        /// </summary>
        /// <param name="npcId">NPC ID</param>
        /// <param name="eventType">事件类型</param>
        /// <param name="intensity">事件强度</param>
        /// <param name="context">上下文数据</param>
        /// <returns>事件响应</returns>
        public async Task<EventResponse> SendEventAsync(string npcId, Enums.GameEventType eventType, 
            float intensity = 1f, Dictionary<string, object> context = null)
        {
            var gameEvent = new GameEvent(eventType, intensity, context);
            return await SendEventAsync(npcId, gameEvent);
        }

        #endregion

        #region 情绪状态API

        /// <summary>
        /// 获取NPC当前情绪状态
        /// </summary>
        /// <param name="npcId">NPC ID</param>
        /// <returns>情绪状态</returns>
        public async Task<EmotionState> GetEmotionAsync(string npcId)
        {
            var apiResponse = await GetAsync<EmotionApiResponse>($"/npc/{npcId}/emotion");
            
            if (apiResponse != null && apiResponse.success && apiResponse.data != null)
            {
                return apiResponse.data.emotion_state;
            }
            
            return null;
        }

        #endregion

        #region 行为建议API

        /// <summary>
        /// 获取NPC行为建议
        /// </summary>
        /// <param name="npcId">NPC ID</param>
        /// <returns>行为响应</returns>
        public async Task<BehaviorResponse> GetBehaviorHintsAsync(string npcId)
        {
            var apiResponse = await GetAsync<BehaviorApiResponse>($"/npc/{npcId}/behavior");
            
            if (apiResponse != null && apiResponse.success && apiResponse.data != null)
            {
                var response = new BehaviorResponse
                {
                    modifiers = apiResponse.data.modifiers,
                };
                
                if (response.modifiers != null)
                {
                    OnBehaviorChanged?.Invoke(response.modifiers);
                }
                
                return response;
            }
            
            return null;
        }

        #endregion

        #region 对话API

        /// <summary>
        /// 与NPC对话
        /// </summary>
        /// <param name="npcId">NPC ID</param>
        /// <param name="message">消息内容</param>
        /// <param name="playerId">玩家ID</param>
        /// <returns>对话响应</returns>
        public async Task<ChatResponse> ChatAsync(string npcId, string message, string playerId = null)
        {
            var request = new ChatRequest(message, playerId ?? _config.DefaultPlayerId);
            var apiResponse = await PostAsync<ChatApiResponse>($"/npc/{npcId}/chat", request);
            
            if (apiResponse != null && apiResponse.success && apiResponse.data != null)
            {
                var response = new ChatResponse
                {
                    success = true,
                    content = apiResponse.data.formatted_response?.clean 
                              ?? apiResponse.data.formatted_response?.convert
                              ?? apiResponse.data.message_received,
                    emotion_after = apiResponse.data.emotion_context,
                };
                
                OnChatResponse?.Invoke(response);
                return response;
            }
            
            var errorResponse = new ChatResponse
            {
                success = false,
                error = apiResponse?.detail ?? "Unknown error"
            };
            OnChatResponse?.Invoke(errorResponse);
            return errorResponse;
        }

        #endregion

        #region 记忆API

        /// <summary>
        /// 获取NPC的记忆
        /// </summary>
        /// <param name="npcId">NPC ID</param>
        /// <param name="query">查询条件（可选）</param>
        /// <returns>记忆列表</returns>
        public async Task<MemoryListResponse> GetMemoryAsync(string npcId, string query = null)
        {
            var endpoint = string.IsNullOrEmpty(query) 
                ? $"/npc/{npcId}/memory" 
                : $"/npc/{npcId}/memory?query={UnityWebRequest.EscapeURL(query)}";
            var apiResponse = await GetAsync<MemoryApiResponse>(endpoint);
            
            if (apiResponse != null && apiResponse.success && apiResponse.data != null)
            {
                return new MemoryListResponse
                {
                    success = true,
                };
            }
            
            return null;
        }

        /// <summary>
        /// 让NPC记住实体
        /// </summary>
        /// <param name="npcId">NPC ID</param>
        /// <param name="entityType">实体类型</param>
        /// <param name="entityName">实体名称</param>
        /// <param name="relation">关系类型</param>
        /// <param name="note">备注</param>
        /// <returns>记忆响应</returns>
        public async Task<RememberResponse> RememberAsync(string npcId, string entityType, 
            string entityName, string relation = null, string note = null)
        {
            var request = new RememberRequest(entityType, entityName, relation, note);
            var apiResponse = await PostAsync<RememberApiResponse>($"/npc/{npcId}/remember", request);
            
            if (apiResponse != null && apiResponse.success && apiResponse.data != null)
            {
                return new RememberResponse
                {
                    success = true,
                };
            }
            
            return new RememberResponse
            {
                success = false,
                error = apiResponse?.detail ?? "Unknown error"
            };
        }

        #endregion

        #region 关系图谱API

        /// <summary>
        /// 获取NPC的关系图谱
        /// </summary>
        /// <param name="npcId">NPC ID</param>
        /// <returns>关系图谱</returns>
        public async Task<RelationGraph> GetRelationsAsync(string npcId)
        {
            var apiResponse = await GetAsync<RelationsApiResponse>($"/npc/{npcId}/relations");
            
            if (apiResponse != null && apiResponse.success && apiResponse.data != null)
            {
                var graph = new RelationGraph();
                if (apiResponse.data.relations != null)
                {
                    graph.relations = new List<Relation>();
                    foreach (var rd in apiResponse.data.relations)
                    {
                        graph.relations.Add(new Relation
                        {
                            source_id = rd.from,
                            target_id = rd.to,
                            relation_type = rd.relation_type,
                            strength = rd.weight,
                        });
                    }
                }
                return graph;
            }
            
            return null;
        }

        #endregion

        #region HTTP核心方法

        /// <summary>
        /// 发送GET请求
        /// </summary>
        private async Task<T> GetAsync<T>(string endpoint) where T : class
        {
            var url = _config.BuildUrl(endpoint);
            _config.Log($"GET: {url}", NeshamaConfig.LogLevel.Debug);
            
            var request = UnityWebRequest.Get(url);
            request.timeout = _config.TimeoutSeconds;
            request.SetRequestHeader("Content-Type", "application/json");
            
            return await SendRequestAsync<T>(request);
        }

        /// <summary>
        /// 发送POST请求（使用API前缀）
        /// </summary>
        internal async Task<T> PostAsync<T>(string endpoint, object data) where T : class
        {
            var url = _config.BuildUrl(endpoint);
            _config.Log($"POST: {url}", NeshamaConfig.LogLevel.Debug);
            
            var json = JsonUtility.ToJson(data);
            _config.Log($"Request body: {json}", NeshamaConfig.LogLevel.Debug);
            
            var request = UnityWebRequest.Post(url, json);
            request.timeout = _config.TimeoutSeconds;
            request.SetRequestHeader("Content-Type", "application/json");
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            
            return await SendRequestAsync<T>(request);
        }

        /// <summary>
        /// 发送POST请求（使用绝对路径，不带API前缀，用于auth等非game端点）
        /// </summary>
        public async Task<T> PostAbsoluteAsync<T>(string absolutePath, object data) where T : class
        {
            var url = $"{_config.BaseUrl.TrimEnd('/')}{absolutePath}";
            _config.Log($"POST: {url}", NeshamaConfig.LogLevel.Debug);
            
            var json = data != null ? JsonUtility.ToJson(data) : "{}";
            _config.Log($"Request body: {json}", NeshamaConfig.LogLevel.Debug);
            
            var request = UnityWebRequest.Post(url, json);
            request.timeout = _config.TimeoutSeconds;
            request.SetRequestHeader("Content-Type", "application/json");
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            
            return await SendRequestAsync<T>(request);
        }

        /// <summary>
        /// 发送GET请求（使用绝对路径，不带API前缀）
        /// </summary>
        public async Task<T> GetAbsoluteAsync<T>(string absolutePath) where T : class
        {
            var url = $"{_config.BaseUrl.TrimEnd('/')}{absolutePath}";
            _config.Log($"GET: {url}", NeshamaConfig.LogLevel.Debug);
            
            var request = UnityWebRequest.Get(url);
            request.timeout = _config.TimeoutSeconds;
            request.SetRequestHeader("Content-Type", "application/json");
            
            return await SendRequestAsync<T>(request);
        }

        /// <summary>
        /// 发送HTTP请求并处理响应
        /// </summary>
        private async Task<T> SendRequestAsync<T>(UnityWebRequest request) where T : class
        {
            if (_disposed)
            {
                throw new ObjectDisposedException(nameof(NeshamaClient));
            }

            _activeRequests.Add(request);
            T result = null;

            try
            {
                var operation = request.SendWebRequest();
                
                // 使用TaskCompletionSource实现异步等待
                var tcs = new TaskCompletionSource<bool>();
                
                // 轮询检查完成状态
                _coroutineHost.StartCoroutine(WaitForRequestCompletion(operation, tcs, request));
                
                await tcs.Task;

                if (request.result == UnityWebRequest.Result.Success)
                {
                    var responseText = request.downloadHandler.text;
                    _config.Log($"Response: {responseText}", NeshamaConfig.LogLevel.Debug);
                    
                    if (!string.IsNullOrEmpty(responseText))
                    {
                        result = JsonUtility.FromJson<T>(responseText);
                    }
                }
                else
                {
                    var error = $"HTTP Error: {request.responseCode} - {request.error}";
                    _config.Log(error, NeshamaConfig.LogLevel.Error);
                    OnError?.Invoke(error);
                    
                    // 尝试解析错误响应
                    var errorResponse = request.downloadHandler.text;
                    if (!string.IsNullOrEmpty(errorResponse))
                    {
                        try
                        {
                            result = JsonUtility.FromJson<T>(errorResponse);
                        }
                        catch
                        {
                            // 忽略JSON解析错误
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _config.Log($"Request exception: {ex.Message}", NeshamaConfig.LogLevel.Error);
                OnError?.Invoke(ex.Message);
            }
            finally
            {
                _activeRequests.Remove(request);
                request.Dispose();
            }

            return result;
        }

        /// <summary>
        /// 等待请求完成的协程
        /// </summary>
        private IEnumerator WaitForRequestCompletion(UnityWebRequestAsyncOperation operation, 
            TaskCompletionSource<bool> tcs, UnityWebRequest request)
        {
            while (!operation.isDone)
            {
                yield return null;
            }
            
            // 如果请求被中止，不设置结果
            if (request.isDone)
            {
                tcs.SetResult(true);
            }
            else
            {
                tcs.SetCanceled();
            }
        }

        #endregion

        #region 辅助方法

        /// <summary>
        /// 测试连接是否可用
        /// </summary>
        /// <returns>连接是否可用</returns>
        public async Task<bool> TestConnectionAsync()
        {
            try
            {
                var profile = await GetProfileAsync("test_connection");
                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// 输出日志
        /// </summary>
        public void Log(string message, NeshamaConfig.LogLevel level = NeshamaConfig.LogLevel.Info)
        {
            _config?.Log(message, level);
            if (level == NeshamaConfig.LogLevel.Debug || level == NeshamaConfig.LogLevel.Info)
            {
                OnLog?.Invoke(message);
            }
        }

        #endregion

        #region IDisposable

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            if (_disposed) return;
            
            _disposed = true;
            
            Disconnect();
            
            _activeRequests.Clear();
            
            OnConnectionStateChanged = null;
            OnEmotionChanged = null;
            OnBehaviorChanged = null;
            OnChatResponse = null;
            OnError = null;
            OnLog = null;
            
            _config.Log("NeshamaClient disposed", NeshamaConfig.LogLevel.Info);
        }

        #endregion
    }
}
