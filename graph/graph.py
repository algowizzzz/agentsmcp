"""
Custom Graph Implementation for DAG workflows
Provides Node, Edge, and Graph classes without using NetworkX

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import List, Dict, Set, Optional, Any
from enum import Enum
import json


class NodeStatus(Enum):
    """Node execution status"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Node:
    """Represents a node in the DAG"""
    
    def __init__(self, node_id: str, node_type: str, agent_id: Optional[str] = None, 
                 config: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.node_type = node_type  # 'agent', 'human_in_loop', 'decision', etc.
        self.agent_id = agent_id
        self.config = config or {}
        self.status = NodeStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    def add_dependency(self, node_id: str) -> None:
        """Add a dependency node"""
        self.dependencies.add(node_id)
    
    def add_dependent(self, node_id: str) -> None:
        """Add a dependent node"""
        self.dependents.add(node_id)
    
    def is_ready(self, completed_nodes: Set[str]) -> bool:
        """Check if node is ready to execute"""
        return self.dependencies.issubset(completed_nodes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary"""
        return {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'agent_id': self.agent_id,
            'config': self.config,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'dependencies': list(self.dependencies),
            'dependents': list(self.dependents),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create node from dictionary"""
        node = cls(
            node_id=data['node_id'],
            node_type=data['node_type'],
            agent_id=data.get('agent_id'),
            config=data.get('config', {})
        )
        node.status = NodeStatus(data.get('status', 'pending'))
        node.result = data.get('result')
        node.error = data.get('error')
        node.dependencies = set(data.get('dependencies', []))
        node.dependents = set(data.get('dependents', []))
        node.metadata = data.get('metadata', {})
        return node


class Edge:
    """Represents an edge in the DAG"""
    
    def __init__(self, from_node: str, to_node: str, condition: Optional[str] = None):
        self.from_node = from_node
        self.to_node = to_node
        self.condition = condition  # Optional condition for conditional edges
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary"""
        return {
            'from_node': self.from_node,
            'to_node': self.to_node,
            'condition': self.condition,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """Create edge from dictionary"""
        edge = cls(
            from_node=data['from_node'],
            to_node=data['to_node'],
            condition=data.get('condition')
        )
        edge.metadata = data.get('metadata', {})
        return edge


class Graph:
    """Represents a Directed Acyclic Graph for workflows"""
    
    def __init__(self, graph_id: str, name: str = "", description: str = ""):
        self.graph_id = graph_id
        self.name = name
        self.description = description
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.start_nodes: List[str] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_node(self, node: Node) -> None:
        """Add a node to the graph"""
        self.nodes[node.node_id] = node
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph"""
        self.edges.append(edge)
        
        # Update node dependencies
        if edge.from_node in self.nodes and edge.to_node in self.nodes:
            self.nodes[edge.to_node].add_dependency(edge.from_node)
            self.nodes[edge.from_node].add_dependent(edge.to_node)
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_start_nodes(self) -> List[Node]:
        """Get all start nodes (nodes with no dependencies)"""
        if self.start_nodes:
            return [self.nodes[nid] for nid in self.start_nodes if nid in self.nodes]
        return [node for node in self.nodes.values() if not node.dependencies]
    
    def get_ready_nodes(self, completed_nodes: Set[str]) -> List[Node]:
        """Get all nodes that are ready to execute"""
        ready = []
        for node in self.nodes.values():
            if node.status == NodeStatus.PENDING and node.is_ready(completed_nodes):
                ready.append(node)
        return ready
    
    def get_successors(self, node_id: str) -> List[Node]:
        """Get all successor nodes"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[dep] for dep in node.dependents if dep in self.nodes]
    
    def get_predecessors(self, node_id: str) -> List[Node]:
        """Get all predecessor nodes"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[dep] for dep in node.dependencies if dep in self.nodes]
    
    def has_cycle(self) -> bool:
        """Check if graph has a cycle using DFS"""
        visited = set()
        rec_stack = set()
        
        def has_cycle_util(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            node = self.nodes.get(node_id)
            if node:
                for dependent in node.dependents:
                    if dependent not in visited:
                        if has_cycle_util(dependent):
                            return True
                    elif dependent in rec_stack:
                        return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle_util(node_id):
                    return True
        
        return False
    
    def topological_sort(self) -> List[str]:
        """Return topologically sorted node IDs"""
        in_degree = {node_id: len(node.dependencies) for node_id, node in self.nodes.items()}
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        sorted_nodes = []
        
        while queue:
            node_id = queue.pop(0)
            sorted_nodes.append(node_id)
            
            node = self.nodes[node_id]
            for dependent in node.dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        return sorted_nodes if len(sorted_nodes) == len(self.nodes) else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary"""
        return {
            'graph_id': self.graph_id,
            'name': self.name,
            'description': self.description,
            'nodes': {nid: node.to_dict() for nid, node in self.nodes.items()},
            'edges': [edge.to_dict() for edge in self.edges],
            'start_nodes': self.start_nodes,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Convert graph to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Graph':
        """Create graph from dictionary"""
        graph = cls(
            graph_id=data['graph_id'],
            name=data.get('name', ''),
            description=data.get('description', '')
        )
        
        # Add nodes
        for node_data in data.get('nodes', {}).values():
            graph.add_node(Node.from_dict(node_data))
        
        # Add edges
        for edge_data in data.get('edges', []):
            graph.add_edge(Edge.from_dict(edge_data))
        
        graph.start_nodes = data.get('start_nodes', [])
        graph.metadata = data.get('metadata', {})
        
        return graph
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Graph':
        """Create graph from JSON string"""
        return cls.from_dict(json.loads(json_str))
