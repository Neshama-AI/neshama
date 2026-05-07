/**
 * Neshama - Main Application
 * NPC Soul OS - Simplified Router
 */

// Application State
const AppState = {
    currentPage: 'dashboard',
    soulConfig: null,
    emotionData: null,
    memoryData: null,
    chatHistory: [],
    websocket: null,
    npcs: [],
    selectedNPC: null,
    npcDetail: null,
    accountInfo: null,
    billingInfo: null
};

// Router
class Router {
    constructor() {
        this.pages = {};
        this.init();
    }
    
    init() {
        // Register pages - 7 pages
        this.pages = {
            'dashboard': { title: t('nav.dashboard'), render: typeof renderDashboard === 'function' ? renderDashboard : (() => {}) },
            'account': { title: t('nav.account'), render: typeof renderAccount === 'function' ? renderAccount : (() => {}) },
            'billing': { title: t('nav.billing'), render: typeof renderBilling === 'function' ? renderBilling : (() => {}) },
            'templates': { title: t('nav.templates'), render: typeof renderTemplates === 'function' ? renderTemplates : (() => {}) },
            'debug': { title: t('nav.debug'), render: typeof renderDebug === 'function' ? renderDebug : (() => {}) },
            'demo': { title: t('nav.demo'), render: typeof renderDemo === 'function' ? renderDemo : (() => {}) },
            'register': { title: t('nav.register'), render: typeof renderRegister === 'function' ? renderRegister : (() => {}) }
        };
        
        // Bind navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                this.navigate(page);
            });
        });
        
        // Handle hash-based navigation
        const handleHash = () => {
            const hash = window.location.hash.replace('#', '');
            if (hash && this.pages[hash]) {
                this.navigate(hash);
                return true;
            }
            return false;
        };
        
        window.addEventListener('hashchange', handleHash);
        
        // Navigate to the correct page (hash route or dashboard)
        if (!handleHash()) {
            this.navigate('dashboard');
        }
        
        // Start data refresh loop
        this.startDataRefresh();
    }
    
    navigate(page) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });
        
        // Update pages
        document.querySelectorAll('.page').forEach(p => {
            p.classList.toggle('active', p.id === `page-${page}`);
        });
        
        // Update state
        AppState.currentPage = page;
        
        // Update hash
        window.location.hash = page;
        
        // Render page
        if (this.pages[page]) {
            this.pages[page].render();
        }
    }
    
    startDataRefresh() {
        // Refresh dashboard data every 30 seconds
        setInterval(async () => {
            if (AppState.currentPage === 'dashboard') {
                await refreshDashboardData();
            }
        }, 30000);
    }
}

// Initialize router
const router = new Router();

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function animateValue(element, start, end, duration) {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = start + (end - start) * easeOutQuad(progress);
        element.textContent = current.toFixed(2);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function easeOutQuad(x) {
    return 1 - (1 - x) * (1 - x);
}

// Escape HTML helper
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Toast notification system
class Toast {
    static show(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container') || (() => {
            const c = document.createElement('div');
            c.id = 'toast-container';
            c.style.cssText = 'position:fixed;top:20px;right:20px;z-index:10000;display:flex;flex-direction:column;gap:8px;';
            document.body.appendChild(c);
            return c;
        })();
        
        const toast = document.createElement('div');
        const colors = {
            info: 'var(--accent-primary)',
            success: '#22C55E',
            error: '#EF4444',
            warning: '#F59E0B'
        };
        
        toast.style.cssText = `
            padding: 12px 20px;
            border-radius: 8px;
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            border-left: 3px solid ${colors[type] || colors.info};
            color: var(--text-primary);
            font-size: 14px;
            box-shadow: var(--shadow-md);
            animation: fadeInUp 0.3s ease;
            max-width: 360px;
        `;
        toast.textContent = message;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

window.Toast = Toast;

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        Toast.show(t('common.copied') || 'Copied!', 'success');
        return true;
    } catch (err) {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        Toast.show(t('common.copied') || 'Copied!', 'success');
        return true;
    }
}

window.copyToClipboard = copyToClipboard;
