// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - Blueprint函数库头文件
// 提供Blueprint友好的快捷API，一行代码创建NPC

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "NeshamaConfig.h"
// Note: .generated.h must be the last include in UE5
#include "NeshamaBlueprintLibrary.generated.h"

// 前向声明
class UNPCSoulComponent;

// ENeshamaServerMode is already defined in NeshamaConfig.h
// Re-export it here for Blueprint convenience

/**
 * UNeshamaBlueprintLibrary
 * 
 * 纯Blueprint函数库，提供快捷API。
 * Blueprint开发者无需写C++，直接调用这些节点即可：
 * 
 * 快速开始：
 *   1. CreateNPCWithSoul → 创建带灵魂的NPC
 *   2. ChatWithNPC → 与NPC对话
 *   3. SendNPCEvent → 发送游戏事件
 *   4. GetEmotionValue / GetDominantEmotion → 读取情绪
 *   5. TestConnection → 测试服务器连接
 */
UCLASS()
class NESHAMASDK_API UNeshamaBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// ============================================================================
	// 快速开始 - 一行代码创建NPC
	// ============================================================================

	/**
	 * 快速创建带NPCSoulComponent的NPC
	 * 这是Blueprint用户最常用的入口函数
	 * 
	 * @param Owner 拥有此组件的Actor（通常是NPC自身）
	 * @param Preset NPC预设模板名称 (如 "tavern_keeper", "guard_captain", "mystic_traveler")
	 * @param NPCName NPC显示名称
	 * @return 创建的NPCSoulComponent实例，失败返回nullptr
	 * 
	 * Blueprint示例：
	 *   [Event BeginPlay] → [Create NPC With Soul (Self, "tavern_keeper", "Elena")]
	 *   → 保存返回值到变量 → 后续调用Chat/SendEvent等
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama",
		meta = (DisplayName = "Create NPC With Soul",
				ToolTip = "Create an NPC with a soul component. The easiest way to get started!",
				Keywords = "neshama npc create soul spawn"))
	static UNPCSoulComponent* CreateNPCWithSoul(AActor* Owner, const FString& Preset, const FString& NPCName);

	// ============================================================================
	// 事件交互
	// ============================================================================

	/**
	 * 发送游戏事件给NPC
	 * 
	 * @param Soul NPCSoulComponent实例
	 * @param EventType 事件类型名称 (如 "PlayerEntered", "NPCComplimented", "GiftGiven"等)
	 * @param Intensity 事件强度 0.0-1.0
	 * 
	 * Blueprint示例：
	 *   [Key: 1] → [Send NPC Event (Soul, "NPCComplimented", 0.5)]
	 *   [Key: 2] → [Send NPC Event (Soul, "PlayerAttacked", 0.8)]
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama",
		meta = (DisplayName = "Send NPC Event",
				ToolTip = "Send a game event to the NPC, affecting their emotions and behavior",
				Keywords = "neshama event send trigger"))
	static void SendNPCEvent(UNPCSoulComponent* Soul, const FString& EventType, float Intensity = 1.0f);

	// ============================================================================
	// 对话
	// ============================================================================

	/**
	 * 与NPC对话
	 * 
	 * @param Soul NPCSoulComponent实例
	 * @param Message 玩家发送的消息
	 * 
	 * Blueprint示例：
	 *   [Key: E] → [Chat With NPC (Soul, "Hello!")] → [Print String: Response]
	 *   响应通过 OnChatResponseBP 事件获取
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama",
		meta = (DisplayName = "Chat With NPC",
				ToolTip = "Send a chat message to the NPC. Response comes via OnChatResponseBP event",
				Keywords = "neshama chat talk dialogue speak"))
	static void ChatWithNPC(UNPCSoulComponent* Soul, const FString& Message);

	// ============================================================================
	// 情绪查询
	// ============================================================================

	/**
	 * 获取指定情绪的强度值
	 * 
	 * @param Soul NPCSoulComponent实例
	 * @param EmotionType 情绪类型名称 (如 "joy", "anger", "trust", "fear"等)
	 * @return 情绪强度 0.0-1.0
	 * 
	 * Blueprint示例：
	 *   [Get Emotion Value (Soul, "joy")] → [Float > 0.5] → [Set Animation: Happy]
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama",
		meta = (DisplayName = "Get Emotion Value",
				ToolTip = "Get the intensity of a specific emotion (0.0-1.0)",
				CompactNodeTitle = "Emotion",
				Keywords = "neshama emotion value intensity"))
	static float GetEmotionValue(UNPCSoulComponent* Soul, const FString& EmotionType);

	/**
	 * 获取NPC的主导情绪名称
	 * 
	 * @param Soul NPCSoulComponent实例
	 * @return 主导情绪名称 (如 "joy", "anger", "trust"等)
	 * 
	 * Blueprint示例：
	 *   [Get Dominant Emotion (Soul)] → [Switch on String] →
	 *     "joy" → Set Animation: Happy
	 *     "anger" → Set Animation: Angry
	 *     "trust" → Set Animation: Friendly
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama",
		meta = (DisplayName = "Get Dominant Emotion",
				ToolTip = "Get the name of the NPC's dominant emotion",
				CompactNodeTitle = "Dominant",
				Keywords = "neshama emotion dominant primary"))
	static FString GetDominantEmotion(UNPCSoulComponent* Soul);

	// ============================================================================
	// 连接测试
	// ============================================================================

	/**
	 * 测试服务器连接
	 * 
	 * @param ServerUrl 服务器URL
	 * @param ApiKey API Key (可选)
	 * 
	 * Blueprint示例：
	 *   [Test Connection ("https://api.neshama.ai", "")] → [Print String: Result]
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama",
		meta = (DisplayName = "Test Connection",
				ToolTip = "Test connection to a Neshama server",
				Keywords = "neshama connection test verify ping"))
	static void TestConnection(const FString& ServerUrl, const FString& ApiKey);

	// ============================================================================
	// 配置快捷方式
	// ============================================================================

	/**
	 * 设置服务器模式（云端/本地）
	 * 
	 * @param Mode 服务器模式枚举
	 */
	UFUNCTION(BlueprintCallable, Category = "Neshama",
		meta = (DisplayName = "Set Server Mode",
				ToolTip = "Switch between Cloud and Local server mode",
				Keywords = "neshama server mode cloud local"))
	static void SetServerMode(ENeshamaServerMode Mode);

	/**
	 * 获取当前服务器模式
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama",
		meta = (DisplayName = "Get Server Mode",
				ToolTip = "Get the current server mode (Cloud or Local)",
				CompactNodeTitle = "Server Mode"))
	static ENeshamaServerMode GetServerMode();

	/**
	 * 获取可用的NPC预设模板列表
	 * 
	 * @return 预设名称数组
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama",
		meta = (DisplayName = "Get Available Presets",
				ToolTip = "Get the list of available NPC preset templates",
				CompactNodeTitle = "Presets"))
	static TArray<FString> GetAvailablePresets();

	/**
	 * 获取预设的描述文本
	 * 
	 * @param PresetId 预设ID
	 * @return 描述文本
	 */
	UFUNCTION(BlueprintPure, Category = "Neshama",
		meta = (DisplayName = "Get Preset Description",
				ToolTip = "Get the description of an NPC preset template"))
	static FString GetPresetDescription(const FString& PresetId);
};
