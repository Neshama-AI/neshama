# Neshama UE5 SDK — Quick Start Guide

## 🚀 3-Step Quick Start

### Step 1: Install the Plugin

1. Copy the `NeshamaSDK` folder to your project's `Plugins/` directory
2. Restart Unreal Editor
3. The plugin auto-loads — look for **Window → Neshama Setup Wizard**

### Step 2: Configure with Setup Wizard

1. Open **Window → Neshama Setup Wizard**
2. Choose **"Try Without Account"** for free trial (no registration needed!)
3. Select **Cloud** mode (default) — no server setup required
4. Click **"Free Trial (No API Key)"**
5. Done! Connection configured automatically

### Step 3: Add NPC Soul to Your Game

**Blueprint way (no coding!):**

1. Open any Actor Blueprint
2. Click **Add Component** → search **"NPC Soul"**
3. Set **Preset** to `tavern_keeper` (or any template)
4. Set **Display Name** to your NPC's name
5. Hit Play — your NPC now has a soul! ✦

---

## 📘 Blueprint Quick Start

### Basic NPC Setup

Add `NPC Soul` component to any Actor, then wire up these nodes:

```
[Event BeginPlay]
    ↓
[Create NPC With Soul] → (Self, "tavern_keeper", "Elena")
    ↓ (save to variable: MySoul)
[Bind Event: On Emotion Changed]
    ↓
[Bind Event: On Chat Response]
```

### Player Interaction

```
[Key: E] → [Chat With NPC (MySoul, "Hello!")]
                    ↓ (response via event)
[Event On Chat Response] → [Print String: Response]

[Key: 1] → [Send NPC Event (MySoul, "NPCComplimented", 0.5)]
[Key: 2] → [Send NPC Event (MySoul, "PlayerAttacked", 0.8)]
[Key: 3] → [Send NPC Event (MySoul, "GiftGiven", 0.6)]
```

### Emotion-Driven Behavior

```
[Event On Emotion Changed (NewEmotion)]
    ↓
[Get Dominant Emotion (MySoul)]
    ↓
[Switch on String]
    ├─ "joy"     → Set Animation: Idle_Happy
    ├─ "anger"   → Set Animation: Idle_Angry
    ├─ "fear"    → Set Animation: Idle_Scared
    ├─ "trust"   → Set Animation: Idle_Friendly
    └─ (default) → Set Animation: Idle_Neutral
```

### Dialogue Style Switching

```
[Event On Behavior Changed (BehaviorType, Value)]
    ↓
[Branch: BehaviorType == "dialogue_style_change"]
    ├─ True → [Switch on String: Value]
    │    ├─ "hostile"  → Set Dialogue Mode: Hostile
    │    ├─ "friendly" → Set Dialogue Mode: Friendly
    │    ├─ "cold"     → Set Dialogue Mode: Cold
    │    └─ "neutral"  → Set Dialogue Mode: Neutral
    └─ False → (check other behavior types)
```

### Blueprint Node Reference

| Node | Category | Description |
|------|----------|-------------|
| **Create NPC With Soul** | Neshama | One-line NPC creation |
| **Chat With NPC** | Neshama | Send message, response via event |
| **Send NPC Event** | Neshama | Trigger emotion change |
| **Get Emotion Value** | Neshama (Pure) | Get specific emotion intensity |
| **Get Dominant Emotion** | Neshama (Pure) | Get current dominant emotion |
| **Set Server Mode** | Neshama | Switch Cloud/Local |
| **Get Available Presets** | Neshama (Pure) | List preset templates |
| **Test Connection** | Neshama | Verify server connectivity |

---

## 💻 C++ Quick Start

### Basic Usage

```cpp
#include "NPCSoulComponent.h"
#include "Blueprint/NeshamaBlueprintLibrary.h"

// Method 1: Using Blueprint Library (easiest)
UNPCSoulComponent* Soul = UNeshamaBlueprintLibrary::CreateNPCWithSoul(
    MyActor, 
    TEXT("tavern_keeper"), 
    TEXT("Elena")
);

// Chat
Soul->Chat(TEXT("Hello, traveler!"));

// Send events
Soul->SendGameEvent(EGameEventType::NPCComplimented, 0.5f);
Soul->SendGameEvent(EGameEventType::PlayerAttacked, 0.8f);

// Read emotions
FEmotionState Emotion = Soul->GetEmotionState();
float Joy = Emotion.GetJoy();
float Anger = Emotion.GetAnger();
FString Dominant = Emotion.Dominant;
```

