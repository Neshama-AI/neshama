/**
 * Evolution Page - Personality evolution timeline and snapshots
 */

let evolutionHistory = [];
let evolutionSnapshots = [];

// Render Evolution Page
async function renderEvolution() {
    const container = document.getElementById('page-evolution');
    
    try {
        const [historyRes, snapshotsRes] = await Promise.all([
            API.evolution.getHistory(30),
            API.evolution.getSnapshots()
        ]);
        
        evolutionHistory = historyRes.data.history || [];
        evolutionSnapshots = snapshotsRes.data || [];
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('evolution.title')}</h1>
                <p class="page-subtitle">${t('evolution.subtitle')}</p>
            </div>
            
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('evolution.currentVsBaseline')}</span>
                    </div>
                    <div class="mt-4">
                        ${renderBaselineComparison(historyRes.data)}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('evolution.snapshots')}</span>
                        <button class="btn btn-sm btn-primary" onclick="showCreateSnapshotModal()">+ ${t('evolution.create')}</button>
                    </div>
                    <div id="snapshots-list" class="mt-4">
                        ${renderSnapshots(snapshotsRes.data || [])}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('evolution.oceanOverTime')}</span>
                    <select id="evolution-days" class="form-input" style="width: auto;" onchange="changeEvolutionDays()">
                        <option value="7">${t('evolution.last7d')}</option>
                        <option value="14">${t('evolution.last14d')}</option>
                        <option value="30" selected>${t('evolution.last30d')}</option>
                        <option value="60">${t('evolution.last60d')}</option>
                    </select>
                </div>
                <div class="canvas-container" style="height: 300px;">
                    <canvas id="evolution-chart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('evolution.events')}</span>
                </div>
                <div id="evolution-events" class="mt-4">
                    ${renderEvolutionEvents()}
                </div>
            </div>
        `;
        
        // Draw evolution chart
        setTimeout(() => drawEvolutionChart(evolutionHistory), 100);
        
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📈</div>
                <div class="empty-state-text">${t('evolution.failedLoad')}</div>
                <button class="btn btn-primary mt-4" onclick="renderEvolution()">${t('common.retry')}</button>
            </div>
        `;
    }
}

// Render baseline comparison
function renderBaselineComparison(data) {
    if (!data) return `<div class="text-muted">${t('evolution.noData')}</div>`;
    
    const current = data.current || {};
    const baseline = data.baseline || {};
    const keys = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
    const labels = [t('ocean.openness'), t('ocean.conscientiousness'), t('ocean.extraversion'), t('ocean.agreeableness'), t('ocean.neuroticism')];
    
    return keys.map((key, i) => {
        const diff = ((current[key] || 0) - (baseline[key] || 0)) * 100;
        const diffStr = diff >= 0 ? `+${diff.toFixed(0)}` : diff.toFixed(0);
        const diffClass = diff >= 0 ? 'emotion-joy' : 'emotion-sadness';
        
        return `
            <div class="flex items-center justify-between mb-3">
                <span style="width: 120px;">${labels[i]}</span>
                <div style="flex: 1; display: flex; gap: 8px; align-items: center;">
                    <div class="progress-bar" style="flex: 1;">
                        <div class="progress-fill" style="width: ${(current[key] || 0) * 100}%;"></div>
                    </div>
                    <span class="text-accent" style="width: 35px;">${((current[key] || 0) * 100).toFixed(0)}%</span>
                    <span class="${diffClass}" style="width: 45px; font-size: 12px;">${diffStr}%</span>
                </div>
            </div>
        `;
    }).join('');
}

// Render snapshots
function renderSnapshots(snapshots) {
    if (!snapshots.length) {
        return `<div class="text-muted">${t('evolution.noSnapshots')}</div>`;
    }
    
    return snapshots.map(snap => `
        <div class="flex items-center justify-between mb-2" style="padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
            <div>
                <div style="font-weight: 500;">${snap.name}</div>
                <div class="text-muted" style="font-size: 12px;">${snap.date} - ${snap.description || t('evolution.noDescription')}</div>
            </div>
            <div class="flex gap-2">
                <button class="btn btn-icon btn-secondary btn-sm" onclick="compareSnapshots('${snap.id}')" title="Compare">📊</button>
                <button class="btn btn-icon btn-secondary btn-sm" onclick="deleteSnapshot('${snap.id}')" title="${t('common.delete')}">🗑️</button>
            </div>
        </div>
    `).join('');
}

