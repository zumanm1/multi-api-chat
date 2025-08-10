/**
 * Progressive Disclosure JavaScript Library
 * Three-tier information architecture implementation
 */

class ProgressiveDisclosure {
    constructor(options = {}) {
        this.options = {
            persistState: true,
            storageKey: 'pd-state',
            autoCollapse: false,
            animationDuration: 300,
            debugMode: false,
            onExpand: null,
            onCollapse: null,
            onDebugToggle: null,
            ...options
        };
        
        this.state = this.loadState();
        this.instances = new Map();
        this.init();
    }

    init() {
        this.bindEvents();
        this.restoreState();
        
        if (this.options.debugMode) {
            console.log('Progressive Disclosure initialized with state:', this.state);
        }
    }

    bindEvents() {
        // Handle summary clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.pd-summary')) {
                this.toggleSummary(e.target.closest('.pd-summary'));
            }
        });

        // Handle debug toggle clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.pd-debug-toggle')) {
                e.stopPropagation();
                this.toggleDebug(e.target.closest('.pd-debug-toggle'));
            }
        });

        // Handle copy button clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.pd-command-copy')) {
                this.copyToClipboard(e.target.closest('.pd-command-copy'));
            }
        });

        // Handle keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.target.closest('.pd-summary')) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleSummary(e.target.closest('.pd-summary'));
                }
            }
        });

        // Save state on page unload
        window.addEventListener('beforeunload', () => {
            this.saveState();
        });
    }

    toggleSummary(summaryElement) {
        const container = summaryElement.closest('.progressive-disclosure');
        const id = this.getElementId(container);
        const detailsElement = summaryElement.nextElementSibling;
        
        if (!detailsElement || !detailsElement.classList.contains('pd-details')) {
            console.warn('Invalid progressive disclosure structure');
            return;
        }

        const isExpanded = summaryElement.classList.contains('expanded');
        
        if (isExpanded) {
            this.collapse(summaryElement, detailsElement, id);
        } else {
            this.expand(summaryElement, detailsElement, id);
        }
    }

    expand(summaryElement, detailsElement, id) {
        // Auto-collapse others if enabled
        if (this.options.autoCollapse) {
            this.collapseAll();
        }

        summaryElement.classList.add('expanded');
        summaryElement.setAttribute('aria-expanded', 'true');
        
        // Update state
        if (!this.state[id]) this.state[id] = {};
        this.state[id].expanded = true;
        
        // Trigger custom event
        if (this.options.onExpand) {
            this.options.onExpand(id, summaryElement);
        }

        // Dispatch custom event
        summaryElement.dispatchEvent(new CustomEvent('pd:expand', {
            detail: { id, element: summaryElement }
        }));

        this.saveState();
    }

    collapse(summaryElement, detailsElement, id) {
        summaryElement.classList.remove('expanded');
        summaryElement.setAttribute('aria-expanded', 'false');
        
        // Collapse any open debug sections
        const debugElements = detailsElement.querySelectorAll('.pd-debug.expanded');
        debugElements.forEach(debug => {
            debug.classList.remove('expanded');
        });

        // Update state
        if (!this.state[id]) this.state[id] = {};
        this.state[id].expanded = false;
        this.state[id].debugSections = {};

        // Trigger custom event
        if (this.options.onCollapse) {
            this.options.onCollapse(id, summaryElement);
        }

        // Dispatch custom event
        summaryElement.dispatchEvent(new CustomEvent('pd:collapse', {
            detail: { id, element: summaryElement }
        }));

        this.saveState();
    }

    toggleDebug(toggleElement) {
        const section = toggleElement.closest('.pd-details-section');
        const sectionId = section.dataset.section || 'default';
        const container = toggleElement.closest('.progressive-disclosure');
        const containerId = this.getElementId(container);
        const debugElement = section.querySelector('.pd-debug');
        
        if (!debugElement) {
            console.warn('No debug element found');
            return;
        }

        const isExpanded = debugElement.classList.contains('expanded');
        
        if (isExpanded) {
            debugElement.classList.remove('expanded');
            toggleElement.classList.remove('active');
            
            // Update state
            if (this.state[containerId] && this.state[containerId].debugSections) {
                this.state[containerId].debugSections[sectionId] = false;
            }
        } else {
            debugElement.classList.add('expanded');
            toggleElement.classList.add('active');
            
            // Update state
            if (!this.state[containerId]) this.state[containerId] = {};
            if (!this.state[containerId].debugSections) this.state[containerId].debugSections = {};
            this.state[containerId].debugSections[sectionId] = true;
        }

        // Trigger custom event
        if (this.options.onDebugToggle) {
            this.options.onDebugToggle(sectionId, toggleElement, !isExpanded);
        }

        // Dispatch custom event
        toggleElement.dispatchEvent(new CustomEvent('pd:debugToggle', {
            detail: { sectionId, containerId, element: toggleElement, expanded: !isExpanded }
        }));

        this.saveState();
    }

    collapseAll() {
        const expandedSummaries = document.querySelectorAll('.pd-summary.expanded');
        expandedSummaries.forEach(summary => {
            const container = summary.closest('.progressive-disclosure');
            const id = this.getElementId(container);
            const detailsElement = summary.nextElementSibling;
            this.collapse(summary, detailsElement, id);
        });
    }

    expandAll() {
        const summaries = document.querySelectorAll('.pd-summary:not(.expanded)');
        summaries.forEach(summary => {
            const container = summary.closest('.progressive-disclosure');
            const id = this.getElementId(container);
            const detailsElement = summary.nextElementSibling;
            this.expand(summary, detailsElement, id);
        });
    }

    async copyToClipboard(copyButton) {
        const commandBlock = copyButton.closest('.pd-command-block');
        const text = commandBlock.textContent.trim();
        
        try {
            await navigator.clipboard.writeText(text);
            
            // Visual feedback
            const originalText = copyButton.textContent;
            copyButton.textContent = '✓';
            copyButton.style.background = 'var(--apple-green)';
            
            setTimeout(() => {
                copyButton.textContent = originalText;
                copyButton.style.background = '';
            }, 2000);
            
        } catch (err) {
            console.error('Failed to copy text: ', err);
            
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            // Visual feedback
            copyButton.textContent = '✓';
            setTimeout(() => copyButton.textContent = 'Copy', 2000);
        }
    }

    getElementId(element) {
        if (element.id) return element.id;
        
        // Generate a unique ID based on content
        const title = element.querySelector('.pd-summary-title')?.textContent || '';
        const hash = this.simpleHash(title);
        const id = `pd-${hash}`;
        element.id = id;
        return id;
    }

    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash).toString(36);
    }

    loadState() {
        if (!this.options.persistState) return {};
        
        try {
            const saved = localStorage.getItem(this.options.storageKey);
            return saved ? JSON.parse(saved) : {};
        } catch (err) {
            console.warn('Failed to load progressive disclosure state:', err);
            return {};
        }
    }

    saveState() {
        if (!this.options.persistState) return;
        
        try {
            localStorage.setItem(this.options.storageKey, JSON.stringify(this.state));
        } catch (err) {
            console.warn('Failed to save progressive disclosure state:', err);
        }
    }

    restoreState() {
        if (!this.options.persistState || Object.keys(this.state).length === 0) return;
        
        // Restore expanded states
        Object.entries(this.state).forEach(([id, state]) => {
            const container = document.getElementById(id);
            if (!container) return;
            
            const summary = container.querySelector('.pd-summary');
            if (state.expanded && summary) {
                summary.classList.add('expanded');
                summary.setAttribute('aria-expanded', 'true');
            }
            
            // Restore debug section states
            if (state.debugSections) {
                Object.entries(state.debugSections).forEach(([sectionId, isExpanded]) => {
                    const section = container.querySelector(`[data-section="${sectionId}"]`);
                    if (section && isExpanded) {
                        const toggle = section.querySelector('.pd-debug-toggle');
                        const debug = section.querySelector('.pd-debug');
                        if (toggle && debug) {
                            toggle.classList.add('active');
                            debug.classList.add('expanded');
                        }
                    }
                });
            }
        });
    }

    // Public API methods
    createDisclosure(data) {
        return this.generateHTML(data);
    }

    generateHTML(data) {
        const {
            id,
            icon = '📋',
            title = 'Item',
            description = '',
            status = 'info',
            sections = []
        } = data;

        const statusClass = status === 'success' ? 'success' : 
                          status === 'warning' ? 'warning' :
                          status === 'error' ? 'error' : 'info';

        let sectionsHTML = sections.map((section, index) => {
            const sectionId = section.id || `section-${index}`;
            
            let parametersHTML = '';
            if (section.parameters) {
                parametersHTML = `
                    <div class="pd-parameter-grid">
                        ${Object.entries(section.parameters).map(([key, value]) => `
                            <div class="pd-parameter-item">
                                <div class="pd-parameter-label">${key}</div>
                                <div class="pd-parameter-value">${value}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            let commandHTML = '';
            if (section.command) {
                commandHTML = `
                    <div class="pd-command-block">
                        <button class="pd-command-copy">Copy</button>
                        ${section.command}
                    </div>
                `;
            }

            let debugHTML = '';
            if (section.debug) {
                const debugSections = Object.entries(section.debug).map(([key, value]) => `
                    <div class="pd-debug-section">
                        <div class="pd-debug-label">${key}</div>
                        <div class="pd-debug-value">${typeof value === 'object' ? JSON.stringify(value, null, 2) : value}</div>
                    </div>
                `).join('');

                debugHTML = `
                    <div class="pd-debug">
                        <div class="pd-debug-content">
                            <div class="pd-debug-header">
                                <span class="pd-debug-icon">🔍</span>
                                <span class="pd-debug-title">Debug Information</span>
                            </div>
                            ${debugSections}
                        </div>
                    </div>
                `;
            }

            return `
                <div class="pd-details-section" data-section="${sectionId}">
                    <div class="pd-section-header">
                        <div class="pd-section-title">
                            <span class="pd-section-icon">${section.icon || '📄'}</span>
                            ${section.title}
                        </div>
                        ${section.debug ? `
                            <div class="pd-debug-toggle">
                                <span>Debug</span>
                                <span class="pd-debug-toggle-icon">▼</span>
                            </div>
                        ` : ''}
                    </div>
                    ${parametersHTML}
                    ${commandHTML}
                    ${debugHTML}
                </div>
            `;
        }).join('');

        return `
            <div class="progressive-disclosure persistent" ${id ? `id="${id}"` : ''}>
                <div class="pd-summary" tabindex="0" role="button" aria-expanded="false">
                    <div class="pd-level-indicator"></div>
                    <div class="pd-summary-header">
                        <div class="pd-summary-icon">${icon}</div>
                        <div class="pd-summary-content">
                            <div class="pd-summary-title">${title}</div>
                            <div class="pd-summary-description">${description}</div>
                        </div>
                        <div class="pd-summary-status">
                            <div class="pd-status-indicator ${statusClass}"></div>
                            <div class="pd-expand-icon">▼</div>
                        </div>
                    </div>
                </div>
                <div class="pd-details">
                    <div class="pd-level-indicator"></div>
                    <div class="pd-details-content">
                        ${sectionsHTML}
                    </div>
                </div>
            </div>
        `;
    }

    // Utility methods
    destroy() {
        // Clean up event listeners and state
        this.saveState();
        this.instances.clear();
    }

    refresh() {
        this.restoreState();
    }

    clearState() {
        this.state = {};
        if (this.options.persistState) {
            localStorage.removeItem(this.options.storageKey);
        }
    }

    getState() {
        return { ...this.state };
    }

    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.saveState();
        this.restoreState();
    }
}

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.progressiveDisclosure = new ProgressiveDisclosure();
    });
} else {
    window.progressiveDisclosure = new ProgressiveDisclosure();
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProgressiveDisclosure;
}
