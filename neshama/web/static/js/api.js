/**
 * Neshama Soul Panel - API Client
 */

const API = {
    baseUrl: '',
    
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },
    
    // Soul API
    soul: {
        async get() {
            return API.request('/api/soul/');
        },
        
        async update(config) {
            return API.request('/api/soul/', {
                method: 'PUT',
                body: JSON.stringify(config)
            });
        },
        
        async applyPreset(preset) {
            return API.request(`/api/soul/preset/${preset}`, {
                method: 'POST'
            });
        },
        
        async export() {
            return API.request('/api/soul/export');
        },
        
        async import(config) {
            return API.request('/api/soul/import', {
                method: 'POST',
                body: JSON.stringify(config)
            });
        }
    },
    
    // Emotion API
    emotion: {
        async getCurrent() {
            return API.request('/api/emotion/current');
        },
        
        async getHistory(hours = 24) {
            return API.request(`/api/emotion/history?hours=${hours}`);
        },
        
        async getCategories() {
            return API.request('/api/emotion/categories');
        }
    },
    
    // Memory API
    memory: {
        async getLayers() {
            return API.request('/api/memory/layers');
        },
        
        async getLayer(layer, search = '', limit = 50) {
            let url = `/api/memory/${layer}?limit=${limit}`;
            if (search) url += `&search=${encodeURIComponent(search)}`;
            return API.request(url);
        },
        
        async addMemory(layer, memory) {
            return API.request(`/api/memory/${layer}`, {
                method: 'POST',
                body: JSON.stringify(memory)
            });
        },
        
        async deleteMemory(layer, memoryId) {
            return API.request(`/api/memory/${layer}/${memoryId}`, {
                method: 'DELETE'
            });
        },
        
        async updateMemory(layer, memoryId, updates) {
            return API.request(`/api/memory/${layer}/${memoryId}`, {
                method: 'PUT',
                body: JSON.stringify(updates)
            });
        },
        
        async getStats() {
            return API.request('/api/memory/stats/overview');
        }
    },
    
    // Evolution API
    evolution: {
        async getHistory(days = 30) {
            return API.request(`/api/evolution/history?days=${days}`);
        },
        
        async getEvents() {
            return API.request('/api/evolution/events');
        },
        
        async getSnapshots() {
            return API.request('/api/evolution/snapshots');
        },
        
        async createSnapshot(name, description) {
            return API.request('/api/evolution/snapshot', {
                method: 'POST',
                body: JSON.stringify({ name, description })
            });
        },
        
        async compareSnapshots(snap1, snap2) {
            return API.request(`/api/evolution/compare/${snap1}/${snap2}`);
        }
    },
    
    // Config API
    config: {
        async get() {
            return API.request('/api/config/');
        },
        
        async update(updates) {
            return API.request('/api/config/', {
                method: 'PUT',
                body: JSON.stringify(updates)
            });
        },
        
        async getModelProviders() {
            return API.request('/api/config/model/providers');
        },
        
        async getPlatformAdapters() {
            return API.request('/api/config/platform/adapters');
        },
        
        async testModel(config) {
            return API.request('/api/config/model/test', {
                method: 'POST',
                body: JSON.stringify(config)
            });
        },
        
        async export() {
            return API.request('/api/config/export');
        },
        
        async import(config) {
            return API.request('/api/config/import', {
                method: 'POST',
                body: JSON.stringify(config)
            });
        },
        
        async reset() {
            return API.request('/api/config/reset', {
                method: 'POST'
            });
        }
    },
    
    // Chat API
    chat: {
        async getHistory(limit = 50) {
            return API.request(`/api/chat/history?limit=${limit}`);
        },
        
        async clearHistory() {
            return API.request('/api/chat/history', {
                method: 'DELETE'
            });
        }
    },
    
    // Composite Emotion API
    compositeEmotion: {
        async getEmotions(soulId = 'default', neuroticism = 0.5) {
            return API.request(`/api/composite-emotion/emotions?soul_id=${soulId}&neuroticism=${neuroticism}`);
        },
        
        async setEmotion(soulId, emotion, intensity, neuroticism = 0.5) {
            return API.request(`/api/composite-emotion/emotions?soul_id=${soulId}&emotion=${emotion}&intensity=${intensity}&neuroticism=${neuroticism}`, {
                method: 'POST'
            });
        },
        
        async synthesize(soulId = 'default', neuroticism = 0.5) {
            return API.request(`/api/composite-emotion/synthesize?soul_id=${soulId}&neuroticism=${neuroticism}`, {
                method: 'POST'
            });
        },
        
        async tick(soulId = 'default', deltaSeconds = 60, neuroticism = 0.5) {
            return API.request(`/api/composite-emotion/tick?soul_id=${soulId}&delta_seconds=${deltaSeconds}&neuroticism=${neuroticism}`, {
                method: 'POST'
            });
        },
        
        async clear(soulId = 'default') {
            return API.request(`/api/composite-emotion/clear?soul_id=${soulId}`, {
                method: 'POST'
            });
        },
        
        async getTriggered(soulId = 'default', threshold = 0.7) {
            return API.request(`/api/composite-emotion/triggered?soul_id=${soulId}&threshold=${threshold}`);
        }
    },
    
    // Entity Graph API
    entityGraph: {
        async addEntity(graphId = 'default', name, entityType = 'concept', description = '', importance = 0.5) {
            return API.request(`/api/entity-graph/entity?graph_id=${graphId}&name=${encodeURIComponent(name)}&entity_type=${entityType}&description=${encodeURIComponent(description)}&importance=${importance}`, {
                method: 'POST'
            });
        },
        
        async getEntity(graphId = 'default', entityId) {
            return API.request(`/api/entity-graph/entity/${entityId}?graph_id=${graphId}`);
        },
        
        async getEntities(graphId = 'default', entityType = '', nameContains = '', minImportance = 0) {
            let url = `/api/entity-graph/entities?graph_id=${graphId}`;
            if (entityType) url += `&entity_type=${entityType}`;
            if (nameContains) url += `&name_contains=${encodeURIComponent(nameContains)}`;
            if (minImportance) url += `&min_importance=${minImportance}`;
            return API.request(url);
        },
        
        async deleteEntity(graphId = 'default', entityId) {
            return API.request(`/api/entity-graph/entity/${entityId}?graph_id=${graphId}`, {
                method: 'DELETE'
            });
        },
        
        async addRelation(graphId = 'default', sourceId, targetId, relationType = 'related_to', weight = 1.0, direction = 'directed') {
            return API.request(`/api/entity-graph/relation?graph_id=${graphId}&source_id=${sourceId}&target_id=${targetId}&relation_type=${relationType}&weight=${weight}&direction=${direction}`, {
                method: 'POST'
            });
        },
        
        async getRelations(graphId = 'default', entityId = '', relationType = '') {
            let url = `/api/entity-graph/relations?graph_id=${graphId}`;
            if (entityId) url += `&entity_id=${entityId}`;
            if (relationType) url += `&relation_type=${relationType}`;
            return API.request(url);
        },
        
        async deleteRelation(graphId = 'default', relationId) {
            return API.request(`/api/entity-graph/relation/${relationId}?graph_id=${graphId}`, {
                method: 'DELETE'
            });
        },
        
        async getNeighbors(graphId = 'default', entityId, relationType = '') {
            let url = `/api/entity-graph/neighbors/${entityId}?graph_id=${graphId}`;
            if (relationType) url += `&relation_type=${relationType}`;
            return API.request(url);
        },
        
        async findPaths(graphId = 'default', sourceId, targetId, maxDepth = 3) {
            return API.request(`/api/entity-graph/paths/${sourceId}/${targetId}?graph_id=${graphId}&max_depth=${maxDepth}`);
        },
        
        async getStats(graphId = 'default') {
            return API.request(`/api/entity-graph/stats?graph_id=${graphId}`);
        }
    },
    
    // Progressive Summarization API
    progressiveSummarization: {
        async addL0(summarizerId = 'default', role, content, timestamp = null, metadata = null) {
            let url = `/api/summarization/l0/add?summarizer_id=${summarizerId}&role=${role}&content=${encodeURIComponent(content)}`;
            if (timestamp) url += `&timestamp=${timestamp}`;
            return API.request(url, {
                method: 'POST',
                body: metadata ? JSON.stringify(metadata) : undefined
            });
        },
        
        async getL0(summarizerId = 'default', limit = null) {
            let url = `/api/summarization/l0?summarizer_id=${summarizerId}`;
            if (limit) url += `&limit=${limit}`;
            return API.request(url);
        },
        
        async getL1(summarizerId = 'default', limit = null) {
            let url = `/api/summarization/l1?summarizer_id=${summarizerId}`;
            if (limit) url += `&limit=${limit}`;
            return API.request(url);
        },
        
        async getL2(summarizerId = 'default', knowledgeType = '', limit = null) {
            let url = `/api/summarization/l2?summarizer_id=${summarizerId}`;
            if (knowledgeType) url += `&knowledge_type=${knowledgeType}`;
            if (limit) url += `&limit=${limit}`;
            return API.request(url);
        },
        
        async summarizeL0(summarizerId = 'default', force = false) {
            return API.request(`/api/summarization/summarize-l0?summarizer_id=${summarizerId}&force=${force}`, {
                method: 'POST'
            });
        },
        
        async summarizeL1(summarizerId = 'default', force = false) {
            return API.request(`/api/summarization/summarize-l1?summarizer_id=${summarizerId}&force=${force}`, {
                method: 'POST'
            });
        },
        
        async autoProcess(summarizerId = 'default') {
            return API.request(`/api/summarization/auto-process?summarizer_id=${summarizerId}`, {
                method: 'POST'
            });
        },
        
        async getStats(summarizerId = 'default') {
            return API.request(`/api/summarization/stats?summarizer_id=${summarizerId}`);
        }
    },
    
    // Model Marketplace API
    marketplace: {
        async getProviders() {
            return API.request('/api/models/providers');
        },
        
        async getPricing() {
            return API.request('/api/models/pricing');
        },
        
        async search(params = {}) {
            let url = '/api/models/search?';
            const queryParams = [];
            if (params.provider) queryParams.push(`provider=${params.provider}`);
            if (params.task_type) queryParams.push(`task_type=${params.task_type}`);
            if (params.free_only) queryParams.push(`free_only=true`);
            if (params.max_price) queryParams.push(`max_price=${params.max_price}`);
            if (params.query) queryParams.push(`query=${encodeURIComponent(params.query)}`);
            return API.request(url + queryParams.join('&'));
        },
        
        async compare(modelIds) {
            return API.request('/api/models/compare', {
                method: 'POST',
                body: JSON.stringify({ model_ids: modelIds })
            });
        },
        
        async estimateCost(inputTokens, outputRatio = 0.5) {
            return API.request('/api/models/estimate-cost', {
                method: 'POST',
                body: JSON.stringify({
                    input_tokens_per_month: inputTokens,
                    output_ratio: outputRatio
                })
            });
        },
        
        async configure(config) {
            return API.request('/api/models/config', {
                method: 'POST',
                body: JSON.stringify(config)
            });
        },
        
        async test(config) {
            return API.request('/api/models/test', {
                method: 'POST',
                body: JSON.stringify(config)
            });
        }
    },
    
    // Coding Plans API
    codingPlans: {
        async getAll() {
            return API.request('/api/coding-plans/');
        },
        
        async get(planId) {
            return API.request(`/api/coding-plans/${planId}`);
        },
        
        async create(planData) {
            return API.request('/api/coding-plans/', {
                method: 'POST',
                body: JSON.stringify(planData)
            });
        },
        
        async update(planId, planData) {
            return API.request(`/api/coding-plans/${planId}`, {
                method: 'PUT',
                body: JSON.stringify(planData)
            });
        },
        
        async delete(planId) {
            return API.request(`/api/coding-plans/${planId}`, {
                method: 'DELETE'
            });
        },
        
        async test(planId) {
            return API.request(`/api/coding-plans/${planId}/test`, {
                method: 'POST'
            });
        },
        
        async toggle(planId) {
            return API.request(`/api/coding-plans/${planId}/toggle`, {
                method: 'POST'
            });
        },
        
        async getStats(planId) {
            return API.request(`/api/coding-plans/${planId}/stats`);
        }
    },
    
    // Extended Config API
    config: {
        async get() {
            return API.request('/api/config/');
        },
        
        async update(updates) {
            return API.request('/api/config/', {
                method: 'PUT',
                body: JSON.stringify(updates)
            });
        },
        
        async getModelProviders() {
            return API.request('/api/config/model/providers');
        },
        
        async getConfiguredProviders() {
            return API.request('/api/config/model/configured');
        },
        
        async configureProvider(config) {
            return API.request('/api/config/model/configure', {
                method: 'POST',
                body: JSON.stringify(config)
            });
        },
        
        async removeProvider(providerId) {
            return API.request(`/api/config/model/configure/${providerId}`, {
                method: 'DELETE'
            });
        },
        
        async getDefaultModel() {
            return API.request('/api/config/model/default');
        },
        
        async setDefaultModel(config) {
            return API.request('/api/config/model/default', {
                method: 'PUT',
                body: JSON.stringify(config)
            });
        },
        
        async getRoutingStrategy() {
            return API.request('/api/config/model/routing');
        },
        
        async setRoutingStrategy(config) {
            return API.request('/api/config/model/routing', {
                method: 'PUT',
                body: JSON.stringify(config)
            });
        },
        
        async testModel(config) {
            return API.request('/api/config/model/test', {
                method: 'POST',
                body: JSON.stringify(config)
            });
        },
        
        async export() {
            return API.request('/api/config/export');
        },
        
        async import(config) {
            return API.request('/api/config/import', {
                method: 'POST',
                body: JSON.stringify(config)
            });
        },
        
        async reset() {
            return API.request('/api/config/reset', {
                method: 'POST'
            });
        },
        
        async getPlatformAdapters() {
            return API.request('/api/config/platform/adapters');
        }
    },

    // Game API (NPC Studio)
    game: {
        // NPC Management
        async createNPC(name, preset = 'custom', ocean = null) {
            const body = { name, preset };
            if (ocean) body.ocean = ocean;
            return API.request('/api/game/npc/', {
                method: 'POST',
                body: JSON.stringify(body)
            });
        },

        async listNPCs() {
            return API.request('/api/game/npc/');
        },

        async getNPC(npcId) {
            return API.request(`/api/game/npc/${npcId}`);
        },

        async deleteNPC(npcId) {
            return API.request(`/api/game/npc/${npcId}`, {
                method: 'DELETE'
            });
        },

        async updateNPC(npcId, updates) {
            return API.request(`/api/game/npc/${npcId}`, {
                method: 'PUT',
                body: JSON.stringify(updates)
            });
        },

        async exportNPC(npcId) {
            return API.request(`/api/game/npc/${npcId}/export`);
        },

        async batchDelete(npcIds) {
            return API.request('/api/game/npc/batch-delete', {
                method: 'POST',
                body: JSON.stringify({ npc_ids: npcIds })
            });
        },

        // Event System
        async sendEvent(npcId, eventType, intensity = 0.5, context = {}) {
            return API.request(`/api/game/npc/${npcId}/event`, {
                method: 'POST',
                body: JSON.stringify({
                    event_type: eventType,
                    intensity: intensity,
                    context: context
                })
            });
        },

        async getEmotion(npcId) {
            return API.request(`/api/game/npc/${npcId}/emotion`);
        },

        async getEmotionHistory(npcId, limit = 20) {
            return API.request(`/api/game/npc/${npcId}/emotion/history?limit=${limit}`);
        },

        // Behavior System
        async getBehavior(npcId) {
            return API.request(`/api/game/npc/${npcId}/behavior`);
        },

        // Chat
        async chat(npcId, message, playerId = 'player1') {
            return API.request(`/api/game/npc/${npcId}/chat`, {
                method: 'POST',
                body: JSON.stringify({
                    message: message,
                    player_id: playerId
                })
            });
        },

        async getChatHistory(npcId, limit = 50) {
            return API.request(`/api/game/npc/${npcId}/chat/history?limit=${limit}`);
        },

        // Profile
        async getProfile(npcId) {
            return API.request(`/api/game/npc/${npcId}/profile`);
        },

        // Memory
        async getMemory(npcId, query = '') {
            let url = `/api/game/npc/${npcId}/memory`;
            if (query) url += `?query=${encodeURIComponent(query)}`;
            return API.request(url);
        },

        async remember(npcId, entityType, entityName, relation = '', note = '') {
            return API.request(`/api/game/npc/${npcId}/remember`, {
                method: 'POST',
                body: JSON.stringify({
                    entity_type: entityType,
                    entity_name: entityName,
                    relation: relation,
                    note: note
                })
            });
        },

        async forget(npcId, entityName) {
            return API.request(`/api/game/npc/${npcId}/forget`, {
                method: 'POST',
                body: JSON.stringify({ entity_name: entityName })
            });
        },

        // Relations
        async getRelations(npcId) {
            return API.request(`/api/game/npc/${npcId}/relations`);
        },

        async addRelation(npcId, targetName, relationType, note = '') {
            return API.request(`/api/game/npc/${npcId}/relation`, {
                method: 'POST',
                body: JSON.stringify({
                    target_name: targetName,
                    relation_type: relationType,
                    note: note
                })
            });
        },

        // Event Templates
        async getEventTemplates() {
            return API.request('/api/game/events/templates');
        },

        async replayEvents(npcId, eventSequence) {
            return API.request(`/api/game/npc/${npcId}/replay`, {
                method: 'POST',
                body: JSON.stringify({ events: eventSequence })
            });
        },

        // Studio Overview
        async getOverview() {
            return API.request('/api/game/overview');
        },

        async getRecentEvents(limit = 10) {
            return API.request(`/api/game/events/recent?limit=${limit}`);
        },

        async getEmotionHeatmap() {
            return API.request('/api/game/emotion-heatmap');
        },

        // Presets
        async listPresets() {
            return API.request('/api/game/npc/presets');
        },

        async getPreset(presetName) {
            return API.request(`/api/game/npc/presets/${presetName}`);
        }
    },

    // Billing API
    billing: {
        async getPlans() {
            return API.request('/api/billing/plans');
        },

        async getSubscription() {
            return API.request('/api/billing/subscription');
        },

        async getUsage() {
            return API.request('/api/billing/usage');
        },

        async createCheckout(data) {
            return API.request('/api/billing/checkout', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        async createPortal(data) {
            return API.request('/api/billing/portal', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        async requestRefund(data) {
            return API.request('/api/billing/refund', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        async upgrade(data) {
            return API.request('/api/billing/upgrade', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }
    },

    // Presets API (convenience alias)
    presets: {
        async list() {
            return API.request('/api/game/npc/presets');
        },

        async get(presetName) {
            return API.request(`/api/game/npc/presets/${presetName}`);
        }
    }
};

// WebSocket Chat Manager
class ChatWebSocket {
    constructor(url) {
        this.url = url || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/chat/ws`;
        this.ws = null;
        this.listeners = {};
        this.connected = false;
    }
    
    connect(sessionId = 'default') {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(`${this.url}?session_id=${sessionId}`);
                
                this.ws.onopen = () => {
                    this.connected = true;
                    this.emit('connected');
                    resolve();
                };
                
                this.ws.onclose = () => {
                    this.connected = false;
                    this.emit('disconnected');
                };
                
                this.ws.onerror = (error) => {
                    reject(error);
                };
                
                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.emit('message', data);
                    } catch (e) {
                        console.error('Failed to parse message:', e);
                    }
                };
            } catch (error) {
                reject(error);
            }
        });
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    sendMessage(content) {
        this.send({
            type: 'message',
            content: content
        });
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
    
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
    
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }
    
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }
}

// Export
window.API = API;
window.ChatWebSocket = ChatWebSocket;
