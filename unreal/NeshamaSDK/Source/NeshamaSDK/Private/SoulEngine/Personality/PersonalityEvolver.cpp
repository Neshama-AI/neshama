#include "SoulEngine/Personality/PersonalityEvolver.h"
#include "SoulEngine/Personality/OCEANPersonality.h"

UPersonalityEvolver::UPersonalityEvolver()
{
}

void UPersonalityEvolver::RecordInteraction()
{
	TotalInteractions++;
}

void UPersonalityEvolver::Evolve(UOCEANPersonality* Personality, const FSoulEmotionState& EmotionalState)
{
	if (!Personality) return;
	if (TotalInteractions < MinInteractionsForEvolution) return;

	// High joy + trust → increase extraversion, agreeableness
	float PositiveVal = (EmotionalState.Joy + EmotionalState.Trust) * 0.5f;
	if (PositiveVal > 0.5f)
	{
		float Delta = (PositiveVal - 0.5f) * EmotionalInfluenceStrength;
		Personality->AdjustTrait(TEXT("extraversion"), FMath::Min(Delta, MaxDeltaPerStep));
		Personality->AdjustTrait(TEXT("agreeableness"), FMath::Min(Delta * 0.5f, MaxDeltaPerStep));
	}

	// High fear + sadness → increase neuroticism slightly
	float NegativeVal = (EmotionalState.Fear + EmotionalState.Sadness) * 0.5f;
	if (NegativeVal > 0.5f)
	{
		float Delta = (NegativeVal - 0.5f) * EmotionalInfluenceStrength;
		Personality->AdjustTrait(TEXT("neuroticism"), FMath::Min(Delta, MaxDeltaPerStep));
	}

	// High anger + disgust → decrease agreeableness slightly
	float HostileVal = (EmotionalState.Anger + EmotionalState.Disgust) * 0.5f;
	if (HostileVal > 0.6f)
	{
		float Delta = (HostileVal - 0.6f) * EmotionalInfluenceStrength;
		Personality->AdjustTrait(TEXT("agreeableness"), -FMath::Min(Delta, MaxDeltaPerStep));
	}
}

void UPersonalityEvolver::Reset()
{
	TotalInteractions = 0;
}
