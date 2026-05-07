using System;

namespace Neshama.SoulEngine.Entity
{
    /// <summary>
    /// Types of entity nodes.
    /// Ported from Python entity_graph.py EntityType.
    /// </summary>
    public enum EntityType
    {
        Person,
        Place,
        Concept,
        Event,
        Object,
        Organization,
        Abstract,
        Custom
    }

    /// <summary>
    /// Types of relationship edges.
    /// Ported from Python RelationType.
    /// </summary>
    public enum RelationType
    {
        Knows,
        LocatedAt,
        PartOf,
        Caused,
        RelatedTo,
        Likes,
        Dislikes,
        CauseOf,
        Before,
        After,
        SimilarTo,
        OwnedBy,
        CreatedBy,
        MemberOf,
        Custom
    }

    /// <summary>
    /// Edge directionality.
    /// </summary>
    public enum EdgeDirection
    {
        Directed,
        Undirected
    }
}
