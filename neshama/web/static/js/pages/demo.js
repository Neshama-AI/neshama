/**
 * Neshama Demo - Interactive Demo Experience
 * Immersive demonstration of "installing souls into NPCs"
 */

// Demo State
const DemoState = {
    currentStep: 0,
    isGuided: true,
    neshamaEnabled: true,
    npcs: [],
    selectedNPC: null,
    messages: {},
    eventLog: [],
    tutorialShown: false
};

// Demo Flow Steps
const DEMO_STEPS = [
    {
        title_zh: '欢迎来到Neshama演示',
        title_en: 'Welcome to Neshama Demo',
        desc_zh: '这里有3个NPC，他们每个人都有独特的人格和情绪',
        desc_en: 'Meet 3 NPCs, each with unique personality and emotions',
        action: 'observe',
        target: null
    },
    {
        title_zh: '首次对话',
        title_en: 'First Conversation',
        desc_zh: '和艾拉打个招呼',
        desc_en: 'Say hello to Ella',
        action: 'chat',
        target: 'ella',
        hint_zh: '尝试输入: "你好" 或 "今天生意怎么样?"',
        hint_en: 'Try: "Hello" or "How is business today?"'
    },
    {
        title_zh: '情绪影响',
        title_en: 'Emotion Impact',
        desc_zh: '试试攻击艾拉',
        desc_en: 'Try attacking Ella',
        action: 'event',
        target: 'ella',
        event: 'attack',
        hint_zh: '点击"⚔️ 攻击"按钮',
        hint_en: 'Click the "⚔️ Attack" button'
    },
    {
        title_zh: 'NPC记忆',
        title_en: 'NPC Memory',
        desc_zh: '再和艾拉说话',
        desc_en: 'Talk to Ella again',
        action: 'chat',
        target: 'ella',
        hint_zh: '你会发现她记得你攻击了她',
        hint_en: 'She will remember you attacked her'
    },
    {
        title_zh: '关系恢复',
        title_en: 'Relationship Recovery',
        desc_zh: '试试送礼给艾拉',
        desc_en: 'Try gifting Ella',
        action: 'event',
        target: 'ella',
        event: 'gift',
        hint_zh: '点击"🎁 送礼"按钮',
        hint_en: 'Click the "🎁 Gift" button'
    },
    {
        title_zh: 'NPC社交',
        title_en: 'NPC Social Network',
        desc_zh: '看看艾拉在背后怎么说你',
        desc_en: 'See how NPCs talk about you',
        action: 'observe',
        target: 'social',
        hint_zh: 'NPC之间会传播信息',
        hint_en: 'NPCs share information with each other'
    },
    {
        title_zh: '剧情触发',
        title_en: 'Story Triggers',
        desc_zh: '探索剧情分支',
        desc_en: 'Explore story branches',
        action: 'observe',
        target: 'story'
    }
];

// NPC Data for Demo (fallback when API unavailable)
const DEMO_NPCS = {
    ella: {
        id: 'demo-ella',
        name_zh: '艾拉',
        name_en: 'Ella',
        emoji: '🍺',
        occupation_zh: '酒馆老板娘',
        occupation_en: 'Tavern Keeper',
        personality: { openness: 0.4, conscientiousness: 0.5, extraversion: 0.8, agreeableness: 0.75, neuroticism: 0.4 },
        emotions: { joy: 0.4, trust: 0.3, anger: 0.1, fear: 0.0, sadness: 0.1, disgust: 0.0, surprise: 0.1, anticipation: 0.2 },
        relationship: 'friendly',
        preset: 'tavern_keeper',
        color: '#f59e0b'
    },
    kyle: {
        id: 'demo-kyle',
        name_zh: '凯尔',
        name_en: 'Kyle',
        emoji: '🛡️',
        occupation_zh: '守卫队长',
        occupation_en: 'Guard Captain',
        personality: { openness: 0.3, conscientiousness: 0.8, extraversion: 0.4, agreeableness: 0.5, neuroticism: 0.3 },
        emotions: { joy: 0.2, trust: 0.2, anger: 0.1, fear: 0.0, sadness: 0.1, disgust: 0.1, surprise: 0.1, anticipation: 0.1 },
        relationship: 'neutral',
        preset: 'guard_captain',
        color: '#3b82f6'
    },
    mira: {
        id: 'demo-mira',
        name_zh: '米拉',
        name_en: 'Mira',
        emoji: '🔮',
        occupation_zh: '神秘旅人',
        occupation_en: 'Mystic Traveler',
        personality: { openness: 0.85, conscientiousness: 0.5, extraversion: 0.25, agreeableness: 0.55, neuroticism: 0.65 },
        emotions: { joy: 0.1, trust: 0.2, anger: 0.0, fear: 0.1, sadness: 0.1, disgust: 0.0, surprise: 0.3, anticipation: 0.4 },
        relationship: 'neutral',
        preset: 'mystic_traveler',
        color: '#a855f7'
    }
};

// Emotion Labels and Colors
const EMOTIONS = {
    joy: { emoji: '😊', color: '#22c55e', label_zh: '喜悦', label_en: 'Joy' },
    trust: { emoji: '🤝', color: '#3b82f6', label_zh: '信任', label_en: 'Trust' },
    anger: { emoji: '😠', color: '#ef4444', label_zh: '愤怒', label_en: 'Anger' },
    fear: { emoji: '😨', color: '#8b5cf6', label_zh: '恐惧', label_en: 'Fear' },
    sadness: { emoji: '😢', color: '#6366f1', label_zh: '悲伤', label_en: 'Sadness' },
    disgust: { emoji: '🤢', color: '#84cc16', label_zh: '厌恶', label_en: 'Disgust' },
    surprise: { emoji: '😲', color: '#f97316', label_zh: '惊讶', label_en: 'Surprise' },
    anticipation: { emoji: '🤔', color: '#eab308', label_zh: '期待', label_en: 'Anticipation' },
    calm: { emoji: '😌', color: '#06b6d4', label_zh: '平静', label_en: 'Calm' }
};

