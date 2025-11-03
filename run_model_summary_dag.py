#!/usr/bin/env python3
"""
Run Dynamic Model Documentation Summary DAG
Executes the model_summary_dag programmatically using Claude 3.5
"""

import sys
import os
import uuid
import json
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("DYNAMIC MODEL DOCUMENTATION SUMMARY DAG - CLAUDE 3.5")
print("=" * 80)

# Import required modules
print("\n1. Importing required modules...")
try:
    from db.database_call_handler import get_database_handler
    from core.user_registry import UserRegistry
    from workflows.dag.dag_registry import DAGRegistry
    from workflows.dag.orchestrator import WorkflowOrchestrator
    from agents.agent_registry import AgentRegistry
    from tools.tool_registry import ToolRegistry

    print("   ✓ All modules imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import modules: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Initialize components
print("\n2. Initializing components...")
try:
    # Initialize database with correct path
    from db.database import initialize_db
    project_root = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_root, 'data', 'abhikarta.db')

    print(f"   Using database: {db_path}")
    db = initialize_db(db_type='sqlite', db_path=db_path)

    db_handler = get_database_handler()
    user_registry = UserRegistry()  # Singleton, no arguments
    agent_registry = AgentRegistry()  # Singleton, no arguments
    tool_registry = ToolRegistry()  # Singleton, no arguments
    dag_registry = DAGRegistry()  # Singleton, no arguments
    orchestrator = WorkflowOrchestrator()  # Singleton, no arguments

    print("   ✓ All components initialized")
