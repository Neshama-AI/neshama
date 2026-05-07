/**
 * Neshama Soul Panel - Theme Manager
 * Handles theme switching with localStorage persistence
 * 8 switchable themes inspired by OpenClaw/QClaw design
 */

// Available themes with metadata
const THEMES = {
    ocean: {
        id: 'ocean',
        name: 'Ocean',
        nameZh: '海洋',
        emoji: '🌊',
        isDark: true
    },
    spring: {
        id: 'spring',
        name: 'Spring',
        nameZh: '春日',
        emoji: '🌸',
        isDark: false
    },
    midnight: {
        id: 'midnight',
        name: 'Midnight',
        nameZh: '午夜',
        emoji: '🌙',
        isDark: true
    },
    cyberpunk: {
        id: 'cyberpunk',
        name: 'Cyberpunk',
        nameZh: '赛博',
        emoji: '🤖',
        isDark: true
    },
    sunset: {
        id: 'sunset',
        name: 'Sunset',
        nameZh: '黄昏',
        emoji: '🌅',
        isDark: true
    },
    forest: {
        id: 'forest',
        name: 'Forest',
        nameZh: '森林',
        emoji: '🌲',
        isDark: true
    },
    slate: {
        id: 'slate',
        name: 'Slate',
        nameZh: '岩石',
        emoji: '🗿',
        isDark: true
    },
    purple: {
        id: 'purple',
        name: 'Purple Haze',
        nameZh: '紫雾',
        emoji: '💜',
        isDark: true
    }
};

// Storage key
const THEME_STORAGE_KEY = 'neshama-theme';

/**
 * Initialize theme system
 * Load saved theme or use default (ocean)
 */
function initTheme() {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    const themeToApply = savedTheme && THEMES[savedTheme] ? savedTheme : 'ocean';
    setTheme(themeToApply, false); // Don't save again (already saved)
}

/**
 * Get current theme ID
 */
function getCurrentTheme() {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    return savedTheme && THEMES[savedTheme] ? savedTheme : 'ocean';
}

/**
 * Set theme and apply to document
 * @param {string} themeId - Theme identifier
 * @param {boolean} save - Whether to save to localStorage
 */
function setTheme(themeId, save = true) {
    if (!THEMES[themeId]) {
        console.warn(`Theme "${themeId}" not found, using default (ocean)`);
        themeId = 'ocean';
    }
    
    // Remove all existing theme attributes
    document.documentElement.removeAttribute('data-theme');
    
    // Apply new theme
    document.documentElement.setAttribute('data-theme', themeId);
    
    // Save to localStorage if requested
    if (save) {
        localStorage.setItem(THEME_STORAGE_KEY, themeId);
    }
    
    // Update theme selector UI if exists
    updateThemeSelectorUI(themeId);
    
    // Dispatch custom event for other components to listen
    window.dispatchEvent(new CustomEvent('themechange', { 
        detail: { theme: themeId, themeData: THEMES[themeId] }
    }));
}

/**
 * Update theme selector UI to reflect current theme
 * @param {string} activeThemeId - Currently active theme ID
 */
function updateThemeSelectorUI(activeThemeId) {
    const options = document.querySelectorAll('.theme-option');
    options.forEach(option => {
        if (option.dataset.theme === activeThemeId) {
            option.classList.add('active');
        } else {
            option.classList.remove('active');
        }
    });
}

/**
 * Toggle to next theme in the list
 */
function toggleTheme() {
    const themeIds = Object.keys(THEMES);
    const currentIndex = themeIds.indexOf(getCurrentTheme());
    const nextIndex = (currentIndex + 1) % themeIds.length;
    setTheme(themeIds[nextIndex]);
}

/**
 * Get all available themes
 */
function getAllThemes() {
    return Object.values(THEMES);
}

/**
 * Check if a theme is dark
 * @param {string} themeId - Theme identifier
 */
function isDarkTheme(themeId) {
    return THEMES[themeId]?.isDark ?? true;
}

/**
 * Get current language (for theme name display)
 */
function getCurrentLang() {
    return localStorage.getItem('neshama-lang') || 'en';
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', () => {
    // Support URL parameter for theme preview: ?theme=ocean
    const urlParams = new URLSearchParams(window.location.search);
    const urlTheme = urlParams.get('theme');
    if (urlTheme && THEMES[urlTheme]) {
        localStorage.setItem(THEME_STORAGE_KEY, urlTheme);
    }
    initTheme();
});

// Export for global use
window.ThemeManager = {
    THEMES,
    initTheme,
    getCurrentTheme,
    setTheme,
    toggleTheme,
    getAllThemes,
    isDarkTheme,
    THEME_STORAGE_KEY
};
