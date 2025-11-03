# Monitoring System - Complete Artifacts Index

## 📦 Package Contents

This monitoring system provides comprehensive real-time monitoring for the Abhikarta workflow orchestration platform.

## 📄 Files Included

### HTML Templates (6 files)
Place these in your `templates/` directory:

1. **monitoring_dashboard.html** (4.2 KB)
   - Main monitoring dashboard with overview cards
   - Quick stats for users, workflows, agents, HITL
   - Links to detailed monitoring pages
   - Recent activity feed
   - Auto-refresh every 30 seconds

2. **monitoring_users.html** (3.5 KB)
   - User activity tracking
   - Login statistics (today, 7 days, all time)
   - Hourly activity chart
   - Active sessions table
   - Per-user statistics

3. **monitoring_tools.html** (3.6 KB)
   - Tool execution monitoring
   - Success rate tracking
   - Execution count statistics
   - Hourly execution chart
   - Per-tool breakdown with success rates

4. **monitoring_agents.html** (3.6 KB)
   - Agent execution monitoring
   - Success rate tracking
   - Performance metrics
   - Hourly execution chart
   - Per-agent statistics

5. **monitoring_dags.html** (3.8 KB)
   - Workflow/DAG execution monitoring
   - Success rate and running count
   - Started/completed chart
   - Per-DAG statistics
   - Average duration tracking

6. **monitoring_planner.html** (4.3 KB)
   - Plan generation monitoring
   - Approval rate tracking
   - Conversation statistics
   - Plan/conversation chart
   - Status distribution pie chart
   - Top users and recent plans

### Python Modules (3 files)

1. **monitoring_service.py** (10.5 KB)
   - Core monitoring service class
   - Statistics aggregation methods
   - Database query helpers
   - Time range calculations
   - 10-minute interval generation
   - Methods for all monitoring types:
     - `get_user_stats()`
     - `get_tools_stats()`
     - `get_agents_stats()`
     - `get_dags_stats()`
     - `get_planner_stats()`
     - `get_dashboard_stats()`

2. **monitoring_routes.py** (2.8 KB)
   - Flask route definitions for all pages
   - API endpoint definitions
   - Error handling
   - JSON response formatting
   - Routes:
     - `/monitoring` - Dashboard
     - `/monitoring/users` - User monitoring
     - `/monitoring/tools` - Tools monitoring
     - `/monitoring/agents` - Agents monitoring
     - `/monitoring/dags` - DAG monitoring
     - `/monitoring/planner` - Planner monitoring
   - API Endpoints:
     - `/api/monitoring/dashboard`
     - `/api/monitoring/users`
     - `/api/monitoring/tools`
     - `/api/monitoring/agents`
     - `/api/monitoring/dags`
     - `/api/monitoring/planner`

3. **migrate_planner_tables.py** (0.8 KB)
   - Database migration script
   - Creates `plans` table
   - Creates `planner_conversations` table
   - Can be run standalone

### Documentation (3 files)

1. **MONITORING_SETUP_GUIDE.md** (12.4 KB)
   - Complete installation instructions
   - Step-by-step setup process
   - File structure layout
   - Testing procedures
   - Feature breakdown
   - Customization guide
   - Troubleshooting section
   - Performance considerations
   - Security recommendations

2. **MONITORING_QUICK_REFERENCE.md** (8.2 KB)
   - Quick reference card
   - All available pages and URLs
   - API endpoint documentation
   - Metrics structure examples
   - Chart type reference
   - Common queries
   - Customization snippets
   - Debugging tips
   - Performance optimization

3. **monitoring_artifacts_index.md** (This file)
   - Complete file listing
   - Feature overview
   - Installation checklist
   - Usage examples

### Snippets (1 file)

1. **navigation_snippet.html** (0.9 KB)
   - Navigation bar code
   - Dropdown menu version
   - Simple link version
   - Bootstrap 5 compatible

## 🎯 Features Overview

