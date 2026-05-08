// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - Editor模块构建配置

using UnrealBuildTool;

public class NeshamaSDKEditor : ModuleRules
{
	public NeshamaSDKEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

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

		// C++标准设置
		CppStandard = CppStandardVersion.Cpp17;

		// 编辑器特定的定义
		PrivateDefinitions.Add("NESHAMA_SDK_EDITOR=1");
		PrivateDefinitions.Add("WITH_EDITORONLY_DATA=1");

		// 禁用某些警告
		bTreatWarningsAsErrors = false;
	}
}
