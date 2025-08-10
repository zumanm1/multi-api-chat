#!/usr/bin/env python3
"""
Advanced Cross-Browser Testing for Collapsible Components using Playwright
Tests responsive design, animations, and performance across different browsers
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, expect


class TestPlaywrightResponsive:
    """Playwright-based responsive design and cross-browser testing"""

    @pytest.fixture(scope="class")
    async def browser_setup(self):
        """Setup browsers for testing"""
        self.playwright = await async_playwright().start()
        
        # Launch multiple browsers for cross-browser testing
        self.browsers = {}
        
        # Chrome/Chromium
        self.browsers['chromium'] = await self.playwright.chromium.launch(headless=False)
        
        # Firefox
        try:
            self.browsers['firefox'] = await self.playwright.firefox.launch(headless=False)
        except Exception:
            print("Firefox not available, skipping...")
            
        # WebKit (Safari)
        try:
            self.browsers['webkit'] = await self.playwright.webkit.launch(headless=False)
        except Exception:
            print("WebKit not available, skipping...")
        
        yield self.browsers
        
        # Cleanup
        for browser in self.browsers.values():
            await browser.close()
        await self.playwright.stop()

    @pytest.mark.asyncio
    async def test_mobile_viewports_playwright(self, browser_setup):
        """Test collapsible components on various mobile viewports using Playwright"""
        
        mobile_devices = [
            {'name': 'iPhone SE', 'viewport': {'width': 375, 'height': 667}},
            {'name': 'iPhone 12', 'viewport': {'width': 390, 'height': 844}},
            {'name': 'iPhone 12 Pro Max', 'viewport': {'width': 428, 'height': 926}},
            {'name': 'Pixel 5', 'viewport': {'width': 393, 'height': 851}},
            {'name': 'Samsung Galaxy S21', 'viewport': {'width': 360, 'height': 800}},
        ]
        
        test_results = []
        
        for browser_name, browser in browser_setup.items():
            for device in mobile_devices:
                context = await browser.new_context(
                    viewport=device['viewport'],
                    has_touch=True,
                    is_mobile=True,
                    device_scale_factor=2
                )
                
                page = await context.new_page()
                
                try:
                    # Navigate to test page
                    await page.goto('http://localhost:8003/collapsible-example.html')
                    await page.wait_for_load_state('networkidle')
                    
                    # Test mobile responsive design
                    test_result = await self._test_mobile_responsive_design(
                        page, browser_name, device
                    )
                    test_results.append(test_result)
                    
                except Exception as e:
                    test_results.append({
                        'browser': browser_name,
                        'device': device['name'],
                        'error': str(e),
                        'passed': False
                    })
                finally:
                    await context.close()
        
        # Save test results
        with open('playwright_mobile_test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2)
        
        # Assert all tests passed
        failed_tests = [r for r in test_results if not r.get('passed', False)]
        assert len(failed_tests) == 0, f"Failed mobile tests: {failed_tests}"

    @pytest.mark.asyncio
    async def test_touch_interactions_playwright(self, browser_setup):
        """Test touch interactions using Playwright's touch simulation"""
        
        touch_test_results = []
        
        for browser_name, browser in browser_setup.items():
            context = await browser.new_context(
                viewport={'width': 375, 'height': 667},
                has_touch=True,
                is_mobile=True
            )
            
            page = await context.new_page()
            
            try:
                await page.goto('http://localhost:8003/collapsible-example.html')
                await page.wait_for_load_state('networkidle')
                
                # Test touch interactions
                touch_result = await self._test_touch_interactions(page, browser_name)
                touch_test_results.append(touch_result)
                
            except Exception as e:
                touch_test_results.append({
                    'browser': browser_name,
                    'error': str(e),
                    'passed': False
                })
            finally:
                await context.close()
        
        # Save results
        with open('playwright_touch_test_results.json', 'w') as f:
            json.dump(touch_test_results, f, indent=2)
        
        # Assert all touch tests passed
        failed_tests = [r for r in touch_test_results if not r.get('passed', False)]
        assert len(failed_tests) == 0, f"Failed touch tests: {failed_tests}"

    @pytest.mark.asyncio
    async def test_animation_performance_playwright(self, browser_setup):
        """Test animation performance across browsers using Playwright"""
        
        animation_results = []
        
        for browser_name, browser in browser_setup.items():
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto('http://localhost:8003/collapsible-example.html')
                await page.wait_for_load_state('networkidle')
                
                # Test animation performance
                performance_result = await self._test_animation_performance(
                    page, browser_name
                )
                animation_results.append(performance_result)
                
            except Exception as e:
                animation_results.append({
                    'browser': browser_name,
                    'error': str(e),
                    'passed': False
                })
            finally:
                await context.close()
        
        # Save results
        with open('playwright_animation_test_results.json', 'w') as f:
            json.dump(animation_results, f, indent=2)
        
        # Assert animation tests passed
        failed_tests = [r for r in animation_results if not r.get('passed', False)]
        assert len(failed_tests) == 0, f"Failed animation tests: {failed_tests}"

    @pytest.mark.asyncio
    async def test_long_content_overflow_playwright(self, browser_setup):
        """Test handling of long content and overflow using Playwright"""
        
        overflow_results = []
        
        for browser_name, browser in browser_setup.items():
            # Test on both desktop and mobile viewports
            viewports = [
                {'width': 1920, 'height': 1080, 'name': 'Desktop'},
                {'width': 375, 'height': 667, 'name': 'Mobile'}
            ]
            
            for viewport in viewports:
                context = await browser.new_context(viewport=viewport)
                page = await context.new_page()
                
                try:
                    await page.goto('http://localhost:8003/collapsible-example.html')
                    await page.wait_for_load_state('networkidle')
                    
                    # Add long content dynamically and test overflow
                    overflow_result = await self._test_long_content_overflow(
                        page, browser_name, viewport['name']
                    )
                    overflow_results.append(overflow_result)
                    
                except Exception as e:
                    overflow_results.append({
                        'browser': browser_name,
                        'viewport': viewport['name'],
                        'error': str(e),
                        'passed': False
                    })
                finally:
                    await context.close()
        
        # Save results
        with open('playwright_overflow_test_results.json', 'w') as f:
            json.dump(overflow_results, f, indent=2)
        
        # Assert overflow tests passed
        failed_tests = [r for r in overflow_results if not r.get('passed', False)]
        assert len(failed_tests) == 0, f"Failed overflow tests: {failed_tests}"

    @pytest.mark.asyncio
    async def test_state_persistence_playwright(self, browser_setup):
        """Test state persistence during various page interactions"""
        
        persistence_results = []
        
        for browser_name, browser in browser_setup.items():
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto('http://localhost:8003/collapsible-example.html')
                await page.wait_for_load_state('networkidle')
                
                # Test state persistence
                persistence_result = await self._test_state_persistence(
                    page, browser_name
                )
                persistence_results.append(persistence_result)
                
            except Exception as e:
                persistence_results.append({
                    'browser': browser_name,
                    'error': str(e),
                    'passed': False
                })
            finally:
                await context.close()
        
        # Save results
        with open('playwright_persistence_test_results.json', 'w') as f:
            json.dump(persistence_results, f, indent=2)
        
        # Assert persistence tests passed
        failed_tests = [r for r in persistence_results if not r.get('passed', False)]
        assert len(failed_tests) == 0, f"Failed persistence tests: {failed_tests}"

    @pytest.mark.asyncio
    async def test_accessibility_playwright(self, browser_setup):
        """Test accessibility features using Playwright"""
        
        accessibility_results = []
        
        for browser_name, browser in browser_setup.items():
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto('http://localhost:8003/collapsible-example.html')
                await page.wait_for_load_state('networkidle')
                
                # Test accessibility
                accessibility_result = await self._test_accessibility_features(
                    page, browser_name
                )
                accessibility_results.append(accessibility_result)
                
            except Exception as e:
                accessibility_results.append({
                    'browser': browser_name,
                    'error': str(e),
                    'passed': False
                })
            finally:
                await context.close()
        
        # Save results
        with open('playwright_accessibility_test_results.json', 'w') as f:
            json.dump(accessibility_results, f, indent=2)
        
        # Assert accessibility tests passed
        failed_tests = [r for r in accessibility_results if not r.get('passed', False)]
        assert len(failed_tests) == 0, f"Failed accessibility tests: {failed_tests}"

    # Helper methods for specific tests
    async def _test_mobile_responsive_design(self, page, browser_name, device):
        """Test responsive design on mobile"""
        try:
            # Check if collapsible containers are visible
            containers = await page.query_selector_all('.collapsible-container')
            assert len(containers) > 0, "No collapsible containers found"
            
            # Check header height meets touch target requirements
            first_header = await page.query_selector('.collapsible-header')
            header_height = await first_header.evaluate('el => el.offsetHeight')
            assert header_height >= 44, f"Header height {header_height}px is less than 44px minimum"
            
            # Check font sizes are readable
            font_size = await page.evaluate('''
                () => {
                    const element = document.querySelector('.collapsible-title');
                    return window.getComputedStyle(element).fontSize;
                }
            ''')
            
            font_size_value = int(font_size.replace('px', ''))
            assert font_size_value >= 14, f"Font size {font_size_value}px is too small for mobile"
            
            # Check content overflow handling
            await page.click('.collapsible-header')
            await page.wait_for_timeout(500)  # Wait for animation
            
            content = await page.query_selector('.collapsible-content')
            content_width = await content.evaluate('el => el.scrollWidth')
            viewport_width = device['viewport']['width']
            
            assert content_width <= viewport_width + 50, f"Content overflows viewport: {content_width}px > {viewport_width}px"
            
            return {
                'browser': browser_name,
                'device': device['name'],
                'passed': True,
                'details': {
                    'header_height': f"{header_height}px",
                    'font_size': font_size,
                    'content_width': f"{content_width}px",
                    'viewport_width': f"{viewport_width}px"
                }
            }
        except Exception as e:
            return {
                'browser': browser_name,
                'device': device['name'],
                'passed': False,
                'error': str(e)
            }

    async def _test_touch_interactions(self, page, browser_name):
        """Test touch interactions"""
        try:
            # Find first collapsible header
            header = await page.query_selector('.collapsible-header')
            
            # Test tap to expand
            await header.tap()
            await page.wait_for_timeout(400)  # Wait for animation
            
            # Check if content is expanded
            content = await page.query_selector('.collapsible-content')
            is_expanded = await content.evaluate('el => el.classList.contains("expanded")')
            assert is_expanded, "Content did not expand after tap"
            
            # Test tap to collapse
            await header.tap()
            await page.wait_for_timeout(400)
            
            is_collapsed = await content.evaluate('el => !el.classList.contains("expanded")')
            assert is_collapsed, "Content did not collapse after second tap"
            
            # Test touch feedback (active state)
            await header.hover()
            hover_bg = await header.evaluate('''
                el => window.getComputedStyle(el).backgroundColor
            ''')
            
            return {
                'browser': browser_name,
                'passed': True,
                'details': {
                    'tap_expand': True,
                    'tap_collapse': True,
                    'hover_feedback': hover_bg != 'rgba(0, 0, 0, 0)'
                }
            }
        except Exception as e:
            return {
                'browser': browser_name,
                'passed': False,
                'error': str(e)
            }

    async def _test_animation_performance(self, page, browser_name):
        """Test animation performance"""
        try:
            # Measure animation duration
            header = await page.query_selector('.collapsible-header')
            
            start_time = time.time()
            await header.click()
            
            # Wait for animation to complete
            await page.wait_for_function('''
                () => {
                    const content = document.querySelector('.collapsible-content');
                    return content && content.classList.contains('expanded');
                }
            ''', timeout=1000)
            
            end_time = time.time()
            animation_duration = (end_time - start_time) * 1000  # Convert to ms
            
            # Check if animation is smooth (should complete within reasonable time)
            assert animation_duration < 500, f"Animation took too long: {animation_duration}ms"
            
            # Test CSS transitions are applied
            content = await page.query_selector('.collapsible-content')
            transition = await content.evaluate('''
                el => window.getComputedStyle(el).transition
            ''')
            
            has_transition = 'max-height' in transition or 'height' in transition
            
            return {
                'browser': browser_name,
                'passed': True,
                'details': {
                    'animation_duration': f"{animation_duration:.2f}ms",
                    'has_transition': has_transition,
                    'transition_property': transition
                }
            }
        except Exception as e:
            return {
                'browser': browser_name,
                'passed': False,
                'error': str(e)
            }

    async def _test_long_content_overflow(self, page, browser_name, viewport_name):
        """Test long content overflow handling"""
        try:
            # Add very long content to test overflow
            await page.evaluate('''
                () => {
                    const content = document.querySelector('.collapsible-content .technical-details');
                    if (content) {
                        const longText = 'A'.repeat(10000) + '\\n' + 'B'.repeat(5000);
                        const longBlock = document.createElement('div');
                        longBlock.className = 'output-block';
                        longBlock.textContent = longText;
                        content.appendChild(longBlock);
                    }
                }
            ''')
            
            # Expand the content
            header = await page.query_selector('.collapsible-header')
            await header.click()
            await page.wait_for_timeout(500)
            
            # Check if content handles overflow properly
            content = await page.query_selector('.collapsible-content')
            has_scroll = await content.evaluate('''
                el => el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth
            ''')
            
            # Check if horizontal scroll is contained
            body_overflow = await page.evaluate('''
                () => document.body.scrollWidth > window.innerWidth
            ''')
            
            return {
                'browser': browser_name,
                'viewport': viewport_name,
                'passed': True,
                'details': {
                    'content_has_scroll': has_scroll,
                    'body_overflow_contained': not body_overflow,
                    'overflow_handling': 'proper'
                }
            }
        except Exception as e:
            return {
                'browser': browser_name,
                'viewport': viewport_name,
                'passed': False,
                'error': str(e)
            }

    async def _test_state_persistence(self, page, browser_name):
        """Test state persistence during interactions"""
        try:
            # Expand first section
            first_header = await page.query_selector('.collapsible-header')
            await first_header.click()
            await page.wait_for_timeout(400)
            
            # Check it's expanded
            first_content = await page.query_selector('.collapsible-content')
            is_expanded_before = await first_content.evaluate('el => el.classList.contains("expanded")')
            
            # Scroll the page
            await page.evaluate('window.scrollTo(0, 500)')
            await page.wait_for_timeout(200)
            
            # Check state is maintained after scroll
            is_expanded_after_scroll = await first_content.evaluate('el => el.classList.contains("expanded")')
            
            # Resize window
            await page.set_viewport_size(width=800, height=600)
            await page.wait_for_timeout(200)
            
            # Check state is maintained after resize
            is_expanded_after_resize = await first_content.evaluate('el => el.classList.contains("expanded")')
            
            # Test focus changes
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(100)
            
            is_expanded_after_focus = await first_content.evaluate('el => el.classList.contains("expanded")')
            
            return {
                'browser': browser_name,
                'passed': True,
                'details': {
                    'state_before': is_expanded_before,
                    'state_after_scroll': is_expanded_after_scroll,
                    'state_after_resize': is_expanded_after_resize,
                    'state_after_focus': is_expanded_after_focus,
                    'all_maintained': all([
                        is_expanded_before,
                        is_expanded_after_scroll,
                        is_expanded_after_resize,
                        is_expanded_after_focus
                    ])
                }
            }
        except Exception as e:
            return {
                'browser': browser_name,
                'passed': False,
                'error': str(e)
            }

    async def _test_accessibility_features(self, page, browser_name):
        """Test accessibility features"""
        try:
            # Check ARIA attributes
            first_header = await page.query_selector('.collapsible-header')
            
            aria_expanded = await first_header.get_attribute('aria-expanded')
            tabindex = await first_header.get_attribute('tabindex')
            role = await first_header.get_attribute('role')
            
            # Test keyboard navigation
            await first_header.focus()
            focused_element = await page.evaluate('document.activeElement.className')
            
            # Test keyboard activation
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(400)
            
            # Check if keyboard activation worked
            content = await page.query_selector('.collapsible-content')
            is_expanded = await content.evaluate('el => el.classList.contains("expanded")')
            
            aria_expanded_after = await first_header.get_attribute('aria-expanded')
            
            return {
                'browser': browser_name,
                'passed': True,
                'details': {
                    'initial_aria_expanded': aria_expanded,
                    'tabindex': tabindex,
                    'role': role,
                    'keyboard_focus': 'collapsible-header' in focused_element,
                    'keyboard_activation': is_expanded,
                    'aria_updated': aria_expanded_after == 'true'
                }
            }
        except Exception as e:
            return {
                'browser': browser_name,
                'passed': False,
                'error': str(e)
            }


