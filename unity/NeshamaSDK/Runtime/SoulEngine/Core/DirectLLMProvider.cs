using System;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace Neshama.SoulEngine.Core
{
    /// <summary>
    /// LLM provider that directly calls an OpenAI-compatible API.
    /// User provides their own API key and endpoint.
    /// Supports OpenAI, DeepSeek, Moonshot, and any OpenAI-compatible LLM API.
    /// Uses UnityWebRequest (not System.Net.Http) for WebGL compatibility.
    /// </summary>
    public class DirectLLMProvider : ILLMProvider
    {
        private readonly string _apiUrl;
        private readonly string _apiKey;
        private readonly string _model;
        private readonly int _timeoutSeconds;

        /// <summary>
        /// Create a DirectLLMProvider.
        /// </summary>
        /// <param name="apiUrl">Full API URL (e.g. "https://api.openai.com/v1/chat/completions")</param>
        /// <param name="apiKey">API key for authentication</param>
        /// <param name="model">Model name (e.g. "gpt-4o-mini", "deepseek-chat")</param>
        /// <param name="timeoutSeconds">Request timeout in seconds (default 60)</param>
        public DirectLLMProvider(string apiUrl, string apiKey, string model = null, int timeoutSeconds = 60)
        {
            _apiUrl = apiUrl ?? throw new ArgumentNullException(nameof(apiUrl));
            _apiKey = apiKey ?? throw new ArgumentNullException(nameof(apiKey));
            _model = model ?? "gpt-4o-mini";
            _timeoutSeconds = Mathf.Max(10, timeoutSeconds);
        }

        /// <summary>
        /// Generate a response via OpenAI-compatible chat completions endpoint.
        /// POST with messages array in OpenAI format.
        /// </summary>
        public async Task<string> GenerateResponse(string systemPrompt, string userMessage)
        {
            if (string.IsNullOrEmpty(userMessage))
                return "";

            // Build OpenAI-compatible request body
            string body = BuildRequestBody(systemPrompt, userMessage);
            byte[] bodyRaw = Encoding.UTF8.GetBytes(body);

            var request = new UnityWebRequest(_apiUrl, "POST");
            request.timeout = _timeoutSeconds;

            request.SetRequestHeader("Content-Type", "application/json");
            request.SetRequestHeader("Authorization", $"Bearer {_apiKey}");

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
                        string content = ParseOpenAIResponse(json);
                        tcs.TrySetResult(content);
                    }
                    else
                    {
                        string error = request.error ?? $"HTTP {request.responseCode}";
                        tcs.TrySetException(new Exception($"DirectLLMProvider request failed: {error}"));
                    }
                }
                catch (Exception ex)
                {
                    tcs.TrySetException(new Exception($"DirectLLMProvider error: {ex.Message}"));
                }
                finally
                {
                    request.Dispose();
                }
            };

            return await tcs.Task;
        }

        /// <summary>
        /// Build OpenAI-compatible chat completions request body.
        /// </summary>
        private string BuildRequestBody(string systemPrompt, string userMessage)
        {
            // Build JSON manually to avoid dependency on Newtonsoft.Json
            // OpenAI format: {"model":"...", "messages":[{"role":"system","content":"..."},{"role":"user","content":"..."}]}
            var sb = new StringBuilder(512);
            sb.Append("{\"model\":\"");
            sb.Append(EscapeJsonString(_model));
            sb.Append("\",\"messages\":[");

            // System message
            if (!string.IsNullOrEmpty(systemPrompt))
            {
                sb.Append("{\"role\":\"system\",\"content\":\"");
                sb.Append(EscapeJsonString(systemPrompt));
                sb.Append("\"},");
            }

            // User message
            sb.Append("{\"role\":\"user\",\"content\":\"");
            sb.Append(EscapeJsonString(userMessage));
            sb.Append("\"}]}");

            return sb.ToString();
        }

        /// <summary>
        /// Parse OpenAI chat completions response to extract assistant message content.
        /// Response format: {"choices":[{"message":{"content":"..."}}]}
        /// </summary>
        private string ParseOpenAIResponse(string json)
        {
            try
            {
                var response = JsonUtility.FromJson<OpenAIChatResponse>(json);
                if (response?.choices != null && response.choices.Length > 0)
                {
                    var content = response.choices[0].message?.content;
                    if (!string.IsNullOrEmpty(content))
                        return content;
                }
            }
            catch
            {
                // Fallback: try to extract content with simple string search
                const string contentKey = "\"content\":\"";
                int idx = json.IndexOf(contentKey, StringComparison.Ordinal);
                if (idx >= 0)
                {
                    int start = idx + contentKey.Length;
                    int end = json.IndexOf("\"", start, StringComparison.Ordinal);
                    if (end > start)
                        return json.Substring(start, end - start);
                }
            }

            return "[DirectLLMProvider] Empty or unexpected response format";
        }

        /// <summary>
        /// Escape a string for JSON embedding (handles quotes, backslashes, newlines).
        /// </summary>
        private static string EscapeJsonString(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            var sb = new StringBuilder(s.Length + 16);
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"':  sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:   sb.Append(c); break;
                }
            }
            return sb.ToString();
        }

        // OpenAI chat completions response types
        [Serializable]
        private class OpenAIChatResponse
        {
            public OpenAIChoice[] choices;
        }

        [Serializable]
        private class OpenAIChoice
        {
            public OpenAIMessage message;
        }

        [Serializable]
        private class OpenAIMessage
        {
            public string content;
        }
    }
}
