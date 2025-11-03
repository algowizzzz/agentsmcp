# LangGraph Planner for Abhikarta


## © 2025-2030 Ashutosh Sinha


## Overview

The LangGraph Planner is an advanced autonomous workflow planning system that uses a **supervisor pattern** to intelligently analyze user requests and construct executable workflows. Unlike the traditional DAG-based planner, this system can dynamically create StateGraphs, manage complex execution patterns, and make intelligent decisions about the best execution strategy.

## Key Features

### 🤖 Autonomous Planning
- **Supervisor Agent**: Intelligent agent that analyzes requests and decides execution strategy
- **Automatic Resource Discovery**: Finds and evaluates available agents, tools, and MCP servers
- **Smart Strategy Selection**: Decides whether to use existing DAG or create custom StateGraph

### 🔄 Dynamic StateGraph Construction
- **On-the-Fly Workflow Creation**: Constructs executable workflows based on user intent
- **Flexible Execution Modes**: Sequential, parallel, conditional, and loop-based execution
- **Runtime Adaptability**: Adjusts workflow based on intermediate results

### 🚀 Advanced Execution Patterns

#### Parallel Execution
- Identifies independent tasks that can run simultaneously
- Optimizes execution time through parallelization
- Manages parallel branch synchronization

#### Looping Support
- Iterative workflows with configurable conditions
- Maximum iteration limits for safety
- Dynamic loop exit conditions

#### Conditional Branching
- Runtime decision making based on results
- Multiple execution paths
- Conditional routing and filtering

### 👥 Human-in-the-Loop (HITL)
- Automatic checkpoint creation for human review
- Pause-and-resume capability
- Approval/rejection workflow

### 📊 State Management
- Fine-grained state tracking
- Context preservation across steps
- Result aggregation and passing

### 🔗 Hybrid Integration
- Seamless integration with existing DAG orchestrator
- Can use predefined DAGs when appropriate
- Fallback to traditional execution when needed

## Architecture

### High-Level Flow

```
User Request
     ↓
[Analyze Request] → Extract intent, complexity, requirements
     ↓
[Evaluate Resources] → Discover agents, tools, DAGs
     ↓
[Decide Strategy] → Choose: Existing DAG vs Custom StateGraph
     ↓
[Construct Plan] → Build detailed execution plan
     ↓
[Request Approval] → User reviews and approves/rejects
     ↓
[Execute Plan] → Run workflow with state management
     ↓
[Handle HITL] → Pause for human review if needed
     ↓
[Finalize] → Complete and store results
```

### Components

#### 1. Supervisor Graph
The core LangGraph workflow that orchestrates the planning process:
- **analyze_request**: Understands user intent
- **evaluate_resources**: Catalogs available capabilities
- **decide_strategy**: Chooses execution approach
- **construct_plan**: Builds detailed workflow
- **request_approval**: Gets user confirmation
- **execute_plan**: Runs the workflow
- **handle_hitl**: Manages human checkpoints
- **finalize**: Completes execution

#### 2. State Management
WorkflowState TypedDict tracks:
- User input and context
- Planning decisions
- Execution progress
- Results and errors
- HITL status
- Messages and logs

#### 3. Execution Engine
Handles different execution modes:
- **Sequential**: One step after another
- **Parallel**: Multiple steps simultaneously
- **Loop**: Repeated execution with conditions
- **Conditional**: Branching based on results

## Comparison: Traditional DAG vs LangGraph Planner

| Feature | Traditional DAG | LangGraph Planner |
|---------|----------------|-------------------|
| Definition | Pre-defined JSON configs | Dynamic, AI-generated |
| Flexibility | Fixed structure | Adaptive workflows |
| Parallelization | Manual configuration | Automatic detection |
| Conditionals | Limited | Full support |
| Loops | Not supported | Native support |
| Planning | Human-defined | AI-powered |
| Adaptability | Static | Runtime adjustments |
| Best For | Known workflows | Novel/complex tasks |

## Usage

### Basic Usage

```python
from lgraph_planner import LangGraphPlanner, initialize_lgraph_tables

# Initialize
initialize_lgraph_tables()
planner = LangGraphPlanner(llm_provider='anthropic')

# Create a plan
result = planner.create_plan(
    user_id="user_123",
    session_id="session_456",
    user_request="Analyze Q4 sales data and create a report"
)

# Review the plan
print(f"Plan ID: {result['plan_id']}")
print(f"Plan Type: {result['plan_type']}")
print(f"Summary: {result['execution_plan']['details']}")

# Approve and execute
if result['pending_approval']:
    approval = planner.approve_plan(
        plan_id=result['plan_id'],
        user_id="user_123"
    )
    print(f"Workflow started: {approval['workflow_id']}")

# Monitor execution
status = planner.get_workflow_status(approval['workflow_id'])
print(f"Status: {status['status']}")
```

