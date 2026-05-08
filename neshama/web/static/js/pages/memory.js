/**
 * Memory Page - Three-layer memory browser
 */

let currentLayer = 'L0';
let memoryData = {};

// Render Memory Page
async function renderMemory() {
    const container = document.getElementById('page-memory');
    
    try {
        const [layersRes, statsRes] = await Promise.all([
            API.memory.getLayers(),
            API.memory.getStats()
        ]);
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('memory.title')}</h1>
                <p class="page-subtitle">${t('memory.subtitle')}</p>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('memory.layers')}</span>
                    <span class="tag tag-primary">${t('memory.total')}: ${statsRes.data.total_memories}</span>
                </div>
                <div class="flex gap-4 mt-4">
                    ${renderLayerTabs(layersRes.data.layers)}
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title" id="layer-title">${getLayerName(currentLayer)}</span>
                    <div class="flex gap-2">
                        <input type="text" id="memory-search" class="form-input" style="width: 200px;" placeholder="${t('memory.searchPlaceholder')}" onkeyup="searchMemories()">
                        <button class="btn btn-primary btn-sm" onclick="showAddMemoryModal()">+ ${t('memory.add')}</button>
                    </div>
                </div>
                <div id="memory-list" class="mt-4">
                    <div class="loading">${t('memory.loading')}</div>
                </div>
            </div>
        `;
        
        // Load first layer memories
        loadLayerMemories(currentLayer);
        
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">Brain</div>
                <div class="empty-state-text">${t('memory.failedLoad')}</div>
                <button class="btn btn-primary mt-4" onclick="renderMemory()">${t('common.retry')}</button>
            </div>
        `;
    }
}

// Render layer tabs
function renderLayerTabs(layers) {
    return layers.map(layer => `
        <button class="btn ${currentLayer === layer.id ? 'btn-primary' : 'btn-secondary'}" 
            onclick="switchLayer('${layer.id}')">
            <span>${layer.name}</span>
            <span class="tag" style="margin-left: 8px;">${layer.count}</span>
        </button>
    `).join('');
}

// Get layer name
function getLayerName(layer) {
    const names = {
        'L0': t('memory.layer.l0'),
        'L1': t('memory.layer.l1'),
        'L2': t('memory.layer.l2')
    };
    return names[layer] || layer;
}

// Switch layer
function switchLayer(layer) {
    currentLayer = layer;
    
    // Update tab styling
    document.querySelectorAll('.card button.btn').forEach(btn => {
        if (btn.textContent.includes('Memory')) {
            btn.className = btn.textContent.includes(layer) ? 'btn btn-primary' : 'btn btn-secondary';
        }
    });
    
    // Update title
    document.getElementById('layer-title').textContent = getLayerName(layer);
    
    // Load memories
    loadLayerMemories(layer);
}

