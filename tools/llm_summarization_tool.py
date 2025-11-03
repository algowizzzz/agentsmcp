"""
LLM Summarization Tool for Abhikarta
Handles code summarization using LLMs (mock or real)

© 2025 Model Documentation Integration
"""
import os
from typing import Dict, Any, List
from tools.base_tool import BaseTool


class LLMSummarizationTool(BaseTool):
    """Tool for LLM-based code summarization"""
    
    def __init__(self, tool_name: str, description: str, config: Dict[str, Any] = None):
        super().__init__(tool_name, description, config)
        self.prompts_dir = config.get('prompts_dir', 'data/prompts')
        self.default_mock_mode = config.get('default_mock_mode', True)
        self.provider = config.get('provider', 'anthropic')
        self.model = config.get('model', 'claude-sonnet-4.5')
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 2)
        
        # Load prompts
        self.prompts = self._load_prompts()
        
        # Initialize LLM Facade
        self.llm_facade = None
        self._initialize_llm_facade()
    
    def _initialize_llm_facade(self):
        """Initialize LLM Facade for API calls"""
        try:
            from llm.llm_facade import LLMFacade
            self.llm_facade = LLMFacade()
            
            # Test if API key is available
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key and not self.default_mock_mode:
                print("[WARNING] ANTHROPIC_API_KEY not set, will use mock mode")
                self.default_mock_mode = True
        except Exception as e:
            print(f"[WARNING] Could not initialize LLM Facade: {e}. Using mock mode.")
            self.llm_facade = None
            if not self.default_mock_mode:
                self.default_mock_mode = True
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompt templates from files"""
        prompts = {}
        prompt_files = {
            'file_summary': 'file_summary_prompt.txt',
            'hierarchical_summary': 'hierarchical_summary_prompt.txt'
        }
        
        for prompt_name, filename in prompt_files.items():
            filepath = os.path.join(self.prompts_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    prompts[prompt_name] = f.read()
            else:
                prompts[prompt_name] = f"[Prompt not found: {filename}]"
        
        return prompts
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute LLM summarization operations
        
        Args:
            action: Operation to perform (summarize_file, hierarchical_summary, generate_outline)
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with success status and result/error
        """
        try:
            if action == "summarize_file":
                return self._summarize_file(**kwargs)
            elif action == "hierarchical_summary":
                return self._hierarchical_summary(**kwargs)
            elif action == "generate_outline":
                return self._generate_outline(**kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'LLM summarization error: {str(e)}'
            }
    
    def _summarize_file(self, file_path: str, content: str, use_mock: bool = None, template_name: str = None) -> Dict[str, Any]:
        """
        Summarize a single file
        
        Args:
            file_path: Path to the file
            content: File content
            use_mock: Whether to use mock LLM (default from config)
            
        Returns:
            Dictionary with summary
        """
        if use_mock is None:
            use_mock = self.default_mock_mode
        
        # Resolve prompt template with optional overrides from template
        prompt_template = self.prompts.get('file_summary')
        if template_name:
            candidate_path = template_name
            if not os.path.isabs(candidate_path) and os.sep not in candidate_path:
                candidate_path = os.path.join(self.prompts_dir.replace('prompts', 'templates'), f'{template_name}.json')
            try:
                if os.path.exists(candidate_path):
                    import json as _json
                    with open(candidate_path, 'r', encoding='utf-8') as _f:
                        tmpl = _json.load(_f)
                    prm = (tmpl or {}).get('prompts', {})
                    if prm.get('file_summary_prompt_text'):
                        prompt_template = prm['file_summary_prompt_text']
                    elif prm.get('file_summary_prompt_path') and os.path.exists(prm['file_summary_prompt_path']):
                        with open(prm['file_summary_prompt_path'], 'r', encoding='utf-8') as pf:
                            prompt_template = pf.read()
            except Exception:
                pass

        # Format prompt
        prompt = prompt_template.format(
            file_path=file_path,
            content=content
        )
        
        # Generate summary (mock or real)
        if use_mock:
            summary = self._mock_llm_call(prompt, context="file_summary")
        else:
            summary = self._real_llm_call(prompt)
        
        return {
            'success': True,
            'summary': summary,
            'file_path': file_path,
            'mock_mode': use_mock,
            'content_length': len(content)
        }
    
    def _hierarchical_summary(self, parsed_files: List[Dict[str, Any]] = None, file_summaries: Dict[str, Any] = None, use_mock: bool = None, template_name: str = None, debug_dir: str = None, workflow_id: str = None, node_id: str = None) -> Dict[str, Any]:
        """
        Generate hierarchical summary from parsed files or file summaries

        Args:
            parsed_files: List of parsed file dictionaries (preferred)
            file_summaries: Dictionary mapping file paths to summaries (fallback)
            use_mock: Whether to use mock LLM

        Returns:
            Dictionary with hierarchical summary
        """
        if use_mock is None:
            use_mock = self.default_mock_mode

        # Handle parsed files (preferred)
        if parsed_files and isinstance(parsed_files, list):
            # Format parsed files for prompt
            formatted_summaries = self._format_parsed_files(parsed_files)
        elif file_summaries and isinstance(file_summaries, dict):
            # Fallback to file summaries
            parts = []
            for file_path, summary in file_summaries.items():
                if isinstance(summary, dict):
                    txt = summary.get('summary', str(summary))
                else:
                    txt = str(summary)
                parts.append(f"File: {file_path}\nSummary:\n{txt}")
            formatted_summaries = "\n\n".join(parts)
        else:
            # Use mock data
            formatted_summaries = "Mock file summaries for testing purposes"

        # Format file summaries for prompt
        
        # Prepare prompt from default, with optional template overrides
        prompt_template = self.prompts.get('hierarchical_summary', '{file_summaries}')

        # Load template prompt overrides if template_name provided
        if template_name:
            candidate_path = template_name
            if not os.path.isabs(candidate_path) and os.sep not in candidate_path:
                candidate_path = os.path.join('data/templates', f'{template_name}.json')
            try:
                if os.path.exists(candidate_path):
                    import json as _json
                    with open(candidate_path, 'r', encoding='utf-8') as _f:
                        tmpl = _json.load(_f)
                    prm = (tmpl or {}).get('prompts', {})
                    # 1) explicit inline text override
                    if prm.get('hierarchical_summary_prompt_text'):
                        prompt_template = prm['hierarchical_summary_prompt_text']
                    # 2) path override to a file
                    elif prm.get('hierarchical_summary_prompt_path'):
                        pth = prm['hierarchical_summary_prompt_path']
                        if os.path.exists(pth):
                            with open(pth, 'r', encoding='utf-8') as pf:
                                prompt_template = pf.read()
            except Exception:
                pass

        # Format prompt
        prompt = prompt_template.format(
            file_summaries=formatted_summaries
        )

        # Debug artifacts
        if debug_dir:
            try:
                import os
                os.makedirs(debug_dir, exist_ok=True)
                with open(os.path.join(debug_dir, 'hierarchical_prompt.txt'), 'w', encoding='utf-8') as f:
                    f.write(prompt)
                with open(os.path.join(debug_dir, 'file_summaries.txt'), 'w', encoding='utf-8') as f:
                    f.write(formatted_summaries)
            except Exception:
                pass
        
        # Generate summary
        if use_mock:
            summary = self._mock_llm_call(prompt, context="hierarchical_summary")
        else:
            summary = self._real_llm_call(prompt)

        if debug_dir:
            try:
                import os
                with open(os.path.join(debug_dir, 'hierarchical_output.txt'), 'w', encoding='utf-8') as f:
                    f.write(summary)
            except Exception:
                pass
        
        files_count = 0
        if parsed_files and isinstance(parsed_files, list):
            files_count = len(parsed_files)
        elif file_summaries and isinstance(file_summaries, dict):
            files_count = len(file_summaries)

        return {
            'success': True,
            'hierarchical_summary': summary,
            'files_analyzed': files_count,
            'mock_mode': use_mock
        }
    
    def _generate_outline(self, template: Dict[str, Any], summary: str, use_mock: bool = None) -> Dict[str, Any]:
        """
        Generate documentation outline from template and summary
        
        Args:
            template: Documentation template
            summary: Hierarchical summary
            use_mock: Whether to use mock LLM
            
        Returns:
            Dictionary with outline
        """
        if use_mock is None:
            use_mock = self.default_mock_mode
        
        # Simple outline generation based on template structure
        outline = {
            'sections': []
        }
        
        for section in template.get('sections', []):
            section_outline = {
                'id': section.get('id'),
                'title': section.get('title'),
                'description': section.get('description'),
                'key_points': []
            }
            
            # In mock mode, generate simple key points
            if use_mock:
                section_outline['key_points'] = [
                    f"Point 1 for {section.get('title')}",
                    f"Point 2 for {section.get('title')}",
                    f"Point 3 for {section.get('title')}"
                ]
            else:
                # Real LLM would analyze summary and generate specific points
                section_outline['key_points'] = self._generate_section_points(section, summary)
            
            outline['sections'].append(section_outline)
        
        return {
            'success': True,
            'outline': outline,
            'section_count': len(outline['sections']),
            'mock_mode': use_mock
        }
    
    def _mock_llm_call(self, prompt: str, context: str = "generic") -> str:
        """
        Mock LLM response for testing
        
        Args:
            prompt: Input prompt
            context: Context of the call
            
        Returns:
            Mock response string
        """
        if context == "file_summary":
            return """
**Overall Purpose and Role:**
This file serves as a core component of the codebase, implementing key functionality for [specific purpose].

**Key Components and Functionality:**
- Main Class/Function: Implements primary logic
- Helper Functions: Support main operations
- Data Processing: Handles input/output transformations

**Core Algorithms and Logic:**
The file implements [algorithm name] using [approach]. Key steps include:
1. Data validation
2. Core processing
3. Result formatting

**Data Structures:**
- Primary data structure: Dictionary/List of [type]
- Secondary structures: Custom objects for [purpose]

**Dependencies:**
- Internal: Imports from [module names]
- External: Uses [library names] for [purposes]

**Error Handling and Logging:**
- Try-except blocks for [error types]
- Logging at [INFO/DEBUG/ERROR] levels

**Assumptions and Limitations:**
- Assumes input data is [format/type]
- Limited to [constraint]
- Performance considerations: [notes]
"""
        
        elif context == "hierarchical_summary":
            return """
**Overall Model Purpose and Design Philosophy:**
This is a [model type] designed to [primary objective]. The architecture follows a [pattern] approach with modular components.

**Key Functional Blocks/Modules:**
1. Data Ingestion Module: Handles input data loading and validation
2. Core Processing Engine: Implements main calculations
3. Output Generation: Formats and exports results

**Data Flow and Processing Sequence:**
Data flows from ingestion → validation → processing → output generation. Each stage applies transformations and validations.

**Control Flow and Orchestration:**
The main runner script coordinates execution across modules, managing dependencies and sequencing.

**Key Inter-Module Dependencies:**
- Processing engine depends on validated data from ingestion
- Output generation consumes results from processing

**Significant Architectural Patterns:**
- Configuration-driven design
- Separation of concerns between data and logic
- Modular, testable components

**Synthesized Model-Level Assumptions and Limitations:**
- Assumes well-formed input data
- Limited to [scope]
- Performance scales with [factor]
"""
        
        return f"[Mock LLM Response for {context}]\n\nPrompt length: {len(prompt)} characters"
    
    def _real_llm_call(self, prompt: str) -> str:
        """
        Real LLM API call (Claude) with retry logic
        
        Args:
            prompt: Input prompt
            
        Returns:
            LLM response string
        """
        import time
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Try to use Abhikarta's LLM facade
                if self.llm_facade:
                    response = self.llm_facade.generate(
                        prompt=prompt,
                        provider=self.provider,
                        model=self.model,
                        temperature=0.2,
                        max_tokens=8192
                    )
                    
                    # Accept string responses from facade or dict-like responses
                    if isinstance(response, str):
                        if response.strip():
                            return response
                        else:
                            last_error = "Empty string response from LLM"
                            continue
                    if response and isinstance(response, dict):
                        if 'text' in response:
                            return response['text']
                        if 'content' in response:
                            return response['content']
                        last_error = f"Invalid response format: {response}"
                        continue
                    last_error = f"Unexpected response type: {type(response)}"
                    continue
                
                else:
                    # Fallback: Direct API call
                    api_key = os.environ.get('ANTHROPIC_API_KEY')
                    if not api_key:
                        # Gracefully fall back to mock
                        print("[INFO] No API key found, using mock mode")
                        return self._mock_llm_call(prompt, context="file_summary")
                    
                    try:
                        from anthropic import Anthropic
                        client = Anthropic(api_key=api_key)
                        
                        # Map model names for API
                        model_map = {
                            'claude-sonnet-4.5': 'claude-sonnet-4-20250514',
                            'claude-sonnet-4': 'claude-sonnet-4-20250514',
                            'claude-opus-4': 'claude-opus-4-20250514',
                            'claude-haiku-4': 'claude-haiku-4-20250514'
                        }
                        
                        api_model = model_map.get(self.model, 'claude-sonnet-4-20250514')
                        
                        message = client.messages.create(
                            model=api_model,
                            max_tokens=8192,
                            temperature=0.2,
                            messages=[
                                {"role": "user", "content": prompt}
                            ]
                        )
                        
                        return message.content[0].text
                    
                    except Exception as e:
                        last_error = f"Claude API error: {str(e)}"
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (attempt + 1))
                            continue
            
            except Exception as e:
                last_error = f"LLM call error: {str(e)}"
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
        
        # All retries failed, fall back to mock
        print(f"[WARNING] All LLM API attempts failed ({last_error}), falling back to mock mode")
        return self._mock_llm_call(prompt, context="file_summary")

    def _format_parsed_files(self, parsed_files: List[Dict[str, Any]]) -> str:
        """
        Format parsed file data for LLM hierarchical summary prompt

        Args:
            parsed_files: List of parsed file dictionaries

        Returns:
            Formatted string for LLM prompt
        """
        formatted_parts = []

        for file_data in parsed_files:
            relative_path = file_data.get('relative_path', 'unknown')
            file_docstring = file_data.get('file_docstring', '')
            imports = file_data.get('imports', [])
            chunks = file_data.get('chunks', [])

            # Build file summary
            summary_parts = [f"File: {relative_path}"]

            if file_docstring:
                summary_parts.append(f"Purpose: {file_docstring}")

            # Count different types of chunks
            classes = [c for c in chunks if c.get('chunk_type') == 'class']
            functions = [c for c in chunks if c.get('chunk_type') in ['function', 'async_function']]
            methods = [c for c in chunks if c.get('chunk_type') == 'method']

            if classes:
                class_names = [c.get('name', 'Unknown') for c in classes]
                summary_parts.append(f"Classes ({len(classes)}): {', '.join(class_names)}")

            if functions:
                func_names = [f.get('name', 'Unknown') for f in functions[:5]]  # Limit to 5
                if len(functions) > 5:
                    func_names.append(f"... +{len(functions) - 5} more")
                summary_parts.append(f"Functions ({len(functions)}): {', '.join(func_names)}")

            if methods:
                summary_parts.append(f"Methods: {len(methods)} total")

            if imports:
                import_names = [imp.split('.')[-1] for imp in imports[:3]]  # Get module names
                if len(imports) > 3:
                    import_names.append(f"... +{len(imports) - 3} more")
                summary_parts.append(f"Imports: {', '.join(import_names)}")

            # Combine all parts
            formatted_parts.append('\n'.join(summary_parts))

        return '\n\n'.join(formatted_parts)

    def _generate_section_points(self, section: Dict[str, Any], summary: str) -> list:
        """Generate key points for a section based on summary"""
        # Simplified version - in real implementation would use LLM
        return [
            f"Key point 1 based on summary for {section.get('title')}",
            f"Key point 2 based on summary for {section.get('title')}",
            f"Key point 3 based on summary for {section.get('title')}"
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'actions': [
                {
                    'name': 'summarize_file',
                    'description': 'Generate summary for a single file',
                    'parameters': {
                        'file_path': 'Path to the file',
                        'content': 'File content as string',
                        'use_mock': 'Whether to use mock LLM (optional, default from config)'
                    }
                },
                {
                    'name': 'hierarchical_summary',
                    'description': 'Generate hierarchical summary from parsed files or file summaries',
                    'parameters': {
                        'parsed_files': 'List of parsed file dictionaries (preferred)',
                        'file_summaries': 'Dictionary mapping file paths to summaries (fallback)',
                        'use_mock': 'Whether to use mock LLM (optional)'
                    }
                },
                {
                    'name': 'generate_outline',
                    'description': 'Generate documentation outline from template',
                    'parameters': {
                        'template': 'Documentation template dictionary',
                        'summary': 'Hierarchical summary',
                        'use_mock': 'Whether to use mock LLM (optional)'
                    }
                }
            ]
        }

