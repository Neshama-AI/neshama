// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK Editor - Details面板自定义Widget实现文件

#include "SNPCSoulDetailsWidget.h"
#include "NPCSoulComponent.h"
#include "NeshamaTypes.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Notifications/SProgressBar.h"
#include "Styling/AppStyle.h"

#define LOCTEXT_NAMESPACE "SNPCSoulDetailsWidget"

void SNPCSoulDetailsWidget::Construct(const FArguments& InArgs, UNPCSoulComponent* InSoulComponent)
{
	SoulComponent = InSoulComponent;

	if (SoulComponent.IsValid())
	{
		CurrentEmotion = SoulComponent->GetCurrentEmotion();
	}

	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush("DetailsView.CategoryMiddle"))
		.Padding(5.0f)
		[
			SNew(SVerticalBox)

			// 连接状态
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5.0f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(STextBlock)
					.Text(LOCTEXT("ConnectionStatus", "Connection:"))
					.Font(FAppStyle::GetFontStyle("BoldFont"))
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(5.0f, 0.0f)
				[
					SNew(STextBlock)
					.Text(this, &SNPCSoulDetailsWidget::GetConnectionStatusText)
					.ColorAndOpacity(this, &SNPCSoulDetailsWidget::GetConnectionStatusColor)
				]
			]

			// 分隔线
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 5.0f)
			[
				SNew(SSeparator)
			]

			// 情绪状态标题
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5.0f)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("EmotionState", "Emotion State"))
				.Font(FAppStyle::GetFontStyle("BoldFont"))
			]

			// 情绪条列表
			+ SVerticalBox::Slot()
			.AutoHeight()
			.MaxHeight(200.0f)
			.Padding(5.0f)
			[
				SNew(SScrollBox)
				.Orientation(Orient_Vertical)
				+ SScrollBox::Slot()
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(2.0f)
					[
						CreateEmotionBar(LOCTEXT("Joy", "Joy"), CurrentEmotion.GetJoy(), FLinearColor::Green)
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(2.0f)
					[
						CreateEmotionBar(LOCTEXT("Sadness", "Sadness"), CurrentEmotion.GetSadness(), FLinearColor::Blue)
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(2.0f)
					[
						CreateEmotionBar(LOCTEXT("Anger", "Anger"), CurrentEmotion.GetAnger(), FLinearColor::Red)
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(2.0f)
					[
						CreateEmotionBar(LOCTEXT("Fear", "Fear"), CurrentEmotion.GetFear(), FLinearColor(0.5f, 0.f, 0.5f))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(2.0f)
					[
						CreateEmotionBar(LOCTEXT("Trust", "Trust"), CurrentEmotion.GetTrust(), FLinearColor(0.f, 1.f, 1.f))
					]
				]
			]

			// 分隔线
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 5.0f)
			[
				SNew(SSeparator)
			]

			// 测试按钮标题
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5.0f)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("QuickTest", "Quick Test"))
				.Font(FAppStyle::GetFontStyle("BoldFont"))
			]

			// 测试按钮行
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5.0f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(2.0f)
				[
					CreateTestButton(LOCTEXT("Compliment", "Compliment"), EGameEventType::NPCComplimented, 0.3f)
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(2.0f)
				[
					CreateTestButton(LOCTEXT("Insult", "Insult"), EGameEventType::NPCInsulted, 0.6f)
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(2.0f)
				[
					CreateTestButton(LOCTEXT("Attack", "Attack"), EGameEventType::PlayerAttacked, 0.8f)
				]
			]

			// 第二行测试按钮
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5.0f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(2.0f)
				[
					CreateTestButton(LOCTEXT("Gift", "Gift"), EGameEventType::GiftGiven, 0.5f)
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(2.0f)
				[
					CreateTestButton(LOCTEXT("Help", "Help"), EGameEventType::NPCHelped, 0.4f)
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(2.0f)
				[
					SNew(SButton)
					.Text(LOCTEXT("Refresh", "Refresh"))
					.OnClicked(this, &SNPCSoulDetailsWidget::OnRefreshClicked)
					.HAlign(HAlign_Center)
				]
			]

			// 连接/断开按钮
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(5.0f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(2.0f)
				[
					SNew(SButton)
					.Text(LOCTEXT("Connect", "Connect"))
					.OnClicked(this, &SNPCSoulDetailsWidget::OnConnectClicked)
					.IsEnabled(this, &SNPCSoulDetailsWidget::CanConnect)
					.HAlign(HAlign_Center)
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(2.0f)
				[
					SNew(SButton)
					.Text(LOCTEXT("Disconnect", "Disconnect"))
					.OnClicked(this, &SNPCSoulDetailsWidget::OnDisconnectClicked)
					.IsEnabled(this, &SNPCSoulDetailsWidget::CanDisconnect)
					.HAlign(HAlign_Center)
				]
			]
		]
	];
}

