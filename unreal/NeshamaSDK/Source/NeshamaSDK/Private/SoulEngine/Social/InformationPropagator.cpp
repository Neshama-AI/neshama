#include "SoulEngine/Social/InformationPropagator.h"

UInformationPropagator::UInformationPropagator()
{
}

void UInformationPropagator::AddToNpcKnowledge(const FString& NpcId, const FString& InfoId)
{
	TSet<FString>& Knowledge = NpcKnowledge.FindOrAdd(NpcId);
	Knowledge.Add(InfoId);

	FInformation* Info = InformationMap.Find(InfoId);
	if (Info)
	{
		if (!Info->SeenBy.Contains(NpcId))
			Info->SeenBy.Add(NpcId);
	}
}

float UInformationPropagator::GetTrust(const FString& FromNpc, const FString& ToNpc)
{
	if (OnTrustLookup.IsBound())
		return OnTrustLookup.Execute(FromNpc, ToNpc);
	return 0.5f; // Default moderate trust
}

FSpreadResult UInformationPropagator::SpreadInformation(const FString& SourceNpcId, EInfoType InfoType,
	const FString& Content, const TArray<FString>& Targets,
	float Importance, const TArray<FString>& Tags, const FString& ExistingInfoId)
{
	FInformation* Info = nullptr;

	if (!ExistingInfoId.IsEmpty())
	{
		Info = InformationMap.Find(ExistingInfoId);
		if (Info)
		{
			Info->LastSpread = GameTime;
			Info->PropagationCount++;
		}
	}

	if (!Info)
	{
		FInformation NewInfo;
		FString InfoId = ExistingInfoId.IsEmpty() ? FGuid::NewGuid().ToString() : ExistingInfoId;
		NewInfo.InfoId = InfoId;
		NewInfo.InfoType = InfoType;
		NewInfo.OriginalContent = Content;
		NewInfo.CurrentContent = Content;
		NewInfo.SourceNpcId = SourceNpcId;
		NewInfo.Importance = Importance;
		NewInfo.Tags = Tags;
		NewInfo.CreatedAt = GameTime;
		InformationMap.Add(InfoId, NewInfo);
		Info = InformationMap.Find(InfoId);
		AddToNpcKnowledge(SourceNpcId, InfoId);
	}

	FSpreadResult Result;
	Result.InfoId = Info->InfoId;

	for (const FString& TargetId : Targets)
	{
		if (TargetId == SourceNpcId) continue;

		float Trust = GetTrust(SourceNpcId, TargetId);
		float SpreadChance = Trust * 0.7f + Importance * 0.3f;

		if (FMath::FRand() > SpreadChance)
		{
			FSpreadTargetResult TargetResult;
			TargetResult.Target = TargetId;
			TargetResult.bSuccess = false;
			TargetResult.Reason = TEXT("low_trust");
			Result.SpreadTo.Add(TargetResult);
			continue;
		}

		// Apply distortion for rumors
		FString FinalContent = Info->CurrentContent;
		if (InfoType == EInfoType::Rumor)
		{
			FString Distorted;
			float DistortionDelta = 0.0f;
			ApplyDistortion(Info->CurrentContent, Info->DistortionLevel, Trust, Distorted, DistortionDelta);
			Info->DistortionLevel = FMath::Min(1.0f, Info->DistortionLevel + DistortionDelta);
			Info->CurrentContent = Distorted;
			FinalContent = Distorted;
		}

		// Update credibility
		Info->Credibility = FMath::Max(0.1f, Info->Credibility - TrustDecayPerHop);

		// Add to target's knowledge
		AddToNpcKnowledge(TargetId, Info->InfoId);

		FSpreadTargetResult TargetResult;
		TargetResult.Target = TargetId;
		TargetResult.bSuccess = true;
		TargetResult.Content = FinalContent;
		TargetResult.Credibility = Info->Credibility;
		Result.SpreadTo.Add(TargetResult);

		// Trigger emotion reaction
		TriggerEmotionReaction(TargetId, InfoType, FinalContent, Info->Credibility, Importance, SourceNpcId);
	}

	Result.PropagationCount = Info->PropagationCount;
	Result.TotalKnowers = Info->SeenBy.Num();
	return Result;
}

TArray<FInformation> UInformationPropagator::GetNPCKnowledge(const FString& NpcId, int32 Limit)
{
	TArray<FInformation> Result;
	TSet<FString>* Knowledge = NpcKnowledge.Find(NpcId);
	if (!Knowledge) return Result;

	for (const FString& InfoId : *Knowledge)
	{
		FInformation* Info = InformationMap.Find(InfoId);
		if (!Info) continue;
		Result.Add(*Info);
		if (Result.Num() >= Limit) break;
	}
	return Result;
}

