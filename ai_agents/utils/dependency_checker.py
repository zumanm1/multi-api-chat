"""
AI Agents Dependency Checker
Utility to check, validate, and install AI agent dependencies
"""

import logging
import subprocess
import sys
import importlib.util
import os
from typing import List, Dict, Tuple, Any
from pathlib import Path


logger = logging.getLogger(__name__)


# AI Dependencies defined in requirements-ai-agents.txt
AI_DEPENDENCIES = {
    # Core AI Agent Frameworks
    "crewai": {"min_version": "0.41.0", "import_name": "crewai", "description": "Main CrewAI framework"},
    "crewai-tools": {"min_version": "0.4.0", "import_name": "crewai_tools", "description": "CrewAI tools library"},
    "langgraph": {"min_version": "0.0.20", "import_name": "langgraph", "description": "LangGraph for agent workflow orchestration"},
    
    # LangChain Framework and Integrations
    "langchain": {"min_version": "0.1.0", "import_name": "langchain", "description": "LangChain framework (required by CrewAI)"},
    "langchain-openai": {"min_version": "0.0.5", "import_name": "langchain_openai", "description": "OpenAI integration for LangChain"},
    
    # Core Dependencies
    "pydantic": {"min_version": "2.0.0", "import_name": "pydantic", "description": "Data validation (required by CrewAI)"},
    "tiktoken": {"min_version": "0.5.0", "import_name": "tiktoken", "description": "Token counting for LLM interactions"},
    "aiohttp": {"min_version": "3.9.0", "import_name": "aiohttp", "description": "Async HTTP client for API calls"},
    
    # Vector Database and Numerical Operations
    "chromadb": {"min_version": "0.4.0", "import_name": "chromadb", "description": "Vector database for agent memory"},
    "numpy": {"max_version": "2.0.0", "import_name": "numpy", "description": "Numerical operations (pinned to avoid compatibility issues)"},
}


