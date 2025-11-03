"""
Tool Database Handler
Database operations for tools and tool executions

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import Dict, Any, Optional
from db.database_handler_base import DatabaseHandlerBase


class ToolHandler(DatabaseHandlerBase):
    """Handler for tool-related database operations"""
    
    # ==================== Tool Monitoring ====================
    
    def count_tool_nodes(self, start_time: Optional[str] = None) -> int:
        """Count tool executions, optionally since a given time"""
        if start_time:
            result = self.db.fetchone("""
                SELECT COUNT(*) as count FROM workflow_nodes 
                WHERE node_type = 'tool' AND started_at >= ?
            """, (start_time,))
        else:
            result = self.db.fetchone("""
                SELECT COUNT(*) as count FROM workflow_nodes 
                WHERE node_type = 'tool'
            """)
        return result['count'] if result else 0
    
    def get_tool_success_stats(self, start_time: str) -> Dict[str, int]:
        """Get success statistics for tool executions"""
        result = self.db.fetchone("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success
            FROM workflow_nodes
            WHERE node_type = 'tool' AND started_at >= ?
        """, (start_time,))
        
        if result:
            return {
                'total': result['total'] or 0,
                'success': result['success'] or 0
            }
        return {'total': 0, 'success': 0}
    
    def count_tool_nodes_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count tool nodes within a time range"""
        result = self.db.fetchone("""
            SELECT COUNT(*) as count FROM workflow_nodes 
            WHERE node_type = 'tool' AND started_at >= ? AND started_at < ?
        """, (start_time, end_time))
        return result['count'] if result else 0
