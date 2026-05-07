using System;
using System.Collections.Generic;

namespace Neshama.SoulEngine.Story
{
    /// <summary>
    /// A single condition for story triggering.
    /// Ported from Python TriggerCondition.
    /// </summary>
    [Serializable]
    public class TriggerCondition
    {
        public TriggerConditionType conditionType;
        public string npcId;
        public string emotion;
        public float? threshold;
        public string direction; // "rising", "falling", "any"
        public float? changeMagnitude;
        public Dictionary<string, float> emotions; // For EMOTION_COMBO
        public string relationshipType;
        public string relationshipTarget;
        public float? durationSeconds;
        public ConditionOperator op = ConditionOperator.And;
    }

    /// <summary>
    /// An effect to execute when story trigger fires.
    /// </summary>
    [Serializable]
    public class StoryEffect
    {
        public StoryEffectType effectType;
        public string target;
        public Dictionary<string, object> parameters = new Dictionary<string, object>();
    }

    /// <summary>
    /// A story trigger configuration.
    /// Ported from Python StoryTrigger.
    /// </summary>
    [Serializable]
    public class StoryTrigger
    {
        public string triggerId;
        public string name;
        public string description;
        public List<TriggerCondition> conditions = new List<TriggerCondition>();
        public List<StoryEffect> effects = new List<StoryEffect>();
        public float cooldown = 60f;
        public int priority;
        public bool oneShot;
        public bool enabled = true;
    }

    /// <summary>
    /// A triggered story event.
    /// </summary>
    [Serializable]
    public class TriggeredEvent
    {
        public string eventId;
        public string triggerId;
        public string triggerName;
        public string npcId;
        public float triggeredAt; // game time
        public List<StoryEffect> effects = new List<StoryEffect>();
    }

    /// <summary>
    /// Engine for monitoring emotions and triggering story events.
    /// Ported from Python story_trigger.py StoryTriggerEngine.
    /// 
    /// Supports 6 trigger types:
    /// - EMOTION_THRESHOLD: Single emotion exceeds threshold
    /// - EMOTION_COMBO: Multiple emotions at specific levels
    /// - EMOTION_CHANGE: Rapid emotion value changes
    /// - RELATIONSHIP_THRESHOLD: NPC-player relationship reaches threshold
    /// - MULTI_NPC_CONDITION: Multiple NPCs meet conditions simultaneously
    /// - TIME_BASED: Emotion persists for specified duration
    /// </summary>
    public class StoryTriggerEngine
    {
        // ── State ────────────────────────────────────────────────────────────────

        private Dictionary<string, StoryTrigger> _triggers = new Dictionary<string, StoryTrigger>();
        private Dictionary<string, List<float>> _triggerHistory = new Dictionary<string, List<float>>();
        private HashSet<string> _firedOneShot = new HashSet<string>();

        // Emotion snapshots for change detection: npcId → (emotion → (value, gameTime))
        private Dictionary<string, Dictionary<string, EmotionSnapshot>> _emotionSnapshots =
            new Dictionary<string, Dictionary<string, EmotionSnapshot>>();

        // Duration tracking: npcId → (trackingKey → startTime)
        private Dictionary<string, Dictionary<string, float>> _durationTracking =
            new Dictionary<string, Dictionary<string, float>>();

        // Active triggered events
        private Dictionary<string, TriggeredEvent> _activeEvents = new Dictionary<string, TriggeredEvent>();

        // Callbacks
        private List<Action<TriggeredEvent>> _callbacks = new List<Action<TriggeredEvent>>();

        private float _gameTime = 0f;

        private struct EmotionSnapshot
        {
            public float value;
            public float gameTime;
        }

        // ── Registration ─────────────────────────────────────────────────────────

        /// <summary>
        /// Register a story trigger.
        /// </summary>
        public bool RegisterTrigger(StoryTrigger trigger)
        {
            if (_triggers.ContainsKey(trigger.triggerId)) return false;
            _triggers[trigger.triggerId] = trigger;
            return true;
        }

        public bool UnregisterTrigger(string triggerId)
        {
            return _triggers.Remove(triggerId);
        }

        public StoryTrigger GetTrigger(string triggerId)
        {
            StoryTrigger t;
            return _triggers.TryGetValue(triggerId, out t) ? t : null;
        }

        public List<StoryTrigger> ListTriggers()
        {
            return new List<StoryTrigger>(_triggers.Values);
        }

        public void EnableTrigger(string triggerId, bool enabled)
        {
            StoryTrigger t;
            if (_triggers.TryGetValue(triggerId, out t))
                t.enabled = enabled;
        }

        // ── Check Triggers ───────────────────────────────────────────────────────

