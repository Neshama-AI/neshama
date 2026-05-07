/**
 * Debug Page - Combined debugging panel for Emotion, Memory, Relations, Evolution
 * Merged from: emotion.js, composite-emotion.js, entity-graph.js, memory.js, evolution.js
 */

// Debug State
const DebugState = {
    activeTab: 'emotion',
    targetId: '',       // DID or NPC ID to inspect
    emotionData: null,
    memoryData: {},
    currentLayer: 'L0',
    relationData: { entities: [], relations: [] },
    evolutionData: null
};

// Tab definitions
const DEBUG_TABS = [
    { id: 'emotion', label_zh: '情绪', label_en: 'Emotion', icon: '❤️' },
    { id: 'memory', label_zh: '记忆', label_en: 'Memory', icon: '🧠' },
    { id: 'relations', label_zh: '关系图谱', label_en: 'Relations', icon: '🕸️' },
    { id: 'evolution', label_zh: '演化', label_en: 'Evolution', icon: '📈' }
];

// Render Debug Page
async function renderDebug() {
    const container = document.getElementById('page-debug');
    
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">${t('debug.title')}</h1>
            <p class="page-subtitle">${t('debug.subtitle')}</p>
        </div>
        
        <!-- Target Input -->
        <div class="card">
            <div class="debug-target-bar">
                <div class="form-group" style="flex:1; margin:0;">
                    <input type="text" id="debug-target-input" class="form-input" 
                        placeholder="${t('debug.enterTargetId')}" 
                        value="${DebugState.targetId}"
                        onkeydown="if(event.key==='Enter') loadDebugTarget()" />
                </div>
                <button class="btn btn-primary" onclick="loadDebugTarget()">${t('common.search')}</button>
            </div>
        </div>
        
        <!-- Tab Bar -->
        <div class="debug-tabs">
            ${DEBUG_TABS.map(tab => `
                <button class="debug-tab ${tab.id === DebugState.activeTab ? 'active' : ''}" 
                    onclick="switchDebugTab('${tab.id}')">
                    <span class="debug-tab-icon">${tab.icon}</span>
                    <span class="debug-tab-text">${getCurrentLang() === 'zh' ? tab.label_zh : tab.label_en}</span>
                </button>
            `).join('')}
        </div>
        
        <!-- Tab Content -->
        <div id="debug-tab-content">
            <div class="empty-state">
                <div class="empty-state-icon">🔬</div>
                <div class="empty-state-text">${t('debug.selectTarget')}</div>
            </div>
        </div>
    `;
    
    // If we have a target, load data
    if (DebugState.targetId) {
        await loadDebugTarget();
    }
}

function getCurrentLang() {
    return localStorage.getItem('neshama-lang') || 'zh';
}

// Load debug target data
async function loadDebugTarget() {
    const input = document.getElementById('debug-target-input');
    DebugState.targetId = input ? input.value.trim() : '';
    
    if (!DebugState.targetId) {
        Toast.show(t('debug.enterTargetId'), 'warning');
        return;
    }
    
    await renderActiveTab();
}

// Switch debug tab
async function switchDebugTab(tabId) {
    DebugState.activeTab = tabId;
    
    // Update tab active state
    document.querySelectorAll('.debug-tab').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(
            DEBUG_TABS.find(t => t.id === tabId)?.[getCurrentLang() === 'zh' ? 'label_zh' : 'label_en'] || ''
        ));
    });
    
    // Proper re-render of tabs
    const tabContainer = document.querySelector('.debug-tabs');
    if (tabContainer) {
        tabContainer.innerHTML = DEBUG_TABS.map(tab => `
            <button class="debug-tab ${tab.id === DebugState.activeTab ? 'active' : ''}" 
                onclick="switchDebugTab('${tab.id}')">
                <span class="debug-tab-icon">${tab.icon}</span>
                <span class="debug-tab-text">${getCurrentLang() === 'zh' ? tab.label_zh : tab.label_en}</span>
            </button>
        `).join('');
    }
    
    await renderActiveTab();
}

// Render active tab
async function renderActiveTab() {
    const content = document.getElementById('debug-tab-content');
    if (!content) return;
    
    if (!DebugState.targetId) {
        content.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔬</div>
                <div class="empty-state-text">${t('debug.selectTarget')}</div>
            </div>
        `;
        return;
    }
    
    content.innerHTML = `<div class="loading">${t('common.loading')}</div>`;
    
    switch (DebugState.activeTab) {
        case 'emotion':
            await renderDebugEmotion(content);
            break;
        case 'memory':
            await renderDebugMemory(content);
            break;
        case 'relations':
            await renderDebugRelations(content);
            break;
        case 'evolution':
            await renderDebugEvolution(content);
            break;
    }
}

