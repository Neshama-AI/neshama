/**
 * Templates Page - NPC preset template browsing, searching, importing
 */

// Template State
let templatePresets = [];
let templateFilter = '';
let templateCategory = '';

// Preset categories with icons
const PRESET_CATEGORIES = [
    { id: '', label_zh: '全部', label_en: 'All', icon: '📚' },
    { id: 'tavern', label_zh: '酒馆', label_en: 'Tavern', icon: '🍺' },
    { id: 'guard', label_zh: '守卫', label_en: 'Guard', icon: '🛡️' },
    { id: 'merchant', label_zh: '商人', label_en: 'Merchant', icon: '💰' },
    { id: 'mage', label_zh: '法师', label_en: 'Mage', icon: '🧙' },
    { id: 'quest', label_zh: '任务', label_en: 'Quest', icon: '📜' },
    { id: 'story', label_zh: '剧情', label_en: 'Story', icon: '📖' },
    { id: 'custom', label_zh: '自定义', label_en: 'Custom', icon: '✨' }
];

// Built-in presets (fallback when API unavailable)
const BUILTIN_PRESETS = [
    {
        id: 'tavern_keeper',
        name: 'Tavern Keeper',
        name_zh: '酒馆老板娘',
        emoji: '🍺',
        category: 'tavern',
        description: 'A friendly tavern keeper who loves chatting. Gets talkative when trusting, kicks out customers when angry.',
        description_zh: '友好的酒馆老板娘，喜欢和客人聊天。信任时话多，生气时赶人。',
        personality: { openness: 0.4, conscientiousness: 0.5, extraversion: 0.8, agreeableness: 0.75, neuroticism: 0.4 },
        tags: ['social', 'merchant', 'friendly'],
        dialogue_style: 'friendly'
    },
    {
        id: 'guard_captain',
        name: 'Guard Captain',
        name_zh: '守卫队长',
        emoji: '🛡️',
        category: 'guard',
        description: 'A disciplined guard captain who speaks concisely. Hostile to enemies, maintains order at all costs.',
        description_zh: '纪律严明的守卫队长，说话简洁。对敌人敌对，不惜一切代价维持秩序。',
        personality: { openness: 0.3, conscientiousness: 0.9, extraversion: 0.3, agreeableness: 0.4, neuroticism: 0.2 },
        tags: ['combat', 'authority', 'stoic'],
        dialogue_style: 'neutral'
    },
    {
        id: 'mystic_traveler',
        name: 'Mystic Traveler',
        name_zh: '神秘旅者',
        emoji: '🧙',
        category: 'mage',
        description: 'A mysterious traveler who speaks in riddles. May vanish when frightened, reveal deep secrets when trust is established.',
        description_zh: '神秘的旅者，说话谜语化。害怕时可能消失，信任后揭示深层秘密。',
        personality: { openness: 0.85, conscientiousness: 0.5, extraversion: 0.25, agreeableness: 0.55, neuroticism: 0.65 },
        tags: ['quest-giver', 'mysterious', 'magic'],
        dialogue_style: 'mysterious'
    },
    {
        id: 'blacksmith',
        name: 'Blacksmith',
        name_zh: '铁匠',
        emoji: '🔨',
        category: 'merchant',
        description: 'A gruff but skilled blacksmith. Takes pride in work, skeptical of outsiders, loyal to regular customers.',
        description_zh: '粗犷但技艺高超的铁匠。以工作为傲，对外人持怀疑态度，对老主顾忠诚。',
        personality: { openness: 0.25, conscientiousness: 0.8, extraversion: 0.35, agreeableness: 0.45, neuroticism: 0.35 },
        tags: ['crafting', 'merchant', 'gruff'],
        dialogue_style: 'gruff'
    },
    {
        id: 'court_mage',
        name: 'Court Mage',
        name_zh: '宫廷法师',
        emoji: '✨',
        category: 'mage',
        description: 'An erudite court mage obsessed with magical theory. Dismissive of "practical" concerns, helpful when intrigued.',
        description_zh: '博学的宫廷法师，沉迷魔法理论。对"实际问题"不屑一顾，感兴趣时乐于助人。',
        personality: { openness: 0.9, conscientiousness: 0.6, extraversion: 0.2, agreeableness: 0.35, neuroticism: 0.5 },
        tags: ['magic', 'scholar', 'arrogant'],
        dialogue_style: 'formal'
    },
    {
        id: 'street_urchin',
        name: 'Street Urchin',
        name_zh: '街头顽童',
        emoji: '🧒',
        category: 'custom',
        description: 'A quick-witted street urchin who survives by charm and cunning. May steal from you, may save your life.',
        description_zh: '机灵的街头顽童，靠魅力和狡猾生存。可能偷你的东西，也可能救你的命。',
        personality: { openness: 0.6, conscientiousness: 0.25, extraversion: 0.85, agreeableness: 0.5, neuroticism: 0.55 },
        tags: ['thief', 'informant', 'chaotic'],
        dialogue_style: 'casual'
    }
];

