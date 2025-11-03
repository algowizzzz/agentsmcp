# Abhikarta - Refactored Application Structure

## Overview

The Flask application has been refactored from a single 1294-line `app.py` file into a modular, maintainable structure with separate route files organized by functionality.

## New Directory Structure

```
.
├── app.py                              # Main application entry point
└── routes/                             # Route modules directory
    ├── auth_routes.py                  # Authentication (login, logout)
    ├── dashboard_routes.py             # Dashboard and overview
    ├── agent_routes.py                 # Agent management & execution
    ├── tool_routes.py                  # Tool management & execution
    ├── dag_routes.py                   # DAG management
    ├── workflow_routes.py              # Workflow monitoring
    ├── hitl_routes.py                  # Human-In-The-Loop requests
    ├── planner_routes.py               # DAG-based planner
    ├── lgraph_planner_routes.py        # LangGraph autonomous planner
    ├── user_routes.py                  # User management (admin)
    ├── monitoring_routes.py            # Monitoring & statistics
    └── config_routes.py                # Configuration management
```

## Route Classes

Each route file contains a class that encapsulates related routes:

### 1. **AuthRoutes** (`auth_routes.py`)
- Home page (`/`)
- Login page (`/login`)
- Logout (`/logout`)
- Provides `login_required` decorator for other routes

### 2. **DashboardRoutes** (`dashboard_routes.py`)
- Main dashboard (`/dashboard`)
- Shows workflow statistics, HITL requests, and MCP server status

### 3. **AgentRoutes** (`agent_routes.py`)
- List agents (`/agents`)
- Execute agent pages (`/execute_agent`, `/execute_agent/<agent_id>`)
- Create agent (admin) (`/create_agent`)
- API endpoints for agent execution and management
- Enable/disable agents

### 4. **ToolRoutes** (`tool_routes.py`)
- List tools (`/tools`)
- Execute tool pages (`/execute_tool`, `/execute_tool/<tool_name>`)
- Create tool (admin) (`/create_tool`)
- API endpoints for tool execution and management
- Enable/disable tools

### 5. **DAGRoutes** (`dag_routes.py`)
- List DAGs (`/dags`)
- Execute DAG page (`/execute_dag/<dag_id>`)
- API endpoint to start DAG execution

### 6. **WorkflowRoutes** (`workflow_routes.py`)
- List workflows (`/workflows`)
- Workflow detail page (`/workflow/<workflow_id>`)
- API endpoint for workflow status

### 7. **HITLRoutes** (`hitl_routes.py`)
- HITL requests page (`/hitl_requests`)
- API endpoints to approve/reject HITL requests

### 8. **PlannerRoutes** (`planner_routes.py`)
- Planner chat interface (`/planner`)
- Create plan page (`/create_plan`)
- Plan detail page (`/plan/<plan_id>`)
- API endpoints for chat, plan creation, approval, rejection, and execution

### 9. **LGraphPlannerRoutes** (`lgraph_planner_routes.py`)
- LangGraph planner interface (`/lgraph/planner`)
- Create autonomous plan page (`/lgraph/create-plan`)
- Plan detail page (`/lgraph/plan/<plan_id>`)
- API endpoints for chat, plan creation, approval, rejection, and execution

### 10. **UserRoutes** (`user_routes.py`)
- List users (admin) (`/users`)
- Add user page (admin) (`/add_user`)
- Edit user page (admin) (`/edit_user/<user_id>`)
- API endpoints for user CRUD operations

### 11. **MonitoringRoutes** (`monitoring_routes.py`)
- Monitoring dashboard (`/monitoring`)
- Monitoring pages for users, tools, agents, DAGs, planner
- API endpoints for monitoring statistics

### 12. **ConfigRoutes** (`config_routes.py`)
- API endpoint to reload configuration (admin)

## How It Works

### Main Application (`app.py`)

The `app.py` file now:

1. **Initializes the Flask app** and configuration
2. **Sets up databases and registries** (users, agents, tools, DAGs)
3. **Creates route class instances** by passing them:
   - The Flask app instance
   - Required registries and services
   - The `login_required` decorator from `AuthRoutes`
4. **Route classes automatically register** their routes during initialization

### Route Class Pattern

Each route class follows this pattern:

```python
class ExampleRoutes:
    def __init__(self, app, dependencies...):
        self.app = app
        # Store dependencies
        self.register_routes()
    
    def register_routes(self):
        # Define all routes as nested functions
        @self.app.route('/example')
        def example_route():
            # Route logic using self.dependencies
            pass
```

## Benefits of This Structure

1. **Modularity**: Each route file focuses on a specific domain
2. **Maintainability**: Easier to find and modify specific functionality
3. **Scalability**: New features can be added as new route classes
4. **Testability**: Each route class can be tested independently
5. **Clarity**: Clear separation of concerns
6. **Collaboration**: Multiple developers can work on different route files

## Migration from Old Code

The refactoring maintains 100% compatibility with the original code:
- All route paths remain the same
- All functionality is preserved
- No changes to templates or API contracts
- The only difference is internal organization

## Usage

Simply replace your old `app.py` with the new one and add the `routes/` directory:

```bash
# Run the application
python app.py
```

The application will work exactly as before, but with a much cleaner codebase!

## Adding New Routes

To add a new feature:

1. Create a new route file in `routes/` directory
2. Define a route class with `__init__` and `register_routes` methods
3. Import and instantiate the class in `app.py`

Example:

```python
# routes/new_feature_routes.py
class NewFeatureRoutes:
    def __init__(self, app, login_required):
        self.app = app
        self.login_required = login_required
        self.register_routes()
    
    def register_routes(self):
        @self.app.route('/new-feature')
        @self.login_required
        def new_feature():
            return "New Feature!"
```

```python
# In app.py
from routes import NewFeatureRoutes

# ...
new_feature_routes = NewFeatureRoutes(app, login_required)
```

---

© 2025-2030 Ashutosh Sinha
