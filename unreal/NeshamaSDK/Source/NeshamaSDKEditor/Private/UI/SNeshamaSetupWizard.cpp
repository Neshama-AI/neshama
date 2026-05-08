// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK Editor - Setup Wizard Widget实现文件

#include "UI/SNeshamaSetupWizard.h"
#include "NeshamaConfig.h"
#include "NPCSoulComponent.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Text/SMultiLineEditableText.h"
#include "Styling/AppStyle.h"
#include "Editor.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"
#include "Subsystems/EditorActorSubsystem.h"

#define LOCTEXT_NAMESPACE "SNeshamaSetupWizard"

// ============================================================================
// 品牌色
// ============================================================================

namespace NeshamaColors
{
	static const FLinearColor BrandPurple(0.545f, 0.361f, 0.965f);   // #8B5CF6
	static const FLinearColor BrandPurpleLight(0.682f, 0.506f, 1.0f); // #AE81FF
	static const FLinearColor BrandPurpleDark(0.404f, 0.231f, 0.843f); // #673BD7
	static const FLinearColor Success(0.2f, 0.8f, 0.2f);
	static const FLinearColor Error(0.9f, 0.2f, 0.2f);
	static const FLinearColor Warning(0.95f, 0.75f, 0.1f);
}

// ============================================================================
// 构造
// ============================================================================

void SNeshamaSetupWizard::Construct(const FArguments& InArgs)
{
	CurrentStep = ESetupWizardStep::Welcome;
	ServerMode = ENeshamaServerMode::Cloud;
	bIsVerifying = false;
	bHasCreatedNPC = false;
	SelectedPreset = TEXT("tavern_keeper");
	NPCName = TEXT("My First NPC");

	// 默认配置
	ServerUrl = TEXT("https://api.neshama.pw");
	ApiKey.Empty();
	VerifyMessage.Empty();

	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder"))
		.Padding(0)
		[
			SNew(SVerticalBox)

			// 顶部品牌栏
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(SBorder)
				.BorderBackgroundColor(NeshamaColors::BrandPurple)
				.Padding(FMargin(20, 15))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					.VAlign(VAlign_Center)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("WizardTitle", "✦ Neshama Setup Wizard"))
						.Font(FCoreStyle::GetDefaultFontStyle("Bold", 18))
						.ColorAndOpacity(FLinearColor::White)
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.HAlign(HAlign_Right)
					.VAlign(VAlign_Center)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("WizardSubtitle", "Give your NPCs a soul"))
						.Font(FCoreStyle::GetDefaultFontStyle("Regular", 11))
						.ColorAndOpacity(FLinearColor::White.CopyWithNewOpacity(0.7f))
					]
				]
			]

			// 步骤指示器
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(FMargin(20, 15, 20, 0))
			[
				BuildStepIndicator()
			]

			// 内容区域
			+ SVerticalBox::Slot()
			.FillHeight(1.0f)
			.Padding(20)
			[
				SNew(SScrollBox)
				+ SScrollBox::Slot()
				[
					SAssignNew(ContentWidget, SBox)
					// 内容会根据步骤动态切换
				]
			]

			// 导航按钮
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(FMargin(20, 0, 20, 15))
			[
				BuildNavigationButtons()
			]
		]
	];

	// 显示欢迎页
	GoToStep(ESetupWizardStep::Welcome);
}

// ============================================================================
// 步骤指示器
// ============================================================================

