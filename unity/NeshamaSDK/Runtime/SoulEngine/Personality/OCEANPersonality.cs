using System;
using Neshama.SoulEngine.Utils;

namespace Neshama.SoulEngine.Personality
{
    /// <summary>
    /// OCEAN personality model. Ported from Python neshama/core/ocean.py.
    /// Five-Factor Model: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism.
    /// All values normalized to [0, 1].
    /// </summary>
    [Serializable]
    public class OCEANPersonality
    {
        // ── Five Factors ─────────────────────────────────────────────────────────

        /// <summary>开放性 - creativity, curiosity vs conventional, practical</summary>
        public float openness = 0.5f;

        /// <summary>尽责性 - organized, disciplined vs flexible, casual</summary>
        public float conscientiousness = 0.5f;

        /// <summary>外向性 - outgoing, energetic vs reserved, solo</summary>
        public float extraversion = 0.5f;

        /// <summary>宜人性 - cooperative, trusting vs competitive, skeptical</summary>
        public float agreeableness = 0.5f;

        /// <summary>神经质 - sensitive, nervous vs resilient, confident. Higher = more emotionally reactive</summary>
        public float neuroticism = 0.5f;

        // ── Constructors ─────────────────────────────────────────────────────────

        public OCEANPersonality() { }

        public OCEANPersonality(float o, float c, float e, float a, float n)
        {
            openness = MathUtils.Clamp01(o);
            conscientiousness = MathUtils.Clamp01(c);
            extraversion = MathUtils.Clamp01(e);
            agreeableness = MathUtils.Clamp01(a);
            neuroticism = MathUtils.Clamp01(n);
        }

        // ── Decay Modifier ──────────────────────────────────────────────────────

        /// <summary>
        /// Calculate emotion decay modifier based on neuroticism.
        /// High neuroticism = slower decay (emotions linger longer).
        /// Formula: 0.2 + 0.8 * (1 - neuroticism)
        /// neuroticism=0 → modifier=1.0 (full speed decay)
        /// neuroticism=1 → modifier=0.2 (20% speed, emotions last 5x longer)
        /// Ported from Python CompositeEmotion.tick().
        /// </summary>
        public float GetDecayModifier()
        {
            float modifier = 0.2f + 0.8f * (1.0f - neuroticism);
            return Math.Max(0.1f, modifier); // minimum 10% decay speed
        }

        // ── Personality Trait Lookup ─────────────────────────────────────────────

        /// <summary>
        /// Get trait value by name. Used for dynamic modifier lookups.
        /// </summary>
        public float GetTrait(string traitName)
        {
            switch (traitName.ToLower())
            {
                case "openness": return openness;
                case "conscientiousness": return conscientiousness;
                case "extraversion": return extraversion;
                case "agreeableness": return agreeableness;
                case "neuroticism": return neuroticism;
                default: return 0.5f;
            }
        }

        /// <summary>
        /// Set trait value by name, clamped to [0,1].
        /// </summary>
        public void SetTrait(string traitName, float value)
        {
            value = MathUtils.Clamp01(value);
            switch (traitName.ToLower())
            {
                case "openness": openness = value; break;
                case "conscientiousness": conscientiousness = value; break;
                case "extraversion": extraversion = value; break;
                case "agreeableness": agreeableness = value; break;
                case "neuroticism": neuroticism = value; break;
            }
        }

        /// <summary>
        /// Adjust a trait by a delta, clamped to [0,1].
        /// Used for personality micro-evolution.
        /// </summary>
        public void AdjustTrait(string traitName, float delta)
        {
            float current = GetTrait(traitName);
            SetTrait(traitName, current + delta);
        }

        // ── Behavioral Tendencies ────────────────────────────────────────────────

        /// <summary>
        /// Calculate behavioral tendencies based on OCEAN parameters.
        /// Ported from Python OceanManager.calculate_behavioral_tendency().
        /// </summary>
        public BehavioralTendencies GetBehavioralTendencies()
        {
            return new BehavioralTendencies
            {
                creativity = openness,
                planning = conscientiousness,
                socializing = extraversion,
                cooperation = agreeableness,
                stressResistance = 1f - neuroticism,
                emotionalSensitivity = neuroticism,
            };
        }

        // ── Copy ─────────────────────────────────────────────────────────────────

        public OCEANPersonality Clone()
        {
            return new OCEANPersonality(openness, conscientiousness, extraversion, agreeableness, neuroticism);
        }

        // ── Presets ──────────────────────────────────────────────────────────────

        /// <summary>
        /// Apply a preset personality archetype. Returns true if preset found.
        /// </summary>
        public bool ApplyPreset(string presetName)
        {
            var preset = PersonalityPresets.Get(presetName);
            if (preset == null) return false;
            openness = preset.openness;
            conscientiousness = preset.conscientiousness;
            extraversion = preset.extraversion;
            agreeableness = preset.agreeableness;
            neuroticism = preset.neuroticism;
            return true;
        }
    }

    /// <summary>
    /// Behavioral tendencies derived from OCEAN personality.
    /// </summary>
    [Serializable]
    public struct BehavioralTendencies
    {
        public float creativity;       // openness
        public float planning;         // conscientiousness
        public float socializing;      // extraversion
        public float cooperation;      // agreeableness
        public float stressResistance; // 1 - neuroticism
        public float emotionalSensitivity; // neuroticism
    }

    /// <summary>
    /// Preset personality archetypes. Ported from Python OceanManager.PRESETS.
    /// </summary>
    public static class PersonalityPresets
    {
        private static readonly OCEANPersonality Analyst = new OCEANPersonality(0.8f, 0.7f, 0.3f, 0.4f, 0.5f);
        private static readonly OCEANPersonality Helper = new OCEANPersonality(0.5f, 0.6f, 0.7f, 0.9f, 0.4f);
        private static readonly OCEANPersonality Explorer = new OCEANPersonality(0.9f, 0.4f, 0.7f, 0.5f, 0.4f);
        private static readonly OCEANPersonality Leader = new OCEANPersonality(0.6f, 0.8f, 0.8f, 0.5f, 0.4f);
        private static readonly OCEANPersonality Diplomat = new OCEANPersonality(0.7f, 0.6f, 0.6f, 0.8f, 0.4f);
        private static readonly OCEANPersonality Sentinel = new OCEANPersonality(0.3f, 0.9f, 0.4f, 0.7f, 0.4f);
        private static readonly OCEANPersonality Neshama = new OCEANPersonality(0.75f, 0.65f, 0.55f, 0.6f, 0.45f);

        public static OCEANPersonality Get(string name)
        {
            switch (name.ToLower())
            {
                case "analyst": return Analyst;
                case "helper": return Helper;
                case "explorer": return Explorer;
                case "leader": return Leader;
                case "diplomat": return Diplomat;
                case "sentinel": return Sentinel;
                case "neshama": return Neshama;
                default: return null;
            }
        }
    }
}
