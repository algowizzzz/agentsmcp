# Monitoring System Quick Reference

## 📊 Available Pages

| Page | URL | Purpose |
|------|-----|---------|
| **Dashboard** | `/monitoring` | Overview of all system activity |
| **Users** | `/monitoring/users` | User logins, sessions, activity |
| **Tools** | `/monitoring/tools` | Tool executions and performance |
| **Agents** | `/monitoring/agents` | Agent executions and statistics |
| **DAGs** | `/monitoring/dags` | Workflow executions and status |
| **Planner** | `/monitoring/planner` | Plan generation and approvals |

## 🔌 API Endpoints

All endpoints return JSON and require authentication.

```
GET /api/monitoring/dashboard  - Dashboard stats
GET /api/monitoring/users      - User statistics
GET /api/monitoring/tools      - Tools statistics
GET /api/monitoring/agents     - Agent statistics
GET /api/monitoring/dags       - DAG/workflow statistics
GET /api/monitoring/planner    - Planner statistics
```

## 📈 Metrics Collected

### Time Periods
- **Today** - Since midnight today
- **Last 7 Days** - Rolling 7-day window
- **All Time** - Since system start
- **Hourly** - 10-minute intervals for last hour

### User Metrics
```python
{
    'today': 15,                    # Users active today
    'last_7_days': 42,             # Users active in last 7 days
    'total': 150,                  # Total registered users
    'hourly_data': [...],          # 7 data points (10-min intervals)
    'active_sessions': [...],      # Currently active sessions
    'user_stats': [...]            # Per-user statistics
}
```

### Tool/Agent Metrics
```python
{
    'today': 245,                   # Executions today
    'last_7_days': 1823,           # Executions in last 7 days
    'total': 12450,                # Total executions
    'success_rate': 94.5,          # Success percentage (last 7 days)
    'avg_time': '2.3s',            # Average execution time
    'hourly_data': [...],          # Execution counts by interval
    'tool_stats': [...]            # Per-tool/agent breakdown
}
```

### Workflow Metrics
```python
{
    'today': 67,                    # Workflows started today
    'last_7_days': 423,            # Workflows in last 7 days
    'total': 3241,                 # Total workflows
    'success_rate': 89.2,          # Completion rate
    'running_count': 5,            # Currently running
    'avg_duration': '45s',         # Average completion time
    'hourly_data': [...],          # Started/completed by interval
    'dag_stats': [...]             # Per-DAG statistics
}
```

### Planner Metrics
```python
{
    'today': 23,                    # Plans created today
    'last_7_days': 156,            # Plans in last 7 days
    'total': 892,                  # Total plans
    'approval_rate': 78.5,         # Approval percentage
    'conversations_today': 45,     # Conversations today
    'pending_approval': 8,         # Plans awaiting approval
    'hourly_data': [...],          # Plans/conversations by interval
    'status_distribution': {...},  # Plan status breakdown
    'top_users': [...],            # Most active users
    'recent_plans': [...]          # Recent plan list
}
```

## 🎨 Chart Types

### Line Charts
- User activity over time
- Workflow started/completed over time
- Plan generation over time

### Bar Charts
- Tool executions by interval
- Agent executions by interval

### Doughnut/Pie Charts
- Plan status distribution (pending/approved/rejected/executed)

### Progress Bars
- Success rates (per tool, agent, workflow)
- Approval rates

## ⚡ Auto-Refresh

All pages auto-refresh every **30 seconds**.

To change refresh interval, modify in each HTML file:
```javascript
setInterval(loadMonitoring, 30000);  // Change to your desired milliseconds
```

## 🗄️ Database Queries

### Quick Stats Query
```sql
-- User activity today
SELECT COUNT(DISTINCT user_id) 
FROM sessions 
WHERE created_at >= datetime('now', 'start of day');

-- Workflows success rate (last 7 days)
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
FROM workflows 
WHERE created_at >= datetime('now', '-7 days');

-- Currently running workflows
SELECT COUNT(*) 
FROM workflows 
WHERE status = 'running';
```

### Hourly Data Query
```sql
-- Tool executions in 10-minute window
SELECT COUNT(*) 
FROM workflow_nodes 
WHERE node_type = 'tool' 
  AND started_at >= ?
  AND started_at < ?;
```

## 🛠️ Common Customizations

### Add New Metric to Dashboard

1. **Update monitoring_service.py:**
```python
def get_dashboard_stats(self):
    # Add your metric
    custom_metric = self.db.fetchone("SELECT COUNT(*) ...")[0]
    
    return {
        # existing metrics...
        'custom_metric': custom_metric
    }
```

2. **Update monitoring_dashboard.html:**
```html
<div class="card">
    <div class="card-body">
        <h2 id="customMetric">-</h2>
        <small>Custom Metric</small>
    </div>
</div>
```

3. **Update JavaScript:**
```javascript
$('#customMetric').text(data.custom_metric || 0);
```

### Add New Chart

```javascript
let myChart = new Chart(ctx, {
    type: 'line',  // or 'bar', 'pie', 'doughnut'
    data: {
        labels: [...],
        datasets: [{
            label: 'My Data',
            data: [...],
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)'
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});
```

### Change Chart Time Range