### Advanced Usage

#### Parallel Processing
```python
request = """
Process three data sources simultaneously:
1. Fetch weather data
2. Fetch stock prices  
3. Fetch news articles
Then combine and generate report
"""

result = planner.create_plan(user_id, session_id, request)
# Planner automatically detects parallel execution opportunity
```

#### Human-in-the-Loop
```python
request = """
Analyze customer feedback and draft responses.
I want to review before sending.
"""

result = planner.create_plan(user_id, session_id, request)
# Planner adds HITL checkpoint automatically

# After execution reaches checkpoint
planner.approve_hitl(hitl_id, user_id, "Responses look good")
```

#### Looping Workflow
```python
request = """
Monitor API endpoint every 5 minutes.
Alert if response time > 2s.
Stop after 1 hour or when stable.
"""

result = planner.create_plan(user_id, session_id, request)
# Planner creates loop with conditions
```

## Database Schema

### lgraph_plans
Stores plan definitions and approval status:
```sql
CREATE TABLE lgraph_plans (
    plan_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    user_request TEXT,
    plan_type TEXT,
    execution_plan TEXT,
    plan_summary TEXT,
    status TEXT,
    created_at TEXT,
    approved_at TEXT,
    approved_by TEXT,
    rejected_at TEXT,
    rejected_by TEXT,
    rejection_reason TEXT
)
```

### lgraph_workflows
Tracks workflow execution:
```sql
CREATE TABLE lgraph_workflows (
    workflow_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    status TEXT,
    started_at TEXT,
    completed_at TEXT,
    results TEXT,
    error TEXT
)
```

### lgraph_step_logs
Records individual step execution:
```sql
CREATE TABLE lgraph_step_logs (
    log_id INTEGER PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    result TEXT,
    success BOOLEAN,
    executed_at TEXT
)
```

### lgraph_hitl_requests
Manages human-in-the-loop checkpoints:
```sql
CREATE TABLE lgraph_hitl_requests (
    hitl_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    checkpoint TEXT,
    message TEXT,
    status TEXT,
    created_at TEXT,
    responded_at TEXT,
    responded_by TEXT,
    response TEXT
)
```

## Integration with Existing System

### Registries
The LangGraph Planner integrates with existing registries:

```python
# Uses AgentRegistry
self.agent_registry = AgentRegistry()
agents = self.agent_registry.list_agents()

# Uses ToolRegistry  
self.tool_registry = ToolRegistry()
tools = self.tool_registry.list_tools()

# Uses DAGRegistry
self.dag_registry = DAGRegistry()
dags = self.dag_registry.list_dags()
```

### Orchestrator
Can delegate to traditional orchestrator:

```python
if plan_type == PlanType.USE_EXISTING_DAG:
    # Use existing WorkflowOrchestrator
    from orchestrator import WorkflowOrchestrator
    orchestrator = WorkflowOrchestrator()
    workflow_id = orchestrator.start_workflow(...)
```

## Configuration

### LLM Provider
Choose between different LLM providers:

```python
# Use Anthropic Claude
planner = LangGraphPlanner(llm_provider='anthropic')

# Use OpenAI
planner = LangGraphPlanner(llm_provider='openai')

# Use mock for testing
planner = LangGraphPlanner(llm_provider='mock')
```

### Execution Modes
The planner automatically selects the best mode, but you can influence it through request phrasing:

- **Sequential**: "First do X, then Y, then Z"
- **Parallel**: "Simultaneously fetch A, B, and C"
- **Loop**: "Monitor every N minutes until..."
- **Conditional**: "If X then Y, otherwise Z"

## Decision Making Logic

### Strategy Selection
The supervisor uses this logic:

```python
1. Analyze user request
   - Extract intent and complexity
   - Identify key requirements
   
2. Evaluate resources
   - List available agents
   - List available tools
   - List available DAGs
   
3. Decide strategy
   IF matching DAG exists AND request is straightforward:
       → Use existing DAG
   ELSE IF request is complex OR requires novel approach:
       → Create custom StateGraph
   ELSE:
       → Simple sequential execution
       
4. Construct detailed plan
   - Break down into steps
   - Assign agents/tools
   - Identify parallel opportunities
   - Add HITL checkpoints if needed
   
5. Request approval
   - Generate human-readable summary
   - Wait for user confirmation
   
6. Execute
   - Run workflow with state management
   - Handle HITL if required
   - Track progress and results
```

## Best Practices

### 1. Clear Request Phrasing
Good:
```
"Fetch stock prices for AAPL, GOOGL, MSFT in parallel, 
then calculate portfolio value"
```

Better:
```
"I need to:
1. Get current stock prices for AAPL, GOOGL, MSFT (can be parallel)
2. Calculate total portfolio value
3. Compare with yesterday's value
4. Alert me if change > 5%"
```

