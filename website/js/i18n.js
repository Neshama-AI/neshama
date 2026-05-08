// Neshama i18n — Bilingual (EN/ZH) translation system
// No frameworks. Pure JS. localStorage persistence.

(function() {
  'use strict';

  var STORAGE_KEY = 'neshama-lang';

  var translations = {
    en: {
      // ---- Navigation ----
      'nav.features': 'Features',
      'nav.howItWorks': 'How it works',
      'nav.docs': 'Docs',
      'nav.pricing': 'Pricing',
      'nav.getStarted': 'Get Started',

      // ---- Hero ----
      'hero.badge': 'Apache 2.0 · Self-hostable',
      'hero.title': 'Give your NPCs a soul.<br>Not a script.',
      'hero.subtitle': 'Neshama is a soul engine that runs inside your game. Emotions, memory, personality, social relationships — all local, all real-time.',
      'hero.cta.primary': 'Get Started',
      'hero.cta.secondary': 'See the difference',

      // ---- Claims ----
      'claims.label': 'Core claims',
      'claims.title': 'Three things you can verify.',
      'claims.desc': 'No marketing spin. Each claim is testable in under 5 minutes.',
      'claim1.metric': 'Runs in your game, not on our server',
      'claim1.title': 'Local-first soul engine',
      'claim1.desc': 'The emotion engine runs in your game process. Emotions update every frame. No server dependency. Works offline. Your players never hit a cloud endpoint just to feel something.',
      'claim2.metric': '< 10ms. Every frame.',
      'claim2.title': 'Rule-based emotion calculation',
      'claim2.desc': 'Pure rule-based emotion engine. No LLM calls for emotions. Only dialogue generation needs AI. The math is deterministic, testable, and fast enough to run per-frame.',
      'claim3.metric': '3 lines of code',
      'claim3.title': 'Integration under 5 minutes',
      'claim3.desc': 'Create a soul, subscribe to emotion changes, start chatting. That\'s the entire API surface. No config files, no dashboards to configure, no schema to learn.',

      // ---- Compare ----
      'compare.label': 'Side by side',
      'compare.title': 'Same scene. Different soul.',
      'compare.desc': 'Player insults the tavern keeper, then comes back 3 game-days later. Watch what happens.',
      'compare.without': 'Without Neshama',
      'compare.with': 'With Neshama',
      'compare.later': '...3 game-days later...',

      // ---- Architecture ----
      'arch.label': 'Under the hood',
      'arch.title': 'How a soul is built.',
      'arch.desc': 'Five subsystems. One deterministic core. Only dialogue generation touches an LLM.',

      // ---- Integrations ----
      'integrations.label': 'Integrations',
      'integrations.title': 'Drop into your engine.',
      'integrations.desc': 'Native packages for major game engines. REST API for everything else.',

      // ---- Pricing Preview (index page) ----
      'pricing.label': 'Pricing',
      'pricing.preview.title': 'Start free. Scale when ready.',
      'pricing.preview.desc': 'Free tier includes 3 NPC souls. Bring your own LLM key, conversations are unlimited.',
      'pricing.free.name': 'Free',
      'pricing.free.desc': 'Prototype and learn',
      'pricing.free.f1': '3 NPC souls',
      'pricing.free.f2': '5,000 emotion calculations/mo',
      'pricing.free.f3': 'L0 working memory',
      'pricing.free.f4': 'Static OCEAN traits',
      'pricing.free.f5': 'BYOK = unlimited dialogue',
      'pricing.indie.name': 'Indie',
      'pricing.indie.desc': 'Ship your indie game',
      'pricing.indie.f1': '10 NPC souls',
      'pricing.indie.f2': '50,000 emotion calculations/mo',
      'pricing.indie.f3': 'L0 + L1 memory',
      'pricing.indie.f4': 'Dynamic personality evolution',
      'pricing.indie.f5': 'Community support',
      'pricing.studio.name': 'Studio',
      'pricing.studio.desc': 'Mid-size studios',
      'pricing.studio.f1': '50 NPC souls',
      'pricing.studio.f2': '500,000 emotion calculations/mo',
      'pricing.studio.f3': 'L0 + L1 + L2 full memory',
      'pricing.studio.f4': 'Entity graph & social engine',
      'pricing.studio.f5': 'Priority support',
      'pricing.enterprise.name': 'Enterprise',
      'pricing.enterprise.desc': 'AAA & platforms',
      'pricing.enterprise.f1': 'Unlimited NPC souls',
      'pricing.enterprise.f2': 'Unlimited calculations',
      'pricing.enterprise.f3': 'Custom memory hierarchies',
      'pricing.enterprise.f4': 'On-premise deployment',
      'pricing.enterprise.f5': 'SLA & dedicated support',
      'pricing.startTrial': 'Start Trial',
      'pricing.contactUs': 'Contact Us',
      'pricing.byokNote': '<code>BYOK</code> = Bring Your Own Key. Use any of 21 LLM providers. You pay the model provider directly — we don\'t add markup.',

      // ---- CTA ----
      'cta.title': 'Ship NPCs worth talking to.',
      'cta.desc': 'Open source. Self-hostable. Free to start. 3 lines of code.',
      'cta.primary': 'Get Started',
      'cta.secondary': 'Read the Docs',

      // ---- Footer ----
      'footer.desc': 'The soul engine for game NPCs. Open source under Apache 2.0.',
      'footer.product': 'Product',
      'footer.developers': 'Developers',
      'footer.community': 'Community',
      'footer.legal': 'Legal',
      'footer.features': 'Features',
      'footer.pricing': 'Pricing',
      'footer.documentation': 'Documentation',
      'footer.howItWorks': 'How it works',
      'footer.quickStart': 'Quick Start',
      'footer.apiReference': 'API Reference',
      'footer.privacyPolicy': 'Privacy Policy',
      'footer.termsOfService': 'Terms of Service',
      'footer.copyright': '© 2026 Neshama. Built in the open.',

      // ---- Pricing Page ----
      'pricing.page.title': 'Free + BYOK = Unlimited dialogue.',
      'pricing.page.desc': 'The soul engine is free to start. Bring your own LLM key and pay the provider directly — we don\'t add markup.',
      'pricing.page.free.desc': 'Prototype and learn. No credit card required.',
      'pricing.page.free.f1': '3 NPC souls',
      'pricing.page.free.f2': '5,000 emotion calculations/mo',
      'pricing.page.free.f3': 'L0 working memory only',
      'pricing.page.free.f4': 'Static OCEAN traits (no evolution)',
      'pricing.page.free.f5': 'BYOK: unlimited dialogue',
      'pricing.page.free.f6': 'Community support',
      'pricing.page.indie.desc': 'Ship your indie game with living NPCs.',
      'pricing.page.indie.f1': '10 NPC souls',
      'pricing.page.indie.f2': '50,000 emotion calculations/mo',
      'pricing.page.indie.f3': 'L0 + L1 summarized memory',
      'pricing.page.indie.f4': 'Dynamic personality evolution',
      'pricing.page.indie.f5': 'BYOK: unlimited dialogue',
      'pricing.page.indie.f6': 'Community support',
      'pricing.page.studio.desc': 'For studios shipping multiple titles.',
      'pricing.page.studio.f1': '50 NPC souls',
      'pricing.page.studio.f2': '500,000 emotion calculations/mo',
      'pricing.page.studio.f3': 'L0 + L1 + L2 full memory',
      'pricing.page.studio.f4': 'Entity graph & social engine',
      'pricing.page.studio.f5': 'NPC2NPC relationships',
      'pricing.page.studio.f6': 'Priority email support',
      'pricing.page.enterprise.desc': 'AAA studios and platforms.',
      'pricing.page.enterprise.f1': 'Unlimited NPC souls',
      'pricing.page.enterprise.f2': 'Unlimited emotion calculations',
      'pricing.page.enterprise.f3': 'Custom memory hierarchies',
      'pricing.page.enterprise.f4': 'On-premise deployment',
      'pricing.page.enterprise.f5': 'Data residency options',
      'pricing.page.enterprise.f6': 'SLA & dedicated support',
      'pricing.page.startTrial': 'Start Free Trial',
      'pricing.page.byokNote': '<code>BYOK</code> = Bring Your Own Key. Use any of 21 LLM providers (OpenAI, Anthropic, DeepSeek, etc.). You pay the model provider directly — zero markup from us.',
      'pricing.page.emotionNote': '<code>Emotion calculation</code> = One emotion update cycle (stimulus → emotion evaluation → decay → conflict resolution). This is the core compute cost. Dialogue generation is separate and uses your own LLM key.',

      // ---- Comparison Table (pricing page) ----
      'compare.table.title': 'What\'s in each tier.',
      'compare.table.feature': 'Feature',
      'compare.table.npcSouls': 'NPC Souls',
      'compare.table.emotionCalc': 'Emotion Calculations/mo',
      'compare.table.l0': 'L0 Working Memory',
      'compare.table.l1': 'L1 Summarized Memory',
      'compare.table.l2': 'L2 Core Memory',
      'compare.table.personality': 'Personality Evolution',
      'compare.table.entityGraph': 'Entity Graph',
      'compare.table.npc2npc': 'NPC2NPC Social Engine',
      'compare.table.byok': 'BYOK Dialogue',
      'compare.table.selfHost': 'Self-hostable',
      'compare.table.support': 'Support',
      'compare.table.static': 'Static',
      'compare.table.dynamic': 'Dynamic',
      'compare.table.custom': 'Custom',
      'compare.table.community': 'Community',
      'compare.table.priority': 'Priority',
      'compare.table.dedicated': 'Dedicated',
      'compare.table.unlimited': 'Unlimited',

      // ---- FAQ (pricing page) ----
      'faq.title': 'Frequently asked questions.',
      'faq.q1': 'What happens when I hit the emotion calculation limit?',
      'faq.a1': 'The NPC still functions — it just stops updating emotions until the next billing cycle. Dialogue still works (since that uses your own LLM key). The NPC effectively "freezes" its emotional state.',
      'faq.q2': 'What does "BYOK" mean exactly?',
      'faq.a2': 'Bring Your Own Key. You provide your own API key from OpenAI, Anthropic, DeepSeek, or any of our 21 supported providers. We never see your key, and we don\'t add any markup to the model provider\'s pricing. Dialogue costs are between you and the model provider.',
      'faq.q3': 'Can I self-host instead of using the cloud?',
      'faq.a3': 'Yes. Neshama is Apache 2.0 licensed. You can run the entire engine locally or on your own infrastructure. The self-hosted version has no emotion calculation limits. Paid tiers add cloud convenience, managed updates, and support.',
      'faq.q4': 'Why price by "emotion calculations" instead of API calls?',
      'faq.a4': 'Because the emotion engine is what we run on our servers. Each calculation involves: stimulus evaluation, emotion update, decay processing, conflict resolution, and threshold checks. This is the actual compute cost. Dialogue generation uses your own LLM key, so we don\'t charge for that.',
      'faq.q5': 'What\'s the difference between static and dynamic OCEAN traits?',
      'faq.a5': 'Free tier NPCs have fixed personality traits — the OCEAN values you set at creation stay the same forever. Paid tiers unlock dynamic evolution: a repeatedly bullied NPC\'s agreeableness decreases, a praised NPC\'s extraversion increases. This makes NPCs feel alive across sessions.',
      'faq.q6': 'Do I need a separate soul for each NPC?',
      'faq.a6': 'Yes. Each NPC soul has its own personality, emotions, memories, and entity graph. This is what makes each NPC unique. Two tavern keepers with the same preset will diverge over time based on their different experiences.',

      // ---- CTA (pricing page) ----
      'pricing.cta.title': 'Start building souls today.',
      'pricing.cta.desc': '3 NPC souls, free forever. No credit card required.',
      'pricing.cta.primary': 'Get Started',
      'pricing.cta.secondary': 'View on GitHub',

      // ---- Docs Page ----
      'docs.search': 'Search docs...',
      'docs.gettingStarted': 'Getting Started',
      'docs.quickStart': 'Quick Start',
      'docs.installation': 'Installation',
      'docs.unityIntegration': 'Unity Integration',
      'docs.ue5Integration': 'UE5 Integration',
      'docs.coreSystems': 'Core Systems',
      'docs.emotionSystem': 'Emotion System',
      'docs.personalityOCEAN': 'Personality (OCEAN)',
      'docs.memorySystem': 'Memory System',
      'docs.socialEngine': 'Social Engine',
      'docs.apiReference': 'API Reference',
      'docs.apiNpcSoul': 'NPCSoul',
      'docs.apiEmotion': 'CompositeEmotion',
      'docs.apiMemory': 'MemoryManager',
      'docs.apiEntity': 'EntityGraph',
      'docs.guides': 'Guides',
      'docs.soulPresets': 'Soul Presets',
      'docs.llmSetup': 'LLM Provider Setup',
      'docs.selfHosting': 'Self-Hosting',

      // Docs content
      'docs.h1': 'Quick Start',
      'docs.intro': 'Get a soul running in under 5 minutes. No account needed. No credit card. Just Python.',
      'docs.installOrWeb': 'Or install with the web dashboard:',
      'docs.createSoul': 'Create your first soul',
      'docs.unityInstall': 'Install the Neshama Unity package from the Asset Store or via Git URL:',
      'docs.unityThen': 'Then in your NPC MonoBehaviour:',
      'docs.ue5Install': 'The Neshama UE5 plugin is available on the Unreal Marketplace. Add it to your project, then:',
      'docs.emotionIntro': 'Neshama uses a composite emotion model based on 8 primary emotions and 15 composite recipes. All calculations are rule-based and deterministic — no LLM calls needed.',
      'docs.primaryEmotions': 'Primary Emotions',
      'docs.compositeRecipes': 'Composite Recipes (examples)',
      'docs.emotionPerf': 'Each emotion has decay curves, conflict resolution, and threshold-based behavior triggers. The entire calculation takes <1ms per NPC per frame.',
      'docs.personalityIntro': 'The Five-Factor personality model determines how each NPC responds to stimuli:',
      'docs.openness': 'Openness',
      'docs.opennessDesc': 'Creativity, curiosity, aesthetic sensitivity',
      'docs.conscientiousness': 'Conscientiousness',
      'docs.conscientiousnessDesc': 'Self-discipline, organization, reliability',
      'docs.extraversion': 'Extraversion',
      'docs.extraversionDesc': 'Sociability, assertiveness, positive emotions',
      'docs.agreeableness': 'Agreeableness',
      'docs.agreeablenessDesc': 'Cooperation, trust, altruism',
      'docs.neuroticism': 'Neuroticism',
      'docs.neuroticismDesc': 'Emotional instability, anxiety, moodiness',
      'docs.oceanEvolve': 'In paid tiers, OCEAN traits evolve dynamically based on the NPC\'s experiences. A repeatedly insulted NPC\'s agreeableness decreases over time.',
      'docs.memoryIntro': 'Three-tier progressive summarization, inspired by human memory:',
      'docs.l0': 'L0 — Working Memory',
      'docs.l0Desc': 'The last N interactions. Available on Free tier.',
      'docs.l1': 'L1 — Summarized Memory',
      'docs.l1Desc': 'Automatic consolidation of L0 into summaries. Available on Indie tier.',
      'docs.l2': 'L2 — Core Memory',
      'docs.l2Desc': 'Permanent, identity-defining memories. Available on Studio tier.',
      'docs.memoryGoldfish': 'Without L2, NPCs are "goldfish" — they forget important events within a session. L2 memories persist across sessions and shape the NPC\'s personality.',
      'docs.socialIntro': 'The Entity Graph tracks relationships between NPCs and the world:',
      'docs.entityTypes': '8 entity types',
      'docs.entityTypesDesc': 'Person, Organization, Location, Concept, Event, Object, Media, Topic',
      'docs.relationTypes': '15 relation types',
      'docs.relationTypesDesc': 'KNOWS, WORKS_FOR, LOCATED_IN, PART_OF, SIMILAR_TO, etc.',
      'docs.socialBehavior': 'NPCs can form opinions about other NPCs, spread information through social networks, and modify their behavior based on group dynamics.',
      'docs.presetsIntro': 'Neshama ships with built-in soul presets for common NPC archetypes:',
      'docs.preset.tavern': 'tavern_keeper',
      'docs.preset.tavernDesc': 'Gregarious, observant, loyal to regulars',
      'docs.preset.quest': 'quest_giver',
      'docs.preset.questDesc': 'Authoritative, mysterious, guarded',
      'docs.preset.merchant': 'merchant',
      'docs.preset.merchantDesc': 'Shrewd, persuasive, status-conscious',
      'docs.preset.guard': 'guard',
      'docs.preset.guardDesc': 'Rigid, suspicious, duty-bound',
      'docs.preset.healer': 'healer',
      'docs.preset.healerDesc': 'Compassionate, patient, wise',
      'docs.customPreset': 'You can also create custom presets:',
      'docs.llmIntro': 'Neshama supports 21 LLM providers with a unified API. Only dialogue generation uses the LLM — emotions are rule-based.',
      'docs.llmProviders': 'Supported providers include: OpenAI, Anthropic, Google Gemini, DeepSeek, Groq, Mistral, and 15 more. See the full list on GitHub.',
      'docs.selfhostIntro': 'Neshama is Apache 2.0 licensed. Run it yourself:',
      'docs.dockerDeploy': 'Or deploy with Docker:',

      // ---- Language toggle ----
      'lang.toggle': '中文'
    },

    zh: {
      // ---- Navigation ----
      'nav.features': '功能',
      'nav.howItWorks': '工作原理',
      'nav.docs': '文档',
      'nav.pricing': '定价',
      'nav.getStarted': '开始使用',

      // ---- Hero ----
      'hero.badge': 'Apache 2.0 · 可自部署',
      'hero.title': '给NPC灵魂，而不是脚本。',
      'hero.subtitle': 'Neshama 是运行在你游戏内的灵魂引擎。情绪、记忆、人格、社交关系——全部本地计算，全部实时响应。',
      'hero.cta.primary': '开始使用',
      'hero.cta.secondary': '看效果',

      // ---- Claims ----
      'claims.label': '核心主张',
      'claims.title': '三件事，你可以亲自验证。',
      'claims.desc': '没有营销话术。每条主张5分钟内可验证。',
      'claim1.metric': '跑在你的游戏里，不是我们的服务器上',
      'claim1.title': '本地优先的灵魂引擎',
      'claim1.desc': '情绪引擎运行在你的游戏进程里。情绪每帧更新。不依赖服务器。断网也能用。你的玩家不需要访问任何云端接口就能感受到情绪。',
      'claim2.metric': '< 10ms。每帧。',
      'claim2.title': '规则驱动的情绪计算',
      'claim2.desc': '纯规则驱动的情绪引擎。情绪计算不需要调LLM。只有对话生成需要AI。数学是确定性的、可测试的、快到可以逐帧运行。',
      'claim3.metric': '3行代码',
      'claim3.title': '5分钟内集成',
      'claim3.desc': '创建灵魂、订阅情绪变化、开始对话。这就是全部API。没有配置文件，没有控制面板要调，没有新的数据模式要学。',

      // ---- Compare ----
      'compare.label': '对比',
      'compare.title': '同样的场景，不同的灵魂。',
      'compare.desc': '玩家骂了酒馆老板，3个游戏日后回来。看看会发生什么。',
      'compare.without': '没有 Neshama',
      'compare.with': '有 Neshama',
      'compare.later': '...3个游戏日后...',

      // ---- Architecture ----
      'arch.label': '内部架构',
      'arch.title': '灵魂是怎么构成的。',
      'arch.desc': '五个子系统。一个确定性核心。只有对话生成会用LLM。',

      // ---- Integrations ----
      'integrations.label': '集成',
      'integrations.title': '接入你的引擎。',
      'integrations.desc': '主流游戏引擎原生支持。其他平台用REST API。',

      // ---- Pricing Preview (index page) ----
      'pricing.label': '定价',
      'pricing.preview.title': '免费起步，按需扩展。',
      'pricing.preview.desc': '免费版包含3个NPC灵魂。自带LLM Key，对话不限量。',
      'pricing.free.name': '免费',
      'pricing.free.desc': '原型开发和学习',
      'pricing.free.f1': '3个NPC灵魂',
      'pricing.free.f2': '5,000次情绪计算/月',
      'pricing.free.f3': 'L0工作记忆',
      'pricing.free.f4': '静态OCEAN特质',
      'pricing.free.f5': 'BYOK = 无限对话',
      'pricing.indie.name': '独立开发者',
      'pricing.indie.desc': '为你的独立游戏打造活NPC',
      'pricing.indie.f1': '10个NPC灵魂',
      'pricing.indie.f2': '50,000次情绪计算/月',
      'pricing.indie.f3': 'L0 + L1记忆',
      'pricing.indie.f4': '动态人格进化',
      'pricing.indie.f5': '社区支持',
      'pricing.studio.name': '工作室',
      'pricing.studio.desc': '中等规模工作室',
      'pricing.studio.f1': '50个NPC灵魂',
      'pricing.studio.f2': '500,000次情绪计算/月',
      'pricing.studio.f3': 'L0 + L1 + L2完整记忆',
      'pricing.studio.f4': '实体图谱 & 社交引擎',
      'pricing.studio.f5': '优先支持',
      'pricing.enterprise.name': '企业版',
      'pricing.enterprise.desc': '3A和平台',
      'pricing.enterprise.f1': '无限NPC灵魂',
      'pricing.enterprise.f2': '无限计算量',
      'pricing.enterprise.f3': '自定义记忆层级',
      'pricing.enterprise.f4': '私有化部署',
      'pricing.enterprise.f5': 'SLA & 专属支持',
      'pricing.startTrial': '免费试用',
      'pricing.contactUs': '联系我们',
      'pricing.byokNote': '<code>BYOK</code> = 自带Key。支持21家LLM供应商。你直接向模型供应商付费——我们不加价。',

      // ---- CTA ----
      'cta.title': '做出值得对话的NPC。',
      'cta.desc': '开源。可自部署。免费起步。3行代码。',
      'cta.primary': '开始使用',
      'cta.secondary': '阅读文档',

      // ---- Footer ----
      'footer.desc': '游戏NPC的灵魂引擎。Apache 2.0开源协议。',
      'footer.product': '产品',
      'footer.developers': '开发者',
      'footer.community': '社区',
      'footer.legal': '法律',
      'footer.features': '功能',
      'footer.pricing': '定价',
      'footer.documentation': '文档',
      'footer.howItWorks': '工作原理',
      'footer.quickStart': '快速开始',
      'footer.apiReference': 'API参考',
      'footer.privacyPolicy': '隐私政策',
      'footer.termsOfService': '服务条款',
      'footer.copyright': '© 2026 Neshama. 开源构建。',

      // ---- Pricing Page ----
      'pricing.page.title': '免费 + BYOK = 无限对话。',
      'pricing.page.desc': '灵魂引擎免费起步。自带LLM Key，直接向供应商付费——我们不加价。',
      'pricing.page.free.desc': '原型开发和学习。无需信用卡。',
      'pricing.page.free.f1': '3个NPC灵魂',
      'pricing.page.free.f2': '5,000次情绪计算/月',
      'pricing.page.free.f3': '仅L0工作记忆',
      'pricing.page.free.f4': '静态OCEAN特质（无进化）',
      'pricing.page.free.f5': 'BYOK：无限对话',
      'pricing.page.free.f6': '社区支持',
      'pricing.page.indie.desc': '为你的独立游戏打造活NPC。',
      'pricing.page.indie.f1': '10个NPC灵魂',
      'pricing.page.indie.f2': '50,000次情绪计算/月',
      'pricing.page.indie.f3': 'L0 + L1摘要记忆',
      'pricing.page.indie.f4': '动态人格进化',
      'pricing.page.indie.f5': 'BYOK：无限对话',
      'pricing.page.indie.f6': '社区支持',
      'pricing.page.studio.desc': '多项目工作室。',
      'pricing.page.studio.f1': '50个NPC灵魂',
      'pricing.page.studio.f2': '500,000次情绪计算/月',
      'pricing.page.studio.f3': 'L0 + L1 + L2完整记忆',
      'pricing.page.studio.f4': '实体图谱 & 社交引擎',
      'pricing.page.studio.f5': 'NPC2NPC关系',
      'pricing.page.studio.f6': '优先邮件支持',
      'pricing.page.enterprise.desc': '3A工作室和平台。',
      'pricing.page.enterprise.f1': '无限NPC灵魂',
      'pricing.page.enterprise.f2': '无限情绪计算',
      'pricing.page.enterprise.f3': '自定义记忆层级',
      'pricing.page.enterprise.f4': '私有化部署',
      'pricing.page.enterprise.f5': '数据驻留选项',
      'pricing.page.enterprise.f6': 'SLA & 专属支持',
      'pricing.page.startTrial': '免费试用',
      'pricing.page.byokNote': '<code>BYOK</code> = 自带Key。支持21家LLM供应商（OpenAI、Anthropic、DeepSeek等）。你直接向模型供应商付费——我们零加价。',
      'pricing.page.emotionNote': '<code>情绪计算</code> = 一次完整的情绪更新周期（刺激 → 情绪评估 → 衰减 → 冲突解决）。这是核心计算成本。对话生成独立计费，使用你自己的LLM Key。',

      // ---- Comparison Table (pricing page) ----
      'compare.table.title': '各版本功能对比。',
      'compare.table.feature': '功能',
      'compare.table.npcSouls': 'NPC灵魂数',
      'compare.table.emotionCalc': '情绪计算/月',
      'compare.table.l0': 'L0工作记忆',
      'compare.table.l1': 'L1摘要记忆',
      'compare.table.l2': 'L2核心记忆',
      'compare.table.personality': '人格进化',
      'compare.table.entityGraph': '实体图谱',
      'compare.table.npc2npc': 'NPC2NPC社交引擎',
      'compare.table.byok': 'BYOK对话',
      'compare.table.selfHost': '可自部署',
      'compare.table.support': '支持',
      'compare.table.static': '静态',
      'compare.table.dynamic': '动态',
      'compare.table.custom': '自定义',
      'compare.table.community': '社区',
      'compare.table.priority': '优先',
      'compare.table.dedicated': '专属',
      'compare.table.unlimited': '无限',

      // ---- FAQ (pricing page) ----
      'faq.title': '常见问题。',
      'faq.q1': '超过情绪计算上限会怎样？',
      'faq.a1': 'NPC仍然可以工作——只是停止更新情绪，直到下一个计费周期。对话仍然可用（因为用的是你自己的LLM Key）。NPC的情绪状态会"冻结"。',
      'faq.q2': 'BYOK到底是什么意思？',
      'faq.a2': '自带Key。你提供自己的API Key，可以从OpenAI、Anthropic、DeepSeek等21家支持的供应商中选择。我们不会看到你的Key，也不会在模型供应商的价格上加价。对话费用直接在你和模型供应商之间结算。',
      'faq.q3': '可以自部署而不用云服务吗？',
      'faq.a3': '可以。Neshama采用Apache 2.0协议。你可以在本地或自己的基础设施上运行整个引擎。自部署版本没有情绪计算限制。付费版本增加了云端便利、托管更新和技术支持。',
      'faq.q4': '为什么按"情绪计算"而不是API调用计费？',
      'faq.a4': '因为情绪引擎是我们服务器上运行的部分。每次计算包括：刺激评估、情绪更新、衰减处理、冲突解决和阈值检查。这才是实际的计算成本。对话生成使用你自己的LLM Key，所以我们不对此收费。',
      'faq.q5': '静态和动态OCEAN特质有什么区别？',
      'faq.a5': '免费版NPC的人格特质是固定的——创建时设置的OCEAN值永远不会变。付费版解锁动态进化：被反复欺负的NPC宜人性会降低，被表扬的NPC外向性会提高。这让NPC跨会话时感觉是活的。',
      'faq.q6': '每个NPC需要单独的灵魂吗？',
      'faq.a6': '是的。每个NPC灵魂有自己的人格、情绪、记忆和实体图谱。这正是让每个NPC独一无二的原因。两个使用相同预设的酒馆老板，会因为不同的经历随时间分化。',

      // ---- CTA (pricing page) ----
      'pricing.cta.title': '今天就开始构建灵魂。',
      'pricing.cta.desc': '3个NPC灵魂，永久免费。无需信用卡。',
      'pricing.cta.primary': '开始使用',
      'pricing.cta.secondary': '查看 GitHub',

      // ---- Docs Page ----
      'docs.search': '搜索文档...',
      'docs.gettingStarted': '入门指南',
      'docs.quickStart': '快速开始',
      'docs.installation': '安装',
      'docs.unityIntegration': 'Unity集成',
      'docs.ue5Integration': 'UE5集成',
      'docs.coreSystems': '核心系统',
      'docs.emotionSystem': '情绪引擎',
      'docs.personalityOCEAN': '人格 (OCEAN)',
      'docs.memorySystem': '记忆系统',
      'docs.socialEngine': '社交引擎',
      'docs.apiReference': 'API参考',
      'docs.apiNpcSoul': 'NPCSoul',
      'docs.apiEmotion': 'CompositeEmotion',
      'docs.apiMemory': 'MemoryManager',
      'docs.apiEntity': 'EntityGraph',
      'docs.guides': '集成指南',
      'docs.soulPresets': '灵魂预设',
      'docs.llmSetup': 'LLM供应商配置',
      'docs.selfHosting': '自部署',

      // Docs content
      'docs.h1': '快速开始',
      'docs.intro': '5分钟内运行一个灵魂。无需账号。无需信用卡。只需要Python。',
      'docs.installOrWeb': '或安装带Web控制面板的版本：',
      'docs.createSoul': '创建你的第一个灵魂',
      'docs.unityInstall': '从Asset Store或通过Git URL安装Neshama Unity包：',
      'docs.unityThen': '然后在你的NPC MonoBehaviour中：',
      'docs.ue5Install': 'Neshama UE5插件可在Unreal Marketplace获取。添加到你的项目后：',
      'docs.emotionIntro': 'Neshama使用基于8种基础情绪和15种复合配方的复合情绪模型。所有计算都是规则驱动和确定性的——不需要调用LLM。',
      'docs.primaryEmotions': '基础情绪',
      'docs.compositeRecipes': '复合配方（示例）',
      'docs.emotionPerf': '每种情绪都有衰减曲线、冲突解决和基于阈值的行为触发。整个计算耗时<1ms/NPC/帧。',
      'docs.personalityIntro': '五因素人格模型决定每个NPC如何响应刺激：',
      'docs.openness': '开放性',
      'docs.opennessDesc': '创造力、好奇心、审美敏感度',
      'docs.conscientiousness': '尽责性',
      'docs.conscientiousnessDesc': '自律、条理性、可靠性',
      'docs.extraversion': '外向性',
      'docs.extraversionDesc': '社交性、果断性、积极情绪',
      'docs.agreeableness': '宜人性',
      'docs.agreeablenessDesc': '合作、信任、利他',
      'docs.neuroticism': '神经质',
      'docs.neuroticismDesc': '情绪不稳定、焦虑、多愁善感',
      'docs.oceanEvolve': '付费版中，OCEAN特质会根据NPC的经历动态进化。被反复辱骂的NPC宜人性会随时间降低。',
      'docs.memoryIntro': '三层渐进式摘要，灵感来自人类记忆：',
      'docs.l0': 'L0 — 工作记忆',
      'docs.l0Desc': '最近N次交互。免费版可用。',
      'docs.l1': 'L1 — 摘要记忆',
      'docs.l1Desc': '自动将L0整合为摘要。独立开发者版可用。',
      'docs.l2': 'L2 — 核心记忆',
      'docs.l2Desc': '永久的、定义身份的记忆。工作室版可用。',
      'docs.memoryGoldfish': '没有L2，NPC就是"金鱼"——它们会在一个会话内忘记重要事件。L2记忆跨会话持久保存，并塑造NPC的人格。',
      'docs.socialIntro': '实体图谱追踪NPC与世界之间的关系：',
      'docs.entityTypes': '8种实体类型',
      'docs.entityTypesDesc': '人物、组织、地点、概念、事件、物品、媒体、主题',
      'docs.relationTypes': '15种关系类型',
      'docs.relationTypesDesc': 'KNOWS、WORKS_FOR、LOCATED_IN、PART_OF、SIMILAR_TO等',
      'docs.socialBehavior': 'NPC可以对其他NPC形成看法，通过社交网络传播信息，并根据群体动态调整行为。',
      'docs.presetsIntro': 'Neshama内置了常见NPC原型的灵魂预设：',
      'docs.preset.tavern': 'tavern_keeper',
      'docs.preset.tavernDesc': '热情好客、善于观察、对常客忠诚',
      'docs.preset.quest': 'quest_giver',
      'docs.preset.questDesc': '威严、神秘、有所保留',
      'docs.preset.merchant': 'merchant',
      'docs.preset.merchantDesc': '精明、有说服力、在意地位',
      'docs.preset.guard': 'guard',
      'docs.preset.guardDesc': '刻板、多疑、尽职',
      'docs.preset.healer': 'healer',
      'docs.preset.healerDesc': '慈悲、耐心、睿智',
      'docs.customPreset': '你也可以创建自定义预设：',
      'docs.llmIntro': 'Neshama通过统一API支持21家LLM供应商。只有对话生成使用LLM——情绪是规则驱动的。',
      'docs.llmProviders': '支持的供应商包括：OpenAI、Anthropic、Google Gemini、DeepSeek、Groq、Mistral等21家。完整列表见GitHub。',
      'docs.selfhostIntro': 'Neshama采用Apache 2.0协议。你可以自行运行：',
      'docs.dockerDeploy': '或用Docker部署：',

      // ---- Language toggle ----
      'lang.toggle': 'EN'
    }
  };

  // Detect language
  function detectLanguage() {
    // 1. User manual choice takes priority
    var saved = localStorage.getItem(STORAGE_KEY);
    if (saved && (saved === 'en' || saved === 'zh')) return saved;

    // 2. Browser language
    var browserLang = navigator.language || navigator.userLanguage || '';
    if (browserLang.startsWith('zh')) return 'zh';

    // 3. Default to English
    return 'en';
  }

  var currentLang = detectLanguage();

  // Apply translations to all elements with data-i18n attributes
  function applyTranslations(lang) {
    var dict = translations[lang];
    if (!dict) return;

    // Text content elements
    var textEls = document.querySelectorAll('[data-i18n]');
    for (var i = 0; i < textEls.length; i++) {
      var el = textEls[i];
      var key = el.getAttribute('data-i18n');
      if (dict[key] !== undefined) {
        el.textContent = dict[key];
      }
    }

    // HTML content elements
    var htmlEls = document.querySelectorAll('[data-i18n-html]');
    for (var i = 0; i < htmlEls.length; i++) {
      var el = htmlEls[i];
      var key = el.getAttribute('data-i18n-html');
      if (dict[key] !== undefined) {
        el.innerHTML = dict[key];
      }
    }

    // Placeholder elements
    var placeholderEls = document.querySelectorAll('[data-i18n-placeholder]');
    for (var i = 0; i < placeholderEls.length; i++) {
      var el = placeholderEls[i];
      var key = el.getAttribute('data-i18n-placeholder');
      if (dict[key] !== undefined) {
        el.placeholder = dict[key];
      }
    }

    // Update html lang attribute
    document.documentElement.lang = lang;

    // Update lang toggle button text
    var toggleBtn = document.querySelector('.lang-toggle');
    if (toggleBtn) {
      var label = toggleBtn.querySelector('.lang-label');
      if (label) {
        label.textContent = dict['lang.toggle'] || (lang === 'en' ? '中文' : 'EN');
      }
    }
  }

  // Toggle language
  window.toggleLang = function() {
    currentLang = currentLang === 'en' ? 'zh' : 'en';
    localStorage.setItem(STORAGE_KEY, currentLang);
    applyTranslations(currentLang);
  };

  // Get current language
  window.getCurrentLang = function() {
    return currentLang;
  };

  // ---- Exchange Rate: USD → CNY ----
  var currentRate = 7.25; // Fallback default
  var RATE_CACHE_KEY = 'neshama-usd-cny-rate';
  var RATE_TIME_KEY = 'neshama-rate-time';
  var RATE_CACHE_MS = 24 * 60 * 60 * 1000; // 24 hours

  function loadCachedRate() {
    try {
      var cached = localStorage.getItem(RATE_CACHE_KEY);
      var cachedTime = localStorage.getItem(RATE_TIME_KEY);
      if (cached) {
        currentRate = parseFloat(cached);
      }
      // If cache is older than 24h, we'll still use it as fallback
      // but try to refresh
      return cachedTime ? (Date.now() - parseInt(cachedTime, 10)) < RATE_CACHE_MS : false;
    } catch (e) {
      return false;
    }
  }

  window.fetchExchangeRate = function() {
    // Try primary API first, then fallback
    var apis = [
      'https://api.exchangerate-api.com/v4/latest/USD',
      'https://open.er-api.com/v6/latest/USD'
    ];

    function tryApi(index) {
      if (index >= apis.length) return; // All APIs failed
      fetch(apis[index])
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
          if (data.rates && data.rates.CNY) {
            currentRate = data.rates.CNY;
            localStorage.setItem(RATE_CACHE_KEY, String(currentRate));
            localStorage.setItem(RATE_TIME_KEY, String(Date.now()));
            updatePrices();
          }
        })
        .catch(function() {
          tryApi(index + 1); // Try next API
        });
    }

    tryApi(0);
  };

  window.usdToCny = function(usd) {
    return Math.round(usd * currentRate);
  };

  // Regional pricing: will be populated from License API
  var apiPrices = null; // { cn: {free:0, indie:4900, studio:19900, enterprise:79900}, global: {...} }

  window.fetchApiPricing = function() {
    var isCNSite = window.location.hostname === 'neshama.cn' || window.location.hostname.endsWith('.neshama.cn');
    var apiBase = isCNSite ? 'https://api.neshama.cn' : 'https://api.neshama.pw';
    var region = isCNSite ? 'cn' : 'global';
    fetch(apiBase + '/api/license/pricing?region=' + region)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data && data.plans) {
          apiPrices = {};
          data.plans.forEach(function(p) {
            apiPrices[p.plan] = p.monthly_cents;
          });
          apiPrices._currency = data.currency || (isCNSite ? 'CNY' : 'USD');
          apiPrices._symbol = data.symbol || (isCNSite ? '¥' : '$');
          updatePrices();
        }
      })
      .catch(function() {
        // API failed, keep using hardcoded fallback
      });
  };

  window.updatePrices = function() {
    var lang = getCurrentLang();
    var isCNSite = window.location.hostname === 'neshama.cn' || window.location.hostname.endsWith('.neshama.cn');
    var rateNoteEl = document.getElementById('rate-note');
    document.querySelectorAll('[data-usd-price]').forEach(function(el) {
      var usd = parseFloat(el.dataset.usdPrice);
      if (usd < 0) return; // Skip "Custom" etc.
      if (apiPrices) {
        // Use API pricing
        var planName = el.dataset.plan;
        if (planName && apiPrices[planName] !== undefined) {
          var cents = apiPrices[planName];
          el.textContent = apiPrices._symbol + (cents / 100);
        }
      } else if (isCNSite) {
        // Fallback: China site CNY regional pricing
        var cnPrices = { 0: 0, 19: 49, 79: 199, 299: 799 };
        var cny = cnPrices[usd] !== undefined ? cnPrices[usd] : usdToCny(usd);
        el.textContent = '¥' + cny;
      } else {
        // Fallback: International site USD
        el.textContent = '$' + usd;
      }
    });
    // Show/hide rate note
    if (rateNoteEl) {
      rateNoteEl.style.display = isCNSite ? 'block' : 'none';
      if (isCNSite) {
        rateNoteEl.textContent = '* 中国大陆专属定价，支持支付宝/微信支付';
      }
    }
  };

  // Patch applyTranslations to also update prices
  var _origApplyTranslations = applyTranslations;
  applyTranslations = function(lang) {
    _origApplyTranslations(lang);
    updatePrices();
  };

  // Initialize on DOM ready
  function init() {
    // Load cached rate first (instant), then apply translations + update prices
    loadCachedRate();
    applyTranslations(currentLang);
    // Try to refresh rate from API (async, will call updatePrices on success)
    fetchExchangeRate();
    // Fetch pricing from License API (async, will call updatePrices on success)
    fetchApiPricing();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
