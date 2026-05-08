/**
 * NPC Event Tester Page - Test GameEvent effects on NPC emotions
 */

// Event templates (15 types + custom)
const EVENT_TEMPLATES = [
    { type: 'gift', emoji: 'Gift', defaultIntensity: 0.5 },
    { type: 'attack', emoji: 'Attack', defaultIntensity: 0.8 },
    { type: 'help', emoji: 'Help', defaultIntensity: 0.6 },
    { type: 'insult', emoji: 'Insult', defaultIntensity: 0.7 },
    { type: 'compliment', emoji: 'Praise', defaultIntensity: 0.5 },
    { type: 'trade', emoji: 'Trade', defaultIntensity: 0.4 },
    { type: 'join_battle', emoji: 'Battle', defaultIntensity: 0.7 },
    { type: 'leave_battle', emoji: 'Retreat', defaultIntensity: 0.5 },
    { type: 'meet', emoji: 'Meet', defaultIntensity: 0.4 },
    { type: 'depart', emoji: 'Depart', defaultIntensity: 0.4 },
    { type: 'heal', emoji: 'Heal', defaultIntensity: 0.6 },
    { type: 'steal', emoji: 'Steal', defaultIntensity: 0.9 },
    { type: 'promise', emoji: 'Promise', defaultIntensity: 0.5 },
    { type: 'betray', emoji: 'Betray', defaultIntensity: 0.9 },
    { type: 'discover', emoji: 'Discover', defaultIntensity: 0.6 }
];

// Event sequence for batch replay
let eventSequence = [];
let eventLog = [];

