using System;
using System.Collections.Generic;
using UnityEngine;
using Neshama.SoulEngine.Emotion;
using Neshama.SoulEngine.Personality;
using Neshama.SoulEngine.Behavior;
using Neshama.SoulEngine.Memory;
using Neshama.SoulEngine.Social;
using Neshama.SoulEngine.Story;
using Neshama.SoulEngine.Entity;
using Neshama.SoulEngine.Utils;

namespace Neshama.SoulEngine.Core
{
    /// <summary>
    /// Complete soul state for save/load.
    /// All data needed to serialize/deserialize an NPC's entire soul.
    /// </summary>
    [Serializable]
    public class SoulState
    {
        // Identity
        public string npcId;
        public string npcName;

        // Personality
        public OCEANPersonality personality;

        // Emotions
        public float joy;
        public float sadness;
        public float anger;
        public float fear;
        public float surprise;
        public float disgust;
        public float trust;
        public float anticipation;
        public float desire;

        // Memory (serialized as JSON strings for JsonUtility compat)
        public string relationsJson;
        public string memoriesJson;

        // Game time
        public float gameTime;

        // Interaction count
        public int totalInteractions;

        /// <summary>
        /// Create SoulState from current engine state.
        /// </summary>
        public static SoulState Capture(string npcId, string npcName,
            EmotionEngine emotion, OCEANPersonality personality,
            MemorySystem memory, int totalInteractions)
        {
            var state = new SoulState
            {
                npcId = npcId,
                npcName = npcName,
                personality = personality.Clone(),
                totalInteractions = totalInteractions,
            };

            // Capture emotions
            var emo = emotion.CurrentEmotions;
            state.joy = emo.joy;
            state.sadness = emo.sadness;
            state.anger = emo.anger;
            state.fear = emo.fear;
            state.surprise = emo.surprise;
            state.disgust = emo.disgust;
            state.trust = emo.trust;
            state.anticipation = emo.anticipation;
            state.desire = emo.desire;

            // Memory state captured as JSON
            state.gameTime = memory.GameTime;
            state.relationsJson = SerializationUtils.RelationListToJson(memory.GetAllRelations());
            state.memoriesJson = SerializationUtils.MemoryListToJson(memory.GetAllMemories());

            return state;
        }

        /// <summary>
        /// Restore emotion state from saved state.
        /// </summary>
        public void RestoreEmotions(EmotionEngine engine)
        {
            engine.SetEmotion(EmotionType.Joy, joy);
            engine.SetEmotion(EmotionType.Sadness, sadness);
            engine.SetEmotion(EmotionType.Anger, anger);
            engine.SetEmotion(EmotionType.Fear, fear);
            engine.SetEmotion(EmotionType.Surprise, surprise);
            engine.SetEmotion(EmotionType.Disgust, disgust);
            engine.SetEmotion(EmotionType.Trust, trust);
            engine.SetEmotion(EmotionType.Anticipation, anticipation);
            engine.SetEmotion(EmotionType.Desire, desire);
        }

        /// <summary>
        /// Restore memory state from saved state.
        /// </summary>
        public void RestoreMemory(MemorySystem memory)
        {
            memory.RestoreFromSerialized(relationsJson, memoriesJson);
        }

        /// <summary>
        /// Serialize to JSON.
        /// </summary>
        public string ToJson(bool prettyPrint = false)
        {
            return JsonUtility.ToJson(this, prettyPrint);
        }

        /// <summary>
        /// Deserialize from JSON.
        /// </summary>
        public static SoulState FromJson(string json)
        {
            return JsonUtility.FromJson<SoulState>(json);
        }
    }
}
