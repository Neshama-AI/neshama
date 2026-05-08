#include "SoulEngine/Memory/MemorySystem.h"

UMemorySystem::UMemorySystem()
{
}

const TMap<ESoulEventType, UMemorySystem::FRelationMapping>& UMemorySystem::GetEventRelationMappings()
{
	static TMap<ESoulEventType, FRelationMapping> Mappings;
	if (Mappings.Num() > 0) return Mappings;

	Mappings.Add(ESoulEventType::PlayerAttacked,  {TEXT("hostile"),       0.3f, -0.2f});
	Mappings.Add(ESoulEventType::PlayerHelped,     {TEXT("ally"),          0.3f,  0.2f});
	Mappings.Add(ESoulEventType::ItemReceived,     {TEXT("friendly"),      0.1f,  0.1f});
	Mappings.Add(ESoulEventType::ItemLost,         {TEXT("neutral"),      -0.1f, -0.1f});
	Mappings.Add(ESoulEventType::QuestCompleted,   {TEXT("ally"),          0.3f,  0.3f});
	Mappings.Add(ESoulEventType::QuestFailed,      {TEXT("disappointed"), -0.2f, -0.1f});
	Mappings.Add(ESoulEventType::NpcInsulted,      {TEXT("hostile"),       0.2f, -0.3f});
	Mappings.Add(ESoulEventType::NpcComplimented,  {TEXT("friendly"),      0.2f,  0.2f});
	Mappings.Add(ESoulEventType::GiftGiven,        {TEXT("friendly"),      0.2f,  0.3f});
	Mappings.Add(ESoulEventType::EnvironmentChanged,{TEXT("aware"),        0.1f,  0.0f});
	Mappings.Add(ESoulEventType::RelationshipChanged,{TEXT("connected"),   0.2f,  0.0f});
	Mappings.Add(ESoulEventType::CombatStarted,    {TEXT("hostile"),       0.2f,  0.0f});
	Mappings.Add(ESoulEventType::CombatEnded,      {TEXT("tense"),         0.0f,  0.0f});
	Mappings.Add(ESoulEventType::DeathWitnessed,   {TEXT("shaken"),        0.2f,  0.0f});
	Mappings.Add(ESoulEventType::TimePassed,       {TEXT("neutral"),      -0.05f, 0.0f});

	return Mappings;
}

void UMemorySystem::OnGameEvent(ESoulEventType EventType, float Intensity,
	const FString& EntityId, const FString& EntityName,
	const TMap<FString, float>& EmotionalContext)
{
	const auto& Mappings = GetEventRelationMappings();
	const FRelationMapping* MappingPtr = Mappings.Find(EventType);
	if (!MappingPtr) return;

	const FRelationMapping& Mapping = *MappingPtr;

	// Get or create relation
	FEntityRelation* RelationPtr = Relations.Find(EntityId);
	if (!RelationPtr)
	{
		FEntityRelation NewRelation;
		NewRelation.EntityId = EntityId;
		NewRelation.EntityName = EntityName;
		NewRelation.Strength = FMath::Clamp(0.3f + Mapping.StrengthDelta * Intensity, 0.0f, 1.0f);
		NewRelation.Trust = FMath::Clamp(0.3f + Mapping.TrustDelta * Intensity, 0.0f, 1.0f);
		NewRelation.RelationType = Mapping.Relation;
		NewRelation.LastInteractionTime = GameTime;
		NewRelation.InteractionCount = 1;
		Relations.Add(EntityId, NewRelation);
	}
	else
	{
		RelationPtr->Strength = FMath::Clamp(RelationPtr->Strength + Mapping.StrengthDelta * Intensity, -1.0f, 1.0f);
		RelationPtr->Trust = FMath::Clamp(RelationPtr->Trust + Mapping.TrustDelta * Intensity, 0.0f, 1.0f);
		RelationPtr->RelationType = Mapping.Relation;
		RelationPtr->LastInteractionTime = GameTime;
		RelationPtr->InteractionCount++;
	}

	// Create memory entry
	MemoryCounter++;
	FEntityMemory Memory;
	Memory.MemoryId = FString::Printf(TEXT("mem_%d"), MemoryCounter);
	Memory.EntityId = EntityId;
	Memory.EntityName = EntityName;
	Memory.EventType = StaticEnum<ESoulEventType>()->GetNameStringByValue(static_cast<int64>(EventType));
	Memory.Description = GenerateMemoryDescription(EventType, EntityName);
	Memory.Timestamp = GameTime;
	Memory.EmotionalContext = EmotionalContext;
	Memory.TrustAtTime = Relations.FindChecked(EntityId).Trust;
	Memories.Add(Memory);

	// Trim to max
	if (Memories.Num() > MaxMemoriesPerNpc)
	{
		Memories.RemoveAt(0, Memories.Num() - MaxMemoriesPerNpc);
	}
}

