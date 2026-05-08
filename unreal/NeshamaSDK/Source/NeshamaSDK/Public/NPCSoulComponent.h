// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - NPC灵魂组件头文件
// 可挂载到任意Actor的UActorComponent，自动管理NPC灵魂连接

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "NeshamaTypes.h"
#include "NPCSoulComponent.generated.h"

// 前向声明
class UNeshamaClient;
class UNeshamaConfig;

/**
 * NPC灵魂组件
 * 
 * 核心组件，挂载到NPC的Actor上即可使用
 * 自动管理与Neshama服务器的连接，支持情绪状态同步和行为建议获取
 * 
 * 使用方式：
 * 1. 将此组件添加到NPC的Actor上
 * 2. 在Details面板中配置 NpcId 和 Preset
 * 3. 调用 SendGameEvent、Chat 等方法与NPC交互
 * 4. 绑定 OnEmotionChanged 等Blueprint事件获取状态变化通知
 * 
 * Blueprint支持：
 * - 所有API方法都标记为 BlueprintCallable
 * - 所有事件回调都标记为 BlueprintImplementableEvent
 * - 可在Blueprint中直接使用
 */
UCLASS(Blueprintable, BlueprintType, hideCategories = (Object, LOD, Lighting, Collision, Input, Activation, "Components|Activation"), meta = (DisplayName = "NPC Soul", ToolTip = "Neshama NPC灵魂组件"))
class NESHAMASDK_API UNPCSoulComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	// ============================================================================
	// 构造函数
	// ============================================================================

	/** 默认构造函数 */
	UNPCSoulComponent(const FObjectInitializer& ObjectInitializer = FObjectInitializer::Get());

	/**
	 * 析构函数
	 */
	virtual ~UNPCSoulComponent();

	// ============================================================================
	// 编辑器配置属性
	// ============================================================================

	/** NPC身份配置 - 折叠分组 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|NPC Identity",
		meta = (DisplayName = "NPC ID", ToolTip = "NPC唯一标识符，在整个游戏中应该唯一"))
	FString NpcId;

	/** NPC预设模板类型（如 tavern_keeper, guard_captain 等） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|NPC Identity",
		meta = (DisplayName = "Preset", ToolTip = "NPC预设模板类型"))
	FString Preset;

	/** NPC显示名称 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|NPC Identity",
		meta = (DisplayName = "Display Name", ToolTip = "NPC显示名称"))
	FString NpcName;

	/** 连接配置 - 折叠分组 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Auto Connect", ToolTip = "是否在BeginPlay时自动连接服务器"))
	bool bAutoConnect;

	/** 服务器地址（覆盖全局配置） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Custom Server URL", ToolTip = "自定义服务器地址，留空使用全局配置"))
	FString CustomServerUrl;

	/** 调试配置 - 折叠分组 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Debug",
		meta = (DisplayName = "Show Debug Info", ToolTip = "是否在场景中显示调试信息"))
	bool bShowDebugInfo;

	/** 调试信息颜色 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|Debug",
		meta = (DisplayName = "Debug Color", ToolTip = "调试信息颜色"))
	FColor DebugColor;

	// ============================================================================
	// Blueprint可调用方法
	// ============================================================================

	/**
	 * 连接到Neshama服务器
	 * 如果 bAutoConnect 为 true，则在 BeginPlay 时自动调用
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Connection",
		meta = (DisplayName = "Connect", ToolTip = "连接到Neshama服务器"))
	void Connect();

	/**
	 * 断开与Neshama服务器的连接
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Connection",
		meta = (DisplayName = "Disconnect", ToolTip = "断开与Neshama服务器的连接"))
	void Disconnect();

	/**
	 * 发送游戏事件
	 * @param EventType 事件类型枚举
	 * @param Intensity 事件强度 (0-1)
	 * @param Context 上下文数据（可选）
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Event",
		meta = (DisplayName = "Send Game Event", ToolTip = "发送游戏事件到服务器", BlueprintInternalUseOnly = "true"))
	void SendGameEvent(EGameEventType EventType, float Intensity, 
		const TMap<FString, FString>& Context);

	/** 发送游戏事件到服务器（简化版，无需上下文） */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Event",
		meta = (DisplayName = "Send Game Event (Simple)", ToolTip = "发送游戏事件到服务器"))
	void SendGameEvent(EGameEventType EventType, float Intensity = 1.0f);

	/**
	 * 与NPC对话
	 * @param Message 玩家发送的消息
	 * @param PlayerId 玩家ID（可选，默认使用配置的默认玩家ID）
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Chat",
		meta = (DisplayName = "Chat", ToolTip = "与NPC对话"))
	void Chat(const FString& Message, const FString& PlayerId = TEXT(""));

	/**
	 * 获取当前情绪状态
	 * @return 当前情绪状态
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Emotion",
		meta = (DisplayName = "Get Emotion State", ToolTip = "获取当前情绪状态"))
	FEmotionState GetEmotionState() const { return CurrentEmotion; }

	/**
	 * 获取行为建议
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Behavior",
		meta = (DisplayName = "Get Behavior Hints", ToolTip = "获取NPC行为建议"))
	void GetBehaviorHints();

	/**
	 * 让NPC记住实体
	 * @param EntityType 实体类型 (如 "player", "item", "location")
	 * @param EntityName 实体名称
	 * @param Relation 关系类型（可选）
	 * @param Note 备注（可选）
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Memory",
		meta = (DisplayName = "Remember Entity", ToolTip = "让NPC记住实体"))
	void RememberEntity(const FString& EntityType, const FString& EntityName,
		const FString& Relation = TEXT(""), const FString& Note = TEXT(""));

	/**
	 * 获取NPC档案
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|NPC",
		meta = (DisplayName = "Get Profile", ToolTip = "获取NPC档案"))
	void GetProfile();

	/**
	 * 获取关系图谱
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Relation",
		meta = (DisplayName = "Get Relations", ToolTip = "获取NPC关系图谱"))
	void GetRelations();

	/**
	 * 创建NPC（如果服务器端需要）
	 * 通常在游戏开始时调用
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|NPC",
		meta = (DisplayName = "Create NPC", ToolTip = "在服务器上创建NPC"))
	void CreateNPC();

	// ============================================================================
	// Blueprint事件（实现）
	// ============================================================================

	/**
	 * 连接状态变化时触发
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Neshama|Events",
		meta = (DisplayName = "On Connection State Changed", ToolTip = "连接状态变化时触发"))
	void OnConnectionStateChanged(bool bIsConnected);

	/**
	 * 情绪变化时触发
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Neshama|Events",
		meta = (DisplayName = "On Emotion Changed", ToolTip = "情绪变化时触发"))
	void OnEmotionChanged(FEmotionState NewEmotion);

	/**
	 * 行为建议变化时触发
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Neshama|Events",
		meta = (DisplayName = "On Behavior Changed", ToolTip = "行为建议变化时触发"))
	void OnBehaviorChangedBP(FString BehaviorType, FString Value);

	/**
	 * 收到对话回复时触发
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Neshama|Events",
		meta = (DisplayName = "On Chat Response", ToolTip = "收到对话回复时触发"))
	void OnChatResponseBP(FString Response);

	/**
	 * 发生错误时触发
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Neshama|Events",
		meta = (DisplayName = "On Error", ToolTip = "发生错误时触发"))
	void OnErrorBP(FString ErrorMessage);

	/**
	 * 日志消息（用于调试）
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Neshama|Events",
		meta = (DisplayName = "On Log", ToolTip = "日志消息（用于调试）"))
	void OnLogBP(FString LogMessage);

	// ============================================================================
	// 属性访问器
	// ============================================================================

	/** 获取NPC ID */
	UFUNCTION(BlueprintPure, Category = "Neshama|NPC")
	FString GetNpcId() const { return NpcId; }

	/** 获取NPC名称 */
	UFUNCTION(BlueprintPure, Category = "Neshama|NPC")
	FString GetNpcName() const { return NpcName; }

	/** 获取预设 */
	UFUNCTION(BlueprintPure, Category = "Neshama|NPC")
	FString GetPreset() const { return Preset; }

	/** 是否已连接 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Connection")
	bool IsConnected() const;

	/** 获取客户端实例 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Client")
	UNeshamaClient* GetClient() const { return Client; }

	/** 获取当前情绪 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Emotion")
	FEmotionState GetCurrentEmotion() const { return CurrentEmotion; }

	/** 获取主导情绪类型 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Emotion")
	EEmotionType GetDominantEmotionType() const { return CurrentEmotion.GetDominantEmotionType(); }

	/** 获取行为建议列表 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Behavior")
	TArray<FBehaviorHint> GetCurrentBehaviors() const { return CurrentBehaviors; }


	// ============================================================================
	// 内部回调处理
	// ============================================================================

	/**
	 * 连接状态变化回调（由AddDynamic绑定）
	 */
	UFUNCTION()
	void HandleConnectionStateChanged(bool bIsConnected);

	/**
	 * 错误回调（由AddDynamic绑定）
	 */
	UFUNCTION()
	void HandleError(FString ErrorMessage);

	/**
	 * 日志回调（由AddDynamic绑定）
	 */
	UFUNCTION()
	void HandleLog(FString LogMessage);

