using System;
using System.Collections.Generic;

namespace Neshama.SoulEngine.Emotion
{
    /// <summary>
    /// Static event-to-emotion mapping tables. Ported from Python game_event.py EVENT_EMOTION_MAPPINGS.
    /// </summary>
    public static class EventMappings
    {
        /// <summary>
        /// Maps game event type to emotion deltas. Each entry: (emotionName, baseDelta).
        /// </summary>
        public static readonly Dictionary<GameEventType, List<(EmotionType emotion, float baseDelta)>> EmotionMappings =
            new Dictionary<GameEventType, List<(EmotionType, float)>>
        {
            { GameEventType.PlayerAttacked, new List<(EmotionType, float)>
                { (EmotionType.Anger, 0.3f), (EmotionType.Fear, 0.2f) }
            },
            { GameEventType.PlayerHelped, new List<(EmotionType, float)>
                { (EmotionType.Trust, 0.4f), (EmotionType.Joy, 0.3f) }
            },
            { GameEventType.ItemReceived, new List<(EmotionType, float)>
                { (EmotionType.Joy, 0.3f), (EmotionType.Surprise, 0.2f) }
            },
            { GameEventType.ItemLost, new List<(EmotionType, float)>
                { (EmotionType.Sadness, 0.3f), (EmotionType.Anger, 0.2f) }
            },
            { GameEventType.QuestCompleted, new List<(EmotionType, float)>
                { (EmotionType.Joy, 0.4f), (EmotionType.Anticipation, 0.2f) }
                // Note: "pride" is a composite, handled by CompositeEmotion
            },
            { GameEventType.QuestFailed, new List<(EmotionType, float)>
                { (EmotionType.Sadness, 0.3f), (EmotionType.Anger, 0.2f), (EmotionType.Fear, 0.15f) }
            },
            { GameEventType.NpcInsulted, new List<(EmotionType, float)>
                { (EmotionType.Anger, 0.4f), (EmotionType.Sadness, 0.2f), (EmotionType.Disgust, 0.2f) }
            },
            { GameEventType.NpcComplimented, new List<(EmotionType, float)>
                { (EmotionType.Joy, 0.3f), (EmotionType.Trust, 0.3f), (EmotionType.Surprise, 0.1f) }
            },
            { GameEventType.EnvironmentChanged, new List<(EmotionType, float)>
                { (EmotionType.Fear, 0.2f), (EmotionType.Surprise, 0.25f), (EmotionType.Anticipation, 0.15f) }
            },
            { GameEventType.RelationshipChanged, new List<(EmotionType, float)>
                { (EmotionType.Trust, 0.3f), (EmotionType.Sadness, 0.2f) }
            },
            { GameEventType.TimePassed, new List<(EmotionType, float)>
                { (EmotionType.Sadness, 0.05f) }
            },
            { GameEventType.CombatStarted, new List<(EmotionType, float)>
                { (EmotionType.Fear, 0.35f), (EmotionType.Anger, 0.25f), (EmotionType.Surprise, 0.15f) }
            },
            { GameEventType.CombatEnded, new List<(EmotionType, float)>
                { (EmotionType.Joy, 0.2f), (EmotionType.Fear, 0.1f), (EmotionType.Sadness, 0.1f) }
            },
            { GameEventType.DeathWitnessed, new List<(EmotionType, float)>
                { (EmotionType.Sadness, 0.4f), (EmotionType.Fear, 0.3f), (EmotionType.Surprise, 0.2f) }
            },
            { GameEventType.GiftGiven, new List<(EmotionType, float)>
                { (EmotionType.Joy, 0.35f), (EmotionType.Trust, 0.35f), (EmotionType.Surprise, 0.15f) }
            },
        };

        /// <summary>
        /// OCEAN personality modifiers per event type.
        /// Format: (traitName, threshold, multiplier). If traitValue >= threshold, apply multiplier.
        /// Ported from Python PERSONALITY_MODIFIERS.
        /// </summary>
        public static readonly Dictionary<GameEventType, List<(string trait, float threshold, float multiplier)>> PersonalityModifiers =
            new Dictionary<GameEventType, List<(string, float, float)>>
        {
            { GameEventType.PlayerHelped, new List<(string, float, float)>
                { ("extraversion", 0.7f, 1.3f), ("agreeableness", 0.7f, 1.2f) }
            },
            { GameEventType.NpcInsulted, new List<(string, float, float)>
                { ("neuroticism", 0.7f, 1.5f), ("agreeableness", 0.7f, 0.5f) }
            },
            { GameEventType.QuestCompleted, new List<(string, float, float)>
                { ("extraversion", 0.6f, 1.2f), ("conscientiousness", 0.6f, 1.3f) }
            },
            { GameEventType.DeathWitnessed, new List<(string, float, float)>
                { ("neuroticism", 0.7f, 1.4f), ("agreeableness", 0.6f, 0.6f) }
            },
        };

        /// <summary>
        /// Positive emotions used for grudge factor reduction.
        /// Ported from Python POSITIVE_EMOTIONS set.
        /// </summary>
        public static readonly HashSet<EmotionType> PositiveEmotions = new HashSet<EmotionType>
        {
            EmotionType.Joy, EmotionType.Trust
        };

        /// <summary>
        /// Positive emotion names used for grudge factor reduction (matches Python).
        /// </summary>
        public static readonly HashSet<string> PositiveEmotionNames = new HashSet<string>
        {
            "joy", "trust", "gratitude", "love", "relief", "delight", "optimism", "pride"
        };

        /// <summary>
        /// Relationship grudge map. Negative relationships reduce positive emotion effects.
        /// Ported from Python RELATIONSHIP_GRUDGE_MAP.
        /// </summary>
        public static readonly Dictionary<string, float> RelationshipGrudgeMap =
            new Dictionary<string, float>(StringComparer.OrdinalIgnoreCase)
        {
            { "hostile", 0.5f },
            { "dislikes", 0.4f },
            { "enemy", 0.6f },
            { "rival", 0.3f },
            { "suspicious", 0.2f },
            { "neutral", 0.0f },
            { "friendly", 0.0f },
            { "likes", 0.0f },
            { "allied", 0.0f },
        };

        /// <summary>
        /// Get grudge factor for a relationship type. Returns 0 if not found.
        /// </summary>
        public static float GetGrudgeFactor(string relationshipType)
        {
            if (string.IsNullOrEmpty(relationshipType)) return 0f;
            float factor;
            return RelationshipGrudgeMap.TryGetValue(relationshipType.ToLower(), out factor) ? factor : 0f;
        }
    }
}
