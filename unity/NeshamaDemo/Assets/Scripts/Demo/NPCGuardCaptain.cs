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
    /// 守卫队长NPC控制器
    /// 
    /// 特殊行为：
    /// - 玩家靠近城门 → SendEvent(npc_complimented, 0.1)
    /// - 情绪anger>0.8 → 播放拔剑动画，封锁通道
    /// - trust>0.7 → 解锁"夜行通行"特殊对话
    /// - 收到attack → SendEvent(player_attacked, 0.9) + 召唤2个守卫NPC
    /// - NPC移动范围：城门口巡逻路线
    /// </summary>
    [RequireComponent(typeof(NPCSoul))]
    public class NPCGuardCaptain : MonoBehaviour
    {
        #region NPC配置

        [Header("=== 身份配置 ===")]
        [Tooltip("NPC显示名称")]
        [SerializeField] private string npcName = "凯尔";

        [Tooltip("NPC预设模板")]
        [SerializeField] private string preset = "guard_captain";

        [Header("=== 移动配置 ===")]
        [Tooltip("是否启用移动")]
        [SerializeField] private bool enableMovement = true;

        [Tooltip("移动速度")]
        [SerializeField] private float moveSpeed = 1.5f;

        [Tooltip("巡逻点列表")]
        [SerializeField] private List<Vector3> patrolPoints = new List<Vector3>
        {
            new Vector3(0, 0, 0),
            new Vector3(4, 0, 0),
            new Vector3(4, 0, -2),
            new Vector3(0, 0, -2)
        };

        [Tooltip("巡逻等待时间")]
        [SerializeField] private float patrolWaitTime = 4f;

        [Header("=== 交互配置 ===")]
        [Tooltip("城门区域触发距离")]
        [SerializeField] private float gateTriggerDistance = 6f;

        [Tooltip("对话触发距离")]
        [SerializeField] private float talkTriggerDistance = 4f;

        [Tooltip("交互冷却时间")]
        [SerializeField] private float interactionCooldown = 8f;

        [Header("=== 对话配置 ===")]
        [Tooltip("普通问候语")]
        [SerializeField] private string normalGreeting = "站住！有什么事？";

        [Tooltip("友好问候语")]
        [SerializeField] private string friendlyGreeting = "哦，是朋友啊。有什么事需要帮忙吗？";

        [Tooltip("警惕问候语")]
        [SerializeField] private string alertGreeting = "我注意到你了...你最好别打什么主意。";

        [Tooltip("愤怒问候语")]
        [SerializeField] private string angryGreeting = "滚开！不欢迎你！";

        [Tooltip("信任后解锁对话")]
        [SerializeField] private string trustedGreeting = "既然你这么真诚...我可以给你开一张夜行通行证。";

        [Header("=== 召唤守卫配置 ===")]
        [Tooltip("召唤守卫预制件")]
        [SerializeField] private GameObject guardPrefab;

        [Tooltip("召唤守卫位置偏移")]
        [SerializeField] private List<Vector3> guardSpawnOffsets = new List<Vector3>
        {
            new Vector3(2, 0, 1),
            new Vector3(-2, 0, 1)
        };

        [Tooltip("是否已经召唤过守卫")]
        [SerializeField] private bool hasSpawnedGuards = false;

        [Header("=== 封锁配置 ===")]
        [Tooltip("城门封锁状态")]
        [SerializeField] private bool isGateBlocked = false;

        [Tooltip("封锁门预制件")]
        [SerializeField] private GameObject gateBlockPrefab;

        [Tooltip("封锁门位置")]
        [SerializeField] private Vector3 gateBlockPosition = new Vector3(0, 1, 0);

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
        private float _lastTriggerTime;
        private bool _hasUnlockedNightPass;
        private bool _isAlerted;

        // 守卫列表
        private List<GameObject> _spawnedGuards = new List<GameObject>();

        // 封锁门
        private GameObject _gateBlock;

        // 引用
        private Transform _playerTransform;
        private DemoUIManager _uiManager;

        // 动画颜色
        private readonly Color normalColor = new Color(0.7f, 0.8f, 0.9f);
        private readonly Color alertColor = new Color(0.9f, 0.7f, 0.6f);
        private readonly Color angryColor = new Color(0.9f, 0.5f, 0.5f);

        // 是否在城门区域
        private bool _isAtGate = false;

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

            // 创建封锁门（如果需要）
            if (isGateBlocked)
            {
                CreateGateBlock();
            }

            Debug.Log($"[{npcName}] 守卫队长初始化完成");
        }

        /// <summary>
        /// 每帧更新
        /// </summary>
        private void Update()
        {
            // 检查城门区域
            CheckGateProximity();

            // 检查玩家交互
            CheckPlayerInteraction();

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

            // 清理守卫
            foreach (var guard in _spawnedGuards)
            {
                if (guard != null)
                {
                    Destroy(guard);
                }
            }

            // 清理封锁门
            if (_gateBlock != null)
            {
                Destroy(_gateBlock);
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

            // 愤怒值过高 → 封锁城门
            if (emotion.Anger > 0.8f && !isGateBlocked)
            {
                BlockGate();
            }

            // 愤怒值降低 → 解除封锁
            if (emotion.Anger < 0.3f && isGateBlocked)
            {
                UnblockGate();
            }

            // 信任值足够 → 解锁夜行通行证
            if (emotion.Trust > 0.7f && !_hasUnlockedNightPass)
            {
                _hasUnlockedNightPass = true;
                Debug.Log($"[{npcName}] 解锁了夜行通行证对话！");
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

        #region 区域检测

        /// <summary>
        /// 检查城门区域
        /// </summary>
        private void CheckGateProximity()
        {
            if (_playerTransform == null) return;

            float distance = Vector3.Distance(transform.position, _playerTransform.position);

            // 进入城门区域
            if (distance <= gateTriggerDistance && !_isAtGate)
            {
                _isAtGate = true;
                OnPlayerApproachGate();
            }
            // 离开城门区域
            else if (distance > gateTriggerDistance * 1.2f)
            {
                _isAtGate = false;
            }
        }

        /// <summary>
        /// 玩家接近城门
        /// </summary>
        private void OnPlayerApproachGate()
        {
            // 发送情绪事件
            var emotion = _npcSoul?.CurrentEmotion;

            if (emotion != null && emotion.Trust > 0.5f)
            {
                // 友好态度
                _npcSoul?.SendEvent(GameEventType.npc_complimented, 0.1f);
            }
            else if (emotion != null && emotion.Anger > 0.5f)
            {
                // 警惕态度
                _npcSoul?.SendEvent(GameEventType.npc_insulted, 0.2f);
                _isAlerted = true;
            }
            else
            {
                // 中立态度
                _npcSoul?.SendEvent(GameEventType.player_entered, 0.2f);
            }

            Debug.Log($"[{npcName}] 玩家接近城门区域");
        }

        /// <summary>
        /// 检查玩家交互
        /// </summary>
        private void CheckPlayerInteraction()
        {
            if (_playerTransform == null) return;

            float distance = Vector3.Distance(transform.position, _playerTransform.position);

            // 如果愤怒值过高且玩家靠近
            var emotion = _npcSoul?.CurrentEmotion;
            if (emotion != null && emotion.Anger > 0.7f && distance <= talkTriggerDistance)
            {
                // 持续发送警惕信号
                if (Time.time - _lastTriggerTime > interactionCooldown)
                {
                    _npcSoul?.SendEvent(GameEventType.player_entered, 0.1f);
                    _lastTriggerTime = Time.time;
                }
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

            Vector3 direction = (_currentTarget - transform.position);
            direction.y = 0;

            float distance = direction.magnitude;

            if (distance < 0.1f)
            {
                _isMoving = false;
                _isWaiting = true;

                _currentPatrolIndex = (_currentPatrolIndex + 1) % patrolPoints.Count;

                StartCoroutine(WaitAtPatrolPoint());
                return;
            }

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

        #region 封锁系统

        /// <summary>
        /// 封锁城门
        /// </summary>
        private void BlockGate()
        {
            if (isGateBlocked) return;

            isGateBlocked = true;

            // 播放拔剑动画
            TriggerDrawSwordAnimation();

            // 创建封锁门
            CreateGateBlock();

            // 通知场景
            DemoSceneManager.Instance?.TriggerStoryEvent("城门戒严！守卫变得更加警惕。");

            Debug.Log($"[{npcName}] 封锁了城门！");
        }

        /// <summary>
        /// 解除封锁
        /// </summary>
        private void UnblockGate()
        {
            if (!isGateBlocked) return;

            isGateBlocked = false;

            // 销毁封锁门
            if (_gateBlock != null)
            {
                Destroy(_gateBlock);
                _gateBlock = null;
            }

            Debug.Log($"[{npcName}] 解除了城门封锁");
        }

        /// <summary>
        /// 创建封锁门
        /// </summary>
        private void CreateGateBlock()
        {
            if (_gateBlock != null) return;

            // 创建简单的封锁门（Box）
            _gateBlock = GameObject.CreatePrimitive(PrimitiveType.Box);
            _gateBlock.name = "GateBlock";
            _gateBlock.transform.position = gateBlockPosition;
            _gateBlock.transform.localScale = new Vector3(3f, 2f, 0.3f);

            // 设置材质
            var renderer = _gateBlock.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material.color = new Color(0.3f, 0.3f, 0.3f);
            }

            // 移除碰撞体（玩家不能通过但可以看到）
            var collider = _gateBlock.GetComponent<Collider>();
            if (collider != null)
            {
                Destroy(collider);
            }
        }

        #endregion

        #region 召唤守卫

        /// <summary>
        /// 召唤守卫
        /// </summary>
        private void SpawnGuards()
        {
            if (hasSpawnedGuards) return;

            hasSpawnedGuards = true;

            foreach (var offset in guardSpawnOffsets)
            {
                Vector3 spawnPos = transform.position + offset;
                spawnPos.y = 0;

                // 创建守卫
                var guard = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                guard.name = "Guard";
                guard.transform.position = spawnPos;

                // 设置守卫颜色
                var renderer = guard.GetComponent<Renderer>();
                if (renderer != null)
                {
                    renderer.material.color = new Color(0.6f, 0.6f, 0.7f);
                }

                // 移除碰撞体
                var collider = guard.GetComponent<Collider>();
                if (collider != null)
                {
                    Destroy(collider);
                }

                _spawnedGuards.Add(guard);

                Debug.Log($"[{npcName}] 召唤了守卫 at {spawnPos}");
            }
        }

        #endregion

        #region 动画系统

        /// <summary>
        /// 播放拔剑动画
        /// </summary>
        private void TriggerDrawSwordAnimation()
        {
            if (_isPlayingAnimation) return;

            StartCoroutine(PlayAnimationSequence("DrawSword", 1.5f, () =>
            {
                Debug.Log($"[{npcName}] 完成拔剑动画");
            }));
        }

        /// <summary>
        /// 播放动画序列
        /// </summary>
        private System.Collections.IEnumerator PlayAnimationSequence(string animationName, float duration, Action onComplete)
        {
            _isPlayingAnimation = true;
            _currentAnimation = animationName;

            Vector3 originalScale = transform.localScale;

            float elapsed = 0f;

            while (elapsed < duration)
            {
                float t = elapsed / duration;

                switch (animationName)
                {
                    case "DrawSword":
                        // 拔剑动作 - 向右伸展
                        if (t < 0.5f)
                        {
                            float scale = Mathf.Lerp(1f, 1.15f, t * 2f);
                            transform.localScale = new Vector3(scale, scale, scale);
                        }
                        else
                        {
                            float scale = Mathf.Lerp(1.15f, 1.1f, (t - 0.5f) * 2f);
                            transform.localScale = new Vector3(scale, scale, scale);
                        }
                        break;
                }

                elapsed += Time.deltaTime;
                yield return null;
            }

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
            if (_isPlayingAnimation) return;

            // 根据情绪调整
        }

        #endregion

        #region 视觉效果

        /// <summary>
        /// 更新视觉效果
        /// </summary>
        private void UpdateVisualEffect(EmotionState emotion)
        {
            Renderer renderer = GetComponent<Renderer>();
            if (renderer == null)
            {
                renderer = GetComponentInChildren<Renderer>();
            }

            if (renderer != null)
            {
                Color targetColor = normalColor;

                if (_isAlerted)
                    targetColor = alertColor;
                if (emotion.Anger > 0.5f)
                    targetColor = Color.Lerp(alertColor, angryColor, emotion.Anger);

                renderer.material.color = targetColor;
            }
        }

        #endregion

        #region 公共方法

        /// <summary>
        /// 处理攻击事件
        /// </summary>
        public void HandleAttack()
        {
            // 发送被攻击事件
            _npcSoul?.SendEvent(GameEventType.player_attacked, 0.9f);

            // 召唤守卫
            SpawnGuards();

            // 封锁城门
            BlockGate();

            // 通知场景
            DemoSceneManager.Instance?.TriggerStoryEvent("你攻击了守卫队长！他召唤了援军！");

            Debug.Log($"[{npcName}] 遭到攻击，召唤守卫并封锁城门");
        }

        /// <summary>
        /// 获取对话问候语
        /// </summary>
        public string GetGreeting()
        {
            var emotion = _npcSoul?.CurrentEmotion;

            if (emotion == null)
                return normalGreeting;

            if (emotion.Anger > 0.7f)
                return angryGreeting;
            if (_isAlerted)
                return alertGreeting;
            if (emotion.Trust > 0.6f)
                return friendlyGreeting;

            return normalGreeting;
        }

        /// <summary>
        /// 是否城门被封锁
        /// </summary>
        public bool IsGateBlocked()
        {
            return isGateBlocked;
        }

        /// <summary>
        /// 获取NPC名称
        /// </summary>
        public string GetNPCName()
        {
            return npcName;
        }

        #endregion

        #region 调试

        /// <summary>
        /// 绘制Gizmos
        /// </summary>
        private void OnDrawGizmosSelected()
        {
            // 城门触发区域
            Gizmos.color = Color.red;
            Gizmos.DrawWireSphere(transform.position, gateTriggerDistance);

            // 对话触发区域
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position, talkTriggerDistance);

            // 巡逻路径
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

            // 封锁门位置
            Gizmos.color = Color.red;
            Gizmos.DrawWireCube(gateBlockPosition, new Vector3(3f, 2f, 0.3f));

            // 守卫生成位置
            Gizmos.color = Color.yellow;
            foreach (var offset in guardSpawnOffsets)
            {
                Gizmos.DrawWireSphere(transform.position + offset, 0.3f);
            }
        }

        #endregion
    }
}