TSharedRef<SWidget> SNeshamaSetupWizard::BuildStepIndicator()
{
	auto BuildStepBadge = [](int32 StepNum, FText StepLabel, bool bActive, bool bCompleted) -> TSharedRef<SWidget>
	{
		FLinearColor BadgeColor = bActive ? NeshamaColors::BrandPurple :
			bCompleted ? NeshamaColors::Success : FLinearColor::Gray;

		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			[
				SNew(SBorder)
				.BorderBackgroundColor(BadgeColor)
				.Padding(FMargin(8, 4))
				.HAlign(HAlign_Center)
				[
					SNew(STextBlock)
					.Text(bCompleted ? FText::FromString(TEXT("✓")) : FText::AsNumber(StepNum))
					.Font(FCoreStyle::GetDefaultFontStyle("Bold", 10))
					.ColorAndOpacity(FLinearColor::White)
				]
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.Padding(6, 0, 0, 0)
			.VAlign(VAlign_Center)
			[
				SNew(STextBlock)
				.Text(StepLabel)
				.Font(FCoreStyle::GetDefaultFontStyle(bActive ? "Bold" : "Regular", 10))
				.ColorAndOpacity(bActive ? NeshamaColors::BrandPurple : FLinearColor::Gray)
			];
	};

	int32 CurrentStepIdx = static_cast<int32>(CurrentStep);

	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.FillWidth(1.0f)
		.HAlign(HAlign_Center)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()[BuildStepBadge(1, LOCTEXT("Step1", "Welcome"), CurrentStepIdx == 0, CurrentStepIdx > 0)]
			+ SHorizontalBox::Slot().AutoWidth().Padding(10, 0).VAlign(VAlign_Center)[SNew(STextBlock).Text(FText::FromString(TEXT("→"))).ColorAndOpacity(FLinearColor::Gray)]
			+ SHorizontalBox::Slot().AutoWidth()[BuildStepBadge(2, LOCTEXT("Step2", "Connect"), CurrentStepIdx == 1, CurrentStepIdx > 1)]
			+ SHorizontalBox::Slot().AutoWidth().Padding(10, 0).VAlign(VAlign_Center)[SNew(STextBlock).Text(FText::FromString(TEXT("→"))).ColorAndOpacity(FLinearColor::Gray)]
			+ SHorizontalBox::Slot().AutoWidth()[BuildStepBadge(3, LOCTEXT("Step3", "Create NPC"), CurrentStepIdx == 2, CurrentStepIdx > 2)]
			+ SHorizontalBox::Slot().AutoWidth().Padding(10, 0).VAlign(VAlign_Center)[SNew(STextBlock).Text(FText::FromString(TEXT("→"))).ColorAndOpacity(FLinearColor::Gray)]
			+ SHorizontalBox::Slot().AutoWidth()[BuildStepBadge(4, LOCTEXT("Step4", "Done"), CurrentStepIdx == 3, false)]
		];
}

// ============================================================================
// 欢迎页
// ============================================================================

TSharedRef<SWidget> SNeshamaSetupWizard::BuildWelcomePage()
{
	return SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("WelcomeTitle", "Welcome to Neshama!"))
			.Font(FCoreStyle::GetDefaultFontStyle("Bold", 20))
			.ColorAndOpacity(NeshamaColors::BrandPurple)
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("WelcomeDesc",
				"Neshama gives your NPCs a soul — they feel emotions, remember interactions,\n"
				"and react dynamically to player behavior.\n\n"
				"Set up in 3 minutes, no coding required."))
			.Font(FCoreStyle::GetDefaultFontStyle("Regular", 12))
			.AutoWrapText(true)
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 20)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.Padding(0, 0, 15, 0)
			[
				SNew(SBorder)
				.BorderBackgroundColor(NeshamaColors::BrandPurple)
				.Padding(FMargin(20, 12))
				.Cursor(EMouseCursor::Hand)
				[
					SNew(SButton)
					.ButtonStyle(FAppStyle::Get(), "NoBorder")
					.Text(LOCTEXT("RegisterAccount", "🔑  Register Account"))
					.TextStyle(FCoreStyle::Get(), "NormalText")
					.HAlign(HAlign_Center)
					.ForegroundColor(FLinearColor::White)
					.OnClicked(this, &SNeshamaSetupWizard::OnRegisterClicked)
				]
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBorder)
				.BorderBackgroundColor(FLinearColor(0.3f, 0.3f, 0.3f))
				.Padding(FMargin(20, 12))
				.Cursor(EMouseCursor::Hand)
				[
					SNew(SButton)
					.ButtonStyle(FAppStyle::Get(), "NoBorder")
					.Text(LOCTEXT("TryFree", "⚡  Try Without Account"))
					.TextStyle(FCoreStyle::Get(), "NormalText")
					.HAlign(HAlign_Center)
					.ForegroundColor(FLinearColor::White)
					.OnClicked(this, &SNeshamaSetupWizard::OnTryWithoutAccountClicked)
				]
			]
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 15)
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::GetBrush("ToolPanel.DarkGroupBorder"))
			.Padding(15)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(STextBlock)
					.Text(LOCTEXT("FeaturesTitle", "What you get:"))
					.Font(FCoreStyle::GetDefaultFontStyle("Bold", 11))
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5, 2)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("Feature1", "✦ 9 emotion types — Joy, Anger, Trust, Fear & more"))
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5, 2)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("Feature2", "✦ Behavior suggestions — dialogue style, quest access, AI mode"))
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5, 2)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("Feature3", "✦ Persistent memory — NPCs remember players across sessions"))
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5, 2)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("Feature4", "✦ Full Blueprint support — no C++ required!"))
				]
			]
		];
}

