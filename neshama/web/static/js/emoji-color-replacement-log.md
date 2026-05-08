# Emoji & Color Replacement Log
# 14 page JS files under neshama/web/static/js/pages/
# Official palette: #7c5cff (主紫) | #00d4aa (能量青) | #ff6b35 (灵魂之火)

## EMOJI REPLACEMENTS

### 1. billing.js
- Tier emoji: 🎮→Game, 🎬→Pro, 🏢→Enterprise
- Mode: 🔑 BYOK → BYOK, ☁️ hosted → hosted
- Labels: ☁️/🔑 removed from conversation labels
- Callout: 💡 removed
- Feature icons: 🎭→NPC, ☁️→Cloud, 🔊→Voice, 📡→API
- Badge: 🔑 BYOK → BYOK

### 2. chat.js
- NPC avatar: 🎭 → avatar-initial span
- Emotion: emoji → category text
- Empty state: 💬 → "No Chat" text
- Placeholder: 💬 → "Chat" text
- Event buttons: 🎁→Gift, ✨→Praise, ⚔️→Attack, 🤝→Help

### 3. coding-plans.js
- Stat icons: 📦→Plan, ✅→Active, 🔑→Key
- Add button: ➕ removed
- Empty state: 📦→"Plan" text
- Model tag: 🤖 removed
- Warning tags: ⚠️ removed
- Rate icons: ⏱️→RPM, 📅→Day
- Provider map: 🟢→Zhipu, ☁️→Dashscope, 🧪→MiniMax, 🤖→OpenAI, 🧠→Anthropic, 🔵→DeepSeek, 🔮→Model
- Status: ✅/❌ → text Yes/No
- Capabilities: 📞→FC, ⚡→Stream, 👁️→Vision, 🧠→Reason, 📜→ctx

### 4. composite-emotion.js
- BASE_EMOTIONS: all emoji → English labels, colors → official palette
- Empty state: 🎭→"Emotion" text
- Emotion display: emoji span → emotion-dot + label
- Composite map: all emoji → labels
- Fallbacks: 🎭→Emotion, 💭→Emotion

### 5. dashboard.js
- Stat icons: 🎭→NPC, 💬→Chat, 📡→API, ⭐→Pro (with official colors)
- Quick actions: 🔑→Key, 📚→Lib, 📊→Stats, 🎮→Demo (with official colors)
- getEventEmoji→getEventLabel (all event emoji→text)
- getEmotionEmoji→getEmotionDisplay (returns dot+label HTML)
- NPC avatar: 🎭→avatar-initial, emotion emoji→category

### 6. debug.js
- Tab icons: ❤️→Emotion, 🧠→Memory, 🕸️→Relations, 📈→Evolution
- Empty state: 🔬→"Debug" text
- Emotion list: all emoji→labels
- Memory types: 💡→Concept, 👤→Person, 📍→Place, 📅→Event, 📦→Object, 🏢→Org, 📌→Item

### 7. demo.js
- Hints: ⚔️/🎁 removed from hint text
- NPC presets: 🍺→Tavern, 🛡️→Guard, 🔮→Mystic
- EMOTIONS: all emoji→labels
- Events: 🎁→Gift, ⚔️→Attack, 🤝→Help, 💬→Praise, 😤→Insult, 📦→Trade, ⚡→Quest, 💀→Fail
- Logo: 🔮→"Neshama" text
- Comparison: 🧠/📦 removed, ✓/✗ removed
- Toast: 💬 removed
- Story: 🚨/🔮 removed from titles

### 8. emotion.js
- Empty state: ❤️→"Emotion" text
- Emotion map: 😊→Joy, 😢→Sad, 😠→Anger, 😨→Fear, 😲→Surprise, 😒→Disgust, 🤝→Trust, 🤔→Anticipation

### 9. model-marketplace.js
- Stat icons: 🧩→Model, 🤖→Online, 🟢→OK, ✅→Ready
- Filters: 💬→Chat, 💻→Code, 🧠→Reasoning, 👁️→Vision, 📜→LongCtx
- Empty state: 🤖→"Model" text
- Task map: 💬→Chat, 💻→Code, 🧠→Reason, 👁️→Vision, 📜→LongCtx, 📝→Model
- Status: ✅→OK, ⚪→--

### 10. npc-detail.js
- Empty state: 🎭→"NPC" text
- NPC avatar: 🎭→avatar-initial
- Emotion: 😐→category text
- Suggestion: 💡→Tip
- Sidebar: 😐→category text

### 11. npc-event-tester.js
- Events: 15 emojis→labels (🎁→Gift, ⚔️→Attack, 🤝→Help, 💢→Insult, ✨→Praise, 💰→Trade, 🏃→Retreat, 👋→Meet/Depart, 💚→Heal, 💰→Steal, 🤝→Promise, 💔→Betray, 🔍→Discover)
- Empty: 📊→Chart, 🧪→Test, 📋→List
- Emotion: 😐→category text
- Badge: 🔄→Reset
- Sequence: 📋→Seq

### 12. npc-list.js
- Empty state: 🎭→"NPC" text
- NPC avatar: 🎭→avatar-initial
- Emotion: 😐→emotion-dot + label (added EMOTION_COLORS const)
- Close: ✕→×

### 13. settings.js
- Themes: 🌊→Ocean, 🌸→Spring, 🌙→Midnight, 🤖→Cyber, 🌅→Sunset, 🌲→Forest, 🗿→Slate, 💜→Purple
- Fallback: 🎨→Theme
- Empty: 🔧→"Settings" text

### 14. templates.js
- Categories: 📚→All, 🍺→Tavern, 🛡️→Guard, 💰→Merchant, 🧙→Mage, 📜→Quest, 📖→Story, ✨→Custom
- Presets: 🍺→Tavern, 🛡️→Guard, 🧙→Mage, 🔨→Smith, ✨→Custom, 🧒→Child
- Map fallback: 🎭→Template
- Empty: 📚→"Library" text

## COLOR REPLACEMENTS

### Official palette applied:
- #7c5cff (主紫) - Primary, information
- #00d4aa (能量青) - Positive, success
- #ff6b35 (灵魂之火) - Negative, warning
- rgba(124,92,255,0.1) - Tag backgrounds
- #e879a0 - OCEAN agreeableness

### Color mappings:
| Old | New | Files |
|-----|-----|-------|
| #FFD700 | #00d4aa | composite-emotion, emotion |
| #4A90D9 | #7c5cff | composite-emotion, emotion |
| #FF4444 | #ff6b35 | composite-emotion, emotion |
| #9B59B6 | #7c5cff | composite-emotion, emotion |
| #E67E22 | #ff6b35 | composite-emotion, emotion |
| #27AE60 | #00d4aa | composite-emotion, emotion |
| #3498DB | #7c5cff | composite-emotion, emotion |
| #F39C12 | #00d4aa | composite-emotion, emotion |
| #4F46E5 | #7c5cff | emotion |
| #22c55e | #00d4aa | billing, demo, debug, templates |
| #3b82f6 | #7c5cff | demo |
| #ef4444 | #ff6b35 | billing, demo, templates |
| #8b5cf6 | #7c5cff | demo |
| #6366f1 | #7c5cff | demo, debug, templates |
| #4b93ff | #7c5cff | billing, demo, settings |
| rgba(75,147,255,*) | rgba(124,92,255,*) | debug, npc-detail |

## CSS CLASSES NEEDED (add to global CSS)

.avatar-initial {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #7c5cff;
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.emotion-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}

.emotion-label {
  font-size: 12px;
  vertical-align: middle;
}
