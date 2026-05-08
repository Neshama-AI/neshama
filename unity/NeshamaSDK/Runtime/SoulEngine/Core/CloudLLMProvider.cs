using System;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace Neshama.SoulEngine.Core
{
    /// <summary>
    /// LLM provider that calls the Neshama cloud API dialogue endpoint.
    /// Uses NeshamaConfig for API base URL and authentication.
    /// Requires UnityWebRequest (not System.Net.Http) for WebGL compatibility.
    /// </summary>
    public class CloudLLMProvider : ILLMProvider
    {
        private readonly string _baseUrl;
        private readonly string _apiKey;
        private readonly string _npcId;
        private readonly int _timeoutSeconds;

        /// <summary>
        /// Create a CloudLLMProvider.
        /// </summary>
        /// <param name="baseUrl">Neshama API base URL (e.g. "https://api.neshama.pw")</param>
        /// <param name="apiKey">API key for authentication</param>
        /// <param name="npcId">NPC ID to use for chat endpoint</param>
        /// <param name="timeoutSeconds">Request timeout in seconds (default 30)</param>
        public CloudLLMProvider(string baseUrl, string apiKey, string npcId, int timeoutSeconds = 30)
        {
            _baseUrl = baseUrl ?? "https://api.neshama.pw";
            _apiKey = apiKey ?? "";
            _npcId = npcId ?? throw new ArgumentNullException(nameof(npcId));
            _timeoutSeconds = Mathf.Max(5, timeoutSeconds);
        }

        /// <summary>
        /// Generate a response via Neshama cloud chat endpoint.
        /// POST /api/game/npc/{npcId}/chat with message as query param.
        /// </summary>
        public async Task<string> GenerateResponse(string systemPrompt, string userMessage)
        {
            if (string.IsNullOrEmpty(userMessage))
                return "";

            // Build URL: POST /api/game/npc/{npcId}/chat?message={userMessage}
            string url = $"{_baseUrl}/api/game/npc/{_npcId}/chat";
            string encodedMsg = UnityWebRequest.EscapeURL(userMessage);
            url += $"?message={encodedMsg}";

            var request = new UnityWebRequest(url, "POST");
            request.timeout = _timeoutSeconds;

            // Auth header
            if (!string.IsNullOrEmpty(_apiKey))
            {
                request.SetRequestHeader("Authorization", $"Bearer {_apiKey}");
            }
            request.SetRequestHeader("Content-Type", "application/json");

            // Empty body (message sent as query param per API spec)
            byte[] bodyRaw = Encoding.UTF8.GetBytes("{}");
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();

            var tcs = new TaskCompletionSource<string>();

            var operation = request.SendWebRequest();
            operation.completed += _ =>
            {
                try
                {
                    if (request.result == UnityWebRequest.Result.Success)
                    {
                        string json = request.downloadHandler.text;

                        // Parse Neshama API response: {"success": true, "data": {"content": "..."}}
                        var wrapper = JsonUtility.FromJson<CloudChatResponse>(json);
                        if (wrapper?.data != null && !string.IsNullOrEmpty(wrapper.data.content))
                        {
                            tcs.TrySetResult(wrapper.data.content);
                        }
                        else
                        {
                            // Fallback: return raw text if format unexpected
                            tcs.TrySetResult(json);
                        }
                    }
                    else
                    {
                        string error = request.error ?? $"HTTP {request.responseCode}";
                        tcs.TrySetException(new Exception($"CloudLLMProvider request failed: {error}"));
                    }
                }
                catch (Exception ex)
                {
                    tcs.TrySetException(new Exception($"CloudLLMProvider parse error: {ex.Message}"));
                }
                finally
                {
                    request.Dispose();
                }
            };

            return await tcs.Task;
        }

        // Response wrapper for Neshama cloud chat API
        [Serializable]
        private class CloudChatResponse
        {
            public bool success;
            public CloudChatData data;
        }

        [Serializable]
        private class CloudChatData
        {
            public string content;
        }
    }
}
