#include "SoulEngine/Emotion/EmotionEngine.h"
#include "SoulEngine/Emotion/GameEventProcessor.h"
#include "SoulEngine/Emotion/CompositeEmotion.h"
#include "SoulEngine/Emotion/SentimentAnalyzer.h"
#include "SoulEngine/Personality/OCEANPersonality.h"
#include "SoulEngine/Emotion/EventMappings.h"
#include "SoulEngine/Utils/SoulMathUtils.h"

UEmotionEngine::UEmotionEngine()
	: Personality(nullptr)
{
}

void UEmotionEngine::Initialize(UOCEANPersonality* InPersonality)
{
	Personality = InPersonality;
}

// ── Core Methods ─────────────────────────────────────────────────────────────

void UEmotionEngine::SetEmotion(EEmotionType Type, float Intensity)
{
	Emotions.SetValue(Type, Intensity);
}

void UEmotionEngine::AdjustEmotion(EEmotionType Type, float Delta)
{
	// BUG FIX: baseline is 0, not current. When emotion doesn't exist, start from 0.
	// This ensures PlayerAttacked → anger = 0 + 0.3*intensity = 0.24 (not 0.74)
	float Current = Emotions.GetValue(Type);
	Emotions.SetValue(Type, Current + Delta);
}

float UEmotionEngine::GetEmotionValue(EEmotionType Type) const
{
	return Emotions.GetValue(Type);
}

EEmotionType UEmotionEngine::GetDominantEmotion() const
{
	EEmotionType DomType;
	float DomValue;
	Emotions.GetDominant(DomType, DomValue);
	return DomType;
}

void UEmotionEngine::ProcessEvent(EGameEventType EventType, float Intensity, const FString& SourceId)
{
	TArray<FEmotionDelta> Deltas = FGameEventProcessor::ProcessEvent(EventType, Intensity, Personality, SourceId);
	for (const FEmotionDelta& Delta : Deltas)
	{
		AdjustEmotion(Delta.Emotion, Delta.ScaledDelta);
	}
}

void UEmotionEngine::Tick(float DeltaTime)
{
	if (DeltaTime <= 0.0f) return;

	float DecayModifier = Personality ? Personality->GetDecayModifier() : 1.0f;

	for (EEmotionType Type : EmotionTypeHelpers::GetBaseEmotions())
	{
		float Current = Emotions.GetValue(Type);
		if (Current < EmotionDropThreshold)
		{
			Emotions.SetValue(Type, 0.0f);
			continue;
		}

		const auto& HalfLives = GetDefaultHalfLives();
		const float* HalfLifePtr = HalfLives.Find(Type);
		float HalfLife = HalfLifePtr ? *HalfLifePtr : BaseDecayHalfLife;

		float AdjustedHalfLife = HalfLife * DecayModifier;

		// Exponential decay toward 0
		float Decayed = NeshamaSoul::SoulMathUtils::ExponentialDecay(Current, DeltaTime, AdjustedHalfLife);
		Emotions.SetValue(Type, Decayed);
	}
}

