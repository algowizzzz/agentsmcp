# Human-in-the-Loop (HITL) System Documentation


## © 2025-2030 Ashutosh Sinha


## Overview

The Human-in-the-Loop (HITL) system in Abhikarta allows workflows to pause execution and wait for human approval before continuing. This is critical for workflows that require:
- Manual verification before proceeding
- Risk mitigation for high-stakes operations
- Compliance with approval processes
- Human judgment in ambiguous situations

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Workflow Execution                    │
│                                                          │
│  ┌──────┐    ┌──────┐    ┌──────────┐    ┌──────┐    │
│  │Node 1│───▶│Node 2│───▶│HITL Node │───▶│Node 4│    │
│  └──────┘    └──────┘    └────┬─────┘    └──────┘    │
│                                │                        │
│                                │ PAUSE                  │
│                                ▼                        │
│                       ┌────────────────┐               │
│                       │  HITL Request  │               │
│                       │   (Database)   │               │
│                       └────────┬───────┘               │
│                                │                        │
└────────────────────────────────┼────────────────────────┘
                                 │
                                 │
                    ┌────────────▼────────────┐
                    │    User Interface       │
                    │  (HITL Requests Page)   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  User Decision:         │
                    │  - Approve              │
                    │  - Reject               │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Orchestrator Resumes   │
                    │  or Fails Workflow      │
                    └─────────────────────────┘
```

## How HITL Works

### Phase 1: HITL Node Creation in Workflow

A HITL node is defined in a workflow plan like any other node:

```json
{
  "node_id": "approval_step",
  "node_type": "human_in_loop",
  "config": {
    "message": "Please approve the stock purchase of 1000 shares at $150/share",
    "input": {
      "context": {
        "stock": "AAPL",
        "shares": 1000,
        "price": 150
      }
    }
  },
  "dependencies": ["fetch_price", "analyze_risk"]
}
```

**Key Fields:**
- `node_type`: Must be `"human_in_loop"`
- `config.message`: Message displayed to the approver
- `config.input`: Context data for the approver
- `dependencies`: Nodes that must complete before HITL

### Phase 2: Workflow Execution Reaches HITL Node

When the orchestrator reaches a HITL node:

```python
# In orchestrator.py
def _execute_workflow(self, workflow_id: str, graph: Graph) -> None:
    while True:
        ready_nodes = graph.get_ready_nodes(completed_nodes)
        
        if not ready_nodes:
            # Check for HITL nodes
            hitl_nodes = [
                node for node in graph.nodes.values()
                if node.node_type == 'human_in_loop' 
                and node.status == NodeStatus.PENDING
                and node.is_ready(completed_nodes)
            ]
            
            if hitl_nodes:
                for hitl_node in hitl_nodes:
                    self._handle_hitl_node(workflow_id, hitl_node)
                break  # Exit and wait for HITL response
```

**What Happens:**
1. Orchestrator identifies HITL nodes that are ready
2. Calls `_handle_hitl_node()` for each
3. **Pauses workflow execution** (exits the execution loop)
4. Workflow status remains `'running'`
5. Node status changes to `'waiting_hitl'`

### Phase 3: HITL Request Creation

The orchestrator creates a HITL request in the database:

```python
def _handle_hitl_node(self, workflow_id: str, node: Node) -> None:
    request_id = str(uuid.uuid4())
    
    # Mark node as waiting
    node.status = NodeStatus.RUNNING
    self._update_node_status(
        workflow_id, 
        node.node_id, 
        'waiting_hitl',
        datetime.now().isoformat()
    )
    
    # Create HITL request in database
    self.db.insert('hitl_requests', {
        'request_id': request_id,
        'workflow_id': workflow_id,
        'node_id': node.node_id,
        'message': node.config.get('message', 'Approval required'),
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    })
    
    # Log event
    self._log_workflow_event(workflow_id, 'hitl_requested', {
        'node_id': node.node_id,
        'request_id': request_id
    })
```

**Database State:**
```
hitl_requests table:
┌──────────────┬──────────────┬─────────┬────────────┬─────────┐
│ request_id   │ workflow_id  │ node_id │ message    │ status  │
├──────────────┼──────────────┼─────────┼────────────┼─────────┤
│ req-abc-123  │ wf-xyz-789   │ step_3  │ Please...  │ pending │
└──────────────┴──────────────┴─────────┴────────────┴─────────┘

