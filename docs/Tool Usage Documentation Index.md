# Tool Usage Documentation Index


## © 2025-2030 Ashutosh Sinha


This index helps you find the right documentation for understanding how tools work in Abhikarta.

## 📚 Documentation Files

### 1. Quick Reference (Start Here!)
**File:** `TOOLS_QUICK_REFERENCE.md`

**Best for:** Getting a quick understanding of the system

**Contains:**
- TL;DR summary
- Visual flow diagrams
- Component responsibilities table
- Code snippets
- Common patterns
- FAQ

**Read this first if you:** Want a quick overview in 5 minutes

---

### 2. Comprehensive Guide
**File:** `HOW_TOOLS_ARE_USED.md`

**Best for:** Deep understanding of the architecture

**Contains:**
- Detailed architecture explanation
- Complete execution flow
- Component interactions
- Full code examples
- Data flow diagrams
- Design rationale
- Extension strategies

**Read this if you:** 
- Need to understand the full system
- Want to modify the architecture
- Need to explain it to others
- Are debugging issues

---

### 3. Practical Implementation Guide
**File:** `TOOL_ENABLED_AGENT_EXAMPLE.md`

**Best for:** Implementing tool-enabled agents

**Contains:**
- Complete implementation examples
- Step-by-step agent creation
- Security considerations
- Testing strategies
- Migration paths
- Multiple real-world examples

**Read this if you:**
- Want agents to call tools directly
- Need to extend the current system
- Are building complex agents
- Need working code examples

---

## 🎯 Quick Navigation

### I want to understand...

**"How does the system work right now?"**
→ Start with: `TOOLS_QUICK_REFERENCE.md`
→ Then read: `HOW_TOOLS_ARE_USED.md` (sections 1-4)

**"How do I create a workflow with tools?"**
→ Read: `HOW_TOOLS_ARE_USED.md` (Complete Example section)
→ See: `TOOLS_QUICK_REFERENCE.md` (Common Patterns)

**"Can agents call tools? How?"**
→ Current answer: `TOOLS_QUICK_REFERENCE.md` (TL;DR)
→ How to enable it: `TOOL_ENABLED_AGENT_EXAMPLE.md` (all sections)

**"How do I extend the system?"**
→ Read: `HOW_TOOLS_ARE_USED.md` (Extension section)
→ Implement: `TOOL_ENABLED_AGENT_EXAMPLE.md` (Step 1-4)

**"I need code examples"**
→ Quick snippets: `TOOLS_QUICK_REFERENCE.md`
→ Complete examples: `TOOL_ENABLED_AGENT_EXAMPLE.md`
→ Architecture examples: `HOW_TOOLS_ARE_USED.md`

---

## 📖 Reading Paths

### Path 1: For New Users (30 minutes)
1. Read `TOOLS_QUICK_REFERENCE.md` (5 min)
2. Skim `HOW_TOOLS_ARE_USED.md` - Overview and Complete Example (15 min)
3. Review code in actual files: `planner.py`, `orchestrator.py` (10 min)

### Path 2: For Developers Extending the System (1 hour)
1. Read `TOOLS_QUICK_REFERENCE.md` completely (10 min)
2. Read `HOW_TOOLS_ARE_USED.md` completely (25 min)
3. Read `TOOL_ENABLED_AGENT_EXAMPLE.md` - Implementation sections (25 min)

### Path 3: For Implementers (2 hours)
1. All of Path 2 (1 hour)
2. Study `TOOL_ENABLED_AGENT_EXAMPLE.md` - All examples (30 min)
3. Review actual codebase files with new understanding (30 min)

### Path 4: For Architects (Deep Dive)
1. Read all three documents completely
2. Review actual implementation in:
   - `planner.py`
   - `orchestrator.py`
   - `agent_registry.py`
   - `tool_registry.py`
3. Understand trade-offs and design decisions

---

## 🔑 Key Concepts

### Current Architecture
- **Separation**: Tools and agents are separate workflow nodes
- **Orchestration**: Orchestrator coordinates execution
- **Planning**: LLM-based planner creates workflow graphs
- **Registries**: Centralized management of tools and agents

### Node Types
- **Agent Node**: Runs agent logic
- **Tool Node**: Executes a specific tool
- **HITL Node**: Human-in-the-loop approval

### Data Flow
- Results flow between nodes via dependencies
- Use `${node_id.result}` syntax to reference previous results
- Orchestrator manages data passing

---

## 💡 Common Use Cases