FCompositeEmotionResult UEmotionEngine::Synthesize()
{
	TMap<FString, float> AllEmotions = EmotionStateToMap();
	if (AllEmotions.Num() == 0)
	{
		FCompositeEmotionResult Result;
		Result.Name = TEXT("neutral");
		Result.Intensity = 0.0f;
		Result.bIsNovel = false;
		return Result;
	}

	// Apply conflict resolution
	TMap<FString, float> Resolved = ResolveConflicts(AllEmotions);

	// Sort by intensity descending
	TArray<TPair<FString, float>> Sorted;
	for (const auto& KV : Resolved)
	{
		Sorted.Add(TPair<FString, float>(KV.Key, KV.Value));
	}
	Sorted.Sort([](const TPair<FString, float>& A, const TPair<FString, float>& B)
	{
		return B.Value < A.Value;
	});

	// Single dominant emotion
	if (Sorted.Num() == 1)
	{
		FCompositeEmotionResult Result;
		Result.Name = Sorted[0].Key;
		Result.Intensity = Sorted[0].Value;
		Result.bIsNovel = false;
		return Result;
	}

	// Try predefined recipes
	FCompositeEmotionResult Composite = MatchRecipe(Resolved);
	if (!Composite.Name.IsEmpty() && Composite.Name != TEXT("neutral"))
		return Composite;

	// Ad-hoc composite: top 2 base emotions
	if (Sorted.Num() >= 2)
	{
		float Intensity = (Sorted[0].Value + Sorted[1].Value) * 0.5f * 1.1f; // slight boost
		FCompositeEmotionResult Result;
		Result.Name = Sorted[0].Key + TEXT("+") + Sorted[1].Key;
		Result.Intensity = FMath::Min(1.0f, Intensity);
		Result.bIsNovel = true;
		return Result;
	}

	FCompositeEmotionResult Result;
	Result.Name = Sorted[0].Key;
	Result.Intensity = Sorted[0].Value;
	Result.bIsNovel = false;
	return Result;
}

FResponseHint UEmotionEngine::GenerateHint()
{
	TMap<FString, float> EmoDict = EmotionStateToMap();
	FCompositeEmotionResult Composite = Synthesize();
	return FHintGenerator::Generate(EmoDict, Composite);
}

void UEmotionEngine::Clear()
{
	Emotions.Clear();
}

void UEmotionEngine::SetPersonality(UOCEANPersonality* InPersonality)
{
	Personality = InPersonality ? InPersonality : nullptr;
}

float UEmotionEngine::ApplyGrudgeFactor(EGameEventType Type, float Delta, const FString& SourceId) const
{
	// Grudge factor is now handled in GameEventProcessor
	return Delta;
}

// ── Private Methods ──────────────────────────────────────────────────────────

const TMap<EEmotionType, float>& UEmotionEngine::GetDefaultHalfLives()
{
	static TMap<EEmotionType, float> HalfLives;
	if (HalfLives.Num() > 0) return HalfLives;

	HalfLives.Add(EEmotionType::Joy, 120.0f);
	HalfLives.Add(EEmotionType::Sadness, 180.0f);
	HalfLives.Add(EEmotionType::Anger, 90.0f);
	HalfLives.Add(EEmotionType::Fear, 60.0f);
	HalfLives.Add(EEmotionType::Surprise, 30.0f);
	HalfLives.Add(EEmotionType::Disgust, 90.0f);
	HalfLives.Add(EEmotionType::Trust, 240.0f);
	HalfLives.Add(EEmotionType::Anticipation, 120.0f);

	return HalfLives;
}

const TArray<TPair<EEmotionType, EEmotionType>>& UEmotionEngine::GetOpposingPairs()
{
	static TArray<TPair<EEmotionType, EEmotionType>> Pairs = {
		TPair<EEmotionType, EEmotionType>(EEmotionType::Joy, EEmotionType::Sadness),
		TPair<EEmotionType, EEmotionType>(EEmotionType::Trust, EEmotionType::Disgust),
		TPair<EEmotionType, EEmotionType>(EEmotionType::Fear, EEmotionType::Anger),
		TPair<EEmotionType, EEmotionType>(EEmotionType::Anticipation, EEmotionType::Surprise)
	};
	return Pairs;
}

