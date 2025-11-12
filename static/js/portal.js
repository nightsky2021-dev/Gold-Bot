/**
 * User Transaction Portal JavaScript
 * Handles filtering, price refresh, and UI interactions
 */

(function() {
    'use strict';

    // ==================== Price Refresh ====================
    
    function refreshPrices() {
        const refreshBtn = document.getElementById('refresh-prices-btn');
        if (!refreshBtn) return;
        
        refreshBtn.disabled = true;
        refreshBtn.textContent = 'در حال بروزرسانی...';
        
        fetch('/portal/api/prices/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update prices in the DOM
                    data.prices.forEach(product => {
                        const buyPriceEl = document.getElementById(`buy-price-${product.id}`);
                        const sellPriceEl = document.getElementById(`sell-price-${product.id}`);
                        
                        if (buyPriceEl) {
                            buyPriceEl.textContent = formatNumber(product.buy_price);
                            animateChange(buyPriceEl);
                        }
                        
                        if (sellPriceEl) {
                            sellPriceEl.textContent = formatNumber(product.sell_price);
                            animateChange(sellPriceEl);
                        }
                    });
                    
                    // Update timestamp
                    const timestampEl = document.getElementById('prices-updated-at');
                    if (timestampEl) {
                        const now = new Date();
                        timestampEl.textContent = `آخرین بروزرسانی: ${now.toLocaleTimeString('fa-IR')}`;
                    }
                    
                    showNotification('قیمت‌ها با موفقیت بروزرسانی شد', 'success');
                }
            })
            .catch(error => {
                console.error('Error refreshing prices:', error);
                showNotification('خطا در بروزرسانی قیمت‌ها', 'error');
            })
            .finally(() => {
                refreshBtn.disabled = false;
                refreshBtn.textContent = '🔄 بروزرسانی قیمت‌ها';
            });
    }
    
    // ==================== Filtering ====================
    
    function applyFilters() {
        const form = document.getElementById('filter-form');
        if (!form) return;
        
        // Collect filter values
        const params = new URLSearchParams();
        
        const productId = document.getElementById('filter-product');
        if (productId && productId.value) {
            params.append('product_id', productId.value);
        }
        
        const transactionType = document.getElementById('filter-type');
        if (transactionType && transactionType.value) {
            params.append('transaction_type', transactionType.value);
        }
        
        const dateRange = document.getElementById('filter-date-range');
        if (dateRange && dateRange.value) {
            params.append('date_range', dateRange.value);
        }
        
        // For custom date range
        if (dateRange && dateRange.value === 'custom') {
            const dateFrom = document.getElementById('filter-date-from');
            const dateTo = document.getElementById('filter-date-to');
            
            if (dateFrom && dateFrom.value) {
                params.append('date_from', dateFrom.value);
            }
            if (dateTo && dateTo.value) {
                params.append('date_to', dateTo.value);
            }
        }
        
        // Redirect with filters
        window.location.href = window.location.pathname + '?' + params.toString();
    }
    
    function resetFilters() {
        window.location.href = window.location.pathname;
    }
    
    function toggleCustomDateRange() {
        const dateRange = document.getElementById('filter-date-range');
        const customRange = document.getElementById('custom-date-range');
        
        if (!dateRange || !customRange) return;
        
        if (dateRange.value === 'custom') {
            customRange.style.display = 'flex';
        } else {
            customRange.style.display = 'none';
        }
    }
    
    // ==================== Export Functions ====================
    
    function exportData(format) {
        const currentUrl = new URL(window.location.href);
        const params = currentUrl.searchParams.toString();
        
        let exportUrl;
        if (window.location.pathname.includes('/transactions')) {
            exportUrl = `/portal/export/transactions/${format}/?${params}`;
        } else if (window.location.pathname.includes('/statement')) {
            exportUrl = `/portal/export/statement/${format}/?${params}`;
        }
        
        if (exportUrl) {
            showNotification('در حال آماده‌سازی فایل...', 'info');
            window.location.href = exportUrl;
        }
    }
    
    // ==================== UI Helpers ====================
    
    function formatNumber(num) {
        return new Intl.NumberFormat('fa-IR').format(num);
    }
    
    function animateChange(element) {
        element.classList.add('price-updated');
        setTimeout(() => {
            element.classList.remove('price-updated');
        }, 1000);
    }
    
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add styles inline for quick implementation
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#F44336' : '#2196F3'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    // ==================== Transaction Details ====================
    
    function showTransactionDetails(orderId) {
        // In a full implementation, this would open a modal with detailed info
        // For now, we'll just log it
        console.log('Show details for order:', orderId);
    }
    
    // ==================== Chart Initialization (if needed) ====================
    
    function initCharts() {
        // Placeholder for future chart implementation
        // Could use Chart.js or ApexCharts for visualizations
    }
    
    // ==================== Session Management ====================
    
    function checkSession() {
        // Auto-logout after session expires
        const authenticatedAt = sessionStorage.getItem('authenticated_at');
        if (authenticatedAt) {
            const now = new Date().getTime();
            const authTime = new Date(authenticatedAt).getTime();
            const elapsed = now - authTime;
            const oneHour = 60 * 60 * 1000;
            
            if (elapsed > oneHour) {
                showNotification('جلسه شما منقضی شده است. لطفاً دوباره وارد شوید.', 'warning');
                setTimeout(() => {
                    window.location.href = '/portal/logout/';
                }, 2000);
            }
        }
    }
    
    // ==================== Auto-refresh ====================
    
    function enableAutoRefresh(interval = 60000) {
        // Auto-refresh prices every minute (optional)
        setInterval(() => {
            if (document.getElementById('refresh-prices-btn')) {
                refreshPrices();
            }
        }, interval);
    }
    
    // ==================== Event Listeners ====================
    
    function initEventListeners() {
        // Refresh prices button
        const refreshBtn = document.getElementById('refresh-prices-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', refreshPrices);
        }
        
        // Apply filters button
        const applyBtn = document.getElementById('apply-filters-btn');
        if (applyBtn) {
            applyBtn.addEventListener('click', applyFilters);
        }
        
        // Reset filters button
        const resetBtn = document.getElementById('reset-filters-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', resetFilters);
        }
        
        // Date range change
        const dateRange = document.getElementById('filter-date-range');
        if (dateRange) {
            dateRange.addEventListener('change', toggleCustomDateRange);
            // Initialize on load
            toggleCustomDateRange();
        }
        
        // Export buttons
        const exportCsvBtn = document.getElementById('export-csv-btn');
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => exportData('csv'));
        }
        
        const exportPdfBtn = document.getElementById('export-pdf-btn');
        if (exportPdfBtn) {
            exportPdfBtn.addEventListener('click', () => exportData('pdf'));
        }
        
        // Mobile menu toggle (if needed)
        const menuToggle = document.getElementById('mobile-menu-toggle');
        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                const nav = document.querySelector('.portal-nav');
                nav.classList.toggle('mobile-open');
            });
        }
    }
    
    // ==================== Number Formatting ====================
    
    function formatAllNumbers() {
        // Format all numbers with 'data-format-number' attribute
        document.querySelectorAll('[data-format-number]').forEach(el => {
            const value = parseFloat(el.textContent);
            if (!isNaN(value)) {
                el.textContent = formatNumber(value);
            }
        });
    }
    
    // ==================== Initialization ====================
    
    function init() {
        console.log('Portal JS initialized');
        
        // Initialize event listeners
        initEventListeners();
        
        // Format numbers
        formatAllNumbers();
        
        // Check session
        checkSession();
        
        // Initialize charts if needed
        initCharts();
        
        // Optional: Enable auto-refresh (commented out by default)
        // enableAutoRefresh(60000);
        
        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
            
            .price-updated {
                animation: pulse 0.5s ease-out;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Export functions to global scope if needed
    window.PortalApp = {
        refreshPrices,
        applyFilters,
        resetFilters,
        exportData,
        showNotification
    };
    
})();