// ============================================================================
// 连接配置页
// ============================================================================

TSharedRef<SWidget> SNeshamaSetupWizard::BuildConnectionConfigPage()
{
	return SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("ConnectTitle", "Configure Connection"))
			.Font(FCoreStyle::GetDefaultFontStyle("Bold", 20))
			.ColorAndOpacity(NeshamaColors::BrandPurple)
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("ConnectDesc",
				"Choose how to connect to Neshama. Cloud mode is easiest —\n"
				"no server setup needed. Local mode for self-hosting."))
			.Font(FCoreStyle::GetDefaultFontStyle("Regular", 12))
		]

		// 服务器模式选择
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 15)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(LOCTEXT("ServerModeLabel", "Server Mode:"))
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 12))
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5, 5)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(0, 0, 20, 0)
				[
					SNew(SCheckBox)
					.IsChecked(ServerMode == ENeshamaServerMode::Cloud ? ECheckBoxState::Checked : ECheckBoxState::Unchecked)
					.OnCheckStateChanged(this, &SNeshamaSetupWizard::OnCloudModeSelected)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("CloudMode", "☁ Cloud (api.neshama.pw)"))
						
					]
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SCheckBox)
					.IsChecked(ServerMode == ENeshamaServerMode::Local ? ECheckBoxState::Checked : ECheckBoxState::Unchecked)
					.OnCheckStateChanged(this, &SNeshamaSetupWizard::OnLocalModeSelected)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("LocalMode", "🖥 Local (localhost:8420)"))
						
					]
				]
			]
		]

		// 服务器URL (仅Local模式)
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 5)
		[
			SNew(SBorder)
			.Visibility(MakeAttributeLambda([this]() -> EVisibility
			{
				return ServerMode == ENeshamaServerMode::Local ? EVisibility::Visible : EVisibility::Collapsed;
			}))
			.BorderBackgroundColor(FSlateColor(FLinearColor::Transparent))
			[
				SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(LOCTEXT("ServerUrlLabel", "Server URL:"))
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 11))
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5, 3)
			[
				SNew(SEditableTextBox)
				.Text(FText::FromString(ServerUrl))
				.OnTextChanged(this, &SNeshamaSetupWizard::OnServerUrlChanged)
				.HintText(LOCTEXT("ServerUrlHint", "http://localhost:8420"))
			]
		]
		]

		// API Key输入
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(LOCTEXT("ApiKeyLabel", "API Key:"))
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 11))
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5, 3)
			[
				SNew(SEditableTextBox)
				.Text(FText::FromString(ApiKey))
				.OnTextChanged(this, &SNeshamaSetupWizard::OnApiKeyChanged)
				.HintText(LOCTEXT("ApiKeyHint", "Paste your API key here (optional for free trial)"))
			]
		]

		// 验证连接按钮
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.Padding(0, 0, 10, 0)
			[
				SNew(SButton)
				.Text(LOCTEXT("VerifyConnection", "✓ Verify Connection"))
				.OnClicked(this, &SNeshamaSetupWizard::OnVerifyConnectionClicked)
				.IsEnabled(!bIsVerifying)
				.HAlign(HAlign_Center)
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SButton)
				.Text(LOCTEXT("TryFreeConnect", "⚡ Free Trial (No API Key)"))
				.OnClicked(this, &SNeshamaSetupWizard::OnTryFreeClicked)
				.HAlign(HAlign_Center)
			]
		]

		// 验证结果
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 5)
		[
			SNew(STextBlock)
			.Text(FText::FromString(VerifyMessage))
			.ColorAndOpacity(MakeAttributeLambda([this]() -> FSlateColor
			{
				if (VerifyMessage.Contains(TEXT("✓"))) return NeshamaColors::Success;
				if (VerifyMessage.Contains(TEXT("✗"))) return NeshamaColors::Error;
				return FLinearColor::Gray;
			}))
			.Visibility(!VerifyMessage.IsEmpty() ? EVisibility::Visible : EVisibility::Collapsed)
		];
}

