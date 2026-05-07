// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - Blueprint函数库实现文件

#include "Blueprint/NeshamaBlueprintLibrary.h"
#include "NPCSoulComponent.h"
#include "NeshamaClient.h"
#include "NeshamaConfig.h"
#include "GameFramework/Actor.h"

#define LOCTEXT_NAMESPACE "NeshamaBlueprintLibrary"

// ============================================================================
// 快速开始
// ============================================================================

UNPCSoulComponent* UNeshamaBlueprintLibrary::CreateNPCWithSoul(AActor* Owner, const FString& Preset, const FString& NPCName)
{
	if (!Owner)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Neshama] CreateNPCWithSoul: Owner is null"));
		return nullptr;
	}

	// 检查是否已有NPCSoulComponent
	UNPCSoulComponent* ExistingSoul = Owner->FindComponentByClass<UNPCSoulComponent>();
	if (ExistingSoul)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Neshama] CreateNPCWithSoul: Actor already has NPCSoulComponent"));
		return ExistingSoul;
	}

	// 创建NPCSoulComponent
	UNPCSoulComponent* SoulComponent = NewObject<UNPCSoulComponent>(Owner, UNPCSoulComponent::StaticClass());
	if (SoulComponent)
	{
		SoulComponent->RegisterComponent();

		// 生成唯一NpcId
		SoulComponent->NpcId = FString::Printf(TEXT("npc_%s_%s"), *Preset, *FGuid::NewGuid().ToString());
		SoulComponent->Preset = Preset;
		SoulComponent->NpcName = NPCName;
		SoulComponent->bAutoConnect = true;

		UE_LOG(LogTemp, Display, TEXT("[Neshama] NPC '%s' created with preset '%s'"), *NPCName, *Preset);
	}

	return SoulComponent;
}

// ============================================================================
// 事件交互
// ============================================================================

void UNeshamaBlueprintLibrary::SendNPCEvent(UNPCSoulComponent* Soul, const FString& EventType, float Intensity)
{
	if (!Soul)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Neshama] SendNPCEvent: Soul component is null"));
		return;
	}

	// 将字符串事件类型转换为枚举
	static const TMap<FString, EGameEventType> EventTypeMap = {
		{TEXT("PlayerEntered"), EGameEventType::PlayerEntered},
		{TEXT("PlayerLeft"), EGameEventType::PlayerLeft},
		{TEXT("PlayerAttacked"), EGameEventType::PlayerAttacked},
		{TEXT("NPCHealed"), EGameEventType::NPCHealed},
		{TEXT("NPCDamaged"), EGameEventType::NPCDamaged},
		{TEXT("NPCComplimented"), EGameEventType::NPCComplimented},
		{TEXT("NPCInsulted"), EGameEventType::NPCInsulted},
		{TEXT("GiftGiven"), EGameEventType::GiftGiven},
		{TEXT("NPCHelped"), EGameEventType::NPCHelped},
		{TEXT("TradeCompleted"), EGameEventType::TradeCompleted},
		{TEXT("CombatStarted"), EGameEventType::CombatStarted},
		{TEXT("CombatEnded"), EGameEventType::CombatEnded},
		{TEXT("QuestCompleted"), EGameEventType::QuestCompleted},
		{TEXT("QuestAccepted"), EGameEventType::QuestAccepted},
		{TEXT("QuestFailed"), EGameEventType::QuestFailed},
		// 小写兼容
		{TEXT("player_entered"), EGameEventType::PlayerEntered},
		{TEXT("player_left"), EGameEventType::PlayerLeft},
		{TEXT("player_attacked"), EGameEventType::PlayerAttacked},
		{TEXT("npc_healed"), EGameEventType::NPCHealed},
		{TEXT("npc_damaged"), EGameEventType::NPCDamaged},
		{TEXT("npc_complimented"), EGameEventType::NPCComplimented},
		{TEXT("npc_insulted"), EGameEventType::NPCInsulted},
		{TEXT("gift_given"), EGameEventType::GiftGiven},
		{TEXT("npc_helped"), EGameEventType::NPCHelped},
		{TEXT("trade_completed"), EGameEventType::TradeCompleted},
		{TEXT("combat_started"), EGameEventType::CombatStarted},
		{TEXT("combat_ended"), EGameEventType::CombatEnded},
		{TEXT("quest_completed"), EGameEventType::QuestCompleted},
		{TEXT("quest_accepted"), EGameEventType::QuestAccepted},
		{TEXT("quest_failed"), EGameEventType::QuestFailed},
		// 简写
		{TEXT("Greet"), EGameEventType::NPCComplimented},
		{TEXT("Attack"), EGameEventType::PlayerAttacked},
		{TEXT("Gift"), EGameEventType::GiftGiven},
		{TEXT("Help"), EGameEventType::NPCHelped},
		{TEXT("Insult"), EGameEventType::NPCInsulted},
		{TEXT("Heal"), EGameEventType::NPCHealed},
	};

	if (const EGameEventType* FoundType = EventTypeMap.Find(EventType))
	{
		TMap<FString, FString> Context;
		Context.Add(TEXT("source"), TEXT("blueprint"));
		Soul->SendGameEvent(*FoundType, FMath::Clamp(Intensity, 0.0f, 1.0f), Context);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[Neshama] SendNPCEvent: Unknown event type '%s'"), *EventType);
	}
}

// ============================================================================
// 对话
// ============================================================================

