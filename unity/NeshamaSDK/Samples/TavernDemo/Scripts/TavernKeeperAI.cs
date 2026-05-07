using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Neshama.SDK;
using Neshama.SDK.Models;
using Neshama.SDK.Enums;
using TMPro;

namespace Neshama.SDK.Samples
{
    /// <summary>
    /// 酒馆老板娘AI控制器 - Demo示例
    /// 
    /// 演示如何使用NPCSoul组件实现具有情感反应的NPC
    /// 包括：
    /// - 玩家进入触发区时的欢迎反应
    /// - 玩家攻击时的愤怒反应
    /// - 玩家送礼时的友好反应
    /// - 对话系统的使用
    /// </summary>
    public class TavernKeeperAI : MonoBehaviour
    {
        #region 配置

        [Header("=== 身份配置 ===")]
        [Tooltip("NPC显示名称")]
        [SerializeField]
        private string npcName = "酒馆老板娘";

        [Tooltip("NPC预设模板")]
        [SerializeField]
        private string preset = "tavern_keeper";

        [Header("=== 交互配置 ===")]
        [Tooltip("玩家进入触发距离")]
        [SerializeField]
        private float triggerDistance = 3f;

        [Tooltip("交互冷却时间（秒）")]
        [SerializeField]
        private float interactionCooldown = 5f;

        [Tooltip("触发区的球形碰撞半径")]
        [SerializeField]
        private float triggerRadius = 2f;

        [Header("=== 对话配置 ===")]
        [Tooltip("默认问候语")]
        [SerializeField]
        private string defaultGreeting = "欢迎光临！";

        [Tooltip("愤怒时的问候语")]
        [SerializeField]
        private string angryGreeting = "哼，是你啊...";

        [Tooltip("开心时的问候语")]
        [SerializeField]
        private string happyGreeting = "哦，亲爱的朋友来了！";

        [Tooltip("当前NPC灵魂组件")]
        [SerializeField]
        private NPCSoul npcSoul;

        #endregion

        #region 私有变量

        // 玩家引用
        private Transform player;

        // 冷却计时器
        private float lastInteractionTime = -999f;

        // 触发区碰撞器
        private SphereCollider triggerCollider;

        // 当前对话风格
        private string currentDialogueStyle = "friendly";

        // 是否已记住玩家
        private bool hasRememberedPlayer = false;

        // UI引用（用于显示对话）
        private TMPro.TextMeshProUGUI dialogueText;

        // 情绪状态颜色
        private readonly Color joyColor = new Color(0.2f, 0.8f, 0.2f);
        private readonly Color angerColor = new Color(0.8f, 0.2f, 0.2f);
        private readonly Color neutralColor = Color.white;

        #endregion

        #region Unity生命周期

        /// <summary>
        /// 初始化
        /// </summary>
        private void Start()
        {
            // 查找玩家
            player = GameObject.FindGameObjectWithTag("Player")?.transform;

            // 创建触发区
            CreateTriggerZone();

            // 获取或创建NPCSoul组件
            EnsureNPCSoul();

            // 订阅事件
            SubscribeToEvents();

            // 初始化UI
            InitializeUI();

            Debug.Log($"[{npcName}] 酒馆老板娘初始化完成");
        }

        /// <summary>
        /// 每帧更新
        /// </summary>
        private void Update()
        {
            // 检查是否在交互冷却中
            bool canInteract = Time.time - lastInteractionTime >= interactionCooldown;

            // 检查玩家是否在触发区内
            if (player != null && canInteract)
            {
                float distance = Vector3.Distance(transform.position, player.position);

                if (distance <= triggerRadius)
                {
                    // 玩家进入触发区，发送事件
                    OnPlayerEntered();
                    lastInteractionTime = Time.time;
                }
            }
        }

        /// <summary>
        /// 销毁时清理
        /// </summary>
        private void OnDestroy()
        {
            UnsubscribeFromEvents();
        }

        /// <summary>
        /// 绘制Gizmos
        /// </summary>
        private void OnDrawGizmosSelected()
        {
            // 绘制触发区
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position, triggerRadius);

