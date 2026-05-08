/**
 * Billing Page - Subscription plans, usage dashboard, refund, BYOK management
 */

// Billing State
let billingPlans = [];
let currentSubscription = null;
let billingUsage = {};
let userKeyInfo = null;

// Subscription tier details (dual-track: hosted + BYOK)
const TIER_DETAILS = {
    free: {
        name: 'Free',
        price: 0,
        emoji: '🆓',
        color: '#94a3b8',
        limits: { npcs: 3, interactions: 1000, tts_chars: 0, api_calls: 5000 },
        hosted_conversations: 1000,
        byok_enabled: true,
        byok_highlight: true,  // Highlight "BYOK unlimited" as selling point
        features: ['emotion_engine', 'memory_system', 'behavior_mapping', 'sentiment_analysis']
    },
    indie: {
        name: 'Indie',
        price: 19,
        emoji: 'Game',
        color: '#00d4aa',
        limits: { npcs: 10, interactions: 50000, tts_chars: 50000, api_calls: 100000 },
        hosted_conversations: 10000,
        byok_enabled: true,
        byok_highlight: false,
        features: ['emotion_engine', 'memory_system', 'behavior_mapping', 'sentiment_analysis', 'npc2npc_social', 'plot_trigger', 'relation_graph']
    },
    studio: {
        name: 'Studio',
        price: 79,
        emoji: 'Pro',
        color: '#7c5cff',
        limits: { npcs: 50, interactions: 500000, tts_chars: 500000, api_calls: 1000000 },
        hosted_conversations: 100000,
        byok_enabled: true,
        byok_highlight: false,
        features: ['emotion_engine', 'memory_system', 'behavior_mapping', 'sentiment_analysis', 'npc2npc_social', 'plot_trigger', 'relation_graph', 'tts_stt', 'sentiment_enhanced', 'template_market', 'team_collaboration', 'soul_export']
    },
    enterprise: {
        name: 'Enterprise',
        price: 299,
        emoji: 'Enterprise',
        color: '#7c5cff',
        limits: { npcs: -1, interactions: -1, tts_chars: -1, api_calls: -1 },
        hosted_conversations: -1,
        byok_enabled: true,
        byok_highlight: false,
        features: ['emotion_engine', 'memory_system', 'behavior_mapping', 'sentiment_analysis', 'npc2npc_social', 'plot_trigger', 'relation_graph', 'tts_stt', 'sentiment_enhanced', 'template_market', 'team_collaboration', 'soul_export', 'private_deploy', 'sla_guarantee']
    }
};

// Render Billing Page
async function renderBilling() {
    const container = document.getElementById('page-billing');
    
    // Show loading
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">${t('billing.title')}</h1>
            <p class="page-subtitle">${t('billing.subtitle')}</p>
        </div>
        <div class="loading">${t('common.loading')}</div>
    `;
    
    // Load data in parallel
    const [plansRes, usageRes, subRes, keyRes] = await Promise.allSettled([
        API.billing ? API.billing.getPlans() : Promise.reject('no billing module'),
        API.billing ? API.billing.getUsage() : Promise.reject('no billing module'),
        API.billing ? API.billing.getSubscription() : Promise.reject('no billing module'),
        API.provider ? API.provider.getUserKey() : Promise.reject('no provider module')
    ]);
    
    billingPlans = plansRes.status === 'fulfilled' ? (plansRes.value.data?.plans || []) : Object.values(TIER_DETAILS);
    billingUsage = usageRes.status === 'fulfilled' ? (usageRes.value.data || {}) : {};
    currentSubscription = subRes.status === 'fulfilled' ? (subRes.value.data || null) : null;
    userKeyInfo = keyRes.status === 'fulfilled' ? (keyRes.value || {}) : {};
    
    // Determine current tier
    const currentTier = billingUsage.tier || currentSubscription?.tier || 'free';
    const currentMode = userKeyInfo.mode || 'hosted';
    
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">${t('billing.title')}</h1>
            <p class="page-subtitle">${t('billing.subtitle')}</p>
        </div>
        
        <!-- Current Subscription Status -->
        <div class="card subscription-status-card">
            <div class="card-header">
                <span class="card-title">${t('billing.currentPlan')}</span>
                <span class="tag ${currentMode === 'byok' ? 'tag-green' : 'tag-blue'}" style="margin-left:8px;">
                    ${currentMode === 'byok' ? 'BYOK' : t('billing.hostedMode')}
                </span>
            </div>
            <div class="subscription-info">
                <div class="tier-badge" style="border-color: ${TIER_DETAILS[currentTier]?.color || '#94a3b8'}">
                    <span class="tier-emoji">${TIER_DETAILS[currentTier]?.emoji || '🆓'}</span>
                    <span class="tier-name">${TIER_DETAILS[currentTier]?.name || currentTier}</span>
                </div>
                ${currentSubscription?.current_period_end ? `
                    <div class="renewal-info">
                        <span class="text-muted">${t('billing.renewsOn')}</span>
                        <span>${formatDate(currentSubscription.current_period_end)}</span>
                    </div>
                ` : ''}
                <div class="subscription-actions">
                    ${currentTier !== 'enterprise' ? `<button class="btn btn-primary btn-sm" onclick="showUpgradeModal()">${t('billing.upgrade')}</button>` : ''}
                    ${currentTier !== 'free' && currentTier !== 'enterprise' ? `<button class="btn btn-secondary btn-sm" onclick="showManageModal()">${t('billing.managePlan')}</button>` : ''}
                    <button class="btn btn-secondary btn-sm" onclick="router.navigate('account')">${t('billing.manageApiKey')}</button>
                </div>
            </div>
        </div>
        
        <!-- Plans -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">${t('billing.plans')}</span>
                <span class="tag tag-amber" style="margin-left:8px;">${t('billing.dualTrack')}</span>
            </div>
            <div class="plans-grid">
                ${renderPlanCards(currentTier)}
            </div>
        </div>
        
        <!-- Usage Dashboard -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">${t('billing.usageDashboard')}</span>
                <span class="tag tag-amber">${t('billing.thisMonth')}</span>
            </div>
            <div class="usage-grid">
                ${renderUsageMetrics(currentTier, currentMode)}
            </div>
        </div>
        
        <!-- Refund -->
        ${currentTier !== 'free' ? `
        <div class="card">
            <div class="card-header">
                <span class="card-title">${t('billing.refund')}</span>
            </div>
            <div class="refund-section">
                <p class="text-muted">${t('billing.refundDesc')}</p>
                <button class="btn btn-secondary btn-sm mt-3" onclick="showRefundModal()">${t('billing.requestRefund')}</button>
            </div>
        </div>
        ` : ''}
    `;
}

