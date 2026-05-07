#include "SoulEngine/Emotion/SentimentAnalyzer.h"

static float GetEmoValue(const TMap<FString, float>& Dict, const FString& Key)
{
	const float* Val = Dict.Find(Key);
	return Val ? *Val : 0.0f;
}

FResponseHint FHintGenerator::Generate(
	const TMap<FString, float>& Emotions,
	const FCompositeEmotionResult& Composite)
{
	FResponseHint Hint;
	Hint.Tone = EResponseTone::Neutral;
	Hint.Urgency = EUrgency::Low;
	Hint.SuggestedActions.Add(ESuggestedAction::DialogueFriendly);
	Hint.Confidence = 0.0f;
	Hint.Reasoning = TEXT("No strong emotion detected");

	if (Emotions.Num() == 0) return Hint;

	float Anger = GetEmoValue(Emotions, TEXT("anger"));
	float Fear = GetEmoValue(Emotions, TEXT("fear"));
	float Joy = GetEmoValue(Emotions, TEXT("joy"));
	float Trust = GetEmoValue(Emotions, TEXT("trust"));
	float Sadness = GetEmoValue(Emotions, TEXT("sadness"));
	float Surprise = GetEmoValue(Emotions, TEXT("surprise"));
	float Disgust = GetEmoValue(Emotions, TEXT("disgust"));

	// Anger-based responses
	if (Anger > 0.6f)
	{
		Hint.Tone = EResponseTone::Hostile;
		Hint.Urgency = Anger > 0.8f ? EUrgency::High : EUrgency::Medium;
		Hint.SuggestedActions = { ESuggestedAction::DialogueHostile };
		if (Anger > 0.8f) Hint.SuggestedActions.Add(ESuggestedAction::QuestRefuse);
		Hint.Reasoning = FString::Printf(TEXT("High anger (%.2f)"), Anger);
	}
	else if (Anger > 0.3f)
	{
		Hint.Tone = EResponseTone::Angry;
		Hint.Urgency = EUrgency::Medium;
		Hint.SuggestedActions = { ESuggestedAction::DialogueHostile, ESuggestedAction::WithholdInfo };
		Hint.Reasoning = FString::Printf(TEXT("Moderate anger (%.2f)"), Anger);
	}
	// Fear-based responses
	else if (Fear > 0.6f)
	{
		Hint.Tone = EResponseTone::Fearful;
		Hint.Urgency = EUrgency::High;
		Hint.SuggestedActions = { ESuggestedAction::DialogueCautious, ESuggestedAction::Flee };
		Hint.Reasoning = FString::Printf(TEXT("High fear (%.2f)"), Fear);
	}
	else if (Fear > 0.3f)
	{
		Hint.Tone = EResponseTone::Nervous;
		Hint.Urgency = EUrgency::Medium;
		Hint.SuggestedActions = { ESuggestedAction::DialogueCautious };
		Hint.Reasoning = FString::Printf(TEXT("Moderate fear (%.2f)"), Fear);
	}
	// Joy-based responses
	else if (Joy > 0.5f)
	{
		Hint.Tone = EResponseTone::Joyful;
		Hint.Urgency = EUrgency::Low;
		Hint.SuggestedActions = { ESuggestedAction::DialogueFriendly, ESuggestedAction::Celebration };
		if (Trust > 0.4f)
		{
			Hint.SuggestedActions.Add(ESuggestedAction::ShareInfo);
			Hint.SuggestedActions.Add(ESuggestedAction::QuestOffer);
		}
		Hint.Reasoning = FString::Printf(TEXT("High joy (%.2f)"), Joy);
	}
	// Trust-based responses
	else if (Trust > 0.5f)
	{
		Hint.Tone = EResponseTone::Trusting;
		Hint.Urgency = EUrgency::Low;
		Hint.SuggestedActions = { ESuggestedAction::DialogueFriendly, ESuggestedAction::ShareInfo };
		if (Composite.Name == TEXT("love"))
			Hint.SuggestedActions.Add(ESuggestedAction::QuestOffer);
		Hint.Reasoning = FString::Printf(TEXT("High trust (%.2f)"), Trust);
	}
	// Sadness-based responses
	else if (Sadness > 0.4f)
	{
		Hint.Tone = EResponseTone::Sad;
		Hint.Urgency = EUrgency::Low;
		Hint.SuggestedActions = { ESuggestedAction::Consolation, ESuggestedAction::DialogueCautious };
		Hint.Reasoning = FString::Printf(TEXT("Sadness detected (%.2f)"), Sadness);
	}
	// Surprise-based responses
	else if (Surprise > 0.5f)
	{
		Hint.Tone = EResponseTone::Surprised;
		Hint.Urgency = EUrgency::Medium;
		Hint.SuggestedActions = { ESuggestedAction::DialogueCautious };
		Hint.Reasoning = FString::Printf(TEXT("Surprise detected (%.2f)"), Surprise);
	}
	// Disgust-based responses
	else if (Disgust > 0.4f)
	{
		Hint.Tone = EResponseTone::Hostile;
		Hint.Urgency = EUrgency::Medium;
		Hint.SuggestedActions = { ESuggestedAction::DialogueHostile, ESuggestedAction::QuestRefuse };
		Hint.Reasoning = FString::Printf(TEXT("Disgust detected (%.2f)"), Disgust);
	}

	// Composite emotion overrides (higher priority)
	if (Composite.Intensity > 0.5f)
	{
		if (Composite.Name == TEXT("gratitude"))
		{
			Hint.Tone = EResponseTone::Grateful;
			Hint.SuggestedActions = { ESuggestedAction::GiveGift, ESuggestedAction::ShareInfo };
			Hint.Reasoning = TEXT("Gratitude composite emotion");
		}
		else if (Composite.Name == TEXT("pride"))
		{
			Hint.Tone = EResponseTone::Proud;
			Hint.SuggestedActions = { ESuggestedAction::Celebration, ESuggestedAction::QuestOffer };
			Hint.Reasoning = TEXT("Pride composite emotion");
		}
		else if (Composite.Name == TEXT("love"))
		{
			Hint.Tone = EResponseTone::Trusting;
			Hint.SuggestedActions = { ESuggestedAction::ShareInfo, ESuggestedAction::QuestOffer };
			Hint.Reasoning = TEXT("Love composite emotion");
		}
	}

	// Calculate confidence
	int32 NumEmotions = Emotions.Num();
	if (NumEmotions <= 2) Hint.Confidence = 0.9f;
	else
	{
		float MaxIntensity = 0.0f, MinIntensity = TNumericLimits<float>::Max();
		for (const auto& KV : Emotions)
		{
			MaxIntensity = FMath::Max(MaxIntensity, KV.Value);
			MinIntensity = FMath::Min(MinIntensity, KV.Value);
		}
		if (MaxIntensity - MinIntensity > 0.5f) Hint.Confidence = 0.85f;
		else if (NumEmotions >= 4) Hint.Confidence = 0.6f;
		else Hint.Confidence = 0.75f;
	}

	return Hint;
}
