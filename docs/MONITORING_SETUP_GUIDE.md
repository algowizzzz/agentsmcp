# Monitoring System Setup Guide

## Overview

This monitoring system provides real-time statistics and visualizations for:
- **User Activity** - Logins, sessions, and user behavior
- **Tools** - Tool executions, success rates, performance
- **Agents** - Agent executions, errors, statistics
- **DAGs/Workflows** - Workflow executions and success rates
- **Planner** - Plan generation, approvals, conversations

## Features

✅ Real-time statistics (today, last 7 days, all time)
✅ Charts showing activity in 10-minute intervals (last hour)
✅ Auto-refresh every 30 seconds
✅ Success rates and performance metrics
✅ Detailed breakdowns by component
✅ Recent activity feeds

## Installation Steps

### Step 1: Copy Template Files

Copy all HTML templates to your `templates/` directory:

```bash
cp monitoring_dashboard.html templates/
cp monitoring_users.html templates/
cp monitoring_tools.html templates/
cp monitoring_agents.html templates/
cp monitoring_dags.html templates/
cp monitoring_planner.html templates/
```

### Step 2: Create Monitoring Module

Create a `monitoring/` directory in your project:

```bash
mkdir -p monitoring
touch monitoring/__init__.py
cp monitoring_service.py monitoring/
```

### Step 3: Run Database Migration

Add the planner tables to your database:

```bash
python migrate_planner_tables.py
```

This creates:
- `plans` table
- `planner_conversations` table

### Step 4: Add Routes to Flask App

Add the monitoring routes to your main Flask application file (e.g., `app.py`):

```python
from monitoring.monitoring_service import MonitoringService

# ========== MONITORING PAGES ==========

@app.route('/monitoring')
@login_required
def monitoring_dashboard():
    """Main monitoring dashboard"""
    return render_template('monitoring_dashboard.html')

@app.route('/monitoring/users')
@login_required
def monitoring_users():
    """User activity monitoring page"""
    return render_template('monitoring_users.html')

@app.route('/monitoring/tools')
@login_required
def monitoring_tools():
    """Tools monitoring page"""
    return render_template('monitoring_tools.html')

@app.route('/monitoring/agents')
@login_required
def monitoring_agents():
    """Agents monitoring page"""
    return render_template('monitoring_agents.html')

@app.route('/monitoring/dags')
@login_required
def monitoring_dags():
    """DAGs/Workflows monitoring page"""
    return render_template('monitoring_dags.html')

@app.route('/monitoring/planner')
@login_required
def monitoring_planner():
    """Planner monitoring page"""
    return render_template('monitoring_planner.html')

# ========== MONITORING API ENDPOINTS ==========

@app.route('/api/monitoring/dashboard')
@login_required
def api_monitoring_dashboard_stats():
    """API endpoint for dashboard statistics"""
    try:
        monitoring = MonitoringService()
        stats = monitoring.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/users')
@login_required
def api_monitoring_users():
    """API endpoint for user monitoring statistics"""
    try:
        monitoring = MonitoringService()
        stats = monitoring.get_user_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/tools')
@login_required
def api_monitoring_tools():
    """API endpoint for tools monitoring statistics"""
    try:
        monitoring = MonitoringService()
        stats = monitoring.get_tools_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/agents')
@login_required
def api_monitoring_agents():
    """API endpoint for agents monitoring statistics"""
    try:
        monitoring = MonitoringService()
        stats = monitoring.get_agents_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/dags')
@login_required
def api_monitoring_dags():
    """API endpoint for DAGs monitoring statistics"""
    try:
        monitoring = MonitoringService()
        stats = monitoring.get_dags_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/planner')
@login_required
def api_monitoring_planner():
    """API endpoint for planner monitoring statistics"""
    try:
        monitoring = MonitoringService()
        stats = monitoring.get_planner_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Step 5: Update Navigation

Add the monitoring link to your navigation bar. See `navigation_snippet.html` for examples.

Option 1 - Dropdown menu:
```html
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="monitoringDropdown" 
       role="button" data-bs-toggle="dropdown">
        <i class="fas fa-chart-line"></i> Monitoring
    </a>
    <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="/monitoring">Dashboard</a></li>
        <li><a class="dropdown-item" href="/monitoring/users">User Activity</a></li>
        <!-- Add more items -->
    </ul>
