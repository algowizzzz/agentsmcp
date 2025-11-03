# Practical Example: Creating a Tool-Enabled Agent


## © 2025-2030 Ashutosh Sinha

This document shows how to extend the current architecture to allow agents to use tools directly.

## Current vs Extended Architecture

### Current Architecture (Existing)
```python
# Tools and agents are separate nodes in workflow
# Agent cannot call tools - orchestrator must do it

Workflow:
  Node 1 (Tool)  → Node 2 (Agent) → Node 3 (Tool)
  get_data         process_data      save_result
```

### Extended Architecture (New Capability)
```python
# Agent can call tools internally during execution

Workflow:
  Node 1 (Tool-Enabled Agent)
    ├─ internally calls: get_data (tool)
    ├─ processes data
    ├─ internally calls: save_result (tool)
    └─ returns final result
```

## Implementation: Tool-Enabled Agent

### Step 1: Create Enhanced Base Agent

**File:** `agents/tool_enabled_agent.py`

```python
"""
Tool-Enabled Agent Base Class
Agents that can dynamically call tools during execution

© 2025-2030 Ashutosh Sinha
"""

from agents.base_agent import BaseAgent
from tools.tool_registry import ToolRegistry
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ToolEnabledAgent(BaseAgent):
    """Base class for agents that can use tools"""

    def __init__(self, agent_id: str, name: str, description: str,
                 config: Dict[str, Any] = None):
        super().__init__(agent_id, name, description, config)
        self.tool_registry = ToolRegistry()  # Get singleton instance
        self.available_tools = self._get_available_tools()

    def _get_available_tools(self) -> List[str]:
        """Get list of tools this agent can use"""
        # Get from config or use all tools
        if 'allowed_tools' in self.config:
            return self.config['allowed_tools']
        else:
            # Return all tool names
            return [tool['tool_name'] for tool in self.tool_registry.list_tools()]

    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call a tool and return its result
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Parameters to pass to the tool
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.available_tools:
            logger.warning(f"Agent {self.agent_id} attempted to use unauthorized tool: {tool_name}")
            return {
                'success': False,
                'error': f'Tool {tool_name} not available to this agent'
            }

        logger.info(f"Agent {self.agent_id} calling tool: {tool_name}")
        result = self.tool_registry.execute_tool(tool_name, **kwargs)

        if result.get('success'):
            logger.info(f"Tool {tool_name} executed successfully")
        else:
            logger.error(f"Tool {tool_name} failed: {result.get('error')}")

        return result

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a tool"""
        return self.tool_registry.get_tool_info(tool_name)

    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all tools available to this agent"""
        all_tools = self.tool_registry.list_tools()
        return [t for t in all_tools if t['tool_name'] in self.available_tools]
```

### Step 2: Create a Concrete Tool-Enabled Agent

**File:** `agents/stock_analysis_agent.py`

```python
"""
Stock Analysis Agent
Analyzes stock data by calling multiple tools

© 2025-2030 Ashutosh Sinha
"""

from agents.tool_enabled_agent import ToolEnabledAgent
from typing import Dict, Any


class StockAnalysisAgent(ToolEnabledAgent):
    """Agent that analyzes stocks using multiple tools"""
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute stock analysis workflow
        
        Input:
            {
                "symbol": "AAPL",
                "analysis_type": "detailed"  # or "quick"
            }
        
        Returns:
            {
                "success": True,
                "result": {
                    "symbol": "AAPL",
                    "current_price": 150.00,
                    "company_info": {...},
                    "analysis": "..."
                }
            }
        """
        symbol = input_data.get('symbol')
        if not symbol:
            return {'success': False, 'error': 'No symbol provided'}
        
        analysis_type = input_data.get('analysis_type', 'quick')
        
        try:
            # Step 1: Get current stock price using a tool
            price_result = self.call_tool('get_stock_price', symbol=symbol)
            if not price_result.get('success'):
                return price_result  # Return error from tool
            
            price_data = price_result['result']
            current_price = price_data.get('price', 0)
            
            # Step 2: For detailed analysis, get more info
            company_info = None
            if analysis_type == 'detailed':
                info_result = self.call_tool('get_stock_info', symbol=symbol)
                if info_result.get('success'):
                    company_info = info_result['result']
            
            # Step 3: Perform analysis (agent's logic)
            analysis = self._analyze_stock_data(
                symbol, current_price, company_info, analysis_type
            )
            
            # Return results
            return {
                'success': True,
                'result': {
                    'symbol': symbol,
                    'current_price': current_price,
                    'company_info': company_info,
                    'analysis': analysis,
                    'analysis_type': analysis_type
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }
    
    def _analyze_stock_data(self, symbol: str, price: float, 
                           info: Dict, analysis_type: str) -> str:
        """Internal method to analyze stock data"""
        if analysis_type == 'quick':
            return f"Stock {symbol} is trading at ${price:.2f}"
        else:
            # More detailed analysis using company info
            market_cap = info.get('market_cap', 'N/A') if info else 'N/A'
            pe_ratio = info.get('pe_ratio', 'N/A') if info else 'N/A'
            
            return f"""Stock Analysis for {symbol}:
            - Current Price: ${price:.2f}
            - Market Cap: {market_cap}
            - P/E Ratio: {pe_ratio}
            - Recommendation: Based on current metrics, this stock appears {'undervalued' if pe_ratio != 'N/A' and pe_ratio < 20 else 'fairly valued'}.
            """
    
    def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return [
            'stock_analysis',
            'price_lookup',
            'company_research',
            'financial_analysis'
        ]
```

