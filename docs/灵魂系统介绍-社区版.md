# 你的NPC，活着吗？

---

## 一、一个所有人都假装没看见的问题

你做了一个RPG。剧情写了十万字，地图铺了三大陆，Boss战调了四十遍手感。玩家上线——

直奔主线，跳过对话，速通Boss，30小时通关，卸载。

为什么？因为玩家很早就发现了一件事：**这个世界里除了他，没有活人。**

铁匠每天站在同一个位置，说同一句话。酒馆老板永远微笑，永远欢迎光临。村口的小孩从第一章到终章都在玩同一个捉迷藏。你杀了村长，村民毫无反应。你救了世界，NPC照常问你"今天天气不错"。

玩家不是在玩一个世界，他是在翻一本翻完了就不会再打开的画册。

**NPC的问题，不是AI够不够聪明，而是它们有没有灵魂。**

聪明是能回答问题，灵魂是——恐惧时会颤抖，愤怒时会失控，被背叛后会记住你，喜欢你时会笨拙地表达，失去重要的人会真正悲伤。

这是 Neshama 要做的事。

---

## 二、灵魂系统到底是什么

Neshama 不是一个对话插件，不是一个ChatGPT套壳。**它是一套完整的NPC灵魂操作系统。**

如果你把传统NPC比作一个读稿的演员——导演喊action，它说台词；喊cut，它就死机——那Neshama要做的，是让这个演员带上自己的性格、情绪、记忆和社交关系走进片场，然后**按照自己的意志行动**。

它由7个核心模块组成，每一个都解决一个"NPC为什么不像人"的具体问题：

---

### 1. 人格系统 —— NPC不是换皮模板

传统做法：给NPC贴一个标签——"友善的商人"、"暴躁的守卫"。所有"友善商人"一模一样。

Neshama 用 **OCEAN五维人格模型**（开放性/尽责性/外向性/宜人性/神经质）给每个NPC生成独一无二的人格指纹。两个都是"商人"，但一个开放性高（爱聊新鲜事），一个尽责性高（斤斤计较），聊天体验完全不同。

更关键的是：**人格不是静态的。** 一个天真的NPC经历背叛后，宜人性会下降，神经质会上升。你的玩家对NPC做了什么，NPC就会长成什么样。世界塑造角色，角色也塑造世界。

---

### 2. 复合情绪引擎 —— 情绪不是开关，是河流

绝大多数系统的情绪是标签：`happy = true`，`angry = false`。这是开关，不是情绪。

Neshama 实现了 **9种基础情绪**（喜悦/信任/恐惧/惊讶/悲伤/厌恶/愤怒/期待/平静），并且它们会——

- **叠加**：悲伤 + 愤怒 = 绝望。恐惧 + 期待 = 忐忑。
- **冲突**：爱一个人，但恨他做的事——矛盾情绪共存，NPC的对话会流露出撕裂感。
- **衰减**：不会永远愤怒，时间会冲淡一切——除非又被激怒。
- **扩散**：NPC A的愤怒情绪可能影响旁边的NPC B。

**情绪实时驱动行为。** 同样一句"我要离开"，恐惧时的NPC会哀求，愤怒时的NPC会威胁，悲伤时的NPC会沉默。这不是脚本分支，是情绪系统自然涌现的结果。

**快速路径**：所有情绪计算走纯规则引擎，**<10ms完成**，不调LLM，不卡游戏主循环。只有对话生成才调LLM。你可以把情绪引擎跑在每帧Update里。

---

### 3. 实体关系图谱 —— NPC不是失忆的

你今天帮了铁匠，明天他记得你。你偷了酒馆老板的东西，下周全村都知道。

Neshama 用 **8种实体类型 × 15种关系类型** 构建了一个活的社交图谱。每条关系都带有强度和记忆关联——

- NPC记得你对它做过什么（记忆绑关系）
- 关系会随时间自然衰减或加深
- **BFS路径查询**：铁匠不认识你，但铁匠认识酒馆老板，酒馆老板认识你——铁匠会通过酒馆老板间接对你产生印象

这不是预制的剧情标记，是实时演算的关系网络。玩家的每一个行为都在这张网上投下涟漪。

---

### 4. NPC2NPC社交 —— NPC之间会发生什么？