### 2. Specify HITL Requirements
```
"Analyze customer complaints and draft responses.
Please let me review the responses before sending."
```

### 3. Define Loop Conditions
```
"Monitor system health every 5 minutes.
Alert if CPU > 80% or memory > 90%.
Continue for 2 hours or until metrics are normal for 30 minutes."
```

### 4. Leverage Existing Resources
The planner considers existing DAGs, so keep your DAG library updated with commonly used workflows.

## Error Handling

### Plan Rejection
```python
# User can reject plans
planner.reject_plan(
    plan_id=plan_id,
    user_id=user_id,
    reason="Need more detailed analysis steps"
)

# Then create modified plan
new_result = planner.create_plan(
    user_id=user_id,
    session_id=session_id,
    user_request=modified_request
)
```

### Workflow Failures
```python
# Check workflow status
status = planner.get_workflow_status(workflow_id)

if status['status'] == 'failed':
    print(f"Error: {status.get('error')}")
    
    # Retry with modified approach
    # or investigate failed steps
    for step in status['steps']:
        if not step['success']:
            print(f"Failed step: {step['step_id']}")
```

## Performance Considerations

### Parallel Execution
- Automatically identifies independent tasks
- Reduces overall execution time
- Manages resource allocation

### State Management
- Efficient state passing between nodes
- Minimal serialization overhead
- Context-aware execution

### Caching
- Plans can be reused for similar requests
- Step results cached when appropriate
- Reduces redundant LLM calls

## Security

### Approval Required
- All plans require user approval before execution
- Users review detailed execution steps
- Can reject risky operations

### HITL Checkpoints
- Sensitive operations pause for human review
- User controls critical decision points
- Audit trail of all approvals

### Access Control
- User ID tracked throughout workflow
- Session-based isolation
- Database-level security

## Monitoring and Debugging

### Workflow Status
```python
status = planner.get_workflow_status(workflow_id)

print(f"Overall Status: {status['status']}")
print(f"Completed Steps: {len(status['steps'])}")

for step in status['steps']:
    print(f"Step {step['step_id']}: {step['success']}")
    if not step['success']:
        print(f"  Error: {step['result']}")
```

### Plan Details
```python
plan = planner.get_plan(plan_id)

print(f"Plan Type: {plan['plan_type']}")
print(f"Steps: {len(plan['execution_plan']['details']['steps'])}")
print(f"\nSummary:\n{plan['plan_summary']}")
```

### Logging
All major events are logged:
- Plan creation
- Approval/rejection
- Step execution
- HITL requests
- Workflow completion/failure

## Future Enhancements

### Planned Features
1. **Learning from History**: Improve planning based on past executions
2. **Cost Estimation**: Predict execution time and resource usage
3. **Optimization Suggestions**: Recommend efficiency improvements
4. **Template Creation**: Convert successful plans into reusable DAGs
5. **Multi-Agent Collaboration**: Complex tasks with agent coordination
6. **Real-time Monitoring UI**: Visual workflow execution tracking

### Experimental Features
- Self-healing workflows (automatic error recovery)
- Dynamic resource scaling
- Predictive planning based on patterns
- Natural language workflow queries

## Troubleshooting

### Common Issues

**Issue**: Planner always creates simple sequential plans
**Solution**: Provide more detailed requests with explicit parallelization hints

**Issue**: Plans not being approved
**Solution**: Check database for plan status, verify approval workflow

**Issue**: HITL checkpoints not triggering
**Solution**: Explicitly mention review requirements in request

**Issue**: Workflow stuck in "running" state
**Solution**: Check step logs for failed steps, implement timeout handling

## Contributing

When extending the LangGraph Planner:

1. **Add New Execution Modes**: Extend `ExecutionMode` enum and implement handler
2. **Custom State Fields**: Add to `WorkflowState` TypedDict
3. **New Decision Logic**: Modify `_decide_strategy` method
4. **Additional Nodes**: Add nodes to supervisor graph

## License

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com
https://www.github.com/ajsinha/abhikarta

## Support

For questions or issues:
- GitHub Issues: https://github.com/ajsinha/abhikarta/issues
- Email: ajsinha@gmail.com

## Conclusion

The LangGraph Planner represents a significant evolution in the Abhikarta system, moving from static, pre-defined workflows to dynamic, AI-powered autonomous planning. It maintains compatibility with existing components while providing powerful new capabilities for complex, adaptive workflow execution.

Key advantages:
- ✅ Autonomous planning reduces manual workflow definition
- ✅ Dynamic adaptation to novel requests
- ✅ Advanced execution patterns (parallel, loop, conditional)
- ✅ Seamless integration with existing system
- ✅ User control through approval workflow
- ✅ Comprehensive monitoring and debugging

The system is production-ready and designed to scale with your workflow automation needs.


## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
