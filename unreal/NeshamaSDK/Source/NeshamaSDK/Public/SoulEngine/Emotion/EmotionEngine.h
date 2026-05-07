#pragma once

#include "CoreMinimal.h"
#include "SoulEngine/Emotion/EmotionTypes.h"
#include "EmotionEngine.generated.h"

// Forward declarations
class UOCEANPersonality;

/**
 * Conflict resolution strategy for opposing emotion pairs.
 */
UENUM(BlueprintType)
enum class EConflictStrategy : uint8
{
	Dominance,  // Higher intensity wins, loser reduced
	Cancel,     // Opposing emotions reduce each other
	Blend       // Both emotions averaged
};

/**
 * Core emotion engine. Ported from Python/C# EmotionEngine.
 *
 * Manages 8 base emotions with:
 * - Exponential decay (half-life model, decays toward 0)
 * - Conflict resolution for opposing emotion pairs
 * - Composite emotion synthesis (recipes)
 * - OCEAN personality modifiers
 * - Response hint generation
 *
 * BUG FIX NOTES (retained from Python):
 * - Decay baseline is 0, not current value (0+delta, not 0.5+delta)
 * - Attack event: anger=0.24 (0.3*0.8), NOT 0.74 (old bug was 0.5+0.24)
 */
UCLASS(BlueprintType)
class NESHAMASDK_API UEmotionEngine : public UObject
{
	GENERATED_BODY()

public:
	UEmotionEngine();

	/** Initialize with personality reference. */
	void Initialize(UOCEANPersonality* InPersonality);

	// ── Core Methods ─────────────────────────────────────────────────────────

	/** Set a base emotion intensity (overwrites previous value). */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void SetEmotion(EEmotionType Type, float Intensity);

	/**
	 * Adjust an emotion by a delta. Starts from 0 (BUG FIX: 0+delta, not 0.5+delta).
	 * This ensures PlayerAttacked → anger = 0 + 0.3*intensity = 0.24 (not 0.74)
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void AdjustEmotion(EEmotionType Type, float Delta);

	/** Get current value of a single emotion. */
	UFUNCTION(BlueprintCallable, Category = "Neshama", BlueprintPure)
	float GetEmotionValue(EEmotionType Type) const;

	/** Get the dominant emotion type. */
	UFUNCTION(BlueprintCallable, Category = "Neshama", BlueprintPure)
	EEmotionType GetDominantEmotion() const;

	/** Process a game event: apply emotion deltas. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void ProcessEvent(EGameEventType EventType, float Intensity, const FString& SourceId = TEXT(""));

	/** Apply emotion decay. Call every frame with DeltaTime. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void Tick(float DeltaTime);

	/** Synthesize composite emotion from current base emotions. */
	FCompositeEmotionResult Synthesize();

	/** Generate response hints based on current emotion state. */
	FResponseHint GenerateHint();

	/** Get current emotion state. */
	UFUNCTION(BlueprintCallable, Category = "Neshama", BlueprintPure)
	FEmotionState GetCurrentState() const { return Emotions; }

	/** Clear all emotions to 0. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void Clear();

	/** Set personality (allows runtime personality changes). */
	void SetPersonality(UOCEANPersonality* InPersonality);

	// ── Config ──────────────────────────────────────────────────────────────

	/** Base decay half-life fallback (seconds). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float BaseDecayHalfLife = 120.0f;

	/** Threshold below which emotions are dropped to 0. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	float EmotionDropThreshold = 0.01f;

	/** Conflict resolution strategy. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Config")
	EConflictStrategy ConflictStrategy = EConflictStrategy::Dominance;

private:
	/** Current emotion state. */
	UPROPERTY()
	FEmotionState Emotions;

	/** Personality reference. */
	UPROPERTY()
	UOCEANPersonality* Personality;

	/** Default decay half-lives per emotion type. */
	static const TMap<EEmotionType, float>& GetDefaultHalfLives();

	/** Apply conflict resolution for opposing emotion pairs. */
	TMap<FString, float> ResolveConflicts(const TMap<FString, float>& EmotionDict) const;

	/** Match current emotions against predefined composite recipes. */
	FCompositeEmotionResult MatchRecipe(const TMap<FString, float>& EmotionDict) const;

	/** Apply grudge factor from hostile relationships. */
	float ApplyGrudgeFactor(EGameEventType Type, float Delta, const FString& SourceId) const;

	/** Opposing emotion pairs for conflict resolution. */
	static const TArray<TPair<EEmotionType, EEmotionType>>& GetOpposingPairs();

	/** Convert EmotionState to string→float map. */
	TMap<FString, float> EmotionStateToMap() const;
};
