using System;
using System.Collections.Generic;
using Neshama.SoulEngine.Personality;
using Neshama.SoulEngine.Utils;

namespace Neshama.SoulEngine.Emotion
{
    /// <summary>
    /// Core emotion engine. Ported from Python composite.py + fast_path.py.
    /// 
    /// Manages 8 base emotions with:
    /// - Exponential decay (half-life model, decays toward 0)
    /// - Conflict resolution for opposing emotion pairs
    /// - Composite emotion synthesis (recipes)
    /// - OCEAN personality modifiers
    /// - Response hint generation
    /// 
    /// BUG FIX NOTES (retained from Python):
    /// - Decay baseline is 0, not current value (0+delta, not 0.5+delta)
    /// - Attack event: anger=0.24 (0.3*0.8), NOT 0.74 (old bug was 0.5+0.24)
    /// </summary>
    public class EmotionEngine
    {
        // ── Emotion State ────────────────────────────────────────────────────────

        private EmotionState _emotions;

        /// <summary>Current emotion state (all 8 base emotions, 0-1).</summary>
        public EmotionState CurrentEmotions => _emotions;

        // ── Decay Config ─────────────────────────────────────────────────────────

        /// <summary>
        /// Default decay half-life in seconds for each emotion.
        /// Ported from Python CompositeEmotion.DEFAULT_HALF_LIFE.
        /// </summary>
        private static readonly Dictionary<EmotionType, float> DefaultHalfLives =
            new Dictionary<EmotionType, float>
        {
            { EmotionType.Joy, 120f },
            { EmotionType.Sadness, 180f },
            { EmotionType.Anger, 90f },
            { EmotionType.Fear, 60f },
            { EmotionType.Surprise, 30f },
            { EmotionType.Disgust, 90f },
            { EmotionType.Trust, 240f },
            { EmotionType.Anticipation, 120f },
            { EmotionType.Desire, 150f },
        };

        /// <summary>Base decay half-life fallback (seconds).</summary>
        public float BaseDecayHalfLife { get; set; } = 120f;

        /// <summary>Threshold below which emotions are dropped to 0.</summary>
        public float EmotionDropThreshold { get; set; } = 0.01f;

        // ── Conflict Resolution ──────────────────────────────────────────────────

        /// <summary>
        /// Conflict resolution strategy for opposing emotion pairs.
        /// Ported from Python CompositeEmotion.
        /// </summary>
        public enum ConflictStrategy
        {
            Dominance,  // Higher intensity wins, loser reduced
            Cancel,     // Opposing emotions reduce each other
            Blend       // Both emotions averaged
        }

        public ConflictStrategy conflictStrategy = ConflictStrategy.Dominance;

        /// <summary>
        /// Opposing emotion pairs for conflict resolution.
        /// Ported from Python OPPOSING_PAIRS.
        /// </summary>
        private static readonly (EmotionType a, EmotionType b)[] OpposingPairs = new (EmotionType, EmotionType)[]
        {
            (EmotionType.Joy, EmotionType.Sadness),
            (EmotionType.Trust, EmotionType.Disgust),
            (EmotionType.Fear, EmotionType.Anger),
            (EmotionType.Anticipation, EmotionType.Surprise),
        };

        // ── Personality ──────────────────────────────────────────────────────────

        private OCEANPersonality _personality;

        /// <summary>OCEAN personality profile affecting emotion responses.</summary>
        public OCEANPersonality Personality => _personality;

        // ── Thresholds ───────────────────────────────────────────────────────────

        /// <summary>Default threshold for triggering behavior tendencies.</summary>
        public float DefaultThreshold { get; set; } = 0.7f;

        // ── Constructors ─────────────────────────────────────────────────────────

        public EmotionEngine() : this(new OCEANPersonality()) { }

        public EmotionEngine(OCEANPersonality personality)
        {
            _personality = personality ?? new OCEANPersonality();
            _emotions = new EmotionState();
        }

        public EmotionEngine(float neuroticism) : this(new OCEANPersonality(0.5f, 0.5f, 0.5f, 0.5f, neuroticism)) { }

        // ── Core Methods ─────────────────────────────────────────────────────────

        /// <summary>
        /// Set a base emotion intensity (overwrites previous value).
        /// Ported from Python CompositeEmotion.set_base_emotion().
        /// </summary>
        public void SetEmotion(EmotionType type, float intensity)
        {
            _emotions.SetValue(type, intensity);
        }

