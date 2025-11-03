"""
Usage Examples for Enhanced LLM Facade
Demonstrates how to use different LLMs across components

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from llm.llm_facade_enhanced import LLMFacade
from planner.planner_enhanced import Planner
from agents.base_agent_enhanced import (
    LLMAgent, CodeGeneratorAgent, DataAnalystAgent, WorkflowPlannerAgent
)


def example_1_basic_llm_usage():
    """Example 1: Basic LLM facade usage"""
    print("=" * 80)
    print("Example 1: Basic LLM Usage")
    print("=" * 80)
    
    # Use default LLM (from config)
    llm = LLMFacade()
    print(f"Using: {llm.get_model_info()}")
    
    response = llm.generate("Explain quantum computing in simple terms")
    print(f"Response: {response[:200]}...")
    
    print()


def example_2_specific_provider():
    """Example 2: Using specific provider and model"""
    print("=" * 80)
    print("Example 2: Specific Provider and Model")
    print("=" * 80)
    
    # Use Claude Sonnet 4.5
    llm_claude = LLMFacade(provider='anthropic', model='claude-sonnet-4.5')
    print(f"Using: {llm_claude.get_model_info()}")
    
    # Use GPT-4o
    llm_openai = LLMFacade(provider='openai', model='gpt-4o')
    print(f"Using: {llm_openai.get_model_info()}")
    
    # Use Gemini
    llm_google = LLMFacade(provider='google', model='gemini-1.5-pro')
    print(f"Using: {llm_google.get_model_info()}")
    
    print()


def example_3_list_available_models():
    """Example 3: List all available models"""
    print("=" * 80)
    print("Example 3: List Available Models")
    print("=" * 80)
    
    models = LLMFacade.list_available_models()
    
    print(f"Found {len(models)} available models:\n")
    for model in models[:5]:  # Show first 5
        print(f"  {model['provider']}/{model['model']}")
        print(f"    Description: {model['description'][:80]}...")
        print(f"    Best for: {', '.join(model['best_for'][:3])}")
        print()
    
    print()


def example_4_recommended_model():
    """Example 4: Get recommended model for task type"""
    print("=" * 80)
    print("Example 4: Recommended Model for Task Type")
    print("=" * 80)
    
    task_types = ['coding', 'data analysis', 'planning', 'reasoning']
    
    for task in task_types:
        provider, model = LLMFacade.get_recommended_model(task)
        print(f"Task: {task:20s} -> {provider}/{model}")
    
    print()


def example_5_planner_with_different_llms():
    """Example 5: Using planner with different LLMs"""
    print("=" * 80)
    print("Example 5: Planner with Different LLMs")
    print("=" * 80)
    
    # Planner with default LLM
    planner1 = Planner()
    print(f"Planner 1 using: {planner1.get_llm_info()}")
    
    # Planner with specific LLM
    planner2 = Planner(llm_provider='anthropic', llm_model='claude-opus-4')
    print(f"Planner 2 using: {planner2.get_llm_info()}")
    
    # Change LLM dynamically
    planner1.set_llm('openai', 'gpt-4o')
    print(f"Planner 1 changed to: {planner1.get_llm_info()}")
    
    print()


def example_6_chat_with_llm_override():
    """Example 6: Chat with LLM override"""
    print("=" * 80)
    print("Example 6: Chat with LLM Override")
    print("=" * 80)
    
    planner = Planner()
    
    # Normal chat
    response1 = planner.chat(
        user_id='user123',
        message='Create a plan for data processing'
    )
    print(f"Default LLM: {response1['llm_used']['provider']}/{response1['llm_used']['model']}")
    
    # Chat with LLM override
    response2 = planner.chat(
        user_id='user123',
        message='Create a detailed plan for data processing',
        llm_override={'provider': 'anthropic', 'model': 'claude-opus-4'}
    )
    print(f"Override LLM: {response2['llm_used']['provider']}/{response2['llm_used']['model']}")
    
    print()


def example_7_create_plan_with_custom_llm():
    """Example 7: Create plan with custom LLM"""
    print("=" * 80)
    print("Example 7: Create Plan with Custom LLM")
    print("=" * 80)
    
    planner = Planner()
    
    # Create plan with specific LLM
    result = planner.create_plan_from_request(
        user_id='user123',
        request='Process customer data and generate insights',
        available_tools=['csv_reader', 'data_processor', 'report_generator'],
        available_agents=['data_analyst', 'report_writer'],
        llm_override={'provider': 'anthropic', 'model': 'claude-sonnet-4.5'}
    )
    
    print(f"Plan ID: {result['plan_id']}")
    print(f"LLM used: {result['llm_used']['provider']}/{result['llm_used']['model']}")
    print(f"Plan: {result['plan']['name']}")
    print(f"Nodes: {len(result['plan']['nodes'])}")
    
    print()


def example_8_optimize_plan():
    """Example 8: Optimize plan with different LLMs"""
    print("=" * 80)
    print("Example 8: Optimize Plan")
    print("=" * 80)
    
    planner = Planner()
    
    # First create a plan
    result = planner.create_plan_from_request(
        user_id='user123',
        request='Process large dataset',
        available_tools=['reader', 'processor'],
        available_agents=['worker']
    )
    
    plan_id = result['plan_id']
    print(f"Original plan: {plan_id}")
    
    # Optimize for speed
    optimized = planner.optimize_plan(
        plan_id=plan_id,
        optimization_goal='speed'
    )
    
    print(f"Optimized plan: {optimized['plan_id']}")
    print(f"LLM used: {optimized['llm_used']['provider']}/{optimized['llm_used']['model']}")
    
    print()


def example_9_llm_agents():
    """Example 9: LLM-powered agents"""
    print("=" * 80)
    print("Example 9: LLM-Powered Agents")
    print("=" * 80)
    
    # Generic LLM agent
    agent1 = LLMAgent(
        agent_id='assistant',
        name='General Assistant',
        description='Helpful AI assistant'
    )
    
    result1 = agent1.execute({
        'prompt': 'Explain blockchain technology'
    })
    print(f"Agent: {agent1.name}")
    print(f"LLM: {result1['llm_used']['provider']}/{result1['llm_used']['model']}")
    print(f"Response: {result1['response'][:100]}...")
    print()
    
    # Code generator agent (auto-selects best model for coding)
    agent2 = CodeGeneratorAgent()
    
    result2 = agent2.execute({
        'language': 'python',
        'requirements': 'Function to calculate fibonacci numbers'
    })
    print(f"Agent: {agent2.name}")
    print(f"LLM: {result2['llm_used']['provider']}/{result2['llm_used']['model']}")
    print(f"Generated code snippet...")
    print()
    
    # Data analyst agent (auto-selects best model for analysis)
    agent3 = DataAnalystAgent()
    
    result3 = agent3.execute({
        'data': 'Sales: [100, 150, 120, 180, 200]',
        'analysis_type': 'trend'
    })
    print(f"Agent: {agent3.name}")
    print(f"LLM: {result3['llm_used']['provider']}/{result3['llm_used']['model']}")
    print()


def example_10_agent_with_custom_llm():
    """Example 10: Agent with custom LLM"""
    print("=" * 80)
    print("Example 10: Agent with Custom LLM")
    print("=" * 80)
    
    # Create agent with specific LLM
    agent = LLMAgent(
        agent_id='custom_agent',
        name='Custom Agent',
        description='Agent with custom LLM',
        llm_provider='anthropic',
        llm_model='claude-opus-4'
    )
    
    print(f"Agent: {agent.name}")
    print(f"LLM: {agent.get_llm_info()}")
    
    # Change LLM dynamically
    agent.set_llm('openai', 'gpt-4o')
    print(f"Changed to: {agent.get_llm_info()}")
    
    print()


def example_11_structured_output():
    """Example 11: Structured output generation"""
    print("=" * 80)
    print("Example 11: Structured Output Generation")
    print("=" * 80)
    
    llm = LLMFacade(provider='anthropic', model='claude-sonnet-4.5')
    
    # Define schema
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "key_points": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number"}
        }
    }
    
    # Generate structured output
    result = llm.generate_structured(
        prompt="Analyze the impact of AI on healthcare",
        schema=schema
    )
    
    print(f"Structured output:")
    print(f"  Title: {result.get('title', 'N/A')}")
    print(f"  Summary: {result.get('summary', 'N/A')[:80]}...")
    print(f"  Key Points: {len(result.get('key_points', []))}")
    
    print()


def example_12_workflow_planner_agent():
    """Example 12: Workflow Planner Agent"""
    print("=" * 80)
    print("Example 12: Workflow Planner Agent")
    print("=" * 80)
    
    # Create workflow planner agent (auto-selects best model)
    agent = WorkflowPlannerAgent()
    
    result = agent.execute({
        'goal': 'Build a customer analytics dashboard',
        'available_tools': ['database', 'chart_generator', 'dashboard'],
        'available_agents': ['data_fetcher', 'analyst', 'visualizer']
    })
    
    print(f"Agent: {agent.name}")
    print(f"LLM: {result['llm_used']['provider']}/{result['llm_used']['model']}")
    print(f"Plan created: {result['success']}")
    print(f"Response: {result['response'][:200]}...")
    
    print()


def example_13_multi_provider_comparison():
    """Example 13: Compare responses from multiple providers"""
    print("=" * 80)
    print("Example 13: Multi-Provider Comparison")
    print("=" * 80)
    
    prompt = "Explain machine learning in 2 sentences"
    
    providers = [
        ('anthropic', 'claude-sonnet-4.5'),
        ('openai', 'gpt-4o'),
        ('google', 'gemini-1.5-flash')
    ]
    
    for provider, model in providers:
        try:
            llm = LLMFacade(provider=provider, model=model)
            response = llm.generate(prompt)
            print(f"\n{provider}/{model}:")
            print(f"  {response[:150]}...")
        except Exception as e:
            print(f"\n{provider}/{model}: Error - {e}")
    
    print()


def example_14_cost_aware_selection():
    """Example 14: Cost-aware model selection"""
    print("=" * 80)
    print("Example 14: Cost-Aware Model Selection")
    print("=" * 80)
    
    models = LLMFacade.list_available_models()
    
    # Sort by cost (lower cost first)
    sorted_models = sorted(
        [m for m in models if 'cost_per_1m_input_tokens' in m],
        key=lambda x: x.get('cost_per_1m_input_tokens', float('inf'))
    )
    
    print("Most cost-effective models:")
    for model in sorted_models[:5]:
        cost = model.get('cost_per_1m_input_tokens', 0)
        print(f"  {model['provider']}/{model['model']}: ${cost:.2f}/1M tokens")
    
    print()


def example_15_auto_refresh_demo():
    """Example 15: Demonstrate auto-refresh capability"""
    print("=" * 80)
    print("Example 15: Auto-Refresh Configuration")
    print("=" * 80)
    
    # LLM facade automatically refreshes config every 10 minutes
    llm = LLMFacade()
    
    print(f"Current configuration:")
    print(f"  Provider: {llm.provider}")
    print(f"  Model: {llm.model}")
    print(f"  Auto-refresh: Enabled (every 10 minutes)")
    print(f"  Last loaded: {llm.config_manager.last_loaded}")
    
    # Force refresh
    llm.config_manager.load_config()
    print(f"  Configuration refreshed!")
    
    print()


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("ENHANCED LLM FACADE USAGE EXAMPLES")
    print("=" * 80 + "\n")
    
    try:
        example_1_basic_llm_usage()
        example_2_specific_provider()
        example_3_list_available_models()
        example_4_recommended_model()
        example_5_planner_with_different_llms()
        example_6_chat_with_llm_override()
        example_7_create_plan_with_custom_llm()
        example_8_optimize_plan()
        example_9_llm_agents()
        example_10_agent_with_custom_llm()
        example_11_structured_output()
        example_12_workflow_planner_agent()
        example_13_multi_provider_comparison()
        example_14_cost_aware_selection()
        example_15_auto_refresh_demo()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