### Method 2: Add Component in Constructor

```cpp
#include "NPCSoulComponent.h"

AMyNPC::AMyNPC()
{
    // Add NPC Soul component
    SoulComponent = CreateDefaultSubobject<UNPCSoulComponent>(TEXT("SoulComponent"));
    SoulComponent->Preset = TEXT("guard_captain");
    SoulComponent->NpcName = TEXT("Captain Marcus");
    SoulComponent->bAutoConnect = true;
}

void AMyNPC::BeginPlay()
{
    Super::BeginPlay();
    
    // Bind events
    SoulComponent->OnEmotionChanged.AddDynamic(this, &AMyNPC::OnEmotionChanged);
    SoulComponent->OnChatResponseBP.AddDynamic(this, &AMyNPC::OnChatResponse);
}

void AMyNPC::OnEmotionChanged(FEmotionState NewEmotion)
{
    if (NewEmotion.Dominant == TEXT("anger"))
    {
        // Switch to hostile dialogue
        SetDialogueMode(EDialogueMode::Hostile);
    }
    else if (NewEmotion.Dominant == TEXT("joy"))
    {
        SetDialogueMode(EDialogueMode::Friendly);
    }
}

void AMyNPC::OnChatResponse(FString Response)
{
    // Display NPC response in UI
    ShowDialogueText(Response);
}
```

### Using Blueprint Library from C++

```cpp
#include "Blueprint/NeshamaBlueprintLibrary.h"

// Quick event sending with string type (supports aliases)
UNeshamaBlueprintLibrary::SendNPCEvent(SoulComponent, TEXT("Greet"), 0.5f);
UNeshamaBlueprintLibrary::SendNPCEvent(SoulComponent, TEXT("Attack"), 0.8f);

// Read emotions
float Joy = UNeshamaBlueprintLibrary::GetEmotionValue(SoulComponent, TEXT("joy"));
FString Dominant = UNeshamaBlueprintLibrary::GetDominantEmotion(SoulComponent);

// Switch server mode
UNeshamaBlueprintLibrary::SetServerMode(ENeshamaServerMode::Cloud);

// Get available presets
TArray<FString> Presets = UNeshamaBlueprintLibrary::GetAvailablePresets();
```

---

## 🎭 NPC Preset Templates

| Preset | Description | Best For |
|--------|-------------|----------|
| `tavern_keeper` | Friendly, remembers regulars, adjusts prices | Shops, inns |
| `guard_captain` | Suspicious of strangers, rewards loyalty | Guards, soldiers |
| `mystic_traveler` | Speaks in riddles, reveals secrets to trusted | Quests, lore |
| `merchant` | Shrewd pricing, discounts for friends | Trading |
| `healer` | Compassionate, grows fond of visitors | Support NPCs |
| `quest_giver` | Evaluates reputation, offers varied quests | Quest hubs |
| `enemy_boss` | Taunts, remembers defeats, adaptive AI | Boss fights |
| `companion` | Deep bond, morale-based support | Party members |

### Custom NPC Templates

You can use any string as a preset — the server will create a default personality:

```cpp
// Custom preset
SoulComponent->Preset = TEXT("pirate_captain");
```

Or define custom templates through the Neshama Dashboard at https://neshama.game/dashboard

---

## ☁️ Cloud vs Local Mode

### Cloud Mode (Recommended for Beginners)

- **No setup required** — just install the plugin
- **Default server**: `https://api.neshama.pw`
- **Free trial available** — 100 API calls/day
- **Auto-scaling** — handles any load
- **Persistent storage** — NPC memories saved in cloud

### Local Mode (Advanced Users)

