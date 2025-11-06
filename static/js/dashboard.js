/**
 * Dashboard JavaScript
 * Handles auto-refresh, animations, and interactivity
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        autoRefresh: true,
        refreshInterval: 60000, // 60 seconds
        animationDelay: 100,
        chartUpdateInterval: 5000
    };

    // State
    let refreshTimer = null;
    let isRefreshing = false;

    /**
     * Initialize the dashboard
     */
    function init() {
        console.log('Dashboard initializing...');
        
        // Animate elements on load
        animateOnLoad();
        
        // Setup auto-refresh
        if (CONFIG.autoRefresh) {
            setupAutoRefresh();
        }
        
        // Setup event listeners
        setupEventListeners();
        
        // Add keyboard shortcuts
        setupKeyboardShortcuts();
        
        // Format numbers
        formatNumbers();
        
        // Initialize tooltips
        initializeTooltips();
        
        console.log('Dashboard initialized successfully');
    }

    /**
     * Animate elements on page load
     */
    function animateOnLoad() {
        const elements = document.querySelectorAll('.kpi-card, .stat-card, .activity-item');
        
        elements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'all 0.5s ease-out';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * CONFIG.animationDelay);
        });
    }

    /**
     * Setup auto-refresh functionality
     */
    function setupAutoRefresh() {
        refreshTimer = setInterval(() => {
            if (!isRefreshing) {
                refreshDashboard();
            }
        }, CONFIG.refreshInterval);
        
        // Show refresh indicator
        showRefreshIndicator();
    }

    /**
     * Refresh dashboard data
     */
    async function refreshDashboard() {
        if (isRefreshing) return;
        
        isRefreshing = true;
        showRefreshIndicator('در حال بروزرسانی...');
        
        try {
            // Get current page URL
            const response = await fetch(window.location.href, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // Update KPI values
                updateKPIValues(doc);
                
                // Update activity feeds
                updateActivityFeeds(doc);
                
                showRefreshIndicator('بروزرسانی با موفقیت انجام شد', 'success');
                
                setTimeout(() => {
                    hideRefreshIndicator();
                }, 2000);
            } else {
                throw new Error('Failed to refresh');
            }
        } catch (error) {
            console.error('Refresh error:', error);
            showRefreshIndicator('خطا در بروزرسانی', 'error');
            
            setTimeout(() => {
                hideRefreshIndicator();
            }, 3000);
        } finally {
            isRefreshing = false;
        }
    }

    /**
     * Update KPI values from new data
     */
    function updateKPIValues(doc) {
        const kpiCards = document.querySelectorAll('.kpi-card');
        const newKpiCards = doc.querySelectorAll('.kpi-card');
        
        kpiCards.forEach((card, index) => {
            if (newKpiCards[index]) {
                const newValue = newKpiCards[index].querySelector('.kpi-value');
                const currentValue = card.querySelector('.kpi-value');
                
                if (newValue && currentValue) {
                    animateValueChange(currentValue, newValue.textContent);
                }
                
                // Update subtitle
                const newSubtitle = newKpiCards[index].querySelector('.kpi-subtitle');
                const currentSubtitle = card.querySelector('.kpi-subtitle');
                
                if (newSubtitle && currentSubtitle) {
                    currentSubtitle.textContent = newSubtitle.textContent;
                }
            }
        });
    }

    /**
     * Animate value changes
     */
    function animateValueChange(element, newValue) {
        element.style.transform = 'scale(1.2)';
        element.style.color = 'var(--success-color)';
        
        setTimeout(() => {
            element.textContent = newValue;
            element.style.transform = 'scale(1)';
            element.style.color = '';
        }, 300);
    }

    /**
     * Update activity feeds
     */
    function updateActivityFeeds(doc) {
        const activitySections = document.querySelectorAll('.activity-feed, .recent-activity');
        const newActivitySections = doc.querySelectorAll('.activity-feed, .recent-activity');
        
        activitySections.forEach((section, index) => {
            if (newActivitySections[index]) {
                const activityList = section.querySelector('.activity-list') || section;
                const newActivityList = newActivitySections[index].querySelector('.activity-list') || newActivitySections[index];
                
                if (activityList && newActivityList) {
                    // Fade out
                    activityList.style.opacity = '0.5';
                    
                    setTimeout(() => {
                        activityList.innerHTML = newActivityList.innerHTML;
                        activityList.style.opacity = '1';
                    }, 300);
                }
            }
        });
    }

    /**
     * Show refresh indicator
     */
    function showRefreshIndicator(message = 'بروزرسانی خودکار فعال است', type = 'info') {
        let indicator = document.getElementById('refresh-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'refresh-indicator';
            indicator.className = 'refresh-indicator';
            document.body.appendChild(indicator);
        }
        
        indicator.className = `refresh-indicator ${type}`;
        indicator.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
            </svg>
            <span>${message}</span>
        `;
        
        indicator.style.display = 'flex';
    }

    /**
     * Hide refresh indicator
     */
    function hideRefreshIndicator() {
        const indicator = document.getElementById('refresh-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Manual refresh button
        const refreshBtn = document.getElementById('manual-refresh');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', (e) => {
                e.preventDefault();
                refreshDashboard();
            });
        }
        
        // Toggle auto-refresh
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                CONFIG.autoRefresh = e.target.checked;
                if (CONFIG.autoRefresh) {
                    setupAutoRefresh();
                } else {
                    if (refreshTimer) {
                        clearInterval(refreshTimer);
                    }
                    hideRefreshIndicator();
                }
            });
        }
        
        // Card click handlers
        document.querySelectorAll('.kpi-card, .stat-card').forEach(card => {
            card.addEventListener('click', function() {
                const link = this.querySelector('a');
                if (link) {
                    window.location.href = link.href;
                }
            });
        });
    }

    /**
     * Setup keyboard shortcuts
     */
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R: Manual refresh
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                refreshDashboard();
            }
            
            // Ctrl/Cmd + /: Show shortcuts help
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                showKeyboardShortcuts();
            }
        });
    }

    /**
     * Show keyboard shortcuts modal
     */
    function showKeyboardShortcuts() {
        alert(`
میانبرهای صفحه‌کلید:

Ctrl/Cmd + R: بروزرسانی دستی
Ctrl/Cmd + /: نمایش میانبرها
        `.trim());
    }

    /**
     * Format numbers with separators
     */
    function formatNumbers() {
        const numbers = document.querySelectorAll('.kpi-value, .stat-value');
        
        numbers.forEach(element => {
            const value = element.textContent.trim();
            if (!isNaN(value) && value !== '') {
                const formatted = Number(value).toLocaleString('fa-IR');
                element.textContent = formatted;
            }
        });
    }

    /**
     * Initialize tooltips
     */
    function initializeTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            element.classList.add('tooltip');
        });
    }

    /**
     * Add pulse animation to important elements
     */
    function addPulseAnimation(selector) {
        const elements = document.querySelectorAll(selector);
        
        elements.forEach(element => {
            element.style.animation = 'pulse 2s infinite';
        });
    }

    /**
     * Cleanup on page unload
     */
    function cleanup() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', cleanup);

    // Export for external use
    window.Dashboard = {
        refresh: refreshDashboard,
        toggleAutoRefresh: (enabled) => {
            CONFIG.autoRefresh = enabled;
            if (enabled) {
                setupAutoRefresh();
            } else {
                if (refreshTimer) {
                    clearInterval(refreshTimer);
                }
                hideRefreshIndicator();
            }
        }
    };

})();
