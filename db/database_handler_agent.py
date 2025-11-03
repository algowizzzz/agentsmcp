"""
Agent Database Handler
Database operations for agents and agent executions

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import List, Dict, Any, Optional
from db.database_handler_base import DatabaseHandlerBase


class AgentHandler(DatabaseHandlerBase):
    """Handler for agent-related database operations"""
    
    # ==================== Agent Operations ====================
    
    def get_all_agents(self, order_by: str = 'created_at DESC') -> List[Dict[str, Any]]:
        """Get all agents"""
        query = f"SELECT * FROM agents ORDER BY {order_by}"
        return self.db.fetchall(query)
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent by ID"""
        return self.db.fetchone(
            "SELECT * FROM agents WHERE agent_id = ?",
            (agent_id,)
        )
    
    def create_agent(self, agent_data: Dict[str, Any]) -> int:
        """Create a new agent"""
        return self.db.insert('agents', agent_data)
    
    def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> int:
        """Update agent data"""
        return self.db.update(
            'agents',
            update_data,
            'agent_id = ?',
            (agent_id,)
        )
    
    def delete_agent(self, agent_id: str) -> int:
        """Delete an agent"""
        return self.db.delete('agents', 'agent_id = ?', (agent_id,))
    
    def enable_agent(self, agent_id: str) -> bool:
        """Enable an agent"""
        rows = self.update_agent(agent_id, {'enabled': True})
        return rows > 0
    
    def disable_agent(self, agent_id: str) -> bool:
        """Disable an agent"""
        rows = self.update_agent(agent_id, {'enabled': False})
        return rows > 0
    
    # ==================== Agent Statistics ====================
    
    def count_agents(self, enabled_only: bool = False) -> int:
        """Get count of agents"""
        if enabled_only:
            result = self.db.fetchone(
                "SELECT COUNT(*) as count FROM agents WHERE enabled = 1"
            )
        else:
            result = self.db.fetchone("SELECT COUNT(*) as count FROM agents")
        return result['count'] if result else 0
    
    def get_agent_execution_stats(self, agent_id: str, since_time=None):
        """Get execution statistics for an agent"""
        if since_time:
            results = self.db.fetchall("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    AVG(duration) as avg_duration
                FROM agent_executions
                WHERE agent_id = ? AND created_at >= ?
            """, (agent_id, since_time))
        else:
            results = self.db.fetchall("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    AVG(duration) as avg_duration
                FROM agent_executions
                WHERE agent_id = ?
            """, (agent_id,))
        
        return results[0] if results else {'total': 0, 'success': 0, 'failed': 0, 'avg_duration': 0}
    
    def count_agent_nodes(self, start_time: Optional[str] = None) -> int:
        """Count agent executions, optionally since a given time"""
        if start_time:
            result = self.db.fetchone("""
                SELECT COUNT(*) as count FROM workflow_nodes 
                WHERE node_type = 'agent' AND started_at >= ?
            """, (start_time,))
        else:
            result = self.db.fetchone("""
                SELECT COUNT(*) as count FROM workflow_nodes 
                WHERE node_type = 'agent'
            """)
        return result['count'] if result else 0
    
    def get_agent_success_stats(self, start_time: str) -> Dict[str, int]:
        """Get success statistics for agent executions"""
        result = self.db.fetchone("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success
            FROM workflow_nodes
            WHERE node_type = 'agent' AND started_at >= ?
        """, (start_time,))
        
        if result:
            return {
                'total': result['total'] or 0,
                'success': result['success'] or 0
            }
        return {'total': 0, 'success': 0}
    
    def count_agent_nodes_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count agent nodes within a time range"""
        result = self.db.fetchone("""
            SELECT COUNT(*) as count FROM workflow_nodes 
            WHERE node_type = 'agent' AND started_at >= ? AND started_at < ?
        """, (start_time, end_time))
        return result['count'] if result else 0
    
    def get_agent_statistics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get agent statistics with execution counts"""
        return self.db.fetchall("""
            SELECT 
                node_id as agent_id,
                COUNT(*) as total_executions,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM workflow_nodes
            WHERE node_type = 'agent'
            GROUP BY node_id
            ORDER BY total_executions DESC
            LIMIT ?
        """, (limit,))
    
    # ==================== Agent Executions ====================
    
    def get_agent_executions(self, workflow_id: Optional[str] = None, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get agent executions, optionally filtered by workflow or agent"""
        if workflow_id and agent_id:
            return self.db.fetchall(
                "SELECT * FROM agent_executions WHERE workflow_id = ? AND agent_id = ? ORDER BY started_at DESC",
                (workflow_id, agent_id)
            )
        elif workflow_id:
            return self.db.fetchall(
                "SELECT * FROM agent_executions WHERE workflow_id = ? ORDER BY started_at DESC",
                (workflow_id,)
            )
        elif agent_id:
            return self.db.fetchall(
                "SELECT * FROM agent_executions WHERE agent_id = ? ORDER BY started_at DESC",
                (agent_id,)
            )
        else:
            return self.db.fetchall(
                "SELECT * FROM agent_executions ORDER BY started_at DESC"
            )
    
    def get_agent_execution_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent execution"""
        return self.db.fetchone(
            "SELECT * FROM agent_executions WHERE execution_id = ?",
            (execution_id,)
        )
    
    def create_agent_execution(self, execution_data: Dict[str, Any]) -> int:
        """Create a new agent execution record"""
        return self.db.insert('agent_executions', execution_data)
    
    def update_agent_execution(self, execution_id: str, update_data: Dict[str, Any]) -> int:
        """Update agent execution data"""
        return self.db.update(
            'agent_executions',
            update_data,
            'execution_id = ?',
            (execution_id,)
        )
