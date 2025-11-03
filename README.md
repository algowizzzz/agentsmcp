# Abhikarta - Multi-Agent Orchestration System

© 2025-2030 Ashutosh Sinha  
ajsinha@gmail.com  
https://www.github.com/ajsinha/abhikarta

## Overview

Abhikarta is a sophisticated multi-agent orchestration and workflow management framework designed to coordinate multiple specialized AI agents for complex task execution. The system provides a comprehensive platform for planning, executing, monitoring, and managing AI-driven workflows with human oversight capabilities.

## Features

- **AI Planner with Chat Interface**: Chat with AI to create workflow plans from natural language
- **Plan Review & Approval**: Review AI-generated plans before execution
- **Multi-Agent Orchestration**: Coordinate multiple AI agents working collaboratively
- **DAG-Based Workflows**: Define workflows as Directed Acyclic Graphs
- **Execute Tools Individually**: Test and execute tools from the UI
- **Execute Agents Individually**: Test and execute agents from the UI
- **Execute DAGs**: Run pre-defined or AI-generated workflows
- **Human-in-the-Loop (HITL)**: UI-driven human intervention and approval workflows
- **Real-time Monitoring**: Track agent execution and workflow progress
- **User Management**: Full CRUD operations with role-based access control
- **MCP Integration**: Integration with Model Context Protocol tools
- **Professional UI**: Bootstrap-based web interface with jQuery
- **Scalable Architecture**: Multi-threaded, multi-user system design

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, jQuery 3
- **Database**: SQLite (configurable to PostgreSQL)
- **Orchestration**: LangChain, LangGraph
- **Graph Engine**: Custom implementation (no NetworkX)

## Directory Structure

```
abhikarta/
├── core/                    # Core modules
│   ├── properties_configurator.py
│   ├── graph.py            # Custom Graph implementation
│   ├── database.py         # Database abstraction
│   └── user_registry.py    # User management
├── agents/                 # Agent implementations
│   ├── agent_registry.py   # Agent registry
│   └── echo_agent.py       # Sample echo agent
├── tools/                  # Tool implementations
│   └── tool_registry.py    # Tool registry
├── workflows/             # Workflow management
│   ├── dag_registry.py    # DAG registry
│   └── orchestrator.py    # Workflow orchestrator
├── web/                   # Flask web application
│   ├── app.py            # Main Flask app
│   ├── templates/        # HTML templates
│   └── static/           # CSS, JS, images
├── config/               # Configuration files
│   ├── users/           # User configurations
│   ├── agents/          # Agent configurations
│   ├── tools/           # Tool configurations
│   ├── dags/            # DAG definitions
│   └── mcp/             # MCP tool configurations
├── mcp_server/          # Mock MCP server for testing
│   └── mock_mcp_server.py
├── data/                # Database and runtime data
├── logs/                # Application logs
├── application.properties
├── run_server.py        # Main entry point
└── README.md

```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Extract the archive:
```bash
tar -xzf abhikarta.tar.gz
cd abhikarta
```

2. Install dependencies:
```bash
pip install flask requests langchain langgraph
```

Optional for PostgreSQL support:
```bash
pip install psycopg2-binary
```

3. Make the server script executable:
```bash
chmod +x run_server.py
```

## Running the Application

### Start the Mock MCP Server (Terminal 1)

```bash
python3 mcp_server/mock_mcp_server.py
```

The MCP server will start on `http://localhost:8000`

### Start the Main Application (Terminal 2)

```bash
python3 run_server.py
```

The main application will start on `http://localhost:5001`

### Access the Application

Open your browser and navigate to: `http://localhost:5001`

Default credentials:
- Username: `admin`
- Password: `admin`

## User Management

Users are managed through `config/users/users.json`. The file contains:

- `user_id`: Unique user identifier
- `username`: Login username
- `password`: Password (cleartext)
- `full_name`: User's full name
- `email`: User's email
- `role`: User role (`admin` or `user`)
- `approved_tools`: List of tools the user can access
- `approved_agents`: List of agents the user can access
- `approved_dags`: List of DAGs the user can execute

**Note**: The `admin` user cannot be edited or deleted.

### Sample Users

1. **Admin User**
   - Username: `admin`
   - Password: `admin`
   - Access: Full access to all tools, agents, and DAGs