void UNeshamaBlueprintLibrary::ChatWithNPC(UNPCSoulComponent* Soul, const FString& Message)
{
	if (!Soul)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Neshama] ChatWithNPC: Soul component is null"));
		return;
	}

	if (Message.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("[Neshama] ChatWithNPC: Message is empty"));
		return;
	}

	Soul->Chat(Message);
}

// ============================================================================
// 情绪查询
// ============================================================================

float UNeshamaBlueprintLibrary::GetEmotionValue(UNPCSoulComponent* Soul, const FString& EmotionType)
{
	if (!Soul)
	{
		return 0.0f;
	}

	FEmotionState EmotionState = Soul->GetEmotionState();
	return EmotionState.GetEmotionValue(EmotionType.ToLower());
}

FString UNeshamaBlueprintLibrary::GetDominantEmotion(UNPCSoulComponent* Soul)
{
	if (!Soul)
	{
		return TEXT("unknown");
	}

	FEmotionState EmotionState = Soul->GetEmotionState();
	return EmotionState.Dominant;
}

// ============================================================================
// 连接测试
// ============================================================================

void UNeshamaBlueprintLibrary::TestConnection(const FString& ServerUrl, const FString& ApiKey)
{
	UE_LOG(LogTemp, Display, TEXT("[Neshama] Testing connection to: %s"), *ServerUrl);

	// 创建临时客户端测试连接
	UNeshamaClient* TestClient = NewObject<UNeshamaClient>();
	if (TestClient)
	{
		UNeshamaConfig* Config = TestClient->GetConfig();
		if (Config)
		{
			// 解析URL设置配置
			if (ServerUrl.Contains(TEXT("api.neshama.pw")))
			{
				Config->ServerUrl = TEXT("https://api.neshama.pw");
				Config->Port = 443;
			}
			else
			{
				Config->ServerUrl = ServerUrl;
				Config->Port = 8420;
			}
		}

		FOnConnectionStateChanged OnTestComplete;
		OnTestComplete.BindLambda([TestClient](bool bSuccess)
		{
			if (bSuccess)
			{
				UE_LOG(LogTemp, Display, TEXT("[Neshama] Connection test: SUCCESS"));
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("[Neshama] Connection test: FAILED"));
			}
		});

		TestClient->Connect(OnTestComplete);
	}
}

// ============================================================================
// 配置快捷方式
// ============================================================================

void UNeshamaBlueprintLibrary::SetServerMode(ENeshamaServerMode Mode)
{
	UNeshamaConfig* Config = GetMutableDefault<UNeshamaConfig>();
	if (Config)
	{
		switch (Mode)
		{
		case ENeshamaServerMode::Cloud:
			Config->ServerUrl = TEXT("https://api.neshama.pw");
			Config->Port = 443;
			UE_LOG(LogTemp, Display, TEXT("[Neshama] Server mode set to Cloud (api.neshama.pw)"));
			break;

		case ENeshamaServerMode::Local:
			Config->ServerUrl = TEXT("http://localhost");
			Config->Port = 8420;
			UE_LOG(LogTemp, Display, TEXT("[Neshama] Server mode set to Local (localhost:8420)"));
			break;
		}

		Config->SaveConfig();
	}
}

ENeshamaServerMode UNeshamaBlueprintLibrary::GetServerMode()
{
	UNeshamaConfig* Config = GetMutableDefault<UNeshamaConfig>();
	if (Config)
	{
		if (Config->ServerUrl.Contains(TEXT("api.neshama.pw")) ||
			Config->ServerUrl.Contains(TEXT("neshama.ai")))
		{
			return ENeshamaServerMode::Cloud;
		}
	}

	return ENeshamaServerMode::Local;
}

TArray<FString> UNeshamaBlueprintLibrary::GetAvailablePresets()
{
	return {
		TEXT("tavern_keeper"),
		TEXT("guard_captain"),
		TEXT("mystic_traveler"),
		TEXT("merchant"),
		TEXT("healer"),
		TEXT("quest_giver"),
		TEXT("enemy_boss"),
		TEXT("companion")
	};
}

FString UNeshamaBlueprintLibrary::GetPresetDescription(const FString& PresetId)
{
	static const TMap<FString, FString> PresetDescriptions = {
		{TEXT("tavern_keeper"), TEXT("A friendly tavern keeper who loves to chat, remembers regular customers, and adjusts prices based on relationships.")},
		{TEXT("guard_captain"), TEXT("A disciplined guard captain who becomes suspicious of strangers, rewards loyalty, and unlocks quests for trusted allies.")},
		{TEXT("mystic_traveler"), TEXT("An enigmatic mystic who speaks in riddles, reacts to player alignment, and reveals secrets to those who earn their trust.")},
		{TEXT("merchant"), TEXT("A shrewd merchant who adjusts prices based on affinity, offers discounts to friends, and refuses service to enemies.")},
		{TEXT("healer"), TEXT("A compassionate healer who cares for the wounded, grows fond of frequent visitors, and may share rare remedies with trusted allies.")},
		{TEXT("quest_giver"), TEXT("A quest giver who evaluates the player's reputation, offers different quests based on trust level, and remembers past dealings.")},
		{TEXT("enemy_boss"), TEXT("A formidable enemy boss who taunts the player, remembers defeats, and becomes more aggressive or fearful based on history.")},
		{TEXT("companion"), TEXT("A loyal companion who develops a deep bond with the player, reacts emotionally to events, and provides morale-based support.")}
	};

	if (const FString* Desc = PresetDescriptions.Find(PresetId))
	{
		return *Desc;
	}

	return FString::Printf(TEXT("Custom NPC preset: %s"), *PresetId);
}

#undef LOCTEXT_NAMESPACE