In `monitoring_service.py`:

```python
def get_10min_intervals(self):
    # Change to 5-minute intervals for last 30 minutes
    intervals = []
    for i in range(6, -1, -1):  # 6 intervals
        time = now - timedelta(minutes=i * 5)
        # ... rest of code
```

## 🔒 Security Checklist

- [ ] All monitoring routes use `@login_required`
- [ ] Consider `@admin_required` for sensitive data
- [ ] API endpoints validate user permissions
- [ ] No sensitive data exposed in charts
- [ ] Rate limiting on API endpoints (optional)
- [ ] CORS configured properly if using separate frontend

## 🐛 Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In monitoring_service.py
logger = logging.getLogger(__name__)
logger.debug(f"Fetching stats: {query}")
```

### Test API Endpoint
```bash
# Using curl
curl -H "Cookie: session=YOUR_SESSION" \
     http://localhost:5000/api/monitoring/dashboard

# Using Python
import requests
response = requests.get(
    'http://localhost:5000/api/monitoring/dashboard',
    cookies={'session': 'YOUR_SESSION'}
)
print(response.json())
```

### Check Database
```bash
sqlite3 data/abhikarta.db

# Check table structure
.schema plans

# Check data
SELECT COUNT(*) FROM workflows;
SELECT COUNT(*) FROM workflow_nodes WHERE node_type = 'agent';
```

## 📱 Mobile Responsiveness

All pages use Bootstrap responsive classes:
- Cards stack on small screens
- Tables scroll horizontally
- Charts resize automatically
- Navigation collapses to hamburger menu

## 🎯 Performance Tips

### For Large Datasets (>10K records)

1. **Add indexes:**
```sql
CREATE INDEX idx_workflows_created_at ON workflows(created_at);
CREATE INDEX idx_workflow_nodes_started_at ON workflow_nodes(started_at);
CREATE INDEX idx_workflow_nodes_type ON workflow_nodes(node_type);
```

2. **Limit query results:**
```python
# In monitoring_service.py
LIMIT 1000  # Add to expensive queries
```

3. **Cache results:**
```python
from functools import lru_cache
from datetime import datetime

@lru_cache(maxsize=1)
def cached_dashboard_stats():
    return get_dashboard_stats()
```

4. **Reduce refresh frequency:**
```javascript
// Change from 30s to 60s
setInterval(loadMonitoring, 60000);
```

## 📦 Files Included

```
monitoring_dashboard.html       - Main dashboard page
monitoring_users.html          - User activity page
monitoring_tools.html          - Tools monitoring page
monitoring_agents.html         - Agents monitoring page
monitoring_dags.html           - Workflows monitoring page
monitoring_planner.html        - Planner monitoring page
monitoring_service.py          - Backend statistics service
monitoring_routes.py           - Flask route definitions
migrate_planner_tables.py     - Database migration script
navigation_snippet.html        - Navigation code snippet
MONITORING_SETUP_GUIDE.md     - Complete setup guide (this file)
```

## 🚀 Quick Start

```bash
# 1. Copy files
cp monitoring_*.html templates/
mkdir monitoring
cp monitoring_service.py monitoring/

# 2. Run migration
python migrate_planner_tables.py

# 3. Add routes to app.py
# (Copy from monitoring_routes.py)

# 4. Add nav link to base.html
# (Copy from navigation_snippet.html)

# 5. Restart Flask app
python app.py

# 6. Visit http://localhost:5000/monitoring
```

## 💡 Tips & Tricks

### Show Percentage Changes
```javascript
// In your stats update function
let today = data.today;
let yesterday = data.yesterday;
let change = ((today - yesterday) / yesterday * 100).toFixed(1);
$('#change').html(`<span class="${change > 0 ? 'text-success' : 'text-danger'}">
    ${change > 0 ? '+' : ''}${change}%
</span>`);
```

### Add Sparklines
```html
<canvas id="miniChart" width="100" height="30"></canvas>
```

### Export Data
```javascript
function exportToCSV() {
    let csv = 'Time,Count\n';
    hourlyData.forEach(d => {
        csv += `${d.time},${d.count}\n`;
    });
    
    let blob = new Blob([csv], {type: 'text/csv'});
    let url = window.URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.href = url;
    a.download = 'monitoring_data.csv';
    a.click();
}
```

### Add Notifications
```javascript
if (data.pending_hitl > 10) {
    alert(`Warning: ${data.pending_hitl} HITL requests pending!`);
}
```

## 📞 Support

Common issues:
1. **"No data" everywhere** → Generate some activity first
2. **Charts not showing** → Check Chart.js CDN is accessible
3. **API errors** → Check Flask logs with debug=True
4. **Slow performance** → Add database indexes

## ✅ Features Summary

- [x] Real-time dashboard with key metrics
- [x] 6 detailed monitoring pages
- [x] Charts with 10-minute intervals
- [x] Auto-refresh every 30 seconds
- [x] Success rate tracking
- [x] Per-component breakdowns
- [x] Recent activity feeds
- [x] Mobile responsive
- [x] Bootstrap 5 styling
- [x] Chart.js visualizations
- [x] RESTful API endpoints

**Last Updated:** October 29, 2025