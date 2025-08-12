const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

/**
 * Comprehensive Frontend-Backend Integration Test Suite
 * Tests the multi-API chat application's frontend and backend integration
 */

class IntegrationTestSuite {
    constructor() {
        this.browser = null;
        this.page = null;
        this.baseUrl = 'http://localhost:7001';
        this.backendUrl = 'http://localhost:7002';
        this.testResults = [];
        this.screenshots = [];
        this.startTime = Date.now();
    }

    async setup() {
        console.log('🚀 Setting up browser and page...');
        
        this.browser = await puppeteer.launch({
            headless: false, // Set to true for CI/CD
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
            console.log(`🌐 CONSOLE: ${msg.type()}: ${msg.text()}`);
        });

        // Add network monitoring
        this.page.on('response', response => {
            if (response.url().includes(this.backendUrl)) {
                console.log(`🔗 BACKEND REQUEST: ${response.status()} ${response.url()}`);
            }
        });

        // Add error handling
        this.page.on('pageerror', error => {
            console.error(`❌ PAGE ERROR: ${error.message}`);
        });
    }

    async runTest(testName, testFunction) {
        const startTime = Date.now();
        console.log(`\n🧪 Running test: ${testName}`);
        
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
            
            throw error;
        }
    }

    async takeScreenshot(filename) {
        try {
            // Ensure directory exists
            const dir = path.dirname(filename);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            
            await this.page.screenshot({ path: filename, fullPage: true });
            this.screenshots.push(filename);
            console.log(`📸 Screenshot saved: ${filename}`);
        } catch (error) {
            console.error(`Failed to take screenshot: ${error.message}`);
        }
    }

    // Test 1: Backend Health Check
    async testBackendHealth() {
        return await this.runTest('Backend Health Check', async () => {
            const response = await this.page.evaluate(async (backendUrl) => {
                try {
                    const res = await fetch(`${backendUrl}/api/health`);
                    return await res.json();
                } catch (error) {
                    throw new Error(`Backend health check failed: ${error.message}`);
                }
            }, this.backendUrl);

            if (response.status !== 'healthy') {
                throw new Error('Backend is not healthy');
            }

            return response;
        });
    }

    // Test 2: Frontend Page Load
    async testFrontendPageLoad() {
        return await this.runTest('Frontend Page Load', async () => {
            const response = await this.page.goto(this.baseUrl, { 
                waitUntil: 'networkidle2',
                timeout: 30000 
            });
            
            if (!response.ok()) {
                throw new Error(`Failed to load page: ${response.status()}`);
            }

            // Check if main elements are present
            const title = await this.page.title();
            if (!title.includes('Multi-API Chat')) {
                throw new Error(`Unexpected page title: ${title}`);
            }

            // Check key elements
            const elements = await this.page.evaluate(() => {
                return {
                    header: !!document.querySelector('header h1'),
                    navigation: !!document.querySelector('nav'),
                    chatContainer: !!document.querySelector('.chat-container'),
                    providerSelect: !!document.querySelector('.provider-select'),
                    modelSelect: !!document.querySelector('.model-select'),
                    messageInput: !!document.querySelector('.message-input'),
                    sendButton: !!document.querySelector('.send-button')
                };
            });

            const missingElements = Object.entries(elements)
                .filter(([key, value]) => !value)
                .map(([key]) => key);

            if (missingElements.length > 0) {
                throw new Error(`Missing elements: ${missingElements.join(', ')}`);
            }

            return elements;
        });
    }

    // Test 3: Provider Configuration Load
    async testProviderConfigurationLoad() {
        return await this.runTest('Provider Configuration Load', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });

            // Wait for providers to load
            await this.page.waitForSelector('.provider-select option', { timeout: 10000 });

            const providers = await this.page.evaluate(() => {
                const options = document.querySelectorAll('.provider-select option');
                return Array.from(options).map(option => ({
                    value: option.value,
                    text: option.textContent
                })).filter(opt => opt.value); // Filter out empty options
            });

            if (providers.length === 0) {
                throw new Error('No providers loaded');
            }

            // Check if expected providers are present
            const expectedProviders = ['groq', 'cerebras', 'openrouter', 'ollama'];
            const loadedProviderIds = providers.map(p => p.value);
            
            const missingProviders = expectedProviders.filter(id => !loadedProviderIds.includes(id));
            if (missingProviders.length > 0) {
                console.warn(`Missing providers: ${missingProviders.join(', ')}`);
            }

            return {
                providers,
                count: providers.length,
                loadedProviderIds
            };
        });
    }

    // Test 4: Provider Selection and Model Loading
    async testProviderSelectionModelLoading() {
        return await this.runTest('Provider Selection and Model Loading', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });

            // Wait for providers to load
            await this.page.waitForSelector('.provider-select option', { timeout: 10000 });

            // Select a provider (groq as it's usually available)
            await this.page.select('.provider-select', 'groq');

            // Wait for models to load
            await this.page.waitForFunction(() => {
                const modelSelect = document.querySelector('.model-select');
                return modelSelect && modelSelect.children.length > 1 && 
                       !modelSelect.disabled && 
                       !modelSelect.textContent.includes('Loading');
            }, { timeout: 15000 });

            const models = await this.page.evaluate(() => {
                const options = document.querySelectorAll('.model-select option');
                return Array.from(options).map(option => ({
                    value: option.value,
                    text: option.textContent
                })).filter(opt => opt.value);
            });

            if (models.length === 0) {
                throw new Error('No models loaded for selected provider');
            }

            return {
                selectedProvider: 'groq',
                models,
                modelCount: models.length
            };
        });
    }

    // Test 5: Chat Message Sending
    async testChatMessageSending() {
        return await this.runTest('Chat Message Sending', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });

            // Wait for providers and select one
            await this.page.waitForSelector('.provider-select option', { timeout: 10000 });
            await this.page.select('.provider-select', 'groq');

            // Wait for models to load and select one
            await this.page.waitForFunction(() => {
                const modelSelect = document.querySelector('.model-select');
                return modelSelect && modelSelect.children.length > 1 && !modelSelect.disabled;
            }, { timeout: 15000 });

            // Type a test message
            const testMessage = 'Hello, this is a test message. Please respond with "Test received".';
            await this.page.type('.message-input', testMessage);

            // Click send button
            await this.page.click('.send-button');

            // Wait for response
            await this.page.waitForFunction(() => {
                const messages = document.querySelectorAll('.message');
                return messages.length >= 2; // User message + AI response
            }, { timeout: 30000 });

            // Check messages
            const messages = await this.page.evaluate(() => {
                return Array.from(document.querySelectorAll('.message')).map(msg => ({
                    type: msg.classList.contains('user-message') ? 'user' : 'ai',
                    content: msg.querySelector('.message-content')?.textContent || '',
                    timestamp: msg.querySelector('.message-timestamp')?.textContent || ''
                }));
            });

            if (messages.length < 2) {
                throw new Error('Expected at least 2 messages (user + AI response)');
            }

            const userMessage = messages.find(m => m.type === 'user');
            const aiMessage = messages.find(m => m.type === 'ai');

            if (!userMessage || userMessage.content !== testMessage) {
                throw new Error('User message not found or content mismatch');
            }

            if (!aiMessage || aiMessage.content.length < 5) {
                throw new Error('AI response not found or too short');
            }

            return {
                userMessage,
                aiMessage,
                totalMessages: messages.length
            };
        });
    }

    // Test 6: Settings Page Navigation and Functionality
    async testSettingsPageFunctionality() {
        return await this.runTest('Settings Page Functionality', async () => {
            // Navigate to settings page
            const settingsUrl = `${this.baseUrl}/settings.html`;
            await this.page.goto(settingsUrl, { waitUntil: 'networkidle2' });

            // Check if settings elements are present
            const elements = await this.page.evaluate(() => {
                return {
                    providerSettings: !!document.querySelector('.provider-settings'),
                    apiKeyInputs: document.querySelectorAll('input[type="password"]').length,
                    enabledCheckboxes: document.querySelectorAll('input[type="checkbox"]').length,
                    saveButton: !!document.querySelector('.save-button, button[type="submit"]'),
                    testButtons: document.querySelectorAll('.test-button, button[data-test]').length
                };
            });

            if (!elements.providerSettings) {
                throw new Error('Provider settings section not found');
            }

            // Test provider configuration
            const providerCount = await this.page.evaluate(() => {
                const providerSections = document.querySelectorAll('.provider-card, .provider-section');
                return providerSections.length;
            });

            if (providerCount === 0) {
                throw new Error('No provider configuration sections found');
            }

            return {
                elements,
                providerCount,
                hasApiKeyInputs: elements.apiKeyInputs > 0,
                hasEnabledCheckboxes: elements.enabledCheckboxes > 0
            };
        });
    }

    // Test 7: Operations Page Router Management
    async testOperationsPageRouterManagement() {
        return await this.runTest('Operations Page Router Management', async () => {
            const operationsUrl = `${this.baseUrl}/operations.html`;
            await this.page.goto(operationsUrl, { waitUntil: 'networkidle2' });

            // Check router management elements
            const elements = await this.page.evaluate(() => {
                return {
                    devicesList: !!document.querySelector('.devices-list, .router-list'),
                    addDeviceButton: !!document.querySelector('.add-device, .add-router'),
                    deviceCards: document.querySelectorAll('.device-card, .router-card').length,
                    commandInterface: !!document.querySelector('.command-interface, .command-input')
                };
            });

            // Check if devices are loaded
            const deviceCount = await this.page.evaluate(async () => {
                try {
                    const response = await fetch('http://localhost:7002/api/devices');
                    const data = await response.json();
                    return Object.keys(data).length;
                } catch (error) {
                    return 0;
                }
            });

            return {
                elements,
                deviceCount,
                hasDeviceManagement: elements.devicesList && elements.addDeviceButton
            };
        });
    }

    // Test 8: Dashboard Analytics
    async testDashboardAnalytics() {
        return await this.runTest('Dashboard Analytics', async () => {
            const dashboardUrl = `${this.baseUrl}/dashboard.html`;
            await this.page.goto(dashboardUrl, { waitUntil: 'networkidle2' });

            // Wait for dashboard to load
            await this.page.waitForTimeout(3000);

            const analytics = await this.page.evaluate(async () => {
                // Check for analytics elements
                const elements = {
                    usageCharts: document.querySelectorAll('.chart, .usage-chart, canvas').length,
                    statsCards: document.querySelectorAll('.stat-card, .metrics-card').length,
                    providerStatus: document.querySelectorAll('.provider-status, .status-indicator').length
                };

                // Try to fetch usage data
                let usageData = null;
                try {
                    const response = await fetch('http://localhost:7002/api/usage');
                    usageData = await response.json();
                } catch (error) {
                    console.warn('Could not fetch usage data:', error.message);
                }

                return {
                    elements,
                    usageData,
                    hasAnalytics: elements.usageCharts > 0 || elements.statsCards > 0
                };
            });

            return analytics;
        });
    }

    // Test 9: Automation Workflow Functionality
    async testAutomationWorkflowFunctionality() {
        return await this.runTest('Automation Workflow Functionality', async () => {
            const automationUrl = `${this.baseUrl}/automation.html`;
            await this.page.goto(automationUrl, { waitUntil: 'networkidle2' });

            const elements = await this.page.evaluate(() => {
                return {
                    workflowInterface: !!document.querySelector('.workflow-interface, .automation-panel'),
                    naturalLanguageInput: !!document.querySelector('.natural-input, textarea[placeholder*="describe"], input[placeholder*="request"]'),
                    generateConfigButton: !!document.querySelector('.generate-config, .process-request'),
                    deviceSelections: document.querySelectorAll('.device-select, select[name*="device"]').length,
                    executionButtons: document.querySelectorAll('.execute-workflow, .run-automation').length
                };
            });

            const hasAutomationFeatures = elements.workflowInterface && 
                                        elements.naturalLanguageInput && 
                                        elements.generateConfigButton;

            return {
                elements,
                hasAutomationFeatures,
                deviceSelections: elements.deviceSelections
            };
        });
    }

    // Test 10: API Error Handling
    async testAPIErrorHandling() {
        return await this.runTest('API Error Handling', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });

            // Test with invalid backend URL to trigger error handling
            const errorHandling = await this.page.evaluate(async () => {
                // Override fetch to simulate network errors
                const originalFetch = window.fetch;
                let errorCaught = false;

                try {
                    // Try to fetch from non-existent endpoint
                    const response = await fetch('http://localhost:7002/api/nonexistent');
                    return {
                        errorCaught: response.status >= 400,
                        statusCode: response.status,
                        errorHandled: true
                    };
                } catch (error) {
                    return {
                        errorCaught: true,
                        error: error.message,
                        errorHandled: true
                    };
                }
            });

            // Test frontend error display
            await this.page.type('.message-input', 'Test error handling');
            
            // Simulate network failure by intercepting requests
            await this.page.setRequestInterception(true);
            this.page.on('request', request => {
                if (request.url().includes('/api/chat')) {
                    request.abort();
                } else {
                    request.continue();
                }
            });

            await this.page.click('.send-button');

            // Wait for error message to appear
            await this.page.waitForTimeout(3000);

            const errorDisplayed = await this.page.evaluate(() => {
                const errorMessages = document.querySelectorAll('.error-message, .message.error, [class*="error"]');
                return errorMessages.length > 0;
            });

            // Reset request interception
            await this.page.setRequestInterception(false);

            return {
                apiErrorHandling: errorHandling,
                frontendErrorDisplay: errorDisplayed,
                errorHandlingWorking: errorHandling.errorCaught && errorDisplayed
            };
        });
    }

    // Test 11: Responsive Design and Mobile Compatibility
    async testResponsiveDesign() {
        return await this.runTest('Responsive Design', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });

            const viewports = [
                { width: 1920, height: 1080, name: 'Desktop' },
                { width: 1366, height: 768, name: 'Laptop' },
                { width: 768, height: 1024, name: 'Tablet' },
                { width: 375, height: 667, name: 'Mobile' }
            ];

            const responsiveTests = [];

            for (const viewport of viewports) {
                await this.page.setViewport({ width: viewport.width, height: viewport.height });
                await this.page.waitForTimeout(1000);

                const layout = await this.page.evaluate(() => {
                    const chatContainer = document.querySelector('.chat-container');
                    const navigation = document.querySelector('nav');
                    const header = document.querySelector('header');
                    
                    return {
                        chatContainerVisible: chatContainer ? 
                            window.getComputedStyle(chatContainer).display !== 'none' : false,
                        navigationVisible: navigation ? 
                            window.getComputedStyle(navigation).display !== 'none' : false,
                        headerVisible: header ? 
                            window.getComputedStyle(header).display !== 'none' : false,
                        bodyWidth: document.body.clientWidth,
                        scrollWidth: document.body.scrollWidth
                    };
                });

                responsiveTests.push({
                    viewport: viewport.name,
                    dimensions: `${viewport.width}x${viewport.height}`,
                    layout,
                    isResponsive: layout.scrollWidth <= layout.bodyWidth + 50 // Allow small variance
                });

                // Take screenshot for each viewport
                await this.takeScreenshot(`./test_screenshots/responsive_${viewport.name.toLowerCase()}_${Date.now()}.png`);
            }

            // Reset to default viewport
            await this.page.setViewport({ width: 1366, height: 768 });

            const allResponsive = responsiveTests.every(test => test.isResponsive);

            return {
                responsiveTests,
                allViewportsResponsive: allResponsive,
                testedViewports: responsiveTests.length
            };
        });
    }

    // Test 12: Performance and Load Times
    async testPerformanceLoadTimes() {
        return await this.runTest('Performance and Load Times', async () => {
            const performanceMetrics = {};

            // Test main page load time
            const startTime = Date.now();
            const response = await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });
            const loadTime = Date.now() - startTime;

            performanceMetrics.pageLoadTime = loadTime;

            // Get detailed performance metrics
            const metrics = await this.page.evaluate(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                if (perfData) {
                    return {
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
                        totalResourceSize: performance.getEntriesByType('resource')
                            .reduce((total, resource) => total + (resource.transferSize || 0), 0)
                    };
                }
                return null;
            });

            // Test API response times
            const apiTests = [
                { endpoint: '/api/health', expected: 500 },
                { endpoint: '/api/providers', expected: 1000 },
                { endpoint: '/api/settings', expected: 500 }
            ];

            const apiPerformance = [];

            for (const test of apiTests) {
                const apiStart = Date.now();
                try {
                    await this.page.evaluate(async (endpoint, backendUrl) => {
                        const response = await fetch(`${backendUrl}${endpoint}`);
                        return await response.json();
                    }, test.endpoint, this.backendUrl);
                    
                    const apiTime = Date.now() - apiStart;
                    apiPerformance.push({
                        endpoint: test.endpoint,
                        responseTime: apiTime,
                        withinExpected: apiTime <= test.expected,
                        expected: test.expected
                    });
                } catch (error) {
                    apiPerformance.push({
                        endpoint: test.endpoint,
                        error: error.message,
                        withinExpected: false
                    });
                }
            }

            return {
                pageLoadTime: loadTime,
                metrics,
                apiPerformance,
                allAPIsFast: apiPerformance.every(api => api.withinExpected),
                performanceGrade: loadTime <= 3000 ? 'A' : loadTime <= 5000 ? 'B' : 'C'
            };
        });
    }

    // Generate comprehensive test report
    async generateTestReport() {
        const endTime = Date.now();
        const totalDuration = endTime - this.startTime;

        const report = {
            summary: {
                totalTests: this.testResults.length,
                passed: this.testResults.filter(t => t.status === 'PASS').length,
                failed: this.testResults.filter(t => t.status === 'FAIL').length,
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
            }
        };

        // Save report to file
        const reportPath = './test_reports/frontend_backend_integration_report.json';
        const reportDir = path.dirname(reportPath);
        
        if (!fs.existsSync(reportDir)) {
            fs.mkdirSync(reportDir, { recursive: true });
        }

        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

        // Generate HTML report
        const htmlReport = this.generateHTMLReport(report);
        fs.writeFileSync('./test_reports/frontend_backend_integration_report.html', htmlReport);

        return report;
    }

    generateHTMLReport(report) {
        const passedCount = report.summary.passed;
        const failedCount = report.summary.failed;
        const totalCount = report.summary.totalTests;
        const successRate = ((passedCount / totalCount) * 100).toFixed(1);

        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Frontend-Backend Integration Test Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f7; }
        .header { background: linear-gradient(135deg, #007AFF 0%, #AF52DE 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .summary-card h3 { margin: 0 0 10px 0; color: #1d1d1f; }
        .summary-card .value { font-size: 2em; font-weight: 700; margin: 10px 0; }
        .passed { color: #34C759; }
        .failed { color: #FF3B30; }
        .total { color: #007AFF; }
        .test-results { background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
        .test-results h2 { margin: 0; padding: 25px; background: #f5f5f7; border-bottom: 1px solid #d1d1d6; }
        .test-item { padding: 20px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; }
        .test-item:last-child { border-bottom: none; }
        .test-name { font-weight: 600; }
        .test-status { padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .status-pass { background: #34C759; color: white; }
        .status-fail { background: #FF3B30; color: white; }
        .test-duration { color: #8e8e93; font-size: 14px; }
        .error-message { color: #FF3B30; font-size: 14px; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Frontend-Backend Integration Test Report</h1>
        <p>Multi-API Chat Application Test Suite</p>
        <p>Generated: ${new Date(report.summary.timestamp).toLocaleString()}</p>
    </div>

    <div class="summary">
        <div class="summary-card">
            <h3>Total Tests</h3>
            <div class="value total">${totalCount}</div>
            <p>Comprehensive integration tests</p>
        </div>
        <div class="summary-card">
            <h3>Passed</h3>
            <div class="value passed">${passedCount}</div>
            <p>Successfully executed</p>
        </div>
        <div class="summary-card">
            <h3>Failed</h3>
            <div class="value failed">${failedCount}</div>
            <p>Needs attention</p>
        </div>
        <div class="summary-card">
            <h3>Success Rate</h3>
            <div class="value ${successRate >= 80 ? 'passed' : 'failed'}">${successRate}%</div>
            <p>Overall test success</p>
        </div>
        <div class="summary-card">
            <h3>Duration</h3>
            <div class="value total">${(report.summary.totalDuration / 1000).toFixed(1)}s</div>
            <p>Total execution time</p>
        </div>
        <div class="summary-card">
            <h3>Screenshots</h3>
            <div class="value total">${report.summary.screenshots.length}</div>
            <p>Visual evidence captured</p>
        </div>
    </div>

    <div class="test-results">
        <h2>Test Results Details</h2>
        ${report.results.map(test => `
            <div class="test-item">
                <div>
                    <div class="test-name">${test.name}</div>
                    <div class="test-duration">${test.duration}ms</div>
                    ${test.error ? `<div class="error-message">${test.error}</div>` : ''}
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

            console.log('\n🚀 Starting Frontend-Backend Integration Test Suite');
            console.log('=' .repeat(60));

            // Run all tests
            await this.testBackendHealth();
            await this.testFrontendPageLoad();
            await this.testProviderConfigurationLoad();
            await this.testProviderSelectionModelLoading();
            await this.testChatMessageSending();
            await this.testSettingsPageFunctionality();
            await this.testOperationsPageRouterManagement();
            await this.testDashboardAnalytics();
            await this.testAutomationWorkflowFunctionality();
            await this.testAPIErrorHandling();
            await this.testResponsiveDesign();
            await this.testPerformanceLoadTimes();

            console.log('\n📊 Generating test report...');
            const report = await this.generateTestReport();

            console.log('\n' + '=' .repeat(60));
            console.log(`✅ Test Suite Completed!`);
            console.log(`📈 Results: ${report.summary.passed}/${report.summary.totalTests} tests passed`);
            console.log(`⏱️  Total Duration: ${(report.summary.totalDuration / 1000).toFixed(1)}s`);
            console.log(`📋 Report saved to: test_reports/frontend_backend_integration_report.html`);

            if (report.summary.failed > 0) {
                console.log(`⚠️  ${report.summary.failed} test(s) failed - check report for details`);
                process.exit(1);
            }

        } catch (error) {
            console.error('❌ Test suite failed:', error.message);
            await this.takeScreenshot('./test_failures/suite_failure.png');
            process.exit(1);
        } finally {
            await this.cleanup();
        }
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    const testSuite = new IntegrationTestSuite();
    testSuite.runAllTests().catch(console.error);
}

module.exports = IntegrationTestSuite;
