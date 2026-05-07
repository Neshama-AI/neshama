#pragma once

#include "CoreMinimal.h"
#include "SocialTypes.generated.h"

/**
 * Types of social interactions between NPCs.
 */
UENUM(BlueprintType)
enum class ESocialInteractionType : uint8
{
	Gossip,
	Trade,
	Argue,
	Ally,
	Betray,
	Comfort,
	Teach,
	Flirt
};

/**
 * NPC relationship categories.
 */
UENUM(BlueprintType)
enum class ERelationshipCategory : uint8
{
	Friend,
	Enemy,
	Neutral,
	Stranger,
	Romantic,
	Mentor,
	Rival
};
