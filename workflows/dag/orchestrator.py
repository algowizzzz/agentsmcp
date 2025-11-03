"""
Workflow Orchestrator
Executes DAG-based workflows with support for parallel execution and HITL

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
from threading import Thread, Lock
from graph.graph import Graph, Node, NodeStatus
from db.database import get_db
from agents.agent_registry import AgentRegistry
from tools.tool_registry import ToolRegistry


class WorkflowOrchestrator:
    """Orchestrates workflow execution"""
    
    def __init__(self):
        self.agent_registry = AgentRegistry()
        self.tool_registry = ToolRegistry()
        self.db = get_db()
        self._active_workflows: Dict[str, Graph] = {}
        self._lock = Lock()
    
    def start_workflow(self, dag_id: str, session_id: str, user_id: str, 
                       graph: Graph) -> str:
        """Start a new workflow execution"""
        workflow_id = str(uuid.uuid4())
        
        # Save workflow to database
        self.db.insert('workflows', {
            'workflow_id': workflow_id,
            'dag_id': dag_id,
            'session_id': session_id,
            'name': graph.name,
            'description': graph.description,
            'status': 'running',
            'created_at': datetime.now().isoformat(),
            'started_at': datetime.now().isoformat(),
            'created_by': user_id,
            'graph_json': graph.to_json()
        })
        
        # Save workflow nodes
        for node_id, node in graph.nodes.items():
            self.db.insert('workflow_nodes', {
                'workflow_id': workflow_id,
                'node_id': node_id,
                'node_type': node.node_type,
                'agent_id': node.agent_id,
                'status': node.status.value,
                'config': json.dumps(node.config)
            })
        
        # Log event
        self._log_workflow_event(workflow_id, 'workflow_started', {
            'dag_id': dag_id,
            'user_id': user_id
        })
        
        # Store in active workflows
        with self._lock:
            self._active_workflows[workflow_id] = graph
        
        # Start execution in background thread
        thread = Thread(target=self._execute_workflow, args=(workflow_id, graph))
        thread.daemon = True
        thread.start()
        
        return workflow_id
    
    def _execute_workflow(self, workflow_id: str, graph: Graph) -> None:
        """Execute workflow in background"""
        try:
            completed_nodes: Set[str] = set()

            while True:
                # Get ready nodes
                ready_nodes = graph.get_ready_nodes(completed_nodes)

                if not ready_nodes:
                    # Check if all nodes are completed
                    all_completed = all(
                        node.status in [NodeStatus.COMPLETED, NodeStatus.SKIPPED, NodeStatus.FAILED]
                        for node in graph.nodes.values()
                    )
                    
                    if all_completed:
                        self._complete_workflow(workflow_id, graph)
                        break
                    
                    # Check for HITL nodes
                    hitl_nodes = [
                        node for node in graph.nodes.values()
                        if node.node_type == 'human_in_loop' and node.status == NodeStatus.PENDING
                        and node.is_ready(completed_nodes)
                    ]
                    
                    if hitl_nodes:
                        # Wait for HITL approval
                        for hitl_node in hitl_nodes:
                            self._handle_hitl_node(workflow_id, hitl_node)
                        break  # Exit and wait for HITL response
                    else:
                        break  # No more work to do
                
                # Execute ready nodes (can be done in parallel)
                for node in ready_nodes:
                    self._execute_node(workflow_id, graph, node)
                    completed_nodes.add(node.node_id)
        
        except Exception as e:
            self._fail_workflow(workflow_id, str(e))
        
        finally:
            # Remove from active workflows if completed or failed
            status = self.db.fetchone(
                "SELECT status FROM workflows WHERE workflow_id = ?",
                (workflow_id,)
            )
            if status and status['status'] in ['completed', 'failed']:
                with self._lock:
                    self._active_workflows.pop(workflow_id, None)
    
    def _execute_node(self, workflow_id: str, graph: Graph, node: Node) -> None:
        """Execute a single node"""
        try:
            node.status = NodeStatus.RUNNING
            self._update_node_status(workflow_id, node.node_id, 'running', 
                                    datetime.now().isoformat())
            
            self._log_workflow_event(workflow_id, 'node_started', {
                'node_id': node.node_id,
                'node_type': node.node_type
            })
            
            # Execute based on node type
            if node.node_type == 'agent':
                result = self._execute_agent_node(node)
            elif node.node_type == 'tool':
                result = self._execute_tool_node(workflow_id, graph, node)
            else:
                result = {'success': False, 'error': f'Unknown node type: {node.node_type}'}
            
            if result.get('success'):
                node.status = NodeStatus.COMPLETED
                node.result = result.get('result')
                
                self._update_node_status(
                    workflow_id, node.node_id, 'completed',
                    None, datetime.now().isoformat(),
                    json.dumps(node.result)
                )
                
                self._log_workflow_event(workflow_id, 'node_completed', {
                    'node_id': node.node_id,
                    'result': node.result
                })
            else:
                node.status = NodeStatus.FAILED
                node.error = result.get('error')
                
                self._update_node_status(
                    workflow_id, node.node_id, 'failed',
                    None, datetime.now().isoformat(),
                    None, result.get('error')
                )
                
                self._log_workflow_event(workflow_id, 'node_failed', {
                    'node_id': node.node_id,
                    'error': node.error
                })
        
        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            
            self._update_node_status(
                workflow_id, node.node_id, 'failed',
                None, datetime.now().isoformat(),
                None, str(e)
            )
            
            self._log_workflow_event(workflow_id, 'node_failed', {
                'node_id': node.node_id,
                'error': str(e)
            })
    
    def _execute_agent_node(self, node: Node) -> Dict[str, Any]:
        """Execute an agent node"""
        if not node.agent_id:
            return {'success': False, 'error': 'No agent_id specified'}
        
        return self.agent_registry.execute_agent(node.agent_id, node.config.get('input', {}))
    
    def _substitute_node_results(self, input_config: Dict[str, Any], graph: Graph) -> Dict[str, Any]:
        """Substitute node result placeholders in input config"""
        import copy
        import re
        
        # Deep copy to avoid modifying original
        result = copy.deepcopy(input_config)
        
        # Convert to JSON string for easier substitution
        result_str = json.dumps(result)
        
        # Find all placeholders like {node_id.result} or {node_id.result.key}
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\.(result(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\}'
        matches = re.findall(pattern, result_str)
        
        for node_id, result_path in matches:
            # Get the referenced node
            if node_id in graph.nodes:
                ref_node = graph.nodes[node_id]
                
                # Get the node's result
                if ref_node.result is not None:
                    value = ref_node.result
                    
                    # Navigate nested result path if specified (e.g., result.files)
                    path_parts = result_path.split('.')[1:]  # Skip 'result'
                    for part in path_parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            # Path not found, keep placeholder
                            value = None
                            break
                    
                    if value is not None:
                        # Substitute the placeholder with the actual value
                        placeholder = f"{{{node_id}.{result_path}}}"
                        # Always JSON-encode the value for proper substitution
                        value_json = json.dumps(value)
                        # Replace quoted placeholder with the JSON value
                        result_str = result_str.replace(f'"{placeholder}"', value_json)
                        # Also handle unquoted placeholder (for non-string contexts)
                        if not isinstance(value, str):
                            result_str = result_str.replace(placeholder, value_json)
        
        # Convert back to dict
        try:
            return json.loads(result_str)
        except json.JSONDecodeError:
            # If substitution resulted in invalid JSON, return original
            return result
    
    def _execute_tool_node(self, workflow_id: str, graph: Graph, node: Node) -> Dict[str, Any]:
        """Execute a tool node"""
        tool_name = node.config.get('tool_name')
        if not tool_name:
            return {'success': False, 'error': 'No tool_name specified'}
        
        # Get input config and substitute node results if graph is provided
        input_config = node.config.get('input', {})
        if graph:
            input_config = self._substitute_node_results(input_config, graph)

        # Inject debug context so tools can emit artifacts
        try:
            debug_dir = f"/tmp/workflow_artifacts/{workflow_id}/{node.node_id}"
        except Exception:
            debug_dir = None
        # Safe to include even if tools ignore
        if isinstance(input_config, dict):
            input_config.setdefault('workflow_id', workflow_id)
            input_config.setdefault('node_id', node.node_id)
            if debug_dir:
                input_config.setdefault('debug_dir', debug_dir)
        
        return self.tool_registry.execute_tool(tool_name, **input_config)
    
    def _handle_hitl_node(self, workflow_id: str, node: Node) -> None:
        """Handle human-in-the-loop node"""
        request_id = str(uuid.uuid4())
        
        node.status = NodeStatus.RUNNING
        self._update_node_status(workflow_id, node.node_id, 'waiting_hitl', 
                                datetime.now().isoformat())
        
        # Create HITL request
        self.db.insert('hitl_requests', {
            'request_id': request_id,
            'workflow_id': workflow_id,
            'node_id': node.node_id,
            'message': node.config.get('message', 'Approval required'),
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })
        
        self._log_workflow_event(workflow_id, 'hitl_requested', {
            'node_id': node.node_id,
            'request_id': request_id
        })
    
    def approve_hitl(self, workflow_id: str, request_id: str, user_id: str, 
                     response: str = 'approved') -> bool:
        """Approve HITL request"""
        # Update HITL request
        self.db.update(
            'hitl_requests',
            {
                'status': 'approved',
                'responded_at': datetime.now().isoformat(),
                'responded_by': user_id,
                'response': response
            },
            'request_id = ?',
            (request_id,)
        )
        
        # Get workflow and node
        request = self.db.fetchone(
            "SELECT * FROM hitl_requests WHERE request_id = ?",
            (request_id,)
        )
        
        if not request:
            return False
        
        node_id = request['node_id']
        
        # Update node status
        self._update_node_status(workflow_id, node_id, 'completed', 
                                None, datetime.now().isoformat(),
                                json.dumps({'approved': True, 'response': response}))
        
        self._log_workflow_event(workflow_id, 'hitl_approved', {
            'node_id': node_id,
            'request_id': request_id,
            'user_id': user_id
        })
        
        # Resume workflow execution
        with self._lock:
            graph = self._active_workflows.get(workflow_id)
            if graph:
                node = graph.get_node(node_id)
                if node:
                    node.status = NodeStatus.COMPLETED
                    node.result = {'approved': True, 'response': response}
                
                # Continue execution
                thread = Thread(target=self._execute_workflow, args=(workflow_id, graph))
                thread.daemon = True
                thread.start()
        
        return True
    
    def reject_hitl(self, workflow_id: str, request_id: str, user_id: str, 
                    reason: str = 'rejected') -> bool:
        """Reject HITL request"""
        # Update HITL request
        self.db.update(
            'hitl_requests',
            {
                'status': 'rejected',
                'responded_at': datetime.now().isoformat(),
                'responded_by': user_id,
                'response': reason
            },
            'request_id = ?',
            (request_id,)
        )
        
        # Fail workflow
        self._fail_workflow(workflow_id, f'HITL rejected: {reason}')
        
        self._log_workflow_event(workflow_id, 'hitl_rejected', {
            'request_id': request_id,
            'user_id': user_id,
            'reason': reason
        })
        
        return True
    
    def _complete_workflow(self, workflow_id: str, graph: Graph) -> None:
        """Mark workflow as completed"""
        self.db.update(
            'workflows',
            {
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'result': json.dumps({'success': True})
            },
            'workflow_id = ?',
            (workflow_id,)
        )
        
        self._log_workflow_event(workflow_id, 'workflow_completed', {})
    
    def _fail_workflow(self, workflow_id: str, error: str) -> None:
        """Mark workflow as failed"""
        self.db.update(
            'workflows',
            {
                'status': 'failed',
                'completed_at': datetime.now().isoformat(),
                'error': error
            },
            'workflow_id = ?',
            (workflow_id,)
        )
        
        self._log_workflow_event(workflow_id, 'workflow_failed', {'error': error})
    
    def _update_node_status(self, workflow_id: str, node_id: str, status: str,
                           started_at: Optional[str] = None,
                           completed_at: Optional[str] = None,
                           result: Optional[str] = None,
                           error: Optional[str] = None) -> None:
        """Update node status in database"""
        update_data = {'status': status}
        if started_at:
            update_data['started_at'] = started_at
        if completed_at:
            update_data['completed_at'] = completed_at
        if result:
            update_data['result'] = result
        if error:
            update_data['error'] = error
        
        self.db.update(
            'workflow_nodes',
            update_data,
            'workflow_id = ? AND node_id = ?',
            (workflow_id, node_id)
        )
    
    def _log_workflow_event(self, workflow_id: str, event_type: str, 
                           event_data: Dict[str, Any]) -> None:
        """Log workflow event"""
        self.db.insert('workflow_events', {
            'workflow_id': workflow_id,
            'event_type': event_type,
            'event_data': json.dumps(event_data),
            'created_at': datetime.now().isoformat()
        })
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        workflow = self.db.fetchone(
            "SELECT * FROM workflows WHERE workflow_id = ?",
            (workflow_id,)
        )
        
        if not workflow:
            return None
        
        nodes = self.db.fetchall(
            "SELECT * FROM workflow_nodes WHERE workflow_id = ?",
            (workflow_id,)
        )
        
        return {
            'workflow': workflow,
            'nodes': nodes
        }
    
    def get_pending_hitl_requests(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending HITL requests"""
        if workflow_id:
            return self.db.fetchall(
                "SELECT * FROM hitl_requests WHERE workflow_id = ? AND status = 'pending'",
                (workflow_id,)
            )
        else:
            return self.db.fetchall(
                "SELECT * FROM hitl_requests WHERE status = 'pending'"
            )
