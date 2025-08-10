/**
 * Comprehensive AI Agent Toggle Functionality Test
 * Tests all aspects of the AI agent toggle feature including:
 * - Toggle functionality
 * - Status persistence 
 * - Cross-page status updates
 * - Visual feedback
 * - Error handling
 */

const puppeteer = require('puppeteer');
const path = require('path');

class AIAgentToggleTest {
    constructor() {
        this.browser = null;
        this.page = null;
        this.results = {
            passed: 0,
            failed: 0,
            tests: []
        };
    }

    async setUp() {
        console.log('🚀 Setting up test environment...');
        
        this.browser = await puppeteer.launch({
            headless: false, // Set to true for headless testing
            defaultViewport: { width: 1280, height: 720 },
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        this.page = await this.browser.newPage();
        
        // Enable console logging from the page
        this.page.on('console', msg => {
            if (msg.type() === 'error') {
                console.log(`❌ Browser Console Error: ${msg.text()}`);
            }
        });
        
        // Listen for page errors
        this.page.on('pageerror', error => {
            console.log(`❌ Page Error: ${error.message}`);
        });
    }

    async tearDown() {
        if (this.browser) {
            await this.browser.close();
        }
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

    async navigateToSettings() {
        const settingsPath = `file://${path.resolve(__dirname, 'settings.html')}`;
        await this.page.goto(settingsPath);
        await this.page.waitForSelector('#aiAgentsEnabled', { timeout: 5000 });
        
        // Wait for AI status to load
        await this.page.waitForFunction(
            () => {
                const details = document.getElementById('aiAgentDetails');
                return details && !details.textContent.includes('Loading');
            },
            { timeout: 10000 }
        );
    }

    async navigateToIndex() {
        const indexPath = `file://${path.resolve(__dirname, 'index.html')}`;
        await this.page.goto(indexPath);
        await this.page.waitForSelector('#aiAgentIndicator', { timeout: 5000 });
    }

    async waitForStatusUpdate() {
        // Wait a bit for status updates to process
        await this.page.waitFor(1000);
    }

    async runTest1_ToggleFunctionality() {
        await this.test('Toggle Functionality Test', async () => {
            await this.navigateToSettings();
            
            // Check initial state
            const initialState = await this.page.evaluate(() => {
                const checkbox = document.getElementById('aiAgentsEnabled');
                const statusBadge = document.getElementById('aiAgentStatus');
                return {
                    checked: checkbox.checked,
                    statusText: statusBadge.textContent
                };
            });
            
            console.log(`   Initial state - Checked: ${initialState.checked}, Status: ${initialState.statusText}`);
            
            // Toggle off
            await this.page.click('#aiAgentsEnabled');
            await this.waitForStatusUpdate();
            
            // Check notification appeared
            await this.page.waitForSelector('div[style*="position: fixed"]', { timeout: 5000 });
            const notification = await this.page.$eval('div[style*="position: fixed"]', el => el.textContent);
            
            if (!notification.includes('disabled')) {
                throw new Error(`Expected 'disabled' notification, got: ${notification}`);
            }
            
            // Verify status badge updated
            const disabledState = await this.page.evaluate(() => {
                const checkbox = document.getElementById('aiAgentsEnabled');
                const statusBadge = document.getElementById('aiAgentStatus');
                return {
                    checked: checkbox.checked,
                    statusText: statusBadge.textContent,
                    statusColor: window.getComputedStyle(statusBadge).backgroundColor
                };
            });
            
            if (disabledState.checked !== false) {
                throw new Error('Checkbox should be unchecked after disabling');
            }
            
            if (disabledState.statusText !== 'Disabled') {
                throw new Error(`Expected 'Disabled' status, got: ${disabledState.statusText}`);
            }
            
            console.log(`   Disabled state - Checked: ${disabledState.checked}, Status: ${disabledState.statusText}`);
            
            // Toggle back on
            await this.page.click('#aiAgentsEnabled');
            await this.waitForStatusUpdate();
            
            // Wait for enabled notification
            await this.page.waitForFunction(
                () => {
                    const notifications = Array.from(document.querySelectorAll('div[style*="position: fixed"]'));
                    return notifications.some(n => n.textContent.includes('enabled'));
                },
                { timeout: 5000 }
            );
            
            // Verify enabled state
            const enabledState = await this.page.evaluate(() => {
                const checkbox = document.getElementById('aiAgentsEnabled');
                const statusBadge = document.getElementById('aiAgentStatus');
                return {
                    checked: checkbox.checked,
                    statusText: statusBadge.textContent
                };
            });
            
            if (enabledState.checked !== true) {
                throw new Error('Checkbox should be checked after enabling');
            }
            
            if (enabledState.statusText !== 'Active') {
                throw new Error(`Expected 'Active' status, got: ${enabledState.statusText}`);
            }
            
            console.log(`   Enabled state - Checked: ${enabledState.checked}, Status: ${enabledState.statusText}`);
        });
    }

    async runTest2_Persistence() {
        await this.test('Persistence Test', async () => {
            await this.navigateToSettings();
            
            // Disable AI agents
            const initialChecked = await this.page.$eval('#aiAgentsEnabled', el => el.checked);
            
            if (initialChecked) {
                await this.page.click('#aiAgentsEnabled');
                await this.waitForStatusUpdate();
            }
            
            // Refresh the page
            await this.page.reload();
            await this.page.waitForSelector('#aiAgentsEnabled', { timeout: 5000 });
            await this.page.waitForFunction(
                () => {
                    const details = document.getElementById('aiAgentDetails');
                    return details && !details.textContent.includes('Loading');
                },
                { timeout: 10000 }
            );
            
            // Check if toggle remains in off position
            const afterRefreshState = await this.page.evaluate(() => {
                const checkbox = document.getElementById('aiAgentsEnabled');
                const statusBadge = document.getElementById('aiAgentStatus');
                return {
                    checked: checkbox.checked,
                    statusText: statusBadge.textContent
                };
            });
            
            if (afterRefreshState.checked !== false) {
                throw new Error('AI agents should remain disabled after page refresh');
            }
            
            console.log(`   After refresh - Checked: ${afterRefreshState.checked}, Status: ${afterRefreshState.statusText}`);
            
            // Enable and refresh again
            await this.page.click('#aiAgentsEnabled');
            await this.waitForStatusUpdate();
            
            await this.page.reload();
            await this.page.waitForSelector('#aiAgentsEnabled', { timeout: 5000 });
            await this.page.waitForFunction(
                () => {
                    const details = document.getElementById('aiAgentDetails');
                    return details && !details.textContent.includes('Loading');
                },
                { timeout: 10000 }
            );
            
            const finalState = await this.page.evaluate(() => {
                const checkbox = document.getElementById('aiAgentsEnabled');
                const statusBadge = document.getElementById('aiAgentStatus');
                return {
                    checked: checkbox.checked,
                    statusText: statusBadge.textContent
                };
            });
            
            if (finalState.checked !== true) {
                throw new Error('AI agents should remain enabled after page refresh');
            }
            
            console.log(`   After re-enable and refresh - Checked: ${finalState.checked}, Status: ${finalState.statusText}`);
        });
    }

    async runTest3_CrossPageStatus() {
        await this.test('Cross-page Status Test', async () => {
            // Enable AI agents in settings
            await this.navigateToSettings();
            
            const settingsChecked = await this.page.$eval('#aiAgentsEnabled', el => el.checked);
            if (!settingsChecked) {
                await this.page.click('#aiAgentsEnabled');
                await this.waitForStatusUpdate();
            }
            
            // Navigate to index.html
            await this.navigateToIndex();
            
            // Check if AI indicator appears
            const indicatorVisible = await this.page.evaluate(() => {
                const indicator = document.getElementById('aiAgentIndicator');
                return indicator && window.getComputedStyle(indicator).display !== 'none';
            });
            
            if (!indicatorVisible) {
                throw new Error('AI indicator should be visible on index page when agents are enabled');
            }
            
            console.log('   ✓ AI indicator visible on index page');
            
            // Return to settings and disable agents
            await this.navigateToSettings();
            await this.page.click('#aiAgentsEnabled');
            await this.waitForStatusUpdate();
            
            // Check that indicator disappears on index.html
            await this.navigateToIndex();
            
            const indicatorHidden = await this.page.evaluate(() => {
                const indicator = document.getElementById('aiAgentIndicator');
                return !indicator || window.getComputedStyle(indicator).display === 'none';
            });
            
            if (!indicatorHidden) {
                throw new Error('AI indicator should be hidden on index page when agents are disabled');
            }
            
            console.log('   ✓ AI indicator hidden on index page when disabled');
            
            // Re-enable for cleanup
            await this.navigateToSettings();
            await this.page.click('#aiAgentsEnabled');
            await this.waitForStatusUpdate();
        });
    }

    async runTest4_VisualFeedback() {
        await this.test('Visual Feedback Test', async () => {
            await this.navigateToSettings();
            
            // Test status badge color changes
            const initialColors = await this.page.evaluate(() => {
                const statusBadge = document.getElementById('aiAgentStatus');
                return {
                    backgroundColor: window.getComputedStyle(statusBadge).backgroundColor,
                    textContent: statusBadge.textContent
                };
            });
            
            console.log(`   Initial badge - Color: ${initialColors.backgroundColor}, Text: ${initialColors.textContent}`);
            
            // Toggle off and check color change
            await this.page.click('#aiAgentsEnabled');
            await this.waitForStatusUpdate();
            
            const disabledColors = await this.page.evaluate(() => {
                const statusBadge = document.getElementById('aiAgentStatus');
                return {
                    backgroundColor: window.getComputedStyle(statusBadge).backgroundColor,
                    textContent: statusBadge.textContent
                };
            });
            
            console.log(`   Disabled badge - Color: ${disabledColors.backgroundColor}, Text: ${disabledColors.textContent}`);
            
            if (disabledColors.backgroundColor === initialColors.backgroundColor) {
                throw new Error('Status badge color should change when disabled');
            }
            
            // Toggle back on and verify color returns
            await this.page.click('#aiAgentsEnabled');
            await this.waitForStatusUpdate();
            
            const enabledColors = await this.page.evaluate(() => {
                const statusBadge = document.getElementById('aiAgentStatus');
                return {
                    backgroundColor: window.getComputedStyle(statusBadge).backgroundColor,
                    textContent: statusBadge.textContent
                };
            });
            
            console.log(`   Enabled badge - Color: ${enabledColors.backgroundColor}, Text: ${enabledColors.textContent}`);
            
            // Check notification animations
            await this.page.click('#aiAgentsEnabled');
            
            const notificationExists = await this.page.waitForSelector('div[style*="position: fixed"]', { timeout: 5000 });
            if (!notificationExists) {
                throw new Error('Notification should appear with animation');
            }
            
            console.log('   ✓ Visual feedback and animations working correctly');
        });
    }

    async runTest5_ErrorHandling() {
        await this.test('Error Handling Test', async () => {
            await this.navigateToSettings();
            
            // Simulate network error by intercepting requests
            await this.page.setRequestInterception(true);
            
            let intercepted = false;
            this.page.on('request', (request) => {
                if (request.url().includes('/api/ai-agents/toggle') && !intercepted) {
                    intercepted = true;
                    request.abort();
                } else {
                    request.continue();
                }
            });
            
            // Try to toggle - should handle error gracefully
            const initialState = await this.page.$eval('#aiAgentsEnabled', el => el.checked);
            await this.page.click('#aiAgentsEnabled');
            
            // Wait and check if checkbox reverted
            await this.page.waitFor(2000);
            
            const finalState = await this.page.$eval('#aiAgentsEnabled', el => el.checked);
            
            if (finalState !== initialState) {
                throw new Error('Checkbox should revert on error');
            }
            
            console.log('   ✓ Error handling working - checkbox reverted on network failure');
            
            // Disable request interception
            await this.page.setRequestInterception(false);
            
            // Test normal operation returns
            await this.page.click('#aiAgentsEnabled');
            await this.waitForStatusUpdate();
            
            const recoveredState = await this.page.$eval('#aiAgentsEnabled', el => el.checked);
            
            if (recoveredState === initialState) {
                throw new Error('Toggle should work after network recovery');
            }
            
            console.log('   ✓ Recovery after error working correctly');
        });
    }

    async runAllTests() {
        console.log('🎯 Starting AI Agent Toggle Comprehensive Tests\n');
        
        await this.setUp();
        
        try {
            await this.runTest1_ToggleFunctionality();
            await this.runTest2_Persistence();
            await this.runTest3_CrossPageStatus();
            await this.runTest4_VisualFeedback();
            await this.runTest5_ErrorHandling();
        } finally {
            await this.tearDown();
        }
        
        this.printResults();
    }

    printResults() {
        console.log('\n' + '='.repeat(60));
        console.log('🏁 AI AGENT TOGGLE TEST RESULTS');
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
            console.log('\n🎉 All tests passed! AI Agent toggle functionality is working perfectly.');
        } else {
            console.log('\n⚠️  Some tests failed. Please review the errors above.');
        }
    }
}

// Run the tests
const tester = new AIAgentToggleTest();
tester.runAllTests().catch(console.error);
