# Import Issues Troubleshooting Guide


## © 2025-2030 Ashutosh Sinha


## Common Import Errors and Solutions

### Error 1: Cannot find ToolExecutor in __init__.py

**Error Message:**
```
ImportError: cannot import name 'ToolExecutor' from 'langgraph.prebuilt'
```

**Solution:**
This import was removed from the code as it wasn't being used. Make sure you have the latest version of `lgraph_planner.py`.

**If you still see this error:**
```bash
# Update to latest langgraph
pip install --upgrade langgraph --break-system-packages
```

---

### Error 2: No module named 'langgraph'

**Error Message:**
```
ModuleNotFoundError: No module named 'langgraph'
```

**Solution:**
```bash
pip install langgraph langchain langchain-core --break-system-packages
```

**Verify installation:**
```bash
python -c "import langgraph; print('LangGraph version:', langgraph.__version__)"
```

---

### Error 3: No module named 'db' / 'llm' / 'agents' / 'tools' / 'dag'

**Error Message:**
```
ModuleNotFoundError: No module named 'db'
```

**Solution:**
This means you're not running from the correct directory. The lgraph_planner expects this directory structure:

```
abhikarta/
├── db/
│   └── database.py
├── llm/
│   └── llm_facade.py
├── agents/
│   └── agent_registry.py
├── tools/
│   └── tool_registry.py
├── dag/
│   └── dag_registry.py
└── lgraph_planner.py
```

**Steps to fix:**

1. **Check your current directory:**
```bash
pwd
ls -la
```

2. **Navigate to project root:**
```bash
cd /path/to/abhikarta
```

3. **Verify directory structure:**
```bash
ls -la db/ llm/ agents/ tools/ dag/
```

4. **Run from project root:**
```bash
python lgraph_planner.py
```

---

### Error 4: Different directory structure

If your `dag_registry.py` is in a different location (e.g., root directory instead of `dag/`), you need to update the import.

**Option A: Move file to correct location**
```bash
mkdir -p dag
mv dag_registry.py dag/
```

**Option B: Update import in lgraph_planner.py**

Find this line:
```python
from dag.dag_registry import DAGRegistry
```

Change to:
```python
from dag_registry import DAGRegistry  # if in root directory
```

Or:
```python
from workflows.dag_registry import DAGRegistry  # if in workflows/ directory
```

---

### Error 5: Import works but class not found

**Error Message:**
```
AttributeError: module 'db.database' has no attribute 'get_db'
```

**Solution:**
Check that the file contains the expected function/class.

```bash
# Check what's in the file
python -c "from db import database; print(dir(database))"
```

If `get_db` is missing, you may need to implement it or use a different function name.

---

## Installation Verification Script

Run this to verify all dependencies:

```python
# test_imports.py
python test_imports.py
```

This will show which imports work and which need fixing.

---

## Complete Installation Steps

### Step 1: Install Python Dependencies

```bash
# Core dependencies
pip install langgraph langchain langchain-core --break-system-packages

# Optional: Anthropic for Claude
pip install anthropic --break-system-packages

# Optional: OpenAI
pip install openai --break-system-packages
```

### Step 2: Verify Installation

```bash
python test_imports.py
```

### Step 3: Check Directory Structure

```bash
# Create expected structure if needed
mkdir -p db llm agents tools dag graph config/dags config/tools config/mcp

# Verify structure
ls -la db/ llm/ agents/ tools/ dag/
```

### Step 4: Place Files

```bash
# Copy lgraph_planner to project root
cp lgraph_planner.py /path/to/abhikarta/

# Make sure other files are in correct locations
# - db/database.py
# - llm/llm_facade.py
# - agents/agent_registry.py
# - tools/tool_registry.py
# - dag/dag_registry.py
# - graph/graph.py
```

### Step 5: Test Import

```python
# Quick test
python -c "from lgraph_planner import LangGraphPlanner; print('Success!')"
```

---

## Project Structure Reference

Based on your uploaded files, here's the expected structure:

```
abhikarta/
│
├── config/
│   ├── dags/           # DAG JSON configurations
│   │   ├── 01_simple_sequential.json
│   │   ├── 03_parallel_processing.json
│   │   └── 04_parallel_with_hitl.json
│   ├── tools/          # Tool configurations
│   └── mcp/            # MCP server configurations
│       ├── echo_mcp_tool.json
│       └── yahoo_finance_tool.json
│
├── db/
│   └── database.py     # Database connection and operations
│
├── llm/
│   └── llm_facade.py   # LLM provider facade
│
├── agents/
│   ├── agent_registry.py
│   └── echo_agent.py   # Example: echo agent implementation
│
├── tools/
│   ├── base_tool.py
│   ├── mcp_tool.py
│   └── tool_registry.py
│
├── dag/
│   └── dag_registry.py
│
├── graph/
│   └── graph.py        # Graph, Node, Edge classes
│
├── orchestrator.py     # Traditional workflow orchestrator
├── planner.py          # Original planner
├── lgraph_planner.py   # New LangGraph planner (this file)
│
└── main.py or api.py   # Your application entry point
```

---

## Quick Fixes Cheat Sheet

| Error | Quick Fix |
|-------|-----------|
| `ToolExecutor not found` | Use latest lgraph_planner.py (already fixed) |
| `No module named langgraph` | `pip install langgraph --break-system-packages` |
| `No module named db` | Run from project root: `cd /path/to/abhikarta` |
| `get_db not found` | Check db/database.py has get_db function |
| Directory structure wrong | Reorganize files or update imports |

---

## Still Having Issues?

### Debug Mode

Add this to the top of lgraph_planner.py:

```python
import sys
print("Python path:", sys.path)
print("Current directory:", os.getcwd())

# Try importing and show error
try:
    from db.database import get_db
    print("✓ db.database imported successfully")
except ImportError as e:
    print("✗ db.database import failed:", e)
    print("Available modules:", [d for d in os.listdir('.') if os.path.isdir(d)])
```

### Check Python Path

```python
import sys
import os

print("Current directory:", os.getcwd())
print("\nPython path:")
for path in sys.path:
    print(f"  - {path}")
```

### Minimal Test

Create a minimal test file:

```python
# minimal_test.py
print("Starting minimal test...")

# Test 1: LangGraph
try:
    from langgraph.graph import StateGraph
    print("✓ LangGraph OK")
except Exception as e:
    print(f"✗ LangGraph failed: {e}")

# Test 2: Local imports (adjust based on your structure)
try:
    from db.database import get_db
    print("✓ Database OK")
except Exception as e:
    print(f"✗ Database failed: {e}")
    print("  Try: sys.path.append('/path/to/abhikarta')")

print("Test complete!")
```

---

## Contact

If you're still having issues after trying these solutions:

1. Run `python test_imports.py` and share the output
2. Share your directory structure: `tree -L 2` or `ls -R`
3. Share the complete error message with traceback

Email: ajsinha@gmail.com
GitHub: https://github.com/ajsinha/abhikarta


## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
