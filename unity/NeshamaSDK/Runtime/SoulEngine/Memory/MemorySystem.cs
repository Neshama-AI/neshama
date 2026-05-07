using System;
using System.Collections.Generic;
using System.Linq;
using Neshama.SoulEngine.Emotion;

namespace Neshama.SoulEngine.Memory
{
    /// <summary>
    /// NPC relation with an entity.
    /// Ported from Python npc_memory_bridge.py EntityRelation.
    /// </summary>
    [Serializable]
    public class EntityRelation
    {
        public string entityId;
        public string entityName;
        public string relationType = "neutral";
        public float strength = 0.3f;     // -1 to 1
        public float trust = 0.3f;        // 0 to 1
        public float lastInteractionTime; // game time
        public int interactionCount;

        public string GetStrengthCategory()
        {
            if (strength >= 0.8f) return "intimate";
            if (strength >= 0.6f) return "close";
            if (strength >= 0.4f) return "friendly";
            if (strength >= 0.2f) return "neutral";
            if (strength >= 0.0f) return "distant";
            return "hostile";
        }
    }

    /// <summary>
    /// Dialogue context for NPC-Player interaction.
    /// Ported from Python npc_memory_bridge.py DialogueContext.
    /// </summary>
    public class DialogueContext
    {
        public string npcId;
        public string playerId;
        public string playerName;
        public EntityRelation relation;
        public List<EntityMemory> recentMemories = new List<EntityMemory>();
        public Dictionary<string, float> emotionalState = new Dictionary<string, float>();

        /// <summary>
        /// Generate prompt parts for LLM dialogue generation.
        /// Ported from Python DialogueContext.to_prompt_parts().
        /// </summary>
        public List<string> ToPromptParts(int maxMemories = 3)
        {
            var parts = new List<string>();

            if (relation != null)
            {
                parts.Add($"你与{playerName}的关系是{relation.relationType}，" +
                          $"强度{relation.strength:F2}，信任度{relation.trust:F2}");
            }

            if (recentMemories != null && recentMemories.Count > 0)
            {
                var memDescs = recentMemories
                    .Take(maxMemories)
                    .Select(m => $"{m.eventType}({Truncate(m.description, 20)}...)");
                parts.Add($"你最近与{playerName}的交互：{string.Join("、", memDescs)}");
            }

            if (emotionalState != null)
            {
                var significant = emotionalState
                    .Where(kv => kv.Value > 0.2f)
                    .OrderByDescending(kv => kv.Value)
                    .Select(kv => $"{kv.Key}({kv.Value:F2})");
                var sigList = significant.ToList();
                if (sigList.Count > 0)
                {
                    parts.Add($"你当前情绪：{string.Join("、", sigList)}");
                }
            }

            return parts;
        }

        private static string Truncate(string s, int maxLen)
        {
            if (s == null) return "";
            return s.Length <= maxLen ? s : s.Substring(0, maxLen);
        }
    }

    /// <summary>
    /// Memory system for an NPC. Manages entity relations and memories.
    /// Ported from Python npc_memory_bridge.py NPCMemoryBridge (per-NPC portion).
    /// </summary>
    public class MemorySystem
    {
        /// <summary>Maximum memories per NPC before oldest are dropped.</summary>
        public int maxMemoriesPerNpc = 50;

        /// <summary>Relation decay rate per second.</summary>
        public float relationDecayRate = 0.001f;

        // Entity relations: entityId → EntityRelation
        private Dictionary<string, EntityRelation> _relations = new Dictionary<string, EntityRelation>();

        // Memories stored as list (ordered by time)
        private List<EntityMemory> _memories = new List<EntityMemory>();

        // Memory ID counter
        private int _memoryCounter = 0;

        // Game time tracker
        private float _gameTime = 0f;

        /// <summary>
        /// Current game time (in seconds). Updated by Tick().
        /// </summary>
        public float GameTime => _gameTime;

        // ── Game Event Processing ────────────────────────────────────────────────

