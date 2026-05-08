// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - HTTP客户端头文件
// 基于 UE5 FHttpModule 的异步HTTP通信封装

#pragma once

#include "CoreMinimal.h"
#include "NeshamaTypes.h"
#include "NeshamaConfig.h"
#include "NeshamaClient.generated.h"

// 前向声明
class IHttpRequest;
class IHttpResponse;


// ============================================================================
// C++ 内部回调委托声明（非动态，用于C++代码的BindLambda）
// 注意：UE5 DECLARE_DYNAMIC_DELEGATE 不支持 BindLambda，只能用 BindUFunction。
// Blueprint 用户应使用 multicast 事件（OnEmotionChanged, OnChatResponse 等）
// C++ 代码使用 TFunction 回调或非动态委托的 BindLambda。
// ============================================================================

/**
 * 创建NPC响应委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaCreateNPCResponseDelegate, FCreateNPCResponse);

/**
 * NPC档案委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaNPCProfileDelegate, FNPCProfile);

/**
 * 情绪状态委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaEmotionStateDelegate, FEmotionState);

/**
 * 行为响应委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaBehaviorResponseDelegate, FBehaviorResponse);

/**
 * 记忆列表响应委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaMemoryListResponseDelegate, FMemoryListResponse);

/**
 * 记忆响应委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaRememberResponseDelegate, FMemoryListResponse);

/**
 * 关系图谱委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaRelationGraphDelegate, FRelationGraph);

/**
 * 事件响应委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaEventResponseDelegate, FEventResponse);

/**
 * 连接完成回调委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaConnectCompleteDelegate, bool);

/**
 * 对话完成回调委托（C++内部用）
 */
DECLARE_DELEGATE_OneParam(FNeshamaChatCompleteDelegate, FChatResponse);

/**
 * Neshama SDK 核心HTTP客户端
 * 基于 UE5 FHttpModule 的异步HTTP通信封装
 * 支持所有API端点的调用
 */
UCLASS(BlueprintType, Blueprintable)
class NESHAMASDK_API UNeshamaClient : public UObject
{
	GENERATED_BODY()

public:
	// ============================================================================
	// 构造函数
	// ============================================================================

	/**
	 * 创建Neshama客户端
	 * @param Config 配置对象，如果为nullptr则使用默认配置
	 */
	UNeshamaClient(const FObjectInitializer& ObjectInitializer = FObjectInitializer::Get());

	/**
	 * 析构函数 - 清理资源
	 */
	virtual ~UNeshamaClient();

	// ============================================================================
	// 连接管理
	// ============================================================================

	/**
	 * 连接到服务器（Blueprint版，通过OnConnectionStateChanged事件获取结果）
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Connection")
	void Connect();

	/**
	 * 连接到服务器（C++版，支持回调）
	 * @param OnComplete 连接完成回调
	 */
	void ConnectWithCallback(const FNeshamaConnectCompleteDelegate& OnComplete);

	/**
	 * 断开连接
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Connection")
	void Disconnect();

	/**
	 * 取消所有活跃请求
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Connection")
	void CancelAllRequests();

	/**
	 * 检查是否已连接
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Client|Connection")
	bool IsConnected() const { return bIsConnected; }

	/**
	 * 获取连接状态
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Client|Connection")
	EConnectionState GetConnectionState() const { return ConnectionState; }

	// ============================================================================
	// NPC管理API
	// ============================================================================

	/**
	 * 创建新NPC（Blueprint版，通过OnConnectionStateChanged等事件获取结果）
	 * @param Name NPC名称
	 * @param Preset 预设模板
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|NPC")
	void CreateNPC(const FString& Name, const FString& Preset);

	/**
	 * 创建新NPC（C++版，支持回调）
	 */
	void CreateNPCWithCallback(const FString& Name, const FString& Preset,
		const FNeshamaCreateNPCResponseDelegate& OnComplete);

