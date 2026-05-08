// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK Editor - 模块入口实现文件

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "PropertyEditorModule.h"
#include "ISettingsModule.h"
#include "ISettingsSection.h"
#include "ISettingsContainer.h"
#include "NeshamaConfig.h"
#include "NPCSoulComponent.h"
#include "SNeshamaSettingsWidget.h"
#include "SNPCSoulDetailsWidget.h"
#include "UI/SNeshamaSetupWizard.h"

#define LOCTEXT_NAMESPACE "FNeshamaSDKEditorModule"

// ============================================================================
// Tab标识符
// ============================================================================

static const FName NeshamaSetupWizardTabName("NeshamaSetupWizard");

class FNeshamaSDKEditorModule : public IModuleInterface
{
public:
	/** 模块启动时调用 */
	virtual void StartupModule() override;

	/** 模块关闭时调用 */
	virtual void ShutdownModule() override;

private:
	/** 注册Project Settings */
	void RegisterSettings();

	/** 注销Project Settings */
	void UnregisterSettings();

	/** 注册Details面板自定义 */
	void RegisterCustomizations();

	/** 注销Details面板自定义 */
	void UnregisterCustomizations();

	/** 注册NPCSoulComponent的Details面板扩展 */
	void RegisterNPCSoulComponentDetails();

	/** 注册Setup Wizard Tab */
	void RegisterSetupWizardTab();

	/** 注销Setup Wizard Tab */
	void UnregisterSetupWizardTab();

	/** 创建Setup Wizard Tab内容 */
	TSharedRef<SDockTab> OnSpawnSetupWizardTab(const FSpawnTabArgs& SpawnTabArgs);

private:
	/** Tab Spawner句柄 */
};

/** 插件模块实例 */
IMPLEMENT_MODULE(FNeshamaSDKEditorModule, NeshamaSDKEditor)

// ============================================================================
// FNeshamaSDKEditorModule 实现
// ============================================================================

void FNeshamaSDKEditorModule::StartupModule()
{
	UE_LOG(LogTemp, Display, TEXT("[NeshamaSDKEditor] Module starting..."));

	// 注册Settings
	RegisterSettings();

	// 注册Details面板自定义
	RegisterCustomizations();

	// 注册NPCSoulComponent的Details面板扩展
	RegisterNPCSoulComponentDetails();

	// 注册Setup Wizard Tab
	RegisterSetupWizardTab();

	UE_LOG(LogTemp, Display, TEXT("[NeshamaSDKEditor] Module started successfully"));
}

void FNeshamaSDKEditorModule::ShutdownModule()
{
	UE_LOG(LogTemp, Display, TEXT("[NeshamaSDKEditor] Module shutting down..."));

	// 注销Setup Wizard Tab
	UnregisterSetupWizardTab();

	// 注销Details面板自定义
	UnregisterCustomizations();

	// 注销Settings
	UnregisterSettings();

	UE_LOG(LogTemp, Display, TEXT("[NeshamaSDKEditor] Module shut down successfully"));
}

void FNeshamaSDKEditorModule::RegisterSettings()
{
	// 注册Project Settings页面
	ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings");
	
	if (SettingsModule)
	{
		// 创建主容器（Project分区）
		ISettingsContainerPtr SettingsContainer = SettingsModule->GetContainer("Project");
		
		if (SettingsContainer.IsValid())
		{
			// 注册Neshama SDK设置分区
			SettingsContainer->DescribeCategory("NeshamaSDK",
				LOCTEXT("NeshamaSDKCategory", "Neshama SDK"),
				LOCTEXT("NeshamaSDKCategoryTooltip", "Configure the Neshama NPC Soul system"));

			// 注册设置分区
			ISettingsSectionPtr SettingsSection = SettingsModule->RegisterSettings(
				"Project",
				"NeshamaSDK",
				LOCTEXT("NeshamaSDKSettings", "Neshama SDK Settings"),
				LOCTEXT("NeshamaSDKSettingsDescription", "Configure the Neshama SDK connection and behavior settings"),
				GetMutableDefault<UNeshamaConfig>()
			);

			if (SettingsSection.IsValid())
			{
				// 可以在这里绑定设置变更回调
				// SettingsSection->OnSettingChanged().AddRaw(this, &FMyModule::OnSettingsChanged);
			}
		}
	}

	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDKEditor] Settings registered"));
}

void FNeshamaSDKEditorModule::UnregisterSettings()
{
	ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings");
	
	if (SettingsModule)
	{
		SettingsModule->UnregisterSettings(
			"Project",
			"NeshamaSDK",
			"General"
		);
	}

	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDKEditor] Settings unregistered"));
}

void FNeshamaSDKEditorModule::RegisterCustomizations()
{
	FPropertyEditorModule& PropertyModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");
	
	// 注册自定义类型细节（如果有）
	// PropertyModule.RegisterCustomPropertyTypeLayout(...);

	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDKEditor] Customizations registered"));
}

void FNeshamaSDKEditorModule::UnregisterCustomizations()
{
	FPropertyEditorModule* PropertyModule = FModuleManager::GetModulePtr<FPropertyEditorModule>("PropertyEditor");
	
	if (PropertyModule)
	{
		// 注销自定义类型细节
		// PropertyModule->UnregisterCustomPropertyTypeLayout(...);
	}

	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDKEditor] Customizations unregistered"));
}

void FNeshamaSDKEditorModule::RegisterNPCSoulComponentDetails()
{
	// 注册ActorComponent的Details面板扩展
	FPropertyEditorModule& PropertyModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");

	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDKEditor] NPCSoulComponent details registered"));
}

// ============================================================================
// Setup Wizard Tab注册
// ============================================================================

void FNeshamaSDKEditorModule::RegisterSetupWizardTab()
{
	// 创建Workspace菜单分组
	// Neshama workspace group (UE5.6 simplified)
	TSharedPtr<FWorkspaceItem> NeshamaWorkspaceGroup = FWorkspaceItem::NewGroup(
		LOCTEXT("NeshamaWorkspaceGroup", "Neshama"));
	NeshamaWorkspaceGroup->AddItem(
		LOCTEXT("NeshamaWorkspaceGroupTooltip", "Neshama SDK Tools"),
		FSlateIcon());

	// 注册Nomad Tab Spawner
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(
		NeshamaSetupWizardTabName,
		FOnSpawnTab::CreateRaw(this, &FNeshamaSDKEditorModule::OnSpawnSetupWizardTab)
	)
	.SetDisplayName(LOCTEXT("SetupWizardTabTitle", "Neshama Setup Wizard"))
	.SetTooltipText(LOCTEXT("SetupWizardTabTooltip", "Open the Neshama Setup Wizard to configure your SDK and create your first NPC"))
	.SetMenuType(ETabSpawnerMenuType::Hidden)
	.SetIcon(FSlateIcon());

	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDKEditor] Setup Wizard tab registered"));
}

void FNeshamaSDKEditorModule::UnregisterSetupWizardTab()
{
	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(NeshamaSetupWizardTabName);
	UE_LOG(LogTemp, Verbose, TEXT("[NeshamaSDKEditor] Setup Wizard tab unregistered"));
}

TSharedRef<SDockTab> FNeshamaSDKEditorModule::OnSpawnSetupWizardTab(const FSpawnTabArgs& SpawnTabArgs)
{
	return SNew(SDockTab)
		.TabRole(ETabRole::NomadTab)
		.Label(LOCTEXT("SetupWizardTabLabel", "Neshama Setup Wizard"))
		[
			SNew(SNeshamaSetupWizard)
		];
}

#undef LOCTEXT_NAMESPACE