workflow_nodes table:
┌──────────────┬─────────┬──────────────┐
│ workflow_id  │ node_id │ status       │
├──────────────┼─────────┼──────────────┤
│ wf-xyz-789   │ step_3  │ waiting_hitl │
└──────────────┴─────────┴──────────────┘
```

### Phase 4: User Views HITL Request

Users navigate to the HITL Requests page (`/hitl_requests`):

```html
<!-- hitl_requests.html -->
<table class="table">
  <tr>
    <td>req-abc-123...</td>
    <td><a href="/workflow/wf-xyz-789">wf-xyz-789...</a></td>
    <td>Please approve stock purchase...</td>
    <td>2025-10-29 10:30</td>
    <td>
      <button onclick="approveHITL(...)">Approve</button>
      <button onclick="rejectHITL(...)">Reject</button>
    </td>
  </tr>
</table>
```

**The page shows:**
- Request ID
- Link to workflow detail
- Approval message
- Creation timestamp
- Approve/Reject buttons

### Phase 5a: User Approves Request

User clicks "Approve" and optionally provides a comment:

```javascript
function approveHITL(workflowId, requestId) {
    var response = prompt("Enter approval comment (optional):");
    if (response !== null) {
        $.ajax({
            url: '/api/hitl/approve',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                workflow_id: workflowId,
                request_id: requestId,
                response: response
            }),
            success: function() { 
                location.reload(); 
            }
        });
    }
}
```

**Backend Processing:**

```python
@app.route('/api/hitl/approve', methods=['POST'])
def api_hitl_approve():
    data = request.get_json()
    orchestrator = WorkflowOrchestrator()
    
    success = orchestrator.approve_hitl(
        workflow_id=data['workflow_id'],
        request_id=data['request_id'],
        user_id=session['user_id'],
        response=data.get('response', 'approved')
    )
    
    return jsonify({'success': success})
```

**Orchestrator Approval Logic:**

```python
def approve_hitl(self, workflow_id: str, request_id: str, 
                 user_id: str, response: str = 'approved') -> bool:
    # 1. Update HITL request in database
    self.db.update('hitl_requests', {
        'status': 'approved',
        'responded_at': datetime.now().isoformat(),
        'responded_by': user_id,
        'response': response
    }, 'request_id = ?', (request_id,))
    
    # 2. Get request details
    request = self.db.fetchone(
        "SELECT * FROM hitl_requests WHERE request_id = ?",
        (request_id,)
    )
    node_id = request['node_id']
    
    # 3. Update node status to completed
    self._update_node_status(
        workflow_id, 
        node_id, 
        'completed',
        None,
        datetime.now().isoformat(),
        json.dumps({'approved': True, 'response': response})
    )
    
    # 4. Log approval event
    self._log_workflow_event(workflow_id, 'hitl_approved', {
        'node_id': node_id,
        'request_id': request_id,
        'user_id': user_id
    })
    
    # 5. Resume workflow execution
    with self._lock:
        graph = self._active_workflows.get(workflow_id)
        if graph:
            node = graph.get_node(node_id)
            if node:
                node.status = NodeStatus.COMPLETED
                node.result = {
                    'approved': True, 
                    'response': response
                }
            
            # Continue execution in background thread
            thread = Thread(
                target=self._execute_workflow, 
                args=(workflow_id, graph)
            )
            thread.daemon = True
            thread.start()
    
    return True
```

**What Happens:**
1. HITL request marked as `'approved'` in database
2. Node status changes from `'waiting_hitl'` to `'completed'`
3. Node result contains approval details
4. Workflow event logged
5. **Workflow execution resumes** in background thread
6. Subsequent nodes can now execute

### Phase 5b: User Rejects Request

User clicks "Reject" and provides a reason:

```javascript
function rejectHITL(workflowId, requestId) {
    var reason = prompt("Enter rejection reason:");
    if (reason) {
        $.ajax({
            url: '/api/hitl/reject',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                workflow_id: workflowId,
                request_id: requestId,
                reason: reason
            }),
            success: function() { 
                location.reload(); 
            }
        });
    }
}
```

**Orchestrator Rejection Logic:**

```python
def reject_hitl(self, workflow_id: str, request_id: str, 
                user_id: str, reason: str = 'rejected') -> bool:
    # 1. Update HITL request
    self.db.update('hitl_requests', {
        'status': 'rejected',
        'responded_at': datetime.now().isoformat(),
        'responded_by': user_id,
        'response': reason
    }, 'request_id = ?', (request_id,))
    
    # 2. Fail the entire workflow
    self._fail_workflow(workflow_id, f'HITL rejected: {reason}')
    
    # 3. Log rejection event
    self._log_workflow_event(workflow_id, 'hitl_rejected', {
        'request_id': request_id,
        'user_id': user_id,
        'reason': reason
    })
    
    return True
