using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Neshama.SDK;
using Neshama.SDK.Models;
using Neshama.SDK.Enums;

namespace Neshama.Demo
{
    /// <summary>
    /// 神秘旅人NPC控制器
    /// 
    /// 特殊行为：
    /// - 初次见面 → 神秘台词："星辰指引你来到此处..."
    /// - trust>0.6 → 透露预言："北方的龙...不是你想象的那样"
    /// - fear>0.5 → 播放逃跑动画，短暂消失后重新出现
    /// - 被辱骂 → 不愤怒但悲伤："你不理解...没有人理解"
    /// - NPC移动范围：酒馆角落+偶尔在酒馆和城门之间走动
    /// </summary>
    [RequireComponent(typeof(NPCSoul))]
    public class NPCMysticTraveler : MonoBehaviour
    {
        #region NPC配置

        [Header("=== 身份配置 ===")]
        [Tooltip("NPC显示名称")]
        [SerializeField] private string npcName = "神秘的流浪者";

        [Tooltip("NPC预设模板")]
        [SerializeField] private string preset = "mystic_traveler";

        [Tooltip("真名（信任后揭示）")]
        [SerializeField] private string trueName = "艾瑟琳";

        [Header("=== 移动配置 ===")]
        [Tooltip("是否启用移动")]
        [SerializeField] private bool enableMovement = true;

        [Tooltip("移动速度")]
        [SerializeField] private float moveSpeed = 1f;

        [Tooltip("是否启用随机移动")]
        [SerializeField] private bool enableRandomMovement = true;

        [Tooltip("随机移动间隔")]
        [SerializeField] private float randomMoveInterval = 10f;

        [Tooltip("随机移动范围")]
        [SerializeField] private float randomMoveRange = 8f;

        [Tooltip("移动到城门概率")]
        [SerializeField] private float gateMoveProbability = 0.3f;

        [Tooltip("城门位置")]
        [SerializeField] private Vector3 gatePosition = new Vector3(8, 0, 0);

        [Tooltip("酒馆位置")]
        [SerializeField] private Vector3 tavernPosition = new Vector3(0, 0, 0);

        [Header("=== 交互配置 ===")]
        [Tooltip("交互触发距离")]
        [SerializeField] private float interactionDistance = 4f;

        [Tooltip("交互冷却时间")]
        [SerializeField] private float interactionCooldown = 5f;

        [Header("=== 对话配置 ===")]
        [Tooltip("初次见面台词")]
        [SerializeField] private string firstMeetingLine = "星辰指引你来到此处...";

        [Tooltip("普通台词")]
        [SerializeField] private string normalDialogue = "命运的丝线交织在一起...";

        [Tooltip("预言台词")]
        [SerializeField] private string prophecyLine = "北方的龙...不是你想象的那样。那是...";

        [Tooltip("完整预言（高度信任时）")]
        [SerializeField] private string fullProphecyLine = "北方的龙并非敌人，而是沉睡的守护者。当你真正需要它时，它会醒来。";

        [Tooltip("悲伤台词（被辱骂后）")]
        [SerializeField] private string sadDialogue = "你不理解...没有人理解...";

        [Tooltip("信任台词")]
        [SerializeField] private string trustDialogue = "我感觉到了你的真诚...或许，我可以告诉你我的名字。";

        [Tooltip("恐惧台词")]
        [SerializeField] private string fearDialogue = "危险...我感觉到了危险的气息...";

        [Tooltip("逃离台词")]
        [SerializeField] private string fleeDialogue = "我必须离开这里...星辰的指引在召唤我...";

        [Header("=== 消失配置 ===")]
        [Tooltip("消失时间（秒）")]
        [SerializeField] private float disappearDuration = 5f;

        [Tooltip("消失时透明度渐变时间")]
        [SerializeField] private float fadeOutDuration = 1f;

        #endregion

        #region 私有变量

        // NPC灵魂组件
        private NPCSoul _npcSoul;

        // 移动状态
        private Vector3 _currentTarget;
        private bool _isMoving;
        private bool _isWaiting;
        private bool _isAtGate = false;
        private float _lastRandomMoveTime;

