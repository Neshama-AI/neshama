/**
 * Progressive Summarization Page - Memory summarization at multiple levels
 */

let summarizationData = {
    l0: [],
    l1: [],
    l2: [],
    stats: null
};

// Layer configurations
const LAYER_CONFIG = {
    L0: {
        title_key: 'memoryLayer.working.title',
        desc_key: 'memoryLayer.working.desc',
        color: '#64748B',
        bgColor: 'rgba(100, 116, 139, 0.15)'
    },
    L1: {
        title_key: 'memoryLayer.episodic.title',
        desc_key: 'memoryLayer.episodic.desc',
        color: '#4F46E5',
        bgColor: 'rgba(79, 70, 229, 0.15)'
    },
    L2: {
        title_key: 'memoryLayer.semantic.title',
        desc_key: 'memoryLayer.semantic.desc',
        color: '#F59E0B',
        bgColor: 'rgba(245, 158, 11, 0.15)'
    }
};

// Get layer title
function getLayerTitle(layerKey) {
    return t(layerKey);
}

// Get layer description
function getLayerDesc(descKey) {
    return t(descKey);
}

// Render Progressive Summarization Page
async function renderProgressiveSummarization() {
    const container = document.getElementById('page-progressive-summarization');
    
    try {
        const [l0Res, l1Res, l2Res, statsRes] = await Promise.all([
            API.progressiveSummarization.getL0('default'),
            API.progressiveSummarization.getL1('default'),
            API.progressiveSummarization.getL2('default'),
            API.progressiveSummarization.getStats('default')
        ]);
        
        summarizationData.l0 = l0Res.data.entries || [];
        summarizationData.l1 = l1Res.data.entries || [];
        summarizationData.l2 = l2Res.data.entries || [];
        summarizationData.stats = statsRes.data;
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('progressiveSumm.title')}</h1>
                <p class="page-subtitle">${t('progressiveSumm.subtitle')}</p>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('progressiveSumm.statistics')}</span>
                    <button class="btn btn-sm btn-primary" onclick="runAutoProcess()">${t('progressiveSumm.autoProcess')}</button>
                </div>
                <div class="grid-4 mt-4">
                    <div style="padding: 16px; background: ${LAYER_CONFIG.L0.bgColor}; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: 700; color: ${LAYER_CONFIG.L0.color};">${summarizationData.l0.length}</div>
                        <div class="text-muted mt-1">${t('progressiveSumm.l0Entries')}</div>
                    </div>
                    <div style="padding: 16px; background: ${LAYER_CONFIG.L1.bgColor}; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: 700; color: ${LAYER_CONFIG.L1.color};">${summarizationData.l1.length}</div>
                        <div class="text-muted mt-1">${t('progressiveSumm.l1Entries')}</div>
                    </div>
                    <div style="padding: 16px; background: ${LAYER_CONFIG.L2.bgColor}; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: 700; color: ${LAYER_CONFIG.L2.color};">${summarizationData.l2.length}</div>
                        <div class="text-muted mt-1">${t('progressiveSumm.l2Entries')}</div>
                    </div>
                    <div style="padding: 16px; background: var(--bg-tertiary); border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: 700;">${summarizationData.stats?.auto_process_count || 0}</div>
                        <div class="text-muted mt-1">${t('progressiveSumm.autoProcessed')}</div>
                    </div>
                </div>
                ${summarizationData.stats?.last_l0_summary ? `
                    <div class="mt-3 text-muted" style="font-size: 12px;">
                        ${t('progressiveSumm.lastL0Summary')}: ${formatDate(summarizationData.stats.last_l0_summary)}
                    </div>
                ` : ''}
                ${summarizationData.stats?.last_l1_summary ? `
                    <div class="text-muted" style="font-size: 12px;">
                        ${t('progressiveSumm.lastL1Summary')}: ${formatDate(summarizationData.stats.last_l1_summary)}
                    </div>
                ` : ''}
            </div>
            
            <div class="grid-3">
                ${renderL0Panel()}
                ${renderL1Panel()}
                ${renderL2Panel()}
            </div>
        `;
        
    } catch (error) {
        console.error('Progressive summarization load error:', error);
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('progressiveSumm.title')}</h1>
                <p class="page-subtitle">${t('progressiveSumm.subtitle')}</p>
            </div>
            <div class="card">
                <div class="empty-state">
                    <div class="empty-state-icon">📝</div>
                    <div class="empty-state-text">${t('progressiveSumm.failedLoad')}</div>
                    <div class="text-muted mt-2" style="font-size: 12px;">${error.message || ''}</div>
                    <button class="btn btn-primary mt-4" onclick="renderProgressiveSummarization()">${t('common.retry')}</button>
                </div>
            </div>
        `;
        Toast.show(t('common.error'), 'error');
    }
}