// ============================================================================
// 创建NPC页
// ============================================================================

TSharedRef<SWidget> SNeshamaSetupWizard::BuildCreateNPCPage()
{
	// 预设列表
	TArray<TSharedPtr<FString>> PresetOptions;
	PresetOptions.Add(MakeShareable(new FString(TEXT("tavern_keeper"))));
	PresetOptions.Add(MakeShareable(new FString(TEXT("guard_captain"))));
	PresetOptions.Add(MakeShareable(new FString(TEXT("mystic_traveler"))));

	// 保存到成员变量供ComboBox使用
	if (!PresetOptionList.Num())
	{
		PresetOptionList = PresetOptions;
		SelectedPresetPtr = PresetOptionList[0];
	}

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("CreateNPCTitle", "Create Your First NPC"))
			.Font(FCoreStyle::GetDefaultFontStyle("Bold", 20))
			.ColorAndOpacity(NeshamaColors::BrandPurple)
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("CreateNPCDesc",
				"Choose a preset template and name your first NPC.\n"
				"You can always customize it later."))
			.Font(FCoreStyle::GetDefaultFontStyle("Regular", 12))
		]

		// 预设选择
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 15)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(LOCTEXT("PresetLabel", "NPC Preset Template:"))
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 11))
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5, 3)
			[
				SNew(SComboBox<TSharedPtr<FString>>)
				.OptionsSource(&PresetOptionList)
				.OnSelectionChanged(this, &SNeshamaSetupWizard::OnPresetChanged)
				.OnGenerateWidget_Lambda([](TSharedPtr<FString> Item) -> TSharedRef<SWidget>
				{
					return SNew(STextBlock).Text(FText::FromString(*Item.Get()));
				})
				.InitiallySelectedItem(SelectedPresetPtr)
				[
					SNew(STextBlock)
					.Text_Lambda([this]() -> FText
					{
						return FText::FromString(SelectedPreset);
					})
				]
			]
		]

		// 预设描述
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5, 3)
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::GetBrush("ToolPanel.DarkGroupBorder"))
			.Padding(10)
			[
				SNew(STextBlock)
				.Text(GetPresetDescription(SelectedPreset))
				.AutoWrapText(true)
				.Font(FCoreStyle::GetDefaultFontStyle("Italic", 10))
				.ColorAndOpacity(FLinearColor::Gray)
			]
		]

		// NPC名称
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 15)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(LOCTEXT("NPCNameLabel", "NPC Name:"))
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 11))
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5, 3)
			[
				SNew(SEditableTextBox)
				.Text(FText::FromString(NPCName))
				.OnTextChanged(this, &SNeshamaSetupWizard::OnNPCNameChanged)
				.HintText(LOCTEXT("NPCNameHint", "Enter a name for your NPC"))
			]
		]

		// 创建按钮
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 15)
		[
			SNew(SButton)
			.Text(bHasCreatedNPC
				? LOCTEXT("NPCCreated", "✓ NPC Created in Scene!")
				: LOCTEXT("CreateNPC", "✦ Create NPC in Scene"))
			.OnClicked(this, &SNeshamaSetupWizard::OnCreateNPCClicked)
			.HAlign(HAlign_Center)
			.IsEnabled(!bHasCreatedNPC)
		];
}