        /// <summary>
        /// Check all triggers against current state.
        /// Ported from Python check_triggers().
        /// </summary>
        public List<TriggeredEvent> CheckTriggers(
            Dictionary<string, Dictionary<string, float>> npcEmotions = null,
            Dictionary<string, Dictionary<string, string>> npcRelationships = null)
        {
            var triggeredEvents = new List<TriggeredEvent>();
            npcEmotions = npcEmotions ?? new Dictionary<string, Dictionary<string, float>>();
            npcRelationships = npcRelationships ?? new Dictionary<string, Dictionary<string, string>>();

            // Sort by priority (higher first)
            var sorted = new List<StoryTrigger>(_triggers.Values);
            sorted.Sort((a, b) => -a.priority.CompareTo(b.priority));

            foreach (var trigger in sorted)
            {
                if (!trigger.enabled) continue;
                if (trigger.oneShot && _firedOneShot.Contains(trigger.triggerId)) continue;
                if (IsInCooldown(trigger.triggerId, trigger.cooldown)) continue;

                if (CheckConditions(trigger, npcEmotions, npcRelationships))
                {
                    var evt = FireTrigger(trigger);
                    triggeredEvents.Add(evt);

                    // Update history
                    if (!_triggerHistory.ContainsKey(trigger.triggerId))
                        _triggerHistory[trigger.triggerId] = new List<float>();
                    _triggerHistory[trigger.triggerId].Add(_gameTime);

                    if (trigger.oneShot)
                        _firedOneShot.Add(trigger.triggerId);

                    // Notify callbacks
                    foreach (var cb in _callbacks)
                    {
                        try { cb(evt); }
                        catch { /* ignore */ }
                    }
                }
            }

            return triggeredEvents;
        }

        /// <summary>
        /// Update game time. Call in Tick().
        /// </summary>
        public void Tick(float deltaTime)
        {
            _gameTime += deltaTime;
        }

        /// <summary>
        /// Subscribe to trigger events.
        /// </summary>
        public void Subscribe(Action<TriggeredEvent> callback)
        {
            _callbacks.Add(callback);
        }

        public List<TriggeredEvent> GetActiveEvents()
        {
            return new List<TriggeredEvent>(_activeEvents.Values);
        }

        // ── Private Methods ──────────────────────────────────────────────────────

        private bool IsInCooldown(string triggerId, float cooldown)
        {
            List<float> history;
            if (!_triggerHistory.TryGetValue(triggerId, out history) || history.Count == 0)
                return false;
            float lastTriggered = history[history.Count - 1];
            return (_gameTime - lastTriggered) < cooldown;
        }

        private bool CheckConditions(
            StoryTrigger trigger,
            Dictionary<string, Dictionary<string, float>> npcEmotions,
            Dictionary<string, Dictionary<string, string>> npcRelationships)
        {
            if (trigger.conditions == null || trigger.conditions.Count == 0) return false;

            foreach (var condition in trigger.conditions)
            {
                if (!CheckSingleCondition(condition, npcEmotions, npcRelationships))
                    return false; // AND logic (default)
            }
            return true;
        }

        private bool CheckSingleCondition(
            TriggerCondition condition,
            Dictionary<string, Dictionary<string, float>> npcEmotions,
            Dictionary<string, Dictionary<string, string>> npcRelationships)
        {
            switch (condition.conditionType)
            {
                case TriggerConditionType.EmotionThreshold:
                    return CheckEmotionThreshold(condition, npcEmotions);
                case TriggerConditionType.EmotionCombo:
                    return CheckEmotionCombo(condition, npcEmotions);
                case TriggerConditionType.EmotionChange:
                    return CheckEmotionChange(condition, npcEmotions);
                case TriggerConditionType.RelationshipThreshold:
                    return CheckRelationshipThreshold(condition, npcRelationships);
                case TriggerConditionType.MultiNpcCondition:
                    return CheckMultiNpc(condition, npcEmotions);
                case TriggerConditionType.TimeBased:
                    return CheckTimeBased(condition, npcEmotions);
                default: return false;
            }
        }

        private bool CheckEmotionThreshold(
            TriggerCondition cond, Dictionary<string, Dictionary<string, float>> npcEmotions)
        {
            if (cond.npcId == null || cond.emotion == null || !cond.threshold.HasValue) return false;
            Dictionary<string, float> npcEmo;
            if (!npcEmotions.TryGetValue(cond.npcId, out npcEmo)) return false;

            float value;
            if (!npcEmo.TryGetValue(cond.emotion, out value)) return false;

            string dir = cond.direction ?? "rising";
            if (dir == "falling") return value <= cond.threshold.Value;
            return value >= cond.threshold.Value;
        }

