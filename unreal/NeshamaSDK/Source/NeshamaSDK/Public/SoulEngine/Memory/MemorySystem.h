#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Memory/EntityMemory.h"
#include "MemorySystem.generated.h"

/**
 * Memory system for an NPC. Manages entity relations and memories.
 * Ported from Python/C# MemorySystem.
 */
UCLASS(BlueprintType)
class NESHAMASDK_API UMemorySystem : public UObject
{
	GENERATED_BODY()

public:
	UMemorySystem();

	/** Maximum memories per NPC before oldest are dropped. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	int32 MaxMemoriesPerNpc = 50;

	/** Relation decay rate per second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float RelationDecayRate = 0.001f;

	// ── Core Methods ─────────────────────────────────────────────────────────

	/** Process a game event and update entity relation + memory. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void OnGameEvent(ESoulEventType EventType, float Intensity,
		const FString& EntityId, const FString& EntityName,
		const TMap<FString, float>& EmotionalContext);

	/** Get dialogue context for NPC-Player interaction. */
	bool GetDialogueContext(const FString& NpcId, const FString& PlayerId,
		const FString& PlayerName, const TMap<FString, float>& EmotionalState,
		int32 MaxMemories, FDialogueContext& OutContext);

	/** Get memories about a specific entity. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	TArray<FEntityMemory> GetEntityMemories(const FString& EntityId, int32 MaxCount = 10);

	/** Get NPC's relation with an entity. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	bool GetRelation(const FString& EntityId, FEntityRelation& OutRelation);

	/** Get all relations for this NPC. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	TArray<FEntityRelation> GetAllRelations();

	/** Decay relations over time. Call in Tick(). */
	void DecayRelations(float DeltaTime);

	/** Update game time. Call in Tick(). */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void UpdateTime(float DeltaTime);

	/** Get current game time. */
	UFUNCTION(BlueprintCallable, Category = "Neshama", BlueprintPure)
	float GetGameTime() const { return GameTime; }

	/** Clear all data. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void Clear();

private:
	/** Entity relations: EntityId → FEntityRelation */
	UPROPERTY()
	TMap<FString, FEntityRelation> Relations;

	/** Memories stored as list (ordered by time) */
	UPROPERTY()
	TArray<FEntityMemory> Memories;

	/** Memory ID counter */
	int32 MemoryCounter = 0;

	/** Game time tracker */
	float GameTime = 0.0f;

	/** Relation mapping for events */
	struct FRelationMapping
	{
		FString Relation;
		float StrengthDelta;
		float TrustDelta;
	};

	static const TMap<ESoulEventType, FRelationMapping>& GetEventRelationMappings();
	static FString GenerateMemoryDescription(ESoulEventType EventType, const FString& EntityName);
};
