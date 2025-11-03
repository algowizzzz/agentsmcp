"""
Import Verification Test
Test that all imports work correctly

© 2025-2030 Ashutosh Sinha
"""

def test_imports():
    """Test all imports for lgraph_planner"""
    
    print("Testing imports...")
    
    # Test LangGraph imports
    try:
        from langgraph.graph import StateGraph, END
        print("✓ langgraph.graph imports OK")
    except ImportError as e:
        print(f"✗ langgraph.graph import failed: {e}")
        print("  Fix: pip install langgraph --break-system-packages")
    
    # Test LangChain imports
    try:
        from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
        print("✓ langchain_core.messages imports OK")
    except ImportError as e:
        print(f"✗ langchain_core.messages import failed: {e}")
        print("  Fix: pip install langchain-core --break-system-packages")
    
    # Test standard library imports
    try:
        import json
        import uuid
        from datetime import datetime
        from typing import Dict, Any, List, Optional, Literal, TypedDict
        from enum import Enum
        print("✓ Standard library imports OK")
    except ImportError as e:
        print(f"✗ Standard library import failed: {e}")
    
    # Test local imports (these may fail if not in correct directory structure)
    try:
        from db.database import get_db
        print("✓ db.database import OK")
    except ImportError as e:
        print(f"⚠ db.database import failed: {e}")
        print("  Note: This is expected if not running from project root")
    
    try:
        from llm.llm_facade import LLMFacade
        print("✓ llm.llm_facade import OK")
    except ImportError as e:
        print(f"⚠ llm.llm_facade import failed: {e}")
        print("  Note: This is expected if not running from project root")
    
    try:
        from agents.agent_registry import AgentRegistry
        print("✓ agents.agent_registry import OK")
    except ImportError as e:
        print(f"⚠ agents.agent_registry import failed: {e}")
        print("  Note: This is expected if not running from project root")
    
    try:
        from tools.tool_registry import ToolRegistry
        print("✓ tools.tool_registry import OK")
    except ImportError as e:
        print(f"⚠ tools.tool_registry import failed: {e}")
        print("  Note: This is expected if not running from project root")
    
    try:
        from dag.dag_registry import DAGRegistry
        print("✓ dag.dag_registry import OK")
    except ImportError as e:
        print(f"⚠ dag.dag_registry import failed: {e}")
        print("  Note: This is expected if not running from project root")
    
    print("\n" + "="*60)
    print("Import test complete!")
    print("="*60)
    print("\nIf you see ⚠ warnings for local imports, make sure:")
    print("1. You're running from the abhikarta project root directory")
    print("2. The directory structure matches:")
    print("   - db/database.py")
    print("   - llm/llm_facade.py")
    print("   - agents/agent_registry.py")
    print("   - tools/tool_registry.py")
    print("   - dag/dag_registry.py (or adjust import in lgraph_planner.py)")


if __name__ == "__main__":
    test_imports()
