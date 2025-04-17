"""
Table implementation for the lightweight DBMS.
"""
from typing import Dict, Any, List, Optional, Tuple
import pickle
import os

from .bplustree import BPlusTree


class Table:
    """Class representing a table in the database."""
    
    def __init__(self, name: str, schema: Dict[str, str], primary_key: str):
        """
        Initialize a table.
        
        Args:
            name: The name of the table
            schema: A dictionary mapping column names to their types
            primary_key: The name of the primary key column
        """
        self.name = name
        self.schema = schema
        self.primary_key = primary_key
        self.index = BPlusTree(order=4)  # B+ Tree index on the primary key
        self.records = {}  # Dictionary mapping record IDs to records
    
    def insert(self, record: Dict[str, Any]) -> bool:
        """
        Insert a record into the table.
        
        Args:
            record: The record to insert
            
        Returns:
            True if the record was inserted, False otherwise
        """
        # Check if the record has all required columns
        for column in self.schema:
            if column not in record:
                raise ValueError(f"Record is missing column '{column}'")
        
        # Check if the primary key already exists
        primary_key_value = record[self.primary_key]
        if self.index.find(primary_key_value) is not None:
            return False
        
        # Insert the record
        self.index.insert(primary_key_value, record)
        self.records[primary_key_value] = record
        
        return True
    
    def update(self, primary_key_value: Any, record: Dict[str, Any]) -> bool:
        """
        Update a record in the table.
        
        Args:
            primary_key_value: The primary key value of the record to update
            record: The new record
            
        Returns:
            True if the record was updated, False otherwise
        """
        # Check if the record exists
        if self.index.find(primary_key_value) is None:
            return False
        
        # Check if the record has all required columns
        for column in self.schema:
            if column not in record:
                raise ValueError(f"Record is missing column '{column}'")
        
        # Update the record
        self.index.update(primary_key_value, record)
        self.records[primary_key_value] = record
        
        return True
    
    def delete(self, primary_key_value: Any) -> bool:
        """
        Delete a record from the table.
        
        Args:
            primary_key_value: The primary key value of the record to delete
            
        Returns:
            True if the record was deleted, False otherwise
        """
        # Check if the record exists
        if self.index.find(primary_key_value) is None:
            return False
        
        # Delete the record
        self.index.delete(primary_key_value)
        del self.records[primary_key_value]
        
        return True
    
    def select(self, primary_key_value: Any) -> Optional[Dict[str, Any]]:
        """
        Select a record from the table.
        
        Args:
            primary_key_value: The primary key value of the record to select
            
        Returns:
            The record, or None if not found
        """
        return self.index.find(primary_key_value)
    
    def select_range(self, start_key: Any, end_key: Any) -> List[Dict[str, Any]]:
        """
        Select records within a range of primary key values.
        
        Args:
            start_key: The lower bound of the range (inclusive)
            end_key: The upper bound of the range (inclusive)
            
        Returns:
            A list of records within the range
        """
        results = self.index.range_query(start_key, end_key)
        return [record for _, record in results]
    
    def select_where(self, condition: callable) -> List[Dict[str, Any]]:
        """
        Select records that satisfy a condition.
        
        Args:
            condition: A function that takes a record and returns a boolean
            
        Returns:
            A list of records that satisfy the condition
        """
        return [record for record in self.records.values() if condition(record)]
    
    def aggregate(self, column: str, operation: str) -> Any:
        """
        Perform an aggregation operation on a column.
        
        Args:
            column: The column to aggregate
            operation: The operation to perform (sum, avg, min, max, count)
            
        Returns:
            The result of the aggregation
        """
        if column not in self.schema:
            raise ValueError(f"Column '{column}' does not exist")
        
        values = [record[column] for record in self.records.values()]
        
        if operation == 'sum':
            return sum(values)
        elif operation == 'avg':
            return sum(values) / len(values) if values else 0
        elif operation == 'min':
            return min(values) if values else None
        elif operation == 'max':
            return max(values) if values else None
        elif operation == 'count':
            return len(values)
        else:
            raise ValueError(f"Unknown operation '{operation}'")
    
    def save(self, data_dir: str) -> None:
        """
        Save the table to disk.
        
        Args:
            data_dir: The directory to save the table to
        """
        table_dir = os.path.join(data_dir, self.name)
        os.makedirs(table_dir, exist_ok=True)
        
        # Save the records
        records_file = os.path.join(table_dir, 'records.pkl')
        with open(records_file, 'wb') as f:
            pickle.dump(self.records, f)
        
        # Save the index
        index_file = os.path.join(table_dir, 'index.pkl')
        self.index.save_to_file(index_file)
    
    @staticmethod
    def load(name: str, schema: Dict[str, str], primary_key: str, data_dir: str) -> 'Table':
        """
        Load a table from disk.
        
        Args:
            name: The name of the table
            schema: The schema of the table
            primary_key: The primary key of the table
            data_dir: The directory to load the table from
            
        Returns:
            The loaded table
        """
        table = Table(name, schema, primary_key)
        
        table_dir = os.path.join(data_dir, name)
        
        # Load the records
        records_file = os.path.join(table_dir, 'records.pkl')
        if os.path.exists(records_file):
            with open(records_file, 'rb') as f:
                table.records = pickle.load(f)
        
        # Load the index
        index_file = os.path.join(table_dir, 'index.pkl')
        if os.path.exists(index_file):
            table.index = BPlusTree.load_from_file(index_file)
        
        return table
