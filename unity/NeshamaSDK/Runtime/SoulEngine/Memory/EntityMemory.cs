using System;
using System.Collections.Generic;
using Neshama.SoulEngine.Utils;

namespace Neshama.SoulEngine.Memory
{
    /// <summary>
    /// A single entity-related memory entry.
    /// Ported from Python npc_memory_bridge.py EntityMemory.
    /// </summary>
    [Serializable]
    public class EntityMemory
    {
        public string memoryId;
        public string entityId;
        public string entityName;
        public string eventType;
        public string description;
        public float timestamp; // Game time in seconds (not wall clock)
        public Dictionary<string, float> emotionalContext = new Dictionary<string, float>();
        public float trustAtTime;
        public MemoryImportance importance = MemoryImportance.Medium;

        public EntityMemory Clone()
        {
            return new EntityMemory
            {
                memoryId = memoryId,
                entityId = entityId,
                entityName = entityName,
                eventType = eventType,
                description = description,
                timestamp = timestamp,
                emotionalContext = new Dictionary<string, float>(emotionalContext),
                trustAtTime = trustAtTime,
                importance = importance,
            };
        }
    }
}
