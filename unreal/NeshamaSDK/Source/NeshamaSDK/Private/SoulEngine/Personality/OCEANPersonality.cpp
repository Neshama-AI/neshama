#include "SoulEngine/Personality/OCEANPersonality.h"
#include "SoulEngine/Utils/SoulMathUtils.h"

UOCEANPersonality::UOCEANPersonality()
{
}

void UOCEANPersonality::Initialize(float InOpenness, float InConscientiousness, float InExtraversion,
	float InAgreeableness, float InNeuroticism)
{
	Openness = NeshamaSoul::SoulMathUtils::Clamp01(InOpenness);
	Conscientiousness = NeshamaSoul::SoulMathUtils::Clamp01(InConscientiousness);
	Extraversion = NeshamaSoul::SoulMathUtils::Clamp01(InExtraversion);
	Agreeableness = NeshamaSoul::SoulMathUtils::Clamp01(InAgreeableness);
	Neuroticism = NeshamaSoul::SoulMathUtils::Clamp01(InNeuroticism);
}

float UOCEANPersonality::GetDecayModifier() const
{
	float Modifier = 0.2f + 0.8f * (1.0f - Neuroticism);
	return FMath::Max(0.1f, Modifier); // minimum 10% decay speed
}

float UOCEANPersonality::GetTrait(const FString& TraitName) const
{
	FString Lower = TraitName.ToLower();
	if (Lower == TEXT("openness")) return Openness;
	if (Lower == TEXT("conscientiousness")) return Conscientiousness;
	if (Lower == TEXT("extraversion")) return Extraversion;
	if (Lower == TEXT("agreeableness")) return Agreeableness;
	if (Lower == TEXT("neuroticism")) return Neuroticism;
	return 0.5f;
}

void UOCEANPersonality::SetTrait(const FString& TraitName, float Value)
{
	Value = NeshamaSoul::SoulMathUtils::Clamp01(Value);
	FString Lower = TraitName.ToLower();
	if (Lower == TEXT("openness")) Openness = Value;
	else if (Lower == TEXT("conscientiousness")) Conscientiousness = Value;
	else if (Lower == TEXT("extraversion")) Extraversion = Value;
	else if (Lower == TEXT("agreeableness")) Agreeableness = Value;
	else if (Lower == TEXT("neuroticism")) Neuroticism = Value;
}

void UOCEANPersonality::AdjustTrait(const FString& TraitName, float Delta)
{
	float Current = GetTrait(TraitName);
	SetTrait(TraitName, Current + Delta);
}

bool UOCEANPersonality::ApplyPreset(const FString& PresetName)
{
	FString Lower = PresetName.ToLower();

	// Preset personality archetypes
	if (Lower == TEXT("analyst"))
	{
		Initialize(0.8f, 0.7f, 0.3f, 0.4f, 0.5f);
		return true;
	}
	if (Lower == TEXT("helper"))
	{
		Initialize(0.5f, 0.6f, 0.7f, 0.9f, 0.4f);
		return true;
	}
	if (Lower == TEXT("explorer"))
	{
		Initialize(0.9f, 0.4f, 0.7f, 0.5f, 0.4f);
		return true;
	}
	if (Lower == TEXT("leader"))
	{
		Initialize(0.6f, 0.8f, 0.8f, 0.5f, 0.4f);
		return true;
	}
	if (Lower == TEXT("diplomat"))
	{
		Initialize(0.7f, 0.6f, 0.6f, 0.8f, 0.4f);
		return true;
	}
	if (Lower == TEXT("sentinel"))
	{
		Initialize(0.3f, 0.9f, 0.4f, 0.7f, 0.4f);
		return true;
	}
	if (Lower == TEXT("neshama"))
	{
		Initialize(0.75f, 0.65f, 0.55f, 0.6f, 0.45f);
		return true;
	}
	return false;
}
