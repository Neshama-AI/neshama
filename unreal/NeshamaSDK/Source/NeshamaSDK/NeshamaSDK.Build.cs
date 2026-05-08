// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - Runtime模块构建配置

using System;
using System.IO;
using UnrealBuildTool;

public class NeshamaSDK : ModuleRules
{
	public NeshamaSDK(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		
		// UE5.6 默认构建设置（消除升级警告）
		DefaultBuildSettings = BuildSettingsVersion.Latest;

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

		// C++标准设置（UE5.6起必须Cpp20，Cpp17已[Obsolete]）
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

		// 检测项目路径中的非ASCII字符（已知会导致MSVC PCH C1083错误）
		CheckNonAsciiProjectPath();
	}

	/// <summary>
	/// 检测项目路径是否包含非ASCII字符
	/// MSVC c1xx编译器在处理含中文/日文/韩文等非ASCII路径时，
	/// 无法正确访问PCH文件，导致 fatal error C1083: No such file or directory
	/// 修复方法：将项目移至纯ASCII路径（如 C:\Projects\MyGame\）
	/// </summary>
	private void CheckNonAsciiProjectPath()
	{
		try
		{
			string ProjectPath = Target.ProjectFile != null 
				? Target.ProjectFile.Directory.FullName 
				: ModuleDirectory;

			foreach (char c in ProjectPath)
			{
				if (c > 127)
				{
					System.Console.WriteLine(
						"[NeshamaSDK] WARNING: Project path contains non-ASCII characters: " + ProjectPath + "\n" +
						"[NeshamaSDK] This may cause MSVC PCH compilation error C1083 (file not found).\n" +
						"[NeshamaSDK] Fix: Move your project to an ASCII-only path (e.g. C:\\Projects\\MyGame\\)"
					);
					break;
				}
			}
		}
		catch
		{
			// 如果无法检测路径，静默跳过
		}
	}
}
