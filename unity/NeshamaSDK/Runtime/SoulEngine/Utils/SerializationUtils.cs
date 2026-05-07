using System;
using System.Collections.Generic;
using UnityEngine;

namespace Neshama.SoulEngine.Utils
{
    /// <summary>
    /// Serialization utilities for save/load support.
    /// Uses Unity's JsonUtility for [Serializable] types.
    /// </summary>
    public static class SerializationUtils
    {
        /// <summary>
        /// Serialize a [Serializable] object to JSON.
        /// </summary>
        public static string ToJson(object obj, bool prettyPrint = false)
        {
            return JsonUtility.ToJson(obj, prettyPrint);
        }

        /// <summary>
        /// Deserialize JSON to a [Serializable] object.
        /// </summary>
        public static T FromJson<T>(string json) where T : class
        {
            return JsonUtility.FromJson<T>(json);
        }

        /// <summary>
        /// Serialize a Dictionary&lt;string, float&gt; to JSON via wrapper.
        /// JsonUtility doesn't support Dictionary directly.
        /// </summary>
        public static string DictToJson(Dictionary<string, float> dict)
        {
            var wrapper = new FloatDictWrapper { items = new List<FloatKV>() };
            foreach (var kv in dict)
            {
                wrapper.items.Add(new FloatKV { key = kv.Key, value = kv.Value });
            }
            return JsonUtility.ToJson(wrapper);
        }

        /// <summary>
        /// Deserialize JSON to Dictionary&lt;string, float&gt;.
        /// </summary>
        public static Dictionary<string, float> DictFromJson(string json)
        {
            var dict = new Dictionary<string, float>();
            if (string.IsNullOrEmpty(json)) return dict;
            var wrapper = JsonUtility.FromJson<FloatDictWrapper>(json);
            if (wrapper?.items == null) return dict;
            foreach (var kv in wrapper.items)
            {
                dict[kv.key] = kv.value;
            }
            return dict;
        }

        /// <summary>
        /// Serialize a Dictionary&lt;string, string&gt; to JSON via wrapper.
        /// </summary>
        public static string StringDictToJson(Dictionary<string, string> dict)
        {
            var wrapper = new StringDictWrapper { items = new List<StringKV>() };
            foreach (var kv in dict)
            {
                wrapper.items.Add(new StringKV { key = kv.Key, value = kv.Value });
            }
            return JsonUtility.ToJson(wrapper);
        }

        /// <summary>
        /// Deserialize JSON to Dictionary&lt;string, string&gt;.
        /// </summary>
        public static Dictionary<string, string> StringDictFromJson(string json)
        {
            var dict = new Dictionary<string, string>();
            if (string.IsNullOrEmpty(json)) return dict;
            var wrapper = JsonUtility.FromJson<StringDictWrapper>(json);
            if (wrapper?.items == null) return dict;
            foreach (var kv in wrapper.items)
            {
                dict[kv.key] = kv.value;
            }
            return dict;
        }

        // --- Wrapper types for JsonUtility (which doesn't support Dictionary) ---

        [Serializable]
        private class FloatDictWrapper
        {
            public List<FloatKV> items;
        }

        [Serializable]
        private class FloatKV
        {
            public string key;
            public float value;
        }

        [Serializable]
        private class StringDictWrapper
        {
            public List<StringKV> items;
        }

        [Serializable]
        private class StringKV
        {
            public string key;
            public string value;
        }
    }
}