</li>
```

Option 2 - Simple link:
```html
<li class="nav-item">
    <a class="nav-link" href="/monitoring">
        <i class="fas fa-chart-line"></i> Monitoring
    </a>
</li>
```

### Step 6: Verify Dependencies

Ensure you have Chart.js included in your templates (already included in the monitoring templates):

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
```

Also ensure jQuery is available (used for AJAX):

```html
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
```

## File Structure

After installation, your project should have:

```
your_project/
├── monitoring/
│   ├── __init__.py
│   └── monitoring_service.py
├── templates/
│   ├── monitoring_dashboard.html
│   ├── monitoring_users.html
│   ├── monitoring_tools.html
│   ├── monitoring_agents.html
│   ├── monitoring_dags.html
│   └── monitoring_planner.html
├── app.py (with monitoring routes)
└── migrate_planner_tables.py
```

## Testing

### 1. Run Database Migration

```bash
python migrate_planner_tables.py
```

Expected output:
```
Adding planner monitoring tables...
✓ Created plans table
✓ Created planner_conversations table

Migration complete!
```

### 2. Start Your Flask Application

```bash
python app.py
```

### 3. Access Monitoring Pages

Navigate to:
- Main Dashboard: http://localhost:5000/monitoring
- User Activity: http://localhost:5000/monitoring/users
- Tools: http://localhost:5000/monitoring/tools
- Agents: http://localhost:5000/monitoring/agents
- DAGs: http://localhost:5000/monitoring/dags
- Planner: http://localhost:5000/monitoring/planner

### 4. Test API Endpoints

```bash
# Test dashboard stats
curl http://localhost:5000/api/monitoring/dashboard

# Test user stats
curl http://localhost:5000/api/monitoring/users
```

## Features Breakdown

### Dashboard Page (`/monitoring`)
- Quick stats cards for users, workflows, agents, HITL
- Links to detailed monitoring pages
- Recent activity feed
- Auto-refreshes every 30 seconds

### User Activity Page (`/monitoring/users`)
- User logins by time period
- Hourly activity chart
- Active sessions table
- Per-user statistics (logins, workflows created)

### Tools Page (`/monitoring/tools`)
- Tool executions by time period
- Success rate with progress bar
- Average execution time
- Hourly execution chart
- Per-tool statistics table

### Agents Page (`/monitoring/agents`)
- Agent executions by time period
- Success rate with progress bar
- Average execution time
- Hourly execution chart
- Per-agent statistics table

### DAGs Page (`/monitoring/dags`)
- Workflow executions by time period
- Success rate
- Currently running workflows count
- Hourly started/completed chart
- Per-DAG statistics table

### Planner Page (`/monitoring/planner`)
- Plans generated by time period
- Approval rate
- Conversations count
- Pending approvals
- Hourly plans/conversations chart
- Plan status distribution (pie chart)
- Top users by plan count
- Recent plans table

## Customization

### Change Refresh Interval

In each monitoring HTML file, find:

```javascript
setInterval(loadMonitoring, 30000);  // 30 seconds
```

Change `30000` to your desired milliseconds (e.g., `60000` for 1 minute).

### Add More Statistics

Edit `monitoring_service.py` and add methods:

```python
def get_custom_stats(self):
    """Your custom statistics"""
    # Add your queries
    return {...}
```

Then add a corresponding API endpoint and update the frontend.

### Modify Chart Intervals

In `monitoring_service.py`, the `get_10min_intervals()` method creates 7 intervals (last hour).

To change to 5-minute intervals:

