#pragma once

#include "CoreMinimal.h"
#include "EmotionTypes.generated.h"

/**
 * Base emotion types (Plutchik's 8 primary emotions + Neutral).
 * Ported from Python/C# EmotionType enum.
 */
UENUM(BlueprintType)
enum class ESoulEmotionType : uint8
{
	Joy,
	Sadness,
	Anger,
	Fear,
	Surprise,
	Disgust,
	Trust,
	Anticipation,
	Shame UMETA(DisplayName = "Shame"),
	Neutral UMETA(Hidden)
};

/**
 * Game event types that trigger emotion changes.
 * Ported from Python/C# GameEventType enum.
 */
UENUM(BlueprintType)
enum class ESoulEventType : uint8
{
	PlayerAttacked UMETA(DisplayName = "Player Attacked"),
	PlayerHelped UMETA(DisplayName = "Player Helped"),
	ItemReceived UMETA(DisplayName = "Item Received"),
	ItemLost UMETA(DisplayName = "Item Lost"),
	QuestCompleted UMETA(DisplayName = "Quest Completed"),
	QuestFailed UMETA(DisplayName = "Quest Failed"),
	NpcInsulted UMETA(DisplayName = "NPC Insulted"),
	NpcComplimented UMETA(DisplayName = "NPC Complimented"),
	EnvironmentChanged UMETA(DisplayName = "Environment Changed"),
	RelationshipChanged UMETA(DisplayName = "Relationship Changed"),
	TimePassed UMETA(DisplayName = "Time Passed"),
	CombatStarted UMETA(DisplayName = "Combat Started"),
	CombatEnded UMETA(DisplayName = "Combat Ended"),
	DeathWitnessed UMETA(DisplayName = "Death Witnessed"),
	GiftGiven UMETA(DisplayName = "Gift Given")
};

/**
 * Response tone options for NPC dialogue hints.
 */
UENUM(BlueprintType)
enum class EResponseTone : uint8
{
	Friendly,
	Hostile,
	Nervous,
	Joyful,
	Sad,
	Angry,
	Fearful,
	Surprised,
	Trusting,
	Neutral,
	Proud,
	Grateful
};

/**
 * Urgency level for response hints.
 */
UENUM(BlueprintType)
enum class EUrgency : uint8
{
	Low,
	Medium,
	High
};

/**
 * Action suggestion types for NPC behavior.
 */
UENUM(BlueprintType)
enum class ESuggestedAction : uint8
{
	DialogueFriendly,
	DialogueHostile,
	DialogueCautious,
	QuestOffer,
	QuestRefuse,
	ShareInfo,
	WithholdInfo,
	Flee,
	Attack,
	GiveGift,
	ReceiveGift,
	Consolation,
	Celebration,
	Warning
};

/**
 * Emotion state as a USTRUCT. All 8 base emotions with values in [0, 1].
 * Ported from C# EmotionState.
 */
USTRUCT(BlueprintType)
struct FSoulEmotionState
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Joy = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Sadness = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Anger = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Fear = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Surprise = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Disgust = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Trust = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Anticipation = 0.0f;

	/** Get emotion value by EEmotionType. */
	float GetValue(ESoulEmotionType Type) const;

	/** Set emotion value by EEmotionType, clamped to [0,1]. */
	void SetValue(ESoulEmotionType Type, float Value);

	/** Adjust emotion by delta, clamped to [0,1]. */
	void AdjustValue(ESoulEmotionType Type, float Delta);

	/** Get the dominant emotion type and its value. */
	void GetDominant(ESoulEmotionType& OutDominantType, float& OutDominantValue) const;

	/** Clear all emotions to 0. */
	void Clear();
};

/**
 * Represents an emotion change from an event.
 */
USTRUCT(BlueprintType)
struct FEmotionDelta
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	ESoulEmotionType Emotion = ESoulEmotionType::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float BaseDelta = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float ScaledDelta = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	ESoulEventType SourceEvent = ESoulEventType::TimePassed;
};

