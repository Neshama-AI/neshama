#if UNITY_EDITOR
using System;
using System.Text;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;
using Neshama.SDK;
using Neshama.SDK.Models;
using Neshama.SDK.Enums;

namespace Neshama.SDK.Editor
{
    /// <summary>
    /// Neshama Setup Wizard — 引导用户从零开始配置SDK
    /// 菜单: Neshama → Setup Wizard
    /// 
    /// 步骤:
    /// 1. 欢迎 — 了解Neshama是什么
    /// 2. 登录/注册 — 获取API Key或免注册试用
    /// 3. 连接测试 — 验证API Key有效
    /// 4. 创建第一个NPC — 选模板，一键生成
    /// 5. 完成！— 显示快速入门代码
    /// </summary>
    public class SetupWizard : EditorWindow
    {
        private int _step = 0;
        private const int TotalSteps = 5;

        // Step 2: Auth
        private int _authMode = 0; // 0=login, 1=register, 2=apikey, 3=trial
        private string _email = "";
        private string _password = "";
        private string _name = "";
        private string _apiKeyInput = "";
        private string _authMessage = "";
        private bool _authLoading = false;
        private string _obtainedApiKey = "";

        // Step 3: Connection test
        private bool _testPassed = false;
        private string _testMessage = "";
        private bool _testRunning = false;

        // Step 4: NPC creation
        private int _selectedPreset = 0;
        private string[] _presetNames = { "Tavern Keeper (Friendly)", "Guard Captain (Strict)", "Mystic Traveler (Mysterious)", "Custom" };
        private string _npcName = "NPC";

        // Step 5: Done
        private Vector2 _scrollPos;

        [MenuItem("Neshama/Setup Wizard", false, 0)]
        public static void ShowWizard()
        {
            var window = GetWindow<SetupWizard>("Neshama Setup Wizard");
            window.minSize = new Vector2(500, 520);
            window.maxSize = new Vector2(600, 700);
        }

        [MenuItem("Neshama/Open Dashboard", false, 100)]
        public static void OpenDashboard()
        {
            Application.OpenURL("https://api.neshama.pw");
        }

        void OnGUI()
        {
            _scrollPos = EditorGUILayout.BeginScrollView(_scrollPos);

            DrawHeader();
            DrawProgressBar();

            switch (_step)
            {
                case 0: DrawWelcome(); break;
                case 1: DrawAuth(); break;
                case 2: DrawConnectionTest(); break;
                case 3: DrawCreateNPC(); break;
                case 4: DrawDone(); break;
            }

            EditorGUILayout.EndScrollView();
        }

        // ── Header ──────────────────────────────────────────────────────────

        void DrawHeader()
        {
            EditorGUILayout.Space(8);
            var headerStyle = new GUIStyle(EditorStyles.boldLabel)
            {
                fontSize = 20,
                alignment = TextAnchor.MiddleCenter
            };
            EditorGUILayout.LabelField("🔮 Neshama Setup Wizard", headerStyle);
            EditorGUILayout.Space(4);
        }

        void DrawProgressBar()
        {
            EditorGUILayout.Space(4);
            var rect = GUILayoutUtility.GetRect(0, 6, GUILayout.ExpandWidth(true));
            EditorGUI.DrawRect(rect, new Color(0.15f, 0.15f, 0.2f));

            var progressRect = new Rect(rect.x, rect.y, rect.width * ((_step + 1f) / TotalSteps), rect.height);
            EditorGUI.DrawRect(progressRect, new Color(0.3f, 0.58f, 1f));

            EditorGUILayout.Space(4);

            var stepLabels = new[] { "Welcome", "Account", "Test", "Create NPC", "Done!" };
            var stepStyle = new GUIStyle(EditorStyles.miniLabel) { alignment = TextAnchor.MiddleCenter };
            EditorGUILayout.BeginHorizontal();
            foreach (var label in stepLabels)
            {
                EditorGUILayout.LabelField(label, stepStyle);
            }
            EditorGUILayout.EndHorizontal();
            EditorGUILayout.Space(8);
        }

        // ── Step 1: Welcome ─────────────────────────────────────────────────