这是大多数系统完全缺失的一环：**NPC之间有社交。**

Neshama 的NPC会——聊天、八卦、交易、结盟、背叛、安慰、教导、调情。**不需要玩家在场。** 你离线的时候，村里的NPC也在互相交流。

更狠的是**信息传播会失真**。铁匠跟酒馆老板说"那个冒险者救了我的猫"，传到村长耳朵里可能变成"那个冒险者杀了老虎"。传话游戏，真实得令人发笑。

**玩家的行为会通过NPC社交网络自然扩散。** 你不需要写"任务完成，全村民好感+5"这种硬编码——NPC自己会聊，消息自己会传，关系自己会变。

---

### 5. 情感驱动剧情 —— 不是你触发剧情，是情绪触发剧情

传统：玩家走到坐标(X,Y)，触发剧情节点C。

Neshama：NPC的情绪和关系状态满足了条件，剧情**自己发生**。

6种触发条件：情绪阈值 / 情绪组合 / 情绪变化 / 关系变化 / 多NPC共振 / 时间。

- **动态任务**：任务不是写死的。NPC悲伤时可能发布"帮我去祭奠亡妻"的任务，你之前杀了它的妻子——这个任务就是你的行为创造的。
- **世界事件**：一场战争爆发，多个NPC同时陷入恐惧，村庄进入戒严状态。不是一个脚本，是情绪共振的结果。

**脚本给你的是导演的剧本，情绪给你的是真实的生活。**

---

### 6. 记忆系统 —— 记住重要的，忘掉不重要的

三层渐进压缩：**L0原始记忆 → L1摘要 → L2深度洞察。**

你跟NPC说了一段话，L0完整记录。一天后，压缩成L1摘要——"他提到了北方的龙"。一周后，只保留L2洞察——"他是个危险的知情人"。

重要的对话保留细节，不重要的只留印象。**这就是人类的记忆方式。** 不是所有事都记住，但关键的事忘不了。

记忆直接影响对话和决策。NPC不是每次见面都像初次见面。

---

### 7. 语音系统 —— 情绪不只体现在文字里

5个TTS/STT Provider：ElevenLabs / Azure / OpenAI / Whisper / Piper。

核心亮点：**情绪→语音风格映射。** 同一个NPC，开心时语调上扬，愤怒时语速加快，悲伤时声音低沉。情绪引擎的输出直接驱动语音参数。

支持本地（Piper）和云端，你选。

---

## 三、有灵魂 vs 无灵魂：一张表说清楚

| 维度 | 传统NPC | Neshama NPC |
|------|---------|-------------|
| 人格 | 静态标签，千篇一律 | OCEAN五维，动态演化 |
| 情绪 | happy/angry开关 | 9维复合情绪，可叠加/冲突/衰减/扩散 |
| 关系 | 无，或硬编码好感度 | 实体图谱，15种关系类型，BFS路径查询 |
| 社交 | 只和玩家对话 | NPC2NPC自主社交，信息传播+失真 |
| 剧情 | 坐标/脚本触发 | 情绪/关系触发，动态任务生成 |
| 记忆 | 无，或简单对话历史 | 三层渐进压缩，影响决策 |
| 性能 | 全靠LLM（慢+贵） | 快速路径<10ms，情绪计算纯规则 |
| 声音 | 固定音色 | 情绪驱动语音风格 |

**一个有灵魂的NPC，不是更会聊天的NPC，而是你不和它说话它也在过自己生活的NPC。**

---

## 四、接入：5分钟给NPC接上灵魂

- **Unity SDK**：5238行C#，挂上 `NPCSoul` 组件即用
- **UE5 SDK**：19文件C++，Blueprint全支持
- **团结引擎**：零修改兼容（基于Unity 2022 LTS）
- **云API + WebSocket**：实时推送，开箱即用

不需要重写你的游戏架构。你的NPC还是那个NPC，只是它现在有了人格、情绪、记忆、关系和社交。

---

## 五、这不仅仅是一个工具

Neshama 的野心不是做一个更好的对话系统。**我们要改变的是NPC的设计范式。**

过去的20年，游戏图形从像素进化到了光线追踪，物理引擎从弹球进化到了实时流体模拟，音频从MIDI进化到了3D空间声。但NPC呢？还是脚本+状态机，还是那套2004年的技术。

