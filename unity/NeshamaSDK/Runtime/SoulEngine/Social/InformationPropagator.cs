using System;
using System.Collections.Generic;

namespace Neshama.SoulEngine.Social
{
    /// <summary>
    /// Information propagator - NPC gossip and information sharing system.
    /// Ported from Python information_propagator.py InformationPropagator.
    /// 
    /// Features:
    /// - Information spread between NPCs
    /// - Information distortion (rumors change over time)
    /// - Trust-based propagation
    /// - Information decay and forgetting
    /// - Emotion callbacks when NPCs receive info
    /// </summary>
    public class InformationPropagator
    {
        // ── Constants ────────────────────────────────────────────────────────────

        public float distortionChance = 0.15f;
        public float distortionAmount = 0.1f;
        public float decayRate = 0.001f;          // Importance decay per second
        public float minImportance = 0.1f;
        public float trustDecayPerHop = 0.1f;

        // ── Types ────────────────────────────────────────────────────────────────

        public enum InfoType
        {
            PlayerAction,
            WorldEvent,
            NpcSecret,
            QuestInfo,
            Rumor
        }

        [Serializable]
        public class Information
        {
            public string infoId;
            public InfoType infoType;
            public string originalContent;
            public string currentContent;
            public string sourceNpcId;
            public float createdAt;     // game time
            public float lastSpread;    // game time
            public float distortionLevel;
            public float credibility = 1.0f;
            public float importance = 0.5f;
            public List<string> seenBy = new List<string>();
            public int propagationCount;
            public List<string> tags = new List<string>();
        }

        // ── State ────────────────────────────────────────────────────────────────

        private Dictionary<string, Information> _information = new Dictionary<string, Information>();
        private Dictionary<string, HashSet<string>> _npcKnowledge = new Dictionary<string, HashSet<string>>();

        /// <summary>
        /// Emotion callback: called when information reaches an NPC.
        /// Parameters: (npcId, emotionDeltas dict)
        /// </summary>
        public Action<string, Dictionary<string, float>> emotionCallback;

        // Trust lookup function: (fromNpc, toNpc) → trust level
        public Func<string, string, float> trustLookup;

        private Random _random = new Random();
        private float _gameTime = 0f;

        // ── Core Methods ─────────────────────────────────────────────────────────

        /// <summary>
        /// Spread information from source NPC to target NPCs.
        /// Ported from Python spread_information().
        /// </summary>
        public Dictionary<string, object> SpreadInformation(
            string sourceNpcId, InfoType infoType, string content,
            List<string> targets, float importance = 0.5f,
            List<string> tags = null, string existingInfoId = null)
        {
            Information info;

            if (!string.IsNullOrEmpty(existingInfoId) && _information.ContainsKey(existingInfoId))
            {
                info = _information[existingInfoId];
                info.lastSpread = _gameTime;
                info.propagationCount++;
            }
            else
            {
                string infoId = existingInfoId ?? Guid.NewGuid().ToString();
                info = new Information
                {
                    infoId = infoId,
                    infoType = infoType,
                    originalContent = content,
                    currentContent = content,
                    sourceNpcId = sourceNpcId,
                    importance = importance,
                    tags = tags ?? new List<string>(),
                    createdAt = _gameTime,
                };
                _information[infoId] = info;
                AddToNpcKnowledge(sourceNpcId, infoId);
            }

            var spreadResults = new List<Dictionary<string, object>>();

            foreach (var targetId in targets)
            {
                if (targetId == sourceNpcId) continue;

                float trust = GetTrust(sourceNpcId, targetId);
                float spreadChance = trust * 0.7f + importance * 0.3f;

                if ((float)_random.NextDouble() > spreadChance)
                {
                    spreadResults.Add(new Dictionary<string, object>
                    {
                        { "target", targetId },
                        { "success", false },
                        { "reason", "low_trust" },
                    });
                    continue;
                }

                // Apply distortion for rumors
                string finalContent = info.currentContent;
                if (infoType == InfoType.Rumor)
                {
                    string distorted;
                    float distortionDelta;
                    ApplyDistortion(info.currentContent, info.distortionLevel, trust, out distorted, out distortionDelta);
                    info.distortionLevel = Math.Min(1f, info.distortionLevel + distortionDelta);
                    info.currentContent = distorted;
                    finalContent = distorted;
                }

                // Update credibility
                info.credibility = Math.Max(0.1f, info.credibility - trustDecayPerHop);

                // Add to target's knowledge
                AddToNpcKnowledge(targetId, info.infoId);

                spreadResults.Add(new Dictionary<string, object>
                {
                    { "target", targetId },
                    { "success", true },
                    { "content", finalContent },
                    { "credibility", info.credibility },
                });

                // Trigger emotion reaction
                TriggerEmotionReaction(targetId, infoType, finalContent, info.credibility, importance, sourceNpcId);
            }

            return new Dictionary<string, object>
            {
                { "info_id", info.infoId },
                { "spread_to", spreadResults },
                { "propagation_count", info.propagationCount },
                { "total_knowers", info.seenBy.Count },
            };
        }

        /// <summary>
        /// Get all information known by an NPC.
        /// </summary>
        public List<Dictionary<string, object>> GetNPCKnowledge(string npcId, int limit = 50)
        {
            HashSet<string> knownIds;
            if (!_npcKnowledge.TryGetValue(npcId, out knownIds)) return new List<Dictionary<string, object>>();

            var result = new List<Dictionary<string, object>>();
            foreach (var infoId in knownIds)
            {
                Information info;
                if (!_information.TryGetValue(infoId, out info)) continue;

                result.Add(new Dictionary<string, object>
                {
                    { "info_id", infoId },
                    { "info_type", info.infoType.ToString() },
                    { "content", info.currentContent },
                    { "credibility", info.credibility },
                    { "importance", info.importance },
                    { "is_distorted", info.distortionLevel > 0.3f },
                });

                if (result.Count >= limit) break;
            }

            return result;
        }

