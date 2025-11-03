"""
Base Tool and Tool Registry
Foundation for all tools in the system including MCP tools

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import json
import os
import importlib
import requests
from typing import Dict, Any, List, Optional
from threading import Lock
from datetime import datetime

from tools.base_tool import BaseTool
from tools.mcp_tool import MCPTool


class ToolRegistry:
    """Singleton registry for tool management"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ToolRegistry, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._tools: Dict[str, BaseTool] = {}
        self._tool_configs: Dict[str, Dict[str, Any]] = {}
        self._config_dir = 'config/tools'
        self._mcp_config_dir = 'config/mcp'
        self._initialized = True
        self.load_tools()
    
    def load_tools(self) -> None:
        """Load tools from configuration directories"""
        self._tools.clear()
        self._tool_configs.clear()
        
        # Load regular tools
        if os.path.exists(self._config_dir):
            self._load_regular_tools()
        
        # Load MCP tools
        if os.path.exists(self._mcp_config_dir):
            self._load_mcp_tools()
    
    def _load_regular_tools(self) -> None:
        """Load regular (non-MCP) tools"""
        for filename in os.listdir(self._config_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self._config_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        config = json.load(f)
                    
                    # Check if tool is enabled
                    if not config.get('enabled', True):
                        continue  # Skip disabled tools

                    tool_name = config.get('name')
                    module_path = config.get('module')

                    if tool_name and module_path:
                        self._tool_configs[tool_name] = config

                        # Dynamically load tool class
                        try:
                            module_name, class_name = module_path.rsplit('.', 1)
                            module = importlib.import_module(module_name)
                            tool_class = getattr(module, class_name)

                            # Instantiate tool
                            tool = tool_class(
                                tool_name=tool_name,
                                description=config.get('description', ''),
                                config=config.get('config', {})
                            )

                            self._tools[tool_name] = tool
                        except Exception as e:
                            print(f"Error loading tool {tool_name}: {e}")

                except Exception as e:
                    print(f"Error reading tool config {filename}: {e}")

    def _load_mcp_tools(self) -> None:
        """Load MCP tools"""
        for filename in os.listdir(self._mcp_config_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self._mcp_config_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        config = json.load(f)

                    mcp_name = config.get('name')
                    mcp_url = config.get('mcp_url', 'http://localhost:8000')
                    tool_description = config.get('tool_description', {})

                    # Create MCP tools from the tool descriptions
                    for tool_config in tool_description.get('tools', []):
                        tool_name = f"{mcp_name}_{tool_config['name']}"

                        tool = MCPTool(
                            tool_name=tool_name,
                            description=tool_config.get('description', ''),
                            mcp_url=mcp_url,
                            tool_config=tool_config,
                            config=config
                        )

                        self._tools[tool_name] = tool
                        self._tool_configs[tool_name] = tool_config

                except Exception as e:
                    print(f"Error reading MCP config {filename}: {e}")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools"""
        return list(self._tools.values())

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool"""
        tool = self._tools.get(tool_name)
        if not tool:
            return {
                'success': False,
                'error': f'Tool not found: {tool_name}'
            }

        try:
            result = tool.execute(**kwargs)
            return {
                'success': True,
                'result': result,
                'tool_name': tool_name,
                'executed_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool_name': tool_name,
                'executed_at': datetime.now().isoformat()
            }

    def reload(self) -> None:
        """Reload all tools from configuration"""
        self.load_tools()

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool information"""
        tool = self._tools.get(tool_name)
        if tool:
            return tool.to_dict()
        return None

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools with their info"""
        tools_list = []
        for tool in self._tools.values():
            tool_dict = tool.to_dict()
            tool_dict['enabled'] = self.is_tool_enabled(tool.tool_name)
            tools_list.append(tool_dict)
        return tools_list

    def get_tools_for_planner(self) -> List[Dict[str, Any]]:
        """Get tool schemas for planner"""
        return [tool.get_schema() for tool in self._tools.values()]

    def get_mcp_servers_status(self) -> List[Dict[str, Any]]:
        """Get status of all configured MCP servers"""
        import time
        mcp_servers = []

        if not os.path.exists(self._mcp_config_dir):
            return mcp_servers

        for filename in os.listdir(self._mcp_config_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self._mcp_config_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        config = json.load(f)

                    mcp_name = config.get('name', filename.replace('.json', ''))
                    mcp_url = config.get('mcp_url', 'http://localhost:8000')
                    tool_description = config.get('tool_description', {})
                    tool_count = len(tool_description.get('tools', []))

                    # Check server health
                    status = 'offline'
                    response_time = None

                    try:
                        start_time = time.time()
                        response = requests.get(
                            f"{mcp_url}/health",
                            timeout=2
                        )
                        response_time = int((time.time() - start_time) * 1000)

                        if response.status_code == 200:
                            status = 'online'
                    except:
                        status = 'offline'

                    mcp_servers.append({
                        'name': mcp_name,
                        'url': mcp_url,
                        'status': status,
                        'response_time': response_time,
                        'tool_count': tool_count,
                        'config_file': filename
                    })

                except Exception as e:
                    print(f"Error reading MCP config {filename}: {e}")

        return mcp_servers

    def create_tool_from_json(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tool from JSON configuration

        Args:
            tool_data: Dictionary containing tool configuration
                {
                    "name": "tool_name",
                    "description": "Tool description",
                    "module": "tools.module.ClassName",
                    "config": {...}
                }

        Returns:
            Result dictionary with success status
        """
        try:
            tool_name = tool_data.get('name')
            if not tool_name:
                return {'success': False, 'error': 'Tool name is required'}

            # Check if tool already exists
            if tool_name in self._tools:
                return {'success': False, 'error': f'Tool {tool_name} already exists'}

            # Ensure config directory exists
            os.makedirs(self._config_dir, exist_ok=True)

            # Create config file
            config_path = os.path.join(self._config_dir, f"{tool_name}.json")
            if os.path.exists(config_path):
                return {'success': False, 'error': f'Configuration file for {tool_name} already exists'}

            # Prepare configuration
            config = {
                'name': tool_name,
                'description': tool_data.get('description', ''),
                'module': tool_data.get('module'),
                'config': tool_data.get('config', {}),
                'enabled': True
            }

            # Write configuration file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            # Reload tools to include new one
            self.load_tools()

            return {
                'success': True,
                'message': f'Tool {tool_name} created successfully',
                'tool_name': tool_name
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create tool: {str(e)}'
            }

    def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool"""
        try:
            config_path = os.path.join(self._config_dir, f"{tool_name}.json")
            if not os.path.exists(config_path):
                return False

            with open(config_path, 'r') as f:
                config = json.load(f)

            config['enabled'] = True

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            self.load_tools()
            return True
        except:
            return False

    def disable_tool(self, tool_name: str) -> bool:
        """Disable a tool"""
        try:
            config_path = os.path.join(self._config_dir, f"{tool_name}.json")
            if not os.path.exists(config_path):
                return False

            with open(config_path, 'r') as f:
                config = json.load(f)

            config['enabled'] = False

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            # Remove from active tools
            if tool_name in self._tools:
                del self._tools[tool_name]

            return True
        except:
            return False

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled"""
        try:
            config_path = os.path.join(self._config_dir, f"{tool_name}.json")
            if not os.path.exists(config_path):
                return False

            with open(config_path, 'r') as f:
                config = json.load(f)

            return config.get('enabled', True)
        except:
            return False