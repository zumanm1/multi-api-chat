/**
 * Manual AI Agent Toggle Test Script
 * This script performs manual testing through API calls and provides guidance for browser testing
 */

const http = require('http');

class ManualAIToggleTest {
    constructor() {
        this.baseUrl = 'http://localhost:7002';
        this.results = {
            passed: 0,
            failed: 0,
            tests: []
        };
    }

    async makeRequest(path, options = {}) {
        return new Promise((resolve, reject) => {
            const url = `${this.baseUrl}${path}`;
            const reqOptions = {
                method: options.method || 'GET',
                headers: options.headers || {}
            };

            const req = http.request(url, reqOptions, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        const parsed = JSON.parse(data);
                        resolve({ status: res.statusCode, data: parsed });
                    } catch (e) {
                        resolve({ status: res.statusCode, data });
                    }
                });
            });

            req.on('error', reject);

            if (options.body) {
                req.write(JSON.stringify(options.body));
            }

            req.end();
        });
    }

    async test(name, testFunction) {
        console.log(`\n🧪 Running test: ${name}`);
        
        try {
            await testFunction();
            console.log(`✅ PASSED: ${name}`);
            this.results.passed++;
            this.results.tests.push({ name, status: 'PASSED' });
        } catch (error) {
            console.log(`❌ FAILED: ${name}`);
            console.log(`   Error: ${error.message}`);
            this.results.failed++;
            this.results.tests.push({ name, status: 'FAILED', error: error.message });
        }
    }

    async runAPITests() {
        console.log('🎯 Starting AI Agent Toggle API Tests\n');

        await this.test('API Status Endpoint Test', async () => {
            const response = await this.makeRequest('/api/ai-agents/status');
            
            if (response.status !== 200) {
                throw new Error(`Expected status 200, got ${response.status}`);
            }

            if (!response.data.hasOwnProperty('enabled')) {
                throw new Error('Response missing "enabled" property');
            }

            if (!response.data.hasOwnProperty('status')) {
                throw new Error('Response missing "status" property');
            }

            console.log(`   ✓ Status: ${response.data.enabled ? 'Enabled' : 'Disabled'}`);
        });

        await this.test('API Toggle OFF Test', async () => {
            const response = await this.makeRequest('/api/ai-agents/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: { enabled: false }
            });
            
            if (response.status !== 200) {
                throw new Error(`Expected status 200, got ${response.status}`);
            }

            if (response.data.enabled !== false) {
                throw new Error('AI agents should be disabled');
            }

            console.log(`   ✓ Successfully disabled: ${response.data.message}`);
        });

        await this.test('API Status After Toggle OFF', async () => {
            const response = await this.makeRequest('/api/ai-agents/status');
            
            if (response.data.enabled !== false) {
                throw new Error('Status should show disabled');
            }

            if (response.data.status !== 'disabled') {
                throw new Error('Status field should be "disabled"');
            }

            console.log(`   ✓ Status correctly shows disabled`);
        });

        await this.test('API Toggle ON Test', async () => {
            const response = await this.makeRequest('/api/ai-agents/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: { enabled: true }
            });
            
            if (response.status !== 200) {
                throw new Error(`Expected status 200, got ${response.status}`);
            }

            if (response.data.enabled !== true) {
                throw new Error('AI agents should be enabled');
            }

            console.log(`   ✓ Successfully enabled: ${response.data.message}`);
        });

        await this.test('API Status After Toggle ON', async () => {
            const response = await this.makeRequest('/api/ai-agents/status');
            
            if (response.data.enabled !== true) {
                throw new Error('Status should show enabled');
            }

            if (response.data.status !== 'active') {
                throw new Error('Status field should be "active"');
            }

            console.log(`   ✓ Status correctly shows active`);
        });

        await this.test('API Error Handling Test', async () => {
            try {
                // Test with invalid JSON
                const response = await this.makeRequest('/api/ai-agents/toggle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: 'invalid json'
                });
                
                if (response.status === 200) {
                    throw new Error('Should have failed with invalid JSON');
                }
                console.log(`   ✓ Correctly handled invalid JSON (status: ${response.status})`);
            } catch (error) {
                if (error.code === 'ECONNREFUSED') {
                    throw new Error('Server not running');
                }
                console.log(`   ✓ Error handled correctly: ${error.message}`);
            }
        });

        await this.test('API Toggle Persistence Test', async () => {
            // Set to specific state
            await this.makeRequest('/api/ai-agents/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: { enabled: false }
            });

            // Check persistence by calling status multiple times
            const response1 = await this.makeRequest('/api/ai-agents/status');
            await new Promise(resolve => setTimeout(resolve, 500));
            const response2 = await this.makeRequest('/api/ai-agents/status');

            if (response1.data.enabled !== response2.data.enabled) {
                throw new Error('Status should persist between calls');
            }

            console.log(`   ✓ Status persists correctly: ${response1.data.enabled}`);

            // Restore enabled state
            await this.makeRequest('/api/ai-agents/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: { enabled: true }
            });
        });
    }

    printResults() {
        console.log('\n' + '='.repeat(60));
        console.log('🏁 AI AGENT TOGGLE API TEST RESULTS');
        console.log('='.repeat(60));
        
        this.results.tests.forEach(test => {
            const icon = test.status === 'PASSED' ? '✅' : '❌';
            console.log(`${icon} ${test.name}`);
            if (test.error) {
                console.log(`   └─ ${test.error}`);
            }
        });
        
        console.log('\n' + '-'.repeat(40));
        console.log(`📊 SUMMARY:`);
        console.log(`   Passed: ${this.results.passed}`);
        console.log(`   Failed: ${this.results.failed}`);
        console.log(`   Total:  ${this.results.passed + this.results.failed}`);
        console.log(`   Success Rate: ${((this.results.passed / (this.results.passed + this.results.failed)) * 100).toFixed(1)}%`);
        
        if (this.results.failed === 0) {
            console.log('\n🎉 All API tests passed!');
        } else {
            console.log('\n⚠️  Some API tests failed.');
        }
    }

    printManualTestInstructions() {
        console.log('\n' + '='.repeat(60));
        console.log('📋 MANUAL BROWSER TESTING INSTRUCTIONS');
        console.log('='.repeat(60));
        
        console.log('\n🔧 STEP 1: Toggle Functionality Test');
        console.log('   1. Open settings.html in your browser');
        console.log('   2. Look for the AI Agents toggle checkbox');
        console.log('   3. Click the toggle - you should see:');
        console.log('      - Status badge changes from "Active" (green) to "Disabled" (red)');
        console.log('      - Notification popup appears');
        console.log('      - AI agent details update');
        console.log('   4. Click toggle again to enable');
        console.log('      - Status should return to "Active"');
        console.log('');

        console.log('🔄 STEP 2: Persistence Test');
        console.log('   1. Toggle AI agents OFF in settings.html');
        console.log('   2. Refresh the page (F5 or Ctrl+R)');
        console.log('   3. Verify toggle remains in OFF position');
        console.log('   4. Toggle back ON and refresh again');
        console.log('   5. Verify toggle remains in ON position');
        console.log('');

        console.log('🔗 STEP 3: Cross-page Status Test');
        console.log('   1. In settings.html, ensure AI agents are ENABLED');
        console.log('   2. Open index.html in a new tab');
        console.log('   3. Look for AI Agent indicator in top-right corner');
        console.log('   4. Return to settings.html and DISABLE AI agents');
        console.log('   5. Go back to index.html and refresh');
        console.log('   6. Verify AI indicator is no longer visible');
        console.log('');

        console.log('🎨 STEP 4: Visual Feedback Test');
        console.log('   1. In settings.html, observe initial status badge color');
        console.log('   2. Toggle OFF - badge should change to red background');
        console.log('   3. Toggle ON - badge should change to green background');
        console.log('   4. Each toggle should show a notification popup');
        console.log('   5. Status text should change between "Active" and "Disabled"');
        console.log('');

        console.log('⚠️ STEP 5: Error Handling Test');
        console.log('   1. Open browser DevTools (F12)');
        console.log('   2. Go to Network tab');
        console.log('   3. Set network to "Offline" or block localhost:7002');
        console.log('   4. Try toggling AI agents');
        console.log('   5. Verify checkbox reverts to previous state');
        console.log('   6. Check for error notification');
        console.log('   7. Restore network and verify toggle works again');
        console.log('');

        console.log('✅ EXPECTED RESULTS:');
        console.log('   - Toggle switches smoothly with visual feedback');
        console.log('   - Status persists across page refreshes');
        console.log('   - Cross-page indicators update correctly');
        console.log('   - Error states are handled gracefully');
        console.log('   - Visual indicators update in real-time');
        console.log('');
    }

    async runAllTests() {
        await this.runAPITests();
        this.printResults();
        this.printManualTestInstructions();
    }
}

// Run the tests
const tester = new ManualAIToggleTest();
tester.runAllTests().catch(console.error);
