using System;
using Neshama.SoulEngine.Utils;

namespace Neshama.SoulEngine.Personality
{
    /// <summary>
    /// Personality micro-evolution system.
    /// Long-term interactions cause gradual personality shifts.
    /// Ported from design intent in Python npc_manager.py personality handling.
    /// </summary>
    public class PersonalityEvolver
    {
        /// <summary>
        /// Maximum delta per evolution step. Keeps personality stable over short periods.
        /// </summary>
        public float maxDeltaPerStep = 0.01f;

        /// <summary>
        /// Minimum interaction count before evolution can occur.
        /// </summary>
        public int minInteractionsForEvolution = 10;

        /// <summary>
        /// How strongly emotional experience drives personality change.
        /// </summary>
        public float emotionalInfluenceStrength = 0.005f;

        private int _totalInteractions = 0;

        /// <summary>
        /// Record that an interaction occurred.
        /// </summary>
        public void RecordInteraction()
        {
            _totalInteractions++;
        }

        /// <summary>
        /// Evolve personality based on emotional state.
        /// High emotions over time shift personality slightly.
        /// Call this periodically (e.g., every 60 seconds of game time).
        /// </summary>
        /// <param name="personality">The personality to evolve</param>
        /// <param name="emotionalState">Current emotion state</param>
        public void Evolve(OCEANPersonality personality, Emotion.EmotionState emotionalState)
        {
            if (_totalInteractions < minInteractionsForEvolution) return;

            // High joy + trust → increase extraversion, agreeableness
            float positiveVal = (emotionalState.joy + emotionalState.trust) * 0.5f;
            if (positiveVal > 0.5f)
            {
                float delta = (positiveVal - 0.5f) * emotionalInfluenceStrength;
                personality.AdjustTrait("extraversion", Math.Min(delta, maxDeltaPerStep));
                personality.AdjustTrait("agreeableness", Math.Min(delta * 0.5f, maxDeltaPerStep));
            }

            // High fear + sadness → increase neuroticism slightly
            float negativeVal = (emotionalState.fear + emotionalState.sadness) * 0.5f;
            if (negativeVal > 0.5f)
            {
                float delta = (negativeVal - 0.5f) * emotionalInfluenceStrength;
                personality.AdjustTrait("neuroticism", Math.Min(delta, maxDeltaPerStep));
            }

            // High anger + disgust → decrease agreeableness slightly
            float hostileVal = (emotionalState.anger + emotionalState.disgust) * 0.5f;
            if (hostileVal > 0.6f)
            {
                float delta = (hostileVal - 0.6f) * emotionalInfluenceStrength;
                personality.AdjustTrait("agreeableness", -Math.Min(delta, maxDeltaPerStep));
            }
        }

        /// <summary>
        /// Reset the evolver state.
        /// </summary>
        public void Reset()
        {
            _totalInteractions = 0;
        }

        public int TotalInteractions => _totalInteractions;
    }
}