### Step 3: Agent Configuration

**File:** `config/agents/stock_analysis_agent.json`

```json
{
  "agent_id": "stock_analysis_agent",
  "name": "Stock Analysis Agent",
  "description": "Analyzes stocks by fetching data from multiple sources",
  "module": "agents.stock_analysis_agent.StockAnalysisAgent",
  "config": {
    "allowed_tools": [
      "get_stock_price",
      "get_stock_info",
      "mcp_stocks_get_stock_price"
    ],
    "cache_results": true,
    "timeout": 30
  }
}
```

### Step 4: Usage in Workflow

#### Option A: Direct Agent Execution (New Capability)
```python
# The agent handles all tool calls internally
{
  "dag_id": "simple_stock_analysis",
  "nodes": [
    {
      "node_id": "analysis",
      "node_type": "agent",
      "agent_id": "stock_analysis_agent",
      "config": {
        "input": {
          "symbol": "AAPL",
          "analysis_type": "detailed"
        }
      },
      "dependencies": []
    }
  ]
}
```

#### Option B: Mixed Approach
```python
# Combine explicit tool nodes with tool-enabled agents
{
  "dag_id": "hybrid_analysis",
  "nodes": [
    {
      "node_id": "fetch_news",
      "node_type": "tool",
      "tool_name": "get_stock_news",
      "config": {"input": {"symbol": "AAPL"}},
      "dependencies": []
    },
    {
      "node_id": "analysis",
      "node_type": "agent",
      "agent_id": "stock_analysis_agent",
      "config": {
        "input": {
          "symbol": "AAPL",
          "analysis_type": "detailed",
          "news": "${fetch_news.result}"  // Pass news from tool node
        }
      },
      "dependencies": ["fetch_news"]
    }
  ]
}
```

## Advanced Example: Multi-Tool Agent with Decision Logic

```python
"""
Research Agent
Dynamically decides which tools to use based on query
"""

from agents.tool_enabled_agent import ToolEnabledAgent
from typing import Dict, Any, List


class ResearchAgent(ToolEnabledAgent):
    """Agent that performs research using multiple information sources"""
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get('query', '')
        research_depth = input_data.get('depth', 'medium')  # light, medium, deep
        
        # Agent decides which tools to use based on query
        tools_to_use = self._determine_tools(query)
        
        # Collect information from multiple tools
        research_results = {}
        for tool_name in tools_to_use:
            result = self._fetch_from_tool(tool_name, query, research_depth)
            if result:
                research_results[tool_name] = result
        
        # Synthesize results
        synthesis = self._synthesize_results(query, research_results)
        
        return {
            'success': True,
            'result': {
                'query': query,
                'tools_used': tools_to_use,
                'raw_data': research_results,
                'synthesis': synthesis
            }
        }
    
    def _determine_tools(self, query: str) -> List[str]:
        """Decide which tools to use based on query keywords"""
        tools = []
        query_lower = query.lower()
        
        # Simple keyword-based tool selection
        if any(word in query_lower for word in ['stock', 'price', 'market']):
            tools.extend(['get_stock_price', 'get_stock_info'])
        
        if any(word in query_lower for word in ['news', 'article', 'current']):
            tools.append('get_stock_news')
        
        if any(word in query_lower for word in ['weather', 'climate']):
            tools.append('get_weather')
        
        # Fallback: use general search tool
        if not tools:
            tools.append('web_search')
        
        # Only use tools available to this agent
        return [t for t in tools if t in self.available_tools]
    
    def _fetch_from_tool(self, tool_name: str, query: str, 
                         depth: str) -> Dict[str, Any]:
        """Fetch data from a tool with error handling"""
        try:
            # Adapt parameters based on tool
            if 'stock' in tool_name.lower():
                # Extract stock symbol from query
                symbol = self._extract_symbol(query)
                result = self.call_tool(tool_name, symbol=symbol)
            else:
                result = self.call_tool(tool_name, query=query)
            
            if result.get('success'):
                return result['result']
        except Exception as e:
            print(f"Error calling {tool_name}: {e}")
        
        return None
    
    def _extract_symbol(self, query: str) -> str:
        """Extract stock symbol from query"""
        # Simple implementation - could be more sophisticated
        words = query.upper().split()
        # Look for 1-5 letter uppercase words (likely stock symbols)
        for word in words:
            if 1 <= len(word) <= 5 and word.isalpha():
                return word
        return "AAPL"  # Default
    
    def _synthesize_results(self, query: str, results: Dict) -> str:
        """Synthesize information from multiple sources"""
        synthesis = f"Research Summary for: {query}\n\n"
        
        for tool_name, data in results.items():
            synthesis += f"From {tool_name}:\n"
            synthesis += f"  {str(data)[:200]}...\n\n"
        
        synthesis += "Conclusion: Based on the gathered information..."
        return synthesis
```

