#include "SoulEngine/Memory/EntityMemory.h"

TArray<FString> FSoulDialogueContext::ToPromptParts(int32 MaxMemories) const
{
	TArray<FString> Parts;

	if (!Relation.EntityId.IsEmpty())
	{
		Parts.Add(FString::Printf(TEXT("你与%s的关系是%s，强度%.2f，信任度%.2f"),
			*PlayerName, *Relation.RelationType, Relation.Strength, Relation.Trust));
	}

	if (RecentMemories.Num() > 0)
	{
		TArray<FString> MemDescs;
		int32 Count = FMath::Min(MaxMemories, RecentMemories.Num());
		for (int32 i = 0; i < Count; ++i)
		{
			const FEntityMemory& Mem = RecentMemories[i];
			FString Desc = Mem.Description;
			if (Desc.Len() > 20)
				Desc = Desc.Left(20);
			MemDescs.Add(FString::Printf(TEXT("%s(%s...)"), *Mem.EventType, *Desc));
		}
		Parts.Add(FString::Printf(TEXT("你最近与%s的交互：%s"), *PlayerName, *FString::Join(MemDescs, TEXT("、"))));
	}

	{
		TArray<FString> SigList;
		for (const auto& KV : EmotionalState)
		{
			if (KV.Value > 0.2f)
			{
				SigList.Add(FString::Printf(TEXT("%s(%.2f)"), *KV.Key, KV.Value));
			}
		}
		SigList.Sort([](const FString& A, const FString& B) { return A > B; }); // Simple sort
		if (SigList.Num() > 0)
		{
			Parts.Add(FString::Printf(TEXT("你当前情绪：%s"), *FString::Join(SigList, TEXT("、"))));
		}
	}

	return Parts;
}
