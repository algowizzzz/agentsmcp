# How Tools Are Used by Planners and Agents in Abhikarta


## © 2025-2030 Ashutosh Sinha


## Overview

In the Abhikarta system, **tools are not directly used by agents**. Instead, tools and agents are **separate, independent workflow nodes** that are orchestrated together. The system uses a DAG (Directed Acyclic Graph) based workflow model where both tools and agents are first-class citizens.

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────┐
│                       PLANNER                            │
│  (Creates workflow plans with agent & tool nodes)       │
└────────────────┬────────────────────────────────────────┘
                 │ Generates Plan JSON
                 ▼
┌─────────────────────────────────────────────────────────┐
│                    WORKFLOW PLAN                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │ Agent    │───▶│ Tool     │───▶│ Agent    │         │
│  │ Node     │    │ Node     │    │ Node     │         │
│  └──────────┘    └──────────┘    └──────────┘         │
└────────────────┬────────────────────────────────────────┘
                 │ Executes Plan
                 ▼
┌─────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR                           │
│  (Executes nodes based on dependencies)                 │
└─────────────┬────────────────────┬──────────────────────┘
              │                    │
              ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ Agent Registry  │  │ Tool Registry   │
    │ executes agents │  │ executes tools  │
    └─────────────────┘  └─────────────────┘
```

## Key Components

### 1. Planner (`planner.py`)

**Role:** Creates workflow plans from natural language requests

**How it handles tools:**

```python
def create_plan_from_request(self, user_id: str, request: str, 
                             available_tools: List[str],      # <-- Tools passed in
                             available_agents: List[str]):    # <-- Agents passed in
    
    # Planner receives list of available tools and agents
    prompt = f"""Create a workflow plan for: "{request}"
    
    Available tools: {', '.join(available_tools)}
    Available agents: {', '.join(available_agents)}
    
    Generate nodes that can be type "agent" or "tool"
    """
```

**What the planner does:**
1. Receives a list of available tools and agents
2. Sends them to the LLM as context
3. LLM decides which tools/agents to use and in what order
4. Creates a workflow plan with mixed agent and tool nodes
5. Defines dependencies between nodes

**Example Plan Output:**
```json
{
  "dag_id": "generated_plan_abc123",
  "name": "Stock Analysis Workflow",
  "nodes": [
    {
      "node_id": "fetch_price",
      "node_type": "tool",           // <-- This is a TOOL node
      "tool_name": "get_stock_price",
      "config": {
        "input": {"symbol": "AAPL"}
      },
      "dependencies": []
    },
    {
      "node_id": "analyze_data",
      "node_type": "agent",          // <-- This is an AGENT node
      "agent_id": "analysis_agent",
      "config": {
        "input": {"data": "${fetch_price.result}"}  // Uses tool result
      },
      "dependencies": ["fetch_price"]  // Depends on tool node
    }
  ]
}
```

### 2. Orchestrator (`orchestrator.py`)

**Role:** Executes workflow plans by running nodes in the correct order

**How it executes different node types:**

```python
def _execute_node(self, workflow_id: str, graph: Graph, node: Node) -> None:
    # Determine node type and execute accordingly
    if node.node_type == 'agent':
        result = self._execute_agent_node(node)      # Execute agent
    elif node.node_type == 'tool':
        result = self._execute_tool_node(node)       # Execute tool
    elif node.node_type == 'human_in_loop':
        self._handle_hitl_node(workflow_id, node)    # Wait for human

def _execute_agent_node(self, node: Node) -> Dict[str, Any]:
    """Execute an agent node"""
    return self.agent_registry.execute_agent(
        node.agent_id, 
        node.config.get('input', {})
    )

def _execute_tool_node(self, node: Node) -> Dict[str, Any]:
    """Execute a tool node"""
    tool_name = node.config.get('tool_name')
    return self.tool_registry.execute_tool(
        tool_name, 
        **node.config.get('input', {})
    )
```

**Execution Flow:**
1. Orchestrator traverses the workflow DAG
2. Identifies nodes that are ready (dependencies satisfied)
3. For each ready node:
   - If it's an agent node → calls AgentRegistry
   - If it's a tool node → calls ToolRegistry
4. Stores results for downstream nodes to use
5. Continues until all nodes complete

### 3. Agent Registry (`agent_registry.py`)

**Role:** Manages and executes agents

**Current Implementation:**
- Agents do NOT have direct access to tools
- Agents are simple executors that:
  - Receive input data
  - Process it
  - Return output
  
```python
class BaseAgent(ABC):
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task"""
        pass
```

**Example Agent (Echo Agent):**
```python
class EchoAgent(BaseAgent):
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        message = input_data.get('input', 'No input provided')
        return {
            'success': True,
            'echo': message,
            'agent': self.agent_id
        }
```

**Key Point:** Agents do not call tools directly. They only process their input and return results.

### 4. Tool Registry (`tool_registry.py`)

**Role:** Manages and executes tools (including MCP tools)

**How tools are executed:**

```python
def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a tool"""
    tool = self._tools.get(tool_name)
    result = tool.execute(**kwargs)
    return {
        'success': True,
        'result': result,
        'tool_name': tool_name
    }
```

**Tool Types:**
1. **Regular Tools:** Python-based tools
2. **MCP Tools:** Tools from external MCP servers

```python
class MCPTool(BaseTool):
    def execute(self, **kwargs) -> Dict[str, Any]:
        # Makes REST call to MCP server
        response = requests.post(
            f"{self.mcp_url}/execute",
            json={'tool': self.tool_config.get('name'), 'arguments': kwargs}
        )
        return response.json()