## Testing Tool-Enabled Agents

```python
# Test script
from agents.stock_analysis_agent import StockAnalysisAgent

# Create agent instance
agent = StockAnalysisAgent(
    agent_id="test_agent",
    name="Test Stock Agent",
    description="Testing",
    config={"allowed_tools": ["get_stock_price", "get_stock_info"]}
)

# Test execution
result = agent.execute({
    "symbol": "AAPL",
    "analysis_type": "detailed"
})

print(result)
# Output:
# {
#   "success": True,
#   "result": {
#     "symbol": "AAPL",
#     "current_price": 150.00,
#     "company_info": {...},
#     "analysis": "Stock Analysis for AAPL:..."
#   }
# }
```

## Security Considerations

### Tool Access Control

```python
class ToolEnabledAgent(BaseAgent):
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        # Check 1: Is tool in allowed list?
        if tool_name not in self.available_tools:
            return {'success': False, 'error': 'Unauthorized tool'}
        
        # Check 2: Does user have permission? (if user context available)
        # if self.user_id and not user_has_permission(self.user_id, tool_name):
        #     return {'success': False, 'error': 'User lacks permission'}
        
        # Execute with rate limiting
        return self.tool_registry.execute_tool(tool_name, **kwargs)
```

## Benefits of Tool-Enabled Agents

1. **Flexibility**: Agent decides tool usage dynamically
2. **Simplicity**: Single agent node vs. multiple tool nodes
3. **Intelligence**: Agent can adapt tool selection based on context
4. **Reusability**: Complex logic encapsulated in agent
5. **Maintainability**: Tool logic stays in one place

## When to Use Each Approach

### Use Workflow-Level Tools (Current) When:
- ✅ User needs to review/approve tool usage
- ✅ Clear audit trail required
- ✅ Tool sequence is fixed and known
- ✅ Parallel tool execution needed
- ✅ Human-in-the-loop between tools

### Use Agent-Level Tools (Extended) When:
- ✅ Tool selection should be dynamic
- ✅ Agent needs to adapt to runtime conditions
- ✅ Complex tool orchestration logic
- ✅ Simpler workflow structure desired
- ✅ Agent is trusted to make tool decisions

## Migration Path

To migrate existing workflows to use tool-enabled agents:

1. **Keep existing workflows**: They still work as-is
2. **Create new tool-enabled agents**: For new use cases
3. **Gradual transition**: Convert workflows one at a time
4. **Hybrid approach**: Use both patterns as needed

Example migration:
```python
# Old: 3 nodes (tool-agent-tool)
# New: 1 node (tool-enabled agent)

# Before
{
  "nodes": [
    {"node_id": "fetch", "node_type": "tool", "tool_name": "get_data"},
    {"node_id": "process", "node_type": "agent", "agent_id": "processor"},
    {"node_id": "save", "node_type": "tool", "tool_name": "save_data"}
  ]
}

# After
{
  "nodes": [
    {"node_id": "process", "node_type": "agent", "agent_id": "smart_processor"}
  ]
}
```

The `smart_processor` agent internally calls `get_data`, processes it, and calls `save_data`.

## Copyright Notice

© 2025 - 2030 Ashutosh Sinha.

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
