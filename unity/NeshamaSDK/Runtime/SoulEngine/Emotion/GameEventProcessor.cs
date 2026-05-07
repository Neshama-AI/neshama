using System;
using System.Collections.Generic;
using Neshama.SoulEngine.Personality;

namespace Neshama.SoulEngine.Emotion
{
    /// <summary>
    /// Game event processor. Maps game events to emotion deltas.
    /// Ported from Python game_event.py GameEventEngine.
    /// 
    /// Handles:
    /// - Event → emotion delta mapping (15 event types)
    /// - Intensity scaling
    /// - OCEAN personality modifiers
    /// - Grudge factor (hostile relationships reduce positive effects)
    /// </summary>
    public static class GameEventProcessor
    {
        /// <summary>
        /// Process a game event and return emotion deltas.
        /// Ported from Python GameEventEngine.process_event().
        /// </summary>
        public static List<EmotionDelta> ProcessEvent(
            GameEventType eventType,
            float intensity,
            OCEANPersonality personality,
            string sourceId = null,
            string relationshipType = null)
        {
            var deltas = new List<EmotionDelta>();
            List<(EmotionType emotion, float baseDelta)> mappings;
            if (!EventMappings.EmotionMappings.TryGetValue(eventType, out mappings))
                return deltas;

            // Calculate grudge factor
            float grudgeFactor = EventMappings.GetGrudgeFactor(relationshipType);

            foreach (var mapping in mappings)
            {
                float scaled = mapping.baseDelta * intensity;

                // Apply personality modifiers
                List<(string trait, float threshold, float multiplier)> modifiers;
                if (EventMappings.PersonalityModifiers.TryGetValue(eventType, out modifiers))
                {
                    foreach (var mod in modifiers)
                    {
                        float traitValue = personality.GetTrait(mod.trait);
                        if (traitValue >= mod.threshold)
                        {
                            // Only modify positive deltas (joy, trust, etc.)
                            if (scaled > 0f)
                                scaled *= mod.multiplier;
                            break; // Only first matching modifier applies
                        }
                    }
                }

                // Apply grudge factor: reduce positive emotion deltas from hostile sources
                if (grudgeFactor > 0f && IsPositiveEmotion(mapping.emotion) && scaled > 0f)
                {
                    float reduction = 1.0f - grudgeFactor;
                    scaled *= reduction;
                }

                // Clamp to valid range
                scaled = Math.Max(-1f, Math.Min(1f, scaled));

                deltas.Add(new EmotionDelta
                {
                    emotion = mapping.emotion,
                    baseDelta = mapping.baseDelta,
                    scaledDelta = (float)Math.Round(scaled, 4),
                    sourceEvent = eventType
                });
            }

            return deltas;
        }

        /// <summary>
        /// Process a chain of events, accumulating deltas.
        /// Ported from Python GameEventEngine.process_chain().
        /// </summary>
        public static EventChainResult ProcessChain(
            List<GameEvent> events,
            string chainId,
            OCEANPersonality personality)
        {
            var emotionSums = new Dictionary<EmotionType, float>();
            var allDeltas = new List<EmotionDelta>();

            foreach (var evt in events)
            {
                var deltas = ProcessEvent(evt.eventType, evt.intensity, personality);
                foreach (var delta in deltas)
                {
                    if (!emotionSums.ContainsKey(delta.emotion))
                        emotionSums[delta.emotion] = 0f;
                    emotionSums[delta.emotion] += delta.scaledDelta;
                }
                allDeltas.AddRange(deltas);
            }

            // Create summed deltas
            var totalDeltas = new List<EmotionDelta>();
            EmotionType dominantEmotion = EmotionType.Neutral;
            float dominantIntensity = 0f;

            foreach (var kv in emotionSums)
            {
                totalDeltas.Add(new EmotionDelta
                {
                    emotion = kv.Key,
                    scaledDelta = (float)Math.Round(kv.Value, 4),
                    sourceEvent = allDeltas.Count > 0 ? allDeltas[0].sourceEvent : GameEventType.TimePassed
                });

                if (Math.Abs(kv.Value) > dominantIntensity)
                {
                    dominantIntensity = Math.Abs(kv.Value);
                    dominantEmotion = kv.Key;
                }
            }

            return new EventChainResult
            {
                chainId = chainId,
                totalDeltas = totalDeltas,
                dominantEmotion = dominantEmotion,
                dominantIntensity = dominantIntensity,
                eventCount = events.Count
            };
        }

        /// <summary>
        /// Check if an emotion is considered "positive" for grudge factor purposes.
        /// </summary>
        private static bool IsPositiveEmotion(EmotionType type)
        {
            return type == EmotionType.Joy || type == EmotionType.Trust;
        }
    }

    // ── Supporting Types ─────────────────────────────────────────────────────────

    /// <summary>
    /// A game event with type and intensity.
    /// </summary>
    public struct GameEvent
    {
        public GameEventType eventType;
        public float intensity;
        public string sourceId;

        public GameEvent(GameEventType type, float intensity = 1.0f, string sourceId = null)
        {
            this.eventType = type;
            this.intensity = Math.Max(0f, Math.Min(1f, intensity));
            this.sourceId = sourceId;
        }
    }

    /// <summary>
    /// Represents an emotion change from an event.
    /// Ported from Python EmotionDelta.
    /// </summary>
    public struct EmotionDelta
    {
        public EmotionType emotion;
        public float baseDelta;
        public float scaledDelta; // Final delta after intensity scaling + modifiers
        public GameEventType sourceEvent;
    }

    /// <summary>
    /// Result of processing an event chain.
    /// Ported from Python EventChainResult.
    /// </summary>
    public struct EventChainResult
    {
        public string chainId;
        public List<EmotionDelta> totalDeltas;
        public EmotionType dominantEmotion;
        public float dominantIntensity;
        public int eventCount;
    }
}
