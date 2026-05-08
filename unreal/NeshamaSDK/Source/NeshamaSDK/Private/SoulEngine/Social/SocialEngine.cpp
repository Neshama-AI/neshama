#include "SoulEngine/Social/SocialEngine.h"
#include "SoulEngine/Personality/OCEANPersonality.h"

USocialEngine::USocialEngine()
{
}

void USocialEngine::RegisterNPC(const FString& NpcId, UOCEANPersonality* Personality,
	const TMap<FString, float>& Emotions)
{
	NpcPersonalities.Add(NpcId, Personality ? Personality : nullptr);
	NpcEmotions.Add(NpcId, Emotions);
}

void USocialEngine::RegisterNPC(const FString& NpcId, UOCEANPersonality* Personality)
{
	RegisterNPC(NpcId, Personality, TMap<FString, float>());
}

void USocialEngine::UpdateNPCEmotions(const FString& NpcId, const TMap<FString, float>& Emotions)
{
	NpcEmotions.Add(NpcId, Emotions);
}

FString USocialEngine::GetRelationKey(const FString& A, const FString& B)
{
	// Sort IDs to ensure consistent key
	return A < B ? (A + TEXT(":") + B) : (B + TEXT(":") + A);
}

FNPCRelation* USocialEngine::GetOrCreateRelation(const FString& NpcAId, const FString& NpcBId)
{
	FString Key = GetRelationKey(NpcAId, NpcBId);
	FNPCRelation* RelPtr = Relations.Find(Key);
	if (!RelPtr)
	{
		FNPCRelation NewRel;
		NewRel.NpcAId = NpcAId;
		NewRel.NpcBId = NpcBId;
		Relations.Add(Key, NewRel);
		RelPtr = Relations.Find(Key);
	}
	return RelPtr;
}

FSocialEvent USocialEngine::InitiateInteraction(const FString& NpcAId, const FString& NpcBId,
	ESocialInteractionType ForcedType, bool bForceType)
{
	FString Key = GetRelationKey(NpcAId, NpcBId);

	// Check cooldown
	float* LastTime = LastInteractionTimes.Find(Key);
	if (LastTime && GameTime - *LastTime < MinInteractionInterval)
	{
		FSocialEvent Evt;
		Evt.EventId = FGuid::NewGuid().ToString();
		Evt.NpcAId = NpcAId;
		Evt.NpcBId = NpcBId;
		Evt.InteractionType = ESocialInteractionType::Gossip;
		Evt.bSuccess = false;
		Evt.Timestamp = GameTime;
		return Evt;
	}

	// Get or create relation
	FNPCRelation* Relation = GetOrCreateRelation(NpcAId, NpcBId);

	// Get NPC profiles
	UOCEANPersonality** PersonalityAPtr = NpcPersonalities.Find(NpcAId);
	UOCEANPersonality** PersonalityBPtr = NpcPersonalities.Find(NpcBId);
	UOCEANPersonality* PersonalityA = PersonalityAPtr ? *PersonalityAPtr : nullptr;
	UOCEANPersonality* PersonalityB = PersonalityBPtr ? *PersonalityBPtr : nullptr;

	TMap<FString, float>* EmotionsAPtr = NpcEmotions.Find(NpcAId);
	TMap<FString, float>* EmotionsBPtr = NpcEmotions.Find(NpcBId);
	TMap<FString, float> EmotionsA = EmotionsAPtr ? *EmotionsAPtr : TMap<FString, float>();
	TMap<FString, float> EmotionsB = EmotionsBPtr ? *EmotionsBPtr : TMap<FString, float>();

	// Determine interaction type
	ESocialInteractionType InteractionType = bForceType ? ForcedType :
		DecideInteractionType(PersonalityA, EmotionsA, PersonalityB, EmotionsB, *Relation);

	// Calculate effects
	TMap<FString, float> Delta = CalculateInteractionEffects(InteractionType, PersonalityA, PersonalityB, *Relation);

	// Apply delta
	ApplyRelationDelta(*Relation, Delta);

	// Update tracking
	Relation->InteractionCount++;
	Relation->LastInteractionTime = GameTime;
	LastInteractionTimes.Add(Key, GameTime);

	// Create event
	FSocialEvent Evt;
	Evt.EventId = FGuid::NewGuid().ToString();
	Evt.NpcAId = NpcAId;
	Evt.NpcBId = NpcBId;
	Evt.InteractionType = InteractionType;
	Evt.bSuccess = true;
	Evt.Timestamp = GameTime;
	Evt.RelationshipDelta = Delta;

	SocialEvents.Add(Evt);
	if (SocialEvents.Num() > MaxEvents)
	{
		SocialEvents.RemoveAt(0, SocialEvents.Num() - MaxEvents);
	}

	return Evt;
}

bool USocialEngine::GetRelation(const FString& NpcAId, const FString& NpcBId, FNPCRelation& OutRelation)
{
	FString Key = GetRelationKey(NpcAId, NpcBId);
	FNPCRelation* RelPtr = Relations.Find(Key);
	if (!RelPtr) return false;
	OutRelation = *RelPtr;
	return true;
}