### Dashboard Features
- ✅ Active users count (last 24 hours)
- ✅ Workflows created today
- ✅ Agent executions today
- ✅ Pending HITL requests
- ✅ Quick navigation cards
- ✅ Recent activity feed
- ✅ Auto-refresh (30s)

### User Monitoring Features
- ✅ User login counts (today/7days/all-time)
- ✅ Line chart of hourly activity
- ✅ Active sessions table with details
- ✅ Per-user statistics table
- ✅ Session tracking
- ✅ Workflow creation counts

### Tools Monitoring Features
- ✅ Tool execution counts (today/7days/all-time)
- ✅ Success rate percentage with progress bar
- ✅ Average execution time
- ✅ Bar chart of hourly executions
- ✅ Per-tool statistics table
- ✅ Success/failure breakdown
- ✅ Enabled/disabled status

### Agents Monitoring Features
- ✅ Agent execution counts (today/7days/all-time)
- ✅ Success rate percentage with progress bar
- ✅ Average execution time
- ✅ Bar chart of hourly executions
- ✅ Per-agent statistics table
- ✅ Success/failure breakdown
- ✅ Enabled/disabled status

### DAG Monitoring Features
- ✅ Workflow counts (today/7days/all-time)
- ✅ Success rate percentage
- ✅ Currently running workflows count
- ✅ Average duration
- ✅ Dual-line chart (started/completed)
- ✅ Per-DAG statistics table
- ✅ Status breakdown (completed/failed/running)

### Planner Monitoring Features
- ✅ Plan generation counts (today/7days/all-time)
- ✅ Approval rate percentage
- ✅ Conversation counts
- ✅ Pending approval count
- ✅ Dual-line chart (plans/conversations)
- ✅ Doughnut chart for status distribution
- ✅ Top users by plan count
- ✅ Recent plans table with status
- ✅ Plan status tracking

## 📊 Chart Types Used

### Line Charts
- User activity over time
- Workflow started/completed trends
- Plan and conversation trends

### Bar Charts
- Tool executions by time interval
- Agent executions by time interval

### Doughnut Charts
- Plan status distribution (pending/approved/rejected/executed)

### Progress Bars
- Success rates (inline with statistics)
- Approval rates

## 🗄️ Database Tables Used

### Existing Tables
- `users` - User accounts and information
- `sessions` - User sessions and activity
- `workflows` - Workflow executions
- `workflow_nodes` - Individual node executions
- `hitl_requests` - HITL approval requests

### New Tables (Created by Migration)
- `plans` - AI-generated workflow plans
- `planner_conversations` - Chat history with planner

## 🚀 Installation Checklist

- [ ] Copy 6 HTML templates to `templates/` directory
- [ ] Create `monitoring/` directory
- [ ] Copy `monitoring_service.py` to `monitoring/`
- [ ] Create `monitoring/__init__.py`
- [ ] Run `python migrate_planner_tables.py`
- [ ] Add routes from `monitoring_routes.py` to your Flask app
- [ ] Add navigation link from `navigation_snippet.html` to base template
- [ ] Verify Chart.js CDN is accessible
- [ ] Verify jQuery is available
- [ ] Test all monitoring pages
- [ ] Test all API endpoints

## 📱 Technology Stack

### Frontend
- **HTML5** - Page structure
- **Bootstrap 5** - Responsive UI framework
- **Chart.js 3.9.1** - Data visualization
- **jQuery 3.6.0** - AJAX and DOM manipulation
- **Font Awesome** - Icons

### Backend
- **Python 3.x** - Backend logic
- **Flask** - Web framework
- **SQLite/PostgreSQL** - Database
- **datetime** - Time calculations

## 🔗 Page URLs

```
Main Dashboard:      /monitoring
User Activity:       /monitoring/users
Tools Monitoring:    /monitoring/tools
Agents Monitoring:   /monitoring/agents
DAGs Monitoring:     /monitoring/dags
Planner Monitoring:  /monitoring/planner
```

## 🔌 API Endpoints

All endpoints require authentication and return JSON.