protected:
	// ============================================================================
	// 保护方法
	// ============================================================================

	/**
	 * 开始播放时调用
	 */
	virtual void BeginPlay() override;

	/**
	 * 结束播放时调用
	 */
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/**
	 * 每帧更新
	 */
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, 
		FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * 初始化客户端
	 */
	void InitializeClient();

	/**
	 * 订阅客户端事件
	 */
	void SubscribeToClientEvents();

	/**
	 * 取消订阅客户端事件
	 */
	void UnsubscribeFromClientEvents();

	/**
	 * 获取有效的服务器URL
	 */
	FString GetEffectiveServerUrl() const;

private:
	// ============================================================================
	// 私有成员
	// ============================================================================

	/** Neshama客户端实例 */
	UPROPERTY()
	UNeshamaClient* Client;

	/** 当前NPC档案 */
	UPROPERTY()
	FNPCProfile CurrentProfile;

	/** 当前情绪状态 */
	UPROPERTY()
	FEmotionState CurrentEmotion;

	/** 当前行为建议列表 */
	UPROPERTY()
	TArray<FBehaviorHint> CurrentBehaviors;

	/** 当前关系图谱 */
	UPROPERTY()
	FRelationGraph CurrentRelations;

	/** 连接时间（用于调试显示） */
	float ConnectedTime;

	/** 是否已初始化 */
	bool bInitialized;
};

