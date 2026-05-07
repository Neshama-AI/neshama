// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - 模块入口头文件

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

/**
 * Neshama SDK 模块接口
 * 负责模块的加载和卸载
 */
class NESHAMASDK_API FNeshamaSDKModule : public IModuleInterface
{
public:
	/** 模块启动时调用 */
	virtual void StartupModule() override;

	/** 模块关闭时调用 */
	virtual void ShutdownModule() override;

	/**
	 * 检查模块是否已经启动
	 */
	bool IsGameModule() const override
	{
		return true;
	}

private:
	/** 初始化日志系统 */
	void InitializeLogging();

	/** 注册配置 */
	void RegisterSettings();

	/** 注销配置 */
	void UnregisterSettings();
};
