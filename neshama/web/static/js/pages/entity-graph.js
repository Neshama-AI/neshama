/**
 * Entity Graph Page - Entity knowledge graph visualization and management
 */

let entityGraphData = {
    entities: [],
    relations: [],
    stats: null
};

// Entity type icons and colors
const ENTITY_TYPES = [
    { id: 'concept', label_zh: '概念', label_en: 'Concept', icon: 'Idea', color: '#4F46E5' },
    { id: 'person', label_zh: '人物', label_en: 'Person', icon: 'User', color: '#EC4899' },
    { id: 'place', label_zh: '地点', label_en: 'Place', icon: 'Location', color: '#10B981' },
    { id: 'event', label_zh: '事件', label_en: 'Event', icon: 'Date', color: '#F59E0B' },
    { id: 'object', label_zh: '物体', label_en: 'Object', icon: 'Package', color: '#7c5cff' },
    { id: 'organization', label_zh: '组织', label_en: 'Organization', icon: 'Org', color: '#7c5cff' }
];

// Relation types
const RELATION_TYPES = [
    { id: 'related_to', label_zh: '相关于', label_en: 'Related to', icon: 'Link' },
    { id: 'part_of', label_zh: '是...的一部分', label_en: 'Part of', icon: 'Folder' },
    { id: 'causes', label_zh: '导致', label_en: 'Causes', icon: '→' },
    { id: 'located_in', label_zh: '位于', label_en: 'Located in', icon: 'Location' },
    { id: 'works_for', label_zh: '为...工作', label_en: 'Works for', icon: 'Work' },
    { id: 'knows', label_zh: '认识', label_en: 'Knows', icon: 'Partner' },
    { id: 'created_by', label_zh: '由...创建', label_en: 'Created by', icon: 'Author' },
    { id: 'synonymous_to', label_zh: '同义于', label_en: 'Synonymous to', icon: '≈' }
];

// Get localized label for entity/relation type
function getEntityTypeLabel(type) {
    const currentLang = localStorage.getItem('neshama-lang') || 'zh';
    return currentLang === 'zh' ? type.label_zh : type.label_en;
}