// Render Event Tester Page
async function renderNPCEventTester() {
    const container = document.getElementById('page-npc-event-tester');
    
    try {
        const [npcsRes, templatesRes] = await Promise.all([
            API.game.listNPCs(),
            API.game.getEventTemplates()
        ]);
        
        const npcs = npcsRes.data || [];
        const templates = templatesRes.data || EVENT_TEMPLATES;
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('eventTester.title')}</h1>
                <p class="page-subtitle">${t('eventTester.subtitle')}</p>
            </div>
            
            <div class="event-tester-layout">
                <!-- Left: Event Configuration -->
                <div class="event-config-section">
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">${t('eventTester.eventTemplate')}</span>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">${t('eventTester.selectNPC')}</label>
                            <select id="tester-npc-select" class="form-input">
                                <option value="">${t('eventTester.allNPCs')}</option>
                                ${npcs.map(npc => `
                                    <option value="${npc.id}">${escapeHtml(npc.name)}</option>
                                `).join('')}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">${t('eventTester.eventTemplate')}</label>
                            <div class="event-template-grid">
                                ${templates.map(t => `
                                    <button class="event-template-btn ${t.type === 'gift' ? 'active' : ''}" 
                                        data-type="${t.type}" onclick="selectEventTemplate('${t.type}')">
                                        <span class="template-emoji">${t.emoji}</span>
                                        <span class="template-name">${t(`event.${t.type}`)}</span>
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">${t('eventTester.customEvent')}</label>
                            <input type="text" id="custom-event-type" class="form-input" 
                                placeholder="${t('eventTester.selectEventTemplate')}">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">${t('eventTester.intensity')}</label>
                            <div class="range-slider">
                                <input type="range" id="tester-intensity" min="0" max="100" value="50"
                                    oninput="document.getElementById('tester-intensity-value').textContent = this.value + '%'">
                                <span id="tester-intensity-value" class="range-value">50%</span>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">${t('eventTester.context')}</label>
                            <input type="text" id="tester-context" class="form-input" 
                                placeholder="${t('eventTester.contextPlaceholder')}">
                        </div>
                        
                        <button class="btn btn-primary" onclick="sendTestEvent()">
                            ${t('eventTester.sendEvent')}
                        </button>
                    </div>
                    
                    <!-- Batch Replay Section -->
                    <div class="card mt-4">
                        <div class="card-header">
                            <span class="card-title">${t('eventTester.batchReplay')}</span>
                        </div>
                        
                        <div id="event-sequence-list" class="event-sequence-list">
                            ${renderEventSequence()}
                        </div>
                        
                        <div class="flex gap-2 mt-3">
                            <button class="btn btn-secondary btn-sm" onclick="addEventToSequence()">
                                ${t('eventTester.addEvent')}
                            </button>
                            <button class="btn btn-secondary btn-sm" onclick="clearEventSequence()" 
                                ${eventSequence.length === 0 ? 'disabled' : ''}>
                                ${t('eventTester.clearSequence')}
                            </button>
                        </div>
                        
                        <button class="btn btn-primary mt-3" onclick="replayEventSequence()" 
                            ${eventSequence.length === 0 ? 'disabled' : ''}>
                            ${t('eventTester.replaySequence')}
                        </button>
                    </div>
                </div>
                
                <!-- Center: Emotion Change -->
                <div class="emotion-change-section">
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">${t('eventTester.emotionChange')}</span>
                        </div>
                        
                        <div id="emotion-change-display" class="emotion-change-display">
                            <div class="emotion-change-placeholder">
                                <span class="placeholder-icon" style="color:#7c5cff;">Chart</span>
                                <span>${t('eventTester.noEvents')}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Right: Event Log -->
                <div class="event-log-section">
                    <div class="card" style="height: calc(100vh - 180px);">
                        <div class="card-header">
                            <span class="card-title">${t('eventTester.eventLog')}</span>
                            <button class="btn btn-sm btn-secondary" onclick="clearEventLog()">
                                ${t('common.clear')}
                            </button>
                        </div>
                        
                        <div id="event-log-list" class="event-log-list">
                            ${renderEventLog()}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Failed to load event tester:', error);
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('eventTester.title')}</h1>
                <p class="page-subtitle">${t('eventTester.subtitle')}</p>
            </div>
            <div class="empty-state">
                <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">Test</div>
                <div class="empty-state-text">${t('eventTester.loadFailed')}</div>
                <div class="text-muted mt-2" style="font-size: 12px;">${error.message || ''}</div>
                <button class="btn btn-primary mt-4" onclick="renderNPCEventTester()">${t('common.retry')}</button>
            </div>
        `;
    }
}

// Select Event Template
function selectEventTemplate(type) {
    // Update UI
    document.querySelectorAll('.event-template-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.type === type);
    });
    
    // Update custom event input
    const customInput = document.getElementById('custom-event-type');
    if (customInput) customInput.value = '';
    
    // Find template and set intensity
    const template = EVENT_TEMPLATES.find(t => t.type === type);
    if (template) {
        const intensityInput = document.getElementById('tester-intensity');
        if (intensityInput) intensityInput.value = template.defaultIntensity * 100;
        const intensityValue = document.getElementById('tester-intensity-value');
        if (intensityValue) intensityValue.textContent = (template.defaultIntensity * 100) + '%';
    }
}

// Send Test Event
async function sendTestEvent() {
    const npcId = document.getElementById('tester-npc-select')?.value;
    const customType = document.getElementById('custom-event-type')?.value.trim();
    const activeTemplate = document.querySelector('.event-template-btn.active');
    const eventType = customType || activeTemplate?.dataset.type || 'gift';
    const intensity = parseInt(document.getElementById('tester-intensity')?.value || '50') / 100;
    const contextStr = document.getElementById('tester-context')?.value || '';
    
    let context = {};
    if (contextStr) {
        try {
            context = JSON.parse(contextStr);
        } catch {
            context = { note: contextStr };
        }
    }
    
    if (!npcId) {
        showToast(t('eventTester.selectNPC'), 'error');
        return;
    }
    
    try {
        // Get emotion before
        const beforeRes = await API.game.getEmotion(npcId);
        const beforeEmotion = beforeRes.data;
        
        // Send event
        const sendRes = await API.game.sendEvent(npcId, eventType, intensity, context);
        
        if (sendRes.success) {
            // Get emotion after
            await new Promise(r => setTimeout(r, 500)); // Small delay for emotion update
            const afterRes = await API.game.getEmotion(npcId);
            const afterEmotion = afterRes.data;
            
            // Calculate delta
            const delta = {
                valence: afterEmotion.valence - beforeEmotion.valence,
                arousal: afterEmotion.arousal - beforeEmotion.arousal,
                primary: afterEmotion.primary?.category !== beforeEmotion.primary?.category
            };
            
            // Add to log
            eventLog.unshift({
                timestamp: new Date().toISOString(),
                npcId,
                eventType,
                intensity,
                context,
                before: beforeEmotion,
                after: afterEmotion,
                delta
            });
            
            // Update display
            updateEmotionChangeDisplay(beforeEmotion, afterEmotion, delta);
            updateEventLogDisplay();
            
            showToast(t('eventTester.sendSuccess'), 'success');
        } else {
            showToast(t('eventTester.sendFailed'), 'error');
        }
    } catch (error) {
        console.error('Send event failed:', error);
        showToast(t('eventTester.sendFailed'), 'error');
    }
}

