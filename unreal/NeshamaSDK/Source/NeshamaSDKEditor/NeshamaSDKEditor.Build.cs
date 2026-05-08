// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - Editor模块构建配置

using System;
using UnrealBuildTool;

public class NeshamaSDKEditor : ModuleRules
{
	public NeshamaSDKEditor(ReadOnlyTargetRules Target) : base(Target)
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
				"EditorStyle",
				"PropertyEditor",
				"UnrealEd",
				"InputCore",
				"Slate",
				"SlateCore",
				"ToolMenus",
				"WorkspaceMenuStructure"
			}
		);

		// 私有依赖 - 包含Runtime模块
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"NeshamaSDK",
				"Projects",
				"EditorWidgets"
			}
		);

		// C++标准设置（UE5.6起必须Cpp20，Cpp17已[Obsolete]）
		CppStandard = CppStandardVersion.Cpp20;

		// 编辑器特定的定义
		PrivateDefinitions.Add("NESHAMA_SDK_EDITOR=1");
		PrivateDefinitions.Add("WITH_EDITORONLY_DATA=1");

		// 禁用某些警告
		bWarningsAsErrors = false;

		// 检测项目路径中的非ASCII字符（已知会导致MSVC PCH C1083错误）
		CheckNonAsciiProjectPath();
	}

	/// <summary>
	/// 检测项目路径是否包含非ASCII字符（与NeshamaSDK.Build.cs保持一致）
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
					throw new BuildException(
						"[NeshamaSDK] FATAL: Project path contains non-ASCII characters!\n" +
						"[NeshamaSDK] Path: " + ProjectPath + "\n" +
						"[NeshamaSDK] MSVC c1xx cannot handle non-ASCII paths and will fail with C1083.\n" +
						"[NeshamaSDK] Fix: Move your entire project to an ASCII-only path.\n" +
						"[NeshamaSDK] Example: C:\\Projects\\MyGame\\\n" +
						"[NeshamaSDK] Steps:\n" +
						"[NeshamaSDK]   1. Close UE5 Editor\n" +
						"[NeshamaSDK]   2. Move project folder to ASCII path (no Chinese/Japanese/Korean chars)\n" +
						"[NeshamaSDK]   3. Delete Intermediate/ and Binaries/ folders\n" +
						"[NeshamaSDK]   4. Right-click .uproject -> Generate Visual Studio project files\n" +
						"[NeshamaSDK]   5. Reopen .uproject"
					);
				}
			}
		}
		catch (BuildException)
		{
			throw;
		}
		catch
		{
		}
	}
}
