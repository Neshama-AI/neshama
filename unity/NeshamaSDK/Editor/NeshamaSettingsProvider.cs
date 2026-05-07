#if UNITY_EDITOR
using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.ProjectWindowCallback;
using Neshama.SDK;

namespace Neshama.SDK.Editor
{
    /// <summary>
    /// Neshama Project Settings 提供器
    /// 在 Edit → Project Settings → Neshama 中显示配置面板
    /// </summary>
    public class NeshamaSettingsProvider : SettingsProvider
    {
        // 设置文件路径
        private const string SettingsPath = "ProjectSettings/NeshamaSettings.asset";
        
        // 设置实例
        private static NeshamaConfig _settings;

        /// <summary>
        /// 获取或创建设置实例
        /// </summary>
        public static NeshamaConfig Settings
        {
            get
            {
                if (_settings == null)
                {
                    LoadSettings();
                }
                return _settings;
            }
        }

        /// <summary>
        /// 加载设置
        /// </summary>
        [SettingsProvider]
        public static SettingsProvider CreateNeshamaSettingsProvider()
        {
            var provider = new NeshamaSettingsProvider("Project/Neshama", SettingsScope.Project);
            return provider;
        }

        /// <summary>
        /// 构造函数
        /// </summary>
        public NeshamaSettingsProvider(string path, SettingsScope scopes) : base(path, scopes)
        {
        }

        /// <summary>
        /// 加载设置文件
        /// </summary>
        public static void LoadSettings()
        {
            if (File.Exists(SettingsPath))
            {
                try
                {
                    var json = File.ReadAllText(SettingsPath);
                    _settings = JsonUtility.FromJson<NeshamaConfig>(json);
                }
                catch
                {
                    _settings = CreateDefaultSettings();
                }
            }
            else
            {
                _settings = CreateDefaultSettings();
            }
        }

        /// <summary>
        /// 保存设置文件
        /// </summary>
        public static void SaveSettings()
        {
            if (_settings == null) return;

            try
            {
                var json = JsonUtility.ToJson(_settings, true);
                File.WriteAllText(SettingsPath, json);
                EditorUtility.SetDirty(_settings);
            }
            catch (System.Exception e)
            {
                Debug.LogError($"Failed to save Neshama settings: {e.Message}");
            }
        }

        /// <summary>
        /// 创建默认设置
        /// </summary>
        private static NeshamaConfig CreateDefaultSettings()
        {
            var settings = ScriptableObject.CreateInstance<NeshamaConfig>();
            settings.name = "NeshamaSettings";
            return settings;
        }

