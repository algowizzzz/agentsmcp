# Quick Reference: Tools in Abhikarta


## © 2025-2030 Ashutosh Sinha

## TL;DR

**Current System:**
- Tools and agents are SEPARATE workflow nodes
- Planner creates workflows with both tool and agent nodes
- Orchestrator executes them in order
- Agents DO NOT call tools directly

## The Flow in 4 Steps

```
1. USER REQUEST
   "Analyze Apple stock"
   
2. PLANNER CREATES PLAN
   Node 1: Tool (get_stock_price)
   Node 2: Agent (analyze_data)
   
3. ORCHESTRATOR EXECUTES
   Execute Node 1 → Store result
   Execute Node 2 (with Node 1's result)
   
4. RESULTS RETURNED
   User sees complete workflow results
```

## Component Responsibilities

| Component | What It Does | Uses Tools? | Uses Agents? |
|-----------|-------------|-------------|--------------|
| **Planner** | Creates workflow plans | ❌ No | ❌ No |
| **Orchestrator** | Executes workflow nodes | ✅ Via Tool Registry | ✅ Via Agent Registry |
| **Agent** | Processes data/logic | ❌ No (currently) | N/A |
| **Tool** | Performs specific actions | N/A | N/A |
| **Tool Registry** | Manages/executes tools | N/A | N/A |
| **Agent Registry** | Manages/executes agents | N/A | N/A |

## Code Snippets

### How Planner References Tools
```python
# In create_plan_from_request()
prompt = f"""
Available tools: {', '.join(available_tools)}
Available agents: {', '.join(available_agents)}

Create a plan using these...
"""
```

### How Orchestrator Executes Tool Node
```python
# In _execute_tool_node()
tool_name = node.config.get('tool_name')
return self.tool_registry.execute_tool(tool_name, **node.config.get('input', {}))
```

### How Orchestrator Executes Agent Node
```python
# In _execute_agent_node()
return self.agent_registry.execute_agent(node.agent_id, node.config.get('input', {}))
```

### How Agent Currently Works (No Tools)
```python
class EchoAgent(BaseAgent):
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        message = input_data.get('input', 'No input provided')
        return {'success': True, 'echo': message}
        # ❌ Cannot call tools here
```

## Example Workflow Plan

```json
{
  "dag_id": "example_workflow",
  "nodes": [
    {
      "node_id": "step1",
      "node_type": "tool",              ← TOOL NODE
      "tool_name": "get_stock_price",
      "config": {"input": {"symbol": "AAPL"}},
      "dependencies": []
    },
    {
      "node_id": "step2",
      "node_type": "agent",             ← AGENT NODE
      "agent_id": "analysis_agent",
      "config": {"input": {"data": "${step1.result}"}},
      "dependencies": ["step1"]         ← WAITS FOR TOOL
    }
  ]
}
```

## Execution Timeline

```
Time  | Action                        | Component
------|-------------------------------|------------------
t=0   | Workflow starts               | Orchestrator
t=1   | Execute step1 (tool)          | Tool Registry
t=2   | Store step1 result            | Orchestrator
t=3   | Execute step2 (agent)         | Agent Registry
t=4   | Pass step1.result to agent    | Orchestrator
t=5   | Agent processes data          | Agent
t=6   | Store step2 result            | Orchestrator
t=7   | Workflow complete             | Orchestrator
```

## Key Files

| File | Purpose |
|------|---------|
| `planner.py` | Creates workflow plans |
| `orchestrator.py` | Executes workflows |
| `agent_registry.py` | Manages agents |
| `tool_registry.py` | Manages tools (including MCP) |
| `echo_agent.py` | Example agent implementation |

## To Make Agents Use Tools Directly

See `TOOL_ENABLED_AGENT_EXAMPLE.md` for full implementation.

**Quick version:**
```python
# 1. Create enhanced base class
class ToolEnabledAgent(BaseAgent):
    def __init__(self, ...):
        self.tool_registry = ToolRegistry()
    
    def call_tool(self, tool_name, **kwargs):
        return self.tool_registry.execute_tool(tool_name, **kwargs)

# 2. Use in agent
class SmartAgent(ToolEnabledAgent):
    def execute(self, input_data):
        result = self.call_tool("get_stock_price", symbol="AAPL")
        return self.process(result)
```

## Common Patterns

### Pattern 1: Tool → Agent
```
Tool fetches data → Agent processes it
```
Use case: Get data, then analyze

### Pattern 2: Agent → Tool
```
Agent makes decision → Tool executes action
```
Use case: Analyze, then save results

### Pattern 3: Tool → Agent → Tool
```
Tool fetches → Agent decides → Tool acts
```
Use case: Get data, decide action, execute action

### Pattern 4: Parallel Tools → Agent
```
Tool A ──┐
Tool B ──┼→ Agent (processes all)
Tool C ──┘
```
Use case: Gather from multiple sources, then synthesize

## Testing

### Test a Tool
```python
from tools.tool_registry import ToolRegistry

registry = ToolRegistry()
result = registry.execute_tool("echo", message="test")
print(result)
```

### Test an Agent
```python
from agents.agent_registry import AgentRegistry

registry = AgentRegistry()
result = registry.execute_agent("echo_agent", {"input": "test"})
print(result)
```

### Test a Workflow
```python
# Create plan via planner
# Execute via orchestrator
# Check results in database
```

## FAQ

**Q: Can agents call tools?**
A: Not currently. They're separate workflow nodes.

**Q: How do I pass data between nodes?**
A: Use `"${node_id.result}"` in config

**Q: Can I run tools in parallel?**
A: Yes! Just make them have no dependencies on each other

**Q: What are MCP tools?**
A: Tools from external Model Context Protocol servers

**Q: Can I make custom tools?**
A: Yes! Extend BaseTool and add config JSON

**Q: Can I make custom agents?**
A: Yes! Extend BaseAgent and add config JSON

## Next Steps

1. Read `HOW_TOOLS_ARE_USED.md` for deep dive
2. Read `TOOL_ENABLED_AGENT_EXAMPLE.md` for extensions
3. Look at `config/agents/` for examples
4. Look at `config/tools/` for examples
5. Look at `config/mcp/` for MCP tools

## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
