"""
DAG Database Handler
Database operations for DAGs and workflow executions

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import List, Dict, Any
from db.database_handler_base import DatabaseHandlerBase


class DAGHandler(DatabaseHandlerBase):
    """Handler for DAG-related database operations"""
    
    # ==================== DAG Statistics ====================
    
    def get_dag_statistics(self) -> List[Dict[str, Any]]:
        """Get per-DAG statistics"""
        return self.db.fetchall("""
            SELECT 
                dag_id,
                name,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running
            FROM workflows
            GROUP BY dag_id, name
            ORDER BY total DESC
        """)
