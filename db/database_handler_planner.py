"""
Planner Database Handler
Database operations for planner, LGraph planner, plans, and conversations

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import List, Dict, Any, Optional
from db.database_handler_base import DatabaseHandlerBase


class PlannerHandler(DatabaseHandlerBase):
    """Handler for planner-related database operations"""
    
    # ==================== Regular Planner ====================
    
    def count_plans(self, start_time: Optional[str] = None) -> int:
        """Count plans, optionally since a given time"""
        try:
            if not self.table_exists('plans'):
                return 0
            if start_time:
                result = self.db.fetchone(
                    "SELECT COUNT(*) as count FROM plans WHERE created_at >= ?",
                    (start_time,)
                )
            else:
                result = self.db.fetchone("SELECT COUNT(*) as count FROM plans")
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting plans: {e}")
            return 0
    
    def get_plan_approval_stats(self, start_time: str) -> Dict[str, int]:
        """Get approval statistics for plans"""
        try:
            if not self.table_exists('plans'):
                return {'total': 0, 'approved': 0}
            
            result = self.db.fetchone("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved
                FROM plans
                WHERE created_at >= ?
            """, (start_time,))
            
            if result:
                return {
                    'total': result['total'] or 0,
                    'approved': result['approved'] or 0
                }
            return {'total': 0, 'approved': 0}
        except Exception as e:
            print(f"Error getting plan approval stats: {e}")
            return {'total': 0, 'approved': 0}
    
    def count_planner_conversations(self, start_time: str) -> int:
        """Count planner conversations since a given time"""
        try:
            if not self.table_exists('planner_conversations'):
                return 0
            result = self.db.fetchone(
                "SELECT COUNT(*) as count FROM planner_conversations WHERE created_at >= ?",
                (start_time,)
            )
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting planner conversations: {e}")
            return 0
    
    def count_plans_by_status(self, status: str) -> int:
        """Count plans with a specific status"""
        try:
            if not self.table_exists('plans'):
                return 0
            result = self.db.fetchone(
                "SELECT COUNT(*) as count FROM plans WHERE status = ?",
                (status,)
            )
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting plans by status: {e}")
            return 0
    
    def count_plans_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count plans within a time range"""
        try:
            if not self.table_exists('plans'):
                return 0
            result = self.db.fetchone(
                "SELECT COUNT(*) as count FROM plans WHERE created_at >= ? AND created_at < ?",
                (start_time, end_time)
            )
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting plans in time range: {e}")
            return 0
    
    def count_planner_conversations_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count planner conversations within a time range"""
        try:
            if not self.table_exists('planner_conversations'):
                return 0
            result = self.db.fetchone(
                "SELECT COUNT(*) as count FROM planner_conversations WHERE created_at >= ? AND created_at < ?",
                (start_time, end_time)
            )
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting planner conversations in time range: {e}")
            return 0
    
    def get_plan_status_distribution(self) -> Dict[str, int]:
        """Get distribution of plans by status"""
        return {
            'pending_approval': self.count_plans_by_status('pending_approval'),
            'approved': self.count_plans_by_status('approved'),
            'rejected': self.count_plans_by_status('rejected'),
            'executed': self.count_plans_by_status('executed')
        }
    
    def get_top_plan_users(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top users by plan count"""
        try:
            if not self.table_exists('users') or not self.table_exists('plans'):
                return []
            
            return self.db.fetchall("""
                SELECT 
                    u.username,
                    (SELECT COUNT(*) FROM plans WHERE user_id = u.user_id) as plan_count,
                    0 as conversation_count
                FROM users u
                WHERE (SELECT COUNT(*) FROM plans WHERE user_id = u.user_id) > 0
                ORDER BY plan_count DESC
                LIMIT ?
            """, (limit,))
        except Exception as e:
            print(f"Error getting top plan users: {e}")
            return []
    
    def get_recent_plans_with_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent plans with user information"""
        try:
            if not self.table_exists('plans'):
                return []
            
            return self.db.fetchall("""
                SELECT p.*, u.username
                FROM plans p
                JOIN users u ON p.user_id = u.user_id
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (limit,))
        except Exception as e:
            print(f"Error getting recent plans: {e}")
            return []
    
    # ==================== LGraph Planner ====================
    
    def count_lgraph_plans(self, since_time: Optional[str] = None) -> int:
        """Count LangGraph plans, optionally since a given time"""
        try:
            if not self.table_exists('lgraph_plans'):
                return 0
            if since_time:
                result = self.db.fetchone(
                    "SELECT COUNT(*) as count FROM lgraph_plans WHERE created_at >= ?",
                    (since_time,)
                )
            else:
                result = self.db.fetchone("SELECT COUNT(*) as count FROM lgraph_plans")
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting lgraph plans: {e}")
            return 0
    
    def count_lgraph_plans_in_time_range(self, start_time, end_time):
        """Count LangGraph plans within a time range"""
        try:
            if not self.table_exists('lgraph_plans'):
                return 0
            result = self.db.fetchone(
                "SELECT COUNT(*) as count FROM lgraph_plans WHERE created_at >= ? AND created_at < ?",
                (start_time, end_time)
            )
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting lgraph plans in time range: {e}")
            return 0
    
    def count_lgraph_conversations(self, since_time: Optional[str] = None) -> int:
        """Count LangGraph conversations, optionally since a given time"""
        try:
            if not self.table_exists('lgraph_conversations'):
                return 0
            if since_time:
                result = self.db.fetchone(
                    "SELECT COUNT(*) as count FROM lgraph_conversations WHERE created_at >= ?",
                    (since_time,)
                )
            else:
                result = self.db.fetchone("SELECT COUNT(*) as count FROM lgraph_conversations")
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting lgraph conversations: {e}")
            return 0
    
    def count_lgraph_conversations_in_time_range(self, start_time, end_time):
        """Count LangGraph conversations within a time range"""
        try:
            if not self.table_exists('lgraph_conversations'):
                return 0
            result = self.db.fetchone(
                "SELECT COUNT(*) as count FROM lgraph_conversations WHERE created_at >= ? AND created_at < ?",
                (start_time, end_time)
            )
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting lgraph conversations in time range: {e}")
            return 0
    
    def get_lgraph_plan_status_distribution(self):
        """Get distribution of LangGraph plans by status"""
        try:
            if not self.table_exists('lgraph_plans'):
                return {'pending_approval': 0, 'approved': 0, 'rejected': 0, 'executed': 0}
            
            results = self.db.fetchall("""
                SELECT status, COUNT(*) as count
                FROM lgraph_plans
                GROUP BY status
            """)
            
            distribution = {
                'pending_approval': 0,
                'approved': 0,
                'rejected': 0,
                'executed': 0
            }
            
            if results:
                for row in results:
                    status = row.get('status')
                    count = row.get('count', 0)
                    if status in distribution:
                        distribution[status] = count
            
            return distribution
        except Exception as e:
            print(f"Error getting lgraph plan status distribution: {e}")
            return {'pending_approval': 0, 'approved': 0, 'rejected': 0, 'executed': 0}
    
    def get_recent_lgraph_plans_with_users(self, limit=10):
        """Get recent LangGraph plans with user information"""
        try:
            if not self.table_exists('lgraph_plans'):
                return []
            
            results = self.db.fetchall("""
                SELECT 
                    p.plan_id,
                    p.user_id,
                    p.user_request as request,
                    p.status,
                    p.created_at,
                    COALESCE(u.username, p.user_id) as username
                FROM lgraph_plans p
                LEFT JOIN users u ON p.user_id = u.user_id
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (limit,))
            
            return results if results else []
        except Exception as e:
            print(f"Error getting recent lgraph plans: {e}")
            return []
    
    def get_top_plan_users_combined(self, limit=5):
        """Get top users by plan count (combines regular and LangGraph plans)"""
        try:
            if not self.table_exists('users'):
                return []
            
            has_plans = self.table_exists('plans')
            has_lgraph = self.table_exists('lgraph_plans')
            has_conv = self.table_exists('planner_conversations')
            has_lgraph_conv = self.table_exists('lgraph_conversations')
            
            # Build subqueries based on what exists
            plans_subquery = "(SELECT COUNT(*) FROM plans WHERE user_id = u.user_id)" if has_plans else "0"
            lgraph_subquery = "(SELECT COUNT(*) FROM lgraph_plans WHERE user_id = u.user_id)" if has_lgraph else "0"
            conv_subquery = "(SELECT COUNT(*) FROM planner_conversations WHERE user_id = u.user_id)" if has_conv else "0"
            lgraph_conv_subquery = "(SELECT COUNT(*) FROM lgraph_conversations WHERE user_id = u.user_id)" if has_lgraph_conv else "0"
            
            query = f"""
                SELECT 
                    u.user_id,
                    u.username,
                    ({plans_subquery} + {lgraph_subquery}) as plan_count,
                    ({conv_subquery} + {lgraph_conv_subquery}) as conversation_count
                FROM users u
                WHERE ({plans_subquery} + {lgraph_subquery}) > 0
                ORDER BY plan_count DESC
                LIMIT ?
            """
            
            results = self.db.fetchall(query, (limit,))
            return results if results else []
        except Exception as e:
            print(f"Error getting top plan users: {e}")
            return []