// Event effects on emotions
const EVENT_EFFECTS = {
    gift: { joy: 0.3, trust: 0.2, anger: -0.1 },
    attack: { anger: 0.5, fear: 0.2, trust: -0.3, joy: -0.2 },
    help: { trust: 0.3, joy: 0.2, fear: -0.1 },
    compliment: { joy: 0.2, trust: 0.2, anger: -0.1 },
    insult: { anger: 0.4, sadness: 0.2, trust: -0.3 },
    trade: { joy: 0.1, trust: 0.1, anticipation: 0.1 },
    quest_completed: { joy: 0.3, trust: 0.2, pride: 0.2 },
    quest_failed: { sadness: 0.3, anger: 0.2, disappointment: 0.2 },
    item_received: { joy: 0.2, anticipation: 0.1, surprise: 0.2 }
};

// Dialogue templates (with/without Neshama)
const DIALOGUES = {
    ella: {
        greet: {
            neshama: [
                { emotion: 'joy', text_zh: '啊，尊贵的客人！欢迎光临我的小酒馆~', text_en: 'Ah, a valued guest! Welcome to my humble tavern~' },
                { emotion: 'curiosity', text_zh: '看你的样子，是远方来的冒险者吧？', text_en: 'You look like an adventurer from far away?' }
            ],
            basic: [
                { text_zh: '你好，欢迎光临。', text_en: 'Hello, welcome.' },
                { text_zh: '要点什么？', text_en: 'What would you like?' }
            ]
        },
        afterAttack: {
            neshama: [
                { emotion: 'anger', text_zh: '你疯了吗?! 给我滚出去!', text_en: 'Are you mad?! Get out of my tavern!' },
                { emotion: 'fear', text_zh: '卫兵！有人在我的酒馆闹事！', text_en: 'Guards! Someone is causing trouble!' }
            ],
            basic: [
                { text_zh: '你不要乱来。', text_en: 'Stop that.' }
            ]
        },
        afterGift: {
            neshama: [
                { emotion: 'joy', text_zh: '哦？这是给我的吗？好吧...也许你不是那么坏。', text_en: 'Oh? Is this for me? Well... maybe you are not so bad.' },
                { emotion: 'trust', text_zh: '难得遇到你这么慷慨的客人，我请你喝一杯！', text_en: 'Rare to meet such a generous guest! Let me get you a drink on the house!' }
            ],
            basic: [
                { text_zh: '谢谢。', text_en: 'Thanks.' }
            ]
        },
        remembers: {
            neshama: [
                { emotion: 'anger', text_zh: '你还敢来？我还没原谅你呢！', text_en: 'You dare come back? I have not forgiven you!' },
                { emotion: 'caution', text_zh: '你最好老实点，不然我叫卫兵了。', text_en: 'You better behave, or I will call the guards.' }
            ],
            basic: [
                { text_zh: '你好，欢迎光临。', text_en: 'Hello, welcome.' }
            ]
        },
        aboutPlayer: {
            neshama: [
                { emotion: 'disgust', text_zh: '有个粗鲁的冒险者来过我这里，竟然敢攻击我！', text_en: 'A rude adventurer came to my tavern, dared to attack me!' },
                { emotion: 'anger', text_zh: '如果再让我看到他，一定要让凯尔把他赶出去！', text_en: 'If I see him again, I will have Kyle throw him out!' }
            ],
            basic: []
        }
    },
    kyle: {
        greet: {
            neshama: [
                { emotion: 'neutral', text_zh: '站住。你来这里做什么？', text_en: 'Halt. What is your business here?' },
                { emotion: 'caution', text_zh: '我见过你，你是新来的冒险者吧。', text_en: 'I have seen you before, you are the new adventurer.' }
            ],
            basic: [
                { text_zh: '你好。', text_en: 'Hello.' }
            ]
        },
        aboutPlayer: {
            neshama: [
                { emotion: 'anger', text_zh: '艾拉说你最近很嚣张？最好收敛点。', text_en: 'Ella says you have been acting up lately? Behave yourself.' },
                { emotion: 'threat', text_zh: '城门现在戒严了，都是因为你。', text_en: 'The gates are on high alert now, all because of you.' }
            ],
            basic: []
        }
    },
    mira: {
        greet: {
            neshama: [
                { emotion: 'curiosity', text_zh: '旅人啊...你看到了什么？', text_en: 'Traveler... what do you see?' },
                { emotion: 'mystery', text_zh: '星辰指引你来到此处...是巧合，还是命运？', text_en: 'The stars have guided you here... coincidence, or destiny?' }
            ],
            basic: [
                { text_zh: '你好。', text_en: 'Hello.' }
            ]
        },
        afterTrust: {
            neshama: [
                { emotion: 'secret', text_zh: '既然你这么真诚...我告诉你一个秘密：在月圆之夜，湖底沉睡着古老的力量...', text_en: 'Since you are so sincere... I will tell you a secret: On full moon nights, ancient power sleeps beneath the lake...' },
                { emotion: 'quest', text_zh: '这个任务只有你能够完成。你愿意接受吗？', text_en: 'This quest only you can complete. Will you accept?' }
            ],
            basic: []
        }
    }
};

// Relationship labels
const RELATIONSHIP_LABELS = {
    friendly: { label_zh: '友好', label_en: 'Friendly', color: '#22c55e' },
    neutral: { label_zh: '中立', label_en: 'Neutral', color: '#eab308' },
    hostile: { label_zh: '敌对', label_en: 'Hostile', color: '#ef4444' }
};

