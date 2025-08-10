/* ===== COLLAPSIBLE COMPONENT FUNCTIONS ===== */

/**
 * CollapsibleManager - Manages all collapsible components on the page
 */
class CollapsibleManager {
    constructor() {
        this.collapsibles = new Map();
        this.focusedIndex = -1;
        this.keyboardShortcutsEnabled = true;
        this.printMode = false;
        this.init();
    }

    /**
     * Initialize all collapsible components on the page
     */
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.scanAndInitialize();
            this.setupKeyboardShortcuts();
            this.setupAccessibilityFeatures();
        });

        // Re-scan when new content is added dynamically
        this.observeChanges();
    }

    /**
     * Scan for collapsible components and initialize them
     */
    scanAndInitialize() {
        const collapsibleContainers = document.querySelectorAll('.collapsible-container');
        collapsibleContainers.forEach((container, index) => {
            if (!container.dataset.initialized) {
                this.initializeCollapsible(container, index);
            }
        });
    }

    /**
     * Initialize a single collapsible component
     */
    initializeCollapsible(container, id) {
        const header = container.querySelector('.collapsible-header');
        const content = container.querySelector('.collapsible-content');
        const chevron = container.querySelector('.collapsible-chevron');

        if (!header || !content) {
            console.warn('Collapsible component missing required elements:', container);
            return;
        }

        // Set unique ID if not already set
        const collapsibleId = container.id || `collapsible-${id}`;
        container.id = collapsibleId;
        container.dataset.initialized = 'true';

        // Store reference
        this.collapsibles.set(collapsibleId, {
            container,
            header,
            content,
            chevron,
            isExpanded: false,
            isAnimating: false
        });

        // Add click event listener
        header.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggle(collapsibleId);
        });

        // Handle keyboard navigation
        header.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggle(collapsibleId);
            }
        });

        // Make header focusable
        if (!header.getAttribute('tabindex')) {
            header.setAttribute('tabindex', '0');
        }

        // Set initial state based on data attribute
        const initialExpanded = container.dataset.expanded === 'true';
        if (initialExpanded) {
            this.expand(collapsibleId, false); // No animation for initial state
        }
    }

    /**
     * Toggle collapsible state
     */
    toggle(id) {
        const collapsible = this.collapsibles.get(id);
        if (!collapsible || collapsible.isAnimating) return;

        if (collapsible.isExpanded) {
            this.collapse(id);
        } else {
            this.expand(id);
        }
    }

    /**
     * Expand a collapsible component
     */
    expand(id, animate = true) {
        const collapsible = this.collapsibles.get(id);
        if (!collapsible || collapsible.isExpanded) return;

        const { container, header, content, chevron } = collapsible;

        collapsible.isAnimating = true;
        collapsible.isExpanded = true;

        // Add active classes
        header.classList.add('active');
        content.classList.add('expanded');

        // Trigger custom event
        container.dispatchEvent(new CustomEvent('collapsible:expand', {
            detail: { id, collapsible }
        }));

        if (animate) {
            // Get the natural height of the content
            const scrollHeight = content.scrollHeight;
            
            // Set max-height to enable smooth animation
            content.style.maxHeight = scrollHeight + 'px';

            // Add animation classes
            content.classList.add('fade-in');

            // Reset animation flag after transition
            setTimeout(() => {
                collapsible.isAnimating = false;
                content.style.maxHeight = '2000px'; // Reset to CSS value
                content.classList.remove('fade-in');
            }, 300);
        } else {
            collapsible.isAnimating = false;
        }

        // Update ARIA attributes
        header.setAttribute('aria-expanded', 'true');
        content.setAttribute('aria-hidden', 'false');

        // Focus management for keyboard users
        if (document.activeElement === header) {
            // Optionally focus first focusable element in content
            const firstFocusable = content.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                setTimeout(() => firstFocusable.focus(), 100);
            }
        }
    }

    /**
     * Collapse a collapsible component
     */
    collapse(id, animate = true) {
        const collapsible = this.collapsibles.get(id);
        if (!collapsible || !collapsible.isExpanded) return;

        const { container, header, content, chevron } = collapsible;

        collapsible.isAnimating = true;
        collapsible.isExpanded = false;

        // Remove active classes
        header.classList.remove('active');
        content.classList.remove('expanded');

        // Trigger custom event
        container.dispatchEvent(new CustomEvent('collapsible:collapse', {
            detail: { id, collapsible }
        }));

        if (animate) {
            // Set current height then transition to 0
            const currentHeight = content.scrollHeight;
            content.style.maxHeight = currentHeight + 'px';

            // Force reflow
            content.offsetHeight;

            // Animate to collapsed state
            content.style.maxHeight = '0px';

            // Reset animation flag after transition
            setTimeout(() => {
                collapsible.isAnimating = false;
                content.style.maxHeight = '';
            }, 300);
        } else {
            collapsible.isAnimating = false;
        }

        // Update ARIA attributes
        header.setAttribute('aria-expanded', 'false');
        content.setAttribute('aria-hidden', 'true');
    }

    /**
     * Expand all collapsible components
     */
    expandAll() {
        this.collapsibles.forEach((collapsible, id) => {
            if (!collapsible.isExpanded) {
                this.expand(id);
            }
        });
    }

    /**
     * Collapse all collapsible components
     */
    collapseAll() {
        this.collapsibles.forEach((collapsible, id) => {
            if (collapsible.isExpanded) {
                this.collapse(id);
            }
        });
    }

    /**
     * Get collapsible state
     */
    isExpanded(id) {
        const collapsible = this.collapsibles.get(id);
        return collapsible ? collapsible.isExpanded : false;
    }

    /**
     * Observe DOM changes to auto-initialize new collapsibles
     */
    observeChanges() {
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver((mutations) => {
                let shouldScan = false;
                
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === 1) { // Element node
                                if (node.classList?.contains('collapsible-container') || 
                                    node.querySelector?.('.collapsible-container')) {
                                    shouldScan = true;
                                }
                            }
                        });
                    }
                });

                if (shouldScan) {
                    setTimeout(() => this.scanAndInitialize(), 10);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }

    /**
     * Destroy a collapsible component
     */
    destroy(id) {
        const collapsible = this.collapsibles.get(id);
        if (collapsible) {
            const { container, header } = collapsible;
            
            // Remove event listeners
            header.removeEventListener('click', this.toggle);
            header.removeEventListener('keydown', this.toggle);
            
            // Remove from map
            this.collapsibles.delete(id);
            
            // Remove initialization flag
            container.removeAttribute('data-initialized');
        }
    }

    /**
     * Setup keyboard shortcuts for global collapsible management
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (!this.keyboardShortcutsEnabled) return;
            
            // Don't trigger shortcuts if user is typing in inputs
            const activeElement = document.activeElement;
            if (activeElement && (
                activeElement.tagName === 'INPUT' ||
                activeElement.tagName === 'TEXTAREA' ||
                activeElement.tagName === 'SELECT' ||
                activeElement.isContentEditable
            )) {
                return;
            }

            // Global keyboard shortcuts
            if (e.ctrlKey && e.key === 'e') {
                e.preventDefault();
                this.expandAll();
                this.showNotification('Expanded all sections', 'success');
            } else if (e.ctrlKey && e.key === 'c') {
                e.preventDefault();
                this.collapseAll();
                this.showNotification('Collapsed all sections', 'success');
            } else if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                this.togglePrintMode();
            } else if (e.ctrlKey && e.key === 's' && e.shiftKey) {
                e.preventDefault();
                this.exportToText();
            }
            
            // Arrow key navigation
            else if (e.key === 'ArrowDown' && e.ctrlKey) {
                e.preventDefault();
                this.focusNext();
            } else if (e.key === 'ArrowUp' && e.ctrlKey) {
                e.preventDefault();
                this.focusPrevious();
            }
        });

        // Add Help shortcut (? key)
        document.addEventListener('keydown', (e) => {
            if (e.key === '?' && !e.ctrlKey && !e.altKey && !e.metaKey) {
                const activeElement = document.activeElement;
                if (activeElement && (
                    activeElement.tagName === 'INPUT' ||
                    activeElement.tagName === 'TEXTAREA' ||
                    activeElement.isContentEditable
                )) {
                    return;
                }
                e.preventDefault();
                this.showKeyboardHelp();
            }
        });
    }

    /**
     * Setup accessibility features
     */
    setupAccessibilityFeatures() {
        // Add skip link for keyboard users
        this.addSkipLink();
        
        // Setup print mode detection
        this.setupPrintMode();
        
        // Add ARIA live region for announcements
        this.addAriaLiveRegion();
        
        // Enhance header accessibility
        this.enhanceHeaderAccessibility();
    }

    /**
     * Add skip link for keyboard navigation
     */
    addSkipLink() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-link';
        skipLink.textContent = 'Skip to main content';
        skipLink.setAttribute('aria-label', 'Skip to main content');
        
        // Style the skip link
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--apple-blue);
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 1000;
            transition: top 0.3s;
            font-weight: 600;
        `;
        
        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
    }

    /**
     * Add ARIA live region for announcements
     */
    addAriaLiveRegion() {
        if (!document.getElementById('collapsible-announcer')) {
            const announcer = document.createElement('div');
            announcer.id = 'collapsible-announcer';
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            announcer.style.cssText = `
                position: absolute;
                left: -10000px;
                width: 1px;
                height: 1px;
                overflow: hidden;
            `;
            document.body.appendChild(announcer);
        }
    }

    /**
     * Announce message to screen readers
     */
    announce(message) {
        const announcer = document.getElementById('collapsible-announcer');
        if (announcer) {
            announcer.textContent = message;
        }
    }

    /**
     * Enhance header accessibility
     */
    enhanceHeaderAccessibility() {
        this.collapsibles.forEach((collapsible, id) => {
            const { header, content } = collapsible;
            
            // Add role and ARIA attributes
            header.setAttribute('role', 'button');
            header.setAttribute('aria-controls', `content-${id}`);
            content.setAttribute('id', `content-${id}`);
            
            // Add describedby for additional context
            const description = content.querySelector('.technical-details .details-title');
            if (description) {
                const descId = `desc-${id}`;
                description.setAttribute('id', descId);
                header.setAttribute('aria-describedby', descId);
            }
        });
    }

    /**
     * Focus next collapsible header
     */
    focusNext() {
        const headers = Array.from(document.querySelectorAll('.collapsible-header'));
        if (headers.length === 0) return;
        
        let currentIndex = headers.findIndex(header => header === document.activeElement);
        if (currentIndex === -1) currentIndex = -1;
        
        const nextIndex = (currentIndex + 1) % headers.length;
        headers[nextIndex].focus();
        this.announce(`Focused ${headers[nextIndex].querySelector('.collapsible-title span').textContent}`);
    }

    /**
     * Focus previous collapsible header
     */
    focusPrevious() {
        const headers = Array.from(document.querySelectorAll('.collapsible-header'));
        if (headers.length === 0) return;
        
        let currentIndex = headers.findIndex(header => header === document.activeElement);
        if (currentIndex === -1) currentIndex = headers.length;
        
        const prevIndex = (currentIndex - 1 + headers.length) % headers.length;
        headers[prevIndex].focus();
        this.announce(`Focused ${headers[prevIndex].querySelector('.collapsible-title span').textContent}`);
    }

    /**
     * Toggle print mode (expand all sections for printing)
     */
    togglePrintMode() {
        this.printMode = !this.printMode;
        document.body.classList.toggle('print-mode', this.printMode);
        
        if (this.printMode) {
            // Store current states
            this.previewStates = new Map();
            this.collapsibles.forEach((collapsible, id) => {
                this.previewStates.set(id, collapsible.isExpanded);
                if (!collapsible.isExpanded) {
                    this.expand(id, false);
                }
            });
            this.showNotification('Print mode enabled - All sections expanded', 'info');
            this.announce('Print mode enabled. All sections expanded for printing.');
        } else {
            // Restore previous states
            if (this.previewStates) {
                this.collapsibles.forEach((collapsible, id) => {
                    const previousState = this.previewStates.get(id);
                    if (previousState !== collapsible.isExpanded) {
                        if (previousState) {
                            this.expand(id, false);
                        } else {
                            this.collapse(id, false);
                        }
                    }
                });
            }
            this.showNotification('Print mode disabled - States restored', 'info');
            this.announce('Print mode disabled. Section states restored.');
        }
    }

    /**
     * Setup print mode detection
     */
    setupPrintMode() {
        // Detect print with CSS media query
        const printMediaQuery = window.matchMedia('print');
        printMediaQuery.addListener((mql) => {
            if (mql.matches) {
                // Temporarily expand all for printing
                this.expandAllForPrint = true;
                this.collapsibles.forEach((collapsible, id) => {
                    if (!collapsible.isExpanded) {
                        this.expand(id, false);
                    }
                });
            } else if (this.expandAllForPrint) {
                // Restore states after printing
                this.expandAllForPrint = false;
                // Note: We can't reliably restore states after print dialog
            }
        });
    }

    /**
     * Export technical details to text file
     */
    exportToText() {
        let exportContent = 'Technical Details Export\n';
        exportContent += '========================\n\n';
        exportContent += `Generated: ${new Date().toLocaleString()}\n\n`;
        
        this.collapsibles.forEach((collapsible, id) => {
            const { header, content } = collapsible;
            const title = header.querySelector('.collapsible-title span').textContent;
            
            exportContent += `Section: ${title}\n`;
            exportContent += '-'.repeat(title.length + 9) + '\n';
            
            if (collapsible.isExpanded) {
                const technicalDetails = content.querySelector('.technical-details');
                if (technicalDetails) {
                    // Extract commands
                    const commands = technicalDetails.querySelectorAll('.command-block code');
                    if (commands.length > 0) {
                        exportContent += 'Commands:\n';
                        commands.forEach(cmd => {
                            exportContent += `  $ ${cmd.textContent}\n`;
                        });
                        exportContent += '\n';
                    }
                    
                    // Extract outputs
                    const outputs = technicalDetails.querySelectorAll('.output-block');
                    if (outputs.length > 0) {
                        exportContent += 'Output:\n';
                        outputs.forEach(output => {
                            exportContent += `  ${output.textContent}\n`;
                        });
                        exportContent += '\n';
                    }
                    
                    // Extract metrics
                    const metrics = technicalDetails.querySelectorAll('.metric-item');
                    if (metrics.length > 0) {
                        exportContent += 'Metrics:\n';
                        metrics.forEach(metric => {
                            const value = metric.querySelector('.metric-value')?.textContent || '';
                            const label = metric.querySelector('.metric-label')?.textContent || '';
                            exportContent += `  ${label}: ${value}\n`;
                        });
                        exportContent += '\n';
                    }
                }
            } else {
                exportContent += 'Section is collapsed\n\n';
            }
        });
        
        // Create and download file
        const blob = new Blob([exportContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `technical-details-${new Date().toISOString().split('T')[0]}.txt`;
        link.click();
        URL.revokeObjectURL(url);
        
        this.showNotification('Technical details exported', 'success');
        this.announce('Technical details exported to text file');
    }

    /**
     * Show keyboard shortcuts help
     */
    showKeyboardHelp() {
        const helpContent = `
            <div class="keyboard-help">
                <h3>Keyboard Shortcuts</h3>
                <div class="shortcut-group">
                    <h4>Global Controls</h4>
                    <ul>
                        <li><kbd>Ctrl</kbd> + <kbd>E</kbd> - Expand all sections</li>
                        <li><kbd>Ctrl</kbd> + <kbd>C</kbd> - Collapse all sections</li>
                        <li><kbd>Ctrl</kbd> + <kbd>P</kbd> - Toggle print mode</li>
                        <li><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> - Export to text file</li>
                    </ul>
                </div>
                <div class="shortcut-group">
                    <h4>Navigation</h4>
                    <ul>
                        <li><kbd>Ctrl</kbd> + <kbd>↓</kbd> - Focus next section</li>
                        <li><kbd>Ctrl</kbd> + <kbd>↑</kbd> - Focus previous section</li>
                        <li><kbd>Enter</kbd> or <kbd>Space</kbd> - Toggle focused section</li>
                        <li><kbd>?</kbd> - Show this help</li>
                    </ul>
                </div>
                <div class="shortcut-group">
                    <h4>Accessibility</h4>
                    <ul>
                        <li><kbd>Tab</kbd> - Navigate between sections</li>
                        <li>Screen reader support with ARIA labels</li>
                        <li>High contrast mode compatible</li>
                    </ul>
                </div>
            </div>
        `;
        
        this.showModal('Keyboard Shortcuts Help', helpContent);
    }

    /**
     * Show notification toast
     */
    showNotification(message, type = 'info') {
        // Remove existing notification
        const existing = document.querySelector('.collapsible-notification');
        if (existing) existing.remove();
        
        const notification = document.createElement('div');
        notification.className = `collapsible-notification ${type}`;
        notification.textContent = message;
        notification.setAttribute('role', 'status');
        notification.setAttribute('aria-live', 'polite');
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--apple-blue);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 500;
            z-index: 1000;
            box-shadow: var(--shadow-medium);
            transform: translateX(400px);
            transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        `;
        
        // Type-specific styles
        if (type === 'success') {
            notification.style.background = 'var(--apple-green)';
        } else if (type === 'error') {
            notification.style.background = 'var(--apple-red)';
        } else if (type === 'warning') {
            notification.style.background = 'var(--apple-orange)';
        }
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Remove after delay
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Show modal dialog
     */
    showModal(title, content) {
        // Remove existing modal
        const existing = document.querySelector('.collapsible-modal');
        if (existing) existing.remove();
        
        const modal = document.createElement('div');
        modal.className = 'collapsible-modal';
        modal.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="modal-content" role="dialog" aria-modal="true" aria-labelledby="modal-title">
                <div class="modal-header">
                    <h3 id="modal-title">${title}</h3>
                    <button class="modal-close" aria-label="Close">&times;</button>
                </div>
                <div class="modal-body">${content}</div>
            </div>
        `;
        
        // Add modal styles
        const style = document.createElement('style');
        style.textContent = `
            .collapsible-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 2000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .modal-backdrop {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
            }
            .modal-content {
                background: white;
                border-radius: 12px;
                box-shadow: var(--shadow-large);
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                position: relative;
            }
            .modal-header {
                padding: 20px;
                border-bottom: 1px solid var(--apple-gray-5);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .modal-close {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
            }
            .modal-close:hover {
                background: var(--apple-gray-5);
            }
            .modal-body {
                padding: 20px;
            }
            .keyboard-help h3 {
                margin-top: 0;
                color: var(--apple-black);
            }
            .shortcut-group {
                margin-bottom: 20px;
            }
            .shortcut-group h4 {
                color: var(--apple-blue);
                margin-bottom: 8px;
            }
            .shortcut-group ul {
                margin: 0;
                padding-left: 20px;
            }
            .shortcut-group li {
                margin-bottom: 4px;
            }
            kbd {
                background: var(--apple-gray-5);
                border: 1px solid var(--apple-gray-4);
                border-radius: 3px;
                padding: 2px 6px;
                font-family: inherit;
                font-size: 0.9em;
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(modal);
        
        // Focus management
        const closeButton = modal.querySelector('.modal-close');
        closeButton.focus();
        
        // Close handlers
        const closeModal = () => {
            modal.remove();
            style.remove();
        };
        
        closeButton.addEventListener('click', closeModal);
        modal.querySelector('.modal-backdrop').addEventListener('click', closeModal);
        
        // Escape key to close
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    }

    /**
     * Enable/disable keyboard shortcuts
     */
    toggleKeyboardShortcuts(enabled) {
        this.keyboardShortcutsEnabled = enabled;
        this.announce(enabled ? 'Keyboard shortcuts enabled' : 'Keyboard shortcuts disabled');
    }

    /**
     * Refresh/reinitialize all collapsibles
     */
    refresh() {
        this.collapsibles.clear();
        this.scanAndInitialize();
    }
}

/**
 * Utility functions for creating collapsible components programmatically
 */
const CollapsibleUtils = {
    /**
     * Create a new collapsible component
     */
    create({
        title = 'Collapsible Section',
        icon = '📄',
        content = '',
        expanded = false,
        className = '',
        id = null
    } = {}) {
        const container = document.createElement('div');
        container.className = `collapsible-container ${className}`;
        
        if (id) {
            container.id = id;
        }
        
        if (expanded) {
            container.dataset.expanded = 'true';
        }

        container.innerHTML = `
            <div class="collapsible-header" role="button" aria-expanded="${expanded}">
                <div class="collapsible-title">
                    <div class="collapsible-icon">${icon}</div>
                    <span>${title}</span>
                </div>
                <div class="collapsible-chevron"></div>
            </div>
            <div class="collapsible-content" aria-hidden="${!expanded}">
                ${content}
            </div>
        `;

        return container;
    },

    /**
     * Create a technical details section
     */
    createTechnicalDetails({
        title = 'Technical Details',
        commands = [],
        outputs = [],
        metrics = [],
        status = 'info'
    } = {}) {
        let content = `<div class="technical-details">`;
        
        if (title) {
            content += `<div class="details-title">${title}</div>`;
        }

        // Add status indicator
        if (status) {
            const statusText = status.charAt(0).toUpperCase() + status.slice(1);
            content += `<div class="status-indicator ${status}">${statusText}</div>`;
        }

        // Add commands
        commands.forEach(command => {
            content += `<div class="command-block"><code>${command}</code></div>`;
        });

        // Add outputs
        outputs.forEach(output => {
            content += `<div class="output-block">${output}</div>`;
        });

        // Add metrics if provided
        if (metrics.length > 0) {
            content += `<div class="metrics-grid">`;
            metrics.forEach(metric => {
                content += `
                    <div class="metric-item">
                        <div class="metric-value">${metric.value}</div>
                        <div class="metric-label">${metric.label}</div>
                    </div>
                `;
            });
            content += `</div>`;
        }

        content += `</div>`;
        return content;
    },

    /**
     * Create a progress bar
     */
    createProgressBar(label, value, max = 100) {
        const percentage = Math.min((value / max) * 100, 100);
        return `
            <div class="progress-container">
                <div class="progress-label">
                    <span>${label}</span>
                    <span>${value}/${max}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    }
};

/**
 * Animation helpers
 */
const CollapsibleAnimations = {
    /**
     * Add a bounce animation to an element
     */
    bounce(element) {
        element.style.animation = 'none';
        element.offsetHeight; // Force reflow
        element.style.animation = 'bounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
        
        setTimeout(() => {
            element.style.animation = '';
        }, 600);
    },

    /**
     * Add a shake animation to an element
     */
    shake(element) {
        element.style.animation = 'none';
        element.offsetHeight; // Force reflow
        element.style.animation = 'shake 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97)';
        
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    },

    /**
     * Highlight an element temporarily
     */
    highlight(element, duration = 2000) {
        const originalBackground = element.style.backgroundColor;
        element.style.backgroundColor = 'rgba(0, 122, 255, 0.1)';
        element.style.transition = 'background-color 0.3s ease';
        
        setTimeout(() => {
            element.style.backgroundColor = originalBackground;
            setTimeout(() => {
                element.style.transition = '';
            }, 300);
        }, duration);
    }
};

// Global instance
let collapsibleManager = null;

// Initialize when DOM is ready
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            collapsibleManager = new CollapsibleManager();
        });
    } else {
        collapsibleManager = new CollapsibleManager();
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CollapsibleManager,
        CollapsibleUtils,
        CollapsibleAnimations
    };
}

// Add CSS animations if not already present
if (typeof document !== 'undefined') {
    const existingAnimations = document.head.querySelector('#collapsible-animations');
    if (!existingAnimations) {
        const style = document.createElement('style');
        style.id = 'collapsible-animations';
        style.textContent = `
            @keyframes bounce {
                0%, 20%, 53%, 80%, 100% {
                    transform: translate3d(0,0,0);
                }
                40%, 43% {
                    transform: translate3d(0, -10px, 0);
                }
                70% {
                    transform: translate3d(0, -5px, 0);
                }
                90% {
                    transform: translate3d(0, -2px, 0);
                }
            }

            @keyframes shake {
                10%, 90% {
                    transform: translate3d(-1px, 0, 0);
                }
                20%, 80% {
                    transform: translate3d(2px, 0, 0);
                }
                30%, 50%, 70% {
                    transform: translate3d(-4px, 0, 0);
                }
                40%, 60% {
                    transform: translate3d(4px, 0, 0);
                }
            }
        `;
        document.head.appendChild(style);
    }
}
