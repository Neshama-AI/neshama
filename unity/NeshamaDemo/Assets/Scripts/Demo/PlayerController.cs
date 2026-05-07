using System;
using UnityEngine;
using Neshama.SDK;
using Neshama.SDK.Models;
using Neshama.SDK.Enums;

namespace Neshama.Demo
{
    /// <summary>
    /// 玩家控制器 - 处理玩家移动和交互
    /// 
    /// 功能：
    /// - WASD移动 + 鼠标旋转
    /// - 靠近NPC时显示交互提示
    /// - 按E打开对话面板
    /// - Shift+1~8快捷发送事件
    /// </summary>
    public class PlayerController : MonoBehaviour
    {
        #region 移动配置

        [Header("=== 移动配置 ===")]
        [Tooltip("移动速度 (单位/秒)")]
        [SerializeField] private float moveSpeed = 5f;

        [Tooltip("旋转速度")]
        [SerializeField] private float rotationSpeed = 10f;

        [Tooltip("奔跑速度倍率")]
        [SerializeField] private float runSpeedMultiplier = 2f;

        [Header("=== 交互配置 ===")]
        [Tooltip("可交互距离")]
        [SerializeField] private float interactionDistance = 3f;

        [Tooltip("交互提示显示距离")]
        [SerializeField] private float hintDisplayDistance = 4f;

        [Header("=== 相机配置 ===")]
        [Tooltip("第三人称相机")]
        [SerializeField] private Camera thirdPersonCamera;

        [Tooltip("相机跟随距离")]
        [SerializeField] private float cameraDistance = 5f;

        [Tooltip("相机高度")]
        [SerializeField] private float cameraHeight = 2f;

        #endregion

        #region 私有变量

        // 组件引用
        private CharacterController _characterController;
        private Rigidbody _rigidbody;

        // 移动状态
        private Vector3 _moveDirection;
        private Vector3 _currentVelocity;
        private bool _isRunning;
        private bool _canMove = true;

        // 交互状态
        private NPCSoul _currentTargetNPC;
        private bool _isInteracting;

        // UI引用
        private DemoUIManager _uiManager;

        // 交互冷却
        private float _lastInteractionTime = -1f;
        private float _interactionCooldown = 0.5f;

        #endregion

        #region Unity生命周期

        /// <summary>
        /// 初始化
        /// </summary>
        private void Start()
        {
            // 获取组件
            _characterController = GetComponent<CharacterController>();
            _rigidbody = GetComponent<Rigidbody>();

            // 如果没有CharacterController，添加一个
            if (_characterController == null)
            {
                _characterController = gameObject.AddComponent<CharacterController>();
                _characterController.height = 2f;
                _characterController.radius = 0.3f;
                _characterController.center = new Vector3(0, 1f, 0);
            }

            // 锁定鼠标
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;

            // 获取UI管理器
            _uiManager = DemoUIManager.Instance;

            // 等待场景管理器初始化
            if (DemoSceneManager.Instance != null)
            {
                DemoSceneManager.Instance.OnInitializationComplete += OnSceneReady;
            }

            Debug.Log("[PlayerController] 玩家控制器初始化完成");
        }

        /// <summary>
        /// 每帧更新
        /// </summary>
        private void Update()
        {
            if (!_canMove && !_isInteracting) return;

            // 处理输入
            HandleInput();

            // 更新交互状态
            UpdateInteraction();
        }

        /// <summary>
        /// 物理更新
        /// </summary>
        private void FixedUpdate()
        {
            if (!_canMove) return;

            // 应用移动
            ApplyMovement();
        }