            // 绘制交互范围
            Gizmos.color = Color.cyan;
            Gizmos.DrawWireSphere(transform.position, triggerDistance);
        }

        #endregion

        #region 初始化方法

        /// <summary>
        /// 创建触发区碰撞器
        /// </summary>
        private void CreateTriggerZone()
        {
            triggerCollider = GetComponent<SphereCollider>();
            if (triggerCollider == null)
            {
                triggerCollider = gameObject.AddComponent<SphereCollider>();
                triggerCollider.radius = triggerRadius;
                triggerCollider.isTrigger = true;
            }
        }

        /// <summary>
        /// 确保NPCSoul组件存在
        /// </summary>
        private void EnsureNPCSoul()
        {
            if (npcSoul == null)
            {
                npcSoul = GetComponent<NPCSoul>();
                if (npcSoul == null)
                {
                    npcSoul = gameObject.AddComponent<NPCSoul>();
                }
            }

            // 配置NPCSoul
            npcSoul.Configure(
                $"tavern_keeper_{npcName.GetHashCode()}",
                npcName,
                preset,
                true
            );
        }

        /// <summary>
        /// 订阅事件
        /// </summary>
        private void SubscribeToEvents()
        {
            if (npcSoul != null)
            {
                npcSoul.OnEmotionChanged += OnEmotionChanged;
                npcSoul.OnBehaviorChanged += OnBehaviorChanged;
                npcSoul.OnChatResponse += OnChatResponse;
                npcSoul.OnConnectionStateChanged += OnConnectionStateChanged;
            }
        }

        /// <summary>
        /// 取消订阅事件
        /// </summary>
        private void UnsubscribeFromEvents()
        {
            if (npcSoul != null)
            {
                npcSoul.OnEmotionChanged -= OnEmotionChanged;
                npcSoul.OnBehaviorChanged -= OnBehaviorChanged;
                npcSoul.OnChatResponse -= OnChatResponse;
                npcSoul.OnConnectionStateChanged -= OnConnectionStateChanged;
            }
        }

        /// <summary>
        /// 初始化UI（需要TMPro）
        /// </summary>
        private void InitializeUI()
        {
            // 尝试查找UI Canvas
            var canvas = FindObjectOfType<UnityEngine.Canvas>();
            if (canvas != null)
            {
                // 创建对话文本框
                var textObj = new GameObject("DialogueText");
                textObj.transform.SetParent(canvas.transform, false);

                dialogueText = textObj.AddComponent<TMPro.TextMeshProUGUI>();
                dialogueText.text = "";
                dialogueText.fontSize = 24;
                dialogueText.alignment = TextAlignmentOptions.Bottom;
                dialogueText.rectTransform.anchoredPosition = new Vector2(0, 100);
                dialogueText.rectTransform.sizeDelta = new Vector2(600, 100);
                dialogueText.gameObject.SetActive(false);
            }
        }

        #endregion

        #region 交互触发方法

        /// <summary>
        /// 玩家进入触发区
        /// </summary>
        public void OnPlayerEntered()
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 检测到玩家进入");

            // 根据情绪状态决定问候语
            var emotion = npcSoul.CurrentEmotion;
            string greeting = GetGreetingBasedOnEmotion(emotion);

            // 显示问候
            ShowDialogue(greeting);