// Render Templates Page
async function renderTemplates() {
    const container = document.getElementById('page-templates');
    
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">${t('templates.title')}</h1>
            <p class="page-subtitle">${t('templates.subtitle')}</p>
        </div>
        
        <!-- Search & Filter -->
        <div class="card">
            <div class="template-filter-bar">
                <input type="text" id="template-search" class="form-input template-search-input" 
                    placeholder="${t('templates.searchPlaceholder')}" 
                    oninput="filterTemplates()" />
                <div class="template-categories">
                    ${PRESET_CATEGORIES.map(cat => `
                        <button class="category-btn ${cat.id === templateCategory ? 'active' : ''}" 
                            onclick="setTemplateCategory('${cat.id}')">
                            <span>${cat.icon}</span>
                            <span>${getCurrentLang() === 'zh' ? cat.label_zh : cat.label_en}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        </div>
        
        <!-- Template Grid -->
        <div id="template-grid" class="template-grid">
            <div class="loading">${t('common.loading')}</div>
        </div>
    `;
    
    await loadTemplates();
}

// Load templates
async function loadTemplates() {
    const grid = document.getElementById('template-grid');
    if (!grid) return;
    
    try {
        // Try loading from API
        const res = await API.game.listPresets ? API.game.listPresets() : Promise.reject('no presets api');
        templatePresets = (res.data?.presets || []).map(p => normalizePreset(p));
    } catch (e) {
        // Fallback to built-in presets
        templatePresets = BUILTIN_PRESETS;
    }
    
    renderTemplateGrid();
}

// Normalize preset data from API
function normalizePreset(preset) {
    const name = preset.name || preset.id || '';
    const personality = preset.personality || preset.ocean || {};
    return {
        id: preset.id || name.toLowerCase().replace(/\s+/g, '_'),
        name: name,
        name_zh: preset.name_zh || name,
        emoji: preset.emoji || getCategoryEmoji(preset.preset || preset.category),
        category: preset.preset || preset.category || 'custom',
        description: preset.description || '',
        description_zh: preset.description_zh || preset.description || '',
        personality: {
            openness: personality.openness || 0.5,
            conscientiousness: personality.conscientiousness || 0.5,
            extraversion: personality.extraversion || 0.5,
            agreeableness: personality.agreeableness || 0.5,
            neuroticism: personality.neuroticism || 0.5
        },
        tags: preset.tags || [],
        dialogue_style: preset.dialogue_style || 'neutral',
        _raw: preset
    };
}

function getCategoryEmoji(category) {
    const map = {
        tavern_keeper: '🍺', guard_captain: '🛡️', mystic_traveler: '🧙',
        blacksmith: '🔨', merchant: '💰', mage: '✨', custom: '✨'
    };
    return map[category] || '🎭';
}

function getCurrentLang() {
    return localStorage.getItem('neshama-lang') || 'zh';
}

// Filter templates
function filterTemplates() {
    templateFilter = document.getElementById('template-search')?.value?.toLowerCase() || '';
    renderTemplateGrid();
}

function setTemplateCategory(cat) {
    templateCategory = cat;
    // Update active state
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(
            PRESET_CATEGORIES.find(c => c.id === cat)?.[getCurrentLang() === 'zh' ? 'label_zh' : 'label_en'] || ''
        ));
    });
    // Simple: re-render the buttons properly
    const catContainer = document.querySelector('.template-categories');
    if (catContainer) {
        catContainer.innerHTML = PRESET_CATEGORIES.map(c => `
            <button class="category-btn ${c.id === templateCategory ? 'active' : ''}" 
                onclick="setTemplateCategory('${c.id}')">
                <span>${c.icon}</span>
                <span>${getCurrentLang() === 'zh' ? c.label_zh : c.label_en}</span>
            </button>
        `).join('');
    }
    renderTemplateGrid();
}