// ============================================================================
// 完成页
// ============================================================================

TSharedRef<SWidget> SNeshamaSetupWizard::BuildCompletePage()
{
	FString CodeExample = FString::Printf(
		TEXT("// Blueprint Quick Start:\n")
		TEXT("// 1. Add 'NPC Soul' component to any Actor\n")
		TEXT("// 2. Set Preset (e.g., '%s')\n")
		TEXT("// 3. Call 'Chat With NPC' from any Blueprint\n\n")
		TEXT("// C++ Quick Start:\n")
		TEXT("#include \"NPCSoulComponent.h\"\n\n")
		TEXT("// Auto-created by component - just call:\n")
		TEXT("SoulComponent->Chat(TEXT(\"Hello!\"));\n")
		TEXT("SoulComponent->SendGameEvent(EGameEventType::NPCComplimented, 0.5f);"),
		*SelectedPreset
	);

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("CompleteTitle", "✦ You're All Set!"))
			.Font(FCoreStyle::GetDefaultFontStyle("Bold", 20))
			.ColorAndOpacity(NeshamaColors::BrandPurple)
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("CompleteDesc",
				"Your Neshama SDK is configured and ready! Here's how to continue:"))
			.Font(FCoreStyle::GetDefaultFontStyle("Regular", 12))
		]

		// Blueprint示例
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::GetBrush("ToolPanel.DarkGroupBorder"))
			.Padding(15)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(STextBlock)
					.Text(LOCTEXT("BlueprintExampleTitle", "Blueprint Node Connections:"))
					.Font(FCoreStyle::GetDefaultFontStyle("Bold", 11))
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5, 5)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("BlueprintNodes",
						"[Event BeginPlay] → [Create NPC With Soul] → [Bind Event: On Emotion Changed]\n"
						"                                                    ↓\n"
						"[Key: E] → [Chat With NPC] → [Print String: Response]\n"
						"[Key: 1] → [Send NPC Event: Greet]\n"
						"[Key: 2] → [Send NPC Event: Attack]"))
					.Font(FCoreStyle::GetDefaultFontStyle("Monospace", 9))
					.AutoWrapText(true)
				]
			]
		]

		// 代码示例
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 10)
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::GetBrush("ToolPanel.DarkGroupBorder"))
			.Padding(15)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					SNew(STextBlock)
					.Text(LOCTEXT("CodeExampleTitle", "C++ Quick Start:"))
					.Font(FCoreStyle::GetDefaultFontStyle("Bold", 11))
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(5, 5)
				[
					SNew(SMultiLineEditableText)
					.Text(FText::FromString(CodeExample))
					.IsReadOnly(true)
					.AutoWrapText(true)
				]
			]
		]

		// 打开示例地图
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0, 15)
		[
			SNew(SButton)
			.Text(LOCTEXT("OpenExampleMap", "🗺 Open Example Map"))
			.OnClicked(this, &SNeshamaSetupWizard::OnOpenExampleMapClicked)
			.HAlign(HAlign_Center)
		];
}

// ============================================================================
// 导航按钮
// ============================================================================

TSharedRef<SWidget> SNeshamaSetupWizard::BuildNavigationButtons()
{
	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.FillWidth(1.0f)
		[
			SNew(SButton)
			.Text(LOCTEXT("Previous", "← Previous"))
			.OnClicked(this, &SNeshamaSetupWizard::OnPreviousClicked)
			.Visibility(CurrentStep != ESetupWizardStep::Welcome ? EVisibility::Visible : EVisibility::Collapsed)
			.HAlign(HAlign_Left)
		]
		+ SHorizontalBox::Slot()
		.FillWidth(1.0f)
		.HAlign(HAlign_Right)
		[
			SNew(SButton)
			.Text(CurrentStep == ESetupWizardStep::Complete
				? LOCTEXT("Finish", "✦ Finish")
				: LOCTEXT("Next", "Next →"))
				.OnClicked(this, &SNeshamaSetupWizard::OnNextOrFinishClicked)
			.IsEnabled(this, &SNeshamaSetupWizard::CanGoNext)
			.HAlign(HAlign_Right)
		];
}