```

**What Happens:**
1. HITL request marked as `'rejected'`
2. **Entire workflow fails** with rejection reason
3. Workflow status changes to `'failed'`
4. No further nodes execute
5. Workflow is removed from active workflows

### Phase 6: Workflow Continues or Fails

**If Approved:**
```
workflow status: running
node_3 status: completed (the HITL node)
node_4 status: running (next node starts)
node_5 status: pending (waiting for node_4)
```

**If Rejected:**
```
workflow status: failed
error: "HITL rejected: User specified this action is too risky"
node_3 status: waiting_hitl (HITL node never completed)
node_4 status: pending (never executed)
```

## Complete Example: Stock Purchase Workflow

### Workflow Definition

```json
{
  "dag_id": "stock_purchase_workflow",
  "name": "Stock Purchase with Approval",
  "description": "Analyzes and purchases stock with human approval",
  "nodes": [
    {
      "node_id": "fetch_price",
      "node_type": "tool",
      "tool_name": "get_stock_price",
      "config": {"input": {"symbol": "AAPL"}},
      "dependencies": []
    },
    {
      "node_id": "analyze_risk",
      "node_type": "agent",
      "agent_id": "risk_analyzer",
      "config": {"input": {"price_data": "${fetch_price.result}"}},
      "dependencies": ["fetch_price"]
    },
    {
      "node_id": "approval",
      "node_type": "human_in_loop",
      "config": {
        "message": "Risk analysis shows moderate risk. Approve purchase of 1000 AAPL shares?",
        "input": {
          "price": "${fetch_price.result.price}",
          "risk_score": "${analyze_risk.result.risk_score}"
        }
      },
      "dependencies": ["fetch_price", "analyze_risk"]
    },
    {
      "node_id": "execute_purchase",
      "node_type": "tool",
      "tool_name": "purchase_stock",
      "config": {
        "input": {
          "symbol": "AAPL",
          "shares": 1000,
          "approval": "${approval.result.response}"
        }
      },
      "dependencies": ["approval"]
    },
    {
      "node_id": "send_notification",
      "node_type": "tool",
      "tool_name": "send_email",
      "config": {
        "input": {
          "message": "Purchase complete: ${execute_purchase.result}"
        }
      },
      "dependencies": ["execute_purchase"]
    }
  ],
  "start_nodes": ["fetch_price"]
}
```

### Execution Timeline

```
Time   Event                           Status
─────  ──────────────────────────────  ─────────────────
10:00  Workflow starts                 running
10:00  Node: fetch_price starts        running
10:01  Node: fetch_price completes     completed
10:01  Node: analyze_risk starts       running
10:02  Node: analyze_risk completes    completed
10:02  Node: approval starts           waiting_hitl
10:02  HITL request created            pending
       ⏸️  WORKFLOW PAUSES
       
       ... (waiting for user) ...
       
10:15  User views HITL request         pending
10:16  User clicks Approve             approved
10:16  Node: approval completes        completed
10:16  ▶️  WORKFLOW RESUMES
10:16  Node: execute_purchase starts   running
10:17  Node: execute_purchase done     completed
10:17  Node: send_notification starts  running
10:17  Node: send_notification done    completed
10:17  Workflow completes              completed
```

### Database State During Execution

**After HITL Request Created (10:02):**

```sql
-- Workflow
SELECT * FROM workflows WHERE workflow_id = 'wf-123';
```
| workflow_id | status  | started_at | completed_at |
|-------------|---------|------------|--------------|
| wf-123      | running | 10:00      | NULL         |

```sql
-- Nodes
SELECT node_id, status FROM workflow_nodes WHERE workflow_id = 'wf-123';
```
| node_id          | status       |
|------------------|--------------|
| fetch_price      | completed    |
| analyze_risk     | completed    |
| approval         | waiting_hitl |
| execute_purchase | pending      |
| send_notification| pending      |

```sql
-- HITL Request
SELECT * FROM hitl_requests WHERE workflow_id = 'wf-123';
```
| request_id | workflow_id | node_id  | status  | message         |
|------------|-------------|----------|---------|-----------------|
| req-456    | wf-123      | approval | pending | Risk analysis...|

**After Approval (10:16):**

```sql
-- HITL Request Updated
SELECT * FROM hitl_requests WHERE request_id = 'req-456';
```
| request_id | status   | responded_by | response      | responded_at |
|------------|----------|--------------|---------------|--------------|
| req-456    | approved | user-789     | Looks good!   | 10:16        |

```sql
-- Node Updated
SELECT * FROM workflow_nodes WHERE workflow_id = 'wf-123' AND node_id = 'approval';
```
| node_id  | status    | result                                    |
|----------|-----------|-------------------------------------------|
| approval | completed | {"approved":true,"response":"Looks good!"}|

## HITL Use Cases

### 1. Financial Transactions
```json
{
  "node_type": "human_in_loop",
  "config": {
    "message": "Approve transfer of $10,000 to account XXX-1234?"
  }
}
```

### 2. Content Publication
```json
{
  "node_type": "human_in_loop",
  "config": {
    "message": "Review and approve blog post before publishing"
  }
}
```

### 3. Risk Mitigation
```json
{
  "node_type": "human_in_loop",
  "config": {
    "message": "Risk score is HIGH. Approve proceeding with deployment?"
  }
}
```

### 4. Quality Assurance
```json
{
  "node_type": "human_in_loop",
  "config": {
    "message": "Verify data quality before loading to production"
  }
}
```

### 5. Compliance
```json
{
  "node_type": "human_in_loop",
  "config": {
    "message": "Legal review required: Approve contract terms?"
  }
}
```

## API Endpoints

### Get Pending HITL Requests
```python
@app.route('/hitl_requests')
@login_required
def hitl_requests():
    orchestrator = WorkflowOrchestrator()
    requests = orchestrator.get_pending_hitl_requests()
    return render_template('hitl_requests.html', requests=requests)
