/**
 * Soul Config Page - OCEAN sliders, traits, presets
 */

let currentSoulConfig = null;

// Render Soul Config Page
async function renderSoulConfig() {
    const container = document.getElementById('page-soul-config');
    
    try {
        const res = await API.soul.get();
        currentSoulConfig = res.data;
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('soulConfig.title')}</h1>
                <p class="page-subtitle">${t('soulConfig.subtitle')}</p>
            </div>
            
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('soulConfig.oceanTraits')}</span>
                        <span class="tag tag-primary">${t('soulConfig.core')}</span>
                    </div>
                    <div class="mt-4">
                        ${renderOceanSliders(currentSoulConfig.ocean)}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('soulConfig.personalityPreview')}</span>
                        <button class="btn btn-sm btn-secondary" onclick="updateRadarPreview()">${t('soulConfig.refresh')}</button>
                    </div>
                    <div class="canvas-container">
                        <canvas id="config-radar" width="280" height="280"></canvas>
                    </div>
                    <div class="text-center mt-3">
                        <button class="btn btn-primary" onclick="saveSoulConfig()">${t('soulConfig.saveConfig')}</button>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('soulConfig.personalityPresets')}</span>
                </div>
                <div class="grid-4 mt-3">
                    ${renderPresets(currentSoulConfig.presets)}
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('soulConfig.behavioralTraits')}</span>
                </div>
                <div class="mt-4">
                    ${renderTraitSwitches(currentSoulConfig.traits)}
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('soulConfig.desirePriorities')}</span>
                    <span class="text-muted" style="font-size: 12px;">${t('soulConfig.dragToReorder')}</span>
                </div>
                <div id="desires-drag-list" class="mt-3">
                    ${renderDesiresDraggable(currentSoulConfig.desires)}
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('soulConfig.importExport')}</span>
                </div>
                <div class="flex gap-3 mt-3">
                    <button class="btn btn-secondary" onclick="exportSoulConfig()">${t('soulConfig.exportConfig')}</button>
                    <label class="btn btn-secondary" style="cursor: pointer;">
                        ${t('soulConfig.importConfig')}
                        <input type="file" accept=".json" style="display: none;" onchange="importSoulConfig(event)">
                    </label>
                </div>
            </div>
        `;
        
        // Draw initial radar
        setTimeout(() => drawConfigRadar(currentSoulConfig.ocean), 100);
        
        // Setup slider listeners
        setupSliderListeners();
        
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚙️</div>
                <div class="empty-state-text">${t('soulConfig.failedLoad')}</div>
                <button class="btn btn-primary mt-4" onclick="renderSoulConfig()">${t('common.retry')}</button>
            </div>
        `;
    }
}

// Render OCEAN sliders
function renderOceanSliders(ocean) {
    const labels = [t('ocean.openness'), t('ocean.conscientiousness'), t('ocean.extraversion'), t('ocean.agreeableness'), t('ocean.neuroticism')];
    const keys = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
    const descriptions = {
        openness: t('trait.openness'),
        conscientiousness: t('trait.conscientiousness'),
        extraversion: t('trait.extraversion'),
        agreeableness: t('trait.agreeableness'),
        neuroticism: t('trait.neuroticism')
    };
    
    return keys.map((key, i) => `
        <div class="form-group">
            <div class="flex justify-between items-center mb-2">
                <label class="form-label" style="margin-bottom: 0;">${labels[i]}</label>
                <span class="range-value" id="value-${key}">${(ocean[key] || 0.5).toFixed(2)}</span>
            </div>
            <div class="range-slider">
                <input type="range" 
                    id="slider-${key}" 
                    min="0" 
                    max="1" 
                    step="0.01" 
                    value="${ocean[key] || 0.5}"
                    data-trait="${key}">
            </div>
            <div class="text-muted mt-1" style="font-size: 11px;">${descriptions[key]}</div>
        </div>
    `).join('');
}

// Setup slider listeners
function setupSliderListeners() {
    const sliders = document.querySelectorAll('input[type="range"][data-trait]');
    
    sliders.forEach(slider => {
        slider.addEventListener('input', debounce((e) => {
            const key = e.target.dataset.trait;
            const value = parseFloat(e.target.value);
            
            // Update value display
            const valueEl = document.getElementById(`value-${key}`);
            if (valueEl) valueEl.textContent = value.toFixed(2);
            
            // Update preview
            updateRadarPreview();
            
            // Update config
            if (currentSoulConfig) {
                currentSoulConfig.ocean[key] = value;
            }
        }, 100));
    });
}

// Update radar preview
function updateRadarPreview() {
    if (currentSoulConfig) {
        drawConfigRadar(currentSoulConfig.ocean);
    }
}

