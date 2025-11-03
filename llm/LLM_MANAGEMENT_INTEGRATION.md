# LLM Management Integration Guide

## 📦 Files Delivered

1. **llm_management.html** - Frontend UI page
2. **llm_routes.py** - Backend routes for LLM management
3. **auth_routes_updated.py** - Updated auth routes with LLM integration
4. **base_updated.html** - Updated navbar with LLM management link

## 🔧 Integration Steps

### Step 1: Place Files in Your Project

```
your_project/
├── templates/
│   ├── llm_management.html          ← NEW
│   └── base.html                    ← UPDATE with base_updated.html
├── routes/
│   ├── llm_routes.py                ← NEW
│   └── auth_routes.py               ← UPDATE with auth_routes_updated.py
└── config/
    └── llm/
        └── llm_config.json          ← Already created
```

### Step 2: Update Your Main Application File

In your main Flask application file (e.g., `app.py` or `main.py`), add:

```python
from flask import Flask
from llm.llm_facade_enhanced import LLMFacade
from routes.auth_routes import AuthRoutes, initialize_llm_routes

# ... your existing code ...

# Initialize Flask app
app = Flask(__name__)

# Initialize auth routes
auth_routes = AuthRoutes(app, user_registry, get_db)

# ============ NEW: Initialize LLM routes ============
initialize_llm_routes(
    app=app,
    llm_facade_class=LLMFacade,
    auth_routes=auth_routes
)
# ===================================================

# ... rest of your code ...
```

### Step 3: Update Templates

Replace your existing `templates/base.html` with `base_updated.html`:

```bash
cp base_updated.html templates/base.html
```

Copy the new LLM management template:

```bash
cp llm_management.html templates/
```

### Step 4: Ensure LLM Facade is Available

Make sure your LLM facade files are in place:

```
your_project/
├── llm/
│   ├── __init__.py
│   ├── llm_facade_enhanced.py
│   └── llm_config.json
└── config/
    └── llm/
        └── llm_config.json          ← Symlink or copy
```

### Step 5: Add Jinja2 Template Filter

Add this custom filter to your Flask app to format numbers:

```python
@app.template_filter('format_number')
def format_number(value):
    """Format number with thousands separator"""
    try:
        # Convert to number and format
        num = float(value)
        if num >= 1000:
            return f"{num/1000:.0f}"
        return str(int(num))
    except:
        return str(value)

# Register the filter
app.jinja_env.filters['format_number'] = format_number
```

## 🎯 Features Available

### User Features (All Users)

1. **View All LLMs**
   - Browse all configured providers and models
   - See model specifications, costs, and capabilities
   - Filter by provider using tabs

2. **Model Details**
   - View detailed information about any model
   - See pricing, context windows, and features
   - Understand what each model is best for

3. **Test Models**
   - Test individual models with a simple prompt
   - See response time and output
   - Verify connectivity

### Admin Features (Admin Users Only)

1. **Refresh Configuration**
   - Reload LLM config from file
   - No application restart needed

2. **Test All Connections**
   - Test connectivity to all enabled providers
   - See which providers are working

3. **Set Default LLM**
   - Change the system-wide default LLM
   - Updates configuration file automatically

4. **Enable/Disable Models**
   - Toggle individual models on/off
   - Disable entire providers

5. **Enable/Disable Providers**
   - Toggle all models for a provider at once

## 📋 API Endpoints Added

All endpoints require authentication. Admin endpoints require admin role.

### Public Endpoints (Login Required)

- `GET /llm-management` - LLM management page
- `GET /api/llm/model-details?provider=X&model=Y` - Get model details
- `POST /api/llm/test-model` - Test a specific model
- `GET /api/llm/available-models` - List all available models
- `GET /api/llm/recommend-model?task_type=X` - Get recommended model

### Admin Endpoints

- `POST /api/llm/refresh` - Refresh configuration
- `POST /api/llm/test-all` - Test all connections
- `POST /api/llm/set-default` - Set default LLM
- `POST /api/llm/toggle-model` - Enable/disable a model
- `POST /api/llm/toggle-provider` - Enable/disable a provider

## 🔍 Testing the Integration