        /// <summary>
        /// Adjust an emotion by a delta. If not present, starts from 0 (BUG FIX: 0+delta, not 0.5+delta).
        /// Ported from Python CompositeEmotion.adjust_emotion().
        /// </summary>
        public void AdjustEmotion(EmotionType type, float delta)
        {
            float current = _emotions.GetValue(type);
            // BUG FIX: baseline is 0, not current. When emotion doesn't exist, start from 0.
            // This ensures PlayerAttacked → anger = 0 + 0.3*intensity = 0.24 (not 0.74)
            _emotions.SetValue(type, current + delta);
        }

        /// <summary>
        /// Get current value of a single emotion.
        /// </summary>
        public float GetEmotionValue(EmotionType type)
        {
            return _emotions.GetValue(type);
        }

        /// <summary>
        /// Get the dominant emotion type.
        /// </summary>
        public EmotionType GetDominantEmotion()
        {
            _emotions.GetDominant(out var type, out _);
            return type;
        }

        /// <summary>
        /// Process a game event: apply emotion deltas to current state.
        /// Uses GameEventProcessor for delta calculation.
        /// </summary>
        public void ProcessEvent(GameEventType eventType, float intensity, string sourceId = null)
        {
            var deltas = GameEventProcessor.ProcessEvent(eventType, intensity, _personality, sourceId);
            foreach (var delta in deltas)
            {
                AdjustEmotion(delta.emotion, delta.scaledDelta);
            }
        }

        // ── Tick (Decay) ─────────────────────────────────────────────────────────

        /// <summary>
        /// Apply emotion decay. Call every frame with Time.deltaTime.
        /// Ported from Python CompositeEmotion.tick().
        /// 
        /// Decay formula: value = value * pow(0.5, deltaTime / adjustedHalfLife)
        /// Neuroticism modifier: high neuroticism slows decay (emotions linger).
        /// </summary>
        public void Tick(float deltaTime)
        {
            if (deltaTime <= 0f) return;

            float decayModifier = _personality.GetDecayModifier();

            foreach (var type in EmotionTypeExtensions.BaseEmotions)
            {
                float current = _emotions.GetValue(type);
                if (current < EmotionDropThreshold)
                {
                    _emotions.SetValue(type, 0f);
                    continue;
                }

                float halfLife;
                if (!DefaultHalfLives.TryGetValue(type, out halfLife))
                    halfLife = BaseDecayHalfLife;

                float adjustedHalfLife = halfLife * decayModifier;

                // Exponential decay toward 0
                float decayed = MathUtils.ExponentialDecay(current, deltaTime, adjustedHalfLife);
                _emotions.SetValue(type, decayed);
            }
        }

        // ── Composite Emotion Synthesis ──────────────────────────────────────────

        /// <summary>
        /// Synthesize composite emotion from current base emotions.
        /// Ported from Python CompositeEmotion.synthesize().
        /// </summary>
        public CompositeEmotionResult Synthesize()
        {
            var allEmotions = _emotions.ToDictionary();
            if (allEmotions.Count == 0)
            {
                return new CompositeEmotionResult { name = "neutral", intensity = 0f };
            }

            // Apply conflict resolution
            var resolved = ResolveConflicts(allEmotions);

            // Sort by intensity descending
            var sorted = new List<KeyValuePair<string, float>>(resolved);
            sorted.Sort((a, b) => b.Value.CompareTo(a.Value));

            // Single dominant emotion
            if (sorted.Count == 1)
            {
                return new CompositeEmotionResult
                {
                    name = sorted[0].Key,
                    intensity = sorted[0].Value
                };
            }

            // Try predefined recipes
            var composite = MatchRecipe(resolved);
            if (composite.HasValue) return composite.Value;

            // Ad-hoc composite: top 2 base emotions
            if (sorted.Count >= 2)
            {
                float intensity = (sorted[0].Value + sorted[1].Value) * 0.5f * 1.1f; // slight boost
                return new CompositeEmotionResult
                {
                    name = sorted[0].Key + "+" + sorted[1].Key,
                    intensity = Math.Min(1f, intensity),
                    isNovel = true
                };
            }

            return new CompositeEmotionResult
            {
                name = sorted[0].Key,
                intensity = sorted[0].Value
            };
        }

        // ── Conflict Resolution ──────────────────────────────────────────────────