// Render L0 Panel (Working Memory)
function renderL0Panel() {
    const config = LAYER_CONFIG.L0;
    const title = getLayerTitle(config.title_key);
    const description = getLayerDesc(config.desc_key);
    
    return `
        <div class="card" style="border-left: 3px solid ${LAYER_CONFIG.L0.color};">
            <div class="card-header">
                <span class="card-title">${title}</span>
                <span class="tag" style="background: ${LAYER_CONFIG.L0.bgColor}; color: ${LAYER_CONFIG.L0.color};">${summarizationData.l0.length}</span>
            </div>
            <p class="text-muted" style="font-size: 12px; margin-bottom: 12px;">${description}</p>
            
            <div class="mb-3">
                <button class="btn btn-sm btn-secondary" onclick="showAddL0Modal()" style="width: 100%;">
                    + ${t('common.add')} ${t('progressiveSumm.entry')}
                </button>
            </div>
            
            <div id="l0-list" style="max-height: 350px; overflow-y: auto;">
                ${renderL0Entries()}
            </div>
        </div>
    `;
}

// Render L0 entries
function renderL0Entries() {
    if (summarizationData.l0.length === 0) {
        return `
            <div class="empty-state" style="padding: 20px;">
                <div class="empty-state-icon">📝</div>
                <div class="empty-state-text">${t('common.noData')}</div>
            </div>
        `;
    }
    
    return summarizationData.l0.slice(0, 20).map(entry => `
        <div style="padding: 10px; background: var(--bg-tertiary); border-radius: 6px; margin-bottom: 8px;">
            <div class="flex items-center gap-2 mb-2">
                <span class="tag" style="font-size: 10px; padding: 2px 6px;">
                    ${entry.role === 'user' ? '👤' : '🤖'} ${entry.role || 'user'}
                </span>
                ${entry.metadata?.importance ? `
                    <span class="text-accent" style="font-size: 10px;">
                        ${t('memory.importance')}: ${(entry.metadata.importance * 100).toFixed(0)}%
                    </span>
                ` : ''}
            </div>
            <div style="font-size: 13px; line-height: 1.4;">
                ${escapeHtml(entry.content.substring(0, 150))}${entry.content.length > 150 ? '...' : ''}
            </div>
            <div class="text-muted mt-1" style="font-size: 10px;">
                ${formatDate(entry.timestamp)}
            </div>
        </div>
    `).join('');
}

// Render L1 Panel (Episodic Memory)
function renderL1Panel() {
    const config = LAYER_CONFIG.L1;
    const title = getLayerTitle(config.title_key);
    const description = getLayerDesc(config.desc_key);
    
    return `
        <div class="card" style="border-left: 3px solid ${LAYER_CONFIG.L1.color};">
            <div class="card-header">
                <span class="card-title">${title}</span>
                <span class="tag" style="background: ${LAYER_CONFIG.L1.bgColor}; color: ${LAYER_CONFIG.L1.color};">${summarizationData.l1.length}</span>
            </div>
            <p class="text-muted" style="font-size: 12px; margin-bottom: 12px;">${description}</p>
            
            <div class="mb-3">
                <button class="btn btn-sm btn-primary" onclick="summarizeL0()" style="width: 100%;">
                    🔄 ${t('progressiveSumm.summarizeL0')}
                </button>
            </div>
            
            <div id="l1-list" style="max-height: 350px; overflow-y: auto;">
                ${renderL1Entries()}
            </div>
        </div>
    `;
}

