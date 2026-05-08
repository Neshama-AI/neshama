/**
 * Welcome Page - First-time user onboarding
 */

// Welcome page state
let welcomeState = {
    currentStep: 0,
    totalSteps: 3,
    provider: null,
    apiKey: null,
    personality: null,
    theme: 'ocean'
};

/**
 * Render the welcome page
 */
function renderWelcome() {
    const container = document.getElementById('page-welcome');
    if (!container) return;

    welcomeState.currentStep = 0;
    
    container.innerHTML = `
        <div class="welcome-container">
            <div class="welcome-header">
                <div class="welcome-logo">NS</div>
                <h1 class="welcome-title">${t('welcome.title')}</h1>
                <p class="welcome-subtitle">${t('welcome.subtitle')}</p>
            </div>
            
            <div class="welcome-progress">
                <div class="progress-step ${welcomeState.currentStep >= 0 ? 'active' : ''}" data-step="0">
                    <div class="step-number">1</div>
                    <div class="step-label">${t('welcome.step1')}</div>
                </div>
                <div class="progress-line"></div>
                <div class="progress-step ${welcomeState.currentStep >= 1 ? 'active' : ''}" data-step="1">
                    <div class="step-number">2</div>
                    <div class="step-label">${t('welcome.step2')}</div>
                </div>
                <div class="progress-line"></div>
                <div class="progress-step ${welcomeState.currentStep >= 2 ? 'active' : ''}" data-step="2">
                    <div class="step-number">3</div>
                    <div class="step-label">${t('welcome.step3')}</div>
                </div>
            </div>
            
            <div class="welcome-content" id="welcome-content">
                <!-- Step content loaded dynamically -->
            </div>
            
            <div class="welcome-footer">
                <button class="btn btn-secondary" id="welcome-skip" onclick="skipWelcome()">
                    ${t('welcome.skip')}
                </button>
                <button class="btn btn-primary" id="welcome-next" onclick="nextWelcomeStep()">
                    ${t('welcome.next')}
                </button>
            </div>
        </div>
    `;
    
    // Load first step
    loadWelcomeStep(0);
}

/**
 * Load a specific welcome step
 */
async function loadWelcomeStep(stepIndex) {
    const content = document.getElementById('welcome-content');
    const nextBtn = document.getElementById('welcome-next');
    
    switch(stepIndex) {
        case 0:
            // Step 1: Configure LLM Provider
            content.innerHTML = renderWelcomeStep1();
            nextBtn.textContent = t('welcome.next');
            nextBtn.onclick = () => nextWelcomeStep();
            break;
            
        case 1:
            // Step 2: Choose Personality Template
            content.innerHTML = await renderWelcomeStep2();
            nextBtn.textContent = t('welcome.next');
            nextBtn.onclick = () => nextWelcomeStep();
            break;
            
        case 2:
            // Step 3: Start chatting
            content.innerHTML = renderWelcomeStep3();
            nextBtn.textContent = t('welcome.start');
            nextBtn.onclick = () => completeWelcome();
            break;
    }
    
    // Update progress
    document.querySelectorAll('.progress-step').forEach((el, i) => {
        el.classList.toggle('active', i <= stepIndex);
    });
    
    welcomeState.currentStep = stepIndex;
}

/**
 * Render Step 1: Configure LLM Provider
 */
