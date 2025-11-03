#!/usr/bin/env python3
"""
Minimal script to start the Dynamic Model Documentation Summary DAG with Claude 3.5
"""

import sys
import os
import uuid
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Starting Dynamic Model Documentation Summary DAG with Claude 3.5...")

# Quick setup
from db.database import initialize_db
from db.database_call_handler import get_database_handler
from core.user_registry import UserRegistry
from workflows.dag.dag_registry import DAGRegistry
from workflows.dag.orchestrator import WorkflowOrchestrator

db = initialize_db(db_type='sqlite', db_path='data/abhikarta.db')
db_handler = get_database_handler()
user_registry = UserRegistry()
dag_registry = DAGRegistry()
orchestrator = WorkflowOrchestrator()

# Get user
users = db_handler.db.fetchall("SELECT user_id, username FROM users LIMIT 1")
user_id = users[0]['user_id']

# Load and create graph
dag_id = 'model_summary_dag'
dag_config = dag_registry.get_dag_config(dag_id)
graph = dag_registry.create_graph_from_dag(dag_id)

# Create session with parameters
session_id = str(uuid.uuid4())
codebase_path = os.path.dirname(os.path.abspath(__file__))
session_metadata = {
    'dag_id': dag_id,
    'parameters': {'codebase_path': codebase_path}
}

db_handler.db.insert('sessions', {
    'session_id': session_id,
    'user_id': user_id,
    'status': 'active',
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat(),
    'metadata': json.dumps(session_metadata)
})

# Start workflow
workflow_id = orchestrator.start_workflow(dag_id, session_id, user_id, graph)

print(f"✅ Workflow started successfully!")
print(f"   Workflow ID: {workflow_id}")
print(f"   Session ID: {session_id}")
print(f"   DAG: {dag_config['name']}")
print(f"   LLM: Claude 3.5 Sonnet")
print(f"   Codebase: {codebase_path}")
print()
print("📊 Monitor progress at: http://localhost:5001/workflow/" + workflow_id)
print("🔍 Check status with: python3 check_workflow_status.py " + workflow_id)
