/**
 * Composite Emotion Page - Composite emotion synthesis and management
 */

let compositeEmotionData = {
    emotions: {},
    composite: null,
    triggered: []
};

// Base emotion presets for synthesis
const BASE_EMOTIONS = [
    { id: 'joy', label_zh: '喜悦', label_en: 'Joy', emoji: '😊', color: '#00d4aa' },
    { id: 'sadness', label_zh: '悲伤', label_en: 'Sadness', emoji: '😢', color: '#7c5cff' },
    { id: 'anger', label_zh: '愤怒', label_en: 'Anger', emoji: '😠', color: '#ff6b35' },
    { id: 'fear', label_zh: '恐惧', label_en: 'Fear', emoji: '😨', color: '#7c5cff' },
    { id: 'surprise', label_zh: '惊讶', label_en: 'Surprise', emoji: '😮', color: '#ff6b35' },
    { id: 'disgust', label_zh: '厌恶', label_en: 'Disgust', emoji: '🤢', color: '#00d4aa' },
    { id: 'trust', label_zh: '信任', label_en: 'Trust', emoji: '🤝', color: '#7c5cff' },
    { id: 'anticipation', label_zh: '期待', label_en: 'Anticipation', emoji: '🤔', color: '#00d4aa' }
];

// Get localized label for base emotion
function getBaseEmotionLabel(emotion) {
    const currentLang = localStorage.getItem('neshama-lang') || 'zh';
    return currentLang === 'zh' ? emotion.label_zh : emotion.label_en;
}

// Recipe presets for one-click loading
const EMOTION_RECIPES = [
    { name: 'euphoria', label: { zh: '欣快', en: 'Euphoria' }, components: { joy: 0.9, trust: 0.7, anticipation: 0.6 } },
    { name: 'melancholy', label: { zh: '忧郁', en: 'Melancholy' }, components: { sadness: 0.8, fear: 0.4, trust: 0.3 } },
    { name: 'rage', label: { zh: '狂怒', en: 'Rage' }, components: { anger: 0.95, fear: 0.5, disgust: 0.3 } },
    { name: 'anxiety', label: { zh: '焦虑', en: 'Anxiety' }, components: { fear: 0.8, anticipation: 0.7, sadness: 0.3 } },
    { name: 'serenity', label: { zh: '宁静', en: 'Serenity' }, components: { joy: 0.6, trust: 0.7, sadness: 0.1 } },
    { name: 'confusion', label: { zh: '困惑', en: 'Confusion' }, components: { surprise: 0.7, fear: 0.3, anticipation: 0.5 } },
    { name: 'contempt', label: { zh: '轻蔑', en: 'Contempt' }, components: { anger: 0.6, disgust: 0.7, trust: 0.1 } },
    { name: 'hope', label: { zh: '希望', en: 'Hope' }, components: { anticipation: 0.8, joy: 0.5, trust: 0.4 } },
    { name: 'grief', label: { zh: '悲痛', en: 'Grief' }, components: { sadness: 0.95, fear: 0.3, joy: 0.0 } },
    { name: 'admiration', label: { zh: '钦佩', en: 'Admiration' }, components: { trust: 0.8, joy: 0.5, surprise: 0.3 } },
    { name: 'interest', label: { zh: '兴趣', en: 'Interest' }, components: { anticipation: 0.7, surprise: 0.5, trust: 0.4 } },
    { name: 'envy', label: { zh: '嫉妒', en: 'Envy' }, components: { anger: 0.5, sadness: 0.6, anticipation: 0.4 } },
    { name: 'pride', label: { zh: '自豪', en: 'Pride' }, components: { joy: 0.7, anger: 0.3, anticipation: 0.5 } },
    { name: 'remorse', label: { zh: '懊悔', en: 'Remorse' }, components: { sadness: 0.7, fear: 0.4, disgust: 0.3 } },
    { name: 'amazement', label: { zh: '惊异', en: 'Amazement' }, components: { surprise: 0.9, fear: 0.3, joy: 0.4 } }
];