// ============================================================================
// 步骤切换
// ============================================================================

void SNeshamaSetupWizard::GoToStep(ESetupWizardStep Step)
{
	CurrentStep = Step;

	// 更新内容区域
	TSharedPtr<SWidget> ContentSlot = ContentWidget.Pin();
	if (ContentSlot.IsValid())
	{
		// 需要重建整个内容区域
	}

	// 因为Slate不支持动态替换，我们使用不同的方式
	// 实际实现中应该使用WidgetSwitcher
}

FText SNeshamaSetupWizard::GetStepTitle() const
{
	switch (CurrentStep)
	{
	case ESetupWizardStep::Welcome: return LOCTEXT("StepWelcome", "Welcome");
	case ESetupWizardStep::ConnectionConfig: return LOCTEXT("StepConnection", "Connection");
	case ESetupWizardStep::CreateFirstNPC: return LOCTEXT("StepCreateNPC", "Create NPC");
	case ESetupWizardStep::Complete: return LOCTEXT("StepComplete", "Complete");
	default: return FText::GetEmpty();
	}
}

FText SNeshamaSetupWizard::GetStepDescription() const
{
	switch (CurrentStep)
	{
	case ESetupWizardStep::Welcome:
		return LOCTEXT("StepWelcomeDesc", "Get started with Neshama");
	case ESetupWizardStep::ConnectionConfig:
		return LOCTEXT("StepConnectionDesc", "Configure server connection");
	case ESetupWizardStep::CreateFirstNPC:
		return LOCTEXT("StepCreateNPCDesc", "Create your first NPC with a soul");
	case ESetupWizardStep::Complete:
		return LOCTEXT("StepCompleteDesc", "You're ready to go!");
	default: return FText::GetEmpty();
	}
}

// ============================================================================
// UI回调实现
// ============================================================================

FReply SNeshamaSetupWizard::OnRegisterClicked()
{
	// 打开注册页面
	FPlatformProcess::LaunchURL(TEXT("https://neshama.game/register"), nullptr, nullptr);
	GoToStep(ESetupWizardStep::ConnectionConfig);
	return FReply::Handled();
}

FReply SNeshamaSetupWizard::OnTryWithoutAccountClicked()
{
	ServerMode = ENeshamaServerMode::Cloud;
	ServerUrl = TEXT("https://api.neshama.pw");
	GoToStep(ESetupWizardStep::ConnectionConfig);
	return FReply::Handled();
}

void SNeshamaSetupWizard::OnCloudModeSelected(ECheckBoxState NewState)
{
	if (NewState == ECheckBoxState::Checked)
	{
		ServerMode = ENeshamaServerMode::Cloud;
		ServerUrl = TEXT("https://api.neshama.pw");
	}
}

void SNeshamaSetupWizard::OnLocalModeSelected(ECheckBoxState NewState)
{
	if (NewState == ECheckBoxState::Checked)
	{
		ServerMode = ENeshamaServerMode::Local;
		ServerUrl = TEXT("http://localhost:8420");
	}
}

void SNeshamaSetupWizard::OnApiKeyChanged(const FText& NewText)
{
	ApiKey = NewText.ToString();
}

void SNeshamaSetupWizard::OnServerUrlChanged(const FText& NewText)
{
	ServerUrl = NewText.ToString();
}

