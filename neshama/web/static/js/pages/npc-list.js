/**
 * NPC List Page - Display and manage all NPC souls
 */

// Store for selected NPCs (batch operations)
let selectedNPCs = new Set();

// Render NPC List Page
async function renderNPCList() {
    const container = document.getElementById('page-npc-list');
    
    try {
        const res = await API.game.listNPCs();
        AppState.npcs = res.data || [];
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('npcList.title')}</h1>
                <p class="page-subtitle">${t('npcList.subtitle')}</p>
            </div>
            
            <div class="flex justify-between items-center mb-4">
                <div class="search-box" style="max-width: 300px;">
                    <input type="text" id="npc-search" class="form-input" 
                        placeholder="${t('npcList.searchNPCs')}" 
                        oninput="filterNPCs(this.value)">
                </div>
                <div class="flex gap-2">
                    <button class="btn btn-secondary" id="batch-delete-btn" 
                        onclick="batchDeleteNPCs()" disabled>
                        ${t('npcList.batchDelete')}
                        <span id="selected-count" class="badge" style="display: none;">0</span>
                    </button>
                    <button class="btn btn-secondary" id="export-btn"
                        onclick="exportSelectedNPCs()" disabled>
                        ${t('npcList.exportSelected')}
                    </button>
                    <button class="btn btn-primary" onclick="showCreateNPCModal()">
                        ${t('npcList.createNPC')}
                    </button>
                </div>
            </div>
            
            <div id="npc-grid" class="npc-grid">
                ${renderNPCCards(AppState.npcs)}
            </div>
        `;
        
    } catch (error) {
        console.error('Failed to load NPC list:', error);
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('npcList.title')}</h1>
                <p class="page-subtitle">${t('npcList.subtitle')}</p>
            </div>
            <div class="empty-state">
                <div class="empty-state-icon">🎭</div>
                <div class="empty-state-text">${t('npcList.loadFailed')}</div>
                <div class="text-muted mt-2" style="font-size: 12px;">${error.message || ''}</div>
                <button class="btn btn-primary mt-4" onclick="renderNPCList()">${t('common.retry')}</button>
            </div>
        `;
    }
}