void USocialEngine::Tick(float DeltaTime)
{
	GameTime += DeltaTime;
}

ESocialInteractionType USocialEngine::DecideInteractionType(
	UOCEANPersonality* PersonalityA, const TMap<FString, float>& EmotionsA,
	UOCEANPersonality* PersonalityB, const TMap<FString, float>& EmotionsB,
	const FNPCRelation& Relation)
{
	// Simplified decision logic based on personality and relationship
	float ExtraversionA = PersonalityA ? PersonalityA->Extraversion : 0.5f;
	float AgreeablenessA = PersonalityA ? PersonalityA->Agreeableness : 0.5f;

	if (Relation.Trust < 0.3f)
		return ESocialInteractionType::Argue;
	if (Relation.Trust > 0.7f && ExtraversionA > 0.6f)
		return ESocialInteractionType::Gossip;
	if (AgreeablenessA > 0.7f && Relation.Strength > 0.5f)
		return ESocialInteractionType::Comfort;
	if (ExtraversionA > 0.7f)
		return ESocialInteractionType::Gossip;
	if (Relation.Strength > 0.6f)
		return ESocialInteractionType::Trade;

	return ESocialInteractionType::Gossip;
}

TMap<FString, float> USocialEngine::CalculateInteractionEffects(
	ESocialInteractionType Type, UOCEANPersonality* PersonalityA,
	UOCEANPersonality* PersonalityB, const FNPCRelation& Relation)
{
	TMap<FString, float> Delta;
	float AgreA = PersonalityA ? PersonalityA->Agreeableness : 0.5f;
	float AgreB = PersonalityB ? PersonalityB->Agreeableness : 0.5f;
	float AgreAvg = (AgreA + AgreB) * 0.5f;

	switch (Type)
	{
	case ESocialInteractionType::Gossip:
		Delta.Add(TEXT("strength"), 0.05f * AgreAvg);
		Delta.Add(TEXT("familiarity"), 0.1f);
		break;
	case ESocialInteractionType::Trade:
		Delta.Add(TEXT("strength"), 0.08f);
		Delta.Add(TEXT("trust"), 0.05f);
		break;
	case ESocialInteractionType::Argue:
		Delta.Add(TEXT("strength"), -0.15f);
		Delta.Add(TEXT("trust"), -0.1f);
		Delta.Add(TEXT("grudge"), 0.05f);
		break;
	case ESocialInteractionType::Ally:
		Delta.Add(TEXT("strength"), 0.15f);
		Delta.Add(TEXT("trust"), 0.1f);
		Delta.Add(TEXT("bond"), 0.1f);
		break;
	case ESocialInteractionType::Betray:
		Delta.Add(TEXT("strength"), -0.3f);
		Delta.Add(TEXT("trust"), -0.25f);
		Delta.Add(TEXT("grudge"), 0.2f);
		break;
	case ESocialInteractionType::Comfort:
		Delta.Add(TEXT("strength"), 0.1f);
		Delta.Add(TEXT("trust"), 0.08f);
		Delta.Add(TEXT("bond"), 0.05f);
		break;
	case ESocialInteractionType::Teach:
		Delta.Add(TEXT("strength"), 0.05f);
		Delta.Add(TEXT("trust"), 0.1f);
		Delta.Add(TEXT("familiarity"), 0.05f);
		break;
	case ESocialInteractionType::Flirt:
		Delta.Add(TEXT("strength"), 0.08f);
		Delta.Add(TEXT("romanticInterest"), 0.1f);
		break;
	}

	return Delta;
}

void USocialEngine::ApplyRelationDelta(FNPCRelation& Relation, const TMap<FString, float>& Delta)
{
	const float* StrDelta = Delta.Find(TEXT("strength"));
	if (StrDelta) Relation.Strength = FMath::Clamp(Relation.Strength + *StrDelta, -1.0f, 1.0f);

	const float* TrustDelta = Delta.Find(TEXT("trust"));
	if (TrustDelta) Relation.Trust = FMath::Clamp(Relation.Trust + *TrustDelta, 0.0f, 1.0f);

	const float* FamDelta = Delta.Find(TEXT("familiarity"));
	if (FamDelta) Relation.Familiarity = FMath::Clamp(Relation.Familiarity + *FamDelta, 0.0f, 1.0f);

	const float* GrudgeDelta = Delta.Find(TEXT("grudge"));
	if (GrudgeDelta) Relation.Grudge = FMath::Clamp(Relation.Grudge + *GrudgeDelta, 0.0f, 1.0f);

	const float* BondDelta = Delta.Find(TEXT("bond"));
	if (BondDelta) Relation.Bond = FMath::Clamp(Relation.Bond + *BondDelta, 0.0f, 1.0f);

	const float* RomDelta = Delta.Find(TEXT("romanticInterest"));
	if (RomDelta) Relation.RomanticInterest = FMath::Clamp(Relation.RomanticInterest + *RomDelta, 0.0f, 1.0f);
}