我们相信下一个世代的游戏，标志不是画面更真实，而是**世界更真实**。而一个真实的世界里，每个角色都该有自己的灵魂。

**情绪是灵魂的操作系统。** Neshama 就是那层OS。

---

---

# Is Your NPC Alive?

---

## I. The Problem Everyone Pretends Not to See

You built an RPG. 100,000 words of dialogue, three continents of map, boss fights tuned forty times over. Players log in—

Beeline the main quest, skip dialogue, speedrun the boss, finish in 30 hours, uninstall.

Why? Because players figure it out early: **nobody in this world is alive except them.**

The blacksmith stands in the same spot every day, reciting the same line. The tavern keeper smiles forever, always welcoming. The kid at the village gate plays the same hide-and-seek from chapter one to the finale. You killed the village chief—nobody cares. You saved the world—the NPC still says "nice weather today."

The player isn't exploring a living world. They're flipping through a picture book they'll never open again.

**The NPC problem isn't whether AI is smart enough. It's whether they have a soul.**

Smart means answering questions. Soul means—trembling when afraid, losing control when angry, remembering betrayal, expressing affection clumsily, genuinely grieving when someone important is lost.

That's what Neshama is built to do.

---

## II. What Is a Soul System, Really?

Neshama isn't a dialogue plugin. It's not a ChatGPT wrapper. **It's a complete soul operating system for NPCs.**

If traditional NPCs are actors reading from a script—director calls action, they deliver lines; calls cut, they freeze—then Neshama gives that actor a personality, emotions, memories, and social ties, and lets them **walk onto the set and act on their own terms.**

Seven core modules, each solving a specific "why NPCs don't feel alive" problem:

---

### 1. Personality — Not a Reskinned Template

Traditional approach: slap a label on an NPC—"friendly merchant," "grumpy guard." Every "friendly merchant" is identical.

Neshama uses the **OCEAN Big Five model** (Openness/Conscientiousness/Extraversion/Agreeableness/Neuroticism) to generate a unique personality fingerprint for each NPC. Two merchants—both "friendly"—but one high in Openness (loves chatting about new things) and one high in Conscientiousness (meticulous and calculating). Completely different conversation experiences.

And critically: **personality isn't static.** A naive NPC who gets betrayed will see their Agreeableness drop and Neuroticism rise. What your player does to an NPC shapes who that NPC becomes. The world shapes the character; the character shapes the world.

---

### 2. Composite Emotion Engine — Emotion Is a River, Not a Switch

Most systems treat emotion as a tag: `happy = true`, `angry = false`. That's a switch, not an emotion.

Neshama implements **9 base emotions** (Joy/Trust/Fear/Surprise/Sadness/Disgust/Anger/Anticipation/Calm), and they—

- **Blend**: Sadness + Anger = Despair. Fear + Anticipation = Nervousness.
- **Conflict**: Love someone, but hate what they did—contradictory emotions coexist. The NPC's dialogue leaks that inner tension.
- **Decay**: No one stays angry forever—unless provoked again.
- **Spread**: NPC A's anger can influence nearby NPC B.

**Emotions drive behavior in real-time.** The same line—"I'm leaving"—draws a plea from a fearful NPC, a threat from an angry one, silence from a sad one. Not scripted branches—emergent outcomes from the emotion system.

**Fast Path**: All emotion computation runs through pure rule engine—**under 10ms**, no LLM calls, no frame drops. Only dialogue generation hits the LLM. You can run the emotion engine inside every Update tick.

---

### 3. Entity Relationship Graph — NPCs Don't Have Amnesia

You helped the blacksmith today, he remembers tomorrow. You stole from the tavern keeper, the whole village knows by next week.

Neshama builds a living social graph with **8 entity types × 15 relationship types**. Every relationship carries intensity and memory associations—

- NPCs remember what you did to them (memory-bound relationships)
- Relationships naturally decay or deepen over time
- **BFS path queries**: The blacksmith doesn't know you, but he knows the tavern keeper, who knows you—the blacksmith forms an indirect impression through the grapevine

No pre-baked plot markers. A real-time computed relationship network. Every player action sends ripples across this web.

---

### 4. NPC2NPC Social — What Happens Between NPCs?

The blind spot in almost every system: **NPCs have social lives with each other.**