// ============================================================================
// Blueprint函数库扩展
// ============================================================================

/**
 * NPCSoulComponent的Blueprint工具函数
 */
UCLASS()
class NESHAMASDK_API UNPCSoulComponentLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * 获取指定Actor的NPCSoulComponent
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Utilities",
		meta = (DisplayName = "Get NPC Soul Component", CompactNodeTitle = "NPC Soul",
			ToolTip = "获取指定Actor的NPCSoulComponent"))
	static UNPCSoulComponent* GetNPCSoulComponent(AActor* Actor);

	/**
	 * 判断NPC是否具有指定的主导情绪
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Utilities",
		meta = (DisplayName = "Has Dominant Emotion", ToolTip = "判断NPC是否具有指定的主导情绪"))
	static bool HasDominantEmotion(UNPCSoulComponent* SoulComponent, EEmotionType EmotionType);

	/**
	 * 获取NPC情绪的友好描述
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Utilities",
		meta = (DisplayName = "Get Emotion Description", ToolTip = "获取NPC情绪的友好描述"))
	static FString GetEmotionDescription(FEmotionState EmotionState);

	/**
	 * 将情绪状态转换为调试信息字符串
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Utilities",
		meta = (DisplayName = "Emotion To Debug String", ToolTip = "将情绪状态转换为调试信息字符串"))
	static FString EmotionToDebugString(FEmotionState EmotionState);
};
