# Neshama Soul SDK

<div align="center">

**Game NPC Soul Operating System**  
*Give your NPCs a soul in 3 minutes*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Unity: 2022.3+](https://img.shields.io/badge/Unity-2022.3%2B-blue)](https://unity.com/)

</div>

---

## Quick Start (3 Steps!)

### Step 1: Install SDK

**Option A: UPM via Git URL (Recommended)**
1. Open `Window → Package Manager`
2. Click `+ → Add package from git URL...`
3. Paste: `https://github.com/neshama/sdk.git#unity`

**Option B: Setup Wizard (Easiest)**
1. Import the `.unitypackage` from [Releases](https://github.com/neshama/sdk/releases)
2. Open `Neshama → Setup Wizard` — it walks you through everything

### Step 2: Get Your API Key

**Free Account (1000 conversations/month):**
- Visit [api.neshama.ai](https://api.neshama.ai) → Sign Up
- Or use the Setup Wizard inside Unity (`Neshama → Setup Wizard`)

**Free Trial (No registration needed):**
- Click "Try Without Account" in the Setup Wizard
- 50 free conversations, valid 24 hours

### Step 3: Add Soul to Your NPC

```csharp
// 1. Add NPCSoul component to your NPC GameObject
var npcSoul = gameObject.AddComponent<NPCSoul>();

// 2. Send a game event
await npcSoul.SendEvent(GameEventType.player_entered, 0.3f);

// 3. Chat with the NPC
var response = await npcSoul.Chat("Hello!");
Debug.Log($"NPC says: {response.content}");

// 4. Listen for emotion changes
npcSoul.OnEmotionChanged += (emotion) => {
    if (emotion.Anger > 0.5f) Debug.Log("NPC is angry!");
};
```

**Done!** Your NPC now has a soul. 🎉

---

## Setup Wizard

The Setup Wizard (`Neshama → Setup Wizard`) provides a guided setup:

```
Step 1: Welcome — Learn what Neshama does
Step 2: Account — Sign up, log in, paste API Key, or free trial
Step 3: Test — Verify your connection works
Step 4: Create NPC — Choose a preset, one-click create
Step 5: Done! — Get quick-start code snippets
```

---

## Configuration

### Cloud Mode (Default — No deployment needed)

The SDK defaults to cloud mode. Just set your API Key:

```csharp
// Via code
var config = NeshamaConfig.CreateDefault();
config.ApiKey = "nsk_your_api_key_here";
```

Or configure in `Edit → Project Settings → Neshama`:
- **Server Mode**: Cloud
- **API Key**: Paste your key from api.neshama.ai

### Local Mode (Advanced — Self-hosted)

If you prefer running your own backend:

```bash
pip install neshama[web]
neshama dashboard
```

Then set Server Mode to Local in Project Settings.

---

## Core Concepts

### NPCSoul Component

`NPCSoul` is the core MonoBehaviour. Attach it to any NPC GameObject.

| Parameter | Description | Default |
|-----------|-------------|---------|
| NPC Id | Unique NPC identifier | npc_001 |
| Preset | Personality preset | default |
| NPC Name | Display name | NPC |
| Auto Connect | Connect on start | true |

### Emotion System (9 Emotions)

| Emotion | Range | Trigger |
|---------|-------|---------|
| Joy | 0.0-1.0 | Gifts, help, compliments |
| Sadness | 0.0-1.0 | Loss, rejection |
| Anger | 0.0-1.0 | Attacks, insults |
| Fear | 0.0-1.0 | Danger, threats |
| Surprise | 0.0-1.0 | Unexpected events |
| Disgust | 0.0-1.0 | Bad behavior |
| Trust | 0.0-1.0 | Consistent kindness |
| Anticipation | 0.0-1.0 | Promises, upcoming events |
| Shame | 0.0-1.0 | Public failure |

### Behavior Modifiers

Events trigger behavior changes:
- `dialogue_style_change` — NPC speaks differently
- `quest_availability_change` — Quests unlock/lock
- `shop_price_modifier` — Prices change based on relationship
- `movement_speed_change` — NPC speeds up or slows down
- `ai_behavior_change` — AI pattern shifts

---

## API Reference

### NeshamaClient

```csharp
var config = NeshamaConfig.CreateDefault();
config.ApiKey = "nsk_xxx";
var client = new NeshamaClient(config, this);

// Connect
await client.ConnectAsync();

// Events
await client.SendEventAsync(npcId, GameEventType.gift_given, 0.5f);

// Chat
var response = await client.ChatAsync(npcId, "Tell me a story", playerId);

// Emotion
var emotion = await client.GetEmotionAsync(npcId);

// Memory
await client.RememberAsync(npcId, "player", "Hero", "ally", "Helpful adventurer");

// Relations
var relations = await client.GetRelationsAsync(npcId);

// Disconnect
client.Dispose();
```

### NPCSoul (MonoBehaviour)

```csharp
// Connection
await npcSoul.Connect();
npcSoul.Disconnect();

// Events
await npcSoul.SendEvent(GameEventType.player_attacked, 0.8f);
await npcSoul.SendEvent(GameEventType.gift_given, 0.5f);

// Chat
ChatResponse response = await npcSoul.Chat("Hello!", "player_001");

// Memory
await npcSoul.RememberEntity("player", "Hero", "ally", "A good friend");

// Quick checks
bool angry = npcSoul.IsAngry();
bool happy = npcSoul.IsHappy();
bool willTalk = npcSoul.IsWillingToTalk();
string style = npcSoul.GetCurrentDialogueStyle();
```

### Events

```csharp
npcSoul.OnEmotionChanged += (emotion) => { /* react */ };
npcSoul.OnBehaviorChanged += (behaviors) => { /* react */ };
npcSoul.OnChatResponse += (response) => { /* react */ };
npcSoul.OnConnectionStateChanged += (connected) => { /* react */ };
npcSoul.OnError += (error) => { /* handle */ };
```

---

## Event Types

```csharp
public enum GameEventType {
    player_entered,      // Player enters NPC's view
    player_left,         // Player leaves
    player_attacked,     // Player attacks NPC
    npc_healed,          // NPC is healed
    npc_damaged,         // NPC takes damage
    npc_complimented,    // NPC is praised
    npc_insulted,        // NPC is insulted
    gift_given,          // NPC receives a gift
    npc_helped,          // Player helps NPC
    trade_completed,     // Trade finished
    combat_started,      // Combat begins
    combat_ended,        // Combat ends
    quest_completed,     // Quest completed
    quest_accepted,      // Quest accepted
    quest_failed         // Quest failed
}
```

---

## Self-Hosting (Advanced)

<details>
<summary>Click to expand local deployment guide</summary>

### Docker (Recommended)

```bash
cd deploy/cloud
cp .env.example .env
# Edit .env with your API keys
docker compose up -d
```

### Manual

```bash
pip install neshama[web]
NESHAMA_JWT_SECRET=your-secret neshama dashboard
```

See [deploy/cloud/README.md](../../deploy/cloud/README.md) for full details.

</details>

---

## Tuanjie Engine (团结引擎)

Neshama SDK is fully compatible with ByteDance's Tuanjie Engine. Supports OpenHarmony, WeChat Mini Games, and Douyin Mini Games. No code changes needed.

---

## FAQ

**Q: Do I need to deploy a server?**  
No! Cloud mode works out of the box. Just get an API key.

**Q: Is it free?**  
Yes! Free tier includes 1000 conversations/month. Trial mode gives 50 conversations without registration.

**Q: Can I use my own LLM API key?**  
Yes, BYOK (Bring Your Own Key) mode is supported — unlimited conversations with your key.

**Q: What Unity versions are supported?**  
Unity 2022.3 LTS and later.

---

## License

MIT License - See [LICENSE](LICENSE)

<div align="center">

**Made with ❤️ by Neshama AI**

</div>