### Use Case 1: Data Pipeline
```
Tool (fetch) → Tool (transform) → Tool (store)
```
**Doc:** Quick Reference - Pattern examples

### Use Case 2: AI Analysis
```
Tool (fetch data) → Agent (analyze) → Tool (save report)
```
**Doc:** HOW_TOOLS_ARE_USED.md - Complete Example

### Use Case 3: Multi-Source Aggregation
```
Tool A (source 1) ┐
Tool B (source 2) ├→ Agent (synthesize) → Tool (output)
Tool C (source 3) ┘
```
**Doc:** Quick Reference - Pattern 4

### Use Case 4: Dynamic Research
```
Agent (decides tools needed + calls them + synthesizes)
```
**Doc:** TOOL_ENABLED_AGENT_EXAMPLE.md - Research Agent

---

## 🛠️ Code Locations

### Core Files
| File | Location | Purpose |
|------|----------|---------|
| Planner | `workflows/planner.py` | Creates plans |
| Orchestrator | `workflows/orchestrator.py` | Executes workflows |
| Agent Registry | `agents/agent_registry.py` | Manages agents |
| Tool Registry | `tools/tool_registry.py` | Manages tools |
| Base Agent | `agents/agent_registry.py` | Agent base class |
| Echo Agent | `agents/echo_agent.py` | Example agent |

### Configuration
| Type | Location | Purpose |
|------|----------|---------|
| Agent configs | `config/agents/*.json` | Agent definitions |
| Tool configs | `config/tools/*.json` | Tool definitions |
| MCP configs | `config/mcp/*.json` | MCP server definitions |

---

## 🚀 Getting Started

### To Use the Current System:
1. Read `TOOLS_QUICK_REFERENCE.md`
2. Create a plan via Planner UI
3. Approve and execute
4. View results

### To Extend with Tool-Enabled Agents:
1. Read `TOOL_ENABLED_AGENT_EXAMPLE.md`
2. Create `tool_enabled_agent.py` base class
3. Create your custom agent
4. Add configuration JSON
5. Test and deploy

### To Understand Everything:
1. Read all three documents in order
2. Follow the code examples
3. Review actual implementation files
4. Experiment with modifications

---

## 📞 Quick Answers

**Q: Current state - can agents use tools?**
A: No, they're separate nodes. See: Quick Reference TL;DR

**Q: How to enable agents using tools?**
A: See: TOOL_ENABLED_AGENT_EXAMPLE.md

**Q: How does planner know about tools?**
A: They're passed as parameters. See: HOW_TOOLS_ARE_USED.md - Section 1

**Q: How are tools executed?**
A: Via Tool Registry. See: HOW_TOOLS_ARE_USED.md - Section 4

**Q: What are MCP tools?**
A: External tools from MCP servers. See: tool_registry.py and Quick Reference

**Q: Can I create custom tools?**
A: Yes! Extend BaseTool. See: Tool Registry code

**Q: Can I create custom agents?**
A: Yes! Extend BaseAgent. See: echo_agent.py example

**Q: How do workflows work?**
A: DAG execution. See: HOW_TOOLS_ARE_USED.md - Complete Example

---

## 📝 Summary

**If you read ONE document:** `TOOLS_QUICK_REFERENCE.md`

**If you want to UNDERSTAND deeply:** `HOW_TOOLS_ARE_USED.md`

**If you want to IMPLEMENT extensions:** `TOOL_ENABLED_AGENT_EXAMPLE.md`

**If you want ALL knowledge:** Read all three in order!

---

## 🎓 Learning Objectives

After reading the documentation, you should understand:

- ✅ How tools are separate from agents (current architecture)
- ✅ How planner creates workflows with tool and agent nodes
- ✅ How orchestrator executes these nodes
- ✅ How data flows between nodes
- ✅ Why the architecture is designed this way
- ✅ How to extend agents to use tools directly
- ✅ Trade-offs between approaches
- ✅ When to use which pattern

---

## 📚 Additional Resources

- **API Routes:** See `app.py` for REST endpoints
- **Database Schema:** See `database.py` for data structures
- **DAG Configuration:** See `dag_registry.py` for workflow definitions
- **Graph Structure:** See `graph.py` for DAG implementation

---

## 🔄 Updates

This documentation reflects the current state of the system as of the codebase review. 

**Current State:**
- Tools and agents are separate workflow nodes
- Orchestrator coordinates execution
- No direct agent-to-tool calls

**Potential Future State (via extensions):**
- Tool-enabled agents can call tools directly
- Hybrid approach available
- Backward compatible with existing workflows

## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
