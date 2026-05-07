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
    /// 酒馆老板娘NPC控制器 - 继承自NPCSoul的完整使用示例
    /// 
    /// 特殊行为：
    /// - 玩家进入酒馆 → SendEvent(npc_complimented, 0.2) + 播放欢迎动画
    /// - 情绪joy>0.7 → 播放斟酒动画，解锁特殊对话选项
    /// - 情绪anger>0.7 → 播放拍桌子动画，拒绝服务
    /// - 情绪sadness>0.5 → 播放叹气动画，对话中透露烦恼
    /// - 收到gift → 播放开心动画 + trust+0.2
    /// - 收到attack → 播放愤怒动画 + anger+0.3
    /// - NPC移动范围：酒馆吧台附近（巡逻3个点）
    /// </summary>
    [RequireComponent(typeof(NPCSoul))]
    public class NPCTavernKeeper : MonoBehaviour
    {
        #region NPC配置

        [Header("=== 身份配置 ===")]
        [Tooltip("NPC显示名称")]
        [SerializeField] private string npcName = "艾拉";

        [Tooltip("NPC预设模板")]
        [SerializeField] private string preset = "tavern_keeper";

        [Header("=== 移动配置 ===")]
        [Tooltip("是否启用移动")]
        [SerializeField] private bool enableMovement = true;

        [Tooltip("移动速度")]
        [SerializeField] private float moveSpeed = 1f;

        [Tooltip("巡逻点列表")]
        [SerializeField] private List<Vector3> patrolPoints = new List<Vector3>
        {
            new Vector3(0, 0, 0),
            new Vector3(2, 0, 1),
            new Vector3(-1, 0, 2)
        };

        [Tooltip("巡逻等待时间")]
        [SerializeField] private float patrolWaitTime = 3f;

        [Header("=== 交互配置 ===")]
        [Tooltip("交互触发距离")]
        [SerializeField] private float triggerDistance = 4f;

        [Tooltip("交互冷却时间")]
        [SerializeField] private float interactionCooldown = 5f;

        [Header("=== 对话配置 ===")]
        [Tooltip("欢迎语")]
        [SerializeField] private string welcomeGreeting = "欢迎光临！来杯麦酒暖暖身子吧！";

        [Tooltip("高兴时问候语")]
        [SerializeField] private string happyGreeting = "哦，亲爱的朋友来了！今天过得怎么样？";

        [Tooltip("愤怒时问候语")]
        [SerializeField] private string angryGreeting = "哼...是你啊。还想干什么？";

        [Tooltip("悲伤时问候语")]
        [SerializeField] private string sadGreeting = "唉...最近生意不好做啊...";

        [Tooltip("信任后解锁对话")]
        [SerializeField] private string secretGreeting = "既然你这么信任我...我告诉你一个秘密。";

        [Header("=== 动画配置 ===")]
        [Tooltip("欢迎动画持续时间")]
        [SerializeField] private float welcomeAnimationDuration = 1.5f;

        [Tooltip("斟酒动画持续时间")]
        [SerializeField] private float pourDrinkAnimationDuration = 2f;

        [Tooltip("拍桌子动画持续时间")]
        [SerializeField] private float slamTableAnimationDuration = 1f;

        [Tooltip("叹气动画持续时间")]
        [SerializeField] private float sighAnimationDuration = 1.5f;

        #endregion

        #region 私有变量

        // NPC灵魂组件
        private NPCSoul _npcSoul;

        // 移动状态
        private Vector3 _currentTarget;
        private int _currentPatrolIndex;
        private bool _isMoving;
        private bool _isWaiting;

        // 动画状态
        private bool _isPlayingAnimation;
        private string _currentAnimation;

        // 交互状态
        private bool _hasWelcomedPlayer;
        private float _lastTriggerTime;

        // 对话相关
        private bool _hasUnlockedSecret;
        private List<string> _availableDialogueOptions = new List<string>();

        // 引用
        private Transform _playerTransform;
        private DemoUIManager _uiManager;

        // 动画颜色
        private readonly Color normalColor = new Color(1f, 0.9f, 0.8f);
        private readonly Color happyColor = new Color(1f, 0.95f, 0.7f);
        private readonly Color angryColor = new Color(1f, 0.6f, 0.6f);
        private readonly Color sadColor = new Color(0.8f, 0.8f, 0.9f);

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

            // 配置NPCSoul
            ConfigureNPCSoul();

            // 初始化移动目标
            if (patrolPoints.Count > 0)
            {
                _currentPatrolIndex = 0;
                _currentTarget = transform.position + patrolPoints[0];
            }

            // 订阅事件
            SubscribeToEvents();

            // 开始巡逻
            if (enableMovement)
            {
                StartCoroutine(PatrolRoutine());
            }

            Debug.Log($"[{npcName}] 酒馆老板娘初始化完成");
        }

        /// <summary>
        /// 每帧更新
        /// </summary>
        private void Update()
        {
            // 检查玩家是否在触发范围内
            CheckPlayerProximity();

            // 更新移动
            UpdateMovement();

            // 更新动画
            UpdateAnimation();
        }

        /// <summary>
        /// 销毁时清理
        /// </summary>
        private void OnDestroy()
        {
            UnsubscribeFromEvents();
        }

        #endregion

        #region NPC配置

        /// <summary>
        /// 配置NPCSoul组件
        /// </summary>
        private void ConfigureNPCSoul()
        {
            // 设置NPC信息（通过反射或直接访问）
            // 注意：这里假设NPCSoul有公开的属性或我们使用DemoSceneManager中的扩展方法
            if (_npcSoul != null)
            {
                // 设置显示名称
                var nameProperty = typeof(NPCSoul).GetProperty("NpcName");
                // nameProperty?.SetValue(_npcSoul, npcName);
            }
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
            _npcSoul.OnError += OnError;
            _npcSoul.OnLog += OnLog;
        }

        /// <summary>
        /// 取消订阅事件
        /// </summary>
        private void UnsubscribeFromEvents()
        {
            if (_npcSoul == null) return;

            _npcSoul.OnEmotionChanged -= OnEmotionChanged;
            _npcSoul.OnBehaviorChanged -= OnBehaviorChanged;
            _npcSoul.OnError -= OnError;
            _npcSoul.OnLog -= OnLog;
        }

        /// <summary>
        /// 情绪变化回调
        /// </summary>
        private void OnEmotionChanged(EmotionState emotion)
        {
            Debug.Log($"[{npcName}] 情绪变化: {emotion.dominant}");

            // 根据主导情绪触发行为
            switch (emotion.dominant?.ToLower())
            {
                case "joy":
                    if (emotion.Joy > 0.7f)
                    {
                        TriggerPourDrinkAnimation();
                        UnlockSpecialDialogue();
                    }
                    break;

                case "anger":
                    if (emotion.Anger > 0.7f)
                    {
                        TriggerSlamTableAnimation();
                    }
                    break;

                case "sadness":
                    if (emotion.Sadness > 0.5f)
                    {
                        TriggerSighAnimation();
                    }
                    break;

                case "fear":
                    if (emotion.Fear > 0.5f)
                    {
                        TriggerFleeAnimation();
                    }
                    break;
            }

            // 检查信任度
            if (emotion.Trust > 0.6f && !_hasUnlockedSecret)
            {
                _hasUnlockedSecret = true;
                Debug.Log($"[{npcName}] 解锁了秘密对话！");
            }

            // 更新视觉效果
            UpdateVisualEffect(emotion);
        }

        /// <summary>
        /// 行为变化回调
        /// </summary>
        private void OnBehaviorChanged(List<BehaviorHint> behaviors)
        {
            if (behaviors == null || behaviors.Count == 0) return;

            Debug.Log($"[{npcName}] 行为建议变化: {behaviors.Count}个选项");

            // 更新对话选项
            UpdateDialogueOptions(behaviors);
        }

        /// <summary>
        /// 错误回调
        /// </summary>
        private void OnError(string error)
        {
            Debug.LogWarning($"[{npcName}] 错误: {error}");
        }

        /// <summary>
        /// 日志回调
        /// </summary>
        private void OnLog(string message)
        {
            Debug.Log($"[{npcName}] {message}");
        }

        #endregion

        #region 玩家检测

        /// <summary>
        /// 检查玩家是否在触发范围内
        /// </summary>
        private void CheckPlayerProximity()
        {
            if (_playerTransform == null) return;

            float distance = Vector3.Distance(transform.position, _playerTransform.position);

            // 玩家进入触发范围
            if (distance <= triggerDistance && !_hasWelcomedPlayer)
            {
                OnPlayerEntered();
            }
            // 玩家离开触发范围
            else if (distance > triggerDistance * 1.5f)
            {
                _hasWelcomedPlayer = false;
            }
        }

        /// <summary>
        /// 玩家进入触发区
        /// </summary>
        private void OnPlayerEntered()
        {
            if (Time.time - _lastTriggerTime < interactionCooldown) return;

            _hasWelcomedPlayer = true;
            _lastTriggerTime = Time.time;

            // 面向玩家
            FacePlayer();

            // 播放欢迎动画
            TriggerWelcomeAnimation();

            // 发送情绪事件
            _npcSoul?.SendEvent(GameEventType.player_entered, 0.3f);

            Debug.Log($"[{npcName}] 玩家进入酒馆");
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
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), 0.2f);
            }
        }

        #endregion

        #region 巡逻系统

        /// <summary>
        /// 巡逻协程
        /// </summary>
        private System.Collections.IEnumerator PatrolRoutine()
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
                    // 开始移动到下一个巡逻点
                    StartMoveToNextPatrolPoint();
                }

                yield return new WaitForSeconds(0.1f);
            }
        }

        /// <summary>
        /// 开始移动到下一个巡逻点
        /// </summary>
        private void StartMoveToNextPatrolPoint()
        {
            if (patrolPoints.Count == 0) return;

            // 计算目标位置（相对于初始位置）
            Vector3 basePosition = transform.position;
            Vector3 offset = patrolPoints[_currentPatrolIndex];
            _currentTarget = basePosition + offset;

            _isMoving = true;

            Debug.Log($"[{npcName}] 前往巡逻点 {_currentPatrolIndex + 1}");
        }

        /// <summary>
        /// 更新移动
        /// </summary>
        private void UpdateMovement()
        {
            if (!_isMoving || _isPlayingAnimation) return;

            // 计算方向
            Vector3 direction = (_currentTarget - transform.position);
            direction.y = 0;

            float distance = direction.magnitude;

            // 到达目标
            if (distance < 0.1f)
            {
                _isMoving = false;
                _isWaiting = true;

                // 切换到下一个巡逻点
                _currentPatrolIndex = (_currentPatrolIndex + 1) % patrolPoints.Count;

                // 等待
                StartCoroutine(WaitAtPatrolPoint());
                return;
            }

            // 移动
            direction.Normalize();
            transform.position += direction * moveSpeed * Time.deltaTime;

            // 面向移动方向
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), 0.1f);
        }

        /// <summary>
        /// 在巡逻点等待
        /// </summary>
        private System.Collections.IEnumerator WaitAtPatrolPoint()
        {
            yield return new WaitForSeconds(patrolWaitTime);
            _isWaiting = false;
        }

        #endregion

        #region 动画系统

        /// <summary>
        /// 播放欢迎动画
        /// </summary>
        private void TriggerWelcomeAnimation()
        {
            if (_isPlayingAnimation) return;

            StartCoroutine(PlayAnimationSequence("Welcome", welcomeAnimationDuration, () =>
            {
                // 发送欢迎情绪
                _npcSoul?.SendEvent(GameEventType.npc_complimented, 0.2f);

                // 显示欢迎对话
                ShowGreeting();
            }));
        }

        /// <summary>
        /// 播放斟酒动画
        /// </summary>
        private void TriggerPourDrinkAnimation()
        {
            if (_isPlayingAnimation) return;

            StartCoroutine(PlayAnimationSequence("PourDrink", pourDrinkAnimationDuration, () =>
            {
                Debug.Log($"[{npcName}] 完成斟酒动画");
            }));
        }

        /// <summary>
        /// 播放拍桌子动画
        /// </summary>
        private void TriggerSlamTableAnimation()
        {
            if (_isPlayingAnimation) return;

            StartCoroutine(PlayAnimationSequence("SlamTable", slamTableAnimationDuration, () =>
            {
                Debug.Log($"[{npcName}] 完成拍桌子动画");
            }));
        }

        /// <summary>
        /// 播放叹气动画
        /// </summary>
        private void TriggerSighAnimation()
        {
            if (_isPlayingAnimation) return;

            StartCoroutine(PlayAnimationSequence("Sigh", sighAnimationDuration, () =>
            {
                Debug.Log($"[{npcName}] 完成叹气动画");
            }));
        }

        /// <summary>
        /// 播放逃跑动画
        /// </summary>
        private void TriggerFleeAnimation()
        {
            if (_isPlayingAnimation) return;

            StartCoroutine(PlayAnimationSequence("Flee", 2f, async () =>
            {
                // 移动到安全位置
                Vector3 fleeTarget = transform.position + (UnityEngine.Random.onUnitSphere * 5f);
                fleeTarget.y = transform.position.y;

                float elapsed = 0f;
                while (elapsed < 1.5f)
                {
                    transform.position = Vector3.Lerp(transform.position, fleeTarget, Time.deltaTime * 2f);
                    elapsed += Time.deltaTime;
                    yield return null;
                }

                Debug.Log($"[{npcName}] 逃跑后重新出现");

                // 短暂消失后重新出现
                gameObject.SetActive(false);
                yield return new WaitForSeconds(3f);
                gameObject.SetActive(true);
            }));
        }

        /// <summary>
        /// 播放动画序列
        /// </summary>
        private System.Collections.IEnumerator PlayAnimationSequence(string animationName, float duration, Action onComplete)
        {
            _isPlayingAnimation = true;
            _currentAnimation = animationName;

            // 使用简单的缩放动画模拟
            Vector3 originalScale = transform.localScale;
            Vector3 bounceScale = originalScale * 1.1f;

            float elapsed = 0f;
            bool goingUp = true;

            while (elapsed < duration)
            {
                float t = elapsed / duration;

                // 根据动画类型应用不同的效果
                switch (animationName)
                {
                    case "Welcome":
                        // 简单的上下浮动
                        float offset = Mathf.Sin(t * Mathf.PI * 2) * 0.1f;
                        transform.position += Vector3.up * offset * Time.deltaTime;
                        break;

                    case "SlamTable":
                        // 快速下压
                        if (goingUp && t < 0.3f)
                        {
                            transform.localScale = Vector3.Lerp(originalScale, bounceScale, t / 0.3f);
                        }
                        else
                        {
                            goingUp = false;
                            transform.localScale = Vector3.Lerp(bounceScale, originalScale * 0.9f, (t - 0.3f) / 0.7f);
                        }
                        break;

                    case "Sigh":
                        // 缓慢下沉
                        float yOffset = Mathf.Sin(t * Mathf.PI) * 0.2f;
                        transform.position = new Vector3(transform.position.x, transform.position.y - yOffset * Time.deltaTime, transform.position.z);
                        break;

                    case "Flee":
                        // 快速抖动
                        if (elapsed % 0.1f < 0.05f)
                        {
                            transform.position += UnityEngine.Random.insideUnitSphere * 0.1f;
                        }
                        break;
                }

                elapsed += Time.deltaTime;
                yield return null;
            }

            // 恢复原始状态
            transform.localScale = originalScale;
            _isPlayingAnimation = false;
            _currentAnimation = null;

            onComplete?.Invoke();
        }

        /// <summary>
        /// 更新动画状态
        /// </summary>
        private void UpdateAnimation()
        {
            // 根据当前情绪调整动画
            if (_isPlayingAnimation) return;

            var emotion = _npcSoul?.CurrentEmotion;
            if (emotion == null) return;

            // 可以根据情绪状态播放不同的待机动画
            // 这里简化处理，只改变颜色
        }

        #endregion

        #region 视觉效果

        /// <summary>
        /// 更新视觉效果
        /// </summary>
        private void UpdateVisualEffect(EmotionState emotion)
        {
            // 根据情绪改变NPC颜色
            Renderer renderer = GetComponent<Renderer>();
            if (renderer == null)
            {
                // 尝试获取子物体
                renderer = GetComponentInChildren<Renderer>();
            }

            if (renderer != null)
            {
                Color targetColor = normalColor;

                if (emotion.Joy > 0.5f)
                    targetColor = Color.Lerp(normalColor, happyColor, emotion.Joy);
                else if (emotion.Anger > 0.5f)
                    targetColor = Color.Lerp(normalColor, angryColor, emotion.Anger);
                else if (emotion.Sadness > 0.5f)
                    targetColor = Color.Lerp(normalColor, sadColor, emotion.Sadness);

                renderer.material.color = targetColor;
            }
        }

        #endregion

        #region 对话系统

        /// <summary>
        /// 显示问候语
        /// </summary>
        private void ShowGreeting()
        {
            var emotion = _npcSoul?.CurrentEmotion;
            string greeting = welcomeGreeting;

            if (emotion != null)
            {
                if (emotion.Anger > 0.6f)
                    greeting = angryGreeting;
                else if (emotion.Joy > 0.6f)
                    greeting = happyGreeting;
                else if (emotion.Sadness > 0.4f)
                    greeting = sadGreeting;
            }

            _uiManager?.ShowDialogue(npcName, greeting, GetDialogueOptions());
        }

        /// <summary>
        /// 获取对话选项
        /// </summary>
        private List<string> GetDialogueOptions()
        {
            var options = new List<string>
            {
                "给我来杯麦酒",
                "最近生意怎么样？",
                "有什么新鲜事吗？"
            };

            // 信任度高时解锁特殊选项
            if (_hasUnlockedSecret || (_npcSoul?.CurrentEmotion?.Trust ?? 0) > 0.6f)
            {
                options.Add("听说这附近有什么秘密？");
            }

            // 快乐时解锁斟酒对话
            if ((_npcSoul?.CurrentEmotion?.Joy ?? 0) > 0.7f)
            {
                options.Add("能给我调一杯特调吗？");
            }

            // 愤怒时解锁安抚选项
            if ((_npcSoul?.CurrentEmotion?.Anger ?? 0) > 0.5f)
            {
                options.Add("发生什么事了？");
                options.Add("对不起，我错了");
            }

            return options;
        }

        /// <summary>
        /// 更新对话选项
        /// </summary>
        private void UpdateDialogueOptions(List<BehaviorHint> behaviors)
        {
            _availableDialogueOptions.Clear();

            foreach (var behavior in behaviors)
            {
                if (behavior.Type == "dialogue" && !string.IsNullOrEmpty(behavior.Content))
                {
                    _availableDialogueOptions.Add(behavior.Content);
                }
            }
        }

        /// <summary>
        /// 解锁特殊对话
        /// </summary>
        private void UnlockSpecialDialogue()
        {
            Debug.Log($"[{npcName}] 解锁了特殊对话选项！");
        }

        #endregion

        #region 公共方法

        /// <summary>
        /// 获取NPC名称
        /// </summary>
        public string GetNPCName()
        {
            return npcName;
        }

        /// <summary>
        /// 获取NPC灵魂组件
        /// </summary>
        public NPCSoul GetNPCSoul()
        {
            return _npcSoul;
        }

        /// <summary>
        /// 是否正在播放动画
        /// </summary>
        public bool IsPlayingAnimation()
        {
            return _isPlayingAnimation;
        }

        #endregion

        #region 调试

        /// <summary>
        /// 绘制Gizmos
        /// </summary>
        private void OnDrawGizmosSelected()
        {
            // 绘制触发范围
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position, triggerDistance);

            // 绘制巡逻路径
            if (patrolPoints.Count > 1)
            {
                Gizmos.color = Color.blue;
                for (int i = 0; i < patrolPoints.Count; i++)
                {
                    Vector3 point = transform.position + patrolPoints[i];
                    Gizmos.DrawWireSphere(point, 0.3f);

                    int next = (i + 1) % patrolPoints.Count;
                    Vector3 nextPoint = transform.position + patrolPoints[next];
                    Gizmos.DrawLine(point, nextPoint);
                }
            }

            // 绘制当前移动目标
            if (_isMoving)
            {
                Gizmos.color = Color.green;
                Gizmos.DrawSphere(_currentTarget, 0.2f);
            }
        }

        #endregion
    }
}