TMap<FString, float> UEmotionEngine::ResolveConflicts(const TMap<FString, float>& EmotionDict) const
{
	TMap<FString, float> Resolved = EmotionDict;

	for (const auto& Pair : GetOpposingPairs())
	{
		FString AName = EmotionTypeHelpers::ToName(Pair.Key);
		FString BName = EmotionTypeHelpers::ToName(Pair.Value);

		float* AVal = Resolved.Find(AName);
		float* BVal = Resolved.Find(BName);
		if (!AVal || !BVal) continue;

		float A = *AVal;
		float B = *BVal;

		switch (ConflictStrategy)
		{
		case EConflictStrategy::Dominance:
			if (A > B)
				Resolved.Add(BName, FMath::Max(0.0f, B - (A - B) * 0.5f));
			else if (B > A)
				Resolved.Add(AName, FMath::Max(0.0f, A - (B - A) * 0.5f));
			else
			{
				Resolved.Add(AName, A * 0.5f);
				Resolved.Add(BName, B * 0.5f);
			}
			break;

		case EConflictStrategy::Cancel:
			{
				float Diff = FMath::Abs(A - B);
				Resolved.Add(AName, Diff * 0.5f);
				Resolved.Add(BName, Diff * 0.5f);
			}
			break;

		case EConflictStrategy::Blend:
			{
				float Avg = (A + B) * 0.5f;
				Resolved.Add(AName, Avg);
				Resolved.Add(BName, Avg);
			}
			break;
		}
	}

	return Resolved;
}

FCompositeEmotionResult UEmotionEngine::MatchRecipe(const TMap<FString, float>& EmotionDict) const
{
	FCompositeEmotionResult BestMatch;
	BestMatch.Intensity = -1.0f;
	float BestScore = -1.0f;

	for (const FCompositeRecipe& Recipe : FCompositeRecipes::GetAll())
	{
		float Score = 0.0f;
		float WeightedSum = 0.0f;
		float WeightTotal = 0.0f;
		float PresentWeight = 0.0f;
		int32 PresentCount = 0;

		for (const FCompositeRecipeComponent& Component : Recipe.Components)
		{
			FString EmoName = EmotionTypeHelpers::ToName(Component.Emotion);
			WeightTotal += Component.Weight;

			const float* EmoVal = EmotionDict.Find(EmoName);
			if (EmoVal)
			{
				float Contrib = (*EmoVal) * Component.Weight;
				Score += Contrib;
				WeightedSum += Contrib;
				PresentWeight += Component.Weight;
				PresentCount++;
			}
		}

		if (PresentWeight == 0.0f) continue;

		// Require at least 75% of recipe emotions present
		if (PresentCount < FMath::CeilToInt(Recipe.Components.Num() * 0.75f)) continue;

		// Normalize and calculate final score
		float Normalized = WeightTotal > 0.0f ? Score / WeightTotal : 0.0f;
		float Completeness = WeightTotal > 0.0f ? PresentWeight / WeightTotal : 0.0f;
		float FinalScore = Normalized * 0.6f + Completeness * 0.4f;

		if (FinalScore > BestScore)
		{
			BestScore = FinalScore;
			float Intensity = FMath::Min(1.0f, Normalized * 1.2f);
			BestMatch.Name = Recipe.Name;
			BestMatch.Intensity = NeshamaSoul::SoulMathUtils::Round(Intensity);
			BestMatch.bIsNovel = false;
		}
	}

	// Return neutral if no good match found
	if (BestScore < 0.0f)
	{
		BestMatch.Name = TEXT("");
		BestMatch.Intensity = 0.0f;
		BestMatch.bIsNovel = false;
	}
	return BestMatch;
}

TMap<FString, float> UEmotionEngine::EmotionStateToMap() const
{
	TMap<FString, float> Dict;
	auto AddIfSignificant = [&Dict](const FString& Key, float Val)
	{
		if (Val > 0.001f) Dict.Add(Key, Val);
	};

	AddIfSignificant(TEXT("joy"), Emotions.Joy);
	AddIfSignificant(TEXT("sadness"), Emotions.Sadness);
	AddIfSignificant(TEXT("anger"), Emotions.Anger);
	AddIfSignificant(TEXT("fear"), Emotions.Fear);
	AddIfSignificant(TEXT("surprise"), Emotions.Surprise);
	AddIfSignificant(TEXT("disgust"), Emotions.Disgust);
	AddIfSignificant(TEXT("trust"), Emotions.Trust);
	AddIfSignificant(TEXT("anticipation"), Emotions.Anticipation);

	return Dict;
}
