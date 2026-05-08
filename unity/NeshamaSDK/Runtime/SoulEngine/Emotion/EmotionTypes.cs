using System;
using System.Collections.Generic;

namespace Neshama.SoulEngine.Emotion
{
    /// <summary>
    /// Base emotion types. Ported from Python BaseEmotion enum.
    /// 8 primary emotions + Neutral fallback.
    /// </summary>
    public enum EmotionType
    {
        Joy = 0,
        Sadness,
        Anger,
        Fear,
        Surprise,
        Disgust,
        Trust,
        Anticipation,
        Desire,
        Neutral
    }

    /// <summary>
    /// Extension methods for EmotionType.
    /// Provides name conversion and base emotion enumeration.
    /// </summary>
    public static class EmotionTypeExtensions
    {
        /// <summary>
        /// All base emotions (excluding Neutral).
        /// Used for iteration in decay and other batch operations.
        /// </summary>
        public static readonly EmotionType[] BaseEmotions = new EmotionType[]
        {
            EmotionType.Joy,
            EmotionType.Sadness,
            EmotionType.Anger,
            EmotionType.Fear,
            EmotionType.Surprise,
            EmotionType.Disgust,
            EmotionType.Trust,
            EmotionType.Anticipation,
            EmotionType.Desire,
        };

        /// <summary>
        /// Convert EmotionType to lowercase string name.
        /// Matches Python BaseEmotion.value format (e.g. "joy", "anger").
        /// </summary>
        public static string ToName(this EmotionType type)
        {
            switch (type)
            {
                case EmotionType.Joy: return "joy";
                case EmotionType.Sadness: return "sadness";
                case EmotionType.Anger: return "anger";
                case EmotionType.Fear: return "fear";
                case EmotionType.Surprise: return "surprise";
                case EmotionType.Disgust: return "disgust";
                case EmotionType.Trust: return "trust";
                case EmotionType.Anticipation: return "anticipation";
                case EmotionType.Desire: return "desire";
                case EmotionType.Neutral: return "neutral";
                default: return "unknown";
            }
        }

        /// <summary>
        /// Parse a string name to EmotionType. Case-insensitive.
        /// </summary>
        public static EmotionType FromName(string name)
        {
            if (string.IsNullOrEmpty(name)) return EmotionType.Neutral;
            switch (name.ToLower())
            {
                case "joy": return EmotionType.Joy;
                case "sadness": return EmotionType.Sadness;
                case "anger": return EmotionType.Anger;
                case "fear": return EmotionType.Fear;
                case "surprise": return EmotionType.Surprise;
                case "disgust": return EmotionType.Disgust;
                case "trust": return EmotionType.Trust;
                case "anticipation": return EmotionType.Anticipation;
                case "desire": return EmotionType.Desire;
                default: return EmotionType.Neutral;
            }
        }
    }

    /// <summary>
    /// Response tone options for NPC dialogue hints.
    /// Ported from Python fast_path.py ResponseTone enum.
    /// </summary>
    public enum ResponseTone
    {
        Friendly,
        Hostile,
        Nervous,
        Joyful,
        Sad,
        Angry,
        Fearful,
        Surprised,
        Trusting,
        Neutral,
        Proud,
        Grateful
    }

    /// <summary>
    /// Urgency level for response hints.
    /// </summary>
    public enum Urgency
    {
        Low,
        Medium,
        High
    }

    /// <summary>
    /// Action suggestion types for NPC behavior.
    /// </summary>
    public enum SuggestedAction
    {
        DialogueFriendly,
        DialogueHostile,
        DialogueCautious,
        QuestOffer,
        QuestRefuse,
        ShareInfo,
        WithholdInfo,
        Flee,
        Attack,
        GiveGift,
        ReceiveGift,
        Consolation,
        Celebration,
        Warning
    }

    /// <summary>
    /// Game event types that trigger emotion changes.
    /// Ported from Python game_event.py GameEventType enum.
    /// </summary>
    public enum GameEventType
    {
        PlayerAttacked = 0,
        PlayerHelped,
        ItemReceived,
        ItemLost,
        QuestCompleted,
        QuestFailed,
        NpcInsulted,
        NpcComplimented,
        EnvironmentChanged,
        RelationshipChanged,
        TimePassed,
        CombatStarted,
        CombatEnded,
        DeathWitnessed,
        GiftGiven
    }

