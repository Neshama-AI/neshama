#pragma once

#include "CoreMinimal.h"
#include "BehaviorTypes.generated.h"

/**
 * Types of behavior modifications.
 * Ported from Python/C# BehaviorType enum.
 */
UENUM(BlueprintType)
enum class EBehaviorType : uint8
{
	DialogueStyleChange,
	QuestAvailabilityChange,
	FactionShift,
	ShopPriceChange,
	MovementPatternChange,
	InteractionAllowed,
	InfoSharing,
	GiftReaction
};

/**
 * Dialogue style options.
 */
UENUM(BlueprintType)
enum class EDialogueStyle : uint8
{
	Friendly,
	Hostile,
	Neutral,
	Cautious,
	Aggressive,
	Submissive,
	Excited,
	Gloomy
};

/**
 * Quest availability modifiers.
 */
UENUM(BlueprintType)
enum class EQuestModifier : uint8
{
	Available,
	AvailableWithCondition,
	Locked,
	Completed,
	Failed
};

/**
 * Movement pattern options.
 */
UENUM(BlueprintType)
enum class EMovementPattern : uint8
{
	Normal,
	AggressivePatrol,
	Defensive,
	Fleeing,
	Excited,
	Hiding
};
