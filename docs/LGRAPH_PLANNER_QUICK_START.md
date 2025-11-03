# LangGraph Planner - Quick Start Guide

## © 2025-2030 Ashutosh Sinha


## Installation & Setup

### 1. Install Dependencies

```bash
pip install langgraph langchain langchain-core --break-system-packages
```

### 2. Initialize Database

```python
from lgraph_planner import initialize_lgraph_tables

# Run once to create necessary tables
initialize_lgraph_tables()
```

### 3. Create Planner Instance

```python
from lgraph_planner import LangGraphPlanner

# For production with Claude
planner = LangGraphPlanner(llm_provider='anthropic')

# For testing
planner = LangGraphPlanner(llm_provider='mock')
```

## 5-Minute Tutorial

### Step 1: Create Your First Plan

```python
from lgraph_planner import LangGraphPlanner, initialize_lgraph_tables

# Setup
initialize_lgraph_tables()
planner = LangGraphPlanner(llm_provider='anthropic')

# Create plan
result = planner.create_plan(
    user_id="demo_user",
    session_id="demo_session",
    user_request="Fetch current stock price for AAPL and analyze the trend"
)

print(f"✅ Plan created: {result['plan_id']}")
print(f"📋 Plan type: {result['plan_type']}")
print(f"📊 Steps: {len(result['task_breakdown'])}")
```

### Step 2: Review the Plan

```python
# Check plan details
plan = planner.get_plan(result['plan_id'])

print("\n=== Plan Summary ===")
print(plan['plan_summary'])

# View execution steps
for i, step in enumerate(result['task_breakdown'], 1):
    print(f"{i}. {step['step_id']}")
    print(f"   Type: {step['type']}")
    print(f"   Agent/Tool: {step.get('agent_id') or step.get('tool_name')}")
```

### Step 3: Approve and Execute

```python
# Approve the plan
approval = planner.approve_plan(
    plan_id=result['plan_id'],
    user_id="demo_user"
)

print(f"✅ Execution started")
print(f"🔄 Workflow ID: {approval['workflow_id']}")
```

### Step 4: Monitor Execution

```python
import time

workflow_id = approval['workflow_id']

# Check status
while True:
    status = planner.get_workflow_status(workflow_id)
    
    print(f"\nStatus: {status['status']}")
    print(f"Completed steps: {len(status['steps'])}")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(2)

# View results
if status['status'] == 'completed':
    print("\n✅ Workflow completed successfully!")
    print("\nResults:")
    for step_id, result in status['results'].items():
        print(f"  {step_id}: {result}")
```

## Common Use Cases

### Use Case 1: Data Processing Pipeline

```python
request = """
Create a data processing pipeline:
1. Fetch data from API
2. Validate data format
3. Transform to target schema
4. Save to database
"""

result = planner.create_plan("user123", "session456", request)
```

### Use Case 2: Parallel API Calls

```python
request = """
Fetch information from three sources simultaneously:
- Weather data from weather API
- Stock prices from finance API  
- News from news API

Then combine all results into a single report
"""

result = planner.create_plan("user123", "session456", request)
# Planner automatically creates parallel execution plan
```

### Use Case 3: Conditional Workflow

```python
request = """
Check system status:
- If CPU usage > 80%: Send alert and restart service
- If CPU usage normal: Continue monitoring
"""

result = planner.create_plan("user123", "session456", request)
# Planner creates conditional branches
```

### Use Case 4: With Human Review

```python
request = """
Analyze customer feedback and draft responses.
I want to review the responses before they are sent.
"""

result = planner.create_plan("user123", "session456", request)
# Planner adds HITL checkpoint

# After execution reaches checkpoint, approve
planner.approve_hitl(hitl_id, "user123", "Looks good, send them")
```

## Key Methods Reference

### Planning Methods

```python
# Create a plan
result = planner.create_plan(user_id, session_id, user_request)
# Returns: dict with plan_id, plan_type, execution_plan, etc.

# Get plan details
plan = planner.get_plan(plan_id)
# Returns: dict with plan details and summary

# Approve plan
approval = planner.approve_plan(plan_id, user_id)
# Returns: dict with workflow_id

# Reject plan
success = planner.reject_plan(plan_id, user_id, reason)
# Returns: boolean
```

### Monitoring Methods

```python
# Get workflow status
status = planner.get_workflow_status(workflow_id)
# Returns: dict with status, steps, results

# Approve HITL checkpoint
success = planner.approve_hitl(hitl_id, user_id, response)
# Returns: boolean

# Reject HITL checkpoint
success = planner.reject_hitl(hitl_id, user_id, reason)
# Returns: boolean
```

## Integration with Existing System

### Using with Current DAGs

```python
# The planner automatically detects matching DAGs
request = "Run a simple sequential workflow"

result = planner.create_plan(user_id, session_id, request)

# If matching DAG exists (e.g., 'simple_sequential')
if result['plan_type'] == 'use_existing_dag':
    print(f"Using existing DAG: {result['selected_dag_id']}")
```

