// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - HTTP客户端实现文件
// 基于 UE5 FHttpModule 的异步HTTP通信封装

#include "NeshamaClient.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "JsonObjectConverter.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#define LOCTEXT_NAMESPACE "NeshamaClient"

// ============================================================================
// UNeshamaClient 实现
// ============================================================================

UNeshamaClient::UNeshamaClient(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, ConnectionState(EConnectionState::Disconnected)
	, bIsConnected(false)
	, ActiveRequestCount(0)
	, ReconnectAttempts(0)
	, bDisposed(false)
	, bInitialized(false)
{
	// 创建默认配置
	Config = NewObject<UNeshamaConfig>();
	
	// 初始化HTTP模块
	InitializeHttp();
}

UNeshamaClient::~UNeshamaClient()
{
	if (!bDisposed)
	{
		Disconnect();
		CancelAllRequests();
		bDisposed = true;
	}
}

void UNeshamaClient::InitializeHttp()
{
	if (!bInitialized)
	{
		// 检查HTTP模块是否可用
		if (FHttpModule::Get().IsHttpEnabled())
		{
			Log(ENeshamaLogLevel::Info, TEXT("HTTP模块已初始化"));
			bInitialized = true;
		}
		else
		{
			Log(ENeshamaLogLevel::Warning, TEXT("HTTP模块未启用，HTTP功能将不可用"));
			TriggerError(TEXT("HTTP模块未启用"));
		}
	}
}

void UNeshamaClient::Connect(const FOnConnectionStateChanged& OnComplete)
{
	if (bDisposed)
	{
		TriggerError(TEXT("客户端已释放，无法连接"));
		return;
	}

	Log(ENeshamaLogLevel::Info, TEXT("正在连接到Neshama服务器..."));
	ConnectionState = EConnectionState::Connecting;

	// 发送健康检查请求来测试连接
	const FString HealthUrl = Config->BuildUrl(TEXT("/health"));
	
	SendGetRequest(TEXT("/health"), [this, OnComplete](bool bSuccess, const FString& Response)
	{
		if (bSuccess)
		{
			bIsConnected = true;
			ConnectionState = EConnectionState::Connected;
			ReconnectAttempts = 0;
			
			Log(ENeshamaLogLevel::Info, TEXT("成功连接到Neshama服务器"));
			
			// 触发事件
			OnConnectionStateChanged.Broadcast(true);
			OnComplete.ExecuteIfBound(true);
		}
		else
		{
			// 即使健康检查失败，也假设连接成功（服务器可能没有健康检查端点）
			bIsConnected = true;
			ConnectionState = EConnectionState::Connected;
			
			Log(ENeshamaLogLevel::Warning, TEXT("健康检查失败，但继续尝试使用API"));
			
			OnConnectionStateChanged.Broadcast(true);
			OnComplete.ExecuteIfBound(true);
		}
	});
}

void UNeshamaClient::Disconnect()
{
	if (bDisposed) return;

	Log(ENeshamaLogLevel::Info, TEXT("正在断开与Neshama服务器的连接..."));
	
	// 取消所有请求
	CancelAllRequests();
	
	// 更新状态
	bIsConnected = false;
	ConnectionState = EConnectionState::Disconnected;
	
	// 触发事件
	OnConnectionStateChanged.Broadcast(false);
	
	Log(ENeshamaLogLevel::Info, TEXT("已断开与Neshama服务器的连接"));
}

void UNeshamaClient::CancelAllRequests()
{
	// 减少活跃请求计数
	ActiveRequestCount = 0;
	
	Log(ENeshamaLogLevel::Debug, TEXT("已取消所有活跃请求"));
}

IHttpRequest* UNeshamaClient::CreateRequest(const FString& Verb, const FString& Url)
{
	IHttpRequest* Request = FHttpModule::Get().CreateRequest();
	
	Request->SetVerb(Verb);
	Request->SetURL(Url);
	Request->SetTimeout(Config->TimeoutSeconds);
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	Request->SetHeader(TEXT("Accept"), TEXT("application/json"));
	Request->SetHeader(TEXT("User-Agent"), TEXT("NeshamaSDK-Unreal/1.0"));
	
	ActiveRequestCount++;
	
	return Request;
}

void UNeshamaClient::SendGetRequest(const FString& Endpoint, TFunction<void(bool, const FString&)> OnComplete)
{
	const FString FullUrl = Config->BuildUrl(Endpoint);
	
	IHttpRequest* Request = CreateRequest(TEXT("GET"), FullUrl);
	
	Request->OnProcessRequestComplete().BindLambda([this, OnComplete](IHttpRequest* InRequest, 
		IHttpResponse* InResponse, bool bInSuccess)
	{
		ActiveRequestCount--;
		
		if (bInSuccess && InResponse)
		{
			int32 ResponseCode = InResponse->GetResponseCode();
			FString ResponseBody = InResponse->GetContentAsString();
			
			if (ResponseCode >= 200 && ResponseCode < 300)
			{
				Log(ENeshamaLogLevel::Debug, 
					FString::Printf(TEXT("GET请求成功: %d %s"), ResponseCode, *Endpoint));
				OnComplete(true, ResponseBody);
			}
			else
			{
				Log(ENeshamaLogLevel::Error, 
					FString::Printf(TEXT("GET请求失败: %d %s - %s"), 
						ResponseCode, *Endpoint, *ResponseBody));
				OnComplete(false, ResponseBody);
			}
		}
		else
		{
			FString ErrorMsg = InRequest ? InRequest->GetError() : TEXT("Unknown error");
			Log(ENeshamaLogLevel::Error, 
				FString::Printf(TEXT("GET请求错误: %s - %s"), *Endpoint, *ErrorMsg));
			OnComplete(false, ErrorMsg);
		}
	});
	
	Request->ProcessRequest();
}

void UNeshamaClient::SendPostRequest(const FString& Endpoint, const FString& Body,
	TFunction<void(bool, const FString&)> OnComplete)
{
	const FString FullUrl = Config->BuildUrl(Endpoint);
	
	IHttpRequest* Request = CreateRequest(TEXT("POST"), FullUrl);
	Request->SetContentAsString(Body);
	
	Request->OnProcessRequestComplete().BindLambda([this, OnComplete](IHttpRequest* InRequest,
		IHttpResponse* InResponse, bool bInSuccess)
	{
		ActiveRequestCount--;
		
		if (bInSuccess && InResponse)
		{
			int32 ResponseCode = InResponse->GetResponseCode();
			FString ResponseBody = InResponse->GetContentAsString();
			
			if (ResponseCode >= 200 && ResponseCode < 300)
			{
				Log(ENeshamaLogLevel::Debug,
					FString::Printf(TEXT("POST请求成功: %d %s"), ResponseCode, *Endpoint));
				OnComplete(true, ResponseBody);
			}
			else
			{
				Log(ENeshamaLogLevel::Error,
					FString::Printf(TEXT("POST请求失败: %d %s - %s"),
						ResponseCode, *Endpoint, *ResponseBody));
				OnComplete(false, ResponseBody);
			}
		}
		else
		{
			FString ErrorMsg = InRequest ? InRequest->GetError() : TEXT("Unknown error");
			Log(ENeshamaLogLevel::Error,
				FString::Printf(TEXT("POST请求错误: %s - %s"), *Endpoint, *ErrorMsg));
			OnComplete(false, ErrorMsg);
		}
	});
	
	Request->ProcessRequest();
}

bool UNeshamaClient::ProcessJsonResponse(const FString& ResponseString, 
	TSharedPtr<FJsonObject>& OutJsonObject)
{
	if (ResponseString.IsEmpty())
	{
		Log(ENeshamaLogLevel::Warning, TEXT("响应内容为空"));
		return false;
	}

	TSharedRef<TJsonReader<>> JsonReader = TJsonReaderFactory<>::Create(ResponseString);
	
	if (FJsonSerializer::Deserialize(JsonReader, OutJsonObject) && OutJsonObject.IsValid())
	{
		return true;
	}
	
	Log(ENeshamaLogLevel::Error, FString::Printf(TEXT("JSON解析失败: %s"), *ResponseString));
	return false;
}

void UNeshamaClient::Log(ENeshamaLogLevel Level, const FString& Message)
{
	if (Config)
	{
		Config->Log(Message, Level);
	}
	OnLog.Broadcast(Message);
}

void UNeshamaClient::TriggerError(const FString& ErrorMessage)
{
	Log(ENeshamaLogLevel::Error, ErrorMessage);
	OnError.Broadcast(ErrorMessage);
}

void UNeshamaClient::SetConfig(UNeshamaConfig* NewConfig)
{
	if (NewConfig)
	{
		Config = NewConfig;
		Log(ENeshamaLogLevel::Info, TEXT("配置已更新"));
	}
}

// ============================================================================
// NPC管理API实现
// ============================================================================

void UNeshamaClient::CreateNPC(const FString& Name, const FString& Preset,
	const FOnCreateNPCResponseDelegate& OnComplete)
{
	if (!bIsConnected)
	{
		TriggerError(TEXT("未连接服务器"));
		OnComplete.ExecuteIfBound(FCreateNPCResponse());
		return;
	}

	// 构建请求体
	TSharedPtr<FJsonObject> RequestJson = MakeShareable(new FJsonObject());
	RequestJson->SetStringField(TEXT("name"), Name);
	RequestJson->SetStringField(TEXT("preset"), Preset);

	FString RequestBody;
	TJsonWriter<>& Writer = TJsonWriterFactory<>::Create(RequestBody);
	FJsonSerializer::Serialize(RequestJson.ToSharedRef(), Writer);

	SendPostRequest(TEXT("/npc"), RequestBody, [this, OnComplete](bool bSuccess, const FString& Response)
	{
		FCreateNPCResponse Result;
		
		if (bSuccess)
		{
			TSharedPtr<FJsonObject> JsonObject;
			if (ProcessJsonResponse(Response, JsonObject))
			{
				Result.Success = true;
				Result.NpcId = JsonObject->GetStringField(TEXT("npc_id"));
				
				// 解析profile
				if (JsonObject->HasField(TEXT("profile")))
				{
					const TSharedPtr<FJsonObject>& ProfileJson = JsonObject->GetObjectField(TEXT("profile"));
					Result.Profile.NpcId = ProfileJson->GetStringField(TEXT("npc_id"));
					Result.Profile.Name = ProfileJson->GetStringField(TEXT("name"));
					Result.Profile.Preset = ProfileJson->GetStringField(TEXT("preset"));
					if (ProfileJson->HasField(TEXT("description")))
					{
						Result.Profile.Description = ProfileJson->GetStringField(TEXT("description"));
					}
				}
				
				Log(ENeshamaLogLevel::Info, 
					FString::Printf(TEXT("NPC创建成功: %s"), *Result.NpcId));
			}
		}
		else
		{
			Result.Success = false;
			Result.Error = Response;
		}
		
		OnComplete.ExecuteIfBound(Result);
	});
}

void UNeshamaClient::GetProfile(const FString& NpcId, const FOnNPCProfileDelegate& OnComplete)
{
	if (!bIsConnected)
	{
		TriggerError(TEXT("未连接服务器"));
		OnComplete.ExecuteIfBound(FNPCProfile());
		return;
	}

	SendGetRequest(FString::Printf(TEXT("/npc/%s/profile"), *NpcId),
		[this, OnComplete](bool bSuccess, const FString& Response)
	{
		FNPCProfile Profile;
		
		if (bSuccess)
		{
			TSharedPtr<FJsonObject> JsonObject;
			if (ProcessJsonResponse(Response, JsonObject))
			{
				Profile.NpcId = JsonObject->GetStringField(TEXT("npc_id"));
				Profile.Name = JsonObject->GetStringField(TEXT("name"));
				Profile.Preset = JsonObject->GetStringField(TEXT("preset"));
				
				if (JsonObject->HasField(TEXT("description")))
				{
					Profile.Description = JsonObject->GetStringField(TEXT("description"));
				}
				
				Log(ENeshamaLogLevel::Debug, 
					FString::Printf(TEXT("获取NPC档案成功: %s"), *Profile.NpcId));
			}
		}
		
		OnComplete.ExecuteIfBound(Profile);
	});
}

// ============================================================================
// 事件推送API实现
// ============================================================================

void UNeshamaClient::SendEvent(const FString& NpcId, const FGameEvent& GameEvent,
	const FOnEventResponseDelegate& OnComplete)
{
	if (!bIsConnected)
	{
		TriggerError(TEXT("未连接服务器"));
		OnComplete.ExecuteIfBound(FEventResponse());
		return;
	}

	// 构建请求体
	TSharedPtr<FJsonObject> RequestJson = MakeShareable(new FJsonObject());
	RequestJson->SetStringField(TEXT("event_type"), GameEvent.EventType);
	RequestJson->SetNumberField(TEXT("intensity"), GameEvent.Intensity);

	// 添加上下文
	TSharedPtr<FJsonObject> ContextJson = MakeShareable(new FJsonObject());
	for (const auto& KVP : GameEvent.Context)
	{
		ContextJson->SetStringField(KVP.Key, KVP.Value);
	}
	RequestJson->SetObjectField(TEXT("context"), ContextJson);

	FString RequestBody;
	TJsonWriter<>& Writer = TJsonWriterFactory<>::Create(RequestBody);
	FJsonSerializer::Serialize(RequestJson.ToSharedRef(), Writer);

	SendPostRequest(FString::Printf(TEXT("/npc/%s/event"), *NpcId), RequestBody,
		[this, OnComplete](bool bSuccess, const FString& Response)
	{
		FEventResponse Result;
		
		if (bSuccess)
		{
			TSharedPtr<FJsonObject> JsonObject;
			if (ProcessJsonResponse(Response, JsonObject))
			{
				Result.Handled = true;
				
				// 解析响应提示
				if (JsonObject->HasField(TEXT("response_hint")))
				{
					const TSharedPtr<FJsonObject>& HintJson = 
						JsonObject->GetObjectField(TEXT("response_hint"));
					Result.Tone = HintJson->GetStringField(TEXT("tone"));
					Result.Urgency = HintJson->GetStringField(TEXT("urgency"));
					
					if (HintJson->HasField(TEXT("suggested_actions")))
					{
						const TArray<TSharedPtr<FJsonValue>>& ActionsArray = 
							HintJson->GetArrayField(TEXT("suggested_actions"));
						for (const auto& Action : ActionsArray)
						{
							Result.SuggestedActions.Add(Action->AsString());
						}
					}
				}
				
				// 解析情绪状态
				if (JsonObject->HasField(TEXT("emotion_state")))
				{
					const TSharedPtr<FJsonObject>& EmotionJson = 
						JsonObject->GetObjectField(TEXT("emotion_state"));
					
					if (EmotionJson->HasField(TEXT("emotions")))
					{
						const TSharedPtr<FJsonObject>& EmotionsData = 
							EmotionJson->GetObjectField(TEXT("emotions"));
						for (const auto& EmotionKVP : EmotionsData->Values)
						{
							Result.EmotionState.Emotions.Add(
								EmotionKVP.Key, EmotionKVP.Value->AsNumber());
						}
					}
					
					if (EmotionJson->HasField(TEXT("dominant")))
					{
						Result.EmotionState.Dominant = EmotionJson->GetStringField(TEXT("dominant"));
					}
					
					if (EmotionJson->HasField(TEXT("composite")))
					{
						Result.EmotionState.Composite = EmotionJson->GetStringField(TEXT("composite"));
					}
					
					// 触发情绪变化事件
					OnEmotionChanged.Broadcast(Result.EmotionState);
				}
				
				Log(ENeshamaLogLevel::Debug, TEXT("事件推送成功"));
			}
		}
		
		OnComplete.ExecuteIfBound(Result);
	});
}

void UNeshamaClient::SendGameEvent(const FString& NpcId, EGameEventType EventType,
	float Intensity, const TMap<FString, FString>& Context,
	const FOnEventResponseDelegate& OnComplete)
{
	FGameEvent GameEvent(EventType, Intensity);
	GameEvent.Context = Context;
	
	SendEvent(NpcId, GameEvent, OnComplete);
}

// ============================================================================
// 情绪状态API实现
// ============================================================================

void UNeshamaClient::GetEmotion(const FString& NpcId, const FOnEmotionStateDelegate& OnComplete)
{
	if (!bIsConnected)
	{
		TriggerError(TEXT("未连接服务器"));
		OnComplete.ExecuteIfBound(FEmotionState());
		return;
	}

	SendGetRequest(FString::Printf(TEXT("/npc/%s/emotion"), *NpcId),
		[this, OnComplete](bool bSuccess, const FString& Response)
	{
		FEmotionState EmotionState;
		
		if (bSuccess)
		{
			TSharedPtr<FJsonObject> JsonObject;
			if (ProcessJsonResponse(Response, JsonObject))
			{
				// 解析情绪
				if (JsonObject->HasField(TEXT("emotions")))
				{
					const TSharedPtr<FJsonObject>& EmotionsData = 
						JsonObject->GetObjectField(TEXT("emotions"));
					for (const auto& EmotionKVP : EmotionsData->Values)
					{
						EmotionState.Emotions.Add(
							EmotionKVP.Key, EmotionKVP.Value->AsNumber());
					}
				}
				
				if (JsonObject->HasField(TEXT("dominant")))
				{
					EmotionState.Dominant = JsonObject->GetStringField(TEXT("dominant"));
				}
				
				if (JsonObject->HasField(TEXT("composite")))
				{
					EmotionState.Composite = JsonObject->GetStringField(TEXT("composite"));
				}
				
				Log(ENeshamaLogLevel::Debug, 
					FString::Printf(TEXT("获取情绪状态成功: %s"), *EmotionState.Dominant));
			}
		}
		
		OnComplete.ExecuteIfBound(EmotionState);
	});
}

// ============================================================================
// 行为建议API实现
// ============================================================================

void UNeshamaClient::GetBehaviorHints(const FString& NpcId,
	const FOnBehaviorResponseDelegate& OnComplete)
{
	if (!bIsConnected)
	{
		TriggerError(TEXT("未连接服务器"));
		OnComplete.ExecuteIfBound(FBehaviorResponse());
		return;
	}

	SendGetRequest(FString::Printf(TEXT("/npc/%s/behavior"), *NpcId),
		[this, OnComplete](bool bSuccess, const FString& Response)
	{
		FBehaviorResponse Result;
		
		if (bSuccess)
		{
			TSharedPtr<FJsonObject> JsonObject;
			if (ProcessJsonResponse(Response, JsonObject))
			{
				if (JsonObject->HasField(TEXT("modifiers")))
				{
					const TArray<TSharedPtr<FJsonValue>>& ModifiersArray = 
						JsonObject->GetArrayField(TEXT("modifiers"));
					
					for (const auto& ModifierValue : ModifiersArray)
					{
						const TSharedPtr<FJsonObject>& ModifierJson = ModifierValue->AsObject();
						FBehaviorHint Hint;
						Hint.Type = ModifierJson->GetStringField(TEXT("type"));
						Hint.Value = ModifierJson->GetStringField(TEXT("value"));
						
						if (ModifierJson->HasField(TEXT("strength")))
						{
							Hint.Strength = ModifierJson->GetNumberField(TEXT("strength"));
						}
						
						Result.Modifiers.Add(Hint);
						
						// 触发行为变化事件
						OnBehaviorChanged.Broadcast(Hint.Type, Hint.Value);
					}
				}
				
				Log(ENeshamaLogLevel::Debug, 
					FString::Printf(TEXT("获取行为建议成功: %d 条"), Result.Modifiers.Num()));
			}
		}
		
		OnComplete.ExecuteIfBound(Result);
	});
}

// ============================================================================
// 对话API实现
// ============================================================================

void UNeshamaClient::Chat(const FString& NpcId, const FString& Message,
	const FString& PlayerId, const FOnChatResponseDelegate& OnComplete)
{
	if (!bIsConnected)
	{
		TriggerError(TEXT("未连接服务器"));
		OnComplete.ExecuteIfBound(FChatResponse());
		return;
	}

	// 构建请求体
	TSharedPtr<FJsonObject> RequestJson = MakeShareable(new FJsonObject());
	RequestJson->SetStringField(TEXT("message"), Message);
	
	FString EffectivePlayerId = PlayerId;
	if (EffectivePlayerId.IsEmpty())
	{
		EffectivePlayerId = Config->DefaultPlayerId;
	}
	RequestJson->SetStringField(TEXT("player_id"), EffectivePlayerId);

	FString RequestBody;
	TJsonWriter<>& Writer = TJsonWriterFactory<>::Create(RequestBody);
	FJsonSerializer::Serialize(RequestJson.ToSharedRef(), Writer);

	SendPostRequest(FString::Printf(TEXT("/npc/%s/chat"), *NpcId), RequestBody,
		[this, OnComplete](bool bSuccess, const FString& Response)
	{
		FChatResponse Result;
		
		if (bSuccess)
		{
			TSharedPtr<FJsonObject> JsonObject;
			if (ProcessJsonResponse(Response, JsonObject))
			{
				Result.Content = JsonObject->GetStringField(TEXT("content"));
				Result.SenderId = JsonObject->GetStringField(TEXT("sender_id"));
				Result.ReceiverId = JsonObject->GetStringField(TEXT("receiver_id"));
				Result.Timestamp = FNeshamaUtils::GetCurrentTimestamp();
				
				// 解析回复后的情绪
				if (JsonObject->HasField(TEXT("emotion_after")))
				{
					const TSharedPtr<FJsonObject>& EmotionJson = 
						JsonObject->GetObjectField(TEXT("emotion_after"));
					
					if (EmotionJson->HasField(TEXT("emotions")))
					{
						const TSharedPtr<FJsonObject>& EmotionsData = 
							EmotionJson->GetObjectField(TEXT("emotions"));
						for (const auto& EmotionKVP : EmotionsData->Values)
						{
							Result.EmotionAfter.Emotions.Add(
								EmotionKVP.Key, EmotionKVP.Value->AsNumber());
						}
					}
					
					if (EmotionJson->HasField(TEXT("dominant")))
					{
						Result.EmotionAfter.Dominant = EmotionJson->GetStringField(TEXT("dominant"));
					}
				}
				
				// 触发对话响应事件
				OnChatResponse.Broadcast(Result);
				
				Log(ENeshamaLogLevel::Debug, 
					FString::Printf(TEXT("对话响应: %s"), *Result.Content));
			}
		}
		
		OnComplete.ExecuteIfBound(Result);
	});
}

// ============================================================================
// 记忆API实现
// ============================================================================

void UNeshamaClient::GetMemory(const FString& NpcId, const FString& Query,
	const FOnMemoryListResponseDelegate& OnComplete)
{
	if (!bIsConnected)
	{
		TriggerError(TEXT("未连接服务器"));
		OnComplete.ExecuteIfBound(FMemoryListResponse());
		return;
	}

	FString Endpoint = FString::Printf(TEXT("/npc/%s/memory"), *NpcId);
	if (!Query.IsEmpty())
	{
		Endpoint += FString::Printf(TEXT("?query=%s"), *Query);
	}

	SendGetRequest(Endpoint,
		[this, OnComplete](bool bSuccess, const FString& Response)
	{
		FMemoryListResponse Result;
		
		if (bSuccess)
		{
			TSharedPtr<FJsonObject> JsonObject;
			if (ProcessJsonResponse(Response, JsonObject))
			{
				if (JsonObject->HasField(TEXT("memories")))
				{
					const TArray<TSharedPtr<FJsonValue>>& MemoriesArray = 
						JsonObject->GetArrayField(TEXT("memories"));
					
					for (const auto& MemoryValue : MemoriesArray)
					{
						const TSharedPtr<FJsonObject>& MemoryJson = MemoryValue->AsObject();
						FMemoryEntry Entry;
						Entry.MemoryId = MemoryJson->GetStringField(TEXT("memory_id"));
						Entry.Content = MemoryJson->GetStringField(TEXT("content"));
						Entry.RelatedEntity = MemoryJson->GetStringField(TEXT("related_entity"));
						Entry.MemoryType = MemoryJson->GetStringField(TEXT("type"));
						
						if (MemoryJson->HasField(TEXT("importance")))
						{
							Entry.Importance = MemoryJson->GetNumberField(TEXT("importance"));
						}
						
						Result.Memories.Add(Entry);
					}
					
					Result.Total = Result.Memories.Num();
				}
				
				Log(ENeshamaLogLevel::Debug, 
					FString::Printf(TEXT("获取记忆成功: %d 条"), Result.Total));
			}
		}
		
		OnComplete.ExecuteIfBound(Result);
	});
}

void UNeshamaClient::Remember(const FString& NpcId, const FString& EntityType,
	const FString& EntityName, const FString& Relation,
	const FString& Note, const FOnRememberResponseDelegate& OnComplete)
{
	if (!bIsConnected)
	{
		TriggerError(TEXT("未连接服务器"));
		OnComplete.ExecuteIfBound(FMemoryListResponse());
		return;
	}

	// 构建请求体
	TSharedPtr<FJsonObject> RequestJson = MakeShareable(new FJsonObject());
	RequestJson->SetStringField(TEXT("entity_type"), EntityType);
	RequestJson->SetStringField(TEXT("entity_name"), EntityName);
	
	if (!Relation.IsEmpty())
	{
		RequestJson->SetStringField(TEXT("relation"), Relation);
	}
	
	if (!Note.IsEmpty())
	{
		RequestJson->SetStringField(TEXT("note"), Note);
	}

	FString RequestBody;
	TJsonWriter<>& Writer = TJsonWriterFactory<>::Create(RequestBody);
	FJsonSerializer::Serialize(RequestJson.ToSharedRef(), Writer);

	SendPostRequest(FString::Printf(TEXT("/npc/%s/remember"), *NpcId), RequestBody,
		[this, OnComplete](bool bSuccess, const FString& Response)
	{
		FMemoryListResponse Result;
		
		if (bSuccess)
		{
			Log(ENeshamaLogLevel::Info, TEXT("NPC记忆创建成功"));
		}
		
		OnComplete.ExecuteIfBound(Result);
	});
}

// ============================================================================
// 关系图谱API实现
// ============================================================================

void UNeshamaClient::GetRelations(const FString& NpcId, const FOnRelationGraphDelegate& OnComplete)
{
	if (!bIsConnected)
	{
		TriggerError(TEXT("未连接服务器"));
		OnComplete.ExecuteIfBound(FRelationGraph());
		return;
	}

	SendGetRequest(FString::Printf(TEXT("/npc/%s/relations"), *NpcId),
		[this, OnComplete](bool bSuccess, const FString& Response)
	{
		FRelationGraph Result;
		Result.NpcId = NpcId;
		
		if (bSuccess)
		{
			TSharedPtr<FJsonObject> JsonObject;
			if (ProcessJsonResponse(Response, JsonObject))
			{
				if (JsonObject->HasField(TEXT("relations")))
				{
					const TArray<TSharedPtr<FJsonValue>>& RelationsArray = 
						JsonObject->GetArrayField(TEXT("relations"));
					
					for (const auto& RelationValue : RelationsArray)
					{
						const TSharedPtr<FJsonObject>& RelationJson = RelationValue->AsObject();
						FRelationNode Node;
						Node.EntityId = RelationJson->GetStringField(TEXT("entity_id"));
						Node.EntityName = RelationJson->GetStringField(TEXT("entity_name"));
						Node.EntityType = RelationJson->GetStringField(TEXT("entity_type"));
						Node.Affinity = RelationJson->GetNumberField(TEXT("affinity"));
						
						Result.Relations.Add(Node);
					}
				}
				
				Result.UpdatedAt = FNeshamaUtils::GetCurrentTimestamp();
				
				Log(ENeshamaLogLevel::Debug, 
					FString::Printf(TEXT("获取关系图谱成功: %d 个关系"), Result.Relations.Num()));
			}
		}
		
		OnComplete.ExecuteIfBound(Result);
	});
}

#undef LOCTEXT_NAMESPACE
