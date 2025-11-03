"""
User Registry for Abhikarta System
Centralized user management from users.json

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import json
import os
from typing import Dict, List, Optional, Set
from threading import Lock


class User:
    """Represents a user in the system"""
    
    def __init__(self, user_id: str, username: str, password: str, full_name: str,
                 email: str, role: str, approved_tools: List[str], 
                 approved_agents: List[str], approved_dags: List[str]):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.full_name = full_name
        self.email = email
        self.role = role
        self.approved_tools = set(approved_tools)
        self.approved_agents = set(approved_agents)
        self.approved_dags = set(approved_dags)
    
    def has_tool_access(self, tool_name: str) -> bool:
        """Check if user has access to a tool"""
        return self.role == 'admin' or tool_name in self.approved_tools or '*' in self.approved_tools
    
    def has_agent_access(self, agent_id: str) -> bool:
        """Check if user has access to an agent"""
        return self.role == 'admin' or agent_id in self.approved_agents or '*' in self.approved_agents
    
    def has_dag_access(self, dag_id: str) -> bool:
        """Check if user has access to a DAG"""
        return self.role == 'admin' or dag_id in self.approved_dags or '*' in self.approved_dags
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == 'admin'
    
    def to_dict(self, include_password: bool = False) -> Dict:
        """Convert user to dictionary"""
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'approved_tools': list(self.approved_tools),
            'approved_agents': list(self.approved_agents),
            'approved_dags': list(self.approved_dags)
        }
        if include_password:
            data['password'] = self.password
        return data


class UserRegistry:
    """Singleton registry for user management"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(UserRegistry, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._users: Dict[str, User] = {}
        self._users_by_username: Dict[str, User] = {}
        self._config_path = 'config/users/users.json'
        self._initialized = True
        self.load_users()
    
    def load_users(self) -> None:
        """Load users from configuration file"""
        if not os.path.exists(self._config_path):
            # Create default admin user
            self._create_default_admin()
            return
        
        with open(self._config_path, 'r') as f:
            users_data = json.load(f)
        
        self._users.clear()
        self._users_by_username.clear()
        
        for user_data in users_data.get('users', []):
            user = User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                password=user_data['password'],
                full_name=user_data.get('full_name', ''),
                email=user_data.get('email', ''),
                role=user_data.get('role', 'user'),
                approved_tools=user_data.get('approved_tools', []),
                approved_agents=user_data.get('approved_agents', []),
                approved_dags=user_data.get('approved_dags', [])
            )
            self._users[user.user_id] = user
            self._users_by_username[user.username] = user
    
    def _create_default_admin(self) -> None:
        """Create default admin user"""
        admin = User(
            user_id='admin',
            username='admin',
            password='admin',
            full_name='System Administrator',
            email='admin@abhikarta.com',
            role='admin',
            approved_tools=['*'],
            approved_agents=['*'],
            approved_dags=['*']
        )
        self._users['admin'] = admin
        self._users_by_username['admin'] = admin
        
        # Save to file
        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
        self.save_users()
    
    def save_users(self) -> None:
        """Save users to configuration file"""
        users_data = {
            'users': [user.to_dict(include_password=True) for user in self._users.values()]
        }
        
        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
        with open(self._config_path, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        user = self._users_by_username.get(username)
        if user and user.password == password:
            return user
        return None
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self._users_by_username.get(username)
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        return list(self._users.values())
    
    def add_user(self, user: User) -> bool:
        """Add a new user"""
        if user.user_id in self._users or user.username in self._users_by_username:
            return False
        
        self._users[user.user_id] = user
        self._users_by_username[user.username] = user
        self.save_users()
        return True
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user details (admin cannot be updated)"""
        user = self._users.get(user_id)
        if not user or user.user_id == 'admin':
            return False
        
        # Update fields
        if 'full_name' in kwargs:
            user.full_name = kwargs['full_name']
        if 'email' in kwargs:
            user.email = kwargs['email']
        if 'password' in kwargs:
            user.password = kwargs['password']
        if 'role' in kwargs:
            user.role = kwargs['role']
        if 'approved_tools' in kwargs:
            user.approved_tools = set(kwargs['approved_tools'])
        if 'approved_agents' in kwargs:
            user.approved_agents = set(kwargs['approved_agents'])
        if 'approved_dags' in kwargs:
            user.approved_dags = set(kwargs['approved_dags'])
        
        self.save_users()
        return True
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user (admin cannot be deleted)"""
        if user_id == 'admin' or user_id not in self._users:
            return False
        
        user = self._users[user_id]
        del self._users[user_id]
        del self._users_by_username[user.username]
        self.save_users()
        return True
    
    def reload(self) -> None:
        """Reload users from configuration file"""
        self.load_users()
