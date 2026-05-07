#pragma once

#include "CoreMinimal.h"
#include "EntityTypes.generated.h"

/**
 * Types of entity nodes.
 */
UENUM(BlueprintType)
enum class EEntityType : uint8
{
	Person,
	Place,
	Concept,
	Event,
	Object,
	Organization,
	Abstract,
	Custom
};

/**
 * Types of relationship edges.
 */
UENUM(BlueprintType)
enum class ERelationType : uint8
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
};

/**
 * Edge directionality.
 */
UENUM(BlueprintType)
enum class EEdgeDirection : uint8
{
	Directed,
	Undirected
};
