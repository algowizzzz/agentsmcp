"""
Section Drafting Tool for Abhikarta
Drafts documentation sections using AI and templates

© 2025 Model Documentation Integration
"""
import os
import json
from typing import Dict, Any, List
from tools.base_tool import BaseTool


class SectionDraftingTool(BaseTool):
    """Tool for drafting documentation sections using templates and LLM"""
    
    def __init__(self, tool_name: str, description: str, config: Dict[str, Any] = None):
        super().__init__(tool_name, description, config)
        self.default_template = config.get('default_template', 'bmo_model_documentation_template')
        self.templates_dir = config.get('templates_dir', 'data/templates')
        self.prompts_dir = config.get('prompts_dir', 'data/prompts')
        self.use_mock = config.get('use_mock', False)
        self.provider = config.get('provider', 'anthropic')
        self.model = config.get('model', 'claude-sonnet-4.5')
        
        # Load template
        self.template = self._load_template()
        
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
            if not api_key and not self.use_mock:
                print("[WARNING] ANTHROPIC_API_KEY not set, will use mock mode")
                self.use_mock = True
        except Exception as e:
            print(f"[WARNING] Could not initialize LLM Facade: {e}. Using mock mode.")
            self.llm_facade = None
            if not self.use_mock:
                self.use_mock = True
    
    def _load_template(self) -> Dict[str, Any]:
        """Load documentation template"""
        template_path = os.path.join(self.templates_dir, f'{self.default_template}.json')
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute section drafting operations
        
        Args:
            action: Operation to perform (draft_section, draft_subsection, draft_from_template)
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with success status and result/error
        """
        try:
            if action == "draft_section":
                return self._draft_section(**kwargs)
            elif action == "draft_subsection":
                return self._draft_subsection(**kwargs)
            elif action == "draft_from_template":
                return self._draft_from_template(**kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Section drafting error: {str(e)}'
            }
    
    def _draft_section(self, section_id: str, context: Dict[str, Any], 
                       template_name: str = None, use_mock: bool = None,
                       debug_dir: str = None, workflow_id: str = None, node_id: str = None) -> Dict[str, Any]:
        """
        Draft a complete section based on template
        
        Args:
            section_id: Section identifier from template
            context: Context data (file summaries, metadata, etc.)
            use_mock: Whether to use mock LLM
            
        Returns:
            Dictionary with drafted section content
        """
        if use_mock is None:
            use_mock = self.use_mock
        
        # Load template by name or absolute/relative path if provided (overrides default)
        template_to_use = self.template
        if template_name:
            candidate_path = template_name
            # If it's not a path reference, resolve within templates_dir and add .json
            if not os.path.isabs(candidate_path) and os.sep not in candidate_path:
                candidate_path = os.path.join(self.templates_dir, f'{template_name}.json')
            if os.path.exists(candidate_path):
                with open(candidate_path, 'r', encoding='utf-8') as f:
                    template_to_use = json.load(f)
        
        # Find section in template
        section_def = self._find_section(section_id, template_to_use)
        if not section_def:
            return {
                'success': False,
                'error': f'Section not found in template: {section_id}'
            }
        
        # Build prompt for section
        # Inject template prompt controls into context if available
        try:
            template_prompts = (template_to_use or {}).get('prompts', {})
            if template_prompts:
                context = dict(context or {})
                context['template_prompts'] = template_prompts
        except Exception:
            pass

        prompt = self._build_section_prompt(section_def, context)

        # Debug: write prompt
        if debug_dir:
            try:
                import os
                os.makedirs(debug_dir, exist_ok=True)
                fn = f"section_{section_def.get('id','section')}_prompt.txt"
                with open(os.path.join(debug_dir, fn), 'w', encoding='utf-8') as f:
                    f.write(prompt)
            except Exception:
                pass
        
        # Generate content
        if use_mock:
            content = self._mock_draft_section(section_def, context)
        else:
            content = self._llm_draft_section(prompt)
        
        # Debug: write content
        if debug_dir:
            try:
                import os
                fn = f"section_{section_def.get('id','section')}_output.md"
                with open(os.path.join(debug_dir, fn), 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception:
                pass

        return {
            'success': True,
            'section_id': section_id,
            'title': section_def.get('title'),
            'content': content,
            'mock_mode': use_mock
        }
    
    def _draft_subsection(self, section_id: str, subsection_id: str, 
                          context: Dict[str, Any], use_mock: bool = None,
                          debug_dir: str = None, workflow_id: str = None, node_id: str = None) -> Dict[str, Any]:
        """
        Draft a subsection
        
        Args:
            section_id: Parent section identifier
            subsection_id: Subsection identifier
            context: Context data
            use_mock: Whether to use mock LLM
            
        Returns:
            Dictionary with drafted subsection content
        """
        if use_mock is None:
            use_mock = self.use_mock
        
        # Find section and subsection
        section_def = self._find_section(section_id)
        if not section_def:
            return {
                'success': False,
                'error': f'Section not found: {section_id}'
            }
        
        subsection_def = self._find_subsection(section_def, subsection_id)
        if not subsection_def:
            return {
                'success': False,
                'error': f'Subsection not found: {subsection_id}'
            }
        
        # Build prompt
        prompt = self._build_subsection_prompt(section_def, subsection_def, context)
        
        # Generate content
        if use_mock:
            content = self._mock_draft_subsection(subsection_def, context)
        else:
            content = self._llm_draft_section(prompt)

        # Debug: write prompt/content
        if debug_dir:
            try:
                import os
                os.makedirs(debug_dir, exist_ok=True)
                with open(os.path.join(debug_dir, f"{section_id}_{subsection_id}_prompt.txt"), 'w', encoding='utf-8') as f:
                    f.write(prompt)
                with open(os.path.join(debug_dir, f"{section_id}_{subsection_id}_output.md"), 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception:
                pass
        
        return {
            'success': True,
            'section_id': section_id,
            'subsection_id': subsection_id,
            'title': subsection_def.get('title'),
            'content': content,
            'mock_mode': use_mock
        }
    
    def _draft_from_template(self, context: Dict[str, Any], 
                            sections_to_draft: List[str] = None,
                            use_mock: bool = None,
                            template_name: str = None,
                            debug_dir: str = None, workflow_id: str = None, node_id: str = None) -> Dict[str, Any]:
        """
        Draft multiple sections from template
        
        Args:
            context: Context data for all sections
            sections_to_draft: List of section IDs to draft (None = all required)
            use_mock: Whether to use mock LLM
            
        Returns:
            Dictionary with all drafted sections
        """
        if use_mock is None:
            use_mock = self.use_mock
        
        # Resolve template to use (allow overriding by template_name)
        template_to_use = self.template
        if template_name:
            candidate_path = template_name
            if not os.path.isabs(candidate_path) and os.sep not in candidate_path:
                candidate_path = os.path.join('data/templates', f'{template_name}.json')
            if os.path.exists(candidate_path):
                with open(candidate_path, 'r', encoding='utf-8') as f:
                    template_to_use = json.load(f)

        # Determine which sections to draft
        if sections_to_draft is None:
            # Draft all sections in the template in order; if "required" present, prefer those
            required_ids = [s['id'] for s in template_to_use.get('sections', []) if s.get('required', False)]
            all_ids = [s['id'] for s in template_to_use.get('sections', [])]
            sections_to_draft = required_ids if required_ids else all_ids
        
        # Draft each section
        drafted_sections = {}
        errors = []
        
        for section_id in sections_to_draft:
            result = self._draft_section(section_id, context, template_name=template_name, use_mock=use_mock, debug_dir=debug_dir, workflow_id=workflow_id, node_id=node_id)
            if result['success']:
                drafted_sections[section_id] = result
            else:
                errors.append(f"{section_id}: {result.get('error')}")
        
        return {
            'success': len(errors) == 0,
            'sections': drafted_sections,
            'sections_drafted': len(drafted_sections),
            'errors': errors if errors else None,
            'mock_mode': use_mock
        }
    
    def _find_section(self, section_id: str, template: Dict[str, Any] = None) -> Dict[str, Any]:
        """Find section definition in template"""
        if template is None:
            template = self.template
        for section in template.get('sections', []):
            if section.get('id') == section_id:
                return section
        return None
    
    def _find_subsection(self, section_def: Dict[str, Any], 
                        subsection_id: str) -> Dict[str, Any]:
        """Find subsection definition in section"""
        for subsection in section_def.get('subsections', []):
            if subsection.get('id') == subsection_id:
                return subsection
        return None
    
    def _build_section_prompt(self, section_def: Dict[str, Any], 
                             context: Dict[str, Any]) -> str:
        """Build LLM prompt for section drafting
        Prefers a single master prompt (prompts.master_prompt_text). Falls back to
        legacy prefix/suffix/overrides if master is not present.
        """
        template_prompts = context.get('template_prompts', {}) or {}

        # 1) If master prompt provided, render it with variables and return
        master_prompt = template_prompts.get('master_prompt_text', '') or ''
        if master_prompt.strip():
            # Build variables
            section_title = section_def.get('title', section_def.get('id', 'Section'))
            # Build requirements string from description + subsections
            requirements_parts = []
            if section_def.get('description'):
                requirements_parts.append(section_def['description'])
            subs = section_def.get('subsections', []) or []
            if subs:
                sub_lines = [f"- {s.get('title', s.get('id'))}: {s.get('description','').strip()}" for s in subs]
                requirements_parts.append("Subsections to cover:\n" + "\n".join(sub_lines))
            section_requirements = "\n".join([p for p in requirements_parts if p]) or "List the essential points relevant to this section."

            # Repo summary
            repo_summary = context.get('hierarchical_summary', '') or ''

            # File summaries (compact)
            file_summaries = ''
            fs = context.get('file_summaries')
            try:
                if fs and isinstance(fs, dict):
                    items = list(fs.items())[:5]
                    file_summaries = "\n".join([f"{path}:\n{str(summary)[:800]}" for path, summary in items])
                elif fs and isinstance(fs, list):
                    items = fs[:5]
                    file_summaries = "\n\n".join([str(x)[:800] for x in items])
            except Exception:
                file_summaries = ''

            # Metadata string
            metadata = context.get('metadata') or {}
            try:
                metadata_str = json.dumps(metadata, indent=2)
            except Exception:
                metadata_str = str(metadata)

            max_words = (template_prompts.get('max_words')
                         or metadata.get('max_words')
                         or 600)

            # Simple {{var}} substitution
            variables = {
                'section_title': section_title,
                'section_requirements': section_requirements,
                'repo_summary': repo_summary,
                'file_summaries': file_summaries,
                'metadata': metadata_str,
                'max_words': str(max_words),
            }
            rendered = master_prompt
            for key, val in variables.items():
                rendered = rendered.replace(f"{{{{{key}}}}}", str(val))
            return rendered

        # 2) Legacy behavior: prefix/suffix/overrides
        prompt_prefix = template_prompts.get('section_prompt_prefix', '') or ''
        prompt_suffix = template_prompts.get('section_prompt_suffix', '') or ''
        overrides = template_prompts.get('overrides', {}) or {}
        section_override = overrides.get(section_def.get('id', ''), '') or ''

        core = f"""You are a technical documentation expert drafting a section for a BMO Model Documentation.

