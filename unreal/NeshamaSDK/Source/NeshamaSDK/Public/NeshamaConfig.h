// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - 配置头文件
// 提供SDK配置管理、日志和工具函数

#pragma once

#include "CoreMinimal.h"
#include "NeshamaTypes.h"
#include "NeshamaConfig.generated.h"

/**
 * 日志级别枚举
 */
UENUM(BlueprintType)
enum class ENeshamaLogLevel : uint8
{
	/** 不输出日志 */
	None		UMETA(DisplayName = "None"),
	
	/** 错误日志 */
	Error		UMETA(DisplayName = "Error"),
	
	/** 警告日志 */
	Warning		UMETA(DisplayName = "Warning"),
	
	/** 信息日志 */
	Info		UMETA(DisplayName = "Info"),
	
	/** 调试日志 */
	Debug		UMETA(DisplayName = "Debug"),
	
	/** 详细日志 */
	Verbose		UMETA(DisplayName = "Verbose")
};

/**
 * 服务器模式枚举
 */
UENUM(BlueprintType)
enum class ENeshamaServerMode : uint8
{
	/** 云端托管模式（默认，免部署） */
	Cloud		UMETA(DisplayName = "Cloud", ToolTip = "云端托管模式，无需自己部署"),
	
	/** 本地部署模式（需要自己启动后端） */
	Local		UMETA(DisplayName = "Local", ToolTip = "本地部署模式，需要运行后端服务")
};

/**
 * Neshama SDK 配置类
 * 管理SDK的连接参数、日志设置和默认行为
 * 支持通过 Project Settings 进行配置
 * 默认使用云端模式，免部署即可使用
 */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Neshama SDK"))
class NESHAMASDK_API UNeshamaConfig : public UObject
{
	GENERATED_BODY()

public:
	// ============================================================================
	// 构造函数
	// ============================================================================

	/** 默认构造函数 */
	UNeshamaConfig(const FObjectInitializer& ObjectInitializer = FObjectInitializer::Get());

	// ============================================================================
	// 服务器模式配置
	// ============================================================================

	/** 服务器模式：Cloud（云端托管）或 Local（本地部署） */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Server Mode", ToolTip = "云端模式免部署，本地模式需运行后端"))
	ENeshamaServerMode ServerMode;

