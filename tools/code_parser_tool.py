"""
Code Parser Tool for Abhikarta
Parses Python code into AST structures for documentation

© 2025 Model Documentation Integration
"""
import ast
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from tools.base_tool import BaseTool


@dataclass
class CodeChunk:
    """Represents a chunk of code (function, class, method)"""
    name: str
    content: str
    docstring: Optional[str] = None
    chunk_type: str = "unknown"
    line_range: tuple = (0, 0)
    parent: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ParsedFile:
    """Represents a parsed code file with extracted chunks"""
    file_path: str
    full_content: str
    language: str
    chunks: List[CodeChunk]
    imports: List[str] = None
    file_docstring: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.metadata is None:
            self.metadata = {}


class PythonCodeParser:
    """Parser for Python code using AST"""
    
    def parse_file_content(self, file_content: str, file_path: str = "<string>") -> ParsedFile:
        """Parse Python file content into structured representation"""
        tree = ast.parse(file_content)
        source_lines = file_content.splitlines()
        
        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        
        # Extract file-level docstring
        file_docstring = ast.get_docstring(tree)
        
        # Extract top-level chunks
        chunks: List[CodeChunk] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                chunk = self._extract_function_or_method(node, source_lines)
                chunks.append(chunk)
            elif isinstance(node, ast.ClassDef):
                chunk = self._extract_class(node, source_lines)
                chunks.append(chunk)
        
        return ParsedFile(
            file_path=file_path,
            full_content=file_content,
            language="python",
            chunks=chunks,
            imports=imports,
            file_docstring=file_docstring
        )
    
    def _get_node_source(self, node: ast.AST, source_lines: List[str]) -> str:
        """Extract source code for a given AST node"""
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno is not None else start_line + 1
        end_line = min(end_line, len(source_lines))
        return '\n'.join(source_lines[start_line:end_line])
    
    def _extract_function_or_method(self, 
                                     node: ast.FunctionDef, 
                                     source_lines: List[str], 
                                     parent_class_name: Optional[str] = None) -> CodeChunk:
        """Extract function or method definition"""
        name = node.name
        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno is not None else start_line
        source_code = self._get_node_source(node, source_lines)
        docstring = ast.get_docstring(node)
        
        chunk_type = 'method' if parent_class_name else ('async_function' if isinstance(node, ast.AsyncFunctionDef) else 'function')
        
        # Extract parameters
        parameters = {}
        for arg in node.args.args:
            param_name = arg.arg
            param_type = ast.unparse(arg.annotation) if hasattr(arg, 'annotation') and arg.annotation else None
            parameters[param_name] = {"type": param_type, "default": None}
        
        if node.args.vararg:
            parameters[node.args.vararg.arg] = {"type": "*args", "default": None}
        if node.args.kwarg:
            parameters[node.args.kwarg.arg] = {"type": "**kwargs", "default": None}
        
        return_type = ast.unparse(node.returns) if hasattr(node, 'returns') and node.returns else None
        
        metadata = {
            "parameters": parameters,
            "return_type": return_type
        }
        
        return CodeChunk(
            name=name,
            content=source_code,
            docstring=docstring,
            chunk_type=chunk_type,
            line_range=(start_line, end_line),
            parent=parent_class_name,
            metadata=metadata
        )
    
    def _extract_class(self, node: ast.ClassDef, source_lines: List[str], parent_name: Optional[str] = None) -> CodeChunk:
        """Extract class definition including methods"""
        name = node.name
        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno is not None else start_line
        source_code = self._get_node_source(node, source_lines)
        docstring = ast.get_docstring(node)
        
        # Extract base classes
        bases = [ast.unparse(base) for base in node.bases]
        
        metadata = {
            "bases": bases,
            "methods": []
        }
        
        # Extract methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_chunk = self._extract_function_or_method(item, source_lines, parent_class_name=name)
                metadata["methods"].append({
                    "name": method_chunk.name,
                    "type": method_chunk.chunk_type,
                    "docstring": method_chunk.docstring,
                    "line_range": method_chunk.line_range
                })
        
        return CodeChunk(
            name=name,
            content=source_code,
            docstring=docstring,
            chunk_type='class',
            line_range=(start_line, end_line),
            parent=parent_name,
            metadata=metadata
        )


