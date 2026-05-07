/**
 * Chat Page - NPC Conversation Interface
 */

let chatWs = null;
let chatHistory = [];
let selectedChatNPC = null;

// Render Chat Page
async function renderChat() {
    const container = document.getElementById('page-chat');
    
    try {
        const res = await API.game.listNPCs();
        const npcs = res.data || [];
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('chat.title')}</h1>
                <p class="page-subtitle">${t('chat.subtitle')}</p>
            </div>
            
            <div class="chat-layout">
                <!-- NPC List Sidebar -->
                <div class="chat-sidebar">
                    <div class="chat-sidebar-header">
                        <span>${t('nav.npcManagement')}</span>
                    </div>
                    <div class="chat-npc-list">
                        ${npcs.map(npc => `
                            <div class="chat-npc-item ${selectedChatNPC === npc.id ? 'active' : ''}" 
                                onclick="selectChatNPC('${npc.id}')">
                                <span class="npc-avatar-chat">${npc.avatar || '🎭'}</span>
                                <div class="npc-info">
                                    <span class="npc-name">${escapeHtml(npc.name)}</span>
                                    <span class="npc-emotion-tag">
                                        ${npc.emotion?.primary?.emoji || '😐'}
                                        ${npc.emotion?.primary?.category || ''}
                                    </span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- Chat Area -->
                <div class="chat-main">
                    ${selectedChatNPC ? renderChatArea() : renderChatPlaceholder()}
                </div>
            </div>
        `;
        
        // Load chat history if NPC is selected
        if (selectedChatNPC) {
            await loadChatHistory();
        }
        
    } catch (error) {
        console.error('Failed to load chat page:', error);
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('chat.title')}</h1>
            </div>
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <div class="empty-state-text">${t('chat.loadFailed')}</div>
                <button class="btn btn-primary mt-4" onclick="renderChat()">${t('common.retry')}</button>
            </div>
        `;
    }
}

// Render Chat Placeholder
function renderChatPlaceholder() {
    return `
        <div class="chat-placeholder">
            <div class="placeholder-icon">💬</div>
            <div class="placeholder-text">${t('chat.startConversation')}</div>
            <div class="placeholder-hint">${t('chat.selectNPC') || 'Select an NPC from the list to start chatting'}</div>
        </div>
    `;
}

// Render Chat Area
function renderChatArea() {
    return `
        <div class="card" style="height: calc(100vh - 200px); display: flex; flex-direction: column;">
            <div class="card-header" style="flex-shrink: 0;">
                <span class="card-title">${t('npcDetail.chatWith')}</span>
                <div class="flex gap-2">
                    <button class="btn btn-sm btn-secondary" onclick="clearChat()">${t('common.clear')}</button>
                    <button class="btn btn-sm btn-secondary" onclick="loadChatHistory()">${t('common.refresh')}</button>
                </div>
            </div>
            
            <div id="chat-messages" style="flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px;">
                <div class="loading">${t('chat.connecting')}</div>
            </div>
            
            <div id="chat-event-panel" class="chat-event-panel">
                <span class="panel-label">${t('npcDetail.sendGameEvent')}</span>
                <div class="event-quick-btns">
                    <button class="btn btn-sm btn-secondary" onclick="quickSendEvent('gift')">🎁</button>
                    <button class="btn btn-sm btn-secondary" onclick="quickSendEvent('compliment')">✨</button>
                    <button class="btn btn-sm btn-secondary" onclick="quickSendEvent('attack')">⚔️</button>
                    <button class="btn btn-sm btn-secondary" onclick="quickSendEvent('help')">🤝</button>
                </div>
            </div>
            
            <div style="padding: 16px; border-top: 1px solid var(--border-color); flex-shrink: 0;">
                <div class="flex gap-3">
                    <input type="text" id="chat-input" class="form-input" placeholder="${t('chat.typeMessage')}" 
                        style="flex: 1;" onkeypress="handleChatKeypress(event)">
                    <button class="btn btn-primary" onclick="sendChatMessage()">${t('chat.send')}</button>
                </div>
            </div>
        </div>
    `;
}

// Select Chat NPC
function selectChatNPC(npcId) {
    selectedChatNPC = npcId;
    renderChat();
}

// Load Chat History
async function loadChatHistory() {
    if (!selectedChatNPC) return;
    
    try {
        const res = await API.game.getChatHistory(selectedChatNPC);
        chatHistory = res.data || [];
        renderChatHistory();
    } catch (error) {
        console.error('Failed to load chat history:', error);
        showToast(t('chat.loadFailed'), 'error');
    }
}

// Render Chat History
function renderChatHistory() {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    if (chatHistory.length === 0) {
        messagesContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <div class="empty-state-text">${t('chat.startConversation')}</div>
            </div>
        `;
        return;
    }
    
    messagesContainer.innerHTML = chatHistory.map(msg => createMessageHTML(msg)).join('');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Create Message HTML
function createMessageHTML(msg) {
    const isUser = msg.role === 'user';
    const time = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : '';
    
    return `
        <div class="flex ${isUser ? 'justify-end' : ''}" style="max-width: 80%; ${isUser ? 'align-self: flex-end;' : 'align-self: flex-start;'}">
            <div style="padding: 12px 16px; border-radius: 16px; ${isUser ? 
                'background: var(--accent-primary); color: white; border-bottom-right-radius: 4px;' : 
                'background: var(--bg-tertiary); border-bottom-left-radius: 4px;'}">
                <div style="margin-bottom: 4px;">${escapeHtml(msg.content)}</div>
                ${msg.emotion ? `<div class="msg-emotion">${msg.emotion}</div>` : ''}
                <div style="font-size: 10px; opacity: 0.7; text-align: right;">${time}</div>
            </div>
        </div>
    `;
}

// Send Chat Message
async function sendChatMessage() {
    if (!selectedChatNPC) return;
    
    const input = document.getElementById('chat-input');
    const message = input?.value.trim();
    
    if (!message) return;
    
    try {
        const res = await API.game.chat(selectedChatNPC, message);
        
        if (res.data) {
            // Add user message to history
            chatHistory.push({
                role: 'user',
                content: message,
                timestamp: new Date().toISOString()
            });
            
            // Add NPC response to history
            chatHistory.push({
                role: 'assistant',
                content: res.data.content,
                timestamp: new Date().toISOString(),
                emotion: res.data.emotion
            });
            
            // Clear input
            input.value = '';
            
            // Update display
            renderChatHistory();
            
            // Update NPC emotion tag
            if (res.data.emotion) {
                updateNPCEmotionTag(res.data.emotion);
            }
        }
    } catch (error) {
        console.error('Send message failed:', error);
        showToast(t('common.error'), 'error');
    }
}

// Quick Send Event
async function quickSendEvent(eventType) {
    if (!selectedChatNPC) return;
    
    try {
        await API.game.sendEvent(selectedChatNPC, eventType, 0.5);
        showToast(`${t(`event.${eventType}`)} event sent`, 'success');
        
        // Refresh to show new emotion
        await loadChatHistory();
    } catch (error) {
        console.error('Quick send event failed:', error);
        showToast(t('common.error'), 'error');
    }
}

// Update NPC Emotion Tag
function updateNPCEmotionTag(emotion) {
    const tag = document.querySelector(`.chat-npc-item[data-npc-id="${selectedChatNPC}"] .npc-emotion-tag`);
    if (tag && emotion) {
        tag.textContent = emotion;
    }
}

// Handle Chat Keypress
function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

// Clear Chat
async function clearChat() {
    if (!selectedChatNPC) return;
    
    chatHistory = [];
    renderChatHistory();
    showToast(t('chat.cleared'), 'success');
}

// Helper: Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
