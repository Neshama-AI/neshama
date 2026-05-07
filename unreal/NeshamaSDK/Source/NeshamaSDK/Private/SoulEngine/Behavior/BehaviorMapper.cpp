#include "SoulEngine/Behavior/BehaviorMapper.h"
#include "SoulEngine/Personality/OCEANPersonality.h"
#include "SoulEngine/Utils/SoulMathUtils.h"

UBehaviorMapper::UBehaviorMapper()
	: Personality(nullptr)
{
}

void UBehaviorMapper::Initialize(UOCEANPersonality* InPersonality)
{
	Personality = InPersonality;
}

const TArray<UBehaviorMapper::FThresholdConfig>& UBehaviorMapper::GetDefaultThresholdConfigs()
{
	static TArray<FThresholdConfig> Configs;
	if (Configs.Num() > 0) return Configs;

	// High anger thresholds
	Configs.Add({TEXT("anger"), 0.7f, EBehaviorType::InteractionAllowed, -0.3f});
	Configs.Add({TEXT("anger"), 0.8f, EBehaviorType::InfoSharing, -1.0f});
	// High fear thresholds
	Configs.Add({TEXT("fear"), 0.6f, EBehaviorType::MovementPatternChange, 0.0f}); // fleeing
	Configs.Add({TEXT("fear"), 0.7f, EBehaviorType::InteractionAllowed, -0.4f});
	Configs.Add({TEXT("fear"), 0.8f, EBehaviorType::DialogueStyleChange, -0.5f}); // submissive
	// High joy thresholds
	Configs.Add({TEXT("joy"), 0.6f, EBehaviorType::QuestAvailabilityChange, 0.3f});
	Configs.Add({TEXT("joy"), 0.7f, EBehaviorType::ShopPriceChange, -0.1f}); // 10% discount
	Configs.Add({TEXT("joy"), 0.8f, EBehaviorType::InfoSharing, 0.5f});
	// High trust thresholds
	Configs.Add({TEXT("trust"), 0.6f, EBehaviorType::InfoSharing, 0.4f});
	Configs.Add({TEXT("trust"), 0.8f, EBehaviorType::QuestAvailabilityChange, 0.5f});
	Configs.Add({TEXT("trust"), 0.8f, EBehaviorType::GiftReaction, 0.5f});
	// High sadness thresholds
	Configs.Add({TEXT("sadness"), 0.5f, EBehaviorType::DialogueStyleChange, -0.3f});
	Configs.Add({TEXT("sadness"), 0.7f, EBehaviorType::QuestAvailabilityChange, -0.2f});
	Configs.Add({TEXT("sadness"), 0.8f, EBehaviorType::MovementPatternChange, 0.0f}); // hiding
	// High disgust thresholds
	Configs.Add({TEXT("disgust"), 0.5f, EBehaviorType::InteractionAllowed, -0.3f});
	Configs.Add({TEXT("disgust"), 0.7f, EBehaviorType::ShopPriceChange, 0.2f}); // 20% markup
	Configs.Add({TEXT("disgust"), 0.8f, EBehaviorType::InfoSharing, -0.8f});

	return Configs;
}

TArray<UBehaviorMapper::FThresholdConfig> UBehaviorMapper::ApplyPersonalityModifiers()
{
	TArray<FThresholdConfig> Modified;

	for (const FThresholdConfig& Config : GetDefaultThresholdConfigs())
	{
		float ThresholdMod = Config.Threshold;

		// High agreeableness = lower thresholds for positive behaviors
		if (Config.BehaviorType == EBehaviorType::InfoSharing ||
			Config.BehaviorType == EBehaviorType::QuestAvailabilityChange)
		{
			if (Personality)
			{
				float Agreeableness = Personality->Agreeableness;
				if (Agreeableness > 0.6f)
					ThresholdMod = ThresholdMod * (1.0f - (Agreeableness - 0.6f) * 0.3f);
			}
		}

		// High neuroticism = lower thresholds for fear/anger responses
		if (Config.BehaviorType == EBehaviorType::MovementPatternChange ||
			Config.BehaviorType == EBehaviorType::InteractionAllowed)
		{
			if (Personality)
			{
				float Neuroticism = Personality->Neuroticism;
				if (Neuroticism > 0.6f)
					ThresholdMod = ThresholdMod * (1.0f - (Neuroticism - 0.6f) * 0.2f);
			}
		}

		Modified.Add({Config.Emotion, ThresholdMod, Config.BehaviorType, Config.BaseModifier});
	}

	return Modified;
}