int32 UInformationPropagator::DecayInformation(float DeltaTime)
{
	int32 ForgottenCount = 0;
	TArray<FString> ForgottenIds;

	for (auto& KV : InformationMap)
	{
		KV.Value.Importance = FMath::Max(0.0f, KV.Value.Importance - DecayRate * DeltaTime);
		if (KV.Value.Importance < MinImportance)
		{
			ForgottenIds.Add(KV.Key);
			ForgottenCount++;
		}
	}

	// Remove forgotten info from all NPC knowledge
	for (const FString& Id : ForgottenIds)
	{
		for (auto& Knowledge : NpcKnowledge)
		{
			Knowledge.Value.Remove(Id);
		}
		InformationMap.Remove(Id);
	}

	return ForgottenCount;
}

void UInformationPropagator::Tick(float DeltaTime)
{
	GameTime += DeltaTime;
}

void UInformationPropagator::ApplyDistortion(const FString& Content, float CurrentDistortion, float Trust,
	FString& OutResult, float& OutDistortionDelta)
{
	float DistortChance = DistortionChance * (1.0f - Trust);
	if (FMath::FRand() > DistortChance)
	{
		OutResult = Content;
		OutDistortionDelta = 0.0f;
		return;
	}

	TArray<FString> Words;
	Content.ParseIntoArrayWS(Words);
	int32 Type = FMath::RandRange(0, 3);

	if (Type == 0 && Words.Num() > 5)
	{
		// Exaggerate: replace first word with intensifier
		static const TArray<FString> Intensifiers = {TEXT("apparently"), TEXT("supposedly"), TEXT("allegedly")};
		Words[0] = Intensifiers[FMath::RandRange(0, Intensifiers.Num() - 1)];
		if (Words.Num() > 1) Words.RemoveAt(1);
		OutResult = FString::Join(Words, TEXT(" "));
		OutDistortionDelta = DistortionAmount;
	}
	else if (Type == 1 && Words.Num() > 8)
	{
		// Simplify: keep first 3 and last 3
		TArray<FString> Keep;
		for (int32 i = 0; i < 3 && i < Words.Num(); ++i) Keep.Add(Words[i]);
		for (int32 i = FMath::Max(3, Words.Num() - 3); i < Words.Num(); ++i) Keep.Add(Words[i]);
		OutResult = FString::Join(Keep, TEXT(" "));
		OutDistortionDelta = DistortionAmount * 0.5f;
	}
	else if (Type == 2 && Words.Num() > 5)
	{
		// Partial: replace a word with [...]
		int32 Idx = FMath::RandRange(1, Words.Num() - 2);
		Words[Idx] = TEXT("[...]");
		OutResult = FString::Join(Words, TEXT(" "));
		OutDistortionDelta = DistortionAmount * 0.3f;
	}
	else
	{
		OutResult = Content;
		OutDistortionDelta = 0.0f;
	}
}

void UInformationPropagator::TriggerEmotionReaction(const FString& TargetNpcId, EInfoType InfoType,
	const FString& Content, float Credibility, float Importance, const FString& SourceNpcId)
{
	if (!OnEmotionCallback.IsBound()) return;

	TMap<FString, float> EmotionDeltas;
	FString ContentLower = Content.ToLower();

	float IntensityFactor = Credibility * Importance * 0.5f;

	// Attack keywords
	static const TArray<FString> AttackKw = {
		TEXT("attack"), TEXT("hit"), TEXT("kill"), TEXT("fight"), TEXT("hurt"),
		TEXT("暴力"), TEXT("攻击"), TEXT("伤害")
	};
	static const TArray<FString> HelpKw = {
		TEXT("help"), TEXT("save"), TEXT("protect"), TEXT("rescue"), TEXT("heal"),
		TEXT("帮助"), TEXT("拯救"), TEXT("保护")
	};

	bool bIsAttack = false, bIsHelp = false;
	for (const FString& Kw : AttackKw) { if (ContentLower.Contains(Kw)) { bIsAttack = true; break; } }
	for (const FString& Kw : HelpKw) { if (ContentLower.Contains(Kw)) { bIsHelp = true; break; } }

	if (bIsAttack)
	{
		EmotionDeltas.Add(TEXT("trust"), -0.15f * IntensityFactor);
		EmotionDeltas.Add(TEXT("anger"), 0.10f * IntensityFactor);
	}
	else if (bIsHelp)
	{
		EmotionDeltas.Add(TEXT("trust"), 0.10f * IntensityFactor);
		EmotionDeltas.Add(TEXT("joy"), 0.05f * IntensityFactor);
	}
	else if (InfoType == EInfoType::PlayerAction)
	{
		EmotionDeltas.Add(TEXT("trust"), -0.05f * IntensityFactor);
	}

	if (EmotionDeltas.Num() > 0)
	{
		OnEmotionCallback.ExecuteIfBound(TargetNpcId, EmotionDeltas);
	}
}
