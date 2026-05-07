// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - 模块入口实现文件

#include "NeshamaSDKModule.h"
#include "NeshamaConfig.h"
#include "NeshamaClient.h"
#include "NPCSoulComponent.h"
#include "HAL/PlatformProcess.h"
#include "Misc/ConfigCacheIni.h"

#define LOCTEXT_NAMESPACE "FNeshamaSDKModule"

IMPLEMENT_MODULE(FNeshamaSDKModule, NeshamaSDK)

// ============================================================================
// FNeshamaSDKModule 实现
// ============================================================================

void FNeshamaSDKModule::StartupModule()
{
	UE_LOG(LogTemp, Display, TEXT("[NeshamaSDK] Module starting..."));

	// 初始化日志系统
	InitializeLogging();

	// 注册配置
	RegisterSettings();

	UE_LOG(LogTemp, Display, TEXT("[NeshamaSDK] Module started successfully"));
}

void FNeshamaSDKModule::ShutdownModule()
{
	UE_LOG(LogTemp, Display, TEXT("[NeshamaSDK] Module shutting down..."));

	// 注销配置
	UnregisterSettings();

	UE_LOG(LogTemp, Display, TEXT("[NeshamaSDK] Module shut down successfully"));
}

void FNeshamaSDKModule::InitializeLogging()
{
	// 创建日志目录（如果不存在）
	FString LogDirectory = FPaths::ProjectLogDir();
	
	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDK] Log directory: %s"), *LogDirectory);
}

void FNeshamaSDKModule::RegisterSettings()
{
	// 注册Project Settings配置页面
	// 注意：实际的Settings注册需要在Editor模块中完成
	
	// 设置默认值到DefaultEngine.ini
	GConfig->SetString(
		TEXT("/Script/NeshamaSDK.NeshamaConfig"),
		TEXT("ServerUrl"),
		TEXT("https://api.neshama.ai"),
		GEngineIni
	);
	
	GConfig->SetString(
		TEXT("/Script/NeshamaSDK.NeshamaConfig"),
		TEXT("ServerMode"),
		TEXT("Cloud"),
		GEngineIni
	);
	
	GConfig->SetString(
		TEXT("/Script/NeshamaSDK.NeshamaConfig"),
		TEXT("BasePath"),
		TEXT("/api"),
		GEngineIni
	);
	
	GConfig->SetInt(
		TEXT("/Script/NeshamaSDK.NeshamaConfig"),
		TEXT("Port"),
		8420,
		GEngineIni
	);
	
	GConfig->SetInt(
		TEXT("/Script/NeshamaSDK.NeshamaConfig"),
		TEXT("TimeoutSeconds"),
		30,
		GEngineIni
	);
	
	GConfig->SetString(
		TEXT("/Script/NeshamaSDK.NeshamaConfig"),
		TEXT("DefaultPlayerId"),
		TEXT("player_001"),
		GEngineIni
	);
	
	GConfig->SetString(
		TEXT("/Script/NeshamaSDK.NeshamaConfig"),
		TEXT("DefaultPlayerName"),
		TEXT("Player"),
		GEngineIni
	);
	
	GConfig->SetBool(
		TEXT("/Script/NeshamaSDK.NeshamaConfig"),
		TEXT("AutoReconnect"),
		true,
		GEngineIni
	);
	
	GConfig->SetBool(
		TEXT("/Script/NeshamaSDK.NeshamaConfig"),
		TEXT("DebugMode"),
		false,
		GEngineIni
	);
	
	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDK] Settings registered"));
}

void FNeshamaSDKModule::UnregisterSettings()
{
	// 清理工作（如果需要）
	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDK] Settings unregistered"));
}

#undef LOCTEXT_NAMESPACE