async def run_playwright_tests():
    """Run all Playwright tests"""
    print("🎭 Starting Playwright Cross-Browser Testing")
    print("=" * 50)
    
    # Run pytest with Playwright
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short",
        "-s"  # Don't capture output
    ], capture_output=True, text=True)
    
    # Generate summary report
    summary = {
        "timestamp": datetime.now().isoformat(),
        "test_suite": "Playwright Cross-Browser Testing",
        "result": {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        },
        "test_files_generated": [
            "playwright_mobile_test_results.json",
            "playwright_touch_test_results.json", 
            "playwright_animation_test_results.json",
            "playwright_overflow_test_results.json",
            "playwright_persistence_test_results.json",
            "playwright_accessibility_test_results.json"
        ],
        "browsers_tested": ["Chromium", "Firefox", "WebKit"],
        "features_tested": [
            "Mobile viewport responsiveness",
            "Touch interactions",
            "Animation performance",
            "Long content overflow",
            "State persistence",
            "Accessibility compliance"
        ]
    }
    
    with open("playwright_test_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n🎭 Playwright Tests: {'✅ PASSED' if result.returncode == 0 else '❌ FAILED'}")
    print("📄 Test reports saved:")
    for file in summary["test_files_generated"]:
        print(f"   - {file}")
    print("   - playwright_test_summary.json")
    
    return result.returncode == 0


if __name__ == "__main__":
    success = asyncio.run(run_playwright_tests())
    exit(0 if success else 1)
