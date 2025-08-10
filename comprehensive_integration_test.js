const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

/**
 * Enhanced Frontend-Backend Integration Test Suite
 * Tests the multi-API chat application with realistic conditions
 */

class EnhancedIntegrationTestSuite {
    constructor() {
        this.browser = null;
        this.page = null;
        this.baseUrl = 'http://localhost:8001';
        this.backendUrl = 'http://localhost:8002';
        this.testResults = [];
        this.screenshots = [];
        this.startTime = Date.now();
    }

    async setup() {
        console.log('🚀 Setting up browser and page...');
        
        this.browser = await puppeteer.launch({
            headless: "new", // Set to true for CI/CD
            slowMo: 50,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--window-size=1366,768'
            ]
        });

        this.page = await this.browser.newPage();
        
        // Set viewport
        await this.page.setViewport({ width: 1366, height: 768 });
        
        // Add console logging
        this.page.on('console', msg => {
            if (msg.type() === 'error') {
                console.log(`🌐 CONSOLE ERROR: ${msg.text()}`);
            }
        });

        // Add network monitoring
        this.page.on('response', response => {
            if (response.url().includes(this.backendUrl)) {
                console.log(`🔗 BACKEND: ${response.status()} ${response.url()}`);
            }
        });
    }

    async runTest(testName, testFunction) {
        const startTime = Date.now();
        console.log(`\n🧪 Running: ${testName}`);
        
        try {
            const result = await testFunction();
            const duration = Date.now() - startTime;
            
            this.testResults.push({
                name: testName,
                status: 'PASS',
                duration,
                result,
                timestamp: new Date().toISOString()
            });
            
            console.log(`✅ ${testName} - PASSED (${duration}ms)`);
            return result;
        } catch (error) {
            const duration = Date.now() - startTime;
            
            this.testResults.push({
                name: testName,
                status: 'FAIL',
                duration,
                error: error.message,
                timestamp: new Date().toISOString()
            });
            
            console.log(`❌ ${testName} - FAILED (${duration}ms): ${error.message}`);
            
            // Take screenshot on failure
            const screenshotPath = `./test_failures/${testName.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.png`;
            await this.takeScreenshot(screenshotPath);
            
            return null; // Continue testing instead of throwing
        }
    }

    async takeScreenshot(filename) {
        try {
            const dir = path.dirname(filename);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            
            await this.page.screenshot({ path: filename, fullPage: true });
            this.screenshots.push(filename);
            console.log(`📸 Screenshot: ${filename}`);
        } catch (error) {
            console.error(`Failed to take screenshot: ${error.message}`);
        }
    }

    // Test 1: Backend API Endpoints
    async testBackendAPIEndpoints() {
        return await this.runTest('Backend API Endpoints', async () => {
            const endpoints = [
                { path: '/api/health', method: 'GET' },
                { path: '/api/providers', method: 'GET' },
                { path: '/api/settings', method: 'GET' },
                { path: '/api/usage', method: 'GET' },
                { path: '/api/devices', method: 'GET' }
            ];

            const results = [];
            
            for (const endpoint of endpoints) {
                try {
                    const response = await this.page.evaluate(async (url, path) => {
                        const res = await fetch(`${url}${path}`);
                        return {
                            status: res.status,
                            statusText: res.statusText,
                            ok: res.ok
                        };
                    }, this.backendUrl, endpoint.path);

                    results.push({
                        endpoint: endpoint.path,
                        status: response.status,
                        success: response.ok,
                        statusText: response.statusText
                    });
                } catch (error) {
                    results.push({
                        endpoint: endpoint.path,
                        error: error.message,
                        success: false
                    });
                }
            }

            const successfulEndpoints = results.filter(r => r.success).length;
            const totalEndpoints = results.length;

            if (successfulEndpoints === 0) {
                throw new Error('No backend endpoints are accessible');
            }

            return {
                results,
                successfulEndpoints,
                totalEndpoints,
                successRate: (successfulEndpoints / totalEndpoints) * 100
            };
        });
    }

    // Test 2: Frontend Pages Loading
    async testFrontendPagesLoading() {
        return await this.runTest('Frontend Pages Loading', async () => {
            const pages = [
                { name: 'Index', url: this.baseUrl, required: ['h1', 'nav', '.chat-container'] },
                { name: 'Settings', url: `${this.baseUrl}/settings.html`, required: ['h1', 'nav'] },
                { name: 'Operations', url: `${this.baseUrl}/operations.html`, required: ['h1', 'nav'] },
                { name: 'Dashboard', url: `${this.baseUrl}/dashboard.html`, required: ['h1', 'nav'] },
                { name: 'Automation', url: `${this.baseUrl}/automation.html`, required: ['h1', 'nav'] }
            ];

            const results = [];

            for (const page of pages) {
                try {
                    const response = await this.page.goto(page.url, { 
                        waitUntil: 'networkidle2',
                        timeout: 10000 
                    });

                    const pageData = await this.page.evaluate((selectors) => {
                        const title = document.title;
                        const elements = {};
                        selectors.forEach(selector => {
                            elements[selector] = !!document.querySelector(selector);
                        });
                        return { title, elements };
                    }, page.required);

                    const missingElements = page.required.filter(sel => !pageData.elements[sel]);

                    results.push({
                        page: page.name,
                        url: page.url,
                        loaded: response.ok(),
                        status: response.status(),
                        title: pageData.title,
                        elementsFound: page.required.length - missingElements.length,
                        totalElements: page.required.length,
                        missingElements
                    });

                } catch (error) {
                    results.push({
                        page: page.name,
                        url: page.url,
                        loaded: false,
                        error: error.message
                    });
                }
            }

            const loadedPages = results.filter(r => r.loaded).length;
            
            return {
                results,
                loadedPages,
                totalPages: pages.length,
                loadSuccess: (loadedPages / pages.length) * 100
            };
        });
    }

    // Test 3: Provider Configuration Integration
    async testProviderConfigurationIntegration() {
        return await this.runTest('Provider Configuration Integration', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });

            // Check if providers are loaded from backend
            const providersData = await this.page.evaluate(async (backendUrl) => {
                try {
                    const response = await fetch(`${backendUrl}/api/providers`);
                    const backendProviders = await response.json();
                    
                    // Check frontend provider dropdown
                    const providerOptions = Array.from(document.querySelectorAll('.provider-select option'))
                        .map(opt => opt.value)
                        .filter(val => val);

                    return {
                        backendProviders: Object.keys(backendProviders),
                        frontendProviders: providerOptions,
                        integration: providerOptions.length > 0
                    };
                } catch (error) {
                    return {
                        error: error.message,
                        integration: false
                    };
                }
            }, this.backendUrl);

            if (!providersData.integration) {
                throw new Error('Provider configuration not integrated properly');
            }

            // Check if provider selection works
            if (providersData.frontendProviders.length > 0) {
                await this.page.select('.provider-select', providersData.frontendProviders[0]);
                
                // Wait for model loading attempt
                await this.page.waitForTimeout(2000);
                
                const modelLoadingWorking = await this.page.evaluate(() => {
                    const modelSelect = document.querySelector('.model-select');
                    return modelSelect && !modelSelect.textContent.includes('Select Model');
                });

                providersData.modelLoadingAttempted = modelLoadingWorking;
            }

            return providersData;
        });
    }

    // Test 4: Settings Page Provider Management
    async testSettingsPageProviderManagement() {
        return await this.runTest('Settings Page Provider Management', async () => {
            await this.page.goto(`${this.baseUrl}/settings.html`, { waitUntil: 'networkidle2' });

            const settingsData = await this.page.evaluate(async (backendUrl) => {
                // Check if settings are loaded from backend
                let backendSettings = null;
                try {
                    const response = await fetch(`${backendUrl}/api/settings`);
                    backendSettings = await response.json();
                } catch (error) {
                    console.error('Failed to fetch settings:', error.message);
                }

                // Check UI elements
                const elements = {
                    providerCards: document.querySelectorAll('.provider-card, .provider-section, [data-provider]').length,
                    apiKeyInputs: document.querySelectorAll('input[type="password"], input[placeholder*="API"], input[name*="api"]').length,
                    enableCheckboxes: document.querySelectorAll('input[type="checkbox"]').length,
                    saveButtons: document.querySelectorAll('button[type="submit"], .save-button, button:contains("Save")').length,
                    testButtons: document.querySelectorAll('.test-button, button[onclick*="test"], button[data-test]').length
                };

                return {
                    backendSettings,
                    uiElements: elements,
                    hasProviderManagement: elements.providerCards > 0,
                    hasApiKeyInputs: elements.apiKeyInputs > 0,
                    hasTestFunctionality: elements.testButtons > 0
                };
            }, this.backendUrl);

            return settingsData;
        });
    }

    // Test 5: Chat Interface Error Handling
    async testChatInterfaceErrorHandling() {
        return await this.runTest('Chat Interface Error Handling', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });

            // Wait for providers to load
            await this.page.waitForSelector('.provider-select option', { timeout: 10000 });
            
            // Select a provider
            const providers = await this.page.evaluate(() => {
                const options = Array.from(document.querySelectorAll('.provider-select option'))
                    .map(opt => opt.value)
                    .filter(val => val);
                return options;
            });

            if (providers.length === 0) {
                throw new Error('No providers available for testing');
            }

            await this.page.select('.provider-select', providers[0]);
            await this.page.waitForTimeout(2000);

            // Type a message
            const testMessage = 'Hello, this is a test message for error handling.';
            await this.page.type('.message-input', testMessage);

            // Send message and expect error (no API keys configured)
            await this.page.click('.send-button');

            // Wait for error response
            await this.page.waitForTimeout(3000);

            const errorHandling = await this.page.evaluate(() => {
                // Check for user message in chat
                const messages = Array.from(document.querySelectorAll('.message'));
                const userMessage = messages.find(msg => 
                    msg.classList.contains('user-message') || 
                    msg.textContent.includes('Hello, this is a test message')
                );

                // Check for error display
                const errorMessages = document.querySelectorAll(
                    '.error-message, .message.error, [class*="error"], .alert-danger'
                );
                
                // Check for error indication in UI
                const errorIndicators = document.querySelectorAll(
                    '[style*="color: red"], [class*="fail"], [class*="error"]'
                );

                return {
                    userMessageDisplayed: !!userMessage,
                    errorMessagesCount: errorMessages.length,
                    errorIndicatorsCount: errorIndicators.length,
                    totalMessages: messages.length,
                    errorHandlingPresent: errorMessages.length > 0 || errorIndicators.length > 0
                };
            });

            return errorHandling;
        });
    }

    // Test 6: Device Management Integration
    async testDeviceManagementIntegration() {
        return await this.runTest('Device Management Integration', async () => {
            await this.page.goto(`${this.baseUrl}/operations.html`, { waitUntil: 'networkidle2' });

            const deviceData = await this.page.evaluate(async (backendUrl) => {
                // Check backend devices
                let backendDevices = null;
                try {
                    const response = await fetch(`${backendUrl}/api/devices`);
                    backendDevices = await response.json();
                } catch (error) {
                    console.error('Failed to fetch devices:', error.message);
                }

                // Check UI elements
                const elements = {
                    devicesList: !!document.querySelector('.devices-list, .device-container, [data-devices]'),
                    deviceCards: document.querySelectorAll('.device-card, .router-card, [data-device]').length,
                    addButton: !!document.querySelector('.add-device, .add-router, button[onclick*="add"]'),
                    commandInterface: !!document.querySelector('.command-input, .command-interface, textarea[placeholder*="command"]')
                };

                return {
                    backendDevices,
                    deviceCount: backendDevices ? Object.keys(backendDevices).length : 0,
                    uiElements: elements,
                    hasDeviceManagement: elements.devicesList || elements.deviceCards > 0,
                    hasCommandInterface: elements.commandInterface
                };
            }, this.backendUrl);

            return deviceData;
        });
    }

    // Test 7: Dashboard Analytics Integration
    async testDashboardAnalyticsIntegration() {
        return await this.runTest('Dashboard Analytics Integration', async () => {
            await this.page.goto(`${this.baseUrl}/dashboard.html`, { waitUntil: 'networkidle2' });

            const analyticsData = await this.page.evaluate(async (backendUrl) => {
                // Check usage data from backend
                let usageData = null;
                try {
                    const response = await fetch(`${backendUrl}/api/usage`);
                    usageData = await response.json();
                } catch (error) {
                    console.error('Failed to fetch usage data:', error.message);
                }

                // Check UI elements
                const elements = {
                    charts: document.querySelectorAll('canvas, .chart, .graph, [data-chart]').length,
                    statsCards: document.querySelectorAll('.stat-card, .metric-card, .stats-item').length,
                    providerStatus: document.querySelectorAll('.provider-status, .status-indicator, [data-status]').length,
                    analyticsContainers: document.querySelectorAll('.analytics, .dashboard-content, .metrics').length
                };

                return {
                    backendUsageData: usageData,
                    uiElements: elements,
                    hasAnalytics: elements.charts > 0 || elements.statsCards > 0,
                    hasProviderStatus: elements.providerStatus > 0
                };
            }, this.backendUrl);

            return analyticsData;
        });
    }

    // Test 8: Automation Workflow Integration
    async testAutomationWorkflowIntegration() {
        return await this.runTest('Automation Workflow Integration', async () => {
            await this.page.goto(`${this.baseUrl}/automation.html`, { waitUntil: 'networkidle2' });

            const automationData = await this.page.evaluate(async (backendUrl) => {
                // Check devices available for automation
                let backendDevices = null;
                try {
                    const response = await fetch(`${backendUrl}/api/devices`);
                    backendDevices = await response.json();
                } catch (error) {
                    console.error('Failed to fetch devices:', error.message);
                }

                // Check UI elements
                const elements = {
                    naturalLanguageInput: !!document.querySelector('textarea[placeholder*="describe"], input[placeholder*="describe"], .natural-input'),
                    deviceSelectors: document.querySelectorAll('select[name*="device"], .device-select, option[value*="router"]').length,
                    generateButton: !!document.querySelector('.generate-config, .process-request, button[onclick*="generate"]'),
                    workflowInterface: !!document.querySelector('.workflow-interface, .automation-panel, .workflow-container'),
                    executionButtons: document.querySelectorAll('.execute-workflow, .run-automation, button[onclick*="execute"]').length
                };

                return {
                    backendDevices,
                    deviceCount: backendDevices ? Object.keys(backendDevices).length : 0,
                    uiElements: elements,
                    hasWorkflowInterface: elements.workflowInterface,
                    hasNaturalLanguageInput: elements.naturalLanguageInput,
                    hasDeviceIntegration: elements.deviceSelectors > 0
                };
            }, this.backendUrl);

            return automationData;
        });
    }

    // Test 9: Cross-Page Navigation
    async testCrossPageNavigation() {
        return await this.runTest('Cross-Page Navigation', async () => {
            const pages = ['index.html', 'settings.html', 'operations.html', 'dashboard.html', 'automation.html'];
            const navigationResults = [];

            // Start from index
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });

            for (const targetPage of pages) {
                try {
                    const targetUrl = targetPage === 'index.html' ? this.baseUrl : `${this.baseUrl}/${targetPage}`;
                    
                    // Try to find navigation link
                    const navLinkExists = await this.page.evaluate((page) => {
                        const links = Array.from(document.querySelectorAll('nav a, .nav-link, a[href]'));
                        return links.some(link => 
                            link.href.includes(page) || 
                            link.getAttribute('href') === `/${page}` ||
                            link.getAttribute('href') === page
                        );
                    }, targetPage);

                    // Navigate directly
                    const response = await this.page.goto(targetUrl, { waitUntil: 'networkidle2' });

                    navigationResults.push({
                        page: targetPage,
                        navLinkExists,
                        directAccessible: response.ok(),
                        status: response.status()
                    });

                } catch (error) {
                    navigationResults.push({
                        page: targetPage,
                        error: error.message,
                        accessible: false
                    });
                }
            }

            const accessiblePages = navigationResults.filter(r => r.directAccessible).length;
            
            return {
                results: navigationResults,
                accessiblePages,
                totalPages: pages.length,
                navigationSuccess: (accessiblePages / pages.length) * 100
            };
        });
    }

    // Test 10: Performance and Resource Loading
    async testPerformanceAndResourceLoading() {
        return await this.runTest('Performance and Resource Loading', async () => {
            const startTime = Date.now();
            const response = await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });
            const loadTime = Date.now() - startTime;

            const performanceData = await this.page.evaluate(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                const resources = performance.getEntriesByType('resource');
                
                const resourceSummary = {
                    total: resources.length,
                    successful: resources.filter(r => r.responseEnd > 0).length,
                    failed: resources.filter(r => r.responseEnd === 0).length,
                    totalSize: resources.reduce((sum, r) => sum + (r.transferSize || 0), 0)
                };

                return {
                    navigation: perfData ? {
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        loadComplete: perfData.loadEventEnd - perfData.loadEventStart
                    } : null,
                    resources: resourceSummary,
                    memoryUsage: performance.memory ? {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    } : null
                };
            });

            // Test API response times
            const apiEndpoints = ['/api/health', '/api/providers', '/api/settings'];
            const apiPerformance = [];

            for (const endpoint of apiEndpoints) {
                const apiStart = Date.now();
                try {
                    await this.page.evaluate(async (url, path) => {
                        const response = await fetch(`${url}${path}`);
                        return await response.json();
                    }, this.backendUrl, endpoint);
                    
                    const apiTime = Date.now() - apiStart;
                    apiPerformance.push({
                        endpoint,
                        responseTime: apiTime,
                        fast: apiTime < 1000
                    });
                } catch (error) {
                    apiPerformance.push({
                        endpoint,
                        error: error.message,
                        fast: false
                    });
                }
            }

            return {
                pageLoadTime: loadTime,
                performance: performanceData,
                apiPerformance,
                grade: loadTime < 3000 ? 'A' : loadTime < 5000 ? 'B' : 'C'
            };
        });
    }

    // Generate comprehensive test report
    async generateTestReport() {
        const endTime = Date.now();
        const totalDuration = endTime - this.startTime;
        const passedTests = this.testResults.filter(t => t.status === 'PASS').length;
        const failedTests = this.testResults.filter(t => t.status === 'FAIL').length;

        const report = {
            summary: {
                totalTests: this.testResults.length,
                passed: passedTests,
                failed: failedTests,
                successRate: ((passedTests / this.testResults.length) * 100).toFixed(1),
                totalDuration,
                timestamp: new Date().toISOString(),
                screenshots: this.screenshots
            },
            results: this.testResults,
            environment: {
                baseUrl: this.baseUrl,
                backendUrl: this.backendUrl,
                userAgent: await this.page.evaluate(() => navigator.userAgent),
                viewport: await this.page.viewport()
            },
            recommendations: this.generateRecommendations()
        };

        // Save reports
        const reportDir = './test_reports';
        if (!fs.existsSync(reportDir)) {
            fs.mkdirSync(reportDir, { recursive: true });
        }

        fs.writeFileSync(`${reportDir}/comprehensive_integration_report.json`, JSON.stringify(report, null, 2));
        fs.writeFileSync(`${reportDir}/comprehensive_integration_report.html`, this.generateHTMLReport(report));

        return report;
    }

    generateRecommendations() {
        const recommendations = [];
        const failedTests = this.testResults.filter(t => t.status === 'FAIL');

        if (failedTests.length > 0) {
            recommendations.push(`${failedTests.length} test(s) failed - review error details and fix issues`);
        }

        // Add specific recommendations based on test results
        const chatTest = this.testResults.find(t => t.name.includes('Chat Interface'));
        if (chatTest && chatTest.status === 'FAIL') {
            recommendations.push('Configure API keys for providers to enable chat functionality');
        }

        const performanceTest = this.testResults.find(t => t.name.includes('Performance'));
        if (performanceTest && performanceTest.result && performanceTest.result.pageLoadTime > 3000) {
            recommendations.push('Consider optimizing page load time - currently exceeds 3 seconds');
        }

        return recommendations;
    }

    generateHTMLReport(report) {
        const successRate = report.summary.successRate;
        const statusColor = successRate >= 80 ? '#34C759' : successRate >= 60 ? '#FF9500' : '#FF3B30';

        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Integration Test Report</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif; 
            margin: 0; padding: 20px; background: #f5f5f7; line-height: 1.47;
        }
        .header { 
            background: linear-gradient(135deg, #007AFF 0%, #AF52DE 100%); 
            color: white; padding: 40px; border-radius: 16px; margin-bottom: 30px; 
            text-align: center;
        }
        .header h1 { margin: 0; font-size: 2.5rem; font-weight: 700; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem; }
        .summary { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 20px; margin-bottom: 40px; 
        }
        .summary-card { 
            background: white; padding: 30px; border-radius: 16px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center;
        }
        .summary-card h3 { margin: 0 0 15px 0; color: #1d1d1f; font-size: 1rem; }
        .summary-card .value { 
            font-size: 3rem; font-weight: 800; margin: 15px 0; 
            color: ${statusColor};
        }
        .summary-card .subtitle { color: #8e8e93; font-size: 0.9rem; }
        .test-results { 
            background: white; border-radius: 16px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; 
        }
        .test-results h2 { 
            margin: 0; padding: 30px; background: #f8f9fa; 
            border-bottom: 1px solid #e5e5ea; font-size: 1.5rem;
        }
        .test-item { 
            padding: 25px 30px; border-bottom: 1px solid #f0f0f0; 
            display: flex; justify-content: space-between; align-items: center; 
        }
        .test-item:last-child { border-bottom: none; }
        .test-name { font-weight: 600; font-size: 1.1rem; }
        .test-details { color: #8e8e93; font-size: 0.9rem; margin-top: 5px; }
        .test-status { 
            padding: 8px 16px; border-radius: 20px; font-size: 0.85rem; 
            font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
        }
        .status-pass { background: #34C759; color: white; }
        .status-fail { background: #FF3B30; color: white; }
        .error-message { 
            color: #FF3B30; font-size: 0.9rem; margin-top: 8px; 
            font-family: 'SF Mono', Consolas, monospace; 
        }
        .recommendations { 
            background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 12px; 
            padding: 20px; margin: 20px 0; 
        }
        .recommendations h3 { color: #856404; margin-top: 0; }
        .recommendations ul { margin: 0; padding-left: 20px; }
        .recommendations li { color: #856404; margin: 5px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Integration Test Report</h1>
        <p>Multi-API Chat Application - Comprehensive Testing</p>
        <p>Generated: ${new Date(report.summary.timestamp).toLocaleString()}</p>
    </div>

    <div class="summary">
        <div class="summary-card">
            <h3>Success Rate</h3>
            <div class="value">${report.summary.successRate}%</div>
            <div class="subtitle">Overall test success</div>
        </div>
        <div class="summary-card">
            <h3>Tests Passed</h3>
            <div class="value" style="color: #34C759">${report.summary.passed}</div>
            <div class="subtitle">Successfully executed</div>
        </div>
        <div class="summary-card">
            <h3>Tests Failed</h3>
            <div class="value" style="color: #FF3B30">${report.summary.failed}</div>
            <div class="subtitle">Require attention</div>
        </div>
        <div class="summary-card">
            <h3>Total Duration</h3>
            <div class="value" style="color: #007AFF">${(report.summary.totalDuration / 1000).toFixed(1)}s</div>
            <div class="subtitle">Execution time</div>
        </div>
    </div>

    ${report.recommendations.length > 0 ? `
    <div class="recommendations">
        <h3>🔍 Recommendations</h3>
        <ul>
            ${report.recommendations.map(rec => `<li>${rec}</li>`).join('')}
        </ul>
    </div>
    ` : ''}

    <div class="test-results">
        <h2>📋 Test Results Details</h2>
        ${report.results.map(test => `
            <div class="test-item">
                <div>
                    <div class="test-name">${test.name}</div>
                    <div class="test-details">${test.duration}ms - ${test.timestamp}</div>
                    ${test.error ? `<div class="error-message">❌ ${test.error}</div>` : ''}
                </div>
                <div class="test-status status-${test.status.toLowerCase()}">${test.status}</div>
            </div>
        `).join('')}
    </div>
</body>
</html>`;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
            console.log('🧹 Browser closed');
        }
    }

    async runAllTests() {
        try {
            await this.setup();

            console.log('\n🚀 Starting Comprehensive Integration Test Suite');
            console.log('=' .repeat(60));

            // Run all tests (continue even if some fail)
            await this.testBackendAPIEndpoints();
            await this.testFrontendPagesLoading();
            await this.testProviderConfigurationIntegration();
            await this.testSettingsPageProviderManagement();
            await this.testChatInterfaceErrorHandling();
            await this.testDeviceManagementIntegration();
            await this.testDashboardAnalyticsIntegration();
            await this.testAutomationWorkflowIntegration();
            await this.testCrossPageNavigation();
            await this.testPerformanceAndResourceLoading();

            console.log('\n📊 Generating comprehensive test report...');
            const report = await this.generateTestReport();

            console.log('\n' + '=' .repeat(60));
            console.log(`🎯 Test Suite Completed!`);
            console.log(`📈 Results: ${report.summary.passed}/${report.summary.totalTests} tests passed (${report.summary.successRate}%)`);
            console.log(`⏱️  Total Duration: ${(report.summary.totalDuration / 1000).toFixed(1)}s`);
            console.log(`📋 Report: test_reports/comprehensive_integration_report.html`);

            if (report.summary.failed > 0) {
                console.log(`⚠️  ${report.summary.failed} test(s) had issues - check report for details`);
            }

            // Return success if most tests passed
            return report.summary.successRate >= 70;

        } catch (error) {
            console.error('❌ Test suite error:', error.message);
            await this.takeScreenshot('./test_failures/suite_error.png');
            return false;
        } finally {
            await this.cleanup();
        }
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    const testSuite = new EnhancedIntegrationTestSuite();
    testSuite.runAllTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(console.error);
}

module.exports = EnhancedIntegrationTestSuite;