- **Full control** — run your own Neshama backend
- **Default server**: `http://localhost:8420`
- **Unlimited API calls**
- **Self-hosted data** — privacy for sensitive projects
- **Custom modifications** — extend the backend

To switch modes:

**Blueprint:**
```
[Set Server Mode] → Cloud / Local
```

**C++:**
```cpp
UNeshamaBlueprintLibrary::SetServerMode(ENeshamaServerMode::Local);
```

**Project Settings:**
1. Edit → Project Settings → Neshama SDK
2. Change "Server Mode" to Cloud or Local

---

## 🔧 Setup Wizard (Editor Tool)

The Setup Wizard provides a guided, no-code setup experience:

1. **Window → Neshama Setup Wizard** to open
2. **Welcome** — Choose "Register Account" or "Try Without Account"
3. **Connection** — Cloud (default) or Local mode, verify connection
4. **Create NPC** — Pick a preset, name your NPC, click "Create in Scene"
5. **Done** — View code examples and open example map

The wizard automatically:
- Configures Project Settings
- Spawns an Actor with NPCSoulComponent in the scene
- Sets up the correct server URL and mode

---

## 🎮 Event Types Reference

| Event | Effect | Common Use |
|-------|--------|------------|
| `PlayerEntered` | NPC notices player | Proximity trigger |
| `PlayerLeft` | NPC says goodbye | Player exits area |
| `PlayerAttacked` | Anger/fear increase | Combat system |
| `NPCHealed` | Trust/joy increase | Healing mechanics |
| `NPCDamaged` | Fear/anger increase | Damage system |
| `NPCComplimented` | Joy/trust increase | Friendly dialogue |
| `NPCInsulted` | Anger/disgust increase | Hostile dialogue |
| `GiftGiven` | Joy/trust increase | Gift system |
| `NPCHelped` | Trust increase | Quest completion |
| `TradeCompleted` | Trust increase | Shop transactions |
| `CombatStarted` | Fear/anticipation | Battle triggers |
| `CombatEnded` | Emotion stabilization | Battle end |
| `QuestCompleted` | Joy/trust increase | Quest rewards |
| `QuestAccepted` | Anticipation/trust | Quest start |
| `QuestFailed` | Sadness/shame | Quest failure |

---

## 🎨 Advanced: Local Deployment

For advanced users who want full control:

### Prerequisites
- Python 3.10+
- Redis (for caching)
- PostgreSQL (optional, for persistent storage)

### Quick Start
```bash
# Clone the Neshama backend
git clone https://github.com/neshama/neshama-backend.git
cd neshama-backend

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m neshama.server --port 8420

# The server runs at http://localhost:8420
```

### Docker Deployment
```bash
docker run -p 8420:8420 neshama/server:latest
```

### Configuration in UE5
1. Set Server Mode to **Local** in Project Settings
2. Server URL: `http://localhost`
3. Port: `8420`

---

## ❓ FAQ

### Q: Do I need to write C++?
**A: No!** The entire SDK works through Blueprint. Add the NPC Soul component and use Blueprint nodes like "Chat With NPC" and "Send NPC Event".

### Q: Do I need to register an account?
**A: No!** Click "Try Without Account" in the Setup Wizard for a free trial with 100 API calls/day.

### Q: What happens when the trial expires?
**A:** The NPC will still respond but with limited emotion variety. Register for a free account to get more API calls and persistent memories.

### Q: Can I use this in a shipped game?
**A: Yes!** The Runtime module is fully production-ready. The Editor module is only used during development.

### Q: Does it work with multiplayer?
**A: Yes!** Each NPC has a unique NpcId. The cloud server handles concurrent connections. For local mode, the backend supports multiple game instances.

### Q: How do I debug NPC emotions?
**A:**
1. Enable "Show Debug Info" on the NPCSoulComponent
2. Use the Editor Details panel "Quick Test" buttons
3. Check Output Log for `[Neshama]` prefixed messages

---

## 📚 More Resources

- **Full API Documentation**: https://docs.neshama.game/unreal
- **Discord Community**: https://discord.gg/neshama
- **GitHub Examples**: https://github.com/neshama/unreal-examples
- **Video Tutorials**: https://youtube.com/@neshama
