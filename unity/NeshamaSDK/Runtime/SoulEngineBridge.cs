using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using Neshama.SoulEngine.Personality;
using Neshama.SoulEngine.Memory;
using Neshama.SoulEngine.Behavior;
using Neshama.SoulEngine.Emotion;
using Neshama.SDK.Models;
using Neshama.SDK;
// Aliases to disambiguate: SoulEngine is both a namespace and a class
using SoulEngineClass = Neshama.SoulEngine.Core.SoulEngine;
using SoulEventResult = Neshama.SoulEngine.Core.EventResult;
using SoulILLMProvider = Neshama.SoulEngine.Core.ILLMProvider;
using SoulConfig = Neshama.SoulEngine.Core.SoulConfig;
using MockLLMProvider = Neshama.SoulEngine.Core.MockLLMProvider;
using CloudLLMProvider = Neshama.SoulEngine.Core.CloudLLMProvider;
using DirectLLMProvider = Neshama.SoulEngine.Core.DirectLLMProvider;
using SoulEmotionState = Neshama.SoulEngine.Emotion.EmotionState;
using SoulResponseHint = Neshama.SoulEngine.Emotion.ResponseHint;
using SoulSoulState = Neshama.SoulEngine.Core.SoulState;
using SoulGameEventType = Neshama.SoulEngine.Emotion.GameEventType;
using SoulEmotionType = Neshama.SoulEngine.Emotion.EmotionType;

namespace Neshama.SDK
{
    /// <summary>
    /// SoulEngine ↔ NPCSoul MonoBehaviour桥接组件
    /// 
    /// 将纯C#的SoulEngine连接到NPCSoul MonoBehaviour，
    /// 提供本地（无服务器）的灵魂计算能力。
    /// 
    /// 使用方式：
    /// 1. 将此组件添加到与NPCSoul相同的GameObject上
    /// 2. 在Inspector中配置personality（可选，默认全0.5）
    /// 3. 调用 ProcessLocalEvent 处理游戏事件（本地计算，无需服务器）
    /// 4. 调用 ChatLocal 使用本地LLM Provider对话
    /// 5. 监听 OnSoulStateChanged 获取状态变化
    /// 
    /// 桥接逻辑：
    /// NPCSoul的事件 → SoulEngine本地处理 → 结果写回NPCSoul的emotionState
    /// </summary>
    [RequireComponent(typeof(NPCSoul))]
    public class SoulEngineBridge : MonoBehaviour
    {
        #region Inspector配置

        [Header("=== 人格配置 ===")]

        [Tooltip("开放性 (0-1)")]
        [Range(0f, 1f)]
        [SerializeField]
        private float openness = 0.5f;

        [Tooltip("尽责性 (0-1)")]
        [Range(0f, 1f)]
        [SerializeField]
        private float conscientiousness = 0.5f;

        [Tooltip("外向性 (0-1)")]
        [Range(0f, 1f)]
        [SerializeField]
        private float extraversion = 0.5f;

        [Tooltip("宜人性 (0-1)")]
        [Range(0f, 1f)]
        [SerializeField]
        private float agreeableness = 0.5f;

        [Tooltip("神经质 (0-1)")]
        [Range(0f, 1f)]
        [SerializeField]
        private float neuroticism = 0.5f;

        [Header("=== LLM配置 ===")]

        [Tooltip("LLM提供者模式：None=不使用, Mock=测试用, Cloud=Neshama云API, Direct=直连LLM API")]
        [SerializeField]
        private LLMModes llmMode = LLMModes.None;

        [Tooltip("直连LLM的API URL（仅Direct模式）")]
        [SerializeField]
        private string directLlmApiUrl = "https://api.openai.com/v1/chat/completions";

        [Tooltip("直连LLM的API Key（仅Direct模式）")]
        [SerializeField]
        private string directLlmApiKey = "";

        [Tooltip("直连LLM的模型名（仅Direct模式）")]
        [SerializeField]
        private string directLlmModel = "gpt-4o-mini";

        [Header("=== 调试 ===")]

        [Tooltip("是否在Console输出调试日志")]
        [SerializeField]
        private bool debugLog = false;

        #endregion

        #region 枚举

        /// <summary>
        /// LLM提供者模式
        /// </summary>
        public enum LLMModes
        {
            None = 0,
            Mock = 1,
            Cloud = 2,
            Direct = 3
        }

        #endregion

