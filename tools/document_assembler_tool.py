"""
Document Assembler Tool for Abhikarta
Assembles documentation sections into final markdown document

© 2025 Model Documentation Integration
"""
import os
import re
import json
from datetime import datetime
from typing import Dict, Any, List
from tools.base_tool import BaseTool


class DocumentAssemblerTool(BaseTool):
    """Tool for assembling documentation sections into final markdown document"""
    
    def __init__(self, tool_name: str, description: str, config: Dict[str, Any] = None):
        super().__init__(tool_name, description, config)
        self.output_format = config.get('output_format', 'markdown')
        self.include_toc = config.get('include_toc', True)
        self.include_metadata = config.get('include_metadata', True)
        self.toc_depth = config.get('toc_depth', 3)
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute document assembly operations
        
        Args:
            action: Operation to perform (assemble_document, generate_toc, create_metadata)
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with success status and result/error
        """
        try:
            if action == "assemble_document":
                return self._assemble_document(**kwargs)
            elif action == "generate_toc":
                return self._generate_toc(**kwargs)
            elif action == "create_metadata":
                return self._create_metadata(**kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Document assembly error: {str(e)}'
            }
    
    def _assemble_document(self, sections: Dict[str, Any], metadata: Dict[str, Any] = None,
                          template: Dict[str, Any] = None, template_name: str = None, 
                          output_path: str = None, debug_dir: str = None, workflow_id: str = None, node_id: str = None) -> Dict[str, Any]:
        """
        Assemble complete document from sections
        
        Args:
            sections: Dictionary mapping section IDs to section data
            metadata: Document metadata (optional)
            template: Template definition for ordering (optional)
            template_name: Template name to load (optional, alternative to template)
            output_path: Path to write output file (optional)
            
        Returns:
            Dictionary with assembled document
        """
        # Load template by name or absolute/relative path if provided
        if template_name and not template:
            candidate_path = template_name
            if not os.path.isabs(candidate_path) and os.sep not in candidate_path:
                candidate_path = os.path.join('data/templates', f'{template_name}.json')
            if os.path.exists(candidate_path):
                with open(candidate_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
        
        document_parts = []
        
        # 1. Add metadata frontmatter
        if self.include_metadata and metadata:
            frontmatter = self._create_metadata(metadata)
            if frontmatter['success']:
                document_parts.append(frontmatter['frontmatter'])
                document_parts.append('\n\n')
        
        # 2. Collect section content in order
        section_content = self._order_sections(sections, template)
        if debug_dir:
            try:
                os.makedirs(debug_dir, exist_ok=True)
                with open(os.path.join(debug_dir, 'section_order.json'), 'w', encoding='utf-8') as f:
                    json.dump([s.get('title') for s in section_content], f, indent=2)
            except Exception:
                pass
        
        # 3. Generate table of contents
        if self.include_toc:
            toc_result = self._generate_toc(section_content=section_content)
            if toc_result['success']:
                document_parts.append('# Table of Contents\n\n')
                document_parts.append(toc_result['toc'])
                document_parts.append('\n\n')
                document_parts.append('---\n\n')
                if debug_dir:
                    try:
                        with open(os.path.join(debug_dir, 'toc.md'), 'w', encoding='utf-8') as f:
                            f.write(toc_result['toc'])
                    except Exception:
                        pass
        
        # 4. Add all sections
        for section_data in section_content:
            content = section_data.get('content', '')
            if content:
                document_parts.append(content)
                document_parts.append('\n\n')
        
        # 5. Assemble final document
        final_document = ''.join(document_parts)
        if debug_dir:
            try:
                with open(os.path.join(debug_dir, 'assembled.md'), 'w', encoding='utf-8') as f:
                    f.write(final_document)
            except Exception:
                pass
        
        # 6. Write to file if path provided
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_document)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to write document: {str(e)}'
                }
        
        return {
            'success': True,
            'document': final_document,
            'sections_count': len(section_content),
            'character_count': len(final_document),
            'word_count': len(final_document.split()),
            'output_path': output_path
        }
    
    def _order_sections(self, sections: Dict[str, Any], 
                       template: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Order sections according to template or default ordering
        
        Args:
            sections: Dictionary mapping section IDs to section data
            template: Template with section ordering
            
        Returns:
            Ordered list of section data
        """
        ordered_sections = []
        
        if template and 'sections' in template:
            # Order by template
            for section_def in template['sections']:
                section_id = section_def.get('id')
                if section_id in sections:
                    ordered_sections.append(sections[section_id])
        else:
            # Natural ordering (by section ID or title)
            for section_id in sorted(sections.keys()):
                ordered_sections.append(sections[section_id])
        
        return ordered_sections
    
    def _generate_toc(self, section_content: List[Dict[str, Any]] = None,
                     markdown_content: str = None) -> Dict[str, Any]:
        """
        Generate table of contents from section headings
        
        Args:
            section_content: List of section data dictionaries
            markdown_content: Raw markdown content to parse
            
        Returns:
            Dictionary with TOC markdown
        """
        try:
            headings = []
            
            # Extract headings from section content
            if section_content:
                for section in section_content:
                    content = section.get('content', '')
                    headings.extend(self._extract_headings(content))
            
            # Or extract from raw markdown
            elif markdown_content:
                headings = self._extract_headings(markdown_content)
            
            # Build TOC
            toc_lines = []
            for heading in headings:
                level = heading['level']
                title = heading['title']
                anchor = heading['anchor']
                
                # Only include headings up to toc_depth
                if level <= self.toc_depth:
                    indent = '  ' * (level - 1)
                    toc_lines.append(f"{indent}- [{title}](#{anchor})")
            
            toc = '\n'.join(toc_lines)
            
            return {
            'success': True,
            'toc': toc,
                'heading_count': len(headings)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'TOC generation error: {str(e)}'
            }
    
    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract markdown headings from content
        
        Args:
            content: Markdown content
            
        Returns:
            List of heading dictionaries
        """
        headings = []
        
        # Match markdown headings (## Title or ### Title, etc.)
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        
        for line in content.split('\n'):
            match = re.match(heading_pattern, line.strip())
            if match:
                hashes = match.group(1)
                title = match.group(2).strip()
                level = len(hashes)
                
                # Generate anchor (lowercase, spaces to hyphens, remove special chars)
                anchor = re.sub(r'[^\w\s-]', '', title.lower())
                anchor = re.sub(r'[\s_]+', '-', anchor)
                anchor = anchor.strip('-')
                
                headings.append({
                    'level': level,
                    'title': title,
                    'anchor': anchor
                })
        
        return headings
    
    def _create_metadata(self, metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create YAML frontmatter from metadata dictionary
        
        Args:
            metadata_dict: Metadata key-value pairs
            
        Returns:
            Dictionary with formatted frontmatter
        """
        try:
            frontmatter_lines = ['---']
            
            # Add metadata fields
            for key, value in metadata_dict.items():
                if isinstance(value, list):
                    frontmatter_lines.append(f'{key}:')
                    for item in value:
                        frontmatter_lines.append(f'  - {item}')
                elif isinstance(value, str):
                    # Escape quotes in strings
                    escaped_value = value.replace('"', '\\"')
                    frontmatter_lines.append(f'{key}: "{escaped_value}"')
                else:
                    frontmatter_lines.append(f'{key}: {value}')
            
            # Add generation timestamp
            frontmatter_lines.append(f'generated_at: "{datetime.now().isoformat()}"')
            frontmatter_lines.append(f'generator: "Abhikarta Document Assembler"')
            
            frontmatter_lines.append('---')
            
            frontmatter = '\n'.join(frontmatter_lines)
            
            return {
                'success': True,
                'frontmatter': frontmatter
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Metadata creation error: {str(e)}'
            }
    
    def validate_markdown(self, content: str) -> Dict[str, Any]:
        """
        Validate markdown content
        
        Args:
            content: Markdown content to validate
            
        Returns:
            Dictionary with validation results
        """
        issues = []
        
        # Check for common markdown issues
        lines = content.split('\n')
        
        # Check for unclosed code blocks
        code_block_count = 0
        for i, line in enumerate(lines, start=1):
            if line.strip().startswith('```'):
                code_block_count += 1
        
        if code_block_count % 2 != 0:
            issues.append("Unclosed code block detected")
        
        # Check for malformed links
        for i, line in enumerate(lines, start=1):
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            links = re.findall(link_pattern, line)
            for link_text, link_url in links:
                if not link_url.strip():
                    issues.append(f"Line {i}: Empty link URL for '{link_text}'")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues if issues else None,
            'line_count': len(lines),
            'character_count': len(content)
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'actions': [
                {
                    'name': 'assemble_document',
                    'description': 'Assemble complete document from sections',
                    'parameters': {
                        'sections': 'Dictionary mapping section IDs to section data',
                        'metadata': 'Document metadata (optional)',
                        'template': 'Template definition for ordering (optional)',
                        'output_path': 'Path to write output file (optional)'
                    }
                },
                {
                    'name': 'generate_toc',
                    'description': 'Generate table of contents',
                    'parameters': {
                        'section_content': 'List of section data (optional)',
                        'markdown_content': 'Raw markdown content (optional)'
                    }
                },
                {
                    'name': 'create_metadata',
                    'description': 'Create YAML frontmatter',
                    'parameters': {
                        'metadata_dict': 'Metadata key-value pairs'
                    }
                }
            ]
        }
