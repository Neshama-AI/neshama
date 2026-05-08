/**
 * NPC Detail Page - Display NPC profile, emotion timeline, behavior suggestions
 */

// Canvas references for charts
let emotionTimelineChart = null;
let currentTab = 'emotion-log';

// OCEAN Labels
const OCEAN_LABELS = ['O', 'C', 'E', 'A', 'N'];
const OCEAN_KEYS = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];

// Render NPC Detail Page
async function renderNPCDetail() {
    const container = document.getElementById('page-npc-detail');
    if (!container) {
        // Page container might not exist, create it
        const mainContent = document.querySelector('.main-content');
        if (mainContent && !document.getElementById('page-npc-detail')) {
            const div = document.createElement('div');
            div.id = 'page-npc-detail';
            div.className = 'page';
            mainContent.appendChild(div);
        }
    }
    
    const detailContainer = document.getElementById('page-npc-detail') || container;
    
    if (!AppState.selectedNPC) {
        detailContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">NPC</div>
                <div class="empty-state-text">${t('npcDetail.notFound')}</div>
                <button class="btn btn-primary mt-4" onclick="router.navigate('npc-list')">
                    ${t('npcDetail.backToList')}
                </button>
            </div>
        `;
        return;
    }
    
    try {
        const [npcRes, emotionRes, behaviorRes] = await Promise.all([
            API.game.getNPC(AppState.selectedNPC),
            API.game.getEmotion(AppState.selectedNPC),
            API.game.getBehavior(AppState.selectedNPC)
        ]);
        
        AppState.npcDetail = npcRes.data;
        const npc = npcRes.data;
        const emotion = emotionRes.data;
        const behavior = behaviorRes.data;
        
        detailContainer.innerHTML = `
            <div class="page-header">
                <div class="flex items-center gap-3">
                    <button class="btn btn-secondary btn-sm" onclick="router.navigate('npc-list')">
                        ← ${t('npcDetail.backToList')}
                    </button>
                    <div>
                        <h1 class="page-title">${escapeHtml(npc.name)}</h1>
                        <p class="page-subtitle">${t(`npcList.preset.${npc.preset || 'custom'}`)}</p>
                    </div>
                </div>
            </div>
            
            <div class="npc-detail-layout">
                <!-- Left Column: Profile -->
                <div class="npc-profile-section">
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">${t('npcDetail.profile')}</span>
                        </div>
                        <div class="npc-avatar-large">
                            <span class="avatar-initial">${(npc.name || "N").charAt(0).toUpperCase()}</span>
                        </div>
                        <div class="npc-ocean-chart-container">
                            <canvas id="ocean-radar-chart" width="200" height="200"></canvas>
                        </div>
                        <div class="ocean-bars mt-3">
                            ${renderOceanBars(npc.ocean)}
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-header">
                            <span class="card-title">${t('npcDetail.currentBehavior')}</span>
                        </div>
                        <div class="behavior-display">
                            <div class="behavior-type">
                                <span class="behavior-label">${t('npcDetail.behaviorType')}:</span>
                                <span class="behavior-value">${t(`behavior.${behavior.type || 'neutral'}`) || behavior.type}</span>
                            </div>
                            <div class="behavior-strength mt-3">
                                <span class="behavior-label">${t('npcDetail.behaviorStrength')}:</span>
                                <div class="progress-bar mt-2">
                                    <div class="progress-fill" style="width: ${(behavior.strength || 0.5) * 100}%"></div>
                                </div>
                            </div>
                            ${behavior.modifiers && behavior.modifiers.length > 0 ? `
                                <div class="behavior-modifiers mt-3">
                                    <span class="behavior-label">${t('npcDetail.behaviorModifiers')}:</span>
                                    <div class="modifier-tags mt-2">
                                        ${behavior.modifiers.map(m => `<span class="tag tag-secondary">${t(`modifier.${m}`) || m}</span>`).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
                
                <!-- Center Column: Emotion Timeline -->
                <div class="npc-timeline-section">
                    <div class="card" style="height: 400px;">
                        <div class="card-header">
                            <span class="card-title">${t('npcDetail.emotionTimeline')}</span>
                            <span class="tag tag-amber">${t('dashboard.live')}</span>
                        </div>
                        <div class="emotion-state-display mb-3">
                            <div class="current-emotion-emoji">${emotion.primary?.category || 'Neutral'}</div>
                            <div class="current-emotion-name">${emotion.primary?.category || 'Neutral'}</div>
                            <div class="current-emotion-intensity">
                                ${t('npcDetail.intensity')}: ${((emotion.primary?.intensity || 0) * 100).toFixed(0)}%
                            </div>
                        </div>
                        <div class="canvas-container" style="height: 200px;">
                            <canvas id="emotion-timeline-chart"></canvas>
                        </div>
                        <div class="emotion-axes mt-3">
                            <div class="axis-info">
                                <span class="axis-label">${t('dashboard.valence')}:</span>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${((emotion.valence + 1) / 2) * 100}%"></div>
                                </div>
                            </div>
                            <div class="axis-info mt-2">
                                <span class="axis-label">${t('dashboard.arousal')}:</span>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${(emotion.arousal || 0.5) * 100}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Bottom Tabs -->
                    <div class="card mt-4">
                        <div class="tabs">
                            <button class="tab-btn active" data-tab="emotion-log" onclick="switchNPCTab('emotion-log')">
                                ${t('npcDetail.emotionLog')}
                            </button>
                            <button class="tab-btn" data-tab="dialogue" onclick="switchNPCTab('dialogue')">
                                ${t('npcDetail.dialogueTest')}
                            </button>
                            <button class="tab-btn" data-tab="relations" onclick="switchNPCTab('relations')">
                                ${t('npcDetail.entityGraph')}
                            </button>
                            <button class="tab-btn" data-tab="memory" onclick="switchNPCTab('memory')">
                                ${t('npcDetail.memoryBrowser')}
                            </button>
                        </div>
                        
                        <div id="tab-content" class="tab-content mt-3">
                            ${renderEmotionLogTab()}
                        </div>
                    </div>
                </div>
                
                <!-- Right Column: Behavior Suggestions -->
                <div class="npc-behavior-section">
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">${t('npcDetail.behaviorSuggestion')}</span>
                        </div>
                        <div class="suggestion-list">
                            ${renderBehaviorSuggestions(behavior)}
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-header">
                            <span class="card-title">${t('npcDetail.sendGameEvent')}</span>
                        </div>
                        <div class="form-group">
                            <label class="form-label">${t('npcDetail.eventType')}</label>
                            <select id="event-type-select" class="form-input">
                                <option value="gift">${t('event.gift')}</option>
                                <option value="attack">${t('event.attack')}</option>
                                <option value="help">${t('event.help')}</option>
                                <option value="insult">${t('event.insult')}</option>
                                <option value="compliment">${t('event.compliment')}</option>
                                <option value="trade">${t('event.trade')}</option>
                                <option value="join_battle">${t('event.join_battle')}</option>
                                <option value="leave_battle">${t('event.leave_battle')}</option>
                                <option value="meet">${t('event.meet')}</option>
                                <option value="depart">${t('event.depart')}</option>
                                <option value="heal">${t('event.heal')}</option>
                                <option value="steal">${t('event.steal')}</option>
                                <option value="promise">${t('event.promise')}</option>
                                <option value="betray">${t('event.betray')}</option>
                                <option value="discover">${t('event.discover')}</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">${t('npcDetail.eventIntensity')}</label>
                            <div class="range-slider">
                                <input type="range" id="event-intensity" min="0" max="100" value="50"
                                    oninput="document.getElementById('event-intensity-value').textContent = this.value + '%'">
                                <span id="event-intensity-value" class="range-value">50%</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">${t('npcDetail.eventContext')}</label>
                            <input type="text" id="event-context" class="form-input" 
                                placeholder="${t('eventTester.contextPlaceholder')}">
                        </div>
                        <button class="btn btn-primary" onclick="sendNPCEvent()">
                            ${t('npcDetail.sendEvent')}
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Draw charts after DOM is ready
        setTimeout(() => {
            drawOceanRadar(npc.ocean);
            drawEmotionTimeline(emotion);
        }, 100);
        
    } catch (error) {
        console.error('Failed to load NPC detail:', error);
        detailContainer.innerHTML = `
            <div class="page-header">
                <div class="flex items-center gap-3">
                    <button class="btn btn-secondary btn-sm" onclick="router.navigate('npc-list')">
                        ← ${t('npcDetail.backToList')}
                    </button>
                </div>
            </div>
            <div class="empty-state">
                <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">NPC</div>
                <div class="empty-state-text">${t('npcDetail.loadFailed')}</div>
                <div class="text-muted mt-2" style="font-size: 12px;">${error.message || ''}</div>
                <button class="btn btn-primary mt-4" onclick="renderNPCDetail()">${t('common.retry')}</button>
            </div>
        `;
    }
}

// Draw OCEAN Radar Chart
function drawOceanRadar(ocean) {
    const canvas = document.getElementById('ocean-radar-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 30;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Background rings
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    
    for (let i = 1; i <= 5; i++) {
        ctx.beginPath();
        for (let j = 0; j < 5; j++) {
            const angle = (Math.PI * 2 * j / 5) - Math.PI / 2;
            const r = radius * (i / 5);
            const x = centerX + r * Math.cos(angle);
            const y = centerY + r * Math.sin(angle);
            if (j === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.stroke();
    }
    
    // Axis lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    for (let i = 0; i < 5; i++) {
        const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(centerX + radius * Math.cos(angle), centerY + radius * Math.sin(angle));
        ctx.stroke();
    }
    
    // Data polygon
    const values = OCEAN_KEYS.map(k => ocean?.[k] || 0.5);
    
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
        const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
        const value = values[i];
        const x = centerX + radius * value * Math.cos(angle);
        const y = centerY + radius * value * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    
    ctx.fillStyle = 'rgba(124,92,255,0.3)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(124,92,255,0.8)';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Labels
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    
    for (let i = 0; i < 5; i++) {
        const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
        const x = centerX + (radius + 20) * Math.cos(angle);
        const y = centerY + (radius + 20) * Math.sin(angle);
        ctx.fillText(OCEAN_LABELS[i], x, y + 4);
    }
}

// Render OCEAN Bars
function renderOceanBars(ocean) {
    if (!ocean) return '';
    
    return OCEAN_KEYS.map((key, i) => {
        const value = ocean[key] || 0.5;
        const label = OCEAN_LABELS[i];
        return `
            <div class="ocean-bar-item">
                <span class="ocean-bar-label">${label}</span>
                <div class="ocean-bar-track">
                    <div class="ocean-bar-fill" style="width: ${value * 100}%"></div>
                </div>
                <span class="ocean-bar-value">${(value * 100).toFixed(0)}</span>
            </div>
        `;
    }).join('');
}

// Draw Emotion Timeline
function drawEmotionTimeline(emotion) {
    const canvas = document.getElementById('emotion-timeline-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.parentElement?.clientWidth || 400;
    const height = canvas.parentElement?.clientHeight || 200;
    
    canvas.width = width;
    canvas.height = height;
    
    ctx.clearRect(0, 0, width, height);
    
    // Get emotion history (simulated with current data if no history)
    const history = emotion.history || [];
    
    if (history.length === 0) {
        // Draw single point if no history
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(t('common.noData'), width / 2, height / 2);
        return;
    }
    
    // Draw line chart
    const padding = 30;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    
    // Grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight * i / 4);
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }
    
    // Draw line
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(124,92,255,0.8)';
    ctx.lineWidth = 2;
    
    history.forEach((point, i) => {
        const x = padding + (chartWidth * i / Math.max(history.length - 1, 1));
        const y = padding + chartHeight - (point.intensity * chartHeight);
        
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // Draw points
    history.forEach((point, i) => {
        const x = padding + (chartWidth * i / Math.max(history.length - 1, 1));
        const y = padding + chartHeight - (point.intensity * chartHeight);
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(124,92,255,1)';
        ctx.fill();
    });
}

// Render Behavior Suggestions
function renderBehaviorSuggestions(behavior) {
    if (!behavior) return `<div class="text-muted">${t('common.noData')}</div>`;
    
    const suggestions = behavior.suggestions || [];
    
    if (suggestions.length === 0) {
        return `<div class="text-muted">${t('common.noData')}</div>`;
    }
    
    return suggestions.map(s => `
        <div class="suggestion-item">
            <span class="suggestion-icon">${s.icon || 'Tip'}</span>
            <span class="suggestion-text">${escapeHtml(s.text || '')}</span>
        </div>
    `).join('');
}

// Render Emotion Log Tab
function renderEmotionLogTab() {
    const logs = AppState.npcDetail?.emotionLogs || [];
    
    if (logs.length === 0) {
        return `<div class="empty-state">
            <div class="empty-state-text">${t('emotion.noEvents')}</div>
        </div>`;
    }
    
    return `
        <div class="emotion-log-list">
            ${logs.map(log => `
                <div class="emotion-log-item">
                    <span class="log-time">${formatDate(log.timestamp)}</span>
                    <span class="log-event">${log.event || ''}</span>
                    <span class="log-emotion">${log.emotion || ''}</span>
                    <span class="log-change ${log.change > 0 ? 'positive' : 'negative'}">
                        ${log.change > 0 ? '+' : ''}${log.change.toFixed(2)}
                    </span>
                </div>
            `).join('')}
        </div>
    `;
}

// Switch NPC Tab
async function switchNPCTab(tab) {
    currentTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    
    const content = document.getElementById('tab-content');
    if (!content) return;
    
    switch (tab) {
        case 'emotion-log':
            content.innerHTML = renderEmotionLogTab();
            break;
        case 'dialogue':
            content.innerHTML = await renderDialogueTab();
            break;
        case 'relations':
            content.innerHTML = await renderRelationsTab();
            break;
        case 'memory':
            content.innerHTML = await renderMemoryTab();
            break;
    }
}

// Render Dialogue Tab
async function renderDialogueTab() {
    try {
        const res = await API.game.getChatHistory(AppState.selectedNPC);
        const messages = res.data || [];
        
        return `
            <div class="dialogue-container">
                <div id="dialogue-messages" class="dialogue-messages">
                    ${messages.length === 0 ? 
                        `<div class="empty-state"><div class="empty-state-text">${t('chat.startConversation')}</div></div>` :
                        messages.map(m => renderDialogueMessage(m)).join('')
                    }
                </div>
                <div class="dialogue-input-container">
                    <div class="emotion-badge">
                        ${t('npcList.currentEmotion')}: ${AppState.npcDetail?.emotion?.primary?.category || 'Neutral'}
                    </div>
                    <div class="flex gap-2 mt-2">
                        <input type="text" id="dialogue-input" class="form-input" 
                            placeholder="${t('npcDetail.typeMessage')}"
                            onkeypress="if(event.key==='Enter') sendDialogue()">
                        <button class="btn btn-primary" onclick="sendDialogue()">${t('npcDetail.send')}</button>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        return `<div class="text-muted">${t('common.error')}: ${error.message}</div>`;
    }
}

// Render Dialogue Message
function renderDialogueMessage(msg) {
    const isUser = msg.role === 'user';
    return `
        <div class="dialogue-message ${isUser ? 'user' : 'npc'}">
            <div class="message-content">${escapeHtml(msg.content || '')}</div>
            <div class="message-time">${msg.timestamp ? formatDate(msg.timestamp) : ''}</div>
        </div>
    `;
}

// Send Dialogue
async function sendDialogue() {
    const input = document.getElementById('dialogue-input');
    const message = input?.value.trim();
    
    if (!message) return;
    
    try {
        const res = await API.game.chat(AppState.selectedNPC, message);
        input.value = '';
        
        if (res.data) {
            const messagesContainer = document.getElementById('dialogue-messages');
            if (messagesContainer) {
                // Add user message
                messagesContainer.innerHTML += renderDialogueMessage({ role: 'user', content: message, timestamp: new Date().toISOString() });
                // Add NPC response
                messagesContainer.innerHTML += renderDialogueMessage({ role: 'assistant', content: res.data.content, timestamp: new Date().toISOString() });
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }
    } catch (error) {
        showToast(t('common.error'), 'error');
    }
}

// Render Relations Tab
async function renderRelationsTab() {
    try {
        const res = await API.game.getRelations(AppState.selectedNPC);
        const relations = res.data || [];
        
        if (relations.length === 0) {
            return `<div class="empty-state">
                <div class="empty-state-text">${t('common.noData')}</div>
            </div>`;
        }
        
        return `
            <div class="relations-list">
                ${relations.map(r => `
                    <div class="relation-item">
                        <span class="relation-name">${escapeHtml(r.target || '')}</span>
                        <span class="relation-type tag">${t(`npcRelation.${r.type || 'neutral'}`) || r.type}</span>
                        ${r.note ? `<span class="relation-note">${escapeHtml(r.note)}</span>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        return `<div class="text-muted">${t('common.error')}: ${error.message}</div>`;
    }
}

// Render Memory Tab
async function renderMemoryTab() {
    try {
        const res = await API.game.getMemory(AppState.selectedNPC);
        const memories = res.data || [];
        
        if (memories.length === 0) {
            return `<div class="empty-state">
                <div class="empty-state-text">${t('common.noData')}</div>
            </div>`;
        }
        
        return `
            <div class="memory-list">
                ${memories.map(m => `
                    <div class="memory-item">
                        <span class="memory-entity">${escapeHtml(m.entity || '')}</span>
                        <span class="memory-type tag tag-secondary">${m.type || ''}</span>
                        ${m.note ? `<div class="memory-note">${escapeHtml(m.note)}</div>` : ''}
                        <span class="memory-time text-muted">${m.timestamp ? formatDate(m.timestamp) : ''}</span>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        return `<div class="text-muted">${t('common.error')}: ${error.message}</div>`;
    }
}

// Send NPC Event
async function sendNPCEvent() {
    const eventType = document.getElementById('event-type-select')?.value;
    const intensity = parseInt(document.getElementById('event-intensity')?.value || '50') / 100;
    const contextStr = document.getElementById('event-context')?.value || '';
    
    let context = {};
    if (contextStr) {
        try {
            context = JSON.parse(contextStr);
        } catch {
            context = { note: contextStr };
        }
    }
    
    try {
        const res = await API.game.sendEvent(AppState.selectedNPC, eventType, intensity, context);
        if (res.success) {
            showToast(t('npcDetail.eventSent'), 'success');
            // Refresh emotion data
            renderNPCDetail();
        } else {
            showToast(t('npcDetail.eventFailed'), 'error');
        }
    } catch (error) {
        console.error('Send event failed:', error);
        showToast(t('npcDetail.eventFailed'), 'error');
    }
}

// Refresh NPC Detail
async function refreshNPCDetail(npcId) {
    if (AppState.currentPage !== 'npc-detail') return;
    
    try {
        const [emotionRes, behaviorRes] = await Promise.all([
            API.game.getEmotion(npcId),
            API.game.getBehavior(npcId)
        ]);
        
        // Update emotion display if elements exist
        const emojiEl = document.querySelector('.current-emotion-emoji');
        const nameEl = document.querySelector('.current-emotion-name');
        
        if (emojiEl && emotionRes.data?.primary) {
            emojiEl.textContent = emotionRes.data.primary.emoji;
        }
        if (nameEl && emotionRes.data?.primary) {
            nameEl.textContent = emotionRes.data.primary.category;
        }
        
        // Redraw timeline
        drawEmotionTimeline(emotionRes.data);
        
    } catch (error) {
        console.error('Refresh NPC detail failed:', error);
    }
}

// Helper: Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add NPC Detail page container to HTML if needed
function ensureNPCDetailContainer() {
    const mainContent = document.querySelector('.main-content');
    if (mainContent && !document.getElementById('page-npc-detail')) {
        const div = document.createElement('div');
        div.id = 'page-npc-detail';
        div.className = 'page';
        mainContent.appendChild(div);
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', ensureNPCDetailContainer);
