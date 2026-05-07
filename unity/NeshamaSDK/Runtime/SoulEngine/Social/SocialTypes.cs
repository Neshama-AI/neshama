using System;

namespace Neshama.SoulEngine.Social
{
    /// <summary>
    /// Types of social interactions between NPCs.
    /// Ported from Python social_engine.py SocialInteractionType.
    /// </summary>
    public enum SocialInteractionType
    {
        Gossip,
        Trade,
        Argue,
        Ally,
        Betray,
        Comfort,
        Teach,
        Flirt
    }

    /// <summary>
    /// NPC relationship categories.
    /// Ported from Python RelationshipCategory.
    /// </summary>
    public enum RelationshipCategory
    {
        Friend,
        Enemy,
        Neutral,
        Stranger,
        Romantic,
        Mentor,
        Rival
    }
}
