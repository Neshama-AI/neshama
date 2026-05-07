#pragma once

#include "CoreMinimal.h"
#include "EmotionTypes.generated.h"

/**
 * Base emotion types (Plutchik's 8 primary emotions + Neutral).
 * Ported from Python/C# EmotionType enum.
 */
UENUM(BlueprintType)
enum class EEmotionType : uint8
{
	Joy,
	Sadness,
	Anger,
	Fear,
	Surprise,
	Disgust,
	Trust,
	Anticipation,
	Neutral UMETA(Hidden)
};

/**
 * Game event types that trigger emotion changes.
 * Ported from Python/C# GameEventType enum.
 */
UENUM(BlueprintType)
enum class EGameEventType : uint8
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
struct FEmotionState
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
	float GetValue(EEmotionType Type) const;

	/** Set emotion value by EEmotionType, clamped to [0,1]. */
	void SetValue(EEmotionType Type, float Value);

	/** Adjust emotion by delta, clamped to [0,1]. */
	void AdjustValue(EEmotionType Type, float Delta);

	/** Get the dominant emotion type and its value. */
	void GetDominant(EEmotionType& OutDominantType, float& OutDominantValue) const;

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
	EEmotionType Emotion = EEmotionType::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float BaseDelta = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float ScaledDelta = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EGameEventType SourceEvent = EGameEventType::TimePassed;
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
struct FGameEvent
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	EGameEventType EventType = EGameEventType::TimePassed;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	float Intensity = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama")
	FString SourceId;

	FGameEvent() = default;
	FGameEvent(EGameEventType InType, float InIntensity = 1.0f, const FString& InSourceId = TEXT(""))
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
	EEmotionType DominantEmotion = EEmotionType::Neutral;

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
	inline const TArray<EEmotionType>& GetBaseEmotions()
	{
		static const TArray<EEmotionType> BaseEmotions = {
			EEmotionType::Joy, EEmotionType::Sadness, EEmotionType::Anger,
			EEmotionType::Fear, EEmotionType::Surprise, EEmotionType::Disgust,
			EEmotionType::Trust, EEmotionType::Anticipation
		};
		return BaseEmotions;
	}

	/** Convert EEmotionType to name string. */
	inline FString ToName(EEmotionType Type)
	{
		switch (Type)
		{
		case EEmotionType::Joy: return TEXT("joy");
		case EEmotionType::Sadness: return TEXT("sadness");
		case EEmotionType::Anger: return TEXT("anger");
		case EEmotionType::Fear: return TEXT("fear");
		case EEmotionType::Surprise: return TEXT("surprise");
		case EEmotionType::Disgust: return TEXT("disgust");
		case EEmotionType::Trust: return TEXT("trust");
		case EEmotionType::Anticipation: return TEXT("anticipation");
		default: return TEXT("neutral");
		}
	}

	/** Parse name string to EEmotionType. */
	inline EEmotionType FromName(const FString& Name)
	{
		if (Name == TEXT("joy")) return EEmotionType::Joy;
		if (Name == TEXT("sadness")) return EEmotionType::Sadness;
		if (Name == TEXT("anger")) return EEmotionType::Anger;
		if (Name == TEXT("fear")) return EEmotionType::Fear;
		if (Name == TEXT("surprise")) return EEmotionType::Surprise;
		if (Name == TEXT("disgust")) return EEmotionType::Disgust;
		if (Name == TEXT("trust")) return EEmotionType::Trust;
		if (Name == TEXT("anticipation")) return EEmotionType::Anticipation;
		return EEmotionType::Neutral;
	}

	/** Check if emotion is "positive" for grudge factor purposes. */
	inline bool IsPositiveEmotion(EEmotionType Type)
	{
		return Type == EEmotionType::Joy || Type == EEmotionType::Trust;
	}
}