// Draw evolution chart
function drawEvolutionChart(history) {
    const canvas = document.getElementById('evolution-chart');
    if (!canvas || !history.length) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = 300;
    
    // Clear
    ctx.clearRect(0, 0, width, height);
    
    // Margins
    const margin = { top: 20, right: 80, bottom: 50, left: 50 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // Colors for each trait
    const colors = {
        'openness': '#4F46E5',
        'conscientiousness': '#22C55E',
        'extraversion': '#F59E0B',
        'agreeableness': '#EC4899',
        'neuroticism': '#8B5CF6'
    };
    
    const labels = [t('ocean.openness'), t('ocean.conscientiousness'), t('ocean.extraversion'), t('ocean.agreeableness'), t('ocean.neuroticism')];
    const keys = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
    
    // Draw grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 4; i++) {
        const y = margin.top + (chartHeight * i / 4);
        ctx.beginPath();
        ctx.moveTo(margin.left, y);
        ctx.lineTo(width - margin.right, y);
        ctx.stroke();
        
        // Y-axis labels
        ctx.fillStyle = '#64748B';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`${(1 - i / 4).toFixed(1)}`, margin.left - 8, y + 3);
    }
    
    // Sample data
    const step = Math.max(1, Math.floor(history.length / 30));
    const sampledData = history.filter((_, i) => i % step === 0);
    
    // Draw lines for each trait
    keys.forEach((key, traitIdx) => {
        ctx.beginPath();
        ctx.strokeStyle = colors[key];
        ctx.lineWidth = 2;
        
        sampledData.forEach((point, i) => {
            const x = margin.left + (i / (sampledData.length - 1)) * chartWidth;
            const y = margin.top + (1 - (point.values?.[key] || 0.5)) * chartHeight;
            
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
        
        // Points
        sampledData.forEach((point, i) => {
            const x = margin.left + (i / (sampledData.length - 1)) * chartWidth;
            const y = margin.top + (1 - (point.values?.[key] || 0.5)) * chartHeight;
            
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fillStyle = colors[key];
            ctx.fill();
        });
    });
    
    // Legend
    const legendX = width - margin.right + 10;
    labels.forEach((label, i) => {
        const y = margin.top + i * 30 + 10;
        
        ctx.fillStyle = colors[keys[i]];
        ctx.fillRect(legendX, y - 8, 12, 12);
        
        ctx.fillStyle = '#F8FAFC';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(label, legendX + 18, y + 2);
    });
    
    // X-axis labels
    ctx.fillStyle = '#64748B';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    
    const labelCount = 5;
    for (let i = 0; i < labelCount; i++) {
        const idx = Math.floor(i * (sampledData.length - 1) / (labelCount - 1));
        const point = sampledData[idx];
        if (point) {
            const x = margin.left + (idx / (sampledData.length - 1)) * chartWidth;
            const date = new Date(point.date).toLocaleDateString([], { month: 'short', day: 'numeric' });
            ctx.fillText(date, x, height - 15);
        }
    }
}

// Render evolution events
function renderEvolutionEvents() {
    // Mock events based on evolution data
    const events = [
        { type: 'interaction', description: t('evolution.event.interaction'), traits: ['openness'], date: '2 days ago', magnitude: 0.02 },
        { type: 'learning', description: t('evolution.event.learning'), traits: ['conscientiousness'], date: '5 days ago', magnitude: 0.03 },
        { type: 'social', description: t('evolution.event.social'), traits: ['extraversion', 'agreeableness'], date: '1 week ago', magnitude: 0.02 },
        { type: 'challenge', description: t('evolution.event.challenge'), traits: ['neuroticism'], date: '2 weeks ago', magnitude: -0.02 }
    ];
    
    const typeIcons = {
        'interaction': '💬',
        'learning': '📚',
        'social': '🤝',
        'challenge': '⚡'
    };
    
    const typeColors = {
        'interaction': '#4F46E5',
        'learning': '#22C55E',
        'social': '#F59E0B',
        'challenge': '#EF4444'
    };
    
    return events.map(event => `
        <div class="flex items-center gap-4 mb-3" style="padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
            <div style="font-size: 32px;">${typeIcons[event.type] || '📌'}</div>
            <div style="flex: 1;">
                <div style="font-weight: 500;">${event.description}</div>
                <div class="flex gap-2 mt-2">
                    ${event.traits.map(t => `<span class="tag" style="background: ${typeColors[event.type]}20; color: ${typeColors[event.type]};">${t}</span>`).join('')}
                </div>
            </div>
            <div style="text-align: right;">
                <div class="${event.magnitude >= 0 ? 'emotion-joy' : 'emotion-sadness'}">
                    ${event.magnitude >= 0 ? '+' : ''}${(event.magnitude * 100).toFixed(0)}%
                </div>
                <div class="text-muted" style="font-size: 12px;">${event.date}</div>
            </div>
        </div>
    `).join('');
}

// Change evolution days
async function changeEvolutionDays() {
    const select = document.getElementById('evolution-days');
    const days = parseInt(select.value);
    
    try {
        const res = await API.evolution.getHistory(days);
        evolutionHistory = res.data.history || [];
        drawEvolutionChart(evolutionHistory);
    } catch (error) {
        showToast(t('evolution.failedLoad'), 'error');
    }
}

// Show create snapshot modal
function showCreateSnapshotModal() {
    const modal = document.createElement('div');
    modal.id = 'snapshot-modal';
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
        <div class="card" style="width: 400px; max-width: 90%;">
            <div class="card-header">
                <span class="card-title">Create Snapshot</span>
                <button class="btn btn-icon btn-secondary" onclick="closeSnapshotModal()">✕</button>
            </div>
            <div class="mt-4">
                <div class="form-group">
                    <label class="form-label">Name</label>
                    <input type="text" id="snapshot-name" class="form-input" placeholder="e.g., Version 1.0">
                </div>
                <div class="form-group">
                    <label class="form-label">Description</label>
                    <textarea id="snapshot-description" class="form-input" rows="3" placeholder="Describe this snapshot..."></textarea>
                </div>
            </div>
            <div class="flex gap-3 mt-4" style="justify-content: flex-end;">
                <button class="btn btn-secondary" onclick="closeSnapshotModal()">Cancel</button>
                <button class="btn btn-primary" onclick="createSnapshot()">Create</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeSnapshotModal(); });
}