function renderWelcomeStep1() {
    const providers = [
        { id: 'openai', name: 'OpenAI', icon: 'AI', models: ['gpt-4', 'gpt-3.5-turbo'] },
        { id: 'anthropic', name: 'Anthropic Claude', icon: 'Brain', models: ['claude-3-opus', 'claude-3-sonnet'] },
        { id: 'gemini', name: 'Google Gemini', icon: 'Sparkle', models: ['gemini-pro', 'gemini-flash'] },
        { id: 'dashscope', name: 'DashScope (Qwen)', icon: 'OCEAN', models: ['qwen-turbo', 'qwen-plus'] },
        { id: 'zhipu', name: 'Zhipu GLM', icon: 'Docs', models: ['glm-4', 'glm-3-turbo'] },
        { id: 'deepseek', name: 'DeepSeek', icon: 'NS', models: ['deepseek-chat', 'deepseek-coder'] },
        { id: 'moonshot', name: 'Moonshot (Kimi)', icon: 'Moon', models: ['moonshot-v1-8k', 'moonshot-v1-32k'] }
    ];
    
    return `
        <div class="welcome-step">
            <h2 class="step-title">${t('welcome.step1Title')}</h2>
            <p class="step-description">${t('welcome.step1Desc')}</p>
            
            <div class="provider-grid">
                ${providers.map(p => `
                    <div class="provider-card ${welcomeState.provider === p.id ? 'selected' : ''}" 
                         data-provider="${p.id}"
                         onclick="selectProvider('${p.id}')">
                        <div class="provider-icon">${p.icon}</div>
                        <div class="provider-name">${p.name}</div>
                    </div>
                `).join('')}
            </div>
            
            <div class="api-key-section" id="api-key-section" style="display: ${welcomeState.provider ? 'block' : 'none'}">
                <label class="form-label">${t('welcome.apiKey')}</label>
                <input type="password" 
                       id="welcome-api-key" 
                       class="form-input" 
                       placeholder="sk-..."
                       value="${welcomeState.apiKey || ''}"
                       onchange="welcomeState.apiKey = this.value">
            </div>
        </div>
    `;
}

/**
 * Select a provider
 */
function selectProvider(providerId) {
    welcomeState.provider = providerId;
    
    // Update UI
    document.querySelectorAll('.provider-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.provider === providerId);
    });
    
    // Show API key section
    document.getElementById('api-key-section').style.display = 'block';
}

/**
 * Render Step 2: Choose Personality Template
 */
async function renderWelcomeStep2() {
    // Get presets from the backend
    let presets = [
        { id: 'neshama', name: 'Neshama', desc: 'Balanced, helpful companion' },
        { id: 'analyst', name: 'Analyst', desc: 'Logical, data-driven thinker' },
        { id: 'creative', name: 'Creative', desc: 'Imaginative, artistic soul' },
        { id: 'counselor', name: 'Counselor', desc: 'Empathetic, supportive friend' },
        { id: 'explorer', name: 'Explorer', desc: 'Curious, adventure-seeking' }
    ];
    
    try {
        const res = await API.ocean.getPresets();
        if (res.data && res.data.length > 0) {
            presets = res.data.map(p => ({
                id: p.id || p,
                name: p.name || p,
                desc: p.description || ''
            }));
        }
    } catch (e) {
        console.log('Using default presets');
    }
    
    return `
        <div class="welcome-step">
            <h2 class="step-title">${t('welcome.step2Title')}</h2>
            <p class="step-description">${t('welcome.step2Desc')}</p>
            
            <div class="personality-grid">
                ${presets.map(p => `
                    <div class="personality-card ${welcomeState.personality === p.id ? 'selected' : ''}"
                         data-personality="${p.id}"
                         onclick="selectPersonality('${p.id}')">
                        <div class="personality-icon">${getPersonalityIcon(p.id)}</div>
                        <div class="personality-name">${p.name}</div>
                        <div class="personality-desc">${p.desc}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * Get personality icon
 */
function getPersonalityIcon(presetId) {
    const icons = {
        'neshama': 'NS',
        'analyst': 'Stats',
        'creative': 'Art',
        'counselor': 'Heart',
        'explorer': 'Compass',
        'default': 'Sparkle'
    };
    return icons[presetId] || icons['default'];
}

/**
 * Select personality
 */
function selectPersonality(presetId) {
    welcomeState.personality = presetId;
    
    // Update UI
    document.querySelectorAll('.personality-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.personality === presetId);
    });
}

/**
 * Render Step 3: Start Chatting
 */