TSharedRef<SWidget> SNPCSoulDetailsWidget::CreateEmotionBar(const FText& EmotionName, float Value, FLinearColor Color)
{
	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.FillWidth(0.3f)
		[
			SNew(STextBlock)
			.Text(EmotionName)
			.ToolTipText(FText::Format(LOCTEXT("EmotionTooltip", "{0}: {1}%"), EmotionName, FText::AsNumber(Value * 100)))
		]
		+ SHorizontalBox::Slot()
		.FillWidth(0.7f)
		[
			SNew(SProgressBar)
			.Percent(Value)
			.FillColorAndOpacity(Color)
			.ToolTipText(FText::Format(LOCTEXT("EmotionTooltip", "{0}: {1}%"), EmotionName, FText::AsNumber(Value * 100)))
		];
}

TSharedRef<SWidget> SNPCSoulDetailsWidget::CreateTestButton(const FText& Label, EGameEventType EventType, float Intensity)
{
	return SNew(SButton)
		.Text(Label)
		.OnClicked(this, &SNPCSoulDetailsWidget::OnTestEventClicked, EventType)
		.IsEnabled(this, &SNPCSoulDetailsWidget::CanSendEvent)
		.HAlign(HAlign_Center)
		.ToolTipText(LOCTEXT("TestEventTooltip", "Send a test event to this NPC"));
}

FReply SNPCSoulDetailsWidget::OnConnectClicked()
{
	if (UNPCSoulComponent* Soul = SoulComponent.Get())
	{
		Soul->Connect();
	}
	return FReply::Handled();
}

FReply SNPCSoulDetailsWidget::OnDisconnectClicked()
{
	if (UNPCSoulComponent* Soul = SoulComponent.Get())
	{
		Soul->Disconnect();
	}
	return FReply::Handled();
}

FReply SNPCSoulDetailsWidget::OnTestEventClicked(EGameEventType EventType)
{
	if (UNPCSoulComponent* Soul = SoulComponent.Get())
	{
		TMap<FString, FString> Context;
		Context.Add(TEXT("test"), TEXT("true"));
		Context.Add(TEXT("source"), TEXT("editor_test"));
		Soul->SendGameEvent(EventType, 0.5f, Context);
		
		// 更新当前情绪显示
		CurrentEmotion = Soul->GetCurrentEmotion();
	}
	return FReply::Handled();
}

FReply SNPCSoulDetailsWidget::OnRefreshClicked()
{
	if (UNPCSoulComponent* Soul = SoulComponent.Get())
	{
		CurrentEmotion = Soul->GetCurrentEmotion();
	}
	return FReply::Handled();
}

FText SNPCSoulDetailsWidget::GetConnectionStatusText() const
{
	if (UNPCSoulComponent* Soul = SoulComponent.Get())
	{
		return Soul->IsConnected() ? LOCTEXT("Connected", "Connected") : LOCTEXT("Disconnected", "Disconnected");
	}
	return LOCTEXT("Unknown", "Unknown");
}

FSlateColor SNPCSoulDetailsWidget::GetConnectionStatusColor() const
{
	if (UNPCSoulComponent* Soul = SoulComponent.Get())
	{
		return Soul->IsConnected() ? FLinearColor::Green : FLinearColor::Red;
	}
	return FLinearColor::Gray;
}

bool SNPCSoulDetailsWidget::CanConnect() const
{
	if (UNPCSoulComponent* Soul = SoulComponent.Get())
	{
		return !Soul->IsConnected();
	}
	return false;
}

bool SNPCSoulDetailsWidget::CanDisconnect() const
{
	if (UNPCSoulComponent* Soul = SoulComponent.Get())
	{
		return Soul->IsConnected();
	}
	return false;
}

bool SNPCSoulDetailsWidget::CanSendEvent() const
{
	if (UNPCSoulComponent* Soul = SoulComponent.Get())
	{
		return Soul->IsConnected();
	}
	return false;
}

// ============================================================================
// FNPCSoulDetailsCustomization 实现
// ============================================================================

TSharedRef<IPropertyTypeCustomization> FNPCSoulDetailsCustomization::MakeInstance()
{
	return MakeShareable(new FNPCSoulDetailsCustomization());
}

void FNPCSoulDetailsCustomization::CustomizeHeader(TSharedRef<IPropertyHandle> PropertyHandle,
	FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& Utils)
{
	HeaderRow
		.NameContent()
		[
			SNew(STextBlock)
			.Text(LOCTEXT("NPCSoulHeader", "NPC Soul"))
			.Font(FAppStyle::GetFontStyle("BoldFont"))
		]
		.ValueContent()
		[
			SNew(STextBlock)
			.Text(LOCTEXT("NPCSoulValue", "Neshama Soul Component"))
		];
}

void FNPCSoulDetailsCustomization::CustomizeChildren(TSharedRef<IPropertyHandle> PropertyHandle,
	IDetailChildrenBuilder& ChildBuilder, IPropertyTypeCustomizationUtils& Utils)
{
	// 自定义子项（如果需要）
}

UNPCSoulComponent* FNPCSoulDetailsCustomization::GetSoulComponent() const
{
	return nullptr;
}

#undef LOCTEXT_NAMESPACE
