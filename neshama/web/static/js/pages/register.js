/**
 * Neshama - Register / Login Page
 * Registration, login, and trial mode for cloud-hosted Neshama
 */

// ── State ──────────────────────────────────────────────────────────────────────

let registerState = {
    mode: 'login', // 'login' | 'register' | 'trial' | 'success'
    loading: false,
    apiKey: '',
    userId: '',
    trialToken: '',
    error: ''
};

// ── Render ─────────────────────────────────────────────────────────────────────

function renderRegister() {
    const container = document.getElementById('page-register');
    if (!container) return;

    if (registerState.mode === 'success') {
        container.innerHTML = renderSuccessView();
        return;
    }

    container.innerHTML = `
        <div class="register-container">
            <div class="register-card">
                <div class="register-header">
                    <div class="register-logo">🔮</div>
                    <h1 class="register-title">${t('register.welcome')}</h1>
                    <p class="register-subtitle">${t('register.subtitle')}</p>
                </div>

                ${registerState.error ? `
                    <div class="register-error">
                        <span class="error-icon">⚠️</span>
                        ${registerState.error}
                    </div>
                ` : ''}

                ${registerState.mode === 'trial' ? renderTrialView() : renderAuthForm()}

                <div class="register-divider">
                    <span>${t('register.or')}</span>
                </div>

                ${registerState.mode !== 'trial' ? `
                    <button class="register-btn register-btn-trial" onclick="startTrial()" ${registerState.loading ? 'disabled' : ''}>
                        🚀 ${t('register.trialButton')}
                    </button>
                    <p class="register-hint">${t('register.trialHint')}</p>
                ` : `
                    <button class="register-btn register-btn-secondary" onclick="switchMode('login')" ${registerState.loading ? 'disabled' : ''}>
                        ← ${t('register.backToLogin')}
                    </button>
                `}
            </div>
        </div>
    `;
}

function renderAuthForm() {
    const isRegister = registerState.mode === 'register';

    return `
        <form class="register-form" onsubmit="handleAuth(event)">
            ${isRegister ? `
                <div class="register-field">
                    <label class="register-label">${t('register.name')}</label>
                    <input type="text" id="reg-name" class="register-input" 
                           placeholder="${t('register.namePlaceholder')}" required 
                           minlength="1" maxlength="50">
                </div>
            ` : ''}
            <div class="register-field">
                <label class="register-label">${t('register.email')}</label>
                <input type="email" id="reg-email" class="register-input" 
                       placeholder="${t('register.emailPlaceholder')}" required>
            </div>
            <div class="register-field">
                <label class="register-label">${t('register.password')}</label>
                <input type="password" id="reg-password" class="register-input" 
                       placeholder="${t('register.passwordPlaceholder')}" required 
                       minlength="6">
            </div>
            <button type="submit" class="register-btn register-btn-primary" ${registerState.loading ? 'disabled' : ''}>
                ${registerState.loading ? t('register.loading') : (isRegister ? t('register.registerButton') : t('register.loginButton'))}
            </button>
        </form>

        <div class="register-switch">
            ${isRegister ? `
                ${t('register.hasAccount')} 
                <a href="#" onclick="switchMode('login')">${t('register.loginLink')}</a>
            ` : `
                ${t('register.noAccount')} 
                <a href="#" onclick="switchMode('register')">${t('register.registerLink')}</a>
            `}
        </div>

        <div class="register-apikey-section">
            <div class="register-divider" style="margin-top:16px">
                <span>${t('register.or')}</span>
            </div>
            <div class="register-field" style="margin-top:16px">
                <label class="register-label">${t('register.apiKeyLabel')}</label>
                <div class="register-apikey-row">
                    <input type="text" id="reg-apikey" class="register-input" 
                           placeholder="nsk_xxxxxxxxxxxxxxxx">
                    <button class="register-btn register-btn-small" onclick="handleApiKeyLogin()">
                        ${t('register.connectButton')}
                    </button>
                </div>
            </div>
        </div>
    `;
}

function renderTrialView() {
    return `
        <div class="register-trial-info">
            <div class="trial-icon">🎮</div>
            <h3>${t('register.trialTitle')}</h3>
            <ul class="trial-features">
                <li>✅ ${t('register.trialFeature1')}</li>
                <li>✅ ${t('register.trialFeature2')}</li>
                <li>✅ ${t('register.trialFeature3')}</li>
                <li>✅ ${t('register.trialFeature4')}</li>
            </ul>
        </div>
        <button class="register-btn register-btn-trial" onclick="startTrial()" ${registerState.loading ? 'disabled' : ''}>
            🚀 ${t('register.startTrialButton')}
        </button>
    `;
}

