# Abhikarta Database Schema Documentation


## © 2025-2030 Ashutosh Sinha


## Overview

Abhikarta uses a simple but comprehensive database schema to support workflow orchestration, agent execution, human-in-the-loop approvals, and AI-powered planning. The system supports both SQLite (default) and PostgreSQL.

## Database Configuration

### SQLite (Default)
```python
Database(db_type='sqlite', db_path='data/abhikarta.db')
```

### PostgreSQL
```python
Database(
    db_type='postgresql',
    host='localhost',
    port=5432,
    database='abhikarta',
    user='postgres',
    password='yourpassword'
)
```

## Complete Schema

### 1. Users Table

Stores user information and authentication details.

```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT,
    email TEXT,
    role TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
)
```

**Columns:**
- `user_id` - Unique identifier (UUID)
- `username` - Unique username for login
- `full_name` - User's full name
- `email` - Email address
- `role` - User role (admin, user, etc.)
- `created_at` - Account creation timestamp
- `last_login` - Last login timestamp

**Relationships:**
- One-to-many with `sessions`
- One-to-many with `workflows`
- One-to-many with `hitl_requests` (responded_by)

**Indexes:**
- PRIMARY KEY on `user_id`
- UNIQUE on `username`

---

### 2. Sessions Table

Tracks user sessions and their associated workflows.

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    workflow_id TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    metadata TEXT
)
```

**Columns:**
- `session_id` - Unique session identifier (UUID)
- `user_id` - Reference to user
- `workflow_id` - Current workflow (if any)
- `status` - Session status (active, completed, expired)
- `created_at` - Session start time
- `updated_at` - Last activity time
- `completed_at` - Session end time
- `metadata` - Additional session data (JSON)

**Relationships:**
- Many-to-one with `users`
- One-to-many with `workflows`

**Status Values:**
- `active` - Session is active
- `completed` - Session completed normally
- `expired` - Session timed out

---

### 3. Workflows Table

Core table for workflow execution tracking.

```sql
CREATE TABLE workflows (
    workflow_id TEXT PRIMARY KEY,
    dag_id TEXT NOT NULL,
    session_id TEXT,
    name TEXT,
    description TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    completed_at TEXT,
    created_by TEXT,
    graph_json TEXT,
    result TEXT,
    error TEXT
)
```

**Columns:**
- `workflow_id` - Unique workflow identifier (UUID)
- `dag_id` - Reference to DAG definition
- `session_id` - Associated session
- `name` - Workflow name
- `description` - Workflow description
- `status` - Current status
- `created_at` - Creation timestamp
- `started_at` - Execution start time
- `completed_at` - Completion time
- `created_by` - User who created workflow
- `graph_json` - Complete graph structure (JSON)
- `result` - Final result (JSON)
- `error` - Error message if failed

**Relationships:**
- Many-to-one with `sessions`
- One-to-many with `workflow_nodes`
- One-to-many with `workflow_events`
- One-to-many with `hitl_requests`
- One-to-many with `agent_executions`

**Status Values:**
- `pending` - Workflow created, not started
- `running` - Currently executing
- `completed` - Successfully completed
- `failed` - Execution failed
- `cancelled` - Manually cancelled

**Indexes Recommended:**
- PRIMARY KEY on `workflow_id`
- INDEX on `dag_id`
- INDEX on `session_id`
- INDEX on `status`
- INDEX on `created_by`

---

### 4. Workflow Nodes Table

Stores execution details for individual workflow nodes.

```sql
CREATE TABLE workflow_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    node_type TEXT,
    agent_id TEXT,
    status TEXT DEFAULT 'pending',
    started_at TEXT,
    completed_at TEXT,
    result TEXT,
    error TEXT,
    config TEXT,
    UNIQUE(workflow_id, node_id)
)
```

**Columns:**
- `id` - Auto-incrementing primary key
- `workflow_id` - Parent workflow
- `node_id` - Node identifier within workflow
- `node_type` - Type of node (agent, tool, human_in_loop)
- `agent_id` - Agent ID for agent nodes
- `status` - Node execution status
- `started_at` - Node start time
- `completed_at` - Node completion time
- `result` - Node execution result (JSON)
- `error` - Error message if failed
- `config` - Node configuration (JSON)

**Relationships:**
- Many-to-one with `workflows`
- One-to-many with `hitl_requests`

**Node Types:**
- `agent` - Executes an agent
- `tool` - Executes a tool
- `human_in_loop` - Requires human approval

**Status Values:**
- `pending` - Not yet executed
- `running` - Currently executing
- `waiting_hitl` - Waiting for human approval
- `completed` - Successfully completed
- `failed` - Execution failed
- `skipped` - Skipped due to conditions

**Indexes Recommended:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `(workflow_id, node_id)`
- INDEX on `workflow_id`
- INDEX on `status`

---

### 5. Workflow Events Table

Audit log for workflow execution events.

```sql
CREATE TABLE workflow_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

