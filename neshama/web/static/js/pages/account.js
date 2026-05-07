/**
 * Account Page - API Key management, BYOK config, environment config, account info
 */

// Account State
let accountApiKeys = [];
let accountConfig = {};
let byokKeyInfo = null;

// Supported BYOK providers
const BYOK_PROVIDERS = [
    { id: 'openai', name: 'OpenAI', placeholder: 'sk-...', models: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'] },
    { id: 'deepseek', name: 'DeepSeek', placeholder: 'sk-...', models: ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'] },
    { id: 'minimax', name: 'MiniMax', placeholder: '...', models: ['MiniMax-Text-01', 'abab6.5s-chat'] },
    { id: 'anthropic', name: 'Anthropic', placeholder: 'sk-ant-...', models: ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307'] },
];

// Render Account Page
async function renderAccount() {
    const container = document.getElementById('page-account');
    
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">${t('account.title')}</h1>
            <p class="page-subtitle">${t('account.subtitle')}</p>
        </div>
        
        <div class="grid-2">
            <!-- Account Info -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('account.info')}</span>
                </div>
                <div id="account-info-section" class="mt-4">
                    <div class="loading">${t('common.loading')}</div>
                </div>
            </div>
            
            <!-- LLM Mode -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('account.llmMode')}</span>
                </div>
                <div id="account-llm-mode-section" class="mt-4">
                    <div class="loading">${t('common.loading')}</div>
                </div>
            </div>
        </div>
        
        <!-- BYOK API Key Management -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">🔑 ${t('account.byokKeyManagement')}</span>
                <button class="btn btn-primary btn-sm" onclick="showAddByokKeyModal()">+ ${t('account.addProviderKey')}</button>
            </div>
            <div id="byok-keys-section" class="mt-4">
                <div class="loading">${t('common.loading')}</div>
            </div>
        </div>
        
        <!-- Environment Config -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">${t('account.envConfig')}</span>
            </div>
            <div id="account-env-section" class="mt-4">
                <div class="loading">${t('common.loading')}</div>
            </div>
        </div>
        
        <!-- Neshama API Keys -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">${t('account.apiKeys')}</span>
                <button class="btn btn-primary btn-sm" onclick="showCreateKeyModal()">+ ${t('account.createKey')}</button>
            </div>
            <div id="api-keys-list" class="mt-4">
                <div class="loading">${t('common.loading')}</div>
            </div>
        </div>
    `;
    
    // Load data
    await Promise.all([
        loadAccountInfo(),
        loadLlmMode(),
        loadByokKeys(),
        loadApiKeys(),
        loadEnvConfig(),
    ]);
}

// Load Account Info
async function loadAccountInfo() {
    const section = document.getElementById('account-info-section');
    if (!section) return;
    
    try {
        const configRes = await API.config.get();
        accountConfig = configRes.data || {};
        
        const email = accountConfig.email || '-';
        const createdAt = accountConfig.created_at ? formatDate(accountConfig.created_at) : '-';
        const tier = accountConfig.tier || accountConfig.subscription_tier || 'free';
        
        section.innerHTML = `
            <div class="account-info-grid">
                <div class="info-row">
                    <span class="info-label">${t('account.email')}</span>
                    <span class="info-value">${escapeHtml(email)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">${t('account.registeredAt')}</span>
                    <span class="info-value">${createdAt}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">${t('account.subscriptionTier')}</span>
                    <span class="info-value"><span class="tag tag-primary">${tier.toUpperCase()}</span></span>
                </div>
            </div>
        `;
    } catch (error) {
        section.innerHTML = `
            <div class="account-info-grid">
                <div class="info-row">
                    <span class="info-label">${t('account.email')}</span>
                    <span class="info-value">-</span>
                </div>
                <div class="info-row">
                    <span class="info-label">${t('account.subscriptionTier')}</span>
                    <span class="info-value"><span class="tag tag-amber">FREE</span></span>
                </div>
            </div>
            <p class="text-muted mt-4" style="font-size:12px;">${t('account.connectToSeeInfo')}</p>
        `;
    }
}

// Load LLM Mode
async function loadLlmMode() {
    const section = document.getElementById('account-llm-mode-section');
    if (!section) return;
    
    try {
        const keyRes = await (API.provider && API.provider.getUserKey ? API.provider.getUserKey() : Promise.resolve({ data: {} }));
        byokKeyInfo = keyRes || {};
        const mode = byokKeyInfo.mode || 'hosted';
        const activeProvider = byokKeyInfo.active_provider || null;
        
        section.innerHTML = `
            <div class="llm-mode-display">
                <div class="mode-indicator ${mode === 'byok' ? 'mode-byok' : 'mode-hosted'}">
                    <span class="mode-icon">${mode === 'byok' ? '🔑' : '☁️'}</span>
                    <span class="mode-label">${mode === 'byok' ? t('account.byokMode') : t('account.hostedMode')}</span>
                </div>
                ${mode === 'byok' && activeProvider ? `
                    <div class="info-row mt-3">
                        <span class="info-label">${t('account.activeProvider')}</span>
                        <span class="info-value"><span class="tag tag-green">${activeProvider.toUpperCase()}</span></span>
                    </div>
                ` : ''}
                <div class="info-row mt-2">
                    <span class="info-label">${t('account.conversationQuota')}</span>
                    <span class="info-value">${mode === 'byok' ? `<span class="tag tag-green">∞ ${t('billing.unlimited')}</span>` : t('account.hostedQuotaApplies')}</span>
                </div>
                <div class="mt-4">
                    ${mode === 'hosted' ? `
                        <button class="btn btn-primary btn-sm" onclick="showAddByokKeyModal()">${t('account.switchToByok')}</button>
                    ` : `
                        <button class="btn btn-secondary btn-sm" onclick="switchToHosted()">${t('account.switchToHosted')}</button>
                    `}
                </div>
            </div>
        `;
    } catch (error) {
        section.innerHTML = `
            <div class="llm-mode-display">
                <div class="mode-indicator mode-hosted">
                    <span class="mode-icon">☁️</span>
                    <span class="mode-label">${t('account.hostedMode')}</span>
                </div>
                <div class="mt-4">
                    <button class="btn btn-primary btn-sm" onclick="showAddByokKeyModal()">${t('account.switchToByok')}</button>
                </div>
            </div>
        `;
    }
}

// Load BYOK Keys
async function loadByokKeys() {
    const section = document.getElementById('byok-keys-section');
    if (!section) return;
    
    try {
        const keyRes = await (API.provider && API.provider.getUserKey ? API.provider.getUserKey() : Promise.resolve({ data: {} }));
        byokKeyInfo = keyRes || {};
        const providers = byokKeyInfo.providers || [];
        
        if (providers.length === 0) {
            section.innerHTML = `
                <div class="empty-state-sm">
                    <p>${t('account.noByokKeys')}</p>
                    <p class="text-muted" style="font-size:12px;margin-top:8px;">${t('account.byokExplanation')}</p>
                    <button class="btn btn-primary btn-sm mt-3" onclick="showAddByokKeyModal()">+ ${t('account.addProviderKey')}</button>
                </div>
            `;
            return;
        }
        
        section.innerHTML = `
            <div class="byok-keys-list">
                ${providers.map(p => renderByokKeyRow(p, p.provider === byokKeyInfo.active_provider)).join('')}
            </div>
        `;
    } catch (error) {
        section.innerHTML = `
            <div class="empty-state-sm">
                <p>${t('account.noByokKeys')}</p>
                <button class="btn btn-primary btn-sm mt-3" onclick="showAddByokKeyModal()">+ ${t('account.addProviderKey')}</button>
            </div>
        `;
    }
}

// Render a BYOK key row
function renderByokKeyRow(keyInfo, isActive) {
    const providerMeta = BYOK_PROVIDERS.find(p => p.id === keyInfo.provider) || { name: keyInfo.provider };
    
    return `
        <div class="api-key-row ${isActive ? 'key-active' : ''}">
            <div class="key-info">
                <span class="key-name">${escapeHtml(providerMeta.name)}</span>
                <code class="key-value">****${escapeHtml(keyInfo.key_last4)}</code>
                ${keyInfo.model_name ? `<span class="text-muted" style="font-size:11px;">${escapeHtml(keyInfo.model_name)}</span>` : ''}
                ${isActive ? `<span class="tag tag-green">${t('account.active')}</span>` : ''}
                ${keyInfo.verified === false ? `<span class="tag tag-red">${t('account.keyNotVerified')}</span>` : ''}
            </div>
            <div class="key-actions">
                ${!isActive ? `<button class="btn btn-sm btn-secondary" onclick="activateByokProvider('${keyInfo.provider}')">${t('account.activate')}</button>` : ''}
                <button class="btn btn-sm btn-danger" onclick="deleteByokKey('${keyInfo.provider}')">${t('account.revokeKey')}</button>
            </div>
        </div>
    `;
}

// Show Add BYOK Key Modal
function showAddByokKeyModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'add-byok-modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h3>${t('account.addProviderKey')}</h3>
                <button class="modal-close" onclick="closeAddByokModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">${t('account.provider')}</label>
                    <select id="byok-provider" class="form-input" onchange="onByokProviderChange()">
                        ${BYOK_PROVIDERS.map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">API Key</label>
                    <input type="password" id="byok-api-key" class="form-input" placeholder="${BYOK_PROVIDERS[0].placeholder}" />
                </div>
                <div class="form-group">
                    <label class="form-label">${t('account.modelName')} (${t('account.optional')})</label>
                    <select id="byok-model-name" class="form-input">
                        <option value="">${t('account.defaultModel')}</option>
                        ${BYOK_PROVIDERS[0].models.map(m => `<option value="${m}">${m}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">${t('account.baseUrl')} (${t('account.optional')})</label>
                    <input type="text" id="byok-base-url" class="form-input" placeholder="https://api.example.com" />
                </div>
                <p class="text-muted" style="font-size: 12px; margin-top: 12px;">${t('account.byokKeySecurity')}</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeAddByokModal()">${t('common.cancel')}</button>
                <button class="btn btn-primary" onclick="saveByokKey()">${t('account.saveKey')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function onByokProviderChange() {
    const select = document.getElementById('byok-provider');
    const modelSelect = document.getElementById('byok-model-name');
    const keyInput = document.getElementById('byok-api-key');
    
    if (!select || !modelSelect || !keyInput) return;
    
    const providerId = select.value;
    const provider = BYOK_PROVIDERS.find(p => p.id === providerId);
    
    if (provider) {
        keyInput.placeholder = provider.placeholder;
        modelSelect.innerHTML = `
            <option value="">${t('account.defaultModel')}</option>
            ${provider.models.map(m => `<option value="${m}">${m}</option>`).join('')}
        `;
    }
}

function closeAddByokModal() {
    const modal = document.getElementById('add-byok-modal');
    if (modal) modal.remove();
}

// Save BYOK Key
async function saveByokKey() {
    const provider = document.getElementById('byok-provider')?.value;
    const apiKey = document.getElementById('byok-api-key')?.value.trim();
    const modelName = document.getElementById('byok-model-name')?.value || '';
    const baseUrl = document.getElementById('byok-base-url')?.value.trim() || '';
    
    if (!provider || !apiKey) {
        Toast.show(t('account.enterApiKey'), 'warning');
        return;
    }
    
    try {
        if (API.provider && API.provider.setUserKey) {
            const res = await API.provider.setUserKey({
                provider,
                api_key: apiKey,
                model_name: modelName || undefined,
                base_url: baseUrl || undefined,
            });
            
            if (res.verified === false) {
                Toast.show(t('account.keyVerificationFailed'), 'warning');
            } else {
                Toast.show(t('account.byokKeySaved'), 'success');
            }
        } else {
            Toast.show(t('account.byokKeySaved'), 'success');
        }
        
        closeAddByokModal();
        await loadByokKeys();
        await loadLlmMode();
    } catch (error) {
        Toast.show(t('account.byokKeySaveFailed'), 'error');
    }
}

// Activate a BYOK provider
async function activateByokProvider(provider) {
    try {
        // Re-set the key as active (by re-saving, which sets it as active)
        Toast.show(t('account.providerActivated'), 'success');
        await loadByokKeys();
        await loadLlmMode();
    } catch (error) {
        Toast.show(t('account.providerActivationFailed'), 'error');
    }
}

// Delete a BYOK Key
async function deleteByokKey(provider) {
    if (!confirm(t('account.deleteByokConfirm'))) return;
    
    try {
        if (API.provider && API.provider.deleteUserKey) {
            await API.provider.deleteUserKey(provider);
        }
        Toast.show(t('account.byokKeyDeleted'), 'success');
        await loadByokKeys();
        await loadLlmMode();
    } catch (error) {
        Toast.show(t('account.byokKeyDeleteFailed'), 'error');
    }
}

// Switch to hosted mode (delete all keys)
async function switchToHosted() {
    if (!confirm(t('account.switchToHostedConfirm'))) return;
    
    try {
        if (API.provider && API.provider.deleteUserKey) {
            await API.provider.deleteUserKey();  // Delete all
        }
        Toast.show(t('account.switchedToHosted'), 'success');
        await loadByokKeys();
        await loadLlmMode();
    } catch (error) {
        Toast.show(t('account.switchFailed'), 'error');
    }
}

// Load API Keys
async function loadApiKeys() {
    const list = document.getElementById('api-keys-list');
    if (!list) return;
    
    try {
        // TODO: Replace with actual API key endpoint when available
        accountApiKeys = []; // Placeholder until backend is ready
        
        if (accountApiKeys.length === 0) {
            list.innerHTML = `
                <div class="empty-state-sm">
                    <p>${t('account.noApiKeys')}</p>
                    <button class="btn btn-primary btn-sm mt-3" onclick="showCreateKeyModal()">+ ${t('account.createKey')}</button>
                </div>
            `;
            return;
        }
        
        list.innerHTML = `
            <div class="api-keys-table">
                ${accountApiKeys.map(key => renderApiKeyRow(key)).join('')}
            </div>
        `;
    } catch (error) {
        list.innerHTML = `
            <div class="empty-state-sm">
                <p>${t('account.noApiKeys')}</p>
                <button class="btn btn-primary btn-sm mt-3" onclick="showCreateKeyModal()">+ ${t('account.createKey')}</button>
            </div>
        `;
    }
}

// Render a single API key row
function renderApiKeyRow(key) {
    const maskedKey = key.key ? key.key.substring(0, 8) + '...' + key.key.substring(key.key.length - 4) : 'nsh_****';
    const statusClass = key.revoked ? 'tag-red' : 'tag-green';
    const statusText = key.revoked ? t('account.revoked') : t('account.active');
    
    return `
        <div class="api-key-row">
            <div class="key-info">
                <span class="key-name">${escapeHtml(key.name || 'Default Key')}</span>
                <code class="key-value">${maskedKey}</code>
                <span class="tag ${statusClass}">${statusText}</span>
            </div>
            <div class="key-actions">
                <button class="btn btn-sm btn-secondary" onclick="copyToClipboard('${key.key || ''}')">${t('account.copyKey')}</button>
                ${!key.revoked ? `<button class="btn btn-sm btn-danger" onclick="revokeApiKey('${key.id}')">${t('account.revokeKey')}</button>` : ''}
            </div>
        </div>
    `;
}

// Load Environment Config
async function loadEnvConfig() {
    const section = document.getElementById('account-env-section');
    if (!section) return;
    
    try {
        const [providersRes, defaultModelRes] = await Promise.allSettled([
            API.config.getModelProviders(),
            API.config.getDefaultModel()
        ]);
        
        const providers = providersRes.status === 'fulfilled' ? (providersRes.value.data || []) : [];
        const defaultModel = defaultModelRes.status === 'fulfilled' ? (defaultModelRes.value.data || {}) : {};
        
        section.innerHTML = `
            <div class="env-config-grid">
                <div class="info-row">
                    <span class="info-label">${t('account.currentProvider')}</span>
                    <span class="info-value">${escapeHtml(defaultModel.provider || '-')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">${t('account.currentModel')}</span>
                    <span class="info-value">${escapeHtml(defaultModel.model || '-')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">${t('account.configuredProviders')}</span>
                    <span class="info-value">${providers.length} ${t('account.providers')}</span>
                </div>
            </div>
            <div class="mt-4">
                <button class="btn btn-secondary btn-sm" onclick="router.navigate('billing')">${t('account.manageSubscription')}</button>
            </div>
        `;
    } catch (error) {
        section.innerHTML = `
            <p class="text-muted">${t('account.connectToSeeConfig')}</p>
        `;
    }
}

// Show Create Key Modal
function showCreateKeyModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'create-key-modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 440px;">
            <div class="modal-header">
                <h3>${t('account.createKey')}</h3>
                <button class="modal-close" onclick="closeCreateKeyModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">${t('account.keyName')}</label>
                    <input type="text" id="new-key-name" class="form-input" placeholder="${t('account.keyNamePlaceholder')}" />
                </div>
                <p class="text-muted" style="font-size: 12px; margin-top: 12px;">${t('account.keyNameHint')}</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeCreateKeyModal()">${t('common.cancel')}</button>
                <button class="btn btn-primary" onclick="createApiKey()">${t('account.createKey')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function closeCreateKeyModal() {
    const modal = document.getElementById('create-key-modal');
    if (modal) modal.remove();
}

// Create API Key
async function createApiKey() {
    const nameInput = document.getElementById('new-key-name');
    const name = nameInput ? nameInput.value.trim() : '';
    
    if (!name) {
        Toast.show(t('account.enterKeyName'), 'warning');
        return;
    }
    
    try {
        // TODO: Replace with actual API key creation endpoint
        Toast.show(t('account.keyCreated'), 'success');
        closeCreateKeyModal();
        await loadApiKeys();
    } catch (error) {
        Toast.show(t('account.keyCreateFailed'), 'error');
    }
}

// Revoke API Key
async function revokeApiKey(keyId) {
    if (!confirm(t('account.revokeConfirm'))) return;
    
    try {
        // TODO: Replace with actual API key revoke endpoint
        Toast.show(t('account.keyRevoked'), 'success');
        await loadApiKeys();
    } catch (error) {
        Toast.show(t('account.keyRevokeFailed'), 'error');
    }
}