// Load layer memories
async function loadLayerMemories(layer, search = '') {
    const listContainer = document.getElementById('memory-list');
    if (!listContainer) return;
    
    try {
        const res = await API.memory.getLayer(layer, search);
        memoryData[layer] = res.data.memories || [];
        
        if (memoryData[layer].length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">Empty</div>
                    <div class="empty-state-text">${search ? t('memory.noMatch') : t('memory.noMemories')}</div>
                </div>
            `;
            return;
        }
        
        listContainer.innerHTML = memoryData[layer].map(mem => `
            <div class="memory-item mb-3" style="padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                <div class="flex justify-between items-start">
                    <div style="flex: 1;">
                        <div style="font-weight: 500; margin-bottom: 8px;">${escapeHtml(mem.content)}</div>
                        <div class="flex gap-3">
                            <span class="text-muted" style="font-size: 12px;">
                                ${formatDate(mem.timestamp)}
                            </span>
                            ${mem.context ? `<span class="tag">${mem.context}</span>` : ''}
                            ${mem.source ? `<span class="tag tag-amber">${mem.source}</span>` : ''}
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <div style="text-align: right;">
                            <div class="text-accent">${((mem.importance || 0.5) * 100).toFixed(0)}%</div>
                            <div class="text-muted" style="font-size: 10px;">${t('memory.importance')}</div>
                        </div>
                        <button class="btn btn-icon btn-secondary btn-sm" onclick="editMemory('${layer}', '${mem.id}')" title="${t('common.edit')}">Edit</button>
                        <button class="btn btn-icon btn-secondary btn-sm" onclick="deleteMemory('${layer}', '${mem.id}')" title="${t('common.delete')}">Delete</button>
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        listContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">×</div>
                <div class="empty-state-text">${t('memory.addFailed')}</div>
            </div>
        `;
    }
}

// Search memories
let searchTimeout;
function searchMemories() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const searchInput = document.getElementById('memory-search');
        const search = searchInput?.value || '';
        loadLayerMemories(currentLayer, search);
    }, 300);
}

// Show add memory modal
function showAddMemoryModal() {
    const modal = document.createElement('div');
    modal.id = 'memory-modal';
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
        <div class="card" style="width: 500px; max-width: 90%;">
            <div class="card-header">
                <span class="card-title">${t('memory.addMemory')} - ${getLayerName(currentLayer)}</span>
                <button class="btn btn-icon btn-secondary" onclick="closeMemoryModal()">✕</button>
            </div>
            <div class="mt-4">
                <div class="form-group">
                    <label class="form-label">${t('memory.content')}</label>
                    <textarea id="new-memory-content" class="form-input" rows="4" placeholder="${t('memory.enterContent')}"></textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">${t('memory.importance')} (0-1)</label>
                    <input type="range" id="new-memory-importance" min="0" max="1" step="0.1" value="0.5" 
                        oninput="document.getElementById('importance-value').textContent = this.value">
                    <span id="importance-value" class="text-accent">0.5</span>
                </div>
                <div class="form-group">
                    <label class="form-label">${t('memory.contextOptional')}</label>
                    <input type="text" id="new-memory-context" class="form-input" placeholder="${t('memory.contextPlaceholder')}">
                </div>
            </div>
            <div class="flex gap-3 mt-4" style="justify-content: flex-end;">
                <button class="btn btn-secondary" onclick="closeMemoryModal()">${t('common.cancel')}</button>
                <button class="btn btn-primary" onclick="addMemory()">${t('memory.add')}</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeMemoryModal();
    });
}

// Close memory modal
function closeMemoryModal() {
    const modal = document.getElementById('memory-modal');
    if (modal) modal.remove();
}

// Add memory
async function addMemory() {
    const content = document.getElementById('new-memory-content').value.trim();
    const importance = parseFloat(document.getElementById('new-memory-importance').value);
    const context = document.getElementById('new-memory-context').value.trim();
    
    if (!content) {
        showToast(t('memory.enterContent'), 'error');
        return;
    }
    
    try {
        await API.memory.addMemory(currentLayer, {
            content,
            importance,
            context: context || undefined
        });
        
        closeMemoryModal();
        showToast(t('memory.added'));
        loadLayerMemories(currentLayer);
    } catch (error) {
        showToast(t('memory.addFailed'), 'error');
    }
}

// Edit memory
function editMemory(layer, memoryId) {
    const memory = memoryData[layer]?.find(m => m.id === memoryId);
    if (!memory) return;
    
    // For simplicity, just show a prompt
    const newContent = prompt('Edit memory content:', memory.content);
    if (newContent && newContent !== memory.content) {
        updateMemory(layer, memoryId, { content: newContent });
    }
}

// Update memory
async function updateMemory(layer, memoryId, updates) {
    try {
        await API.memory.updateMemory(layer, memoryId, updates);
        showToast(t('memory.updated'));
        loadLayerMemories(layer);
    } catch (error) {
        showToast(t('memory.updateFailed'), 'error');
    }
}

// Delete memory
async function deleteMemory(layer, memoryId) {
    if (!confirm(t('memory.deleteConfirm'))) return;
    
    try {
        await API.memory.deleteMemory(layer, memoryId);
        showToast(t('memory.deleted'));
        loadLayerMemories(layer);
    } catch (error) {
        showToast(t('memory.deleteFailed'), 'error');
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format date
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