/**
 * Result of composite emotion computation.
 */
USTRUCT(BlueprintType)
struct FCompositeEmotionResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Name = TEXT("neutral");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Intensity = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	bool bIsNovel = false;
};

/**
 * Response hint for NPC dialogue generation.
 */
USTRUCT(BlueprintType)
struct FResponseHint
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EResponseTone Tone = EResponseTone::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EUrgency Urgency = EUrgency::Low;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TArray<ESuggestedAction> SuggestedActions;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Confidence = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString Reasoning;
};

/**
 * A game event with type and intensity.
 */
USTRUCT(BlueprintType)
struct FSoulGameEvent
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	ESoulEventType EventType = ESoulEventType::TimePassed;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Intensity = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString SourceId;

	FSoulGameEvent() = default;
	FSoulGameEvent(ESoulEventType InType, float InIntensity = 1.0f, const FString& InSourceId = TEXT(""))
		: EventType(InType), Intensity(FMath::Clamp(InIntensity, 0.0f, 1.0f)), SourceId(InSourceId) {}
};

/**
 * Result of processing an event chain.
 */
USTRUCT(BlueprintType)
struct FEventChainResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString ChainId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	TArray<FEmotionDelta> TotalDeltas;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	ESoulEmotionType DominantEmotion = ESoulEmotionType::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float DominantIntensity = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	int32 EventCount = 0;
};

/**
 * Helper functions for EEmotionType.
 */
namespace EmotionTypeHelpers
{
	/** Get all base emotions (8 primary). */
	inline const TArray<ESoulEmotionType>& GetBaseEmotions()
	{
		static const TArray<ESoulEmotionType> BaseEmotions = {
			ESoulEmotionType::Joy, ESoulEmotionType::Sadness, ESoulEmotionType::Anger,
			ESoulEmotionType::Fear, ESoulEmotionType::Surprise, ESoulEmotionType::Disgust,
			ESoulEmotionType::Trust, ESoulEmotionType::Anticipation
		};
		return BaseEmotions;
	}

	/** Convert ESoulEmotionType to name string. */
	inline FString ToName(ESoulEmotionType Type)
	{
		switch (Type)
		{
		case ESoulEmotionType::Joy: return TEXT("joy");
		case ESoulEmotionType::Sadness: return TEXT("sadness");
		case ESoulEmotionType::Anger: return TEXT("anger");
		case ESoulEmotionType::Fear: return TEXT("fear");
		case ESoulEmotionType::Surprise: return TEXT("surprise");
		case ESoulEmotionType::Disgust: return TEXT("disgust");
		case ESoulEmotionType::Trust: return TEXT("trust");
		case ESoulEmotionType::Anticipation: return TEXT("anticipation");
		default: return TEXT("neutral");
		}
	}

	/** Parse name string to EEmotionType. */
	inline ESoulEmotionType FromName(const FString& Name)
	{
		if (Name == TEXT("joy")) return ESoulEmotionType::Joy;
		if (Name == TEXT("sadness")) return ESoulEmotionType::Sadness;
		if (Name == TEXT("anger")) return ESoulEmotionType::Anger;
		if (Name == TEXT("fear")) return ESoulEmotionType::Fear;
		if (Name == TEXT("surprise")) return ESoulEmotionType::Surprise;
		if (Name == TEXT("disgust")) return ESoulEmotionType::Disgust;
		if (Name == TEXT("trust")) return ESoulEmotionType::Trust;
		if (Name == TEXT("anticipation")) return ESoulEmotionType::Anticipation;
		return ESoulEmotionType::Neutral;
	}

	/** Check if emotion is "positive" for grudge factor purposes. */
	inline bool IsPositiveEmotion(ESoulEmotionType Type)
	{
		return Type == ESoulEmotionType::Joy || Type == ESoulEmotionType::Trust;
	}
}
