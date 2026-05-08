#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Behavior/BehaviorTypes.h"
#include "BehaviorMapper.generated.h"

// Forward declarations
class UOCEANPersonality;

/**
 * A single behavior modification from emotion state.
 */
USTRUCT(BlueprintType)
struct FBehaviorModifier
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	ESoulBehaviorType BehaviorType = ESoulBehaviorType::DialogueStyleChange;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float ModifierValue = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	bool bEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	int32 Priority = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Description;
};

/**
 * Complete behavior profile for an NPC.
 * Ported from Python/C# BehaviorProfile.
 */
USTRUCT(BlueprintType)
struct FBehaviorProfile
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TArray<FBehaviorModifier> Modifiers;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EDialogueStyle DialogueStyle = EDialogueStyle::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EMovementPattern MovementPattern = EMovementPattern::Normal;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EQuestModifier QuestModifier = EQuestModifier::Available;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float ShopPriceMultiplier = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float FactionPointModifier = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	bool bWillTalk = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	bool bWillShareSecrets = false;
};

/**
 * Maps emotion states to game behaviors.
 * Ported from Python/C# BehaviorMapper.
 * Converts emotion intensities into actionable behavior modifiers.
 * Pure rule-based, no LLM calls.
 */
UCLASS(BlueprintType)
class NESHAMASDK_API UBehaviorMapper : public UObject
{
	GENERATED_BODY()

public:
	UBehaviorMapper();

	/** Initialize with personality reference. */
	void Initialize(UOCEANPersonality* InPersonality);

	/** Generate behavior profile from emotion state. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	FBehaviorProfile GenerateBehavior(const TMap<FString, float>& EmotionState);

private:
	UPROPERTY()
	UOCEANPersonality* Personality;

	/** Threshold config: Emotion name, threshold, behavior type, base modifier. */
	struct FThresholdConfig
	{
		FString Emotion;
		float Threshold;
		ESoulBehaviorType BehaviorType;
		float BaseModifier;
	};

	static const TArray<FThresholdConfig>& GetDefaultThresholdConfigs();
	TArray<FThresholdConfig> ApplyPersonalityModifiers();

	void DeriveDialogueStyle(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions);
	void DeriveMovementPattern(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions);
	void DeriveQuestModifier(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions);
	void DeriveShopPrice(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions);
	void DeriveFactionShift(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions);
	void DeriveInteractionFlags(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions);

	static float GetEmoValue(const TMap<FString, float>& Dict, const FString& Key);
};