// Render Plan Cards
function renderPlanCards(currentTier) {
    const tiers = ['free', 'indie', 'studio', 'enterprise'];
    
    return tiers.map(tier => {
        const details = TIER_DETAILS[tier];
        const isCurrent = tier === currentTier;
        const isUpgrade = tiers.indexOf(tier) > tiers.indexOf(currentTier);
        
        return `
            <div class="plan-card ${isCurrent ? 'plan-current' : ''} ${details.byok_highlight ? 'plan-highlight-byok' : ''}" style="--plan-color: ${details.color}">
                <div class="plan-header">
                    <span class="plan-emoji">${details.emoji}</span>
                    <h3 class="plan-name">${details.name}</h3>
                    <div class="plan-price">
                        ${details.price === 0 ? t('billing.free') : `$${details.price}`}
                        ${details.price > 0 ? `<span class="plan-period">/${t('billing.month')}</span>` : ''}
                    </div>
                </div>
                <div class="plan-limits">
                    <div class="plan-limit-item">
                        <span class="limit-label">NPCs</span>
                        <span class="limit-value">${details.limits.npcs === -1 ? '∞' : details.limits.npcs}</span>
                    </div>
                    <div class="plan-limit-item plan-limit-hosted">
                        <span class="limit-label">${t('billing.hostedConversations')}</span>
                        <span class="limit-value">${details.hosted_conversations === -1 ? '∞' : formatNumber(details.hosted_conversations)}</span>
                    </div>
                    <div class="plan-limit-item plan-limit-byok ${details.byok_highlight ? 'plan-byok-highlight' : ''}">
                        <span class="limit-label">${t('billing.byokConversations')}</span>
                        <span class="limit-value">${t('billing.unlimited')}</span>
                    </div>
                    <div class="plan-limit-item">
                        <span class="limit-label">TTS</span>
                        <span class="limit-value">${details.limits.tts_chars === -1 ? '∞' : formatNumber(details.limits.tts_chars)}</span>
                    </div>
                </div>
                ${details.byok_highlight ? `
                    <div class="plan-byok-callout">
                        ${t('billing.byokCallout')}
                    </div>
                ` : ''}
                <div class="plan-action">
                    ${isCurrent ? `<span class="tag tag-green">${t('billing.currentPlanTag')}</span>` :
                      isUpgrade ? `<button class="btn btn-primary btn-sm plan-btn" onclick="upgradeTo('${tier}')">${t('billing.upgradeTo', { name: details.name })}</button>` :
                      `<button class="btn btn-secondary btn-sm plan-btn" onclick="downgradeTo('${tier}')">${t('billing.downgradeTo', { name: details.name })}</button>`}
                </div>
            </div>
        `;
    }).join('');
}

