// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - 配置实现文件

#include "NeshamaConfig.h"
#include "GenericPlatform/GenericPlatform.h"

#define LOCTEXT_NAMESPACE "NeshamaConfig"

// ============================================================================
// UNeshamaConfig 实现
// ============================================================================

UNeshamaConfig::UNeshamaConfig(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, ServerMode(ENeshamaServerMode::Cloud)
	, ApiKey(TEXT(""))
	, bTrialMode(false)
	, TrialToken(TEXT(""))
	, ServerUrl(TEXT("https://api.neshama.pw"))
	, BasePath(TEXT("/api"))
	, Port(8420)
	, TimeoutSeconds(30)
	, bAutoReconnect(true)
	, MaxReconnectAttempts(3)
	, ReconnectIntervalSeconds(5.0f)
	, LogLevel(ENeshamaLogLevel::Info)
	, bDisplayOnScreen(false)
	, ScreenLogDuration(5.0f)
	, DefaultPlayerId(TEXT("player_001"))
	, DefaultPlayerName(TEXT("Player"))
	, bDebugMode(false)
	, bAutoHeartbeat(true)
	, HeartbeatIntervalSeconds(30.0f)
{
}

FString UNeshamaConfig::BuildUrl(const FString& Endpoint) const
{
	// 构建URL格式: https://api.neshama.pw/api/endpoint (Cloud)
	//              http://localhost:8420/api/endpoint (Local)
	FString Url = ServerUrl;
	
	// 确保URL不以斜杠结尾
	Url.RemoveFromEnd(TEXT("/"));
	
	// 本地模式下添加端口
	if (ServerMode == ENeshamaServerMode::Local && !ServerUrl.Contains(TEXT(":")) && Port != 80)
	{
		Url.Appendf(TEXT(":%d"), Port);
	}
	
	// 添加基础路径
	Url.Append(BasePath);
	
	// 添加端点（确保端点以斜杠开头）
	FString CleanEndpoint = Endpoint;
	if (!CleanEndpoint.StartsWith(TEXT("/")))
	{
		Url.AppendChar(TEXT('/'));
	}
	Url.Append(CleanEndpoint);
	
	return Url;
}

bool UNeshamaConfig::IsValid() const
{
	// 检查服务器地址是否有效
	if (ServerUrl.IsEmpty())
	{
		return false;
	}
	
	// 本地模式下检查端口范围
	if (ServerMode == ENeshamaServerMode::Local && (Port <= 0 || Port > 65535))
	{
		return false;
	}

	// 检查超时设置
	if (TimeoutSeconds < 1)
	{
		return false;
	}
	
	return true;
}

FString UNeshamaConfig::GetAuthHeader() const
{
	if (bTrialMode && !TrialToken.IsEmpty())
	{
		return FString::Printf(TEXT("Bearer %s"), *TrialToken);
	}
	if (!ApiKey.IsEmpty())
	{
		return FString::Printf(TEXT("Bearer %s"), *ApiKey);
	}
	return TEXT("");
}

bool UNeshamaConfig::HasAuth() const
{
	return !ApiKey.IsEmpty() || (bTrialMode && !TrialToken.IsEmpty());
}

void UNeshamaConfig::Log(const FString& Message, ENeshamaLogLevel Level)
{
	if (!ShouldLog(Level))
	{
		return;
	}
	
	const FString FullMessage = GetLogPrefix() + TEXT(" ") + Message;
	
	// 根据日志级别输出到不同通道
	switch (Level)
	{
	case ENeshamaLogLevel::Error:
		UE_LOG(LogTemp, Error, TEXT("%s"), *FullMessage);
		if (bDisplayOnScreen)
		{
			GEngine->AddOnScreenDebugMessage(-1, ScreenLogDuration, FColor::Red, FullMessage);
		}
		break;
		
	case ENeshamaLogLevel::Warning:
		UE_LOG(LogTemp, Warning, TEXT("%s"), *FullMessage);
		if (bDisplayOnScreen)
		{
			GEngine->AddOnScreenDebugMessage(-1, ScreenLogDuration, FColor::Yellow, FullMessage);
		}
		break;
		
	case ENeshamaLogLevel::Info:
		UE_LOG(LogTemp, Display, TEXT("%s"), *FullMessage);
		if (bDisplayOnScreen)
		{
			GEngine->AddOnScreenDebugMessage(-1, ScreenLogDuration, FColor::Cyan, FullMessage);
		}
		break;
		
	case ENeshamaLogLevel::Debug:
		UE_LOG(LogTemp, Verbose, TEXT("%s"), *FullMessage);
		if (bDisplayOnScreen)
		{
			GEngine->AddOnScreenDebugMessage(-1, ScreenLogDuration, FColor::White, FullMessage);
		}
		break;
		
	case ENeshamaLogLevel::Verbose:
		UE_LOG(LogTemp, VeryVerbose, TEXT("%s"), *FullMessage);
		break;
		
	default:
		UE_LOG(LogTemp, Log, TEXT("%s"), *FullMessage);
		break;
	}
}

UNeshamaConfig* UNeshamaConfig::CreateDefault()
{
	return CreateDefaultInternal();
}

UNeshamaConfig* UNeshamaConfig::Get()
{
	// 从Project Settings获取配置
	// 注意：这里需要确保配置已保存在DefaultGame.ini中
	return CreateDefaultInternal();
}

FString UNeshamaConfig::GetLogLevelName(ENeshamaLogLevel Level)
{
	switch (Level)
	{
	case ENeshamaLogLevel::None: return TEXT("NONE");
	case ENeshamaLogLevel::Error: return TEXT("ERROR");
	case ENeshamaLogLevel::Warning: return TEXT("WARNING");
	case ENeshamaLogLevel::Info: return TEXT("INFO");
	case ENeshamaLogLevel::Debug: return TEXT("DEBUG");
	case ENeshamaLogLevel::Verbose: return TEXT("VERBOSE");
	default: return TEXT("UNKNOWN");
	}
}

bool UNeshamaConfig::ShouldLog(ENeshamaLogLevel Level) const
{
	// 如果日志级别为None，不输出任何日志
	if (LogLevel == ENeshamaLogLevel::None)
	{
		return false;
	}
	
	// 比较日志级别
	return static_cast<uint8>(Level) <= static_cast<uint8>(LogLevel);
}

UNeshamaConfig* UNeshamaConfig::CreateDefaultInternal()
{
	// 创建一个新的配置实例，使用默认值
	UNeshamaConfig* Config = NewObject<UNeshamaConfig>();
	return Config;
}

// ============================================================================
// 工具函数实现
// ============================================================================

namespace FNeshamaUtils
{
	FString EscapeJsonString(const FString& Input)
	{
		FString Output;
		Output.Reserve(Input.Len());
		
		for (const TCHAR& Char : Input)
		{
			switch (Char)
			{
			case TEXT('\\'): Output += TEXT("\\\\"); break;
			case TEXT('"'): Output += TEXT("\\\""); break;
			case TEXT('\n'): Output += TEXT("\\n"); break;
			case TEXT('\r'): Output += TEXT("\\r"); break;
			case TEXT('\t'): Output += TEXT("\\t"); break;
			case TEXT('\b'): Output += TEXT("\\b"); break;
			case TEXT('\f'): Output += TEXT("\\f"); break;
			default: Output += Char; break;
			}
		}
		
		return Output;
	}

	FString ArrayToJsonString(const TArray<FString>& Array)
	{
		if (Array.Num() == 0)
		{
			return TEXT("[]");
		}
		
		FString Output = TEXT("[");
		for (int32 i = 0; i < Array.Num(); ++i)
		{
			if (i > 0)
			{
				Output += TEXT(", ");
			}
			Output += TEXT("\"") + EscapeJsonString(Array[i]) + TEXT("\"");
		}
		Output += TEXT("]");
		
		return Output;
	}

	FString MapToJsonString(const TMap<FString, FString>& Map)
	{
		if (Map.Num() == 0)
		{
			return TEXT("{}");
		}
		
		FString Output = TEXT("{");
		bool bFirst = true;
		for (const auto& KVP : Map)
		{
			if (!bFirst)
			{
				Output += TEXT(", ");
			}
			bFirst = false;
			Output += TEXT("\"") + EscapeJsonString(KVP.Key) + TEXT("\": \"") + 
					  EscapeJsonString(KVP.Value) + TEXT("\"");
		}
		Output += TEXT("}");
		
		return Output;
	}

	FString FloatMapToJsonString(const TMap<FString, float>& Map)
	{
		if (Map.Num() == 0)
		{
			return TEXT("{}");
		}
		
		FString Output = TEXT("{");
		bool bFirst = true;
		for (const auto& KVP : Map)
		{
			if (!bFirst)
			{
				Output += TEXT(", ");
			}
			bFirst = false;
			Output += TEXT("\"") + EscapeJsonString(KVP.Key) + TEXT("\": ") + 
					  FString::SanitizeFloat(KVP.Value);
		}
		Output += TEXT("}");
		
		return Output;
	}

	FString GenerateUUID()
	{
		// 使用UE的FGuid生成UUID
		FGuid Guid = FGuid::NewGuid();
		return Guid.ToString(EGuidFormats::DigitsWithHyphens);
	}

	int64 GetCurrentTimestamp()
	{
		return FDateTime::Now().ToUnixTimestamp();
	}
}

#undef LOCTEXT_NAMESPACE