        #region 运行时状态

        private SoulEngineClass _engine;
        private NPCSoul _npcSoul;
        private SoulILLMProvider _llmProvider;

        /// <summary>底层SoulEngine实例</summary>
        public SoulEngineClass Engine => _engine;

        /// <summary>是否已初始化</summary>
        public bool IsInitialized => _engine != null;

        #endregion

        #region 事件回调

        /// <summary>
        /// 灵魂状态变化事件（本地计算后触发）
        /// 参数：SoulEventResult（包含情绪、行为、复合情绪等完整结果）
        /// </summary>
        public event Action<SoulEventResult> OnSoulStateChanged;

        /// <summary>
        /// 本地情绪更新事件（简化版，SDK Models格式，与NPCSoul一致）
        /// </summary>
        public event Action<Neshama.SDK.Models.EmotionState> OnLocalEmotionChanged;

        #endregion

        #region Unity生命周期

        private void Awake()
        {
            InitializeBridge();
        }

        private void Update()
        {
            if (_engine != null)
            {
                _engine.Tick(Time.deltaTime);
            }
        }

        private void OnDestroy()
        {
            _engine?.Dispose();
            _engine = null;
        }

        #endregion

        #region 初始化

        /// <summary>
        /// 初始化桥接：创建SoulEngine，关联NPCSoul
        /// </summary>
        private void InitializeBridge()
        {
            // 获取NPCSoul组件
            _npcSoul = GetComponent<NPCSoul>();
            if (_npcSoul == null)
            {
                Debug.LogError("[SoulEngineBridge] NPCSoul component not found on same GameObject!");
                return;
            }

            // 创建SoulEngine实例
            var personality = new OCEANPersonality(
                openness, conscientiousness, extraversion, agreeableness, neuroticism);
            var config = SoulConfig.Default;

            _engine = new SoulEngineClass(
                _npcSoul.NpcId,
                _npcSoul.NpcName,
                config,
                personality);

            // 初始化LLM Provider
            InitializeLLMProvider();

            // 首次同步情绪状态到NPCSoul
            SyncEmotionToNPCSoul();

            LogDebug("SoulEngineBridge initialized");
        }

        /// <summary>
        /// 根据配置初始化LLM Provider
        /// </summary>
        private void InitializeLLMProvider()
        {
            switch (llmMode)
            {
                case LLMModes.Mock:
                    _llmProvider = new MockLLMProvider();
                    break;
                case LLMModes.Cloud:
                    _llmProvider = new CloudLLMProvider(
                        "https://api.neshama.pw",
                        "", // API key from NeshamaConfig
                        _npcSoul?.NpcId ?? "npc_001");
                    break;
                case LLMModes.Direct:
                    if (!string.IsNullOrEmpty(directLlmApiKey))
                    {
                        _llmProvider = new DirectLLMProvider(
                            directLlmApiUrl, directLlmApiKey, directLlmModel);
                    }
                    else
                    {
                        Debug.LogWarning("[SoulEngineBridge] DirectLLM mode but no API Key set, falling back to Mock");
                        _llmProvider = new MockLLMProvider();
                    }
                    break;
                case LLMModes.None:
                default:
                    _llmProvider = null;
                    break;
            }
        }

        #endregion

        #region 核心API - 本地事件处理

        /// <summary>
        /// 处理游戏事件（本地SoulEngine计算，无需服务器）
        /// </summary>
        /// <param name="eventType">SoulEngine游戏事件类型</param>
        /// <param name="intensity">事件强度 (0-1)</param>
        /// <param name="sourceId">事件来源实体ID（可选）</param>
        /// <returns>事件处理结果</returns>
        public SoulEventResult ProcessLocalEvent(SoulGameEventType eventType, float intensity, string sourceId = null)
        {
            if (_engine == null)
            {
                Debug.LogWarning("[SoulEngineBridge] Engine not initialized, cannot process event");
                return default;
            }

            // 通过SoulEngine处理事件
            var result = _engine.ProcessEvent(eventType, intensity, sourceId);

            // 将结果同步回NPCSoul
            SyncEmotionToNPCSoul();

            // 触发事件
            OnSoulStateChanged?.Invoke(result);
            OnLocalEmotionChanged?.Invoke(ConvertToSDKEmotionState(result.emotionState));

            LogDebug($"Local event processed: {eventType} intensity={intensity:F2} " +
                     $"dominant={_engine.Emotion.GetDominantEmotion()}");

            return result;
        }

