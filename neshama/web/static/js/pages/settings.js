/**
 * Settings Page - Model and platform configuration
 */

let currentConfig = null;

/**
 * Render the new theme selector UI
 */
function renderThemeSelector(currentTheme) {
    const themes = [
        { id: 'ocean', emoji: 'Ocean' },
        { id: 'spring', emoji: 'Spring' },
        { id: 'midnight', emoji: 'Midnight' },
        { id: 'cyberpunk', emoji: 'Cyber' },
        { id: 'sunset', emoji: 'Sunset' },
        { id: 'forest', emoji: 'Forest' },
        { id: 'slate', emoji: 'Slate' },
        { id: 'purple', emoji: 'Purple' }
    ];
    
    return `
        <div class="theme-selector">
            ${themes.map(theme => `
                <div class="theme-option ${currentTheme === theme.id ? 'active' : ''}" 
                     data-theme="${theme.id}"
                     onclick="selectTheme('${theme.id}')">
                    <div class="theme-preview"></div>
                    <div class="theme-name-en">${theme.emoji} ${t('theme.' + theme.id)}</div>
                </div>
            `).join('')}
        </div>
    `;
}

/**
 * Select and apply a theme
 */
function selectTheme(themeId) {
    window.ThemeManager.setTheme(themeId);
}

/**
 * Get current theme from ThemeManager
 */
function getCurrentTheme() {
    return window.ThemeManager?.getCurrentTheme() || 'ocean';
}

