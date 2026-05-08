#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Emotion/EmotionTypes.h"
#include "EventMappings.generated.h"

/**
 * A single emotion mapping entry: (emotion, baseDelta).
 */
USTRUCT(BlueprintType)
struct FEventEmotionMapping
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	ESoulEmotionType Emotion = ESoulEmotionType::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float BaseDelta = 0.0f;

	FEventEmotionMapping() = default;
	FEventEmotionMapping(ESoulEmotionType InEmotion, float InBaseDelta)
		: Emotion(InEmotion), BaseDelta(InBaseDelta) {}
};

/**
 * OCEAN personality modifier entry: (Trait, Threshold, Multiplier).
 */
USTRUCT(BlueprintType)
struct FPersonalityModifier
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Trait;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Threshold = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Multiplier = 1.0f;

	FPersonalityModifier() = default;
	FPersonalityModifier(const FString& InTrait, float InThreshold, float InMultiplier)
		: Trait(InTrait), Threshold(InThreshold), Multiplier(InMultiplier) {}
};

/**
 * Static event-to-emotion mapping tables.
 * Ported from Python/C# EventMappings.
 */
class NESHAMASDK_API FEventMappings
{
public:
	/** Maps game event type to emotion deltas. */
	static const TMap<ESoulEventType, TArray<FEventEmotionMapping>>& GetEmotionMappings();

	/** OCEAN personality modifiers per event type. */
	static const TMap<ESoulEventType, TArray<FPersonalityModifier>>& GetPersonalityModifiers();

	/** Positive emotion types for grudge factor reduction. */
	static const TSet<ESoulEmotionType>& GetPositiveEmotions();

	/** Positive emotion names for grudge factor reduction. */
	static const TSet<FString>& GetPositiveEmotionNames();

	/** Relationship grudge map. Negative relationships reduce positive emotion effects. */
	static const TMap<FString, float>& GetRelationshipGrudgeMap();

	/** Get grudge factor for a relationship type. Returns 0 if not found. */
	static float GetGrudgeFactor(const FString& RelationshipType);
};