// Render Composite Emotion Page
async function renderCompositeEmotion() {
    const container = document.getElementById('page-composite-emotion');
    
    try {
        const [emotionsRes, triggeredRes] = await Promise.all([
            API.compositeEmotion.getEmotions('default'),
            API.compositeEmotion.getTriggered('default', 0.7)
        ]);
        
        compositeEmotionData.emotions = emotionsRes.data.emotions || {};
        compositeEmotionData.triggered = triggeredRes.data.triggered || [];
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('compositeEmotion.title')}</h1>
                <p class="page-subtitle">${t('compositeEmotion.subtitle')}</p>
            </div>
            
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('compositeEmotion.currentComposite')}</span>
                        <span class="tag tag-amber">${t('dashboard.live')}</span>
                    </div>
                    <div id="composite-display" class="mt-4">
                        ${renderCompositeDisplay()}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('compositeEmotion.activeEmotions')}</span>
                        <button class="btn btn-sm btn-secondary" onclick="clearAllEmotions()">${t('common.clear')}</button>
                    </div>
                    <div id="emotions-display" class="mt-4">
                        ${renderEmotionsList()}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('compositeEmotion.synthesize')}</span>
                </div>
                <div class="mt-4">
                    ${renderSynthesisPanel()}
                </div>
            </div>
            
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('compositeEmotion.timeDecay')}</span>
                    </div>
                    <div class="mt-4">
                        <div class="flex gap-2 mb-3">
                            <input type="number" id="tick-delta" class="form-input" value="60" min="1" max="3600" style="width: 120px;">
                            <span class="text-muted" style="line-height: 40px;">${t('compositeEmotion.seconds')}</span>
                            <button class="btn btn-primary" onclick="performTick()">${t('compositeEmotion.tick')}</button>
                        </div>
                        <div class="form-label">${t('compositeEmotion.decayLog')}</div>
                        <div id="decay-log" class="mt-2" style="max-height: 150px; overflow-y: auto;">
                            <div class="text-muted" style="padding: 8px;">${t('common.noData')}</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('compositeEmotion.triggeredBehaviors')}</span>
                        <span class="tag tag-primary">${t('compositeEmotion.threshold')}: 0.7</span>
                    </div>
                    <div id="triggered-display" class="mt-4">
                        ${renderTriggeredList()}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('compositeEmotion.recipes')}</span>
                </div>
                <div class="mt-4">
                    ${renderRecipeGrid()}
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Composite emotion load error:', error);
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('compositeEmotion.title')}</h1>
                <p class="page-subtitle">${t('compositeEmotion.subtitle')}</p>
            </div>
            <div class="card">
                <div class="empty-state">
                    <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">Emotion</div>
                    <div class="empty-state-text">${t('compositeEmotion.failedLoad')}</div>
                    <div class="text-muted mt-2" style="font-size: 12px;">${error.message || ''}</div>
                    <button class="btn btn-primary mt-4" onclick="renderCompositeEmotion()">${t('common.retry')}</button>
                </div>
            </div>
        `;
        Toast.show(t('common.error'), 'error');
    }
}

// Render composite emotion display
function renderCompositeDisplay() {
    if (!compositeEmotionData.composite) {
        return `
            <div class="empty-state" style="padding: 20px;">
                <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">Emotion</div>
                <div class="empty-state-text">${t('compositeEmotion.noComposite')}</div>
            </div>
        `;
    }
    
    const composite = compositeEmotionData.composite;
    return `
        <div class="flex items-center gap-4">
            <div style="font-size: 64px;">${getCompositeEmoji(composite.name)}</div>
            <div>
                <div style="font-size: 24px; font-weight: 600;">${composite.name}</div>
                <div class="mt-2">
                    <div class="form-label">${t('compositeEmotion.intensity')}</div>
                    <div class="progress-bar" style="width: 200px;">
                        <div class="progress-fill" style="width: ${composite.intensity * 100}%;"></div>
                    </div>
                    <span class="text-accent">${(composite.intensity * 100).toFixed(0)}%</span>
                </div>
                ${composite.is_novel ? `<span class="tag tag-amber mt-3">${t('compositeEmotion.novel')}</span>` : ''}
            </div>
        </div>
        <div class="mt-4" style="padding-top: 16px; border-top: 1px solid var(--border-color);">
            <div class="form-label">${t('compositeEmotion.components')}</div>
            <div class="flex gap-2 mt-2" style="flex-wrap: wrap;">
                ${Object.entries(composite.components || {}).map(([emotion, weight]) => {
                    const baseEmotion = BASE_EMOTIONS.find(e => e.id === emotion);
                    return `<span class="tag" style="background: ${baseEmotion?.color}33; color: ${baseEmotion?.color || '#fff'};">
                        ${baseEmotion?.emoji || ''} ${emotion}: ${(weight * 100).toFixed(0)}%
                    </span>`;
                }).join('')}
            </div>
        </div>
    `;
}

// Render active emotions list
function renderEmotionsList() {
    const emotions = compositeEmotionData.emotions;
    const emotionEntries = Object.entries(emotions);
    
    if (emotionEntries.length === 0) {
        return `<div class="text-muted">${t('common.noData')}</div>`;
    }
    
    return emotionEntries.map(([emotion, intensity]) => {
        const baseEmotion = BASE_EMOTIONS.find(e => e.id === emotion);
        return `
            <div class="flex items-center justify-between mb-2" style="padding: 10px; background: var(--bg-tertiary); border-radius: 8px;">
                <div class="flex items-center gap-2">
                    <span class="emotion-dot" style="background:${baseEmotion?.color || '#94a3b8'}"></span> <span>${baseEmotion?.label_en || baseEmotion?.label_zh || 'Emotion'}</span>
                    <span>${baseEmotion ? getBaseEmotionLabel(baseEmotion) : emotion}</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="progress-bar" style="width: 100px;">
                        <div class="progress-fill" style="width: ${intensity * 100}%; background: ${baseEmotion?.color || 'var(--accent-primary)'};"></div>
                    </div>
                    <span class="text-accent" style="min-width: 45px; text-align: right;">${(intensity * 100).toFixed(0)}%</span>
                </div>
            </div>
        `;
    }).join('');
}

// Render synthesis panel
function renderSynthesisPanel() {
    return `
        <div class="mb-4">
            <div class="form-label">${t('compositeEmotion.selectEmotions')}</div>
            <div class="flex gap-2" style="flex-wrap: wrap;">
                ${BASE_EMOTIONS.map(emotion => `
                    <label class="emotion-selector ${compositeEmotionData.emotions[emotion.id] ? 'selected' : ''}" 
                           style="--emotion-color: ${emotion.color};">
                        <input type="checkbox" id="emotion-${emotion.id}" value="${emotion.id}" 
                               onchange="updateSynthesisPanel()">
                        <span style="font-size: 24px;">${emotion.emoji}</span>
                        <span>${getBaseEmotionLabel(emotion)}</span>
                    </label>
                `).join('')}
            </div>
        </div>
        
        <div id="weight-sliders">
            ${BASE_EMOTIONS.map(emotion => `
                <div class="form-group weight-slider" id="slider-${emotion.id}" style="display: none;">
                    <label class="form-label">
                        <span style="font-size: 16px; margin-right: 8px;">${emotion.emoji}</span>
                        ${getBaseEmotionLabel(emotion)} ${t('compositeEmotion.weight')}
                    </label>
                    <div class="flex items-center gap-2">
                        <input type="range" id="weight-${emotion.id}" min="0" max="100" value="50"
                               style="flex: 1;" oninput="updateSynthesisDisplay()">
                        <span id="weight-value-${emotion.id}" class="text-accent" style="min-width: 45px;">50%</span>
                    </div>
                </div>
            `).join('')}
        </div>
        
        <div class="flex gap-2 mt-4">
            <button class="btn btn-primary" onclick="synthesizeComposite()">${t('compositeEmotion.synthesize')}</button>
            <button class="btn btn-secondary" onclick="resetSynthesis()">${t('common.reset')}</button>
        </div>
        
        <style>
            .emotion-selector {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 4px;
                padding: 12px 16px;
                background: var(--bg-tertiary);
                border: 2px solid var(--border-color);
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.2s;
                min-width: 80px;
            }
            .emotion-selector input {
                display: none;
            }
            .emotion-selector:hover {
                border-color: var(--emotion-color);
                background: var(--bg-card-hover);
            }
            .emotion-selector.selected {
                border-color: var(--emotion-color);
                background: color-mix(in srgb, var(--emotion-color) 15%, transparent);
            }
            .emotion-selector span:last-child {
                font-size: 12px;
                color: var(--text-secondary);
            }
        </style>
    `;
}

// Update synthesis panel visibility
function updateSynthesisPanel() {
    BASE_EMOTIONS.forEach(emotion => {
        const checkbox = document.getElementById(`emotion-${emotion.id}`);
        const slider = document.getElementById(`slider-${emotion.id}`);
        const selector = checkbox?.closest('.emotion-selector');
        
        if (checkbox && slider) {
            slider.style.display = checkbox.checked ? 'block' : 'none';
            if (selector) {
                selector.classList.toggle('selected', checkbox.checked);
            }
        }
    });
}

// Update synthesis display
function updateSynthesisDisplay() {
    BASE_EMOTIONS.forEach(emotion => {
        const slider = document.getElementById(`weight-${emotion.id}`);
        const valueDisplay = document.getElementById(`weight-value-${emotion.id}`);
        if (slider && valueDisplay) {
            valueDisplay.textContent = `${slider.value}%`;
        }
    });
}

// Synthesize composite emotion
async function synthesizeComposite() {
    const selectedEmotions = {};
    
    BASE_EMOTIONS.forEach(emotion => {
        const checkbox = document.getElementById(`emotion-${emotion.id}`);
        const slider = document.getElementById(`weight-${emotion.id}`);
        if (checkbox?.checked && slider) {
            selectedEmotions[emotion.id] = parseInt(slider.value) / 100;
        }
    });
    
    if (Object.keys(selectedEmotions).length === 0) {
        return;
    }
    
    try {
        // Set each selected emotion
        for (const [emotionId, intensity] of Object.entries(selectedEmotions)) {
            await API.compositeEmotion.setEmotion('default', emotionId, intensity);
        }
        
        // Synthesize
        const result = await API.compositeEmotion.synthesize('default');
        compositeEmotionData.composite = result.data;
        
        // Refresh
        await refreshEmotionData();
        await renderCompositeEmotion();
        
    } catch (error) {
        console.error('Synthesis error:', error);
        Toast.show(error.message || t('common.error'), 'error');
    }
}

// Reset synthesis panel
function resetSynthesis() {
    BASE_EMOTIONS.forEach(emotion => {
        const checkbox = document.getElementById(`emotion-${emotion.id}`);
        const slider = document.getElementById(`weight-${emotion.id}`);
        if (checkbox) checkbox.checked = false;
        if (slider) slider.value = 50;
    });
    updateSynthesisPanel();
    updateSynthesisDisplay();
}

// Perform time tick
async function performTick() {
    const deltaInput = document.getElementById('tick-delta');
    const delta = parseInt(deltaInput?.value || 60);
    
    try {
        const result = await API.compositeEmotion.tick('default', delta);
        compositeEmotionData.emotions = result.data.emotions || {};
        
        // Update decay log
        const logContainer = document.getElementById('decay-log');
        if (logContainer) {
            const logEntry = document.createElement('div');
            logEntry.style.cssText = 'padding: 8px; background: var(--bg-tertiary); border-radius: 4px; margin-bottom: 8px;';
            logEntry.innerHTML = `
                <div class="text-muted" style="font-size: 11px;">${new Date().toLocaleTimeString()}</div>
                <div>${t('compositeEmotion.tickApplied')}: ${delta}s</div>
            `;
            logContainer.insertBefore(logEntry, logContainer.firstChild);
            
            // Keep only last 10 entries
            while (logContainer.children.length > 10) {
                logContainer.removeChild(logContainer.lastChild);
            }
        }
        
        // Refresh displays
        const emotionsDisplay = document.getElementById('emotions-display');
        if (emotionsDisplay) {
            emotionsDisplay.innerHTML = renderEmotionsList();
        }
        
        // Refresh triggered
        await refreshTriggeredData();
        
    } catch (error) {
        console.error('Tick error:', error);
        Toast.show(error.message || t('common.error'), 'error');
    }
}

// Clear all emotions
async function clearAllEmotions() {
    try {
        await API.compositeEmotion.clear('default');
        compositeEmotionData.emotions = {};
        compositeEmotionData.composite = null;
        compositeEmotionData.triggered = [];
        await renderCompositeEmotion();
        Toast.show(t('common.success'), 'success');
    } catch (error) {
        console.error('Clear error:', error);
        Toast.show(error.message || t('common.error'), 'error');
    }
}

// Render triggered behaviors
function renderTriggeredList() {
    const triggered = compositeEmotionData.triggered;
    
    if (!triggered || triggered.length === 0) {
        return `<div class="text-muted">${t('common.noData')}</div>`;
    }
    
    return triggered.map(item => {
        const baseEmotion = BASE_EMOTIONS.find(e => e.id === item.emotion);
        return `
            <div class="flex items-center justify-between mb-2" style="padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
                <div class="flex items-center gap-3">
                    <span class="emotion-dot" style="background:${baseEmotion?.color || '#94a3b8'};width:12px;height:12px;"></span> <span>${baseEmotion?.label_en || baseEmotion?.label_zh || 'Emotion'}</span>
                    <div>
                        <div style="font-weight: 500;">${item.behavior || item.emotion}</div>
                        <div class="text-muted" style="font-size: 12px;">${item.description || (baseEmotion ? getBaseEmotionLabel(baseEmotion) : item.emotion)}</div>
                    </div>
                </div>
                <span class="text-accent">${(item.intensity * 100).toFixed(0)}%</span>
            </div>
        `;
    }).join('');
}

// Render recipe grid
function renderRecipeGrid() {
    return `
        <div class="flex gap-3" style="flex-wrap: wrap;">
            ${EMOTION_RECIPES.map(recipe => {
                const currentLang = localStorage.getItem('neshama-lang') || 'zh';
                const label = currentLang === 'zh' ? recipe.label.zh : recipe.label.en;
                return `
                    <button class="btn btn-secondary" style="padding: 8px 12px; font-size: 13px;" 
                            onclick="loadRecipe('${recipe.name}')">
                        ${label}
                    </button>
                `;
            }).join('')}
        </div>
    `;
}

// Load recipe
async function loadRecipe(recipeName) {
    const recipe = EMOTION_RECIPES.find(r => r.name === recipeName);
    if (!recipe) return;
    
    try {
        // Clear first
        await API.compositeEmotion.clear('default');
        
        // Set each emotion
        for (const [emotionId, intensity] of Object.entries(recipe.components)) {
            await API.compositeEmotion.setEmotion('default', emotionId, intensity);
        }
        
        // Synthesize
        const result = await API.compositeEmotion.synthesize('default');
        compositeEmotionData.composite = result.data;
        
        // Refresh
        await refreshEmotionData();
        await renderCompositeEmotion();
        
    } catch (error) {
        console.error('Load recipe error:', error);
    }
}

// Refresh emotion data
async function refreshEmotionData() {
    try {
        const emotionsRes = await API.compositeEmotion.getEmotions('default');
        compositeEmotionData.emotions = emotionsRes.data.emotions || {};
        
        await refreshTriggeredData();
    } catch (error) {
        console.error('Refresh error:', error);
    }
}

// Refresh triggered data
async function refreshTriggeredData() {
    try {
        const triggeredRes = await API.compositeEmotion.getTriggered('default', 0.7);
        compositeEmotionData.triggered = triggeredRes.data.triggered || [];
        
        const triggeredDisplay = document.getElementById('triggered-display');
        if (triggeredDisplay) {
            triggeredDisplay.innerHTML = renderTriggeredList();
        }
    } catch (error) {
        console.error('Refresh triggered error:', error);
    }
}

// Get composite emoji based on name
function getCompositeEmoji(name) {
    const emojiMap = {
        'euphoria': 'Euphoria', 'melancholy': 'Melancholy', 'rage': 'Rage', 'anxiety': 'Anxiety',
        'serenity': 'Serenity', 'confusion': 'Confusion', 'contempt': 'Contempt', 'hope': 'Hope',
        'grief': 'Grief', 'admiration': 'Admiration', 'interest': 'Interest', 'envy': 'Envy',
        'pride': 'Pride', 'remorse': 'Remorse', 'amazement': 'Amazement', 'joy': 'Joy',
        'sadness': 'Sad', 'anger': 'Anger', 'fear': 'Fear', 'surprise': 'Surprise'
    };
    return emojiMap[name?.toLowerCase()] || 'Emotion';
}

// Get emotion emoji
function getEmotionEmoji(emotion) {
    const baseEmotion = BASE_EMOTIONS.find(e => e.id === emotion);
    return baseEmotion?.label_en || baseEmotion?.label_zh || 'Emotion';
}

// Format date
function formatDate(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
