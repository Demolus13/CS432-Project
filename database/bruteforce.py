"""
Brute Force DB implementation for comparison with B+ Tree.
"""
import pickle
from typing import Any, List, Optional, Tuple, Dict


class BruteForceDB:
    """A simple brute force database implementation for comparison."""
    
    def __init__(self):
        """Initialize an empty brute force database."""
        self.data = {}  # Dictionary to store key-value pairs
    
    def insert(self, key: Any, value: Any) -> None:
        """
        Insert a key-value pair into the database.
        
        Args:
            key: The key to insert
            value: The value associated with the key
        """
        self.data[key] = value
    
    def find(self, key: Any) -> Optional[Any]:
        """
        Find a value by key in the database.
        
        Args:
            key: The key to search for
            
        Returns:
            The value associated with the key, or None if not found
        """
        return self.data.get(key)
    
    def range_query(self, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        """
        Find all key-value pairs within a range.
        
        Args:
            start_key: The lower bound of the range (inclusive)
            end_key: The upper bound of the range (inclusive)
            
        Returns:
            A list of (key, value) tuples within the range
        """
        result = []
        for key, value in self.data.items():
            if start_key <= key <= end_key:
                result.append((key, value))
        return result
    
    def delete(self, key: Any) -> bool:
        """
        Delete a key-value pair from the database.
        
        Args:
            key: The key to delete
            
        Returns:
            True if the key was found and deleted, False otherwise
        """
        if key in self.data:
            del self.data[key]
            return True
        return False
    
    def update(self, key: Any, value: Any) -> bool:
        """
        Update the value associated with a key.
        
        Args:
            key: The key to update
            value: The new value
            
        Returns:
            True if the key was found and updated, False otherwise
        """
        if key in self.data:
            self.data[key] = value
            return True
        return False
    
    def save_to_file(self, filename: str) -> None:
        """
        Save the database to a file.
        
        Args:
            filename: The name of the file to save to
        """
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load_from_file(filename: str) -> 'BruteForceDB':
        """
        Load a database from a file.
        
        Args:
            filename: The name of the file to load from
            
        Returns:
            The loaded database
        """
        with open(filename, 'rb') as f:
            return pickle.load(f)
