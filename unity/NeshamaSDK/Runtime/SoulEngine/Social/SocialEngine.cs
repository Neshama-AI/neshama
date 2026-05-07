using System;
using System.Collections.Generic;
using Neshama.SoulEngine.Personality;

namespace Neshama.SoulEngine.Social
{
    /// <summary>
    /// Relationship between two NPCs.
    /// Ported from Python social_engine.py NPCRelation.
    /// </summary>
    [Serializable]
    public class NPCRelation
    {
        public string npcAId;
        public string npcBId;
        public float strength = 0.5f;          // -1 to 1
        public float trust = 0.5f;             // 0 to 1
        public float familiarity = 0.0f;       // 0 to 1
        public int interactionCount;
        public float lastInteractionTime;       // game time
        public RelationshipCategory category = RelationshipCategory.Neutral;
        public float grudge = 0.0f;            // 0 to 1
        public float bond = 0.0f;              // 0 to 1
        public float romanticInterest = 0.0f;   // 0 to 1
    }

    /// <summary>
    /// Record of a social interaction.
    /// Ported from Python SocialEvent.
    /// </summary>
    [Serializable]
    public class SocialEvent
    {
        public string eventId;
        public string npcAId;
        public string npcBId;
        public SocialInteractionType interactionType;
        public float timestamp;
        public bool success = true;
        public Dictionary<string, float> relationshipDelta = new Dictionary<string, float>();
    }

    /// <summary>
    /// Social engine managing NPC-to-NPC relationships.
    /// Ported from Python social_engine.py NPCSocialEngine.
    /// 
    /// Features:
    /// - NPC-to-NPC social interactions (8 types)
    /// - Relationship strength tracking
    /// - Grudge factor (negative relationships affect positive interactions)
    /// - Social tick for autonomous interactions
    /// </summary>
    public class SocialEngine
    {
        // ── Constants ────────────────────────────────────────────────────────────

        public float minInteractionInterval = 30f;
        public int maxInteractionsPerTick = 3;
        public float trustThresholdForDeep = 0.7f;
        public float familiarityThreshold = 0.3f;

        // ── State ────────────────────────────────────────────────────────────────

        // Relations: key = (min_id, max_id) → NPCRelation
        private Dictionary<string, NPCRelation> _relations = new Dictionary<string, NPCRelation>();

        // NPC profiles: npcId → personality
        private Dictionary<string, OCEANPersonality> _npcPersonalities = new Dictionary<string, OCEANPersonality>();

        // NPC emotions: npcId → emotion dict
        private Dictionary<string, Dictionary<string, float>> _npcEmotions = new Dictionary<string, Dictionary<string, float>>();

        // Last interaction times: key → game time
        private Dictionary<string, float> _lastInteractionTimes = new Dictionary<string, float>();

        // Social event history
        private List<SocialEvent> _socialEvents = new List<SocialEvent>();
        private int _maxEvents = 1000;

        // Game time
        private float _gameTime = 0f;

        // Random for decisions
        private Random _random = new Random();

        // ── Registration ─────────────────────────────────────────────────────────

        /// <summary>
        /// Register an NPC with the social engine.
        /// </summary>
        public void RegisterNPC(string npcId, OCEANPersonality personality = null, Dictionary<string, float> emotions = null)
        {
            _npcPersonalities[npcId] = personality ?? new OCEANPersonality();
            _npcEmotions[npcId] = emotions ?? new Dictionary<string, float>();
        }

        /// <summary>
        /// Update NPC emotion state.
        /// </summary>
        public void UpdateNPCEmotions(string npcId, Dictionary<string, float> emotions)
        {
            _npcEmotions[npcId] = emotions ?? new Dictionary<string, float>();
        }

        // ── Interactions ─────────────────────────────────────────────────────────

