using System;
using System.Collections.Generic;
using Neshama.SoulEngine.Personality;

namespace Neshama.SoulEngine.Behavior
{
    /// <summary>
    /// Maps emotion states to game behaviors.
    /// Ported from Python npc_behavior.py NPCBehaviorBridge.
    /// 
    /// Converts emotion intensities into actionable behavior modifiers.
    /// Pure rule-based, no LLM calls.
    /// </summary>
    public class BehaviorMapper
    {
        /// <summary>
        /// A single behavior modification from emotion state.
        /// </summary>
        public struct BehaviorModifier
        {
            public BehaviorType behaviorType;
            public float modifierValue;
            public bool enabled;
            public int priority;
            public string description;
        }

        /// <summary>
        /// Complete behavior profile for an NPC.
        /// Ported from Python BehaviorProfile.
        /// </summary>
        public class BehaviorProfile
        {
            public List<BehaviorModifier> modifiers = new List<BehaviorModifier>();
            public DialogueStyle dialogueStyle = DialogueStyle.Neutral;
            public MovementPattern movementPattern = MovementPattern.Normal;
            public QuestModifier questModifier = QuestModifier.Available;
            public float shopPriceMultiplier = 1.0f;
            public float factionPointModifier = 0.0f;
            public bool willTalk = true;
            public bool willShareSecrets = false;
        }

        // ── Threshold Configs ────────────────────────────────────────────────────

        /// <summary>
        /// Emotion threshold configurations.
        /// Format: (emotionName, threshold, behaviorType, baseModifier)
        /// Ported from Python EMOTION_THRESHOLD_CONFIGS.
        /// </summary>
        private static readonly (string emotion, float threshold, BehaviorType behaviorType, float baseModifier)[] DefaultThresholdConfigs =
        {
            // High anger thresholds
            ("anger", 0.7f, BehaviorType.InteractionAllowed, -0.3f),
            ("anger", 0.8f, BehaviorType.InfoSharing, -1.0f),
            // High fear thresholds
            ("fear", 0.6f, BehaviorType.MovementPatternChange, 0.0f), // fleeing
            ("fear", 0.7f, BehaviorType.InteractionAllowed, -0.4f),
            ("fear", 0.8f, BehaviorType.DialogueStyleChange, -0.5f), // submissive
            // High joy thresholds
            ("joy", 0.6f, BehaviorType.QuestAvailabilityChange, 0.3f),
            ("joy", 0.7f, BehaviorType.ShopPriceChange, -0.1f), // 10% discount
            ("joy", 0.8f, BehaviorType.InfoSharing, 0.5f),
            // High trust thresholds
            ("trust", 0.6f, BehaviorType.InfoSharing, 0.4f),
            ("trust", 0.8f, BehaviorType.QuestAvailabilityChange, 0.5f),
            ("trust", 0.8f, BehaviorType.GiftReaction, 0.5f),
            // High sadness thresholds
            ("sadness", 0.5f, BehaviorType.DialogueStyleChange, -0.3f),
            ("sadness", 0.7f, BehaviorType.QuestAvailabilityChange, -0.2f),
            ("sadness", 0.8f, BehaviorType.MovementPatternChange, 0.0f), // hiding
            // High disgust thresholds
            ("disgust", 0.5f, BehaviorType.InteractionAllowed, -0.3f),
            ("disgust", 0.7f, BehaviorType.ShopPriceChange, 0.2f), // 20% markup
            ("disgust", 0.8f, BehaviorType.InfoSharing, -0.8f),
        };

        private OCEANPersonality _personality;

        public BehaviorMapper() : this(new OCEANPersonality()) { }

        public BehaviorMapper(OCEANPersonality personality)
        {
            _personality = personality ?? new OCEANPersonality();
        }

        // ── Core Method ──────────────────────────────────────────────────────────

        /// <summary>
        /// Generate behavior profile from emotion state.
        /// Ported from Python NPCBehaviorBridge.generate_behavior().
        /// </summary>
        public BehaviorProfile GenerateBehavior(Dictionary<string, float> emotionState)
        {
            var profile = new BehaviorProfile();
            var thresholds = ApplyPersonalityModifiers();

            // Check each threshold
            foreach (var config in thresholds)
            {
                float intensity = GetValue(emotionState, config.emotion);
                if (intensity >= config.threshold)
                {
                    float overflow = intensity - config.threshold;
                    float scaledModifier = config.baseModifier * (1f + overflow);

                    profile.modifiers.Add(new BehaviorModifier
                    {
                        behaviorType = config.behaviorType,
                        modifierValue = (float)Math.Round(scaledModifier, 4),
                        enabled = true,
                        priority = (int)(intensity * 10),
                        description = $"Emotion {config.emotion} ({intensity:F2}) affects {config.behaviorType}"
                    });
                }
            }

            // Derive aggregate behaviors
            DeriveDialogueStyle(profile, emotionState);
            DeriveMovementPattern(profile, emotionState);
            DeriveQuestModifier(profile, emotionState);
            DeriveShopPrice(profile, emotionState);
            DeriveFactionShift(profile, emotionState);
            DeriveInteractionFlags(profile, emotionState);

            return profile;
        }

        // ── Personality Modifiers ────────────────────────────────────────────────