**Section to Draft:**
Title: {section_def.get('title')}
Description: {section_def.get('description')}

**Section Requirements:**
- Required: {section_def.get('required', False)}
- Follow BMO documentation standards
- Use clear, professional language
- Include technical details where appropriate

**Context Information:**
"""
        
        # Add file summaries if available
        if 'file_summaries' in context:
            core += "\n**File Summaries:**\n"
            for file_path, summary in list(context['file_summaries'].items())[:5]:
                core += f"\n{file_path}:\n{summary}\n"
        
        # Add hierarchical summary if available
        if 'hierarchical_summary' in context:
            core += f"\n**Overall Codebase Summary:**\n{context['hierarchical_summary']}\n"
        
        # Add metadata if available
        if 'metadata' in context:
            core += f"\n**Project Metadata:**\n{json.dumps(context['metadata'], indent=2)}\n"
        
        # Add subsections structure if present
        if 'subsections' in section_def:
            core += "\n**Subsections to Cover:**\n"
            for subsection in section_def['subsections']:
                core += f"- {subsection.get('title')}: {subsection.get('description')}\n"
        
        core += """

**Instructions:**
1. Draft the section content in markdown format
2. Use appropriate heading levels (## for section, ### for subsections)
3. Include technical details from the context provided
4. Follow the subsection structure if specified
5. Be thorough but concise
6. Use bullet points, code blocks, and tables where appropriate

Draft the section now:
"""
        # Compose with prefix/suffix/overrides
        parts = []
        if prompt_prefix:
            parts.append(prompt_prefix.strip())
        if section_override:
            parts.append(section_override.strip())
        parts.append(core.strip())
        if prompt_suffix:
            parts.append(prompt_suffix.strip())
        return "\n\n".join([p for p in parts if p])
    
    def _build_subsection_prompt(self, section_def: Dict[str, Any], 
                                subsection_def: Dict[str, Any],
                                context: Dict[str, Any]) -> str:
        """Build LLM prompt for subsection drafting"""
        prompt = f"""You are a technical documentation expert drafting a subsection for BMO Model Documentation.

**Parent Section:** {section_def.get('title')}
**Subsection to Draft:**
Title: {subsection_def.get('title')}
Description: {subsection_def.get('description')}

**Context Information:**
"""
        
        if 'file_summaries' in context:
            prompt += "\n**Relevant Code:**\n"
            for file_path, summary in list(context['file_summaries'].items())[:3]:
                prompt += f"{file_path}: {summary[:200]}...\n"
        
        prompt += """

**Instructions:**
Draft this subsection in markdown format using ### heading level.

Subsection content:
"""
        
        return prompt
    
    def _llm_draft_section(self, prompt: str) -> str:
        """Call LLM to draft section"""
        try:
            if self.llm_facade:
                response = self.llm_facade.generate(
                    prompt=prompt,
                    provider=self.provider,
                    model=self.model,
                    temperature=0.3,
                    max_tokens=4096
                )

                # Accept string responses directly
                if isinstance(response, str):
                    return response
                # Or dict-like responses
                if response and isinstance(response, dict):
                    if 'text' in response:
                        return response['text']
                    if 'content' in response:
                        return response['content']
            
            # Fallback to direct API call
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if api_key:
                from anthropic import Anthropic
                client = Anthropic(api_key=api_key)
                
                message = client.messages.create(
                    model='claude-sonnet-4-20250514',
                    max_tokens=4096,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                return message.content[0].text
        
        except Exception as e:
            print(f"[WARNING] LLM call failed: {e}, using mock")
        
        # Fallback to mock
        return "[LLM API failed, using mock content]"
    
    def _mock_draft_section(self, section_def: Dict[str, Any], 
                           context: Dict[str, Any]) -> str:
        """Generate mock section content"""
        title = section_def.get('title', 'Section')
        description = section_def.get('description', '')
        
        content = f"## {title}\n\n"
        content += f"{description}\n\n"
        
        # Add subsections if present
        if 'subsections' in section_def:
            for subsection in section_def['subsections']:
                content += f"### {subsection.get('title')}\n\n"
                content += f"{subsection.get('description')}\n\n"
                content += "**Key Points:**\n"
                content += "- Point 1: Analysis and discussion\n"
                content += "- Point 2: Technical details\n"
                content += "- Point 3: Conclusions and observations\n\n"
        else:
            content += "**Overview:**\n\n"
            content += "This section provides comprehensive coverage of the topic.\n\n"
            content += "**Key Points:**\n"
            content += "- Point 1: Based on codebase analysis\n"
            content += "- Point 2: Technical implementation details\n"
            content += "- Point 3: Observations and recommendations\n\n"
        
        return content
    
    def _mock_draft_subsection(self, subsection_def: Dict[str, Any], 
                              context: Dict[str, Any]) -> str:
        """Generate mock subsection content"""
        title = subsection_def.get('title', 'Subsection')
        description = subsection_def.get('description', '')
        
        content = f"### {title}\n\n"
        content += f"{description}\n\n"
        content += "**Details:**\n"
        content += "- Key aspect 1\n"
        content += "- Key aspect 2\n"
        content += "- Key aspect 3\n\n"
        
        return content
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'actions': [
                {
                    'name': 'draft_section',
                    'description': 'Draft a complete section from template',
                    'parameters': {
                        'section_id': 'Section identifier from template',
                        'context': 'Context data (file summaries, metadata)',
                        'use_mock': 'Whether to use mock LLM (optional)'
                    }
                },
                {
                    'name': 'draft_subsection',
                    'description': 'Draft a subsection',
                    'parameters': {
                        'section_id': 'Parent section ID',
                        'subsection_id': 'Subsection ID',
                        'context': 'Context data',
                        'use_mock': 'Whether to use mock LLM (optional)'
                    }
                },
                {
                    'name': 'draft_from_template',
                    'description': 'Draft multiple sections from template',
                    'parameters': {
                        'context': 'Context data for all sections',
                        'sections_to_draft': 'List of section IDs (optional, defaults to all required)',
                        'use_mock': 'Whether to use mock LLM (optional)'
                    }
                }
            ]
        }
