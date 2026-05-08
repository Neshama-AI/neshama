# R8: Build.cs bTreatWarningsAsErrors → bWarningsAsErrors

## 日期
2026-05-08

## 问题
NeshamaSDK 在 UE 5.6.1 中编译 Build.cs 阶段报错：
```
NeshamaSDK.Build.cs(60,3): error CS0103: The name 'bTreatWarningsAsErrors' does not exist
NeshamaSDKEditor.Build.cs(48,3): error CS0103: The name 'bTreatWarningsAsErrors' does not exist
```

## 根因
UE 5.6 的 ModuleRules API 移除了 `bTreatWarningsAsErrors` 属性，替换为 `bWarningsAsErrors`。

官方文档确认（UE 5.6 Module Properties）：
> `bWarningsAsErrors (Boolean)`: Whether to enable all warnings as errors. UE enables most warnings as errors already, but disables a few (such as deprecation warnings).

## 修复方案
- `bTreatWarningsAsErrors = false;` → `bWarningsAsErrors = false;`
- 语义完全对等，只是属性名变更

## 涉及文件
1. `Source/NeshamaSDK/NeshamaSDK.Build.cs` 第60行
2. `Source/NeshamaSDKEditor/NeshamaSDKEditor.Build.cs` 第48行

## 其他属性检查
- `bEnableExceptions` — UE 5.6 仍有效 ✓
- `bUseRTTI` — UE 5.6 仍有效 ✓
- `PrivateDefinitions` / `PublicDefinitions` — R1已修复 ✓
- `CppStandard` / `PCHUsage` — 无变更 ✓

## 打包版本
v7