```

### Approve HITL Request
```python
@app.route('/api/hitl/approve', methods=['POST'])
@login_required
def api_hitl_approve():
    data = request.get_json()
    orchestrator = WorkflowOrchestrator()
    
    success = orchestrator.approve_hitl(
        workflow_id=data['workflow_id'],
        request_id=data['request_id'],
        user_id=session['user_id'],
        response=data.get('response', 'approved')
    )
    
    return jsonify({'success': success})
```

### Reject HITL Request
```python
@app.route('/api/hitl/reject', methods=['POST'])
@login_required
def api_hitl_reject():
    data = request.get_json()
    orchestrator = WorkflowOrchestrator()
    
    success = orchestrator.reject_hitl(
        workflow_id=data['workflow_id'],
        request_id=data['request_id'],
        user_id=session['user_id'],
        reason=data.get('reason', 'rejected')
    )
    
    return jsonify({'success': success})
```

## Advanced Features

### Multiple HITL Nodes in Sequence

```json
{
  "nodes": [
    {"node_id": "draft", "node_type": "agent", ...},
    {"node_id": "review_1", "node_type": "human_in_loop", 
     "config": {"message": "First review"}, 
     "dependencies": ["draft"]},
    {"node_id": "revise", "node_type": "agent", 
     "dependencies": ["review_1"]},
    {"node_id": "review_2", "node_type": "human_in_loop",
     "config": {"message": "Final review"},
     "dependencies": ["revise"]},
    {"node_id": "publish", "node_type": "tool",
     "dependencies": ["review_2"]}
  ]
}
```

**Flow:**
1. Agent creates draft
2. Human reviews → if approved, continues
3. Agent revises based on feedback
4. Human final review → if approved, continues
5. Tool publishes content

### Parallel HITL Nodes

```json
{
  "nodes": [
    {"node_id": "analyze", "node_type": "agent", ...},
    {"node_id": "legal_review", "node_type": "human_in_loop",
     "dependencies": ["analyze"]},
    {"node_id": "financial_review", "node_type": "human_in_loop",
     "dependencies": ["analyze"]},
    {"node_id": "execute", "node_type": "tool",
     "dependencies": ["legal_review", "financial_review"]}
  ]
}
```

**Flow:**
- Both reviews can happen simultaneously
- Execution only proceeds if BOTH are approved
- If either is rejected, workflow fails

### Conditional HITL

```json
{
  "nodes": [
    {"node_id": "calculate_risk", "node_type": "agent", ...},
    {"node_id": "approval", "node_type": "human_in_loop",
     "config": {
       "message": "Risk score: ${calculate_risk.result.score}. Approve?",
       "condition": "${calculate_risk.result.score > 0.7}"
     },
     "dependencies": ["calculate_risk"]},
    {"node_id": "proceed", "node_type": "tool",
     "dependencies": ["calculate_risk", "approval"]}
  ]
}
```

**Note:** Current implementation doesn't support conditions, but this shows the pattern for future enhancement.

## Error Handling

### Timeout (Future Enhancement)
```python
# Not yet implemented, but planned:
{
  "node_type": "human_in_loop",
  "config": {
    "message": "Approve?",
    "timeout_seconds": 3600,  # 1 hour
    "timeout_action": "reject"  # or "approve"
  }
}
```

### Missing Responder
- HITL requests remain pending until responded to
- No automatic timeout currently
- Workflow stays in `running` status indefinitely

### Workflow Cleanup
```python
# Admin can manually fail abandoned workflows
db.update('workflows', 
  {'status': 'failed', 'error': 'Abandoned - no HITL response'},
  'workflow_id = ?', (workflow_id,))
