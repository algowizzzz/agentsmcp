"""
Cache Manager Tool for Abhikarta
Manages caching of LLM results and other expensive operations

© 2025 Model Documentation Integration
"""
import os
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from tools.base_tool import BaseTool


class CacheManagerTool(BaseTool):
    """Tool for caching LLM results and expensive operations"""
    
    def __init__(self, tool_name: str, description: str, config: Dict[str, Any] = None):
        super().__init__(tool_name, description, config)
        self.cache_db_path = config.get('cache_db_path', 'data/cache.db')
        self.default_ttl = config.get('default_ttl', 86400)  # 24 hours default
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize cache database"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.cache_db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        # Create cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Create index on expires_at for efficient cleanup
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
        ''')
        
        conn.commit()
        conn.close()
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute cache operations
        
        Args:
            action: Operation to perform (cache_result, get_cached, invalidate_cache, clear_expired)
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with success status and result/error
        """
        try:
            if action == "cache_result":
                return self._cache_result(**kwargs)
            elif action == "get_cached":
                return self._get_cached(**kwargs)
            elif action == "invalidate_cache":
                return self._invalidate_cache(**kwargs)
            elif action == "clear_expired":
                return self._clear_expired(**kwargs)
            elif action == "clear_all":
                return self._clear_all(**kwargs)
            elif action == "get_stats":
                return self._get_stats(**kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Cache operation error: {str(e)}'
            }
    
    def _cache_result(self, key: str = None, value: Any = None, ttl: int = None,
                     metadata: Dict[str, Any] = None, auto_key: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store a result in cache
        
        Args:
            key: Cache key (if not provided, generated from auto_key)
            value: Value to cache
            ttl: Time to live in seconds
            metadata: Additional metadata
            auto_key: Dictionary to generate key from (hashed)
            
        Returns:
            Dictionary with success status
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # Generate key if not provided
        if key is None and auto_key is not None:
            key = self._generate_key(auto_key)
        elif key is None:
            return {
                'success': False,
                'error': 'Either key or auto_key must be provided'
            }
        
        # Calculate expiry time
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Serialize value
        if not isinstance(value, str):
            value_str = json.dumps(value)
        else:
            value_str = value
        
        # Serialize metadata
        metadata_str = json.dumps(metadata) if metadata else None
        
        # Store in database
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO cache (key, value, created_at, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (key, value_str, datetime.now(), expires_at, metadata_str))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'key': key,
            'expires_at': expires_at.isoformat(),
            'ttl': ttl
        }
    
    def _get_cached(self, key: str = None, auto_key: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Retrieve cached result
        
        Args:
            key: Cache key (if not provided, generated from auto_key)
            auto_key: Dictionary to generate key from
            
        Returns:
            Dictionary with cached value or None if not found/expired
        """
        # Generate key if not provided
        if key is None and auto_key is not None:
            key = self._generate_key(auto_key)
        elif key is None:
            return {
                'success': False,
                'error': 'Either key or auto_key must be provided'
            }
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        # Retrieve from database
        cursor.execute('''
            SELECT value, expires_at, metadata, created_at
            FROM cache
            WHERE key = ?
        ''', (key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return {
                'success': True,
                'found': False,
                'value': None
            }
        
        value_str, expires_at_str, metadata_str, created_at_str = row
        
        # Check if expired
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now() > expires_at:
            # Remove expired entry
            self._invalidate_cache(key=key)
            return {
                'success': True,
                'found': False,
                'value': None,
                'expired': True
            }
        
        # Deserialize value
        try:
            value = json.loads(value_str)
        except json.JSONDecodeError:
            value = value_str
        
        # Deserialize metadata
        metadata = None
        if metadata_str:
            try:
                metadata = json.loads(metadata_str)
            except json.JSONDecodeError:
                pass
        
        return {
            'success': True,
            'found': True,
            'value': value,
            'metadata': metadata,
            'created_at': created_at_str,
            'expires_at': expires_at_str
        }
    
    def _invalidate_cache(self, key: str = None, auto_key: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Invalidate (delete) a cache entry
        
        Args:
            key: Cache key
            auto_key: Dictionary to generate key from
            
        Returns:
            Dictionary with success status
        """
        # Generate key if not provided
        if key is None and auto_key is not None:
            key = self._generate_key(auto_key)
        elif key is None:
            return {
                'success': False,
                'error': 'Either key or auto_key must be provided'
            }
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'deleted': deleted > 0
        }
    
    def _clear_expired(self) -> Dict[str, Any]:
        """
        Clear all expired cache entries
        
        Returns:
            Dictionary with count of cleared entries
        """
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM cache
            WHERE expires_at < ?
        ''', (datetime.now(),))
        
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'cleared_count': deleted_count
        }
    
    def _clear_all(self) -> Dict[str, Any]:
        """
        Clear all cache entries
        
        Returns:
            Dictionary with count of cleared entries
        """
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM cache')
        total_count = cursor.fetchone()[0]
        
        cursor.execute('DELETE FROM cache')
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'cleared_count': total_count
        }
    
    def _get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute('SELECT COUNT(*) FROM cache')
        total_count = cursor.fetchone()[0]
        
        # Expired entries
        cursor.execute('SELECT COUNT(*) FROM cache WHERE expires_at < ?', (datetime.now(),))
        expired_count = cursor.fetchone()[0]
        
        # Valid entries
        valid_count = total_count - expired_count
        
        # Database size
        db_size = os.path.getsize(self.cache_db_path) if os.path.exists(self.cache_db_path) else 0
        
        conn.close()
        
        return {
            'success': True,
            'stats': {
                'total_entries': total_count,
                'valid_entries': valid_count,
                'expired_entries': expired_count,
                'db_size_bytes': db_size,
                'db_size_mb': round(db_size / (1024 * 1024), 2)
            }
        }
    
    def _generate_key(self, data: Dict[str, Any]) -> str:
        """
        Generate cache key from data dictionary
        
        Args:
            data: Data to generate key from
            
        Returns:
            SHA256 hash as key
        """
        # Sort keys for consistent hashing
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'actions': [
                {
                    'name': 'cache_result',
                    'description': 'Store a result in cache',
                    'parameters': {
                        'key': 'Cache key (optional if auto_key provided)',
                        'value': 'Value to cache',
                        'ttl': 'Time to live in seconds (optional)',
                        'metadata': 'Additional metadata (optional)',
                        'auto_key': 'Dictionary to generate key from (optional)'
                    }
                },
                {
                    'name': 'get_cached',
                    'description': 'Retrieve cached result',
                    'parameters': {
                        'key': 'Cache key (optional if auto_key provided)',
                        'auto_key': 'Dictionary to generate key from (optional)'
                    }
                },
                {
                    'name': 'invalidate_cache',
                    'description': 'Invalidate a cache entry',
                    'parameters': {
                        'key': 'Cache key (optional if auto_key provided)',
                        'auto_key': 'Dictionary to generate key from (optional)'
                    }
                },
                {
                    'name': 'clear_expired',
                    'description': 'Clear all expired cache entries',
                    'parameters': {}
                },
                {
                    'name': 'clear_all',
                    'description': 'Clear all cache entries',
                    'parameters': {}
                },
                {
                    'name': 'get_stats',
                    'description': 'Get cache statistics',
                    'parameters': {}
                }
            ]
        }

