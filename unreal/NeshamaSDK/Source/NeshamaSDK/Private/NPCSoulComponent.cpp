// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - NPC灵魂组件实现文件

#include "NPCSoulComponent.h"
#include "NeshamaClient.h"
#include "NeshamaConfig.h"
#include "GameFramework/Actor.h"
#include "Engine/DrawDebugUtils.h"

#define LOCTEXT_NAMESPACE "NPCSoulComponent"

// ============================================================================
// UNPCSoulComponent 实现
// ============================================================================

UNPCSoulComponent::UNPCSoulComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, NpcId(TEXT("npc_001"))
	, Preset(TEXT("default"))
	, NpcName(TEXT("NPC"))
	, bAutoConnect(true)
	, bShowDebugInfo(false)
	, DebugColor(FColor::Cyan)
	, Client(nullptr)
	, ConnectedTime(0.0f)
	, bInitialized(false)
{
	// 启用Tick
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;
	
	// 默认每帧更新（用于调试显示）
	SetComponentTickEnabled(true);
}

UNPCSoulComponent::~UNPCSoulComponent()
{
	// 确保在销毁时断开连接
	if (bInitialized)
	{
		Disconnect();
	}
}

void UNPCSoulComponent::BeginPlay()
{
	Super::BeginPlay();

	// 生成默认NpcId（如果没有设置）
	if (NpcId.IsEmpty() || NpcId == TEXT("npc_001"))
	{
		NpcId = FString::Printf(TEXT("%s_%s"), *Preset, *FGuid::NewGuid().ToString());
	}

	// 初始化客户端
	InitializeClient();

	// 自动连接
	if (bAutoConnect)
	{
		Connect();
	}

	bInitialized = true;
}

void UNPCSoulComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// 断开连接
	if (bAutoConnect)
	{
		Disconnect();
	}

	// 取消订阅事件
	UnsubscribeFromClientEvents();

	// 清理客户端
	if (Client)
	{
		Client->RemoveFromRoot();
		Client = nullptr;
	}

	Super::EndPlay(EndPlayReason);
}

void UNPCSoulComponent::TickComponent(float DeltaTime, ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// 调试信息显示（仅在编辑器中）
#if WITH_EDITOR
	if (bShowDebugInfo && IsValid(GetOwner()))
	{
		FString DebugInfo = FString::Printf(
			TEXT("[%s]\nEmotion: %s\nState: %s"),
			*NpcName,
			*CurrentEmotion.Dominant,
			*IsConnected() ? TEXT("Connected") : TEXT("Disconnected")
		);

		DrawDebugString(
			GetWorld(),
			GetOwner()->GetActorLocation() + FVector(0, 0, 100),
			DebugInfo,
			nullptr,
			DebugColor,
			0.0f,
			true
		);
	}
#endif
}

void UNPCSoulComponent::InitializeClient()
{
	if (!Client)
	{
		// 创建客户端
		Client = NewObject<UNeshamaClient>(this);
		Client->AddToRoot();
		
		// 如果有自定义服务器URL，更新配置
		if (!CustomServerUrl.IsEmpty())
		{
			UNeshamaConfig* Config = Client->GetConfig();
			if (Config)
			{
				Config->ServerUrl = CustomServerUrl;
			}
		}
		
		// 订阅事件
		SubscribeToClientEvents();
	}
}

void UNPCSoulComponent::SubscribeToClientEvents()
{
	if (!Client) return;

	// 使用蓝图可绑定的事件（OnConnectionStateChanged等）
	// 这些会在UNeshamaClient中触发时自动广播到BP
}

void UNPCSoulComponent::UnsubscribeFromClientEvents()
{
	if (!Client) return;
	
	// 清空所有绑定
	Client->OnConnectionStateChanged.Clear();
	Client->OnEmotionChanged.Clear();
	Client->OnBehaviorChanged.Clear();
	Client->OnChatResponse.Clear();
	Client->OnError.Clear();
	Client->OnLog.Clear();
}

FString UNPCSoulComponent::GetEffectiveServerUrl() const
{
	if (!CustomServerUrl.IsEmpty())
	{
		return CustomServerUrl;
	}
	
	// 从全局配置获取
	UNeshamaConfig* Config = UNeshamaConfig::Get();
	if (Config)
	{
		return Config->ServerUrl;
	}
	
	return TEXT("http://localhost:8420");
}