// ========================================
// Emotion Tab
// ========================================
async function renderDebugEmotion(container) {
    try {
        const [currentRes, historyRes] = await Promise.allSettled([
            API.game.getEmotion(DebugState.targetId),
            API.game.getEmotionHistory(DebugState.targetId, 20)
        ]);
        
        const current = currentRes.status === 'fulfilled' ? (currentRes.value.data || {}) : {};
        const history = historyRes.status === 'fulfilled' ? (historyRes.value.data || []) : [];
        
        DebugState.emotionData = current;
        
        const emotions = current.emotions || current.primary || {};
        const ocean = current.ocean || current.personality || {};
        
        container.innerHTML = `
            <div class="grid-2">
                <!-- Emotion 9-Grid -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('debug.emotionGrid')}</span>
                        <span class="tag tag-amber">${t('dashboard.live')}</span>
                    </div>
                    <div class="emotion-grid-9">
                        ${renderEmotionGrid(emotions)}
                    </div>
                </div>
                
                <!-- OCEAN Radar -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('debug.oceanRadar')}</span>
                    </div>
                    <div class="canvas-container" style="height: 220px;">
                        <canvas id="debug-ocean-canvas"></canvas>
                    </div>
                    ${ocean ? renderOceanTextValues(ocean) : '<p class="text-muted mt-2">—</p>'}
                </div>
            </div>
            
            <!-- Emotion History Curve -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('debug.emotionHistory')}</span>
                </div>
                <div class="canvas-container" style="height: 200px;">
                    <canvas id="debug-emotion-history-canvas"></canvas>
                </div>
            </div>
        `;
        
        // Draw charts
        setTimeout(() => {
            drawOceanRadar(ocean);
            drawEmotionHistoryCurve(history);
        }, 100);
        
    } catch (error) {
        container.innerHTML = `<div class="empty-state-sm">${t('emotion.failedLoad')}</div>`;
    }
}

// Render 9-grid emotion display
function renderEmotionGrid(emotions) {
    const emotionList = [
        { key: 'joy', label: t('emotion.joy'), emoji: '😊' },
        { key: 'trust', label: t('emotion.trust'), emoji: '🤝' },
        { key: 'fear', label: t('emotion.fear'), emoji: '😨' },
        { key: 'surprise', label: t('emotion.surprise'), emoji: '😮' },
        { key: 'anticipation', label: t('emotion.anticipation'), emoji: '🤔' },
        { key: 'sadness', label: t('emotion.sadness'), emoji: '😢' },
        { key: 'anger', label: t('emotion.anger'), emoji: '😠' },
        { key: 'disgust', label: t('emotion.disgust'), emoji: '🤢' },
    ];
    
    return emotionList.map(e => {
        const value = emotions[e.key] || emotions[e.key + '_intensity'] || 0;
        const pct = Math.min(value * 100, 100);
        return `
            <div class="emotion-grid-item" style="--intensity: ${pct}%">
                <span class="emotion-grid-emoji">${e.emoji}</span>
                <span class="emotion-grid-label">${e.label}</span>
                <span class="emotion-grid-value">${(value * 100).toFixed(0)}%</span>
                <div class="emotion-grid-bar" style="width: ${pct}%"></div>
            </div>
        `;
    }).join('');
}

// Render OCEAN text values
function renderOceanTextValues(ocean) {
    const traits = [
        { key: 'openness', label: t('ocean.openness') },
        { key: 'conscientiousness', label: t('ocean.conscientiousness') },
        { key: 'extraversion', label: t('ocean.extraversion') },
        { key: 'agreeableness', label: t('ocean.agreeableness') },
        { key: 'neuroticism', label: t('ocean.neuroticism') }
    ];
    
    return `<div class="ocean-mini mt-3">
        ${traits.map(tr => `
            <div class="ocean-mini-row">
                <span class="ocean-mini-key" style="width:60px">${tr.label}</span>
                <div class="ocean-mini-bar-bg" style="flex:1">
                    <div class="ocean-mini-bar-fill" style="width: ${(ocean[tr.key] || 0) * 100}%"></div>
                </div>
                <span class="ocean-value-sm">${((ocean[tr.key] || 0) * 100).toFixed(0)}%</span>
            </div>
        `).join('')}
    </div>`;
}