FBehaviorProfile UBehaviorMapper::GenerateBehavior(const TMap<FString, float>& EmotionState)
{
	FBehaviorProfile Profile;
	TArray<FThresholdConfig> Thresholds = ApplyPersonalityModifiers();

	// Check each threshold
	for (const FThresholdConfig& Config : Thresholds)
	{
		float Intensity = GetEmoValue(EmotionState, Config.Emotion);
		if (Intensity >= Config.Threshold)
		{
			float Overflow = Intensity - Config.Threshold;
			float ScaledModifier = Config.BaseModifier * (1.0f + Overflow);

			FBehaviorModifier Mod;
			Mod.BehaviorType = Config.BehaviorType;
			Mod.ModifierValue = NeshamaSoul::SoulMathUtils::Round(ScaledModifier);
			Mod.bEnabled = true;
			Mod.Priority = static_cast<int32>(Intensity * 10);
			Mod.Description = FString::Printf(TEXT("Emotion %s (%.2f) affects %d"),
				*Config.Emotion, Intensity, static_cast<int32>(Config.BehaviorType));
			Profile.Modifiers.Add(Mod);
		}
	}

	// Derive aggregate behaviors
	DeriveDialogueStyle(Profile, EmotionState);
	DeriveMovementPattern(Profile, EmotionState);
	DeriveQuestModifier(Profile, EmotionState);
	DeriveShopPrice(Profile, EmotionState);
	DeriveFactionShift(Profile, EmotionState);
	DeriveInteractionFlags(Profile, EmotionState);

	return Profile;
}

void UBehaviorMapper::DeriveDialogueStyle(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions)
{
	float Anger = GetEmoValue(Emotions, TEXT("anger"));
	float Fear = GetEmoValue(Emotions, TEXT("fear"));
	float Joy = GetEmoValue(Emotions, TEXT("joy"));
	float Sadness = GetEmoValue(Emotions, TEXT("sadness"));

	if (Anger > 0.5f) Profile.DialogueStyle = EDialogueStyle::Aggressive;
	else if (Fear > 0.5f) Profile.DialogueStyle = EDialogueStyle::Submissive;
	else if (Joy > 0.5f) Profile.DialogueStyle = EDialogueStyle::Excited;
	else if (Sadness > 0.4f) Profile.DialogueStyle = EDialogueStyle::Gloomy;
	else if (Anger > 0.3f || Fear > 0.3f) Profile.DialogueStyle = EDialogueStyle::Cautious;
	else Profile.DialogueStyle = EDialogueStyle::Neutral;
}

void UBehaviorMapper::DeriveMovementPattern(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions)
{
	float Fear = GetEmoValue(Emotions, TEXT("fear"));
	float Anger = GetEmoValue(Emotions, TEXT("anger"));
	float Joy = GetEmoValue(Emotions, TEXT("joy"));
	float Sadness = GetEmoValue(Emotions, TEXT("sadness"));

	if (Fear > 0.6f) Profile.MovementPattern = EMovementPattern::Fleeing;
	else if (Sadness > 0.6f) Profile.MovementPattern = EMovementPattern::Hiding;
	else if (Anger > 0.6f) Profile.MovementPattern = EMovementPattern::AggressivePatrol;
	else if (Fear > 0.4f || Anger > 0.4f) Profile.MovementPattern = EMovementPattern::Defensive;
	else if (Joy > 0.5f) Profile.MovementPattern = EMovementPattern::Excited;
	else Profile.MovementPattern = EMovementPattern::Normal;
}

