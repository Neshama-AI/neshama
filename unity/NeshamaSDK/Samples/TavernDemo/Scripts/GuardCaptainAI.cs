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
    /// 守卫队长AI控制器 - Demo示例
    /// 
    /// 演示如何使用NPCSoul组件实现更严肃、更有军事风格的NPC
    /// 包括：
    /// - 敌人接近时的戒备反应
    /// - 任务完成时的认可反应
    /// - 战斗开始时的战斗对话风格
    /// - 更严格的判断逻辑
    /// </summary>
    public class GuardCaptainAI : MonoBehaviour
    {
        #region 配置

        [Header("=== 身份配置 ===")]
        [Tooltip("NPC显示名称")]
        [SerializeField]
        private string npcName = "守卫队长";

        [Tooltip("NPC预设模板")]
        [SerializeField]
        private string preset = "guard_captain";

        [Header("=== 警戒配置 ===")]
        [Tooltip("警戒范围")]
        [SerializeField]
        private float alertRadius = 10f;

        [Tooltip("敌人检测范围")]
        [SerializeField]
        private float enemyDetectionRadius = 15f;

        [Tooltip("警戒阈值（0-1）")]
        [SerializeField]
        [Range(0f, 1f)]
        private float alertThreshold = 0.6f;

        [Header("=== 战斗配置 ===")]
        [Tooltip("战斗状态时移动速度倍数")]
        [SerializeField]
        private float combatSpeedMultiplier = 1.5f;

        [Tooltip("战斗命令显示时间")]
        [SerializeField]
        private float combatCommandDisplayTime = 2f;

        [Header("=== 对话配置 ===")]
        [Tooltip("默认敬礼语")]
        [SerializeField]
        private string defaultSalute = "职责所在！";

        [Tooltip("进入戒备时的警告语")]
        [SerializeField]
        private string alertWarning = "站住！前方禁止通行！";

        [Tooltip("战斗开始时的命令")]
        [SerializeField]
        private string combatStartCommand = "准备战斗！保护平民！";

        [Tooltip("任务完成时的认可语")]
        [SerializeField]
        private string questCompletedPraise = "干得漂亮！城民们会记住你的名字。";

        [Tooltip("NPC灵魂组件")]
        [SerializeField]
        private NPCSoul npcSoul;

        #endregion

        #region 枚举定义

        /// <summary>
        /// 守卫状态
        /// </summary>
        private enum GuardState
        {
            Idle,       // 空闲
            Alert,      // 戒备
            Combat,     // 战斗
            PostCombat  // 战后
        }

        #endregion

        #region 私有变量

        // 当前守卫状态
        private GuardState currentState = GuardState.Idle;

        // 警戒等级（0-1）
        private float alertLevel = 0f;

        // 敌人列表
        private List<Transform> detectedEnemies = new List<Transform>();

        // 玩家引用
        private Transform player;

        // NPC导航代理
        private UnityEngine.AI.NavMeshAgent navAgent;

        // 基础速度
        private float baseSpeed;

        // UI文本组件
        private TMPro.TextMeshProUGUI statusText;

        // 警戒指示器
        private GameObject alertIndicator;

        // 警戒状态颜色
        private readonly Color idleColor = Color.green;
        private readonly Color alertColor = Color.yellow;
        private readonly Color combatColor = Color.red;
        private readonly Color postCombatColor = Color.blue;

        // 战斗冷却时间
        private float lastCombatTime = -999f;
        private float combatCooldown = 10f;

        // 是否在执行任务
        private bool isOnMission = false;

        // 任务完成后的额外信任
        private float trustBonus = 0f;

        #endregion

        #region Unity生命周期

        /// <summary>
        /// 初始化
        /// </summary>
        private void Start()
        {
            // 查找玩家
            player = GameObject.FindGameObjectWithTag("Player")?.transform;

            // 获取导航代理
            navAgent = GetComponent<UnityEngine.AI.NavMeshAgent>();
            if (navAgent != null)
            {
                baseSpeed = navAgent.speed;
            }

            // 确保NPCSoul组件存在
            EnsureNPCSoul();

            // 订阅事件
            SubscribeToEvents();

            // 初始化UI
            InitializeUI();

            // 创建警戒指示器
            CreateAlertIndicator();

            Debug.Log($"[{npcName}] 守卫队长初始化完成，状态: {currentState}");
        }

        /// <summary>
        /// 每帧更新
        /// </summary>
        private void Update()
        {
            // 检测敌人
            DetectEnemies();

            // 更新警戒等级
            UpdateAlertLevel();

            // 根据状态更新行为
            UpdateBehavior();

            // 更新指示器
            UpdateAlertIndicator();
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
            // 绘制警戒范围
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position, alertRadius);

            // 绘制敌人检测范围
            Gizmos.color = Color.red;
            Gizmos.DrawWireSphere(transform.position, enemyDetectionRadius);
        }

        #endregion

        #region 初始化方法

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
                $"guard_captain_{npcName.GetHashCode()}",
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
                npcSoul.OnConnectionStateChanged -= OnConnectionStateChanged;
            }
        }

        /// <summary>
        /// 初始化UI
        /// </summary>
        private void InitializeUI()
        {
            var canvas = FindObjectOfType<UnityEngine.Canvas>();
            if (canvas != null)
            {
                // 创建状态文本
                var textObj = new GameObject("StatusText");
                textObj.transform.SetParent(canvas.transform, false);

                statusText = textObj.AddComponent<TMPro.TextMeshProUGUI>();
                statusText.text = defaultSalute;
                statusText.fontSize = 20;
                statusText.alignment = TextAlignmentOptions.Top;
                statusText.rectTransform.anchoredPosition = new Vector2(0, -50);
                statusText.rectTransform.sizeDelta = new Vector2(500, 50);
            }
        }

        /// <summary>
        /// 创建警戒指示器
        /// </summary>
        private void CreateAlertIndicator()
        {
            // 创建简单的指示器球
            alertIndicator = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            alertIndicator.name = "AlertIndicator";
            alertIndicator.transform.SetParent(transform);
            alertIndicator.transform.localPosition = Vector3.up * 2.5f;
            alertIndicator.transform.localScale = Vector3.one * 0.3f;

            // 移除碰撞器
            var collider = alertIndicator.GetComponent<Collider>();
            if (collider != null) Destroy(collider);

            // 设置材质
            var renderer = alertIndicator.GetComponent<Renderer>();
            renderer.material = new Material(Shader.Find("Standard"));
            renderer.material.color = idleColor;

            // 隐藏指示器（除非在警戒状态）
            alertIndicator.SetActive(false);
        }

        #endregion

        #region 敌人检测与警戒

        /// <summary>
        /// 检测敌人
        /// </summary>
        private void DetectEnemies()
        {
            detectedEnemies.Clear();

            // 查找所有敌人标签的对象
            var enemies = FindObjectsOfType<Collider>();
            foreach (var enemy in enemies)
            {
                if (enemy.CompareTag("Enemy"))
                {
                    float distance = Vector3.Distance(transform.position, enemy.transform.position);
                    if (distance <= enemyDetectionRadius)
                    {
                        detectedEnemies.Add(enemy.transform);
                    }
                }
            }
        }

        /// <summary>
        /// 更新警戒等级
        /// </summary>
        private void UpdateAlertLevel()
        {
            // 根据敌人数量和距离计算警戒等级
            float targetAlert = 0f;

            foreach (var enemy in detectedEnemies)
            {
                float distance = Vector3.Distance(transform.position, enemy.position);
                float distanceFactor = 1f - (distance / enemyDetectionRadius);
                targetAlert += distanceFactor * 0.5f;
            }

            // 平滑过渡
            alertLevel = Mathf.Lerp(alertLevel, targetAlert, Time.deltaTime * 2f);
            alertLevel = Mathf.Clamp01(alertLevel);

            // 根据警戒等级设置状态
            if (alertLevel >= alertThreshold && currentState == GuardState.Idle)
            {
                SetState(GuardState.Alert);
            }
            else if (alertLevel < alertThreshold * 0.5f && currentState == GuardState.Alert)
            {
                SetState(GuardState.Idle);
            }
        }

        /// <summary>
        /// 更新行为
        /// </summary>
        private void UpdateBehavior()
        {
            switch (currentState)
            {
                case GuardState.Idle:
                    // 空闲状态，正常巡逻
                    if (navAgent != null && !navAgent.hasPath)
                    {
                        // 简单的巡逻逻辑
                        Patrol();
                    }
                    break;

                case GuardState.Alert:
                    // 戒备状态，面向威胁
                    FaceNearestEnemy();
                    break;

                case GuardState.Combat:
                    // 战斗状态
                    UpdateCombat();
                    break;

                case GuardState.PostCombat:
                    // 战后状态，逐渐恢复
                    if (Time.time - lastCombatTime > combatCooldown)
                    {
                        SetState(GuardState.Idle);
                    }
                    break;
            }

            // 更新速度
            if (navAgent != null)
            {
                float targetSpeed = currentState == GuardState.Combat 
                    ? baseSpeed * combatSpeedMultiplier 
                    : baseSpeed;
                navAgent.speed = Mathf.Lerp(navAgent.speed, targetSpeed, Time.deltaTime * 2f);
            }
        }

        /// <summary>
        /// 更新警戒指示器
        /// </summary>
        private void UpdateAlertIndicator()
        {
            if (alertIndicator == null) return;

            // 只有在警戒或战斗状态显示
            alertIndicator.SetActive(currentState != GuardState.Idle);

            // 根据警戒等级更新颜色
            Color indicatorColor;
            if (currentState == GuardState.Combat)
            {
                indicatorColor = combatColor;
            }
            else if (currentState == GuardState.Alert)
            {
                // 闪烁效果
                float blink = Mathf.Sin(Time.time * 5f) * 0.5f + 0.5f;
                indicatorColor = Color.Lerp(alertColor, combatColor, blink * alertLevel);
            }
            else
            {
                indicatorColor = idleColor;
            }

            alertIndicator.GetComponent<Renderer>().material.color = indicatorColor;
        }

        /// <summary>
        /// 简单巡逻逻辑
        /// </summary>
        private void Patrol()
        {
            if (navAgent == null || !navAgent.isActiveAndEnabled) return;

            // 在附近随机选择一个点
            Vector3 randomPoint = transform.position + Random.insideUnitSphere * alertRadius;
            if (UnityEngine.AI.NavMesh.SamplePosition(randomPoint, out var hit, 5f, UnityEngine.AI.NavMesh.AllAreas))
            {
                navAgent.SetDestination(hit.position);
            }
        }

        /// <summary>
        /// 面向最近的敌人
        /// </summary>
        private void FaceNearestEnemy()
        {
            if (detectedEnemies.Count == 0) return;

            Transform nearest = null;
            float nearestDist = float.MaxValue;

            foreach (var enemy in detectedEnemies)
            {
                float dist = Vector3.Distance(transform.position, enemy.position);
                if (dist < nearestDist)
                {
                    nearestDist = dist;
                    nearest = enemy;
                }
            }

            if (nearest != null)
            {
                Vector3 direction = (nearest.position - transform.position).normalized;
                direction.y = 0;
                transform.rotation = Quaternion.Slerp(
                    transform.rotation, 
                    Quaternion.LookRotation(direction), 
                    Time.deltaTime * 5f
                );
            }
        }

        /// <summary>
        /// 更新战斗行为
        /// </summary>
        private void UpdateCombat()
        {
            if (navAgent == null) return;

            // 面向最近的敌人并移动
            FaceNearestEnemy();

            if (detectedEnemies.Count > 0)
            {
                // 保持一定距离
                Transform nearest = GetNearestEnemy();
                if (nearest != null)
                {
                    float dist = Vector3.Distance(transform.position, nearest.position);
                    if (dist > 3f)
                    {
                        navAgent.SetDestination(nearest.position);
                    }
                    else if (dist < 2f)
                    {
                        // 后退
                        Vector3 away = (transform.position - nearest.position).normalized;
                        navAgent.SetDestination(transform.position + away * 2f);
                    }
                }
            }
        }

        /// <summary>
        /// 获取最近的敌人
        /// </summary>
        private Transform GetNearestEnemy()
        {
            if (detectedEnemies.Count == 0) return null;

            Transform nearest = null;
            float nearestDist = float.MaxValue;

            foreach (var enemy in detectedEnemies)
            {
                float dist = Vector3.Distance(transform.position, enemy.position);
                if (dist < nearestDist)
                {
                    nearestDist = dist;
                    nearest = enemy;
                }
            }

            return nearest;
        }

        /// <summary>
        /// 设置守卫状态
        /// </summary>
        private void SetState(GuardState newState)
        {
            if (currentState == newState) return;

            var oldState = currentState;
            currentState = newState;

            Debug.Log($"[{npcName}] 状态从 {oldState} 变为 {newState}");

            // 状态变化处理
            switch (newState)
            {
                case GuardState.Alert:
                    HandleAlertStateEnter();
                    break;

                case GuardState.Combat:
                    HandleCombatStateEnter();
                    break;

                case GuardState.PostCombat:
                    HandlePostCombatStateEnter();
                    break;

                case GuardState.Idle:
                    HandleIdleStateEnter();
                    break;
            }
        }

        #endregion

        #region 状态处理

        /// <summary>
        /// 进入戒备状态
        /// </summary>
        private void HandleAlertStateEnter()
        {
            ShowStatus(alertWarning);

            // 发送被侮辱事件（因为敌人接近了警戒范围）
            _ = SendEventAsync(GameEventType.npc_insulted, alertLevel, new Dictionary<string, object>
            {
                { "reason", "enemy_approaching" }
            });
        }

        /// <summary>
        /// 进入战斗状态
        /// </summary>
        private void HandleCombatStateEnter()
        {
            ShowStatus(combatStartCommand);

            // 发送战斗开始事件
            _ = SendEventAsync(GameEventType.combat_started, 0.7f, new Dictionary<string, object>
            {
                { "enemy_count", detectedEnemies.Count }
            });
        }

        /// <summary>
        /// 进入战后状态
        /// </summary>
        private void HandlePostCombatStateEnter()
        {
            lastCombatTime = Time.time;

            ShowStatus("威胁解除...恢复警戒状态。");

            // 发送战斗结束事件
            _ = SendEventAsync(GameEventType.combat_ended, 0.5f, new Dictionary<string, object>
            {
                { "duration", Time.time - lastCombatTime }
            });
        }

        /// <summary>
        /// 进入空闲状态
        /// </summary>
        private void HandleIdleStateEnter()
        {
            ShowStatus(defaultSalute);
            alertLevel = 0f;
        }

        #endregion

        #region 公共交互方法

        /// <summary>
        /// 敌人进入攻击范围（由战斗系统调用）
        /// </summary>
        public void OnEnemyInRange(int enemyCount)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 敌人进入攻击范围: {enemyCount}");

            if (currentState != GuardState.Combat)
            {
                SetState(GuardState.Combat);
            }
        }

        /// <summary>
        /// 玩家完成守卫任务
        /// </summary>
        public void OnQuestCompleted(string questName)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 任务完成: {questName}");

            ShowStatus(questCompletedPraise);

            // 发送任务完成事件
            _ = SendEventAsync(GameEventType.quest_completed, 0.8f, new Dictionary<string, object>
            {
                { "quest_name", questName },
                { "quest_type", "guard_duty" }
            });

            // 增加信任
            trustBonus += 0.2f;

            // 解锁新对话
            StartCoroutine(UnlockNewDialogueAfterDelay(3f));
        }

        /// <summary>
        /// 玩家接受守卫任务
        /// </summary>
        public void OnQuestAccepted(string questName)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 任务接受: {questName}");

            ShowStatus($"很好！任务详情已记录。保持警惕！");

            // 发送任务接受事件
            _ = SendEventAsync(GameEventType.quest_accepted, 0.4f, new Dictionary<string, object>
            {
                { "quest_name", questName }
            });

            isOnMission = true;
        }

        /// <summary>
        /// 玩家与守卫队长对话
        /// </summary>
        public async void OnPlayerChat(string message)
        {
            if (npcSoul == null || !npcSoul.IsConnected)
            {
                ShowStatus("我现在没空...正在执行任务。");
                return;
            }

            // 根据状态决定是否回应
            if (currentState == GuardState.Combat)
            {
                ShowStatus("没时间聊天！专心战斗！");
                return;
            }

            // 发送对话
            var response = await npcSoul.Chat(message, player?.name ?? "player_001");

            if (response != null && response.success)
            {
                ShowStatus(response.content);

                // 如果玩家表现好，增加信任
                if (response.ShouldShareInfo())
                {
                    trustBonus += 0.1f;
                    StartCoroutine(ShareGuardSecretAfterDelay(2f));
                }
            }
        }

        /// <summary>
        /// 玩家帮助守卫
        /// </summary>
        public void OnPlayerHelped(string helpType)
        {
            if (npcSoul == null || !npcSoul.IsConnected) return;

            Debug.Log($"[{npcName}] 玩家帮助: {helpType}");

            ShowStatus($"多亏了你！职责得以履行。`r`n感谢你的协助！");

            // 发送帮助事件
            _ = SendEventAsync(GameEventType.npc_helped, 0.7f, new Dictionary<string, object>
            {
                { "help_type", helpType }
            });

            trustBonus += 0.15f;
        }

        #endregion

        #region 辅助方法

        /// <summary>
        /// 发送事件
        /// </summary>
        private async System.Threading.Tasks.Task SendEventAsync(
            GameEventType eventType, 
            float intensity, 
            Dictionary<string, object> context)
        {
            if (npcSoul == null) return;
            await npcSoul.SendEvent(eventType, intensity, context);
        }

        /// <summary>
        /// 显示状态文本
        /// </summary>
        private void ShowStatus(string text)
        {
            if (statusText != null)
            {
                statusText.text = $"[{npcName}] {text}";

                // 重置颜色
                statusText.color = Color.white;
            }
            else
            {
                Debug.Log($"[{npcName}]: {text}");
            }
        }

        /// <summary>
        /// 延迟解锁新对话
        /// </summary>
        private IEnumerator UnlockNewDialogueAfterDelay(float delay)
        {
            yield return new WaitForSeconds(delay);

            if (npcSoul != null && npcSoul.IsHappy())
            {
                ShowStatus("既然你这么可靠...告诉你一个秘密。`r`n夜间巡逻时，小心城墙东侧的阴影...");
            }
        }

        /// <summary>
        /// 延迟分享守卫秘密
        /// </summary>
        private IEnumerator ShareGuardSecretAfterDelay(float delay)
        {
            yield return new WaitForSeconds(delay);

            if (trustBonus > 0.2f)
            {
                ShowStatus("你是可以信赖的伙伴。`r`n据说每月的满月之夜，地下金库会有异动...");
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

            // 根据恐惧情绪调整警戒等级
            if (newEmotion != null && newEmotion.Fear > 0.5f)
            {
                alertLevel = Mathf.Max(alertLevel, 0.7f);
                if (currentState == GuardState.Idle)
                {
                    SetState(GuardState.Alert);
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
                        Debug.Log($"[{npcName}] 对话风格变为: {behavior.value}");
                        
                        // 根据对话风格调整行为
                        if (behavior.value == "hostile")
                        {
                            // 更严格的检查
                            alertThreshold = Mathf.Max(0.3f, alertThreshold - 0.2f);
                        }
                    }

                    if (behavior.IsQuestAvailabilityChange())
                    {
                        if (behavior.IsQuestUnlocked())
                        {
                            ShowStatus("新任务已解锁。前往市政厅了解详情。");
                            isOnMission = false;
                        }
                    }
                }
            }
        }

        /// <summary>
        /// 连接状态变化回调
        /// </summary>
        private void OnConnectionStateChanged(bool connected)
        {
            Debug.Log($"[{npcName}] 连接状态: {(connected ? "已连接" : "已断开")}");
        }

        #endregion

        #region 公共属性

        /// <summary>
        /// 获取当前警戒等级
        /// </summary>
        public float AlertLevel => alertLevel;

        /// <summary>
        /// 获取当前状态
        /// </summary>
        public GuardState CurrentGuardState => currentState;

        /// <summary>
        /// 获取检测到的敌人数量
        /// </summary>
        public int EnemyCount => detectedEnemies.Count;

        /// <summary>
        /// 是否处于战斗状态
        /// </summary>
        public bool IsInCombat => currentState == GuardState.Combat;

        /// <summary>
        /// 是否正在执行任务
        /// </summary>
        public bool IsOnMission => isOnMission;

        /// <summary>
        /// 获取信任加成
        /// </summary>
        public float TrustBonus => trustBonus;

        #endregion
    }
}
