#!/usr/bin/env python3
"""
AI Dependencies Check CLI Tool
Command line interface for checking and installing AI agent dependencies
"""

import sys
import argparse
import logging
from typing import Any

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_dependency_checker():
    """Load the dependency checker module"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "dependency_checker", 
            "ai_agents/utils/dependency_checker.py"
        )
        dependency_checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dependency_checker)
        return dependency_checker
    except Exception as e:
        print(f"Error loading dependency checker: {e}")
        print("Make sure ai_agents/utils/dependency_checker.py exists")
        sys.exit(1)

def cmd_check(args):
    """Check AI dependencies"""
    dc = load_dependency_checker()
    
    print("🔍 Checking AI Dependencies...")
    print("=" * 50)
    
    status = dc.check_ai_dependencies()
    
    # Basic status
    print(f"Total packages: {status['total_packages']}")
    print(f"Installed: {status['installed_count']}")
    print(f"Missing: {len(status['missing_packages'])}")
    print(f"Version issues: {len(status['outdated_packages'])}")
    
    # Color coding
    if status['all_installed']:
        print("✅ Status: ALL DEPENDENCIES SATISFIED")
    else:
        print("❌ Status: DEPENDENCIES NOT SATISFIED")
    
    print()
    
    # Missing packages
    if status['missing_packages']:
        print(f"📦 Missing Packages ({len(status['missing_packages'])}):")
        for pkg in status['missing_packages']:
            min_ver = f" (>={pkg['min_version']})" if pkg.get('min_version') != 'latest' else ""
            print(f"  • {pkg['package']}{min_ver}")
            if args.verbose:
                print(f"    {pkg['description']}")
        print()
    
    # Version issues
    if status['outdated_packages']:
        print(f"⚠️ Version Issues ({len(status['outdated_packages'])}):")
        for pkg in status['outdated_packages']:
            current = pkg['current_version']
            if pkg.get('issue') == 'version_too_high':
                required = f"<{pkg['max_allowed']}"
                issue = "too high"
            else:
                required = f">={pkg['min_required']}"
                issue = "too low"
            print(f"  • {pkg['package']} {current} (need {required}) - version {issue}")
        print()
    
    # Installed packages
    if status['installed_packages'] and args.verbose:
        print(f"✅ Installed Packages ({len(status['installed_packages'])}):")
        for pkg, version in status['installed_packages'].items():
            print(f"  • {pkg}: {version}")
        print()
    
    # Recommendations
    env_status = dc.validate_ai_environment()
    if env_status['recommendations']:
        print("💡 Recommendations:")
        for rec in env_status['recommendations']:
            print(f"  • {rec}")
        print()
    
    if not status['all_installed']:
        print("🚀 To install missing dependencies:")
        print("  python check_ai_deps.py install")
        print("  OR")
        print("  pip install -r requirements-ai-agents.txt")

def cmd_install(args):
    """Install AI dependencies"""
    dc = load_dependency_checker()
    
    if not args.yes:
        # Show what will be installed
        missing = dc.get_missing_dependencies()
        if not missing:
            print("✅ All dependencies are already installed!")
            return
        
        print("📦 The following packages will be installed:")
        for pkg in missing:
            min_ver = f" (>={pkg['min_version']})" if pkg.get('min_version') != 'latest' else ""
            print(f"  • {pkg['package']}{min_ver}")
        
        response = input("\nContinue with installation? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Installation cancelled.")
            return
    
    print("\n🚀 Installing AI dependencies...")
    print("This may take several minutes...")
    
    result = dc.install_ai_dependencies()
    
    if result['success']:
        print("✅ Installation completed successfully!")
        print("\n🔍 Checking dependencies after installation...")
        
        # Re-check dependencies
        status = dc.check_ai_dependencies()
        if status['all_installed']:
            print("✅ All dependencies are now satisfied!")
        else:
            remaining = len(status['missing_packages'])
            print(f"⚠️  {remaining} dependencies still missing. Check the output above for errors.")
    else:
        print(f"❌ Installation failed: {result['message']}")
        if args.verbose and result['error']:
            print(f"Error details: {result['error']}")
        if result['output']:
            print("Output:")
            print(result['output'])

def cmd_status(args):
    """Show detailed status"""
    dc = load_dependency_checker()
    
    print("📊 AI Dependencies Status Report")
    print("=" * 50)
    
    # Environment info
    env_status = dc.validate_ai_environment()
    print(f"Python version: {env_status['python_version']}")
    print(f"Requirements file: {'✅ Found' if env_status['requirements_file_exists'] else '❌ Missing'}")
    print(f"Environment ready: {'✅ Yes' if env_status['environment_ready'] else '❌ No'}")
    print()
    
    # Dependency details
    status = dc.check_ai_dependencies()
    print("📦 Package Details:")
    for pkg_name, details in status['details'].items():
        status_icon = "✅" if details['installed'] else "❌"
        version_info = f" ({details['version']})" if details['installed'] else ""
        req_info = " - meets requirements" if details.get('meets_requirements', True) else " - VERSION ISSUE"
        
        print(f"  {status_icon} {pkg_name}{version_info}{req_info}")
        if args.verbose:
            print(f"     {details['description']}")
    
    print()
    
    # Summary
    if status['all_installed']:
        print("🎉 Summary: All AI dependencies are properly installed!")
    else:
        missing_count = len(status['missing_packages'])
        issue_count = len(status['outdated_packages'])
        print(f"📋 Summary: {missing_count} missing, {issue_count} version issues")

def cmd_list(args):
    """List all AI dependencies"""
    dc = load_dependency_checker()
    
    print("📋 AI Dependencies List")
    print("=" * 50)
    
    # Get the AI_DEPENDENCIES dict from the module
    ai_deps = dc.AI_DEPENDENCIES
    
    for pkg_name, requirements in ai_deps.items():
        description = requirements.get('description', 'No description')
        min_ver = requirements.get('min_version', '')
        max_ver = requirements.get('max_version', '')
        
        version_req = []
        if min_ver:
            version_req.append(f">={min_ver}")
        if max_ver:
            version_req.append(f"<{max_ver}")
        
        version_info = f" ({', '.join(version_req)})" if version_req else ""
        
        print(f"📦 {pkg_name}{version_info}")
        if args.verbose or args.descriptions:
            print(f"   {description}")
        print()

def main():
    parser = argparse.ArgumentParser(
        description="AI Dependencies Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s check                    # Check dependency status
  %(prog)s check -v                 # Check with verbose output
  %(prog)s install                  # Install missing dependencies (with prompt)
  %(prog)s install -y               # Install without prompt
  %(prog)s status                   # Show detailed status report
  %(prog)s list                     # List all dependencies
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check AI dependencies status')
    check_parser.set_defaults(func=cmd_check)
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install missing AI dependencies')
    install_parser.add_argument('-y', '--yes', action='store_true',
                               help='Install without confirmation prompt')
    install_parser.set_defaults(func=cmd_install)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show detailed status report')
    status_parser.set_defaults(func=cmd_status)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all AI dependencies')
    list_parser.add_argument('-d', '--descriptions', action='store_true',
                            help='Show package descriptions')
    list_parser.set_defaults(func=cmd_list)
    
    args = parser.parse_args()
    
    if not args.command:
        # Default to check command
        args.command = 'check'
        args.func = cmd_check
    
    setup_logging(args.verbose)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
