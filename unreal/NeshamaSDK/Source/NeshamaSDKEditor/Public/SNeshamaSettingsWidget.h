// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK Editor - 设置面板Widget头文件

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

/**
 * Neshama SDK 设置面板Widget
 * 用于Project Settings中的SDK配置页面
 */
class SNeshamaSettingsWidget : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNeshamaSettingsWidget) {}
	SLATE_END_ARGS()

	/** 构造Widget */
	void Construct(const FArguments& InArgs);

private:
	// ============================================================================
	// UI回调函数
	// ============================================================================

	/** 服务器URL改变回调 */
	void OnServerUrlChanged(const FText& Text);

	/** 端口号改变回调 */
	void OnPortChanged(int32 NewValue);

	/** 超时时间改变回调 */
	void OnTimeoutChanged(int32 NewValue);

	/** 自动重连改变回调 */
	void OnAutoReconnectChanged(ECheckBoxState NewState);

	/** 默认玩家ID改变回调 */
	void OnDefaultPlayerIdChanged(const FText& Text);

	/** 调试模式改变回调 */
	void OnDebugModeChanged(ECheckBoxState NewState);

	/** 保存按钮点击回调 */
	FReply OnSaveClicked();

	/** 重置按钮点击回调 */
	FReply OnResetClicked();

	// ============================================================================
	// 数据获取
	// ============================================================================

	/** 获取当前配置 */
	class UNeshamaConfig* GetConfig() const;

	// ============================================================================
	// UI构建
	// ============================================================================

	/** 创建配置分组 */
	TSharedRef<SWidget> CreateConfigGroup(const FText& GroupName, const FText& GroupTooltip);

	/** 创建整数输入框 */
	TSharedRef<SWidget> CreateIntInputField(
		const FText& Label,
		const FText& Tooltip,
		int32& Value,
		const FOnTextChanged& OnChanged);

private:
	/** 配置缓存 */
	mutable TWeakObjectPtr<class UNeshamaConfig> CachedConfig;
};