        /// <summary>
        /// Event-to-relation mapping rules.
        /// Ported from Python EVENT_RELATION_MAPPINGS.
        /// </summary>
        private static readonly Dictionary<GameEventType, RelationMapping> EventRelationMappings =
            new Dictionary<GameEventType, RelationMapping>
        {
            { GameEventType.PlayerAttacked, new RelationMapping { relation = "hostile", strengthDelta = 0.3f, trustDelta = -0.2f } },
            { GameEventType.PlayerHelped, new RelationMapping { relation = "ally", strengthDelta = 0.3f, trustDelta = 0.2f } },
            { GameEventType.ItemReceived, new RelationMapping { relation = "friendly", strengthDelta = 0.1f, trustDelta = 0.1f } },
            { GameEventType.ItemLost, new RelationMapping { relation = "neutral", strengthDelta = -0.1f, trustDelta = -0.1f } },
            { GameEventType.QuestCompleted, new RelationMapping { relation = "ally", strengthDelta = 0.3f, trustDelta = 0.3f } },
            { GameEventType.QuestFailed, new RelationMapping { relation = "disappointed", strengthDelta = -0.2f, trustDelta = -0.1f } },
            { GameEventType.NpcInsulted, new RelationMapping { relation = "hostile", strengthDelta = 0.2f, trustDelta = -0.3f } },
            { GameEventType.NpcComplimented, new RelationMapping { relation = "friendly", strengthDelta = 0.2f, trustDelta = 0.2f } },
            { GameEventType.GiftGiven, new RelationMapping { relation = "friendly", strengthDelta = 0.2f, trustDelta = 0.3f } },
            { GameEventType.EnvironmentChanged, new RelationMapping { relation = "aware", strengthDelta = 0.1f, trustDelta = 0f } },
            { GameEventType.RelationshipChanged, new RelationMapping { relation = "connected", strengthDelta = 0.2f, trustDelta = 0f } },
            { GameEventType.CombatStarted, new RelationMapping { relation = "hostile", strengthDelta = 0.2f, trustDelta = 0f } },
            { GameEventType.CombatEnded, new RelationMapping { relation = "tense", strengthDelta = 0.0f, trustDelta = 0f } },
            { GameEventType.DeathWitnessed, new RelationMapping { relation = "shaken", strengthDelta = 0.2f, trustDelta = 0f } },
            { GameEventType.TimePassed, new RelationMapping { relation = "neutral", strengthDelta = -0.05f, trustDelta = 0f } },
        };

        // ── Core Methods ─────────────────────────────────────────────────────────

        /// <summary>
        /// Process a game event and update entity relation + memory.
        /// Ported from Python NPCMemoryBridge.on_game_event().
        /// </summary>
        public void OnGameEvent(GameEventType eventType, float intensity, string entityId, string entityName,
            Dictionary<string, float> emotionalContext = null)
        {
            RelationMapping mapping;
            if (!EventRelationMappings.TryGetValue(eventType, out mapping))
                return;

            // Get or create relation
            EntityRelation relation;
            if (!_relations.TryGetValue(entityId, out relation))
            {
                relation = new EntityRelation
                {
                    entityId = entityId,
                    entityName = entityName,
                    strength = Math.Max(0f, Math.Min(1f, 0.3f + mapping.strengthDelta * intensity)),
                    trust = Math.Max(0f, Math.Min(1f, 0.3f + mapping.trustDelta * intensity)),
                    relationType = mapping.relation,
                    lastInteractionTime = _gameTime,
                    interactionCount = 1,
                };
                _relations[entityId] = relation;
            }
            else
            {
                relation.strength = Math.Max(-1f, Math.Min(1f, relation.strength + mapping.strengthDelta * intensity));
                relation.trust = Math.Max(0f, Math.Min(1f, relation.trust + mapping.trustDelta * intensity));
                relation.relationType = mapping.relation;
                relation.lastInteractionTime = _gameTime;
                relation.interactionCount++;
            }

            // Create memory entry
            _memoryCounter++;
            var memory = new EntityMemory
            {
                memoryId = $"mem_{_memoryCounter}",
                entityId = entityId,
                entityName = entityName,
                eventType = eventType.ToString(),
                description = GenerateMemoryDescription(eventType, entityName),
                timestamp = _gameTime,
                emotionalContext = emotionalContext != null
                    ? new Dictionary<string, float>(emotionalContext)
                    : new Dictionary<string, float>(),
                trustAtTime = relation.trust,
            };
            _memories.Add(memory);

            // Trim to max
            if (_memories.Count > maxMemoriesPerNpc)
            {
                _memories = _memories.GetRange(_memories.Count - maxMemoriesPerNpc, maxMemoriesPerNpc);
            }
        }

