# Getting Started with Neshama

> **From zero to a soul-powered NPC in 5 minutes — no server deployment needed.**

---

## What is Neshama?

Neshama is a **Soul Operating System for Game NPCs**. It gives your NPCs:

```
  ❤️  Emotions    — 9 emotions that respond to game events
  🧠  Memory      — Multi-layer memory (short/medium/long term)
  🎭  Personality  — OCEAN model (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
  🕸️  Social      — Relationship graphs between NPCs and players
  💬  Dialogue    — AI-driven conversations with personality
```

**Before Neshama:**
```
  Player: "Hello, can you help me?"
  NPC:    "I can help you with quest #42."
  ── Static. Boring. No personality.
```

**After Neshama:**
```
  Player: "Hello, can you help me?"  
  NPC:    *looks up nervously* "I... I suppose so. You're not like the others
          who came through here. There's something... kind about you."
  ── Emotional. Memorable. Alive.
```

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Unity | 2022.3 LTS or later |
| Internet | Required for cloud mode |
| API Key | Free at api.neshama.ai (or use trial mode) |

> **Don't have Unity?** Neshama also works with Unreal Engine 5. See the [UE SDK](../unreal/NeshamaSDK/).

---

## Step 1: Install the SDK (1 minute)

### Option A: Setup Wizard (Recommended for beginners)