        void DrawWelcome()
        {
            EditorGUILayout.Space(10);

            var titleStyle = new GUIStyle(EditorStyles.boldLabel) { fontSize = 16, wordWrap = true };
            var bodyStyle = new GUIStyle(EditorStyles.label) { wordWrap = true, fontSize = 13 };

            EditorGUILayout.LabelField("Welcome to Neshama! 👋", titleStyle);
            EditorGUILayout.Space(8);
            EditorGUILayout.LabelField(
                "Neshama gives your game NPCs a soul — with emotions, memory, personality, and social relationships. " +
                "Your NPCs will remember players, react to events, and evolve over time.",
                bodyStyle
            );

            EditorGUILayout.Space(16);

            EditorGUILayout.LabelField("What you'll get:", EditorStyles.boldLabel);
            EditorGUILayout.LabelField("  ❤️  9 emotions that respond to game events", bodyStyle);
            EditorGUILayout.LabelField("  🧠  Multi-layer memory (short / medium / long term)", bodyStyle);
            EditorGUILayout.LabelField("  🎭  OCEAN personality model", bodyStyle);
            EditorGUILayout.LabelField("  🕸️  Social relationship graph", bodyStyle);
            EditorGUILayout.LabelField("  💬  AI-driven conversations", bodyStyle);

            EditorGUILayout.Space(16);

            EditorGUILayout.LabelField("This wizard will guide you through:", EditorStyles.boldLabel);
            EditorGUILayout.LabelField("  1. Create an account (or try for free)", bodyStyle);
            EditorGUILayout.LabelField("  2. Verify your connection", bodyStyle);
            EditorGUILayout.LabelField("  3. Create your first soul-powered NPC", bodyStyle);

            EditorGUILayout.Space(20);

            if (GUILayout.Button("Let's Get Started! →", GUILayout.Height(40)))
            {
                _step = 1;
            }
        }

        // ── Step 2: Auth ────────────────────────────────────────────────────

        void DrawAuth()
        {
            var titleStyle = new GUIStyle(EditorStyles.boldLabel) { fontSize = 14 };
            var bodyStyle = new GUIStyle(EditorStyles.label) { wordWrap = true };

            EditorGUILayout.LabelField("Connect Your Account", titleStyle);
            EditorGUILayout.Space(4);
            EditorGUILayout.LabelField("Sign up, log in, paste an API Key, or try for free:", bodyStyle);
            EditorGUILayout.Space(8);

            // Auth mode tabs
            var tabs = new[] { "Sign Up", "Log In", "API Key", "Free Trial" };
            _authMode = GUILayout.Toolbar(_authMode, tabs);

            EditorGUILayout.Space(10);

            switch (_authMode)
            {
                case 0: DrawRegisterForm(); break;
                case 1: DrawLoginForm(); break;
                case 2: DrawApiKeyForm(); break;
                case 3: DrawTrialForm(); break;
            }

            if (!string.IsNullOrEmpty(_authMessage))
            {
                EditorGUILayout.Space(4);
                var isGood = _authMessage.StartsWith("✅");
                var msgStyle = new GUIStyle(EditorStyles.helpBox) { fontSize = 12 };
                if (isGood) GUI.color = Color.green;
                else GUI.color = new Color(1f, 0.4f, 0.4f);
                EditorGUILayout.LabelField(_authMessage, msgStyle);
                GUI.color = Color.white;
            }

            EditorGUILayout.Space(12);
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("← Back", GUILayout.Width(80)))
            {
                _step = 0;
                _authMessage = "";
            }
            if (GUILayout.Button("Skip (use local server)", GUILayout.Width(180)))
            {
                var config = NeshamaSettingsProvider.Settings;
                if (config != null)
                {
                    config.CurrentServerMode = NeshamaConfig.ServerMode.Local;
                    NeshamaSettingsProvider.SaveSettings();
                }
                _step = 2;
            }
            EditorGUILayout.EndHorizontal();
        }

        void DrawRegisterForm()
        {
            _name = EditorGUILayout.TextField("Name", _name);
            _email = EditorGUILayout.TextField("Email", _email);
            _password = EditorGUILayout.PasswordField("Password", _password);

            EditorGUILayout.Space(6);
            if (GUILayout.Button("Create Account", GUILayout.Height(32)))
            {
                DoRegister();
            }
        }

        void DrawLoginForm()
        {
            _email = EditorGUILayout.TextField("Email", _email);
            _password = EditorGUILayout.PasswordField("Password", _password);

            EditorGUILayout.Space(6);
            if (GUILayout.Button("Sign In", GUILayout.Height(32)))
            {
                DoLogin();
            }
        }