// Close snapshot modal
function closeSnapshotModal() {
    const modal = document.getElementById('snapshot-modal');
    if (modal) modal.remove();
}

// Create snapshot
async function createSnapshot() {
    const name = document.getElementById('snapshot-name').value.trim();
    const description = document.getElementById('snapshot-description').value.trim();
    
    if (!name) {
        showToast('Please enter a name', 'error');
        return;
    }
    
    try {
        await API.evolution.createSnapshot(name, description);
        closeSnapshotModal();
        showToast('Snapshot created');
        renderEvolution();
    } catch (error) {
        showToast('Failed to create snapshot', 'error');
    }
}

// Compare snapshots
async function compareSnapshots(snapId) {
    // For demo, compare with first snapshot
    if (evolutionSnapshots.length < 2) {
        showToast('Need at least 2 snapshots to compare', 'error');
        return;
    }
    
    const otherSnap = evolutionSnapshots.find(s => s.id !== snapId);
    if (!otherSnap) return;
    
    try {
        const res = await API.evolution.compareSnapshots(snapId, otherSnap.id);
        showToast(`Comparing: ${res.data.differences.openness > 0 ? '↑' : '↓'} openness by ${(res.data.differences.openness * 100).toFixed(0)}%`);
    } catch (error) {
        showToast('Failed to compare snapshots', 'error');
    }
}

// Delete snapshot
async function deleteSnapshot(snapId) {
    if (!confirm('Delete this snapshot?')) return;
    showToast('Snapshot deleted (demo mode)');
    renderEvolution();
}