        private List<(string emotion, float threshold, BehaviorType behaviorType, float baseModifier)> ApplyPersonalityModifiers()
        {
            var modified = new List<(string, float, BehaviorType, float)>();

            foreach (var config in DefaultThresholdConfigs)
            {
                float thresholdMod = config.threshold;

                // High agreeableness = lower thresholds for positive behaviors
                if (config.behaviorType == BehaviorType.InfoSharing || 
                    config.behaviorType == BehaviorType.QuestAvailabilityChange)
                {
                    float agreeableness = _personality.agreeableness;
                    if (agreeableness > 0.6f)
                        thresholdMod = thresholdMod * (1f - (agreeableness - 0.6f) * 0.3f);
                }

                // High neuroticism = lower thresholds for fear/anger responses
                if (config.behaviorType == BehaviorType.MovementPatternChange || 
                    config.behaviorType == BehaviorType.InteractionAllowed)
                {
                    float neuroticism = _personality.neuroticism;
                    if (neuroticism > 0.6f)
                        thresholdMod = thresholdMod * (1f - (neuroticism - 0.6f) * 0.2f);
                }

                modified.Add((config.emotion, thresholdMod, config.behaviorType, config.baseModifier));
            }

            return modified;
        }

        // ── Derivation Methods ───────────────────────────────────────────────────

        private void DeriveDialogueStyle(BehaviorProfile profile, Dictionary<string, float> emotions)
        {
            float anger = GetValue(emotions, "anger");
            float fear = GetValue(emotions, "fear");
            float joy = GetValue(emotions, "joy");
            float sadness = GetValue(emotions, "sadness");

            if (anger > 0.5f) profile.dialogueStyle = DialogueStyle.Aggressive;
            else if (fear > 0.5f) profile.dialogueStyle = DialogueStyle.Submissive;
            else if (joy > 0.5f) profile.dialogueStyle = DialogueStyle.Excited;
            else if (sadness > 0.4f) profile.dialogueStyle = DialogueStyle.Gloomy;
            else if (anger > 0.3f || fear > 0.3f) profile.dialogueStyle = DialogueStyle.Cautious;
            else profile.dialogueStyle = DialogueStyle.Neutral;
        }

        private void DeriveMovementPattern(BehaviorProfile profile, Dictionary<string, float> emotions)
        {
            float fear = GetValue(emotions, "fear");
            float anger = GetValue(emotions, "anger");
            float joy = GetValue(emotions, "joy");
            float sadness = GetValue(emotions, "sadness");

            if (fear > 0.6f) profile.movementPattern = MovementPattern.Fleeing;
            else if (sadness > 0.6f) profile.movementPattern = MovementPattern.Hiding;
            else if (anger > 0.6f) profile.movementPattern = MovementPattern.AggressivePatrol;
            else if (fear > 0.4f || anger > 0.4f) profile.movementPattern = MovementPattern.Defensive;
            else if (joy > 0.5f) profile.movementPattern = MovementPattern.Excited;
            else profile.movementPattern = MovementPattern.Normal;
        }

        private void DeriveQuestModifier(BehaviorProfile profile, Dictionary<string, float> emotions)
        {
            float anger = GetValue(emotions, "anger");
            float trust = GetValue(emotions, "trust");
            float sadness = GetValue(emotions, "sadness");

            if (anger > 0.7f) profile.questModifier = QuestModifier.Locked;
            else if (trust > 0.7f) profile.questModifier = QuestModifier.Available;
            else if (sadness > 0.5f) profile.questModifier = QuestModifier.AvailableWithCondition;
            else profile.questModifier = QuestModifier.Available;
        }

        private void DeriveShopPrice(BehaviorProfile profile, Dictionary<string, float> emotions)
        {
            float joy = GetValue(emotions, "joy");
            float trust = GetValue(emotions, "trust");
            float anger = GetValue(emotions, "anger");
            float disgust = GetValue(emotions, "disgust");

            float multiplier = 1.0f;

            // Positive emotions = discount
            if (joy > 0.5f) multiplier -= 0.1f * joy;
            if (trust > 0.5f) multiplier -= 0.1f * trust;

            // Negative emotions = markup
            if (anger > 0.4f) multiplier += 0.15f * anger;
            if (disgust > 0.4f) multiplier += 0.2f * disgust;

            profile.shopPriceMultiplier = Math.Max(0.5f, Math.Min(2.0f, multiplier));
        }

        private void DeriveFactionShift(BehaviorProfile profile, Dictionary<string, float> emotions)
        {
            float anger = GetValue(emotions, "anger");
            float disgust = GetValue(emotions, "disgust");
            float trust = GetValue(emotions, "trust");
            float joy = GetValue(emotions, "joy");

            float shift = 0.0f;
            if (trust > 0.4f) shift += 0.1f * trust;
            if (joy > 0.4f) shift += 0.1f * joy;
            if (anger > 0.4f) shift -= 0.15f * anger;
            if (disgust > 0.4f) shift -= 0.1f * disgust;

            profile.factionPointModifier = Math.Max(-1f, Math.Min(1f, shift));
        }

        private void DeriveInteractionFlags(BehaviorProfile profile, Dictionary<string, float> emotions)
        {
            float anger = GetValue(emotions, "anger");
            float fear = GetValue(emotions, "fear");
            float disgust = GetValue(emotions, "disgust");
            float trust = GetValue(emotions, "trust");

            // Will talk
            if (anger > 0.8f || fear > 0.8f || disgust > 0.8f)
                profile.willTalk = false;
            else if (anger > 0.5f || fear > 0.6f || disgust > 0.5f)
                profile.willTalk = false;
            else
                profile.willTalk = true;

            // Will share secrets
            if (trust > 0.7f) profile.willShareSecrets = true;
            else if (anger > 0.3f || fear > 0.4f) profile.willShareSecrets = false;
            else profile.willShareSecrets = false;
        }

        private static float GetValue(Dictionary<string, float> dict, string key)
        {
            float val;
            return dict != null && dict.TryGetValue(key, out val) ? val : 0f;
        }
    }
}
