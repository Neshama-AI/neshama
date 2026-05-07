# UE Marketplace Submission Checklist

## Pre-Submission Requirements

### ✅ Plugin Structure

- [x] `NeshamaSDK.uplugin` — Valid JSON, FileVersion 3
- [x] `Resources/Icon128.png` — 128×128 plugin icon
- [x] `Source/NeshamaSDK/` — Runtime module
- [x] `Source/NeshamaSDKEditor/` — Editor module
- [x] `Content/` — Blueprint assets directory (with README)
- [x] `Documentation/QuickStart.md` — Getting started guide
- [x] No absolute paths in any file
- [x] No symlinks or external references
- [x] All source files have proper copyright headers

### ✅ .uplugin File Validation

```json
{
    "FileVersion": 3,
    "Version": 1,
    "VersionName": "1.0.0",
    "FriendlyName": "Neshama SDK",
    "Category": "Soul|AI|NPC",
    "CanContainContent": true,
    "Modules": [
        { "Name": "NeshamaSDK", "Type": "Runtime" },
        { "Name": "NeshamaSDKEditor", "Type": "Editor" }
    ]
}
```

- [x] FileVersion is 3 (required by UE5)
- [x] VersionName is semantic version "1.0.0"
- [x] FriendlyName is set
- [x] Description is meaningful
- [x] Category follows UE convention: "Soul|AI|NPC"
- [x] CanContainContent is true (for Blueprint assets)
- [x] All module entries have correct Name, Type, LoadingPhase
- [x] AdditionalDependencies listed: HTTP, Json, JsonUtilities, WebSocket

### ✅ Build Configuration

- [x] `NeshamaSDK.Build.cs` — Runtime module build config
  - [x] PublicDependencyModuleNames: Core, CoreUObject, Engine, HTTP, Json, JsonUtilities
  - [x] CppStandard: Cpp17
  - [x] bTreatWarningsAsErrors: false (recommended for first submission)

- [x] `NeshamaSDKEditor.Build.cs` — Editor module build config
  - [x] PublicDependencyModuleNames: Core, CoreUObject, Engine, Slate, SlateCore, EditorStyle, etc.
  - [x] PrivateDependencyModuleNames: NeshamaSDK
  - [x] CppStandard: Cpp17

### ✅ Supported Engine Versions

| Version | Status |
|---------|--------|
| UE 5.3 | ✅ Supported |
| UE 5.4 | ✅ Supported |
| UE 5.5 | ✅ Supported |

**Minimum Engine Version**: 5.3

### ✅ Supported Platforms

| Platform | Runtime | Editor |
|----------|---------|--------|
| Win64 | ✅ | ✅ |
| Mac | ✅ | ✅ |
| Linux | ✅ | ✅ |
| Android | ⚠️ HTTP only (no WebSocket) | N/A |
| iOS | ⚠️ HTTP only (no WebSocket) | N/A |

### ✅ Code Quality

- [x] All UCLASS/USTRUCT/UENUM have proper macros
- [x] All Blueprint-exposed functions have BlueprintCallable or BlueprintPure
- [x] All Blueprint events use BlueprintImplementableEvent or BlueprintAssignable
- [x] UPROPERTY has proper Category, meta, DisplayName, ToolTip
- [x] UFUNCTION has proper Category, meta, DisplayName, ToolTip, Keywords
- [x] No raw pointers to UObjects — use UPROPERTY() or TWeakObjectPtr
- [x] Includes use proper module paths
- [x] GENERATED_BODY() in all UCLASS/USTRUCT
- [x] .generated.h included last in header files
- [x] No compilation warnings in Development build

### ✅ Blueprint Compatibility

- [x] NPCSoulComponent is Blueprintable and BlueprintType
- [x] UNeshamaBlueprintLibrary has all key functions as BlueprintCallable
- [x] All enums use UENUM(BlueprintType)
- [x] All structs use USTRUCT(BlueprintType)
- [x] Events use BlueprintImplementableEvent for BP override
- [x] Delegates use DECLARE_DYNAMIC_DELEGATE for BP binding
- [x] CompactNodeTitle used for frequently-used pure functions

### ✅ Editor Integration

- [x] Setup Wizard accessible via Window menu
- [x] Project Settings page registered for UNeshamaConfig
- [x] NPCSoulComponent has Details panel customization
- [x] Quick Test buttons in Details panel
- [x] Plugin icon visible in Editor