        void DrawApiKeyForm()
        {
            _apiKeyInput = EditorGUILayout.TextField("API Key", _apiKeyInput);

            EditorGUILayout.Space(6);
            if (GUILayout.Button("Connect", GUILayout.Height(32)))
            {
                DoApiKeyConnect();
            }
        }

        void DrawTrialForm()
        {
            EditorGUILayout.LabelField("🎮 Free Trial Mode", EditorStyles.boldLabel);
            EditorGUILayout.Space(4);
            EditorGUILayout.LabelField(
                "Try Neshama without creating an account:\n" +
                "• 50 free AI conversations\n" +
                "• No email required\n" +
                "• Valid for 24 hours\n" +
                "• Upgrade to full account anytime",
                new GUIStyle(EditorStyles.label) { wordWrap = true }
            );

            EditorGUILayout.Space(8);
            if (GUILayout.Button("🚀 Start Free Trial", GUILayout.Height(36)))
            {
                DoTrial();
            }
        }

        async void DoRegister()
        {
            if (string.IsNullOrEmpty(_email) || string.IsNullOrEmpty(_password) || string.IsNullOrEmpty(_name))
            {
                _authMessage = "❌ Please fill in all fields";
                return;
            }
            _authLoading = true;
            _authMessage = "⏳ Creating account...";
            Repaint();

            try
            {
                var config = NeshamaConfig.CreateDefault();
                var client = new NeshamaClient(config, CreateTempMono());
                var result = await client.PostAbsoluteAsync<object>("/api/auth/register", new
                {
                    email = _email,
                    password = _password,
                    name = _name
                });

                if (result != null)
                {
                    var dict = result as System.Collections.IDictionary;
                    if (dict != null && dict.Contains("api_key"))
                    {
                        _obtainedApiKey = dict["api_key"]?.ToString() ?? "";
                        ApplyApiKey(_obtainedApiKey);
                        _authMessage = "✅ Account created! API Key saved.";
                        _step = 2;
                    }
                    else
                    {
                        _authMessage = "❌ Unexpected response from server";
                    }
                }
            }
            catch (Exception e)
            {
                _authMessage = $"❌ {e.Message}";
            }
            _authLoading = false;
            Repaint();
        }

        async void DoLogin()
        {
            if (string.IsNullOrEmpty(_email) || string.IsNullOrEmpty(_password))
            {
                _authMessage = "❌ Please fill in all fields";
                return;
            }
            _authLoading = true;
            _authMessage = "⏳ Signing in...";
            Repaint();

            try
            {
                var config = NeshamaConfig.CreateDefault();
                var client = new NeshamaClient(config, CreateTempMono());
                var result = await client.PostAbsoluteAsync<object>("/api/auth/login", new
                {
                    email = _email,
                    password = _password
                });

                if (result != null)
                {
                    var dict = result as System.Collections.IDictionary;
                    if (dict != null && dict.Contains("api_key"))
                    {
                        _obtainedApiKey = dict["api_key"]?.ToString() ?? "";
                        ApplyApiKey(_obtainedApiKey);
                        _authMessage = "✅ Signed in! API Key saved.";
                        _step = 2;
                    }
                }
            }
            catch (Exception e)
            {
                _authMessage = $"❌ {e.Message}";
            }
            _authLoading = false;
            Repaint();
        }

        void DoApiKeyConnect()
        {
            if (string.IsNullOrEmpty(_apiKeyInput))
            {
                _authMessage = "❌ Please enter your API Key";
                return;
            }
            ApplyApiKey(_apiKeyInput);
            _obtainedApiKey = _apiKeyInput;
            _authMessage = "✅ API Key saved!";
            _step = 2;
            Repaint();
        }

        async void DoTrial()
        {
            _authLoading = true;
            _authMessage = "⏳ Starting trial...";
            Repaint();

            try
            {
                var config = NeshamaConfig.CreateDefault();
                config.TrialMode = true;
                var client = new NeshamaClient(config, CreateTempMono());
                var result = await client.PostAbsoluteAsync<object>("/api/auth/trial", null);

                if (result != null)
                {
                    var dict = result as System.Collections.IDictionary;
                    if (dict != null && dict.Contains("trial_token"))
                    {
                        var token = dict["trial_token"]?.ToString() ?? "";
                        config.TrialToken = token;
                        config.TrialMode = true;
                        config.CurrentServerMode = NeshamaConfig.ServerMode.Cloud;
                        ApplyConfig(config);
                        _authMessage = "✅ Trial started! 50 free conversations.";
                        _step = 2;
                    }
                }
            }
            catch (Exception e)
            {
                _authMessage = $"❌ {e.Message}";
            }
            _authLoading = false;
            Repaint();
        }

