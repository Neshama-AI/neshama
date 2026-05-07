using System;
using System.Collections.Generic;
using UnityEngine;
using Neshama.SDK;
using Neshama.SDK.Models;
using Neshama.SDK.Enums;

namespace Neshama.Demo
{
    /// <summary>
    /// 交互系统 - 负责玩家与NPC之间的交互检测和处理
    /// 
    /// 功能：
    /// - 碰撞体检测（玩家靠近NPC 3米内可交互）
    /// - 多种交互类型（E对话、Q送礼、R攻击、F夸赞）
    /// - NPC面朝玩家
    /// - 对话中玩家不能移动
    /// </summary>
    public class InteractionSystem : MonoBehaviour
    {
        #region 交互配置

        [Header("=== 交互配置 ===")]
        [Tooltip("可交互距离（米）")]
        [SerializeField] private float interactionRange = 3f;

        [Tooltip("交互冷却时间（秒）")]
        [SerializeField] private float interactionCooldown = 0.5f;

        [Header("=== 交互提示配置 ===")]
        [Tooltip("交互提示UI预制件")]
        [SerializeField] private GameObject interactionHintPrefab;

        [Tooltip("提示显示在NPC上方的高度")]
        [SerializeField] private float hintHeight = 2.5f;

        #endregion

        #region 私有变量

        // 玩家引用
        private PlayerController _playerController;

        // UI管理器
        private DemoUIManager _uiManager;

        // 交互状态
        private NPCSoul _currentNPC;
        private bool _canInteract = true;
        private float _lastInteractionTime;

        // 交互提示UI实例
        private GameObject _hintInstance;

        // 可交互NPC列表
        private List<NPCSoul> _interactableNPCs = new List<NPCSoul>();

        // 交互提示文本
        private TMPro.TextMeshPro _hintText;

        #endregion

        #region Unity生命周期

        /// <summary>
        /// 初始化
        /// </summary>
        private void Start()
        {
            _playerController = GetComponent<PlayerController>();
            _uiManager = DemoUIManager.Instance;

            Debug.Log("[InteractionSystem] 交互系统初始化完成");
        }

        /// <summary>
        /// 每帧更新
        /// </summary>
        private void Update()
        {
            // 检查交互冷却
            UpdateCooldown();

            // 检测可交互NPC
            DetectInteractableNPCs();

            // 处理交互输入
            HandleInteractionInput();

            // 更新交互提示
            UpdateInteractionHint();
        }

        #endregion

        #region NPC检测

        /// <summary>
        /// 检测场景中可交互的NPC
        /// </summary>
        private void DetectInteractableNPCs()
        {
            _interactableNPCs.Clear();

            foreach (var npc in DemoSceneManager.Instance.GetAllNPCs())
            {
                if (npc == null) continue;

                float distance = Vector3.Distance(transform.position, npc.transform.position);
                if (distance <= interactionRange)
                {
                    _interactableNPCs.Add(npc);
                }
            }

            // 更新当前最近的NPC
            if (_interactableNPCs.Count > 0)
            {
                _currentNPC = FindNearestNPC();
            }
            else
            {
                _currentNPC = null;
            }
        }