void UNPCSoulComponent::Connect()
{
	if (!Client)
	{
		InitializeClient();
	}

	if (Client)
	{
		// 清空之前的回调
		Client->OnConnectionStateChanged.Clear();
		Client->OnEmotionChanged.Clear();
		Client->OnBehaviorChanged.Clear();
		Client->OnChatResponse.Clear();
		Client->OnError.Clear();
		Client->OnLog.Clear();

		// 绑定连接状态变化回调
		Client->OnConnectionStateChanged.AddDynamic(this, &UNPCSoulComponent::HandleConnectionStateChanged);
		
		// 绑定错误回调
		Client->OnError.AddDynamic(this, &UNPCSoulComponent::HandleError);
		
		// 绑定日志回调
		Client->OnLog.AddDynamic(this, &UNPCSoulComponent::HandleLog);

		// 调用连接
		FOnConnectCompleteDelegate OnComplete;
		OnComplete.BindLambda([this](bool bSuccess)
		{
			if (bSuccess)
			{
				ConnectedTime = GetWorld()->GetTimeSeconds();
				
				// 创建NPC（如果需要）
				if (!Preset.IsEmpty())
				{
					CreateNPC();
				}
			}
		});
		
		Client->Connect(OnComplete);
	}
}

void UNPCSoulComponent::Disconnect()
{
	if (Client)
	{
		Client->OnConnectionStateChanged.Clear();
		Client->OnEmotionChanged.Clear();
		Client->OnBehaviorChanged.Clear();
		Client->OnChatResponse.Clear();
		Client->OnError.Clear();
		Client->OnLog.Clear();
		
		Client->Disconnect();
	}
}

bool UNPCSoulComponent::IsConnected() const
{
	return Client && Client->IsConnected();
}

void UNPCSoulComponent::SendGameEvent(EGameEventType EventType, float Intensity,
	const TMap<FString, FString>& Context)
{
	if (!Client || !Client->IsConnected())
	{
		UE_LOG(LogTemp, Warning, TEXT("[NPCSoul] Not connected, cannot send event"));
		return;
	}

	FOnEventResponseDelegate OnComplete;
	OnComplete.BindLambda([this](FEventResponse Response)
	{
		// 更新当前情绪状态
		if (Response.EmotionState.Emotions.Num() > 0)
		{
			CurrentEmotion = Response.EmotionState;
			
			// 触发Blueprint事件
			OnEmotionChanged(Response.EmotionState);
		}
		
		// 更新行为建议
		if (Response.BehaviorHints.Num() > 0)
		{
			CurrentBehaviors = Response.BehaviorHints;
			
			// 触发Blueprint事件
			for (const FBehaviorHint& Hint : Response.BehaviorHints)
			{
				OnBehaviorChangedBP(Hint.Type, Hint.Value);
			}
		}
	});

	Client->SendGameEvent(NpcId, EventType, Intensity, Context, OnComplete);
}

void UNPCSoulComponent::SendGameEventSimple(EGameEventType EventType, float Intensity)
{
	SendGameEvent(EventType, Intensity, TMap<FString, FString>());
}

void UNPCSoulComponent::Chat(const FString& Message, const FString& PlayerId)
{
	if (!Client || !Client->IsConnected())
	{
		UE_LOG(LogTemp, Warning, TEXT("[NPCSoul] Not connected, cannot send chat"));
		return;
	}

	FOnChatCompleteDelegate OnComplete;
	OnComplete.BindLambda([this](FChatResponse Response)
	{
		// 更新情绪状态
		if (Response.EmotionAfter.Emotions.Num() > 0)
		{
			CurrentEmotion = Response.EmotionAfter;
			OnEmotionChanged(Response.EmotionAfter);
		}
		
		// 触发Blueprint事件
		OnChatResponseBP(Response.Content);
	});

	Client->Chat(NpcId, Message, PlayerId, OnComplete);
}

void UNPCSoulComponent::GetBehaviorHints()
{
	if (!Client || !Client->IsConnected())
	{
		UE_LOG(LogTemp, Warning, TEXT("[NPCSoul] Not connected, cannot get behavior hints"));
		return;
	}

	FOnBehaviorResponseDelegate OnComplete;
	OnComplete.BindLambda([this](FBehaviorResponse Response)
	{
		CurrentBehaviors = Response.Modifiers;
		
		// 触发Blueprint事件
		for (const FBehaviorHint& Hint : Response.Modifiers)
		{
			OnBehaviorChangedBP(Hint.Type, Hint.Value);
		}
	});

	Client->GetBehaviorHints(NpcId, OnComplete);
}

void UNPCSoulComponent::RememberEntity(const FString& EntityType, const FString& EntityName,
	const FString& Relation, const FString& Note)
{
	if (!Client || !Client->IsConnected())
	{
		UE_LOG(LogTemp, Warning, TEXT("[NPCSoul] Not connected, cannot remember entity"));
		return;
	}

	FOnRememberResponseDelegate OnComplete;
	OnComplete.BindLambda([this](FMemoryListResponse Response)
	{
		UE_LOG(LogTemp, Display, TEXT("[NPCSoul] Entity remembered successfully"));
	});

	Client->Remember(NpcId, EntityType, EntityName, Relation, Note, OnComplete);
}

