# Database & HITL Documentation Index


## © 2025-2030 Ashutosh Sinha


## Overview

This index provides quick access to comprehensive documentation on Abhikarta's database schema and Human-in-the-Loop (HITL) system.

## 📚 Available Documentation

### 1. [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
**Complete Database Schema Documentation**

**What's Inside:**
- All 9 database tables with complete column definitions
- Entity Relationship Diagram (ERD)
- Common SQL queries and examples
- Performance optimization tips
- Backup and maintenance procedures
- Migration strategies

**Tables Documented:**
- `users` - User accounts and authentication
- `sessions` - User session tracking
- `workflows` - Workflow execution records
- `workflow_nodes` - Individual node execution details
- `workflow_events` - Audit log of workflow events
- `agent_executions` - Agent execution tracking
- `hitl_requests` - Human-in-the-loop approval requests
- `plans` - AI-generated workflow plans
- `planner_conversations` - Chat history with AI planner

**Read this if you want to:**
- Understand the complete data model
- Write queries against the database
- Add new tables or columns
- Optimize database performance
- Set up backups
- Debug data issues

---

### 2. [HITL_SYSTEM.md](HITL_SYSTEM.md)
**Human-in-the-Loop System Documentation**

**What's Inside:**
- Complete HITL architecture explanation
- Step-by-step workflow execution with HITL
- Code examples and database state diagrams
- Real-world use cases
- API endpoints
- Best practices and troubleshooting

**Topics Covered:**
- How HITL nodes pause workflows
- Approval and rejection flows
- Database state during HITL
- Complete execution timeline examples
- Multiple HITL patterns (sequential, parallel)
- Security and access control
- Monitoring and metrics

**Read this if you want to:**
- Understand how HITL works
- Implement HITL in workflows
- Debug HITL issues
- Monitor HITL performance
- Design approval processes
- Ensure compliance and audit trails

---

## 🎯 Quick Reference

### Database Tables Quick View

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| **users** | User accounts | user_id, username, role |
| **sessions** | User sessions | session_id, user_id, workflow_id |
| **workflows** | Workflow executions | workflow_id, dag_id, status |
| **workflow_nodes** | Node executions | workflow_id, node_id, status |
| **workflow_events** | Audit log | workflow_id, event_type |
| **agent_executions** | Agent tracking | agent_id, status |
| **hitl_requests** | Approval requests | request_id, workflow_id, status |
| **plans** | Generated plans | plan_id, user_id, status |
| **planner_conversations** | Chat history | conversation_id, user_id |

### HITL Status Flow

```
Workflow Execution
       ↓
   HITL Node Reached
       ↓
  Request Created (status: pending)
       ↓
   Node Status: waiting_hitl
       ↓
   Workflow PAUSES
       ↓
   User Views Request
       ↓
    ┌──────┴──────┐
    ↓             ↓
 APPROVE       REJECT
    ↓             ↓
Request:       Request:
approved       rejected
    ↓             ↓
Node:          Workflow:
completed      failed
    ↓
Workflow
RESUMES
```

### Key Relationships

```
users (1) ──→ (N) sessions
users (1) ──→ (N) workflows
users (1) ──→ (N) plans

workflows (1) ──→ (N) workflow_nodes
workflows (1) ──→ (N) workflow_events
workflows (1) ──→ (N) hitl_requests

workflow_nodes (1) ──→ (N) hitl_requests

sessions (1) ──→ (N) workflows
```

---

## 🔍 Common Scenarios

### Scenario 1: Creating a Workflow with HITL

**Step 1:** Define workflow with HITL node
```json
{
  "node_id": "approval",
  "node_type": "human_in_loop",
  "config": {
    "message": "Please approve this action"
  },
  "dependencies": ["previous_step"]
}
```

**Step 2:** Execute workflow
- Workflow reaches HITL node
- Pauses execution
- Creates entry in `hitl_requests` table

**Step 3:** User approves
- Updates `hitl_requests.status = 'approved'`
- Updates `workflow_nodes.status = 'completed'`
- Workflow resumes

**Database tables involved:**
- `workflows` - Main workflow record
- `workflow_nodes` - HITL node record
- `hitl_requests` - Approval request
- `workflow_events` - Event log

---

### Scenario 2: Querying Workflow Status

```sql
-- Get workflow with all nodes
SELECT 
    w.workflow_id,
    w.name,
    w.status,
    n.node_id,
    n.status as node_status
FROM workflows w
LEFT JOIN workflow_nodes n ON w.workflow_id = n.workflow_id
WHERE w.workflow_id = ?;

-- Get pending HITL requests
SELECT 
    h.*,
    w.name as workflow_name
FROM hitl_requests h
JOIN workflows w ON h.workflow_id = w.workflow_id
WHERE h.status = 'pending'
ORDER BY h.created_at ASC;

-- Get workflow event timeline
SELECT * FROM workflow_events
WHERE workflow_id = ?
ORDER BY created_at ASC;
```