void UBehaviorMapper::DeriveQuestModifier(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions)
{
	float Anger = GetEmoValue(Emotions, TEXT("anger"));
	float Trust = GetEmoValue(Emotions, TEXT("trust"));
	float Sadness = GetEmoValue(Emotions, TEXT("sadness"));

	if (Anger > 0.7f) Profile.QuestModifier = EQuestModifier::Locked;
	else if (Trust > 0.7f) Profile.QuestModifier = EQuestModifier::Available;
	else if (Sadness > 0.5f) Profile.QuestModifier = EQuestModifier::AvailableWithCondition;
	else Profile.QuestModifier = EQuestModifier::Available;
}

void UBehaviorMapper::DeriveShopPrice(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions)
{
	float Joy = GetEmoValue(Emotions, TEXT("joy"));
	float Trust = GetEmoValue(Emotions, TEXT("trust"));
	float Anger = GetEmoValue(Emotions, TEXT("anger"));
	float Disgust = GetEmoValue(Emotions, TEXT("disgust"));

	float Multiplier = 1.0f;

	// Positive emotions = discount
	if (Joy > 0.5f) Multiplier -= 0.1f * Joy;
	if (Trust > 0.5f) Multiplier -= 0.1f * Trust;

	// Negative emotions = markup
	if (Anger > 0.4f) Multiplier += 0.15f * Anger;
	if (Disgust > 0.4f) Multiplier += 0.2f * Disgust;

	Profile.ShopPriceMultiplier = FMath::Clamp(Multiplier, 0.5f, 2.0f);
}

void UBehaviorMapper::DeriveFactionShift(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions)
{
	float Anger = GetEmoValue(Emotions, TEXT("anger"));
	float Disgust = GetEmoValue(Emotions, TEXT("disgust"));
	float Trust = GetEmoValue(Emotions, TEXT("trust"));
	float Joy = GetEmoValue(Emotions, TEXT("joy"));

	float Shift = 0.0f;
	if (Trust > 0.4f) Shift += 0.1f * Trust;
	if (Joy > 0.4f) Shift += 0.1f * Joy;
	if (Anger > 0.4f) Shift -= 0.15f * Anger;
	if (Disgust > 0.4f) Shift -= 0.1f * Disgust;

	Profile.FactionPointModifier = FMath::Clamp(Shift, -1.0f, 1.0f);
}

void UBehaviorMapper::DeriveInteractionFlags(FBehaviorProfile& Profile, const TMap<FString, float>& Emotions)
{
	float Anger = GetEmoValue(Emotions, TEXT("anger"));
	float Fear = GetEmoValue(Emotions, TEXT("fear"));
	float Disgust = GetEmoValue(Emotions, TEXT("disgust"));
	float Trust = GetEmoValue(Emotions, TEXT("trust"));

	// Will talk
	if (Anger > 0.8f || Fear > 0.8f || Disgust > 0.8f)
		Profile.bWillTalk = false;
	else if (Anger > 0.5f || Fear > 0.6f || Disgust > 0.5f)
		Profile.bWillTalk = false;
	else
		Profile.bWillTalk = true;

	// Will share secrets
	if (Trust > 0.7f) Profile.bWillShareSecrets = true;
	else if (Anger > 0.3f || Fear > 0.4f) Profile.bWillShareSecrets = false;
	else Profile.bWillShareSecrets = false;
}

float UBehaviorMapper::GetEmoValue(const TMap<FString, float>& Dict, const FString& Key)
{
	const float* Val = Dict.Find(Key);
	return Val ? *Val : 0.0f;
}