        /// <summary>
        /// 处理SDK枚举类型的游戏事件（自动映射到SoulEngine类型）
        /// </summary>
        /// <param name="sdkEventType">SDK游戏事件类型</param>
        /// <param name="intensity">事件强度 (0-1)</param>
        /// <param name="sourceId">事件来源实体ID（可选）</param>
        /// <returns>事件处理结果</returns>
        public SoulEventResult ProcessLocalEvent(Enums.GameEventType sdkEventType, float intensity, string sourceId = null)
        {
            SoulGameEventType engineType = MapEventType(sdkEventType);
            return ProcessLocalEvent(engineType, intensity, sourceId);
        }

        #endregion

        #region 核心API - 对话

        /// <summary>
        /// 本地对话（使用SoulEngine构建上下文 + LLM生成回复）
        /// </summary>
        /// <param name="message">玩家消息</param>
        /// <param name="playerId">玩家ID</param>
        /// <returns>NPC回复</returns>
        public async Task<string> ChatLocal(string message, string playerId = null)
        {
            if (_engine == null)
            {
                Debug.LogWarning("[SoulEngineBridge] Engine not initialized, cannot chat");
                return "[SoulEngineBridge not initialized]";
            }

            if (_llmProvider == null)
            {
                Debug.LogWarning("[SoulEngineBridge] No LLM provider configured, set llmMode in Inspector");
                return "[No LLM provider configured]";
            }

            return await _engine.Chat(message, _llmProvider);
        }

        #endregion

        #region 核心API - 状态访问

        /// <summary>获取当前情绪状态（SoulEngine原生结构体）</summary>
        public SoulEmotionState GetCurrentEmotionState()
        {
            return _engine?.Emotion?.CurrentEmotions ?? default;
        }

        /// <summary>获取当前行为配置</summary>
        public BehaviorMapper.BehaviorProfile GetBehaviorProfile()
        {
            return _engine?.GetBehaviorProfile();
        }

        /// <summary>获取对话上下文</summary>
        public DialogueContext GetDialogueContext(string playerId, string playerName = null)
        {
            return _engine?.GetDialogueContext(playerId, playerName);
        }

        /// <summary>获取当前OCEAN人格</summary>
        public OCEANPersonality GetPersonality()
        {
            return _engine?.Personality;
        }

        /// <summary>获取复合情绪</summary>
        public CompositeEmotionResult GetCompositeEmotion()
        {
            return _engine?.Emotion?.Synthesize() ?? default(CompositeEmotionResult);
        }

        /// <summary>获取行为建议</summary>
        public SoulResponseHint GetResponseHint()
        {
            return _engine?.Emotion?.GenerateHint() ?? new SoulResponseHint();
        }

        #endregion

        #region 核心API - 存档/读档

        /// <summary>
        /// 保存灵魂状态（用于游戏存档）
        /// </summary>
        public SoulSoulState SaveState()
        {
            return _engine?.SaveState();
        }

        /// <summary>
        /// 加载灵魂状态（用于游戏读档）
        /// </summary>
        public void LoadState(SoulSoulState state)
        {
            if (_engine == null || state == null) return;
            _engine.LoadState(state);
            SyncEmotionToNPCSoul();
        }

        #endregion

        #region 核心API - 配置

        /// <summary>
        /// 运行时修改人格参数
        /// </summary>
        public void SetPersonality(float o, float c, float e, float a, float n)
        {
            openness = o;
            conscientiousness = c;
            extraversion = e;
            agreeableness = a;
            neuroticism = n;

            if (_engine?.Personality != null)
            {
                _engine.Personality.openness = o;
                _engine.Personality.conscientiousness = c;
                _engine.Personality.extraversion = e;
                _engine.Personality.agreeableness = a;
                _engine.Personality.neuroticism = n;
            }
        }

        /// <summary>
        /// 切换LLM提供者
        /// </summary>
        public void SetLLMProvider(SoulILLMProvider provider)
        {
            _llmProvider = provider;
        }

        #endregion

        #region 内部 - 事件类型映射

