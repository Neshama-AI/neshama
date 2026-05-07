# Neshama Examples

This directory contains example scripts and configurations for Neshama.

## Quick Examples

### Basic Chat

```python
from neshama.core.engine import NeshamaEngine

# Create engine
engine = NeshamaEngine()

# Start conversation
response = engine.chat("Hello!")
print(response.content)
```

### Multi-turn Conversation

```python
from neshama.core.engine import NeshamaEngine

engine = NeshamaEngine()

# Create session
session = engine.create_session(user_id="user123")

# Multi-turn chat
response1 = engine.chat("I'm feeling sad today", session_id=session.id)
response2 = engine.chat("Can you help me?", session_id=session.id)
```

### Custom Personality

```python
from neshama.core.ocean import OceanManager
from neshama.core.personality import Personality

# Create from preset
personality = Personality.from_preset("MyBot", "neshama")

# Customize
personality.add_desire("求知欲", "想知道本质", 1)
personality.set_response_style(directness=0.8, humor=0.6)

# Generate SKILL.md
skill_md = personality.generate_skill_md()
```

### Emotion Recognition

```python
from neshama.soul.emotion import recognize_emotion, EmotionCategory

# Recognize emotions
emotions = recognize_emotion("I'm so happy today!")

for emotion in emotions:
    print(f"{emotion.category.value}: {emotion.intensity:.2f}")
```

### Memory System

```python
from neshama.memory import Memory, MemoryConfig

# Create memory
config = MemoryConfig(agent_id="my_agent")
memory = Memory(config=config)

# Add conversation
memory.add_turn("user", "Hello")
memory.add_turn("assistant", "Hi!")

# Get context
context = memory.get_short_term_context()
```
