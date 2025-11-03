"""
Dynamic DAG Generator
Generates documentation DAGs dynamically from templates

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import json
import os
from typing import Dict, Any, List
import re


class DynamicDAGGenerator:
    """Generate DAGs dynamically from documentation templates"""
    
    def __init__(self, templates_dir: str = 'data/templates'):
        self.templates_dir = templates_dir
    
    def generate_documentation_dag(self, template_name: str, dag_id: str = None) -> Dict[str, Any]:
        """
        Generate a full documentation DAG from a template
        
        Args:
            template_name: Name of template file (without .json)
            dag_id: Optional DAG ID (defaults to template_name + "_dag")
            
        Returns:
            Complete DAG configuration dictionary
        """
        # Load template
        template = self._load_template(template_name)
        
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Generate DAG ID
        if not dag_id:
            dag_id = f"{template_name}_generated_dag"
        
        # Extract H1 sections (top-level sections only)
        h1_sections = self._extract_h1_sections(template)
        
        print(f"[DynamicDAGGenerator] Found {len(h1_sections)} H1 sections in template")
        for section in h1_sections:
            print(f"  - {section['id']}: {section['title']}")
        
        # Build DAG structure
        dag = {
            "dag_id": dag_id,
            "name": f"Dynamic {template['name']}",
            "description": f"Auto-generated from template: {template['name']}. Adapts to template changes automatically.",
            "nodes": [],
            "start_nodes": ["scan_codebase"],
            "parameters": {
                "codebase_path": {
                    "description": "Path to the codebase to document",
                    "required": True,
                    "type": "string",
                    "example": "/path/to/project"
                },
                "output_path": {
                    "description": "Path to write final documentation",
                    "required": False,
                    "type": "string",
                    "default": f"/tmp/abhikarta_{dag_id}_output.md"
                },
                "template_name": {
                    "description": "Template to use for documentation structure",
                    "required": False,
                    "type": "string",
                    "default": template_name
                },
                "metadata": {
                    "description": "Project metadata (name, version, authors, etc.)",
                    "required": False,
                    "type": "object",
                    "default": {
                        "doc_id": "AUTO-GENERATED",
                        "model_name": "Unknown Model",
                        "doc_version": "1.0",
                        "status": "Draft",
                        "publication_date": "AUTO"
                    }
                }
            }
        }
        
        # Add fixed preprocessing nodes
        dag["nodes"].extend(self._create_preprocessing_nodes())
        
        # Dynamically create section drafting nodes
        section_nodes = self._create_section_nodes(h1_sections)
        dag["nodes"].extend(section_nodes)
        
        # Add assembly and output nodes
        section_node_ids = [f"draft_{section['id']}" for section in h1_sections]
        dag["nodes"].extend(self._create_assembly_nodes(h1_sections, section_node_ids))
        
        return dag
    
    def _load_template(self, template_name: str) -> Dict[str, Any]:
        """Load template from file"""
        template_path = os.path.join(self.templates_dir, f"{template_name}.json")
        
        if not os.path.exists(template_path):
            return None
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _extract_h1_sections(self, template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract H1 (top-level) sections from template
        
        H1 sections are identified by:
        1. No subsections (leaf sections), OR
        2. Title starts with a number (e.g., "1. Introduction")
        3. Not in another section's subsections
        
        Args:
            template: Template dictionary
            
        Returns:
            List of H1 section definitions
        """
        h1_sections = []
        
        for section in template.get('sections', []):
            # Check if this is a top-level section
            # Criteria: Has a numbered title like "1. Introduction" or is executive_summary/conclusion
            title = section.get('title', '')
            section_id = section.get('id', '')
            
            # Pattern: starts with number, or is special section
            is_h1 = (
                re.match(r'^\d+\.', title) or  # Starts with "1." or "2." etc.
                section_id in ['executive_summary', 'conclusion', 'introduction'] or
                not section.get('subsections')  # No subsections = leaf section = H1
            )
            
            if is_h1:
                h1_sections.append(section)
        
        # If no H1 sections found, use all sections
        if not h1_sections:
            print("[WARNING] No H1 sections identified, using all sections")
            h1_sections = template.get('sections', [])
        
        return h1_sections
    
    def _create_preprocessing_nodes(self) -> List[Dict[str, Any]]:
        """Create fixed preprocessing nodes (scan, parse, summarize)"""
        return [
            {
                "node_id": "scan_codebase",
                "node_type": "tool",
                "config": {
                    "tool_name": "filesystem_tool",
                    "input": {
                        "action": "list_directory",
                        "path": "{codebase_path}",
                        "extensions": [".py", ".js", ".ts", ".java", ".go", ".md", ".json"],
                        "recursive": True
                    }
                },
                "dependencies": []
            },
            {
                "node_id": "parse_all_files",
                "node_type": "tool",
                "config": {
                    "tool_name": "code_parser_tool",
                    "input": {
                        "action": "analyze_structure",
                        "files": "{scan_codebase.result.files}"
                    }
                },
                "dependencies": ["scan_codebase"]
            },
            {
                "node_id": "generate_file_summaries",
                "node_type": "tool",
                "config": {
                    "tool_name": "llm_summarization_tool",
                    "input": {
                        "action": "hierarchical_summary",
                        "file_summaries": "{parse_all_files.result.summaries}",
                        "use_mock": False
                    }
                },
                "dependencies": ["parse_all_files"]
            }
        ]
    
    def _create_section_nodes(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create section drafting nodes dynamically
        
        Args:
            sections: List of H1 section definitions from template
            
        Returns:
            List of DAG node configurations
        """
        nodes = []
        
        for section in sections:
            section_id = section['id']
            node_id = f"draft_{section_id}"
            
            # Determine context based on section requirements
            context = {
                "hierarchical_summary": "{generate_file_summaries.result.hierarchical_summary}",
                "metadata": "{metadata}"
            }
            
            # Add file summaries for implementation-heavy sections
            if section_id in ['implementation', 'methodology', 'data']:
                context["file_summaries"] = "{parse_all_files.result.summaries}"
            
            node = {
                "node_id": node_id,
                "node_type": "tool",
                "config": {
                    "tool_name": "section_drafting_tool",
                    "input": {
                        "action": "draft_section",
                        "section_id": section_id,
                        "template_name": "{template_name}",
                        "context": context,
                        "use_mock": False
                    }
                },
                "dependencies": ["generate_file_summaries"]
            }
            
            nodes.append(node)
        
        return nodes
    
    def _create_assembly_nodes(self, sections: List[Dict[str, Any]], 
                               section_node_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Create document assembly and output nodes
        
        Args:
            sections: List of H1 sections
            section_node_ids: List of section node IDs that were created
            
        Returns:
            List of assembly and output node configurations
        """
        # Build sections mapping for assembly
        sections_mapping = {}
        for section in sections:
            section_id = section['id']
            node_id = f"draft_{section_id}"
            sections_mapping[section_id] = f"{{{node_id}.result}}"
        
        return [
            {
                "node_id": "assemble_document",
                "node_type": "tool",
                "config": {
                    "tool_name": "document_assembler_tool",
                    "input": {
                        "action": "assemble_document",
                        "template_name": "{template_name}",
                        "sections": sections_mapping,
                        "metadata": "{metadata}",
                        "output_path": None
                    }
                },
                "dependencies": section_node_ids
            },
            {
                "node_id": "write_final_doc",
                "node_type": "tool",
                "config": {
                    "tool_name": "filesystem_tool",
                    "input": {
                        "action": "write_file",
                        "file_path": "{output_path}",
                        "content": "{assemble_document.result.document}"
                    }
                },
                "dependencies": ["assemble_document"]
            }
        ]
    
    def save_dag(self, dag: Dict[str, Any], output_path: str):
        """Save generated DAG to file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dag, f, indent=2)
        
        print(f"[DynamicDAGGenerator] DAG saved to: {output_path}")


# CLI tool for generating DAGs
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dynamic_dag_generator.py <template_name> [dag_id] [output_path]")
        print("\nExample:")
        print("  python dynamic_dag_generator.py bmo_model_documentation_template")
        print("  python dynamic_dag_generator.py bmo_model_documentation_template bmo_doc_dag")
        sys.exit(1)
    
    template_name = sys.argv[1]
    dag_id = sys.argv[2] if len(sys.argv) > 2 else None
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not output_path:
        output_path = f"config/dags/{dag_id or template_name + '_generated'}.json"
    
    generator = DynamicDAGGenerator()
    dag = generator.generate_documentation_dag(template_name, dag_id)
    generator.save_dag(dag, output_path)
    
    print(f"\n✅ Generated DAG with {len(dag['nodes'])} nodes:")
    for node in dag['nodes']:
        deps = ', '.join(node['dependencies']) if node['dependencies'] else 'Start Node'
        print(f"  • {node['node_id']} → depends on: {deps}")