// Update Emotion Change Display
function updateEmotionChangeDisplay(before, after, delta) {
    const container = document.getElementById('emotion-change-display');
    if (!container) return;
    
    container.innerHTML = `
        <div class="emotion-comparison">
            <div class="emotion-state">
                <span class="state-label">${t('eventTester.beforeEmotion')}</span>
                <span class="emotion-emoji large">${before.primary?.category || 'Neutral'}</span>
                <span class="emotion-name">${before.primary?.category || 'Neutral'}</span>
                <div class="emotion-bars">
                    <div class="emotion-bar-row">
                        <span class="bar-label">Valence</span>
                        <div class="mini-bar">
                            <div class="mini-bar-fill" style="width: ${((before.valence + 1) / 2) * 100}%"></div>
                        </div>
                    </div>
                    <div class="emotion-bar-row">
                        <span class="bar-label">Arousal</span>
                        <div class="mini-bar">
                            <div class="mini-bar-fill" style="width: ${before.arousal * 100}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="emotion-arrow">→</div>
            
            <div class="emotion-state">
                <span class="state-label">${t('eventTester.afterEmotion')}</span>
                <span class="emotion-emoji large">${after.primary?.category || 'Neutral'}</span>
                <span class="emotion-name">${after.primary?.category || 'Neutral'}</span>
                <div class="emotion-bars">
                    <div class="emotion-bar-row">
                        <span class="bar-label">Valence</span>
                        <div class="mini-bar">
                            <div class="mini-bar-fill" style="width: ${((after.valence + 1) / 2) * 100}%"></div>
                        </div>
                        <span class="delta ${delta.valence > 0 ? 'positive' : delta.valence < 0 ? 'negative' : ''}">
                            ${delta.valence > 0 ? '+' : ''}${(delta.valence * 100).toFixed(0)}
                        </span>
                    </div>
                    <div class="emotion-bar-row">
                        <span class="bar-label">Arousal</span>
                        <div class="mini-bar">
                            <div class="mini-bar-fill" style="width: ${after.arousal * 100}%"></div>
                        </div>
                        <span class="delta ${delta.arousal > 0 ? 'positive' : delta.arousal < 0 ? 'negative' : ''}">
                            ${delta.arousal > 0 ? '+' : ''}${(delta.arousal * 100).toFixed(0)}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        
        ${delta.primary ? `
            <div class="emotion-changed-badge">
                <span class="badge-icon" style="color:#7c5cff;">Reset</span>
                <span>Emotion Changed!</span>
            </div>
        ` : ''}
    `;
}

// Render Event Sequence
function renderEventSequence() {
    if (eventSequence.length === 0) {
        return `<div class="text-muted" style="text-align: center; padding: 20px;">
            ${t('eventTester.eventSequence')}: ${t('common.noData')}
        </div>`;
    }
    
    return eventSequence.map((event, i) => {
        const template = EVENT_TEMPLATES.find(t => t.type === event.type);
        return `
            <div class="sequence-item">
                <span class="sequence-index">${i + 1}</span>
                <span class="sequence-emoji">${template?.emoji || 'Seq'}</span>
                <span class="sequence-name">${t(`event.${event.type}`) || event.type}</span>
                <span class="sequence-intensity">${(event.intensity * 100).toFixed(0)}%</span>
                <button class="btn btn-icon btn-sm" onclick="removeFromSequence(${i})">×</button>
            </div>
        `;
    }).join('');
}