Neshama's NPCs chat, gossip, trade, form alliances, betray, comfort, teach, flirt. **No player required.** While you're offline, village NPCs are still talking to each other.

Even better: **information distorts as it propagates.** The blacksmith tells the tavern keeper "that adventurer saved my cat." By the time it reaches the village chief, it's "that adventurer killed a tiger." Telephone game, hilariously authentic.

**Player actions spread naturally through the NPC social network.** No need for hardcoded "quest complete, all villager affinity +5"—NPCs talk, news travels, relationships shift. Organically.

---

### 5. Emotion-Driven Storytelling — Emotions Trigger Stories, Not Scripts

Traditional: Player walks to coordinate (X,Y), triggers story node C.

Neshama: An NPC's emotional and relational state meets a condition, and the story **emerges on its own.**

Six trigger types: Emotion threshold / Emotion combination / Emotion change / Relationship change / Multi-NPC resonance / Time.

- **Dynamic quests**: Not scripted. A grieving NPC might post a quest "help me mourn my late wife"—and if you killed her, that quest is a consequence you created.
- **World events**: War breaks out, multiple NPCs enter fear simultaneously, the village goes into lockdown. Not a script—an emotional resonance cascade.

**Scripts give you a director's screenplay. Emotions give you real life.**

---

### 6. Memory — Remember What Matters, Forget What Doesn't

Three-layer progressive compression: **L0 raw memory → L1 summary → L2 deep insight.**

You tell an NPC something. L0 records it verbatim. A day later, compressed to L1: "He mentioned a dragon in the north." A week later, only L2 remains: "He's a dangerous informant."

Important conversations retain detail. Unimportant ones fade to impressions. **That's how human memory works.** Not everything is remembered, but the critical things are unforgettable.

Memory directly influences dialogue and decisions. NPCs don't greet you like a stranger every single time.

---

### 7. Voice — Emotion Lives Beyond Text

5 TTS/STT providers: ElevenLabs / Azure / OpenAI / Whisper / Piper.

Key feature: **Emotion-to-voice-style mapping.** Same NPC—pitch rises when joyful, pace quickens when angry, tone drops when sorrowful. Emotion engine output directly drives voice parameters.

Local (Piper) or cloud—your call.

---

## III. With Soul vs. Without: One Table Tells the Story

| Dimension | Traditional NPC | Neshama NPC |
|-----------|----------------|-------------|
| Personality | Static label, one-size-fits-all | OCEAN Big Five, dynamically evolving |
| Emotion | happy/angry toggle | 9-dimensional composite, blendable/conflicting/decaying/spreading |
| Relationships | None, or hardcoded affinity | Entity graph, 15 relationship types, BFS path queries |
| Social | Only talks to the player | NPC2NPC autonomous socializing, info propagation + distortion |
| Storytelling | Coordinate/script triggers | Emotion/relationship triggers, dynamic quest generation |
| Memory | None, or raw chat history | 3-layer progressive compression, decision-influencing |
| Performance | All LLM (slow + expensive) | Fast path <10ms, emotion via pure rules |
| Voice | Fixed tone | Emotion-driven voice style |

**An NPC with a soul isn't one that chats better. It's one that lives its own life even when you're not talking to it.**

---

## IV. Integration: Give Your NPC a Soul in 5 Minutes

- **Unity SDK**: 5,238 lines of C#, just attach the `NPCSoul` component
- **UE5 SDK**: 19 C++ files, full Blueprint support
- **Tuanjie Engine**: Zero-modification compatibility (based on Unity 2022 LTS)
- **Cloud API + WebSocket**: Real-time push, plug and play

No need to rewrite your game architecture. Your NPC is still your NPC—it just now has personality, emotion, memory, relationships, and a social life.

---

## V. More Than a Tool

Neshama's ambition isn't to build a better dialogue system. **We want to change the NPC design paradigm.**

Over the past 20 years, game graphics evolved from pixels to ray tracing, physics engines from pinball to real-time fluid simulation, audio from MIDI to 3D spatial sound. But NPCs? Still scripts + state machines. Still the same tech from 2004.

We believe the next generation of games won't be defined by more realistic graphics, but by **more realistic worlds**. And in a real world, every character has a soul of their own.

**Emotion is the operating system of the soul.** Neshama is that OS.
