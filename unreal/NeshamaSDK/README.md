# ✦ Neshama SDK for Unreal Engine 5

**Give your NPCs a soul** — emotions, memories, and dynamic behavior in 3 minutes.

[![UE5](https://img.shields.io/badge/UE5-5.3%2B-blue)](https://www.unrealengine.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🚀 3-Step Quick Start

### 1. Install Plugin
Copy `NeshamaSDK/` to your project's `Plugins/` folder, restart UE5.

### 2. Setup Wizard
**Window → Neshama Setup Wizard** → Click **"Try Without Account"** → Done!

### 3. Add NPC Soul
Open any Actor → **Add Component → NPC Soul** → Set Preset → Hit Play ✦

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎭 **9 Emotions** | Joy, Anger, Trust, Fear, Sadness, Surprise, Disgust, Anticipation, Shame |
| 🧠 **Behavior Suggestions** | Dialogue style, quest access, shop prices, AI mode, movement speed |
| 💭 **Persistent Memory** | NPCs remember players across sessions |
| 💬 **Chat System** | AI-powered dialogue with emotion tracking |
| 🔗 **Relationship Graph** | NPC-player affinity tracking |
| 🎨 **Full Blueprint Support** | No C++ required! |
| ☁️ **Cloud Mode** | No server setup, free trial available |
| 🖥 **Local Mode** | Self-hosted for full control |

---

## 📘 Blueprint & C++ Dual Paths

### Blueprint (No Coding!)

```
[Event BeginPlay]
    ↓
[Create NPC With Soul] → (Self, "tavern_keeper", "Elena")
    ↓
[Bind Event: On Emotion Changed]
    ↓
[Key: E] → [Chat With NPC] → [Print String: Response]
[Key: 1] → [Send NPC Event: Greet]
[Key: 2] → [Send NPC Event: Attack]
```

### C++

```cpp
#include "NPCSoulComponent.h"
#include "Blueprint/NeshamaBlueprintLibrary.h"

// One-line NPC creation
UNPCSoulComponent* Soul = UNeshamaBlueprintLibrary::CreateNPCWithSoul(
    MyActor, "tavern_keeper", "Elena");

// Chat
Soul->Chat(TEXT("Hello!"));

// Send events
Soul->SendGameEvent(EGameEventType::NPCComplimented, 0.5f);

// Read emotions
float Joy = Soul->GetEmotionState().GetJoy();
FString Dominant = Soul->GetEmotionState().Dominant;
```

---

## ⚡ Free Trial — No Registration Required

Click **"Try Without Account"** in the Setup Wizard:
- ✅ 100 API calls/day (free)
- ✅ Cloud mode — no server setup
- ✅ All 9 emotions + behavior suggestions
- ✅ Full Blueprint support

Register at https://neshama.game for:
- 🔓 Unlimited API calls
- 💾 Persistent NPC memories
- 📊 Analytics dashboard
- 🎯 Custom NPC templates

---

## ☁️ Cloud vs Local Mode

### Cloud (Recommended)
- **No setup** — just install and go
- **Default**: `https://api.neshama.ai`
- **Free tier**: 100 calls/day
- Switch in Blueprint: `[Set Server Mode → Cloud]`

### Local (Advanced)
- **Full control** — run your own backend
- **Default**: `http://localhost:8420`
- **Unlimited** API calls
- Switch in Blueprint: `[Set Server Mode → Local]`

---

## 📁 Plugin Structure

```
NeshamaSDK/
├── NeshamaSDK.uplugin              # Plugin descriptor
├── Resources/
│   └── Icon128.png                 # Plugin icon
├── Source/
│   ├── NeshamaSDK/                 # Runtime module
│   │   ├── Private/
│   │   │   ├── NPCSoulComponent.cpp
│   │   │   ├── NeshamaClient.cpp
│   │   │   ├── NeshamaConfig.cpp
│   │   │   ├── NeshamaSDKModule.cpp
│   │   │   └── Blueprint/
│   │   │       └── NeshamaBlueprintLibrary.cpp
│   │   └── Public/
│   │       ├── NPCSoulComponent.h
│   │       ├── NeshamaClient.h
│   │       ├── NeshamaConfig.h
│   │       ├── NeshamaTypes.h
│   │       ├── NeshamaSDKModule.h
│   │       └── Blueprint/
│   │           └── NeshamaBlueprintLibrary.h
│   └── NeshamaSDKEditor/           # Editor module
│       ├── Private/
│       │   ├── NeshamaSDKEditorModule.cpp
│       │   ├── SNPCSoulDetailsWidget.cpp
│       │   ├── SNeshamaSettingsWidget.cpp
│       │   └── UI/
│       │       └── SNeshamaSetupWizard.cpp
│       └── Public/
│           ├── SNPCSoulDetailsWidget.h
│           ├── SNeshamaSettingsWidget.h
│           └── UI/
│               └── SNeshamaSetupWizard.h
├── Content/                        # Blueprint assets (created in Editor)
│   ├── UI/
│   ├── Blueprints/
│   └── Data/
└── Documentation/
    ├── QuickStart.md
    └── MarketplaceChecklist.md
```

---

## 🎭 NPC Preset Templates

| Preset | Best For |
|--------|----------|
| `tavern_keeper` | Shops, inns — friendly, remembers regulars |
| `guard_captain` | Guards — suspicious, rewards loyalty |
| `mystic_traveler` | Quests — enigmatic, reveals secrets |
| `merchant` | Trading — shrewd pricing, affinity-based discounts |
| `healer` | Support — compassionate, grows fond of visitors |
| `quest_giver` | Quests — reputation-based quest offers |
| `enemy_boss` | Bosses — taunts, adaptive AI, remembers defeats |
| `companion` | Party — deep bond, morale-based support |

Use any string as a custom preset — the server generates a default personality.

---

## 🔧 Advanced: Local Deployment

```bash
# Quick start with Docker
docker run -p 8420:8420 neshama/server:latest

# Or install from source
git clone https://github.com/neshama/neshama-backend.git
pip install -r requirements.txt
python -m neshama.server --port 8420
```

Then switch to Local mode in Project Settings or Blueprint.

---

## 📚 Documentation

- **[Quick Start Guide](Documentation/QuickStart.md)** — Detailed setup instructions
- **[Marketplace Checklist](Documentation/MarketplaceChecklist.md)** — Submission requirements
- **[Blueprint Examples](Content/README.md)** — Node graphs and patterns
- **[Full API Docs](https://docs.neshama.game/unreal)** — Complete reference

---

## 🛠 Supported Versions

- **Unreal Engine**: 5.3, 5.4, 5.5
- **Platforms**: Win64, Mac, Linux (Runtime), Android/iOS (HTTP only)
- **C++ Standard**: C++17

---

## 📝 License

MIT License — Free for personal and commercial use.

---

## 🤝 Community

- **Discord**: https://discord.gg/neshama
- **GitHub**: https://github.com/neshama
- **Email**: support@neshama.game
