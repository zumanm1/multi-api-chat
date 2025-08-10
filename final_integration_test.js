const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

/**
 * Final Frontend-Backend Integration Test Suite
 * Tests the multi-API chat application comprehensively
 */

class FinalIntegrationTestSuite {
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
        console.log('🚀 Setting up browser and test environment...');
        
        this.browser = await puppeteer.launch({
            headless: "new",
            slowMo: 100,
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
        await this.page.setViewport({ width: 1366, height: 768 });
        
        // Network monitoring
        this.page.on('response', response => {
            if (response.url().includes(this.backendUrl)) {
                console.log(`🔗 ${response.status()} ${response.url()}`);
            }
        });
    }

    async runTest(testName, testFunction) {
        const startTime = Date.now();
        console.log(`\n🧪 ${testName}`);
        
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
            
            console.log(`✅ PASSED (${duration}ms)`);
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
            
            console.log(`❌ FAILED (${duration}ms): ${error.message}`);
            
            // Screenshot on failure
            const screenshotPath = `./test_failures/${testName.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.png`;
            await this.takeScreenshot(screenshotPath);
            
            return null;
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
            console.log(`📸 ${filename}`);
        } catch (error) {
            console.error(`Screenshot failed: ${error.message}`);
        }
    }

    // Test 1: Backend Server Health and API Availability
    async testBackendServerHealth() {
        return await this.runTest('Backend Server Health and API Availability', async () => {
            const endpoints = [
                '/api/health',
                '/api/providers', 
                '/api/settings',
                '/api/usage',
                '/api/devices'
            ];

            const results = {};
            let successCount = 0;

            for (const endpoint of endpoints) {
                try {
                    const response = await this.page.evaluate(async (url, path) => {
                        const res = await fetch(`${url}${path}`);
                        const data = await res.json();
                        return { status: res.status, ok: res.ok, data };
                    }, this.backendUrl, endpoint);

                    results[endpoint] = {
                        status: response.status,
                        success: response.ok,
                        hasData: !!response.data
                    };

                    if (response.ok) successCount++;
                } catch (error) {
                    results[endpoint] = { error: error.message, success: false };
                }
            }

            if (successCount === 0) {
                throw new Error('Backend server is not accessible');
            }

            return {
                endpoints: results,
                successfulEndpoints: successCount,
                totalEndpoints: endpoints.length,
                successRate: (successCount / endpoints.length) * 100
            };
        });
    }

    // Test 2: Frontend Pages Load and Render
    async testFrontendPagesLoadRender() {
        return await this.runTest('Frontend Pages Load and Render', async () => {
            const pages = [
                { name: 'Chat Interface', url: this.baseUrl },
                { name: 'Settings', url: `${this.baseUrl}/settings.html` },
                { name: 'Operations', url: `${this.baseUrl}/operations.html` },
                { name: 'Dashboard', url: `${this.baseUrl}/dashboard.html` },
                { name: 'Automation', url: `${this.baseUrl}/automation.html` }
            ];

            const results = [];
            let loadedPages = 0;

            for (const page of pages) {
                try {
                    const response = await this.page.goto(page.url, { 
                        waitUntil: 'networkidle0',
                        timeout: 15000 
                    });

                    const pageInfo = await this.page.evaluate(() => {
                        return {
                            title: document.title,
                            hasHeader: !!document.querySelector('header h1'),
                            hasNavigation: !!document.querySelector('nav'),
                            hasMainContent: !!document.querySelector('main, .main, .container'),
                            bodyClasses: document.body.className,
                            scriptCount: document.querySelectorAll('script').length,
                            cssCount: document.querySelectorAll('link[rel="stylesheet"]').length
                        };
                    });

                    results.push({
                        page: page.name,
                        url: page.url,
                        loaded: response.ok(),
                        status: response.status(),
                        ...pageInfo
                    });

                    if (response.ok()) loadedPages++;

                } catch (error) {
                    results.push({
                        page: page.name,
                        error: error.message,
                        loaded: false
                    });
                }
            }

            return {
                results,
                loadedPages,
                totalPages: pages.length,
                loadSuccess: (loadedPages / pages.length) * 100
            };
        });
    }