### 1. Test the Page Loads

```bash
# Start your Flask app
python app.py

# Navigate to: http://localhost:5000/llm-management
```

You should see:
- Summary cards showing provider/model counts
- Tabs for each provider
- Table of all models

### 2. Test Model Details

Click the info icon (ℹ️) on any model to see:
- Full model specifications
- Pricing information
- Capabilities

### 3. Test a Model

Click the test icon (🧪) on any enabled model to:
- Send a test prompt
- See the response
- Verify the model works

### 4. Admin Functions (if admin)

- Click "Refresh Config" to reload configuration
- Click "Test Connections" to test all providers
- Click the star (⭐) to set a model as default
- Click enable/disable buttons to toggle models

## 🐛 Troubleshooting

### Issue: Page not loading (404)

**Solution:** Make sure routes are initialized:

```python
# In your main app file
initialize_llm_routes(app, LLMFacade, auth_routes)
```

### Issue: "Template not found"

**Solution:** Verify template is in correct location:

```bash
ls templates/llm_management.html
```

### Issue: LLM management link not in navbar

**Solution:** Make sure you updated `base.html` with the new version.

### Issue: API endpoints returning 500 errors

**Solution:** Check that:
1. `llm_config.json` exists and is valid JSON
2. LLMFacade is properly imported
3. Check application logs for Python errors

### Issue: "Config manager not initialized"

**Solution:** Create an LLMFacade instance at startup:

```python
# In your app initialization
from llm.llm_facade_enhanced import LLMFacade

# Create one instance to initialize the config manager
_ = LLMFacade()
```

### Issue: Can't enable/disable models

**Solution:** Verify:
1. User has admin role
2. Config file has write permissions
3. Path to config file is correct in `llm_routes.py`

## 🎨 Customization

### Change Navbar Icon

Edit `base_updated.html`, line with LLM Management:

```html
<li><a class="dropdown-item" href="{{ url_for('llm_management') }}">
    <i class="fas fa-microchip"></i> LLM Management  <!-- Change icon -->
</a></li>
```

### Add More Provider Icons

Edit `llm_management.html`, in the provider tabs section:

```html
{% elif provider_name == 'your_provider' %}
    <i class="fas fa-your-icon"></i>
```

### Customize Test Prompt

Edit `llm_routes.py`, in `api_test_llm_model`:

```python
test_prompt = "Your custom test prompt here"
```

### Change Summary Cards

Edit `llm_management.html`, the summary cards section to add/remove metrics.

## 📊 Monitoring

The LLM management page provides visibility into:

1. **Provider Status**
   - Which providers are enabled
   - Number of models per provider
   - Configuration status

2. **Model Usage**
   - Which models are enabled
   - Current default model
   - Model capabilities

3. **Cost Tracking**
   - Cost per million tokens (input/output)
   - Compare costs across models
   - Choose cost-effective options

4. **Health Checks**
   - Test individual models
   - Test all connections at once
   - Verify API connectivity

## 🔐 Security Considerations

1. **Admin-Only Actions**
   - Only admins can modify configuration
   - Regular users can only view and test

2. **API Key Protection**
   - API keys never displayed in UI
   - Keys stored in environment variables
   - Config shows only environment variable names

3. **Audit Trail**
   - Consider logging all configuration changes
   - Track which admin made changes
   - Log all test requests

## 📚 Additional Resources

- **LLM Facade Documentation**: See `README_LLM_FACADE.md`
- **Usage Examples**: See `llm_usage_examples.py`
- **Quick Start**: See `QUICK_START.md`

## 🎓 Next Steps

1. **Integrate with Components**
   - Update planner to show LLM selector
   - Add LLM choice to agent execution
   - Show LLM used in workflow logs

2. **Add Cost Tracking**
   - Track token usage per request
   - Calculate actual costs
   - Show cost analytics

3. **Add History**
   - Log all LLM requests
   - Show recent test results
   - Track configuration changes

4. **Enhance UI**
   - Add charts for cost comparison
   - Show performance metrics
   - Add model recommendations

---

**Need Help?** Check the troubleshooting section or review the source code comments.

**Version**: 1.0.0  
**Created**: October 2025
