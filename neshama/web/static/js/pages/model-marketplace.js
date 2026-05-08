/**
 * Model Marketplace Page - 2026 新增
 * 模型市场 - 浏览、搜索、对比模型
 */

let marketplaceData = {
    providers: [],
    stats: {},
    filters: {
        provider: null,
        taskType: null,
        freeOnly: false,
        maxPrice: null,
        query: ''
    },
    selectedModels: [],
    costEstimate: {
        inputTokens: 1000000,
        outputRatio: 0.5
    }
};

// Render Model Marketplace
async function renderModelMarketplace() {
    const container = document.getElementById('page-model-marketplace');
    
    try {
        const res = await API.marketplace.getProviders();
        marketplaceData.providers = res.data.providers;
        marketplaceData.stats = res.data.stats;
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('marketplace.title')}</h1>
                <p class="page-subtitle">${t('marketplace.subtitle')}</p>
            </div>
            
            <!-- Stats Bar -->
            <div class="grid-4 mb-4">
                <div class="stat-card">
                    <div class="stat-icon" style="color:#7c5cff;">Model</div>
                    <div class="stat-content">
                        <div class="stat-value">${marketplaceData.stats.total_providers}</div>
                        <div class="stat-label">${t('marketplace.providers')}</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="color:#00d4aa;">Online</div>
                    <div class="stat-content">
                        <div class="stat-value">${marketplaceData.stats.total_models}</div>
                        <div class="stat-label">${t('marketplace.models')}</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="color:#00d4aa;">OK</div>
                    <div class="stat-content">
                        <div class="stat-value">${marketplaceData.stats.free_models}</div>
                        <div class="stat-label">${t('marketplace.freeModels')}</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="color:#00d4aa;">Ready</div>
                    <div class="stat-content">
                        <div class="stat-value">${marketplaceData.stats.connected_providers}</div>
                        <div class="stat-label">${t('marketplace.connected')}</div>
                    </div>
                </div>
            </div>
            
            <!-- Search & Filters -->
            <div class="card mb-4">
                <div class="card-header">
                    <span class="card-title">${t('marketplace.searchFilters')}</span>
                    <button class="btn btn-sm btn-secondary" onclick="clearFilters()">${t('common.clear')}</button>
                </div>
                <div class="filters-grid">
                    <div class="filter-group">
                        <label class="form-label">${t('marketplace.search')}</label>
                        <input type="text" id="marketplace-search" class="form-input" 
                            placeholder="${t('marketplace.searchPlaceholder')}" 
                            value="${marketplaceData.filters.query}"
                            oninput="debounce(applyFilters, 300)()">
                    </div>
                    <div class="filter-group">
                        <label class="form-label">${t('marketplace.provider')}</label>
                        <select id="filter-provider" class="form-input" onchange="applyFilters()">
                            <option value="">${t('marketplace.allProviders')}</option>
                            ${marketplaceData.providers.map(p => `
                                <option value="${p.id}" ${marketplaceData.filters.provider === p.id ? 'selected' : ''}>
                                    ${p.emoji} ${p.name}
                                </option>
                            `).join('')}
                        </select>
                    </div>
                    <div class="filter-group">
                        <label class="form-label">${t('marketplace.taskType')}</label>
                        <select id="filter-task" class="form-input" onchange="applyFilters()">
                            <option value="">${t('marketplace.allTasks')}</option>
                            <option value="chat" ${marketplaceData.filters.taskType === 'chat' ? 'selected' : ''}>Chat ${t('marketplace.taskChat')}</option>
                            <option value="coding" ${marketplaceData.filters.taskType === 'coding' ? 'selected' : ''}>Code ${t('marketplace.taskCoding')}</option>
                            <option value="reasoning" ${marketplaceData.filters.taskType === 'reasoning' ? 'selected' : ''}>Reasoning ${t('marketplace.taskReasoning')}</option>
                            <option value="vision" ${marketplaceData.filters.taskType === 'vision' ? 'selected' : ''}>Vision ${t('marketplace.taskVision')}</option>
                            <option value="long_context" ${marketplaceData.filters.taskType === 'long_context' ? 'selected' : ''}>LongCtx ${t('marketplace.taskLongContext')}</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label class="form-label">${t('marketplace.priceRange')}</label>
                        <select id="filter-price" class="form-input" onchange="applyFilters()">
                            <option value="">${t('marketplace.allPrices')}</option>
                            <option value="0" ${marketplaceData.filters.maxPrice === 0 ? 'selected' : ''}>🆓 ${t('marketplace.freeOnly')}</option>
                            <option value="0.5" ${marketplaceFilters.maxPrice === 0.5 ? 'selected' : ''}>≤ $0.5/M</option>
                            <option value="2" ${marketplaceFilters.maxPrice === 2 ? 'selected' : ''}>≤ $2/M</option>
                            <option value="5" ${marketplaceFilters.maxPrice === 5 ? 'selected' : ''}>≤ $5/M</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <!-- Provider Cards -->
            <div id="provider-cards" class="provider-grid">
                ${renderProviderCards()}
            </div>
            
            <!-- Compare Panel (hidden by default) -->
            <div id="compare-panel" class="compare-panel hidden">
                <div class="compare-header">
                    <span class="card-title">${t('marketplace.compareModels')} (<span id="compare-count">0</span>/5)</span>
                    <div class="flex gap-2">
                        <button class="btn btn-sm btn-secondary" onclick="clearComparison()">${t('common.clear')}</button>
                        <button class="btn btn-sm btn-primary" onclick="showComparison()">${t('marketplace.viewCompare')}</button>
                    </div>
                </div>
                <div id="compare-items" class="compare-items"></div>
            </div>
            
            <!-- Cost Calculator -->
            <div class="card mt-4">
                <div class="card-header">
                    <span class="card-title">${t('marketplace.costCalculator')}</span>
                </div>
                <div class="cost-calculator">
                    <div class="cost-inputs">
                        <div class="form-group">
                            <label class="form-label">${t('marketplace.monthlyInputTokens')}</label>
                            <input type="number" id="calc-input-tokens" class="form-input" 
                                value="${marketplaceData.costEstimate.inputTokens}"
                                oninput="updateCostEstimate()">
                        </div>
                        <div class="form-group">
                            <label class="form-label">${t('marketplace.outputRatio')}: <span id="ratio-value">${marketplaceData.costEstimate.outputRatio * 100}%</span></label>
                            <input type="range" id="calc-output-ratio" class="form-input" 
                                min="0" max="1" step="0.1" value="${marketplaceData.costEstimate.outputRatio}"
                                oninput="document.getElementById('ratio-value').textContent = (this.value * 100) + '%'; marketplaceData.costEstimate.outputRatio = parseFloat(this.value); updateCostEstimate()">
                        </div>
                    </div>
                    <div class="cost-chart-container">
                        <canvas id="cost-chart" width="600" height="200"></canvas>
                    </div>
                    <div id="cost-recommendations" class="cost-recommendations"></div>
                </div>
            </div>
            
            <!-- Comparison Modal -->
            <div id="compare-modal" class="modal hidden">
                <div class="modal-backdrop" onclick="closeCompareModal()"></div>
                <div class="modal-content modal-lg">
                    <div class="modal-header">
                        <span class="modal-title">${t('marketplace.modelComparison')}</span>
                        <button class="modal-close" onclick="closeCompareModal()">×</button>
                    </div>
                    <div id="compare-table" class="modal-body"></div>
                </div>
            </div>
            
            <!-- Config Modal -->
            <div id="config-modal" class="modal hidden">
                <div class="modal-backdrop" onclick="closeConfigModal()"></div>
                <div class="modal-content">
                    <div class="modal-header">
                        <span class="modal-title">${t('marketplace.configureProvider')}</span>
                        <button class="modal-close" onclick="closeConfigModal()">×</button>
                    </div>
                    <div id="config-form" class="modal-body"></div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Model marketplace load error:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">Model</div>
                <div class="empty-state-text">${t('marketplace.failedLoad')}</div>
                <div class="text-muted mt-2" style="font-size: 12px;">${error.message || ''}</div>
                <button class="btn btn-primary mt-4" onclick="renderModelMarketplace()">${t('common.retry')}</button>
            </div>
        `;
        Toast.show(t('common.error'), 'error');
    }
}

// Render Provider Cards
function renderProviderCards() {
    const filteredProviders = getFilteredProviders();
    
    if (filteredProviders.length === 0) {
        return `<div class="empty-state"><div class="empty-state-text">${t('common.noData')}</div></div>`;
    }
    
    return filteredProviders.map(provider => `
        <div class="provider-card" style="--provider-color: ${provider.color}">
            <div class="provider-header">
                <div class="provider-info">
                    <span class="provider-emoji">${provider.emoji}</span>
                    <span class="provider-name">${provider.name}</span>
                    <span class="status-indicator ${provider.status}"></span>
                </div>
                <button class="btn btn-sm ${provider.status === 'connected' ? 'btn-secondary' : 'btn-primary'}" 
                    onclick="openConfigModal('${provider.id}', '${provider.name}')">
                    ${provider.status === 'connected' ? t('marketplace.configure') : t('marketplace.setup')}
                </button>
            </div>
            <div class="provider-models">
                ${provider.models.map(model => renderModelRow(provider, model)).join('')}
            </div>
        </div>
    `).join('');
}

// Render Model Row
function renderModelRow(provider, model) {
    const isSelected = marketplaceData.selectedModels.includes(model.id);
    const priceClass = getPriceClass(model.input_price);
    
    return `
        <div class="model-row ${isSelected ? 'selected' : ''}" data-model-id="${model.id}">
            <div class="model-checkbox">
                <input type="checkbox" ${isSelected ? 'checked' : ''} 
                    onchange="toggleModelSelection('${model.id}')"
                    ${marketplaceData.selectedModels.length >= 5 && !isSelected ? 'disabled' : ''}>
            </div>
            <div class="model-info">
                <div class="model-name">${model.name}</div>
                <div class="model-meta">
                    <span class="tag tag-sm">LongCtx ${formatContextWindow(model.context_window)}</span>
                    ${model.task_types.map(tt => `<span class="task-tag">${getTaskIcon(tt)}</span>`).join('')}
                </div>
            </div>
            <div class="model-pricing">
                ${model.is_free 
                    ? `<span class="price-free">🆓 ${t('marketplace.free')}</span>`
                    : `<span class="price-input ${priceClass}">$${model.input_price}/M</span>
                       <span class="price-output ${priceClass}">$${model.output_price}/M</span>`
                }
            </div>
        </div>
    `;
}

// Get Price Class
function getPriceClass(price) {
    if (price === 0) return 'price-free';
    if (price <= 0.3) return 'price-cheap';
    if (price <= 2) return 'price-medium';
    return 'price-expensive';
}

// Get Task Icon
function getTaskIcon(taskType) {
    const icons = {
        'chat': 'Chat',
        'coding': 'Code',
        'reasoning': 'Reason',
        'vision': 'Vision',
        'long_context': 'LongCtx'
    };
    return icons[taskType] || 'Model';
}

// Format Context Window
function formatContextWindow(tokens) {
    if (tokens >= 1000000) return (tokens / 1000000).toFixed(0) + 'M';
    if (tokens >= 1000) return (tokens / 1000) + 'K';
    return tokens;
}

// Get Filtered Providers
function getFilteredProviders() {
    let providers = marketplaceData.providers;
    
    // Apply search query
    if (marketplaceData.filters.query) {
        const q = marketplaceData.filters.query.toLowerCase();
        providers = providers.map(p => ({
            ...p,
            models: p.models.filter(m => 
                m.id.toLowerCase().includes(q) || 
                m.name.toLowerCase().includes(q) ||
                p.name.toLowerCase().includes(q)
            )
        })).filter(p => p.models.length > 0);
    }
    
    // Apply provider filter
    if (marketplaceData.filters.provider) {
        providers = providers.filter(p => p.id === marketplaceData.filters.provider);
    }
    
    // Apply task type filter
    if (marketplaceData.filters.taskType) {
        providers = providers.map(p => ({
            ...p,
            models: p.models.filter(m => m.task_types.includes(marketplaceData.filters.taskType))
        })).filter(p => p.models.length > 0);
    }
    
    // Apply price filter
    if (marketplaceData.filters.maxPrice !== null) {
        if (marketplaceData.filters.maxPrice === 0) {
            providers = providers.map(p => ({
                ...p,
                models: p.models.filter(m => m.is_free)
            })).filter(p => p.models.length > 0);
        } else {
            providers = providers.map(p => ({
                ...p,
                models: p.models.filter(m => !m.is_free && m.input_price <= marketplaceData.filters.maxPrice)
            })).filter(p => p.models.length > 0);
        }
    }
    
    return providers;
}

// Apply Filters
function applyFilters() {
    marketplaceData.filters = {
        query: document.getElementById('marketplace-search').value,
        provider: document.getElementById('filter-provider').value || null,
        taskType: document.getElementById('filter-task').value || null,
        maxPrice: document.getElementById('filter-price').value ? parseFloat(document.getElementById('filter-price').value) : null,
        freeOnly: document.getElementById('filter-price').value === '0'
    };
    
    document.getElementById('provider-cards').innerHTML = renderProviderCards();
}

// Clear Filters
function clearFilters() {
    marketplaceData.filters = {
        provider: null,
        taskType: null,
        freeOnly: false,
        maxPrice: null,
        query: ''
    };
    document.getElementById('marketplace-search').value = '';
    document.getElementById('filter-provider').value = '';
    document.getElementById('filter-task').value = '';
    document.getElementById('filter-price').value = '';
    document.getElementById('provider-cards').innerHTML = renderProviderCards();
}

// Toggle Model Selection
function toggleModelSelection(modelId) {
    const index = marketplaceData.selectedModels.indexOf(modelId);
    if (index > -1) {
        marketplaceData.selectedModels.splice(index, 1);
    } else if (marketplaceData.selectedModels.length < 5) {
        marketplaceData.selectedModels.push(modelId);
    }
    
    updateComparePanel();
    document.getElementById('provider-cards').innerHTML = renderProviderCards();
}

// Update Compare Panel
function updateComparePanel() {
    const panel = document.getElementById('compare-panel');
    const items = document.getElementById('compare-items');
    const count = document.getElementById('compare-count');
    
    if (marketplaceData.selectedModels.length === 0) {
        panel.classList.add('hidden');
        return;
    }
    
    panel.classList.remove('hidden');
    count.textContent = marketplaceData.selectedModels.length;
    
    // Get model info
    const models = [];
    marketplaceData.providers.forEach(p => {
        p.models.forEach(m => {
            if (marketplaceData.selectedModels.includes(m.id)) {
                models.push({...m, provider: p});
            }
        });
    });
    
    items.innerHTML = models.map(m => `
        <div class="compare-item" style="--provider-color: ${m.provider.color}">
            <span class="compare-model-name">${m.provider.emoji} ${m.name}</span>
            <button class="compare-remove" onclick="toggleModelSelection('${m.id}')">×</button>
        </div>
    `).join('');
}

// Show Comparison
async function showComparison() {
    if (marketplaceData.selectedModels.length < 2) {
        showToast(t('marketplace.needMoreModels'), 'warning');
        return;
    }
    
    try {
        const res = await API.marketplace.compare(marketplaceData.selectedModels);
        const models = res.data.models;
        
        const modal = document.getElementById('compare-modal');
        const table = document.getElementById('compare-table');
        
        table.innerHTML = `
            <table class="compare-table">
                <thead>
                    <tr>
                        <th>${t('marketplace.model')}</th>
                        <th>${t('marketplace.provider')}</th>
                        <th>${t('marketplace.inputPrice')}</th>
                        <th>${t('marketplace.outputPrice')}</th>
                        <th>${t('marketplace.context')}</th>
                        <th>${t('marketplace.tasks')}</th>
                        <th>${t('marketplace.status')}</th>
                    </tr>
                </thead>
                <tbody>
                    ${models.map(m => `
                        <tr>
                            <td><strong>${m.model_name}</strong></td>
                            <td><span style="color: ${m.provider_color}">${m.provider_emoji}</span> ${m.provider_name}</td>
                            <td class="${getPriceClass(m.input_price)}">$${m.input_price}/M</td>
                            <td class="${getPriceClass(m.output_price)}">$${m.output_price}/M</td>
                            <td>${formatContextWindow(m.context_window)}</td>
                            <td>${m.task_types.map(tt => getTaskIcon(tt)).join(' ')}</td>
                            <td><span class="status-badge ${m.status}">${m.status === 'connected' ? 'OK' : '--'}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        modal.classList.remove('hidden');
    } catch (error) {
        showToast(t('marketplace.compareFailed'), 'error');
    }
}

// Close Compare Modal
function closeCompareModal() {
    document.getElementById('compare-modal').classList.add('hidden');
}

// Clear Comparison
function clearComparison() {
    marketplaceData.selectedModels = [];
    updateComparePanel();
    document.getElementById('provider-cards').innerHTML = renderProviderCards();
}

// Update Cost Estimate
async function updateCostEstimate() {
    const inputTokens = parseInt(document.getElementById('calc-input-tokens').value) || 1000000;
    const outputRatio = marketplaceData.costEstimate.outputRatio;
    
    try {
        const res = await API.marketplace.estimateCost(inputTokens, outputRatio);
        const estimates = res.data.estimates.slice(0, 10); // Top 10
        const recommended = res.data.recommended;
        
        // Draw chart
        drawCostChart(estimates);
        
        // Show recommendations
        const recContainer = document.getElementById('cost-recommendations');
        recContainer.innerHTML = `
            <div class="recommendation-title">${t('marketplace.recommended')}</div>
            <div class="recommendation-cards">
                ${recommended.map((m, i) => `
                    <div class="recommendation-card rank-${i + 1}">
                        <div class="rank-badge">#${i + 1}</div>
                        <div class="rec-info">
                            <div class="rec-name">${m.provider_emoji} ${m.model_name}</div>
                            <div class="rec-price">$${m.estimated_monthly_cost}${t('marketplace.perMonth')}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Cost estimate failed:', error);
    }
}

// Draw Cost Chart
function drawCostChart(estimates) {
    const canvas = document.getElementById('cost-chart');
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    // Find max cost for scaling
    const maxCost = Math.max(...estimates.map(e => e.estimated_monthly_cost));
    const barWidth = Math.min(50, (width - 100) / estimates.length - 10);
    const chartHeight = height - 60;
    
    estimates.forEach((model, i) => {
        const x = 50 + i * (barWidth + 10);
        const barHeight = (model.estimated_monthly_cost / maxCost) * chartHeight;
        const y = chartHeight - barHeight + 20;
        
        // Color based on rank
        let color;
        if (i < 3) {
            color = '#00d4aa'; // Green for cheap
        } else if (model.estimated_monthly_cost < maxCost * 0.5) {
            color = '#ff6b35'; // Yellow for medium
        } else {
            color = '#ff6b35'; // Red for expensive
        }
        
        // Draw bar
        ctx.fillStyle = color;
        ctx.fillRect(x, y, barWidth, barHeight);
        
        // Draw label
        ctx.fillStyle = '#94A3B8';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        
        // Truncate name if needed
        let name = model.model_name;
        if (name.length > 8) name = name.slice(0, 6) + '..';
        ctx.fillText(name, x + barWidth / 2, height - 10);
        
        // Draw value
        ctx.fillStyle = '#F8FAFC';
        ctx.fillText('$' + model.estimated_monthly_cost.toFixed(0), x + barWidth / 2, y - 5);
    });
}

// Open Config Modal
function openConfigModal(providerId, providerName) {
    const modal = document.getElementById('config-modal');
    const form = document.getElementById('config-form');
    
    form.innerHTML = `
        <div class="form-group">
            <label class="form-label">${t('marketplace.provider')}</label>
            <input type="text" class="form-input" value="${providerName}" disabled>
        </div>
        <div class="form-group">
            <label class="form-label">${t('marketplace.apiKey')}</label>
            <input type="password" id="config-api-key" class="form-input" placeholder="sk-...">
        </div>
        <div class="form-group">
            <label class="form-label">${t('marketplace.baseURL')} (${t('marketplace.optional')})</label>
            <input type="text" id="config-base-url" class="form-input" placeholder="https://api.example.com/v1">
        </div>
        <div class="flex gap-3 mt-4">
            <button class="btn btn-secondary" onclick="testProviderConnection('${providerId}')">${t('marketplace.testConnection')}</button>
            <button class="btn btn-primary" onclick="saveProviderConfig('${providerId}')" style="margin-left: auto;">${t('common.save')}</button>
        </div>
    `;
    
    modal.classList.remove('hidden');
}

// Close Config Modal
function closeConfigModal() {
    document.getElementById('config-modal').classList.add('hidden');
}

// Test Provider Connection
async function testProviderConnection(providerId) {
    const apiKey = document.getElementById('config-api-key').value;
    const baseUrl = document.getElementById('config-base-url').value;
    
    if (!apiKey) {
        showToast(t('marketplace.enterApiKey'), 'warning');
        return;
    }
    
    try {
        const res = await API.marketplace.test({provider_id: providerId, api_key: apiKey, base_url: baseUrl});
        if (res.success) {
            showToast(`${t('marketplace.connectionSuccess')} (${res.latency_ms}ms)`, 'success');
        } else {
            showToast(t('marketplace.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(t('marketplace.connectionFailed'), 'error');
    }
}

// Save Provider Config
async function saveProviderConfig(providerId) {
    const apiKey = document.getElementById('config-api-key').value;
    const baseUrl = document.getElementById('config-base-url').value;
    
    if (!apiKey) {
        showToast(t('marketplace.enterApiKey'), 'warning');
        return;
    }
    
    try {
        await API.marketplace.configure({provider_id: providerId, api_key: apiKey, base_url: baseUrl});
        showToast(t('marketplace.configSaved'), 'success');
        closeConfigModal();
        renderModelMarketplace(); // Refresh
    } catch (error) {
        showToast(t('marketplace.configFailed'), 'error');
    }
}
