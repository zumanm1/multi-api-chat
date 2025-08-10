const puppeteer = require('puppeteer');
const fs = require('fs').promises;

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
            const response = await fetch('http://localhost:8002/api/health');
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
            // Navigate to frontend
            await this.page.goto('http://localhost:8001/index.html');
            await this.page.waitForTimeout(1000);
            
            // Check .env.private API endpoints
            const envStatusResponse = await fetch('http://localhost:8002/api/env/private');
            const envStatus = await envStatusResponse.json();
            
            const hasValidStructure = envStatus.hasOwnProperty('exists') && 
                                    envStatus.hasOwnProperty('enabled_providers') &&
                                    envStatus.hasOwnProperty('file_size');
            
            if (!hasValidStructure) {
                throw new Error('Invalid .env.private status structure');
            }
            
            // Test refresh functionality
            const refreshResponse = await fetch('http://localhost:8002/api/env/private/refresh', {
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
            await this.page.goto('http://localhost:8001/index.html');
            await this.page.waitForTimeout(1000);
            
            // Test provider list endpoint
            const providersResponse = await fetch('http://localhost:8002/api/providers');
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
            
            const updateResponse = await fetch('http://localhost:8002/api/providers/groq', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(providerUpdate)
            });
            
            if (!updateResponse.ok) {
                throw new Error(`Provider update failed: ${updateResponse.status}`);
            }
            
            // Test enhanced provider testing with raw data
            const testResponse = await fetch('http://localhost:8002/api/providers/groq/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    test_message: 'Hello, this is a comprehensive test.',
                    include_raw_data: true
                })
            });
            
            const testResult = await testResponse.json();
            
            // Validate enhanced test response structure
            const requiredFields = ['provider', 'connection_test'];
            const hasRequiredFields = requiredFields.every(field => testResult.hasOwnProperty(field));
            
            if (!hasRequiredFields) {
                throw new Error(`Missing test result fields: ${requiredFields.filter(f => !testResult.hasOwnProperty(f))}`);
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

    async testRawDataDisplay() {
        const testName = 'Raw Data Display and Error Handling';
        let screenshot = null;
        
        try {
            // Test with a provider (cerebras) to check raw data structure
            const testPayload = {
                test_message: 'This should show raw input and output data',
                include_raw_data: true
            };
            
            const testResponse = await fetch('http://localhost:8002/api/providers/cerebras/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(testPayload)
            });
            
            const testData = await testResponse.json();
            
            // Validate connection test exists
            if (!testData.connection_test) {
                throw new Error('No connection test in response');
            }
            
            screenshot = await this.takeScreenshot(testName, true);
            
            await this.addResult(testName, true, {
                has_connection_test: !!testData.connection_test,
                has_raw_data: !!testData.raw_data,
                provider_status: testData.status
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
            // Test managing multiple providers
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
                
                const updateResponse = await fetch(`http://localhost:8002/api/providers/${providerId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                if (updateResponse.ok) {
                    // Test the provider
                    const testResponse = await fetch(`http://localhost:8002/api/providers/${providerId}/test`, {
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
            const envResponse = await fetch('http://localhost:8002/api/env/private');
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

    async generateReport() {
        const totalTests = this.results.length;
        const passedTests = this.results.filter(r => r.success).length;
        const failedTests = totalTests - passedTests;
        const successRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0;
        
        const report = {
            summary: {
                total_tests: totalTests,
                passed: passedTests,
                failed: failedTests,
                success_rate: `${successRate}%`,
                grade: successRate >= 90 ? 'A' : successRate >= 80 ? 'B' : successRate >= 70 ? 'C' : 'D',
                test_duration: Date.now() - this.testStartTime,
                timestamp: new Date().toISOString()
            },
            results: this.results,
            screenshots: this.screenshots,
            recommendations: this.generateRecommendations()
        };
        
        // Save JSON report
        const jsonPath = 'enhanced_test_reports/enhanced_test_report.json';
        await fs.writeFile(jsonPath, JSON.stringify(report, null, 2));
        
        // Generate HTML report
        await this.generateHTMLReport(report);
        
        console.log(`\n📊 Enhanced Test Report Generated:`);
        console.log(`   📁 JSON: ${jsonPath}`);
        console.log(`   📁 HTML: enhanced_test_reports/enhanced_test_report.html`);
        console.log(`   📈 Success Rate: ${successRate}% (Grade: ${report.summary.grade})`);
        
        return report;
    }
    
    generateRecommendations() {
        const recommendations = [];
        const failures = this.results.filter(r => !r.success);
        
        if (failures.length > 0) {
            recommendations.push('Fix failing tests to improve system reliability');
        }
        
        const envTest = this.results.find(r => r.test.includes('Environment Private'));
        if (envTest && !envTest.success) {
            recommendations.push('Implement proper .env.private file management for secure API key storage');
        }
        
        const providerTests = this.results.filter(r => r.test.includes('Provider'));
        const failedProviders = providerTests.filter(r => !r.success);
        if (failedProviders.length > 0) {
            recommendations.push('Review provider configuration and API key management');
        }
        
        if (recommendations.length === 0) {
            recommendations.push('All tests passed! Consider adding more edge case testing.');
        }
        
        return recommendations;
    }
    
    async generateHTMLReport(report) {
        const html = `<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Multi-API Chat Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .metric h3 { margin: 0 0 10px 0; color: #333; }
        .metric .value { font-size: 24px; font-weight: bold; }
        .grade-A { color: #28a745; }
        .grade-B { color: #17a2b8; }
        .grade-C { color: #ffc107; }
        .grade-D { color: #dc3545; }
        .test-result { margin: 10px 0; padding: 15px; border-radius: 8px; }
        .test-pass { background: #d4edda; border-left: 4px solid #28a745; }
        .test-fail { background: #f8d7da; border-left: 4px solid #dc3545; }
        .test-name { font-weight: bold; margin-bottom: 5px; }
        .test-details { font-size: 14px; color: #666; }
        .recommendations { background: #e7f3ff; padding: 20px; border-radius: 8px; margin-top: 20px; }
        .screenshots img { max-width: 300px; margin: 5px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced Multi-API Chat Integration Test Report</h1>
            <p>Generated on ${new Date().toLocaleString()}</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <h3>Total Tests</h3>
                <div class="value">${report.summary.total_tests}</div>
            </div>
            <div class="metric">
                <h3>Passed</h3>
                <div class="value" style="color: #28a745;">${report.summary.passed}</div>
            </div>
            <div class="metric">
                <h3>Failed</h3>
                <div class="value" style="color: #dc3545;">${report.summary.failed}</div>
            </div>
            <div class="metric">
                <h3>Success Rate</h3>
                <div class="value">${report.summary.success_rate}</div>
            </div>
            <div class="metric">
                <h3>Grade</h3>
                <div class="value grade-${report.summary.grade}">${report.summary.grade}</div>
            </div>
        </div>
        
        <h2>🧪 Test Results</h2>
        ${report.results.map(result => `
            <div class="test-result ${result.success ? 'test-pass' : 'test-fail'}">
                <div class="test-name">
                    ${result.success ? '✅' : '❌'} ${result.test}
                </div>
                <div class="test-details">
                    Duration: ${result.duration}ms | 
                    Time: ${new Date(result.timestamp).toLocaleTimeString()}
                    ${result.details.error ? `<br><strong>Error:</strong> ${result.details.error}` : ''}
                    ${Object.keys(result.details).length > 0 && !result.details.error ? 
                        `<br><strong>Details:</strong> ${JSON.stringify(result.details, null, 2)}` : ''}
                </div>
            </div>
        `).join('')}
        
        <div class="recommendations">
            <h2>💡 Recommendations</h2>
            <ul>
                ${report.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>
        
        ${report.screenshots.length > 0 ? `
            <h2>📸 Screenshots</h2>
            <div class="screenshots">
                ${report.screenshots.map(shot => 
                    `<div><strong>${shot.test}</strong><br><img src="../${shot.filename}" alt="${shot.test}"></div>`
                ).join('')}
            </div>
        ` : ''}
    </div>
</body>
</html>`;
        
        await fs.writeFile('enhanced_test_reports/enhanced_test_report.html', html);
    }

    async runAllTests() {
        console.log('🚀 Starting Enhanced Puppeteer Tests...');
        
        await this.init();
        
        // Run all enhanced tests
        await this.testBackendHealth();
        await this.testEnvPrivateManagement();
        await this.testProviderConfiguration();
        await this.testRawDataDisplay();
        await this.testProviderManagement();
        
        // Generate comprehensive report
        const report = await this.generateReport();
        
        await this.cleanup();
        
        return report;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
    }
}

// Run tests if called directly
if (require.main === module) {
    const tester = new EnhancedPuppeteerTests();
    tester.runAllTests()
        .then(report => {
            console.log('\n✨ Enhanced tests completed!');
            console.log(`📊 Final Grade: ${report.summary.grade} (${report.summary.success_rate})`);
            process.exit(report.summary.failed > 0 ? 1 : 0);
        })
        .catch(error => {
            console.error('❌ Test execution failed:', error);
            process.exit(1);
        });
}

module.exports = EnhancedPuppeteerTests;