bool UMemorySystem::GetDialogueContext(const FString& NpcId, const FString& PlayerId,
	const FString& PlayerName, const TMap<FString, float>& EmotionalState,
	int32 MaxMemories, FSoulDialogueContext& OutContext)
{
	const FEntityRelation* RelPtr = Relations.Find(PlayerId);
	if (!RelPtr) return false;

	OutContext.NpcId = NpcId;
	OutContext.PlayerId = PlayerId;
	OutContext.PlayerName = PlayerName.IsEmpty() ? RelPtr->EntityName : PlayerName;
	OutContext.Relation = *RelPtr;
	OutContext.EmotionalState = EmotionalState;

	// Get recent memories about this player
	TArray<FEntityMemory> PlayerMemories;
	for (const FEntityMemory& Mem : Memories)
	{
		if (Mem.EntityId == PlayerId)
			PlayerMemories.Add(Mem);
	}
	if (PlayerMemories.Num() > MaxMemories)
	{
		PlayerMemories.RemoveAt(0, PlayerMemories.Num() - MaxMemories);
	}
	OutContext.RecentMemories = PlayerMemories;

	return true;
}

TArray<FEntityMemory> UMemorySystem::GetEntityMemories(const FString& EntityId, int32 MaxCount)
{
	TArray<FEntityMemory> Result;
	for (int32 i = Memories.Num() - 1; i >= 0 && Result.Num() < MaxCount; --i)
	{
		if (Memories[i].EntityId == EntityId)
			Result.Add(Memories[i]);
	}
	return Result;
}

bool UMemorySystem::GetRelation(const FString& EntityId, FEntityRelation& OutRelation)
{
	const FEntityRelation* RelPtr = Relations.Find(EntityId);
	if (!RelPtr) return false;
	OutRelation = *RelPtr;
	return true;
}

TArray<FEntityRelation> UMemorySystem::GetAllRelations()
{
	TArray<FEntityRelation> Result;
	for (const auto& KV : Relations)
	{
		Result.Add(KV.Value);
	}
	return Result;
}

void UMemorySystem::DecayRelations(float DeltaTime)
{
	for (auto& KV : Relations)
	{
		FEntityRelation& Relation = KV.Value;
		float DecayFactor = 1.0f - (RelationDecayRate * DeltaTime * 0.1f);
		Relation.Strength *= DecayFactor;

		float TrustDecay = 1.0f - (RelationDecayRate * DeltaTime * 0.05f);
		Relation.Trust *= TrustDecay;
	}
}

void UMemorySystem::UpdateTime(float DeltaTime)
{
	GameTime += DeltaTime;
}

void UMemorySystem::Clear()
{
	Relations.Empty();
	Memories.Empty();
	MemoryCounter = 0;
}

FString UMemorySystem::GenerateMemoryDescription(ESoulEventType EventType, const FString& EntityName)
{
	switch (EventType)
	{
	case ESoulEventType::PlayerAttacked:    return FString::Printf(TEXT("被%s攻击"), *EntityName);
	case ESoulEventType::PlayerHelped:      return FString::Printf(TEXT("被%s帮助"), *EntityName);
	case ESoulEventType::ItemReceived:      return FString::Printf(TEXT("从%s处收到物品"), *EntityName);
	case ESoulEventType::ItemLost:          return FString::Printf(TEXT("被%s夺走物品"), *EntityName);
	case ESoulEventType::QuestCompleted:    return FString::Printf(TEXT("与%s完成任务"), *EntityName);
	case ESoulEventType::QuestFailed:       return FString::Printf(TEXT("与%s任务失败"), *EntityName);
	case ESoulEventType::NpcInsulted:       return FString::Printf(TEXT("被%s侮辱"), *EntityName);
	case ESoulEventType::NpcComplimented:   return FString::Printf(TEXT("被%s称赞"), *EntityName);
	case ESoulEventType::GiftGiven:         return FString::Printf(TEXT("收到%s的礼物"), *EntityName);
	case ESoulEventType::EnvironmentChanged:return TEXT("环境发生变化");
	case ESoulEventType::RelationshipChanged:return FString::Printf(TEXT("与%s关系改变"), *EntityName);
	case ESoulEventType::CombatStarted:     return FString::Printf(TEXT("与%s开始战斗"), *EntityName);
	case ESoulEventType::CombatEnded:       return FString::Printf(TEXT("与%s结束战斗"), *EntityName);
	case ESoulEventType::DeathWitnessed:    return FString::Printf(TEXT("目睹%s死亡"), *EntityName);
	case ESoulEventType::TimePassed:        return TEXT("时间流逝");
	default:                                return FString::Printf(TEXT("与%s发生未知事件"), *EntityName);
	}
}
