# UE5 C++ SDK 编译验证计划

## 目标
使 NeshamaSDK 插件在 UE 5.6.1 中编译通过（UHT解析 + C++编译两个阶段）

## 背景
- NeshamaSDK 已有 25+ C++ 文件的预修代码（commit d6e7a57）
- UE5 版本比预期新（5.6.1 vs 预期5.4），需注意API兼容性
- 用户环境：Win11, AMD Ryzen 9 5900HX, VS2022 BuildTools 14.50

## 编译流程
1. **Build.cs阶段** — 模块定义、依赖声明
2. **UHT阶段** — 头文件解析、反射代码生成
3. **C++编译阶段** — 实际编译所有.cpp

## 已知UHT限制（本轮发现）
| 限制 | 解决方案 |
|------|----------|
| `Definitions`属性不存在 | 用`PrivateDefinitions`/`PublicDefinitions` |
| 模板类型不能做默认参数 | 拆函数重载或去掉默认值 |
| 不支持同名UFUNCTION重载 | 改不同函数名（加Simple后缀） |
| `BlueprintAssignable`只能用于MULTICAST | `DECLARE_DYNAMIC_DELEGATE` → `DECLARE_DYNAMIC_MULTICAST_DELEGATE` |
| USTRUCT不能与引擎内置类型同名 | 加Soul前缀（FDialogueContext→FSoulDialogueContext） |
| 枚举UMETA ToolTip不能与UPROPERTY ToolTip重复 | 删除枚举ToolTip |

## 预判C++编译阶段问题
- NeshamaClient.cpp/NPCSoulComponent.cpp: BindLambda→AddLambda（multicast委托不能BindLambda）
- UE 5.6 API变更兼容性
- HTTP模块引用方式

## 验证标准
- UE5编辑器正常启动，无Incompatible module警告
- 插件在内容浏览器可见
- Blueprint节点可用

## 关键文件路径
- 用户项目：`C:\Users\刘舟\Documents\Unreal Projects\我的项目\`
- 插件目录：`Plugins\NeshamaSDK\`
- 日志目录：`Saved\Logs\`
- GitHub源：`./Neshama/unreal/NeshamaSDK/`