    /// <summary>
    /// Emotion state as a mutable struct for performance.
    /// All 9 base emotions with values in [0, 1].
    /// </summary>
    [Serializable]
    public struct EmotionState
    {
        public float joy;
        public float sadness;
        public float anger;
        public float fear;
        public float surprise;
        public float disgust;
        public float trust;
        public float anticipation;
        public float desire;

        public EmotionState Clone()
        {
            return new EmotionState
            {
                joy = joy, sadness = sadness, anger = anger, fear = fear,
                surprise = surprise, disgust = disgust, trust = trust, anticipation = anticipation,
                desire = desire
            };
        }

        /// <summary>
        /// Get emotion value by EmotionType.
        /// </summary>
        public float GetValue(EmotionType type)
        {
            switch (type)
            {
                case EmotionType.Joy: return joy;
                case EmotionType.Sadness: return sadness;
                case EmotionType.Anger: return anger;
                case EmotionType.Fear: return fear;
                case EmotionType.Surprise: return surprise;
                case EmotionType.Disgust: return disgust;
                case EmotionType.Trust: return trust;
                case EmotionType.Anticipation: return anticipation;
                case EmotionType.Desire: return desire;
                default: return 0f;
            }
        }

        /// <summary>
        /// Set emotion value by EmotionType, clamped to [0,1].
        /// </summary>
        public void SetValue(EmotionType type, float value)
        {
            value = Clamp01(value);
            switch (type)
            {
                case EmotionType.Joy: joy = value; break;
                case EmotionType.Sadness: sadness = value; break;
                case EmotionType.Anger: anger = value; break;
                case EmotionType.Fear: fear = value; break;
                case EmotionType.Surprise: surprise = value; break;
                case EmotionType.Disgust: disgust = value; break;
                case EmotionType.Trust: trust = value; break;
                case EmotionType.Anticipation: anticipation = value; break;
                case EmotionType.Desire: desire = value; break;
            }
        }

        /// <summary>
        /// Adjust emotion by delta, clamped to [0,1].
        /// </summary>
        public void AdjustValue(EmotionType type, float delta)
        {
            SetValue(type, GetValue(type) + delta);
        }

        /// <summary>
        /// Get the dominant emotion type and its value.
        /// </summary>
        public void GetDominant(out EmotionType dominantType, out float dominantValue)
        {
            float maxVal = -1f;
            EmotionType dom = EmotionType.Neutral;

            Check(ref maxVal, ref dom, EmotionType.Joy, joy);
            Check(ref maxVal, ref dom, EmotionType.Sadness, sadness);
            Check(ref maxVal, ref dom, EmotionType.Anger, anger);
            Check(ref maxVal, ref dom, EmotionType.Fear, fear);
            Check(ref maxVal, ref dom, EmotionType.Surprise, surprise);
            Check(ref maxVal, ref dom, EmotionType.Disgust, disgust);
            Check(ref maxVal, ref dom, EmotionType.Trust, trust);
            Check(ref maxVal, ref dom, EmotionType.Anticipation, anticipation);
            Check(ref maxVal, ref dom, EmotionType.Desire, desire);

            dominantType = dom;
            dominantValue = maxVal < 0f ? 0f : maxVal;
        }

        /// <summary>
        /// Convert to dictionary of emotion name → value.
        /// </summary>
        public Dictionary<string, float> ToDictionary()
        {
            var dict = new Dictionary<string, float>(8);
            if (joy > 0.001f) dict["joy"] = joy;
            if (sadness > 0.001f) dict["sadness"] = sadness;
            if (anger > 0.001f) dict["anger"] = anger;
            if (fear > 0.001f) dict["fear"] = fear;
            if (surprise > 0.001f) dict["surprise"] = surprise;
            if (disgust > 0.001f) dict["disgust"] = disgust;
            if (trust > 0.001f) dict["trust"] = trust;
            if (anticipation > 0.001f) dict["anticipation"] = anticipation;
            if (desire > 0.001f) dict["desire"] = desire;
            return dict;
        }

        /// <summary>
        /// Clear all emotions to 0.
        /// </summary>
        public void Clear()
        {
            joy = sadness = anger = fear = surprise = disgust = trust = anticipation = desire = 0f;
        }

        private void Check(ref float maxVal, ref EmotionType dom, EmotionType type, float val)
        {
            if (val > maxVal)
            {
                maxVal = val;
                dom = type;
            }
        }

        private static float Clamp01(float v) => v < 0f ? 0f : (v > 1f ? 1f : v);
    }
}
