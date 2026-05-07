using System;

namespace Neshama.SoulEngine.Story
{
    /// <summary>
    /// Types of trigger conditions.
    /// Ported from Python story_trigger.py TriggerConditionType.
    /// </summary>
    public enum TriggerConditionType
    {
        EmotionThreshold,
        EmotionCombo,
        EmotionChange,
        RelationshipThreshold,
        MultiNpcCondition,
        TimeBased
    }

    /// <summary>
    /// Types of story effects.
    /// Ported from Python StoryEffectType.
    /// </summary>
    public enum StoryEffectType
    {
        SpawnQuest,
        UnlockDialogue,
        ChangeFaction,
        TriggerWorldEvent,
        ModifyNpc,
        SendNotification
    }

    /// <summary>
    /// Logical operators for combining conditions.
    /// </summary>
    public enum ConditionOperator
    {
        And,
        Or
    }
}
