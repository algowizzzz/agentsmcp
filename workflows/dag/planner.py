"""
Planner Component
AI-powered workflow planning and task decomposition

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from db.database import get_db
from llm.llm_facade import LLMFacade


class Planner:
    """AI-powered workflow planner"""
    
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
        prompt = f"""You are an AI workflow planner for the Abhikarta system.
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
    
    def create_plan_from_request(self, user_id: str, request: str, 
                                 available_tools: List[str], 
                                 available_agents: List[str]) -> Dict[str, Any]:
        """Create an executable plan from natural language request"""
        
        # Create prompt for plan generation
        prompt = f"""Create a detailed workflow plan for the following request:
"{request}"

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
                "name": f"Plan for: {request[:50]}",
                "description": f"Auto-generated plan for: {request}",
                "nodes": [
                    {
                        "node_id": "step_1",
                        "node_type": "agent",
                        "agent_id": available_agents[0] if available_agents else "echo_agent",
                        "config": {"input": {"request": request}},
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
        self.db.insert('plans', {
            'plan_id': plan_id,
            'user_id': user_id,
            'request': request,
            'plan_json': json.dumps(plan_data),
            'status': 'pending_approval',
            'created_at': datetime.now().isoformat()
        })
        
        return {
            'plan_id': plan_id,
            'plan': plan_data,
            'status': 'pending_approval',
            'message': 'Plan created successfully. Please review and approve.'
        }
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a plan by ID"""
        plan = self.db.fetchone(
            "SELECT * FROM plans WHERE plan_id = ?",
            (plan_id,)
        )
        
        if plan:
            plan_data = json.loads(plan['plan_json'])
            return {
                'plan_id': plan['plan_id'],
                'user_id': plan['user_id'],
                'request': plan['request'],
                'plan': plan_data,
                'status': plan['status'],
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
    
    def get_user_plans(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all plans for a user"""
        plans = self.db.fetchall(
            "SELECT * FROM plans WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return plans
    
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
    """Initialize database tables for planner"""
    db = get_db()
    
    # Plans table
    db.execute("""
        CREATE TABLE IF NOT EXISTS plans (
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
    """)
    
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
