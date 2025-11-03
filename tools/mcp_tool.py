"""
Base Tool and Tool Registry
Foundation for all tools in the system including MCP tools

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""
from typing import Dict, Any

import requests

from tools.base_tool import BaseTool


class MCPTool(BaseTool):
    """Tool that calls MCP server endpoints"""

    def __init__(self, tool_name: str, description: str, mcp_url: str,
                 tool_config: Dict[str, Any], config: Dict[str, Any] = None):
        super().__init__(tool_name, description, config)
        self.mcp_url = mcp_url
        self.tool_config = tool_config
        self.input_schema = tool_config.get('input_schema', {})

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute MCP tool via REST call"""
        try:
            # Prepare request payload
            payload = {
                'tool': self.tool_config.get('name'),
                'arguments': kwargs
            }

            # Make REST call to MCP server
            response = requests.post(
                f"{self.mcp_url}/execute",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'result': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'MCP call failed: {response.status_code}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'input_schema': self.input_schema
        }
