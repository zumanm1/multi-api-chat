"""
AI Agents Package for Multi-API Chat Platform
Provides intelligent agent capabilities using CrewAI framework
"""

from .integration import (
    get_ai_integration,
    is_ai_enabled,
    process_ai_request,
    get_ai_status
)

from .configs.agents_config import AGENTS_CONFIG

__version__ = "1.0.0"
__author__ = "Multi-API Chat Platform"
__description__ = "AI Agent System using CrewAI"

# Export main interface functions
__all__ = [
    "get_ai_integration",
    "is_ai_enabled", 
    "process_ai_request",
    "get_ai_status",
    "AGENTS_CONFIG"
]