        /// <summary>
        /// Initiate a social interaction between two NPCs.
        /// Ported from Python NPCSocialEngine.initiate_interaction().
        /// </summary>
        public SocialEvent InitiateInteraction(
            string npcAId, string npcBId,
            SocialInteractionType? forcedType = null)
        {
            string key = GetRelationKey(npcAId, npcBId);

            // Check cooldown
            float lastTime;
            if (_lastInteractionTimes.TryGetValue(key, out lastTime))
            {
                if (_gameTime - lastTime < minInteractionInterval)
                {
                    return new SocialEvent
                    {
                        eventId = Guid.NewGuid().ToString(),
                        npcAId = npcAId,
                        npcBId = npcBId,
                        interactionType = SocialInteractionType.Gossip,
                        success = false,
                        timestamp = _gameTime,
                    };
                }
            }

            // Get or create relation
            NPCRelation relation = GetOrCreateRelation(npcAId, npcBId);

            // Get NPC profiles
            OCEANPersonality personalityA, personalityB;
            _npcPersonalities.TryGetValue(npcAId, out personalityA);
            _npcPersonalities.TryGetValue(npcBId, out personalityB);
            personalityA = personalityA ?? new OCEANPersonality();
            personalityB = personalityB ?? new OCEANPersonality();

            Dictionary<string, float> emotionsA, emotionsB;
            _npcEmotions.TryGetValue(npcAId, out emotionsA);
            _npcEmotions.TryGetValue(npcBId, out emotionsB);
            emotionsA = emotionsA ?? new Dictionary<string, float>();
            emotionsB = emotionsB ?? new Dictionary<string, float>();

            // Determine interaction type
            SocialInteractionType interactionType;
            if (forcedType.HasValue)
            {
                interactionType = forcedType.Value;
            }
            else
            {
                interactionType = DecideInteractionType(personalityA, emotionsA, personalityB, emotionsB, relation);
            }

            // Calculate effects
            var delta = CalculateInteractionEffects(interactionType, personalityA, personalityB, relation);

            // Apply delta
            ApplyRelationDelta(relation, delta);

            // Update tracking
            relation.interactionCount++;
            relation.lastInteractionTime = _gameTime;
            _lastInteractionTimes[key] = _gameTime;

            // Create event
            var evt = new SocialEvent
            {
                eventId = Guid.NewGuid().ToString(),
                npcAId = npcAId,
                npcBId = npcBId,
                interactionType = interactionType,
                success = true,
                timestamp = _gameTime,
                relationshipDelta = delta,
            };

            _socialEvents.Add(evt);
            if (_socialEvents.Count > _maxEvents)
                _socialEvents = _socialEvents.GetRange(_socialEvents.Count - _maxEvents, _maxEvents);

            return evt;
        }

        /// <summary>
        /// Get relationship between two NPCs.
        /// </summary>
        public NPCRelation GetRelation(string npcAId, string npcBId)
        {
            string key = GetRelationKey(npcAId, npcBId);
            NPCRelation rel;
            return _relations.TryGetValue(key, out rel) ? rel : null;
        }

        /// <summary>
        /// Get social graph for an NPC.
        /// Ported from Python NPCSocialEngine.get_social_graph().
        /// </summary>
        public Dictionary<string, List<NPCRelation>> GetSocialGraph(string npcId)
        {
            var result = new Dictionary<string, List<NPCRelation>>
            {
                { "friends", new List<NPCRelation>() },
                { "enemies", new List<NPCRelation>() },
                { "neutrals", new List<NPCRelation>() },
                { "strangers", new List<NPCRelation>() },
            };

            foreach (var kv in _relations)
            {
                var rel = kv.Value;
                if (rel.npcAId != npcId && rel.npcBId != npcId) continue;

                switch (rel.category)
                {
                    case RelationshipCategory.Friend: result["friends"].Add(rel); break;
                    case RelationshipCategory.Enemy: result["enemies"].Add(rel); break;
                    case RelationshipCategory.Stranger: result["strangers"].Add(rel); break;
                    default: result["neutrals"].Add(rel); break;
                }
            }

            return result;
        }

        // ── Tick ─────────────────────────────────────────────────────────────────

