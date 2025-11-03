"""
Monitoring Database Handler
Aggregates monitoring statistics from all specialized handlers

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from db.database_handler_base import DatabaseHandlerBase


class MonitoringHandler(DatabaseHandlerBase):
    """Handler for monitoring and aggregating statistics across all domains"""
    
    def __init__(self, database, workflow_handler, user_handler, agent_handler, 
                 tool_handler, dag_handler, planner_handler, hitl_handler):
        """
        Initialize monitoring handler with all specialized handlers
        
        Args:
            database: Database instance
            workflow_handler: WorkflowHandler instance
            user_handler: UserHandler instance
            agent_handler: AgentHandler instance
            tool_handler: ToolHandler instance
            dag_handler: DAGHandler instance
            planner_handler: PlannerHandler instance
            hitl_handler: HITLHandler instance
        """
        super().__init__(database)
        self.workflow_handler = workflow_handler
        self.user_handler = user_handler
        self.agent_handler = agent_handler
        self.tool_handler = tool_handler
        self.dag_handler = dag_handler
        self.planner_handler = planner_handler
        self.hitl_handler = hitl_handler
