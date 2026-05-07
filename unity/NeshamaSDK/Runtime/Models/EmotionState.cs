using System;
using System.Collections.Generic;
using UnityEngine;

namespace Neshama.SDK.Models
{
    /// <summary>
    /// 情绪状态数据类
    /// 包含九种基础情绪的强度值、主导情绪和复合情绪
    /// 
    /// 注意：Unity的JsonUtility不支持Dictionary序列化，
    /// 因此emotions字段使用EmotionEntry数组代替。
    /// 在序列化/反序列化时，会自动在数组和Dictionary之间转换。
    /// </summary>
    [Serializable]
    public class EmotionState
    {
        /// <summary>
        /// 情绪条目（用于JSON序列化，替代Dictionary）
        /// </summary>
        [SerializeField]
        public List<EmotionEntry> emotion_list;

        /// <summary>
        /// 主导情绪类型（如"anger"、"joy"等）
        /// </summary>
        [SerializeField]
        public string dominant;

        /// <summary>
        /// 复合情绪描述（如"resentment"、"satisfaction"等）
        /// </summary>
        [SerializeField]
        public string composite;

        // 内部缓存
        private Dictionary<string, float> _emotionsCache;
        private bool _cacheDirty = true;

        /// <summary>
        /// 获取情绪字典（从emotion_list转换）
        /// </summary>
        public Dictionary<string, float> emotions
        {
            get
            {
                if (_cacheDirty || _emotionsCache == null)
                {
                    _emotionsCache = new Dictionary<string, float>();
                    if (emotion_list != null)
                    {
                        foreach (var entry in emotion_list)
                        {
                            _emotionsCache[entry.key] = entry.value;
                        }
                    }
                    _cacheDirty = false;
                }
                return _emotionsCache;
            }
        }

        /// <summary>
        /// 从字典设置情绪值
        /// </summary>
        public void SetEmotionsFromDict(Dictionary<string, float> dict)
        {
            emotion_list = new List<EmotionEntry>();
            if (dict != null)
            {
                foreach (var kvp in dict)
                {
                    emotion_list.Add(new EmotionEntry { key = kvp.Key, value = kvp.Value });
                }
            }
            _cacheDirty = true;
        }

        /// <summary>
        /// 获取指定情绪的强度值
        /// </summary>
        /// <param name="emotionType">情绪类型名称</param>
        /// <returns>情绪强度值，0-1范围</returns>
        public float GetEmotionValue(string emotionType)
        {
            if (emotions != null && emotions.TryGetValue(emotionType, out float value))
            {
                return value;
            }
            return 0f;
        }

        /// <summary>
        /// 获取喜悦情绪强度
        /// </summary>
        public float Joy => GetEmotionValue("joy");

        /// <summary>
        /// 获取悲伤情绪强度
        /// </summary>
        public float Sadness => GetEmotionValue("sadness");

        /// <summary>
        /// 获取愤怒情绪强度
        /// </summary>
        public float Anger => GetEmotionValue("anger");

        /// <summary>
        /// 获取恐惧情绪强度
        /// </summary>
        public float Fear => GetEmotionValue("fear");

        /// <summary>
        /// 获取惊讶情绪强度
        /// </summary>
        public float Surprise => GetEmotionValue("surprise");

        /// <summary>
        /// 获取厌恶情绪强度
        /// </summary>
        public float Disgust => GetEmotionValue("disgust");

        /// <summary>
        /// 获取信任情绪强度
        /// </summary>
        public float Trust => GetEmotionValue("trust");

        /// <summary>
        /// 获取期待情绪强度
        /// </summary>
        public float Anticipation => GetEmotionValue("anticipation");

        /// <summary>
        /// 获取羞愧情绪强度
        /// </summary>
        public float Shame => GetEmotionValue("shame");

        /// <summary>
        /// 获取主导情绪对应的EmotionType枚举
        /// </summary>
        public Enums.EmotionType GetDominantEmotionType()
        {
            if (string.IsNullOrEmpty(dominant)) return Enums.EmotionType.Joy;
            
            try
            {
                return (Enums.EmotionType)Enum.Parse(typeof(Enums.EmotionType), dominant, true);
            }
            catch
            {
                return Enums.EmotionType.Joy;
            }
        }

        /// <summary>
        /// 判断当前是否处于负面情绪状态
        /// </summary>
        public bool IsNegative()
        {
            return Anger > 0.5f || Fear > 0.5f || Sadness > 0.5f || Disgust > 0.5f;
        }

        /// <summary>
        /// 判断当前是否处于正面情绪状态
        /// </summary>
        public bool IsPositive()
        {
            return Joy > 0.5f || Trust > 0.5f;
        }

        /// <summary>
        /// 获取最高情绪强度值
        /// </summary>
        public float GetHighestValue()
        {
            float max = 0f;
            if (emotions != null)
            {
                foreach (var value in emotions.Values)
                {
                    if (value > max) max = value;
                }
            }
            return max;
        }

        public override string ToString()
        {
            return $"EmotionState: dominant={dominant}, composite={composite}, anger={Anger}, joy={Joy}";
        }
    }

    /// <summary>
    /// 情绪条目（用于JsonUtility序列化，替代Dictionary）
    /// </summary>
    [Serializable]
    public class EmotionEntry
    {
        /// <summary>
        /// 情绪类型名称
        /// </summary>
        [SerializeField]
        public string key;

        /// <summary>
        /// 情绪强度值（0-1）
        /// </summary>
        [SerializeField]
        public float value;
    }

    /// <summary>
    /// 情绪状态变化事件的回调参数
    /// </summary>
    public class EmotionChangedEventArgs
    {
        public string NpcId { get; set; }
        public EmotionState OldState { get; set; }
        public EmotionState NewState { get; set; }
        public float ChangeMagnitude { get; set; }
    }
}