        /// <summary>
        /// 绘制设置GUI
        /// </summary>
        public override void OnGUI(string searchContext)
        {
            EditorGUILayout.LabelField("Neshama SDK Configuration", EditorStyles.boldLabel);
            EditorGUILayout.Space();

            if (Settings == null)
            {
                EditorGUILayout.HelpBox("Failed to load settings. Please restart Unity.", MessageType.Error);
                return;
            }

            // 服务器配置
            EditorGUILayout.LabelField("Server Configuration", EditorStyles.boldLabel);
            EditorGUI.indentLevel++;
            
            EditorGUI.BeginChangeCheck();
            
            var serverMode = (NeshamaConfig.ServerMode)EditorGUILayout.EnumPopup("Server Mode", Settings.CurrentServerMode);
            Settings.CurrentServerMode = serverMode;
            
            var baseUrl = EditorGUILayout.TextField("Base URL", Settings.BaseUrl);
            Settings.BaseUrl = baseUrl;
            
            EditorGUI.indentLevel++;
            EditorGUILayout.LabelField("Authentication", EditorStyles.boldLabel);
            
            Settings.ApiKey = EditorGUILayout.TextField("API Key", Settings.ApiKey);
            Settings.TrialMode = EditorGUILayout.Toggle("Trial Mode", Settings.TrialMode);
            if (Settings.TrialMode)
            {
                Settings.TrialToken = EditorGUILayout.TextField("Trial Token", Settings.TrialToken);
            }
            
            EditorGUI.indentLevel--;
            
            Settings.TimeoutSeconds = EditorGUILayout.IntField("Timeout (seconds)", Settings.TimeoutSeconds);
            Settings.MaxRetries = EditorGUILayout.IntField("Max Retries", Settings.MaxRetries);
            Settings.RetryDelaySeconds = EditorGUILayout.FloatField("Retry Delay", Settings.RetryDelaySeconds);
            
            EditorGUI.indentLevel--;
            EditorGUILayout.Space();

            // 连接配置
            EditorGUILayout.LabelField("Connection", EditorStyles.boldLabel);
            EditorGUI.indentLevel++;
            
            Settings.AutoConnect = EditorGUILayout.Toggle("Auto Connect", Settings.AutoConnect);
            Settings.HeartbeatInterval = EditorGUILayout.FloatField("Heartbeat Interval", Settings.HeartbeatInterval);
            
            EditorGUI.indentLevel--;
            EditorGUILayout.Space();

            // 默认值配置
            EditorGUILayout.LabelField("Defaults", EditorStyles.boldLabel);
            EditorGUI.indentLevel++;
            
            Settings.DefaultPlayerId = EditorGUILayout.TextField("Default Player ID", Settings.DefaultPlayerId);
            Settings.DefaultPreset = EditorGUILayout.TextField("Default Preset", Settings.DefaultPreset);
            
            EditorGUI.indentLevel--;
            EditorGUILayout.Space();

            // 调试配置
            EditorGUILayout.LabelField("Debug", EditorStyles.boldLabel);
            EditorGUI.indentLevel++;
            
            Settings.DebugMode = EditorGUILayout.Toggle("Debug Mode", Settings.DebugMode);
            Settings.LogLevel = (NeshamaConfig.LogLevel)EditorGUILayout.EnumPopup("Log Level", Settings.LogLevel);
            
            EditorGUI.indentLevel--;
            EditorGUILayout.Space();

            if (EditorGUI.EndChangeCheck())
            {
                SaveSettings();
            }

            // 测试连接按钮
            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Connection Test", EditorStyles.boldLabel);
            
            EditorGUILayout.BeginHorizontal();
            
            if (GUILayout.Button("Test Connection", GUILayout.Height(30)))
            {
                TestConnection();
            }
            
            if (GUILayout.Button("Reset to Defaults", GUILayout.Height(30)))
            {
                if (EditorUtility.DisplayDialog("Reset Settings", 
                    "Are you sure you want to reset all settings to defaults?", 
                    "Reset", "Cancel"))
                {
                    Settings.BaseUrl = "https://api.neshama.ai";
                    Settings.CurrentServerMode = NeshamaConfig.ServerMode.Cloud;
                    Settings.ApiKey = "";
                    Settings.TrialMode = false;
                    Settings.TrialToken = "";
                    Settings.TimeoutSeconds = 30;
                    Settings.MaxRetries = 3;
                    Settings.RetryDelaySeconds = 1f;
                    Settings.AutoConnect = true;
                    Settings.HeartbeatInterval = 30f;
                    Settings.DefaultPlayerId = "player_001";
                    Settings.DefaultPreset = "default";
                    Settings.DebugMode = false;
                    Settings.LogLevel = NeshamaConfig.LogLevel.Info;
                    SaveSettings();
                }
            }
            
            EditorGUILayout.EndHorizontal();

            // 显示当前配置信息
            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Current Configuration", EditorStyles.boldLabel);
            
            var info = $"API Base: {Settings.GetFullApiBaseUrl()}\n" +
                      $"Config Valid: {Settings.IsValid()}";
            
            EditorGUILayout.HelpBox(info, MessageType.Info);
        }

        /// <summary>
        /// 测试连接
        /// </summary>
        private static async void TestConnection()
        {
            if (!Settings.IsValid())
            {
                EditorUtility.DisplayDialog("Invalid Configuration", 
                    "Please check your settings before testing connection.", 
                    "OK");
                return;
            }

            try
            {
                EditorUtility.DisplayProgressBar("Testing Connection", "Connecting to server...", 0.5f);
                
                // 创建一个临时GameObject来运行协程
                var testObj = new GameObject("NeshamaConnectionTest");
                var testComponent = testObj.AddComponent<ConnectionTestComponent>();
                
                var client = new NeshamaClient(Settings, testComponent);
                bool success = await client.TestConnectionAsync();
                
                // 清理
                client.Dispose();
                DestroyImmediate(testObj);
                EditorUtility.ClearProgressBar();
                
                if (success)
                {
                    EditorUtility.DisplayDialog("Connection Test", 
                        "Successfully connected to Neshama server!", 
                        "OK");
                }
                else
                {
                    EditorUtility.DisplayDialog("Connection Test", 
                        "Failed to connect. Please check the server URL and try again.", 
                        "OK");
                }
            }
            catch (System.Exception e)
            {
                EditorUtility.ClearProgressBar();
                EditorUtility.DisplayDialog("Connection Error", 
                    $"Connection test failed:\n{e.Message}", 
                    "OK");
            }
        }

        /// <summary>
        /// 连接测试组件
        /// </summary>
        private class ConnectionTestComponent : MonoBehaviour
        {
        }

        /// <summary>
        /// 菜单项：打开Neshama设置
        /// </summary>
        [MenuItem("Edit/Project Settings/Neshama")]
        public static void OpenSettings()
        {
            SettingsService.OpenProjectSettings("Project/Neshama");
        }

        /// <summary>
        /// 菜单项：重置设置
        /// </summary>
        [MenuItem("Window/Neshama/Reset Settings")]
        public static void ResetSettings()
        {
            if (EditorUtility.DisplayDialog("Reset Settings", 
                "Are you sure you want to reset all Neshama settings to defaults?", 
                "Reset", "Cancel"))
            {
                if (File.Exists(SettingsPath))
                {
                    File.Delete(SettingsPath);
                }
                LoadSettings();
            }
        }
    }
}
#endif
