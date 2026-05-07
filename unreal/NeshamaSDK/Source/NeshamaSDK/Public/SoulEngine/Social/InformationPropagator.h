#pragma once

#include "CoreMinimal.h"
#include "InformationPropagator.generated.h"

/**
 * Types of information.
 */
UENUM(BlueprintType)
enum class EInfoType : uint8
{
	Fact,
	Rumor,
	Warning,
	QuestInfo,
	PlayerAction,
	Event,
	Secret
};

/**
 * Information item.
 */
USTRUCT(BlueprintType)
struct FInformation
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString InfoId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EInfoType InfoType = EInfoType::Fact;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString OriginalContent;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString CurrentContent;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString SourceNpcId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Importance = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Credibility = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float DistortionLevel = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float CreatedAt = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float LastSpread = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TArray<FString> SeenBy;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	int32 PropagationCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TArray<FString> Tags;
};

/**
 * Spread result for a single target.
 */
USTRUCT(BlueprintType)
struct FSpreadTargetResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Target;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	bool bSuccess = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Reason;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Content;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Credibility = 0.0f;
};

/**
 * Result of spreading information.
 */
USTRUCT(BlueprintType)
struct FSpreadResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString InfoId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TArray<FSpreadTargetResult> SpreadTo;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	int32 PropagationCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	int32 TotalKnowers = 0;
};

/**
 * Information propagator with distortion for rumors.
 * Ported from Python/C# InformationPropagator.
 */
UCLASS(BlueprintType)
class NESHAMASDK_API UInformationPropagator : public UObject
{
	GENERATED_BODY()

public:
	UInformationPropagator();

	/** Chance of distortion per hop for rumors. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float DistortionChance = 0.3f;

	/** Amount of distortion applied. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float DistortionAmount = 0.1f;

	/** Credibility decay per hop. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float TrustDecayPerHop = 0.1f;

	/** Minimum importance before information is forgotten. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float MinImportance = 0.05f;

	/** Decay rate for information importance. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float DecayRate = 0.001f;

	/** Spread information from source NPC to target NPCs. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	FSpreadResult SpreadInformation(const FString& SourceNpcId, EInfoType InfoType,
		const FString& Content, const TArray<FString>& Targets,
		float Importance = 0.5f, const TArray<FString>& Tags = TArray<FString>(),
		const FString& ExistingInfoId = TEXT(""));

	/** Get all information known by an NPC. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	TArray<FInformation> GetNPCKnowledge(const FString& NpcId, int32 Limit = 50);

	/** Decay information importance over time. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	int32 DecayInformation(float DeltaTime);

	/** Update game time. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void Tick(float DeltaTime);

	/** Trust lookup function delegate. */
	DECLARE_DELEGATE_RetVal_TwoParams(float, FOnTrustLookup, const FString& /*FromNpc*/, const FString& /*ToNpc*/);

	/** Emotion callback delegate. */
	DECLARE_DELEGATE_TwoParams(FOnEmotionCallback, const FString& /*NpcId*/, const TMap<FString, float>& /*EmotionDeltas*/);

	/** Trust lookup delegate. */
	FOnTrustLookup OnTrustLookup;

	/** Emotion callback delegate. */
	FOnEmotionCallback OnEmotionCallback;

private:
	UPROPERTY()
	TMap<FString, FInformation> InformationMap;

	TMap<FString, TSet<FString>> NpcKnowledge;

	float GameTime = 0.0f;

	void AddToNpcKnowledge(const FString& NpcId, const FString& InfoId);
	float GetTrust(const FString& FromNpc, const FString& ToNpc);
	void ApplyDistortion(const FString& Content, float CurrentDistortion, float Trust,
		FString& OutResult, float& OutDistortionDelta);
	void TriggerEmotionReaction(const FString& TargetNpcId, EInfoType InfoType,
		const FString& Content, float Credibility, float Importance, const FString& SourceNpcId);
};
