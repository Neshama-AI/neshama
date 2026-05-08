#include "SoulEngine/Emotion/EventMappings.h"

const TMap<ESoulEventType, TArray<FEventEmotionMapping>>& FEventMappings::GetEmotionMappings()
{
	static TMap<ESoulEventType, TArray<FEventEmotionMapping>> Mappings;
	if (Mappings.Num() > 0) return Mappings;

	Mappings.Add(ESoulEventType::PlayerAttacked, {
		FEventEmotionMapping(ESoulEmotionType::Anger, 0.3f),
		FEventEmotionMapping(ESoulEmotionType::Fear, 0.2f)
	});
	Mappings.Add(ESoulEventType::PlayerHelped, {
		FEventEmotionMapping(ESoulEmotionType::Trust, 0.4f),
		FEventEmotionMapping(ESoulEmotionType::Joy, 0.3f)
	});
	Mappings.Add(ESoulEventType::ItemReceived, {
		FEventEmotionMapping(ESoulEmotionType::Joy, 0.3f),
		FEventEmotionMapping(ESoulEmotionType::Surprise, 0.2f)
	});
	Mappings.Add(ESoulEventType::ItemLost, {
		FEventEmotionMapping(ESoulEmotionType::Sadness, 0.3f),
		FEventEmotionMapping(ESoulEmotionType::Anger, 0.2f)
	});
	Mappings.Add(ESoulEventType::QuestCompleted, {
		FEventEmotionMapping(ESoulEmotionType::Joy, 0.4f),
		FEventEmotionMapping(ESoulEmotionType::Anticipation, 0.2f)
	});
	Mappings.Add(ESoulEventType::QuestFailed, {
		FEventEmotionMapping(ESoulEmotionType::Sadness, 0.3f),
		FEventEmotionMapping(ESoulEmotionType::Anger, 0.2f),
		FEventEmotionMapping(ESoulEmotionType::Fear, 0.15f)
	});
	Mappings.Add(ESoulEventType::NpcInsulted, {
		FEventEmotionMapping(ESoulEmotionType::Anger, 0.4f),
		FEventEmotionMapping(ESoulEmotionType::Sadness, 0.2f),
		FEventEmotionMapping(ESoulEmotionType::Disgust, 0.2f)
	});
	Mappings.Add(ESoulEventType::NpcComplimented, {
		FEventEmotionMapping(ESoulEmotionType::Joy, 0.3f),
		FEventEmotionMapping(ESoulEmotionType::Trust, 0.3f),
		FEventEmotionMapping(ESoulEmotionType::Surprise, 0.1f)
	});
	Mappings.Add(ESoulEventType::EnvironmentChanged, {
		FEventEmotionMapping(ESoulEmotionType::Fear, 0.2f),
		FEventEmotionMapping(ESoulEmotionType::Surprise, 0.25f),
		FEventEmotionMapping(ESoulEmotionType::Anticipation, 0.15f)
	});
	Mappings.Add(ESoulEventType::RelationshipChanged, {
		FEventEmotionMapping(ESoulEmotionType::Trust, 0.3f),
		FEventEmotionMapping(ESoulEmotionType::Sadness, 0.2f)
	});
	Mappings.Add(ESoulEventType::TimePassed, {
		FEventEmotionMapping(ESoulEmotionType::Sadness, 0.05f)
	});
	Mappings.Add(ESoulEventType::CombatStarted, {
		FEventEmotionMapping(ESoulEmotionType::Fear, 0.35f),
		FEventEmotionMapping(ESoulEmotionType::Anger, 0.25f),
		FEventEmotionMapping(ESoulEmotionType::Surprise, 0.15f)
	});
	Mappings.Add(ESoulEventType::CombatEnded, {
		FEventEmotionMapping(ESoulEmotionType::Joy, 0.2f),
		FEventEmotionMapping(ESoulEmotionType::Fear, 0.1f),
		FEventEmotionMapping(ESoulEmotionType::Sadness, 0.1f)
	});
	Mappings.Add(ESoulEventType::DeathWitnessed, {
		FEventEmotionMapping(ESoulEmotionType::Sadness, 0.4f),
		FEventEmotionMapping(ESoulEmotionType::Fear, 0.3f),
		FEventEmotionMapping(ESoulEmotionType::Surprise, 0.2f)
	});
	Mappings.Add(ESoulEventType::GiftGiven, {
		FEventEmotionMapping(ESoulEmotionType::Joy, 0.35f),
		FEventEmotionMapping(ESoulEmotionType::Trust, 0.35f),
		FEventEmotionMapping(ESoulEmotionType::Surprise, 0.15f)
	});

	return Mappings;
}

const TMap<ESoulEventType, TArray<FPersonalityModifier>>& FEventMappings::GetPersonalityModifiers()
{
	static TMap<ESoulEventType, TArray<FPersonalityModifier>> Modifiers;
	if (Modifiers.Num() > 0) return Modifiers;

	Modifiers.Add(ESoulEventType::PlayerHelped, {
		FPersonalityModifier(TEXT("extraversion"), 0.7f, 1.3f),
		FPersonalityModifier(TEXT("agreeableness"), 0.7f, 1.2f)
	});
	Modifiers.Add(ESoulEventType::NpcInsulted, {
		FPersonalityModifier(TEXT("neuroticism"), 0.7f, 1.5f),
		FPersonalityModifier(TEXT("agreeableness"), 0.7f, 0.5f)
	});
	Modifiers.Add(ESoulEventType::QuestCompleted, {
		FPersonalityModifier(TEXT("extraversion"), 0.6f, 1.2f),
		FPersonalityModifier(TEXT("conscientiousness"), 0.6f, 1.3f)
	});
	Modifiers.Add(ESoulEventType::DeathWitnessed, {
		FPersonalityModifier(TEXT("neuroticism"), 0.7f, 1.4f),
		FPersonalityModifier(TEXT("agreeableness"), 0.6f, 0.6f)
	});

	return Modifiers;
}

const TSet<ESoulEmotionType>& FEventMappings::GetPositiveEmotions()
{
	static TSet<ESoulEmotionType> Positive = { ESoulEmotionType::Joy, ESoulEmotionType::Trust };
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
