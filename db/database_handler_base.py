"""
Database Handler Base
Base class for all database handlers with common utilities

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

from typing import Optional


class DatabaseHandlerBase:
    """Base class for all database handlers"""
    
    def __init__(self, database):
        """
        Initialize the handler with a database instance
        
        Args:
            database: Database instance from database.py
        """
        self.db = database
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            result = self.db.fetchone(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return result is not None
        except:
            return False