2. **User1**
   - Username: `user1`
   - Password: `user1`
   - Access: Limited tools and DAGs

3. **User2**
   - Username: `user2`
   - Password: `user2`
   - Access: All tools, limited agents and DAGs

## Configuration

### Application Properties

Edit `application.properties` to configure:

```properties
# Server Configuration
server.host=0.0.0.0
server.port=5001
server.debug=true

# LLM Configuration
llm.default.provider=mock
llm.openai.api_key=
llm.claude.api_key=

# MCP Configuration
mcp.config.dir=config/mcp
mcp.auto.load=true

# Session Configuration
session.timeout=3600

# Logging
logging.level=INFO
logging.file=logs/abhikarta.log
```

### Database Configuration

By default, the system uses SQLite. To use PostgreSQL, modify the database initialization in `web/app.py`:

```python
initialize_db(
    db_type='postgresql',
    host='localhost',
    port=5432,
    database='abhikarta',
    user='postgres',
    password='your_password'
)
```

## Creating Custom Agents

1. Create a new Python file in the `agents/` directory
2. Extend the `BaseAgent` class
3. Implement the `execute()` method
4. Create a configuration file in `config/agents/`

Example agent configuration (`config/agents/my_agent.json`):

```json
{
  "agent_id": "my_agent",
  "name": "My Custom Agent",
  "description": "Description of the agent",
  "module": "agents.my_agent.MyAgent",
  "config": {}
}
```

## Creating Custom Tools

1. Create a new Python file in the `tools/` directory
2. Extend the `BaseTool` class
3. Implement the `execute()` method
4. Create a configuration file in `config/tools/`

## Creating DAGs

DAG definitions are JSON files in `config/dags/`. Each DAG specifies:

- `dag_id`: Unique DAG identifier
- `name`: Human-readable name
- `description`: DAG description
- `nodes`: Array of node definitions
- `start_nodes`: Array of starting node IDs

Example node:

```json
{
  "node_id": "task1",
  "node_type": "agent",
  "agent_id": "echo_agent",
  "config": {
    "input": {
      "message": "Hello World"
    }
  },
  "dependencies": []
}
```

### Node Types

- `agent`: Execute an agent
- `tool`: Execute a tool
- `human_in_loop`: Wait for human approval

## MCP Tools

MCP (Model Context Protocol) tools are configured in `config/mcp/`. These tools communicate with MCP servers via REST.

Example configuration:

```json
{
  "mcp_url": "http://localhost:8000",
  "name": "echo_mcp_tool",
  "tool_description": {
    "tools": [
      {
        "name": "echo",
        "description": "Echo back the input",
        "input_schema": {
          "type": "object",
          "properties": {
            "input": {
              "type": "string",
              "description": "User input"
            }
          },
          "required": ["input"]
        }
      }
    ]
  }
}
```

## Workflow Execution

1. Navigate to the **DAGs** page
2. Select a DAG to execute
3. Click **Execute**
4. Monitor progress on the **Workflow Detail** page
5. Approve HITL requests when they appear

## AI Planner

The AI Planner allows you to create workflows through natural language conversation.

### Using the Planner

1. Navigate to the **Planner** page
2. Chat with the AI to describe your task
3. Click **Create Plan from Request** to generate a workflow
4. Review the generated plan
5. Approve or reject the plan
6. Execute approved plans

### Plan Review and Approval

1. Navigate to **Planner** page to see pending plans
2. Click on a plan to review details
3. Review the proposed workflow steps
4. Click **Approve** to allow execution
5. Click **Reject** to deny execution
6. Execute approved plans directly from the plan detail page

### Example Planner Interactions

**Create a simple workflow:**
```
User: Create a plan to fetch stock data for AAPL and send a report
Planner: [Generates a workflow with nodes for fetching data, processing, and reporting]
```

**Ask about capabilities:**
```
User: What tools are available?
Planner: [Lists available tools based on your permissions]
```

## Execute Tools and Agents

### Execute Individual Tools

1. Navigate to **Execute > Execute Tool**
2. Select a tool from the list
3. Fill in required parameters
4. Click **Execute Tool**
5. View the execution result

### Execute Individual Agents