        /// <summary>
        /// Resolve opposing emotion pairs.
        /// Ported from Python CompositeEmotion._resolve_conflicts().
        /// </summary>
        private Dictionary<string, float> ResolveConflicts(Dictionary<string, float> emotions)
        {
            var resolved = new Dictionary<string, float>(emotions);

            foreach (var pair in OpposingPairs)
            {
                string aName = pair.a.ToName();
                string bName = pair.b.ToName();

                if (!resolved.ContainsKey(aName) || !resolved.ContainsKey(bName)) continue;

                float aVal = resolved[aName];
                float bVal = resolved[bName];

                switch (conflictStrategy)
                {
                    case ConflictStrategy.Dominance:
                        if (aVal > bVal)
                            resolved[bName] = Math.Max(0f, bVal - (aVal - bVal) * 0.5f);
                        else if (bVal > aVal)
                            resolved[aName] = Math.Max(0f, aVal - (bVal - aVal) * 0.5f);
                        else
                        {
                            resolved[aName] = aVal * 0.5f;
                            resolved[bName] = bVal * 0.5f;
                        }
                        break;

                    case ConflictStrategy.Cancel:
                        float diff = Math.Abs(aVal - bVal);
                        resolved[aName] = diff * 0.5f;
                        resolved[bName] = diff * 0.5f;
                        break;

                    case ConflictStrategy.Blend:
                        float avg = (aVal + bVal) * 0.5f;
                        resolved[aName] = avg;
                        resolved[bName] = avg;
                        break;
                }
            }

            return resolved;
        }

        // ── Recipe Matching ──────────────────────────────────────────────────────

        /// <summary>
        /// Match current emotions against predefined composite recipes.
        /// Ported from Python CompositeEmotion._match_recipe().
        /// </summary>
        private CompositeEmotionResult? MatchRecipe(Dictionary<string, float> emotions)
        {
            CompositeEmotionResult? bestMatch = null;
            float bestScore = -1f;

            foreach (var recipe in CompositeRecipes.All)
            {
                float score = 0f;
                float weightedSum = 0f;
                float weightTotal = 0f;
                float presentWeight = 0f;
                int presentCount = 0;

                foreach (var component in recipe.components)
                {
                    string emotionName = component.emotion.ToName();
                    weightTotal += component.weight;

                    if (emotions.ContainsKey(emotionName))
                    {
                        float contrib = emotions[emotionName] * component.weight;
                        score += contrib;
                        weightedSum += contrib;
                        presentWeight += component.weight;
                        presentCount++;
                    }
                }

                if (presentWeight == 0f) continue;

                // Require at least 75% of recipe emotions present
                if (presentCount < recipe.components.Length * 0.75f) continue;

                // Normalize and calculate final score
                float normalized = weightTotal > 0f ? score / weightTotal : 0f;
                float completeness = weightTotal > 0f ? presentWeight / weightTotal : 0f;
                float finalScore = normalized * 0.6f + completeness * 0.4f;

                if (finalScore > bestScore)
                {
                    bestScore = finalScore;
                    float intensity = Math.Min(1f, normalized * 1.2f);
                    bestMatch = new CompositeEmotionResult
                    {
                        name = recipe.name,
                        intensity = (float)Math.Round(intensity, 4),
                        isNovel = false
                    };
                }
            }

            return bestMatch;
        }

        // ── Response Hint Generation ─────────────────────────────────────────────

        /// <summary>
        /// Generate response hints based on current emotion state.
        /// Ported from Python EmotionFastPath._generate_hint().
        /// </summary>
        public ResponseHint GenerateHint()
        {
            var emotions = _emotions.ToDictionary();
            var composite = Synthesize();
            return HintGenerator.Generate(emotions, composite);
        }

        // ── State Access ─────────────────────────────────────────────────────────

        /// <summary>
        /// Clear all emotions to 0.
        /// </summary>
        public void Clear()
        {
            _emotions.Clear();
        }

        /// <summary>
        /// Set personality (allows runtime personality changes).
        /// </summary>
        public void SetPersonality(OCEANPersonality personality)
        {
            _personality = personality ?? new OCEANPersonality();
        }
    }

    // ── Supporting Types ─────────────────────────────────────────────────────────

    /// <summary>
    /// Result of composite emotion computation.
    /// Ported from Python CompositeEmotionResult.
    /// </summary>
    public struct CompositeEmotionResult
    {
        public string name;
        public float intensity;
        public bool isNovel;
    }

    /// <summary>
    /// Response hint for NPC dialogue generation.
    /// Ported from Python ResponseHint.
    /// </summary>
    public struct ResponseHint
    {
        public ResponseTone tone;
        public Urgency urgency;
        public SuggestedAction[] suggestedActions;
        public float confidence;
        public string reasoning;
    }
}
