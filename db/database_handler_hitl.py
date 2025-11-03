"""
HITL Database Handler
Database operations for Human-in-the-Loop (HITL) requests

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import List, Dict, Any, Optional
from db.database_handler_base import DatabaseHandlerBase


class HITLHandler(DatabaseHandlerBase):
    """Handler for HITL-related database operations"""
    
    # ==================== HITL Requests ====================
    
    def get_hitl_requests(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all HITL requests for a specific workflow"""
        return self.db.fetchall(
            "SELECT * FROM hitl_requests WHERE workflow_id = ?",
            (workflow_id,)
        )
    
    def get_pending_hitl_requests(self) -> List[Dict[str, Any]]:
        """Get all pending HITL requests across all workflows"""
        return self.db.fetchall(
            "SELECT * FROM hitl_requests WHERE status = 'pending' ORDER BY created_at ASC"
        )
    
    def get_hitl_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific HITL request"""
        return self.db.fetchone(
            "SELECT * FROM hitl_requests WHERE request_id = ?",
            (request_id,)
        )
    
    def create_hitl_request(self, request_data: Dict[str, Any]) -> int:
        """Create a new HITL request"""
        return self.db.insert('hitl_requests', request_data)
    
    def update_hitl_request(self, request_id: str, update_data: Dict[str, Any]) -> int:
        """Update HITL request data"""
        return self.db.update(
            'hitl_requests',
            update_data,
            'request_id = ?',
            (request_id,)
        )
    
    def count_pending_hitl_requests(self) -> int:
        """Count pending HITL requests"""
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM hitl_requests WHERE status = 'pending'"
        )
        return result['count'] if result else 0