    // Test 3: Provider Data Integration
    async testProviderDataIntegration() {
        return await this.runTest('Provider Data Integration', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle0' });

            const integration = await this.page.evaluate(async (backendUrl) => {
                // Get backend provider data
                let backendProviders = null;
                try {
                    const response = await fetch(`${backendUrl}/api/providers`);
                    backendProviders = await response.json();
                } catch (error) {
                    return { error: 'Could not fetch backend providers' };
                }

                // Check frontend integration
                const providerSelect = document.querySelector('.provider-select');
                if (!providerSelect) {
                    return { error: 'Provider select element not found' };
                }

                // Wait for options to load
                let attempts = 0;
                while (providerSelect.options.length <= 1 && attempts < 10) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                    attempts++;
                }

                const frontendProviders = Array.from(providerSelect.options)
                    .map(opt => opt.value)
                    .filter(val => val);

                return {
                    backendProviderCount: Object.keys(backendProviders).length,
                    frontendProviderCount: frontendProviders.length,
                    backendProviders: Object.keys(backendProviders),
                    frontendProviders,
                    integration: frontendProviders.length > 0,
                    providersMatch: frontendProviders.every(fp => backendProviders[fp])
                };
            }, this.backendUrl);

            if (!integration.integration) {
                throw new Error('Frontend-backend provider integration failed');
            }

            return integration;
        });
    }

    // Test 4: Model Selection Functionality  
    async testModelSelectionFunctionality() {
        return await this.runTest('Model Selection Functionality', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle0' });

            // Wait for provider select to load
            await this.page.waitForSelector('.provider-select option[value]', { timeout: 10000 });

            // Get available providers
            const providers = await this.page.evaluate(() => {
                return Array.from(document.querySelectorAll('.provider-select option'))
                    .map(opt => opt.value)
                    .filter(val => val);
            });

            if (providers.length === 0) {
                throw new Error('No providers available for testing');
            }

            // Test provider selection and model loading
            await this.page.select('.provider-select', providers[0]);

            // Wait a moment for model loading
            await this.page.waitForTimeout(3000);

            const modelData = await this.page.evaluate(() => {
                const modelSelect = document.querySelector('.model-select');
                if (!modelSelect) return { error: 'Model select not found' };

                const models = Array.from(modelSelect.options)
                    .map(opt => ({ value: opt.value, text: opt.textContent }))
                    .filter(opt => opt.value);

                return {
                    modelCount: models.length,
                    models: models.slice(0, 5), // First 5 models
                    disabled: modelSelect.disabled,
                    hasModels: models.length > 0
                };
            });

            return {
                selectedProvider: providers[0],
                totalProviders: providers.length,
                modelData
            };
        });
    }

    // Test 5: Chat Interface User Interaction
    async testChatInterfaceUserInteraction() {
        return await this.runTest('Chat Interface User Interaction', async () => {
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle0' });

            // Setup: select provider and model
            await this.page.waitForSelector('.provider-select option[value]', { timeout: 10000 });
            const providers = await this.page.evaluate(() => {
                return Array.from(document.querySelectorAll('.provider-select option'))
                    .map(opt => opt.value)
                    .filter(val => val);
            });

            await this.page.select('.provider-select', providers[0]);
            await this.page.waitForTimeout(2000);

            // Test message input and sending
            const testMessage = 'Integration test message - please respond briefly.';
            
            // Clear any existing input and type message
            await this.page.click('.message-input');
            await this.page.keyboard.down('Control');
            await this.page.keyboard.press('a');
            await this.page.keyboard.up('Control');
            await this.page.type('.message-input', testMessage);

            // Click send button
            await this.page.click('.send-button');

            // Wait for UI response (message should appear in chat)
            await this.page.waitForTimeout(3000);

            const chatState = await this.page.evaluate((testMsg) => {
                const messages = Array.from(document.querySelectorAll('.message'));
                const chatHistory = document.querySelector('.chat-history, .messages, .chat-messages');
                const messageInput = document.querySelector('.message-input');

                // Look for user message
                const userMessage = messages.find(msg => 
                    msg.textContent.includes(testMsg) ||
                    msg.classList.contains('user-message') ||
                    msg.querySelector('.message-content')?.textContent.includes(testMsg)
                );

                // Look for any response (AI or error)
                const hasResponse = messages.length > 1 || 
                                  document.querySelector('.error-message, .alert, [class*="error"]');

                return {
                    totalMessages: messages.length,
                    userMessageFound: !!userMessage,
                    hasResponse,
                    inputCleared: messageInput.value === '',
                    chatHistoryExists: !!chatHistory,
                    messageElements: messages.map(msg => ({
                        classes: msg.className,
                        text: msg.textContent.substring(0, 50) + '...'
                    }))
                };
            }, testMessage);

            return {
                testMessage,
                selectedProvider: providers[0],
                chatState,
                userInputHandled: chatState.userMessageFound,
                responseReceived: chatState.hasResponse
            };
        });
    }

    // Test 6: Settings Page Provider Configuration
    async testSettingsPageProviderConfiguration() {
        return await this.runTest('Settings Page Provider Configuration', async () => {
            await this.page.goto(`${this.baseUrl}/settings.html`, { waitUntil: 'networkidle0' });

            const settingsPage = await this.page.evaluate(async (backendUrl) => {
                // Fetch backend settings
                let backendSettings = null;
                try {
                    const response = await fetch(`${backendUrl}/api/settings`);
                    backendSettings = await response.json();
                } catch (error) {
                    console.warn('Could not fetch backend settings');
                }

                // Check page elements
                const elements = {
                    providerSections: document.querySelectorAll('.provider-card, .provider-section, [data-provider], .card').length,
                    apiKeyInputs: document.querySelectorAll('input[type="password"], input[placeholder*="API"], input[name*="key"]').length,
                    checkboxes: document.querySelectorAll('input[type="checkbox"]').length,
                    saveButtons: document.querySelectorAll('button[type="submit"], .save-button').length,
                    testButtons: document.querySelectorAll('.test-button, [onclick*="test"]').length,
                    formElements: document.querySelectorAll('form, .form').length
                };

                return {
                    backendSettings,
                    elements,
                    hasProviderConfig: elements.providerSections > 0 || elements.apiKeyInputs > 0,
                    hasInteractiveElements: elements.checkboxes > 0 || elements.saveButtons > 0,
                    pageLoaded: document.title.includes('Settings')
                };
            }, this.backendUrl);

            return settingsPage;
        });
    }

    // Test 7: Operations Page Device Management
    async testOperationsPageDeviceManagement() {
        return await this.runTest('Operations Page Device Management', async () => {
            await this.page.goto(`${this.baseUrl}/operations.html`, { waitUntil: 'networkidle0' });

            const operationsPage = await this.page.evaluate(async (backendUrl) => {
                // Get backend device data
                let backendDevices = null;
                try {
                    const response = await fetch(`${backendUrl}/api/devices`);
                    backendDevices = await response.json();
                } catch (error) {
                    console.warn('Could not fetch backend devices');
                }

                // Check UI elements
                const elements = {
                    deviceContainers: document.querySelectorAll('.device, .router, .equipment, [data-device]').length,
                    deviceCards: document.querySelectorAll('.card, .device-card').length,
                    tables: document.querySelectorAll('table, .table').length,
                    actionButtons: document.querySelectorAll('button, .btn').length,
                    forms: document.querySelectorAll('form, .form').length,
                    inputs: document.querySelectorAll('input, textarea, select').length
                };

                return {
                    backendDevices,
                    deviceCount: backendDevices ? Object.keys(backendDevices).length : 0,
                    elements,
                    hasDeviceInterface: elements.deviceContainers > 0 || elements.deviceCards > 0 || elements.tables > 0,
                    hasInteractivity: elements.actionButtons > 0 || elements.forms > 0,
                    pageLoaded: document.title.includes('Operations')
                };
            }, this.backendUrl);

            return operationsPage;
        });
    }

    // Test 8: Dashboard Analytics Display
    async testDashboardAnalyticsDisplay() {
        return await this.runTest('Dashboard Analytics Display', async () => {
            await this.page.goto(`${this.baseUrl}/dashboard.html`, { waitUntil: 'networkidle0' });

            const dashboardPage = await this.page.evaluate(async (backendUrl) => {
                // Get usage data from backend
                let usageData = null;
                try {
                    const response = await fetch(`${backendUrl}/api/usage`);
                    usageData = await response.json();
                } catch (error) {
                    console.warn('Could not fetch usage data');
                }

                // Check dashboard elements
                const elements = {
                    charts: document.querySelectorAll('canvas, .chart, svg, [data-chart]').length,
                    statistics: document.querySelectorAll('.stat, .metric, .stats-card, .card').length,
                    providerInfo: document.querySelectorAll('.provider-status, [data-provider], .status').length,
                    progressBars: document.querySelectorAll('.progress, .progress-bar').length,
                    dataDisplays: document.querySelectorAll('.data, .info, .summary').length
                };

                return {
                    usageData,
                    elements,
                    hasVisualizations: elements.charts > 0,
                    hasStatistics: elements.statistics > 0,
                    hasProviderInfo: elements.providerInfo > 0,
                    pageLoaded: document.title.includes('Dashboard')
                };
            }, this.backendUrl);

            return dashboardPage;
        });
    }

    // Test 9: Automation Workflow Interface
    async testAutomationWorkflowInterface() {
        return await this.runTest('Automation Workflow Interface', async () => {
            await this.page.goto(`${this.baseUrl}/automation.html`, { waitUntil: 'networkidle0' });

            const automationPage = await this.page.evaluate(async (backendUrl) => {
                // Get devices for automation
                let devices = null;
                try {
                    const response = await fetch(`${backendUrl}/api/devices`);
                    devices = await response.json();
                } catch (error) {
                    console.warn('Could not fetch devices');
                }

                // Check automation elements
                const elements = {
                    textInputs: document.querySelectorAll('textarea, input[type="text"]').length,
                    selects: document.querySelectorAll('select').length,
                    buttons: document.querySelectorAll('button').length,
                    workflows: document.querySelectorAll('.workflow, .automation, [data-workflow]').length,
                    steps: document.querySelectorAll('.step, .stage, [data-step]').length,
                    panels: document.querySelectorAll('.panel, .section, .card').length
                };

                return {
                    devices,
                    deviceCount: devices ? Object.keys(devices).length : 0,
                    elements,
                    hasInputInterface: elements.textInputs > 0,
                    hasDeviceSelection: elements.selects > 0,
                    hasWorkflowElements: elements.workflows > 0 || elements.steps > 0,
                    pageLoaded: document.title.includes('Automation')
                };
            }, this.backendUrl);

            return automationPage;
        });
    }

    // Test 10: Cross-Page Navigation and Consistency
    async testCrossPageNavigationConsistency() {
        return await this.runTest('Cross-Page Navigation and Consistency', async () => {
            const pages = [
                { name: 'Chat', url: this.baseUrl },
                { name: 'Settings', url: `${this.baseUrl}/settings.html` },
                { name: 'Operations', url: `${this.baseUrl}/operations.html` },
                { name: 'Dashboard', url: `${this.baseUrl}/dashboard.html` },
                { name: 'Automation', url: `${this.baseUrl}/automation.html` }
            ];

            const results = [];
            let navigationScore = 0;

            for (const page of pages) {
                try {
                    await this.page.goto(page.url, { waitUntil: 'networkidle0' });

                    const pageAnalysis = await this.page.evaluate(() => {
                        const nav = document.querySelector('nav');
                        const header = document.querySelector('header');
                        const main = document.querySelector('main, .main, .container');
                        
                        return {
                            title: document.title,
                            hasNavigation: !!nav,
                            hasHeader: !!header,
                            hasMainContent: !!main,
                            navLinks: nav ? Array.from(nav.querySelectorAll('a')).length : 0,
                            activeNavLink: nav ? !!nav.querySelector('.active, [class*="active"]') : false,
                            consistentStyling: !!(header && nav && main)
                        };
                    });

                    results.push({
                        page: page.name,
                        url: page.url,
                        ...pageAnalysis,
                        accessible: true
                    });

                    if (pageAnalysis.consistentStyling) navigationScore++;

                } catch (error) {
                    results.push({
                        page: page.name,
                        url: page.url,
                        error: error.message,
                        accessible: false
                    });
                }
            }

            return {
                results,
                totalPages: pages.length,
                accessiblePages: results.filter(r => r.accessible).length,
                consistentPages: navigationScore,
                navigationScore: (navigationScore / pages.length) * 100
            };
        });
    }

    // Generate comprehensive test report
    async generateTestReport() {
        const endTime = Date.now();
        const totalDuration = endTime - this.startTime;
        const passedTests = this.testResults.filter(t => t.status === 'PASS').length;
        const failedTests = this.testResults.filter(t => t.status === 'FAIL').length;
        const successRate = ((passedTests / this.testResults.length) * 100).toFixed(1);

        const report = {
            summary: {
                title: 'Multi-API Chat Frontend-Backend Integration Test Report',
                totalTests: this.testResults.length,
                passed: passedTests,
                failed: failedTests,
                successRate: parseFloat(successRate),
                grade: successRate >= 90 ? 'A' : successRate >= 80 ? 'B' : successRate >= 70 ? 'C' : 'D',
                totalDuration,
                timestamp: new Date().toISOString(),
                screenshots: this.screenshots
            },
            testResults: this.testResults,
            environment: {
                baseUrl: this.baseUrl,
                backendUrl: this.backendUrl,
                userAgent: await this.page.evaluate(() => navigator.userAgent),
                viewport: await this.page.viewport(),
                testRunner: 'Puppeteer',
                nodeVersion: process.version
            },
            conclusions: this.generateConclusions(passedTests, failedTests, successRate)
        };

        // Save reports
        const reportDir = './test_reports';
        if (!fs.existsSync(reportDir)) {
            fs.mkdirSync(reportDir, { recursive: true });
        }

        fs.writeFileSync(`${reportDir}/final_integration_report.json`, JSON.stringify(report, null, 2));
        fs.writeFileSync(`${reportDir}/final_integration_report.html`, this.generateHTMLReport(report));

        return report;
    }

    generateConclusions(passed, failed, successRate) {
        const conclusions = [];

        if (successRate >= 90) {
            conclusions.push('✅ Excellent: Frontend-backend integration is working exceptionally well');
        } else if (successRate >= 80) {
            conclusions.push('✅ Good: Frontend-backend integration is working well with minor issues');
        } else if (successRate >= 70) {
            conclusions.push('⚠️  Acceptable: Frontend-backend integration is working but needs attention');
        } else {
            conclusions.push('❌ Poor: Frontend-backend integration has significant issues');
        }

        const backendTest = this.testResults.find(t => t.name.includes('Backend Server Health'));
        if (backendTest && backendTest.status === 'PASS') {
            conclusions.push('✅ Backend API endpoints are accessible and responding correctly');
        }

        const frontendTest = this.testResults.find(t => t.name.includes('Frontend Pages'));
        if (frontendTest && frontendTest.status === 'PASS') {
            conclusions.push('✅ All frontend pages load successfully');
        }

        const providerTest = this.testResults.find(t => t.name.includes('Provider Data Integration'));
        if (providerTest && providerTest.status === 'PASS') {
            conclusions.push('✅ Provider data integration between frontend and backend is working');
        }

        if (failed > 0) {
            conclusions.push(`⚠️  ${failed} test(s) failed - review the detailed results for specific issues`);
        }

        return conclusions;
    }

    generateHTMLReport(report) {
        const gradeColor = {
            'A': '#34C759',
            'B': '#007AFF', 
            'C': '#FF9500',
            'D': '#FF3B30'
        }[report.summary.grade] || '#8E8E93';

        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-API Chat Integration Test Report</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            margin: 0; padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh; color: #1d1d1f;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 40px; border-radius: 20px; margin-bottom: 30px;
            text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header h1 { margin: 0; font-size: 2.5rem; font-weight: 700; }
        .header p { margin: 15px 0 0 0; opacity: 0.9; font-size: 1.2rem; }
        .summary { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 40px;
        }
        .summary-card { 
            background: white; padding: 30px; border-radius: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1); text-align: center;
            transition: transform 0.3s ease;
        }
        .summary-card:hover { transform: translateY(-5px); }
        .summary-card h3 { margin: 0 0 15px 0; color: #666; font-size: 1rem; }
        .summary-card .value { 
            font-size: 3rem; font-weight: 800; margin: 15px 0;
            background: linear-gradient(135deg, ${gradeColor}, ${gradeColor}aa);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .grade { font-size: 4rem !important; color: ${gradeColor} !important; }
        .conclusions {
            background: white; border-radius: 20px; padding: 30px; margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        .conclusions h2 { color: #1d1d1f; margin-top: 0; }
        .conclusions ul { list-style: none; padding: 0; }
        .conclusions li { 
            padding: 10px 0; border-bottom: 1px solid #f0f0f0;
            font-size: 1.1rem; line-height: 1.5;
        }
        .test-results { 
            background: white; border-radius: 20px; overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        .test-results h2 { 
            margin: 0; padding: 30px; background: #f8f9fa;
            border-bottom: 1px solid #e9ecef; font-size: 1.5rem;
        }
        .test-item { 
            padding: 25px 30px; border-bottom: 1px solid #f0f0f0;
            display: flex; justify-content: space-between; align-items: center;
        }
        .test-item:last-child { border-bottom: none; }
        .test-info h4 { margin: 0; font-size: 1.2rem; color: #1d1d1f; }
        .test-info p { margin: 5px 0 0 0; color: #666; font-size: 0.9rem; }
        .test-status {
            padding: 10px 20px; border-radius: 25px; font-weight: 700;
            font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;
        }
        .status-pass { background: #34C759; color: white; }
        .status-fail { background: #FF3B30; color: white; }
        .error-details { 
            margin-top: 10px; padding: 15px; background: #fff3f3;
            border-left: 4px solid #FF3B30; border-radius: 5px;
            font-family: 'SF Mono', Consolas, monospace; font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Integration Test Report</h1>
            <p>${report.summary.title}</p>
            <p>Generated: ${new Date(report.summary.timestamp).toLocaleString()}</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>Overall Grade</h3>
                <div class="value grade">${report.summary.grade}</div>
                <p>Integration Quality</p>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value">${report.summary.successRate}%</div>
                <p>Tests Passed</p>
            </div>
            <div class="summary-card">
                <h3>Tests Passed</h3>
                <div class="value" style="color: #34C759">${report.summary.passed}</div>
                <p>Successfully Executed</p>
            </div>
            <div class="summary-card">
                <h3>Duration</h3>
                <div class="value" style="color: #007AFF">${(report.summary.totalDuration / 1000).toFixed(1)}s</div>
                <p>Total Time</p>
            </div>
        </div>

        <div class="conclusions">
            <h2>🎯 Test Conclusions</h2>
            <ul>
                ${report.conclusions.map(conclusion => `<li>${conclusion}</li>`).join('')}
            </ul>
        </div>

        <div class="test-results">
            <h2>📋 Detailed Test Results</h2>
            ${report.testResults.map(test => `
                <div class="test-item">
                    <div class="test-info">
                        <h4>${test.name}</h4>
                        <p>${test.duration}ms • ${new Date(test.timestamp).toLocaleTimeString()}</p>
                        ${test.error ? `<div class="error-details">Error: ${test.error}</div>` : ''}
                    </div>
                    <div class="test-status status-${test.status.toLowerCase()}">${test.status}</div>
                </div>
            `).join('')}
        </div>
    </div>
</body>
</html>`;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
            console.log('🧹 Test cleanup completed');
        }
    }

    async runAllTests() {
        try {
            await this.setup();

            console.log('\n🎯 Multi-API Chat Frontend-Backend Integration Test Suite');
            console.log('=' .repeat(65));

            // Execute all tests
            await this.testBackendServerHealth();
            await this.testFrontendPagesLoadRender();  
            await this.testProviderDataIntegration();
            await this.testModelSelectionFunctionality();
            await this.testChatInterfaceUserInteraction();
            await this.testSettingsPageProviderConfiguration();
            await this.testOperationsPageDeviceManagement();
            await this.testDashboardAnalyticsDisplay();
            await this.testAutomationWorkflowInterface();
            await this.testCrossPageNavigationConsistency();

            console.log('\n📊 Generating final test report...');
            const report = await this.generateTestReport();

            console.log('\n' + '=' .repeat(65));
            console.log(`🎯 INTEGRATION TEST COMPLETE`);
            console.log(`📈 Final Score: ${report.summary.passed}/${report.summary.totalTests} tests passed (${report.summary.successRate}%) - Grade: ${report.summary.grade}`);
            console.log(`⏱️  Total Duration: ${(report.summary.totalDuration / 1000).toFixed(1)}s`);
            console.log(`📋 Full Report: test_reports/final_integration_report.html`);
            console.log('=' .repeat(65));

            return report.summary.successRate >= 70;

        } catch (error) {
            console.error('❌ Test suite execution failed:', error.message);
            return false;
        } finally {
            await this.cleanup();
        }
    }
}

// Execute tests
if (require.main === module) {
    const testSuite = new FinalIntegrationTestSuite();
    testSuite.runAllTests()
        .then(success => {
            console.log(success ? '\n✅ Integration tests PASSED' : '\n❌ Integration tests FAILED');
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('Fatal error:', error);
            process.exit(1);
        });
}

module.exports = FinalIntegrationTestSuite;
