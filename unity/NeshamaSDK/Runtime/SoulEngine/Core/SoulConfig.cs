using System;
using UnityEngine;

namespace Neshama.SoulEngine.Core
{
    /// <summary>
    /// Engine configuration. All tunable parameters in one place.
    /// </summary>
    [Serializable]
    public class SoulConfig
    {
        [Header("Emotion")]
        [Tooltip("Emotion decay half-life base (seconds)")]
        public float emotionBaseHalfLife = 120f;

        [Tooltip("Emotions below this are dropped to 0")]
        public float emotionDropThreshold = 0.01f;

        [Header("Memory")]
        [Tooltip("Max memories per NPC before oldest dropped")]
        public int maxMemoriesPerNpc = 50;

        [Tooltip("Relation decay rate per second")]
        public float relationDecayRate = 0.001f;

        [Header("Social")]
        [Tooltip("Min seconds between same-NPC-pair interactions")]
        public float minSocialInteractionInterval = 30f;

        [Tooltip("Max autonomous social interactions per tick")]
        public int maxSocialInteractionsPerTick = 3;

        [Header("Story")]
        [Tooltip("Default story trigger cooldown (seconds)")]
        public float defaultStoryCooldown = 60f;

        [Header("Personality")]
        [Tooltip("Max personality delta per evolution step")]
        public float personalityMaxDeltaPerStep = 0.01f;

        [Tooltip("Min interactions before personality can evolve")]
        public int personalityMinInteractionsForEvolution = 10;

        [Tooltip("Seconds between personality evolution checks")]
        public float personalityEvolutionInterval = 60f;

        /// <summary>
        /// Default configuration.
        /// </summary>
        public static SoulConfig Default => new SoulConfig();
    }
}