function renderWelcomeStep3() {
    return `
        <div class="welcome-step">
            <h2 class="step-title">${t('welcome.step3Title')}</h2>
            <p class="step-description">${t('welcome.step3Desc')}</p>
            
            <div class="start-options">
                <div class="start-option" onclick="completeWelcome('dashboard')">
                    <div class="option-icon">Stats</div>
                    <div class="option-title">${t('welcome.openDashboard')}</div>
                    <div class="option-desc">${t('welcome.openDashboardDesc')}</div>
                </div>
                
                <div class="start-option" onclick="completeWelcome('chat')">
                    <div class="option-icon">Chat</div>
                    <div class="option-title">${t('welcome.startChat')}</div>
                    <div class="option-desc">${t('welcome.startChatDesc')}</div>
                </div>
            </div>
            
            <div class="theme-preview">
                <h3>${t('welcome.previewTheme')}</h3>
                <div class="theme-options">
                    <div class="theme-option ${welcomeState.theme === 'ocean' ? 'selected' : ''}" onclick="welcomeState.theme = 'ocean'; renderWelcomeStep3();">
                        OCEAN Ocean
                    </div>
                    <div class="theme-option ${welcomeState.theme === 'midnight' ? 'selected' : ''}" onclick="welcomeState.theme = 'midnight'; renderWelcomeStep3();">
                        Moon Midnight
                    </div>
                    <div class="theme-option ${welcomeState.theme === 'cyberpunk' ? 'selected' : ''}" onclick="welcomeState.theme = 'cyberpunk'; renderWelcomeStep3();">
                        AI Cyberpunk
                    </div>
                    <div class="theme-option ${welcomeState.theme === 'sunset' ? 'selected' : ''}" onclick="welcomeState.theme = 'sunset'; renderWelcomeStep3();">
                        Sunset Sunset
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Go to next step
 */
function nextWelcomeStep() {
    // Validate current step
    if (welcomeState.currentStep === 0) {
        if (!welcomeState.provider) {
            alert(t('welcome.selectProvider'));
            return;
        }
        if (!welcomeState.apiKey) {
            alert(t('welcome.enterApiKey'));
            return;
        }
    }
    
    if (welcomeState.currentStep === 1) {
        if (!welcomeState.personality) {
            welcomeState.personality = 'neshama'; // Default
        }
    }
    
    if (welcomeState.currentStep < welcomeState.totalSteps - 1) {
        loadWelcomeStep(welcomeState.currentStep + 1);
    }
}

/**
 * Skip welcome
 */
function skipWelcome() {
    completeWelcome('dashboard');
}

/**
 * Complete welcome flow
 */
async function completeWelcome(target = 'dashboard') {
    // Save configuration
    try {
        await API.config.update({
            model: {
                provider: welcomeState.provider,
                apiKey: welcomeState.apiKey
            },
            theme: welcomeState.theme,
            personality: welcomeState.personality
        });
    } catch (e) {
        console.log('Config save skipped');
    }
    
    // Mark welcome as completed
    localStorage.setItem('neshama_welcome_completed', 'true');
    localStorage.setItem('neshama_theme', welcomeState.theme);
    
    // Apply theme
    if (window.ThemeManager) {
        window.ThemeManager.setTheme(welcomeState.theme);
    }
    
    // Navigate to target
    if (target === 'chat') {
        navigateTo('chat');
    } else {
        navigateTo('dashboard');
    }
}

/**
 * Check if welcome is needed
 */
function needsWelcome() {
    // Demo page doesn't need welcome - skip onboarding for demo visitors
    const hash = window.location.hash.replace('#', '');
    if (hash === 'demo') return false;
    const completed = localStorage.getItem('neshama_welcome_completed');
    return completed !== 'true';
}

/**
 * Render welcome in modal (for first-time users)
 */
function renderWelcomeInModal(container) {
    welcomeState.currentStep = 0;
    
    container.innerHTML = `
        <div class="welcome-container">
            <div class="welcome-header">
                <div class="welcome-logo">NS</div>
                <h1 class="welcome-title">${t('welcome.title')}</h1>
                <p class="welcome-subtitle">${t('welcome.subtitle')}</p>
            </div>
            
            <div class="welcome-progress">
                <div class="progress-step active" data-step="0">
                    <div class="step-number">1</div>
                    <div class="step-label">${t('welcome.step1')}</div>
                </div>
                <div class="progress-line"></div>
                <div class="progress-step" data-step="1">
                    <div class="step-number">2</div>
                    <div class="step-label">${t('welcome.step2')}</div>
                </div>
                <div class="progress-line"></div>
                <div class="progress-step" data-step="2">
                    <div class="step-number">3</div>
                    <div class="step-label">${t('welcome.step3')}</div>
                </div>
            </div>
            
            <div class="welcome-content" id="welcome-content">
                <!-- Step content loaded dynamically -->
            </div>
            
            <div class="welcome-footer">
                <button class="btn btn-secondary" id="welcome-skip" onclick="skipWelcomeModal()">
                    ${t('welcome.skip')}
                </button>
                <button class="btn btn-primary" id="welcome-next" onclick="nextWelcomeModalStep()">
                    ${t('welcome.next')}
                </button>
            </div>
        </div>
    `;
    
    // Load first step
    loadWelcomeModalStep(0);
}

/**
 * Load a specific welcome step in modal
 */
async function loadWelcomeModalStep(stepIndex) {
    const content = document.getElementById('welcome-content');
    const nextBtn = document.getElementById('welcome-next');
    const skipBtn = document.getElementById('welcome-skip');
    
    switch(stepIndex) {
        case 0:
            content.innerHTML = renderWelcomeStep1();
            nextBtn.textContent = t('welcome.next');
            nextBtn.onclick = () => nextWelcomeModalStep();
            skipBtn.style.display = 'none';
            break;
            
        case 1:
            content.innerHTML = await renderWelcomeStep2();
            nextBtn.textContent = t('welcome.next');
            nextBtn.onclick = () => nextWelcomeModalStep();
            skipBtn.style.display = 'inline-block';
            break;
            
        case 2:
            content.innerHTML = renderWelcomeStep3();
            nextBtn.textContent = t('welcome.start');
            nextBtn.onclick = () => completeWelcomeModal();
            skipBtn.style.display = 'inline-block';
            break;
    }
    
    // Update progress
    document.querySelectorAll('.progress-step').forEach((el, i) => {
        el.classList.toggle('active', i <= stepIndex);
    });
    
    welcomeState.currentStep = stepIndex;
}

/**
 * Go to next step in modal
 */
function nextWelcomeModalStep() {
    if (welcomeState.currentStep === 0) {
        if (!welcomeState.provider) {
            alert(t('welcome.selectProvider'));
            return;
        }
        if (!welcomeState.apiKey) {
            welcomeState.apiKey = document.getElementById('welcome-api-key')?.value || '';
            if (!welcomeState.apiKey) {
                alert(t('welcome.enterApiKey'));
                return;
            }
        }
    }
    
    if (welcomeState.currentStep === 1) {
        if (!welcomeState.personality) {
            welcomeState.personality = 'neshama';
        }
    }
    
    if (welcomeState.currentStep < welcomeState.totalSteps - 1) {
        loadWelcomeModalStep(welcomeState.currentStep + 1);
    }
}

/**
 * Skip welcome in modal
 */
function skipWelcomeModal() {
    completeWelcomeModal();
}

/**
 * Complete welcome flow in modal
 */
async function completeWelcomeModal() {
    // Save configuration
    try {
        await API.config.update({
            model: {
                provider: welcomeState.provider || 'openai',
                apiKey: welcomeState.apiKey || ''
            },
            theme: welcomeState.theme,
            personality: welcomeState.personality || 'neshama'
        });
    } catch (e) {
        console.log('Config save skipped');
    }
    
    // Mark welcome as completed
    localStorage.setItem('neshama_welcome_completed', 'true');
    localStorage.setItem('neshama_theme', welcomeState.theme);
    
    // Apply theme
    if (window.ThemeManager) {
        window.ThemeManager.setTheme(welcomeState.theme);
    }
    
    // Hide modal and navigate to dashboard
    const modal = document.getElementById('welcome-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    // Navigate to dashboard
    router.navigate('dashboard');
}