            // 发送玩家进入事件
            _ = SendEventWithContext(GameEventType.player_entered, 0.3f, new Dictionary<string, object>
            {
                { "player_name", player?.name ?? "Unknown" }
            });
        }

        /// <summary>
        /// 玩家攻击NPC（通过碰撞检测触发）
        /// </summary>
        public void OnPlayerAttacked(float damage)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 玩家攻击了NPC，造成 {damage} 点伤害");

            // 显示愤怒台词
            ShowDialogue("啊！你疯了吗？！");

            // 发送攻击事件
            _ = SendEventWithContext(GameEventType.player_attacked, Mathf.Clamp01(damage / 50f), new Dictionary<string, object>
            {
                { "damage", damage }
            });

            // 检查是否应该拒绝服务
            CheckServiceRefusal();
        }

        /// <summary>
        /// 玩家赠送礼物
        /// </summary>
        public void OnGiftReceived(string giftName, int value)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 收到礼物: {giftName} (价值: {value})");

            // 显示感谢
            ShowDialogue($"哦，这真是太感谢了！");

            // 发送礼物事件
            _ = SendEventWithContext(GameEventType.gift_given, Mathf.Clamp01(value / 10f), new Dictionary<string, object>
            {
                { "gift_name", giftName },
                { "gift_value", value }
            });

            // 高价值礼物会分享秘密
            if (value >= 5)
            {
                StartCoroutine(ShareSecretAfterDelay(2f));
            }

            // 让NPC记住玩家
            if (!hasRememberedPlayer)
            {
                RememberPlayerAsAlly();
            }
        }

        /// <summary>
        /// 玩家帮助了NPC
        /// </summary>
        public void OnPlayerHelped(string helpType)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 玩家帮助了NPC: {helpType}");

            // 显示感谢
            ShowDialogue($"你真是个好人！");

            // 发送帮助事件
            _ = SendEventWithContext(GameEventType.npc_helped, 0.8f, new Dictionary<string, object>
            {
                { "help_type", helpType }
            });
        }

        /// <summary>
        /// 玩家与NPC交易完成
        /// </summary>
        public void OnTradeCompleted(int amount)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 交易完成: {amount} 金币");

            // 发送交易事件
            _ = SendEventWithContext(GameEventType.trade_completed, 0.5f, new Dictionary<string, object>
            {
                { "amount", amount }
            });
        }

        /// <summary>
        /// 玩家任务完成
        /// </summary>
        public void OnQuestCompleted(string questName)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 任务完成: {questName}");

            // 显示祝贺
            ShowDialogue($"干得漂亮！不愧是我认识的人！");

            // 发送任务完成事件
            _ = SendEventWithContext(GameEventType.quest_completed, 0.7f, new Dictionary<string, object>
            {
                { "quest_name", questName }
            });
        }

        #endregion

        #region 辅助方法

        /// <summary>
        /// 发送带上下文的事件
        /// </summary>
        private async System.Threading.Tasks.Task SendEventWithContext(
            GameEventType eventType, 
            float intensity, 
            Dictionary<string, object> context)
        {
            if (npcSoul == null) return;

            var response = await npcSoul.SendEvent(eventType, intensity, context);

            if (response != null)
            {
                Debug.Log($"[{npcName}] 事件已处理，情绪变为: {response.emotion_state?.dominant}");
            }
        }

        /// <summary>
        /// 根据情绪获取问候语
        /// </summary>
        private string GetGreetingBasedOnEmotion(EmotionState emotion)
        {
            if (emotion == null) return defaultGreeting;

            if (emotion.Anger > 0.5f)
            {
                return angryGreeting;
            }
            else if (emotion.Joy > 0.5f)
            {
                return happyGreeting;
            }

            return defaultGreeting;
        }

        /// <summary>
        /// 显示对话
        /// </summary>
        private void ShowDialogue(string text)
        {
            if (dialogueText != null)
            {
                dialogueText.text = text;
                dialogueText.gameObject.SetActive(true);

                // 3秒后隐藏
                CancelInvoke(nameof(HideDialogue));
                Invoke(nameof(HideDialogue), 3f);
            }
            else
            {
                Debug.Log($"[{npcName}]: {text}");
            }
        }

        /// <summary>
        /// 隐藏对话
        /// </summary>
        private void HideDialogue()
        {
            if (dialogueText != null)
            {
                dialogueText.gameObject.SetActive(false);
            }
        }

        /// <summary>
        /// 检查是否应该拒绝服务
        /// </summary>
        private void CheckServiceRefusal()
        {
            if (npcSoul.CurrentBehaviors == null) return;

            foreach (var behavior in npcSoul.CurrentBehaviors)
            {
                if (behavior.suggested_actions != null && 
                    behavior.suggested_actions.Contains("refuse_conversation"))
                {
                    ShowDialogue("你现在不受到欢迎，离开这里！");
                    return;
                }
            }
        }

        /// <summary>
        /// 让NPC记住玩家为盟友
        /// </summary>
        private async void RememberPlayerAsAlly()
        {
            if (npcSoul == null) return;

            var response = await npcSoul.RememberEntity(
                "player",
                player?.name ?? "Unknown Player",
                "ally",
                "帮助过酒馆的善良冒险者"
            );

            if (response != null && response.success)
            {
                hasRememberedPlayer = true;
                Debug.Log($"[{npcName}] 记住了玩家");
            }
        }

        /// <summary>
        /// 延迟分享秘密
        /// </summary>
        private IEnumerator ShareSecretAfterDelay(float delay)
        {
            yield return new WaitForSeconds(delay);

            // 根据情绪状态决定分享什么秘密
            if (npcSoul.IsHappy())
            {
                ShowDialogue("既然你这么大方...我告诉你一个秘密吧。听说地下城里有一件传说中的酒杯...");
            }
            else if (!npcSoul.IsAngry())
            {
                ShowDialogue("你人真不错...我告诉你，后院的地窖里藏着一些好东西。");
            }
        }

        #endregion

        #region 事件回调

        /// <summary>
        /// 情绪变化回调
        /// </summary>
        private void OnEmotionChanged(EmotionState newEmotion)
        {
            Debug.Log($"[{npcName}] 情绪变化: {newEmotion?.dominant}");

            // 更新对话风格
            if (newEmotion != null)
            {
                if (newEmotion.Anger > 0.5f)
                {
                    currentDialogueStyle = "hostile";
                }
                else if (newEmotion.Joy > 0.5f)
                {
                    currentDialogueStyle = "friendly";
                }
                else
                {
                    currentDialogueStyle = "neutral";
                }
            }
        }

        /// <summary>
        /// 行为变化回调
        /// </summary>
        private void OnBehaviorChanged(List<BehaviorHint> behaviors)
        {
            Debug.Log($"[{npcName}] 行为变化: {behaviors?.Count ?? 0} 个修改器");

            if (behaviors != null)
            {
                foreach (var behavior in behaviors)
                {
                    if (behavior.IsDialogueStyleChange())
                    {
                        currentDialogueStyle = behavior.value;
                        Debug.Log($"[{npcName}] 对话风格变为: {behavior.value}");
                    }

                    if (behavior.IsQuestAvailabilityChange())
                    {
                        if (behavior.IsQuestLocked())
                        {
                            ShowDialogue("最近我有些私事要处理，任务暂时搁置吧...");
                        }
                        else if (behavior.IsQuestUnlocked())
                        {
                            ShowDialogue("啊，对了！我正好有个任务想托付给你...");
                        }
                    }
                }
            }
        }

        /// <summary>
        /// 对话响应回调
        /// </summary>
        private void OnChatResponse(ChatResponse response)
        {
            if (response != null && response.success)
            {
                ShowDialogue(response.content);
            }
        }

        /// <summary>
        /// 连接状态变化回调
        /// </summary>
        private void OnConnectionStateChanged(bool connected)
        {
            Debug.Log($"[{npcName}] 连接状态变化: {(connected ? "已连接" : "已断开")}");
        }

        #endregion

        #region 公共方法

        /// <summary>
        /// 触发对话（供UI按钮调用）
        /// </summary>
        public async void TriggerChat(string message)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            if (!npcSoul.IsWillingToTalk())
            {
                ShowDialogue("我现在不想和你说话...");
                return;
            }

            var response = await npcSoul.Chat(message, player?.name ?? "player_001");

            if (response != null && response.success)
            {
                ShowDialogue(response.content);
            }
        }

        /// <summary>
        /// 获取当前情绪描述
        /// </summary>
        public string GetCurrentEmotionDescription()
        {
            var emotion = npcSoul?.CurrentEmotion;
            if (emotion == null) return "未知";

            return $"{emotion.dominant} ({emotion.composite})";
        }

        /// <summary>
        /// 获取当前对话风格
        /// </summary>
        public string GetCurrentDialogueStyle()
        {
            return currentDialogueStyle;
        }

        #endregion
    }
}