class CodeParserTool(BaseTool):
    """Tool for parsing code files into AST structures"""
    
    def __init__(self, tool_name: str, description: str, config: Dict[str, Any] = None):
        super().__init__(tool_name, description, config)
        self.parser = PythonCodeParser()
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute code parsing operations
        
        Args:
            action: Operation to perform (parse_python_file, extract_metadata, analyze_structure)
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with success status and result/error
        """
        try:
            if action == "parse_python_file":
                return self._parse_python_file(**kwargs)
            elif action == "parse_files_batch":
                return self._parse_files_batch(**kwargs)
            elif action == "extract_metadata":
                return self._extract_metadata(**kwargs)
            elif action == "analyze_structure":
                return self._analyze_structure(**kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Code parser error: {str(e)}'
            }

    def _parse_files_batch(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse a batch of files and extract structured information

        Args:
            files: List of file dictionaries from scan_codebase

        Returns:
            Dictionary with parsed file information
        """
        try:
            parsed_files = []
            file_summaries = {}

            for file_data in files:
                file_path = file_data.get('path', '')
                relative_path = file_data.get('relative_path', '')

                # Only parse Python files
                if not file_path.endswith('.py'):
                    continue

                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Parse the file
                    parsed_file = self.parser.parse_file_content(content, file_path)

                    # Convert to dictionary and add metadata
                    file_dict = {
                        'file_path': file_path,
                        'relative_path': relative_path,
                        'language': parsed_file.language,
                        'file_docstring': parsed_file.file_docstring,
                        'imports': parsed_file.imports,
                        'chunks': [asdict(chunk) for chunk in parsed_file.chunks],
                        'metadata': parsed_file.metadata
                    }

                    parsed_files.append(file_dict)

                    # Create a summary for LLM
                    summary_parts = []
                    if parsed_file.file_docstring:
                        summary_parts.append(f"Purpose: {parsed_file.file_docstring[:200]}...")

                    classes = [c for c in parsed_file.chunks if c.chunk_type == 'class']
                    functions = [c for c in parsed_file.chunks if c.chunk_type in ['function', 'async_function']]

                    if classes:
                        summary_parts.append(f"Classes: {', '.join(c.name for c in classes)}")
                    if functions:
                        summary_parts.append(f"Functions: {', '.join(f.name for f in functions[:5])}")
                    if parsed_file.imports:
                        summary_parts.append(f"Imports: {', '.join(parsed_file.imports[:3])}")

                    file_summaries[relative_path] = {
                        'summary': '\\n'.join(summary_parts) if summary_parts else 'Python module with basic functionality',
                        'classes': len(classes),
                        'functions': len(functions),
                        'imports': len(parsed_file.imports)
                    }

                except Exception as e:
                    # Log error but continue with other files
                    print(f"Warning: Could not parse {file_path}: {e}")
                    continue

            return {
                'success': True,
                'parsed_files': parsed_files,
                'file_summaries': file_summaries,
                'total_parsed': len(parsed_files)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Batch parsing error: {str(e)}'
            }

    def _parse_python_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse Python file into AST chunks
        
        Args:
            file_path: Path to the file being parsed
            content: File content as string
            
        Returns:
            Dictionary with parsed file structure
        """
        try:
            parsed_file = self.parser.parse_file_content(content, file_path)
            
            # Convert to serializable format
            result = {
                'file_path': parsed_file.file_path,
                'language': parsed_file.language,
                'file_docstring': parsed_file.file_docstring,
                'imports': parsed_file.imports,
                'chunks': []
            }
            
            for chunk in parsed_file.chunks:
                chunk_data = {
                    'name': chunk.name,
                    'type': chunk.chunk_type,
                    'docstring': chunk.docstring,
                    'line_range': list(chunk.line_range),
                    'parent': chunk.parent,
                    'metadata': chunk.metadata
                }
                result['chunks'].append(chunk_data)
            
            return {
                'success': True,
                'parsed_file': result,
                'chunk_count': len(result['chunks']),
                'import_count': len(result['imports'])
            }
        
        except SyntaxError as e:
            return {
                'success': False,
                'error': f'Python syntax error: {str(e)}',
                'line': e.lineno if hasattr(e, 'lineno') else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Parse error: {str(e)}'
            }
    
    def _extract_metadata(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from parsed file
        
        Args:
            parsed_data: Previously parsed file data
            
        Returns:
            Dictionary with extracted metadata
        """
        try:
            metadata = {
                'file_path': parsed_data.get('file_path'),
                'language': parsed_data.get('language'),
                'imports': parsed_data.get('imports', []),
                'file_docstring': parsed_data.get('file_docstring'),
                'functions': [],
                'classes': [],
                'methods': []
            }
            
            for chunk in parsed_data.get('chunks', []):
                if chunk['type'] in ['function', 'async_function']:
                    metadata['functions'].append({
                        'name': chunk['name'],
                        'docstring': chunk['docstring'],
                        'parameters': chunk['metadata'].get('parameters', {}),
                        'return_type': chunk['metadata'].get('return_type')
                    })
                elif chunk['type'] == 'class':
                    metadata['classes'].append({
                        'name': chunk['name'],
                        'docstring': chunk['docstring'],
                        'bases': chunk['metadata'].get('bases', []),
                        'method_count': len(chunk['metadata'].get('methods', []))
                    })
                elif chunk['type'] == 'method':
                    metadata['methods'].append({
                        'name': chunk['name'],
                        'parent_class': chunk['parent'],
                        'docstring': chunk['docstring']
                    })
            
            return {
                'success': True,
                'metadata': metadata,
                'summary': {
                    'total_imports': len(metadata['imports']),
                    'total_functions': len(metadata['functions']),
                    'total_classes': len(metadata['classes']),
                    'total_methods': len(metadata['methods'])
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Metadata extraction error: {str(e)}'
            }
    
    def _analyze_structure(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze relationships between parsed files
        
        Args:
            files: List of parsed file dictionaries
            
        Returns:
            Dictionary with structure analysis
        """
        try:
            all_imports = []
            all_classes = []
            all_functions = []
            dependency_map = {}
            
            for file_data in files:
                file_path = file_data.get('file_path', 'unknown')
                imports = file_data.get('imports', [])
                all_imports.extend(imports)
                
                dependency_map[file_path] = imports
                
                for chunk in file_data.get('chunks', []):
                    if chunk['type'] == 'class':
                        all_classes.append({
                            'name': chunk['name'],
                            'file': file_path
                        })
                    elif chunk['type'] in ['function', 'async_function']:
                        all_functions.append({
                            'name': chunk['name'],
                            'file': file_path
                        })
            
            return {
                'success': True,
                'analysis': {
                    'total_files': len(files),
                    'total_classes': len(all_classes),
                    'total_functions': len(all_functions),
                    'unique_imports': list(set(all_imports)),
                    'dependency_map': dependency_map
                },
                'classes': all_classes,
                'functions': all_functions
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Structure analysis error: {str(e)}'
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'actions': [
                {
                    'name': 'parse_python_file',
                    'description': 'Parse Python file into AST chunks',
                    'parameters': {
                        'file_path': 'Path to the file',
                        'content': 'File content as string'
                    }
                },
                {
                    'name': 'parse_files_batch',
                    'description': 'Parse multiple Python files and extract structured information',
                    'parameters': {
                        'files': 'List of file dictionaries from scan_codebase'
                    }
                },
                {
                    'name': 'extract_metadata',
                    'description': 'Extract metadata from parsed file',
                    'parameters': {
                        'parsed_data': 'Previously parsed file data'
                    }
                },
                {
                    'name': 'analyze_structure',
                    'description': 'Analyze relationships between files',
                    'parameters': {
                        'files': 'List of parsed file dictionaries'
                    }
                }
            ]
        }

