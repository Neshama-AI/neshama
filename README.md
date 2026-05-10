# Neshama Soul

Give your NPCs a soul, not just a script.

---

## What is Neshama Soul?

Neshama Soul is a real-time NPC emotion and personality engine for Unreal Engine 5. It gives every NPC its own emotions, drives, and personality — running entirely locally with no server or API required.

Instead of scripting NPC reactions, you define who the NPC is. The engine handles the rest.

---

## Features

### Real-time Emotion Engine
9 base emotions (joy, trust, fear, surprise, sadness, disgust, anger, anticipation, calm) that:
- Layer and blend (anger + betrayal = rage)
- Decay over time
- Spread between NPCs socially
- Drive behavior without LLM calls

**< 10ms per update** — safe for game loop.

### OCEAN Personality Model
Every NPC gets a unique personality fingerprint across 5 dimensions:
- **Openness** — curious vs traditional
- **Conscientiousness** — disciplined vs flexible
- **Extraversion** — outgoing vs reserved
- **Agreeableness** — trusting vs skeptical
- **Neuroticism** — stable vs anxious

Personality shifts based on player interactions. Betray a trusting NPC and their agreeableness drops.

### Drive System
NPCs have drives (survival, status, affiliation, etc.) that create emergent behavior. An NPC with high status drive will seek recognition. One with high affiliation will prioritize relationships.

### Social Memory
NPCs remember interactions and share information. Help the blacksmith today, and the innkeeper knows by tomorrow. Relationships decay naturally or strengthen through repeated contact.

---

## Quick Start

### 1. Install Plugin
Copy `NeshamaSoul` folder to your UE5 project's `Plugins/` directory.

### 2. Add Component
Add `MyNeshamaSoulComponent` to any Actor or Character.

### 3. Configure
Set OCEAN values and initial drives in the Details panel.

### 4. Run
```cpp
// In your character class
void AMyNPC::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    SoulComponent->Update(DeltaTime);
}
```

---

## Example Output

```
[MyNPC] Drive=survival Emotion=fear
[MyNPC] Drive=survival Emotion=fear → anger (player attacked)
[MyNPC] Drive=affiliation Emotion=trust (player helped)
```

---

## Technical Details

| | |
|---|---|
| Engine | UE 5.4+ |
| Platform | Win64, Mac, Linux |
| Dependencies | None (pure C API) |
| Performance | < 10ms per NPC per frame |
| License | MIT |

---

## Resources

- [Documentation](https://docs.neshama.game)
- [Discord](https://discord.gg/neshama)
- [GitHub](https://github.com/Neshama-AI/neshama)

---

## License

MIT License. See [LICENSE](LICENSE).