	/**
	 * 获取NPC档案（Blueprint版）
	 * @param NpcId NPC ID
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|NPC")
	void GetProfile(const FString& NpcId);

	/**
	 * 获取NPC档案（C++版，支持回调）
	 */
	void GetProfileWithCallback(const FString& NpcId, const FNeshamaNPCProfileDelegate& OnComplete);

	// ============================================================================
	// 事件推送API
	// ============================================================================

	/**
	 * 推送游戏事件（Blueprint版）
	 * @param NpcId NPC ID
	 * @param GameEvent 游戏事件
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Event")
	void SendEvent(const FString& NpcId, const FGameEvent& GameEvent);

	/**
	 * 推送游戏事件（C++版，支持回调）
	 */
	void SendEventWithCallback(const FString& NpcId, const FGameEvent& GameEvent,
		const FNeshamaEventResponseDelegate& OnComplete);

	/**
	 * 推送游戏事件（使用枚举类型，Blueprint内部用）
	 * @param NpcId NPC ID
	 * @param EventType 事件类型枚举
	 * @param Intensity 事件强度
	 * @param Context 上下文数据
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Event", meta = (BlueprintInternalUseOnly = "true"))
	void SendGameEvent(const FString& NpcId, EGameEventType EventType, 
		float Intensity, const TMap<FString, FString>& Context);

	/**
	 * 推送游戏事件（C++版，支持回调）
	 */
	void SendGameEventWithCallback(const FString& NpcId, EGameEventType EventType, 
		float Intensity, const TMap<FString, FString>& Context,
		const FNeshamaEventResponseDelegate& OnComplete);

	// ============================================================================
	// 情绪状态API
	// ============================================================================

	/**
	 * 获取NPC当前情绪状态（Blueprint版）
	 * @param NpcId NPC ID
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Emotion")
	void GetEmotion(const FString& NpcId);

	/**
	 * 获取NPC当前情绪状态（C++版，支持回调）
	 */
	void GetEmotionWithCallback(const FString& NpcId, const FNeshamaEmotionStateDelegate& OnComplete);

	// ============================================================================
	// 行为建议API
	// ============================================================================

	/**
	 * 获取NPC行为建议（Blueprint版）
	 * @param NpcId NPC ID
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Behavior")
	void GetBehaviorHints(const FString& NpcId);

	/**
	 * 获取NPC行为建议（C++版，支持回调）
	 */
	void GetBehaviorHintsWithCallback(const FString& NpcId, const FNeshamaBehaviorResponseDelegate& OnComplete);

	// ============================================================================
	// 对话API
	// ============================================================================

	/**
	 * 与NPC对话（Blueprint版，通过OnChatResponse事件获取结果）
	 * @param NpcId NPC ID
	 * @param Message 消息内容
	 * @param PlayerId 玩家ID（可选，默认使用配置中的默认玩家ID）
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Chat")
	void Chat(const FString& NpcId, const FString& Message, const FString& PlayerId);

	/**
	 * 与NPC对话（C++版，支持回调）
	 */
	void ChatWithCallback(const FString& NpcId, const FString& Message, 
		const FString& PlayerId, const FNeshamaChatCompleteDelegate& OnComplete);

	// ============================================================================
	// 记忆API
	// ============================================================================

	/**
	 * 获取NPC的记忆（Blueprint版）
	 * @param NpcId NPC ID
	 * @param Query 查询条件（可选）
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Memory")
	void GetMemory(const FString& NpcId, const FString& Query);

	/**
	 * 获取NPC的记忆（C++版，支持回调）
	 */
	void GetMemoryWithCallback(const FString& NpcId, const FString& Query,
		const FNeshamaMemoryListResponseDelegate& OnComplete);

	/**
	 * 让NPC记住实体（Blueprint版）
	 * @param NpcId NPC ID
	 * @param EntityType 实体类型
	 * @param EntityName 实体名称
	 * @param Relation 关系类型（可选）
	 * @param Note 备注（可选）
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Memory")
	void Remember(const FString& NpcId, const FString& EntityType,
		const FString& EntityName, const FString& Relation, const FString& Note);

	/**
	 * 让NPC记住实体（C++版，支持回调）
	 */
	void RememberWithCallback(const FString& NpcId, const FString& EntityType,
		const FString& EntityName, const FString& Relation,
		const FString& Note, const FNeshamaRememberResponseDelegate& OnComplete);