**Columns:**
- `id` - Auto-incrementing primary key
- `workflow_id` - Associated workflow
- `event_type` - Type of event
- `event_data` - Event details (JSON)
- `created_at` - Event timestamp

**Relationships:**
- Many-to-one with `workflows`

**Event Types:**
- `workflow_started` - Workflow execution began
- `workflow_completed` - Workflow finished successfully
- `workflow_failed` - Workflow failed
- `node_started` - Node execution began
- `node_completed` - Node finished successfully
- `node_failed` - Node execution failed
- `hitl_requested` - HITL approval requested
- `hitl_approved` - HITL request approved
- `hitl_rejected` - HITL request rejected

**Example Event Data:**
```json
{
  "node_id": "step_1",
  "node_type": "agent",
  "agent_id": "echo_agent",
  "result": {"success": true, "output": "..."}
}
```

**Indexes Recommended:**
- PRIMARY KEY on `id`
- INDEX on `workflow_id`
- INDEX on `event_type`
- INDEX on `created_at`

---

### 6. Agent Executions Table

Detailed tracking of agent executions (optional, for analytics).

```sql
CREATE TABLE agent_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT UNIQUE NOT NULL,
    agent_id TEXT NOT NULL,
    workflow_id TEXT,
    node_id TEXT,
    input TEXT,
    output TEXT,
    status TEXT DEFAULT 'pending',
    started_at TEXT,
    completed_at TEXT,
    error TEXT
)
```

**Columns:**
- `id` - Auto-incrementing primary key
- `execution_id` - Unique execution identifier (UUID)
- `agent_id` - Agent that was executed
- `workflow_id` - Associated workflow (if any)
- `node_id` - Associated workflow node (if any)
- `input` - Agent input data (JSON)
- `output` - Agent output data (JSON)
- `status` - Execution status
- `started_at` - Start timestamp
- `completed_at` - Completion timestamp
- `error` - Error message if failed

**Relationships:**
- Many-to-one with `workflows` (optional)
- Many-to-one with `workflow_nodes` (optional)

**Status Values:**
- `pending` - Queued for execution
- `running` - Currently executing
- `completed` - Successfully completed
- `failed` - Execution failed

**Use Cases:**
- Analytics on agent performance
- Debugging agent issues
- Usage tracking
- Performance monitoring

**Indexes Recommended:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `execution_id`
- INDEX on `agent_id`
- INDEX on `workflow_id`
- INDEX on `status`

---

### 7. HITL Requests Table

Manages human-in-the-loop approval requests.

```sql
CREATE TABLE hitl_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT UNIQUE NOT NULL,
    workflow_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    responded_at TEXT,
    responded_by TEXT,
    response TEXT
)
```

**Columns:**
- `id` - Auto-incrementing primary key
- `request_id` - Unique request identifier (UUID)
- `workflow_id` - Parent workflow
- `node_id` - Node awaiting approval
- `message` - Message/context for approver
- `status` - Request status
- `created_at` - Request creation time
- `responded_at` - Response timestamp
- `responded_by` - User who responded
- `response` - Approval comment or rejection reason

**Relationships:**
- Many-to-one with `workflows`
- Many-to-one with `workflow_nodes`
- Many-to-one with `users` (responded_by)

**Status Values:**
- `pending` - Awaiting response
- `approved` - Request approved
- `rejected` - Request rejected

**Indexes Recommended:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `request_id`
- INDEX on `workflow_id`
- INDEX on `status`
- INDEX on `created_at`

---

### 8. Plans Table

Stores AI-generated workflow plans awaiting approval.

```sql
CREATE TABLE plans (
    plan_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    request TEXT,
    plan_json TEXT,
    status TEXT DEFAULT 'pending_approval',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    approved_at TEXT,
    rejected_at TEXT,
    rejection_reason TEXT
)
```

