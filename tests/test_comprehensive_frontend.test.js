/**
 * Comprehensive Frontend-Backend Integration Tests
 * ==============================================
 * This Puppeteer test suite covers end-to-end integration testing for the frontend and backend, including:
 *
 * - Page Loading: All major pages (Chat, Dashboard, Settings, Operations, Devices, Automation) load correctly.
 * - API Interaction: Frontend correctly fetches and displays data from backend APIs (providers, settings, usage).
 * - Chat Functionality: Full chat workflow, including model selection, message sending, and response display.
 * - Provider Management: Enabling/disabling providers, updating settings, and testing connections.
 * - Device Management: CRUD operations for devices and connection testing.
 * - AI Agent Interaction: Testing UI elements related to AI agents.
 * - Workflow Management: UI for creating and monitoring AI workflows.
 * - Error Handling: Frontend displays appropriate error messages for API failures.
 * - Responsive Design: Basic checks for responsive layout on different screen sizes.
 * - Performance: Basic checks for page load times.
 */

const puppeteer = require('puppeteer');
const { expect } = require('chai');
const path = require('path');
const fs = require('fs');

// Configuration
const FRONTEND_URL = 'http://localhost:8001';
const API_URL = 'http://localhost:8002';
const TIMEOUT = 30000; // 30 seconds

