#pragma once

#include "CoreMinimal.h"
#include "OCEANPersonality.generated.h"

/**
 * OCEAN personality model. Ported from Python/C# OCEANPersonality.
 * Five-Factor Model: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism.
 * All values normalized to [0, 1].
 */
UCLASS(BlueprintType)
class NESHAMASDK_API UOCEANPersonality : public UObject
{
	GENERATED_BODY()

public:
	UOCEANPersonality();

	/** Initialize with OCEAN values. */
	void Initialize(float InOpenness, float InConscientiousness, float InExtraversion,
		float InAgreeableness, float InNeuroticism);

	// ── Five Factors ─────────────────────────────────────────────────────────

	/** 开放性 - creativity, curiosity vs conventional, practical */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|OCEAN")
	float Openness = 0.5f;

	/** 尽责性 - organized, disciplined vs flexible, casual */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|OCEAN")
	float Conscientiousness = 0.5f;

	/** 外向性 - outgoing, energetic vs reserved, solo */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|OCEAN")
	float Extraversion = 0.5f;

	/** 宜人性 - cooperative, trusting vs competitive, skeptical */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|OCEAN")
	float Agreeableness = 0.5f;

	/** 神经质 - sensitive, nervous vs resilient, confident */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|OCEAN")
	float Neuroticism = 0.5f;

	// ── Decay Modifier ──────────────────────────────────────────────────────

	/**
	 * Calculate emotion decay modifier based on neuroticism.
	 * High neuroticism = slower decay (emotions linger longer).
	 * Formula: 0.2 + 0.8 * (1 - neuroticism)
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama", BlueprintPure)
	float GetDecayModifier() const;

	// ── Personality Trait Lookup ─────────────────────────────────────────────

	/** Get trait value by name. Used for dynamic modifier lookups. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	float GetTrait(const FString& TraitName) const;

	/** Set trait value by name, clamped to [0,1]. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void SetTrait(const FString& TraitName, float Value);

	/** Adjust a trait by a delta, clamped to [0,1]. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	void AdjustTrait(const FString& TraitName, float Delta);

	// ── Presets ──────────────────────────────────────────────────────────────

	/** Apply a preset personality archetype. Returns true if preset found. */
	UFUNCTION(BlueprintCallable, Category = "Neshama")
	bool ApplyPreset(const FString& PresetName);
};

/**
 * Behavioral tendencies derived from OCEAN personality.
 */
USTRUCT(BlueprintType)
struct FBehavioralTendencies
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Creativity = 0.0f;           // openness

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Planning = 0.0f;             // conscientiousness

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Socializing = 0.0f;          // extraversion

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Cooperation = 0.0f;          // agreeableness

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float StressResistance = 0.0f;     // 1 - neuroticism

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float EmotionalSensitivity = 0.0f; // neuroticism
};
