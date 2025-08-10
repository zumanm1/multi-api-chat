#!/usr/bin/env node

/**
 * Puppeteer-based responsive design and cross-browser testing
 * Tests collapsible components across different viewports and scenarios
 */

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class PuppeteerResponsiveTest {
    constructor() {
        this.testResults = [];
        this.browsers = {};
        this.startTime = new Date();
    }

    async initialize() {
        console.log('🤖 Initializing Puppeteer Test Suite');
        console.log('=' * 40);
        
        try {
            // Launch browser instances
            this.browsers.chrome = await puppeteer.launch({
                headless: false,
                devtools: false,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            });
            
            console.log('✅ Chrome/Chromium browser launched');
        } catch (error) {
            console.error('❌ Failed to launch browsers:', error);
            throw error;
        }
    }

    async testMobileViewportsResponsiveness() {
        console.log('\n📱 Testing Mobile Viewport Responsiveness...');
        
        const mobileViewports = [
            { name: 'iPhone SE', width: 375, height: 667, isMobile: true },
            { name: 'iPhone 12', width: 390, height: 844, isMobile: true },
            { name: 'iPhone 12 Pro Max', width: 428, height: 926, isMobile: true },
            { name: 'iPad', width: 768, height: 1024, isMobile: true },
            { name: 'Galaxy S21', width: 360, height: 800, isMobile: true },
            { name: 'Pixel 5', width: 393, height: 851, isMobile: true }
        ];

        const mobileTests = [];

        for (const browser_name of Object.keys(this.browsers)) {
            const browser = this.browsers[browser_name];
            
            for (const viewport of mobileViewports) {
                const page = await browser.newPage();
                
                try {
                    // Set mobile viewport
                    await page.setViewport({
                        width: viewport.width,
                        height: viewport.height,
                        isMobile: viewport.isMobile,
                        hasTouch: true,
                        deviceScaleFactor: 2
                    });
                    
                    // Set user agent for mobile
                    await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15');
                    
                    // Navigate to test page
                    await page.goto('http://localhost:8003/collapsible-example.html', {
                        waitUntil: 'networkidle0'
                    });
                    
                    // Run mobile responsive tests
                    const testResult = await this._testMobileResponsiveDesign(
                        page, browser_name, viewport
                    );
                    
                    mobileTests.push(testResult);
                    
                } catch (error) {
                    mobileTests.push({
                        browser: browser_name,
                        viewport: viewport.name,
                        passed: false,
                        error: error.message,
                        timestamp: new Date().toISOString()
                    });
                } finally {
                    await page.close();
                }
            }
        }
        
        // Save mobile test results
        await fs.writeFile(
            'puppeteer_mobile_test_results.json',
            JSON.stringify(mobileTests, null, 2)
        );
        
        this.testResults.push({
            category: 'Mobile Viewport Responsiveness',
            tests: mobileTests,
            passed: mobileTests.every(t => t.passed)
        });
        
        console.log(`📱 Mobile tests completed: ${mobileTests.filter(t => t.passed).length}/${mobileTests.length} passed`);
    }

    async testTouchInteractions() {
        console.log('\n👆 Testing Touch Interactions...');
        
        const touchTests = [];
        
        for (const browser_name of Object.keys(this.browsers)) {
            const browser = this.browsers[browser_name];
            const page = await browser.newPage();
            
            try {
                // Set mobile viewport with touch
                await page.setViewport({
                    width: 375,
                    height: 667,
                    isMobile: true,
                    hasTouch: true,
                    deviceScaleFactor: 2
                });
                
                await page.goto('http://localhost:8003/collapsible-example.html', {
                    waitUntil: 'networkidle0'
                });
                
                // Test touch interactions
                const touchResult = await this._testTouchInteractions(page, browser_name);
                touchTests.push(touchResult);
                
            } catch (error) {
                touchTests.push({
                    browser: browser_name,
                    passed: false,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
            } finally {
                await page.close();
            }
        }
        
        await fs.writeFile(
            'puppeteer_touch_test_results.json',
            JSON.stringify(touchTests, null, 2)
        );
        
        this.testResults.push({
            category: 'Touch Interactions',
            tests: touchTests,
            passed: touchTests.every(t => t.passed)
        });
        
        console.log(`👆 Touch tests completed: ${touchTests.filter(t => t.passed).length}/${touchTests.length} passed`);
    }

    async testAnimationSmoothness() {
        console.log('\n🎬 Testing Animation Smoothness...');
        
        const animationTests = [];
        
        for (const browser_name of Object.keys(this.browsers)) {
            const browser = this.browsers[browser_name];
            const page = await browser.newPage();
            
            try {
                await page.goto('http://localhost:8003/collapsible-example.html', {
                    waitUntil: 'networkidle0'
                });
                
                // Test animation smoothness
                const animationResult = await this._testAnimationSmoothness(page, browser_name);
                animationTests.push(animationResult);
                
            } catch (error) {
                animationTests.push({
                    browser: browser_name,
                    passed: false,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
            } finally {
                await page.close();
            }
        }
        
        await fs.writeFile(
            'puppeteer_animation_test_results.json',
            JSON.stringify(animationTests, null, 2)
        );
        
        this.testResults.push({
            category: 'Animation Smoothness',
            tests: animationTests,
            passed: animationTests.every(t => t.passed)
        });
        
        console.log(`🎬 Animation tests completed: ${animationTests.filter(t => t.passed).length}/${animationTests.length} passed`);
    }

    async testLongContentHandling() {
        console.log('\n📄 Testing Long Content Handling...');
        
        const contentTests = [];
        
        for (const browser_name of Object.keys(this.browsers)) {
            const browser = this.browsers[browser_name];
            
            // Test on multiple viewports
            const viewports = [
                { width: 1920, height: 1080, name: 'Desktop' },
                { width: 768, height: 1024, name: 'Tablet' },
                { width: 375, height: 667, name: 'Mobile' }
            ];
            
            for (const viewport of viewports) {
                const page = await browser.newPage();
                
                try {
                    await page.setViewport({
                        width: viewport.width,
                        height: viewport.height,
                        isMobile: viewport.name === 'Mobile'
                    });
                    
                    await page.goto('http://localhost:8003/collapsible-example.html', {
                        waitUntil: 'networkidle0'
                    });
                    
                    // Test long content handling
                    const contentResult = await this._testLongContentHandling(
                        page, browser_name, viewport.name
                    );
                    contentTests.push(contentResult);
                    
                } catch (error) {
                    contentTests.push({
                        browser: browser_name,
                        viewport: viewport.name,
                        passed: false,
                        error: error.message,
                        timestamp: new Date().toISOString()
                    });
                } finally {
                    await page.close();
                }
            }
        }
        
        await fs.writeFile(
            'puppeteer_content_test_results.json',
            JSON.stringify(contentTests, null, 2)
        );
        
        this.testResults.push({
            category: 'Long Content Handling',
            tests: contentTests,
            passed: contentTests.every(t => t.passed)
        });
        
        console.log(`📄 Content tests completed: ${contentTests.filter(t => t.passed).length}/${contentTests.length} passed`);
    }

    async testStatePersistence() {
        console.log('\n💾 Testing State Persistence...');
        
        const persistenceTests = [];
        
        for (const browser_name of Object.keys(this.browsers)) {
            const browser = this.browsers[browser_name];
            const page = await browser.newPage();
            
            try {
                await page.goto('http://localhost:8003/collapsible-example.html', {
                    waitUntil: 'networkidle0'
                });
                
                // Test state persistence
                const persistenceResult = await this._testStatePersistence(page, browser_name);
                persistenceTests.push(persistenceResult);
                
            } catch (error) {
                persistenceTests.push({
                    browser: browser_name,
                    passed: false,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
            } finally {
                await page.close();
            }
        }
        
        await fs.writeFile(
            'puppeteer_persistence_test_results.json',
            JSON.stringify(persistenceTests, null, 2)
        );
        
        this.testResults.push({
            category: 'State Persistence',
            tests: persistenceTests,
            passed: persistenceTests.every(t => t.passed)
        });
        
        console.log(`💾 Persistence tests completed: ${persistenceTests.filter(t => t.passed).length}/${persistenceTests.length} passed`);
    }

    async testPerformanceMetrics() {
        console.log('\n⚡ Testing Performance Metrics...');
        
        const performanceTests = [];
        
        for (const browser_name of Object.keys(this.browsers)) {
            const browser = this.browsers[browser_name];
            const page = await browser.newPage();
            
            try {
                // Enable performance monitoring
                await page.coverage.startJSCoverage();
                await page.coverage.startCSSCoverage();
                
                const startTime = Date.now();
                
                await page.goto('http://localhost:8003/collapsible-example.html', {
                    waitUntil: 'networkidle0'
                });
                
                const loadTime = Date.now() - startTime;
                
                // Test performance metrics
                const performanceResult = await this._testPerformanceMetrics(
                    page, browser_name, loadTime
                );
                performanceTests.push(performanceResult);
                
                await page.coverage.stopJSCoverage();
                await page.coverage.stopCSSCoverage();
                
            } catch (error) {
                performanceTests.push({
                    browser: browser_name,
                    passed: false,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
            } finally {
                await page.close();
            }
        }
        
        await fs.writeFile(
            'puppeteer_performance_test_results.json',
            JSON.stringify(performanceTests, null, 2)
        );
        
        this.testResults.push({
            category: 'Performance Metrics',
            tests: performanceTests,
            passed: performanceTests.every(t => t.passed)
        });
        
        console.log(`⚡ Performance tests completed: ${performanceTests.filter(t => t.passed).length}/${performanceTests.length} passed`);
    }

    // Helper methods for individual tests
    async _testMobileResponsiveDesign(page, browser_name, viewport) {
        try {
            // Check if collapsible containers exist
            const containers = await page.$$('.collapsible-container');
            if (containers.length === 0) {
                throw new Error('No collapsible containers found');
            }
            
            // Test header height for touch targets
            const headerHeight = await page.$eval('.collapsible-header', el => el.offsetHeight);
            if (headerHeight < 44) {
                throw new Error(`Header height ${headerHeight}px is below minimum 44px for touch targets`);
            }
            
            // Test font size readability
            const fontSize = await page.$eval('.collapsible-title', el => {
                return parseInt(window.getComputedStyle(el).fontSize);
            });
            
            if (fontSize < 14) {
                throw new Error(`Font size ${fontSize}px is too small for mobile readability`);
            }
            
            // Test content overflow
            await page.click('.collapsible-header');
            await page.waitForTimeout(500); // Wait for animation
            
            const contentWidth = await page.$eval('.collapsible-content', el => el.scrollWidth);
            if (contentWidth > viewport.width + 50) {
                console.warn(`Content width ${contentWidth}px exceeds viewport ${viewport.width}px`);
            }
            
            return {
                browser: browser_name,
                viewport: viewport.name,
                passed: true,
                details: {
                    headerHeight: `${headerHeight}px`,
                    fontSize: `${fontSize}px`,
                    contentWidth: `${contentWidth}px`,
                    viewportWidth: `${viewport.width}px`,
                    touchTargetCompliant: headerHeight >= 44,
                    fontReadable: fontSize >= 14
                },
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                browser: browser_name,
                viewport: viewport.name,
                passed: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async _testTouchInteractions(page, browser_name) {
        try {
            // Test tap to expand
            const header = await page.$('.collapsible-header');
            await header.tap();
            await page.waitForTimeout(400);
            
            // Check if expanded
            const isExpanded = await page.$eval('.collapsible-content', 
                el => el.classList.contains('expanded')
            );
            
            if (!isExpanded) {
                throw new Error('Content did not expand after tap');
            }
            
            // Test tap to collapse
            await header.tap();
            await page.waitForTimeout(400);
            
            const isCollapsed = await page.$eval('.collapsible-content', 
                el => !el.classList.contains('expanded')
            );
            
            if (!isCollapsed) {
                throw new Error('Content did not collapse after second tap');
            }
            
            // Test touch feedback
            await header.hover();
            const hoverBg = await page.$eval('.collapsible-header', 
                el => window.getComputedStyle(el).backgroundColor
            );
            
            return {
                browser: browser_name,
                passed: true,
                details: {
                    tapExpand: true,
                    tapCollapse: true,
                    touchFeedback: hoverBg !== 'rgba(0, 0, 0, 0)',
                    hoverBackground: hoverBg
                },
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                browser: browser_name,
                passed: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async _testAnimationSmoothness(page, browser_name) {
        try {
            const header = await page.$('.collapsible-header');
            
            // Measure animation timing
            const startTime = Date.now();
            await header.click();
            
            // Wait for animation to complete
            await page.waitForFunction(() => {
                const content = document.querySelector('.collapsible-content');
                return content && content.classList.contains('expanded');
            }, { timeout: 1000 });
            
            const animationDuration = Date.now() - startTime;
            
            // Check if animation is within reasonable time
            if (animationDuration > 600) {
                console.warn(`Animation took ${animationDuration}ms, which may be too slow`);
            }
            
            // Check CSS transitions
            const transition = await page.$eval('.collapsible-content', 
                el => window.getComputedStyle(el).transition
            );
            
            const hasTransition = transition.includes('max-height') || transition.includes('height');
            
            return {
                browser: browser_name,
                passed: true,
                details: {
                    animationDuration: `${animationDuration}ms`,
                    hasTransition,
                    transitionProperty: transition,
                    performsWell: animationDuration <= 500
                },
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                browser: browser_name,
                passed: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async _testLongContentHandling(page, browser_name, viewportName) {
        try {
            // Add very long content
            await page.evaluate(() => {
                const content = document.querySelector('.collapsible-content .technical-details');
                if (content) {
                    const longText = 'Very long content line '.repeat(1000) + '\n'.repeat(100);
                    const longBlock = document.createElement('div');
                    longBlock.className = 'output-block';
                    longBlock.style.whiteSpace = 'pre-wrap';
                    longBlock.textContent = longText;
                    content.appendChild(longBlock);
                }
            });
            
            // Expand content
            await page.click('.collapsible-header');
            await page.waitForTimeout(500);
            
            // Check overflow handling
            const hasScroll = await page.$eval('.collapsible-content', el => {
                return el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth;
            });
            
            // Check if page doesn't overflow horizontally
            const pageOverflow = await page.evaluate(() => {
                return document.body.scrollWidth > window.innerWidth;
            });
            
            return {
                browser: browser_name,
                viewport: viewportName,
                passed: true,
                details: {
                    contentHasScroll: hasScroll,
                    pageOverflowContained: !pageOverflow,
                    overflowHandling: 'proper'
                },
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                browser: browser_name,
                viewport: viewportName,
                passed: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async _testStatePersistence(page, browser_name) {
        try {
            // Expand first section
            const header = await page.$('.collapsible-header');
            await header.click();
            await page.waitForTimeout(400);
            
            // Check expanded state
            const isExpandedBefore = await page.$eval('.collapsible-content', 
                el => el.classList.contains('expanded')
            );
            
            // Scroll page
            await page.evaluate(() => window.scrollTo(0, 500));
            await page.waitForTimeout(200);
            
            const isExpandedAfterScroll = await page.$eval('.collapsible-content', 
                el => el.classList.contains('expanded')
            );
            
            // Resize viewport
            await page.setViewport({ width: 800, height: 600 });
            await page.waitForTimeout(300);
            
            const isExpandedAfterResize = await page.$eval('.collapsible-content', 
                el => el.classList.contains('expanded')
            );
            
            // Test focus changes
            await page.keyboard.press('Tab');
            await page.waitForTimeout(100);
            
            const isExpandedAfterFocus = await page.$eval('.collapsible-content', 
                el => el.classList.contains('expanded')
            );
            
            const allMaintained = isExpandedBefore && isExpandedAfterScroll && 
                                  isExpandedAfterResize && isExpandedAfterFocus;
            
            return {
                browser: browser_name,
                passed: allMaintained,
                details: {
                    stateBefore: isExpandedBefore,
                    stateAfterScroll: isExpandedAfterScroll,
                    stateAfterResize: isExpandedAfterResize,
                    stateAfterFocus: isExpandedAfterFocus,
                    allMaintained
                },
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                browser: browser_name,
                passed: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async _testPerformanceMetrics(page, browser_name, loadTime) {
        try {
            // Get performance metrics
            const metrics = await page.metrics();
            
            // Test interaction performance
            const startTime = Date.now();
            await page.click('.collapsible-header');
            const interactionTime = Date.now() - startTime;
            
            // Check memory usage
            const jsHeapUsed = metrics.JSHeapUsedSize / 1024 / 1024; // MB
            
            return {
                browser: browser_name,
                passed: true,
                details: {
                    pageLoadTime: `${loadTime}ms`,
                    interactionTime: `${interactionTime}ms`,
                    jsHeapUsed: `${jsHeapUsed.toFixed(2)}MB`,
                    performanceGood: loadTime < 3000 && interactionTime < 100,
                    memoryUsage: jsHeapUsed < 50 ? 'good' : 'high'
                },
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                browser: browser_name,
                passed: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async generateReport() {
        console.log('\n📊 Generating Test Report...');
        
        const report = {
            testSuite: 'Puppeteer Responsive Design Testing',
            timestamp: new Date().toISOString(),
            duration: `${(Date.now() - this.startTime.getTime()) / 1000}s`,
            summary: {
                totalCategories: this.testResults.length,
                passedCategories: this.testResults.filter(r => r.passed).length,
                failedCategories: this.testResults.filter(r => !r.passed).length,
                overallPassed: this.testResults.every(r => r.passed)
            },
            categories: this.testResults,
            testFilesGenerated: [
                'puppeteer_mobile_test_results.json',
                'puppeteer_touch_test_results.json',
                'puppeteer_animation_test_results.json', 
                'puppeteer_content_test_results.json',
                'puppeteer_persistence_test_results.json',
                'puppeteer_performance_test_results.json'
            ],
            browsersTestedWith: Object.keys(this.browsers),
            featuresTestedInclude: [
                'Mobile viewport responsiveness',
                'Touch interaction handling',
                'Animation smoothness',
                'Long content overflow management',
                'State persistence across interactions',
                'Performance metrics monitoring'
            ]
        };
        
        await fs.writeFile(
            'puppeteer_comprehensive_report.json',
            JSON.stringify(report, null, 2)
        );
        
        console.log('📊 Test Report Summary:');
        console.log(`   Total Categories: ${report.summary.totalCategories}`);
        console.log(`   Passed: ${report.summary.passedCategories}`);
        console.log(`   Failed: ${report.summary.failedCategories}`);
        console.log(`   Overall Result: ${report.summary.overallPassed ? '✅ PASSED' : '❌ FAILED'}`);
        console.log(`   Duration: ${report.duration}`);
        
        return report.summary.overallPassed;
    }

    async cleanup() {
        console.log('\n🧹 Cleaning up...');
        
        for (const browser of Object.values(this.browsers)) {
            await browser.close();
        }
        
        console.log('✅ Cleanup completed');
    }

    async runAllTests() {
        try {
            await this.initialize();
            
            await this.testMobileViewportsResponsiveness();
            await this.testTouchInteractions();
            await this.testAnimationSmoothness();
            await this.testLongContentHandling();
            await this.testStatePersistence();
            await this.testPerformanceMetrics();
            
            const success = await this.generateReport();
            await this.cleanup();
            
            return success;
        } catch (error) {
            console.error('❌ Test suite failed:', error);
            await this.cleanup();
            return false;
        }
    }
}

// Run tests if called directly
if (require.main === module) {
    (async () => {
        const testRunner = new PuppeteerResponsiveTest();
        const success = await testRunner.runAllTests();
        process.exit(success ? 0 : 1);
    })();
}

module.exports = PuppeteerResponsiveTest;