// Render Settings Page
async function renderSettings() {
    const container = document.getElementById('page-settings');
    const currentTheme = getCurrentTheme();
    
    try {
        const [configRes, providersRes, adaptersRes] = await Promise.all([
            API.config.get(),
            API.config.getModelProviders(),
            API.config.getPlatformAdapters()
        ]);
        
        currentConfig = configRes.data;
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('settings.title')}</h1>
                <p class="page-subtitle">${t('settings.subtitle')}</p>
            </div>
            
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('settings.modelConfig')}</span>
                    </div>
                    <div class="mt-4">
                        <div class="form-group">
                            <label class="form-label">${t('settings.provider')}</label>
                            <select id="config-provider" class="form-input" onchange="updateModelOptions()">
                                ${providersRes.data.map(p => `
                                    <option value="${p.id}" ${currentConfig.model.provider === p.id ? 'selected' : ''}>
                                        ${p.name}
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">${t('settings.model')}</label>
                            <select id="config-model" class="form-input">
                                ${renderModelOptions(providersRes.data, currentConfig.model.provider)}
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">${t('settings.temperature')}: <span id="temp-value">${currentConfig.model.temperature}</span></label>
                            <input type="range" id="config-temperature" class="form-input" 
                                min="0" max="1" step="0.1" value="${currentConfig.model.temperature}"
                                oninput="document.getElementById('temp-value').textContent = this.value">
                        </div>
                        <div class="form-group">
                            <label class="form-label">${t('settings.maxTokens')}</label>
                            <input type="number" id="config-max-tokens" class="form-input" 
                                value="${currentConfig.model.max_tokens}" min="100" max="32000">
                        </div>
                        <div class="form-group">
                            <label class="form-label">${t('settings.apiKey')}</label>
                            <div class="flex gap-2">
                                <input type="password" id="config-api-key" class="form-input" 
                                    value="••••••••••••••••" placeholder="Enter API key">
                                <button class="btn btn-secondary" onclick="testApiKey()">${t('settings.test')}</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('theme.appearance')}</span>
                    </div>
                    <div class="mt-4">
                        <div class="form-group">
                            <label class="form-label">${t('theme.chooseTheme')}</label>
                            ${renderThemeSelector(currentTheme)}
                        </div>
                        <div class="form-group" style="margin-top: 24px;">
                            <label class="form-label">${t('theme.current')}: ${getThemeDisplayName(currentTheme)}</label>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('settings.behavior')}</span>
                </div>
                <div class="mt-4">
                    <div class="grid-2 gap-4">
                        ${renderBehaviorToggle(t('settings.streamResponses'), 'stream_responses', currentConfig.behavior.stream_responses)}
                        ${renderBehaviorToggle(t('settings.showEmotions'), 'show_emotions', currentConfig.behavior.show_emotions)}
                        ${renderBehaviorToggle(t('settings.enableEvolution'), 'enable_evolution', currentConfig.behavior.enable_evolution)}
                        ${renderBehaviorToggle(t('settings.memoryEnabled'), 'memory_enabled', currentConfig.behavior.memory_enabled)}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('settings.debug')}</span>
                </div>
                <div class="mt-4">
                    <div class="grid-2 gap-4">
                        <div class="form-group">
                            <label class="form-label">${t('settings.logLevel')}</label>
                            <select id="config-log-level" class="form-input">
                                <option value="debug" ${currentConfig.debug.log_level === 'debug' ? 'selected' : ''}>${t('settings.logDebug')}</option>
                                <option value="info" ${currentConfig.debug.log_level === 'info' ? 'selected' : ''}>${t('settings.logInfo')}</option>
                                <option value="warn" ${currentConfig.debug.log_level === 'warn' ? 'selected' : ''}>${t('settings.logWarn')}</option>
                                <option value="error" ${currentConfig.debug.log_level === 'error' ? 'selected' : ''}>${t('settings.logError')}</option>
                            </select>
                        </div>
                        ${renderBehaviorToggle(t('settings.showTimestamps'), 'show_timestamps', currentConfig.debug.show_timestamps)}
                        ${renderBehaviorToggle(t('settings.performanceMetrics'), 'performance_metrics', currentConfig.debug.performance_metrics)}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('settings.importExportReset')}</span>
                </div>
                <div class="flex gap-3 mt-4">
                    <button class="btn btn-secondary" onclick="exportConfig()">${t('settings.exportConfig')}</button>
                    <label class="btn btn-secondary" style="cursor: pointer;">
                        ${t('settings.importConfig')}
                        <input type="file" accept=".json" style="display: none;" onchange="importConfig(event)">
                    </label>
                    <button class="btn btn-secondary" style="margin-left: auto;" onclick="resetConfig()">${t('settings.resetDefaults')}</button>
                </div>
            </div>
            
            <div class="flex gap-3 mt-4" style="justify-content: flex-end;">
                <button class="btn btn-secondary" onclick="renderSettings()">${t('settings.discardChanges')}</button>
                <button class="btn btn-primary" onclick="saveConfig()">${t('settings.saveSettings')}</button>
            </div>
        `;
        
    } catch (error) {
        console.error('Settings load error:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">Settings</div>
                <div class="empty-state-text">${t('settings.failedLoad')}</div>
                <div class="text-muted mt-2" style="font-size: 12px;">${error.message || ''}</div>
                <button class="btn btn-primary mt-4" onclick="renderSettings()">${t('common.retry')}</button>
            </div>
        `;
        Toast.show(t('common.error'), 'error');
    }
}

/**
 * Get display name for a theme
 */
function getThemeDisplayName(themeId) {
    const themeEmojis = {
        'ocean': 'Ocean',
        'spring': 'Spring',
        'midnight': 'Midnight',
        'cyberpunk': 'Cyber',
        'sunset': 'Sunset',
        'forest': 'Forest',
        'slate': 'Slate',
        'purple': 'Purple'
    };
    const emoji = themeEmojis[themeId] || 'Theme';
    return `${emoji} ${t('theme.' + themeId)}`;
}

// Render model options
function renderModelOptions(providers, currentProvider) {
    const provider = providers.find(p => p.id === currentProvider);
    if (!provider) return '<option value="">Select model</option>';
    
    return provider.models.map(m => `
        <option value="${m}">${m}</option>
    `).join('');
}

// Update model options based on provider
function updateModelOptions() {
    const provider = document.getElementById('config-provider').value;
    // In a real app, this would fetch models for the selected provider
    const mockModels = {
        'openai': ['gpt-4', 'gpt-3.5-turbo'],
        'anthropic': ['claude-3-opus', 'claude-3-sonnet'],
        'google': ['gemini-pro'],
        'mock': ['mock-model']
    };
    
    const models = mockModels[provider] || ['default-model'];
    document.getElementById('config-model').innerHTML = models.map(m => 
        `<option value="${m}">${m}</option>`
    ).join('');
}

// Render behavior toggle
function renderBehaviorToggle(label, key, value) {
    return `
        <div class="flex justify-between items-center" style="padding: 14px 16px; background: var(--bg-tertiary); border-radius: 10px;">
            <span>${label}</span>
            <label class="switch">
                <input type="checkbox" id="behavior-${key}" ${value ? 'checked' : ''}>
                <span class="slider"></span>
            </label>
        </div>
    `;
}

// Test API key
async function testApiKey() {
    const provider = document.getElementById('config-provider').value;
    const apiKey = document.getElementById('config-api-key').value;
    
    if (apiKey === '••••••••••••••••' || apiKey.length < 10) {
        showToast(t('settings.enterValidKey'), 'error');
        return;
    }
    
    showToast(t('settings.testing'));
    
    try {
        const res = await API.config.testApiKey(provider, apiKey);
        if (res.success) {
            showToast(t('settings.keyValid'));
        } else {
            showToast(t('settings.keyInvalid'), 'error');
        }
    } catch (error) {
        showToast(t('common.error'), 'error');
    }
}

// Save config
async function saveConfig() {
    const updates = {
        model: {
            provider: document.getElementById('config-provider').value,
            model_name: document.getElementById('config-model').value,
            temperature: parseFloat(document.getElementById('config-temperature').value),
            max_tokens: parseInt(document.getElementById('config-max-tokens').value)
        },
        appearance: {
            theme: getCurrentTheme(),
            accent_color: currentConfig?.appearance?.accent_color || '#7c5cff',
            font_size: currentConfig?.appearance?.font_size || 14
        },
        behavior: {
            stream_responses: document.getElementById('behavior-stream_responses')?.checked ?? true,
            show_emotions: document.getElementById('behavior-show_emotions')?.checked ?? true,
            enable_evolution: document.getElementById('behavior-enable_evolution')?.checked ?? true,
            memory_enabled: document.getElementById('behavior-memory_enabled')?.checked ?? true
        },
        debug: {
            log_level: document.getElementById('config-log-level').value,
            show_timestamps: document.getElementById('behavior-show_timestamps')?.checked ?? true,
            performance_metrics: document.getElementById('behavior-performance_metrics')?.checked ?? false
        }
    };
    
    try {
        await API.config.update(updates);
        showToast(t('settings.saved'));
    } catch (error) {
        showToast(t('settings.saveFailed'), 'error');
    }
}

// Export config
async function exportConfig() {
    try {
        const res = await API.config.export();
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = res.filename;
        a.click();
        URL.revokeObjectURL(url);
        showToast(t('common.success'));
    } catch (error) {
        showToast(t('common.error'), 'error');
    }
}

// Import config
async function importConfig(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        const text = await file.text();
        const config = JSON.parse(text);
        await API.config.import(config);
        showToast(t('common.success'));
        renderSettings();
    } catch (error) {
        showToast(t('common.error'), 'error');
    }
}

// Reset config
async function resetConfig() {
    if (!confirm(t('settings.resetConfirm'))) return;
    
    try {
        await API.config.reset();
        showToast(t('settings.resetDone'));
        renderSettings();
    } catch (error) {
        showToast(t('settings.resetFailed'), 'error');
    }
}
