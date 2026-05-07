using System;
using System.Collections.Generic;

namespace Neshama.SoulEngine.Emotion
{
    /// <summary>
    /// Generates response hints from emotion state.
    /// Ported from Python fast_path.py EmotionFastPath._generate_hint() and _infer_response().
    /// </summary>
    public static class HintGenerator
    {
        /// <summary>
        /// Generate a response hint from emotion state and composite emotion.
        /// </summary>
        public static ResponseHint Generate(
            Dictionary<string, float> emotions,
            CompositeEmotionResult composite)
        {
            var (tone, urgency, actions, reasoning) = InferResponse(emotions, composite);
            float confidence = CalculateConfidence(emotions);

            return new ResponseHint
            {
                tone = tone,
                urgency = urgency,
                suggestedActions = actions.ToArray(),
                confidence = confidence,
                reasoning = reasoning,
            };
        }

        /// <summary>
        /// Infer response parameters from emotion state.
        /// Ported from Python EmotionFastPath._infer_response().
        /// </summary>
        private static (ResponseTone, Urgency, List<SuggestedAction>, string) InferResponse(
            Dictionary<string, float> emotions,
            CompositeEmotionResult composite)
        {
            ResponseTone tone = ResponseTone.Neutral;
            Urgency urgency = Urgency.Low;
            var actions = new List<SuggestedAction> { SuggestedAction.DialogueFriendly };
            string reasoning = "No strong emotion detected";

            if (emotions == null || emotions.Count == 0)
                return (tone, urgency, actions, reasoning);

            float anger = GetValue(emotions, "anger");
            float fear = GetValue(emotions, "fear");
            float joy = GetValue(emotions, "joy");
            float trust = GetValue(emotions, "trust");
            float sadness = GetValue(emotions, "sadness");
            float surprise = GetValue(emotions, "surprise");
            float disgust = GetValue(emotions, "disgust");

            // Anger-based responses
            if (anger > 0.6f)
            {
                tone = ResponseTone.Hostile;
                urgency = anger > 0.8f ? Urgency.High : Urgency.Medium;
                actions = new List<SuggestedAction> { SuggestedAction.DialogueHostile };
                if (anger > 0.8f) actions.Add(SuggestedAction.QuestRefuse);
                reasoning = $"High anger ({anger:F2})";
            }
            else if (anger > 0.3f)
            {
                tone = ResponseTone.Angry;
                urgency = Urgency.Medium;
                actions = new List<SuggestedAction> { SuggestedAction.DialogueHostile, SuggestedAction.WithholdInfo };
                reasoning = $"Moderate anger ({anger:F2})";
            }
            // Fear-based responses
            else if (fear > 0.6f)
            {
                tone = ResponseTone.Fearful;
                urgency = Urgency.High;
                actions = new List<SuggestedAction> { SuggestedAction.DialogueCautious, SuggestedAction.Flee };
                reasoning = $"High fear ({fear:F2})";
            }
            else if (fear > 0.3f)
            {
                tone = ResponseTone.Nervous;
                urgency = Urgency.Medium;
                actions = new List<SuggestedAction> { SuggestedAction.DialogueCautious };
                reasoning = $"Moderate fear ({fear:F2})";
            }
            // Joy-based responses
            else if (joy > 0.5f)
            {
                tone = ResponseTone.Joyful;
                urgency = Urgency.Low;
                actions = new List<SuggestedAction> { SuggestedAction.DialogueFriendly, SuggestedAction.Celebration };
                if (trust > 0.4f)
                {
                    actions.Add(SuggestedAction.ShareInfo);
                    actions.Add(SuggestedAction.QuestOffer);
                }
                reasoning = $"High joy ({joy:F2})";
            }
            // Trust-based responses
            else if (trust > 0.5f)
            {
                tone = ResponseTone.Trusting;
                urgency = Urgency.Low;
                actions = new List<SuggestedAction> { SuggestedAction.DialogueFriendly, SuggestedAction.ShareInfo };
                if (composite.name == "love")
                    actions.Add(SuggestedAction.QuestOffer);
                reasoning = $"High trust ({trust:F2})";
            }
            // Sadness-based responses
            else if (sadness > 0.4f)
            {
                tone = ResponseTone.Sad;
                urgency = Urgency.Low;
                actions = new List<SuggestedAction> { SuggestedAction.Consolation, SuggestedAction.DialogueCautious };
                reasoning = $"Sadness detected ({sadness:F2})";
            }
            // Surprise-based responses
            else if (surprise > 0.5f)
            {
                tone = ResponseTone.Surprised;
                urgency = Urgency.Medium;
                actions = new List<SuggestedAction> { SuggestedAction.DialogueCautious };
                reasoning = $"Surprise detected ({surprise:F2})";
            }
            // Disgust-based responses
            else if (disgust > 0.4f)
            {
                tone = ResponseTone.Hostile;
                urgency = Urgency.Medium;
                actions = new List<SuggestedAction> { SuggestedAction.DialogueHostile, SuggestedAction.QuestRefuse };
                reasoning = $"Disgust detected ({disgust:F2})";
            }

            // Composite emotion overrides (higher priority)
            if (composite.intensity > 0.5f)
            {
                if (composite.name == "gratitude")
                {
                    tone = ResponseTone.Grateful;
                    actions = new List<SuggestedAction> { SuggestedAction.GiveGift, SuggestedAction.ShareInfo };
                    reasoning = "Gratitude composite emotion";
                }
                else if (composite.name == "pride")
                {
                    tone = ResponseTone.Proud;
                    actions = new List<SuggestedAction> { SuggestedAction.Celebration, SuggestedAction.QuestOffer };
                    reasoning = "Pride composite emotion";
                }
                else if (composite.name == "love")
                {
                    tone = ResponseTone.Trusting;
                    actions = new List<SuggestedAction> { SuggestedAction.ShareInfo, SuggestedAction.QuestOffer };
                    reasoning = "Love composite emotion";
                }
            }

            return (tone, urgency, actions, reasoning);
        }

        /// <summary>
        /// Calculate confidence in the emotion interpretation.
        /// Ported from Python EmotionFastPath._calculate_confidence().
        /// </summary>
        private static float CalculateConfidence(Dictionary<string, float> emotions)
        {
            if (emotions == null || emotions.Count == 0) return 0.5f;

            int numEmotions = emotions.Count;
            if (numEmotions <= 2) return 0.9f;

            float maxIntensity = 0f, minIntensity = float.MaxValue;
            foreach (var kv in emotions)
            {
                if (kv.Value > maxIntensity) maxIntensity = kv.Value;
                if (kv.Value < minIntensity) minIntensity = kv.Value;
            }

            // Clear dominance = high confidence
            if (maxIntensity - minIntensity > 0.5f) return 0.85f;

            // Many weak emotions = lower confidence
            if (numEmotions >= 4) return 0.6f;

            return 0.75f;
        }

        private static float GetValue(Dictionary<string, float> dict, string key)
        {
            float val;
            return dict != null && dict.TryGetValue(key, out val) ? val : 0f;
        }
    }
}
