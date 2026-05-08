/**
 * Neshama Dashboard - Theme Manager
 * Single light theme, no switching
 */

// Fixed theme ID
const THEME_ID = 'light';
const THEME_STORAGE_KEY = 'neshama-theme';

/**
 * Initialize theme system
 * Always uses the light theme
 */
function initTheme() {
    // Ensure no dark theme attribute is set
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem(THEME_STORAGE_KEY, THEME_ID);
}

/**
 * Get current theme ID (always 'light')
 */
function getCurrentTheme() {
    return THEME_ID;
}

/**
 * Set theme - no-op, always light
 */
function setTheme() {
    initTheme();
}

/**
 * Toggle theme - no-op, always light
 */
function toggleTheme() {
    // No theme switching
}

/**
 * Get all available themes (just one)
 */
function getAllThemes() {
    return [{ id: THEME_ID, name: 'Light', nameZh: '浅色', isDark: false }];
}

/**
 * Check if a theme is dark - always false
 */
function isDarkTheme() {
    return false;
}

/**
 * Get current language
 */
function getCurrentLang() {
    return localStorage.getItem('neshama-lang') || 'en';
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
});

// Export for global use
window.ThemeManager = {
    initTheme,
    getCurrentTheme,
    setTheme,
    toggleTheme,
    getAllThemes,
    isDarkTheme,
    THEME_STORAGE_KEY
};
