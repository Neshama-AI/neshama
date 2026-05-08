#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;
using Neshama.SDK;
using Neshama.SDK.Models;
using Neshama.SDK.Enums;
using System.Collections.Generic;

namespace Neshama.SDK.Editor
{
    /// <summary>
    /// NPCSoul组件的自定义Inspector编辑器
    /// 提供可视化情绪状态显示、行为建议和测试功能
    /// </summary>
    [CustomEditor(typeof(NPCSoul))]
    public class NPCSoulEditor : UnityEditor.Editor
    {
        // NPCSoul实例
        private NPCSoul _npcSoul;

        // 折叠状态
        private bool _showIdentity = true;
        private bool _showConnection = true;
        private bool _showEmotion = true;
        private bool _showBehaviors = true;
        private bool _showDebug = true;

        // 测试输入
        private string _testMessage = "";
        private string _testPlayerId = "player_001";
        private GameEventType _testEventType = GameEventType.player_entered;
        private float _testIntensity = 0.5f;

        // 颜色
        private readonly Color _joyColor = new Color(0.2f, 0.8f, 0.2f);
        private readonly Color _angerColor = new Color(0.8f, 0.2f, 0.2f);
        private readonly Color _fearColor = new Color(0.6f, 0.4f, 0.8f);
        private readonly Color _sadnessColor = new Color(0.3f, 0.5f, 0.8f);
        private readonly Color _neutralColor = new Color(0.7f, 0.7f, 0.7f);

        /// <summary>
        /// 启用时获取目标
        /// </summary>
        private void OnEnable()
        {
            _npcSoul = (NPCSoul)target;
        }

        /// <summary>
        /// 绘制自定义Inspector
        /// </summary>
        public override void OnInspectorGUI()
        {
            // 绘制默认Inspector（会包含所有SerializeField）
            DrawDefaultInspector();

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("═══════════════════════════════════", EditorStyles.boldLabel);
            EditorGUILayout.LabelField("Neshama Soul - Runtime Status", EditorStyles.boldLabel);
            EditorGUILayout.LabelField("═══════════════════════════════════", EditorStyles.boldLabel);

            if (!Application.isPlaying)
            {
                EditorGUILayout.HelpBox("Runtime information will be displayed when playing.", MessageType.Info);
                return;
            }

            // 连接状态
            DrawConnectionStatus();

            // 情绪状态
            DrawEmotionStatus();

            // 行为建议
            DrawBehaviorHints();

            // 测试工具
            DrawTestTools();

            // 刷新按钮
            EditorGUILayout.Space();
            if (GUILayout.Button("Refresh State", GUILayout.Height(25)))
            {
                RefreshState();
            }

            // 强制重绘
            if (GUI.changed)
            {
                EditorUtility.SetDirty(target);
            }
        }

