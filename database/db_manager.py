"""
Database manager for the lightweight DBMS.
"""
import os
import json
import shutil
from typing import Dict, Any, List, Optional

from .table import Table


class Database:
    """Class representing a database."""
    
    def __init__(self, name: str, data_dir: str = 'data'):
        """
        Initialize a database.
        
        Args:
            name: The name of the database
            data_dir: The directory to store the database files
        """
        self.name = name
        self.data_dir = os.path.join(data_dir, name)
        self.tables = {}
        
        # Create the data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing tables
        self._load_tables()
    
    def create_table(self, name: str, schema: Dict[str, str], primary_key: str) -> Table:
        """
        Create a new table.
        
        Args:
            name: The name of the table
            schema: A dictionary mapping column names to their types
            primary_key: The name of the primary key column
            
        Returns:
            The created table
        """
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists")
        
        if primary_key not in schema:
            raise ValueError(f"Primary key '{primary_key}' is not in the schema")
        
        table = Table(name, schema, primary_key)
        self.tables[name] = table
        
        # Save the table schema
        self._save_table_schema(name, schema, primary_key)
        
        return table
    
    def drop_table(self, name: str) -> bool:
        """
        Drop a table.
        
        Args:
            name: The name of the table to drop
            
        Returns:
            True if the table was dropped, False otherwise
        """
        if name not in self.tables:
            return False
        
        # Remove the table from memory
        del self.tables[name]
        
        # Remove the table files
        table_dir = os.path.join(self.data_dir, name)
        if os.path.exists(table_dir):
            shutil.rmtree(table_dir)
        
        return True
    
    def get_table(self, name: str) -> Optional[Table]:
        """
        Get a table by name.
        
        Args:
            name: The name of the table
            
        Returns:
            The table, or None if not found
        """
        return self.tables.get(name)
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            A list of table names
        """
        return list(self.tables.keys())
    
    def save(self) -> None:
        """Save the database to disk."""
        for name, table in self.tables.items():
            table.save(self.data_dir)
    
    def _save_table_schema(self, name: str, schema: Dict[str, str], primary_key: str) -> None:
        """
        Save a table schema to disk.
        
        Args:
            name: The name of the table
            schema: The schema of the table
            primary_key: The primary key of the table
        """
        table_dir = os.path.join(self.data_dir, name)
        os.makedirs(table_dir, exist_ok=True)
        
        # Save the schema
        schema_file = os.path.join(table_dir, 'schema.json')
        with open(schema_file, 'w') as f:
            json.dump({'schema': schema, 'primary_key': primary_key}, f)
    
    def _load_tables(self) -> None:
        """Load tables from disk."""
        if not os.path.exists(self.data_dir):
            return
        
        # Get all table directories
        for table_name in os.listdir(self.data_dir):
            table_dir = os.path.join(self.data_dir, table_name)
            if os.path.isdir(table_dir):
                self._load_table(table_name, table_dir)
    
    def _load_table(self, name: str, table_dir: str) -> None:
        """
        Load a table from disk.
        
        Args:
            name: The name of the table
            table_dir: The directory containing the table files
        """
        # Load the schema
        schema_file = os.path.join(table_dir, 'schema.json')
        if not os.path.exists(schema_file):
            return
        
        with open(schema_file, 'r') as f:
            schema_data = json.load(f)
        
        schema = schema_data['schema']
        primary_key = schema_data['primary_key']
        
        # Load the table
        table = Table.load(name, schema, primary_key, self.data_dir)
        
        # Add the table to the database
        self.tables[name] = table
