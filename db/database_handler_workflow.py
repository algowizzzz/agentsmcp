"""
Workflow Database Handler
Database operations for workflows, events, and nodes

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import List, Dict, Any, Optional
from db.database_handler_base import DatabaseHandlerBase


class WorkflowHandler(DatabaseHandlerBase):
    """Handler for workflow-related database operations"""
    
    # ==================== Workflow Operations ====================
    
    def get_all_workflows(self, limit: Optional[int] = None, order_by: str = 'created_at DESC') -> List[Dict[str, Any]]:
        """Get all workflows with optional limit and ordering"""
        query = f"SELECT * FROM workflows ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        return self.db.fetchall(query)
    
    def get_workflow_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow by ID"""
        return self.db.fetchone(
            "SELECT * FROM workflows WHERE workflow_id = ?",
            (workflow_id,)
        )
    
    def get_workflows_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get workflows filtered by status"""
        return self.db.fetchall(
            "SELECT * FROM workflows WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
    
    def get_recent_workflows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent workflows"""
        return self.get_all_workflows(limit=limit, order_by='created_at DESC')
    
    def create_workflow(self, workflow_data: Dict[str, Any]) -> int:
        """Create a new workflow"""
        return self.db.insert('workflows', workflow_data)
    
    def update_workflow(self, workflow_id: str, update_data: Dict[str, Any]) -> int:
        """Update workflow data"""
        return self.db.update(
            'workflows',
            update_data,
            'workflow_id = ?',
            (workflow_id,)
        )
    
    def delete_workflow(self, workflow_id: str) -> int:
        """Delete a workflow"""
        return self.db.delete('workflows', 'workflow_id = ?', (workflow_id,))
    
    # ==================== Workflow Statistics ====================
    
    def get_workflow_count(self, status: Optional[str] = None) -> int:
        """Get count of workflows, optionally filtered by status"""
        if status:
            result = self.db.fetchone(
                "SELECT COUNT(*) as count FROM workflows WHERE status = ?",
                (status,)
            )
        else:
            result = self.db.fetchone("SELECT COUNT(*) as count FROM workflows")
        
        return result['count'] if result else 0
    
    def get_workflow_statistics(self) -> Dict[str, int]:
        """Get comprehensive workflow statistics"""
        return {
            'total': self.get_workflow_count(),
            'running': self.get_workflow_count('running'),
            'completed': self.get_workflow_count('completed'),
            'failed': self.get_workflow_count('failed'),
            'pending': self.get_workflow_count('pending')
        }
    
    def count_workflows_by_time(self, start_time: str) -> int:
        """Count workflows created since a given time"""
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM workflows WHERE created_at >= ?",
            (start_time,)
        )
        return result['count'] if result else 0
    
    def get_workflow_success_stats(self, start_time: str) -> Dict[str, int]:
        """Get success statistics for workflows"""
        result = self.db.fetchone("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as started
            FROM workflows
            WHERE created_at >= ?
        """, (start_time,))
        
        if result:
            return {
                'total': result['total'] or 0,
                'completed': result['completed'] or 0,
                'started': result['started'] or 0
            }
        return {'total': 0, 'completed': 0, 'started': 0}
    
    def count_workflows_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count workflows within a time range"""
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM workflows WHERE created_at >= ? AND created_at < ?",
            (start_time, end_time)
        )
        return result['count'] if result else 0
    
    def count_workflows_started_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count workflows started within a time range"""
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM workflows WHERE started_at >= ? AND started_at < ?",
            (start_time, end_time)
        )
        return result['count'] if result else 0
    
    def count_workflows_completed_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count workflows completed within a time range"""
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM workflows WHERE completed_at >= ? AND completed_at < ?",
            (start_time, end_time)
        )
        return result['count'] if result else 0
    
    # ==================== Workflow Events ====================
    
    def get_workflow_events(self, workflow_id: str, order_by: str = 'created_at DESC') -> List[Dict[str, Any]]:
        """Get all events for a specific workflow"""
        return self.db.fetchall(
            f"SELECT * FROM workflow_events WHERE workflow_id = ? ORDER BY {order_by}",
            (workflow_id,)
        )
    
    def create_workflow_event(self, event_data: Dict[str, Any]) -> int:
        """Create a new workflow event"""
        return self.db.insert('workflow_events', event_data)
    
    def get_events_by_type(self, workflow_id: str, event_type: str) -> List[Dict[str, Any]]:
        """Get workflow events filtered by type"""
        return self.db.fetchall(
            "SELECT * FROM workflow_events WHERE workflow_id = ? AND event_type = ? ORDER BY created_at DESC",
            (workflow_id, event_type)
        )
    
    # ==================== Workflow Nodes ====================
    
    def get_workflow_nodes(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all nodes for a specific workflow"""
        return self.db.fetchall(
            "SELECT * FROM workflow_nodes WHERE workflow_id = ?",
            (workflow_id,)
        )
    
    def get_node_by_id(self, workflow_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow node"""
        return self.db.fetchone(
            "SELECT * FROM workflow_nodes WHERE workflow_id = ? AND node_id = ?",
            (workflow_id, node_id)
        )
    
    def create_workflow_node(self, node_data: Dict[str, Any]) -> int:
        """Create a new workflow node"""
        return self.db.insert('workflow_nodes', node_data)
    
    def update_workflow_node(self, workflow_id: str, node_id: str, update_data: Dict[str, Any]) -> int:
        """Update workflow node data"""
        return self.db.update(
            'workflow_nodes',
            update_data,
            'workflow_id = ? AND node_id = ?',
            (workflow_id, node_id)
        )