**Columns:**
- `plan_id` - Unique plan identifier
- `user_id` - User who requested the plan
- `request` - Original natural language request
- `plan_json` - Generated plan structure (JSON)
- `status` - Plan status
- `created_at` - Plan creation time
- `approved_at` - Approval timestamp
- `rejected_at` - Rejection timestamp
- `rejection_reason` - Reason for rejection

**Relationships:**
- Many-to-one with `users`

**Status Values:**
- `pending_approval` - Awaiting user approval
- `approved` - Plan approved, ready for execution
- `rejected` - Plan rejected by user
- `executed` - Plan has been executed

**Plan JSON Structure:**
```json
{
  "dag_id": "generated_plan_abc123",
  "name": "Stock Analysis Workflow",
  "description": "Analyzes stock data",
  "nodes": [
    {
      "node_id": "step_1",
      "node_type": "tool",
      "tool_name": "get_stock_price",
      "config": {"input": {"symbol": "AAPL"}},
      "dependencies": []
    }
  ],
  "start_nodes": ["step_1"]
}
```

**Indexes Recommended:**
- PRIMARY KEY on `plan_id`
- INDEX on `user_id`
- INDEX on `status`
- INDEX on `created_at`

---

### 9. Planner Conversations Table

Stores conversation history with the AI planner.

```sql
CREATE TABLE planner_conversations (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    message TEXT,
    response TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

**Columns:**
- `conversation_id` - Unique conversation identifier (UUID)
- `user_id` - User having the conversation
- `message` - User's message
- `response` - AI planner's response
- `created_at` - Message timestamp

**Relationships:**
- Many-to-one with `users`

**Use Cases:**
- Chat history
- Context for multi-turn conversations
- Analytics on user interactions
- Improving planner responses

**Indexes Recommended:**
- PRIMARY KEY on `conversation_id`
- INDEX on `user_id`
- INDEX on `created_at`

---

## Entity Relationship Diagram

```
┌─────────────┐
│   Users     │
│             │
│ user_id (PK)│──┐
│ username    │  │
│ role        │  │
└─────────────┘  │
                 │
                 │ 1:N
                 │
        ┌────────┴────────┐
        │                 │
        │                 │
┌───────▼───────┐  ┌──────▼──────┐
│   Sessions    │  │   Workflows │
│               │  │             │
│ session_id(PK)│  │workflow_id  │──┐
│ user_id (FK)  │  │(PK)         │  │
│ workflow_id   │──│dag_id       │  │
└───────────────┘  │created_by   │  │
                   │(FK)         │  │
                   └─────────────┘  │
                         │          │
                         │ 1:N      │ 1:N
                    ┌────┴────┐     │
                    │         │     │
           ┌────────▼──┐ ┌────▼────▼────┐
           │Workflow   │ │Workflow_Events│
           │Nodes      │ │               │
           │           │ │id (PK)        │
           │node_id(PK)│ │workflow_id(FK)│
           │workflow_id│ │event_type     │
           │(FK)       │ └───────────────┘
           │node_type  │
           └───┬───────┘
               │
               │ 1:N
               │
       ┌───────▼────────┐
       │  HITL_Requests │
       │                │
       │request_id (PK) │
       │workflow_id (FK)│
       │node_id (FK)    │
       │responded_by(FK)│
       └────────────────┘

┌─────────────────┐        ┌──────────────────┐
│     Plans       │        │   Planner        │
│                 │        │   Conversations  │
│plan_id (PK)     │        │                  │
│user_id (FK)     │        │conversation_id   │
│plan_json        │        │(PK)              │
│status           │        │user_id (FK)      │
└─────────────────┘        └──────────────────┘
```

---

## Common Queries

### Get Active Workflows
```sql
SELECT * FROM workflows 
WHERE status = 'running' 
ORDER BY started_at DESC;
```

### Get Pending HITL Requests
```sql
SELECT h.*, w.name as workflow_name 
FROM hitl_requests h
JOIN workflows w ON h.workflow_id = w.workflow_id
WHERE h.status = 'pending'
ORDER BY h.created_at ASC;
```

### Get Workflow Execution Details
```sql
SELECT 
    w.*,
    (SELECT COUNT(*) FROM workflow_nodes WHERE workflow_id = w.workflow_id) as total_nodes,
    (SELECT COUNT(*) FROM workflow_nodes WHERE workflow_id = w.workflow_id AND status = 'completed') as completed_nodes
