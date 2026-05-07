/**
 * Dashboard Page - Neshama NPC Soul OS Overview
 * Simplified: Active NPCs, Usage, Subscription, Quick Actions
 */

// Render Dashboard
async function renderDashboard() {
    const container = document.getElementById('page-dashboard');
    
    try {
        // Fetch data in parallel
        const [overviewRes, usageRes] = await Promise.allSettled([
            API.game.getOverview(),
            API.billing ? API.billing.getUsage() : Promise.reject('no billing')
        ]);
        
        const overview = overviewRes.status === 'fulfilled' ? (overviewRes.value.data || {}) : {};
        const usage = usageRes.status === 'fulfilled' ? (usageRes.value.data || {}) : {};
        
        // Update app state
        AppState.npcs = overview.npcs || [];
        
        const activeNPCs = overview.totalNPCs || overview.npcs?.length || 0;
        const monthlyInteractions = usage.monthly_interactions || usage.interactions || 0;
        const apiCalls = usage.api_calls || 0;
        const tier = usage.tier || overview.tier || 'free';
        const tierLabel = tier.charAt(0).toUpperCase() + tier.slice(1);
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('dashboard.title')}</h1>
                <p class="page-subtitle">${t('dashboard.subtitle')}</p>
            </div>
            
            <!-- Stats Cards -->
            <div class="grid-4">
                <div class="card stat-card">
                    <div class="stat-icon">🎭</div>
                    <div class="stat-info">
                        <div class="stat-value">${activeNPCs}</div>
                        <div class="stat-label">${t('dashboard.activeNPCs')}</div>
                    </div>
                </div>
                <div class="card stat-card">
                    <div class="stat-icon">💬</div>
                    <div class="stat-info">
                        <div class="stat-value">${formatNumber(monthlyInteractions)}</div>
                        <div class="stat-label">${t('dashboard.monthlyInteractions')}</div>
                    </div>
                </div>
                <div class="card stat-card">
                    <div class="stat-icon">📡</div>
                    <div class="stat-info">
                        <div class="stat-value">${formatNumber(apiCalls)}</div>
                        <div class="stat-label">${t('dashboard.apiCalls')}</div>
                    </div>
                </div>
                <div class="card stat-card">
                    <div class="stat-icon">⭐</div>
                    <div class="stat-info">
                        <div class="stat-value">${tierLabel}</div>
                        <div class="stat-label">${t('dashboard.subscription')}</div>
                    </div>
                </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('dashboard.quickActions')}</span>
                </div>
                <div class="quick-actions-grid">
                    <button class="quick-action-btn" onclick="router.navigate('account')">
                        <span class="action-icon">🔑</span>
                        <span class="action-text">${t('dashboard.createAPIKey')}</span>
                    </button>
                    <button class="quick-action-btn" onclick="router.navigate('templates')">
                        <span class="action-icon">📚</span>
                        <span class="action-text">${t('dashboard.browseTemplates')}</span>
                    </button>
                    <button class="quick-action-btn" onclick="router.navigate('billing')">
                        <span class="action-icon">📊</span>
                        <span class="action-text">${t('dashboard.viewUsage')}</span>
                    </button>
                    <button class="quick-action-btn" onclick="router.navigate('demo')">
                        <span class="action-icon">🎮</span>
                        <span class="action-text">${t('dashboard.tryDemo')}</span>
                    </button>
                </div>
            </div>
            
            <!-- Recent Activity & NPC Overview -->
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('dashboard.recentActivity')}</span>
                    </div>
                    <div id="dashboard-activity" class="activity-list">
                        ${await renderRecentActivity(overview)}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('dashboard.npcOverview')}</span>
                    </div>
                    <div id="dashboard-npcs" class="npc-overview-list">
                        ${renderNPCOverview(overview.npcs || [])}
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Dashboard load error:', error);
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('dashboard.title')}</h1>
                <p class="page-subtitle">${t('dashboard.subtitle')}</p>
            </div>
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-text">${t('dashboard.failedLoad')}</div>
                <button class="btn btn-primary mt-4" onclick="renderDashboard()">${t('common.retry')}</button>
            </div>
        `;
    }
}

// Format number with K/M suffix
function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return String(num);
}

// Render recent activity
async function renderRecentActivity(overview) {
    try {
        const res = await API.game.getRecentEvents(8);
        const events = res.data || [];
        
        if (!events || events.length === 0) {
            return `<div class="empty-state-sm">${t('emotion.noEvents')}</div>`;
        }
        
        return events.map(e => `
            <div class="activity-item">
                <span class="activity-emoji">${getEventEmoji(e.eventType)}</span>
                <span class="activity-text">${t('event.' + e.eventType) || e.eventType}</span>
                <span class="activity-target">${escapeHtml(e.npcName || '')}</span>
                <span class="activity-time">${e.timestamp ? formatDate(e.timestamp) : ''}</span>
            </div>
        `).join('');
    } catch (err) {
        return `<div class="empty-state-sm">${t('common.noData')}</div>`;
    }
}

// Get event emoji
function getEventEmoji(eventType) {
    const map = {
        gift: '🎁', attack: '⚔️', help: '🤝', insult: '😤',
        compliment: '🌟', trade: '💰', join_battle: '🗡️', leave_battle: '🏳️',
        meet: '👋', depart: '👋', heal: '💚', steal: '🫣',
        promise: '🤞', betray: '💀', discover: '🔍'
    };
    return map[eventType] || '📌';
}

// Render NPC Overview (simplified)
function renderNPCOverview(npcs) {
    if (!npcs || npcs.length === 0) {
        return `<div class="empty-state-sm">${t('npcList.noNPCs')}</div>`;
    }
    
    return npcs.slice(0, 8).map(npc => {
        const emotion = npc.emotion || {};
        return `
            <div class="npc-overview-item">
                <span class="npc-avatar-sm">${npc.avatar || '🎭'}</span>
                <span class="npc-name-sm">${escapeHtml(npc.name)}</span>
                <span class="npc-emotion-sm">${emotion.primary?.emoji || '😐'}</span>
            </div>
        `;
    }).join('');
}

// Refresh Dashboard Data
async function refreshDashboardData() {
    try {
        const overviewRes = await API.game.getOverview();
        const overview = overviewRes.data || {};
        
        // Update stats if elements exist
        const statValues = document.querySelectorAll('.stat-value');
        if (statValues[0]) statValues[0].textContent = overview.totalNPCs || 0;
        if (statValues[1]) statValues[1].textContent = formatNumber(overview.monthlyInteractions || 0);
        if (statValues[2]) statValues[2].textContent = formatNumber(overview.apiCalls || 0);
    } catch (error) {
        console.error('Refresh dashboard failed:', error);
    }
}

// Get Emotion Emoji (shared utility)
function getEmotionEmoji(emotion) {
    const map = {
        joy: '😊', sadness: '😢', anger: '😠', fear: '😨',
        surprise: '😮', disgust: '🤢', trust: '🤝', anticipation: '🤔',
        calm: '😌', curiosity: '🧐'
    };
    return map[emotion] || '😐';
}