### ✅ Documentation

- [x] README.md with 3-step quick start
- [x] Documentation/QuickStart.md with detailed guide
- [x] Content/README.md with Blueprint examples
- [x] Code comments on all public APIs
- [x] Blueprint node descriptions (DisplayName, ToolTip, Keywords)

---

## Marketplace Submission Assets

### Required Files

| Asset | Format | Description |
|-------|--------|-------------|
| Plugin Icon | 128×128 PNG | Purple crystal ball (brand color #8B5CF6) |
| Feature Image | 1920×1080 PNG | SDK features showcase |
| Screenshot 1 | 1920×1080 PNG | Setup Wizard in action |
| Screenshot 2 | 1920×1080 PNG | Blueprint node graph example |
| Screenshot 3 | 1920×1080 PNG | NPC emotion state visualization |
| Screenshot 4 | 1920×1080 PNG | Details panel with Quick Test |
| Video | MP4 | 2-minute quick start walkthrough |

### Marketplace Description (Draft)

**Title**: Neshama SDK — Give Your NPCs a Soul

**Short Description** (160 chars):
AI-powered NPC emotion system for Unreal Engine 5. 9 emotions, behavior suggestions, persistent memory. No C++ required — full Blueprint support!

**Full Description**:

Neshama SDK gives your NPCs emotions, memories, and dynamic behavior — making them feel truly alive.

✦ KEY FEATURES
• 9 Emotion Types — Joy, Anger, Trust, Fear & more
• Behavior Suggestions — Dialogue style, quest access, AI mode
• Persistent Memory — NPCs remember players across sessions
• Full Blueprint Support — No C++ required!
• Cloud & Local Modes — No server setup needed to start
• Setup Wizard — Get started in 3 minutes

✦ QUICK START (3 Steps)
1. Install the plugin
2. Open Window → Neshama Setup Wizard
3. Add "NPC Soul" component to any Actor — done!

✦ BLUEPRINT-FRIENDLY
Every API is exposed as Blueprint nodes:
• Create NPC With Soul — One-click NPC creation
• Chat With NPC — Send messages, get responses
• Send NPC Event — Trigger emotion changes
• Get Emotion Value — Read specific emotions
• Get Dominant Emotion — Check current mood

✦ EMOTION-DRIVEN GAMEPLAY
NPCs react dynamically based on their emotional state:
• A tavern keeper who gives discounts when happy
• A guard captain who becomes suspicious after being insulted
• A quest giver who locks quests when angered
• A companion who fights harder when motivated

✦ NO REGISTRATION REQUIRED
Start with the free trial — 100 API calls/day, no account needed. Upgrade for persistent memories and more calls.

✦ ENTERPRISE-READY
For studios needing full control, run the open-source Neshama backend locally. Unlimited API calls, self-hosted data, custom modifications.

**Tags**: AI, NPC, Emotion, Behavior, Dialogue, Memory, Soul, Character, RPG, Blueprint

**Category**: Code Plugins → AI

---

## Testing Checklist

### Build Testing
- [ ] Clean build on Win64 (Development Editor)
- [ ] Clean build on Mac (Development Editor)
- [ ] Clean build on Linux (Development Editor)
- [ ] No compilation warnings
- [ ] No linker errors

### Runtime Testing
- [ ] Plugin loads correctly in new project
- [ ] Setup Wizard opens and functions
- [ ] NPCSoulComponent can be added to Actor
- [ ] Cloud mode connection works
- [ ] Local mode connection works
- [ ] Chat API returns responses
- [ ] Events affect NPC emotions
- [ ] Memory persists across sessions

### Blueprint Testing
- [ ] All Blueprint nodes appear in context menu
- [ ] All nodes execute without errors
- [ ] Events fire correctly in Blueprint
- [ ] Properties editable in Details panel
- [ ] Presets load correctly

### Packaging Testing
- [ ] Game packages successfully with plugin
- [ ] Runtime module included in package
- [ ] Editor module excluded from package
- [ ] No missing DLL/shared library errors at runtime

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | TBD | Initial release |

---

## Known Limitations

1. **WebSocket not supported on mobile** — HTTP polling fallback only
2. **Trial mode limited to 100 API calls/day** — Register for more
3. **.uasset Blueprint files must be created in Editor** — Cannot be generated by code
4. **Setup Wizard requires Editor module** — Not available in game runtime
5. **API Key stored in plain text in config** — Future: use encrypted storage
