"""
Template Manager Tool for Abhikarta
Handles BMO documentation templates

© 2025 Model Documentation Integration
"""
import json
import os
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool


class TemplateManagerTool(BaseTool):
    """Tool for managing documentation templates"""
    
    def __init__(self, tool_name: str, description: str, config: Dict[str, Any] = None):
        super().__init__(tool_name, description, config)
        self.templates_dir = config.get('templates_dir', 'data/templates')
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute template management operations
        
        Args:
            action: Operation to perform (load_template, validate_structure, extract_section_schema)
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with success status and result/error
        """
        try:
            if action == "load_template":
                return self._load_template(**kwargs)
            elif action == "validate_structure":
                return self._validate_structure(**kwargs)
            elif action == "extract_section_schema":
                return self._extract_section_schema(**kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Template manager error: {str(e)}'
            }
    
    def _load_template(self, template_path: str) -> Dict[str, Any]:
        """
        Load a documentation template from JSON file
        
        Args:
            template_path: Path to template JSON file
            
        Returns:
            Dictionary with loaded template
        """
        if not os.path.exists(template_path):
            return {
                'success': False,
                'error': f'Template file not found: {template_path}'
            }
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            # Extract template metadata
            metadata = {
                'name': template.get('document_name', 'Unknown'),
                'version': template.get('version', '1.0'),
                'section_count': len(template.get('sections', [])),
                'has_metadata_fields': 'metadata_fields' in template
            }
            
            return {
                'success': True,
                'template': template,
                'metadata': metadata,
                'template_path': template_path
            }
        
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Invalid JSON in template: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error loading template: {str(e)}'
            }
    
    def _validate_structure(self, data: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data structure against template
        
        Args:
            data: Data to validate
            template: Template to validate against
            
        Returns:
            Dictionary with validation result
        """
        try:
            errors = []
            warnings = []
            
            # Check required template sections
            template_sections = template.get('sections', [])
            data_sections = data.get('sections', {})
            
            # Build section ID map from template
            template_section_ids = set()
            for section in template_sections:
                template_section_ids.add(section.get('id'))
                
                # Check for subsections
                if 'subsections' in section:
                    for subsection in section['subsections']:
                        subsection_id = subsection.get('id')
                        template_section_ids.add(subsection_id)
            
            # Check if all template sections are present in data
            missing_sections = template_section_ids - set(data_sections.keys())
            if missing_sections:
                warnings.append(f"Missing sections in data: {', '.join(missing_sections)}")
            
            # Check for extra sections in data
            extra_sections = set(data_sections.keys()) - template_section_ids
            if extra_sections:
                warnings.append(f"Extra sections in data: {', '.join(extra_sections)}")
            
            # Validate metadata fields
            if 'metadata_fields' in template:
                template_metadata_ids = {field['id'] for field in template['metadata_fields']}
                data_metadata = data.get('metadata_values', {})
                
                missing_metadata = template_metadata_ids - set(data_metadata.keys())
                if missing_metadata:
                    warnings.append(f"Missing metadata fields: {', '.join(missing_metadata)}")
            
            # Validate section content
            for section_id, section_data in data_sections.items():
                if not isinstance(section_data, dict):
                    errors.append(f"Section {section_id} is not a dictionary")
                    continue
                
                if 'content' not in section_data:
                    warnings.append(f"Section {section_id} missing 'content' field")
            
            is_valid = len(errors) == 0
            
            return {
                'success': True,
                'is_valid': is_valid,
                'errors': errors,
                'warnings': warnings,
                'sections_validated': len(data_sections),
                'template_sections': len(template_section_ids)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def _extract_section_schema(self, template: Dict[str, Any], section_id: str) -> Dict[str, Any]:
        """
        Extract schema for a specific section from template
        
        Args:
            template: Template dictionary
            section_id: ID of section to extract
            
        Returns:
            Dictionary with section schema
        """
        try:
            # Search for section in template
            for section in template.get('sections', []):
                if section.get('id') == section_id:
                    return {
                        'success': True,
                        'section_schema': section,
                        'section_id': section_id
                    }
                
                # Check subsections
                if 'subsections' in section:
                    for subsection in section['subsections']:
                        if subsection.get('id') == section_id:
                            return {
                                'success': True,
                                'section_schema': subsection,
                                'section_id': section_id,
                                'parent_section': section.get('id')
                            }
            
            return {
                'success': False,
                'error': f'Section not found in template: {section_id}'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Schema extraction error: {str(e)}'
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'actions': [
                {
                    'name': 'load_template',
                    'description': 'Load BMO template from JSON file',
                    'parameters': {
                        'template_path': 'Path to template JSON file'
                    }
                },
                {
                    'name': 'validate_structure',
                    'description': 'Validate data against template structure',
                    'parameters': {
                        'data': 'Data to validate',
                        'template': 'Template to validate against'
                    }
                },
                {
                    'name': 'extract_section_schema',
                    'description': 'Extract schema for specific section',
                    'parameters': {
                        'template': 'Template dictionary',
                        'section_id': 'ID of section to extract'
                    }
                }
            ]
        }

