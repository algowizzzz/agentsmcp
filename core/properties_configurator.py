"""
Properties Configurator for Abhikarta System
Manages application configuration from properties files

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import os
from typing import Any, Dict, Optional


class PropertiesConfigurator:
    """Singleton class to manage application properties"""
    
    _instance = None
    _properties: Dict[str, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PropertiesConfigurator, cls).__new__(cls)
        return cls._instance
    
    def load_properties(self, filepath: str) -> None:
        """Load properties from a file"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Properties file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self._properties[key.strip()] = value.strip()
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a property value"""
        return self._properties.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get a property as integer"""
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a property as boolean"""
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ('true', 'yes', '1', 'on')
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a property as float"""
        value = self.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    
    def set(self, key: str, value: str) -> None:
        """Set a property value"""
        self._properties[key] = value
    
    def get_all(self) -> Dict[str, str]:
        """Get all properties"""
        return self._properties.copy()

    def get_system_name(self) -> str:
        """Get the system/application name"""
        return self.get('app.name', 'Abhikarta')