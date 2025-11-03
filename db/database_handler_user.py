"""
User Database Handler
Database operations for users and sessions

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import List, Dict, Any, Optional
from db.database_handler_base import DatabaseHandlerBase


class UserHandler(DatabaseHandlerBase):
    """Handler for user and session-related database operations"""
    
    # ==================== User Operations ====================
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific user"""
        return self.db.fetchone(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a user by username"""
        return self.db.fetchone(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
    
    def create_user(self, user_data: Dict[str, Any]) -> int:
        """Create a new user"""
        return self.db.insert('users', user_data)
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> int:
        """Update user data"""
        return self.db.update(
            'users',
            update_data,
            'user_id = ?',
            (user_id,)
        )
    
    def count_total_users(self) -> int:
        """Get total count of users"""
        result = self.db.fetchone("SELECT COUNT(*) as count FROM users")
        return result['count'] if result else 0
    
    def count_distinct_users_in_sessions(self, start_time: str) -> int:
        """Count distinct users in sessions since a given time"""
        result = self.db.fetchone(
            "SELECT COUNT(DISTINCT user_id) as count FROM sessions WHERE created_at >= ?",
            (start_time,)
        )
        return result['count'] if result else 0
    
    def get_user_statistics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user statistics with session and workflow counts"""
        return self.db.fetchall("""
            SELECT 
                u.username,
                u.role,
                u.last_login,
                (SELECT COUNT(*) FROM sessions WHERE user_id = u.user_id) as session_count,
                (SELECT COUNT(*) FROM workflows WHERE created_by = u.user_id) as workflow_count
            FROM users u
            ORDER BY workflow_count DESC
            LIMIT ?
        """, (limit,))
    
    def count_active_users_in_last_24h(self, time_24h_ago: str) -> int:
        """Count active users in the last 24 hours"""
        result = self.db.fetchone(
            "SELECT COUNT(DISTINCT user_id) as count FROM sessions WHERE updated_at >= ?",
            (time_24h_ago,)
        )
        return result['count'] if result else 0
    
    # ==================== Session Operations ====================
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific session"""
        return self.db.fetchone(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,)
        )
    
    def get_user_sessions(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sessions for a specific user"""
        if status:
            return self.db.fetchall(
                "SELECT * FROM sessions WHERE user_id = ? AND status = ? ORDER BY updated_at DESC",
                (user_id, status)
            )
        else:
            return self.db.fetchall(
                "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            )
    
    def create_session(self, session_data: Dict[str, Any]) -> int:
        """Create a new session"""
        return self.db.insert('sessions', session_data)
    
    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> int:
        """Update session data"""
        return self.db.update(
            'sessions',
            update_data,
            'session_id = ?',
            (session_id,)
        )
    
    def count_sessions_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count sessions created within a time range"""
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM sessions WHERE created_at >= ? AND created_at < ?",
            (start_time, end_time)
        )
        return result['count'] if result else 0
    
    def get_active_sessions_with_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get active sessions with user information"""
        return self.db.fetchall("""
            SELECT s.*, u.username 
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.status = 'active'
            ORDER BY s.updated_at DESC
            LIMIT ?
        """, (limit,))