def check_package_installed(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """
    Check if a package is installed and get its version.
    
    Args:
        package_name: The package name as it appears in pip
        import_name: The name used to import the package (if different from package_name)
    
    Returns:
        Tuple of (is_installed, version_string)
    """
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        # Try to import the module
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            return False, ""
        
        # Try to get the version
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            return True, version
        except ImportError:
            # Module exists but can't be imported (might be broken installation)
            return False, ""
    
    except Exception as e:
        logger.debug(f"Error checking package {package_name}: {e}")
        return False, ""


def compare_versions(current_version: str, required_version: str, operator: str = ">=") -> bool:
    """
    Compare version strings.
    
    Args:
        current_version: Current installed version
        required_version: Required version
        operator: Comparison operator (">=", "<=", "==", ">", "<")
    
    Returns:
        True if version requirement is satisfied
    """
    if current_version == "unknown" or not current_version:
        return False
    
    try:
        # Try to import packaging, fall back to simple string comparison
        try:
            from packaging import version
            current = version.parse(current_version)
            required = version.parse(required_version)
            
            if operator == ">=":
                return current >= required
            elif operator == "<=":
                return current <= required
            elif operator == "==":
                return current == required
            elif operator == ">":
                return current > required
            elif operator == "<":
                return current < required
            else:
                logger.warning(f"Unsupported version operator: {operator}")
                return True
        
        except ImportError:
            # Fallback to simple string-based version comparison
            logger.debug("packaging library not available, using simple version comparison")
            return _simple_version_compare(current_version, required_version, operator)
    
    except Exception as e:
        logger.debug(f"Error comparing versions {current_version} {operator} {required_version}: {e}")
        # If we can't parse versions, assume it's okay
        return True


def _simple_version_compare(current: str, required: str, operator: str) -> bool:
    """
    Simple version comparison fallback when packaging library is not available.
    
    Args:
        current: Current version string
        required: Required version string
        operator: Comparison operator
    
    Returns:
        True if version requirement is satisfied
    """
    try:
        # Split version strings into components
        current_parts = [int(x) for x in current.split('.') if x.isdigit()]
        required_parts = [int(x) for x in required.split('.') if x.isdigit()]
        
        # Pad with zeros to make same length
        max_len = max(len(current_parts), len(required_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        required_parts.extend([0] * (max_len - len(required_parts)))
        
        # Compare
        if operator == ">=":
            return current_parts >= required_parts
        elif operator == "<=":
            return current_parts <= required_parts
        elif operator == "==":
            return current_parts == required_parts
        elif operator == ">":
            return current_parts > required_parts
        elif operator == "<":
            return current_parts < required_parts
        else:
            return True
    
    except Exception:
        # If simple comparison fails, assume it's okay
        return True


def check_ai_dependencies() -> Dict[str, Any]:
    """
    Check if all AI dependencies are installed and meet version requirements.
    
    Returns:
        Dictionary with dependency status information
    """
    results = {
        "all_installed": True,
        "missing_packages": [],
        "outdated_packages": [],
        "installed_packages": {},
        "total_packages": len(AI_DEPENDENCIES),
        "installed_count": 0,
        "details": {}
    }
    
    for package_name, requirements in AI_DEPENDENCIES.items():
        import_name = requirements.get("import_name", package_name)
        description = requirements.get("description", "")
        
        is_installed, version = check_package_installed(package_name, import_name)
        
        package_info = {
            "installed": is_installed,
            "version": version,
            "description": description,
            "meets_requirements": True
        }
        
        if is_installed:
            results["installed_count"] += 1
            results["installed_packages"][package_name] = version
            
            # Check version requirements
            if "min_version" in requirements:
                meets_min = compare_versions(version, requirements["min_version"], ">=")
                if not meets_min:
                    results["outdated_packages"].append({
                        "package": package_name,
                        "current_version": version,
                        "min_required": requirements["min_version"],
                        "description": description
                    })
                    package_info["meets_requirements"] = False
                    results["all_installed"] = False
            
            if "max_version" in requirements:
                meets_max = compare_versions(version, requirements["max_version"], "<")
                if not meets_max:
                    results["outdated_packages"].append({
                        "package": package_name,
                        "current_version": version,
                        "max_allowed": requirements["max_version"],
                        "description": description,
                        "issue": "version_too_high"
                    })
                    package_info["meets_requirements"] = False
                    results["all_installed"] = False
        else:
            results["missing_packages"].append({
                "package": package_name,
                "import_name": import_name,
                "description": description,
                "min_version": requirements.get("min_version", "latest"),
                "max_version": requirements.get("max_version")
            })
            results["all_installed"] = False
        
        results["details"][package_name] = package_info
    
    return results


def get_missing_dependencies() -> List[Dict[str, str]]:
    """
    Get a list of missing AI dependencies.
    
    Returns:
        List of missing dependencies with details
    """
    status = check_ai_dependencies()
    return status["missing_packages"]


def install_ai_dependencies(requirements_file: str = "requirements-ai-agents.txt") -> Dict[str, Any]:
    """
    Install AI dependencies using pip and the requirements file.
    
    Args:
        requirements_file: Path to the requirements file
    
    Returns:
        Dictionary with installation status and results
    """
    result = {
        "success": False,
        "message": "",
        "output": "",
        "error": ""
    }
    
    # Check if requirements file exists
    if not os.path.exists(requirements_file):
        result["message"] = f"Requirements file '{requirements_file}' not found"
        result["error"] = "Requirements file missing"
        logger.error(result["message"])
        return result
    
    try:
        # Run pip install command
        cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        result["output"] = process.stdout
        result["error"] = process.stderr
        
        if process.returncode == 0:
            result["success"] = True
            result["message"] = "AI dependencies installed successfully"
            logger.info(result["message"])
        else:
            result["message"] = f"Failed to install AI dependencies (exit code: {process.returncode})"
            logger.error(f"{result['message']}. Error: {process.stderr}")
    
    except subprocess.TimeoutExpired:
        result["message"] = "Installation timed out after 5 minutes"
        result["error"] = "Timeout"
        logger.error(result["message"])
    
    except Exception as e:
        result["message"] = f"Error during installation: {str(e)}"
        result["error"] = str(e)
        logger.error(result["message"])
    
    return result


def log_dependency_status(log_level: int = logging.INFO) -> None:
    """
    Log the current dependency status with detailed information.
    
    Args:
        log_level: Logging level to use
    """
    status = check_ai_dependencies()
    
    logger.log(log_level, "=== AI Agents Dependency Status ===")
    logger.log(log_level, f"Total packages: {status['total_packages']}")
    logger.log(log_level, f"Installed packages: {status['installed_count']}")
    logger.log(log_level, f"All dependencies satisfied: {status['all_installed']}")
    
    if status["missing_packages"]:
        logger.log(log_level, f"Missing packages ({len(status['missing_packages'])}):")
        for pkg in status["missing_packages"]:
            min_ver = f" (>={pkg['min_version']})" if pkg.get('min_version') != 'latest' else ""
            max_ver = f" (<{pkg['max_version']})" if pkg.get('max_version') else ""
            version_info = f"{min_ver}{max_ver}"
            logger.log(log_level, f"  - {pkg['package']}{version_info}: {pkg['description']}")
    
    if status["outdated_packages"]:
        logger.log(log_level, f"Version issues ({len(status['outdated_packages'])}):")
        for pkg in status["outdated_packages"]:
            if pkg.get("issue") == "version_too_high":
                logger.log(log_level, f"  - {pkg['package']} {pkg['current_version']} (max allowed: <{pkg['max_allowed']})")
            else:
                logger.log(log_level, f"  - {pkg['package']} {pkg['current_version']} (min required: >={pkg['min_required']})")
    
    if status["installed_packages"]:
        logger.log(log_level, f"Successfully installed packages ({len(status['installed_packages'])}):")
        for pkg, version in status["installed_packages"].items():
            logger.log(log_level, f"  - {pkg}: {version}")
    
    # Provide installation instructions if needed
    if not status["all_installed"]:
        logger.log(log_level, "")
        logger.log(log_level, "To install missing AI dependencies, run:")
        logger.log(log_level, "  pip install -r requirements-ai-agents.txt")
        logger.log(log_level, "")


def get_installation_command() -> str:
    """
    Get the pip command to install AI dependencies.
    
    Returns:
        The pip install command string
    """
    return "pip install -r requirements-ai-agents.txt"


def validate_ai_environment() -> Dict[str, Any]:
    """
    Comprehensive validation of the AI environment.
    
    Returns:
        Dictionary with validation results and recommendations
    """
    status = check_ai_dependencies()
    
    validation = {
        "environment_ready": status["all_installed"],
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "pip_available": True,
        "requirements_file_exists": os.path.exists("requirements-ai-agents.txt"),
        "recommendations": [],
        "dependency_status": status
    }
    
    # Check Python version (prefer 3.11 as per user rules)
    if sys.version_info < (3, 8):
        validation["recommendations"].append("Python 3.8+ is required for AI agents")
        validation["environment_ready"] = False
    elif sys.version_info.major == 3 and sys.version_info.minor != 11:
        validation["recommendations"].append("Python 3.11 is preferred for optimal compatibility")
    
    # Check pip availability
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        validation["pip_available"] = False
        validation["recommendations"].append("pip is required to install AI dependencies")
        validation["environment_ready"] = False
    
    # Check requirements file
    if not validation["requirements_file_exists"]:
        validation["recommendations"].append("requirements-ai-agents.txt file is missing")
        validation["environment_ready"] = False
    
    # Add recommendations based on dependency status
    if status["missing_packages"]:
        validation["recommendations"].append(f"Install {len(status['missing_packages'])} missing AI packages")
        validation["recommendations"].append("Run: pip install -r requirements-ai-agents.txt")
    
    if status["outdated_packages"]:
        validation["recommendations"].append(f"Update {len(status['outdated_packages'])} packages with version issues")
    
    return validation


# Testing function
def test_dependency_checker():
    """Test the dependency checker functionality"""
    print("=== AI Dependency Checker Test ===")
    
    # Test dependency checking
    status = check_ai_dependencies()
    print(f"All dependencies installed: {status['all_installed']}")
    print(f"Installed: {status['installed_count']}/{status['total_packages']}")
    
    # Test missing dependencies
    missing = get_missing_dependencies()
    print(f"Missing packages: {len(missing)}")
    
    # Test environment validation
    validation = validate_ai_environment()
    print(f"Environment ready: {validation['environment_ready']}")
    print(f"Python version: {validation['python_version']}")
    
    # Log status
    log_dependency_status()
    
    print("\nTest completed!")


if __name__ == "__main__":
    test_dependency_checker()