        /// <summary>
        /// 查找最近的NPC
        /// </summary>
        private NPCSoul FindNearestNPC()
        {
            NPCSoul nearest = null;
            float nearestDistance = float.MaxValue;

            foreach (var npc in _interactableNPCs)
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

        #endregion

        #region 交互处理

        /// <summary>
        /// 处理交互输入
        /// </summary>
        private void HandleInteractionInput()
        {
            if (_playerController != null && _playerController.IsInteracting()) return;
            if (!_canInteract) return;
            if (_currentNPC == null) return;

            // E键 - 对话
            if (Input.GetKeyDown(KeyCode.E))
            {
                StartDialogue();
            }

            // Q键 - 送礼
            else if (Input.GetKeyDown(KeyCode.Q))
            {
                GiveGift();
            }

            // R键 - 攻击
            else if (Input.GetKeyDown(KeyCode.R))
            {
                AttackNPC();
            }

            // F键 - 夸赞
            else if (Input.GetKeyDown(KeyCode.F))
            {
                ComplimentNPC();
            }
        }

        /// <summary>
        /// 开始对话
        /// </summary>
        private void StartDialogue()
        {
            if (_currentNPC == null) return;

            // 通知玩家控制器开始交互
            _playerController?.SetCanMove(false);

            // 让NPC面向玩家
            FacePlayer(_currentNPC);

            // 打开对话面板
            _uiManager?.ShowDialoguePanel(_currentNPC);

            // 发送进入事件
            _currentNPC.SendEvent(GameEventType.player_entered, 0.3f);

            // 触发冷却
            TriggerCooldown();

            Debug.Log($"[InteractionSystem] 开始与 {_currentNPC.NpcName} 对话");
        }

        /// <summary>
        /// 送礼
        /// </summary>
        private void GiveGift()
        {
            if (_currentNPC == null) return;

            // 发送送礼事件
            _currentNPC.SendEvent(GameEventType.gift_given, 0.8f);

            // 显示提示
            _uiManager?.ShowNotification($"向 {_currentNPC.NpcName} 送出了一份礼物");

            // 触发冷却
            TriggerCooldown();

            Debug.Log($"[InteractionSystem] 向 {_currentNPC.NpcName} 送礼");
        }

        /// <summary>
        /// 攻击NPC
        /// </summary>
        private void AttackNPC()
        {
            if (_currentNPC == null) return;

            // 发送攻击事件（情绪立即变化）
            _currentNPC.SendEvent(GameEventType.player_attacked, 1.0f);

            // 显示警告提示
            _uiManager?.ShowNotification($"你攻击了 {_currentNPC.NpcName}！", DemoUIManager.NotificationType.Warning);

            // NPC面向玩家（愤怒时）
            FacePlayer(_currentNPC);

            // 触发冷却
            TriggerCooldown();

            Debug.Log($"[InteractionSystem] 攻击了 {_currentNPC.NpcName}");
        }

        /// <summary>
        /// 夸赞NPC
        /// </summary>
        private void ComplimentNPC()
        {
            if (_currentNPC == null) return;

            // 发送夸赞事件
            _currentNPC.SendEvent(GameEventType.npc_complimented, 0.6f);

            // 显示提示
            _uiManager?.ShowNotification($"你夸赞了 {_currentNPC.NpcName}");

            // NPC面向玩家
            FacePlayer(_currentNPC);

            // 触发冷却
            TriggerCooldown();

            Debug.Log($"[InteractionSystem] 夸赞了 {_currentNPC.NpcName}");
        }

        /// <summary>
        /// 让NPC面朝玩家
        /// </summary>
        private void FacePlayer(NPCSoul npc)
        {
            if (npc == null) return;

            Vector3 direction = (transform.position - npc.transform.position).normalized;
            direction.y = 0;

            if (direction.sqrMagnitude > 0.01f)
            {
                npc.transform.rotation = Quaternion.LookRotation(direction);
            }
        }

        #endregion

        #region 冷却系统

        /// <summary>
        /// 更新冷却
        /// </summary>
        private void UpdateCooldown()
        {
            if (_canInteract) return;

            if (Time.time - _lastInteractionTime >= interactionCooldown)
            {
                _canInteract = true;
            }
        }

        /// <summary>
        /// 触发冷却
        /// </summary>
        private void TriggerCooldown()
        {
            _canInteract = false;
            _lastInteractionTime = Time.time;
        }

        #endregion

        #region 交互提示

        /// <summary>
        /// 更新交互提示UI
        /// </summary>
        private void UpdateInteractionHint()
        {
            if (_currentNPC == null)
            {
                HideHint();
                return;
            }

            ShowHint();
        }

        /// <summary>
        /// 显示提示
        /// </summary>
        private void ShowHint()
        {
            // 创建提示UI（如果不存在）
            if (_hintInstance == null)
            {
                CreateHintUI();
            }

            // 更新位置到NPC头顶
            if (_currentNPC != null && _hintInstance != null)
            {
                Vector3 hintPos = _currentNPC.transform.position + Vector3.up * hintHeight;
                _hintInstance.transform.position = hintPos;

                // 使提示始终面向相机
                _hintInstance.transform.LookAt(Camera.main.transform);
                _hintInstance.transform.Rotate(0, 180f, 0);

                // 显示提示
                _hintInstance.SetActive(true);

                // 更新提示文本
                UpdateHintText();
            }
        }

        /// <summary>
        /// 隐藏提示
        /// </summary>
        private void HideHint()
        {
            if (_hintInstance != null)
            {
                _hintInstance.SetActive(false);
            }
        }

        /// <summary>
        /// 创建提示UI
        /// </summary>
        private void CreateHintUI()
        {
            // 使用Unity UI Canvas创建提示
            var canvas = FindObjectOfType<Canvas>();
            if (canvas == null)
            {
                var canvasObj = new GameObject("InteractionCanvas");
                canvas = canvasObj.AddComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                canvasObj.AddComponent<UnityEngine.UI.CanvasScaler>();
                canvasObj.AddComponent<UnityEngine.UI.GraphicRaycaster>();
            }

            // 创建提示背景
            _hintInstance = new GameObject("InteractionHint");
            _hintInstance.transform.SetParent(canvas.transform);
            _hintInstance.SetActive(false);

            // 添加CanvasGroup用于透明度控制
            var canvasGroup = _hintInstance.AddComponent<UnityEngine.UI.CanvasGroup>();
            canvasGroup.alpha = 0.9f;

            // 添加背景图片
            var image = _hintInstance.AddComponent<UnityEngine.UI.Image>();
            image.color = new Color(0, 0, 0, 0.7f);

            // 添加布局组件
            var layout = _hintInstance.AddComponent<UnityEngine.UI.VerticalLayoutGroup>();
            layout.padding = new RectOffset(10, 10, 5, 5);
            layout.spacing = 5;

            // 设置位置
            var rect = _hintInstance.GetComponent<RectTransform>();
            rect.sizeDelta = new Vector2(200, 80);
            rect.anchoredPosition = new Vector2(0, 100);

            // 添加文本
            var textObj = new GameObject("HintText");
            textObj.transform.SetParent(_hintInstance.transform);
            _hintText = textObj.AddComponent<TMPro.TextMeshPro>();
            _hintText.text = "[E] 对话  [Q] 送礼\n[R] 攻击  [F] 夸赞";
            _hintText.fontSize = 14;
            _hintText.alignment = TMPro.TextAlignmentOptions.Center;
            _hintText.color = Color.white;

            var textRect = textObj.GetComponent<RectTransform>();
            textRect.sizeDelta = new Vector2(180, 60);
        }

        /// <summary>
        /// 更新提示文本
        /// </summary>
        private void UpdateHintText()
        {
            if (_hintText == null || _currentNPC == null) return;

            // 根据当前情绪状态调整提示
            var emotion = _currentNPC.CurrentEmotion;
            string emotionEmoji = GetEmotionEmoji(emotion?.dominant);

            _hintText.text = $"{_currentNPC.NpcName} {emotionEmoji}\n[E] 对话  [Q] 送礼\n[R] 攻击  [F] 夸赞";
        }

        /// <summary>
        /// 获取情绪对应的emoji
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

        #region 公共方法

        /// <summary>
        /// 获取当前可交互的NPC
        /// </summary>
        public NPCSoul GetCurrentNPC()
        {
            return _currentNPC;
        }

        /// <summary>
        /// 是否在交互范围内
        /// </summary>
        public bool IsInRange(NPCSoul npc)
        {
            if (npc == null) return false;
            return Vector3.Distance(transform.position, npc.transform.position) <= interactionRange;
        }

        /// <summary>
        /// 获取交互范围内的NPC列表
        /// </summary>
        public List<NPCSoul> GetInteractableNPCs()
        {
            return new List<NPCSoul>(_interactableNPCs);
        }

        #endregion

        #region 调试

        /// <summary>
        /// 绘制Gizmos
        /// </summary>
        private void OnDrawGizmos()
        {
            // 绘制交互范围
            Gizmos.color = _currentNPC != null ? Color.green : Color.yellow;
            Gizmos.DrawWireSphere(transform.position, interactionRange);

            // 绘制到当前NPC的连线
            if (_currentNPC != null)
            {
                Gizmos.color = Color.cyan;
                Gizmos.DrawLine(transform.position, _currentNPC.transform.position);
            }
        }

        #endregion
    }
}