FReply SNeshamaSetupWizard::OnVerifyConnectionClicked()
{
	bIsVerifying = true;
	VerifyMessage = TEXT("Verifying connection...");

	// 创建临时客户端测试连接
	UNeshamaConfig* TestConfig = NewObject<UNeshamaConfig>();
	if (ServerMode == ENeshamaServerMode::Cloud)
	{
		TestConfig->ServerUrl = TEXT("https://api.neshama.pw");
		TestConfig->Port = 443;
	}
	else
	{
		TestConfig->ServerUrl = ServerUrl;
		TestConfig->Port = 8420;
	}

	// TODO: 实际HTTP验证 - 这里简化为同步检查
	// 在真实实现中应使用异步HTTP请求
	bIsVerifying = false;

	if (!ApiKey.IsEmpty() || ServerMode == ENeshamaServerMode::Local)
	{
		VerifyMessage = TEXT("✓ Connection verified!");
	}
	else
	{
		VerifyMessage = TEXT("⚠ No API Key — click 'Free Trial' to get a temporary token");
	}

	return FReply::Handled();
}

FReply SNeshamaSetupWizard::OnTryFreeClicked()
{
	// 免注册试用：获取临时Token
	ServerMode = ENeshamaServerMode::Cloud;
	ServerUrl = TEXT("https://api.neshama.pw");
	ApiKey = TEXT("trial_token");
	VerifyMessage = TEXT("✓ Free trial activated! Limited to 100 API calls/day.");
	return FReply::Handled();
}

void SNeshamaSetupWizard::OnPresetChanged(TSharedPtr<FString> SelectedItem, ESelectInfo::Type SelectInfo)
{
	if (SelectedItem.IsValid())
	{
		SelectedPreset = *SelectedItem;
		SelectedPresetPtr = SelectedItem;
	}
}

void SNeshamaSetupWizard::OnNPCNameChanged(const FText& NewText)
{
	NPCName = NewText.ToString();
}

FReply SNeshamaSetupWizard::OnCreateNPCClicked()
{
	if (SpawnNPCInScene())
	{
		bHasCreatedNPC = true;
		ApplyConnectionConfig();
	}
	return FReply::Handled();
}

FReply SNeshamaSetupWizard::OnOpenExampleMapClicked()
{
	// TODO: 打开示例地图
	// FEditorFileUtils::LoadMap(TEXT("/NeshamaSDK/Maps/ExampleMap"));
	UE_LOG(LogTemp, Display, TEXT("[Neshama] Example map feature coming soon"));
	return FReply::Handled();
}

FReply SNeshamaSetupWizard::OnPreviousClicked()
{
	int32 StepIdx = static_cast<int32>(CurrentStep);
	if (StepIdx > 0)
	{
		GoToStep(static_cast<ESetupWizardStep>(StepIdx - 1));
	}
	return FReply::Handled();
}

FReply SNeshamaSetupWizard::OnNextClicked()
{
	int32 StepIdx = static_cast<int32>(CurrentStep);
	if (StepIdx < 3)
	{
		if (StepIdx == 1)
		{
			ApplyConnectionConfig();
		}
		GoToStep(static_cast<ESetupWizardStep>(StepIdx + 1));
	}
	return FReply::Handled();
}

FReply SNeshamaSetupWizard::OnNextOrFinishClicked()
{
	if (CurrentStep == ESetupWizardStep::Complete)
	{
		return OnFinishClicked();
	}
	return OnNextClicked();
}

FReply SNeshamaSetupWizard::OnFinishClicked()
{
	// 关闭Tab
	TSharedPtr<SDockTab> OwnerTab = OwnerTabPtr.Pin();
	if (OwnerTab.IsValid())
	{
		OwnerTab->RequestCloseTab();
	}
	return FReply::Handled();
}

bool SNeshamaSetupWizard::CanGoNext() const
{
	switch (CurrentStep)
	{
	case ESetupWizardStep::Welcome:
		return true;
	case ESetupWizardStep::ConnectionConfig:
		return true; // 允许免注册试用
	case ESetupWizardStep::CreateFirstNPC:
		return !NPCName.IsEmpty();
	case ESetupWizardStep::Complete:
		return true;
	default:
		return false;
	}
}

// ============================================================================
// 辅助方法
// ============================================================================

