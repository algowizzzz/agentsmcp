"""
FileSystem Tool for Abhikarta
Handles file I/O operations for documentation workflow

© 2025 Model Documentation Integration
"""
import os
import json
from typing import Dict, Any, List
from tools.base_tool import BaseTool


class FileSystemTool(BaseTool):
    """Tool for file system operations"""
    
    def __init__(self, tool_name: str, description: str, config: Dict[str, Any] = None):
        super().__init__(tool_name, description, config)
        self.allowed_extensions = config.get('allowed_extensions', ['.py', '.js', '.java', '.ts', '.md', '.json'])
        self.max_file_size = config.get('max_file_size', 10 * 1024 * 1024)  # 10MB default
        
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute file system operations
        
        Args:
            action: Operation to perform (list_directory, read_file, write_file, write_json)
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with success status and result/error
        """
        try:
            if action == "list_directory":
                return self._list_directory(**kwargs)
            elif action == "read_file":
                return self._read_file(**kwargs)
            elif action == "write_file":
                return self._write_file(**kwargs)
            elif action == "write_json":
                return self._write_json(**kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'FileSystem error: {str(e)}'
            }
    
    def _list_directory(self, path: str, extensions: List[str] = None, recursive: bool = True) -> Dict[str, Any]:
        """
        List files in a directory
        
        Args:
            path: Directory path to scan
            extensions: List of file extensions to filter (e.g., ['.py', '.js'])
            recursive: Whether to scan subdirectories
            
        Returns:
            Dictionary with file list
        """
        if not os.path.exists(path):
            return {
                'success': False,
                'error': f'Path does not exist: {path}'
            }
        
        if not os.path.isdir(path):
            return {
                'success': False,
                'error': f'Path is not a directory: {path}'
            }
        
        # Use provided extensions or default to allowed extensions
        filter_extensions = extensions if extensions else self.allowed_extensions
        
        files = []
        
        if recursive:
            for root, dirs, filenames in os.walk(path):
                # Skip hidden directories and common non-code directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.git']]
                
                for filename in filenames:
                    if filename.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, filename)
                    file_ext = os.path.splitext(filename)[1]
                    
                    if not filter_extensions or file_ext in filter_extensions:
                        rel_path = os.path.relpath(file_path, path)
                        files.append({
                            'path': file_path,
                            'relative_path': rel_path,
                            'name': filename,
                            'size': os.path.getsize(file_path)
                        })
        else:
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    file_ext = os.path.splitext(filename)[1]
                    if not filter_extensions or file_ext in filter_extensions:
                        files.append({
                            'path': file_path,
                            'relative_path': filename,
                            'name': filename,
                            'size': os.path.getsize(file_path)
                        })
        
        return {
            'success': True,
            'files': files,
            'count': len(files),
            'scanned_path': path
        }
    
    def _read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read file contents
        
        Args:
            file_path: Path to file to read
            
        Returns:
            Dictionary with file contents
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'File does not exist: {file_path}'
            }
        
        if not os.path.isfile(file_path):
            return {
                'success': False,
                'error': f'Path is not a file: {file_path}'
            }
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            return {
                'success': False,
                'error': f'File too large ({file_size} bytes, max {self.max_file_size})'
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'success': True,
                'content': content,
                'file_path': file_path,
                'size': file_size
            }
        except UnicodeDecodeError:
            return {
                'success': False,
                'error': f'File is not a text file or has invalid encoding: {file_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading file: {str(e)}'
            }
    
    def _write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file
        
        Args:
            file_path: Path to file to write
            content: Content to write
            
        Returns:
            Dictionary with success status
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'file_path': file_path,
                'bytes_written': len(content.encode('utf-8'))
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error writing file: {str(e)}'
            }
    
    def _write_json(self, file_path: str, data: Any) -> Dict[str, Any]:
        """
        Write data to a JSON file
        
        Args:
            file_path: Path to JSON file to write
            data: Data to serialize as JSON
            
        Returns:
            Dictionary with success status
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'file_path': file_path,
                'bytes_written': os.path.getsize(file_path)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error writing JSON file: {str(e)}'
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'actions': [
                {
                    'name': 'list_directory',
                    'description': 'List files in a directory',
                    'parameters': {
                        'path': 'Directory path to scan',
                        'extensions': 'Optional list of file extensions to filter',
                        'recursive': 'Whether to scan subdirectories (default: true)'
                    }
                },
                {
                    'name': 'read_file',
                    'description': 'Read file contents',
                    'parameters': {
                        'file_path': 'Path to file to read'
                    }
                },
                {
                    'name': 'write_file',
                    'description': 'Write content to a file',
                    'parameters': {
                        'file_path': 'Path to file to write',
                        'content': 'Content to write'
                    }
                },
                {
                    'name': 'write_json',
                    'description': 'Write data to a JSON file',
                    'parameters': {
                        'file_path': 'Path to JSON file to write',
                        'data': 'Data to serialize as JSON'
                    }
                }
            ]
        }

