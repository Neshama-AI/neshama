#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Memory/MemoryTypes.h"
#include "SoulEngine/Emotion/EmotionTypes.h"
#include "EntityMemory.generated.h"

/**
 * A single entity-related memory entry.
 * Ported from Python/C# EntityMemory.
 */
USTRUCT(BlueprintType)
struct FEntityMemory
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString MemoryId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString EntityId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString EntityName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString EventType;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Timestamp = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TMap<FString, float> EmotionalContext;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float TrustAtTime = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EMemoryImportance Importance = EMemoryImportance::Medium;
};

/**
 * NPC relation with an entity.
 * Ported from Python/C# EntityRelation.
 */
USTRUCT(BlueprintType)
struct FEntityRelation
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString EntityId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString EntityName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString RelationType = TEXT("neutral");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Strength = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Trust = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float LastInteractionTime = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	int32 InteractionCount = 0;

	FString GetStrengthCategory() const
	{
		if (Strength >= 0.8f) return TEXT("intimate");
		if (Strength >= 0.6f) return TEXT("close");
		if (Strength >= 0.4f) return TEXT("friendly");
		if (Strength >= 0.2f) return TEXT("neutral");
		if (Strength >= 0.0f) return TEXT("distant");
		return TEXT("hostile");
	}
};

/**
 * Dialogue context for NPC-Player interaction.
 * Ported from Python/C# DialogueContext.
 */
USTRUCT(BlueprintType)
struct FSoulDialogueContext
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString NpcId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString PlayerId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString PlayerName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FEntityRelation Relation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TArray<FEntityMemory> RecentMemories;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TMap<FString, float> EmotionalState;

	/** Generate prompt parts for LLM dialogue generation. */
	TArray<FString> ToPromptParts(int32 MaxMemories = 3) const;
};