except Exception as e:
    print(f"   ✗ Failed to initialize components: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Get user
print("\n3. Getting user...")
try:
    users = db_handler.db.fetchall("SELECT user_id, username FROM users LIMIT 1")
    if not users:
        print("   ✗ No users found!")
        sys.exit(1)

    user_id = users[0]['user_id']
    username = users[0]['username']
    user = user_registry.get_user(user_id)

    print(f"   ✓ Using user: {username} ({user_id})")
except Exception as e:
    print(f"   ✗ Failed to get user: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Load DAG
print("\n4. Loading DAG 'model_summary_dag'...")
try:
    dag_id = 'model_summary_dag'
    dag_config = dag_registry.get_dag_config(dag_id)

    if not dag_config:
        print(f"   ✗ DAG '{dag_id}' not found!")
        sys.exit(1)

    print(f"   ✓ DAG loaded: {dag_config['name']}")
    print(f"      Description: {dag_config['description']}")
    print(f"      Nodes: {len(dag_config['nodes'])}")

    # Display nodes
    for node in dag_config['nodes']:
        print(f"        - {node['node_id']} ({node['node_type']})")

except Exception as e:
    print(f"   ✗ Failed to load DAG: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create graph from DAG
print("\n5. Creating graph from DAG...")
try:
    graph = dag_registry.create_graph_from_dag(dag_id)

    if not graph:
        print("   ✗ Failed to create graph from DAG")
        sys.exit(1)

    print(f"   ✓ Graph created successfully")
    print(f"      Graph ID: {graph.graph_id}")
    print(f"      Nodes: {len(graph.nodes)}")
    print(f"      Start nodes: {graph.start_nodes}")

except Exception as e:
    print(f"   ✗ Failed to create graph: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Set parameters and create session
print("\n6. Setting workflow parameters and creating session...")
try:
    # Set the codebase path parameter for the model summary
    codebase_path = os.path.dirname(os.path.abspath(__file__))  # Current project root

    parameters = {
        'codebase_path': codebase_path
    }

    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    # Store parameters in session metadata
    session_metadata = {
        'dag_id': dag_id,
        'parameters': parameters
    }

    db_handler.db.insert('sessions', {
        'session_id': session_id,
        'user_id': user_id,
        'status': 'active',
        'created_at': now,
        'updated_at': now,
        'metadata': json.dumps(session_metadata)
    })

    print(f"   ✓ Session created: {session_id}")
    print(f"   ✓ Parameters set:")
    print(f"      codebase_path: {codebase_path}")

except Exception as e:
    print(f"   ✗ Failed to create session with parameters: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Start workflow
print("\n7. Starting workflow execution with Claude 3.5...")
try:
    workflow_id = orchestrator.start_workflow(dag_id, session_id, user_id, graph)

    print(f"   ✓ Workflow started successfully!")
    print(f"      Workflow ID: {workflow_id}")
    print(f"      Session ID: {session_id}")
    print(f"      Using Claude 3.5 Sonnet for LLM generation")

except Exception as e:
    print(f"   ✗ Failed to start workflow: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Wait for workflow to complete (check status)
print("\n8. Monitoring workflow status...")
import time

max_wait_time = 300  # 5 minutes max for model summary
check_interval = 5   # Check every 5 seconds
elapsed = 0

try:
    while elapsed < max_wait_time:
        # Get workflow status
        workflow = db_handler.db.fetchone(
            "SELECT * FROM workflows WHERE workflow_id = ?",
            (workflow_id,)
        )

        if not workflow:
            print(f"   ✗ Workflow not found in database")
            break

        status = workflow['status']
        print(f"   Status: {status} (elapsed: {elapsed}s)")

        if status == 'completed':
            print(f"\n   ✓ Workflow completed successfully!")

            # Display results
            results = workflow.get('results')
            if results:
                results_data = json.loads(results) if isinstance(results, str) else results
                print(f"\n   Results:")
                print(f"      {json.dumps(results_data, indent=6)}")

            break
        elif status == 'failed':
            print(f"\n   ✗ Workflow failed!")

            # Display error
            error = workflow.get('error')
            if error:
                print(f"\n   Error:")
                print(f"      {error}")

            break
        elif status in ['pending', 'running', 'active']:
            time.sleep(check_interval)
            elapsed += check_interval
        else:
            print(f"\n   ? Unknown status: {status}")
            break

    if elapsed >= max_wait_time:
        print(f"\n   ⚠ Workflow still running after {max_wait_time}s")
        print(f"      Final status: {status}")
        print(f"      Check workflow status manually: {workflow_id}")

except Exception as e:
    print(f"   ✗ Error monitoring workflow: {e}")
    import traceback
    traceback.print_exc()

# Check if output files were created
print("\n9. Checking output files...")
try:
    # Common output locations for model summary
    possible_outputs = [
        "/tmp/model_summary.md",
        "/tmp/model_documentation.md",
        "/tmp/abhikarta_model_summary.md",
        f"{codebase_path}/MODEL_SUMMARY.md",
        f"{codebase_path}/docs/MODEL_DOCUMENTATION.md"
    ]

    found_files = []
    for output_file in possible_outputs:
        if os.path.exists(output_file):
            found_files.append(output_file)

    if found_files:
        print(f"   ✓ Found {len(found_files)} output file(s):")
        for file_path in found_files:
            print(f"      - {file_path}")
            file_size = os.path.getsize(file_path)
            print(f"        Size: {file_size} bytes")

            # Show first few lines of the file
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()[:10]  # First 10 lines
                print(f"        Preview:")
                for i, line in enumerate(lines, 1):
                    print(f"          {i:2d}: {line.rstrip()}")
                if len(lines) == 10:
                    print("          ... (truncated)")
            except Exception as e:
                print(f"        Error reading file: {e}")
    else:
        print("   ⚠ No output files found in expected locations")
        print("      Checking workflow metadata for output paths...")

        # Check workflow metadata for output paths
        try:
            workflow_meta = db_handler.db.fetchone(
                "SELECT metadata FROM workflows WHERE workflow_id = ?",
                (workflow_id,)
            )
            if workflow_meta and workflow_meta.get('metadata'):
                meta_data = json.loads(workflow_meta['metadata'])
                if 'output_files' in meta_data:
                    print("      Output files from metadata:")
                    for file_path in meta_data['output_files']:
                        print(f"        - {file_path}")
        except:
            pass

except Exception as e:
    print(f"   ✗ Error checking output files: {e}")

# Summary
print("\n" + "=" * 80)
print("MODEL SUMMARY DAG EXECUTION SUMMARY")
print("=" * 80)
print(f"\nWorkflow ID: {workflow_id}")
print(f"Session ID: {session_id}")
print(f"DAG ID: {dag_id}")
print(f"LLM Model: Claude 3.5 Sonnet (claude-sonnet-4.5)")
print(f"\nTo view workflow details:")
print(f"  - Check database: SELECT * FROM workflows WHERE workflow_id = '{workflow_id}'")
print(f"  - Check web UI: http://localhost:5001/workflow/{workflow_id}")
print(f"  - Check session: SELECT * FROM sessions WHERE session_id = '{session_id}'")
print("=" * 80)

print("\n🎉 Dynamic Model Documentation Summary completed with Claude 3.5!")
print("📄 Check the output files above for your generated documentation.")