// Render template grid
function renderTemplateGrid() {
    const grid = document.getElementById('template-grid');
    if (!grid) return;
    
    let filtered = templatePresets;
    
    // Category filter
    if (templateCategory) {
        filtered = filtered.filter(p => p.category === templateCategory || p.id.includes(templateCategory));
    }
    
    // Text filter
    if (templateFilter) {
        filtered = filtered.filter(p =>
            (p.name || '').toLowerCase().includes(templateFilter) ||
            (p.name_zh || '').toLowerCase().includes(templateFilter) ||
            (p.description || '').toLowerCase().includes(templateFilter) ||
            (p.description_zh || '').toLowerCase().includes(templateFilter) ||
            (p.tags || []).some(t => t.toLowerCase().includes(templateFilter))
        );
    }
    
    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📚</div>
                <div class="empty-state-text">${t('templates.noTemplates')}</div>
            </div>
        `;
        return;
    }
    
    const lang = getCurrentLang();
    
    grid.innerHTML = filtered.map(preset => `
        <div class="template-card" onclick="showTemplateDetail('${preset.id}')">
            <div class="template-card-header">
                <span class="template-emoji">${preset.emoji}</span>
                <h3 class="template-name">${lang === 'zh' ? (preset.name_zh || preset.name) : preset.name}</h3>
            </div>
            <div class="template-ocean-preview">
                ${renderOceanMini(preset.personality)}
            </div>
            <p class="template-desc">${lang === 'zh' ? (preset.description_zh || preset.description) : preset.description}</p>
            <div class="template-tags">
                ${(preset.tags || []).slice(0, 3).map(tag => `<span class="tag tag-sm">${tag}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

// Render mini OCEAN bars
function renderOceanMini(ocean) {
    if (!ocean) return '';
    const traits = [
        { key: 'O', value: ocean.openness, color: '#6366f1' },
        { key: 'C', value: ocean.conscientiousness, color: '#22c55e' },
        { key: 'E', value: ocean.extraversion, color: '#f59e0b' },
        { key: 'A', value: ocean.agreeableness, color: '#ec4899' },
        { key: 'N', value: ocean.neuroticism, color: '#ef4444' }
    ];
    
    return `
        <div class="ocean-mini">
            ${traits.map(t => `
                <div class="ocean-mini-row">
                    <span class="ocean-mini-key">${t.key}</span>
                    <div class="ocean-mini-bar-bg">
                        <div class="ocean-mini-bar-fill" style="width: ${(t.value || 0) * 100}%; background: ${t.color};"></div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Show template detail
function showTemplateDetail(presetId) {
    const preset = templatePresets.find(p => p.id === presetId);
    if (!preset) return;
    
    const lang = getCurrentLang();
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'template-detail-modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <div class="template-detail-title">
                    <span class="template-emoji-lg">${preset.emoji}</span>
                    <div>
                        <h3>${lang === 'zh' ? (preset.name_zh || preset.name) : preset.name}</h3>
                        <span class="tag tag-sm">${preset.dialogue_style}</span>
                    </div>
                </div>
                <button class="modal-close" onclick="closeTemplateDetail()">&times;</button>
            </div>
            <div class="modal-body">
                <p class="template-detail-desc">${lang === 'zh' ? (preset.description_zh || preset.description) : preset.description}</p>
                
                <h4 class="section-title-sm">${t('templates.oceanProfile')}</h4>
                ${renderOceanDetail(preset.personality)}
                
                ${preset._raw?.initial_emotions ? `
                    <h4 class="section-title-sm">${t('templates.initialEmotions')}</h4>
                    <div class="emotion-presets-grid">
                        ${Object.entries(preset._raw.initial_emotions).map(([k, v]) => `
                            <div class="emotion-preset-item">
                                <span>${getEmotionEmoji(k)}</span>
                                <span>${k}</span>
                                <span>${(v * 100).toFixed(0)}%</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                
                ${preset._raw?.behaviors ? `
                    <h4 class="section-title-sm">${t('templates.behaviors')}</h4>
                    <div class="behavior-list">
                        ${Object.entries(preset._raw.behaviors).map(([key, items]) => `
                            <div class="behavior-group">
                                <span class="behavior-key">${key.replace(/_/g, ' ')}</span>
                                <ul class="behavior-items">
                                    ${(Array.isArray(items) ? items : [items]).map(item => 
                                        typeof item === 'string' ? `<li>${item}</li>` : 
                                        `<li>${Object.entries(item).map(([k,v]) => `${k}: ${v}`).join(', ')}</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeTemplateDetail()">${t('common.cancel')}</button>
                <button class="btn btn-primary" onclick="useTemplate('${preset.id}')">${t('templates.useTemplate')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function closeTemplateDetail() {
    const modal = document.getElementById('template-detail-modal');
    if (modal) modal.remove();
}

// Render detailed OCEAN profile
function renderOceanDetail(ocean) {
    if (!ocean) return '<p class="text-muted">—</p>';
    const traits = [
        { key: 'openness', label: t('ocean.openness'), value: ocean.openness, color: '#6366f1' },
        { key: 'conscientiousness', label: t('ocean.conscientiousness'), value: ocean.conscientiousness, color: '#22c55e' },
        { key: 'extraversion', label: t('ocean.extraversion'), value: ocean.extraversion, color: '#f59e0b' },
        { key: 'agreeableness', label: t('ocean.agreeableness'), value: ocean.agreeableness, color: '#ec4899' },
        { key: 'neuroticism', label: t('ocean.neuroticism'), value: ocean.neuroticism, color: '#ef4444' }
    ];
    
    return `
        <div class="ocean-detail">
            ${traits.map(t => `
                <div class="ocean-detail-row">
                    <span class="ocean-label">${t.label}</span>
                    <div class="ocean-bar-bg">
                        <div class="ocean-bar-fill" style="width: ${(t.value || 0) * 100}%; background: ${t.color};"></div>
                    </div>
                    <span class="ocean-value">${((t.value || 0) * 100).toFixed(0)}%</span>
                </div>
            `).join('')}
        </div>
    `;
}

// Use template - copy YAML to clipboard
async function useTemplate(presetId) {
    const preset = templatePresets.find(p => p.id === presetId);
    if (!preset) return;
    
    // Generate YAML from preset data
    const yaml = generateYaml(preset);
    await copyToClipboard(yaml);
    closeTemplateDetail();
}

// Generate YAML string from preset
function generateYaml(preset) {
    const p = preset.personality || {};
    const raw = preset._raw || {};
    
    let yaml = `# NPC Preset: ${preset.name}\n`;
    yaml += `# Generated from Neshama Template Library\n\n`;
    yaml += `name: ${preset.name_zh || preset.name}\n`;
    yaml += `preset: ${preset.id}\n\n`;
    yaml += `description: >\n  ${preset.description || preset.description_zh || ''}\n\n`;
    yaml += `personality:\n`;
    yaml += `  openness: ${p.openness || 0.5}\n`;
    yaml += `  conscientiousness: ${p.conscientiousness || 0.5}\n`;
    yaml += `  extraversion: ${p.extraversion || 0.5}\n`;
    yaml += `  agreeableness: ${p.agreeableness || 0.5}\n`;
    yaml += `  neuroticism: ${p.neuroticism || 0.5}\n\n`;
    
    if (raw.initial_emotions) {
        yaml += `initial_emotions:\n`;
        Object.entries(raw.initial_emotions).forEach(([k, v]) => {
            yaml += `  ${k}: ${v}\n`;
        });
        yaml += '\n';
    }
    
    if (raw.dialogue_style) {
        yaml += `dialogue_style: ${raw.dialogue_style}\n\n`;
    }
    
    if (raw.emotion_thresholds) {
        yaml += `emotion_thresholds:\n`;
        Object.entries(raw.emotion_thresholds).forEach(([emotion, thresholds]) => {
            yaml += `  ${emotion}:\n`;
            Object.entries(thresholds).forEach(([key, val]) => {
                yaml += `    ${key}: ${val}\n`;
            });
        });
        yaml += '\n';
    }
    
    if (raw.behaviors) {
        yaml += `behaviors:\n`;
        Object.entries(raw.behaviors).forEach(([key, items]) => {
            yaml += `  ${key}:\n`;
            (Array.isArray(items) ? items : [items]).forEach(item => {
                if (typeof item === 'string') {
                    yaml += `    - ${item}\n`;
                } else {
                    yaml += `    - ${Object.entries(item).map(([k,v]) => `${k}: ${v}`).join(', ')}\n`;
                }
            });
        });
        yaml += '\n';
    }
    
    return yaml;
}