```
Dashboard Stats:     GET /api/monitoring/dashboard
User Stats:          GET /api/monitoring/users
Tools Stats:         GET /api/monitoring/tools
Agents Stats:        GET /api/monitoring/agents
DAGs Stats:          GET /api/monitoring/dags
Planner Stats:       GET /api/monitoring/planner
```

## 📈 Metrics Time Periods

All monitoring pages show metrics for:
1. **Today** - Since midnight (local time)
2. **Last 7 Days** - Rolling 7-day window
3. **All Time** - Since system installation
4. **Hourly** - Last hour in 10-minute intervals (7 data points)

## 🎨 Color Scheme

The monitoring pages use Bootstrap 5 color classes:
- **Primary (Blue)** - User-related items
- **Success (Green)** - Tools, successful operations
- **Info (Cyan)** - Agents, informational items
- **Warning (Yellow)** - DAGs, warnings
- **Secondary (Gray)** - Planner, neutral items
- **Danger (Red)** - Errors, failed operations

## 📊 Sample Data Structure

### Dashboard Stats Response
```json
{
  "active_users": 15,
  "workflows_today": 45,
  "agent_executions_today": 234,
  "pending_hitl": 3,
  "recent_activity": [
    {
      "type": "workflow",
      "type_color": "primary",
      "event": "Workflow started: Data Analysis",
      "user": "john_doe",
      "time": "2025-10-29T10:30:00"
    }
  ]
}
```

### User Stats Response
```json
{
  "today": 12,
  "last_7_days": 45,
  "total": 150,
  "hourly_data": [
    {"time": "09:40", "count": 2},
    {"time": "09:50", "count": 3},
    {"time": "10:00", "count": 5}
  ],
  "active_sessions": [...],
  "user_stats": [...]
}
```

## 🛠️ Customization Points

### Easy to Customize
- Refresh interval (default: 30 seconds)
- Chart time range (default: last hour)
- Chart interval size (default: 10 minutes)
- Color schemes
- Card layouts
- Table columns

### Advanced Customization
- Add new metrics
- Create custom charts
- Add alerting thresholds
- Implement caching
- Add export functionality
- Custom time ranges

## 🔒 Security Features

- ✅ Login required for all pages
- ✅ Login required for all API endpoints
- ✅ No sensitive data in charts
- ✅ SQL injection protection (parameterized queries)
- ✅ XSS protection (JSON responses)
- ⚠️ Add admin-only access as needed
- ⚠️ Add rate limiting as needed

## ⚡ Performance Features

- ✅ Efficient SQL queries with proper WHERE clauses
- ✅ Limited result sets (LIMIT in queries)
- ✅ Aggregated statistics (COUNT, SUM)
- ✅ Client-side caching (chart destruction/recreation)
- ⚠️ Add database indexes for large datasets
- ⚠️ Add Redis caching for high traffic
- ⚠️ Add pagination for large tables

## 📱 Responsive Design

All pages are mobile-responsive:
- ✅ Cards stack on mobile
- ✅ Tables scroll horizontally
- ✅ Charts resize automatically
- ✅ Navigation collapses to hamburger
- ✅ Touch-friendly buttons

## 🐛 Testing Checklist

### Manual Testing
- [ ] Dashboard loads without errors
- [ ] All 6 monitoring pages load
- [ ] Charts display correctly
- [ ] Auto-refresh works
- [ ] All tables show data (if available)
- [ ] Navigation links work
- [ ] Mobile view works

### API Testing
- [ ] All 6 API endpoints return valid JSON
- [ ] Error handling works (500 responses)
- [ ] Authentication required
- [ ] Data matches database

### Database Testing
- [ ] Migration script runs successfully
- [ ] All queries execute without errors
- [ ] Indexes improve performance (optional)

## 📚 Related Documentation

See also:
- **DATABASE_SCHEMA.md** - Complete database schema
- **HITL_SYSTEM.md** - Human-in-the-loop documentation
- **DOCUMENTATION_INDEX.md** - Complete system documentation

## 💡 Usage Examples

### Adding Monitoring to Existing Page

