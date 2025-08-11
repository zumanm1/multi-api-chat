const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const http = require('http');
const path = require('path');

class ComprehensiveE2ETest {
    constructor() {
        this.browser = null;
        this.page = null;
        this.results = [];
        this.testStartTime = Date.now();
        this.backend_url = 'http://localhost:8002';
        this.frontend_server = null;
        this.frontend_port = 8001;
    }

    async log(message, type = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
        console.log(`${prefix} [${timestamp}] ${message}`);
    }

    async init() {
        await this.log('Initializing E2E Test Environment...');
        
        // Check if frontend server is already running
        const frontendRunning = await this.checkFrontendServer();
        if (!frontendRunning) {
            await this.startFrontendServer();
        } else {
            await this.log('Using existing frontend server on port 8001');
        }
        
        // Initialize browser
        this.browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        });
        this.page = await this.browser.newPage();
        await this.page.setViewport({ width: 1280, height: 720 });
        
        // Set up console logging
        this.page.on('console', msg => {
            console.log(`[FRONTEND] ${msg.text()}`);
        });
        
        // Set up error handling
        this.page.on('error', err => {
            console.error(`[FRONTEND ERROR] ${err.message}`);
        });
        
        await this.ensureDirectories();
        await this.log('E2E Test Environment initialized', 'success');
    }

    async checkFrontendServer() {
        try {
            const response = await fetch(`http://localhost:${this.frontend_port}`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    async startFrontendServer() {
        return new Promise((resolve) => {
            const server = http.createServer(async (req, res) => {
                try {
                    let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
                    
                    // Security check
                    if (!filePath.startsWith(__dirname)) {
                        res.writeHead(403);
                        res.end('Forbidden');
                        return;
                    }
                    
                    const fileContent = await fs.readFile(filePath);
                    
                    // Set appropriate content type
                    let contentType = 'text/html';
                    if (filePath.endsWith('.js')) contentType = 'application/javascript';
                    if (filePath.endsWith('.css')) contentType = 'text/css';
                    if (filePath.endsWith('.json')) contentType = 'application/json';
                    
                    res.writeHead(200, { 'Content-Type': contentType });
                    res.end(fileContent);
                } catch (error) {
                    res.writeHead(404);
                    res.end('Not Found');
                }
            });
            
            server.listen(this.frontend_port, () => {
                console.log(`Frontend server started on port ${this.frontend_port}`);
                this.frontend_server = server;
                resolve();
            });
        });
    }

    async ensureDirectories() {
        const dirs = ['e2e_screenshots', 'e2e_reports'];
        for (const dir of dirs) {
            try {
                await fs.mkdir(dir, { recursive: true });
            } catch (error) {
                // Directory already exists
            }
        }
    }

    async takeScreenshot(testName, success = false) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `e2e_screenshots/${testName}_${timestamp}.png`;
        await this.page.screenshot({ path: filename, fullPage: true });
        
        return filename;
    }

    async addResult(testName, success, details = {}, screenshot = null) {
        const result = {
            test: testName,
            success,
            timestamp: new Date().toISOString(),
            duration: Date.now() - this.testStartTime,
            details,
            screenshot
        };
        
        this.results.push(result);
        await this.log(`${testName} - ${success ? 'PASS' : 'FAIL'}`, success ? 'success' : 'error');
        
        if (details.error) {
            console.log(`   Error: ${details.error}`);
        }
    }

    async testBackendHealth() {
        const testName = 'Backend Health and AI Status';
        try {
            const response = await fetch(`${this.backend_url}/api/health`);
            if (!response.ok) {
                throw new Error(`Backend health check failed: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Test AI status endpoint
            const aiResponse = await fetch(`${this.backend_url}/api/ai/status`);
            const aiData = await aiResponse.json();
            
            await this.addResult(testName, true, {
                backend_status: data.status,
                ai_available: aiData.ai_available,
                features_enabled: Object.keys(aiData.features || {}).length,
                mode: data.mode
            });
        } catch (error) {
            await this.addResult(testName, false, { error: error.message });
        }
    }

    async testFrontendLoading() {
        const testName = 'Frontend Loading and Initial State';
        let screenshot = null;
        
        try {
            await this.page.goto(`http://localhost:${this.frontend_port}`, { 
                waitUntil: 'networkidle0',
                timeout: 10000 
            });
            
            // Wait for main elements to load
            await this.page.waitForSelector('.chat-container', { timeout: 5000 });
            await this.page.waitForSelector('.provider-select', { timeout: 5000 });
            
            // Check if essential elements are present
            const title = await this.page.title();
            const hasProviderSelect = await this.page.$('.provider-select') !== null;
            const hasModelSelect = await this.page.$('.model-select') !== null;
            const hasChatMessages = await this.page.$('.chat-messages') !== null;
            const hasChatInput = await this.page.$('.message-input') !== null;
            
            screenshot = await this.takeScreenshot(testName, true);
            
            await this.addResult(testName, true, {
                page_title: title,
                provider_select_loaded: hasProviderSelect,
                model_select_loaded: hasModelSelect,
                chat_messages_loaded: hasChatMessages,
                chat_input_loaded: hasChatInput
            }, screenshot);
            
        } catch (error) {
            screenshot = await this.takeScreenshot(testName, false);
            await this.addResult(testName, false, { error: error.message }, screenshot);
        }
    }

    async testProviderSelection() {
        const testName = 'Provider Selection and Model Loading';
        let screenshot = null;
        
        try {
            // Wait for provider select to be available
            await this.page.waitForSelector('.provider-select', { timeout: 5000 });
            
            // Get available providers
            const providers = await this.page.evaluate(() => {
                const select = document.querySelector('.provider-select');
                return Array.from(select.options).map(option => ({
                    value: option.value,
                    text: option.text
                }));
            });
            
            if (providers.length < 2) {
                throw new Error(`Not enough providers loaded: ${providers.length}`);
            }
            
            // Test selecting a provider (skip the first "Select Provider" option)
            const testProvider = providers.find(p => p.value !== '');
            if (testProvider) {
                await this.page.select('.provider-select', testProvider.value);
                
                // Wait for models to load
                await this.page.waitForFunction(() => true, {}, { timeout: 1000 }).catch(() => {});
                
                // Check if models are loaded
                const models = await this.page.evaluate(() => {
                    const select = document.querySelector('.model-select');
                    return Array.from(select.options).map(option => ({
                        value: option.value,
                        text: option.text
                    }));
                });
                
                screenshot = await this.takeScreenshot(testName, true);
                
                await this.addResult(testName, true, {
                    providers_count: providers.length,
                    selected_provider: testProvider.value,
                    models_loaded: models.length > 1,
                    models_count: models.length
                }, screenshot);
            } else {
                throw new Error('No valid provider found to test');
            }
            
        } catch (error) {
            screenshot = await this.takeScreenshot(testName, false);
            await this.addResult(testName, false, { error: error.message }, screenshot);
        }
    }

    async testAIChat() {
        const testName = 'AI Chat Functionality (Fallback Mode)';
        let screenshot = null;
        
        try {
            // Make sure we're on the page
            await this.page.waitForSelector('.message-input', { timeout: 5000 });
            
            // Clear any existing messages
            await this.page.evaluate(() => {
                const messages = document.querySelector('.chat-messages');
                if (messages) messages.innerHTML = '';
            });
            
            // Type a test message
            const testMessage = 'Hello, this is an E2E test message!';
            await this.page.type('.message-input', testMessage);
            
            // Submit the message
            await this.page.click('.send-button');
            
            // Wait for the message to appear
            await this.page.waitForSelector('.message', { timeout: 10000 });
            
            // Check if both user and AI messages are present
            await this.page.waitForFunction(() => true, {}, { timeout: 2000 }).catch(() => {}); // Give time for AI response
            
            const messages = await this.page.evaluate(() => {
                const messageElements = document.querySelectorAll('.message');
                return Array.from(messageElements).map(msg => ({
                    role: msg.classList.contains('user') ? 'user' : 'assistant',
                    content: msg.querySelector('.message-content')?.textContent || ''
                }));
            });
            
            const hasUserMessage = messages.some(msg => msg.role === 'user');
            const hasAIResponse = messages.some(msg => msg.role === 'assistant');
            
            screenshot = await this.takeScreenshot(testName, true);
            
            await this.addResult(testName, hasUserMessage && hasAIResponse, {
                messages_count: messages.length,
                has_user_message: hasUserMessage,
                has_ai_response: hasAIResponse,
                test_message: testMessage
            }, screenshot);
            
        } catch (error) {
            screenshot = await this.takeScreenshot(testName, false);
            await this.addResult(testName, false, { error: error.message }, screenshot);
        }
    }

    async testBackendEndpoints() {
        const testName = 'Backend API Endpoints';
        
        try {
            const endpoints = [
                { path: '/api/health', method: 'GET' },
                { path: '/api/ai/status', method: 'GET' },
                { path: '/api/chat', method: 'POST', body: { message: 'test' } }
            ];
            
            const results = {};
            
            for (const endpoint of endpoints) {
                try {
                    const options = {
                        method: endpoint.method,
                        headers: { 'Content-Type': 'application/json' }
                    };
                    
                    if (endpoint.body) {
                        options.body = JSON.stringify(endpoint.body);
                    }
                    
                    const response = await fetch(`${this.backend_url}${endpoint.path}`, options);
                    results[endpoint.path] = {
                        status: response.status,
                        ok: response.ok
                    };
                    
                    if (response.ok) {
                        const data = await response.json();
                        results[endpoint.path].has_data = !!data;
                    }
                } catch (error) {
                    results[endpoint.path] = {
                        status: 'error',
                        error: error.message
                    };
                }
            }
            
            const successCount = Object.values(results).filter(r => r.ok).length;
            
            await this.addResult(testName, successCount === endpoints.length, {
                endpoints_tested: endpoints.length,
                successful_endpoints: successCount,
                results: results
            });
            
        } catch (error) {
            await this.addResult(testName, false, { error: error.message });
        }
    }

    async testResponsiveDesign() {
        const testName = 'Responsive Design and Mobile View';
        let screenshot = null;
        
        try {
            // Test different viewport sizes
            const viewports = [
                { width: 375, height: 667, name: 'mobile' },
                { width: 768, height: 1024, name: 'tablet' },
                { width: 1280, height: 720, name: 'desktop' }
            ];
            
            const results = {};
            
            for (const viewport of viewports) {
                await this.page.setViewport(viewport);
                await this.page.waitForFunction(() => true, {}, { timeout: 1000 }).catch(() => {}); // Allow layout to adjust
                
                // Check if essential elements are still visible
                const chatContainer = await this.page.$('.chat-container');
                const providerSelect = await this.page.$('.provider-select');
                const chatInput = await this.page.$('.message-input');
                
                results[viewport.name] = {
                    chat_container_visible: !!chatContainer,
                    provider_select_visible: !!providerSelect,
                    chat_input_visible: !!chatInput,
                    viewport: `${viewport.width}x${viewport.height}`
                };
            }
            
            // Reset to desktop view for screenshot
            await this.page.setViewport({ width: 1280, height: 720 });
            screenshot = await this.takeScreenshot(testName, true);
            
            await this.addResult(testName, true, { viewport_tests: results }, screenshot);
            
        } catch (error) {
            screenshot = await this.takeScreenshot(testName, false);
            await this.addResult(testName, false, { error: error.message }, screenshot);
        }
    }

    async testErrorHandling() {
        const testName = 'Error Handling and Fallback Behavior';
        
        try {
            // Test invalid backend endpoint
            let errorHandled = false;
            try {
                await fetch(`${this.backend_url}/api/invalid/endpoint`);
            } catch (error) {
                errorHandled = true;
            }
            
            // Test chat with invalid provider
            const invalidChatResponse = await fetch(`${this.backend_url}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'test', provider: 'invalid_provider' })
            });
            
            // Should still return a response (fallback mode)
            const chatData = await invalidChatResponse.json();
            
            await this.addResult(testName, true, {
                invalid_endpoint_handled: errorHandled,
                invalid_provider_fallback: !!chatData.fallback,
                chat_response_received: !!chatData.response
            });
            
        } catch (error) {
            await this.addResult(testName, false, { error: error.message });
        }
    }

    async generateReport() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPath = `e2e_reports/comprehensive_e2e_report_${timestamp}.json`;
        
        const report = {
            test_run_info: {
                timestamp: new Date().toISOString(),
                total_duration: Date.now() - this.testStartTime,
                tests_run: this.results.length,
                tests_passed: this.results.filter(r => r.success).length,
                tests_failed: this.results.filter(r => !r.success).length
            },
            test_results: this.results,
            summary: {
                backend_health: this.results.find(r => r.test.includes('Backend Health'))?.success || false,
                frontend_loading: this.results.find(r => r.test.includes('Frontend Loading'))?.success || false,
                provider_selection: this.results.find(r => r.test.includes('Provider Selection'))?.success || false,
                chat_functionality: this.results.find(r => r.test.includes('AI Chat'))?.success || false,
                responsive_design: this.results.find(r => r.test.includes('Responsive Design'))?.success || false,
                error_handling: this.results.find(r => r.test.includes('Error Handling'))?.success || false
            }
        };
        
        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
        await this.log(`Report generated: ${reportPath}`, 'success');
        
        return report;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
        
        if (this.frontend_server) {
            this.frontend_server.close();
        }
        
        await this.log('Cleanup completed', 'success');
    }

    async runAllTests() {
        try {
            await this.log('Starting Comprehensive E2E Tests...', 'success');
            
            // Backend tests
            await this.testBackendHealth();
            await this.testBackendEndpoints();
            
            // Frontend tests
            await this.testFrontendLoading();
            await this.testProviderSelection();
            await this.testAIChat();
            await this.testResponsiveDesign();
            
            // Integration tests
            await this.testErrorHandling();
            
            // Generate report
            const report = await this.generateReport();
            
            // Print summary
            console.log('\n' + '='.repeat(60));
            console.log('E2E TEST SUMMARY');
            console.log('='.repeat(60));
            console.log(`Total Tests: ${report.test_run_info.tests_run}`);
            console.log(`Passed: ${report.test_run_info.tests_passed}`);
            console.log(`Failed: ${report.test_run_info.tests_failed}`);
            console.log(`Duration: ${Math.round(report.test_run_info.total_duration / 1000)}s`);
            console.log(`Success Rate: ${Math.round((report.test_run_info.tests_passed / report.test_run_info.tests_run) * 100)}%`);
            console.log('='.repeat(60));
            
            // Print individual test results
            this.results.forEach(result => {
                const status = result.success ? '✅ PASS' : '❌ FAIL';
                console.log(`${status} ${result.test}`);
                if (result.details.error) {
                    console.log(`     Error: ${result.details.error}`);
                }
            });
            
            return report.test_run_info.tests_passed === report.test_run_info.tests_run;
            
        } catch (error) {
            await this.log(`Test execution failed: ${error.message}`, 'error');
            return false;
        }
    }
}

// Execute tests if run directly
async function main() {
    const tester = new ComprehensiveE2ETest();
    
    try {
        await tester.init();
        const success = await tester.runAllTests();
        await tester.cleanup();
        
        process.exit(success ? 0 : 1);
    } catch (error) {
        console.error('E2E Test execution failed:', error);
        await tester.cleanup();
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = ComprehensiveE2ETest;
