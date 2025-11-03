"""
Base Tool and Tool Registry
Foundation for all tools in the system including MCP tools

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """Base class for all tools"""

    def __init__(self, tool_name: str, description: str, config: Dict[str, Any] = None):
        self.tool_name = tool_name
        self.description = description
        self.config = config or {}
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool"""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary"""
        return {
            'tool_name': self.tool_name,
            'description': self.description,
            'config': self.config,
            'schema': self.get_schema(),
            'metadata': self.metadata
        }