        /// <summary>
        /// Update game time.
        /// </summary>
        public void Tick(float deltaTime)
        {
            _gameTime += deltaTime;
        }

        // ── Private Methods ──────────────────────────────────────────────────────

        private NPCRelation GetOrCreateRelation(string npcAId, string npcBId)
        {
            string key = GetRelationKey(npcAId, npcBId);
            NPCRelation rel;
            if (!_relations.TryGetValue(key, out rel))
            {
                rel = new NPCRelation { npcAId = key.Substring(0, key.IndexOf(':')), npcBId = key.Substring(key.IndexOf(':') + 1) };
                _relations[key] = rel;
            }
            return rel;
        }

        private string GetRelationKey(string a, string b)
        {
            return string.Compare(a, b, StringComparison.Ordinal) < 0 ? a + ":" + b : b + ":" + a;
        }

        /// <summary>
        /// Decide interaction type based on personality, emotions, and relationship.
        /// Ported from Python _decide_interaction_type().
        /// </summary>
        private SocialInteractionType DecideInteractionType(
            OCEANPersonality personalityA, Dictionary<string, float> emotionsA,
            OCEANPersonality personalityB, Dictionary<string, float> emotionsB,
            NPCRelation relation)
        {
            float anger = GetValue(emotionsA, "anger") + GetValue(emotionsA, "contempt");
            if (anger > 0.6f) return SocialInteractionType.Argue;

            float sadness = GetValue(emotionsB, "sadness") + GetValue(emotionsB, "anxiety");
            if (sadness > 0.5f && relation.trust > 0.4f) return SocialInteractionType.Comfort;

            if (relation.romanticInterest > 0.5f) return SocialInteractionType.Flirt;

            if (personalityA.agreeableness > 0.6f)
            {
                if (relation.familiarity < familiarityThreshold)
                    return SocialInteractionType.Gossip;
                return _random.Next(2) == 0 ? SocialInteractionType.Comfort : SocialInteractionType.Gossip;
            }

            if (personalityA.agreeableness < 0.4f)
                return _random.Next(2) == 0 ? SocialInteractionType.Argue : SocialInteractionType.Trade;

            if (personalityA.extraversion > 0.6f)
            {
                float joy = GetValue(emotionsA, "joy") + GetValue(emotionsA, "delight");
                if (joy > 0.5f)
                    return _random.Next(2) == 0 ? SocialInteractionType.Flirt : SocialInteractionType.Ally;
                return SocialInteractionType.Gossip;
            }

            if (relation.trust > trustThresholdForDeep)
                return _random.Next(2) == 0 ? SocialInteractionType.Ally : SocialInteractionType.Teach;

            if (relation.familiarity < 0.1f) return SocialInteractionType.Gossip;
            return SocialInteractionType.Trade;
        }