// Add Event to Sequence
function addEventToSequence() {
    const activeTemplate = document.querySelector('.event-template-btn.active');
    const customType = document.getElementById('custom-event-type')?.value.trim();
    const eventType = customType || activeTemplate?.dataset.type;
    
    if (!eventType) {
        showToast(t('eventTester.selectEventTemplate'), 'error');
        return;
    }
    
    const intensity = parseInt(document.getElementById('tester-intensity')?.value || '50') / 100;
    
    eventSequence.push({
        type: eventType,
        intensity,
        delay: 1000 // ms delay between events
    });
    
    updateEventSequenceDisplay();
}

// Remove from Sequence
function removeFromSequence(index) {
    eventSequence.splice(index, 1);
    updateEventSequenceDisplay();
}

// Clear Event Sequence
function clearEventSequence() {
    eventSequence = [];
    updateEventSequenceDisplay();
}

// Update Event Sequence Display
function updateEventSequenceDisplay() {
    const container = document.getElementById('event-sequence-list');
    if (container) {
        container.innerHTML = renderEventSequence();
    }
    
    const replayBtn = document.querySelector('.card button[onclick="replayEventSequence()"]');
    if (replayBtn) {
        replayBtn.disabled = eventSequence.length === 0;
    }
}

// Replay Event Sequence
async function replayEventSequence() {
    const npcId = document.getElementById('tester-npc-select')?.value;
    
    if (!npcId || eventSequence.length === 0) return;
    
    try {
        const res = await API.game.replayEvents(npcId, eventSequence);
        
        if (res.success) {
            // Update log with batch results
            if (res.data?.results) {
                res.data.results.forEach(result => {
                    eventLog.unshift({
                        timestamp: new Date().toISOString(),
                        npcId,
                        ...result
                    });
                });
            }
            
            updateEventLogDisplay();
            showToast(t('eventTester.replayComplete'), 'success');
        } else {
            showToast(t('eventTester.replayFailed'), 'error');
        }
    } catch (error) {
        console.error('Replay failed:', error);
        showToast(t('eventTester.replayFailed'), 'error');
    }
}

// Render Event Log
function renderEventLog() {
    if (eventLog.length === 0) {
        return `
            <div class="empty-state">
                <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">List</div>
                <div class="empty-state-text">${t('eventTester.noEvents')}</div>
            </div>
        `;
    }
    
    return eventLog.map(log => {
        const template = EVENT_TEMPLATES.find(t => t.type === log.eventType);
        return `
            <div class="log-item">
                <div class="log-header">
                    <span class="log-time">${formatDate(log.timestamp)}</span>
                    <span class="log-emoji">${template?.emoji || 'Seq'}</span>
                    <span class="log-event">${t(`event.${log.eventType}`) || log.eventType}</span>
                </div>
                <div class="log-details">
                    <span class="log-intensity">Intensity: ${(log.intensity * 100).toFixed(0)}%</span>
                    ${log.delta ? `
                        <span class="log-delta ${log.delta.valence > 0 || log.delta.arousal > 0 ? 'positive' : log.delta.valence < 0 || log.delta.arousal < 0 ? 'negative' : ''}">
                            Δ: V${log.delta.valence > 0 ? '+' : ''}${(log.delta.valence * 100).toFixed(0)} | 
                            A${log.delta.arousal > 0 ? '+' : ''}${(log.delta.arousal * 100).toFixed(0)}
                        </span>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Update Event Log Display
function updateEventLogDisplay() {
    const container = document.getElementById('event-log-list');
    if (container) {
        container.innerHTML = renderEventLog();
    }
}

// Clear Event Log
function clearEventLog() {
    eventLog = [];
    updateEventLogDisplay();
}

// Helper: Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
