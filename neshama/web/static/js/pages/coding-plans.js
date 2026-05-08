/**
 * Coding Plans Page - 2026 新增
 * 编码套餐管理 - 管理编程套餐和使用限制
 */

let codingPlansData = {
    plans: [],
    stats: {},
    selectedPlan: null
};

// Render Coding Plans Page
async function renderCodingPlans() {
    const container = document.getElementById('page-coding-plans');
    
    try {
        const res = await API.codingPlans.getAll();
        codingPlansData.plans = res.data.plans;
        codingPlansData.stats = {
            total: res.data.total,
            enabled: res.data.enabled_count,
            configured: res.data.configured_count
        };
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('codingPlans.title')}</h1>
                <p class="page-subtitle">${t('codingPlans.subtitle')}</p>
            </div>
            
            <!-- Stats Bar -->
            <div class="grid-3 mb-4">
                <div class="stat-card">
                    <div class="stat-icon" style="color:#7c5cff;">Plan</div>
                    <div class="stat-content">
                        <div class="stat-value">${codingPlansData.stats.total}</div>
                        <div class="stat-label">${t('codingPlans.totalPlans')}</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="color:#00d4aa;">Active</div>
                    <div class="stat-content">
                        <div class="stat-value">${codingPlansData.stats.enabled}</div>
                        <div class="stat-label">${t('codingPlans.activePlans')}</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="color:#7c5cff;">Key</div>
                    <div class="stat-content">
                        <div class="stat-value">${codingPlansData.stats.configured}</div>
                        <div class="stat-label">${t('codingPlans.configuredPlans')}</div>
                    </div>
                </div>
            </div>
            
            <!-- Add Plan Button -->
            <div class="flex gap-3 mb-4">
                <button class="btn btn-primary" onclick="openAddPlanModal()">
                    ${t('codingPlans.addPlan')}
                </button>
            </div>
            
            <!-- Plans List -->
            <div id="plans-list" class="plans-grid">
                ${renderPlansList()}
            </div>
            
            <!-- Add/Edit Plan Modal -->
            <div id="plan-modal" class="modal hidden">
                <div class="modal-backdrop" onclick="closePlanModal()"></div>
                <div class="modal-content modal-lg">
                    <div class="modal-header">
                        <span class="modal-title" id="plan-modal-title">${t('codingPlans.addPlan')}</span>
                        <button class="modal-close" onclick="closePlanModal()">×</button>
                    </div>
                    <div id="plan-form-container" class="modal-body"></div>
                </div>
            </div>
            
            <!-- Plan Details Modal -->
            <div id="detail-modal" class="modal hidden">
                <div class="modal-backdrop" onclick="closeDetailModal()"></div>
                <div class="modal-content modal-lg">
                    <div class="modal-header">
                        <span class="modal-title" id="detail-modal-title">${t('codingPlans.planDetails')}</span>
                        <button class="modal-close" onclick="closeDetailModal()">×</button>
                    </div>
                    <div id="detail-content" class="modal-body"></div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Coding plans load error:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">Plan</div>
                <div class="empty-state-text">${t('codingPlans.failedLoad')}</div>
                <div class="text-muted mt-2" style="font-size: 12px;">${error.message || ''}</div>
                <button class="btn btn-primary mt-4" onclick="renderCodingPlans()">${t('common.retry')}</button>
            </div>
        `;
        Toast.show(t('common.error'), 'error');
    }
}

// Render Plans List
function renderPlansList() {
    if (codingPlansData.plans.length === 0) {
        return `
            <div class="empty-state">
                <div class="empty-state-icon" style="font-size:24px;color:#7c5cff;">Plan</div>
                <div class="empty-state-text">${t('codingPlans.noPlans')}</div>
                <button class="btn btn-primary mt-4" onclick="openAddPlanModal()">
                    ${t('codingPlans.createFirst')}
                </button>
            </div>
        `;
    }
    
    return codingPlansData.plans.map(plan => renderPlanCard(plan)).join('');
}

// Render Plan Card
function renderPlanCard(plan) {
    const statusClass = plan.enabled ? 'enabled' : 'disabled';
    const configClass = plan.configured ? 'configured' : 'not-configured';
    
    return `
        <div class="plan-card ${statusClass}">
            <div class="plan-header">
                <div class="plan-info">
                    <h3 class="plan-name">${plan.plan_name}</h3>
                    <span class="provider-badge">${getProviderEmoji(plan.provider_name)} ${plan.provider_name}</span>
                </div>
                <div class="plan-toggle">
                    <label class="toggle-switch">
                        <input type="checkbox" ${plan.enabled ? 'checked' : ''} 
                            onchange="togglePlan('${plan.plan_id}')">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            </div>
            
            <div class="plan-models">
                <div class="form-label">${t('codingPlans.models')}</div>
                <div class="model-tags">
                    ${plan.models.map(m => `
                        <span class="model-tag">${m.name}</span>
                    `).join('')}
                </div>
            </div>
            
            ${plan.restrictions.restriction_list.length > 0 ? `
                <div class="plan-restrictions">
                    <div class="form-label">${t('codingPlans.restrictions')}</div>
                    <div class="restriction-tags">
                        ${plan.restrictions.restriction_list.map(r => `
                            <span class="restriction-tag warning">${getRestrictionLabel(r)}</span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="plan-rate-limits">
                <div class="rate-limit-item">
                    <span class="rate-icon" style="color:#7c5cff;">RPM</span>
                    <span>${plan.rate_limits.rpm} RPM</span>
                </div>
                <div class="rate-limit-item">
                    <span class="rate-icon" style="color:#ff6b35;">Day</span>
                    <span>${plan.rate_limits.rpd} RPD</span>
                </div>
            </div>
            
            <div class="plan-status">
                <span class="status-badge ${configClass}">
                    ${plan.configured ? t('codingPlans.configured') : t('codingPlans.notConfigured')}
                </span>
                <span class="usage-badge">
                    ${plan.session_stats.request_count} ${t('codingPlans.requests')}
                </span>
            </div>
            
            <div class="plan-actions">
                <button class="btn btn-sm btn-secondary" onclick="viewPlanDetails('${plan.plan_id}')">
                    ${t('codingPlans.viewDetails')}
                </button>
                <button class="btn btn-sm btn-secondary" onclick="editPlan('${plan.plan_id}')">
                    ${t('common.edit')}
                </button>
                <button class="btn btn-sm btn-secondary" onclick="testPlanConnection('${plan.plan_id}')">
                    ${t('codingPlans.testConnection')}
                </button>
                <button class="btn btn-sm btn-danger" onclick="deletePlan('${plan.plan_id}')">
                    ${t('common.delete')}
                </button>
            </div>
        </div>
    `;
}

// Get Provider Emoji
function getProviderEmoji(provider) {
    const emojis = {
        'zhipu': 'Zhipu',
        'dashscope': 'Dashscope',
        'minimax': 'MiniMax',
        'openai': 'OpenAI',
        'anthropic': 'Anthropic',
        'deepseek': 'DeepSeek',
    };
    return emojis[provider] || 'Model';
}

// Get Restriction Label
function getRestrictionLabel(restriction) {
    const labels = {
        'interactive_coding_only': t('codingPlans.restrictionInteractive'),
        'no_backend': t('codingPlans.restrictionNoBackend'),
        'no_automation': t('codingPlans.restrictionNoAutomation'),
        'no_curl': t('codingPlans.restrictionNoCurl'),
    };
    return labels[restriction] || restriction;
}

// Toggle Plan
async function togglePlan(planId) {
    try {
        await API.codingPlans.toggle(planId);
        showToast(t('codingPlans.planToggled'), 'success');
        renderCodingPlans();
    } catch (error) {
        showToast(t('codingPlans.toggleFailed'), 'error');
    }
}

// Open Add Plan Modal
function openAddPlanModal() {
    codingPlansData.selectedPlan = null;
    
    const modal = document.getElementById('plan-modal');
    const title = document.getElementById('plan-modal-title');
    const formContainer = document.getElementById('plan-form-container');
    
    title.textContent = t('codingPlans.addPlan');
    
    formContainer.innerHTML = `
        <form id="add-plan-form" onsubmit="submitPlanForm(event)">
            <div class="grid-2">
                <div class="form-group">
                    <label class="form-label">${t('codingPlans.planName')}</label>
                    <input type="text" id="plan-name" class="form-input" required
                        placeholder="${t('codingPlans.planNamePlaceholder')}">
                </div>
                <div class="form-group">
                    <label class="form-label">${t('codingPlans.provider')}</label>
                    <select id="plan-provider" class="form-input" required>
                        <option value="">${t('codingPlans.selectProvider')}</option>
                        <option value="zhipu">智谱 GLM</option>
                        <option value="dashscope">阿里云百炼</option>
                        <option value="minimax">MiniMax</option>
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                    </select>
                </div>
            </div>
            
            <div class="form-group">
                <label class="form-label">${t('codingPlans.apiKey')}</label>
                <input type="password" id="plan-api-key" class="form-input" required
                    placeholder="sk-...">
            </div>
            
            <div class="form-group">
                <label class="form-label">${t('codingPlans.baseURL')} (${t('codingPlans.optional')})</label>
                <input type="text" id="plan-base-url" class="form-input"
                    placeholder="https://api.example.com/v1">
            </div>
            
            <div class="form-group">
                <label class="form-label">${t('codingPlans.apiStyle')}</label>
                <select id="plan-api-style" class="form-input">
                    <option value="openai_chat">OpenAI Chat</option>
                    <option value="openai_responses">OpenAI Responses</option>
                    <option value="anthropic">Anthropic</option>
                </select>
            </div>
            
            <div class="form-group">
                <label class="form-label">${t('codingPlans.models')}</label>
                <div class="model-checkboxes">
                    <label class="checkbox-item">
                        <input type="checkbox" name="models" value="glm-4.7">
                        <span>GLM-4.7</span>
                    </label>
                    <label class="checkbox-item">
                        <input type="checkbox" name="models" value="glm-4-plus">
                        <span>GLM-4 Plus</span>
                    </label>
                    <label class="checkbox-item">
                        <input type="checkbox" name="models" value="qwq-32b">
                        <span>QwQ-32B</span>
                    </label>
                    <label class="checkbox-item">
                        <input type="checkbox" name="models" value="qwen-plus">
                        <span>通义千问 Plus</span>
                    </label>
                    <label class="checkbox-item">
                        <input type="checkbox" name="models" value="codestral">
                        <span>Codestral</span>
                    </label>
                </div>
            </div>
            
            <div class="form-group">
                <label class="form-label">${t('codingPlans.restrictions')}</label>
                <div class="restriction-checkboxes">
                    <label class="checkbox-item">
                        <input type="checkbox" name="restrictions" value="interactive_coding_only">
                        <span>${t('codingPlans.restrictionInteractive')}</span>
                    </label>
                    <label class="checkbox-item">
                        <input type="checkbox" name="restrictions" value="no_backend">
                        <span>${t('codingPlans.restrictionNoBackend')}</span>
                    </label>
                    <label class="checkbox-item">
                        <input type="checkbox" name="restrictions" value="no_automation">
                        <span>${t('codingPlans.restrictionNoAutomation')}</span>
                    </label>
                </div>
            </div>
            
            <div class="flex gap-3 mt-4">
                <button type="button" class="btn btn-secondary" onclick="closePlanModal()">
                    ${t('common.cancel')}
                </button>
                <button type="submit" class="btn btn-primary" style="margin-left: auto;">
                    ${t('common.save')}
                </button>
            </div>
        </form>
    `;
    
    modal.classList.remove('hidden');
}

// Edit Plan
function editPlan(planId) {
    const plan = codingPlansData.plans.find(p => p.plan_id === planId);
    if (!plan) return;
    
    codingPlansData.selectedPlan = plan;
    
    const modal = document.getElementById('plan-modal');
    const title = document.getElementById('plan-modal-title');
    const formContainer = document.getElementById('plan-form-container');
    
    title.textContent = t('codingPlans.editPlan');
    
    formContainer.innerHTML = `
        <form id="edit-plan-form" onsubmit="submitPlanForm(event)">
            <input type="hidden" id="edit-plan-id" value="${plan.plan_id}">
            
            <div class="grid-2">
                <div class="form-group">
                    <label class="form-label">${t('codingPlans.planName')}</label>
                    <input type="text" id="plan-name" class="form-input" required value="${plan.plan_name}">
                </div>
                <div class="form-group">
                    <label class="form-label">${t('codingPlans.provider')}</label>
                    <input type="text" class="form-input" value="${getProviderEmoji(plan.provider_name)} ${plan.provider_name}" disabled>
                    <input type="hidden" id="plan-provider" value="${plan.provider_name}">
                </div>
            </div>
            
            <div class="form-group">
                <label class="form-label">${t('codingPlans.newApiKey')} (${t('codingPlans.leaveBlank')})</label>
                <input type="password" id="plan-api-key" class="form-input" placeholder="••••••••">
            </div>
            
            <div class="form-group">
                <label class="form-label">${t('codingPlans.apiStyle')}</label>
                <select id="plan-api-style" class="form-input">
                    <option value="openai_chat" ${plan.api_style === 'openai_chat' ? 'selected' : ''}>OpenAI Chat</option>
                    <option value="openai_responses" ${plan.api_style === 'openai_responses' ? 'selected' : ''}>OpenAI Responses</option>
                    <option value="anthropic" ${plan.api_style === 'anthropic' ? 'selected' : ''}>Anthropic</option>
                </select>
            </div>
            
            <div class="form-group">
                <label class="form-label">${t('codingPlans.enabled')}</label>
                <label class="toggle-switch">
                    <input type="checkbox" id="plan-enabled" ${plan.enabled ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            <div class="flex gap-3 mt-4">
                <button type="button" class="btn btn-secondary" onclick="closePlanModal()">
                    ${t('common.cancel')}
                </button>
                <button type="submit" class="btn btn-primary" style="margin-left: auto;">
                    ${t('common.save')}
                </button>
            </div>
        </form>
    `;
    
    modal.classList.remove('hidden');
}

// Submit Plan Form
async function submitPlanForm(event) {
    event.preventDefault();
    
    const isEdit = codingPlansData.selectedPlan !== null;
    const planId = isEdit ? codingPlansData.selectedPlan.plan_id : null;
    
    // Collect form data
    const formData = {
        plan_name: document.getElementById('plan-name').value,
        provider_name: document.getElementById('plan-provider').value,
        api_key: document.getElementById('plan-api-key').value,
        base_url: document.getElementById('plan-base-url')?.value || null,
        api_style: document.getElementById('plan-api-style').value,
        enabled: document.getElementById('plan-enabled')?.checked ?? true,
    };
    
    // Collect selected models
    const modelCheckboxes = document.querySelectorAll('input[name="models"]:checked');
    formData.models = Array.from(modelCheckboxes).map(cb => cb.value);
    
    if (formData.models.length === 0) {
        showToast(t('codingPlans.selectModels'), 'warning');
        return;
    }
    
    try {
        if (isEdit) {
            await API.codingPlans.update(planId, formData);
            showToast(t('codingPlans.planUpdated'), 'success');
        } else {
            await API.codingPlans.create(formData);
            showToast(t('codingPlans.planCreated'), 'success');
        }
        closePlanModal();
        renderCodingPlans();
    } catch (error) {
        showToast(isEdit ? t('codingPlans.updateFailed') : t('codingPlans.createFailed'), 'error');
    }
}

// Close Plan Modal
function closePlanModal() {
    document.getElementById('plan-modal').classList.add('hidden');
    codingPlansData.selectedPlan = null;
}

// View Plan Details
async function viewPlanDetails(planId) {
    const plan = codingPlansData.plans.find(p => p.plan_id === planId);
    if (!plan) return;
    
    try {
        const statsRes = await API.codingPlans.getStats(planId);
        const stats = statsRes.data;
        
        const modal = document.getElementById('detail-modal');
        const title = document.getElementById('detail-modal-title');
        const content = document.getElementById('detail-content');
        
        title.textContent = plan.plan_name;
        
        content.innerHTML = `
            <div class="plan-details">
                <div class="detail-section">
                    <h4>${t('codingPlans.basicInfo')}</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">${t('codingPlans.provider')}</span>
                            <span class="detail-value">${getProviderEmoji(plan.provider_name)} ${plan.provider_name}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">${t('codingPlans.apiStyle')}</span>
                            <span class="detail-value">${plan.api_style}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">${t('codingPlans.status')}</span>
                            <span class="detail-value">${plan.enabled ? t('codingPlans.enabled') : t('codingPlans.disabled')}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">${t('codingPlans.configured')}</span>
                            <span class="detail-value">${plan.configured ? 'Yes' : 'No'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>${t('codingPlans.models')}</h4>
                    <div class="model-tags">
                        ${plan.models.map(m => `
                            <div class="model-detail-card">
                                <div class="model-name">${m.name}</div>
                                <div class="model-capabilities">
                                    ${m.capabilities.supports_function_call ? 'FC' : '--'}&nbsp;
                                    ${m.capabilities.supports_streaming ? 'Stream' : '--'}&nbsp;
                                    ${m.capabilities.supports_vision ? 'Vision' : '--'}&nbsp;
                                    ${m.capabilities.supports_reasoning ? 'Reason' : '--'}&nbsp;
                                    ${m.capabilities.context_size / 1000}K ctx
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>${t('codingPlans.restrictions')}</h4>
                    <div class="restriction-tags">
                        ${plan.restrictions.restriction_list.map(r => `
                            <span class="restriction-tag warning">${getRestrictionLabel(r)}</span>
                        `).join('') || '<span class="text-muted">' + t('codingPlans.noRestrictions') + '</span>'}
                    </div>
                    <div class="detail-grid mt-3">
                        <div class="detail-item">
                            <span class="detail-label">${t('codingPlans.maxSessionHours')}</span>
                            <span class="detail-value">${plan.restrictions.max_session_duration_hours}h</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">${t('codingPlans.maxRequestsPerSession')}</span>
                            <span class="detail-value">${plan.restrictions.max_requests_per_session}</span>
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>${t('codingPlans.usageStats')}</h4>
                    <div class="usage-chart">
                        <div class="usage-bar-container">
                            <div class="usage-bar-label">${t('codingPlans.dailyUsage')}</div>
                            <div class="usage-bar">
                                <div class="usage-bar-fill" style="width: ${(stats.used_today / stats.daily_limit) * 100}%"></div>
                            </div>
                            <div class="usage-bar-value">${stats.used_today} / ${stats.daily_limit}</div>
                        </div>
                    </div>
                    <div class="detail-grid mt-3">
                        <div class="detail-item">
                            <span class="detail-label">${t('codingPlans.totalRequests')}</span>
                            <span class="detail-value">${stats.request_count}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">${t('codingPlans.remainingToday')}</span>
                            <span class="detail-value">${stats.remaining_today}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">${t('codingPlans.rateLimits')}</span>
                            <span class="detail-value">${plan.rate_limits.rpm} RPM / ${plan.rate_limits.rpd} RPD</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        modal.classList.remove('hidden');
    } catch (error) {
        showToast(t('codingPlans.loadDetailsFailed'), 'error');
    }
}

// Close Detail Modal
function closeDetailModal() {
    document.getElementById('detail-modal').classList.add('hidden');
}

// Test Plan Connection
async function testPlanConnection(planId) {
    try {
        const res = await API.codingPlans.test(planId);
        if (res.success) {
            showToast(`${t('codingPlans.connectionSuccess')} (${res.latency_ms}ms)`, 'success');
        } else {
            showToast(t('codingPlans.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(t('codingPlans.connectionFailed'), 'error');
    }
}

// Delete Plan
async function deletePlan(planId) {
    if (!confirm(t('codingPlans.deleteConfirm'))) {
        return;
    }
    
    try {
        await API.codingPlans.delete(planId);
        showToast(t('codingPlans.planDeleted'), 'success');
        renderCodingPlans();
    } catch (error) {
        showToast(t('codingPlans.deleteFailed'), 'error');
    }
}