function renderSuccessView() {
    const isTrial = !registerState.apiKey;
    const token = isTrial ? registerState.trialToken : registerState.apiKey;

    return `
        <div class="register-container">
            <div class="register-card register-success-card">
                <div class="success-icon">🎉</div>
                <h1 class="register-title">${t('register.successTitle')}</h1>
                <p class="register-subtitle">${t('register.successSubtitle')}</p>

                <div class="success-apikey-box">
                    <label class="register-label">${isTrial ? t('register.trialTokenLabel') : t('register.apiKeyLabel')}</label>
                    <div class="success-apikey-row">
                        <code class="success-apikey" id="success-token">${token}</code>
                        <button class="register-btn register-btn-small" onclick="copyToken()">
                            📋 ${t('register.copyButton')}
                        </button>
                    </div>
                    ${isTrial ? `<p class="success-hint">${t('register.trialExpiryHint')}</p>` : ''}
                </div>

                <div class="success-steps">
                    <h3>${t('register.quickStart')}</h3>
                    <div class="success-step">
                        <span class="step-number">1</span>
                        <span>${t('register.step1')}</span>
                    </div>
                    <div class="success-step">
                        <span class="step-number">2</span>
                        <span>${t('register.step2')}</span>
                    </div>
                    <div class="success-step">
                        <span class="step-number">3</span>
                        <span>${t('register.step3')}</span>
                    </div>
                </div>

                <button class="register-btn register-btn-primary" onclick="goToDashboard()">
                    ${t('register.goDashboard')} →
                </button>
            </div>
        </div>
    `;
}

// ── Actions ────────────────────────────────────────────────────────────────────

async function handleAuth(event) {
    event.preventDefault();
    registerState.loading = true;
    registerState.error = '';
    renderRegister();

    try {
        const isRegister = registerState.mode === 'register';
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const name = isRegister ? document.getElementById('reg-name').value : '';

        const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
        const body = isRegister ? { email, password, name } : { email, password };

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        const data = await response.json();

        if (!response.ok) {
            registerState.error = data.detail || t('register.errorGeneric');
            registerState.loading = false;
            renderRegister();
            return;
        }

        // Success
        registerState.apiKey = data.api_key;
        registerState.userId = data.user_id;
        registerState.loading = false;
        registerState.mode = 'success';

        // Store in localStorage
        localStorage.setItem('neshama_api_key', data.api_key);
        localStorage.setItem('neshama_user_id', data.user_id);
        localStorage.setItem('neshama_tier', data.tier);
        if (data.token) {
            localStorage.setItem('neshama_token', data.token);
        }

        renderRegister();
    } catch (err) {
        registerState.error = t('register.errorNetwork');
        registerState.loading = false;
        renderRegister();
    }
}

async function handleApiKeyLogin() {
    const apiKey = document.getElementById('reg-apikey').value.trim();
    if (!apiKey) return;

    registerState.loading = true;
    registerState.error = '';
    renderRegister();

    try {
        const response = await fetch('/api/auth/me', {
            headers: { 'Authorization': `Bearer ${apiKey}` },
        });

        if (!response.ok) {
            registerState.error = t('register.errorInvalidKey');
            registerState.loading = false;
            renderRegister();
            return;
        }

        const data = await response.json();
        registerState.apiKey = apiKey;
        registerState.userId = data.user_id;
        registerState.loading = false;
        registerState.mode = 'success';

        localStorage.setItem('neshama_api_key', apiKey);
        localStorage.setItem('neshama_user_id', data.user_id);
        localStorage.setItem('neshama_tier', data.tier);

        renderRegister();
    } catch (err) {
        registerState.error = t('register.errorNetwork');
        registerState.loading = false;
        renderRegister();
    }
}

async function startTrial() {
    registerState.loading = true;
    registerState.error = '';
    renderRegister();

    try {
        const response = await fetch('/api/auth/trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        const data = await response.json();

        if (!response.ok) {
            registerState.error = data.detail || t('register.errorTrial');
            registerState.loading = false;
            renderRegister();
            return;
        }

        registerState.trialToken = data.trial_token;
        registerState.loading = false;
        registerState.mode = 'success';

        localStorage.setItem('neshama_trial_token', data.trial_token);
        localStorage.setItem('neshama_trial_remaining', data.remaining_conversations);
        localStorage.setItem('neshama_mode', 'trial');

        renderRegister();
    } catch (err) {
        registerState.error = t('register.errorNetwork');
        registerState.loading = false;
        renderRegister();
    }
}

function switchMode(mode) {
    registerState.mode = mode;
    registerState.error = '';
    renderRegister();
}

function copyToken() {
    const token = document.getElementById('success-token');
    if (token) {
        navigator.clipboard.writeText(token.textContent).then(() => {
            const btn = event.target;
            btn.textContent = '✅';
            setTimeout(() => btn.textContent = '📋 ' + t('register.copyButton'), 1500);
        });
    }
}

function goToDashboard() {
    // Navigate to dashboard page
    if (typeof navigateTo === 'function') {
        navigateTo('dashboard');
    } else {
        window.location.hash = 'dashboard';
    }
}