FROM workflows w
WHERE w.workflow_id = ?;
```

### Get User's Recent Plans
```sql
SELECT * FROM plans 
WHERE user_id = ? 
ORDER BY created_at DESC 
LIMIT 10;
```

### Get Workflow Event Log
```sql
SELECT * FROM workflow_events 
WHERE workflow_id = ? 
ORDER BY created_at ASC;
```

### Agent Performance Statistics
```sql
SELECT 
    agent_id,
    COUNT(*) as total_executions,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    AVG(JULIANDAY(completed_at) - JULIANDAY(started_at)) * 86400 as avg_duration_seconds
FROM agent_executions
GROUP BY agent_id;
```

---

## Data Types and Formats

### Timestamps
All timestamps are stored as ISO 8601 strings:
```
2025-10-29T12:34:56.789Z
```

### JSON Fields
Fields storing JSON data:
- `sessions.metadata`
- `workflows.graph_json`
- `workflows.result`
- `workflow_nodes.result`
- `workflow_nodes.config`
- `workflow_events.event_data`
- `agent_executions.input`
- `agent_executions.output`
- `plans.plan_json`

### UUIDs
All ID fields (except auto-increment) use UUID v4:
```
550e8400-e29b-41d4-a716-446655440000
```

---

## Database Migrations

### Adding a New Table
```python
db = get_db()
db.execute("""
    CREATE TABLE IF NOT EXISTS new_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        field1 TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")
```

### Adding a Column
```python
# SQLite doesn't support ALTER COLUMN easily
# Recommended: Create new table, copy data, drop old, rename

# For simple additions:
db.execute("ALTER TABLE workflows ADD COLUMN new_field TEXT")
```

---

## Performance Considerations

### Recommended Indexes

```sql
-- Workflows
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_created_by ON workflows(created_by);
CREATE INDEX idx_workflows_dag_id ON workflows(dag_id);

-- Workflow Nodes
CREATE INDEX idx_workflow_nodes_workflow_id ON workflow_nodes(workflow_id);
CREATE INDEX idx_workflow_nodes_status ON workflow_nodes(status);

-- Workflow Events
CREATE INDEX idx_workflow_events_workflow_id ON workflow_events(workflow_id);
CREATE INDEX idx_workflow_events_created_at ON workflow_events(created_at);

-- HITL Requests
CREATE INDEX idx_hitl_requests_workflow_id ON hitl_requests(workflow_id);
CREATE INDEX idx_hitl_requests_status ON hitl_requests(status);

-- Plans
CREATE INDEX idx_plans_user_id ON plans(user_id);
CREATE INDEX idx_plans_status ON plans(status);

-- Agent Executions
CREATE INDEX idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX idx_agent_executions_workflow_id ON agent_executions(workflow_id);
```

### Query Optimization Tips

1. **Use Indexes** - Add indexes on frequently queried columns
2. **Limit Result Sets** - Always use LIMIT for large tables
3. **Connection Pooling** - Reuse database connections
4. **Batch Operations** - Insert multiple rows in single transaction
5. **Vacuum** (SQLite) - Periodically vacuum to reclaim space

---

## Backup and Maintenance

### SQLite Backup
```bash
# Simple copy (when DB is not in use)
cp data/abhikarta.db data/abhikarta.db.backup

# Using SQLite command
sqlite3 data/abhikarta.db ".backup data/abhikarta.db.backup"
```

### PostgreSQL Backup
```bash
pg_dump abhikarta > abhikarta_backup.sql
```

### Cleanup Old Data
```python
# Delete old completed workflows
db.execute("""
    DELETE FROM workflows 
    WHERE status = 'completed' 
    AND completed_at < datetime('now', '-30 days')
""")

# Archive old events
db.execute("""
    DELETE FROM workflow_events 
    WHERE created_at < datetime('now', '-90 days')
""")
```

---

## Summary

The Abhikarta database schema is designed for:
- ✅ **Workflow orchestration** with DAG-based execution
- ✅ **Human-in-the-loop** approvals with full audit trail
- ✅ **AI-powered planning** with conversation history
- ✅ **Agent/tool execution** tracking
- ✅ **Comprehensive event logging** for debugging
- ✅ **User session management** for multi-user support
- ✅ **Scalability** - Works with SQLite for small deployments, PostgreSQL for production

**Total Tables: 9**
- Core: users, sessions, workflows, workflow_nodes, workflow_events
- Execution: agent_executions, hitl_requests
- Planning: plans, planner_conversations

**Key Design Principles:**
- Simple normalized structure
- Comprehensive audit trail
- Flexible JSON storage for complex data
- Support for both embedded (SQLite) and server (PostgreSQL) databases

## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
