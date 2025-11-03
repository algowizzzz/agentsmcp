"""
LangGraph Planner Component
AI-powered workflow planning and task decomposition using LangGraph

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from db.database import get_db
from llm.llm_facade import LLMFacade


class LangGraphPlanner:
    """AI-powered workflow planner using LangGraph"""

    def __init__(self, llm_provider: str = 'mock'):
        self.llm = LLMFacade(provider=llm_provider)
        self.db = get_db()

    def chat(self, user_id: str, message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Chat with the planner"""
        conversation_history = conversation_history or []

        # Build context from conversation history
        context = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in conversation_history[-5:]  # Last 5 messages for context
        ])

        # Create prompt with context
        prompt = f"""You are an AI workflow planner for the Abhikarta system using LangGraph.
Previous conversation:
{context}

Current user message: {message}

Please provide a helpful response. If the user wants to create a workflow plan, 
suggest a step-by-step plan. If they want to execute something, confirm what 
they want to execute."""

        response = self.llm.generate(prompt)

        # Save conversation to database
        conversation_id = self._save_conversation(user_id, message, response)

        return {
            'response': response,
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat()
        }

    def create_plan_from_request(self, user_id: str, user_request: str,
                                 available_tools: List[str],
                                 available_agents: List[str],
                                 session_id: str = None,
                                 options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an executable plan from natural language request"""

        options = options or {}

        # Create prompt for plan generation
        prompt = f"""Create a detailed workflow plan for the following request:
"{user_request}"

Available tools: {', '.join(available_tools)}
Available agents: {', '.join(available_agents)}

Generate a JSON workflow plan with the following structure:
{{
  "dag_id": "generated_plan_<unique_id>",
  "name": "<descriptive name>",
  "description": "<description>",
  "nodes": [
    {{
      "node_id": "<unique_node_id>",
      "node_type": "agent" or "tool",
      "agent_id": "<agent_id>" or "tool_name": "<tool_name>",
      "config": {{"input": {{}}}},
      "dependencies": []
    }}
  ],
  "start_nodes": ["<first_node_id>"]
}}

Provide ONLY the JSON, no other text."""

        # Generate plan using LLM
        llm_response = self.llm.generate(prompt)

        # For mock mode, create a simple plan
        plan_id = f"generated_plan_{uuid.uuid4().hex[:8]}"

        try:
            # Try to parse JSON from LLM response
            plan_data = json.loads(llm_response)
        except:
            # If parsing fails, create a default plan
            plan_data = {
                "dag_id": plan_id,
                "name": f"Plan for: {user_request[:50]}",
                "description": f"Auto-generated plan for: {user_request}",
                "nodes": [
                    {
                        "node_id": "step_1",
                        "node_type": "agent",
                        "agent_id": available_agents[0] if available_agents else "echo_agent",
                        "config": {"input": {"request": user_request}},
                        "dependencies": []
                    },
                    {
                        "node_id": "step_2",
                        "node_type": "agent",
                        "agent_id": available_agents[0] if available_agents else "echo_agent",
                        "config": {"input": {"message": "Processing complete"}},
                        "dependencies": ["step_1"]
                    }
                ],
                "start_nodes": ["step_1"]
            }

        # Save plan to database
        plan_id = plan_data['dag_id']

        # Prepare data for insertion
        plan_record = {
            'plan_id': plan_id,
            'user_id': user_id,
            'request': user_request,
            'plan_json': json.dumps(plan_data),
            'status': 'pending_approval',
            'created_at': datetime.now().isoformat()
        }

        # Add optional fields if columns exist
        try:
            # Check if session_id column exists
            self.db.execute("SELECT session_id FROM plans LIMIT 1")
            plan_record['session_id'] = session_id
        except:
            pass

        try:
            # Check if options_json column exists
            self.db.execute("SELECT options_json FROM plans LIMIT 1")
            plan_record['options_json'] = json.dumps(options) if options else None
        except:
            pass

        self.db.insert('plans', plan_record)

        return {
            'plan_id': plan_id,
            'plan': plan_data,
            'status': 'pending_approval',
            'session_id': session_id,
            'options': options,
            'message': 'Plan created successfully. Please review and approve.'
        }

    def create_autonomous_plan(self, user_id: str, user_request: str,
                              available_tools: List[str] = None,
                              available_agents: List[str] = None,
                              auto_approve: bool = False,
                              session_id: str = None,
                              options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create an autonomous plan that can be executed without explicit approval

        Args:
            user_id: The user creating the plan
            user_request: Natural language description of the task
            available_tools: List of available tool names
            available_agents: List of available agent IDs
            auto_approve: Whether to automatically approve the plan
            session_id: Optional session ID for tracking
            options: Optional dictionary of additional options/configuration

        Returns:
            Dict containing plan_id, plan data, and status
        """
        available_tools = available_tools or []
        available_agents = available_agents or []
        options = options or {}

        # Create prompt for autonomous plan generation
        prompt = f"""Create an autonomous workflow plan for the following request:
"{user_request}"

Available tools: {', '.join(available_tools) if available_tools else 'None'}
Available agents: {', '.join(available_agents) if available_agents else 'None'}

This plan should be safe to execute autonomously. Generate a JSON workflow plan with:
{{
  "dag_id": "auto_plan_<unique_id>",
  "name": "<descriptive name>",
  "description": "<description>",
  "autonomous": true,
  "nodes": [
    {{
      "node_id": "<unique_node_id>",
      "node_type": "agent" or "tool",
      "agent_id": "<agent_id>" or "tool_name": "<tool_name>",
      "config": {{"input": {{}}}},
      "dependencies": []
    }}
  ],
  "start_nodes": ["<first_node_id>"]
}}

Provide ONLY the JSON, no other text."""

        # Generate plan using LLM
        llm_response = self.llm.generate(prompt)

        plan_id = f"auto_plan_{uuid.uuid4().hex[:8]}"

        try:
            # Try to parse JSON from LLM response
            plan_data = json.loads(llm_response)
            plan_data['autonomous'] = True
        except:
            # If parsing fails, create a default autonomous plan
            plan_data = {
                "dag_id": plan_id,
                "name": f"Autonomous Plan: {user_request[:50]}",
                "description": f"Auto-generated autonomous plan for: {user_request}",
                "autonomous": True,
                "nodes": [
                    {
                        "node_id": "auto_step_1",
                        "node_type": "agent",
                        "agent_id": available_agents[0] if available_agents else "echo_agent",
                        "config": {"input": {"request": user_request}},
                        "dependencies": []
                    }
                ],
                "start_nodes": ["auto_step_1"]
            }

        # Save plan to database
        plan_id = plan_data['dag_id']
        status = 'approved' if auto_approve else 'pending_approval'

        # Prepare data for insertion
        plan_record = {
            'plan_id': plan_id,
            'user_id': user_id,
            'request': user_request,
            'plan_json': json.dumps(plan_data),
            'status': status,
            'created_at': datetime.now().isoformat(),
            'approved_at': datetime.now().isoformat() if auto_approve else None
        }

        # Add optional fields if columns exist
        try:
            # Check if session_id column exists
            self.db.execute("SELECT session_id FROM plans LIMIT 1")
            plan_record['session_id'] = session_id
        except:
            pass

        try:
            # Check if options_json column exists
            self.db.execute("SELECT options_json FROM plans LIMIT 1")
            plan_record['options_json'] = json.dumps(options) if options else None
        except:
            pass

        try:
            # Check if autonomous column exists
            self.db.execute("SELECT autonomous FROM plans LIMIT 1")
            plan_record['autonomous'] = True
        except:
            pass

        self.db.insert('plans', plan_record)

        return {
            'plan_id': plan_id,
            'plan': plan_data,
            'status': status,
            'autonomous': True,
            'session_id': session_id,
            'options': options,
            'message': f'Autonomous plan created successfully. Status: {status}'
        }

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a plan by ID"""
        plan = self.db.fetchone(
            "SELECT * FROM plans WHERE plan_id = ?",
            (plan_id,)
        )

        if plan:
            plan_data = json.loads(plan['plan_json'])
            options = json.loads(plan['options_json']) if plan.get('options_json') else {}
            return {
                'plan_id': plan['plan_id'],
                'user_id': plan['user_id'],
                'session_id': plan.get('session_id'),
                'user_request': plan['request'],  # Changed from 'request' to 'user_request'
                'plan': plan_data,
                'options': options,
                'status': plan['status'],
                'autonomous': plan.get('autonomous', False),
                'created_at': plan['created_at']
            }

        return None

    def approve_plan(self, plan_id: str) -> bool:
        """Approve a plan for execution"""
        self.db.update(
            'plans',
            {'status': 'approved', 'approved_at': datetime.now().isoformat()},
            'plan_id = ?',
            (plan_id,)
        )
        return True

    def reject_plan(self, plan_id: str, reason: str = '') -> bool:
        """Reject a plan"""
        self.db.update(
            'plans',
            {'status': 'rejected', 'rejected_at': datetime.now().isoformat(), 'rejection_reason': reason},
            'plan_id = ?',
            (plan_id,)
        )
        return True

    def get_user_plans(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all plans for a user

        Args:
            user_id: The user ID to fetch plans for
            limit: Optional limit on number of plans to return

        Returns:
            List of plan dictionaries
        """
        if limit:
            plans = self.db.fetchall(
                "SELECT * FROM plans WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
        else:
            plans = self.db.fetchall(
                "SELECT * FROM plans WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )

        # Parse JSON data for each plan
        result = []
        for plan in plans:
            try:
                plan_dict = dict(plan)
                plan_dict['plan'] = json.loads(plan_dict['plan_json'])
                plan_dict['options'] = json.loads(plan_dict['options_json']) if plan_dict.get('options_json') else {}
                result.append(plan_dict)
            except:
                result.append(dict(plan))

        return result

    def get_autonomous_plans(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get autonomous plans for a user

        Args:
            user_id: The user ID
            status: Optional filter by status (e.g., 'approved', 'pending_approval', 'rejected')

        Returns:
            List of autonomous plan dictionaries
        """
        if status:
            plans = self.db.fetchall(
                "SELECT * FROM plans WHERE user_id = ? AND autonomous = 1 AND status = ? ORDER BY created_at DESC",
                (user_id, status)
            )
        else:
            plans = self.db.fetchall(
                "SELECT * FROM plans WHERE user_id = ? AND autonomous = 1 ORDER BY created_at DESC",
                (user_id,)
            )

        # Parse JSON data for each plan
        result = []
        for plan in plans:
            try:
                plan_dict = dict(plan)
                plan_dict['plan'] = json.loads(plan_dict['plan_json'])
                plan_dict['options'] = json.loads(plan_dict['options_json']) if plan_dict.get('options_json') else {}
                result.append(plan_dict)
            except:
                result.append(dict(plan))

        return result

    def get_plans_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all plans for a specific session

        Args:
            session_id: The session ID

        Returns:
            List of plan dictionaries for the session
        """
        plans = self.db.fetchall(
            "SELECT * FROM plans WHERE session_id = ? ORDER BY created_at DESC",
            (session_id,)
        )

        # Parse JSON data for each plan
        result = []
        for plan in plans:
            try:
                plan_dict = dict(plan)
                plan_dict['plan'] = json.loads(plan_dict['plan_json'])
                plan_dict['options'] = json.loads(plan_dict['options_json']) if plan_dict.get('options_json') else {}
                result.append(plan_dict)
            except:
                result.append(dict(plan))

        return result

    def _save_conversation(self, user_id: str, message: str, response: str) -> str:
        """Save conversation to database"""
        conversation_id = str(uuid.uuid4())

        self.db.insert('planner_conversations', {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'message': message,
            'response': response,
            'created_at': datetime.now().isoformat()
        })

        return conversation_id

    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        conversations = self.db.fetchall(
            "SELECT * FROM planner_conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        return conversations


# Initialize plans table
def initialize_planner_tables():
    """Initialize database tables for LangGraph planner"""
    db = get_db()

    # Plans table
    db.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            plan_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_id TEXT,
            request TEXT,
            plan_json TEXT,
            options_json TEXT,
            status TEXT DEFAULT 'pending_approval',
            autonomous INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            approved_at TEXT,
            rejected_at TEXT,
            rejection_reason TEXT
        )
    """)

    # Add missing columns if they don't exist (for existing tables)
    try:
        db.execute("ALTER TABLE plans ADD COLUMN session_id TEXT")
    except:
        pass  # Column already exists

    try:
        db.execute("ALTER TABLE plans ADD COLUMN options_json TEXT")
    except:
        pass  # Column already exists

    try:
        db.execute("ALTER TABLE plans ADD COLUMN autonomous INTEGER DEFAULT 0")
    except:
        pass  # Column already exists

    # Planner conversations table
    db.execute("""
        CREATE TABLE IF NOT EXISTS planner_conversations (
            conversation_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            message TEXT,
            response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)