// Render NPC Cards
function renderNPCCards(npcs) {
    if (!npcs || npcs.length === 0) {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">🎭</div>
                <div class="empty-state-text">${t('npcList.noNPCs')}</div>
                <div class="text-muted mt-2">${t('npcList.createFirst')}</div>
                <button class="btn btn-primary mt-4" onclick="showCreateNPCModal()">
                    ${t('npcList.createNPC')}
                </button>
            </div>
        `;
    }
    
    return npcs.map(npc => {
        const emotion = npc.emotion || {};
        const emotionLabel = emotion.primary?.category || 'Neutral';
        const emotionName = emotion.primary?.category || 'Neutral';
        const isOnline = npc.online || false;
        
        return `
            <div class="npc-card" data-npc-id="${npc.id}" onclick="viewNPCDetail('${npc.id}')">
                <div class="npc-card-header">
                    <div class="npc-avatar">
                        ${npc.avatar || '🎭'}
                    </div>
                    <div class="npc-status ${isOnline ? 'online' : 'offline'}"></div>
                    <input type="checkbox" class="npc-checkbox" 
                        onclick="event.stopPropagation(); toggleNPCSelection('${npc.id}')"
                        ${selectedNPCs.has(npc.id) ? 'checked' : ''}>
                </div>
                <div class="npc-card-body">
                    <h3 class="npc-name">${escapeHtml(npc.name)}</h3>
                    <div class="npc-preset">${t(`npcList.preset.${npc.preset || 'custom'}`) || npc.preset}</div>
                    <div class="npc-emotion">
                        <span class="emotion-dot" style="background:${EMOTION_COLORS[emotionLabel] || '#94a3b8'}"></span><span class="emotion-label">${emotionLabel}</span>
                        <span class="emotion-name">${emotionName}</span>
                    </div>
                </div>
                <div class="npc-card-footer">
                    <button class="btn btn-sm btn-secondary" 
                        onclick="event.stopPropagation(); viewNPCDetail('${npc.id}')">
                        ${t('npcList.viewDetail')}
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Show Create NPC Modal
function showCreateNPCModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'create-npc-modal';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h3>${t('npcList.createNPC')}</h3>
                <button class="btn btn-icon" onclick="closeCreateNPCModal()">✕</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">${t('npcList.npcName')}</label>
                    <input type="text" id="new-npc-name" class="form-input" 
                        placeholder="${t('npcList.npcNamePlaceholder')}">
                </div>
                <div class="form-group">
                    <label class="form-label">${t('npcList.selectPreset')}</label>
                    <select id="new-npc-preset" class="form-input">
                        <option value="tavern_keeper">${t('npcList.preset.tavern_keeper')}</option>
                        <option value="guard_captain">${t('npcList.preset.guard_captain')}</option>
                        <option value="custom">${t('npcList.preset.custom')}</option>
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeCreateNPCModal()">
                    ${t('common.cancel')}
                </button>
                <button class="btn btn-primary" onclick="createNPC()">
                    ${t('npcList.createNPC')}
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    
    // Focus on name input
    setTimeout(() => {
        document.getElementById('new-npc-name').focus();
    }, 100);
}

// Close Create NPC Modal
function closeCreateNPCModal() {
    const modal = document.getElementById('create-npc-modal');
    if (modal) modal.remove();
}

// Create NPC
async function createNPC() {
    const name = document.getElementById('new-npc-name').value.trim();
    const preset = document.getElementById('new-npc-preset').value;
    
    if (!name) {
        showToast(t('npcList.enterName'), 'error');
        return;
    }
    
    try {
        const res = await API.game.createNPC(name, preset);
        if (res.success) {
            showToast(t('npcList.createSuccess'), 'success');
            closeCreateNPCModal();
            renderNPCList();
        } else {
            showToast(t('npcList.createFailed'), 'error');
        }
    } catch (error) {
        console.error('Create NPC failed:', error);
        showToast(t('npcList.createFailed'), 'error');
    }
}

// Toggle NPC Selection (for batch operations)
function toggleNPCSelection(npcId) {
    if (selectedNPCs.has(npcId)) {
        selectedNPCs.delete(npcId);
    } else {
        selectedNPCs.add(npcId);
    }
    updateBatchButtonState();
}

// Update Batch Button State
function updateBatchButtonState() {
    const count = selectedNPCs.size;
    const batchBtn = document.getElementById('batch-delete-btn');
    const exportBtn = document.getElementById('export-btn');
    const countBadge = document.getElementById('selected-count');
    
    if (batchBtn) {
        batchBtn.disabled = count === 0;
    }
    if (exportBtn) {
        exportBtn.disabled = count === 0;
    }
    if (countBadge) {
        if (count > 0) {
            countBadge.style.display = 'inline';
            countBadge.textContent = count;
        } else {
            countBadge.style.display = 'none';
        }
    }
}

// Batch Delete NPCs
async function batchDeleteNPCs() {
    if (selectedNPCs.size === 0) return;
    
    if (!confirm(t('npcList.deleteConfirm'))) return;
    
    try {
        const res = await API.game.batchDelete([...selectedNPCs]);
        if (res.success) {
            showToast(t('npcList.deleteSuccess'), 'success');
            selectedNPCs.clear();
            updateBatchButtonState();
            renderNPCList();
        } else {
            showToast(t('npcList.deleteFailed'), 'error');
        }
    } catch (error) {
        console.error('Batch delete failed:', error);
        showToast(t('npcList.deleteFailed'), 'error');
    }
}

// Export Selected NPCs
async function exportSelectedNPCs() {
    if (selectedNPCs.size === 0) return;
    
    try {
        for (const npcId of selectedNPCs) {
            const res = await API.game.exportNPC(npcId);
            if (res.success && res.data) {
                downloadJSON(res.data, `npc_${npcId}.json`);
            }
        }
        showToast(t('npcList.exportSuccess'), 'success');
    } catch (error) {
        console.error('Export failed:', error);
        showToast(t('npcList.deleteFailed'), 'error');
    }
}

// View NPC Detail
function viewNPCDetail(npcId) {
    AppState.selectedNPC = npcId;
    router.navigate('npc-detail');
}

// Filter NPCs by search query
function filterNPCs(query) {
    const filtered = AppState.npcs.filter(npc => 
        npc.name.toLowerCase().includes(query.toLowerCase()) ||
        (npc.preset && npc.preset.toLowerCase().includes(query.toLowerCase()))
    );
    
    const grid = document.getElementById('npc-grid');
    if (grid) {
        grid.innerHTML = renderNPCCards(filtered);
    }
}

// Refresh NPC List
async function refreshNPCList() {
    try {
        const res = await API.game.listNPCs();
        AppState.npcs = res.data || [];
        
        const grid = document.getElementById('npc-grid');
        if (grid) {
            const searchQuery = document.getElementById('npc-search')?.value || '';
            const filtered = searchQuery ? 
                AppState.npcs.filter(npc => 
                    npc.name.toLowerCase().includes(searchQuery.toLowerCase())
                ) : AppState.npcs;
            grid.innerHTML = renderNPCCards(filtered);
        }
    } catch (error) {
        console.error('Refresh NPC list failed:', error);
    }
}

// Download JSON file
function downloadJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Helper: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