// Render Entity Graph Page
async function renderEntityGraph() {
    const container = document.getElementById('page-entity-graph');
    
    try {
        const [entitiesRes, relationsRes, statsRes] = await Promise.all([
            API.entityGraph.getEntities('default'),
            API.entityGraph.getRelations('default'),
            API.entityGraph.getStats('default')
        ]);
        
        entityGraphData.entities = entitiesRes.data.entities || [];
        entityGraphData.relations = relationsRes.data.relations || [];
        entityGraphData.stats = statsRes.data;
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('entityGraph.title')}</h1>
                <p class="page-subtitle">${t('entityGraph.subtitle')}</p>
            </div>
            
            <div class="grid-4">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('entityGraph.totalEntities')}</span>
                    </div>
                    <div class="stat-value">${entityGraphData.entities.length}</div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('entityGraph.totalRelations')}</span>
                    </div>
                    <div class="stat-value">${entityGraphData.relations.length}</div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('entityGraph.entityTypes')}</span>
                    </div>
                    <div class="stat-value">${statsRes.data?.entity_type_counts ? Object.keys(statsRes.data.entity_type_counts).length : 0}</div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('entityGraph.density')}</span>
                    </div>
                    <div class="stat-value">${(statsRes.data?.density || 0).toFixed(2)}</div>
                </div>
            </div>
            
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('entityGraph.entities')}</span>
                        <button class="btn btn-sm btn-primary" onclick="showAddEntityModal()">+ ${t('common.add')}</button>
                    </div>
                    <div class="flex gap-2 mb-3">
                        <select id="entity-type-filter" class="form-input" style="width: auto;" onchange="filterEntities()">
                            <option value="">${t('entityGraph.allTypes')}</option>
                            ${ENTITY_TYPES.map(type => `<option value="${type.id}">${type.icon} ${getEntityTypeLabel(type)}</option>`).join('')}
                        </select>
                        <input type="text" id="entity-search" class="form-input" style="flex: 1;" 
                               placeholder="${t('common.search')}..." onkeyup="filterEntities()">
                    </div>
                    <div id="entities-list" class="mt-3" style="max-height: 400px; overflow-y: auto;">
                        ${renderEntitiesList()}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('entityGraph.relations')}</span>
                        <button class="btn btn-sm btn-primary" onclick="showAddRelationModal()">+ ${t('common.add')}</button>
                    </div>
                    <div class="flex gap-2 mb-3">
                        <select id="relation-type-filter" class="form-input" style="width: auto;" onchange="filterRelations()">
                            <option value="">${t('entityGraph.allTypes')}</option>
                            ${RELATION_TYPES.map(type => `<option value="${type.id}">${type.icon} ${getEntityTypeLabel(type)}</option>`).join('')}
                        </select>
                    </div>
                    <div id="relations-list" class="mt-3" style="max-height: 400px; overflow-y: auto;">
                        ${renderRelationsList()}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('entityGraph.pathQuery')}</span>
                </div>
                <div class="mt-4">
                    <div class="flex gap-2 items-end">
                        <div class="form-group" style="flex: 1; margin-bottom: 0;">
                            <label class="form-label">${t('entityGraph.fromEntity')}</label>
                            <select id="path-source" class="form-input">
                                <option value="">${t('entityGraph.selectEntity')}</option>
                                ${entityGraphData.entities.map(e => `<option value="${e.id}">${getEntityIcon(e.entity_type)} ${e.name}</option>`).join('')}
                            </select>
                        </div>
                        <span style="padding: 10px; font-size: 20px;">→</span>
                        <div class="form-group" style="flex: 1; margin-bottom: 0;">
                            <label class="form-label">${t('entityGraph.toEntity')}</label>
                            <select id="path-target" class="form-input">
                                <option value="">${t('entityGraph.selectEntity')}</option>
                                ${entityGraphData.entities.map(e => `<option value="${e.id}">${getEntityIcon(e.entity_type)} ${e.name}</option>`).join('')}
                            </select>
                        </div>
                        <button class="btn btn-primary" onclick="findPaths()">${t('entityGraph.findPath')}</button>
                    </div>
                    <div id="path-result" class="mt-4">
                        <div class="text-muted">${t('entityGraph.pathHint')}</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('entityGraph.entityDetails')}</span>
                </div>
                <div id="entity-details" class="mt-3">
                    <div class="empty-state">
                        <div class="empty-state-icon">Here</div>
                        <div class="empty-state-text">${t('entityGraph.selectEntityHint')}</div>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Entity graph load error:', error);
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('entityGraph.title')}</h1>
                <p class="page-subtitle">${t('entityGraph.subtitle')}</p>
            </div>
            <div class="card">
                <div class="empty-state">
                    <div class="empty-state-icon">Search</div>
                    <div class="empty-state-text">${t('entityGraph.failedLoad')}</div>
                    <div class="text-muted mt-2" style="font-size: 12px;">${error.message || ''}</div>
                    <button class="btn btn-primary mt-4" onclick="renderEntityGraph()">${t('common.retry')}</button>
                </div>
            </div>
        `;
        Toast.show(t('common.error'), 'error');
    }
}

// Render entities list
function renderEntitiesList(entities = null) {
    const list = entities || entityGraphData.entities;
    
    if (list.length === 0) {
        return `<div class="text-muted">${t('common.noData')}</div>`;
    }
    
    return list.map(entity => {
        const typeInfo = ENTITY_TYPES.find(t => t.id === entity.entity_type) || ENTITY_TYPES[0];
        return `
            <div class="entity-item" onclick="showEntityDetails('${entity.id}')" 
                 style="padding: 12px; background: var(--bg-tertiary); border-radius: 8px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s;">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <span style="font-size: 24px; color: ${typeInfo.color};">${typeInfo.icon}</span>
                        <div>
                            <div style="font-weight: 500;">${escapeHtml(entity.name)}</div>
                            <div class="flex gap-2 mt-1">
                                <span class="tag" style="background: ${typeInfo.color}22; color: ${typeInfo.color};">${typeInfo.label}</span>
                                ${entity.description ? `<span class="text-muted" style="font-size: 12px;">${escapeHtml(entity.description).substring(0, 30)}...</span>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-accent">${((entity.importance || 0.5) * 100).toFixed(0)}%</span>
                        <button class="btn btn-icon btn-secondary btn-sm" onclick="event.stopPropagation(); deleteEntity('${entity.id}')" title="${t('common.delete')}">Delete</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Render relations list
function renderRelationsList(relations = null) {
    const list = relations || entityGraphData.relations;
    
    if (list.length === 0) {
        return `<div class="text-muted">${t('common.noData')}</div>`;
    }
    
    return list.map(relation => {
        const sourceEntity = entityGraphData.entities.find(e => e.id === relation.source_id);
        const targetEntity = entityGraphData.entities.find(e => e.id === relation.target_id);
        const relationType = RELATION_TYPES.find(r => r.id === relation.relation_type) || RELATION_TYPES[0];
        
        return `
            <div style="padding: 12px; background: var(--bg-tertiary); border-radius: 8px; margin-bottom: 8px;">
                <div class="flex items-center gap-2">
                    <span style="font-weight: 500;">${escapeHtml(sourceEntity?.name || relation.source_id)}</span>
                    <span class="text-muted">${relationType.icon} ${relationType.label}</span>
                    <span style="font-weight: 500;">${escapeHtml(targetEntity?.name || relation.target_id)}</span>
                </div>
                ${relation.weight !== undefined && relation.weight !== 1 ? `
                    <div class="text-muted mt-1" style="font-size: 12px;">
                        Weight: ${relation.weight.toFixed(2)}
                    </div>
                ` : ''}
                <div class="flex justify-end mt-2">
                    <button class="btn btn-icon btn-secondary btn-sm" onclick="deleteRelation('${relation.id}')" title="${t('common.delete')}">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

// Filter entities
function filterEntities() {
    const typeFilter = document.getElementById('entity-type-filter')?.value || '';
    const searchQuery = document.getElementById('entity-search')?.value.toLowerCase() || '';
    
    const filtered = entityGraphData.entities.filter(entity => {
        const matchesType = !typeFilter || entity.entity_type === typeFilter;
        const matchesSearch = !searchQuery || 
            entity.name.toLowerCase().includes(searchQuery) ||
            (entity.description && entity.description.toLowerCase().includes(searchQuery));
        return matchesType && matchesSearch;
    });
    
    const listContainer = document.getElementById('entities-list');
    if (listContainer) {
        listContainer.innerHTML = renderEntitiesList(filtered);
    }
}

// Filter relations
function filterRelations() {
    const typeFilter = document.getElementById('relation-type-filter')?.value || '';
    
    const filtered = entityGraphData.relations.filter(relation => {
        return !typeFilter || relation.relation_type === typeFilter;
    });
    
    const listContainer = document.getElementById('relations-list');
    if (listContainer) {
        listContainer.innerHTML = renderRelationsList(filtered);
    }
}

// Show add entity modal
function showAddEntityModal() {
    const modal = document.createElement('div');
    modal.id = 'entity-modal';
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
    
    const currentLang = localStorage.getItem('neshama-lang') || 'zh';
    
    modal.innerHTML = `
        <div class="card" style="width: 500px; max-width: 90%;">
            <div class="card-header">
                <span class="card-title">${t('entityGraph.addEntity')}</span>
                <button class="btn btn-icon btn-secondary" onclick="closeEntityModal()">✕</button>
            </div>
            <div class="mt-4">
                <div class="form-group">
                    <label class="form-label">${t('entityGraph.entityName')}</label>
                    <input type="text" id="new-entity-name" class="form-input" placeholder="${t('entityGraph.namePlaceholder')}">
                </div>
                <div class="form-group">
                    <label class="form-label">${t('entityGraph.entityType')}</label>
                    <select id="new-entity-type" class="form-input">
                        ${ENTITY_TYPES.map(type => `<option value="${type.id}">${type.icon} ${getEntityTypeLabel(type)}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">${t('entityGraph.description')}</label>
                    <input type="text" id="new-entity-description" class="form-input" placeholder="${t('entityGraph.descriptionPlaceholder')}">
                </div>
                <div class="form-group">
                    <label class="form-label">${t('entityGraph.importance')} (0-1)</label>
                    <div class="flex items-center gap-2">
                        <input type="range" id="new-entity-importance" min="0" max="100" value="50" style="flex: 1;"
                               oninput="document.getElementById('entity-importance-value').textContent = this.value + '%'">
                        <span id="entity-importance-value" class="text-accent">50%</span>
                    </div>
                </div>
                <div class="flex gap-2 mt-4">
                    <button class="btn btn-primary" onclick="addEntity()">${t('common.add')}</button>
                    <button class="btn btn-secondary" onclick="closeEntityModal()">${t('common.cancel')}</button>
                </div>
            </div>
        </div>
    `;
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeEntityModal();
    });
    
    document.body.appendChild(modal);
}

// Close entity modal
function closeEntityModal() {
    const modal = document.getElementById('entity-modal');
    if (modal) modal.remove();
}

// Add entity
async function addEntity() {
    const name = document.getElementById('new-entity-name')?.value?.trim();
    const entityType = document.getElementById('new-entity-type')?.value;
    const description = document.getElementById('new-entity-description')?.value?.trim();
    const importance = parseInt(document.getElementById('new-entity-importance')?.value || 50) / 100;
    
    if (!name) return;
    
    try {
        await API.entityGraph.addEntity('default', name, entityType, description, importance);
        closeEntityModal();
        await renderEntityGraph();
    } catch (error) {
        console.error('Add entity error:', error);
    }
}

// Delete entity
async function deleteEntity(entityId) {
    if (!confirm(t('entityGraph.deleteConfirm'))) return;
    
    try {
        await API.entityGraph.deleteEntity('default', entityId);
        await renderEntityGraph();
    } catch (error) {
        console.error('Delete entity error:', error);
    }
}

// Show add relation modal
function showAddRelationModal() {
    if (entityGraphData.entities.length < 2) {
        alert(t('entityGraph.needMoreEntities'));
        return;
    }
    
    const modal = document.createElement('div');
    modal.id = 'relation-modal';
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
    
    const currentLang = localStorage.getItem('neshama-lang') || 'zh';
    
    modal.innerHTML = `
        <div class="card" style="width: 500px; max-width: 90%;">
            <div class="card-header">
                <span class="card-title">${t('entityGraph.addRelation')}</span>
                <button class="btn btn-icon btn-secondary" onclick="closeRelationModal()">✕</button>
            </div>
            <div class="mt-4">
                <div class="form-group">
                    <label class="form-label">${t('entityGraph.sourceEntity')}</label>
                    <select id="new-relation-source" class="form-input">
                        ${entityGraphData.entities.map(e => `<option value="${e.id}">${getEntityIcon(e.entity_type)} ${escapeHtml(e.name)}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">${t('entityGraph.relationType')}</label>
                    <select id="new-relation-type" class="form-input">
                        ${RELATION_TYPES.map(type => `<option value="${type.id}">${type.icon} ${getEntityTypeLabel(type)}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">${t('entityGraph.targetEntity')}</label>
                    <select id="new-relation-target" class="form-input">
                        ${entityGraphData.entities.map(e => `<option value="${e.id}">${getEntityIcon(e.entity_type)} ${escapeHtml(e.name)}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">${t('entityGraph.weight')} (0-1)</label>
                    <div class="flex items-center gap-2">
                        <input type="range" id="new-relation-weight" min="0" max="100" value="100" style="flex: 1;"
                               oninput="document.getElementById('relation-weight-value').textContent = this.value + '%'">
                        <span id="relation-weight-value" class="text-accent">100%</span>
                    </div>
                </div>
                <div class="flex gap-2 mt-4">
                    <button class="btn btn-primary" onclick="addRelation()">${t('common.add')}</button>
                    <button class="btn btn-secondary" onclick="closeRelationModal()">${t('common.cancel')}</button>
                </div>
            </div>
        </div>
    `;
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeRelationModal();
    });
    
    document.body.appendChild(modal);
}

// Close relation modal
function closeRelationModal() {
    const modal = document.getElementById('relation-modal');
    if (modal) modal.remove();
}

// Add relation
async function addRelation() {
    const sourceId = document.getElementById('new-relation-source')?.value;
    const targetId = document.getElementById('new-relation-target')?.value;
    const relationType = document.getElementById('new-relation-type')?.value;
    const weight = parseInt(document.getElementById('new-relation-weight')?.value || 100) / 100;
    
    if (!sourceId || !targetId || !relationType) return;
    if (sourceId === targetId) {
        alert(t('entityGraph.sameEntityError'));
        return;
    }
    
    try {
        await API.entityGraph.addRelation('default', sourceId, targetId, relationType, weight);
        closeRelationModal();
        await renderEntityGraph();
    } catch (error) {
        console.error('Add relation error:', error);
    }
}

// Delete relation
async function deleteRelation(relationId) {
    try {
        await API.entityGraph.deleteRelation('default', relationId);
        await renderEntityGraph();
    } catch (error) {
        console.error('Delete relation error:', error);
    }
}

// Find paths between entities
async function findPaths() {
    const sourceId = document.getElementById('path-source')?.value;
    const targetId = document.getElementById('path-target')?.value;
    
    if (!sourceId || !targetId) return;
    
    const resultContainer = document.getElementById('path-result');
    resultContainer.innerHTML = `<div class="loading">${t('common.loading')}</div>`;
    
    try {
        const result = await API.entityGraph.findPaths('default', sourceId, targetId);
        const paths = result.data.paths || [];
        
        if (paths.length === 0) {
            resultContainer.innerHTML = `
                <div class="empty-state" style="padding: 20px;">
                    <div class="empty-state-icon">Search</div>
                    <div class="empty-state-text">${t('entityGraph.noPathFound')}</div>
                </div>
            `;
            return;
        }
        
        resultContainer.innerHTML = `
            <div style="padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
                <div class="form-label mb-2">${t('entityGraph.pathsFound')}: ${paths.length}</div>
                ${paths.slice(0, 5).map((path, idx) => `
                    <div style="padding: 8px; background: var(--bg-card); border-radius: 6px; margin-bottom: 8px;">
                        <div class="text-muted mb-1" style="font-size: 12px;">Path ${idx + 1}</div>
                        <div class="flex items-center gap-2" style="flex-wrap: wrap;">
                            ${path.map((node, i) => {
                                const entity = node.entity;
                                const edge = node.edge;
                                const typeInfo = ENTITY_TYPES.find(t => t.id === entity.entity_type) || ENTITY_TYPES[0];
                                return `
                                    ${i > 0 ? `<span class="text-muted">→</span>` : ''}
                                    <span class="tag" style="background: ${typeInfo.color}22; color: ${typeInfo.color};">
                                        ${typeInfo.icon} ${escapeHtml(entity.name)}
                                    </span>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `).join('')}
                ${paths.length > 5 ? `<div class="text-muted text-center">...and ${paths.length - 5} more</div>` : ''}
            </div>
        `;
        
    } catch (error) {
        console.error('Find paths error:', error);
        resultContainer.innerHTML = `
            <div class="empty-state" style="padding: 20px;">
                <div class="empty-state-icon">×</div>
                <div class="empty-state-text">${t('common.error')}</div>
            </div>
        `;
    }
}

// Show entity details
async function showEntityDetails(entityId) {
    const detailsContainer = document.getElementById('entity-details');
    if (!detailsContainer) return;
    
    try {
        const result = await API.entityGraph.getEntity('default', entityId);
        const entity = result.data;
        const typeInfo = ENTITY_TYPES.find(t => t.id === entity.entity_type) || ENTITY_TYPES[0];
        
        // Get neighbors
        const neighborsResult = await API.entityGraph.getNeighbors('default', entityId);
        const neighbors = neighborsResult.data.neighbors || [];
        
        detailsContainer.innerHTML = `
            <div style="padding: 16px; background: var(--bg-tertiary); border-radius: 12px;">
                <div class="flex items-center gap-3 mb-4">
                    <span style="font-size: 48px; color: ${typeInfo.color};">${typeInfo.icon}</span>
                    <div>
                        <div style="font-size: 24px; font-weight: 600;">${escapeHtml(entity.name)}</div>
                        <div class="flex gap-2 mt-1">
                            <span class="tag" style="background: ${typeInfo.color}22; color: ${typeInfo.color};">${typeInfo.label}</span>
                            <span class="text-muted">${t('entityGraph.importance')}: ${((entity.importance || 0.5) * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                </div>
                
                ${entity.description ? `
                    <div class="mb-4">
                        <div class="form-label">${t('entityGraph.description')}</div>
                        <div>${escapeHtml(entity.description)}</div>
                    </div>
                ` : ''}
                
                <div class="mb-4">
                    <div class="form-label">${t('entityGraph.connections')} (${neighbors.length})</div>
                    ${neighbors.length > 0 ? `
                        <div class="flex gap-2" style="flex-wrap: wrap;">
                            ${neighbors.map(n => {
                                const neighborType = ENTITY_TYPES.find(t => t.id === n.entity.entity_type) || ENTITY_TYPES[0];
                                const relationType = RELATION_TYPES.find(r => r.id === n.edge.relation_type) || RELATION_TYPES[0];
                                return `
                                    <span class="tag" style="background: ${neighborType.color}22; color: ${neighborType.color};">
                                        ${relationType.icon} ${escapeHtml(n.entity.name)}
                                    </span>
                                `;
                            }).join('')}
                        </div>
                    ` : `<div class="text-muted">${t('common.noData')}</div>`}
                </div>
                
                <div class="flex gap-2">
                    <button class="btn btn-sm btn-secondary" onclick="showEditEntityModal('${entityId}')">${t('common.edit')}</button>
                    <button class="btn btn-sm btn-secondary" onclick="deleteEntity('${entityId}')">${t('common.delete')}</button>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Show entity details error:', error);
    }
}

// Show edit entity modal (simplified - same as add)
function showEditEntityModal(entityId) {
    const entity = entityGraphData.entities.find(e => e.id === entityId);
    if (!entity) return;
    
    // For now, just show a prompt
    const newName = prompt(t('entityGraph.enterNewName'), entity.name);
    if (newName && newName.trim()) {
        // Would need an update API call here
        console.log('Update entity:', entityId, newName);
    }
}

// Get entity icon
function getEntityIcon(entityType) {
    const typeInfo = ENTITY_TYPES.find(t => t.id === entityType);
    return typeInfo?.icon || 'Thought';
}

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