// Draw config radar chart
function drawConfigRadar(ocean) {
    const canvas = document.getElementById('config-radar');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 35;
    
    // Clear
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
    
    // Axes
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    for (let i = 0; i < 5; i++) {
        const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(centerX + radius * Math.cos(angle), centerY + radius * Math.sin(angle));
        ctx.stroke();
    }
    
    // Data
    const keys = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
    const labels = [t('ocean.openness'), t('ocean.conscientiousness'), t('ocean.extraversion'), t('ocean.agreeableness'), t('ocean.neuroticism')];
    const values = keys.map(key => ocean[key] || 0.5);
    
    // Fill
    ctx.fillStyle = 'rgba(79, 70, 229, 0.35)';
    ctx.beginPath();
    values.forEach((value, i) => {
        const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
        const r = radius * value;
        const x = centerX + r * Math.cos(angle);
        const y = centerY + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.fill();
    
    // Border
    ctx.strokeStyle = '#4F46E5';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Points
    values.forEach((value, i) => {
        const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
        const r = radius * value;
        const x = centerX + r * Math.cos(angle);
        const y = centerY + r * Math.sin(angle);
        
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#F59E0B';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
    });
    
    // Labels
    ctx.fillStyle = '#F8FAFC';
    ctx.font = '11px -apple-system, BlinkMacSystemFont, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    values.forEach((value, i) => {
        const angle = (Math.PI * 2 * i / 5) - Math.PI / 2;
        const labelRadius = radius + 20;
        const x = centerX + labelRadius * Math.cos(angle);
        const y = centerY + labelRadius * Math.sin(angle);
        ctx.fillText(labels[i], x, y);
    });
}

// Render presets
function renderPresets(presets) {
    const presetDescriptions = {
        'analyst': t('preset.analyst'),
        'helper': t('preset.helper'),
        'explorer': t('preset.explorer'),
        'leader': t('preset.leader'),
        'diplomat': t('preset.diplomat'),
        'sentinel': t('preset.sentinel'),
        'neshama': t('preset.neshama')
    };
    
    return presets.map(preset => `
        <div class="card" style="padding: 16px; cursor: pointer;" onclick="applyPreset('${preset}')">
            <div style="font-weight: 600; text-transform: capitalize;">${preset}</div>
            <div class="text-muted mt-1" style="font-size: 11px;">${presetDescriptions[preset] || ''}</div>
        </div>
    `).join('');
}

// Apply preset
async function applyPreset(preset) {
    try {
        await API.soul.applyPreset(preset);
        showToast(`${t('toast.presetApplied')}: ${preset}`);
        renderSoulConfig();
    } catch (error) {
        showToast(`${t('toast.presetFailed')}: ${error.message}`, 'error');
    }
}

// Render trait switches
function renderTraitSwitches(traits) {
    const traitLabels = {
        'directness': t('trait.directness'),
        'humor_level': t('trait.humorLevel'),
        'empathy_level': t('trait.empathyLevel'),
        'curiosity': t('trait.curiosity'),
        'creativity': t('trait.creativity')
    };
    
    return Object.entries(traits).map(([key, value]) => `
        <div class="flex justify-between items-center mb-3" style="padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
            <span>${traitLabels[key] || key}</span>
            <label class="switch">
                <input type="checkbox" ${value > 0.5 ? 'checked' : ''} 
                    onchange="updateTrait('${key}', this.checked ? 1 : 0)">
                <span class="slider"></span>
            </label>
        </div>
    `).join('') + `
        <style>
            .switch { position: relative; display: inline-block; width: 48px; height: 24px; }
            .switch input { opacity: 0; width: 0; height: 0; }
            .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: var(--bg-tertiary); border-radius: 24px; transition: 0.3s; }
            .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background: white; border-radius: 50%; transition: 0.3s; }
            input:checked + .slider { background: var(--accent-primary); }
            input:checked + .slider:before { transform: translateX(24px); }
        </style>
    `;
}

// Update trait
function updateTrait(trait, value) {
    if (currentSoulConfig) {
        currentSoulConfig.traits[trait] = value;
    }
}

// Render desires draggable
function renderDesiresDraggable(desires) {
    if (!desires) return `<div class="text-muted">${t('common.noData')}</div>`;
    
    return desires.map((d, i) => `
        <div class="flex items-center justify-between mb-2 desire-item" 
            style="padding: 12px 16px; background: var(--bg-tertiary); border-radius: 8px; cursor: grab;" 
            draggable="true" data-id="${d.id}">
            <div class="flex items-center gap-3">
                <span style="color: var(--text-muted);">☰</span>
                <span style="font-weight: 500;">${d.name}</span>
            </div>
            <div class="flex items-center gap-2">
                <span class="tag">${d.id}</span>
                <button class="btn btn-icon btn-secondary btn-sm" onclick="toggleDesireActive('${d.id}')">
                    ${d.active ? '✓' : '○'}
                </button>
            </div>
        </div>
    `).join('');
}

// Toggle desire active
function toggleDesireActive(id) {
    if (currentSoulConfig && currentSoulConfig.desires) {
        const desire = currentSoulConfig.desires.find(d => d.id === id);
        if (desire) {
            desire.active = !desire.active;
            renderSoulConfig();
        }
    }
}

// Save soul config
async function saveSoulConfig() {
    try {
        await API.soul.update(currentSoulConfig);
        showToast(t('soulConfig.saved'));
    } catch (error) {
        showToast(`${t('soulConfig.saveFailed')}: ${error.message}`, 'error');
    }
}

// Export soul config
async function exportSoulConfig() {
    try {
        const res = await API.soul.export();
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = res.filename;
        a.click();
        URL.revokeObjectURL(url);
        showToast(t('soulConfig.exported'));
    } catch (error) {
        showToast(`${t('soulConfig.exportFailed')}: ${error.message}`, 'error');
    }
}

// Import soul config
async function importSoulConfig(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        const text = await file.text();
        const config = JSON.parse(text);
        await API.soul.import(config);
        showToast(t('soulConfig.imported'));
        renderSoulConfig();
    } catch (error) {
        showToast(`${t('soulConfig.importFailed')}: ${error.message}`, 'error');
    }
}
