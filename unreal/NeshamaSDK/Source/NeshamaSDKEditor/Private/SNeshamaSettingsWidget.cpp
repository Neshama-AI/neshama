// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK Editor - 设置面板Widget实现文件

#include "SNeshamaSettingsWidget.h"
#include "NeshamaConfig.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SNumericEntryBox.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "Styling/AppStyle.h"

#define LOCTEXT_NAMESPACE "SNeshamaSettingsWidget"

void SNeshamaSettingsWidget::Construct(const FArguments& InArgs)
{
	// 获取配置
	CachedConfig = GetConfig();

	ChildSlot
	[
		SNew(SVerticalBox)
		
		// 服务器配置分组
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(10.0f)
		[
			CreateConfigGroup(
				LOCTEXT("ServerConfig", "Server Configuration"),
				LOCTEXT("ServerConfigTooltip", "Configure Neshama server connection"))
		]
		
		// 连接配置分组
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(10.0f)
		[
			CreateConfigGroup(
				LOCTEXT("ConnectionConfig", "Connection Configuration"),
				LOCTEXT("ConnectionConfigTooltip", "Configure connection behavior"))
		]
		
		// 默认玩家配置分组
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(10.0f)
		[
			CreateConfigGroup(
				LOCTEXT("PlayerConfig", "Default Player Configuration"),
				LOCTEXT("PlayerConfigTooltip", "Configure default player settings"))
		]
		
		// 调试配置分组
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(10.0f)
		[
			CreateConfigGroup(
				LOCTEXT("DebugConfig", "Debug Configuration"),
				LOCTEXT("DebugConfigTooltip", "Configure debug options"))
		]
		
		// 按钮行
		+ SVerticalBox::Slot()
		.AutoHeight()
		.HAlign(HAlign_Right)
		.Padding(10.0f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.Padding(5.0f)
			[
				SNew(SButton)
				.Text(LOCTEXT("Reset", "Reset to Defaults"))
				.ToolTipText(LOCTEXT("ResetTooltip", "Reset all settings to default values"))
				.OnClicked(this, &SNeshamaSettingsWidget::OnResetClicked)
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.Padding(5.0f)
			[
				SNew(SButton)
				.Text(LOCTEXT("Save", "Save"))
				.ToolTipText(LOCTEXT("SaveTooltip", "Save settings"))
				.OnClicked(this, &SNeshamaSettingsWidget::OnSaveClicked)
			]
		]
	];
}

TSharedRef<SWidget> SNeshamaSettingsWidget::CreateConfigGroup(const FText& GroupName, const FText& GroupTooltip)
{
	return SNew(SExpanderArrow)
		.IndentAmount(10.0f)
		.HeaderContent()
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(STextBlock)
				.Text(GroupName)
				.ToolTipText(GroupTooltip)
				.Font(FEditorStyle::GetFontStyle("DetailsView.CategoryTextStyle"))
			]
		]
		.BodyContent()
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::GetBrush("DetailsView.CategoryMiddle"))
			.Padding(10.0f)
			[
				SNew(SVerticalBox)
				// 子项将在此处添加
			]
		];
}

void SNeshamaSettingsWidget::OnServerUrlChanged(const FText& Text)
{
	if (UNeshamaConfig* Config = GetConfig())
	{
		Config->ServerUrl = Text.ToString();
	}
}

void SNeshamaSettingsWidget::OnPortChanged(int32 NewValue)
{
	if (UNeshamaConfig* Config = GetConfig())
	{
		Config->Port = NewValue;
	}
}

void SNeshamaSettingsWidget::OnTimeoutChanged(int32 NewValue)
{
	if (UNeshamaConfig* Config = GetConfig())
	{
		Config->TimeoutSeconds = NewValue;
	}
}

void SNeshamaSettingsWidget::OnAutoReconnectChanged(ECheckBoxState NewState)
{
	if (UNeshamaConfig* Config = GetConfig())
	{
		Config->bAutoReconnect = (NewState == ECheckBoxState::Checked);
	}
}

void SNeshamaSettingsWidget::OnDefaultPlayerIdChanged(const FText& Text)
{
	if (UNeshamaConfig* Config = GetConfig())
	{
		Config->DefaultPlayerId = Text.ToString();
	}
}

void SNeshamaSettingsWidget::OnDebugModeChanged(ECheckBoxState NewState)
{
	if (UNeshamaConfig* Config = GetConfig())
	{
		Config->bDebugMode = (NewState == ECheckBoxState::Checked);
	}
}

FReply SNeshamaSettingsWidget::OnSaveClicked()
{
	if (UNeshamaConfig* Config = GetConfig())
	{
		Config->SaveConfig();
		UE_LOG(LogTemp, Display, TEXT("[NeshamaSDK] Settings saved"));
	}
	return FReply::Handled();
}

FReply SNeshamaSettingsWidget::OnResetClicked()
{
	// 重置为默认值
	if (UNeshamaConfig* Config = GetConfig())
	{
		Config->ServerUrl = TEXT("https://api.neshama.pw");
		Config->BasePath = TEXT("/api");
		Config->Port = 443;
		Config->ServerMode = ENeshamaServerMode::Cloud;
		Config->TimeoutSeconds = 30;
		Config->bAutoReconnect = true;
		Config->MaxReconnectAttempts = 3;
		Config->ReconnectIntervalSeconds = 5.0f;
		Config->DefaultPlayerId = TEXT("player_001");
		Config->DefaultPlayerName = TEXT("Player");
		Config->bDebugMode = false;
		Config->bAutoHeartbeat = true;
		Config->HeartbeatIntervalSeconds = 30.0f;
		
		Config->SaveConfig();
		UE_LOG(LogTemp, Display, TEXT("[NeshamaSDK] Settings reset to defaults"));
	}
	return FReply::Handled();
}

UNeshamaConfig* SNeshamaSettingsWidget::GetConfig() const
{
	if (!CachedConfig.IsValid())
	{
		CachedConfig = UNeshamaConfig::Get();
	}
	return CachedConfig.Get();
}

#undef LOCTEXT_NAMESPACE