```

## Security Considerations

### Access Control
```python
# Only authorized users should approve
@app.route('/api/hitl/approve', methods=['POST'])
@login_required
def api_hitl_approve():
    user = user_registry.get_user(session['user_id'])
    
    # Check if user has approval permission
    if not user.can_approve_hitl():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # ... proceed with approval
```

### Audit Trail
Every HITL action is logged:
```python
# In workflow_events table
{
  'event_type': 'hitl_approved',
  'event_data': {
    'request_id': 'req-456',
    'user_id': 'user-789',
    'response': 'Approved after review'
  }
}
```

### Double-Approval Prevention
```python
# Check status before approving
request = db.fetchone(
    "SELECT status FROM hitl_requests WHERE request_id = ?",
    (request_id,)
)

if request['status'] != 'pending':
    return jsonify({'error': 'Request already handled'})
```

## Monitoring and Metrics

### Key Metrics

**HITL Request Volume:**
```sql
SELECT COUNT(*) FROM hitl_requests 
WHERE created_at > datetime('now', '-24 hours');
```

**Average Response Time:**
```sql
SELECT AVG(
    JULIANDAY(responded_at) - JULIANDAY(created_at)
) * 86400 as avg_seconds
FROM hitl_requests 
WHERE status != 'pending';
```

**Approval Rate:**
```sql
SELECT 
    COUNT(CASE WHEN status = 'approved' THEN 1 END) * 1.0 / COUNT(*) 
FROM hitl_requests 
WHERE status != 'pending';
```

**Pending Requests:**
```sql
SELECT COUNT(*) FROM hitl_requests WHERE status = 'pending';
```

## Best Practices

### 1. Clear Messages
❌ Bad: "Approve?"
✅ Good: "Approve purchase of 1000 AAPL shares at $150/share (total: $150,000)?"

### 2. Provide Context
```json
{
  "message": "Approve deployment?",
  "input": {
    "environment": "production",
    "risk_score": 0.3,
    "last_deployment": "2025-10-20",
    "changes": "Updated user service, fixed 3 bugs"
  }
}
```

### 3. Strategic Placement
- Place HITL nodes AFTER data collection
- Place BEFORE irreversible actions
- Don't overuse - too many approvals slow workflows

### 4. Appropriate Granularity
- One HITL for entire operation (e.g., "Approve $10K transfer")
- Not multiple HITLs for sub-steps (e.g., "Open connection?", "Send data?", "Close connection?")

### 5. Timeout Strategy (Future)
- Set reasonable timeouts
- Define timeout behavior (auto-approve vs auto-reject)
- Notify if approval is time-sensitive

## Troubleshooting

### Issue: Workflow Stuck in Running Status
**Cause:** HITL request pending, waiting for approval
**Solution:**
```sql
-- Find pending HITL requests
SELECT * FROM hitl_requests 
WHERE workflow_id = ? AND status = 'pending';
```

### Issue: Node Shows waiting_hitl But No HITL Request
**Cause:** Request creation failed
**Solution:**
```sql
-- Check workflow events
SELECT * FROM workflow_events 
WHERE workflow_id = ? AND event_type = 'hitl_requested';
```

### Issue: Approved But Workflow Not Continuing
**Cause:** Workflow thread may have died
**Solution:** Current implementation requires workflow thread to be running. Future enhancement: periodic check for approved HITL requests.

## Summary

The HITL system provides:
- ✅ **Pause/Resume** - Workflows pause at HITL nodes and resume after approval
- ✅ **Approval/Rejection** - Users can approve (continue) or reject (fail workflow)
- ✅ **Audit Trail** - All approvals/rejections are logged with user and timestamp
- ✅ **Context Passing** - HITL nodes can access results from previous nodes
- ✅ **Flexible Placement** - HITL nodes can be placed anywhere in workflow
- ✅ **Multiple HITL** - Support for sequential and parallel HITL nodes
- ✅ **User Interface** - Dedicated page for viewing and responding to requests

**Key Components:**
1. **HITL Nodes** in workflow definitions
2. **Orchestrator** manages pause/resume
3. **Database** stores requests and responses
4. **Web UI** for user interaction
5. **Background Threads** for async execution

The system is production-ready for workflows requiring human judgment, approval processes, compliance checks, and risk mitigation.


## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