        /// <summary>
        /// 销毁时清理
        /// </summary>
        private void OnDestroy()
        {
            // 恢复鼠标状态
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        #endregion

        #region 输入处理

        /// <summary>
        /// 处理输入
        /// </summary>
        private void HandleInput()
        {
            // 鼠标旋转
            HandleMouseRotation();

            // WASD移动
            float horizontal = Input.GetAxisRaw("Horizontal");
            float vertical = Input.GetAxisRaw("Vertical");
            _moveDirection = new Vector3(horizontal, 0, vertical).normalized;

            // 奔跑
            _isRunning = Input.GetKey(KeyCode.LeftShift);

            // 交互输入
            if (Input.GetKeyDown(KeyCode.E) && CanInteract())
            {
                StartInteraction();
            }

            // 取消交互
            if (Input.GetKeyDown(KeyCode.Escape) && _isInteracting)
            {
                EndInteraction();
            }

            // 快捷事件（Shift + 数字键）
            HandleQuickEvents();
        }

        /// <summary>
        /// 处理鼠标旋转
        /// </summary>
        private void HandleMouseRotation()
        {
            if (_isInteracting) return;

            float mouseX = Input.GetAxis("Mouse X") * rotationSpeed * Time.deltaTime;
            transform.Rotate(Vector3.up, mouseX);
        }

        /// <summary>
        /// 处理快捷事件
        /// </summary>
        private void HandleQuickEvents()
        {
            if (!Input.GetKey(KeyCode.LeftShift)) return;

            // Shift + 1: 送礼
            if (Input.GetKeyDown(KeyCode.Alpha1))
            {
                SendEventToTarget(GameEventType.gift_given, 0.8f);
                ShowHint("送出礼物");
            }
            // Shift + 2: 攻击
            else if (Input.GetKeyDown(KeyCode.Alpha2))
            {
                SendEventToTarget(GameEventType.player_attacked, 1.0f);
                ShowHint("攻击了NPC！");
            }
            // Shift + 3: 帮助
            else if (Input.GetKeyDown(KeyCode.Alpha3))
            {
                SendEventToTarget(GameEventType.npc_helped, 0.7f);
                ShowHint("帮助了NPC");
            }
            // Shift + 4: 赞美
            else if (Input.GetKeyDown(KeyCode.Alpha4))
            {
                SendEventToTarget(GameEventType.npc_complimented, 0.6f);
                ShowHint("赞美了NPC");
            }
            // Shift + 5: 侮辱
            else if (Input.GetKeyDown(KeyCode.Alpha5))
            {
                SendEventToTarget(GameEventType.npc_insulted, 0.8f);
                ShowHint("侮辱了NPC");
            }
            // Shift + 6: 交易
            else if (Input.GetKeyDown(KeyCode.Alpha6))
            {
                SendEventToTarget(GameEventType.trade_completed, 0.5f);
                ShowHint("完成交易");
            }
            // Shift + 7: 接受任务
            else if (Input.GetKeyDown(KeyCode.Alpha7))
            {
                SendEventToTarget(GameEventType.quest_accepted, 0.6f);
                ShowHint("接受了任务");
            }
            // Shift + 8: 完成任务
            else if (Input.GetKeyDown(KeyCode.Alpha8))
            {
                SendEventToTarget(GameEventType.quest_completed, 0.9f);
                ShowHint("完成了任务");
            }
        }

        /// <summary>
        /// 发送事件给目标NPC
        /// </summary>
        private void SendEventToTarget(GameEventType eventType, float intensity)
        {
            if (_currentTargetNPC != null)
            {
                _currentTargetNPC.SendEvent(eventType, intensity);
            }
            else
            {
                // 向所有NPC发送事件
                DemoSceneManager.Instance.SendGlobalEvent(eventType, intensity);
            }
        }

        #endregion

        #region 移动控制

        /// <summary>
        /// 应用移动
        /// </summary>
        private void ApplyMovement()
        {
            if (_moveDirection.magnitude < 0.1f) return;
            if (_isInteracting) return;

            // 计算目标速度
            float speed = moveSpeed * (_isRunning ? runSpeedMultiplier : 1f);
            Vector3 targetVelocity = transform.TransformDirection(_moveDirection) * speed;

            // 平滑移动
            _currentVelocity = Vector3.Lerp(_currentVelocity, targetVelocity, Time.fixedDeltaTime * 10f);

            // 应用移动
            Vector3 move = _currentVelocity * Time.fixedDeltaTime;
            if (_characterController != null)
            {
                _characterController.Move(move);
            }
            else
            {
                transform.position += move;
            }

            // 地面检测
            if (_characterController != null && !_characterController.isGrounded)
            {
                _characterController.Move(Vector3.down * 9.8f * Time.fixedDeltaTime);
            }
        }

        #endregion

        #region 交互系统

        /// <summary>
        /// 更新交互状态
        /// </summary>
        private void UpdateInteraction()
        {
            // 查找最近的NPC
            NPCSoul nearestNPC = FindNearestNPC();

            // 更新当前目标
            if (nearestNPC != null && nearestNPC != _currentTargetNPC)
            {
                _currentTargetNPC = nearestNPC;
            }

            // 显示/隐藏交互提示
            UpdateInteractionHint();
        }

        /// <summary>
        /// 查找最近的NPC
        /// </summary>
        private NPCSoul FindNearestNPC()
        {
            NPCSoul nearest = null;
            float nearestDistance = hintDisplayDistance;

            foreach (var npc in DemoSceneManager.Instance.GetAllNPCs())
            {
                float distance = Vector3.Distance(transform.position, npc.transform.position);
                if (distance < nearestDistance)
                {
                    nearestDistance = distance;
                    nearest = npc;
                }
            }

            return nearest;
        }

        /// <summary>
        /// 更新交互提示UI
        /// </summary>
        private void UpdateInteractionHint()
        {
            if (_uiManager == null) return;

            if (_currentTargetNPC != null && !_isInteracting)
            {
                float distance = Vector3.Distance(transform.position, _currentTargetNPC.transform.position);
                if (distance <= hintDisplayDistance)
                {
                    _uiManager.ShowInteractionHint(_currentTargetNPC.NpcName);
                }
                else
                {
                    _uiManager.HideInteractionHint();
                }
            }
            else
            {
                _uiManager.HideInteractionHint();
            }
        }

        /// <summary>
        /// 是否可以交互
        /// </summary>
        private bool CanInteract()
        {
            if (_isInteracting) return false;
            if (Time.time - _lastInteractionTime < _interactionCooldown) return false;
            if (_currentTargetNPC == null) return false;

            float distance = Vector3.Distance(transform.position, _currentTargetNPC.transform.position);
            return distance <= interactionDistance;
        }

        /// <summary>
        /// 开始交互
        /// </summary>
        private void StartInteraction()
        {
            if (_currentTargetNPC == null) return;

            _isInteracting = true;
            _canMove = false;
            _lastInteractionTime = Time.time;

            // 停止移动
            _currentVelocity = Vector3.zero;
            _moveDirection = Vector3.zero;

            // 面向NPC
            Vector3 direction = (_currentTargetNPC.transform.position - transform.position).normalized;
            direction.y = 0;
            if (direction.sqrMagnitude > 0.01f)
            {
                transform.rotation = Quaternion.LookRotation(direction);
            }

            // 打开对话面板
            _uiManager.ShowDialoguePanel(_currentTargetNPC);

            Debug.Log($"[PlayerController] 开始与 {_currentTargetNPC.NpcName} 交互");
        }

        /// <summary>
        /// 结束交互
        /// </summary>
        public void EndInteraction()
        {
            _isInteracting = false;
            _canMove = true;

            // 关闭对话面板
            _uiManager?.HideDialoguePanel();

            Debug.Log("[PlayerController] 结束交互");
        }

        /// <summary>
        /// 显示提示信息
        /// </summary>
        private void ShowHint(string message)
        {
            _uiManager?.ShowNotification(message);
        }

        #endregion

        #region 公共方法

        /// <summary>
        /// 场景就绪回调
        /// </summary>
        private void OnSceneReady()
        {
            Debug.Log("[PlayerController] 场景已就绪，等待玩家输入...");
        }

        /// <summary>
        /// 设置是否可以移动
        /// </summary>
        public void SetCanMove(bool canMove)
        {
            _canMove = canMove;
            if (!canMove)
            {
                _currentVelocity = Vector3.zero;
                _moveDirection = Vector3.zero;
            }
        }

        /// <summary>
        /// 获取当前目标NPC
        /// </summary>
        public NPCSoul GetCurrentTarget()
        {
            return _currentTargetNPC;
        }

        /// <summary>
        /// 是否正在交互
        /// </summary>
        public bool IsInteracting()
        {
            return _isInteracting;
        }

        /// <summary>
        /// 获取玩家位置
        /// </summary>
        public Vector3 GetPosition()
        {
            return transform.position;
        }

        #endregion

        #region 调试

        /// <summary>
        /// 绘制Gizmos
        /// </summary>
        private void OnDrawGizmosSelected()
        {
            // 绘制交互范围
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position, interactionDistance);

            // 绘制提示范围
            Gizmos.color = Color.cyan;
            Gizmos.DrawWireSphere(transform.position, hintDisplayDistance);
        }

        #endregion
    }
}
