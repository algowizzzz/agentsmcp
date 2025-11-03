"""
Code Analyzer Tool for Abhikarta
Analyzes code to detect languages, extract dependencies, and identify functional blocks

© 2025 Model Documentation Integration
"""
import os
import re
from typing import Dict, Any, List
from tools.base_tool import BaseTool


class CodeAnalyzerTool(BaseTool):
    """Tool for code analysis - language detection, dependency extraction"""
    
    def __init__(self, tool_name: str, description: str, config: Dict[str, Any] = None):
        super().__init__(tool_name, description, config)
        
        # Language detection patterns
        self.language_patterns = {
            'python': {
                'extensions': ['.py', '.pyw'],
                'patterns': [r'^import\s+', r'^from\s+\w+\s+import', r'^def\s+\w+', r'^class\s+\w+']
            },
            'javascript': {
                'extensions': ['.js', '.jsx', '.mjs'],
                'patterns': [r'^import\s+', r'^const\s+\w+\s*=', r'^function\s+\w+', r'^export\s+']
            },
            'typescript': {
                'extensions': ['.ts', '.tsx'],
                'patterns': [r'^import\s+', r'^interface\s+\w+', r'^type\s+\w+', r':\s*\w+\s*=']
            },
            'java': {
                'extensions': ['.java'],
                'patterns': [r'^package\s+', r'^import\s+java\.', r'^public\s+class\s+', r'^private\s+']
            },
            'go': {
                'extensions': ['.go'],
                'patterns': [r'^package\s+', r'^import\s+\(', r'^func\s+\w+', r'^type\s+\w+\s+struct']
            }
        }
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute code analysis operations
        
        Args:
            action: Operation to perform (detect_language, extract_dependencies, identify_functional_blocks)
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with success status and result/error
        """
        try:
            if action == "detect_language":
                return self._detect_language(**kwargs)
            elif action == "extract_dependencies":
                return self._extract_dependencies(**kwargs)
            elif action == "identify_functional_blocks":
                return self._identify_functional_blocks(**kwargs)
            elif action == "analyze_file":
                return self._analyze_file(**kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Code analysis error: {str(e)}'
            }
    
    def _detect_language(self, file_path: str, content: str = None) -> Dict[str, Any]:
        """
        Detect programming language of a file
        
        Args:
            file_path: Path to the file
            content: File content (optional, for pattern matching)
            
        Returns:
            Dictionary with detected language
        """
        # Get file extension
        _, ext = os.path.splitext(file_path)
        
        detected_languages = []
        confidence_scores = {}
        
        # Check by extension first
        for lang, lang_info in self.language_patterns.items():
            if ext in lang_info['extensions']:
                detected_languages.append(lang)
                confidence_scores[lang] = 1.0
        
        # If content provided, check patterns
        if content and not detected_languages:
            for lang, lang_info in self.language_patterns.items():
                matches = 0
                for pattern in lang_info['patterns']:
                    if re.search(pattern, content, re.MULTILINE):
                        matches += 1
                
                if matches > 0:
                    confidence = matches / len(lang_info['patterns'])
                    confidence_scores[lang] = confidence
                    if confidence > 0.5:
                        detected_languages.append(lang)
        
        # Select best match
        if detected_languages:
            primary_language = max(confidence_scores, key=confidence_scores.get)
        else:
            primary_language = 'unknown'
        
        return {
            'success': True,
            'file_path': file_path,
            'language': primary_language,
            'confidence': confidence_scores.get(primary_language, 0.0),
            'all_detected': list(confidence_scores.keys())
        }
    
    def _extract_dependencies(self, file_path: str, content: str, 
                            language: str = None) -> Dict[str, Any]:
        """
        Extract dependencies from code
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language (auto-detected if not provided)
            
        Returns:
            Dictionary with extracted dependencies
        """
        if not language:
            detect_result = self._detect_language(file_path, content)
            language = detect_result['language']
        
        dependencies = {
            'imports': [],
            'internal': [],
            'external': []
        }
        
        if language == 'python':
            dependencies = self._extract_python_dependencies(content)
        elif language in ['javascript', 'typescript']:
            dependencies = self._extract_js_dependencies(content)
        elif language == 'java':
            dependencies = self._extract_java_dependencies(content)
        elif language == 'go':
            dependencies = self._extract_go_dependencies(content)
        
        return {
            'success': True,
            'file_path': file_path,
            'language': language,
            'dependencies': dependencies,
            'total_imports': len(dependencies['imports'])
        }
    
    def _extract_python_dependencies(self, content: str) -> Dict[str, List[str]]:
        """Extract Python imports and dependencies"""
        dependencies = {
            'imports': [],
            'internal': [],
            'external': []
        }
        
        # Match: import module
        import_pattern = r'^import\s+([\w.]+)'
        # Match: from module import ...
        from_pattern = r'^from\s+([\w.]+)\s+import'
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Match import statements
            import_match = re.match(import_pattern, line)
            if import_match:
                module = import_match.group(1).split('.')[0]
                dependencies['imports'].append(module)
                
                # Classify as internal or external
                if module.startswith('_') or '.' in import_match.group(1):
                    dependencies['internal'].append(module)
                else:
                    dependencies['external'].append(module)
            
            # Match from...import statements
            from_match = re.match(from_pattern, line)
            if from_match:
                module = from_match.group(1).split('.')[0]
                if module not in dependencies['imports']:
                    dependencies['imports'].append(module)
                    
                    if module.startswith('.') or module.startswith('_'):
                        dependencies['internal'].append(module)
                    else:
                        dependencies['external'].append(module)
        
        return dependencies
    
    def _extract_js_dependencies(self, content: str) -> Dict[str, List[str]]:
        """Extract JavaScript/TypeScript imports"""
        dependencies = {
            'imports': [],
            'internal': [],
            'external': []
        }
        
        # Match: import ... from 'module'
        import_pattern = r"import\s+.+\s+from\s+['\"]([^'\"]+)['\"]"
        # Match: require('module')
        require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
        
        for line in content.split('\n'):
            # ES6 imports
            for match in re.finditer(import_pattern, line):
                module = match.group(1)
                dependencies['imports'].append(module)
                
                # Classify
                if module.startswith('.') or module.startswith('/'):
                    dependencies['internal'].append(module)
                else:
                    dependencies['external'].append(module)
            
            # CommonJS requires
            for match in re.finditer(require_pattern, line):
                module = match.group(1)
                if module not in dependencies['imports']:
                    dependencies['imports'].append(module)
                    
                    if module.startswith('.') or module.startswith('/'):
                        dependencies['internal'].append(module)
                    else:
                        dependencies['external'].append(module)
        
        return dependencies
    
    def _extract_java_dependencies(self, content: str) -> Dict[str, List[str]]:
        """Extract Java imports"""
        dependencies = {
            'imports': [],
            'internal': [],
            'external': []
        }
        
        import_pattern = r'^import\s+([\w.]+);'
        
        for line in content.split('\n'):
            match = re.match(import_pattern, line.strip())
            if match:
                import_path = match.group(1)
                dependencies['imports'].append(import_path)
                
                # Classify by package prefix
                if import_path.startswith('java.') or import_path.startswith('javax.'):
                    dependencies['external'].append(import_path)
                else:
                    dependencies['internal'].append(import_path)
        
        return dependencies
    
    def _extract_go_dependencies(self, content: str) -> Dict[str, List[str]]:
        """Extract Go imports"""
        dependencies = {
            'imports': [],
            'internal': [],
            'external': []
        }
        
        # Single import
        single_pattern = r'^import\s+"([^"]+)"'
        # Multi-line imports
        in_import_block = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('import ('):
                in_import_block = True
                continue
            elif line == ')' and in_import_block:
                in_import_block = False
                continue
            
            if in_import_block:
                match = re.match(r'"([^"]+)"', line)
                if match:
                    package = match.group(1)
                    dependencies['imports'].append(package)
                    
                    # Classify
                    if '/' in package:
                        dependencies['external'].append(package)
                    else:
                        dependencies['internal'].append(package)
            else:
                match = re.match(single_pattern, line)
                if match:
                    package = match.group(1)
                    dependencies['imports'].append(package)
                    
                    if '/' in package:
                        dependencies['external'].append(package)
                    else:
                        dependencies['internal'].append(package)
        
        return dependencies
    
    def _identify_functional_blocks(self, file_path: str, content: str, 
                                   language: str = None) -> Dict[str, Any]:
        """
        Identify functional blocks (classes, functions) in code
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            
        Returns:
            Dictionary with identified functional blocks
        """
        if not language:
            detect_result = self._detect_language(file_path, content)
            language = detect_result['language']
        
        blocks = {
            'classes': [],
            'functions': [],
            'methods': []
        }
        
        if language == 'python':
            blocks = self._identify_python_blocks(content)
        elif language in ['javascript', 'typescript']:
            blocks = self._identify_js_blocks(content)
        
        return {
            'success': True,
            'file_path': file_path,
            'language': language,
            'blocks': blocks,
            'total_classes': len(blocks['classes']),
            'total_functions': len(blocks['functions'])
        }
    
    def _identify_python_blocks(self, content: str) -> Dict[str, List[str]]:
        """Identify Python classes and functions"""
        blocks = {
            'classes': [],
            'functions': [],
            'methods': []
        }
        
        class_pattern = r'^class\s+(\w+)'
        func_pattern = r'^def\s+(\w+)'
        method_pattern = r'^\s+def\s+(\w+)'
        
        for line in content.split('\n'):
            # Classes
            class_match = re.match(class_pattern, line)
            if class_match:
                blocks['classes'].append(class_match.group(1))
            
            # Top-level functions
            func_match = re.match(func_pattern, line)
            if func_match:
                blocks['functions'].append(func_match.group(1))
            
            # Methods (indented functions)
            method_match = re.match(method_pattern, line)
            if method_match:
                blocks['methods'].append(method_match.group(1))
        
        return blocks
    
    def _identify_js_blocks(self, content: str) -> Dict[str, List[str]]:
        """Identify JavaScript/TypeScript classes and functions"""
        blocks = {
            'classes': [],
            'functions': [],
            'methods': []
        }
        
        class_pattern = r'class\s+(\w+)'
        func_pattern = r'function\s+(\w+)'
        arrow_pattern = r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>'
        
        for line in content.split('\n'):
            # Classes
            for match in re.finditer(class_pattern, line):
                blocks['classes'].append(match.group(1))
            
            # Functions
            for match in re.finditer(func_pattern, line):
                blocks['functions'].append(match.group(1))
            
            # Arrow functions
            for match in re.finditer(arrow_pattern, line):
                blocks['functions'].append(match.group(1))
        
        return blocks
    
    def _analyze_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Comprehensive file analysis
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            Dictionary with complete analysis
        """
        # Detect language
        lang_result = self._detect_language(file_path, content)
        language = lang_result['language']
        
        # Extract dependencies
        deps_result = self._extract_dependencies(file_path, content, language)
        
        # Identify functional blocks
        blocks_result = self._identify_functional_blocks(file_path, content, language)
        
        return {
            'success': True,
            'file_path': file_path,
            'language': language,
            'confidence': lang_result['confidence'],
            'dependencies': deps_result['dependencies'],
            'functional_blocks': blocks_result['blocks'],
            'metrics': {
                'lines': len(content.split('\n')),
                'characters': len(content),
                'imports': len(deps_result['dependencies']['imports']),
                'classes': len(blocks_result['blocks']['classes']),
                'functions': len(blocks_result['blocks']['functions'])
            }
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'actions': [
                {
                    'name': 'detect_language',
                    'description': 'Detect programming language of a file',
                    'parameters': {
                        'file_path': 'Path to the file',
                        'content': 'File content (optional)'
                    }
                },
                {
                    'name': 'extract_dependencies',
                    'description': 'Extract dependencies from code',
                    'parameters': {
                        'file_path': 'Path to the file',
                        'content': 'File content',
                        'language': 'Programming language (optional)'
                    }
                },
                {
                    'name': 'identify_functional_blocks',
                    'description': 'Identify classes and functions',
                    'parameters': {
                        'file_path': 'Path to the file',
                        'content': 'File content',
                        'language': 'Programming language (optional)'
                    }
                },
                {
                    'name': 'analyze_file',
                    'description': 'Comprehensive file analysis',
                    'parameters': {
                        'file_path': 'Path to the file',
                        'content': 'File content'
                    }
                }
            ]
        }