        /// <summary>
        /// 绘制连接状态
        /// </summary>
        private void DrawConnectionStatus()
        {
            _showConnection = EditorGUILayout.Foldout(_showConnection, "Connection Status", true);

            if (!_showConnection) return;

            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            // 连接状态指示
            var style = new GUIStyle(EditorStyles.label) { alignment = TextAnchor.MiddleCenter };
            var statusColor = _npcSoul.IsConnected ? Color.green : Color.red;
            var statusText = _npcSoul.IsConnected ? "● CONNECTED" : "○ DISCONNECTED";

            var oldColor = GUI.contentColor;
            GUI.contentColor = statusColor;
            EditorGUILayout.LabelField(statusText, style);
            GUI.contentColor = oldColor;

            EditorGUILayout.LabelField($"NPC ID: {_npcSoul.NpcId}");
            EditorGUILayout.LabelField($"Preset: {_npcSoul.Preset}");
            EditorGUILayout.LabelField($"Running Time: {_npcSoul.RunningTime:F1}s");

            EditorGUILayout.BeginHorizontal();

            if (GUILayout.Button(_npcSoul.IsConnected ? "Disconnect" : "Connect"))
            {
                if (_npcSoul.IsConnected)
                {
                    _npcSoul.Disconnect();
                }
                else
                {
                    _ = _npcSoul.Connect();
                }
            }

            EditorGUILayout.EndHorizontal();

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 绘制情绪状态
        /// </summary>
        private void DrawEmotionStatus()
        {
            _showEmotion = EditorGUILayout.Foldout(_showEmotion, "Emotion State", true);

            if (!_showEmotion) return;

            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            var emotion = _npcSoul.CurrentEmotion;

            if (emotion == null)
            {
                EditorGUILayout.HelpBox("No emotion data available.", MessageType.Info);
                EditorGUILayout.EndVertical();
                return;
            }

            // 主导情绪
            EditorGUILayout.LabelField("Dominant Emotion", EditorStyles.boldLabel);
            
            var emotionType = emotion.GetDominantEmotionType();
            var emotionColor = GetEmotionColor(emotionType);
            
            var oldColor = GUI.contentColor;
            GUI.contentColor = emotionColor;
            EditorGUILayout.LabelField($"  {emotion.dominant?.ToUpper() ?? "NONE"}", EditorStyles.boldLabel);
            GUI.contentColor = oldColor;

            EditorGUILayout.LabelField($"Composite: {emotion.composite ?? "N/A"}");

            EditorGUILayout.Space();

            // 情绪条
            EditorGUILayout.LabelField("Emotion Bars", EditorStyles.boldLabel);

            DrawEmotionBar("Joy (喜悦)", emotion.Joy, _joyColor);
            DrawEmotionBar("Anger (愤怒)", emotion.Anger, _angerColor);
            DrawEmotionBar("Fear (恐惧)", emotion.Fear, _fearColor);
            DrawEmotionBar("Sadness (悲伤)", emotion.Sadness, _sadnessColor);
            DrawEmotionBar("Trust (信任)", emotion.Trust, _joyColor);
            DrawEmotionBar("Surprise (惊讶)", emotion.Surprise, _fearColor);
            DrawEmotionBar("Disgust (厌恶)", emotion.Disgust, _angerColor);
            DrawEmotionBar("Anticipation (期待)", emotion.Anticipation, _joyColor);
            DrawEmotionBar("Shame (羞愧)", emotion.Shame, _sadnessColor);

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 绘制情绪条
        /// </summary>
        private void DrawEmotionBar(string label, float value, Color color)
        {
            EditorGUILayout.BeginHorizontal();
            
            EditorGUILayout.LabelField(label, GUILayout.Width(120));
            
            // 背景条
            var rect = GUILayoutUtility.GetRect(0, 16, GUILayout.ExpandWidth(true));
            EditorGUI.DrawRect(rect, _neutralColor * 0.5f);
            
            // 填充条
            var fillRect = new Rect(rect.x, rect.y, rect.width * value, rect.height);
            EditorGUI.DrawRect(fillRect, color);
            
            // 数值
            EditorGUILayout.LabelField($"{value:F2}", GUILayout.Width(40));
            
            EditorGUILayout.EndHorizontal();
        }

        /// <summary>
        /// 获取情绪对应的颜色
        /// </summary>
        private Color GetEmotionColor(Enums.EmotionType emotionType)
        {
            switch (emotionType)
            {
                case Enums.EmotionType.Joy:
                    return _joyColor;
                case Enums.EmotionType.Anger:
                case Enums.EmotionType.Disgust:
                    return _angerColor;
                case Enums.EmotionType.Fear:
                case Enums.EmotionType.Surprise:
                    return _fearColor;
                case Enums.EmotionType.Sadness:
                case Enums.EmotionType.Shame:
                    return _sadnessColor;
                default:
                    return _neutralColor;
            }
        }

        /// <summary>
        /// 绘制行为建议
        /// </summary>
        private void DrawBehaviorHints()
        {
            _showBehaviors = EditorGUILayout.Foldout(_showBehaviors, "Behavior Hints", true);

            if (!_showBehaviors) return;

            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            var behaviors = _npcSoul.CurrentBehaviors;

            if (behaviors == null || behaviors.Count == 0)
            {
                EditorGUILayout.HelpBox("No behavior modifiers active.", MessageType.Info);
                EditorGUILayout.EndVertical();
                return;
            }

            EditorGUILayout.LabelField($"Active Modifiers ({behaviors.Count})", EditorStyles.boldLabel);

            foreach (var behavior in behaviors)
            {
                EditorGUILayout.BeginVertical("HelpBox");
                
                EditorGUILayout.LabelField($"Type: {behavior.type}", EditorStyles.boldLabel);
                EditorGUILayout.LabelField($"Value: {behavior.value}");
                
                if (behavior.strength > 0)
                {
                    EditorGUILayout.LabelField($"Strength: {behavior.strength:F2}");
                }
                
                if (behavior.suggested_actions != null && behavior.suggested_actions.Count > 0)
                {
                    EditorGUILayout.LabelField("Suggested Actions:");
                    foreach (var action in behavior.suggested_actions)
                    {
                        EditorGUILayout.LabelField($"  - {action}");
                    }
                }
                
                EditorGUILayout.EndVertical();
                EditorGUILayout.Space(2);
            }

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 绘制测试工具
        /// </summary>
        private void DrawTestTools()
        {
            _showDebug = EditorGUILayout.Foldout(_showDebug, "Test Tools", true);

            if (!_showDebug) return;

            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            // 发送事件测试
            EditorGUILayout.LabelField("Test Game Event", EditorStyles.boldLabel);

            _testEventType = (GameEventType)EditorGUILayout.EnumPopup("Event Type", _testEventType);
            _testIntensity = EditorGUILayout.Slider("Intensity", _testIntensity, 0f, 1f);

            if (GUILayout.Button("Send Event"))
            {
                SendTestEvent();
            }

            EditorGUILayout.Space();

            // 对话测试
            EditorGUILayout.LabelField("Test Chat", EditorStyles.boldLabel);

            _testMessage = EditorGUILayout.TextField("Message", _testMessage);
            _testPlayerId = EditorGUILayout.TextField("Player ID", _testPlayerId);

            GUI.enabled = !string.IsNullOrEmpty(_testMessage);
            if (GUILayout.Button("Send Chat"))
            {
                SendTestChat();
            }
            GUI.enabled = true;

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 刷新状态
        /// </summary>
        private async void RefreshState()
        {
            if (!_npcSoul.IsConnected) return;

            await _npcSoul.GetCurrentEmotion();
            await _npcSoul.GetBehaviorHints();

            Repaint();
        }

        /// <summary>
        /// 发送测试事件
        /// </summary>
        private async void SendTestEvent()
        {
            if (!_npcSoul.IsConnected)
            {
                Debug.LogWarning("Not connected to server");
                return;
            }

            Debug.Log($"[Test] Sending event: {_testEventType} with intensity {_testIntensity}");
            var response = await _npcSoul.SendEvent(_testEventType, _testIntensity);

            if (response != null)
            {
                Debug.Log($"[Test] Event response: {response.emotion_state?.dominant}");
            }

            Repaint();
        }

        /// <summary>
        /// 发送测试对话
        /// </summary>
        private async void SendTestChat()
        {
            if (!_npcSoul.IsConnected)
            {
                Debug.LogWarning("Not connected to server");
                return;
            }

            Debug.Log($"[Test] Sending chat: {_testMessage}");
            var response = await _npcSoul.Chat(_testMessage, _testPlayerId);

            if (response != null && response.success)
            {
                Debug.Log($"[Test] NPC response: {response.content}");
            }

            _testMessage = ""; // 清空输入
            Repaint();
        }
    }
}
#endif
