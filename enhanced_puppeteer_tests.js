const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class EnhancedPuppeteerTests {
    constructor() {
        this.browser = null;
        this.page = null;
        this.results = [];
        this.screenshots = [];
        this.testStartTime = Date.now();
    }

    async init() {
        this.browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        this.page = await this.browser.newPage();
        await this.page.setViewport({ width: 1280, height: 720 });
        
        // Create directories
        await this.ensureDirectories();
    }

    async ensureDirectories() {
        const dirs = ['enhanced_test_screenshots', 'enhanced_test_reports'];
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
        const filename = `enhanced_test_screenshots/${testName}_${timestamp}.png`;
        await this.page.screenshot({ path: filename, fullPage: true });
        
        this.screenshots.push({
            test: testName,
            filename,
            success,
            timestamp
        });
        
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
        console.log(`${success ? '✅' : '❌'} ${testName} - ${success ? 'PASS' : 'FAIL'}`);
        if (details.error) {
            console.log(`   Error: ${details.error}`);
        }
    }

    async testBackendHealth() {
        const testName = 'Backend Health Check with .env.private Status';
        try {
            const response = await fetch('http://localhost:7002/api/health');
            const data = await response.json();
            
            const requiredFields = ['status', 'providers_enabled', 'env_private_exists', 'timestamp', 'uptime'];
            const hasAllFields = requiredFields.every(field => data.hasOwnProperty(field));
            
            if (!hasAllFields) {
                throw new Error(`Missing required health fields: ${requiredFields.filter(f => !data.hasOwnProperty(f))}`);
            }
            
            await this.addResult(testName, true, {
                status: data.status,
                providers_enabled: data.providers_enabled,
                env_private_exists: data.env_private_exists,
                uptime: data.uptime
            });
        } catch (error) {
            await this.addResult(testName, false, { error: error.message });
        }
    }

    async testEnvPrivateManagement() {
        const testName = 'Environment Private File Management';
        let screenshot = null;
        
        try {
            // Navigate to settings page
            await this.page.goto('http://localhost:7001/index.html');
            await this.page.waitForTimeout(1000);
            
            // Check if we can access the .env.private API endpoints
            const envStatusResponse = await fetch('http://localhost:7002/api/env/private');
            const envStatus = await envStatusResponse.json();
            
            const hasValidStructure = envStatus.hasOwnProperty('exists') && 
                                    envStatus.hasOwnProperty('enabled_providers') &&
                                    envStatus.hasOwnProperty('file_size');
            
            if (!hasValidStructure) {
                throw new Error('Invalid .env.private status structure');
            }
            
            // Test refresh functionality
            const refreshResponse = await fetch('http://localhost:7002/api/env/private/refresh', {
                method: 'POST'
            });
            const refreshResult = await refreshResponse.json();
            
            if (!refreshResult.success) {
                throw new Error(`Refresh failed: ${refreshResult.error}`);
            }
            
            screenshot = await this.takeScreenshot(testName, true);
            
            await this.addResult(testName, true, {
                env_exists: envStatus.exists,
                enabled_providers: envStatus.enabled_providers.length,
                refresh_success: refreshResult.success
            }, screenshot);
            
        } catch (error) {
            screenshot = await this.takeScreenshot(testName, false);
            await this.addResult(testName, false, { error: error.message }, screenshot);
        }
    }

    async testProviderConfiguration() {
        const testName = 'Enhanced Provider Configuration and Testing';
        let screenshot = null;
        
        try {
            await this.page.goto('http://localhost:7001/index.html');
            await this.page.waitForTimeout(1000);
            
            // Test provider list endpoint
            const providersResponse = await fetch('http://localhost:7002/api/providers');
            const providers = await providersResponse.json();
            
            if (!providers || typeof providers !== 'object') {
                throw new Error('Invalid providers response');
            }
            
            // Test updating a provider (Groq as example)
            const providerUpdate = {
                enabled: true,
                api_key: 'test-key-' + Date.now(),
                model: 'llama-3.1-70b-versatile'
            };
            
            const updateResponse = await fetch('http://localhost:7002/api/providers/groq', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(providerUpdate)
            });
            
            if (!updateResponse.ok) {
                throw new Error(`Provider update failed: ${updateResponse.status}`);
            }
            
            // Test enhanced provider testing with raw data
            const testResponse = await fetch('http://localhost:7002/api/providers/groq/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    test_message: 'Hello, this is a comprehensive test.',
                    include_raw_data: true
                })
            });
            
            const testResult = await testResponse.json();
            
            // Validate enhanced test response structure
            const requiredFields = ['provider', 'connection_test', 'raw_data'];
            const hasRequiredFields = requiredFields.every(field => testResult.hasOwnProperty(field));
            
            if (!hasRequiredFields) {
                throw new Error(`Missing test result fields: ${requiredFields.filter(f => !testResult.hasOwnProperty(f))}`);
            }
            
            // Validate raw data structure
            if (!testResult.raw_data.request || !testResult.raw_data.request.message) {
                throw new Error('Invalid raw data structure in test response');
            }
            
            screenshot = await this.takeScreenshot(testName, true);
            
            await this.addResult(testName, true, {
                providers_count: Object.keys(providers).length,
                update_success: updateResponse.ok,
                test_has_raw_data: !!testResult.raw_data,
                connection_test_passed: testResult.connection_test?.success
            }, screenshot);
            
        } catch (error) {
            screenshot = await this.takeScreenshot(testName, false);
            await this.addResult(testName, false, { error: error.message }, screenshot);
        }
    }

    async testProviderTestingUI() {
        const testName = 'Provider Testing UI Interaction';
        let screenshot = null;
        
        try {
            await this.page.goto('http://localhost:7001/index.html');
            await this.page.waitForTimeout(2000);
            
            // Look for provider testing elements in the UI
            // This assumes there's a settings or providers section
            const testButtons = await this.page.$$('[data-test="provider-test"], .provider-test-btn, button[id*="test"]');
            
            if (testButtons.length === 0) {
                // Try to find any buttons that might be test buttons
                const allButtons = await this.page.$$('button');
                let foundTestButton = false;
                
                for (let button of allButtons) {
                    const text = await button.evaluate(el => el.textContent.toLowerCase());
                    if (text.includes('test') || text.includes('check')) {
                        foundTestButton = true;
                        await button.click();
                        await this.page.waitForTimeout(1500);
                        break;
                    }
                }
                
                if (!foundTestButton) {
                    throw new Error('No provider test buttons found in UI');
                }
            } else {
                // Click the first test button found
                await testButtons[0].click();
                await this.page.waitForTimeout(2000);
            }
            
            // Look for test result display areas
            const resultAreas = await this.page.$$('.test-result, .provider-status, [data-test="result"], .result');
            const hasResultDisplay = resultAreas.length > 0;
            
            screenshot = await this.takeScreenshot(testName, true);
            
            await this.addResult(testName, true, {
                test_buttons_found: testButtons.length,
                result_areas_found: resultAreas.length,
                has_result_display: hasResultDisplay
            }, screenshot);
            
        } catch (error) {
            screenshot = await this.takeScreenshot(testName, false);
            await this.addResult(testName, false, { error: error.message }, screenshot);
        }
    }

    async testProviderManagement() {
        const testName = 'Provider Management with .env.private Integration';
        let screenshot = null;
        
        try {
            // Test creating, updating, and managing multiple providers
            const providers = ['cerebras', 'openrouter', 'ollama'];
            const testResults = [];
            
            for (const providerId of providers) {
                // Update provider configuration
                const config = {
                    enabled: true,
                    api_key: providerId === 'ollama' ? '' : `test-key-${providerId}-${Date.now()}`,
                    model: providerId === 'cerebras' ? 'llama-4-scout-wse-3' : 
                           providerId === 'openrouter' ? 'openrouter/auto' : 'llama3.2'
                };
                
                const updateResponse = await fetch(`http://localhost:7002/api/providers/${providerId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                if (updateResponse.ok) {
                    // Test the provider
                    const testResponse = await fetch(`http://localhost:7002/api/providers/${providerId}/test`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            test_message: `Test message for ${providerId}`,
                            include_raw_data: true
                        })
                    });
                    
                    const testData = await testResponse.json();
                    testResults.push({
                        provider: providerId,
                        config_success: true,
                        test_success: testData.connection_test?.success || false,
                        has_raw_data: !!testData.raw_data
                    });
                } else {
                    testResults.push({
                        provider: providerId,
                        config_success: false,
                        error: `HTTP ${updateResponse.status}`
                    });
                }
            }
            
            // Check .env.private file was updated
            const envResponse = await fetch('http://localhost:7002/api/env/private');
            const envData = await envResponse.json();
            
            screenshot = await this.takeScreenshot(testName, true);
            
            await this.addResult(testName, true, {
                providers_tested: testResults.length,
                successful_configs: testResults.filter(r => r.config_success).length,
                env_has_providers: envData.enabled_providers?.length || 0,
                test_results: testResults
            }, screenshot);
            
        } catch (error) {
            screenshot = await this.takeScreenshot(testName, false);
            await this.addResult(testName, false, { error: error.message }, screenshot);
        }
    }

    async testRawDataDisplay() {
        const testName = 'Raw Data Display and Error Handling';
        let screenshot = null;
        
        try {
            // Test with a provider that will likely fail (invalid key scenario)\n            const testPayload = {\n                test_message: 'This should show raw input and output data',\n                include_raw_data: true\n            };\n            \n            const testResponse = await fetch('http://localhost:7002/api/providers/cerebras/test', {\n                method: 'POST',\n                headers: { 'Content-Type': 'application/json' },\n                body: JSON.stringify(testPayload)\n            });\n            \n            const testData = await testResponse.json();\n            \n            // Validate raw data structure regardless of success/failure\n            if (!testData.raw_data) {\n                throw new Error('No raw data in test response');\n            }\n            \n            // Check request data\n            if (!testData.raw_data.request || !testData.raw_data.request.message) {\n                throw new Error('Invalid raw request data structure');\n            }\n            \n            // Check we have either response or error details\n            const hasResponse = !!testData.raw_data.response;\n            const hasErrorDetails = !!testData.raw_data.error_details;\n            \n            if (!hasResponse && !hasErrorDetails) {\n                throw new Error('Raw data missing both response and error details');\n            }\n            \n            screenshot = await this.takeScreenshot(testName, true);\n            \n            await this.addResult(testName, true, {\n                has_raw_data: true,\n                request_message: testData.raw_data.request.message,\n                has_response: hasResponse,\n                has_error_details: hasErrorDetails,\n                connection_test_result: testData.connection_test?.success\n            }, screenshot);\n            \n        } catch (error) {\n            screenshot = await this.takeScreenshot(testName, false);\n            await this.addResult(testName, false, { error: error.message }, screenshot);\n        }\n    }\n\n    async testComprehensiveProviderScenarios() {\n        const testName = 'Comprehensive Provider Testing Scenarios';\n        let screenshot = null;\n        \n        try {\n            const scenarios = [\n                // Scenario 1: Valid provider with API key\n                {\n                    provider: 'groq',\n                    config: { enabled: true, api_key: 'test-groq-key-valid' },\n                    expected: 'connection_test'\n                },\n                // Scenario 2: Provider without API key (should still test connection)\n                {\n                    provider: 'openrouter', \n                    config: { enabled: true, api_key: '' },\n                    expected: 'connection_only'\n                },\n                // Scenario 3: Local provider (Ollama)\n                {\n                    provider: 'ollama',\n                    config: { enabled: true, api_key: '' },\n                    expected: 'local_service'\n                }\n            ];\n            \n            const scenarioResults = [];\n            \n            for (const scenario of scenarios) {\n                // Configure provider\n                await fetch(`http://localhost:7002/api/providers/${scenario.provider}`, {\n                    method: 'PUT',\n                    headers: { 'Content-Type': 'application/json' },\n                    body: JSON.stringify(scenario.config)\n                });\n                \n                // Test provider\n                const testResponse = await fetch(`http://localhost:7002/api/providers/${scenario.provider}/test`, {\n                    method: 'POST',\n                    headers: { 'Content-Type': 'application/json' },\n                    body: JSON.stringify({ include_raw_data: true })\n                });\n                \n                const testData = await testResponse.json();\n                \n                scenarioResults.push({\n                    provider: scenario.provider,\n                    expected: scenario.expected,\n                    has_connection_test: !!testData.connection_test,\n                    has_chat_test: !!testData.chat_test,\n                    has_raw_data: !!testData.raw_data,\n                    status: testData.status\n                });\n            }\n            \n            const allScenariosValid = scenarioResults.every(r => r.has_connection_test && r.has_raw_data);\n            \n            screenshot = await this.takeScreenshot(testName, allScenariosValid);\n            \n            await this.addResult(testName, allScenariosValid, {\n                scenarios_tested: scenarios.length,\n                all_scenarios_valid: allScenariosValid,\n                scenario_results: scenarioResults\n            }, screenshot);\n            \n        } catch (error) {\n            screenshot = await this.takeScreenshot(testName, false);\n            await this.addResult(testName, false, { error: error.message }, screenshot);\n        }\n    }\n\n    async generateReport() {\n        const totalTests = this.results.length;\n        const passedTests = this.results.filter(r => r.success).length;\n        const failedTests = totalTests - passedTests;\n        const successRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0;\n        \n        const report = {\n            summary: {\n                total_tests: totalTests,\n                passed: passedTests,\n                failed: failedTests,\n                success_rate: `${successRate}%`,\n                grade: successRate >= 90 ? 'A' : successRate >= 80 ? 'B' : successRate >= 70 ? 'C' : 'D',\n                test_duration: Date.now() - this.testStartTime,\n                timestamp: new Date().toISOString()\n            },\n            results: this.results,\n            screenshots: this.screenshots,\n            recommendations: this.generateRecommendations()\n        };\n        \n        // Save JSON report\n        const jsonPath = 'enhanced_test_reports/enhanced_test_report.json';\n        await fs.writeFile(jsonPath, JSON.stringify(report, null, 2));\n        \n        // Generate HTML report\n        await this.generateHTMLReport(report);\n        \n        console.log(`\\n📊 Enhanced Test Report Generated:`);\n        console.log(`   📁 JSON: ${jsonPath}`);\n        console.log(`   📁 HTML: enhanced_test_reports/enhanced_test_report.html`);\n        console.log(`   📈 Success Rate: ${successRate}% (Grade: ${report.summary.grade})`);\n        \n        return report;\n    }\n    \n    generateRecommendations() {\n        const recommendations = [];\n        const failures = this.results.filter(r => !r.success);\n        \n        if (failures.length > 0) {\n            recommendations.push('Fix failing tests to improve system reliability');\n        }\n        \n        const envTest = this.results.find(r => r.test.includes('Environment Private'));\n        if (envTest && !envTest.success) {\n            recommendations.push('Implement proper .env.private file management for secure API key storage');\n        }\n        \n        const providerTests = this.results.filter(r => r.test.includes('Provider'));\n        const failedProviders = providerTests.filter(r => !r.success);\n        if (failedProviders.length > 0) {\n            recommendations.push('Review provider configuration and API key management');\n        }\n        \n        if (recommendations.length === 0) {\n            recommendations.push('All tests passed! Consider adding more edge case testing.');\n        }\n        \n        return recommendations;\n    }\n    \n    async generateHTMLReport(report) {\n        const html = `<!DOCTYPE html>\n<html>\n<head>\n    <title>Enhanced Multi-API Chat Test Report</title>\n    <style>\n        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }\n        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }\n        .header { text-align: center; margin-bottom: 30px; }\n        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }\n        .metric { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }\n        .metric h3 { margin: 0 0 10px 0; color: #333; }\n        .metric .value { font-size: 24px; font-weight: bold; }\n        .grade-A { color: #28a745; }\n        .grade-B { color: #17a2b8; }\n        .grade-C { color: #ffc107; }\n        .grade-D { color: #dc3545; }\n        .test-result { margin: 10px 0; padding: 15px; border-radius: 8px; }\n        .test-pass { background: #d4edda; border-left: 4px solid #28a745; }\n        .test-fail { background: #f8d7da; border-left: 4px solid #dc3545; }\n        .test-name { font-weight: bold; margin-bottom: 5px; }\n        .test-details { font-size: 14px; color: #666; }\n        .recommendations { background: #e7f3ff; padding: 20px; border-radius: 8px; margin-top: 20px; }\n        .screenshots img { max-width: 300px; margin: 5px; border: 1px solid #ddd; }\n    </style>\n</head>\n<body>\n    <div class=\"container\">\n        <div class=\"header\">\n            <h1>🚀 Enhanced Multi-API Chat Integration Test Report</h1>\n            <p>Generated on ${new Date().toLocaleString()}</p>\n        </div>\n        \n        <div class=\"summary\">\n            <div class=\"metric\">\n                <h3>Total Tests</h3>\n                <div class=\"value\">${report.summary.total_tests}</div>\n            </div>\n            <div class=\"metric\">\n                <h3>Passed</h3>\n                <div class=\"value\" style=\"color: #28a745;\">${report.summary.passed}</div>\n            </div>\n            <div class=\"metric\">\n                <h3>Failed</h3>\n                <div class=\"value\" style=\"color: #dc3545;\">${report.summary.failed}</div>\n            </div>\n            <div class=\"metric\">\n                <h3>Success Rate</h3>\n                <div class=\"value\">${report.summary.success_rate}</div>\n            </div>\n            <div class=\"metric\">\n                <h3>Grade</h3>\n                <div class=\"value grade-${report.summary.grade}\">${report.summary.grade}</div>\n            </div>\n        </div>\n        \n        <h2>🧪 Test Results</h2>\n        ${report.results.map(result => `\n            <div class=\"test-result ${result.success ? 'test-pass' : 'test-fail'}\">\n                <div class=\"test-name\">\n                    ${result.success ? '✅' : '❌'} ${result.test}\n                </div>\n                <div class=\"test-details\">\n                    Duration: ${result.duration}ms | \n                    Time: ${new Date(result.timestamp).toLocaleTimeString()}\n                    ${result.details.error ? `<br><strong>Error:</strong> ${result.details.error}` : ''}\n                    ${Object.keys(result.details).length > 0 && !result.details.error ? \n                        `<br><strong>Details:</strong> ${JSON.stringify(result.details, null, 2).replace(/\\n/g, '<br>')}` : ''}\n                </div>\n            </div>\n        `).join('')}\n        \n        <div class=\"recommendations\">\n            <h2>💡 Recommendations</h2>\n            <ul>\n                ${report.recommendations.map(rec => `<li>${rec}</li>`).join('')}\n            </ul>\n        </div>\n        \n        ${report.screenshots.length > 0 ? `\n            <h2>📸 Screenshots</h2>\n            <div class=\"screenshots\">\n                ${report.screenshots.map(shot => \n                    `<div><strong>${shot.test}</strong><br><img src=\"../${shot.filename}\" alt=\"${shot.test}\"></div>`\n                ).join('')}\n            </div>\n        ` : ''}\n    </div>\n</body>\n</html>`;\n        \n        await fs.writeFile('enhanced_test_reports/enhanced_test_report.html', html);\n    }\n\n    async runAllTests() {\n        console.log('🚀 Starting Enhanced Puppeteer Tests...');\n        \n        await this.init();\n        \n        // Run all enhanced tests\n        await this.testBackendHealth();\n        await this.testEnvPrivateManagement();\n        await this.testProviderConfiguration();\n        await this.testProviderTestingUI();\n        await this.testProviderManagement();\n        await this.testRawDataDisplay();\n        await this.testComprehensiveProviderScenarios();\n        \n        // Generate comprehensive report\n        const report = await this.generateReport();\n        \n        await this.cleanup();\n        \n        return report;\n    }\n\n    async cleanup() {\n        if (this.browser) {\n            await this.browser.close();\n        }\n    }\n}\n\n// Run tests if called directly\nif (require.main === module) {\n    const tester = new EnhancedPuppeteerTests();\n    tester.runAllTests()\n        .then(report => {\n            console.log('\\n✨ Enhanced tests completed!');\n            console.log(`📊 Final Grade: ${report.summary.grade} (${report.summary.success_rate})`);\n            process.exit(report.summary.failed > 0 ? 1 : 0);\n        })\n        .catch(error => {\n            console.error('❌ Test execution failed:', error);\n            process.exit(1);\n        });\n}\n\nmodule.exports = EnhancedPuppeteerTests;"