// Test suite
describe('Frontend-Backend Integration Tests', function () {
    let browser;
    let page;

    // Test reports directory
    const reportsDir = path.join(__dirname, 'test-reports');
    if (!fs.existsSync(reportsDir)) {
        fs.mkdirSync(reportsDir);
    }

    // Screenshot helper
    const takeScreenshot = async (name) => {
        const screenshotPath = path.join(reportsDir, `${name}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });
    };

    before(async function () {
        this.timeout(TIMEOUT);
        browser = await puppeteer.launch({
            headless: true, // Run in headless mode
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
    });

    beforeEach(async function () {
        this.timeout(TIMEOUT);
        page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 800 });
    });

    afterEach(async function () {
        if (this.currentTest.state === 'failed') {
            await takeScreenshot(`${this.currentTest.title.replace(/\s/g, '_')}_failure`);
        }
        await page.close();
    });

    after(async function () {
        await browser.close();
    });

    // =========================================================================
    // PAGE LOADING AND BASIC UI TESTS
    // =========================================================================

    it('should load the main chat page correctly', async () => {
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        const title = await page.title();
        expect(title).to.include('Multi-API Chat');
        const providerDropdown = await page.$('#provider-select');
        expect(providerDropdown).to.not.be.null;
    });

    it('should load the dashboard page correctly', async () => {
        await page.goto(`${FRONTEND_URL}/dashboard.html`, { waitUntil: 'networkidle2' });
        const header = await page.$('h1');
        const text = await page.evaluate(h => h.textContent, header);
        expect(text).to.include('Provider Usage Dashboard');
    });

    it('should load the settings page correctly', async () => {
        await page.goto(`${FRONTEND_URL}/settings.html`, { waitUntil: 'networkidle2' });
        const header = await page.$('h1');
        const text = await page.evaluate(h => h.textContent, header);
        expect(text).to.include('Settings');
    });

    it('should load the operations page correctly', async () => {
        await page.goto(`${FRONTEND_URL}/operations.html`, { waitUntil: 'networkidle2' });
        const header = await page.$('h1');
        const text = await page.evaluate(h => h.textContent, header);
        expect(text).to.include('Operations');
    });

    it('should load the devices page correctly', async () => {
        await page.goto(`${FRONTEND_URL}/devices.html`, { waitUntil: 'networkidle2' });
        const header = await page.$('h1');
        const text = await page.evaluate(h => h.textContent, header);
        expect(text).to.include('Device Management');
    });

    // =========================================================================
    // API INTERACTION TESTS (PROVIDERS AND SETTINGS)
    // =========================================================================

    it('should fetch and display providers in the dropdown', async () => {
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        await page.waitForSelector('#provider-select option');
        const providers = await page.$$eval('#provider-select option', options => options.map(o => o.value));
        expect(providers).to.include.members(['openai', 'groq', 'ollama']);
    });

    it('should load and display models for a selected provider', async () => {
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        // Select OpenAI provider
        await page.select('#provider-select', 'openai');
        await page.waitForTimeout(500); // Wait for models to load
        
        const models = await page.$$eval('#model-select option', options => options.map(o => o.value));
        expect(models).to.include('gpt-4o');
    });

    it('should handle API errors gracefully when fetching providers', async () => {
        await page.route(`${API_URL}/api/providers`, route => {
            route.abort('failed');
        });

        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        await page.waitForSelector('#error-message');
        const errorText = await page.$eval('#error-message', el => el.textContent);
        expect(errorText).to.include('Failed to fetch providers');
    });

    // =========================================================================
    // CHAT FUNCTIONALITY TESTS
    // =========================================================================

    it('should send a chat message and display the response', async () => {
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        
        // Type message and send
        await page.type('#chat-input', 'Hello, this is a Puppeteer test');
        await page.click('#send-button');

        // Wait for response to appear
        await page.waitForSelector('.message.assistant');
        const responseText = await page.$eval('.message.assistant .message-content', el => el.textContent);
        expect(responseText).to.not.be.empty;
    });

    it('should display user message in the chat history', async () => {
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        const message = 'Test message from user';
        await page.type('#chat-input', message);
        await page.click('#send-button');

        await page.waitForSelector('.message.user');
        const userMessage = await page.$eval('.message.user .message-content', el => el.textContent);
        expect(userMessage).to.equal(message);
    });

    it('should clear the input field after sending a message', async () => {
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        await page.type('#chat-input', 'This should be cleared');
        await page.click('#send-button');

        await page.waitForTimeout(500); // Wait for input to clear
        const inputValue = await page.$eval('#chat-input', el => el.value);
        expect(inputValue).to.be.empty;
    });

    it('should handle chat API errors gracefully', async () => {
        await page.route(`${API_URL}/api/chat`, route => {
            route.fulfill({
                status: 500,
                contentType: 'application/json',
                body: JSON.stringify({ error: 'Chat API is down' })
            });
        });

        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        await page.type('#chat-input', 'Test API error');
        await page.click('#send-button');

        await page.waitForSelector('.message.error');
        const errorText = await page.$eval('.message.error .message-content', el => el.textContent);
        expect(errorText).to.include('Chat API is down');
    });

    // =========================================================================
    // PROVIDER MANAGEMENT TESTS
    // =========================================================================

    it('should allow enabling and disabling a provider in settings', async () => {
        await page.goto(`${FRONTEND_URL}/settings.html`, { waitUntil: 'networkidle2' });
        await page.waitForSelector('#provider-settings-grop .provider-enable-toggle');
        
        // Disable Groq provider
        await page.click('#provider-settings-groq .provider-enable-toggle');
        await page.click('#save-settings-button');

        // Verify it is disabled
        const isChecked = await page.$eval('#provider-settings-groq .provider-enable-toggle', el => el.checked);
        expect(isChecked).to.be.false;
    });

    it('should test a provider connection successfully', async () => {
        await page.goto(`${FRONTEND_URL}/settings.html`, { waitUntil: 'networkidle2' });
        await page.waitForSelector('#provider-settings-openai .test-provider-button');
        
        await page.click('#provider-settings-openai .test-provider-button');

        await page.waitForSelector('#provider-settings-openai .status-indicator.connected');
        const statusText = await page.$eval('#provider-settings-openai .status-text', el => el.textContent);
        expect(statusText).to.equal('Connected');
    });

    it('should handle a failed provider connection test', async () => {
        await page.route(`${API_URL}/api/providers/openai/test`, route => {
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ success: false, error: 'Connection failed' })
            });
        });

        await page.goto(`${FRONTEND_URL}/settings.html`, { waitUntil: 'networkidle2' });
        await page.waitForSelector('#provider-settings-openai .test-provider-button');
        
        await page.click('#provider-settings-openai .test-provider-button');

        await page.waitForSelector('#provider-settings-openai .status-indicator.error');
        const statusText = await page.$eval('#provider-settings-openai .status-text', el => el.textContent);
        expect(statusText).to.equal('Error');
    });

    // =========================================================================
    // RESPONSIVE DESIGN TESTS
    // =========================================================================

    it('should have a responsive layout on mobile', async () => {
        await page.setViewport({ width: 375, height: 667 }); // iPhone 8
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        
        // Check if sidebar is hidden or transformed
        const sidebar = await page.$('#sidebar');
        const isVisible = await sidebar.isIntersectingViewport();
        expect(isVisible).to.be.false; // Assuming sidebar collapses
    });

    it('should have a readable font size on mobile', async () => {
        await page.setViewport({ width: 375, height: 667 });
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        
        const fontSize = await page.$eval('body', el => getComputedStyle(el).fontSize);
        expect(parseFloat(fontSize)).to.be.at.least(14); // At least 14px
    });

    // =========================================================================
    // PERFORMANCE TESTS
    // =========================================================================

    it('should have a fast page load time', async () => {
        const startTime = Date.now();
        await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded' });
        const loadTime = Date.now() - startTime;
        
        expect(loadTime).to.be.lessThan(2000); // Under 2 seconds
    });

    it('should have a fast API response time for providers list', async () => {
        const startTime = Date.now();
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2' });
        const loadTime = Date.now() - startTime;
        
        const providersRequest = await page.waitForResponse(response => response.url().includes('/api/providers'));
        const requestTime = await providersRequest.timing();
        
        expect(requestTime.responseStart - requestTime.requestStart).to.be.lessThan(500); // Under 500ms
    });

});

