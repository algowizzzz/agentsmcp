"""
Unified Database Handler
Delegates to specialized handlers for different database operations
Maintains backward compatibility with DatabaseCallHandler interface

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import List, Dict, Any, Optional
from db.database import get_db
from db.database_handler_base import DatabaseHandlerBase
from db.database_handler_workflow import WorkflowHandler
from db.database_handler_user import UserHandler
from db.database_handler_agent import AgentHandler
from db.database_handler_tool import ToolHandler
from db.database_handler_dag import DAGHandler
from db.database_handler_hitl import HITLHandler
from db.database_handler_planner import PlannerHandler
from db.database_handler_monitoring import MonitoringHandler


class DatabaseCallHandler(DatabaseHandlerBase):
    """
    Unified database handler that delegates to specialized handlers
    Maintains backward compatibility with the original DatabaseCallHandler
    """
    
    def __init__(self, database):
        """
        Initialize the unified handler with all specialized handlers
        
        Args:
            database: Database instance from database.py
        """
        super().__init__(database)
        
        # Initialize all specialized handlers
        self.workflow = WorkflowHandler(database)
        self.user = UserHandler(database)
        self.agent = AgentHandler(database)
        self.tool = ToolHandler(database)
        self.dag = DAGHandler(database)
        self.hitl = HITLHandler(database)
        self.planner = PlannerHandler(database)
        self.monitoring = MonitoringHandler(
            database, 
            self.workflow, 
            self.user, 
            self.agent, 
            self.tool, 
            self.dag, 
            self.planner, 
            self.hitl
        )
    
    # ==================== Workflow Operations (Delegate to WorkflowHandler) ====================
    
    def get_all_workflows(self, limit: Optional[int] = None, order_by: str = 'created_at DESC') -> List[Dict[str, Any]]:
        """Get all workflows with optional limit and ordering"""
        return self.workflow.get_all_workflows(limit, order_by)
    
    def get_workflow_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow by ID"""
        return self.workflow.get_workflow_by_id(workflow_id)
    
    def get_workflows_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get workflows filtered by status"""
        return self.workflow.get_workflows_by_status(status)
    
    def get_recent_workflows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent workflows"""
        return self.workflow.get_recent_workflows(limit)
    
    def create_workflow(self, workflow_data: Dict[str, Any]) -> int:
        """Create a new workflow"""
        return self.workflow.create_workflow(workflow_data)
    
    def update_workflow(self, workflow_id: str, update_data: Dict[str, Any]) -> int:
        """Update workflow data"""
        return self.workflow.update_workflow(workflow_id, update_data)
    
    def delete_workflow(self, workflow_id: str) -> int:
        """Delete a workflow"""
        return self.workflow.delete_workflow(workflow_id)
    
    def get_workflow_count(self, status: Optional[str] = None) -> int:
        """Get count of workflows, optionally filtered by status"""
        return self.workflow.get_workflow_count(status)
    
    def get_workflow_statistics(self) -> Dict[str, int]:
        """Get comprehensive workflow statistics"""
        return self.workflow.get_workflow_statistics()
    
    def count_workflows_by_time(self, start_time: str) -> int:
        """Count workflows created since a given time"""
        return self.workflow.count_workflows_by_time(start_time)
    
    def get_workflow_success_stats(self, start_time: str) -> Dict[str, int]:
        """Get success statistics for workflows"""
        return self.workflow.get_workflow_success_stats(start_time)
    
    def count_workflows_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count workflows within a time range"""
        return self.workflow.count_workflows_in_time_range(start_time, end_time)
    
    def count_workflows_started_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count workflows started within a time range"""
        return self.workflow.count_workflows_started_in_time_range(start_time, end_time)
    
    def count_workflows_completed_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count workflows completed within a time range"""
        return self.workflow.count_workflows_completed_in_time_range(start_time, end_time)
    
    def get_workflow_events(self, workflow_id: str, order_by: str = 'created_at DESC') -> List[Dict[str, Any]]:
        """Get all events for a specific workflow"""
        return self.workflow.get_workflow_events(workflow_id, order_by)
    
    def create_workflow_event(self, event_data: Dict[str, Any]) -> int:
        """Create a new workflow event"""
        return self.workflow.create_workflow_event(event_data)
    
    def get_events_by_type(self, workflow_id: str, event_type: str) -> List[Dict[str, Any]]:
        """Get workflow events filtered by type"""
        return self.workflow.get_events_by_type(workflow_id, event_type)
    
    def get_workflow_nodes(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all nodes for a specific workflow"""
        return self.workflow.get_workflow_nodes(workflow_id)
    
    def get_node_by_id(self, workflow_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow node"""
        return self.workflow.get_node_by_id(workflow_id, node_id)
    
    def create_workflow_node(self, node_data: Dict[str, Any]) -> int:
        """Create a new workflow node"""
        return self.workflow.create_workflow_node(node_data)
    
    def update_workflow_node(self, workflow_id: str, node_id: str, update_data: Dict[str, Any]) -> int:
        """Update workflow node data"""
        return self.workflow.update_workflow_node(workflow_id, node_id, update_data)
    
    # ==================== User Operations (Delegate to UserHandler) ====================
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific user"""
        return self.user.get_user_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a user by username"""
        return self.user.get_user_by_username(username)
    
    def create_user(self, user_data: Dict[str, Any]) -> int:
        """Create a new user"""
        return self.user.create_user(user_data)
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> int:
        """Update user data"""
        return self.user.update_user(user_id, update_data)
    
    def count_total_users(self) -> int:
        """Get total count of users"""
        return self.user.count_total_users()
    
    def count_distinct_users_in_sessions(self, start_time: str) -> int:
        """Count distinct users in sessions since a given time"""
        return self.user.count_distinct_users_in_sessions(start_time)
    
    def get_user_statistics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user statistics with session and workflow counts"""
        return self.user.get_user_statistics(limit)
    
    def count_active_users_in_last_24h(self, time_24h_ago: str) -> int:
        """Count active users in the last 24 hours"""
        return self.user.count_active_users_in_last_24h(time_24h_ago)
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific session"""
        return self.user.get_session_by_id(session_id)
    
    def get_user_sessions(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sessions for a specific user"""
        return self.user.get_user_sessions(user_id, status)
    
    def create_session(self, session_data: Dict[str, Any]) -> int:
        """Create a new session"""
        return self.user.create_session(session_data)
    
    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> int:
        """Update session data"""
        return self.user.update_session(session_id, update_data)
    
    def count_sessions_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count sessions created within a time range"""
        return self.user.count_sessions_in_time_range(start_time, end_time)
    
    def get_active_sessions_with_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get active sessions with user information"""
        return self.user.get_active_sessions_with_users(limit)
    
    # ==================== Agent Operations (Delegate to AgentHandler) ====================
    
    def get_all_agents(self, order_by: str = 'created_at DESC') -> List[Dict[str, Any]]:
        """Get all agents"""
        return self.agent.get_all_agents(order_by)
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent by ID"""
        return self.agent.get_agent_by_id(agent_id)
    
    def create_agent(self, agent_data: Dict[str, Any]) -> int:
        """Create a new agent"""
        return self.agent.create_agent(agent_data)
    
    def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> int:
        """Update agent data"""
        return self.agent.update_agent(agent_id, update_data)
    
    def delete_agent(self, agent_id: str) -> int:
        """Delete an agent"""
        return self.agent.delete_agent(agent_id)
    
    def enable_agent(self, agent_id: str) -> bool:
        """Enable an agent"""
        return self.agent.enable_agent(agent_id)
    
    def disable_agent(self, agent_id: str) -> bool:
        """Disable an agent"""
        return self.agent.disable_agent(agent_id)
    
    def count_agents(self, enabled_only: bool = False) -> int:
        """Get count of agents"""
        return self.agent.count_agents(enabled_only)
    
    def get_agent_execution_stats(self, agent_id: str, since_time=None):
        """Get execution statistics for an agent"""
        return self.agent.get_agent_execution_stats(agent_id, since_time)
    
    def count_agent_nodes(self, start_time: Optional[str] = None) -> int:
        """Count agent executions, optionally since a given time"""
        return self.agent.count_agent_nodes(start_time)
    
    def get_agent_success_stats(self, start_time: str) -> Dict[str, int]:
        """Get success statistics for agent executions"""
        return self.agent.get_agent_success_stats(start_time)
    
    def count_agent_nodes_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count agent nodes within a time range"""
        return self.agent.count_agent_nodes_in_time_range(start_time, end_time)
    
    def get_agent_statistics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get agent statistics with execution counts"""
        return self.agent.get_agent_statistics(limit)
    
    def get_agent_executions(self, workflow_id: Optional[str] = None, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get agent executions, optionally filtered by workflow or agent"""
        return self.agent.get_agent_executions(workflow_id, agent_id)
    
    def get_agent_execution_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent execution"""
        return self.agent.get_agent_execution_by_id(execution_id)
    
    def create_agent_execution(self, execution_data: Dict[str, Any]) -> int:
        """Create a new agent execution record"""
        return self.agent.create_agent_execution(execution_data)
    
    def update_agent_execution(self, execution_id: str, update_data: Dict[str, Any]) -> int:
        """Update agent execution data"""
        return self.agent.update_agent_execution(execution_id, update_data)
    
    # ==================== Tool Operations (Delegate to ToolHandler) ====================
    
    def count_tool_nodes(self, start_time: Optional[str] = None) -> int:
        """Count tool executions, optionally since a given time"""
        return self.tool.count_tool_nodes(start_time)
    
    def get_tool_success_stats(self, start_time: str) -> Dict[str, int]:
        """Get success statistics for tool executions"""
        return self.tool.get_tool_success_stats(start_time)
    
    def count_tool_nodes_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count tool nodes within a time range"""
        return self.tool.count_tool_nodes_in_time_range(start_time, end_time)
    
    # ==================== DAG Operations (Delegate to DAGHandler) ====================
    
    def get_dag_statistics(self) -> List[Dict[str, Any]]:
        """Get per-DAG statistics"""
        return self.dag.get_dag_statistics()
    
    # ==================== HITL Operations (Delegate to HITLHandler) ====================
    
    def get_hitl_requests(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all HITL requests for a specific workflow"""
        return self.hitl.get_hitl_requests(workflow_id)
    
    def get_pending_hitl_requests(self) -> List[Dict[str, Any]]:
        """Get all pending HITL requests across all workflows"""
        return self.hitl.get_pending_hitl_requests()
    
    def get_hitl_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific HITL request"""
        return self.hitl.get_hitl_request_by_id(request_id)
    
    def create_hitl_request(self, request_data: Dict[str, Any]) -> int:
        """Create a new HITL request"""
        return self.hitl.create_hitl_request(request_data)
    
    def update_hitl_request(self, request_id: str, update_data: Dict[str, Any]) -> int:
        """Update HITL request data"""
        return self.hitl.update_hitl_request(request_id, update_data)
    
    def count_pending_hitl_requests(self) -> int:
        """Count pending HITL requests"""
        return self.hitl.count_pending_hitl_requests()
    
    # ==================== Planner Operations (Delegate to PlannerHandler) ====================
    
    def count_plans(self, start_time: Optional[str] = None) -> int:
        """Count plans, optionally since a given time"""
        return self.planner.count_plans(start_time)
    
    def get_plan_approval_stats(self, start_time: str) -> Dict[str, int]:
        """Get approval statistics for plans"""
        return self.planner.get_plan_approval_stats(start_time)
    
    def count_planner_conversations(self, start_time: str) -> int:
        """Count planner conversations since a given time"""
        return self.planner.count_planner_conversations(start_time)
    
    def count_plans_by_status(self, status: str) -> int:
        """Count plans with a specific status"""
        return self.planner.count_plans_by_status(status)
    
    def count_plans_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count plans within a time range"""
        return self.planner.count_plans_in_time_range(start_time, end_time)
    
    def count_planner_conversations_in_time_range(self, start_time: str, end_time: str) -> int:
        """Count planner conversations within a time range"""
        return self.planner.count_planner_conversations_in_time_range(start_time, end_time)
    
    def get_plan_status_distribution(self) -> Dict[str, int]:
        """Get distribution of plans by status"""
        return self.planner.get_plan_status_distribution()
    
    def get_top_plan_users(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top users by plan count"""
        return self.planner.get_top_plan_users(limit)
    
    def get_recent_plans_with_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent plans with user information"""
        return self.planner.get_recent_plans_with_users(limit)
    
    def count_lgraph_plans(self, since_time: Optional[str] = None) -> int:
        """Count LangGraph plans, optionally since a given time"""
        return self.planner.count_lgraph_plans(since_time)
    
    def count_lgraph_plans_in_time_range(self, start_time, end_time):
        """Count LangGraph plans within a time range"""
        return self.planner.count_lgraph_plans_in_time_range(start_time, end_time)
    
    def count_lgraph_conversations(self, since_time: Optional[str] = None) -> int:
        """Count LangGraph conversations, optionally since a given time"""
        return self.planner.count_lgraph_conversations(since_time)
    
    def count_lgraph_conversations_in_time_range(self, start_time, end_time):
        """Count LangGraph conversations within a time range"""
        return self.planner.count_lgraph_conversations_in_time_range(start_time, end_time)
    
    def get_lgraph_plan_status_distribution(self):
        """Get distribution of LangGraph plans by status"""
        return self.planner.get_lgraph_plan_status_distribution()
    
    def get_recent_lgraph_plans_with_users(self, limit=10):
        """Get recent LangGraph plans with user information"""
        return self.planner.get_recent_lgraph_plans_with_users(limit)
    
    def get_top_plan_users_combined(self, limit=5):
        """Get top users by plan count (combines regular and LangGraph plans)"""
        return self.planner.get_top_plan_users_combined(limit)


# Global database instance
_handler_instance: Optional[DatabaseCallHandler] = None

def get_database_handler():
    """Get or create the global database handler instance"""
    global _handler_instance
    if _handler_instance is None:
        # Default to SQLite, can be configured
        _handler_instance = DatabaseCallHandler(get_db())
    
    return _handler_instance