// Game Events
const GAME_EVENTS = [
    { id: 'gift', emoji: '🎁', label_zh: '送礼', label_en: 'Gift', type: 'gift_given' },
    { id: 'attack', emoji: '⚔️', label_zh: '攻击', label_en: 'Attack', type: 'player_attacked' },
    { id: 'help', emoji: '🤝', label_zh: '帮助', label_en: 'Help', type: 'player_helped' },
    { id: 'compliment', emoji: '💬', label_zh: '夸赞', label_en: 'Compliment', type: 'npc_complimented' },
    { id: 'insult', emoji: '😤', label_zh: '辱骂', label_en: 'Insult', type: 'npc_insulted' },
    { id: 'trade', emoji: '📦', label_zh: '交易', label_en: 'Trade', type: 'item_received' },
    { id: 'quest_complete', emoji: '⚡', label_zh: '任务完成', label_en: 'Quest Done', type: 'quest_completed' },
    { id: 'quest_fail', emoji: '💀', label_zh: '任务失败', label_en: 'Quest Failed', type: 'quest_failed' }
];

// ============================================
// Demo Page Rendering
// ============================================

function renderDemo() {
    const page = document.getElementById('page-demo');
    if (!page) return;

    const lang = getCurrentLang();
    const isZh = lang === 'zh';

    page.innerHTML = `
        <div class="demo-container">
            <!-- Demo Header -->
            <header class="demo-header">
                <div class="demo-brand">
                    <span class="demo-logo">🔮</span>
                    <div class="demo-brand-text">
                        <h1 class="demo-title">Neshama</h1>
                        <p class="demo-tagline">${isZh ? '体验NPC灵魂' : 'Experience NPC Souls'}</p>
                    </div>
                </div>
                <div class="demo-controls">
                    <button class="demo-toggle-btn ${DemoState.neshamaEnabled ? 'active' : ''}" id="neshama-toggle">
                        <span class="toggle-label">${isZh ? '有Neshama' : 'With Neshama'}</span>
                        <span class="toggle-separator">/</span>
                        <span class="toggle-label">${isZh ? '无Neshama' : 'Without'}</span>
                    </button>
                </div>
            </header>

            <!-- Demo Flow Guide -->
            ${DemoState.isGuided ? renderDemoFlow() : ''}

            <!-- NPC Cards Grid -->
            <section class="demo-npc-section">
                <h2 class="demo-section-title">${isZh ? '选择你的NPC' : 'Choose Your NPC'}</h2>
                <div class="demo-npc-grid" id="npc-grid">
                    ${renderNPCCards()}
                </div>
            </section>

            <!-- Comparison Section -->
            <section class="demo-comparison" id="demo-comparison">
                ${renderComparison()}
            </section>
        </div>

        <!-- NPC Interaction Modal -->
        <div class="demo-modal" id="demo-modal">
            <div class="demo-modal-content">
                <button class="demo-modal-close" id="modal-close">✕</button>
                ${renderNPCPanel()}
            </div>
        </div>

        <!-- Demo Flow Modal -->
        <div class="demo-flow-modal" id="demo-flow-modal">
            <div class="demo-flow-content">
                ${renderFlowContent()}
            </div>
        </div>
    `;

    initDemoEventListeners();
}

function renderDemoFlow() {
    const lang = getCurrentLang();
    const isZh = lang === 'zh';
    const currentStep = DEMO_STEPS[DemoState.currentStep];

    return `
        <div class="demo-flow-bar">
            <div class="flow-steps">
                ${DEMO_STEPS.map((step, i) => `
                    <div class="flow-step ${i < DemoState.currentStep ? 'completed' : ''} ${i === DemoState.currentStep ? 'active' : ''}" 
                         data-step="${i}">
                        <span class="flow-step-num">${i + 1}</span>
                        <span class="flow-step-title">${isZh ? step.title_zh : step.title_en}</span>
                    </div>
                `).join('')}
            </div>
            <div class="flow-actions">
                <button class="flow-skip-btn" id="flow-skip">${isZh ? '自由探索' : 'Free Explore'}</button>
                <button class="flow-next-btn" id="flow-next" ${DemoState.currentStep >= DEMO_STEPS.length - 1 ? 'disabled' : ''}>
                    ${isZh ? '下一步' : 'Next'} →
                </button>
            </div>
        </div>
    `;
}

function renderNPCCards() {
    const lang = getCurrentLang();
    const isZh = lang === 'zh';

    return Object.entries(DEMO_NPCS).map(([key, npc]) => {
        const dominantEmotion = getDominantEmotion(npc.emotions);
        const emotionInfo = EMOTIONS[dominantEmotion] || EMOTIONS.joy;
        const relInfo = RELATIONSHIP_LABELS[npc.relationship] || RELATIONSHIP_LABELS.neutral;

        return `
            <div class="demo-npc-card" data-npc="${key}" style="--npc-color: ${npc.color}">
                <div class="npc-avatar-wrapper">
                    <div class="npc-avatar">${npc.emoji}</div>
                    <div class="npc-avatar-glow"></div>
                </div>
                <div class="npc-info">
                    <h3 class="npc-name">${isZh ? npc.name_zh : npc.name_en}</h3>
                    <p class="npc-occupation">${isZh ? npc.occupation_zh : npc.occupation_en}</p>
                </div>
                <div class="npc-emotion-grid">
                    ${renderEmotionGrid(npc.emotions)}
                </div>
                <div class="npc-dominant-emotion">
                    <span class="emotion-emoji">${emotionInfo.emoji}</span>
                    <span class="emotion-label">${isZh ? emotionInfo.label_zh : emotionInfo.label_en}</span>
                </div>
                <div class="npc-relationship" style="--rel-color: ${relInfo.color}">
                    <span class="rel-indicator"></span>
                    <span>${isZh ? relInfo.label_zh : relInfo.label_en}</span>
                </div>
                <button class="npc-interact-btn">
                    ${isZh ? '互动' : 'Interact'}
                </button>
            </div>
        `;
    }).join('');
}

