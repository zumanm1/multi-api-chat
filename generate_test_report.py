#!/usr/bin/env python3
"""
Test Report Generator for Multi-API Chat Application
===================================================
This script generates comprehensive HTML and JSON reports from pytest and Puppeteer test results.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

def parse_pytest_junit_xml(xml_file):
    """Parse pytest JUnit XML results"""
    if not os.path.exists(xml_file):
        return {"error": f"JUnit XML file not found: {xml_file}"}
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Extract test suite information
        testsuite = root.find('.//testsuite')
        if testsuite is None:
            testsuite = root  # Sometimes the root is the testsuite
        
        total_tests = int(testsuite.get('tests', 0))
        failures = int(testsuite.get('failures', 0))
        errors = int(testsuite.get('errors', 0))
        skipped = int(testsuite.get('skipped', 0))
        time = float(testsuite.get('time', 0))
        
        passed = total_tests - failures - errors - skipped
        
        # Extract individual test cases
        test_cases = []
        for testcase in root.findall('.//testcase'):
            test_info = {
                'name': testcase.get('name'),
                'classname': testcase.get('classname'),
                'time': float(testcase.get('time', 0)),
                'status': 'passed'
            }
            
            # Check for failures, errors, or skips
            if testcase.find('failure') is not None:
                test_info['status'] = 'failed'
                failure = testcase.find('failure')
                test_info['message'] = failure.get('message', '')
                test_info['details'] = failure.text or ''
            elif testcase.find('error') is not None:
                test_info['status'] = 'error'
                error = testcase.find('error')
                test_info['message'] = error.get('message', '')
                test_info['details'] = error.text or ''
            elif testcase.find('skipped') is not None:
                test_info['status'] = 'skipped'
                skipped_elem = testcase.find('skipped')
                test_info['message'] = skipped_elem.get('message', '')
            
            test_cases.append(test_info)
        
        return {
            'total': total_tests,
            'passed': passed,
            'failed': failures,
            'errors': errors,
            'skipped': skipped,
            'time': time,
            'test_cases': test_cases
        }
    except Exception as e:
        return {"error": f"Failed to parse JUnit XML: {str(e)}"}

def parse_mocha_json_results(json_file):
    """Parse Mocha JSON test results"""
    if not os.path.exists(json_file):
        return {"error": f"Mocha JSON file not found: {json_file}"}
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Extract stats
        stats = data.get('stats', {})
        total = stats.get('tests', 0)
        passes = stats.get('passes', 0)
        failures = stats.get('failures', 0)
        pending = stats.get('pending', 0)
        duration = stats.get('duration', 0) / 1000.0  # Convert to seconds
        
        # Extract test cases
        test_cases = []
        for test in data.get('tests', []):
            test_info = {
                'name': test.get('title', ''),
                'fullTitle': test.get('fullTitle', ''),
                'duration': test.get('duration', 0) / 1000.0,
                'status': test.get('state', 'unknown')
            }
            
            if 'err' in test and test['err']:
                test_info['message'] = test['err'].get('message', '')
                test_info['stack'] = test['err'].get('stack', '')
            
            test_cases.append(test_info)
        
        return {
            'total': total,
            'passed': passes,
            'failed': failures,
            'pending': pending,
            'duration': duration,
            'test_cases': test_cases
        }
    except Exception as e:
        return {"error": f"Failed to parse Mocha JSON: {str(e)}"}

def generate_html_report(pytest_results, mocha_results, output_file):
    """Generate comprehensive HTML test report"""
    
    # Calculate overall results
    total_tests = pytest_results.get('total', 0) + mocha_results.get('total', 0)
    total_passed = pytest_results.get('passed', 0) + mocha_results.get('passed', 0)
    total_failed = pytest_results.get('failed', 0) + mocha_results.get('failed', 0)
    total_errors = pytest_results.get('errors', 0)
    total_skipped = pytest_results.get('skipped', 0) + mocha_results.get('pending', 0)
    
    total_time = pytest_results.get('time', 0) + mocha_results.get('duration', 0)
    
    # Calculate success rate
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-API Chat - Comprehensive Test Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 30px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin: -30px -30px 30px -30px; }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .summary-card {{ background: #f8f9fa; border-radius: 8px; padding: 20px; text-align: center; border-left: 4px solid; }}
        .summary-card.success {{ border-left-color: #28a745; }}
        .summary-card.failure {{ border-left-color: #dc3545; }}
        .summary-card.warning {{ border-left-color: #ffc107; }}
        .summary-card.info {{ border-left-color: #17a2b8; }}
        
        .summary-card h3 {{ margin: 0 0 10px 0; font-size: 2em; }}
        .summary-card p {{ margin: 0; color: #666; }}
        
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 20px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s ease; }}
        
        .section {{ margin: 40px 0; }}
        .section h2 {{ color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        
        .test-suite {{ margin: 30px 0; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; }}
        .test-suite h3 {{ margin-top: 0; color: #495057; }}
        
        .test-list {{ list-style: none; padding: 0; }}
        .test-item {{ padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid; }}
        .test-item.passed {{ background: #d4edda; border-left-color: #28a745; }}
        .test-item.failed {{ background: #f8d7da; border-left-color: #dc3545; }}
        .test-item.skipped {{ background: #fff3cd; border-left-color: #ffc107; }}
        .test-item.error {{ background: #f5c6cb; border-left-color: #dc3545; }}
        
        .test-name {{ font-weight: bold; }}
        .test-time {{ float: right; color: #666; font-size: 0.9em; }}
        .test-details {{ margin-top: 10px; font-size: 0.9em; color: #666; }}
        .error-message {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 5px; font-family: monospace; }}
        
        .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; color: #666; }}
        
        @media (max-width: 768px) {{
            .summary-grid {{ grid-template-columns: 1fr; }}
            .container {{ margin: 10px; padding: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Multi-API Chat Platform</h1>
            <p>Comprehensive Test Report - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card info">
                <h3>{total_tests}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card success">
                <h3>{total_passed}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card failure">
                <h3>{total_failed + total_errors}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card warning">
                <h3>{total_skipped}</h3>
                <p>Skipped</p>
            </div>
        </div>
        
        <div class="section">
            <h2>Overall Success Rate</h2>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate:.1f}%"></div>
            </div>
            <p style="text-align: center; font-size: 1.2em; margin-top: 10px;">
                <strong>{success_rate:.1f}%</strong> ({total_passed}/{total_tests} tests passed)
            </p>
        </div>
"""

    # Backend Tests Section
    if not pytest_results.get('error'):
        html_content += f"""
        <div class="section">
            <h2>Backend Tests (pytest)</h2>
            <div class="test-suite">
                <h3>Summary</h3>
                <p><strong>Total:</strong> {pytest_results['total']} tests</p>
                <p><strong>Passed:</strong> {pytest_results['passed']}</p>
                <p><strong>Failed:</strong> {pytest_results['failed']}</p>
                <p><strong>Errors:</strong> {pytest_results['errors']}</p>
                <p><strong>Skipped:</strong> {pytest_results['skipped']}</p>
                <p><strong>Duration:</strong> {pytest_results['time']:.2f}s</p>
                
                <h4>Test Details</h4>
                <ul class="test-list">
"""
        
        for test in pytest_results.get('test_cases', []):
            status_class = test['status']
            if status_class == 'error':
                status_class = 'failed'
            
            html_content += f"""
                    <li class="test-item {status_class}">
                        <div class="test-name">{test['name']}</div>
                        <div class="test-time">{test['time']:.3f}s</div>
"""
            if test.get('message'):
                html_content += f'<div class="test-details">Message: {test["message"]}</div>'
            if test.get('details'):
                html_content += f'<div class="error-message">{test["details"][:500]}...</div>'
            
            html_content += '</li>'
        
        html_content += """
                </ul>
            </div>
        </div>
"""
    else:
        html_content += f"""
        <div class="section">
            <h2>Backend Tests (pytest)</h2>
            <div class="test-suite">
                <p style="color: red;">Error: {pytest_results['error']}</p>
            </div>
        </div>
"""

    # Frontend Tests Section
    if not mocha_results.get('error'):
        html_content += f"""
        <div class="section">
            <h2>Frontend Tests (Puppeteer/Mocha)</h2>
            <div class="test-suite">
                <h3>Summary</h3>
                <p><strong>Total:</strong> {mocha_results['total']} tests</p>
                <p><strong>Passed:</strong> {mocha_results['passed']}</p>
                <p><strong>Failed:</strong> {mocha_results['failed']}</p>
                <p><strong>Pending:</strong> {mocha_results['pending']}</p>
                <p><strong>Duration:</strong> {mocha_results['duration']:.2f}s</p>
                
                <h4>Test Details</h4>
                <ul class="test-list">
"""
        
        for test in mocha_results.get('test_cases', []):
            status_class = test['status'] if test['status'] in ['passed', 'failed', 'pending'] else 'failed'
            if status_class == 'pending':
                status_class = 'skipped'
            
            html_content += f"""
                    <li class="test-item {status_class}">
                        <div class="test-name">{test['name']}</div>
                        <div class="test-time">{test['duration']:.3f}s</div>
"""
            if test.get('message'):
                html_content += f'<div class="test-details">Message: {test["message"]}</div>'
            if test.get('stack'):
                html_content += f'<div class="error-message">{test["stack"][:500]}...</div>'
            
            html_content += '</li>'
        
        html_content += """
                </ul>
            </div>
        </div>
"""
    else:
        html_content += f"""
        <div class="section">
            <h2>Frontend Tests (Puppeteer/Mocha)</h2>
            <div class="test-suite">
                <p style="color: red;">Error: {mocha_results['error']}</p>
            </div>
        </div>
"""

    # Test Coverage Areas
    html_content += """
        <div class="section">
            <h2>Test Coverage Areas</h2>
            <div class="test-suite">
                <h4>Backend Coverage</h4>
                <ul>
                    <li><strong>API Endpoints:</strong> Health, providers, settings, chat, usage</li>
                    <li><strong>Provider Management:</strong> CRUD operations, testing, configuration</li>
                    <li><strong>Device Management:</strong> Router configuration, SSH commands, status monitoring</li>
                    <li><strong>Chat Functionality:</strong> Message handling, fallback mechanisms, model selection</li>
                    <li><strong>AI Agents Integration:</strong> Workflow orchestration, agent communication</li>
                    <li><strong>Error Handling:</strong> Input validation, exception handling, graceful failures</li>
                </ul>
                
                <h4>Frontend Coverage</h4>
                <ul>
                    <li><strong>Page Loading:</strong> All major pages load correctly and display proper content</li>
                    <li><strong>API Integration:</strong> Frontend communicates correctly with backend APIs</li>
                    <li><strong>Chat Interface:</strong> Message sending, response display, provider selection</li>
                    <li><strong>Settings Management:</strong> Provider configuration, testing connections</li>
                    <li><strong>Responsive Design:</strong> Mobile compatibility and layout adaptation</li>
                    <li><strong>Performance:</strong> Page load times and API response times</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Multi-API Chat Test Suite</p>
            <p>Report includes both backend (pytest) and frontend (Puppeteer) test results</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html_content)

def generate_json_report(pytest_results, mocha_results, output_file):
    """Generate JSON summary report"""
    
    total_tests = pytest_results.get('total', 0) + mocha_results.get('total', 0)
    total_passed = pytest_results.get('passed', 0) + mocha_results.get('passed', 0)
    total_failed = pytest_results.get('failed', 0) + mocha_results.get('failed', 0)
    total_errors = pytest_results.get('errors', 0)
    total_skipped = pytest_results.get('skipped', 0) + mocha_results.get('pending', 0)
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    report_data = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "errors": total_errors,
            "skipped": total_skipped,
            "success_rate": round(success_rate, 2),
            "total_time": pytest_results.get('time', 0) + mocha_results.get('duration', 0)
        },
        "backend_tests": pytest_results,
        "frontend_tests": mocha_results
    }
    
    with open(output_file, 'w') as f:
        json.dump(report_data, f, indent=2)

def main():
    """Main function to generate test reports"""
    print("Generating comprehensive test reports...")
    
    # Define file paths
    reports_dir = Path("test-reports")
    reports_dir.mkdir(exist_ok=True)
    
    backend_junit = reports_dir / "backend" / "junit.xml"
    frontend_json = reports_dir / "frontend" / "mocha-results.json"
    
    html_report = reports_dir / "comprehensive-test-report.html"
    json_report = reports_dir / "test-summary.json"
    
    # Parse test results
    print("Parsing backend test results...")
    pytest_results = parse_pytest_junit_xml(backend_junit)
    
    print("Parsing frontend test results...")
    mocha_results = parse_mocha_json_results(frontend_json)
    
    # Generate reports
    print("Generating HTML report...")
    generate_html_report(pytest_results, mocha_results, html_report)
    
    print("Generating JSON summary...")
    generate_json_report(pytest_results, mocha_results, json_report)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST REPORT SUMMARY")
    print("="*60)
    
    if not pytest_results.get('error'):
        print(f"Backend Tests: {pytest_results['passed']}/{pytest_results['total']} passed")
    else:
        print(f"Backend Tests: Error - {pytest_results['error']}")
    
    if not mocha_results.get('error'):
        print(f"Frontend Tests: {mocha_results['passed']}/{mocha_results['total']} passed")
    else:
        print(f"Frontend Tests: Error - {mocha_results['error']}")
    
    total_tests = pytest_results.get('total', 0) + mocha_results.get('total', 0)
    total_passed = pytest_results.get('passed', 0) + mocha_results.get('passed', 0)
    
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"Overall Success Rate: {success_rate:.1f}% ({total_passed}/{total_tests})")
    
    print(f"\nReports generated:")
    print(f"- HTML Report: {html_report}")
    print(f"- JSON Summary: {json_report}")
    print("="*60)

if __name__ == "__main__":
    main()