        void ApplyApiKey(string apiKey)
        {
            var config = NeshamaSettingsProvider.Settings;
            if (config != null)
            {
                config.ApiKey = apiKey;
                config.CurrentServerMode = NeshamaConfig.ServerMode.Cloud;
                config.TrialMode = false;
                NeshamaSettingsProvider.SaveSettings();
            }
        }

        void ApplyConfig(NeshamaConfig source)
        {
            var config = NeshamaSettingsProvider.Settings;
            if (config != null)
            {
                config.TrialMode = source.TrialMode;
                config.TrialToken = source.TrialToken;
                config.CurrentServerMode = source.CurrentServerMode;
                config.ApiKey = source.ApiKey;
                NeshamaSettingsProvider.SaveSettings();
            }
        }

        MonoBehaviour CreateTempMono()
        {
            var go = new GameObject("NeshamaSetupTemp");
            go.hideFlags = HideFlags.HideAndDontSave;
            return go.AddComponent<SetupWizardHelper>();
        }

        // ── Step 3: Connection Test ─────────────────────────────────────────

        void DrawConnectionTest()
        {
            var titleStyle = new GUIStyle(EditorStyles.boldLabel) { fontSize = 14 };

            EditorGUILayout.LabelField("Test Connection", titleStyle);
            EditorGUILayout.Space(4);
            EditorGUILayout.LabelField("Let's verify your setup is working correctly.");
            EditorGUILayout.Space(10);

            var config = NeshamaSettingsProvider.Settings;
            if (config != null)
            {
                EditorGUILayout.LabelField("Server Mode:", config.CurrentServerMode.ToString());
                EditorGUILayout.LabelField("Base URL:", config.BaseUrl);
                EditorGUILayout.LabelField("Auth:", config.HasAuth() ? "✅ Configured" : "❌ Not set");
            }

            EditorGUILayout.Space(10);

            if (_testRunning)
            {
                EditorGUILayout.LabelField("⏳ Testing connection...");
            }
            else if (_testPassed)
            {
                EditorGUILayout.LabelField("✅ Connection successful!", new GUIStyle(EditorStyles.boldLabel) { normal = { textColor = Color.green } });
            }
            else if (!string.IsNullOrEmpty(_testMessage))
            {
                EditorGUILayout.LabelField($"❌ {_testMessage}", new GUIStyle(EditorStyles.wordWrappedLabel) { normal = { textColor = Color.red } });
            }

            EditorGUILayout.Space(16);

            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("← Back", GUILayout.Width(80)))
            {
                _step = 1;
                _testPassed = false;
                _testMessage = "";
            }
            if (GUILayout.Button("Test Connection", GUILayout.Height(36)))
            {
                DoConnectionTest();
            }
            if (_testPassed && GUILayout.Button("Next →", GUILayout.Height(36)))
            {
                _step = 3;
            }
            EditorGUILayout.EndHorizontal();
        }

        async void DoConnectionTest()
        {
            _testRunning = true;
            _testPassed = false;
            _testMessage = "";
            Repaint();

            try
            {
                var config = NeshamaSettingsProvider.Settings ?? NeshamaConfig.CreateDefault();
                var client = new NeshamaClient(config, CreateTempMono());

                // Try health endpoint first
                bool success = await client.TestConnectionAsync();

                _testPassed = success;
                if (!success)
                {
                    _testMessage = "Could not connect to server. Check your settings.";
                }
            }
            catch (Exception e)
            {
                _testPassed = false;
                _testMessage = e.Message;
            }

            _testRunning = false;
            Repaint();
        }

        // ── Step 4: Create NPC ──────────────────────────────────────────────

        void DrawCreateNPC()
        {
            var titleStyle = new GUIStyle(EditorStyles.boldLabel) { fontSize = 14 };
            var bodyStyle = new GUIStyle(EditorStyles.label) { wordWrap = true };

            EditorGUILayout.LabelField("Create Your First NPC", titleStyle);
            EditorGUILayout.Space(4);
            EditorGUILayout.LabelField("Choose a personality preset, and we'll create a ready-to-use NPC GameObject.", bodyStyle);
            EditorGUILayout.Space(10);

            _selectedPreset = EditorGUILayout.Popup("Preset", _selectedPreset, _presetNames);
            _npcName = EditorGUILayout.TextField("NPC Name", _npcName);

            EditorGUILayout.Space(6);
            EditorGUILayout.LabelField("Preset Preview:", EditorStyles.boldLabel);

            string previewText = _selectedPreset switch
            {
                0 => "Friendly, warm, remembers regular customers. High Agreeableness, moderate Extraversion.",
                1 => "Strict, disciplined, respects strength. Low Agreeableness, high Conscientiousness.",
                2 => "Mysterious, wise, speaks in riddles. High Openness, low Extraversion.",
                _ => "Configure your own OCEAN personality values."
            };
            EditorGUILayout.LabelField(previewText, new GUIStyle(EditorStyles.wordWrappedLabel) { fontSize = 12 });

            EditorGUILayout.Space(16);

            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("← Back", GUILayout.Width(80)))
            {
                _step = 2;
            }
            if (GUILayout.Button("🎮 Create NPC GameObject", GUILayout.Height(40)))
            {
                CreateNPCGameObject();
                _step = 4;
            }
            EditorGUILayout.EndHorizontal();
        }

        void CreateNPCGameObject()
        {
            var preset = _selectedPreset switch
            {
                0 => "tavern_keeper",
                1 => "guard_captain",
                2 => "mystic_traveler",
                _ => "default"
            };

            // Create GameObject
            var npcObj = new GameObject(_npcName);
            var soul = npcObj.AddComponent<NPCSoul>();

            // Configure NPCSoul
            soul.Configure(
                $"npc_{_npcName.GetHashCode()}",
                _npcName,
                preset,
                true
            );

            // Select it in hierarchy
            Selection.activeGameObject = npcObj;
            SceneView.FrameLastActiveSceneView();

            Debug.Log($"[Neshama] Created NPC '{_npcName}' with preset '{preset}'");
        }

        // ── Step 5: Done! ───────────────────────────────────────────────────

        void DrawDone()
        {
            var titleStyle = new GUIStyle(EditorStyles.boldLabel) { fontSize = 16 };
            var bodyStyle = new GUIStyle(EditorStyles.label) { wordWrap = true, fontSize = 12 };
            var codeStyle = new GUIStyle(EditorStyles.textArea)
            {
                fontSize = 11,
                fontFamily = "Consolas",
                wordWrap = true
            };

            EditorGUILayout.LabelField("🎉 You're All Set!", titleStyle);
            EditorGUILayout.Space(4);
            EditorGUILayout.LabelField("Your first soul-powered NPC is ready. Here's how to use it:", bodyStyle);

            EditorGUILayout.Space(10);

            EditorGUILayout.LabelField("Quick Start Code:", EditorStyles.boldLabel);
            EditorGUILayout.Space(4);

            var code = @"// In your game script:
var npcSoul = GetComponent<NPCSoul>();

// Send a game event
await npcSoul.SendEvent(GameEventType.player_entered, 0.3f);

// Chat with the NPC
var response = await npcSoul.Chat(""Hello!"", ""player_001"");

// Listen for emotion changes
npcSoul.OnEmotionChanged += (emotion) => {
    if (emotion.Anger > 0.5f) Debug.Log(""NPC is angry!"");
};";
            EditorGUILayout.TextArea(code, codeStyle, GUILayout.Height(160));

            EditorGUILayout.Space(10);

            EditorGUILayout.LabelField("Next Steps:", EditorStyles.boldLabel);
            EditorGUILayout.LabelField("• Edit your NPC's OCEAN personality in the Inspector", bodyStyle);
            EditorGUILayout.LabelField("• Try sending different GameEventType values", bodyStyle);
            EditorGUILayout.LabelField("• Check the Dashboard at api.neshama.pw", bodyStyle);
            EditorGUILayout.LabelField("• Read the full docs: neshama.ai/docs", bodyStyle);

            EditorGUILayout.Space(16);

            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("← Back", GUILayout.Width(80)))
            {
                _step = 3;
            }
            if (GUILayout.Button("Open Dashboard", GUILayout.Height(36)))
            {
                Application.OpenURL("https://api.neshama.pw");
            }
            if (GUILayout.Button("Close Wizard", GUILayout.Height(36)))
            {
                Close();
            }
            EditorGUILayout.EndHorizontal();
        }
    }

    /// <summary>
    /// Helper MonoBehaviour for running async operations in Editor
    /// </summary>
    public class SetupWizardHelper : MonoBehaviour { }
}
#endif