// Render Usage Metrics
function renderUsageMetrics(currentTier, currentMode) {
    const tierLimits = TIER_DETAILS[currentTier]?.limits || TIER_DETAILS.free.limits;
    const hostedLimit = TIER_DETAILS[currentTier]?.hosted_conversations || 1000;
    const isByok = currentMode === 'byok';
    
    const metrics = [
        {
            label: t('billing.npcCount'),
            used: billingUsage.npc_count || billingUsage.npcs || 0,
            limit: tierLimits.npcs,
            icon: 'NPC',
            color: '#7c5cff'
        },
        {
            label: t('billing.hostedConversations'),
            used: billingUsage.hosted_conversation_count || billingUsage.hosted_conversations || 0,
            limit: isByok ? -1 : hostedLimit,  // BYOK = unlimited
            icon: 'Cloud',
            color: '#00d4aa',
            badge: isByok ? 'BYOK' : null,
            badgeColor: '#00d4aa'
        },
        {
            label: t('billing.ttsUsage'),
            used: billingUsage.tts_chars || 0,
            limit: tierLimits.tts_chars,
            icon: 'Voice',
            color: '#ff6b35'
        },
        {
            label: t('billing.apiCalls'),
            used: billingUsage.api_calls || 0,
            limit: tierLimits.api_calls,
            icon: 'API',
            color: '#7c5cff'
        }
    ];
    
    return metrics.map(m => {
        const percentage = m.limit === -1 ? Math.min((m.used / 1000) * 100, 100) : Math.min((m.used / m.limit) * 100, 100);
        const displayLimit = m.limit === -1 ? (isByok && m.label === t('billing.hostedConversations') ? t('billing.byokUnlimited') : '∞') : formatNumber(m.limit);
        const barColor = percentage > 90 ? '#ff6b35' : percentage > 70 ? '#ff6b35' : m.color;
        
        return `
            <div class="usage-metric">
                <div class="metric-header">
                    <span class="metric-icon">${m.icon}</span>
                    <span class="metric-label">${m.label}</span>
                    ${m.badge ? `<span class="tag" style="background:${m.badgeColor};color:#fff;font-size:10px;margin-left:4px;">${m.badge}</span>` : ''}
                </div>
                <div class="metric-values">
                    <span class="metric-used">${formatNumber(m.used)}</span>
                    <span class="metric-limit">/ ${displayLimit}</span>
                </div>
                ${m.limit !== -1 || !isByok ? `
                <div class="usage-bar-bg">
                    <div class="usage-bar-fill" style="width: ${percentage}%; background: ${barColor};"></div>
                </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

// Upgrade
async function upgradeTo(tier) {
    try {
        if (API.billing && API.billing.createCheckout) {
            const res = await API.billing.createCheckout({ tier, interval: 'month' });
            if (res.data?.checkout_url) {
                window.open(res.data.checkout_url, '_blank');
                return;
            }
        }
        Toast.show(t('billing.upgradeHint') || `Upgrade to ${TIER_DETAILS[tier]?.name} — Stripe integration required`, 'info');
    } catch (error) {
        Toast.show(t('billing.upgradeFailed'), 'error');
    }
}

function downgradeTo(tier) {
    Toast.show(t('billing.downgradeHint') || `Please contact support to downgrade`, 'info');
}

function showUpgradeModal() {
    // Scroll to plans section
    const plansCard = document.querySelector('.plans-grid');
    if (plansCard) plansCard.scrollIntoView({ behavior: 'smooth' });
}

function showManageModal() {
    try {
        if (API.billing && API.billing.createPortal) {
            API.billing.createPortal({ return_url: window.location.href }).then(res => {
                if (res.data?.portal_url) {
                    window.open(res.data.portal_url, '_blank');
                    return;
                }
            });
        }
    } catch (e) {}
    Toast.show(t('billing.manageHint') || 'Please contact support to manage your plan', 'info');
}

function showRefundModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'refund-modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 440px;">
            <div class="modal-header">
                <h3>${t('billing.requestRefund')}</h3>
                <button class="modal-close" onclick="closeRefundModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">${t('billing.refundReason')}</label>
                    <textarea id="refund-reason" class="form-input" rows="3" placeholder="${t('billing.refundReasonPlaceholder')}"></textarea>
                </div>
                <p class="text-muted" style="font-size: 12px;">${t('billing.refundPolicy')}</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeRefundModal()">${t('common.cancel')}</button>
                <button class="btn btn-danger" onclick="submitRefund()">${t('billing.submitRefund')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function closeRefundModal() {
    const modal = document.getElementById('refund-modal');
    if (modal) modal.remove();
}

async function submitRefund() {
    const reasonInput = document.getElementById('refund-reason');
    const reason = reasonInput ? reasonInput.value.trim() : '';
    
    if (!reason) {
        Toast.show(t('billing.enterRefundReason'), 'warning');
        return;
    }
    
    try {
        if (API.billing && API.billing.requestRefund) {
            await API.billing.requestRefund({ reason });
        }
        Toast.show(t('billing.refundSubmitted'), 'success');
        closeRefundModal();
    } catch (error) {
        Toast.show(t('billing.refundFailed'), 'error');
    }
}