        /// <summary>
        /// Get dialogue context for NPC-Player interaction.
        /// </summary>
        public DialogueContext GetDialogueContext(
            string npcId, string playerId, string playerName = null,
            Dictionary<string, float> emotionalState = null, int maxMemories = 5)
        {
            EntityRelation relation;
            if (!_relations.TryGetValue(playerId, out relation))
                return null;

            var memories = _memories
                .Where(m => m.entityId == playerId)
                .ToList();
            if (memories.Count > maxMemories)
                memories = memories.GetRange(memories.Count - maxMemories, maxMemories);

            return new DialogueContext
            {
                npcId = npcId,
                playerId = playerId,
                playerName = playerName ?? relation.entityName,
                relation = relation,
                recentMemories = memories,
                emotionalState = emotionalState ?? new Dictionary<string, float>(),
            };
        }

        /// <summary>
        /// Get memories about a specific entity.
        /// </summary>
        public List<EntityMemory> GetEntityMemories(string entityId, int maxCount = 10)
        {
            var result = _memories
                .Where(m => m.entityId == entityId)
                .ToList();
            if (result.Count > maxCount)
                result = result.GetRange(result.Count - maxCount, maxCount);
            result.Reverse(); // Most recent first
            return result;
        }

        /// <summary>
        /// Get NPC's relation with an entity.
        /// </summary>
        public EntityRelation GetRelation(string entityId)
        {
            EntityRelation rel;
            return _relations.TryGetValue(entityId, out rel) ? rel : null;
        }

        /// <summary>
        /// Get all relations for this NPC.
        /// </summary>
        public List<EntityRelation> GetAllRelations()
        {
            return _relations.Values.ToList();
        }

        /// <summary>
        /// Decay relations over time. Call in Tick().
        /// Ported from Python NPCMemoryBridge.decay_relations().
        /// </summary>
        public void DecayRelations(float deltaTime)
        {
            foreach (var relation in _relations.Values)
            {
                float decayFactor = 1f - (relationDecayRate * deltaTime * 0.1f);
                relation.strength *= decayFactor;

                float trustDecay = 1f - (relationDecayRate * deltaTime * 0.05f);
                relation.trust *= trustDecay;
            }
        }

        /// <summary>
        /// Update game time. Call in Tick().
        /// </summary>
        public void UpdateTime(float deltaTime)
        {
            _gameTime += deltaTime;
        }

        /// <summary>
        /// Clear all data.
        /// </summary>
        public void Clear()
        {
            _relations.Clear();
            _memories.Clear();
            _memoryCounter = 0;
        }

        // ── Memory Description Generation ────────────────────────────────────────

        private static string GenerateMemoryDescription(GameEventType eventType, string entityName)
        {
            switch (eventType)
            {
                case GameEventType.PlayerAttacked: return $"被{entityName}攻击";
                case GameEventType.PlayerHelped: return $"被{entityName}帮助";
                case GameEventType.ItemReceived: return $"从{entityName}处收到物品";
                case GameEventType.ItemLost: return $"被{entityName}夺走物品";
                case GameEventType.QuestCompleted: return $"与{entityName}完成任务";
                case GameEventType.QuestFailed: return $"与{entityName}任务失败";
                case GameEventType.NpcInsulted: return $"被{entityName}侮辱";
                case GameEventType.NpcComplimented: return $"被{entityName}称赞";
                case GameEventType.GiftGiven: return $"收到{entityName}的礼物";
                case GameEventType.EnvironmentChanged: return "环境发生变化";
                case GameEventType.RelationshipChanged: return $"与{entityName}关系改变";
                case GameEventType.CombatStarted: return $"与{entityName}开始战斗";
                case GameEventType.CombatEnded: return $"与{entityName}结束战斗";
                case GameEventType.DeathWitnessed: return $"目睹{entityName}死亡";
                case GameEventType.TimePassed: return "时间流逝";
                default: return $"与{entityName}发生未知事件";
            }
        }

        // ── Helper Struct ────────────────────────────────────────────────────────

        private struct RelationMapping
        {
            public string relation;
            public float strengthDelta;
            public float trustDelta;
        }
    }
}
