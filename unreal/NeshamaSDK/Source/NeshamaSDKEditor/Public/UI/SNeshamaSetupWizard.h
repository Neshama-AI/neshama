// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK Editor - Setup Wizard Widget头文件
// 通过 Window → Neshama Setup Wizard 打开的向导式配置工具

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "NeshamaConfig.h"

/**
 * Setup Wizard步骤枚举
 */
enum class ESetupWizardStep : uint8
{
	/** 欢迎页 */
	Welcome,
	/** 连接配置 */
	ConnectionConfig,
	/** 创建第一个NPC */
	CreateFirstNPC,
	/** 完成 */
	Complete
};

/**
 * Neshama Setup Wizard
 * 
 * Editor Tool Widget，通过 Window → Neshama Setup Wizard 打开。
 * 引导用户完成：
 *   1. 欢迎/注册
 *   2. 连接配置（云端/本地模式，API Key）
 *   3. 创建第一个NPC
 *   4. 完成并查看示例
 */
class SNeshamaSetupWizard : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNeshamaSetupWizard) {}
	SLATE_END_ARGS()

	/** 构造Widget */
	void Construct(const FArguments& InArgs);

private:
	// ============================================================================
	// 当前状态
	// ============================================================================

	/** 当前步骤 */
	ESetupWizardStep CurrentStep;

	/** 服务器模式 */
	ENeshamaServerMode ServerMode;

	/** API Key */
	FString ApiKey;

	/** 服务器URL */
	FString ServerUrl;

	/** 是否正在验证 */
	bool bIsVerifying;

	/** 验证结果消息 */
	FString VerifyMessage;

	/** 选中的NPC预设 */
	FString SelectedPreset;

	/** NPC名称 */
	FString NPCName;

	/** 是否已创建NPC */
	bool bHasCreatedNPC;

	/** 内容区域Widget指针 */
	TWeakPtr<SWidget> ContentWidget;

	/** Owner Tab指针（用于关闭） */
	TWeakPtr<class SDockTab> OwnerTabPtr;

	/** 预设选项列表 */
	TArray<TSharedPtr<FString>> PresetOptionList;

	/** 当前选中的预设指针 */
	TSharedPtr<FString> SelectedPresetPtr;

	// ============================================================================
	// UI回调函数
	// ============================================================================

	/** "注册账号"按钮点击回调 */
	FReply OnRegisterClicked();

	/** "免注册试用"按钮点击回调 */
	FReply OnTryWithoutAccountClicked();

	/** 服务器模式改变回调 */
	void OnServerModeChanged(ENeshamaServerMode NewMode);

	/** Cloud模式单选回调 */
	void OnCloudModeSelected(ECheckBoxState NewState);

	/** Local模式单选回调 */
	void OnLocalModeSelected(ECheckBoxState NewState);

	/** API Key改变回调 */
	void OnApiKeyChanged(const FText& NewText);

	/** 服务器URL改变回调 */
	void OnServerUrlChanged(const FText& NewText);

	/** "验证连接"按钮点击回调 */
	FReply OnVerifyConnectionClicked();

	/** "免注册试用"连接按钮点击回调 */
	FReply OnTryFreeClicked();

	/** 预设选择改变回调 */
	void OnPresetChanged(TSharedPtr<FString> SelectedItem, ESelectInfo::Type SelectInfo);

	/** NPC名称改变回调 */
	void OnNPCNameChanged(const FText& NewText);

	/** "在场景中创建"按钮点击回调 */
	FReply OnCreateNPCClicked();

	/** "打开示例地图"按钮点击回调 */
	FReply OnOpenExampleMapClicked();

	/** "上一步"按钮点击回调 */
	FReply OnPreviousClicked();

	/** "下一步"按钮点击回调 */
	FReply OnNextClicked();

	/** "完成"按钮点击回调 */
	FReply OnFinishClicked();

	// ============================================================================
	// UI构建
	// ============================================================================

	/** 构建欢迎页 */
	TSharedRef<SWidget> BuildWelcomePage();

	/** 构建连接配置页 */
	TSharedRef<SWidget> BuildConnectionConfigPage();

	/** 构建创建NPC页 */
	TSharedRef<SWidget> BuildCreateNPCPage();

	/** 构建完成页 */
	TSharedRef<SWidget> BuildCompletePage();

	/** 构建导航按钮 */
	TSharedRef<SWidget> BuildNavigationButtons();

	/** 构建步骤指示器 */
	TSharedRef<SWidget> BuildStepIndicator();

	/** 获取步骤标题 */
	FText GetStepTitle() const;

	/** 获取步骤描述 */
	FText GetStepDescription() const;

	/** 切换到指定步骤 */
	void GoToStep(ESetupWizardStep Step);

	/** 获取预设的友好名称 */
	FText GetPresetDisplayName(const FString& PresetId) const;

	/** 获取预设的描述 */
	FText GetPresetDescription(const FString& PresetId) const;

	/** 是否可以进入下一步 */
	bool CanGoNext() const;

	/** 应用连接配置到全局设置 */
	void ApplyConnectionConfig();

	/** 在场景中创建带NPCSoulComponent的Actor */
	bool SpawnNPCInScene();
};
