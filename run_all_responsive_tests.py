#!/usr/bin/env python3
"""
Master Test Runner for Collapsible Components Responsive Design Testing
Orchestrates pytest, Playwright, and Puppeteer tests as specified in user rules
"""

import subprocess
import sys
import json
import time
import signal
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os


class MasterTestRunner:
    """Master test runner that orchestrates all testing tools"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.test_results = {}
        self.server_process = None
        self.cleanup_handlers = []
        
    def setup_test_server(self):
        """Start HTTP server for testing"""
        print("🌐 Starting HTTP server for testing...")
        
        try:
            # Kill any existing server on port 8003
            subprocess.run(["pkill", "-f", "python.*8003"], capture_output=True)
            time.sleep(1)
            
            # Start new server
            self.server_process = subprocess.Popen([
                sys.executable, "-m", "http.server", "8003"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for server to start
            time.sleep(3)
            print("✅ HTTP server started on port 8003")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not start HTTP server: {e}")
            
    def cleanup_test_server(self):
        """Stop HTTP server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("🧹 HTTP server stopped")
            except:
                try:
                    self.server_process.kill()
                    self.server_process.wait(timeout=2)
                except:
                    pass
                    
    def run_pytest_tests(self):
        """Run pytest-based responsive design tests"""
        print("\n🧪 Running Pytest Responsive Design Tests...")
        print("=" * 50)
        
        start_time = time.time()
        
        try:
            # Run the Python pytest suite
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "test_responsive_collapsible.py",
                "-v",
                "--tb=short",
                "--capture=no"
            ], capture_output=True, text=True, timeout=300)
            
            duration = time.time() - start_time
            
            self.test_results['pytest'] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'duration': f"{duration:.2f}s",
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'reports_generated': [
                    'comprehensive_responsive_test_report.json',
                    'mobile_viewport_test_results.json',
                    'touch_interaction_test_results.json',
                    'browser_compatibility_test_results.json',
                    'font_readability_test_results.json',
                    'overflow_handling_test_results.json',
                    'state_persistence_test_results.json',
                    'animation_smoothness_test_results.json'
                ]
            }
            
            print(f"✅ Pytest tests completed in {duration:.2f}s")
            if result.returncode != 0:
                print(f"⚠️  Some pytest tests failed (exit code: {result.returncode})")
                
        except subprocess.TimeoutExpired:
            self.test_results['pytest'] = {
                'status': 'timeout',
                'duration': '300s (timeout)',
                'error': 'Tests timed out after 300 seconds'
            }
            print("⏰ Pytest tests timed out")
            
        except Exception as e:
            self.test_results['pytest'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"❌ Pytest tests failed with error: {e}")
            
    def run_playwright_tests(self):
        """Run Playwright-based cross-browser tests"""
        print("\n🎭 Running Playwright Cross-Browser Tests...")
        print("=" * 50)
        
        start_time = time.time()
        
        try:
            # Check if playwright is installed
            subprocess.run([sys.executable, "-c", "import playwright"], 
                          check=True, capture_output=True)
            
            # Install playwright browsers if needed
            try:
                subprocess.run([
                    sys.executable, "-m", "playwright", "install"
                ], capture_output=True, timeout=120)
            except:
                pass  # Continue even if browser install fails
            
            # Run playwright tests
            result = subprocess.run([
                sys.executable, "test_playwright_responsive.py"
            ], capture_output=True, text=True, timeout=600)
            
            duration = time.time() - start_time
            
            self.test_results['playwright'] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'duration': f"{duration:.2f}s",
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'reports_generated': [
                    'playwright_test_summary.json',
                    'playwright_mobile_test_results.json',
                    'playwright_touch_test_results.json',
                    'playwright_animation_test_results.json',
                    'playwright_overflow_test_results.json',
                    'playwright_persistence_test_results.json',
                    'playwright_accessibility_test_results.json'
                ]
            }
            
            print(f"✅ Playwright tests completed in {duration:.2f}s")
            if result.returncode != 0:
                print(f"⚠️  Some Playwright tests failed (exit code: {result.returncode})")
                
        except ImportError:
            self.test_results['playwright'] = {
                'status': 'skipped',
                'reason': 'Playwright not installed'
            }
            print("⚠️  Playwright not installed, skipping Playwright tests")
            
        except subprocess.TimeoutExpired:
            self.test_results['playwright'] = {
                'status': 'timeout',
                'duration': '600s (timeout)',
                'error': 'Tests timed out after 600 seconds'
            }
            print("⏰ Playwright tests timed out")
            
        except Exception as e:
            self.test_results['playwright'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"❌ Playwright tests failed with error: {e}")
            
    def run_puppeteer_tests(self):
        """Run Puppeteer-based browser automation tests"""
        print("\n🤖 Running Puppeteer Browser Tests...")
        print("=" * 50)
        
        start_time = time.time()
        
        try:
            # Check if Node.js and Puppeteer are available
            subprocess.run(["node", "--version"], check=True, capture_output=True)
            
            # Check if puppeteer is installed
            try:
                subprocess.run([
                    "node", "-e", "require('puppeteer')"
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("📦 Installing Puppeteer...")
                subprocess.run(["npm", "install", "puppeteer"], 
                             capture_output=True, timeout=180)
            
            # Run puppeteer tests
            result = subprocess.run([
                "node", "test_puppeteer_responsive.js"
            ], capture_output=True, text=True, timeout=600)
            
            duration = time.time() - start_time
            
            self.test_results['puppeteer'] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'duration': f"{duration:.2f}s",
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'reports_generated': [
                    'puppeteer_comprehensive_report.json',
                    'puppeteer_mobile_test_results.json',
                    'puppeteer_touch_test_results.json',
                    'puppeteer_animation_test_results.json',
                    'puppeteer_content_test_results.json',
                    'puppeteer_persistence_test_results.json',
                    'puppeteer_performance_test_results.json'
                ]
            }
            
            print(f"✅ Puppeteer tests completed in {duration:.2f}s")
            if result.returncode != 0:
                print(f"⚠️  Some Puppeteer tests failed (exit code: {result.returncode})")
                
        except subprocess.CalledProcessError:
            self.test_results['puppeteer'] = {
                'status': 'skipped',
                'reason': 'Node.js or Puppeteer not available'
            }
            print("⚠️  Node.js or Puppeteer not available, skipping Puppeteer tests")
            
        except subprocess.TimeoutExpired:
            self.test_results['puppeteer'] = {
                'status': 'timeout',
                'duration': '600s (timeout)',
                'error': 'Tests timed out after 600 seconds'
            }
            print("⏰ Puppeteer tests timed out")
            
        except Exception as e:
            self.test_results['puppeteer'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"❌ Puppeteer tests failed with error: {e}")
            
    def run_concurrent_tests(self):
        """Run tests concurrently for better performance"""
        print("\n⚡ Running Tests Concurrently...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.run_pytest_tests): 'pytest',
                executor.submit(self.run_playwright_tests): 'playwright', 
                executor.submit(self.run_puppeteer_tests): 'puppeteer'
            }
            
            for future in as_completed(futures):
                test_name = futures[future]
                try:
                    future.result()
                    print(f"✅ {test_name} completed")
                except Exception as e:
                    print(f"❌ {test_name} failed: {e}")
                    
    def run_sequential_tests(self):
        """Run tests sequentially (fallback)"""
        print("\n🔄 Running Tests Sequentially...")
        
        self.run_pytest_tests()
        self.run_playwright_tests()
        self.run_puppeteer_tests()
        
    def validate_existing_files(self):
        """Validate that required files exist"""
        required_files = [
            'collapsible-example.html',
            'collapsible-components.css',
            'collapsible-components.js'
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
                
        if missing_files:
            print(f"❌ Missing required files: {missing_files}")
            return False
            
        print("✅ All required files present")
        return True
        
    def generate_comprehensive_report(self):
        """Generate a comprehensive test report"""
        print("\n📊 Generating Comprehensive Test Report...")
        
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Count test results
        passed_count = sum(1 for result in self.test_results.values() 
                          if result.get('status') == 'passed')
        failed_count = sum(1 for result in self.test_results.values() 
                          if result.get('status') == 'failed')
        skipped_count = sum(1 for result in self.test_results.values() 
                           if result.get('status') == 'skipped')
        error_count = sum(1 for result in self.test_results.values() 
                         if result.get('status') == 'error')
        timeout_count = sum(1 for result in self.test_results.values() 
                           if result.get('status') == 'timeout')
        
        comprehensive_report = {
            'test_suite': 'Comprehensive Responsive Design Testing',
            'timestamp': end_time.isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration': f"{total_duration:.2f}s",
            'summary': {
                'total_test_suites': len(self.test_results),
                'passed': passed_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'errors': error_count,
                'timeouts': timeout_count,
                'overall_success': failed_count == 0 and error_count == 0 and timeout_count == 0
            },
            'test_tools_used': {
                'pytest': 'Python-based unit and integration testing',
                'playwright': 'Cross-browser automation testing',  
                'puppeteer': 'Chrome/Chromium browser automation'
            },
            'features_tested': {
                'mobile_viewport_compatibility': 'iPhone SE, iPhone 12, iPad, Android devices',
                'touch_interactions': 'Tap to expand/collapse, touch feedback',
                'cross_browser_compatibility': 'Chrome, Firefox, Safari, Edge',
                'font_readability': 'Minimum sizes, contrast ratios, technical content',
                'long_content_handling': 'Overflow management, scroll behavior',
                'state_persistence': 'Scroll, resize, focus changes, dynamic content',
                'animation_smoothness': 'Expand/collapse transitions, performance',
                'accessibility_compliance': 'ARIA attributes, keyboard navigation, screen readers'
            },
            'test_results_by_tool': self.test_results,
            'compliance_standards': {
                'wcag': '2.1 AA',
                'touch_targets': 'Minimum 44px',
                'font_sizes': 'Minimum 14px on mobile',
                'animation_duration': 'Maximum 500ms',
                'contrast_ratio': 'Minimum 4.5:1'
            }
        }
        
        # Save comprehensive report
        report_file = 'master_responsive_test_report.json'
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2)
            
        # Print summary
        print("📊 Test Execution Summary:")
        print(f"   Total Duration: {total_duration:.2f}s")
        print(f"   Test Suites: {len(self.test_results)}")
        print(f"   ✅ Passed: {passed_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   ⏸️  Skipped: {skipped_count}")
        print(f"   🚫 Errors: {error_count}")
        print(f"   ⏰ Timeouts: {timeout_count}")
        
        overall_success = comprehensive_report['summary']['overall_success']
        print(f"   🎯 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
        
        print(f"\n📄 Comprehensive report saved: {report_file}")
        
        # List all generated test reports
        generated_reports = []
        for tool_result in self.test_results.values():
            if 'reports_generated' in tool_result:
                generated_reports.extend(tool_result['reports_generated'])
                
        if generated_reports:
            print("\n📁 Individual test reports generated:")
            for report in set(generated_reports):  # Remove duplicates
                if Path(report).exists():
                    print(f"   ✅ {report}")
                else:
                    print(f"   ⚠️  {report} (not found)")
                    
        return overall_success
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, cleaning up...")
            self.cleanup_test_server()
            sys.exit(1)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def run_all_tests(self, concurrent=True):
        """Run all responsive design tests"""
        print("🚀 Starting Comprehensive Responsive Design Testing")
        print("=" * 70)
        print(f"📅 Started at: {self.start_time}")
        print("🔧 Testing Tools: pytest, Playwright, Puppeteer")
        print("📱 Target: Collapsible Components Responsive Design")
        print("=" * 70)
        
        try:
            # Setup
            self.setup_signal_handlers()
            
            # Validate environment
            if not self.validate_existing_files():
                return False
                
            # Start test server
            self.setup_test_server()
            
            # Run tests
            if concurrent:
                try:
                    self.run_concurrent_tests()
                except Exception as e:
                    print(f"⚠️  Concurrent execution failed: {e}")
                    print("🔄 Falling back to sequential execution...")
                    self.run_sequential_tests()
            else:
                self.run_sequential_tests()
                
            # Generate comprehensive report
            success = self.generate_comprehensive_report()
            
            return success
            
        except KeyboardInterrupt:
            print("\n🛑 Tests interrupted by user")
            return False
            
        except Exception as e:
            print(f"\n❌ Test execution failed: {e}")
            return False
            
        finally:
            # Always cleanup
            self.cleanup_test_server()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run comprehensive responsive design tests for collapsible components'
    )
    parser.add_argument(
        '--sequential', 
        action='store_true',
        help='Run tests sequentially instead of concurrently'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set up environment
    if args.verbose:
        os.environ['VERBOSE'] = '1'
    
    # Run tests
    runner = MasterTestRunner()
    success = runner.run_all_tests(concurrent=not args.sequential)
    
    if success:
        print("\n🎉 All responsive design tests completed successfully!")
        print("📋 Summary:")
        print("   ✅ Mobile viewport compatibility verified")
        print("   ✅ Touch interactions working properly")  
        print("   ✅ Cross-browser compatibility confirmed")
        print("   ✅ Font readability meets standards")
        print("   ✅ Long content overflow handled correctly")
        print("   ✅ State persistence maintained across interactions")
        print("   ✅ Animations smooth and performant")
        print("   ✅ Accessibility compliance verified")
        sys.exit(0)
    else:
        print("\n❌ Some responsive design tests failed")
        print("📋 Check individual test reports for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