	/** API Key（从注册或试用获得） */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "API Key", ToolTip = "从Neshama注册页面获取的API Key"))
	FString ApiKey;

	/** 是否启用试用模式（无需API Key） */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Trial Mode", ToolTip = "试用模式，自动获取临时Token"))
	bool bTrialMode;

	/** 试用Token（自动获取，无需手动填写） */
	UPROPERTY(Config, VisibleAnywhere, BlueprintReadOnly, Category = "Neshama|Connection",
		meta = (DisplayName = "Trial Token"))
	FString TrialToken;

	// ============================================================================
	// 连接配置
	// ============================================================================

	/** 服务器地址 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Server URL", ToolTip = "Neshama服务器地址"))
	FString ServerUrl;

	/** API基础路径 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Base Path", ToolTip = "API基础路径"))
	FString BasePath;

	/** 服务器端口 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Port", ToolTip = "服务器端口"))
	int32 Port;

	/** 连接超时时间（秒） */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Timeout (s)", ClampMin = "1", ClampMax = "120"))
	int32 TimeoutSeconds;

	/** 是否自动重连 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Auto Reconnect"))
	bool bAutoReconnect;

	/** 最大重连次数 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Max Reconnect Attempts", ClampMin = "0", ClampMax = "10"))
	int32 MaxReconnectAttempts;

	/** 重连间隔时间（秒） */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Connection",
		meta = (DisplayName = "Reconnect Interval (s)", ClampMin = "1", ClampMax = "60"))
	float ReconnectIntervalSeconds;

	// ============================================================================
	// 日志配置
	// ============================================================================

	/** 日志级别 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Logging",
		meta = (DisplayName = "Log Level"))
	ENeshamaLogLevel LogLevel;

	/** 是否在屏幕上显示日志 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Logging",
		meta = (DisplayName = "Display on Screen"))
	bool bDisplayOnScreen;

	/** 日志保留时间（秒） */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Logging",
		meta = (DisplayName = "Screen Log Duration (s)", ClampMin = "1", ClampMax = "30"))
	float ScreenLogDuration;

	// ============================================================================
	// 默认玩家配置
	// ============================================================================

	/** 默认玩家ID */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Player",
		meta = (DisplayName = "Default Player ID"))
	FString DefaultPlayerId;

	/** 默认玩家名称 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Player",
		meta = (DisplayName = "Default Player Name"))
	FString DefaultPlayerName;

	// ============================================================================
	// 功能开关
	// ============================================================================

	/** 是否启用调试模式 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Feature",
		meta = (DisplayName = "Debug Mode"))
	bool bDebugMode;

	/** 是否启用自动心跳 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Feature",
		meta = (DisplayName = "Auto Heartbeat"))
	bool bAutoHeartbeat;

	/** 心跳间隔（秒） */
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category = "Neshama|Feature",
		meta = (DisplayName = "Heartbeat Interval (s)", ClampMin = "10", ClampMax = "300"))
	float HeartbeatIntervalSeconds;

	// ============================================================================
	// 公共方法
	// ============================================================================

	/**
	 * 构建完整的API URL
	 * @param Endpoint API端点路径（不含基础路径）
	 * @return 完整的URL
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Config")
	FString BuildUrl(const FString& Endpoint) const;

	/**
	 * 获取认证头（Bearer Token）
	 * 试用模式返回试用Token，否则返回API Key
	 * @return 认证头字符串
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Config")
	FString GetAuthHeader() const;

	/**
	 * 是否已配置认证信息
	 * @return 是否有可用的认证
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Config")
	bool HasAuth() const;

	/**
	 * 检查配置是否有效
	 * @return 是否有效
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Config")
	bool IsValid() const;

	/**
	 * 记录日志
	 * @param Message 日志消息
	 * @param Level 日志级别
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama|Logging")
	void Log(const FString& Message, ENeshamaLogLevel Level = ENeshamaLogLevel::Info);

	/**
	 * 创建默认配置
	 * @return 默认配置实例
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Config")
	static UNeshamaConfig* CreateDefault();

	/**
	 * 获取当前配置实例（从Project Settings）
	 * @return 配置实例
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Config")
	static UNeshamaConfig* Get();

	/**
	 * 获取日志级别的显示名称
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama|Logging")
	static FString GetLogLevelName(ENeshamaLogLevel Level);

protected:
	/** 获取日志前缀 */
	virtual FString GetLogPrefix() const { return TEXT("[Neshama]"); }

	/** 是否应该输出该级别的日志 */
	bool ShouldLog(ENeshamaLogLevel Level) const;

private:
	/** 创建默认配置（内部） */
	static UNeshamaConfig* CreateDefaultInternal();
};

// ============================================================================
// 工具函数
// ============================================================================

namespace FNeshamaUtils
{
	/**
	 * 将FString转换为JSON格式的字符串（转义特殊字符）
	 */
	NESHAMASDK_API FString EscapeJsonString(const FString& Input);

	/**
	 * 将FString列表转换为JSON数组字符串
	 */
	NESHAMASDK_API FString ArrayToJsonString(const TArray<FString>& Array);

	/**
	 * 将FStringMap转换为JSON对象字符串
	 */
	NESHAMASDK_API FString MapToJsonString(const TMap<FString, FString>& Map);

	/**
	 * 将float Map转换为JSON对象字符串
	 */
	NESHAMASDK_API FString FloatMapToJsonString(const TMap<FString, float>& Map);

	/**
	 * 生成UUID
	 */
	NESHAMASDK_API FString GenerateUUID();

	/**
	 * 获取当前时间戳（Unix格式）
	 */
	NESHAMASDK_API int64 GetCurrentTimestamp();

	/**
	 * 判断字符串是否为空或仅包含空白字符
	 */
	inline bool IsNullOrWhitespace(const FString& Str)
	{
		return Str.TrimStartAndEnd().IsEmpty();
	}
}
