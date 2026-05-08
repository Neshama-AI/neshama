// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - Runtime模块构建配置

using UnrealBuildTool;

public class NeshamaSDK : ModuleRules
{
	public NeshamaSDK(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		
		// 公共依赖
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"HTTP",
				"Json",
				"JsonUtilities",
				"WebSockets"
			}
		);

		// 私有依赖
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				// 可以添加更多私有依赖
			}
		);

		// 动态加载的模块
		// HTTP is already in PublicDependencyModuleNames, no need to dynamically load

		// C++标准设置
		CppStandard = CppStandardVersion.Cpp20;

		// 是否为Rocket编辑器构建
		if (Target.bBuildEditor == false)
		{
			// 游戏Target配置
			PrivateDefinitions.Add("NESHAMA_SDK_VERSION=1");
		}
		else
		{
			// 编辑器Target配置
			PrivateDefinitions.Add("NESHAMA_SDK_VERSION=1");
			PrivateDefinitions.Add("WITH_EDITOR=1");
		}

		// 网络超时设置
		PrivateDefinitions.Add("NESHAMA_DEFAULT_TIMEOUT=30");

		// 日志级别定义
		PublicDefinitions.Add("NESHAMA_LOG_LEVEL=2");

		// 禁用某些警告
		bWarningsAsErrors = false;
		
		// 允许不安全的代码（如果需要）
		bEnableExceptions = false;
		bUseRTTI = false;
	}
}
