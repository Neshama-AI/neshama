using System;

namespace Neshama.SoulEngine.Behavior
{
    /// <summary>
    /// Types of behavior modifications.
    /// Ported from Python npc_behavior.py BehaviorType enum.
    /// </summary>
    public enum BehaviorType
    {
        DialogueStyleChange,
        QuestAvailabilityChange,
        FactionShift,
        ShopPriceChange,
        MovementPatternChange,
        InteractionAllowed,
        InfoSharing,
        GiftReaction
    }

    /// <summary>
    /// Dialogue style options.
    /// Ported from Python DialogueStyle enum.
    /// </summary>
    public enum DialogueStyle
    {
        Friendly,
        Hostile,
        Neutral,
        Cautious,
        Aggressive,
        Submissive,
        Excited,
        Gloomy
    }

    /// <summary>
    /// Quest availability modifiers.
    /// </summary>
    public enum QuestModifier
    {
        Available,
        AvailableWithCondition,
        Locked,
        Completed,
        Failed
    }

    /// <summary>
    /// Movement pattern options.
    /// </summary>
    public enum MovementPattern
    {
        Normal,
        AggressivePatrol,
        Defensive,
        Fleeing,
        Excited,
        Hiding
    }
}