        /// <summary>
        /// Decay information importance over time.
        /// Ported from Python decay_information().
        /// </summary>
        public int DecayInformation(float deltaTime)
        {
            int forgottenCount = 0;
            var forgottenIds = new List<string>();

            foreach (var kv in _information)
            {
                var info = kv.Value;
                info.importance = Math.Max(0f, info.importance - decayRate * deltaTime);

                if (info.importance < minImportance)
                {
                    forgottenIds.Add(kv.Key);
                    forgottenCount++;
                }
            }

            // Remove forgotten info from all NPC knowledge
            foreach (var id in forgottenIds)
            {
                foreach (var knowledge in _npcKnowledge.Values)
                    knowledge.Remove(id);
                _information.Remove(id);
            }

            return forgottenCount;
        }

        /// <summary>
        /// Update game time. Call in Tick().
        /// </summary>
        public void Tick(float deltaTime)
        {
            _gameTime += deltaTime;
        }

        // ── Private Methods ──────────────────────────────────────────────────────

        private void AddToNpcKnowledge(string npcId, string infoId)
        {
            HashSet<string> knowledge;
            if (!_npcKnowledge.TryGetValue(npcId, out knowledge))
            {
                knowledge = new HashSet<string>();
                _npcKnowledge[npcId] = knowledge;
            }
            knowledge.Add(infoId);

            Information info;
            if (_information.TryGetValue(infoId, out info))
            {
                if (!info.seenBy.Contains(npcId))
                    info.seenBy.Add(npcId);
            }
        }

        private float GetTrust(string fromNpc, string toNpc)
        {
            if (trustLookup != null)
                return trustLookup(fromNpc, toNpc);
            return 0.5f; // Default moderate trust
        }

        /// <summary>
        /// Apply distortion to content (rumors change over time).
        /// Ported from Python _apply_distortion().
        /// </summary>
        private void ApplyDistortion(string content, float currentDistortion, float trust,
            out string result, out float distortionDelta)
        {
            float distortChance = distortionChance * (1f - trust);
            if ((float)_random.NextDouble() > distortChance)
            {
                result = content;
                distortionDelta = 0f;
                return;
            }

            string[] words = content.Split(' ');
            int type = _random.Next(4);

            if (type == 0 && words.Length > 5)
            {
                // Exaggerate: add intensifier at start
                string[] intensifiers = { "apparently", "supposedly", "allegedly" };
                var newWords = new List<string>(words);
                newWords[0] = intensifiers[_random.Next(intensifiers.Length)];
                if (newWords.Count > 1) newWords.RemoveAt(1);
                result = string.Join(" ", newWords.ToArray());
                distortionDelta = distortionAmount;
            }
            else if (type == 1 && words.Length > 8)
            {
                // Simplify: keep first 3 and last 3
                var keep = new List<string>();
                for (int i = 0; i < 3 && i < words.Length; i++) keep.Add(words[i]);
                for (int i = Math.Max(3, words.Length - 3); i < words.Length; i++) keep.Add(words[i]);
                result = string.Join(" ", keep.ToArray());
                distortionDelta = distortionAmount * 0.5f;
            }
            else if (type == 2 && words.Length > 5)
            {
                // Partial: replace a word with [...]
                var newWords = new List<string>(words);
                int idx = _random.Next(1, newWords.Count - 1);
                newWords[idx] = "[...]";
                result = string.Join(" ", newWords.ToArray());
                distortionDelta = distortionAmount * 0.3f;
            }
            else
            {
                result = content;
                distortionDelta = 0f;
            }
        }

        /// <summary>
        /// Trigger emotion reaction in target NPC.
        /// Ported from Python _trigger_emotion_reaction().
        /// Secondhand information has half the emotional impact.
        /// </summary>
        private void TriggerEmotionReaction(
            string targetNpcId, InfoType infoType, string content,
            float credibility, float importance, string sourceNpcId)
        {
            if (emotionCallback == null) return;

            var emotionDeltas = new Dictionary<string, float>();
            string contentLower = content.ToLower();

            float intensityFactor = credibility * importance * 0.5f;

            // Attack keywords
            string[] attackKw = { "attack", "hit", "kill", "fight", "hurt", "暴力", "攻击", "伤害" };
            string[] helpKw = { "help", "save", "protect", "rescue", "heal", "帮助", "拯救", "保护" };

            bool isAttack = false, isHelp = false;
            foreach (var kw in attackKw) if (contentLower.Contains(kw)) { isAttack = true; break; }
            foreach (var kw in helpKw) if (contentLower.Contains(kw)) { isHelp = true; break; }

            if (isAttack)
            {
                emotionDeltas["trust"] = -0.15f * intensityFactor;
                emotionDeltas["anger"] = 0.10f * intensityFactor;
            }
            else if (isHelp)
            {
                emotionDeltas["trust"] = 0.10f * intensityFactor;
                emotionDeltas["joy"] = 0.05f * intensityFactor;
            }
            else if (infoType == InfoType.PlayerAction)
            {
                emotionDeltas["trust"] = -0.05f * intensityFactor;
            }

            if (emotionDeltas.Count > 0)
            {
                try { emotionCallback(targetNpcId, emotionDeltas); }
                catch { /* ignore callback errors */ }
            }
        }
    }
}