	// ============================================================================
	// 关系图谱API
	// ============================================================================

	/**
	 * 获取NPC的关系图谱（Blueprint版）
	 * @param NpcId NPC ID
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client|Relation")
	void GetRelations(const FString& NpcId);

	/**
	 * 获取NPC的关系图谱（C++版，支持回调）
	 */
	void GetRelationsWithCallback(const FString& NpcId, const FNeshamaRelationGraphDelegate& OnComplete);

	// ============================================================================
	// 配置和事件
	// ============================================================================

	/** 获取配置 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Client")
	UNeshamaConfig* GetConfig() const { return Config; }

	/** 设置配置 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Client")
	void SetConfig(UNeshamaConfig* NewConfig);

	/**
	 * 连接状态变化事件
	 * Blueprint可绑定此事件
	 */
	UPROPERTY(BlueprintAssignable, Category = "Neshama|Client|Events")
	FOnConnectionStateChanged OnConnectionStateChanged;

	/**
	 * 情绪变化事件
	 */
	UPROPERTY(BlueprintAssignable, Category = "Neshama|Client|Events")
	FOnEmotionChanged OnEmotionChanged;

	/**
	 * 行为变化事件
	 */
	UPROPERTY(BlueprintAssignable, Category = "Neshama|Client|Events")
	FOnBehaviorChanged OnBehaviorChanged;

	/**
	 * 对话响应事件
	 */
	UPROPERTY(BlueprintAssignable, Category = "Neshama|Client|Events")
	FOnChatResponse OnChatResponse;

	/**
	 * 错误事件
	 */
	UPROPERTY(BlueprintAssignable, Category = "Neshama|Client|Events")
	FOnError OnError;

	/**
	 * 日志事件
	 */
	UPROPERTY(BlueprintAssignable, Category = "Neshama|Client|Events")
	FOnLog OnLog;

protected:
	// ============================================================================
	// 受保护的方法
	// ============================================================================

	/**
	 * 初始化HTTP模块
	 */
	void InitializeHttp();

	/**
	 * 创建HTTP请求
	 * @param Verb HTTP方法 (GET, POST, PUT, DELETE)
	 * @param Url 完整URL
	 * @return HTTP请求指针
	 */
	IHttpRequest* CreateRequest(const FString& Verb, const FString& Url);

	/**
	 * 发送GET请求
	 */
	void SendGetRequest(const FString& Endpoint, TFunction<void(bool, const FString&)> OnComplete);

	/**
	 * 发送POST请求
	 */
	void SendPostRequest(const FString& Endpoint, const FString& Body, 
		TFunction<void(bool, const FString&)> OnComplete);

	/**
	 * 处理JSON响应
	 */
	bool ProcessJsonResponse(const FString& ResponseString, TSharedPtr<FJsonObject>& OutJsonObject);

	/**
	 * 记录日志
	 */
	void Log(ENeshamaLogLevel Level, const FString& Message);

	/**
	 * 触发错误回调
	 */
	void TriggerError(const FString& ErrorMessage);

private:
	// ============================================================================
	// 私有成员
	// ============================================================================

	/** 配置对象 */
	UPROPERTY()
	UNeshamaConfig* Config;

	/** 连接状态 */
	UPROPERTY()
	EConnectionState ConnectionState;

	/** 是否已连接 */
	UPROPERTY()
	bool bIsConnected;

	/** 当前活跃的请求数量 */
	int32 ActiveRequestCount;

	/** 重连尝试次数 */
	int32 ReconnectAttempts;

	/** 是否正在释放 */
	bool bDisposed;

	/** 标记是否已初始化 */
	bool bInitialized;
};

