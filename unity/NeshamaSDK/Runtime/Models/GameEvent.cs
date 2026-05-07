using System;
using System.Collections.Generic;
using UnityEngine;

namespace Neshama.SDK.Models
{
    /// <summary>
    /// 游戏事件数据类
    /// 用于描述游戏中发生的各类事件，推送给后端处理
    /// 
    /// 注意：Unity的JsonUtility不支持Dictionary<string, object>序列化，
    /// 因此context字段使用ContextEntry数组代替。
    /// </summary>
    [Serializable]
    public class GameEvent
    {
        /// <summary>
        /// 事件类型（如 player_attacked, npc_complimented 等）
        /// </summary>
        [SerializeField]
        public string event_type;

        /// <summary>
        /// 事件强度，范围0-1
        /// 用于表示事件的严重程度或重要程度
        /// </summary>
        [SerializeField]
        [Range(0f, 1f)]
        public float intensity;

        /// <summary>
        /// 事件上下文条目（用于JSON序列化，替代Dictionary）
        /// </summary>
        [SerializeField]
        public List<ContextEntry> context_entries;

        /// <summary>
        /// 事件发生的时间戳（Unix时间戳）
        /// </summary>
        [SerializeField]
        public long timestamp;

        /// <summary>
        /// 获取上下文字典（从context_entries转换）
        /// </summary>
        public Dictionary<string, object> context
        {
            get
            {
                var dict = new Dictionary<string, object>();
                if (context_entries != null)
                {
                    foreach (var entry in context_entries)
                    {
                        dict[entry.key] = entry.GetValue();
                    }
                }
                return dict;
            }
        }

        /// <summary>
        /// 创建一个新的游戏事件
        /// </summary>
        /// <param name="eventType">事件类型名称</param>
        /// <param name="intensity">事件强度（0-1）</param>
        /// <param name="context">上下文数据</param>
        public GameEvent(string eventType, float intensity = 1f, Dictionary<string, object> context = null)
        {
            this.event_type = eventType;
            this.intensity = Mathf.Clamp01(intensity);
            this.context_entries = ContextEntry.FromDict(context);
            this.timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        }

        /// <summary>
        /// 根据枚举类型创建游戏事件
        /// </summary>
        /// <param name="eventType">事件类型枚举</param>
        /// <param name="intensity">事件强度（0-1）</param>
        /// <param name="context">上下文数据</param>
        public GameEvent(Enums.GameEventType eventType, float intensity = 1f, Dictionary<string, object> context = null)
            : this(eventType.ToString().ToLower(), intensity, context)
        {
        }

        /// <summary>
        /// 添加上下文信息
        /// </summary>
        /// <param name="key">键名</param>
        /// <param name="value">值</param>
        public void AddContext(string key, object value)
        {
            if (context_entries == null)
            {
                context_entries = new List<ContextEntry>();
            }
            context_entries.Add(new ContextEntry { key = key, value_string = value?.ToString() ?? "" });
        }

        /// <summary>
        /// 创建玩家进入事件
        /// </summary>
        public static GameEvent PlayerEntered(string playerName = null)
        {
            var ctx = new Dictionary<string, object>();
            if (!string.IsNullOrEmpty(playerName))
            {
                ctx["player_name"] = playerName;
            }
            return new GameEvent(Enums.GameEventType.player_entered, 0.5f, ctx);
        }

        /// <summary>
        /// 创建玩家攻击事件
        /// </summary>
        public static GameEvent PlayerAttacked(float damage, string weaponName = null)
        {
            var ctx = new Dictionary<string, object>
            {
                { "damage", damage }
            };
            if (!string.IsNullOrEmpty(weaponName))
            {
                ctx["weapon_name"] = weaponName;
            }
            return new GameEvent(Enums.GameEventType.player_attacked, Mathf.Clamp01(damage / 100f), ctx);
        }

        /// <summary>
        /// 创建NPC被赞美事件
        /// </summary>
        public static GameEvent NpcComplimented(string complimentType = "general")
        {
            var ctx = new Dictionary<string, object>
            {
                { "compliment_type", complimentType }
            };
            return new GameEvent(Enums.GameEventType.npc_complimented, 0.7f, ctx);
        }

        /// <summary>
        /// 创建礼物赠送事件
        /// </summary>
        public static GameEvent GiftGiven(string giftName, int value = 1)
        {
            var ctx = new Dictionary<string, object>
            {
                { "gift_name", giftName },
                { "gift_value", value }
            };
            return new GameEvent(Enums.GameEventType.gift_given, Mathf.Clamp01(value / 10f), ctx);
        }

        /// <summary>
        /// 创建任务完成事件
        /// </summary>
        public static GameEvent QuestCompleted(string questName, int reward = 0)
        {
            var ctx = new Dictionary<string, object>
            {
                { "quest_name", questName },
                { "reward", reward }
            };
            return new GameEvent(Enums.GameEventType.quest_completed, 0.8f, ctx);
        }

        public override string ToString()
        {
            return $"GameEvent: {event_type}, intensity={intensity}";
        }
    }

    /// <summary>
    /// 上下文条目（用于JsonUtility序列化，替代Dictionary<string, object>）
    /// </summary>
    [Serializable]
    public class ContextEntry
    {
        [SerializeField]
        public string key;

        [SerializeField]
        public string value_string;

        [SerializeField]
        public float value_number;

        [SerializeField]
        public bool value_is_number;

        /// <summary>
        /// 获取值
        /// </summary>
        public object GetValue()
        {
            return value_is_number ? (object)value_number : value_string;
        }

        /// <summary>
        /// 从Dictionary转换为ContextEntry列表
        /// </summary>
        public static List<ContextEntry> FromDict(Dictionary<string, object> dict)
        {
            var entries = new List<ContextEntry>();
            if (dict != null)
            {
                foreach (var kvp in dict)
                {
                    var entry = new ContextEntry { key = kvp.Key };
                    if (kvp.Value is float f)
                    {
                        entry.value_number = f;
                        entry.value_is_number = true;
                    }
                    else if (kvp.Value is int i)
                    {
                        entry.value_number = i;
                        entry.value_is_number = true;
                    }
                    else if (kvp.Value is double d)
                    {
                        entry.value_number = (float)d;
                        entry.value_is_number = true;
                    }
                    else
                    {
                        entry.value_string = kvp.Value?.ToString() ?? "";
                        entry.value_is_number = false;
                    }
                    entries.Add(entry);
                }
            }
            return entries;
        }
    }

    /// <summary>
    /// 事件发送请求的响应数据类
    /// </summary>
    [Serializable]
    public class EventResponse
    {
        /// <summary>
        /// 事件处理后的情绪状态
        /// </summary>
        [SerializeField]
        public EmotionState emotion_state;

        /// <summary>
        /// 响应提示信息
        /// </summary>
        [SerializeField]
        public ResponseHint response_hint;

        /// <summary>
        /// 事件是否被成功处理
        /// </summary>
        [SerializeField]
        public bool success;

        /// <summary>
        /// 错误信息（如果有）
        /// </summary>
        [SerializeField]
        public string error;
    }

    /// <summary>
    /// 响应提示信息
    /// </summary>
    [Serializable]
    public class ResponseHint
    {
        /// <summary>
        /// 语气（如 "hostile", "friendly", "neutral"）
        /// </summary>
        [SerializeField]
        public string tone;

        /// <summary>
        /// 紧急程度（如 "high", "medium", "low"）
        /// </summary>
        [SerializeField]
        public string urgency;

        /// <summary>
        /// 建议的行为列表
        /// </summary>
        [SerializeField]
        public List<string> suggested_actions;
    }
}