// Draw OCEAN radar chart on canvas
function drawOceanRadar(ocean) {
    const canvas = document.getElementById('debug-ocean-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const w = canvas.parentElement?.clientWidth || 400;
    const h = canvas.parentElement?.clientHeight || 220;
    canvas.width = w;
    canvas.height = h;
    
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(cx, cy) - 40;
    
    const labels = ['O', 'C', 'E', 'A', 'N'];
    const values = [
        ocean?.openness || 0,
        ocean?.conscientiousness || 0,
        ocean?.extraversion || 0,
        ocean?.agreeableness || 0,
        ocean?.neuroticism || 0
    ];
    
    ctx.clearRect(0, 0, w, h);
    
    // Draw concentric pentagons
    for (let ring = 1; ring <= 4; ring++) {
        const rr = r * ring / 4;
        ctx.beginPath();
        for (let i = 0; i < 5; i++) {
            const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
            const x = cx + rr * Math.cos(angle);
            const y = cy + rr * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.stroke();
    }
    
    // Draw data polygon
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
        const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
        const val = values[i];
        const x = cx + r * val * Math.cos(angle);
        const y = cy + r * val * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(75, 147, 255, 0.2)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(75, 147, 255, 0.8)';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Draw points and labels
    for (let i = 0; i < 5; i++) {
        const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
        const val = values[i];
        const x = cx + r * val * Math.cos(angle);
        const y = cy + r * val * Math.sin(angle);
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(75, 147, 255, 1)';
        ctx.fill();
        
        // Label
        const lx = cx + (r + 20) * Math.cos(angle);
        const ly = cy + (r + 20) * Math.sin(angle);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(labels[i], lx, ly);
    }
}

// Draw emotion history curve
function drawEmotionHistoryCurve(history) {
    const canvas = document.getElementById('debug-emotion-history-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const w = canvas.parentElement?.clientWidth || 800;
    const h = canvas.parentElement?.clientHeight || 200;
    canvas.width = w;
    canvas.height = h;
    
    ctx.clearRect(0, 0, w, h);
    
    if (!history || history.length === 0) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(t('common.noData'), w / 2, h / 2);
        return;
    }
    
    const padding = 40;
    const chartW = w - padding * 2;
    const chartH = h - padding * 2;
    
    // Grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartH * i / 4);
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(w - padding, y);
        ctx.stroke();
    }
    
    // Line
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(75, 147, 255, 0.8)';
    ctx.lineWidth = 2;
    
    history.forEach((point, i) => {
        const x = padding + (chartW * i / Math.max(history.length - 1, 1));
        const intensity = point.intensity || point.intensity_avg || 0.5;
        const y = padding + chartH - (intensity * chartH);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // Fill
    const lastX = padding + chartW;
    ctx.lineTo(lastX, padding + chartH);
    ctx.lineTo(padding, padding + chartH);
    ctx.closePath();
    ctx.fillStyle = 'rgba(75, 147, 255, 0.1)';
    ctx.fill();
}


// ========================================
// Memory Tab
// ========================================
async function renderDebugMemory(container) {
    try {
        const [layersRes, statsRes] = await Promise.allSettled([
            API.memory.getLayers(),
            API.memory.getStats()
        ]);
        
        const layers = layersRes.status === 'fulfilled' ? (layersRes.value.data?.layers || ['L0', 'L1', 'L2']) : ['L0', 'L1', 'L2'];
        const stats = statsRes.status === 'fulfilled' ? (statsRes.value.data || {}) : {};
        
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('memory.layers')}</span>
                    <span class="tag tag-primary">${t('memory.total')}: ${stats.total_memories || 0}</span>
                </div>
                <div class="memory-layer-tabs">
                    ${layers.map(layer => `
                        <button class="layer-tab ${layer === DebugState.currentLayer ? 'active' : ''}" 
                            onclick="switchDebugLayer('${layer}')">
                            ${getLayerName(layer)}
                        </button>
                    `).join('')}
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title" id="debug-layer-title">${getLayerName(DebugState.currentLayer)}</span>
                    <div class="flex gap-2">
                        <input type="text" id="debug-memory-search" class="form-input" style="width:200px;" 
                            placeholder="${t('memory.searchPlaceholder')}" onkeyup="searchDebugMemories()" />
                    </div>
                </div>
                <div id="debug-memory-list" class="mt-4">
                    <div class="loading">${t('memory.loading')}</div>
                </div>
            </div>
        `;
        
        await loadDebugLayerMemories(DebugState.currentLayer);
        
    } catch (error) {
        container.innerHTML = `<div class="empty-state-sm">${t('memory.failedLoad')}</div>`;
    }
}

function getLayerName(layer) {
    const map = {
        'L0': t('memory.layer.l0'),
        'L1': t('memory.layer.l1'),
        'L2': t('memory.layer.l2')
    };
    return map[layer] || layer;
}

async function switchDebugLayer(layer) {
    DebugState.currentLayer = layer;
    
    document.querySelectorAll('.layer-tab').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.trim() === getLayerName(layer));
    });
    
    const title = document.getElementById('debug-layer-title');
    if (title) title.textContent = getLayerName(layer);
    
    await loadDebugLayerMemories(layer);
}

async function loadDebugLayerMemories(layer) {
    const list = document.getElementById('debug-memory-list');
    if (!list) return;
    
    list.innerHTML = `<div class="loading">${t('memory.loading')}</div>`;
    
    try {
        const search = document.getElementById('debug-memory-search')?.value || '';
        const res = await API.memory.getLayer(layer.toLowerCase(), search);
        const memories = res.data?.memories || res.data || [];
        
        if (memories.length === 0) {
            list.innerHTML = `<div class="empty-state-sm">${t('memory.noMemories')}</div>`;
            return;
        }
        
        list.innerHTML = memories.map(m => `
            <div class="memory-item">
                <div class="memory-item-header">
                    <span class="memory-importance" style="--imp: ${(m.importance || 0.5) * 100}%">
                        ${t('memory.importance')}: ${((m.importance || 0.5) * 100).toFixed(0)}%
                    </span>
                    <span class="memory-time">${m.timestamp ? formatDate(m.timestamp) : ''}</span>
                </div>
                <div class="memory-content">${escapeHtml(m.content || m.summary || '')}</div>
                ${m.context ? `<div class="memory-context">${escapeHtml(m.context)}</div>` : ''}
            </div>
        `).join('');
        
    } catch (error) {
        list.innerHTML = `<div class="empty-state-sm">${t('memory.failedLoad')}</div>`;
    }
}

function searchDebugMemories() {
    loadDebugLayerMemories(DebugState.currentLayer);
}


// ========================================
// Relations Tab (simple list, no Canvas graph)
// ========================================
async function renderDebugRelations(container) {
    try {
        const [entitiesRes, relationsRes] = await Promise.allSettled([
            API.entityGraph.getEntities(DebugState.targetId),
            API.entityGraph.getRelations(DebugState.targetId)
        ]);
        
        const entities = entitiesRes.status === 'fulfilled' ? (entitiesRes.value.data?.entities || []) : [];
        const relations = relationsRes.status === 'fulfilled' ? (relationsRes.value.data?.relations || []) : [];
        
        DebugState.relationData = { entities, relations };
        
        container.innerHTML = `
            <div class="grid-2">
                <!-- Entities List -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('entityGraph.entities')} (${entities.length})</span>
                    </div>
                    <div class="relation-list">
                        ${entities.length === 0 ? `<div class="empty-state-sm">${t('common.noData')}</div>` :
                          entities.map(e => `
                            <div class="relation-item">
                                <span class="entity-type-badge">${getEntityTypeEmoji(e.entity_type)}</span>
                                <span class="entity-name">${escapeHtml(e.name)}</span>
                                <span class="tag tag-sm">${e.entity_type}</span>
                                ${e.description ? `<p class="entity-desc">${escapeHtml(e.description)}</p>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- Relations List -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('entityGraph.relations')} (${relations.length})</span>
                    </div>
                    <div class="relation-list">
                        ${relations.length === 0 ? `<div class="empty-state-sm">${t('common.noData')}</div>` :
                          relations.map(r => `
                            <div class="relation-item">
                                <span class="relation-source">${escapeHtml(r.source_name || r.source_id || '?')}</span>
                                <span class="relation-arrow">→</span>
                                <span class="relation-type-tag">${r.relation_type}</span>
                                <span class="relation-arrow">→</span>
                                <span class="relation-target">${escapeHtml(r.target_name || r.target_id || '?')}</span>
                                ${r.weight ? `<span class="tag tag-sm">${r.weight}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        container.innerHTML = `<div class="empty-state-sm">${t('entityGraph.failedLoad')}</div>`;
    }
}

function getEntityTypeEmoji(type) {
    const map = { concept: '💡', person: '👤', place: '📍', event: '📅', object: '📦', organization: '🏢' };
    return map[type] || '📌';
}


// ========================================
// Evolution Tab
// ========================================
async function renderDebugEvolution(container) {
    try {
        const [historyRes, snapshotsRes] = await Promise.allSettled([
            API.evolution.getHistory(30),
            API.evolution.getSnapshots()
        ]);
        
        const history = historyRes.status === 'fulfilled' ? (historyRes.value.data?.history || []) : [];
        const snapshots = snapshotsRes.status === 'fulfilled' ? (snapshotsRes.value.data || []) : [];
        
        container.innerHTML = `
            <div class="grid-2">
                <!-- OCEAN Over Time -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('evolution.oceanOverTime')}</span>
                    </div>
                    <div class="canvas-container" style="height: 250px;">
                        <canvas id="debug-evolution-chart"></canvas>
                    </div>
                </div>
                
                <!-- Baseline vs Current -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('evolution.currentVsBaseline')}</span>
                    </div>
                    <div id="debug-baseline" class="mt-4">
                        ${renderBaselineComparison(historyRes.status === 'fulfilled' ? historyRes.value.data : {})}
                    </div>
                </div>
            </div>
            
            <!-- Evolution Timeline -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('evolution.events')}</span>
                </div>
                <div class="evolution-timeline">
                    ${renderEvolutionTimeline(history)}
                </div>
            </div>
        `;
        
        setTimeout(() => drawEvolutionChart(history), 100);
        
    } catch (error) {
        container.innerHTML = `<div class="empty-state-sm">${t('evolution.failedLoad')}</div>`;
    }
}

function renderBaselineComparison(data) {
    if (!data || !data.baseline || !data.current) {
        return `<p class="text-muted">${t('evolution.noData')}</p>`;
    }
    
    const traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
    const labels = [t('ocean.openness'), t('ocean.conscientiousness'), t('ocean.extraversion'), t('ocean.agreeableness'), t('ocean.neuroticism')];
    
    return traits.map((trait, i) => {
        const base = data.baseline[trait] || 0;
        const curr = data.current[trait] || 0;
        const delta = curr - base;
        const deltaClass = delta > 0 ? 'positive' : delta < 0 ? 'negative' : '';
        
        return `
            <div class="baseline-row">
                <span class="baseline-label">${labels[i]}</span>
                <span class="baseline-value">${(base * 100).toFixed(0)}%</span>
                <span class="baseline-arrow">→</span>
                <span class="baseline-value current">${(curr * 100).toFixed(0)}%</span>
                <span class="baseline-delta ${deltaClass}">${delta > 0 ? '+' : ''}${(delta * 100).toFixed(1)}%</span>
            </div>
        `;
    }).join('');
}

function renderEvolutionTimeline(history) {
    if (!history || history.length === 0) {
        return `<div class="empty-state-sm">${t('evolution.noData')}</div>`;
    }
    
    return history.slice(0, 20).map(item => `
        <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <span class="timeline-time">${item.timestamp ? formatDate(item.timestamp) : ''}</span>
                <span class="timeline-type">${t('evolution.event.type.' + item.event_type) || item.event_type || ''}</span>
                <span class="timeline-desc">${escapeHtml(item.description || '')}</span>
            </div>
        </div>
    `).join('');
}

// Draw evolution chart
function drawEvolutionChart(history) {
    const canvas = document.getElementById('debug-evolution-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const w = canvas.parentElement?.clientWidth || 500;
    const h = canvas.parentElement?.clientHeight || 250;
    canvas.width = w;
    canvas.height = h;
    
    ctx.clearRect(0, 0, w, h);
    
    if (!history || history.length === 0) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(t('common.noData'), w / 2, h / 2);
        return;
    }
    
    const padding = 40;
    const chartW = w - padding * 2;
    const chartH = h - padding * 2;
    const colors = ['#6366f1', '#22c55e', '#f59e0b', '#ec4899', '#ef4444'];
    const traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
    
    // Grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartH * i / 4);
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(w - padding, y);
        ctx.stroke();
    }
    
    // Draw each trait line
    traits.forEach((trait, ti) => {
        ctx.beginPath();
        ctx.strokeStyle = colors[ti];
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.7;
        
        history.forEach((point, i) => {
            const val = point.ocean?.[trait] || point[trait] || 0.5;
            const x = padding + (chartW * i / Math.max(history.length - 1, 1));
            const y = padding + chartH - (val * chartH);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
    });
    
    ctx.globalAlpha = 1;
}
