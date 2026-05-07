using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using Neshama.SDK;
using Neshama.SDK.Models;

namespace Neshama.Demo
{
    /// <summary>
    /// Demo UI管理器 - 管理所有UI面板
    /// 
    /// 功能：
    /// - 对话面板（NPC名字 + 情绪emoji + 打字机效果 + 对话选项）
    /// - 情绪面板（9个情绪条 + 主导情绪 + 关系状态）
    /// - 信息提示（右上角社交事件 + 左上角剧情触发）
    /// - 快捷事件栏（8个按钮）
    /// </summary>
    public class DemoUIManager : MonoBehaviour
    {
        #region 单例

        private static DemoUIManager _instance;
        public static DemoUIManager Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = FindObjectOfType<DemoUIManager>();
                }
                return _instance;
            }
        }

        #endregion

        #region UI面板引用

        [Header("=== 对话面板 ===")]
        [SerializeField] private GameObject dialoguePanel;
        [SerializeField] private TextMeshProUGUI npcNameText;
        [SerializeField] private TextMeshProUGUI emotionEmojiText;
        [SerializeField] private TextMeshProUGUI dialogueText;
        [SerializeField] private Transform dialogueOptionsContainer;
        [SerializeField] private GameObject dialogueOptionButtonPrefab;

        [Header("=== 情绪面板 ===")]
        [SerializeField] private GameObject emotionPanel;
        [SerializeField] private TextMeshProUGUI dominantEmotionText;
        [SerializeField] private Image dominantEmotionIcon;
        [SerializeField] private TextMeshProUGUI relationshipStatusText;
        [SerializeField] private Dictionary<string, Image> emotionBars = new Dictionary<string, Image>();
        [SerializeField] private Dictionary<string, TextMeshProUGUI> emotionValueTexts = new Dictionary<string, TextMeshProUGUI>();

        [Header("=== 信息提示 ===")]
        [SerializeField] private GameObject notificationPanel;
        [SerializeField] private TextMeshProUGUI notificationText;
        [SerializeField] private Image notificationIcon;

        [Header("=== 剧情提示 ===")]
        [SerializeField] private GameObject storyPanel;
        [SerializeField] private TextMeshProUGUI storyText;

        [Header("=== 交互提示 ===")]
        [SerializeField] private GameObject interactionHint;
        [SerializeField] private TextMeshProUGUI interactionHintText;

        [Header("=== 快捷事件栏 ===")]
        [SerializeField] private GameObject quickEventBar;
        [SerializeField] private Button[] quickEventButtons;

        [Header("=== 提示配置 ===")]
        [SerializeField] private float notificationDuration = 3f;
        [SerializeField] private float typewriterSpeed = 0.05f;

        #endregion

        #region 私有变量

        // 当前交互的NPC
        private NPCSoul _currentNPC;

        // 打字机效果状态
        private Coroutine _typewriterCoroutine;
        private bool _isTyping;
        private string _currentFullText;

        // 通知队列
        private Queue<NotificationData> _notificationQueue = new Queue<NotificationData>();
        private bool _isShowingNotification;

        // UI面板初始化状态
        private bool _isInitialized;

        // 情绪条配置
        private readonly string[] _emotionNames = { "joy", "sadness", "anger", "fear", "surprise", "disgust", "trust", "anticipation", "shame" };
        private readonly Color[] _emotionColors = {
            new Color(0.2f, 0.8f, 0.2f),    // joy - 绿色
            new Color(0.3f, 0.3f, 0.8f),    // sadness - 蓝色
            new Color(0.9f, 0.2f, 0.2f),    // anger - 红色
            new Color(0.5f, 0.3f, 0.8f),    // fear - 紫色
            new Color(0.9f, 0.7f, 0.2f),    // surprise - 橙色
            new Color(0.5f, 0.8f, 0.2f),    // disgust - 黄绿色
            new Color(0.2f, 0.6f, 0.8f),    // trust - 青色
            new Color(0.8f, 0.5f, 0.2f),    // anticipation - 棕色
            new Color(0.9f, 0.6f, 0.8f)     // shame - 粉色
        };

        #endregion

        #region Unity生命周期

        /// <summary>
        /// 初始化
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
        }

        /// <summary>
        /// 启动时初始化UI
        /// </summary>
        private void Start()
        {
            // 如果没有预设UI，创建默认UI
            if (!HasUIPrefabs())
            {
                CreateDefaultUI();
            }

            // 隐藏所有面板
            HideAllPanels();

            // 初始化情绪条
            InitializeEmotionBars();

            _isInitialized = true;

            Debug.Log("[DemoUIManager] UI管理器初始化完成");
        }

        #endregion

        #region UI创建

        /// <summary>
        /// 检查是否有预设UI
        /// </summary>
        private bool HasUIPrefabs()
        {
            return dialoguePanel != null && emotionPanel != null;
        }

        /// <summary>
        /// 创建默认UI
        /// </summary>
        private void CreateDefaultUI()
        {
            // 创建Canvas
            var canvasObj = CreateCanvas();
            var canvas = canvasObj.GetComponent<Canvas>();

            // 创建对话面板
            CreateDialoguePanel(canvas.transform);

            // 创建情绪面板
            CreateEmotionPanel(canvas.transform);

            // 创建通知面板
            CreateNotificationPanel(canvas.transform);

            // 创建剧情提示面板
            CreateStoryPanel(canvas.transform);

            // 创建交互提示
            CreateInteractionHint(canvas.transform);

            // 创建快捷事件栏
            CreateQuickEventBar(canvas.transform);
        }

        /// <summary>
        /// 创建Canvas
        /// </summary>
        private GameObject CreateCanvas()
        {
            var canvasObj = new GameObject("DemoCanvas");
            var canvas = canvasObj.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 100;

            canvasObj.AddComponent<CanvasScaler>();
            canvasObj.AddComponent<GraphicRaycaster>();

            return canvasObj;
        }

        /// <summary>
        /// 创建对话面板
        /// </summary>
        private void CreateDialoguePanel(Transform parent)
        {
            // 面板背景
            dialoguePanel = CreatePanel("DialoguePanel", parent);
            dialoguePanel.GetComponent<RectTransform>().anchoredPosition = new Vector2(0, -100);
            dialoguePanel.GetComponent<RectTransform>().sizeDelta = new Vector2(500, 200);

            var panelImage = dialoguePanel.AddComponent<Image>();
            panelImage.color = new Color(0.1f, 0.1f, 0.15f, 0.9f);

            var layout = dialoguePanel.AddComponent<VerticalLayoutGroup>();
            layout.padding = new RectOffset(15, 15, 10, 10);
            layout.spacing = 5;

            // NPC名字
            var nameObj = new GameObject("NPCName");
            nameObj.transform.SetParent(dialoguePanel.transform);
            npcNameText = nameObj.AddComponent<TextMeshProUGUI>();
            npcNameText.fontSize = 18;
            npcNameText.color = Color.yellow;
            npcNameText.text = "NPC";

            // 情绪emoji
            var emojiObj = new GameObject("EmotionEmoji");
            emojiObj.transform.SetParent(dialoguePanel.transform);
            emotionEmojiText = emojiObj.AddComponent<TextMeshProUGUI>();
            emotionEmojiText.fontSize = 24;
            emotionEmojiText.text = "😊";

            // 对话文本
            var dialogueObj = new GameObject("DialogueText");
            dialogueObj.transform.SetParent(dialoguePanel.transform);
            dialogueText = dialogueObj.AddComponent<TextMeshProUGUI>();
            dialogueText.fontSize = 16;
            dialogueText.color = Color.white;
            dialogueText.text = "...";
            dialogueText.alignment = TextAlignmentOptions.Left;

            var dialogueRect = dialogueObj.GetComponent<RectTransform>();
            dialogueRect.sizeDelta = new Vector2(470, 60);

            // 对话选项容器
            var optionsObj = new GameObject("DialogueOptions");
            optionsObj.transform.SetParent(dialoguePanel.transform);
            dialogueOptionsContainer = optionsObj.transform;

            var optionsLayout = optionsObj.AddComponent<HorizontalLayoutGroup>();
            optionsLayout.spacing = 10;
            optionsLayout.childAlignment = TextAnchor.MiddleCenter;

            // 初始隐藏
            dialoguePanel.SetActive(false);
        }

        /// <summary>
        /// 创建情绪面板
        /// </summary>
        private void CreateEmotionPanel(Transform parent)
        {
            // 面板背景
            emotionPanel = CreatePanel("EmotionPanel", parent);
            emotionPanel.GetComponent<RectTransform>().anchoredPosition = new Vector2(-200, 0);
            emotionPanel.GetComponent<RectTransform>().sizeDelta = new Vector2(180, 320);

            var panelImage = emotionPanel.AddComponent<Image>();
            panelImage.color = new Color(0.1f, 0.1f, 0.15f, 0.85f);

            // 标题
            var titleObj = new GameObject("Title");
            titleObj.transform.SetParent(emotionPanel.transform);
            var titleText = titleObj.AddComponent<TextMeshProUGUI>();
            titleText.fontSize = 14;
            titleText.color = Color.white;
            titleText.text = "情绪状态";

            // 主导情绪
            var dominantObj = new GameObject("DominantEmotion");
            dominantObj.transform.SetParent(emotionPanel.transform);
            dominantEmotionText = dominantObj.AddComponent<TextMeshProUGUI>();
            dominantEmotionText.fontSize = 16;
            dominantEmotionText.color = Color.cyan;
            dominantEmotionText.text = "喜悦";

            // 情绪条容器
            var barsContainer = new GameObject("EmotionBars");
            barsContainer.transform.SetParent(emotionPanel.transform);
            var barsLayout = barsContainer.AddComponent<VerticalLayoutGroup>();
            barsLayout.spacing = 4;
            barsLayout.padding = new RectOffset(5, 5, 5, 5);

            // 创建9个情绪条
            for (int i = 0; i < _emotionNames.Length; i++)
            {
                CreateEmotionBar(barsContainer.transform, _emotionNames[i], _emotionColors[i], i);
            }

            // 关系状态
            var statusObj = new GameObject("RelationshipStatus");
            statusObj.transform.SetParent(emotionPanel.transform);
            relationshipStatusText = statusObj.AddComponent<TextMeshProUGUI>();
            relationshipStatusText.fontSize = 12;
            relationshipStatusText.color = Color.gray;
            relationshipStatusText.text = "关系: 陌生";

            // 初始隐藏
            emotionPanel.SetActive(false);
        }

        /// <summary>
        /// 创建单个情绪条
        /// </summary>
        private void CreateEmotionBar(Transform parent, string emotionName, Color color, int index)
        {
            var barObj = new GameObject($"Bar_{emotionName}");
            barObj.transform.SetParent(parent);

            var barLayout = barObj.AddComponent<HorizontalLayoutGroup>();
            barLayout.spacing = 5;

            // 名称
            var nameObj = new GameObject("Name");
            nameObj.transform.SetParent(barObj.transform);
            var nameText = nameObj.AddComponent<TextMeshProUGUI>();
            nameText.fontSize = 10;
            nameText.color = Color.white;
            nameText.text = GetEmotionChineseName(emotionName);
            nameText.alignment = TextAlignmentOptions.Left;

            var nameRect = nameObj.GetComponent<RectTransform>();
            nameRect.sizeDelta = new Vector2(50, 15);

            // 背景条
            var bgObj = new GameObject("Background");
            bgObj.transform.SetParent(barObj.transform);
            var bgImage = bgObj.AddComponent<Image>();
            bgImage.color = new Color(0.3f, 0.3f, 0.3f);

            var bgRect = bgObj.GetComponent<RectTransform>();
            bgRect.sizeDelta = new Vector2(80, 12);

            // 填充条
            var fillObj = new GameObject("Fill");
            fillObj.transform.SetParent(bgObj.transform);
            var fillImage = fillObj.AddComponent<Image>();
            fillImage.color = color;

            var fillRect = fillObj.GetComponent<RectTransform>();
            fillRect.sizeDelta = new Vector2(0, 12);
            fillRect.anchorMin = new Vector2(0, 0);
            fillRect.anchorMax = new Vector2(0, 1);
            fillRect.pivot = new Vector2(0, 0.5f);
            fillRect.offsetMin = Vector2.zero;
            fillRect.offsetMax = Vector2.zero;

            // 存储引用
            emotionBars[emotionName] = fillImage;

            // 数值文本
            var valueObj = new GameObject("Value");
            valueObj.transform.SetParent(barObj.transform);
            var valueText = valueObj.AddComponent<TextMeshProUGUI>();
            valueText.fontSize = 10;
            valueText.color = Color.white;
            valueText.text = "0%";
            valueText.alignment = TextAlignmentOptions.Right;

            var valueRect = valueObj.GetComponent<RectTransform>();
            valueRect.sizeDelta = new Vector2(35, 15);
        }

        /// <summary>
        /// 创建通知面板
        /// </summary>
        private void CreateNotificationPanel(Transform parent)
        {
            notificationPanel = CreatePanel("NotificationPanel", parent);
            notificationPanel.GetComponent<RectTransform>().anchorMin = new Vector2(1, 1);
            notificationPanel.GetComponent<RectTransform>().anchorMax = new Vector2(1, 1);
            notificationPanel.GetComponent<RectTransform>().anchoredPosition = new Vector2(-120, -50);
            notificationPanel.GetComponent<RectTransform>().sizeDelta = new Vector2(220, 60);

            var panelImage = notificationPanel.AddComponent<Image>();
            panelImage.color = new Color(0.15f, 0.15f, 0.2f, 0.9f);

            var layout = notificationPanel.AddComponent<HorizontalLayoutGroup>();
            layout.padding = new RectOffset(10, 10, 5, 5);
            layout.spacing = 10;

            // 图标
            var iconObj = new GameObject("Icon");
            iconObj.transform.SetParent(notificationPanel.transform);
            notificationIcon = iconObj.AddComponent<Image>();
            notificationIcon.color = Color.yellow;

            var iconRect = iconObj.GetComponent<RectTransform>();
            iconRect.sizeDelta = new Vector2(30, 30);

            // 文本
            var textObj = new GameObject("Text");
            textObj.transform.SetParent(notificationPanel.transform);
            notificationText = textObj.AddComponent<TextMeshProUGUI>();
            notificationText.fontSize = 14;
            notificationText.color = Color.white;
            notificationText.text = "";
            notificationText.alignment = TextAlignmentOptions.Left;

            var textRect = textObj.GetComponent<RectTransform>();
            textRect.sizeDelta = new Vector2(150, 40);

            notificationPanel.SetActive(false);
        }

        /// <summary>
        /// 创建剧情提示面板
        /// </summary>
        private void CreateStoryPanel(Transform parent)
        {
            storyPanel = CreatePanel("StoryPanel", parent);
            storyPanel.GetComponent<RectTransform>().anchorMin = new Vector2(0, 1);
            storyPanel.GetComponent<RectTransform>().anchorMax = new Vector2(0, 1);
            storyPanel.GetComponent<RectTransform>().anchoredPosition = new Vector2(150, -50);
            storyPanel.GetComponent<RectTransform>().sizeDelta = new Vector2(280, 60);

            var panelImage = storyPanel.AddComponent<Image>();
            panelImage.color = new Color(0.8f, 0.3f, 0.2f, 0.9f);

            var layout = storyPanel.AddComponent<HorizontalLayoutGroup>();
            layout.padding = new RectOffset(15, 15, 10, 10);

            storyText = storyPanel.AddComponent<TextMeshProUGUI>();
            storyText.fontSize = 16;
            storyText.color = Color.white;
            storyText.text = "";
            storyText.alignment = TextAlignmentOptions.Center;

            storyPanel.SetActive(false);
        }

        /// <summary>
        /// 创建交互提示
        /// </summary>
        private void CreateInteractionHint(Transform parent)
        {
            interactionHint = CreatePanel("InteractionHint", parent);
            interactionHint.GetComponent<RectTransform>().anchoredPosition = new Vector2(0, 150);
            interactionHint.GetComponent<RectTransform>().sizeDelta = new Vector2(250, 50);

            var panelImage = interactionHint.AddComponent<Image>();
            panelImage.color = new Color(0.2f, 0.8f, 0.2f, 0.9f);

            interactionHintText = interactionHint.AddComponent<TextMeshProUGUI>();
            interactionHintText.fontSize = 16;
            interactionHintText.color = Color.white;
            interactionHintText.text = "[E] 对话  [Q] 送礼  [R] 攻击  [F] 夸赞";
            interactionHintText.alignment = TextAlignmentOptions.Center;

            interactionHint.SetActive(false);
        }

        /// <summary>
        /// 创建快捷事件栏
        /// </summary>
        private void CreateQuickEventBar(Transform parent)
        {
            quickEventBar = CreatePanel("QuickEventBar", parent);
            quickEventBar.GetComponent<RectTransform>().anchorMin = new Vector2(0.5f, 0);
            quickEventBar.GetComponent<RectTransform>().anchorMax = new Vector2(0.5f, 0);
            quickEventBar.GetComponent<RectTransform>().anchoredPosition = new Vector2(0, 80);
            quickEventBar.GetComponent<RectTransform>().sizeDelta = new Vector2(500, 50);

            var panelImage = quickEventBar.AddComponent<Image>();
            panelImage.color = new Color(0.1f, 0.1f, 0.15f, 0.8f);

            var layout = quickEventBar.AddComponent<HorizontalLayoutGroup>();
            layout.spacing = 5;
            layout.childAlignment = TextAnchor.MiddleCenter;

            // 创建8个快捷按钮
            quickEventButtons = new Button[8];
            string[] buttonLabels = { "送礼", "攻击", "帮助", "赞美", "侮辱", "交易", "接任务", "完成" };

            for (int i = 0; i < 8; i++)
            {
                var btnObj = new GameObject($"QuickButton_{i + 1}");
                btnObj.transform.SetParent(quickEventBar.transform);

                var btn = btnObj.AddComponent<Button>();
                var btnImage = btnObj.AddComponent<Image>();
                btnImage.color = GetQuickButtonColor(i);

                var text = btnObj.AddComponent<TextMeshProUGUI>();
                text.text = $"[Shift+{i + 1}] {buttonLabels[i]}";
                text.fontSize = 12;
                text.color = Color.white;
                text.alignment = TextAlignmentOptions.Center;

                var btnRect = btnObj.GetComponent<RectTransform>();
                btnRect.sizeDelta = new Vector2(55, 35);

                quickEventButtons[i] = btn;
            }
        }

        /// <summary>
        /// 创建面板
        /// </summary>
        private GameObject CreatePanel(string name, Transform parent)
        {
            var panel = new GameObject(name);
            panel.transform.SetParent(parent);

            var rect = panel.AddComponent<RectTransform>();
            rect.anchorMin = new Vector2(0.5f, 0.5f);
            rect.anchorMax = new Vector2(0.5f, 0.5f);
            rect.pivot = new Vector2(0.5f, 0.5f);

            return panel;
        }

        #endregion

        #region 情绪条初始化

        /// <summary>
        /// 初始化情绪条
        /// </summary>
        private void InitializeEmotionBars()
        {
            // 情绪条已经在CreateEmotionBar中创建并存储在字典中
            Debug.Log($"[DemoUIManager] 已初始化 {emotionBars.Count} 个情绪条");
        }

        /// <summary>
        /// 获取情绪中文名
        /// </summary>
        private string GetEmotionChineseName(string emotion)
        {
            return emotion.ToLower() switch
            {
                "joy" => "喜悦",
                "sadness" => "悲伤",
                "anger" => "愤怒",
                "fear" => "恐惧",
                "surprise" => "惊讶",
                "disgust" => "厌恶",
                "trust" => "信任",
                "anticipation" => "期待",
                "shame" => "羞愧",
                _ => emotion
            };
        }

        #endregion

        #region 对话面板

        /// <summary>
        /// 显示对话面板
        /// </summary>
        public void ShowDialoguePanel(NPCSoul npc)
        {
            if (!_isInitialized) return;

            _currentNPC = npc;

            // 更新NPC信息
            if (npcNameText != null)
                npcNameText.text = npc.NpcName;

            // 更新情绪
            UpdateEmotionDisplay(npc.CurrentEmotion);

            // 显示面板
            if (dialoguePanel != null)
                dialoguePanel.SetActive(true);

            // 显示情绪面板
            if (emotionPanel != null)
                emotionPanel.SetActive(true);

            // 隐藏交互提示
            HideInteractionHint();

            Debug.Log($"[DemoUIManager] 打开与 {npc.NpcName} 的对话");
        }

        /// <summary>
        /// 隐藏对话面板
        /// </summary>
        public void HideDialoguePanel()
        {
            if (dialoguePanel != null)
                dialoguePanel.SetActive(false);

            if (emotionPanel != null)
                emotionPanel.SetActive(false);

            _currentNPC = null;

            Debug.Log("[DemoUIManager] 关闭对话面板");
        }

        /// <summary>
        /// 显示对话
        /// </summary>
        public void ShowDialogue(string npcName, string message, List<string> options = null)
        {
            if (!_isInitialized) return;

            // 更新名字
            if (npcNameText != null)
                npcNameText.text = npcName;

            // 打字机效果
            StartTypewriterEffect(message);

            // 更新对话选项
            UpdateDialogueOptions(options);

            // 显示面板
            if (dialoguePanel != null)
                dialoguePanel.SetActive(true);
        }

        /// <summary>
        /// 更新对话选项
        /// </summary>
        private void UpdateDialogueOptions(List<string> options)
        {
            if (dialogueOptionsContainer == null) return;

            // 清除现有选项
            foreach (Transform child in dialogueOptionsContainer)
            {
                Destroy(child.gameObject);
            }

            if (options == null || options.Count == 0) return;

            // 创建新选项
            foreach (var option in options)
            {
                var optionObj = Instantiate(dialogueOptionButtonPrefab, dialogueOptionsContainer);
                if (optionObj == null)
                {
                    // 如果没有预制件，手动创建
                    optionObj = new GameObject("Option");
                    optionObj.transform.SetParent(dialogueOptionsContainer);

                    var btn = optionObj.AddComponent<Button>();
                    var btnImage = optionObj.AddComponent<Image>();
                    btnImage.color = new Color(0.3f, 0.3f, 0.4f);

                    var text = optionObj.AddComponent<TextMeshProUGUI>();
                    text.text = option;
                    text.fontSize = 12;
                    text.color = Color.white;

                    var rect = optionObj.GetComponent<RectTransform>();
                    rect.sizeDelta = new Vector2(140, 30);
                }
                else
                {
                    var text = optionObj.GetComponentInChildren<TextMeshProUGUI>();
                    if (text != null)
                        text.text = option;
                }
            }
        }

        /// <summary>
        /// 打字机效果
        /// </summary>
        private void StartTypewriterEffect(string message)
        {
            if (_typewriterCoroutine != null)
            {
                StopCoroutine(_typewriterCoroutine);
            }

            _typewriterCoroutine = StartCoroutine(TypewriterCoroutine(message));
        }

        /// <summary>
        /// 打字机协程
        /// </summary>
        private IEnumerator TypewriterCoroutine(string message)
        {
            _isTyping = true;
            _currentFullText = message;

            if (dialogueText != null)
            {
                dialogueText.text = "";

                foreach (char c in message)
                {
                    dialogueText.text += c;
                    yield return new WaitForSeconds(typewriterSpeed);
                }
            }

            _isTyping = false;
        }

        /// <summary>
        /// 更新情绪显示
        /// </summary>
        public void UpdateEmotionDisplay(EmotionState emotion)
        {
            if (!_isInitialized || emotion == null) return;

            // 更新emoji
            if (emotionEmojiText != null)
            {
                emotionEmojiText.text = GetEmotionEmoji(emotion.dominant);
            }

            // 更新主导情绪
            if (dominantEmotionText != null)
            {
                dominantEmotionText.text = GetEmotionChineseName(emotion.dominant);
            }

            // 更新情绪条
            foreach (var emotionName in _emotionNames)
            {
                if (emotionBars.TryGetValue(emotionName, out Image bar))
                {
                    float value = emotion.GetEmotionValue(emotionName);
                    UpdateEmotionBar(bar, value);
                }
            }

            // 更新关系状态
            UpdateRelationshipStatus(emotion);
        }

        /// <summary>
        /// 更新情绪条
        /// </summary>
        private void UpdateEmotionBar(Image bar, float value)
        {
            if (bar == null) return;

            var rect = bar.GetComponent<RectTransform>();
            float width = Mathf.Lerp(0, 80, value);
            rect.sizeDelta = new Vector2(width, 12);
        }

        /// <summary>
        /// 更新关系状态
        /// </summary>
        private void UpdateRelationshipStatus(EmotionState emotion)
        {
            if (relationshipStatusText == null) return;

            string status = emotion.Trust > 0.7f ? "友好" :
                           emotion.Trust > 0.4f ? "熟悉" :
                           emotion.Anger > 0.5f ? "敌对" :
                           "陌生";

            relationshipStatusText.text = $"关系: {status}";
        }

        /// <summary>
        /// 获取情绪emoji
        /// </summary>
        private string GetEmotionEmoji(string dominant)
        {
            if (string.IsNullOrEmpty(dominant)) return "😐";

            return dominant.ToLower() switch
            {
                "joy" => "😊",
                "sadness" => "😢",
                "anger" => "😠",
                "fear" => "😨",
                "surprise" => "😮",
                "disgust" => "🤢",
                "trust" => "🤝",
                "anticipation" => "🤔",
                "shame" => "😳",
                _ => "😐"
            };
        }

        #endregion

        #region 通知系统

        /// <summary>
        /// 显示通知
        /// </summary>
        public void ShowNotification(string message, NotificationType type = NotificationType.Info)
        {
            NotificationData data = new NotificationData
            {
                Message = message,
                Type = type
            };

            _notificationQueue.Enqueue(data);

            if (!_isShowingNotification)
            {
                StartCoroutine(ShowNotificationRoutine());
            }
        }

        /// <summary>
        /// 显示通知协程
        /// </summary>
        private IEnumerator ShowNotificationRoutine()
        {
            _isShowingNotification = true;

            while (_notificationQueue.Count > 0)
            {
                NotificationData data = _notificationQueue.Dequeue();

                if (notificationText != null)
                    notificationText.text = data.Message;

                if (notificationIcon != null)
                    notificationIcon.color = GetNotificationColor(data.Type);

                if (notificationPanel != null)
                    notificationPanel.SetActive(true);

                yield return new WaitForSeconds(notificationDuration);

                if (notificationPanel != null)
                    notificationPanel.SetActive(false);

                yield return new WaitForSeconds(0.3f);
            }

            _isShowingNotification = false;
        }

        /// <summary>
        /// 获取通知颜色
        /// </summary>
        private Color GetNotificationColor(NotificationType type)
        {
            return type switch
            {
                NotificationType.Info => Color.cyan,
                NotificationType.Success => Color.green,
                NotificationType.Warning => Color.yellow,
                NotificationType.Error => Color.red,
                _ => Color.white
            };
        }

        /// <summary>
        /// 显示剧情通知
        /// </summary>
        public void ShowStoryNotification(string message)
        {
            if (storyText != null)
                storyText.text = message;

            if (storyPanel != null)
            {
                storyPanel.SetActive(true);

                // 3秒后自动隐藏
                StartCoroutine(HideStoryPanelRoutine());
            }
        }

        /// <summary>
        /// 隐藏剧情面板协程
        /// </summary>
        private IEnumerator HideStoryPanelRoutine()
        {
            yield return new WaitForSeconds(4f);

            if (storyPanel != null)
                storyPanel.SetActive(false);
        }

        #endregion

        #region 交互提示

        /// <summary>
        /// 显示交互提示
        /// </summary>
        public void ShowInteractionHint(string npcName)
        {
            if (interactionHint != null)
            {
                interactionHintText.text = $"{npcName}\n[E] 对话  [Q] 送礼  [R] 攻击  [F] 夸赞";
                interactionHint.SetActive(true);
            }
        }

        /// <summary>
        /// 隐藏交互提示
        /// </summary>
        public void HideInteractionHint()
        {
            if (interactionHint != null)
                interactionHint.SetActive(false);
        }

        #endregion

        #region 辅助方法

        /// <summary>
        /// 获取快捷按钮颜色
        /// </summary>
        private Color GetQuickButtonColor(int index)
        {
            Color[] colors = {
                new Color(0.2f, 0.8f, 0.2f),    // 绿色 - 送礼
                new Color(0.9f, 0.2f, 0.2f),    // 红色 - 攻击
                new Color(0.2f, 0.6f, 0.8f),    // 青色 - 帮助
                new Color(0.9f, 0.7f, 0.2f),    // 橙色 - 赞美
                new Color(0.8f, 0.3f, 0.8f),    // 紫色 - 侮辱
                new Color(0.3f, 0.7f, 0.5f),    // 青绿 - 交易
                new Color(0.5f, 0.5f, 0.9f),    // 蓝色 - 接任务
                new Color(0.9f, 0.9f, 0.2f)     // 黄色 - 完成
            };

            return colors[index % colors.Length];
        }

        /// <summary>
        /// 隐藏所有面板
        /// </summary>
        private void HideAllPanels()
        {
            if (dialoguePanel != null) dialoguePanel.SetActive(false);
            if (emotionPanel != null) emotionPanel.SetActive(false);
            if (notificationPanel != null) notificationPanel.SetActive(false);
            if (storyPanel != null) storyPanel.SetActive(false);
            if (interactionHint != null) interactionHint.SetActive(false);
        }

        #endregion

        #region 数据结构

        /// <summary>
        /// 通知数据结构
        /// </summary>
        private struct NotificationData
        {
            public string Message;
            public NotificationType Type;
        }

        /// <summary>
        /// 通知类型
        /// </summary>
        public enum NotificationType
        {
            Info,
            Success,
            Warning,
            Error
        }

        #endregion
    }
}