        private bool CheckEmotionCombo(
            TriggerCondition cond, Dictionary<string, Dictionary<string, float>> npcEmotions)
        {
            if (cond.npcId == null || cond.emotions == null) return false;
            Dictionary<string, float> npcEmo;
            if (!npcEmotions.TryGetValue(cond.npcId, out npcEmo)) return false;

            foreach (var kv in cond.emotions)
            {
                float value;
                if (!npcEmo.TryGetValue(kv.Key, out value) || value < kv.Value)
                    return false;
            }
            return true;
        }

        private bool CheckEmotionChange(
            TriggerCondition cond, Dictionary<string, Dictionary<string, float>> npcEmotions)
        {
            if (cond.npcId == null || cond.emotion == null || !cond.changeMagnitude.HasValue) return false;
            Dictionary<string, float> npcEmo;
            if (!npcEmotions.TryGetValue(cond.npcId, out npcEmo)) return false;

            float current = 0f;
            npcEmo.TryGetValue(cond.emotion, out current);

            // Update snapshot
            if (!_emotionSnapshots.ContainsKey(cond.npcId))
                _emotionSnapshots[cond.npcId] = new Dictionary<string, EmotionSnapshot>();

            var snapshots = _emotionSnapshots[cond.npcId];
            EmotionSnapshot snap;
            if (snapshots.TryGetValue(cond.emotion, out snap))
            {
                float change = Math.Abs(current - snap.value);

                string dir = cond.direction;
                if (dir == "rising" && current <= snap.value)
                {
                    snapshots[cond.emotion] = new EmotionSnapshot { value = current, gameTime = _gameTime };
                    return false;
                }
                if (dir == "falling" && current >= snap.value)
                {
                    snapshots[cond.emotion] = new EmotionSnapshot { value = current, gameTime = _gameTime };
                    return false;
                }

                if (change >= cond.changeMagnitude.Value)
                {
                    snapshots[cond.emotion] = new EmotionSnapshot { value = current, gameTime = _gameTime };
                    return true;
                }
            }
            else
            {
                snapshots[cond.emotion] = new EmotionSnapshot { value = current, gameTime = _gameTime };
            }
            return false;
        }

        private bool CheckRelationshipThreshold(
            TriggerCondition cond, Dictionary<string, Dictionary<string, string>> npcRelationships)
        {
            if (cond.npcId == null || cond.relationshipTarget == null || cond.relationshipType == null)
                return false;
            Dictionary<string, string> npcRels;
            if (!npcRelationships.TryGetValue(cond.npcId, out npcRels)) return false;

            string currentRel;
            if (!npcRels.TryGetValue(cond.relationshipTarget, out currentRel)) return false;
            return currentRel == cond.relationshipType;
        }

        private bool CheckMultiNpc(
            TriggerCondition cond, Dictionary<string, Dictionary<string, float>> npcEmotions)
        {
            if (cond.emotion == null || !cond.threshold.HasValue) return false;

            int count = 0;
            foreach (var kv in npcEmotions)
            {
                float value;
                if (kv.Value.TryGetValue(cond.emotion, out value) && value >= cond.threshold.Value)
                    count++;
            }
            return count >= 2;
        }

        private bool CheckTimeBased(
            TriggerCondition cond, Dictionary<string, Dictionary<string, float>> npcEmotions)
        {
            if (cond.npcId == null || cond.emotion == null || !cond.threshold.HasValue || !cond.durationSeconds.HasValue)
                return false;

            Dictionary<string, float> npcEmo;
            if (!npcEmotions.TryGetValue(cond.npcId, out npcEmo)) return false;

            float value;
            if (!npcEmo.TryGetValue(cond.emotion, out value)) return false;

            string trackingKey = cond.npcId + ":" + cond.emotion;

            if (value >= cond.threshold.Value)
            {
                if (!_durationTracking.ContainsKey(cond.npcId))
                    _durationTracking[cond.npcId] = new Dictionary<string, float>();

                if (!_durationTracking[cond.npcId].ContainsKey(trackingKey))
                    _durationTracking[cond.npcId][trackingKey] = _gameTime;

                float startTime = _durationTracking[cond.npcId][trackingKey];
                return (_gameTime - startTime) >= cond.durationSeconds.Value;
            }
            else
            {
                if (_durationTracking.ContainsKey(cond.npcId))
                    _durationTracking[cond.npcId].Remove(trackingKey);
            }
            return false;
        }

        private TriggeredEvent FireTrigger(StoryTrigger trigger)
        {
            string npcId = null;
            foreach (var cond in trigger.conditions)
            {
                if (cond.npcId != null) { npcId = cond.npcId; break; }
            }

            var evt = new TriggeredEvent
            {
                eventId = Guid.NewGuid().ToString(),
                triggerId = trigger.triggerId,
                triggerName = trigger.name,
                npcId = npcId,
                triggeredAt = _gameTime,
                effects = new List<StoryEffect>(trigger.effects),
            };

            _activeEvents[evt.eventId] = evt;
            return evt;
        }
    }
}