void UNPCSoulComponent::GetProfile()
{
	if (!Client || !Client->IsConnected())
	{
		UE_LOG(LogTemp, Warning, TEXT("[NPCSoul] Not connected, cannot get profile"));
		return;
	}

	FOnNPCProfileDelegate OnComplete;
	OnComplete.BindLambda([this](FNPCProfile Profile)
	{
		CurrentProfile = Profile;
		UE_LOG(LogTemp, Display, TEXT("[NPCSoul] Profile retrieved: %s"), *Profile.Name);
	});

	Client->GetProfile(NpcId, OnComplete);
}

void UNPCSoulComponent::GetRelations()
{
	if (!Client || !Client->IsConnected())
	{
		UE_LOG(LogTemp, Warning, TEXT("[NPCSoul] Not connected, cannot get relations"));
		return;
	}

	FOnRelationGraphDelegate OnComplete;
	OnComplete.BindLambda([this](FRelationGraph Relations)
	{
		CurrentRelations = Relations;
		UE_LOG(LogTemp, Display, TEXT("[NPCSoul] Relations retrieved: %d"), Relations.Relations.Num());
	});

	Client->GetRelations(NpcId, OnComplete);
}

void UNPCSoulComponent::CreateNPC()
{
	if (!Client || !Client->IsConnected())
	{
		UE_LOG(LogTemp, Warning, TEXT("[NPCSoul] Not connected, cannot create NPC"));
		return;
	}

	FOnCreateNPCResponseDelegate OnComplete;
	OnComplete.BindLambda([this](FCreateNPCResponse Response)
	{
		if (Response.Success)
		{
			CurrentProfile = Response.Profile;
			UE_LOG(LogTemp, Display, TEXT("[NPCSoul] NPC created: %s"), *Response.NpcId);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[NPCSoul] Failed to create NPC: %s"), *Response.Error);
		}
	});

	Client->CreateNPC(NpcName, Preset, OnComplete);
}

// ============================================================================
// 内部回调处理
// ============================================================================

void UNPCSoulComponent::HandleConnectionStateChanged(bool bIsConnected)
{
	OnConnectionStateChanged(bIsConnected);
}

void UNPCSoulComponent::HandleError(FString ErrorMessage)
{
	OnErrorBP(ErrorMessage);
}

void UNPCSoulComponent::HandleLog(FString LogMessage)
{
	OnLogBP(LogMessage);
}

// ============================================================================
// UNPCSoulComponentLibrary 实现
// ============================================================================

UNPCSoulComponent* UNPCSoulComponentLibrary::GetNPCSoulComponent(AActor* Actor)
{
	if (!Actor) return nullptr;
	return Actor->FindComponentByClass<UNPCSoulComponent>();
}

bool UNPCSoulComponentLibrary::HasDominantEmotion(UNPCSoulComponent* SoulComponent, 
	EEmotionType EmotionType)
{
	if (!SoulComponent) return false;
	return SoulComponent->GetDominantEmotionType() == EmotionType;
}

FString UNPCSoulComponentLibrary::GetEmotionDescription(FEmotionState EmotionState)
{
	FString EmotionName;
	
	switch (EmotionState.GetDominantEmotionType())
	{
	case EEmotionType::Joy:
		EmotionName = TEXT("开心");
		break;
	case EEmotionType::Sadness:
		EmotionName = TEXT("悲伤");
		break;
	case EEmotionType::Anger:
		EmotionName = TEXT("愤怒");
		break;
	case EEmotionType::Fear:
		EmotionName = TEXT("恐惧");
		break;
	case EEmotionType::Surprise:
		EmotionName = TEXT("惊讶");
		break;
	case EEmotionType::Disgust:
		EmotionName = TEXT("厌恶");
		break;
	case EEmotionType::Trust:
		EmotionName = TEXT("信任");
		break;
	case EEmotionType::Anticipation:
		EmotionName = TEXT("期待");
		break;
	case EEmotionType::Shame:
		EmotionName = TEXT("羞愧");
		break;
	default:
		EmotionName = TEXT("未知");
		break;
	}
	
	if (!EmotionState.Composite.IsEmpty())
	{
		return FString::Printf(TEXT("%s (%s)"), *EmotionName, *EmotionState.Composite);
	}
	
	return EmotionName;
}

FString UNPCSoulComponentLibrary::EmotionToDebugString(FEmotionState EmotionState)
{
	FString Output = FString::Printf(
		TEXT("Dominant: %s\nComposite: %s\nEmotions:\n"),
		*EmotionState.Dominant,
		*EmotionState.Composite
	);
	
	for (const auto& KVP : EmotionState.Emotions)
	{
		Output += FString::Printf(TEXT("  %s: %.2f\n"), *KVP.Key, KVP.Value);
	}
	
	return Output;
}

#undef LOCTEXT_NAMESPACE
