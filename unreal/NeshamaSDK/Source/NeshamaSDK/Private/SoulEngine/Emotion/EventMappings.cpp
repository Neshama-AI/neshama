#include "SoulEngine/Emotion/EventMappings.h"

const TMap<EGameEventType, TArray<FEventEmotionMapping>>& FEventMappings::GetEmotionMappings()
{
	static TMap<EGameEventType, TArray<FEventEmotionMapping>> Mappings;
	if (Mappings.Num() > 0) return Mappings;

	Mappings.Add(EGameEventType::PlayerAttacked, {
		FEventEmotionMapping(EEmotionType::Anger, 0.3f),
		FEventEmotionMapping(EEmotionType::Fear, 0.2f)
	});
	Mappings.Add(EGameEventType::PlayerHelped, {
		FEventEmotionMapping(EEmotionType::Trust, 0.4f),
		FEventEmotionMapping(EEmotionType::Joy, 0.3f)
	});
	Mappings.Add(EGameEventType::ItemReceived, {
		FEventEmotionMapping(EEmotionType::Joy, 0.3f),
		FEventEmotionMapping(EEmotionType::Surprise, 0.2f)
	});
	Mappings.Add(EGameEventType::ItemLost, {
		FEventEmotionMapping(EEmotionType::Sadness, 0.3f),
		FEventEmotionMapping(EEmotionType::Anger, 0.2f)
	});
	Mappings.Add(EGameEventType::QuestCompleted, {
		FEventEmotionMapping(EEmotionType::Joy, 0.4f),
		FEventEmotionMapping(EEmotionType::Anticipation, 0.2f)
	});
	Mappings.Add(EGameEventType::QuestFailed, {
		FEventEmotionMapping(EEmotionType::Sadness, 0.3f),
		FEventEmotionMapping(EEmotionType::Anger, 0.2f),
		FEventEmotionMapping(EEmotionType::Fear, 0.15f)
	});
	Mappings.Add(EGameEventType::NpcInsulted, {
		FEventEmotionMapping(EEmotionType::Anger, 0.4f),
		FEventEmotionMapping(EEmotionType::Sadness, 0.2f),
		FEventEmotionMapping(EEmotionType::Disgust, 0.2f)
	});
	Mappings.Add(EGameEventType::NpcComplimented, {
		FEventEmotionMapping(EEmotionType::Joy, 0.3f),
		FEventEmotionMapping(EEmotionType::Trust, 0.3f),
		FEventEmotionMapping(EEmotionType::Surprise, 0.1f)
	});
	Mappings.Add(EGameEventType::EnvironmentChanged, {
		FEventEmotionMapping(EEmotionType::Fear, 0.2f),
		FEventEmotionMapping(EEmotionType::Surprise, 0.25f),
		FEventEmotionMapping(EEmotionType::Anticipation, 0.15f)
	});
	Mappings.Add(EGameEventType::RelationshipChanged, {
		FEventEmotionMapping(EEmotionType::Trust, 0.3f),
		FEventEmotionMapping(EEmotionType::Sadness, 0.2f)
	});
	Mappings.Add(EGameEventType::TimePassed, {
		FEventEmotionMapping(EEmotionType::Sadness, 0.05f)
	});
	Mappings.Add(EGameEventType::CombatStarted, {
		FEventEmotionMapping(EEmotionType::Fear, 0.35f),
		FEventEmotionMapping(EEmotionType::Anger, 0.25f),
		FEventEmotionMapping(EEmotionType::Surprise, 0.15f)
	});
	Mappings.Add(EGameEventType::CombatEnded, {
		FEventEmotionMapping(EEmotionType::Joy, 0.2f),
		FEventEmotionMapping(EEmotionType::Fear, 0.1f),
		FEventEmotionMapping(EEmotionType::Sadness, 0.1f)
	});
	Mappings.Add(EGameEventType::DeathWitnessed, {
		FEventEmotionMapping(EEmotionType::Sadness, 0.4f),
		FEventEmotionMapping(EEmotionType::Fear, 0.3f),
		FEventEmotionMapping(EEmotionType::Surprise, 0.2f)
	});
	Mappings.Add(EGameEventType::GiftGiven, {
		FEventEmotionMapping(EEmotionType::Joy, 0.35f),
		FEventEmotionMapping(EEmotionType::Trust, 0.35f),
		FEventEmotionMapping(EEmotionType::Surprise, 0.15f)
	});

	return Mappings;
}

const TMap<EGameEventType, TArray<FPersonalityModifier>>& FEventMappings::GetPersonalityModifiers()
{
	static TMap<EGameEventType, TArray<FPersonalityModifier>> Modifiers;
	if (Modifiers.Num() > 0) return Modifiers;

	Modifiers.Add(EGameEventType::PlayerHelped, {
		FPersonalityModifier(TEXT("extraversion"), 0.7f, 1.3f),
		FPersonalityModifier(TEXT("agreeableness"), 0.7f, 1.2f)
	});
	Modifiers.Add(EGameEventType::NpcInsulted, {
		FPersonalityModifier(TEXT("neuroticism"), 0.7f, 1.5f),
		FPersonalityModifier(TEXT("agreeableness"), 0.7f, 0.5f)
	});
	Modifiers.Add(EGameEventType::QuestCompleted, {
		FPersonalityModifier(TEXT("extraversion"), 0.6f, 1.2f),
		FPersonalityModifier(TEXT("conscientiousness"), 0.6f, 1.3f)
	});
	Modifiers.Add(EGameEventType::DeathWitnessed, {
		FPersonalityModifier(TEXT("neuroticism"), 0.7f, 1.4f),
		FPersonalityModifier(TEXT("agreeableness"), 0.6f, 0.6f)
	});

	return Modifiers;
}

const TSet<EEmotionType>& FEventMappings::GetPositiveEmotions()
{
	static TSet<EEmotionType> Positive = { EEmotionType::Joy, EEmotionType::Trust };
	return Positive;
}

const TSet<FString>& FEventMappings::GetPositiveEmotionNames()
{
	static TSet<FString> Names = {
		TEXT("joy"), TEXT("trust"), TEXT("gratitude"), TEXT("love"),
		TEXT("relief"), TEXT("delight"), TEXT("optimism"), TEXT("pride")
	};
	return Names;
}

const TMap<FString, float>& FEventMappings::GetRelationshipGrudgeMap()
{
	static TMap<FString, float> GrudgeMap;
	if (GrudgeMap.Num() > 0) return GrudgeMap;

	GrudgeMap.Add(TEXT("hostile"), 0.5f);
	GrudgeMap.Add(TEXT("dislikes"), 0.4f);
	GrudgeMap.Add(TEXT("enemy"), 0.6f);
	GrudgeMap.Add(TEXT("rival"), 0.3f);
	GrudgeMap.Add(TEXT("suspicious"), 0.2f);
	GrudgeMap.Add(TEXT("neutral"), 0.0f);
	GrudgeMap.Add(TEXT("friendly"), 0.0f);
	GrudgeMap.Add(TEXT("likes"), 0.0f);
	GrudgeMap.Add(TEXT("allied"), 0.0f);

	return GrudgeMap;
}

float FEventMappings::GetGrudgeFactor(const FString& RelationshipType)
{
	if (RelationshipType.IsEmpty()) return 0.0f;
	const auto& Map = GetRelationshipGrudgeMap();
	const float* Factor = Map.Find(RelationshipType.ToLower());
	return Factor ? *Factor : 0.0f;
}
