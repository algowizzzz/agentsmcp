# Abhikarta - Quick Start Guide

## © 2025-2030 Ashutosh Sinha

## Installation

```bash
# Extract archive
tar -xzf abhikarta.tar.gz
cd abhikarta

# Install dependencies
pip install -r requirements.txt
```

## Start the System

### Terminal 1 - Start Mock MCP Server
```bash
python3 mcp_server/mock_mcp_server.py
```

### Terminal 2 - Start Main Application
```bash
python3 run_server.py
```

## Access the Application

1. Open browser: http://localhost:5001
2. Login with: admin / admin

## Try it Out

### Option 1: Use the AI Planner
1. Go to **Planner** page
2. Chat: "Create a plan to process data"
3. Review the generated plan
4. Approve and execute it

### Option 2: Execute a Pre-defined DAG
1. Go to **DAGs** page
2. Click **Execute** on "Simple Sequential Workflow"
3. Watch the workflow progress
4. Try "Parallel Processing with Human Review" to see HITL in action

### Option 3: Execute Tools or Agents Individually
1. Go to **Execute > Execute Tool**
2. Select a tool and provide parameters
3. Click **Execute Tool** and see results
4. Or go to **Execute > Execute Agent** to test agents

### Option 4: Manage Users (Admin Only)
1. Go to **Users** page
2. Click **Add User** to create new users
3. Click **Edit** to modify user permissions
4. Control access to tools, agents, and DAGs

## Default Users

- admin / admin - Full access
- user1 / user1 - Limited access
- user2 / user2 - Limited access

That's it! You're ready to go!


## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
