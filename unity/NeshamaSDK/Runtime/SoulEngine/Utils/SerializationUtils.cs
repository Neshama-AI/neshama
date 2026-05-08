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

        // --- EntityRelation serialization ---

        /// <summary>
        /// Serialize a list of EntityRelation objects to JSON.
        /// JsonUtility can serialize EntityRelation directly (no Dictionary fields).
        /// </summary>
        public static string RelationListToJson(List<Memory.EntityRelation> relations)
        {
            var wrapper = new EntityRelationListWrapper { items = relations ?? new List<Memory.EntityRelation>() };
            return JsonUtility.ToJson(wrapper);
        }

        /// <summary>
        /// Deserialize JSON to a list of EntityRelation objects.
        /// </summary>
        public static List<Memory.EntityRelation> RelationListFromJson(string json)
        {
            if (string.IsNullOrEmpty(json)) return new List<Memory.EntityRelation>();
            var wrapper = JsonUtility.FromJson<EntityRelationListWrapper>(json);
            return wrapper?.items ?? new List<Memory.EntityRelation>();
        }

        // --- EntityMemory serialization ---

        /// <summary>
        /// Serialize a list of EntityMemory objects to JSON.
        /// Converts emotionalContext Dictionary to JSON string for JsonUtility compat.
        /// </summary>
        public static string MemoryListToJson(List<Memory.EntityMemory> memories)
        {
            var serializable = new List<SerializableEntityMemory>();
            if (memories != null)
            {
                foreach (var mem in memories)
                {
                    serializable.Add(new SerializableEntityMemory
                    {
                        memoryId = mem.memoryId,
                        entityId = mem.entityId,
                        entityName = mem.entityName,
                        eventType = mem.eventType,
                        description = mem.description,
                        timestamp = mem.timestamp,
                        emotionalContextJson = DictToJson(mem.emotionalContext),
                        trustAtTime = mem.trustAtTime,
                        importance = (int)mem.importance,
                    });
                }
            }
            var wrapper = new EntityMemoryListWrapper { items = serializable };
            return JsonUtility.ToJson(wrapper);
        }

        /// <summary>
        /// Deserialize JSON to a list of EntityMemory objects.
        /// Restores emotionalContext Dictionary from JSON string.
        /// </summary>
        public static List<Memory.EntityMemory> MemoryListFromJson(string json)
        {
            var result = new List<Memory.EntityMemory>();
            if (string.IsNullOrEmpty(json)) return result;
            var wrapper = JsonUtility.FromJson<EntityMemoryListWrapper>(json);
            if (wrapper?.items == null) return result;

            foreach (var sm in wrapper.items)
            {
                result.Add(new Memory.EntityMemory
                {
                    memoryId = sm.memoryId,
                    entityId = sm.entityId,
                    entityName = sm.entityName,
                    eventType = sm.eventType,
                    description = sm.description,
                    timestamp = sm.timestamp,
                    emotionalContext = DictFromJson(sm.emotionalContextJson),
                    trustAtTime = sm.trustAtTime,
                    importance = (Memory.MemoryImportance)sm.importance,
                });
            }
            return result;
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

        [Serializable]
        private class EntityRelationListWrapper
        {
            public List<Memory.EntityRelation> items;
        }

        [Serializable]
        private class SerializableEntityMemory
        {
            public string memoryId;
            public string entityId;
            public string entityName;
            public string eventType;
            public string description;
            public float timestamp;
            public string emotionalContextJson; // Dictionary serialized as JSON string
            public float trustAtTime;
            public int importance;
        }

        [Serializable]
        private class EntityMemoryListWrapper
        {
            public List<SerializableEntityMemory> items;
        }
    }
}