```html
<!-- In any page -->
<div class="card">
    <div class="card-header">Quick Stats</div>
    <div class="card-body">
        <p>Active Workflows: <strong id="workflowCount">-</strong></p>
    </div>
</div>

<script>
$.get('/api/monitoring/dags', function(data) {
    $('#workflowCount').text(data.running_count);
});
</script>
```

### Creating Custom Alert

```python
# In monitoring_service.py
def check_alerts(self):
    alerts = []
    stats = self.get_dags_stats()
    
    if stats['running_count'] > 10:
        alerts.append({
            'level': 'warning',
            'message': f"{stats['running_count']} workflows running"
        })
    
    return alerts
```

### Exporting Data

```javascript
// Add export button
function exportData() {
    $.get('/api/monitoring/users', function(data) {
        let csv = 'Time,Count\n';
        data.hourly_data.forEach(d => {
            csv += `${d.time},${d.count}\n`;
        });
        
        let blob = new Blob([csv], {type: 'text/csv'});
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        a.href = url;
        a.download = 'user_activity.csv';
        a.click();
    });
}
```

## 🎓 Learning Resources

### Understanding the Code

1. **Start with monitoring_dashboard.html**
   - See how cards fetch data
   - Understand AJAX pattern
   - Learn chart basics

2. **Read monitoring_service.py**
   - Understand time range calculations
   - Learn SQL aggregation
   - See data structure

3. **Review monitoring_routes.py**
   - Understand Flask routing
   - Learn error handling
   - See JSON responses

### Next Steps

1. Install the system
2. Generate some test data
3. View the monitoring pages
4. Customize refresh interval
5. Add your own metrics
6. Set up alerting

## 📞 Support & Troubleshooting

### Common Issues

**Q: Charts not displaying**
A: Verify Chart.js CDN is loaded. Check browser console for errors.

**Q: "No data" everywhere**
A: This is normal for new installations. Generate activity first.

**Q: API returns 500 error**
A: Check Flask logs. Ensure monitoring module is in Python path.

**Q: Auto-refresh not working**
A: Check browser console for JS errors. Verify API endpoints work.

### Getting Help

1. Read MONITORING_SETUP_GUIDE.md
2. Check MONITORING_QUICK_REFERENCE.md
3. Review Flask application logs
4. Inspect browser console
5. Verify database schema

## ✅ System Requirements

- Python 3.7+
- Flask 2.0+
- SQLite 3 or PostgreSQL
- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Internet connection (for CDN resources)

## 🎉 What's Included

### Summary
- **6 HTML pages** - Complete monitoring interface
- **3 Python files** - Backend logic and routes
- **3 Documentation files** - Setup and reference
- **1 Snippet file** - Navigation integration
- **Total: 13 files**

### Lines of Code
- HTML/JavaScript: ~1,200 lines
- Python: ~650 lines
- Documentation: ~1,500 lines
- **Total: ~3,350 lines**

### Features Count
- ✅ 6 Monitoring pages
- ✅ 6 API endpoints
- ✅ 10 Chart visualizations
- ✅ 15+ Statistics tables
- ✅ Auto-refresh capability
- ✅ Mobile responsive
- ✅ Real-time updates

## 🏆 Best Practices

This monitoring system follows best practices:
- ✅ Separation of concerns (templates/logic/routes)
- ✅ RESTful API design
- ✅ Responsive design
- ✅ Error handling
- ✅ Security (authentication)
- ✅ Performance (efficient queries)
- ✅ Maintainability (clear code structure)
- ✅ Documentation (comprehensive guides)

## 📅 Version History

**Version 1.0** (October 2025)
- Initial release
- 6 monitoring pages
- 6 API endpoints
- Chart.js integration
- Auto-refresh capability
- Complete documentation

## 📄 License

© 2025-2030 Ashutosh Sinha
All files included in this monitoring system.

---

**Ready to install?** Start with MONITORING_SETUP_GUIDE.md for step-by-step instructions!

**Need quick answers?** Check MONITORING_QUICK_REFERENCE.md for common tasks!

**Have questions?** Review the troubleshooting sections in the documentation!