---

### Scenario 3: Monitoring HITL Performance

```sql
-- Pending requests count
SELECT COUNT(*) FROM hitl_requests 
WHERE status = 'pending';

-- Average approval time
SELECT AVG(
    JULIANDAY(responded_at) - JULIANDAY(created_at)
) * 86400 as avg_seconds
FROM hitl_requests 
WHERE status IN ('approved', 'rejected');

-- Approval rate
SELECT 
    status,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM hitl_requests
WHERE status != 'pending'
GROUP BY status;
```

---

## 📖 Reading Paths

### For Developers
1. Read **DATABASE_SCHEMA.md** - Sections 1-7 (Core tables)
2. Read **HITL_SYSTEM.md** - "How HITL Works" section
3. Review code examples in both documents

### For Architects
1. Read **DATABASE_SCHEMA.md** - Complete document
2. Read **HITL_SYSTEM.md** - Complete document
3. Review ERD and architecture diagrams
4. Study performance optimization sections

### For Operations
1. Read **DATABASE_SCHEMA.md** - Backup and maintenance sections
2. Read **HITL_SYSTEM.md** - Monitoring and troubleshooting sections
3. Review common queries

### For Business Analysts
1. Read **HITL_SYSTEM.md** - Overview and use cases
2. Skim **DATABASE_SCHEMA.md** - Table purposes only
3. Review HITL best practices

---

## 🛠️ Quick Start

### Setting Up Database

```python
from db.database import initialize_db

# SQLite (default)
db = initialize_db(db_type='sqlite', db_path='data/abhikarta.db')

# PostgreSQL
db = initialize_db(
    db_type='postgresql',
    host='localhost',
    database='abhikarta',
    user='postgres',
    password='password'
)
```

### Creating HITL Workflow
```python
workflow_plan = {
    "dag_id": "approval_workflow",
    "nodes": [
        {
            "node_id": "step1",
            "node_type": "agent",
            "agent_id": "data_collector",
            "dependencies": []
        },
        {
            "node_id": "approval",
            "node_type": "human_in_loop",
            "config": {
                "message": "Review data and approve next step"
            },
            "dependencies": ["step1"]
        },
        {
            "node_id": "step2",
            "node_type": "agent",
            "agent_id": "data_processor",
            "dependencies": ["approval"]
        }
    ],
    "start_nodes": ["step1"]
}
```

### Querying HITL Requests

```python
from workflows.dag.orchestrator import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()

# Get all pending requests
pending = orchestrator.get_pending_hitl_requests()

# Approve a request
orchestrator.approve_hitl(
    workflow_id='wf-123',
    request_id='req-456',
    user_id='user-789',
    response='Approved after review'
)
```

---

## 💡 Key Insights

### Database Design Principles
1. **Normalized Structure** - Minimal redundancy
2. **JSON Flexibility** - Complex data in JSON columns
3. **Audit Trail** - workflow_events table logs everything
4. **Dual Database Support** - SQLite for dev, PostgreSQL for prod
5. **Simple API** - Easy CRUD operations

### HITL Design Principles
1. **Non-Blocking** - Workflow pauses, system continues
2. **Audit Trail** - All approvals/rejections logged
3. **Context Passing** - HITL nodes access previous results
4. **Flexible Placement** - HITL anywhere in workflow
5. **User Control** - Humans make final decisions

---

## 🔗 Related Documentation

- **HOW_TOOLS_ARE_USED.md** - How tools integrate with workflows
- **TOOL_ENABLED_AGENT_EXAMPLE.md** - Agent architecture
- **CREATE_AGENT_TOOL_SUMMARY.md** - Creating agents and tools
- **DOCUMENTATION_INDEX.md** - Complete documentation index

---

## 📝 Summary

**Database:**
- 9 tables covering users, workflows, nodes, events, HITL, plans
- Supports SQLite and PostgreSQL
- Comprehensive audit trail
- Flexible JSON storage

**HITL:**
- Workflows pause at HITL nodes
- Users approve or reject via web UI
- Approval resumes workflow
- Rejection fails workflow
- Complete audit trail maintained

**Both systems work together to provide:**
- ✅ Persistent workflow state
- ✅ Human oversight of automated processes
- ✅ Complete audit trail
- ✅ Flexible workflow orchestration
- ✅ Production-ready reliability

For detailed information, see the full documentation files linked above.


## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