function renderEmotionGrid(emotions) {
    return Object.entries(emotions).slice(0, 9).map(([emotion, value]) => {
        const info = EMOTIONS[emotion] || EMOTIONS.joy;
        const brightness = Math.max(0.2, value);
        return `
            <div class="emotion-dot" 
                 data-emotion="${emotion}"
                 style="background-color: ${info.color}; opacity: ${brightness};"
                 title="${info.label_zh}: ${(value * 100).toFixed(0)}%">
            </div>
        `;
    }).join('');
}

function renderNPCPanel() {
    const lang = getCurrentLang();
    const isZh = lang === 'zh';
    const npc = DemoState.selectedNPC ? DEMO_NPCS[DemoState.selectedNPC] : null;
    
    if (!npc) return '<div class="demo-modal-loading">Loading...</div>';

    const messages = DemoState.messages[DemoState.selectedNPC] || [];
    const dominantEmotion = getDominantEmotion(npc.emotions);
    const emotionInfo = EMOTIONS[dominantEmotion] || EMOTIONS.joy;
    const relInfo = RELATIONSHIP_LABELS[npc.relationship] || RELATIONSHIP_LABELS.neutral;

    return `
        <div class="npc-panel">
            <!-- Left: NPC Info -->
            <div class="npc-panel-left">
                <div class="npc-panel-avatar">${npc.emoji}</div>
                <h2 class="npc-panel-name">${isZh ? npc.name_zh : npc.name_en}</h2>
                <p class="npc-panel-occupation">${isZh ? npc.occupation_zh : npc.occupation_en}</p>
                
                <!-- Personality Radar -->
                <div class="npc-personality-radar">
                    <canvas id="radar-canvas" width="180" height="180"></canvas>
                </div>
                
                <!-- Emotion Bars -->
                <div class="npc-emotion-bars">
                    <h4>${isZh ? '情绪状态' : 'Emotion State'}</h4>
                    ${renderEmotionBars(npc.emotions)}
                </div>
                
                <!-- Relationship -->
                <div class="npc-relation-status">
                    <span class="rel-badge" style="--rel-color: ${relInfo.color}">
                        ${isZh ? relInfo.label_zh : relInfo.label_en}
                    </span>
                </div>
            </div>
            
            <!-- Right: Chat & Events -->
            <div class="npc-panel-right">
                <!-- Chat Area -->
                <div class="npc-chat-area">
                    <h4>${isZh ? '对话' : 'Dialogue'}</h4>
                    <div class="chat-messages" id="chat-messages">
                        ${renderChatMessages(messages)}
                    </div>
                    <div class="chat-input-area">
                        <input type="text" 
                               class="chat-input" 
                               id="chat-input"
                               placeholder="${isZh ? '输入对话...' : 'Type a message...'}"
                               ${!DemoState.neshamaEnabled ? 'disabled' : ''}>
                        <button class="chat-send-btn" id="chat-send">
                            ${isZh ? '发送' : 'Send'}
                        </button>
                    </div>
                </div>
                
                <!-- Event Buttons -->
                <div class="npc-events-area">
                    <h4>${isZh ? '快捷事件' : 'Quick Events'}</h4>
                    <div class="event-buttons-grid">
                        ${GAME_EVENTS.map(event => `
                            <button class="event-btn" 
                                    data-event="${event.id}"
                                    ${!DemoState.neshamaEnabled ? 'disabled' : ''}>
                                <span class="event-emoji">${event.emoji}</span>
                                <span class="event-label">${isZh ? event.label_zh : event.label_en}</span>
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderEmotionBars(emotions) {
    return Object.entries(emotions).map(([emotion, value]) => {
        const info = EMOTIONS[emotion] || EMOTIONS.joy;
        return `
            <div class="emotion-bar-item">
                <span class="emotion-bar-emoji">${info.emoji}</span>
                <div class="emotion-bar-track">
                    <div class="emotion-bar-fill" 
                         style="width: ${value * 100}%; background-color: ${info.color};"
                         data-value="${value}"></div>
                </div>
                <span class="emotion-bar-value">${(value * 100).toFixed(0)}%</span>
            </div>
        `;
    }).join('');
}

function renderChatMessages(messages) {
    if (!messages || messages.length === 0) {
        const lang = getCurrentLang();
        const isZh = lang === 'zh';
        return `
            <div class="chat-empty">
                <p>${isZh ? '开始对话吧...' : 'Start a conversation...'}</p>
            </div>
        `;
    }

    return messages.map(msg => `
        <div class="chat-message ${msg.role}">
            <div class="message-content">
                ${msg.text_zh ? `<p class="msg-text">${msg.text_zh}</p>` : ''}
                ${msg.text_en ? `<p class="msg-text-en">${msg.text_en}</p>` : ''}
            </div>
            ${msg.emotion ? `<span class="message-emotion">${EMOTIONS[msg.emotion]?.emoji || ''}</span>` : ''}
        </div>
    `).join('');
}

function renderComparison() {
    const lang = getCurrentLang();
    const isZh = lang === 'zh';

    return `
        <div class="comparison-container">
            <div class="comparison-header">
                <h3>${isZh ? '有/无Neshama 对比' : 'With/Without Neshama Comparison'}</h3>
            </div>
            <div class="comparison-grid">
                <div class="comparison-col ${DemoState.neshamaEnabled ? 'active' : ''}">
                    <h4>${isZh ? '🧠 有Neshama' : '🧠 With Neshama'}</h4>
                    <ul>
                        <li>${isZh ? '✓ 对话随情绪变化' : '✓ Dialogues change with emotions'}</li>
                        <li>✓ ${isZh ? '情绪实时更新' : 'Real-time emotion updates'}</li>
                        <li>✓ ${isZh ? '记住玩家行为' : 'Remembers player actions'}</li>
                        <li>✓ ${isZh ? 'NPC之间传播信息' : 'NPCs share information'}</li>
                        <li>✓ ${isZh ? '触发剧情分支' : 'Story branches triggered'}</li>
                    </ul>
                </div>
                <div class="comparison-col ${!DemoState.neshamaEnabled ? 'active' : ''}">
                    <h4>${isZh ? '📦 无Neshama' : '📦 Without Neshama'}</h4>
                    <ul>
                        <li>${isZh ? '✗ 固定模板回复' : '✗ Fixed template responses'}</li>
                        <li>✗ ${isZh ? '情绪永远不变' : 'Emotions never change'}</li>
                        <li>✗ ${isZh ? '不记住玩家' : 'Does not remember player'}</li>
                        <li>✗ ${isZh ? 'NPC之间无互动' : 'No NPC interactions'}</li>
                        <li>✗ ${isZh ? '无法触发剧情' : 'Cannot trigger stories'}</li>
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function renderFlowContent() {
    const lang = getCurrentLang();
    const isZh = lang === 'zh';
    const step = DEMO_STEPS[DemoState.currentStep];

    return `
        <div class="flow-modal-header">
            <span class="flow-step-indicator">${DemoState.currentStep + 1} / ${DEMO_STEPS.length}</span>
        </div>
        <div class="flow-modal-body">
            <h2 class="flow-modal-title">${isZh ? step.title_zh : step.title_en}</h2>
            <p class="flow-modal-desc">${isZh ? step.desc_zh : step.desc_en}</p>
            ${step.hint_zh ? `<p class="flow-modal-hint">💡 ${isZh ? step.hint_zh : step.hint_en}</p>` : ''}
        </div>
        <div class="flow-modal-footer">
            <button class="flow-modal-skip" id="flow-modal-skip">
                ${isZh ? '跳过引导' : 'Skip Tutorial'}
            </button>
            <button class="flow-modal-next" id="flow-modal-next" 
                    ${DemoState.currentStep >= DEMO_STEPS.length - 1 ? 'disabled' : ''}>
                ${DemoState.currentStep >= DEMO_STEPS.length - 1 ? 
                    (isZh ? '完成！' : 'Complete!') : 
                    (isZh ? '下一步' : 'Next Step')}
            </button>
        </div>
    `;
}

// ============================================
// Event Handlers
// ============================================

function initDemoEventListeners() {
    // NPC card click
    document.querySelectorAll('.demo-npc-card').forEach(card => {
        card.addEventListener('click', () => {
            const npcKey = card.dataset.npc;
            openNPCPanel(npcKey);
        });
    });

    // Modal close
    const modalClose = document.getElementById('modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', closeNPCPanel);
    }

    // Neshama toggle
    const toggle = document.getElementById('neshama-toggle');
    if (toggle) {
        toggle.addEventListener('click', toggleNeshama);
    }

    // Chat send
    const chatSend = document.getElementById('chat-send');
    const chatInput = document.getElementById('chat-input');
    if (chatSend && chatInput) {
        chatSend.addEventListener('click', () => sendChat(chatInput.value));
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendChat(chatInput.value);
        });
    }

    // Event buttons
    document.querySelectorAll('.event-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const eventType = btn.dataset.event;
            triggerEvent(eventType);
        });
    });

    // Flow controls
    const flowSkip = document.getElementById('flow-skip');
    const flowNext = document.getElementById('flow-next');
    const flowModalSkip = document.getElementById('flow-modal-skip');
    const flowModalNext = document.getElementById('flow-modal-next');

    if (flowSkip) flowSkip.addEventListener('click', skipFlow);
    if (flowNext) flowNext.addEventListener('click', advanceFlow);
    if (flowModalSkip) flowModalSkip.addEventListener('click', skipFlow);
    if (flowModalNext) flowModalNext.addEventListener('click', advanceFlow);

    // Draw radar chart
    drawRadarChart();

    // Update emotion bars animation
    animateEmotionBars();
}

function openNPCPanel(npcKey) {
    DemoState.selectedNPC = npcKey;
    if (!DemoState.messages[npcKey]) {
        DemoState.messages[npcKey] = [];
    }
    
    const modal = document.getElementById('demo-modal');
    if (modal) {
        modal.classList.add('active');
        // Re-render panel content
        const content = modal.querySelector('.demo-modal-content');
        if (content) {
            content.innerHTML = `
                <button class="demo-modal-close" id="modal-close">✕</button>
                ${renderNPCPanel()}
            `;
            initDemoEventListeners();
        }
    }
    
    // Show greeting on first open
    if (DemoState.messages[npcKey].length === 0) {
        setTimeout(() => showGreeting(npcKey), 300);
    }
}

function closeNPCPanel() {
    const modal = document.getElementById('demo-modal');
    if (modal) {
        modal.classList.remove('active');
    }
    DemoState.selectedNPC = null;
}

function toggleNeshama() {
    DemoState.neshamaEnabled = !DemoState.neshamaEnabled;
    updateToggleUI();
    showToast(DemoState.neshamaEnabled ? 
        (getCurrentLang() === 'zh' ? 'Neshama 已启用' : 'Neshama Enabled') : 
        (getCurrentLang() === 'zh' ? 'Neshama 已禁用' : 'Neshama Disabled'));
}

function updateToggleUI() {
    const toggle = document.getElementById('neshama-toggle');
    if (toggle) {
        toggle.classList.toggle('active', DemoState.neshamaEnabled);
    }
    const comparison = document.getElementById('demo-comparison');
    if (comparison) {
        comparison.innerHTML = renderComparison();
    }
}

function showGreeting(npcKey) {
    const npc = DEMO_NPCS[npcKey];
    if (!npc) return;

    const lang = getCurrentLang();
    const isZh = lang === 'zh';
    let dialogues;

    if (DemoState.neshamaEnabled && DIALOGUES[npcKey]?.greet) {
        dialogues = DIALOGUES[npcKey].greet.neshama;
    } else if (DIALOGUES[npcKey]?.greet) {
        dialogues = DIALOGUES[npcKey].greet.basic;
    } else {
        dialogues = [{ text_zh: '你好，陌生人。', text_en: 'Hello, stranger.' }];
    }

    const dialogue = dialogues[Math.floor(Math.random() * dialogues.length)];
    
    addMessage(npcKey, {
        role: 'npc',
        text_zh: dialogue.text_zh,
        text_en: dialogue.text_en,
        emotion: dialogue.emotion
    });
}

function sendChat(text) {
    if (!text.trim() || !DemoState.selectedNPC) return;

    const npcKey = DemoState.selectedNPC;
    const npc = DEMO_NPCS[npcKey];
    
    // Add user message
    addMessage(npcKey, {
        role: 'user',
        text_zh: text,
        text_en: text
    });

    // Generate NPC response
    generateResponse(npcKey, text);

    // Clear input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.value = '';

    // Check for demo step completion
    checkStepCompletion('chat');
}

function generateResponse(npcKey, userText) {
    const npc = DEMO_NPCS[npcKey];
    const lang = getCurrentLang();
    const isZh = lang === 'zh';
    
    // Simulate thinking
    setTimeout(() => {
        let response;
        let emotion = 'neutral';

        // Check for attack keywords
        const isAttack = /攻击|打|杀|滚|滚开/i.test(userText);
        const isGift = /礼物|送|谢谢|感谢/i.test(userText);
        const isHello = /你好|hi|hello|嗨/i.test(userText);
        const isHelp = /帮助|帮忙|救/i.test(userText);

        // Get dialogue based on context
        if (isAttack && DemoState.neshamaEnabled) {
            const dialogues = DIALOGUES[npcKey]?.afterAttack?.neshama || DIALOGUES[npcKey]?.afterAttack?.basic;
            response = dialogues[Math.floor(Math.random() * dialogues.length)];
        } else if (isGift && DemoState.neshamaEnabled) {
            const dialogues = DIALOGUES[npcKey]?.afterGift?.neshama || DIALOGUES[npcKey]?.afterGift?.basic;
            response = dialogues[Math.floor(Math.random() * dialogues.length)];
        } else if (isHello) {
            if (DemoState.neshamaEnabled && DIALOGUES[npcKey]?.greet?.neshama) {
                response = DIALOGUES[npcKey].greet.neshama[Math.floor(Math.random() * DIALOGUES[npcKey].greet.neshama.length)];
            } else {
                response = DIALOGUES[npcKey]?.greet?.basic?.[Math.floor(Math.random() * DIALOGUES[npcKey].greet.basic.length)] || 
                           { text_zh: '你好。', text_en: 'Hello.' };
            }
        } else if (DemoState.neshamaEnabled) {
            // Generate contextual response
            response = generateContextualResponse(npcKey, npc, userText);
        } else {
            // Basic template response
            response = {
                text_zh: `好的，我听到了。`,
                text_en: `Okay, I heard you.`
            };
        }

        addMessage(npcKey, {
            role: 'npc',
            text_zh: response.text_zh,
            text_en: response.text_en,
            emotion: response.emotion || emotion
        });
    }, 500 + Math.random() * 1000);
}

function generateContextualResponse(npcKey, npc, userText) {
    const lang = getCurrentLang();
    const isZh = lang === 'zh';
    
    // Check memory for previous interactions
    const messages = DemoState.messages[npcKey] || [];
    const wasAttacked = DemoState.eventLog.some(e => e.npc === npcKey && e.event === 'attack');
    const wasGifted = DemoState.eventLog.some(e => e.npc === npcKey && e.event === 'gift');

    // Generate response based on relationship and memory
    if (wasAttacked) {
        return DIALOGUES[npcKey]?.remembers?.neshama?.[Math.floor(Math.random() * DIALOGUES[npcKey].remembers.neshama.length)] || {
            text_zh: '你还敢来？',
            text_en: 'You dare come back?'
        };
    }

    // Contextual greetings and responses
    const responses = {
        ella: [
            { text_zh: '今天的麦酒特别香，你要来一杯吗？', text_en: 'The mead is especially fragrant today, would you like a cup?' },
            { text_zh: '最近冒险者多了，生意还不错。', text_en: 'More adventurers lately, business is good.' },
            { text_zh: '你想听故事吗？我这儿有很多有趣的传闻。', text_en: 'Want to hear a story? I have many interesting rumors here.' }
        ],
        kyle: [
            { text_zh: '城门守卫是这座城市的第一道防线。', text_en: 'The gate guards are the first line of defense.' },
            { text_zh: '最近有魔兽出没的报告。', text_en: 'There have been reports of monsters nearby.' },
            { text_zh: '没有可疑情况的话，不要在城门口逗留。', text_en: 'Do not loiter at the gate unless you have business.' }
        ],
        mira: [
            { text_zh: '星辰在诉说着什么...你能听到吗？', text_en: 'The stars are speaking... can you hear them?' },
            { text_zh: '每一片落叶都有它的故事。', text_en: 'Every falling leaf has its own story.' },
            { text_zh: '命运是一条河流，我们都是其中的水滴。', text_en: 'Fate is a river, and we are all droplets within it.' }
        ]
    };

    const npcResponses = responses[npcKey] || responses.ella;
    return npcResponses[Math.floor(Math.random() * npcResponses.length)];
}

function triggerEvent(eventType) {
    if (!DemoState.selectedNPC) return;

    const npcKey = DemoState.selectedNPC;
    const npc = DEMO_NPCS[npcKey];
    const effects = EVENT_EFFECTS[eventType] || {};

    // Apply emotion effects with animation
    Object.entries(effects).forEach(([emotion, delta]) => {
        if (npc.emotions[emotion] !== undefined) {
            npc.emotions[emotion] = Math.max(0, Math.min(1, npc.emotions[emotion] + delta));
        }
    });

    // Update relationship based on event
    if (eventType === 'attack') {
        npc.relationship = 'hostile';
    } else if (eventType === 'gift' || eventType === 'help' || eventType === 'compliment') {
        npc.relationship = 'friendly';
    }

    // Log event
    DemoState.eventLog.push({ npc: npcKey, event: eventType, time: Date.now() });

    // Show event effect message
    const lang = getCurrentLang();
    const isZh = lang === 'zh';
    const eventInfo = GAME_EVENTS.find(e => e.id === eventType);
    const messages = DemoState.messages[npcKey] || [];

    if (DemoState.neshamaEnabled) {
        let response;
        if (eventType === 'attack') {
            response = DIALOGUES[npcKey]?.afterAttack?.neshama?.[0] || {
                text_zh: '你怎么敢！', text_en: 'How dare you!'
            };
        } else if (eventType === 'gift') {
            response = DIALOGUES[npcKey]?.afterGift?.neshama?.[0] || {
                text_zh: '谢谢你！', text_en: 'Thank you!'
            };
        } else if (eventType === 'insult') {
            response = {
                text_zh: '你的言辞令人厌恶...',
                text_en: 'Your words are disgusting...'
            };
        } else if (eventType === 'quest_complete') {
            response = {
                text_zh: '干得漂亮！我会记住你的功绩。',
                text_en: 'Well done! I will remember your deeds.'
            };
        } else if (eventType === 'quest_fail') {
            response = {
                text_zh: '这真是令人失望...',
                text_en: 'This is truly disappointing...'
            };
        } else {
            response = {
                text_zh: `（${eventInfo?.emoji || ''} ${eventInfo?.label_zh || eventType}）`,
                text_en: `（${eventInfo?.emoji || ''} ${eventInfo?.label_en || eventType}）`
            };
        }

        addMessage(npcKey, {
            role: 'npc',
            text_zh: response.text_zh,
            text_en: response.text_en,
            emotion: response.emotion || getDominantEmotion(npc.emotions)
        });
    } else {
        addMessage(npcKey, {
            role: 'system',
            text_zh: `（${eventInfo?.emoji || ''} ${eventInfo?.label_zh || eventType}）`,
            text_en: `（${eventInfo?.emoji || ''} ${eventInfo?.label_en || eventType}）`
        });
    }

    // Update UI
    updatePanelUI();
    updateNPCCards();

    // Check for demo step completion
    checkStepCompletion('event', eventType);

    // Show NPC-to-NPC communication if applicable
    if (DemoState.neshamaEnabled && (eventType === 'attack' || eventType === 'gift')) {
        showNPCCommunication(npcKey, eventType);
    }
}

function addMessage(npcKey, message) {
    if (!DemoState.messages[npcKey]) {
        DemoState.messages[npcKey] = [];
    }
    DemoState.messages[npcKey].push(message);

    // Update chat UI if panel is open
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages && DemoState.selectedNPC === npcKey) {
        chatMessages.innerHTML = renderChatMessages(DemoState.messages[npcKey]);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function updatePanelUI() {
    const modal = document.getElementById('demo-modal');
    if (modal && modal.classList.contains('active')) {
        const content = modal.querySelector('.demo-modal-content');
        if (content) {
            content.innerHTML = `
                <button class="demo-modal-close" id="modal-close">✕</button>
                ${renderNPCPanel()}
            `;
            initDemoEventListeners();
        }
    }
}

function updateNPCCards() {
    const grid = document.getElementById('npc-grid');
    if (grid) {
        grid.innerHTML = renderNPCCards();
        initDemoEventListeners();
    }
}

function showNPCCommunication(fromNpc, eventType) {
    const lang = getCurrentLang();
    const isZh = lang === 'zh';
    
    // Find another NPC to talk to
    const otherNpcs = Object.keys(DEMO_NPCS).filter(k => k !== fromNpc);
    if (otherNpcs.length === 0) return;

    const targetNpc = otherNpcs[Math.floor(Math.random() * otherNpcs.length)];
    const fromNpcData = DEMO_NPCS[fromNpc];
    const targetNpcData = DEMO_NPCS[targetNpc];

    let message;
    if (eventType === 'attack') {
        message = {
            speaker: targetNpcData.name_en,
            text_zh: `${targetNpcData.name_zh}对${fromNpcData.name_zh}说：「${fromNpcData.name_zh === 'Ella' ? '艾拉' : fromNpcData.name_zh}告诉我有个粗鲁的冒险者...」`,
            text_en: `${targetNpcData.name_en} says to someone: "Ella told me about a rude adventurer..."`
        };
        
        // Update target NPC relationship
        targetNpcData.emotions.anger = Math.min(1, (targetNpcData.emotions.anger || 0) + 0.1);
        targetNpcData.relationship = 'neutral';
    } else if (eventType === 'gift') {
        message = {
            speaker: targetNpcData.name_en,
            text_zh: `${targetNpcData.name_zh}听到${fromNpcData.name_zh}说：「有个不错的冒险者送我礼物呢~」`,
            text_en: `${targetNpcData.name_en} heard: "An adventurer gave me a nice gift~"`
        };
    }

    if (message) {
        // Show as toast notification
        showToast(`💬 ${isZh ? message.text_zh : message.text_en}`, 'info');
        
        // Add to NPC's message if panel is open
        if (DemoState.selectedNPC === targetNpc) {
            addMessage(targetNpc, {
                role: 'npc-others',
                text_zh: message.text_zh,
                text_en: message.text_en
            });
        }
    }

    // Check for story trigger
    if (eventType === 'attack' && fromNpc === 'kyle') {
        showStoryTrigger('gate_alert');
    }
}

function showStoryTrigger(storyId) {
    const lang = getCurrentLang();
    const isZh = lang === 'zh';

    const stories = {
        gate_alert: {
            title_zh: '🚨 剧情触发：城门戒严',
            title_en: '🚨 Story Trigger: Gate on Alert',
            desc_zh: '由于你对守卫队长的无礼行为，城门加强了戒备...',
            desc_en: 'Due to your disrespect to the Guard Captain, the gates are now on high alert...'
        },
        secret_quest: {
            title_zh: '🔮 剧情触发：秘密任务',
            title_en: '🔮 Story Trigger: Secret Quest',
            desc_zh: '米拉决定向你透露一个古老的秘密...',
            desc_en: 'Mira has decided to reveal an ancient secret to you...'
        }
    };

    const story = stories[storyId];
    if (story) {
        showToast(`${isZh ? story.title_zh : story.title_en}\n${isZh ? story.desc_zh : story.desc_en}`, 'story');
    }
}

function checkStepCompletion(type, eventType) {
    const step = DEMO_STEPS[DemoState.currentStep];
    if (!step || !DemoState.isGuided) return;

    if (step.action === 'chat' && type === 'chat') {
        // Chat step completed
    } else if (step.action === 'event' && type === 'event' && step.event === eventType) {
        // Event step completed
    }
}

function skipFlow() {
    DemoState.isGuided = false;
    const flowBar = document.querySelector('.demo-flow-bar');
    if (flowBar) flowBar.style.display = 'none';
    const flowModal = document.getElementById('demo-flow-modal');
    if (flowModal) flowModal.classList.remove('active');
    showToast(getCurrentLang() === 'zh' ? '已进入自由探索模式' : 'Entered free explore mode');
}

function advanceFlow() {
    if (DemoState.currentStep < DEMO_STEPS.length - 1) {
        DemoState.currentStep++;
        updateFlowUI();
        
        // Show hint for current step
        const step = DEMO_STEPS[DemoState.currentStep];
        if (step.target && step.action === 'chat') {
            // Highlight the NPC card
            const card = document.querySelector(`.demo-npc-card[data-npc="${step.target}"]`);
            if (card) {
                card.classList.add('highlight');
                setTimeout(() => card.classList.remove('highlight'), 3000);
            }
        }
    }
}

function updateFlowUI() {
    // Update flow bar
    document.querySelectorAll('.flow-step').forEach((el, i) => {
        el.classList.toggle('completed', i < DemoState.currentStep);
        el.classList.toggle('active', i === DemoState.currentStep);
    });

    // Update next button
    const flowNext = document.getElementById('flow-next');
    if (flowNext) {
        flowNext.disabled = DemoState.currentStep >= DEMO_STEPS.length - 1;
    }

    // Update modal
    const modal = document.getElementById('demo-flow-modal');
    if (modal && modal.classList.contains('active')) {
        modal.querySelector('.demo-flow-content').innerHTML = renderFlowContent();
        initDemoEventListeners();
    }
}

function drawRadarChart() {
    const canvas = document.getElementById('radar-canvas');
    if (!canvas || !DemoState.selectedNPC) return;

    const npc = DEMO_NPCS[DemoState.selectedNPC];
    if (!npc) return;

    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 70;

    const traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
    const traitLabels = ['O', 'C', 'E', 'A', 'N'];
    const personality = npc.personality;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw background rings
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 1; i <= 5; i++) {
        ctx.beginPath();
        const r = (radius / 5) * i;
        for (let j = 0; j <= traits.length; j++) {
            const angle = (Math.PI * 2 / traits.length) * j - Math.PI / 2;
            const x = centerX + Math.cos(angle) * r;
            const y = centerY + Math.sin(angle) * r;
            if (j === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.stroke();
    }

    // Draw axes
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    for (let i = 0; i < traits.length; i++) {
        const angle = (Math.PI * 2 / traits.length) * i - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(centerX + Math.cos(angle) * radius, centerY + Math.sin(angle) * radius);
        ctx.stroke();

        // Labels
        ctx.fillStyle = 'var(--text-secondary)';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(traitLabels[i], 
            centerX + Math.cos(angle) * (radius + 15), 
            centerY + Math.sin(angle) * (radius + 15) + 4);
    }

    // Draw data polygon
    ctx.beginPath();
    ctx.fillStyle = `${npc.color}40`;
    ctx.strokeStyle = npc.color;
    ctx.lineWidth = 2;

    for (let i = 0; i < traits.length; i++) {
        const value = personality[traits[i]] || 0.5;
        const angle = (Math.PI * 2 / traits.length) * i - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius * value;
        const y = centerY + Math.sin(angle) * radius * value;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Draw data points
    ctx.fillStyle = npc.color;
    for (let i = 0; i < traits.length; i++) {
        const value = personality[traits[i]] || 0.5;
        const angle = (Math.PI * 2 / traits.length) * i - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius * value;
        const y = centerY + Math.sin(angle) * radius * value;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
    }
}

function animateEmotionBars() {
    document.querySelectorAll('.emotion-bar-fill').forEach(bar => {
        const currentWidth = bar.style.width;
        bar.style.transition = 'width 0.5s ease-out';
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = currentWidth;
        }, 50);
    });
}

function getDominantEmotion(emotions) {
    if (!emotions) return 'joy';
    let maxEmotion = 'joy';
    let maxValue = 0;
    Object.entries(emotions).forEach(([emotion, value]) => {
        if (value > maxValue) {
            maxValue = value;
            maxEmotion = emotion;
        }
    });
    return maxEmotion;
}

function getCurrentLang() {
    return window.currentLang || 'en';
}

// Initialize demo - Router calls window.renderDemo() when navigating to this page
// No need for DOMContentLoaded listener since Router handles page rendering

// Export for app.js - called by Router when navigating to demo page
const _originalRenderDemo = renderDemo;
window.renderDemo = function() {
    _originalRenderDemo();
    
    // Show flow modal on first visit (only when this page is actually navigated to)
    if (!DemoState.tutorialShown) {
        DemoState.tutorialShown = true;
        const modal = document.getElementById('demo-flow-modal');
        if (modal) modal.classList.add('active');
    }
};
window.DemoState = DemoState;