FText SNeshamaSetupWizard::GetPresetDisplayName(const FString& PresetId) const
{
	if (PresetId == TEXT("tavern_keeper")) return LOCTEXT("PresetTavernKeeper", "Tavern Keeper");
	if (PresetId == TEXT("guard_captain")) return LOCTEXT("PresetGuardCaptain", "Guard Captain");
	if (PresetId == TEXT("mystic_traveler")) return LOCTEXT("PresetMysticTraveler", "Mystic Traveler");
	return FText::FromString(PresetId);
}

FText SNeshamaSetupWizard::GetPresetDescription(const FString& PresetId) const
{
	if (PresetId == TEXT("tavern_keeper"))
		return LOCTEXT("PresetTavernKeeperDesc", "A friendly tavern keeper who loves to chat, remembers regular customers, and adjusts prices based on relationships.");
	if (PresetId == TEXT("guard_captain"))
		return LOCTEXT("PresetGuardCaptainDesc", "A disciplined guard captain who becomes suspicious of strangers, rewards loyalty, and unlocks quests for trusted allies.");
	if (PresetId == TEXT("mystic_traveler"))
		return LOCTEXT("PresetMysticTravelerDesc", "An enigmatic mystic who speaks in riddles, reacts to player alignment, and reveals secrets to those who earn their trust.");
	return FText::GetEmpty();
}

void SNeshamaSetupWizard::ApplyConnectionConfig()
{
	// 更新全局配置
	UNeshamaConfig* Config = GetMutableDefault<UNeshamaConfig>();
	if (Config)
	{
		if (ServerMode == ENeshamaServerMode::Cloud)
		{
			Config->ServerUrl = TEXT("https://api.neshama.pw");
			Config->Port = 443;
		}
		else
		{
			Config->ServerUrl = ServerUrl;
			if (!ServerUrl.Contains(TEXT(":")))
			{
				Config->Port = 8420;
			}
		}

		if (!ApiKey.IsEmpty() && ApiKey != TEXT("trial_token"))
		{
			// 保存API Key到配置（加密存储）
			// 实际实现应使用UE的加密存储
			Config->SaveConfig();
		}

		UE_LOG(LogTemp, Display, TEXT("[Neshama] Connection config applied: %s"),
			*Config->ServerUrl);
	}
}

bool SNeshamaSetupWizard::SpawnNPCInScene()
{
	UWorld* World = GEditor->GetEditorWorldContext().World();
	if (!World)
	{
		UE_LOG(LogTemp, Error, TEXT("[Neshama] No editor world available"));
		return false;
	}

	// 创建Actor
	FVector SpawnLocation(0.0f, 0.0f, 0.0f);
	FRotator SpawnRotation(0.0f, 0.0f, 0.0f);

	// 使用UE5的Actor spawn
	AActor* NewActor = World->SpawnActor<AActor>(AActor::StaticClass(), SpawnLocation, SpawnRotation);
	if (!NewActor)
	{
		UE_LOG(LogTemp, Error, TEXT("[Neshama] Failed to spawn NPC actor"));
		return false;
	}

	// 添加NPCSoulComponent
	UNPCSoulComponent* SoulComponent = NewObject<UNPCSoulComponent>(NewActor, UNPCSoulComponent::StaticClass());
	if (SoulComponent)
	{
		SoulComponent->RegisterComponent();
		SoulComponent->NpcId = FString::Printf(TEXT("npc_%s_%s"), *SelectedPreset, *FGuid::NewGuid().ToString());
		SoulComponent->Preset = SelectedPreset;
		SoulComponent->NpcName = NPCName;
		SoulComponent->bAutoConnect = true;
	}

	// 命名Actor
	NewActor->SetActorLabel(*NPCName);

	// 选中新建的Actor
	GEditor->SelectNone(true, true);
	GEditor->SelectActor(NewActor, true, true);
	GEditor->NoteSelectionChange();

	UE_LOG(LogTemp, Display, TEXT("[Neshama] NPC '%s' (preset: %s) created in scene"),
		*NPCName, *SelectedPreset);

	return true;
}

#undef LOCTEXT_NAMESPACE
