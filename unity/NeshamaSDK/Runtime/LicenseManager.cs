// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - License Manager
// Handles license validation, offline grace period, region isolation, and feature gating

using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace Neshama.SDK
{
    /// <summary>
    /// License information returned from the validation server.
    /// Includes region fields for cross-region arbitrage prevention.
    /// </summary>
    [Serializable]
    public class LicenseInfo
    {
        public bool Valid;
        public string Plan = "free";
        public int MaxNpcs = 3;
        public List<string> Features = new List<string>();
        public string ExpiresAt = "";
        public string Region = "global";
        public bool RegionMatch = true;
        public string GraceUntil = null;
        public string LastValidatedAt = "";
        public string Error = null;

        // Local cache timestamp (not from server)
        [NonSerialized]
        public DateTime CachedAt;

        /// <summary>
        /// Check if a feature is available in this license.
        /// </summary>
        public bool HasFeature(string featureName)
        {
            return Features != null && Features.Contains(featureName);
        }

        /// <summary>
        /// Check if this license is within the grace period.
        /// </summary>
        public bool IsWithinGracePeriod()
        {
            if (string.IsNullOrEmpty(GraceUntil)) return false;
            if (DateTime.TryParse(GraceUntil, null, System.Globalization.DateTimeStyles.RoundtripKind, out DateTime graceEnd))
            {
                return DateTime.UtcNow < graceEnd;
            }
            return false;
        }

        /// <summary>
        /// Check if the license has expired.
        /// </summary>
        public bool IsExpired()
        {
            if (string.IsNullOrEmpty(ExpiresAt)) return !Valid;
            if (DateTime.TryParse(ExpiresAt, null, System.Globalization.DateTimeStyles.RoundtripKind, out DateTime expiry))
            {
                return DateTime.UtcNow > expiry;
            }
            return !Valid;
        }

        /// <summary>
        /// Check if there's a region mismatch. Returns a user-friendly error message.
        /// </summary>
        public string GetRegionMismatchMessage()
        {
            if (RegionMatch) return null;
            string regionName = Region == "cn" ? "China (中国区)" : "Global (国际区)";
            return $"License key region mismatch. This key is for {regionName}. " +
                   $"Cross-region usage is not permitted.";
        }

        /// <summary>
        /// Deserialize from JSON response.
        /// </summary>
        public static LicenseInfo FromJson(string json)
        {
            try
            {
                return JsonUtility.FromJson<LicenseInfo>(json);
            }
            catch (Exception e)
            {
                Debug.LogError($"[NeshamaLicense] Failed to parse license JSON: {e.Message}");
                return new LicenseInfo();
            }
        }

        /// <summary>
        /// Serialize to JSON for local caching.
        /// </summary>
        public string ToJson()
        {
            return JsonUtility.ToJson(this);
        }
    }

    /// <summary>
    /// License Manager — handles license validation, offline grace period,
    /// region isolation, and feature gating for the Neshama SDK.
    /// 
    /// Region Isolation:
    ///   The SDK automatically detects its region from the configured API URL:
    ///   - api.neshama.cn  → China region
    ///   - api.neshama.pw  → Global region
    ///   License keys with mismatched regions are rejected with a clear error.
    /// 
    /// Usage:
    ///   var info = await LicenseManager.InitializeAsync();
    ///   if (LicenseManager.HasFeature("social_engine")) { ... }
    ///   int maxNpcs = LicenseManager.GetMaxNPCs();
    /// </summary>
    public static class LicenseManager
    {
        // ── Constants ──────────────────────────────────────────────────────────

        private const string LICENSE_PREFS_KEY = "nsh_license_key";
        private const string LICENSE_CACHE_KEY = "nsh_license_cache";
        private const string LICENSE_CACHE_TIME_KEY = "nsh_license_cache_time";
        private const string LICENSE_VALIDATED_KEY = "nsh_last_validated";
        private const string LICENSE_REGION_KEY = "nsh_detected_region";
        private const string ENCRYPTION_KEY = "nsh_enc_key_2024";

        private static readonly TimeSpan CACHE_DURATION = TimeSpan.FromMinutes(5);
        private static readonly TimeSpan GRACE_PERIOD = TimeSpan.FromDays(7);

        // Default server URL (overridden by NeshamaConfig)
        private static string _serverUrl = "https://api.neshama.pw";

        // ── State ──────────────────────────────────────────────────────────────

        private static LicenseInfo _currentLicense;
        private static string _machineId;
        private static bool _initialized;
        private static string _detectedRegion;

        /// <summary>Current license info (null if not initialized).</summary>
        public static LicenseInfo CurrentLicense => _currentLicense;

        /// <summary>Whether the license manager has been initialized.</summary>
        public static bool IsInitialized => _initialized;

        /// <summary>Detected region from the server URL ("cn" or "global").</summary>
        public static string DetectedRegion => _detectedRegion ?? DetectRegion();

        // ── Public API ─────────────────────────────────────────────────────────

        /// <summary>
        /// Set the server URL for license validation.
        /// Call this before InitializeAsync if using a custom server.
        /// The URL determines the region:
        ///   - api.neshama.cn  → cn (China)
        ///   - api.neshama.pw  → global
        /// </summary>
        public static void SetServerUrl(string url)
        {
            _serverUrl = url?.TrimEnd('/') ?? "https://api.neshama.pw";
            _detectedRegion = DetectRegion();
            Debug.Log($"[NeshamaLicense] Server URL set to {_serverUrl}, region: {_detectedRegion}");
        }

        /// <summary>
        /// Initialize the license manager on startup.
        /// If online, validates the license with the server.
        /// If offline, uses the cached license + grace period.
        /// </summary>
        public static async Task<LicenseInfo> InitializeAsync()
        {
            string licenseKey = GetStoredLicenseKey();
            
            if (string.IsNullOrEmpty(licenseKey))
            {
                Debug.Log("[NeshamaLicense] No license key stored, using Free tier");
                _currentLicense = CreateFreeLicense();
                _initialized = true;
                return _currentLicense;
            }

            try
            {
                _currentLicense = await ValidateAsync(licenseKey);
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[NeshamaLicense] Online validation failed, checking offline cache: {e.Message}");
                _currentLicense = GetOfflineLicense(licenseKey);
            }

            _initialized = true;
            return _currentLicense;
        }

        /// <summary>
        /// Validate a license key with the server.
        /// On success, caches the result locally for offline grace period.
        /// The server automatically detects the region from the request Host header.
        /// </summary>
        public static async Task<LicenseInfo> ValidateAsync(string licenseKey)
        {
            string machineId = GetMachineId();
            string url = $"{_serverUrl}/api/license/validate";

            var requestBody = new LicenseRequestBody
            {
                license_key = licenseKey,
                machine_id = machineId,
            };

            string jsonBody = JsonUtility.ToJson(requestBody);

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.timeout = 10;

                var tcs = new TaskCompletionSource<UnityWebRequest>();

                var operation = request.SendWebRequest();
                operation.completed += _ => tcs.SetResult(request);

                await tcs.Task;

                if (request.result == UnityWebRequest.Result.Success)
                {
                    var info = LicenseInfo.FromJson(request.downloadHandler.text);
                    info.CachedAt = DateTime.UtcNow;

                    // Cache locally
                    CacheLicense(info, licenseKey);
                    StoreLicenseKey(licenseKey);

                    if (!info.RegionMatch)
                    {
                        string msg = info.GetRegionMismatchMessage();
                        Debug.LogError($"[NeshamaLicense] REGION MISMATCH: {msg}");
                    }
                    else if (info.Valid)
                    {
                        Debug.Log($"[NeshamaLicense] Validated: plan={info.Plan}, region={info.Region}, max_npcs={info.MaxNpcs}");
                    }
                    else
                    {
                        Debug.LogWarning($"[NeshamaLicense] Validation failed: {info.Error}");
                    }

                    return info;
                }
                else
                {
                    Debug.LogWarning($"[NeshamaLicense] Validation request failed: {request.error}");
                    throw new Exception($"License validation failed: {request.error}");
                }
            }
        }

        /// <summary>
        /// Activate (bind) a license key to this machine.
        /// Call this once after the user enters their license key.
        /// The server checks that the license region matches the API region.
        /// </summary>
        public static async Task<bool> ActivateAsync(string licenseKey)
        {
            string machineId = GetMachineId();
            string url = $"{_serverUrl}/api/license/activate";

            var requestBody = new LicenseRequestBody
            {
                license_key = licenseKey,
                machine_id = machineId,
            };

            string jsonBody = JsonUtility.ToJson(requestBody);

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.timeout = 10;

                var tcs = new TaskCompletionSource<UnityWebRequest>();

                var operation = request.SendWebRequest();
                operation.completed += _ => tcs.SetResult(request);

                await tcs.Task;

                if (request.result == UnityWebRequest.Result.Success)
                {
                    var response = JsonUtility.FromJson<ActivateResponseData>(request.downloadHandler.text);
                    if (response.success)
                    {
                        StoreLicenseKey(licenseKey);
                        Debug.Log("[NeshamaLicense] License activated successfully");
                        return true;
                    }

                    // Check for region mismatch in the error message
                    if (response.message != null && response.message.Contains("region mismatch"))
                    {
                        Debug.LogError($"[NeshamaLicense] REGION MISMATCH: {response.message}");
                    }
                    else
                    {
                        Debug.LogWarning($"[NeshamaLicense] Activation failed: {response.message}");
                    }
                    return false;
                }
                else
                {
                    Debug.LogError($"[NeshamaLicense] Activation request failed: {request.error}");
                    return false;
                }
            }
        }

        /// <summary>
        /// Deactivate (unbind) this machine from the current license.
        /// </summary>
        public static async Task<bool> DeactivateAsync()
        {
            string licenseKey = GetStoredLicenseKey();
            if (string.IsNullOrEmpty(licenseKey)) return false;

            string machineId = GetMachineId();
            string url = $"{_serverUrl}/api/license/deactivate";

            var requestBody = new LicenseRequestBody
            {
                license_key = licenseKey,
                machine_id = machineId,
            };

            string jsonBody = JsonUtility.ToJson(requestBody);

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.timeout = 10;

                var tcs = new TaskCompletionSource<UnityWebRequest>();

                var operation = request.SendWebRequest();
                operation.completed += _ => tcs.SetResult(request);

                await tcs.Task;

                if (request.result == UnityWebRequest.Result.Success)
                {
                    var response = JsonUtility.FromJson<ActivateResponseData>(request.downloadHandler.text);
                    if (response.success)
                    {
                        ClearStoredLicense();
                        _currentLicense = CreateFreeLicense();
                        Debug.Log("[NeshamaLicense] License deactivated");
                        return true;
                    }
                    return false;
                }
                return false;
            }
        }

        /// <summary>
        /// Check if a feature is available in the current license.
        /// </summary>
        public static bool HasFeature(string featureName)
        {
            if (_currentLicense == null)
            {
                Debug.LogWarning("[NeshamaLicense] License not initialized, call InitializeAsync first");
                return false;
            }
            return _currentLicense.HasFeature(featureName);
        }

        /// <summary>
        /// Get the maximum number of NPCs allowed by the current license.
        /// </summary>
        public static int GetMaxNPCs()
        {
            if (_currentLicense == null) return 3;
            return _currentLicense.MaxNpcs;
        }

        /// <summary>
        /// Get the current plan name.
        /// </summary>
        public static string GetCurrentPlan()
        {
            if (_currentLicense == null) return "free";
            return _currentLicense.Plan;
        }

        /// <summary>
        /// Get the machine fingerprint for this device.
        /// CPU ID + GPU ID + MAC address → SHA256
        /// </summary>
        public static string GetMachineId()
        {
            if (!string.IsNullOrEmpty(_machineId)) return _machineId;

            string cpuId = SystemInfo.processorType + "_" + SystemInfo.processorCount;
            string gpuId = SystemInfo.graphicsDeviceName + "_" + SystemInfo.graphicsDeviceID;
            string macAddr = GetMacAddress();

            string raw = $"{cpuId}|{gpuId}|{macAddr}";
            _machineId = ComputeSHA256(raw);
            return _machineId;
        }

        // ── Region Detection ───────────────────────────────────────────────────

        /// <summary>
        /// Detect the region from the configured server URL.
        ///   - Contains "neshama.cn" → cn (China)
        ///   - Contains "neshama.pw" or other → global
        /// </summary>
        private static string DetectRegion()
        {
            if (_serverUrl.Contains("neshama.cn"))
            {
                return "cn";
            }
            return "global";
        }

        /// <summary>
        /// Get a display-friendly region name.
        /// </summary>
        public static string GetRegionDisplayName(string regionCode)
        {
            switch (regionCode)
            {
                case "cn": return "China (中国区)";
                case "global": return "Global (国际区)";
                default: return regionCode;
            }
        }

        // ── Offline Grace Period ───────────────────────────────────────────────

        /// <summary>
        /// Get a license from offline cache with grace period checking.
        /// </summary>
        private static LicenseInfo GetOfflineLicense(string licenseKey)
        {
            LicenseInfo cached = LoadCachedLicense();
            if (cached == null)
            {
                Debug.LogWarning("[NeshamaLicense] No cached license, falling back to Free tier");
                return CreateFreeLicense();
            }

            // Check if cache is recent enough
            string validatedStr = PlayerPrefs.GetString(LICENSE_VALIDATED_KEY, "");
            if (!string.IsNullOrEmpty(validatedStr))
            {
                if (DateTime.TryParse(validatedStr, null, System.Globalization.DateTimeStyles.RoundtripKind, out DateTime lastValidated))
                {
                    TimeSpan sinceValidation = DateTime.UtcNow - lastValidated;
                    if (sinceValidation <= GRACE_PERIOD)
                    {
                        Debug.Log($"[NeshamaLicense] Offline grace period: {sinceValidation.Days}d since last validation");
                        cached.Valid = true;
                        cached.RegionMatch = true; // Trust cached result within grace period
                        return cached;
                    }
                    else
                    {
                        Debug.LogWarning($"[NeshamaLicense] Grace period exceeded ({sinceValidation.Days}d), downgrading to Free");
                        return CreateGracePeriodFreeLicense(lastValidated);
                    }
                }
            }

            // No validation timestamp — check cache time
            if (cached.CachedAt != default)
            {
                TimeSpan sinceCache = DateTime.UtcNow - cached.CachedAt;
                if (sinceCache <= GRACE_PERIOD)
                {
                    Debug.Log("[NeshamaLicense] Using cached license within grace period");
                    cached.Valid = true;
                    cached.RegionMatch = true;
                    return cached;
                }
            }

            Debug.LogWarning("[NeshamaLicense] Grace period expired, using Free tier");
            return CreateFreeLicense();
        }

        /// <summary>
        /// Create a Free-tier license with a grace_until timestamp.
        /// </summary>
        private static LicenseInfo CreateGracePeriodFreeLicense(DateTime lastValidated)
        {
            DateTime graceEnd = lastValidated + GRACE_PERIOD;
            return new LicenseInfo
            {
                Valid = false,
                Plan = "free",
                MaxNpcs = 3,
                Features = new List<string> { "basic_emotion", "ocean_personality", "l0_memory" },
                ExpiresAt = "",
                Region = DetectedRegion,
                RegionMatch = true,
                GraceUntil = graceEnd.ToString("o"),
                LastValidatedAt = lastValidated.ToString("o"),
            };
        }

        /// <summary>
        /// Create a default Free-tier license.
        /// </summary>
        private static LicenseInfo CreateFreeLicense()
        {
            return new LicenseInfo
            {
                Valid = false,
                Plan = "free",
                MaxNpcs = 3,
                Features = new List<string> { "basic_emotion", "ocean_personality", "l0_memory" },
                ExpiresAt = "",
                Region = DetectedRegion,
                RegionMatch = true,
                GraceUntil = null,
                LastValidatedAt = DateTime.UtcNow.ToString("o"),
            };
        }

        // ── Local Storage (Encrypted PlayerPrefs) ──────────────────────────────

        private static void StoreLicenseKey(string key)
        {
            string encrypted = SimpleEncrypt(key);
            PlayerPrefs.SetString(LICENSE_PREFS_KEY, encrypted);
            PlayerPrefs.SetString(LICENSE_REGION_KEY, DetectedRegion);
            PlayerPrefs.Save();
        }

        private static string GetStoredLicenseKey()
        {
            string encrypted = PlayerPrefs.GetString(LICENSE_PREFS_KEY, "");
            if (string.IsNullOrEmpty(encrypted)) return "";
            return SimpleDecrypt(encrypted);
        }

        private static void ClearStoredLicense()
        {
            PlayerPrefs.DeleteKey(LICENSE_PREFS_KEY);
            PlayerPrefs.DeleteKey(LICENSE_CACHE_KEY);
            PlayerPrefs.DeleteKey(LICENSE_CACHE_TIME_KEY);
            PlayerPrefs.DeleteKey(LICENSE_VALIDATED_KEY);
            PlayerPrefs.DeleteKey(LICENSE_REGION_KEY);
            PlayerPrefs.Save();
        }

        private static void CacheLicense(LicenseInfo info, string licenseKey)
        {
            string json = info.ToJson();
            string encrypted = SimpleEncrypt(json);
            PlayerPrefs.SetString(LICENSE_CACHE_KEY, encrypted);
            PlayerPrefs.SetString(LICENSE_CACHE_TIME_KEY, DateTime.UtcNow.ToString("o"));
            PlayerPrefs.SetString(LICENSE_VALIDATED_KEY, DateTime.UtcNow.ToString("o"));
            PlayerPrefs.SetString(LICENSE_REGION_KEY, DetectedRegion);
            PlayerPrefs.Save();
        }

        private static LicenseInfo LoadCachedLicense()
        {
            string encrypted = PlayerPrefs.GetString(LICENSE_CACHE_KEY, "");
            if (string.IsNullOrEmpty(encrypted)) return null;

            string json = SimpleDecrypt(encrypted);
            if (string.IsNullOrEmpty(json)) return null;

            return LicenseInfo.FromJson(json);
        }

        // ── Simple XOR Encryption ──────────────────────────────────────────────
        // Not cryptographically secure, but prevents casual inspection of
        // PlayerPrefs. Production should use platform-specific keychain.

        private static string SimpleEncrypt(string plainText)
        {
            if (string.IsNullOrEmpty(plainText)) return "";
            byte[] keyBytes = Encoding.UTF8.GetBytes(ENCRYPTION_KEY);
            byte[] textBytes = Encoding.UTF8.GetBytes(plainText);
            byte[] result = new byte[textBytes.Length];

            for (int i = 0; i < textBytes.Length; i++)
            {
                result[i] = (byte)(textBytes[i] ^ keyBytes[i % keyBytes.Length]);
            }

            return Convert.ToBase64String(result);
        }

        private static string SimpleDecrypt(string cipherText)
        {
            if (string.IsNullOrEmpty(cipherText)) return "";
            try
            {
                byte[] keyBytes = Encoding.UTF8.GetBytes(ENCRYPTION_KEY);
                byte[] cipherBytes = Convert.FromBase64String(cipherText);
                byte[] result = new byte[cipherBytes.Length];

                for (int i = 0; i < cipherBytes.Length; i++)
                {
                    result[i] = (byte)(cipherBytes[i] ^ keyBytes[i % keyBytes.Length]);
                }

                return Encoding.UTF8.GetString(result);
            }
            catch
            {
                return "";
            }
        }

        // ── Utility ────────────────────────────────────────────────────────────

        private static string ComputeSHA256(string input)
        {
            using (var sha256 = System.Security.Cryptography.SHA256.Create())
            {
                byte[] hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
                var sb = new StringBuilder(64);
                foreach (byte b in hash)
                {
                    sb.Append(b.ToString("x2"));
                }
                return sb.ToString();
            }
        }

        private static string GetMacAddress()
        {
            // Unity doesn't expose MAC directly; use deviceUniqueIdentifier as fallback
            return SystemInfo.deviceUniqueIdentifier;
        }

        // ── Internal Request/Response Types ────────────────────────────────────

        [Serializable]
        private class LicenseRequestBody
        {
            public string license_key;
            public string machine_id;
        }

        [Serializable]
        private class ActivateResponseData
        {
            public bool success;
            public string message;
            public string region;
        }
    }
}