        /// <summary>
        /// 将SDK枚举的GameEventType映射到SoulEngine的GameEventType。
        /// 两个枚举的值不完全对应，需要显式映射。
        /// </summary>
        private static SoulGameEventType MapEventType(Enums.GameEventType sdkType)
        {
            switch (sdkType)
            {
                case Enums.GameEventType.player_attacked:
                    return SoulGameEventType.PlayerAttacked;
                case Enums.GameEventType.npc_helped:
                    return SoulGameEventType.PlayerHelped;
                case Enums.GameEventType.gift_given:
                    return SoulGameEventType.GiftGiven;
                case Enums.GameEventType.npc_complimented:
                    return SoulGameEventType.NpcComplimented;
                case Enums.GameEventType.npc_insulted:
                    return SoulGameEventType.NpcInsulted;
                case Enums.GameEventType.combat_started:
                    return SoulGameEventType.CombatStarted;
                case Enums.GameEventType.combat_ended:
                    return SoulGameEventType.CombatEnded;
                case Enums.GameEventType.quest_completed:
                    return SoulGameEventType.QuestCompleted;
                case Enums.GameEventType.quest_failed:
                    return SoulGameEventType.QuestFailed;
                // SDK特有事件：映射到最接近的SoulEngine事件
                case Enums.GameEventType.player_entered:
                    return SoulGameEventType.RelationshipChanged;
                case Enums.GameEventType.player_left:
                    return SoulGameEventType.TimePassed;
                case Enums.GameEventType.npc_healed:
                    return SoulGameEventType.PlayerHelped;
                case Enums.GameEventType.npc_damaged:
                    return SoulGameEventType.PlayerAttacked;
                case Enums.GameEventType.trade_completed:
                    return SoulGameEventType.ItemReceived;
                case Enums.GameEventType.quest_accepted:
                    return SoulGameEventType.QuestCompleted;
                default:
                    return SoulGameEventType.TimePassed;
            }
        }

        #endregion

        #region 内部 - 状态同步

        /// <summary>
        /// 将SoulEngine的情绪状态同步到NPCSoul的SDK Models.EmotionState。
        /// 
        /// NPCSoul._currentEmotion是private字段，无法直接写入。
        /// 此方法通过创建SDK格式的EmotionState并触发OnLocalEmotionChanged事件，
        /// 让外部订阅者（如UI、调试面板）获取本地计算的情绪数据。
        /// </summary>
        private void SyncEmotionToNPCSoul()
        {
            if (_engine == null || _npcSoul == null) return;

            var engineEmo = _engine.Emotion.CurrentEmotions;
            var sdkEmotion = ConvertToSDKEmotionState(engineEmo);

            // 触发本地情绪变化事件
            OnLocalEmotionChanged?.Invoke(sdkEmotion);

            LogDebug($"Synced emotion to NPCSoul: dominant={sdkEmotion.dominant} composite={sdkEmotion.composite}");
        }

        /// <summary>
        /// 将SoulEngine.Emotion.EmotionState（struct）转换为SDK.Models.EmotionState（class）。
        /// </summary>
        private Neshama.SDK.Models.EmotionState ConvertToSDKEmotionState(SoulEmotionState engineEmo)
        {
            var composite = _engine?.Emotion?.Synthesize() ?? default(CompositeEmotionResult);

            var sdkEmotion = new Neshama.SDK.Models.EmotionState();
            var emoList = new List<EmotionEntry>
            {
                new EmotionEntry { key = "joy", value = engineEmo.joy },
                new EmotionEntry { key = "sadness", value = engineEmo.sadness },
                new EmotionEntry { key = "anger", value = engineEmo.anger },
                new EmotionEntry { key = "fear", value = engineEmo.fear },
                new EmotionEntry { key = "surprise", value = engineEmo.surprise },
                new EmotionEntry { key = "disgust", value = engineEmo.disgust },
                new EmotionEntry { key = "trust", value = engineEmo.trust },
                new EmotionEntry { key = "anticipation", value = engineEmo.anticipation },
                new EmotionEntry { key = "desire", value = engineEmo.desire },
            };
            sdkEmotion.emotion_list = emoList;

            // 设置主导情绪
            engineEmo.GetDominant(out var dominantType, out var dominantValue);
            sdkEmotion.dominant = dominantType.ToName();

            // 设置复合情绪
            sdkEmotion.composite = composite.name;

            return sdkEmotion;
        }

        #endregion

        #region 内部 - 日志

        private void LogDebug(string message)
        {
            if (debugLog)
            {
                Debug.Log($"[SoulEngineBridge:{_npcSoul?.NpcName ?? "???"}] {message}");
            }
        }

        #endregion
    }
}