### Accessing Available Resources

```python
# The planner automatically queries these on plan creation:
# - AgentRegistry.list_agents()
# - ToolRegistry.list_tools()
# - DAGRegistry.list_dags()

# You can access the same information:
from agents.agent_registry import AgentRegistry
from tools.tool_registry import ToolRegistry
from dag.dag_registry import DAGRegistry

agent_registry = AgentRegistry()
tool_registry = ToolRegistry()
dag_registry = DAGRegistry()

print("Available agents:", agent_registry.list_agents())
print("Available tools:", tool_registry.list_tools())
print("Available DAGs:", dag_registry.list_dags())
```

## Testing Your Setup

### Basic Test

```python
from lgraph_planner import LangGraphPlanner, initialize_lgraph_tables

def test_basic_planning():
    """Test basic planning functionality"""
    
    # Setup
    initialize_lgraph_tables()
    planner = LangGraphPlanner(llm_provider='mock')
    
    # Create plan
    result = planner.create_plan(
        user_id="test_user",
        session_id="test_session",
        user_request="Echo hello world"
    )
    
    # Verify
    assert result['plan_id'] is not None
    assert result['status'] == 'pending_approval'
    assert len(result['task_breakdown']) > 0
    
    print("✅ Basic planning test passed!")

# Run test
test_basic_planning()
```

### Integration Test

```python
def test_full_workflow():
    """Test complete workflow from planning to execution"""
    
    initialize_lgraph_tables()
    planner = LangGraphPlanner(llm_provider='mock')
    
    # Create plan
    result = planner.create_plan(
        user_id="test_user",
        session_id="test_session",
        user_request="Test workflow"
    )
    
    plan_id = result['plan_id']
    print(f"Plan created: {plan_id}")
    
    # Approve
    approval = planner.approve_plan(plan_id, "test_user")
    workflow_id = approval['workflow_id']
    print(f"Workflow started: {workflow_id}")
    
    # Check status
    status = planner.get_workflow_status(workflow_id)
    print(f"Status: {status['status']}")
    
    print("✅ Full workflow test passed!")

# Run test
test_full_workflow()
```

## Troubleshooting

### Issue: Import Errors

```bash
# Install missing dependencies
pip install langgraph langchain langchain-core --break-system-packages

# Verify installation
python -c "import langgraph; print('LangGraph installed')"
```

### Issue: Database Errors

```python
# Reinitialize tables
from lgraph_planner import initialize_lgraph_tables
initialize_lgraph_tables()

# Verify tables exist
from db.database import get_db
db = get_db()
tables = db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [t['name'] for t in tables])
```

### Issue: LLM Provider Errors

```python
# Use mock provider for testing
planner = LangGraphPlanner(llm_provider='mock')

# For production, ensure LLM credentials are configured
# Check llm/llm_facade.py for configuration
```

## Next Steps

1. **Explore Examples**: Check `lgraph_planner_examples.py` for detailed usage examples
2. **Read Documentation**: Review `LGRAPH_PLANNER_README.md` for architecture details
3. **Customize**: Extend the planner with custom execution modes or decision logic
4. **Integrate**: Connect with your existing agents, tools, and MCP servers

## Tips for Best Results

### 1. Be Specific in Requests

❌ Bad: "Do some analysis"
✅ Good: "Analyze Q4 sales data, identify trends, and create summary report"

### 2. Indicate Parallelization

❌ Implicit: "Get data from API1, API2, API3"
✅ Explicit: "Simultaneously fetch data from API1, API2, and API3"

### 3. Specify Review Points

❌ Implicit: "Generate customer responses"
✅ Explicit: "Generate customer responses, let me review before sending"

### 4. Define Loop Conditions

❌ Vague: "Monitor the system"
✅ Clear: "Monitor system every 5 minutes for 1 hour or until CPU < 50%"

## Resources

- **Main Implementation**: `lgraph_planner.py`
- **Usage Examples**: `lgraph_planner_examples.py`
- **Full Documentation**: `LGRAPH_PLANNER_README.md`
- **Abhikarta System**: https://github.com/ajsinha/abhikarta

## Quick Reference Card

```python
# Setup
from lgraph_planner import LangGraphPlanner, initialize_lgraph_tables
initialize_lgraph_tables()
planner = LangGraphPlanner(llm_provider='anthropic')

# Create & Execute
result = planner.create_plan(user_id, session_id, request)
approval = planner.approve_plan(result['plan_id'], user_id)
status = planner.get_workflow_status(approval['workflow_id'])

# HITL
planner.approve_hitl(hitl_id, user_id, "approved")

# Monitoring
plan = planner.get_plan(plan_id)
status = planner.get_workflow_status(workflow_id)
```

---

**Happy Planning!** 🚀

For questions or issues:
- Email: ajsinha@gmail.com
- GitHub: https://github.com/ajsinha/abhikarta


## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
