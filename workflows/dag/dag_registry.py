"""
DAG Registry
Manages DAG definitions and templates

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import json
import os
from typing import Dict, List, Optional
from threading import Lock
from graph.graph import Graph, Node, Edge


class DAGRegistry:
    """Singleton registry for DAG management"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DAGRegistry, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._dags: Dict[str, Dict] = {}
        self._config_dir = 'config/dags'
        self._initialized = True
        self.load_dags()
    
    def load_dags(self) -> None:
        """Load DAG definitions from configuration directory"""
        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir, exist_ok=True)
            return
        
        self._dags.clear()
        
        for filename in os.listdir(self._config_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self._config_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        dag_config = json.load(f)
                    
                    dag_id = dag_config.get('dag_id')
                    if dag_id:
                        self._dags[dag_id] = dag_config
                
                except Exception as e:
                    print(f"Error reading DAG config {filename}: {e}")
    
    def get_dag_config(self, dag_id: str) -> Optional[Dict]:
        """Get DAG configuration"""
        return self._dags.get(dag_id)
    
    def get_all_dags(self) -> List[Dict]:
        """Get all DAG configurations"""
        return list(self._dags.values())
    
    def create_graph_from_dag(self, dag_id: str) -> Optional[Graph]:
        """Create a Graph instance from DAG configuration"""
        dag_config = self._dags.get(dag_id)
        if not dag_config:
            return None
        
        graph = Graph(
            graph_id=dag_id,
            name=dag_config.get('name', dag_id),
            description=dag_config.get('description', '')
        )
        
        # Add nodes
        for node_config in dag_config.get('nodes', []):
            node = Node(
                node_id=node_config['node_id'],
                node_type=node_config.get('node_type', 'agent'),
                agent_id=node_config.get('agent_id'),
                config=node_config.get('config', {})
            )
            graph.add_node(node)
        
        # Add edges based on dependencies
        for node_config in dag_config.get('nodes', []):
            node_id = node_config['node_id']
            for dep in node_config.get('dependencies', []):
                edge = Edge(from_node=dep, to_node=node_id)
                graph.add_edge(edge)
        
        # Set start nodes
        graph.start_nodes = dag_config.get('start_nodes', [])
        
        return graph
    
    def reload(self) -> None:
        """Reload all DAGs from configuration"""
        self.load_dags()
    
    def list_dags(self) -> List[Dict]:
        """List all DAGs with basic info"""
        return [
            {
                'dag_id': dag.get('dag_id'),
                'name': dag.get('name', dag.get('dag_id')),
                'description': dag.get('description', ''),
                'node_count': len(dag.get('nodes', []))
            }
            for dag in self._dags.values()
        ]
    
    def add_dag(self, dag_config: Dict) -> bool:
        """Add a new DAG configuration"""
        dag_id = dag_config.get('dag_id')
        if not dag_id:
            return False
        
        self._dags[dag_id] = dag_config
        
        # Save to file
        filepath = os.path.join(self._config_dir, f"{dag_id}.json")
        os.makedirs(self._config_dir, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(dag_config, f, indent=2)
        
        return True
    
    def update_dag(self, dag_id: str, dag_config: Dict) -> bool:
        """Update an existing DAG configuration"""
        if dag_id not in self._dags:
            return False
        
        self._dags[dag_id] = dag_config
        
        # Update file
        filepath = os.path.join(self._config_dir, f"{dag_id}.json")
        with open(filepath, 'w') as f:
            json.dump(dag_config, f, indent=2)
        
        return True
    
    def delete_dag(self, dag_id: str) -> bool:
        """Delete a DAG configuration"""
        if dag_id not in self._dags:
            return False
        
        del self._dags[dag_id]
        
        # Delete file
        filepath = os.path.join(self._config_dir, f"{dag_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return True