```

## Complete Example: Stock Analysis Workflow

Let's trace a complete example from user request to execution:

### Step 1: User Request
```
User: "Get Apple stock price and analyze it"
```

### Step 2: Planner Creates Plan

The planner receives:
- **Available Tools:** `["get_stock_price", "get_stock_info"]`
- **Available Agents:** `["echo_agent", "analysis_agent"]`

Creates plan:
```json
{
  "dag_id": "stock_analysis_plan",
  "nodes": [
    {
      "node_id": "step_1",
      "node_type": "tool",
      "tool_name": "get_stock_price",
      "config": {"input": {"symbol": "AAPL"}},
      "dependencies": []
    },
    {
      "node_id": "step_2",
      "node_type": "agent",
      "agent_id": "analysis_agent",
      "config": {"input": {"price_data": "${step_1.result}"}},
      "dependencies": ["step_1"]
    }
  ]
}
```

### Step 3: Orchestrator Executes Plan

**Execution Timeline:**

```
t=0: Start workflow
     └─ Ready nodes: [step_1]

t=1: Execute step_1 (tool node)
     ├─ Call: tool_registry.execute_tool("get_stock_price", symbol="AAPL")
     ├─ Tool makes API call
     └─ Result: {"success": True, "result": {"price": 150.00}}

t=2: Mark step_1 complete
     └─ Ready nodes: [step_2]

t=3: Execute step_2 (agent node)
     ├─ Call: agent_registry.execute_agent("analysis_agent", 
     │                                       {"price_data": {"price": 150.00}})
     ├─ Agent analyzes data
     └─ Result: {"success": True, "result": {"analysis": "Price is stable"}}

t=4: Mark step_2 complete
     └─ Workflow complete
```

### Step 4: Results Stored
- Each node's result is stored
- Available for downstream nodes via `${node_id.result}`
- User can view in workflow detail page

## Data Flow Between Nodes

```
┌─────────────┐
│  Tool Node  │
│ "step_1"    │  Output: {"price": 150.00}
└──────┬──────┘
       │ Dependencies flow
       ▼
┌─────────────┐
│ Agent Node  │
│ "step_2"    │  Input: {"price_data": {"price": 150.00}}
└─────────────┘
```

The orchestrator:
1. Waits for step_1 to complete
2. Extracts result from step_1
3. Passes it as input to step_2
4. Can use template syntax: `"${step_1.result}"`

## Why This Architecture?

### Advantages:

1. **Separation of Concerns**
   - Tools focus on specific actions (API calls, data fetch)
   - Agents focus on reasoning/processing
   - Orchestrator focuses on coordination

2. **Flexibility**
   - Can chain any combination of tools and agents
   - Can run multiple tools in parallel
   - Can insert human-in-the-loop nodes

3. **Reusability**
   - Same tool can be used by different workflows
   - Same agent can process different tool outputs
   - Tools and agents are independent

4. **Testability**
   - Tools can be tested independently
   - Agents can be tested with mock data
   - Workflows can be validated before execution

5. **Extensibility**
   - Add new tools without modifying agents
   - Add new agents without modifying tools
   - Support external MCP tools seamlessly

### Current Limitations:

1. **No Agent-Tool Direct Calls**
   - Agents cannot dynamically call tools
   - All tool usage must be pre-planned
   - Cannot have agent decide "I need tool X now"

2. **Static Workflows**
   - Workflow structure is fixed at plan time
   - No dynamic branching based on tool results
   - No conditional tool execution

## How to Extend: Agent with Tool Access

If you want agents to use tools directly, you would need to:

### Option 1: Pass Tool Registry to Agents

```python
class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, description: str, 
                 config: Dict[str, Any] = None,
                 tool_registry: ToolRegistry = None):  # Add tool registry
        self.agent_id = agent_id
        self.name = name
        self.tool_registry = tool_registry  # Store reference

class SmartAgent(BaseAgent):
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Agent can now call tools directly
        stock_data = self.tool_registry.execute_tool(
            "get_stock_price", 
            symbol="AAPL"
        )
        
        # Process the data
        analysis = self.analyze(stock_data)
        return {'success': True, 'result': analysis}
```

### Option 2: Create Tool-Enabled Agent Type

```python
class ToolEnabledAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_registry = ToolRegistry()  # Get singleton instance
    
    def call_tool(self, tool_name: str, **kwargs):
        """Helper method to call tools"""
        return self.tool_registry.execute_tool(tool_name, **kwargs)
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Use helper to call tools
        result = self.call_tool("some_tool", param="value")
        return self.process(result)
```

## Summary

**Current Architecture:**
- ✅ Tools and agents are separate workflow nodes
- ✅ Planner decides which tools/agents to use
- ✅ Orchestrator executes them in sequence/parallel
- ✅ Tools and agents are independent and reusable
- ❌ Agents cannot dynamically call tools

**To enable dynamic tool usage by agents:**
- Modify BaseAgent to accept ToolRegistry
- Update AgentRegistry to inject tool registry
- Implement tool-calling methods in agent classes

**Best Use Cases:**
- Current architecture: Pre-planned, structured workflows
- Extended architecture: Dynamic, AI-driven tool selection

The current design favors explicit, reviewable workflows where users can see exactly which tools will be used before execution. This is valuable for:
- Compliance and auditing
- Security (users approve tool usage)
- Debugging (clear execution trace)
- Testing (reproducible workflows)

## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