1. Download the latest `.unitypackage` from [GitHub Releases](https://github.com/neshama/sdk/releases)
2. In Unity: `Assets → Import Package → Custom Package...`
3. Select the downloaded file
4. Import everything

### Option B: UPM via Git URL

```
Window → Package Manager → + → Add from git URL
https://github.com/neshama/sdk.git#unity
```

### Option C: From Disk

If you cloned the repo:
```
Window → Package Manager → + → Add from disk
→ Select NeshamaSDK/package.json
```

---

## Step 2: Get Your API Key (1 minute)

### Option A: Free Account (1000 conversations/month)

```
 ┌─────────────────────────────────┐
 │  🔮 api.neshama.ai              │
 │                                 │
 │  Email:    your@email.com       │
 │  Password: ••••••••             │
 │  Name:     YourName             │
 │                                 │
 │  [Create Account]               │
 │                                 │
 │  ✅ Your API Key:               │
 │  nsk_a1b2c3d4e5f6g7h8...       │
 │  [📋 Copy]                      │
 └─────────────────────────────────┘
```

1. Visit [api.neshama.ai](https://api.neshama.ai)
2. Click **"Get Started"** in the sidebar
3. Fill in your email, password, and name
4. Click **"Create Account"**
5. Copy your API Key

### Option B: Free Trial (No registration!)

```
 ┌─────────────────────────────────┐
 │  🎮 Free Trial                  │
 │                                 │
 │  ✅ 50 free AI conversations    │
 │  ✅ No email required           │
 │  ✅ Valid for 24 hours          │
 │  ✅ Upgrade anytime             │
 │                                 │
 │  [🚀 Start Free Trial]         │
 └─────────────────────────────────┘
```

1. In the Setup Wizard or web dashboard, click **"Try Without Account"**
2. Get your trial token immediately
3. Start building!

### Option C: Inside Unity Setup Wizard

Open `Neshama → Setup Wizard` and follow the guided steps.

---

## Step 3: Configure the SDK (30 seconds)

### In Project Settings:

```
Edit → Project Settings → Neshama

┌─────────────────────────────────────┐
│ Server Mode:  [Cloud ▾]            │
│ API Key:      nsk_xxxxxxxxxxxxx    │
│ Base URL:     https://api.neshama.ai│
│ Timeout:      30s                   │
│                                     │
│ [Test Connection]  ✅ Connected!    │
└─────────────────────────────────────┘
```

### Or in code:

```csharp
var config = NeshamaConfig.CreateDefault();
config.ApiKey = "nsk_your_api_key_here";
var client = new NeshamaClient(config, this);
```

---

## Step 4: Create Your First NPC (1 minute)

### Via Setup Wizard:

```
Neshama → Setup Wizard → Step 4: Create NPC

┌─────────────────────────────────────┐
│ Preset:  [Tavern Keeper (Friendly)▾]│
│ Name:    Elena                      │
│                                     │
│ Preview:                            │
│ Friendly, warm, remembers regular   │
│ customers. High Agreeableness.      │
│                                     │
│ [🎮 Create NPC GameObject]          │
└─────────────────────────────────────┘
```

### Via Code:

```csharp
// Create a new NPC GameObject
var npcObj = new GameObject("Elena");

// Add the soul component
var soul = npcObj.AddComponent<NPCSoul>();

// Configure it (or use the Inspector)
soul.NpcName = "Elena";
soul.Preset = "tavern_keeper";
```

---

## Step 5: Bring Your NPC to Life (2 minutes)

### Send Game Events

```csharp
// Player enters NPC's view
await soul.SendEvent(GameEventType.player_entered, 0.3f);

// Player gives a gift
await soul.SendEvent(GameEventType.gift_given, 0.5f);

// Player attacks the NPC
await soul.SendEvent(GameEventType.player_attacked, 0.9f);

// Player helps the NPC
await soul.SendEvent(GameEventType.npc_helped, 0.7f);
```

### Chat with the NPC

```csharp
var response = await soul.Chat("Hello Elena! What can you tell me about this village?");
Debug.Log($"Elena says: {response.content}");
```

### Listen for Emotions

```csharp
soul.OnEmotionChanged += (emotion) => {
    Debug.Log($"Dominant emotion: {emotion.dominant}");
    Debug.Log($"Joy: {emotion.Joy:F2}");
    Debug.Log($"Anger: {emotion.Anger:F2}");
    Debug.Log($"Trust: {emotion.Trust:F2}");
    
    // React in your game
    if (emotion.Anger > 0.7f) {
        animator.SetTrigger("Angry");
        // NPC refuses to trade
    }
    if (emotion.Joy > 0.5f) {
        animator.SetTrigger("Smile");
        // NPC offers a discount
    }
};
```

### Complete Example

```csharp
using UnityEngine;
using Neshama.SDK;
using Neshama.SDK.Enums;
using Neshama.SDK.Models;

public class MyNPC : MonoBehaviour
{
    private NPCSoul _soul;

    async void Start()
    {
        _soul = GetComponent<NPCSoul>();
        
        // Listen for emotions
        _soul.OnEmotionChanged += OnEmotionChanged;
        _soul.OnChatResponse += OnChatResponse;
        
        // Greet when player approaches
        await _soul.SendEvent(GameEventType.player_entered, 0.3f);
        var greeting = await _soul.Chat("Welcome, traveler!");
    }
    
    // Called when player clicks NPC
    public async void OnInteract(string message)
    {
        await _soul.Chat(message, "player_001");
    }
    
    // Called when player gives gift
    public async void OnGiftGiven(string giftName, int value)
    {
        await _soul.SendEvent(GameEventType.gift_given, value / 10f);
    }
    
    private void OnEmotionChanged(EmotionState emotion)
    {
        // Update NPC animation and behavior based on emotions
        if (emotion.Anger > 0.7f) Debug.Log("NPC is furious!");
        if (emotion.Trust > 0.5f) Debug.Log("NPC trusts the player");
    }
    
    private void OnChatResponse(ChatResponse response)
    {
        // Display dialogue in your UI
        Debug.Log($"NPC: {response.content}");
    }
}
```

---

## What's Next?

```
  ┌───────────────────────────────────────────────────┐
  │              Your Learning Path                    │
  │                                                   │
  │  ✅  Quick Start (you are here)                   │
  │  │                                                │
  │  ├── 📖 OCEAN Personality Model                   │
  │  │     Customize your NPC's personality traits     │
  │  │                                                │
  │  ├── 🧠 Memory System                             │
  │  │     Short, medium, and long-term memory         │
  │  │                                                │
  │  ├── 🕸️ Relationship Graph                        │
  │  │     NPC-NPC and NPC-Player relationships        │
  │  │                                                │
  │  ├── 🎭 Composite Emotions                        │
  │  │     Combine basic emotions into complex ones    │
  │  │                                                │
  │  └── 🏗️ Advanced: Self-Hosted Backend              │
  │        Deploy on your own server                   │
  └───────────────────────────────────────────────────┘
```

### Key Resources

| Resource | Link |
|----------|------|
| Dashboard | [api.neshama.ai](https://api.neshama.ai) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Emotion System | [SOUL.md](SOUL.md) |
| Memory System | [MEMORY.md](MEMORY.md) |
| OCEAN Model | [OCEAN.md](OCEAN.md) |
| Self-Hosting | [deploy/cloud/README.md](../deploy/cloud/README.md) |

### Quick Reference

```
  ┌──────────────────────────────────────────────────┐
  │  Neshama Quick Commands (Unity)                  │
  │                                                  │
  │  Neshama → Setup Wizard     Guided setup         │
  │  Neshama → Open Dashboard   Web dashboard        │
  │  Edit → Project Settings → Neshama               │
  │                              Change config        │
  └──────────────────────────────────────────────────┘
```

---

## Troubleshooting

### "Connection failed"

```
✓ Check Server Mode is set to Cloud
✓ Verify your API Key is correct (starts with nsk_)
✓ Test Connection in Project Settings
```

### "Trial expired"

```
✓ Trial tokens last 24 hours
✓ Register a free account for 1000 conversations/month
✓ Use BYOK mode with your own API key for unlimited
```

### "NPC not responding to chat"

```
✓ Ensure NPCSoul component is attached and enabled
✓ Check Auto Connect is enabled
✓ Look for errors in Console (enable Debug Mode)
```

---

## Need Help?

- 📧 Email: [support@neshama.ai](mailto:support@neshama.ai)
- 🐛 Issues: [GitHub Issues](https://github.com/neshama/sdk/issues)
- 📖 Docs: [neshama.ai/docs](https://neshama.ai/docs)

Happy soul-building! 🔮
