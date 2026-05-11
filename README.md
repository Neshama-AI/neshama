# Neshama Soul Engine

A lightweight, self-contained C++17 library for simulating NPC personality, emotions, drives, and memory in games.

## What It Does

Give your NPCs a persistent "soul" — a stateful personality that evolves over time based on events and interactions.

| Core System | What It Provides |
|-------------|------------------|
| **OCEAN Personality** | 5-dimensional personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) |
| **Emotion System** | 8 basic emotions (joy, sadness, anger, fear, surprise, disgust, trust, anticipation) with real-time intensity updates |
| **Drive System** | 5-tier motivational hierarchy (Physiological → Safety → Love/Belonging → Esteem → Self-Actualization) |
| **Memory System** | Three-tier memory (L0: immediate → L1: working → L2: long-term) with importance-weighted decay |
| **Self Evolver** | Detects gradual personality drift and can self-modify within safe bounds |
| **Social Engine** | Social graph with relationship states (friend, rival, neutral) and interaction modeling |
| **Snapshot** | Full state serialization (JSON) with cross-version migration support |

## Architecture

```
Game/Engine
    ↓
UE5 SDK (C++ Plugin) or Unity SDK (C# Wrapper) or Python Bindings
    ↓
neshama_c_api.dll  (C ABI wrapper, UE5 only)
    ↓
neshama_v2.dll     (Core engine, shared)
```

- **Unity**: `NeshamaSoulAgent.cs` → `NeshamaNative.cs` → `neshama_v2.dll` (direct)
- **UE5**: `NeshamaSoulModule` → `neshama_c_api.dll` → `neshama_v2.dll` (via C wrapper)
- **Python**: pybind11 bindings → `neshama_v2.dll` / `libneshama_v2.so`

## Build from Source

### Prerequisites

- C++17 compiler (MSVC, GCC, Clang)
- CMake 3.15+
- (Optional) Python 3.8+ for bindings

### Steps

```bash
git clone https://github.com/Neshama-AI/neshama.git
cd neshama
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
ctest --output-on-failure
```

### Build Options

| Option | Default | Description |
|--------|---------|-------------|
| `NEShamA_BUILD_TESTS` | ON | Build test executables |
| `NEShamA_BUILD_PYTHON` | OFF | Build Python bindings |
| `NEShamA_BUILD_SHARED` | ON | Build as shared library |

### Python Bindings

```bash
cd neshama
pip install .
python -m pytest tests/test_python_bindings.py -v
```

## SDKs

Pre-built SDK packages with ready-to-use DLLs:

| Platform | Package | Location |
|----------|---------|----------|
| **UE5 (R19–R21)** | `sdk/ue5/NeshamaSoul_v1.1/` | C++ plugin with neshama_c_api.dll |
| **Unity (2021.3+)** | `sdk/unity/NeshamaSoul-AssetStore/` | C# package with neshama_v2.dll |
| **Python** | `pip install neshama-v2` | Requires building from source |

### Unity Quick Start

1. Import `NeshamaSoul-v*.unitypackage` into your Unity project
2. Add `NeshamaSoulAgent` component to any GameObject
3. Configure OCEAN personality in Inspector
4. Call `soul.Tick(deltaTime)` in your update loop

### UE5 Quick Start

1. Copy `NeshamaSoul` plugin to your project's `Plugins` folder
2. Add `UNeshamaSoulComponent` to your pawn/character
3. Configure personality and drives via Blueprint or C++
4. Call `TickComponent()` each frame

## API Overview

### Core Types

```cpp
// Personality
struct OceanTraits { float openness, conscientiousness, extraversion, agreeableness, neuroticism; };

// Drives (0.0 - 1.0)
enum class DriveType { Physiological, Safety, Love, Esteem, SelfActualization };

// Emotions (0.0 - 1.0)
enum class EmotionType { Joy, Sadness, Anger, Fear, Surprise, Disgust, Trust, Anticipation };

// State snapshot
struct SoulSnapshot { OceanTraits ocean; std::vector<EmotionData> emotions; std::vector<DriveData> drives; ... };
```

### C API (for FFI)

```c
neshama_soul_create(uint64_t* out_id);
neshama_soul_destroy(uint64_t soul_id);
neshama_ocean_set(uint64_t soul_id, float o, float c, float e, float a, float n);
neshama_emotion_get_dominant(uint64_t soul_id, int* type, float* intensity);
neshama_drive_get_dominant(uint64_t soul_id, int* type, float* intensity);
neshama_soul_tick(uint64_t soul_id, float delta_time, const char* event_json);
neshama_snapshot_export(uint64_t soul_id, char* buffer, int buffer_size);
neshama_snapshot_import(uint64_t soul_id, const char* json);
```

Full API in `include/neshama/neshama_c_api.h`

## Limitations

- No compound emotions (only 8 basic emotions implemented)
- No built-in LLM integration (you handle NLP/event extraction)
- No multiplayer state sync (your game networking layer handles that)
- Web visualization panel is not yet available in this release

## License

MIT

## Links

- [Documentation](https://neshama.ai/docs)
- [Issue Tracker](https://github.com/Neshama-AI/neshama/issues)
- [Discord Community](https://discord.gg/neshama)
- [Support on Afdian (爱发电)](https://ifdian.net/a/neshama)