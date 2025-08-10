"""
Simple replacement for crewai_tools to avoid import errors
This provides basic tool functionality without external dependencies
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for agent tools - simplified version"""
    
    def __init__(self):
        self.name: str = getattr(self, 'name', self.__class__.__name__)
        self.description: str = getattr(self, 'description', 'Base agent tool')
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def _run(self, *args, **kwargs) -> str:
        """Execute the tool - must be implemented by subclasses"""
        pass
    
    def run(self, *args, **kwargs) -> str:
        """Public interface to run the tool"""
        try:
            return self._run(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Tool {self.name} error: {str(e)}")
            return f"Tool error: {str(e)}"
    
    def __call__(self, *args, **kwargs) -> str:
        """Make the tool callable"""
        return self.run(*args, **kwargs)


def tool(func):
    """Simple decorator for tool functions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Tool function error: {str(e)}")
            return f"Tool error: {str(e)}"
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