1. Navigate to **Execute > Execute Agent**
2. Select an agent from the list
3. Provide input data in JSON format
4. Click **Execute Agent**
5. View the execution result

These features are useful for:
- Testing tools and agents
- Quick one-off executions
- Debugging and development
- Learning how tools and agents work

## User Management

### Adding Users (Admin Only)

1. Navigate to **Users** page
2. Click **Add User**
3. Fill in user details:
   - User ID and Username
   - Password
   - Full name and email
   - Role (User or Admin)
4. Select permissions:
   - Approved tools
   - Approved agents
   - Approved DAGs
5. Click **Add User**

### Editing Users (Admin Only)

1. Navigate to **Users** page
2. Click **Edit** on the user to modify
3. Update user details and permissions
4. Click **Save Changes**

**Note**: The admin user cannot be edited or deleted.

### Deleting Users (Admin Only)

1. Navigate to **Users** page
2. Click **Edit** on the user
3. Click **Delete User** button
4. Confirm deletion

## Workflow Execution

1. Navigate to the **DAGs** page
2. Select a DAG to execute
3. Click **Execute**
4. Monitor progress on the **Workflow Detail** page
5. Approve HITL requests when they appear

## Human-in-the-Loop (HITL)

HITL nodes pause workflow execution and wait for human approval:

1. Navigate to **HITL Requests** page
2. Review pending requests
3. Click **Approve** or **Reject**
4. Workflow continues or halts based on the decision

## API Endpoints

### Workflow Management

- `POST /api/execute_dag` - Execute a DAG
- `GET /api/workflow_status/<workflow_id>` - Get workflow status

### HITL Management

- `POST /api/hitl_approve` - Approve HITL request
- `POST /api/hitl_reject` - Reject HITL request

### Configuration

- `POST /api/reload_config` - Reload all configurations (admin only)

## Database Schema

The system uses the following main tables:

- `users` - User information
- `sessions` - Session tracking
- `workflows` - Workflow executions
- `workflow_nodes` - Workflow node states
- `workflow_events` - Workflow event log
- `agent_executions` - Agent execution history
- `hitl_requests` - HITL request tracking

## Reloading Configuration

As an admin, you can reload all configurations without restarting:

1. Click on your username in the navigation
2. Select **Reload Config**
3. Confirm the action

This reloads:
- Users
- Agents
- Tools
- DAGs

## Troubleshooting

### Port Already in Use

If port 5001 or 8000 is already in use, edit `application.properties` to change the port.

### Database Locked

If you encounter database locked errors, ensure only one instance of the server is running.

### MCP Tools Not Working

1. Verify the Mock MCP Server is running on port 8000
2. Check the `mcp_url` in MCP tool configurations
3. Check MCP server logs for errors

## Development

### Adding New Features

1. Create new modules in appropriate directories
2. Update registries to load new components
3. Add corresponding HTML pages in `web/templates/`
4. Update navigation in `base.html`

### Testing

Test individual components:

```python
# Test agent
from agents.agent_registry import AgentRegistry
registry = AgentRegistry()
result = registry.execute_agent('echo_agent', {'input': 'test'})
print(result)
```

## Production Deployment

For production deployment:

1. Change `server.debug=false` in `application.properties`
2. Use a production WSGI server (gunicorn, uWSGI)
3. Configure PostgreSQL instead of SQLite
4. Set up proper logging
5. Use environment variables for secrets
6. Enable SSL/TLS
7. Set up proper authentication (not cleartext passwords)

Example with Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5001 web.app:app
```

## Security Notes

**IMPORTANT**: This system uses cleartext password comparison for demonstration purposes. For production use:

1. Implement proper password hashing (bcrypt, argon2)
2. Use secure session management
3. Implement rate limiting
4. Use HTTPS
5. Implement proper input validation
6. Set up audit logging
7. Use environment variables for sensitive configuration

## License

© 2025-2030 Ashutosh Sinha  
ajsinha@gmail.com  
https://www.github.com/ajsinha/abhikarta

## Support

For issues, questions, or contributions, please contact:
- Email: ajsinha@gmail.com
- GitHub: https://www.github.com/ajsinha/abhikarta

## Acknowledgments

Built with:
- Flask
- Bootstrap
- jQuery
- LangChain
- LangGraph

[REDACTED_TOKEN]