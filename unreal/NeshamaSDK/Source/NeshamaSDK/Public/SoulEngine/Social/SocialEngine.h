#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Social/NeshamaSocialTypes.h"
#include "SocialEngine.generated.h"

// Forward declarations
class UOCEANPersonality;

/**
 * Relationship between two NPCs.
 */
USTRUCT(BlueprintType)
struct FNPCRelation
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString NpcAId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString NpcBId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Strength = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Trust = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Familiarity = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	int32 InteractionCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float LastInteractionTime = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	ERelationshipCategory Category = ERelationshipCategory::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Grudge = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Bond = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float RomanticInterest = 0.0f;
};

/**
 * Record of a social interaction.
 */
USTRUCT(BlueprintType)
struct FSocialEvent
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString EventId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString NpcAId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString NpcBId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	ESocialInteractionType InteractionType = ESocialInteractionType::Gossip;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Timestamp = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	bool bSuccess = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TMap<FString, float> RelationshipDelta;
};

/**
 * Social engine managing NPC-to-NPC relationships.
 * Ported from Python/C# SocialEngine.
 */
UCLASS(BlueprintType)
class NESHAMASDK_API USocialEngine : public UObject
{
	GENERATED_BODY()

public:
	USocialEngine();

	/** Min seconds between same-NPC-pair interactions. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float MinInteractionInterval = 30.0f;

	/** Max autonomous social interactions per tick. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	int32 MaxInteractionsPerTick = 3;

	/** Trust threshold for deep interactions. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float TrustThresholdForDeep = 0.7f;

	/** Familiarity threshold. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float FamiliarityThreshold = 0.3f;

	/** Register an NPC with the social engine. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void RegisterNPC(const FString& NpcId, UOCEANPersonality* Personality,
		const TMap<FString, float>& Emotions);

	/** Register an NPC with the social engine (without initial emotions). */
	UFUNCTION(BlueprintCallable, Category = "Neshama",
		meta = (DisplayName = "Register NPC"))
	void RegisterNPCSimple(const FString& NpcId, UOCEANPersonality* Personality = nullptr);

	/** Update NPC emotion state. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void UpdateNPCEmotions(const FString& NpcId, const TMap<FString, float>& Emotions);

	/** Initiate a social interaction between two NPCs. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	FSocialEvent InitiateInteraction(const FString& NpcAId, const FString& NpcBId,
		ESocialInteractionType ForcedType = ESocialInteractionType::Gossip,
		bool bForceType = false);

	/** Get relationship between two NPCs. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	bool GetRelation(const FString& NpcAId, const FString& NpcBId, FNPCRelation& OutRelation);

	/** Update game time. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void Tick(float DeltaTime);

	/** Get current game time. */
	UFUNCTION(BlueprintCallable, Category = "Neshama", BlueprintPure)
	float GetGameTime() const { return GameTime; }

private:
	/** Relations: key = sorted pair → NPCRelation */
	UPROPERTY()
	TMap<FString, FNPCRelation> Relations;

	/** NPC profiles */
	UPROPERTY()
	TMap<FString, UOCEANPersonality*> NpcPersonalities;

	/** NPC emotions */
	TMap<FString, TMap<FString, float>> NpcEmotions;

	/** Last interaction times */
	TMap<FString, float> LastInteractionTimes;

	/** Social event history */
	UPROPERTY()
	TArray<FSocialEvent> SocialEvents;

	int32 MaxEvents = 1000;
	float GameTime = 0.0f;

	static FString GetRelationKey(const FString& A, const FString& B);
	FNPCRelation* GetOrCreateRelation(const FString& NpcAId, const FString& NpcBId);

	ESocialInteractionType DecideInteractionType(
		UOCEANPersonality* PersonalityA, const TMap<FString, float>& EmotionsA,
		UOCEANPersonality* PersonalityB, const TMap<FString, float>& EmotionsB,
		const FNPCRelation& Relation);

	TMap<FString, float> CalculateInteractionEffects(
		ESocialInteractionType Type, UOCEANPersonality* PersonalityA,
		UOCEANPersonality* PersonalityB, const FNPCRelation& Relation);

	void ApplyRelationDelta(FNPCRelation& Relation, const TMap<FString, float>& Delta);
};