```python
for i in range(12, -1, -1):  # 12 intervals = 1 hour
    time = now - timedelta(minutes=i * 5)
```

### Add Alerts

You can add alerting by checking thresholds:

```python
def check_alerts(self):
    """Check for alert conditions"""
    alerts = []
    
    # Check for high failure rate
    stats = self.get_tools_stats()
    if stats['success_rate'] < 50:
        alerts.append({
            'type': 'error',
            'message': 'Tool success rate below 50%'
        })
    
    return alerts
```

## Troubleshooting

### Issue: "Table doesn't exist" errors

**Solution:** Run the migration script:
```bash
python migrate_planner_tables.py
```

### Issue: Charts not displaying

**Solution:** Check that Chart.js is loaded:
1. Open browser developer console
2. Look for errors related to Chart.js
3. Verify the CDN link is accessible

### Issue: "No data" in all tables

**Solution:** This is normal for a new installation. Generate some activity:
1. Create workflows
2. Execute agents/tools
3. Create user sessions
4. The monitoring will show data as activity occurs

### Issue: API endpoints return 500 errors

**Solution:** Check Flask logs for errors:
```bash
# Enable debug mode in Flask
app.run(debug=True)
```

Common issues:
- Import errors (monitoring module not in PYTHONPATH)
- Database connection issues
- Missing login_required decorator

### Issue: Auto-refresh not working

**Solution:** Check browser console for JavaScript errors. Ensure:
1. jQuery is loaded
2. No CORS issues
3. API endpoints are returning valid JSON

## Performance Considerations

### Large Databases

For databases with millions of records, consider:

1. **Add indexes:**
```sql
CREATE INDEX idx_workflows_created_at ON workflows(created_at);
CREATE INDEX idx_workflow_nodes_started_at ON workflow_nodes(started_at);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);
```

2. **Use pagination:**
```python
# Limit results in queries
LIMIT 100
```

3. **Cache statistics:**
```python
from functools import lru_cache
from datetime import datetime

@lru_cache(maxsize=128)
def cached_stats(cache_key):
    # Cache for 30 seconds
    pass
```

### High Traffic

For high-traffic sites:

1. **Reduce refresh frequency:**
   Change from 30s to 60s or 120s

2. **Use Redis for caching:**
```python
import redis
r = redis.Redis()

def get_cached_stats(key, ttl=30):
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    
    stats = compute_stats()
    r.setex(key, ttl, json.dumps(stats))
    return stats
```

3. **Offload to background jobs:**
   Pre-compute stats every minute and store in database

## Security

### Access Control

Ensure monitoring pages are protected:

```python
@app.route('/monitoring')
@login_required
@admin_required  # Add this for admin-only access
def monitoring_dashboard():
    return render_template('monitoring_dashboard.html')
```

### Rate Limiting

Add rate limiting to API endpoints:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/monitoring/dashboard')
@limiter.limit("10 per minute")
def api_monitoring_dashboard_stats():
    pass
```

## Next Steps

1. ✅ Install and test basic monitoring
2. ✅ Customize refresh intervals and chart intervals
3. ✅ Add monitoring link to navigation
4. ✅ Set up alerting (optional)
5. ✅ Add caching for performance (optional)
6. ✅ Implement access control
7. ✅ Monitor and tune database indexes

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Flask application logs
3. Check browser console for JavaScript errors
4. Verify database schema matches expected structure

## Summary

The monitoring system provides:
- ✅ **6 monitoring pages** with detailed statistics
- ✅ **6 API endpoints** for real-time data
- ✅ **Charts and visualizations** using Chart.js
- ✅ **Auto-refresh** capability
- ✅ **Time-based aggregations** (today, 7 days, all time, hourly)
- ✅ **Component breakdowns** (per-tool, per-agent, per-DAG, per-user)
- ✅ **Performance metrics** (success rates, execution times)

All code is production-ready and follows best practices for:
- Database querying
- Error handling
- Frontend/backend separation
- Real-time updates
- Responsive design