// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK Editor - Details面板自定义Widget头文件

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "PropertyCustomizationHelpers.h"
#include "NeshamaTypes.h"

/**
 * NPCSoulComponent的Details面板自定义Widget
 * 用于在Details面板中可视化显示情绪状态和快速测试
 */
class SNPCSoulDetailsWidget : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNPCSoulDetailsWidget) {}
	SLATE_END_ARGS()

	/** 构造Widget */
	void Construct(const FArguments& InArgs, class UNPCSoulComponent* InSoulComponent);

private:
	// ============================================================================
	// UI回调函数
	// ============================================================================

	/** 连接按钮点击回调 */
	FReply OnConnectClicked();

	/** 断开连接按钮点击回调 */
	FReply OnDisconnectClicked();

	/** 测试事件按钮点击回调 */
	FReply OnTestEventClicked(EGameEventType EventType);

	/** 刷新状态按钮点击回调 */
	FReply OnRefreshClicked();

	// ============================================================================
	// UI构建
	// ============================================================================

	/** 创建情绪条 */
	TSharedRef<SWidget> CreateEmotionBar(const FText& EmotionName, float Value, FLinearColor Color);

	/** 创建行为建议列表 */
	TSharedRef<SWidget> CreateBehaviorList();

	/** 创建测试按钮 */
	TSharedRef<SWidget> CreateTestButton(const FText& Label, EGameEventType EventType, float Intensity);

private:
	/** NPCSoulComponent引用 */
	TWeakObjectPtr<class UNPCSoulComponent> SoulComponent;

	/** 当前情绪状态 */
	FEmotionState CurrentEmotion;
};

// ============================================================================
// Details面板自定义细节类
// ============================================================================

/**
 * NPCSoulComponent的Details面板自定义细节
 * 用于在Details面板中添加自定义行
 */
class FNPCSoulDetailsCustomization : public IPropertyTypeCustomization
{
public:
	/** 创建一个新的细节实例 */
	static TSharedRef<IPropertyTypeCustomization> MakeInstance();

	/** IPropertyTypeCustomization 接口 */
	virtual void CustomizeHeader(TSharedRef<IPropertyHandle> PropertyHandle,
		FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& Utils) override;
	
	virtual void CustomizeChildren(TSharedRef<IPropertyHandle> PropertyHandle,
		IDetailChildrenBuilder& ChildBuilder, IPropertyTypeCustomizationUtils& Utils) override;

private:
	/** 获取绑定的NPCSoulComponent */
	UNPCSoulComponent* GetSoulComponent() const;
};
