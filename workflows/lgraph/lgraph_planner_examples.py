"""
LangGraph Planner - Usage Examples and Documentation

This file demonstrates how to use the autonomous LangGraph-based planner
in the Abhikarta system.

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from lgraph_planner import LangGraphPlanner, initialize_lgraph_tables


# ============================================================================
# SETUP
# ============================================================================

def setup_planner():
    """Initialize the LangGraph planner"""
    
    # Initialize database tables
    initialize_lgraph_tables()
    
    # Create planner instance (use 'anthropic' for Claude, 'mock' for testing)
    planner = LangGraphPlanner(llm_provider='anthropic')
    
    return planner


# ============================================================================
# EXAMPLE 1: Simple Sequential Task
# ============================================================================

def example_simple_request():
    """Example: Simple request that creates a sequential plan"""
    
    planner = setup_planner()
    
    # User makes a request
    user_request = "Fetch the latest stock price for AAPL and analyze the trend"
    user_id = "user_123"
    session_id = "session_456"
    
    # Create plan
    result = planner.create_plan(
        user_id=user_id,
        session_id=session_id,
        user_request=user_request
    )
    
    print("=== Plan Created ===")
    print(f"Plan ID: {result['plan_id']}")
    print(f"Plan Type: {result['plan_type']}")
    print(f"Status: {result['status']}")
    print(f"\nExecution Plan:")
    print(result['execution_plan'])
    print(f"\nTask Breakdown:")
    for task in result['task_breakdown']:
        print(f"  - {task['step_id']}: {task.get('name', 'N/A')}")
    
    # User reviews and approves
    if result['pending_approval']:
        print("\n=== Approving Plan ===")
        approval_result = planner.approve_plan(
            plan_id=result['plan_id'],
            user_id=user_id
        )
        
        print(f"Approval Status: {approval_result['success']}")
        print(f"Workflow ID: {approval_result.get('workflow_id')}")
        
        # Check workflow status
        if approval_result.get('workflow_id'):
            status = planner.get_workflow_status(approval_result['workflow_id'])
            print(f"\nWorkflow Status: {status['status']}")


# ============================================================================
# EXAMPLE 2: Using Existing DAG
# ============================================================================

def example_use_existing_dag():
    """Example: Request that matches existing DAG"""
    
    planner = setup_planner()
    
    # User request that matches an existing DAG
    user_request = "Run a simple sequential data processing workflow"
    user_id = "user_123"
    session_id = "session_789"
    
    # The planner will detect that 'simple_sequential' DAG exists
    # and decide to use it instead of creating a new plan
    result = planner.create_plan(
        user_id=user_id,
        session_id=session_id,
        user_request=user_request
    )
    
    print("=== Plan Created (Using Existing DAG) ===")
    print(f"Plan ID: {result['plan_id']}")
    print(f"Plan Type: {result['plan_type']}")  # Should be 'use_existing_dag'
    print(f"Selected DAG: {result['execution_plan'].get('details', {}).get('dag_id')}")


# ============================================================================
# EXAMPLE 3: Parallel Processing
# ============================================================================

def example_parallel_processing():
    """Example: Request requiring parallel execution"""
    
    planner = setup_planner()
    
    user_request = """
    Process three different data sources simultaneously:
    1. Fetch weather data
    2. Fetch stock market data
    3. Fetch news articles
    Then combine all results and generate a report
    """
    
    user_id = "user_123"
    session_id = "session_abc"
    
    result = planner.create_plan(
        user_id=user_id,
        session_id=session_id,
        user_request=user_request
    )
    
    print("=== Parallel Processing Plan ===")
    print(f"Plan ID: {result['plan_id']}")
    print(f"Execution Mode: {result['execution_plan'].get('details', {}).get('execution_mode')}")
    
    # The planner should identify parallel execution opportunities
    parallel_groups = result['execution_plan'].get('details', {}).get('parallel_groups', {})
    if parallel_groups:
        print(f"\nParallel Groups:")
        for group_name, steps in parallel_groups.items():
            print(f"  {group_name}: {len(steps)} steps")


# ============================================================================
# EXAMPLE 4: Human-in-the-Loop
# ============================================================================

def example_with_hitl():
    """Example: Request with human review checkpoint"""
    
    planner = setup_planner()
    
    user_request = """
    Analyze customer feedback data and prepare a response strategy.
    I want to review the analysis before we proceed with sending responses.
    """
    
    user_id = "user_123"
    session_id = "session_def"
    
    result = planner.create_plan(
        user_id=user_id,
        session_id=session_id,
        user_request=user_request
    )
    
    print("=== Plan with HITL ===")
    print(f"Plan ID: {result['plan_id']}")
    print(f"Requires HITL: {result['requires_hitl']}")
    
    # Approve plan
    approval = planner.approve_plan(result['plan_id'], user_id)
    workflow_id = approval.get('workflow_id')
    
    # During execution, when HITL checkpoint is reached
    # The system will pause and create a HITL request
    # User can then approve or reject
    
    # Example HITL approval (in practice, hitl_id comes from workflow status)
    # hitl_id = "hitl_xyz"
    # planner.approve_hitl(hitl_id, user_id, "Analysis looks good, proceed")


# ============================================================================
# EXAMPLE 5: Complex Multi-Step with Conditionals
# ============================================================================

def example_complex_conditional():
    """Example: Complex request with conditional logic"""
    
    planner = setup_planner()
    
    user_request = """
    Check if there are any critical alerts in the system.
    If there are critical alerts:
      - Notify the on-call team
      - Create incident tickets
      - Start diagnostics
    If there are no critical alerts:
      - Run routine health checks
      - Generate standard report
    """
    
    user_id = "user_123"
    session_id = "session_ghi"
    
    result = planner.create_plan(
        user_id=user_id,
        session_id=session_id,
        user_request=user_request
    )
    
    print("=== Conditional Execution Plan ===")
    print(f"Plan ID: {result['plan_id']}")
    
    details = result['execution_plan'].get('details', {})
    print(f"Execution Mode: {details.get('execution_mode')}")
    
    # Show conditional branches
    for step in details.get('steps', []):
        if step.get('conditional'):
            print(f"\nConditional Step: {step['step_id']}")
            print(f"  Condition: {step['conditional'].get('condition')}")
            print(f"  Branches: {len(step['conditional'].get('branches', []))}")


# ============================================================================
# EXAMPLE 6: Looping Workflow
# ============================================================================

def example_with_loops():
    """Example: Request requiring iterative processing"""
    
    planner = setup_planner()
    
    user_request = """
    Monitor the API endpoint every 5 minutes for the next hour.
    If the response time exceeds 2 seconds, send an alert.
    Continue monitoring until either:
    - Response time is consistently under 2 seconds for 15 minutes
    - Or the hour is up
    """
    
    user_id = "user_123"
    session_id = "session_jkl"
    
    result = planner.create_plan(
        user_id=user_id,
        session_id=session_id,
        user_request=user_request
    )
    
    print("=== Loop-Based Execution Plan ===")
    print(f"Plan ID: {result['plan_id']}")
    
    details = result['execution_plan'].get('details', {})
    loop_config = details.get('loop_config')
    
    if loop_config:
        print(f"\nLoop Configuration:")
        print(f"  Max Iterations: {loop_config.get('max_iterations')}")
        print(f"  Condition: {loop_config.get('condition')}")


# ============================================================================
# EXAMPLE 7: Autonomous Decision Making
# ============================================================================

def example_autonomous_planning():
    """Example: Let planner autonomously decide best approach"""
    
    planner = setup_planner()
    
    # Vague request - planner decides the best approach
    user_request = "Help me understand our quarterly performance"
    
    user_id = "user_123"
    session_id = "session_mno"
    
    result = planner.create_plan(
        user_id=user_id,
        session_id=session_id,
        user_request=user_request
    )
    
    print("=== Autonomous Planning ===")
    print(f"Plan ID: {result['plan_id']}")
    print(f"Plan Type: {result['plan_type']}")
    
    # Show planner's reasoning
    strategy = result['execution_plan'].get('strategy', {})
    print(f"\nPlanner's Strategy:")
    print(f"  Chosen Approach: {strategy.get('strategy')}")
    print(f"  Reasoning: {strategy.get('reasoning')}")
    print(f"  Execution Mode: {strategy.get('execution_mode')}")
    print(f"  Estimated Steps: {strategy.get('estimated_steps')}")


# ============================================================================
# EXAMPLE 8: Monitoring and Management
# ============================================================================

def example_monitoring():
    """Example: Monitor workflow execution"""
    
    planner = setup_planner()
    
    # Assume we have a running workflow
    workflow_id = "some_workflow_id"
    
    # Get current status
    status = planner.get_workflow_status(workflow_id)
    
    if status:
        print("=== Workflow Status ===")
        print(f"Workflow ID: {status['workflow_id']}")
        print(f"Status: {status['status']}")
        print(f"Started: {status['started_at']}")
        print(f"Completed: {status.get('completed_at', 'Still running')}")
        
        print(f"\nCompleted Steps: {len(status['steps'])}")
        for step in status['steps']:
            print(f"  - {step['step_id']}: {'✓' if step['success'] else '✗'}")
        
        if status.get('results'):
            print(f"\nResults:")
            for step_id, result in status['results'].items():
                print(f"  {step_id}: {result}")


# ============================================================================
# EXAMPLE 9: Error Handling and Recovery
# ============================================================================

def example_error_handling():
    """Example: Handle errors and rejections"""
    
    planner = setup_planner()
    
    user_request = "Do something risky"
    user_id = "user_123"
    session_id = "session_pqr"
    
    # Create plan
    result = planner.create_plan(
        user_id=user_id,
        session_id=session_id,
        user_request=user_request
    )
    
    # User reviews and rejects
    if result['pending_approval']:
        print("=== Rejecting Plan ===")
        rejection = planner.reject_plan(
            plan_id=result['plan_id'],
            user_id=user_id,
            reason="This approach seems risky, let's reconsider"
        )
        
        print(f"Plan rejected: {rejection}")
        
        # User can now submit a modified request
        modified_request = "Do something safer with proper safeguards"
        new_result = planner.create_plan(
            user_id=user_id,
            session_id=session_id,
            user_request=modified_request
        )
        
        print(f"\nNew plan created: {new_result['plan_id']}")


# ============================================================================
# EXAMPLE 10: Integration with Existing System
# ============================================================================

def example_integration():
    """Example: Using both LangGraph planner and traditional DAG orchestrator"""
    
    planner = setup_planner()
    
    # Request that could use either approach
    user_request = "Process incoming data with validation"
    user_id = "user_123"
    session_id = "session_stu"
    
    result = planner.create_plan(
        user_id=user_id,
        session_id=session_id,
        user_request=user_request
    )
    
    print("=== Hybrid Execution ===")
    
    # Check if using existing DAG
    if result['plan_type'] == 'use_existing_dag':
        print("Using traditional DAG orchestrator")
        dag_id = result['execution_plan'].get('details', {}).get('dag_id')
        print(f"DAG ID: {dag_id}")
        
        # The system automatically uses WorkflowOrchestrator
        # User doesn't need to know the difference
    else:
        print("Using LangGraph StateGraph")
        print(f"Custom plan with {len(result['task_breakdown'])} steps")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_plan_summary(planner: LangGraphPlanner, plan_id: str):
    """Get detailed summary of a plan"""
    
    plan = planner.get_plan(plan_id)
    
    if plan:
        print(f"\n=== Plan Summary: {plan_id} ===")
        print(f"User Request: {plan['user_request']}")
        print(f"Plan Type: {plan['plan_type']}")
        print(f"Status: {plan['status']}")
        print(f"Created: {plan['created_at']}")
        print(f"\n{plan['plan_summary']}")
    else:
        print(f"Plan {plan_id} not found")


def list_all_plans(planner: LangGraphPlanner, user_id: str):
    """List all plans for a user"""
    
    # This would require a method in the planner
    # For now, query database directly
    from db.database import get_db
    
    db = get_db()
    plans = db.fetchall(
        "SELECT plan_id, user_request, plan_type, status, created_at "
        "FROM lgraph_plans WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    
    print(f"\n=== Plans for User {user_id} ===")
    for plan in plans:
        print(f"\n{plan['plan_id']}")
        print(f"  Request: {plan['user_request'][:60]}...")
        print(f"  Type: {plan['plan_type']}")
        print(f"  Status: {plan['status']}")
        print(f"  Created: {plan['created_at']}")


# ============================================================================
# KEY FEATURES DEMONSTRATION
# ============================================================================

def demonstrate_key_features():
    """Demonstrate key features of LangGraph planner"""
    
    print("=" * 80)
    print("LANGGRAPH PLANNER - KEY FEATURES")
    print("=" * 80)
    
    features = [
        {
            "name": "Autonomous Planning",
            "description": "Supervisor agent analyzes request and automatically decides "
                         "whether to use existing DAG or create custom StateGraph"
        },
        {
            "name": "Dynamic StateGraph Construction",
            "description": "Creates executable workflows on-the-fly based on available "
                         "agents, tools, and MCP servers"
        },
        {
            "name": "Parallel Execution",
            "description": "Identifies and executes independent tasks in parallel for "
                         "better performance"
        },
        {
            "name": "Looping Support",
            "description": "Supports iterative workflows with configurable conditions "
                         "and max iterations"
        },
        {
            "name": "Conditional Branching",
            "description": "Routes execution based on runtime conditions and results"
        },
        {
            "name": "Human-in-the-Loop",
            "description": "Automatic HITL checkpoints for human review and approval"
        },
        {
            "name": "State Management",
            "description": "Fine-grained state tracking across workflow execution"
        },
        {
            "name": "Hybrid Integration",
            "description": "Seamlessly integrates with existing DAG-based orchestrator"
        },
        {
            "name": "Approval Workflow",
            "description": "User reviews and approves plans before execution"
        },
        {
            "name": "Comprehensive Monitoring",
            "description": "Detailed logging and status tracking for all executions"
        }
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"\n{i}. {feature['name']}")
        print(f"   {feature['description']}")
    
    print("\n" + "=" * 80)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Run examples to demonstrate LangGraph planner capabilities
    """
    
    print("\n" + "=" * 80)
    print("LANGGRAPH PLANNER - USAGE EXAMPLES")
    print("=" * 80 + "\n")
    
    # Demonstrate features
    demonstrate_key_features()
    
    # Run examples (comment out as needed)
    print("\n\n--- Example 1: Simple Sequential Task ---")
    # example_simple_request()
    
    print("\n\n--- Example 2: Using Existing DAG ---")
    # example_use_existing_dag()
    
    print("\n\n--- Example 3: Parallel Processing ---")
    # example_parallel_processing()
    
    print("\n\n--- Example 4: Human-in-the-Loop ---")
    # example_with_hitl()
    
    print("\n\n--- Example 5: Complex Conditional ---")
    # example_complex_conditional()
    
    print("\n\n--- Example 6: Looping Workflow ---")
    # example_with_loops()
    
    print("\n\n--- Example 7: Autonomous Planning ---")
    # example_autonomous_planning()
    
    print("\n\n--- Example 8: Monitoring ---")
    # example_monitoring()
    
    print("\n\n--- Example 9: Error Handling ---")
    # example_error_handling()
    
    print("\n\n--- Example 10: Integration ---")
    # example_integration()
    
    print("\n" + "=" * 80)
    print("Examples complete!")
    print("=" * 80 + "\n")
