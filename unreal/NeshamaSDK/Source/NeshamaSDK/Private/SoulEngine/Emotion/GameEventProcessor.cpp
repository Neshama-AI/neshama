#include "SoulEngine/Emotion/GameEventProcessor.h"
#include "SoulEngine/Emotion/EventMappings.h"
#include "SoulEngine/Personality/OCEANPersonality.h"
#include "SoulEngine/Utils/SoulMathUtils.h"

TArray<FEmotionDelta> FGameEventProcessor::ProcessEvent(
	ESoulEventType EventType,
	float Intensity,
	const UOCEANPersonality* Personality,
	const FString& SourceId,
	const FString& RelationshipType)
{
	TArray<FEmotionDelta> Deltas;

	const auto& Mappings = FEventMappings::GetEmotionMappings();
	const TArray<FEventEmotionMapping>* FoundMappings = Mappings.Find(EventType);
	if (!FoundMappings) return Deltas;

	float GrudgeFactor = FEventMappings::GetGrudgeFactor(RelationshipType);

	for (const FEventEmotionMapping& Mapping : *FoundMappings)
	{
		float Scaled = Mapping.BaseDelta * Intensity;

		// Apply personality modifiers
		const auto& Modifiers = FEventMappings::GetPersonalityModifiers();
		const TArray<FPersonalityModifier>* FoundModifiers = Modifiers.Find(EventType);
		if (FoundModifiers)
		{
			for (const FPersonalityModifier& Mod : *FoundModifiers)
			{
				float TraitValue = Personality ? Personality->GetTrait(Mod.Trait) : 0.5f;
				if (TraitValue >= Mod.Threshold)
				{
					// Only modify positive deltas
					if (Scaled > 0.0f)
						Scaled *= Mod.Multiplier;
					break; // Only first matching modifier applies
				}
			}
		}

		// Apply grudge factor: reduce positive emotion deltas from hostile sources
		if (GrudgeFactor > 0.0f && EmotionTypeHelpers::IsPositiveEmotion(Mapping.Emotion) && Scaled > 0.0f)
		{
			float Reduction = 1.0f - GrudgeFactor;
			Scaled *= Reduction;
		}

		// Clamp to valid range
		Scaled = FMath::Clamp(Scaled, -1.0f, 1.0f);

		FEmotionDelta Delta;
		Delta.Emotion = Mapping.Emotion;
		Delta.BaseDelta = Mapping.BaseDelta;
		Delta.ScaledDelta = NeshamaSoul::SoulMathUtils::Round(Scaled);
		Delta.SourceEvent = EventType;
		Deltas.Add(Delta);
	}

	return Deltas;
}

FEventChainResult FGameEventProcessor::ProcessChain(
	const TArray<FSoulGameEvent>& Events,
	const FString& ChainId,
	const UOCEANPersonality* Personality)
{
	TMap<ESoulEmotionType, float> EmotionSums;
	TArray<FEmotionDelta> AllDeltas;

	for (const FSoulGameEvent& Evt : Events)
	{
		TArray<FEmotionDelta> Deltas = ProcessEvent(Evt.EventType, Evt.Intensity, Personality, Evt.SourceId);
		for (const FEmotionDelta& Delta : Deltas)
		{
			float& Sum = EmotionSums.FindOrAdd(Delta.Emotion, 0.0f);
			Sum += Delta.ScaledDelta;
		}
		AllDeltas.Append(Deltas);
	}

	// Create summed deltas
	TArray<FEmotionDelta> TotalDeltas;
	ESoulEmotionType DominantEmotion = ESoulEmotionType::Neutral;
	float DominantIntensity = 0.0f;

	for (const auto& KV : EmotionSums)
	{
		FEmotionDelta Delta;
		Delta.Emotion = KV.Key;
		Delta.ScaledDelta = NeshamaSoul::SoulMathUtils::Round(KV.Value);
		Delta.SourceEvent = AllDeltas.Num() > 0 ? AllDeltas[0].SourceEvent : ESoulEventType::TimePassed;
		TotalDeltas.Add(Delta);

		if (FMath::Abs(KV.Value) > DominantIntensity)
		{
			DominantIntensity = FMath::Abs(KV.Value);
			DominantEmotion = KV.Key;
		}
	}

	FEventChainResult Result;
	Result.ChainId = ChainId;
	Result.TotalDeltas = TotalDeltas;
	Result.DominantEmotion = DominantEmotion;
	Result.DominantIntensity = DominantIntensity;
	Result.EventCount = Events.Num();
	return Result;
}
