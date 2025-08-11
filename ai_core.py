"""
AI Core Module - Minimal AI functionality without circular imports
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Simple dependency checker without complex imports
def check_ai_packages() -> Dict[str, Any]:
    """Check if AI packages can be imported"""
    result = {
        "packages_available": {},
        "all_available": False,
        "timestamp": datetime.now().isoformat()
    }
    
    # Test core AI packages
    packages_to_test = [
        ("crewai", "CrewAI framework"),
        ("langchain", "LangChain framework"), 
        ("langgraph", "LangGraph for workflows"),
        ("langchain_openai", "LangChain OpenAI integration")
    ]
    
    available_count = 0
    for package_name, description in packages_to_test:
        try:
            __import__(package_name)
            result["packages_available"][package_name] = {
                "available": True,
                "description": description,
                "error": None
            }
            available_count += 1
            logger.info(f"✓ {package_name} is available")
        except ImportError as e:
            result["packages_available"][package_name] = {
                "available": False,
                "description": description,
                "error": str(e)
            }
            logger.warning(f"✗ {package_name} not available: {e}")
    
    result["all_available"] = available_count == len(packages_to_test)
    result["available_count"] = available_count
    result["total_count"] = len(packages_to_test)
    
    return result

def get_ai_status() -> Dict[str, Any]:
    """Get AI system status without complex dependencies"""
    package_check = check_ai_packages()
    
    return {
        "ai_available": package_check["all_available"],
        "package_status": package_check,
        "features_enabled": {
            "dependency_check": True,
            "basic_ai": package_check["all_available"],
            "advanced_workflows": False,  # Disabled to avoid circular imports
            "full_integration": False     # Will be enabled when circular imports are fixed
        },
        "status_message": _get_status_message(package_check),
        "timestamp": datetime.now().isoformat()
    }

def _get_status_message(package_check: Dict[str, Any]) -> str:
    """Generate human-readable status message"""
    if package_check["all_available"]:
        return "Core AI packages are available. Full integration temporarily disabled due to circular imports."
    elif package_check["available_count"] > 0:
        return f"Partial AI support: {package_check['available_count']}/{package_check['total_count']} packages available"
    else:
        return "No AI packages available. Install with: pip install -r requirements-ai-agents.txt"

def get_installation_command() -> str:
    """Get command to install AI dependencies"""
    return "pip install -r requirements-ai-agents.txt"

# Fallback functions for when full AI integration isn't available
def fallback_ai_chat(message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Fallback AI chat function"""
    return {
        "success": False,
        "response": "AI chat functionality is temporarily disabled due to integration issues. Please use the regular chat providers instead.",
        "fallback": True,
        "timestamp": datetime.now().isoformat()
    }

def fallback_ai_analytics(message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Fallback AI analytics function"""
    return {
        "success": False,
        "response": "AI analytics functionality is temporarily disabled. Basic analytics are available through the usage endpoints.",
        "fallback": True,
        "timestamp": datetime.now().isoformat()
    }

def fallback_ai_operation(operation_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """General fallback for AI operations"""
    return {
        "success": False,
        "response": f"AI {operation_type} functionality is temporarily disabled due to integration issues.",
        "fallback": True,
        "operation_type": operation_type,
        "timestamp": datetime.now().isoformat()
    }

# Module initialization
_ai_status = None

def initialize_ai_core():
    """Initialize AI core module"""
    global _ai_status
    logger.info("Initializing AI core module...")
    _ai_status = get_ai_status()
    
    if _ai_status["ai_available"]:
        logger.info("✓ AI core packages are available")
    else:
        logger.warning("✗ Some AI packages are missing")
    
    return _ai_status

def get_cached_ai_status() -> Dict[str, Any]:
    """Get cached AI status or initialize if needed"""
    global _ai_status
    if _ai_status is None:
        _ai_status = initialize_ai_core()
    return _ai_status

# Simple health check
def ai_health_check() -> Dict[str, Any]:
    """Simple AI health check without complex dependencies"""
    status = get_cached_ai_status()
    return {
        "healthy": True,
        "ai_packages_available": status["ai_available"],
        "features_working": ["dependency_check", "health_check"],
        "features_disabled": ["advanced_workflows", "full_integration"],
        "reason_disabled": "Avoiding circular imports while core dependencies are being resolved"
    }