        /// <summary>
        /// Calculate relationship delta from an interaction.
        /// Ported from Python _calculate_interaction_effects().
        /// </summary>
        private Dictionary<string, float> CalculateInteractionEffects(
            SocialInteractionType type, OCEANPersonality personalityA,
            OCEANPersonality personalityB, NPCRelation relation)
        {
            var delta = new Dictionary<string, float>();

            // Base effects per interaction type
            var baseEffects = new Dictionary<string, float>();
            switch (type)
            {
                case SocialInteractionType.Gossip:
                    baseEffects["strength"] = 0.05f; baseEffects["familiarity"] = 0.1f;
                    break;
                case SocialInteractionType.Trade:
                    baseEffects["strength"] = 0.1f; baseEffects["trust"] = 0.1f; baseEffects["familiarity"] = 0.1f;
                    break;
                case SocialInteractionType.Argue:
                    baseEffects["strength"] = -0.15f; baseEffects["trust"] = -0.1f;
                    break;
                case SocialInteractionType.Ally:
                    baseEffects["strength"] = 0.25f; baseEffects["trust"] = 0.2f; baseEffects["familiarity"] = 0.15f;
                    break;
                case SocialInteractionType.Betray:
                    baseEffects["strength"] = -0.5f; baseEffects["trust"] = -0.6f; baseEffects["grudge"] = 0.4f;
                    break;
                case SocialInteractionType.Comfort:
                    baseEffects["strength"] = 0.1f; baseEffects["bond"] = 0.15f; baseEffects["familiarity"] = 0.05f;
                    break;
                case SocialInteractionType.Teach:
                    baseEffects["strength"] = 0.1f; baseEffects["trust"] = 0.1f; baseEffects["familiarity"] = 0.1f;
                    break;
                case SocialInteractionType.Flirt:
                    baseEffects["strength"] = 0.1f; baseEffects["romanticInterest"] = 0.15f; baseEffects["familiarity"] = 0.05f;
                    break;
            }

            // Personality modifier
            float agreeableness = personalityA.agreeableness;
            float modifier = 1.0f;
            if (type == SocialInteractionType.Comfort || type == SocialInteractionType.Gossip)
                modifier = 1.0f + (agreeableness - 0.5f) * 0.5f;
            else if (type == SocialInteractionType.Argue)
                modifier = 1.0f - (agreeableness - 0.5f) * 0.5f;

            foreach (var kv in baseEffects)
                delta[kv.Key] = kv.Value * modifier;

            // Grudge modifier
            if (relation.grudge > 0.3f)
            {
                if (type == SocialInteractionType.Argue)
                {
                    float str;
                    if (delta.TryGetValue("strength", out str))
                        delta["strength"] = str * 0.5f;
                }
                else if (type == SocialInteractionType.Ally || type == SocialInteractionType.Comfort)
                {
                    float str;
                    if (delta.TryGetValue("strength", out str))
                        delta["strength"] = str * 0.3f;
                }
            }

            return delta;
        }

        /// <summary>
        /// Apply relationship delta to a relation.
        /// Ported from Python _apply_relation_delta().
        /// </summary>
        private void ApplyRelationDelta(NPCRelation relation, Dictionary<string, float> delta)
        {
            if (delta.ContainsKey("strength"))
                relation.strength = Math.Max(-1f, Math.Min(1f, relation.strength + delta["strength"]));
            if (delta.ContainsKey("trust"))
                relation.trust = Math.Max(0f, Math.Min(1f, relation.trust + delta["trust"]));
            if (delta.ContainsKey("familiarity"))
                relation.familiarity = Math.Max(0f, Math.Min(1f, relation.familiarity + delta["familiarity"]));
            if (delta.ContainsKey("grudge"))
                relation.grudge = Math.Max(0f, Math.Min(1f, relation.grudge + delta["grudge"]));
            if (delta.ContainsKey("bond"))
                relation.bond = Math.Max(0f, Math.Min(1f, relation.bond + delta["bond"]));
            if (delta.ContainsKey("romanticInterest"))
                relation.romanticInterest = Math.Max(0f, Math.Min(1f, relation.romanticInterest + delta["romanticInterest"]));

            UpdateRelationCategory(relation);
        }

        private void UpdateRelationCategory(NPCRelation relation)
        {
            if (relation.romanticInterest > 0.6f && relation.strength > 0.5f)
                relation.category = RelationshipCategory.Romantic;
            else if (relation.grudge > 0.5f)
                relation.category = RelationshipCategory.Enemy;
            else if (relation.strength > 0.7f)
                relation.category = RelationshipCategory.Friend;
            else if (relation.strength > 0.3f)
                relation.category = RelationshipCategory.Neutral;
            else if (relation.strength < -0.3f)
                relation.category = RelationshipCategory.Enemy;
            else if (relation.familiarity < 0.1f)
                relation.category = RelationshipCategory.Stranger;
            else
                relation.category = RelationshipCategory.Neutral;
        }

        private static float GetValue(Dictionary<string, float> dict, string key)
        {
            float val;
            return dict != null && dict.TryGetValue(key, out val) ? val : 0f;
        }
    }
}