        // 交互状态
        private bool _hasMetPlayer = false;
        private float _lastInteractionTime;
        private bool _hasRevealedName = false;
        private bool _hasRevealedFullProphecy = false;

        // 消失状态
        private bool _isDisappearing;
        private bool _isVisible = true;

        // 动画状态
        private bool _isPlayingAnimation;

        // 引用
        private Transform _playerTransform;
        private DemoUIManager _uiManager;

        // 颜色配置
        private readonly Color normalColor = new Color(0.8f, 0.7f, 0.9f);
        private readonly Color fearColor = new Color(0.6f, 0.6f, 0.7f);
        private readonly Color trustColor = new Color(0.7f, 0.8f, 0.9f);
        private readonly Color hiddenColor = new Color(0.5f, 0.5f, 0.6f);

        // 透明度
        private float _currentAlpha = 1f;
        private Renderer[] _renderers;

        #endregion

        #region Unity生命周期

        /// <summary>
        /// 初始化
        /// </summary>
        private void Start()
        {
            // 获取组件引用
            _npcSoul = GetComponent<NPCSoul>();
            _playerTransform = GameObject.FindGameObjectWithTag("Player")?.transform;
            _uiManager = DemoUIManager.Instance;

            // 获取渲染器
            _renderers = GetComponentsInChildren<Renderer>();

            // 设置初始位置
            _currentTarget = tavernPosition;
            _isAtGate = false;

            // 订阅事件
            SubscribeToEvents();

            // 开始随机移动
            if (enableMovement && enableRandomMovement)
            {
                StartCoroutine(RandomMovementRoutine());
            }

            // 开始移动循环
            StartCoroutine(MovementRoutine());

            Debug.Log($"[{npcName}] 神秘旅人初始化完成");
        }

        /// <summary>
        /// 每帧更新
        /// </summary>
        private void Update()
        {
            // 检查玩家交互
            CheckPlayerInteraction();

            // 更新移动
            if (!_isDisappearing)
            {
                UpdateMovement();
            }

            // 更新透明度
            UpdateVisibility();
        }

        /// <summary>
        /// 销毁时清理
        /// </summary>
        private void OnDestroy()
        {
            UnsubscribeFromEvents();
        }

        #endregion

        #region 事件订阅

        /// <summary>
        /// 订阅NPCSoul事件
        /// </summary>
        private void SubscribeToEvents()
        {
            if (_npcSoul == null) return;

            _npcSoul.OnEmotionChanged += OnEmotionChanged;
            _npcSoul.OnBehaviorChanged += OnBehaviorChanged;
        }

        /// <summary>
        /// 取消订阅事件
        /// </summary>
        private void UnsubscribeFromEvents()
        {
            if (_npcSoul == null) return;

            _npcSoul.OnEmotionChanged -= OnEmotionChanged;
            _npcSoul.OnBehaviorChanged -= OnBehaviorChanged;
        }

        /// <summary>
        /// 情绪变化回调
        /// </summary>
        private void OnEmotionChanged(EmotionState emotion)
        {
            Debug.Log($"[{npcName}] 情绪变化: {emotion.dominant}");

            // 恐惧值过高 → 逃跑消失
            if (emotion.Fear > 0.5f && !_isDisappearing)
            {
                TriggerDisappearSequence();
            }

            // 悲伤值高但不愤怒 → 显示悲伤台词
            if (emotion.Sadness > 0.4f && emotion.Anger < 0.3f)
            {
                // 不愤怒但悲伤
            }

            // 信任值高 → 揭示预言
            if (emotion.Trust > 0.6f)
            {
                if (!_hasRevealedName)
                {
                    _hasRevealedName = true;
                    Debug.Log($"[{npcName}] 揭示了真名: {trueName}");
                }

                if (emotion.Trust > 0.8f && !_hasRevealedFullProphecy)
                {
                    _hasRevealedFullProphecy = true;
                    Debug.Log($"[{npcName}] 揭示了完整预言！");
                }
            }

            // 更新视觉效果
            UpdateVisualEffect(emotion);
        }