// Render L1 entries
function renderL1Entries() {
    if (summarizationData.l1.length === 0) {
        return `
            <div class="empty-state" style="padding: 20px;">
                <div class="empty-state-icon">📖</div>
                <div class="empty-state-text">${t('common.noData')}</div>
                <div class="text-muted mt-2" style="font-size: 11px;">
                    ${t('progressiveSumm.l1Hint')}
                </div>
            </div>
        `;
    }
    
    return summarizationData.l1.map(entry => `
        <div style="padding: 12px; background: var(--bg-tertiary); border-radius: 6px; margin-bottom: 8px;">
            <div style="font-size: 13px; line-height: 1.5; margin-bottom: 8px;">
                ${escapeHtml(entry.summary?.substring(0, 200) || entry.content?.substring(0, 200) || '')}
                ${(entry.summary?.length || entry.content?.length || 0) > 200 ? '...' : ''}
            </div>
            <div class="flex justify-between items-center">
                <div class="flex gap-2">
                    ${entry.emotion ? `<span class="tag" style="font-size: 10px;">${entry.emotion}</span>` : ''}
                    ${entry.topics?.map(topic => `<span class="tag tag-amber" style="font-size: 10px;">#${topic}</span>`).join('') || ''}
                </div>
                <span class="text-muted" style="font-size: 10px;">${formatDate(entry.timestamp)}</span>
            </div>
            <div class="mt-2">
                <span class="text-muted" style="font-size: 10px;">
                    ${t('progressiveSumm.sourceEntries')}: ${entry.source_count || 1}
                </span>
            </div>
        </div>
    `).join('');
}

// Render L2 Panel (Semantic Memory)
function renderL2Panel() {
    const config = LAYER_CONFIG.L2;
    const title = getLayerTitle(config.title_key);
    const description = getLayerDesc(config.desc_key);
    
    return `
        <div class="card" style="border-left: 3px solid ${LAYER_CONFIG.L2.color};">
            <div class="card-header">
                <span class="card-title">${title}</span>
                <span class="tag" style="background: ${LAYER_CONFIG.L2.bgColor}; color: ${LAYER_CONFIG.L2.color};">${summarizationData.l2.length}</span>
            </div>
            <p class="text-muted" style="font-size: 12px; margin-bottom: 12px;">${description}</p>
            
            <div class="mb-3">
                <button class="btn btn-sm btn-secondary" onclick="summarizeL1()" style="width: 100%; background: ${LAYER_CONFIG.L2.color};">
                    🌟 ${t('progressiveSumm.summarizeL1')}
                </button>
            </div>
            
            <div id="l2-list" style="max-height: 350px; overflow-y: auto;">
                ${renderL2Entries()}
            </div>
        </div>
    `;
}

// Render L2 entries
function renderL2Entries() {
    if (summarizationData.l2.length === 0) {
        return `
            <div class="empty-state" style="padding: 20px;">
                <div class="empty-state-icon">🧠</div>
                <div class="empty-state-text">${t('common.noData')}</div>
                <div class="text-muted mt-2" style="font-size: 11px;">
                    ${t('progressiveSumm.l2Hint')}
                </div>
            </div>
        `;
    }
    
    return summarizationData.l2.map(entry => `
        <div style="padding: 12px; background: var(--bg-tertiary); border-radius: 6px; margin-bottom: 8px;">
            <div class="flex items-center gap-2 mb-2">
                ${entry.knowledge_type ? `<span class="tag" style="background: ${LAYER_CONFIG.L2.bgColor}; color: ${LAYER_CONFIG.L2.color};">${entry.knowledge_type}</span>` : ''}
            </div>
            <div style="font-size: 13px; line-height: 1.5;">
                ${escapeHtml(entry.knowledge?.substring(0, 200) || entry.content?.substring(0, 200) || '')}
                ${(entry.knowledge?.length || entry.content?.length || 0) > 200 ? '...' : ''}
            </div>
            <div class="flex gap-2 mt-2" style="flex-wrap: wrap;">
                ${entry.evidence?.slice(0, 3).map(e => `<span class="text-muted" style="font-size: 10px; background: var(--bg-card); padding: 2px 6px; border-radius: 4px;">${escapeHtml(e).substring(0, 30)}...</span>`).join('') || ''}
            </div>
            <div class="mt-2">
                <span class="text-muted" style="font-size: 10px;">
                    ${t('progressiveSumm.confidence')}: ${((entry.confidence || 0.5) * 100).toFixed(0)}%
                </span>
            </div>
        </div>
    `).join('');
}

// Show add L0 entry modal
function showAddL0Modal() {
    const modal = document.createElement('div');
    modal.id = 'l0-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    modal.innerHTML = `
        <div class="card" style="width: 600px; max-width: 90%;">
            <div class="card-header">
                <span class="card-title">${t('progressiveSumm.addL0Entry')}</span>
                <button class="btn btn-icon btn-secondary" onclick="closeL0Modal()">✕</button>
            </div>
            <div class="mt-4">
                <div class="form-group">
                    <label class="form-label">${t('progressiveSumm.role')}</label>
                    <select id="new-l0-role" class="form-input">
                        <option value="user">👤 User</option>
                        <option value="assistant">🤖 Assistant</option>
                        <option value="system">⚙️ System</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">${t('memory.content')}</label>
                    <textarea id="new-l0-content" class="form-input" rows="5" placeholder="${t('progressiveSumm.contentPlaceholder')}"></textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">${t('memory.importance')} (0-1)</label>
                    <div class="flex items-center gap-2">
                        <input type="range" id="new-l0-importance" min="0" max="100" value="50" style="flex: 1;"
                               oninput="document.getElementById('l0-importance-value').textContent = this.value + '%'">
                        <span id="l0-importance-value" class="text-accent">50%</span>
                    </div>
                </div>
                <div class="flex gap-2 mt-4">
                    <button class="btn btn-primary" onclick="addL0Entry()">${t('common.add')}</button>
                    <button class="btn btn-secondary" onclick="closeL0Modal()">${t('common.cancel')}</button>
                </div>
            </div>
        </div>
    `;
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeL0Modal();
    });
    
    document.body.appendChild(modal);
}

// Close L0 modal
function closeL0Modal() {
    const modal = document.getElementById('l0-modal');
    if (modal) modal.remove();
}

// Add L0 entry
async function addL0Entry() {
    const role = document.getElementById('new-l0-role')?.value || 'user';
    const content = document.getElementById('new-l0-content')?.value?.trim();
    const importance = parseInt(document.getElementById('new-l0-importance')?.value || 50) / 100;
    
    if (!content) return;
    
    try {
        await API.progressiveSummarization.addL0('default', role, content, null, { importance });
        closeL0Modal();
        await renderProgressiveSummarization();
    } catch (error) {
        console.error('Add L0 entry error:', error);
    }
}

// Summarize L0 to L1
async function summarizeL0() {
    try {
        const result = await API.progressiveSummarization.summarizeL0('default');
        
        if (result.data.summarized) {
            await renderProgressiveSummarization();
        } else {
            alert(t('progressiveSumm.noL0ToSummarize'));
        }
    } catch (error) {
        console.error('Summarize L0 error:', error);
    }
}

// Summarize L1 to L2
async function summarizeL1() {
    try {
        const result = await API.progressiveSummarization.summarizeL1('default');
        
        if (result.data.summarized) {
            await renderProgressiveSummarization();
        } else {
            alert(t('progressiveSumm.noL1ToSummarize'));
        }
    } catch (error) {
        console.error('Summarize L1 error:', error);
    }
}

// Run auto process
async function runAutoProcess() {
    try {
        await API.progressiveSummarization.autoProcess('default');
        await renderProgressiveSummarization();
    } catch (error) {
        console.error('Auto process error:', error);
    }
}

// Format date
function formatDate(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
