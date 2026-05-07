#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Emotion/EmotionTypes.h"
#include "PersonalityEvolver.generated.h"

// Forward declarations
class UOCEANPersonality;

/**
 * Personality micro-evolution system.
 * Long-term interactions cause gradual personality shifts.
 * Ported from Python/C# PersonalityEvolver.
 */
UCLASS(BlueprintType)
class NESHAMASDK_API UPersonalityEvolver : public UObject
{
	GENERATED_BODY()

public:
	UPersonalityEvolver();

	/** Maximum delta per evolution step. Keeps personality stable over short periods. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float MaxDeltaPerStep = 0.01f;

	/** Minimum interaction count before evolution can occur. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	int32 MinInteractionsForEvolution = 10;

	/** How strongly emotional experience drives personality change. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float EmotionalInfluenceStrength = 0.005f;

	/** Record that an interaction occurred. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void RecordInteraction();

	/**
	 * Evolve personality based on emotional state.
	 * High emotions over time shift personality slightly.
	 * Call this periodically (e.g., every 60 seconds of game time).
	 */
	void Evolve(UOCEANPersonality* Personality, const FEmotionState& EmotionalState);

	/** Reset the evolver state. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void Reset();

	/** Get total interaction count. */
	UFUNCTION(BlueprintCallable, Category = "Neshama", BlueprintPure)
	int32 GetTotalInteractions() const { return TotalInteractions; }

private:
	UPROPERTY()
	int32 TotalInteractions = 0;
};