        /// <summary>
        /// 行为变化回调
        /// </summary>
        private void OnBehaviorChanged(List<BehaviorHint> behaviors)
        {
            Debug.Log($"[{npcName}] 行为建议: {behaviors?.Count ?? 0}个");
        }

        #endregion

        #region 玩家检测

        /// <summary>
        /// 检查玩家交互
        /// </summary>
        private void CheckPlayerInteraction()
        {
            if (_playerTransform == null) return;
            if (_isDisappearing) return;

            float distance = Vector3.Distance(transform.position, _playerTransform.position);

            // 检测是否应该显示初次见面台词
            if (distance <= interactionDistance && !_hasMetPlayer)
            {
                _hasMetPlayer = true;
                OnFirstMeeting();
            }
        }

        /// <summary>
        /// 初次见面
        /// </summary>
        private void OnFirstMeeting()
        {
            // 面向玩家
            FacePlayer();

            // 显示神秘台词
            ShowMysteriousDialogue(firstMeetingLine);

            // 发送情绪事件
            _npcSoul?.SendEvent(GameEventType.player_entered, 0.2f);

            Debug.Log($"[{npcName}] 初次与玩家相遇");
        }

        /// <summary>
        /// 面向玩家
        /// </summary>
        private void FacePlayer()
        {
            if (_playerTransform == null) return;

            Vector3 direction = (_playerTransform.position - transform.position).normalized;
            direction.y = 0;

            if (direction.sqrMagnitude > 0.01f)
            {
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), 0.1f);
            }
        }

        #endregion

        #region 移动系统

        /// <summary>
        /// 随机移动协程
        /// </summary>
        private System.Collections.IEnumerator RandomMovementRoutine()
        {
            while (true)
            {
                if (enableRandomMovement && !_isMoving && !_isWaiting && !_isDisappearing)
                {
                    // 检查是否应该移动到城门
                    if (UnityEngine.Random.value < gateMoveProbability && !_isAtGate)
                    {
                        // 移动到城门
                        _currentTarget = gatePosition;
                        _isMoving = true;
                        _isAtGate = true;

                        Debug.Log($"[{npcName}] 决定前往城门");
                    }
                    else if (_isAtGate && UnityEngine.Random.value < gateMoveProbability)
                    {
                        // 返回酒馆
                        _currentTarget = tavernPosition;
                        _isMoving = true;
                        _isAtGate = false;

                        Debug.Log($"[{npcName}] 决定返回酒馆");
                    }
                    else
                    {
                        // 随机移动
                        if (UnityEngine.Random.value > 0.5f)
                        {
                            Vector3 randomOffset = UnityEngine.Random.insideUnitSphere * randomMoveRange;
                            randomOffset.y = 0;
                            _currentTarget = tavernPosition + randomOffset;
                            _isMoving = true;

                            Debug.Log($"[{npcName}] 开始随机漫步");
                        }
                    }
                }

                yield return new WaitForSeconds(randomMoveInterval);
            }
        }

        /// <summary>
        /// 移动协程
        /// </summary>
        private System.Collections.IEnumerator MovementRoutine()
        {
            while (true)
            {
                if (!enableMovement || _isPlayingAnimation)
                {
                    yield return new WaitForSeconds(0.5f);
                    continue;
                }

                if (!_isMoving && !_isWaiting)
                {
                    // 等待一会儿再移动
                    yield return new WaitForSeconds(2f);
                }

                yield return new WaitForSeconds(0.1f);
            }
        }

        /// <summary>
        /// 更新移动
        /// </summary>
        private void UpdateMovement()
        {
            if (!_isMoving) return;

            Vector3 direction = (_currentTarget - transform.position);
            direction.y = 0;

            float distance = direction.magnitude;

            // 到达目标
            if (distance < 0.5f)
            {
                _isMoving = false;
                _isWaiting = true;

                // 等待一段时间
                StartCoroutine(WaitAtLocation());

                return;
            }

            // 移动
            direction.Normalize();
            transform.position += direction * moveSpeed * Time.deltaTime;

            // 面向移动方向
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), 0.1f);
        }

        /// <summary>
        /// 在位置等待
        /// </summary>
        private System.Collections.IEnumerator WaitAtLocation()
        {
            yield return new WaitForSeconds(randomMoveInterval);

            // 到达新位置后可能说一句话
            if (_isAtGate)
            {
                ShowMysteriousDialogue("城门的气息...不安的气息...");
            }
            else
            {
                ShowMysteriousDialogue("在这里休息片刻...");
            }

            _isWaiting = false;
        }

        #endregion

        #region 消失/出现系统

        /// <summary>
        /// 触发消失序列
        /// </summary>
        private void TriggerDisappearSequence()
        {
            if (_isDisappearing) return;

            _isDisappearing = true;

            // 显示恐惧台词
            ShowMysteriousDialogue(fleeDialogue);

            StartCoroutine(DisappearSequence());
        }

        /// <summary>
        /// 消失序列
        /// </summary>
        private System.Collections.IEnumerator DisappearSequence()
        {
            _isPlayingAnimation = true;

            // 渐变消失
            float elapsed = 0f;
            while (elapsed < fadeOutDuration)
            {
                _currentAlpha = Mathf.Lerp(1f, 0f, elapsed / fadeOutDuration);
                elapsed += Time.deltaTime;
                yield return null;
            }

            _currentAlpha = 0f;
            _isVisible = false;

            // 完全消失
            gameObject.SetActive(false);

            // 等待
            yield return new WaitForSeconds(disappearDuration);

            // 重新出现
            Reappear();
        }

        /// <summary>
        /// 重新出现
        /// </summary>
        private void Reappear()
        {
            // 随机一个新位置
            Vector3 newPosition = tavernPosition + UnityEngine.Random.insideUnitSphere * 3f;
            newPosition.y = 0;
            transform.position = newPosition;

            // 重新激活
            gameObject.SetActive(true);

            // 淡入
            StartCoroutine(ReappearSequence());
        }

        /// <summary>
        /// 重新出现序列
        /// </summary>
        private System.Collections.IEnumerator ReappearSequence()
        {
            _currentAlpha = 0f;
            _isVisible = true;
            _isDisappearing = false;

            // 渐变出现
            float elapsed = 0f;
            while (elapsed < fadeOutDuration)
            {
                _currentAlpha = Mathf.Lerp(0f, 1f, elapsed / fadeOutDuration);
                elapsed += Time.deltaTime;
                yield return null;
            }

            _currentAlpha = 1f;
            _isPlayingAnimation = false;

            // 显示重新出现的台词
            ShowMysteriousDialogue("星辰再次指引我回到这里...");
        }

        /// <summary>
        /// 更新可见性
        /// </summary>
        private void UpdateVisibility()
        {
            if (_renderers == null) return;

            foreach (var renderer in _renderers)
            {
                if (renderer == null) continue;

                Material mat = renderer.material;

                // 检查是否支持透明度
                if (mat.HasProperty("_Color"))
                {
                    Color color = mat.color;
                    color.a = _currentAlpha;
                    mat.color = color;

                    // 设置渲染模式为透明
                    if (_currentAlpha < 1f)
                    {
                        SetMaterialTransparent(mat);
                    }
                    else
                    {
                        SetMaterialOpaque(mat);
                    }
                }
            }
        }

        /// <summary>
        /// 设置材质为透明
        /// </summary>
        private void SetMaterialTransparent(Material mat)
        {
            mat.SetFloat("_Mode", 3); // Transparent mode
            mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            mat.SetInt("_ZWrite", 0);
            mat.DisableKeyword("_ALPHATEST_ON");
            mat.EnableKeyword("_ALPHABLEND_ON");
            mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            mat.renderQueue = 3000;
        }

        /// <summary>
        /// 设置材质为不透明
        /// </summary>
        private void SetMaterialOpaque(Material mat)
        {
            mat.SetFloat("_Mode", 0); // Opaque mode
            mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.One);
            mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.Zero);
            mat.SetInt("_ZWrite", 1);
            mat.DisableKeyword("_ALPHATEST_ON");
            mat.DisableKeyword("_ALPHABLEND_ON");
            mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            mat.renderQueue = -1;
        }

        #endregion

        #region 对话系统

        /// <summary>
        /// 显示神秘对话
        /// </summary>
        private void ShowMysteriousDialogue(string message)
        {
            _uiManager?.ShowDialogue(npcName, message, GetDialogueOptions());
        }

        /// <summary>
        /// 获取对话选项
        /// </summary>
        private List<string> GetDialogueOptions()
        {
            var options = new List<string>
            {
                "你是谁？",
                "你从哪里来？"
            };

            // 信任后解锁
            if (_hasRevealedName)
            {
                options.Add($"你的名字是 {trueName}？");
                options.Add("告诉我关于你的故事");
            }

            // 揭示预言
            if (_hasRevealedFullProphecy)
            {
                options.Add("完整预言是什么？");
                options.Add("我该如何准备？");
            }
            else if (_npcSoul?.CurrentEmotion?.Trust > 0.6f)
            {
                options.Add("你能告诉我一些预言吗？");
            }

            // 恐惧状态
            if (_npcSoul?.CurrentEmotion?.Fear > 0.3f)
            {
                options.Add("发生什么事了？");
                options.Add("你需要帮助吗？");
            }

            return options;
        }

        /// <summary>
        /// 获取当前对话
        /// </summary>
        public string GetCurrentDialogue()
        {
            var emotion = _npcSoul?.CurrentEmotion;

            if (emotion == null)
                return normalDialogue;

            if (emotion.Fear > 0.5f)
                return fearDialogue;
            if (emotion.Sadness > 0.4f)
                return sadDialogue;
            if (_hasRevealedFullProphecy)
                return fullProphecyLine;
            if (_npcSoul.CurrentEmotion.Trust > 0.6f)
                return prophecyLine;
            if (!_hasMetPlayer)
                return firstMeetingLine;

            return normalDialogue;
        }

        #endregion

        #region 视觉效果

        /// <summary>
        /// 更新视觉效果
        /// </summary>
        private void UpdateVisualEffect(EmotionState emotion)
        {
            if (_renderers == null || _renderers.Length == 0)
            {
                var renderer = GetComponent<Renderer>();
                if (renderer != null)
                {
                    _renderers = new Renderer[] { renderer };
                }
            }

            if (_renderers == null) return;

            Color targetColor = normalColor;

            if (emotion.Fear > 0.3f)
                targetColor = Color.Lerp(normalColor, fearColor, emotion.Fear);
            else if (emotion.Trust > 0.6f)
                targetColor = trustColor;

            foreach (var renderer in _renderers)
            {
                if (renderer == null) continue;
                renderer.material.color = Color.Lerp(renderer.material.color, targetColor, Time.deltaTime * 2f);
            }
        }

        #endregion

        #region 公共方法

        /// <summary>
        /// 获取显示名称
        /// </summary>
        public string GetDisplayName()
        {
            if (_hasRevealedName)
                return $"{npcName} ({trueName})";
            return npcName;
        }

        /// <summary>
        /// 是否可见
        /// </summary>
        public bool IsVisible()
        {
            return _isVisible;
        }

        /// <summary>
        /// 是否正在消失
        /// </summary>
        public bool IsDisappearing()
        {
            return _isDisappearing;
        }

        /// <summary>
        /// 获取真名
        /// </summary>
        public string GetTrueName()
        {
            return trueName;
        }

        #endregion

        #region 调试

        /// <summary>
        /// 绘制Gizmos
        /// </summary>
        private void OnDrawGizmosSelected()
        {
            // 交互范围
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position, interactionDistance);

            // 移动范围
            Gizmos.color = new Color(0.5f, 0.3f, 0.8f, 0.5f);
            Gizmos.DrawWireSphere(tavernPosition, randomMoveRange);

            // 酒馆位置
            Gizmos.color = Color.green;
            Gizmos.DrawWireSphere(tavernPosition, 0.5f);

            // 城门位置
            Gizmos.color = Color.red;
            Gizmos.DrawWireSphere(gatePosition, 0.5f);

            // 连接线
            Gizmos.color = Color.gray;
            Gizmos.DrawLine(tavernPosition, gatePosition);
        }

        #endregion
    }
}
