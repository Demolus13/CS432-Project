"""
B+ Tree implementation for the lightweight DBMS.
"""
import pickle
from typing import Any, List, Optional, Tuple, Dict, Union


class BPlusTreeNode:
    """Base class for B+ Tree nodes."""

    def __init__(self, order: int, is_leaf: bool = False):
        """
        Initialize a B+ Tree node.

        Args:
            order: The maximum number of children a node can have
            is_leaf: Whether this node is a leaf node
        """
        self.order = order
        self.is_leaf = is_leaf
        self.keys = []
        self.parent = None

        # For internal nodes, children are nodes
        # For leaf nodes, children are values (records)
        self.children = []

        # For leaf nodes, next_leaf points to the next leaf node
        self.next_leaf = None


class BPlusTreeLeafNode(BPlusTreeNode):
    """Leaf node of a B+ Tree that stores keys and values."""

    def __init__(self, order: int):
        """Initialize a leaf node."""
        super().__init__(order, is_leaf=True)
        self.values = []  # Store values (records) corresponding to keys

    def insert(self, key: Any, value: Any) -> Optional['BPlusTreeLeafNode']:
        """
        Insert a key-value pair into the leaf node.

        Args:
            key: The key to insert
            value: The value associated with the key

        Returns:
            A new leaf node if this node was split, None otherwise
        """
        # Find the position to insert the key
        i = 0
        while i < len(self.keys) and key > self.keys[i]:
            i += 1

        # Check if the key already exists
        if i < len(self.keys) and self.keys[i] == key:
            # Update the value if the key already exists
            self.values[i] = value
            return None

        # Insert the key and value at the found position
        self.keys.insert(i, key)
        self.values.insert(i, value)

        # If the node is full, split it
        if len(self.keys) > self.order - 1:
            return self._split()

        return None

    def _split(self) -> 'BPlusTreeLeafNode':
        """
        Split the leaf node when it's full.

        Returns:
            The new leaf node created after splitting
        """
        # Create a new leaf node
        new_node = BPlusTreeLeafNode(self.order)

        # Find the middle index
        mid = len(self.keys) // 2

        # Move half of the keys and values to the new node
        new_node.keys = self.keys[mid:]
        new_node.values = self.values[mid:]

        # Update this node's keys and values
        self.keys = self.keys[:mid]
        self.values = self.values[:mid]

        # Update the leaf node chain
        new_node.next_leaf = self.next_leaf
        self.next_leaf = new_node

        # Set the parent of the new node
        new_node.parent = self.parent

        return new_node

    def find(self, key: Any) -> Optional[Any]:
        """
        Find a value by key in the leaf node.

        Args:
            key: The key to search for

        Returns:
            The value associated with the key, or None if not found
        """
        for i, k in enumerate(self.keys):
            if k == key:
                return self.values[i]
        return None

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
        for i, key in enumerate(self.keys):
            if start_key <= key <= end_key:
                result.append((key, self.values[i]))
        return result

    def delete(self, key: Any) -> Tuple[bool, bool]:
        """
        Delete a key-value pair from the leaf node.

        Args:
            key: The key to delete

        Returns:
            A tuple of (success, underflow) where success indicates if the key was found and deleted,
            and underflow indicates if the node is now underfilled
        """
        for i, k in enumerate(self.keys):
            if k == key:
                self.keys.pop(i)
                self.values.pop(i)
                # Check if the node is underfilled (less than half full)
                underflow = len(self.keys) < (self.order // 2)
                return True, underflow
        return False, False

    def update(self, key: Any, value: Any) -> bool:
        """
        Update the value associated with a key.

        Args:
            key: The key to update
            value: The new value

        Returns:
            True if the key was found and updated, False otherwise
        """
        for i, k in enumerate(self.keys):
            if k == key:
                self.values[i] = value
                return True
        return False

    def borrow_from_sibling(self, sibling: 'BPlusTreeLeafNode', is_left: bool) -> Any:
        """
        Borrow a key-value pair from a sibling node.

        Args:
            sibling: The sibling node to borrow from
            is_left: True if the sibling is the left sibling, False if it's the right sibling

        Returns:
            The key that should be updated in the parent
        """
        if is_left:
            # Borrow from the left sibling
            key = sibling.keys.pop(-1)
            value = sibling.values.pop(-1)
            self.keys.insert(0, key)
            self.values.insert(0, value)
            return self.keys[0]  # Return the new first key of this node
        else:
            # Borrow from the right sibling
            key = sibling.keys.pop(0)
            value = sibling.values.pop(0)
            self.keys.append(key)
            self.values.append(value)
            return sibling.keys[0] if sibling.keys else key  # Return the new first key of the right sibling

    def merge_with_sibling(self, sibling: 'BPlusTreeLeafNode', is_left: bool) -> None:
        """
        Merge with a sibling node.

        Args:
            sibling: The sibling node to merge with
            is_left: True if the sibling is the left sibling, False if it's the right sibling
        """
        if is_left:
            # Merge with the left sibling
            sibling.keys.extend(self.keys)
            sibling.values.extend(self.values)
            sibling.next_leaf = self.next_leaf
        else:
            # Merge with the right sibling
            self.keys.extend(sibling.keys)
            self.values.extend(sibling.values)
            self.next_leaf = sibling.next_leaf


class BPlusTreeInternalNode(BPlusTreeNode):
    """Internal node of a B+ Tree that stores keys and child nodes."""

    def __init__(self, order: int):
        """Initialize an internal node."""
        super().__init__(order, is_leaf=False)

    def insert(self, key: Any, child: BPlusTreeNode) -> Optional[Tuple['BPlusTreeInternalNode', Any]]:
        """
        Insert a key and child node into the internal node.

        Args:
            key: The key to insert
            child: The child node to insert

        Returns:
            A tuple of (new_node, mid_key) if this node was split, None otherwise
        """
        # Find the position to insert the key
        i = 0
        while i < len(self.keys) and key > self.keys[i]:
            i += 1

        # Insert the key and child at the found position
        self.keys.insert(i, key)
        self.children.insert(i + 1, child)

        # Set the parent of the child node
        child.parent = self

        # If the node is full, split it
        if len(self.keys) > self.order - 1:
            return self._split()

        return None

    def _split(self) -> Tuple['BPlusTreeInternalNode', Any]:
        """
        Split the internal node when it's full.

        Returns:
            A tuple of (new_node, mid_key) where new_node is the new internal node
            created after splitting and mid_key is the key that will be pushed up to the parent
        """
        # Create a new internal node
        new_node = BPlusTreeInternalNode(self.order)

        # Find the middle index
        mid = len(self.keys) // 2

        # Get the middle key that will be pushed up to the parent
        mid_key = self.keys[mid]

        # Move half of the keys and children to the new node
        new_node.keys = self.keys[mid + 1:]
        new_node.children = self.children[mid + 1:]

        # Update this node's keys and children
        self.keys = self.keys[:mid]
        self.children = self.children[:mid + 1]

        # Update the parent of the moved children
        for child in new_node.children:
            child.parent = new_node

        # Set the parent of the new node
        new_node.parent = self.parent

        return new_node, mid_key

    def find_child(self, key: Any) -> BPlusTreeNode:
        """
        Find the child node that should contain the key.

        Args:
            key: The key to search for

        Returns:
            The child node that should contain the key
        """
        # If the key is less than the first key, return the first child
        if not self.keys or key < self.keys[0]:
            return self.children[0]

        # Find the appropriate child based on the key
        for i, k in enumerate(self.keys):
            if i + 1 < len(self.keys) and self.keys[i] <= key < self.keys[i + 1]:
                return self.children[i + 1]

        # If the key is greater than or equal to the last key, return the last child
        return self.children[-1]

    def find_child_index(self, child: BPlusTreeNode) -> int:
        """
        Find the index of a child node.

        Args:
            child: The child node to find

        Returns:
            The index of the child node
        """
        for i, c in enumerate(self.children):
            if c is child:
                return i
        return -1

    def delete_key(self, key_index: int) -> Tuple[bool, bool]:
        """
        Delete a key and its right child from the internal node.

        Args:
            key_index: The index of the key to delete

        Returns:
            A tuple of (success, underflow) where success indicates if the key was deleted,
            and underflow indicates if the node is now underfilled
        """
        if key_index < 0 or key_index >= len(self.keys):
            return False, False

        # Delete the key and its right child
        self.keys.pop(key_index)
        self.children.pop(key_index + 1)

        # Check if the node is underfilled (less than half full)
        underflow = len(self.keys) < (self.order // 2)
        return True, underflow

    def borrow_from_sibling(self, sibling: 'BPlusTreeInternalNode', is_left: bool, parent_key_index: int) -> None:
        """
        Borrow a key-child pair from a sibling node.

        Args:
            sibling: The sibling node to borrow from
            is_left: True if the sibling is the left sibling, False if it's the right sibling
            parent_key_index: The index of the parent key between this node and the sibling
        """
        parent = self.parent

        if is_left:
            # Borrow from the left sibling
            # Move the parent key down to this node
            self.keys.insert(0, parent.keys[parent_key_index])
            # Move the rightmost child of the sibling to this node
            child = sibling.children.pop(-1)
            self.children.insert(0, child)
            child.parent = self
            # Move the rightmost key of the sibling up to the parent
            parent.keys[parent_key_index] = sibling.keys.pop(-1)
        else:
            # Borrow from the right sibling
            # Move the parent key down to this node
            self.keys.append(parent.keys[parent_key_index])
            # Move the leftmost child of the sibling to this node
            child = sibling.children.pop(0)
            self.children.append(child)
            child.parent = self
            # Move the leftmost key of the sibling up to the parent
            parent.keys[parent_key_index] = sibling.keys.pop(0)

    def merge_with_sibling(self, sibling: 'BPlusTreeInternalNode', is_left: bool, parent_key_index: int) -> None:
        """
        Merge with a sibling node.

        Args:
            sibling: The sibling node to merge with
            is_left: True if the sibling is the left sibling, False if it's the right sibling
            parent_key_index: The index of the parent key between this node and the sibling
        """
        parent = self.parent
        parent_key = parent.keys[parent_key_index]

        if is_left:
            # Merge with the left sibling
            # Move the parent key down to the sibling
            sibling.keys.append(parent_key)
            # Move all keys and children from this node to the sibling
            sibling.keys.extend(self.keys)
            sibling.children.extend(self.children)
            # Update the parent of the moved children
            for child in self.children:
                child.parent = sibling
        else:
            # Merge with the right sibling
            # Move the parent key down to this node
            self.keys.append(parent_key)
            # Move all keys and children from the sibling to this node
            self.keys.extend(sibling.keys)
            self.children.extend(sibling.children)
            # Update the parent of the moved children
            for child in sibling.children:
                child.parent = self


class BPlusTree:
    """B+ Tree implementation for indexing."""

    def __init__(self, order: int = 4):
        """
        Initialize a B+ Tree.

        Args:
            order: The maximum number of children a node can have
        """
        self.order = order
        self.root = BPlusTreeLeafNode(order)
        self.height = 1

    def insert(self, key: Any, value: Any) -> bool:
        """
        Insert a key-value pair into the B+ Tree.

        Args:
            key: The key to insert
            value: The value associated with the key

        Returns:
            True if the key was inserted, False if it already exists and was updated
        """
        # Find the leaf node where the key should be inserted
        leaf_node = self._find_leaf_node(key)

        # Check if the key already exists
        existing_value = leaf_node.find(key)
        if existing_value is not None:
            # Update the value if the key already exists
            leaf_node.update(key, value)
            return False

        # Insert the key-value pair into the leaf node
        new_node = leaf_node.insert(key, value)

        # If the leaf node was split, update the tree
        if new_node:
            self._insert_in_parent(leaf_node, new_node.keys[0], new_node)

        return True

    def _insert_in_parent(self, left_node: BPlusTreeNode, key: Any, right_node: BPlusTreeNode) -> None:
        """
        Insert a key and right node into the parent of the left node.

        Args:
            left_node: The left node
            key: The key to insert
            right_node: The right node
        """
        # If the left node is the root, create a new root
        if left_node.parent is None:
            new_root = BPlusTreeInternalNode(self.order)
            new_root.keys = [key]
            new_root.children = [left_node, right_node]
            left_node.parent = new_root
            right_node.parent = new_root
            self.root = new_root
            self.height += 1
            return

        # Insert the key and right node into the parent
        parent = left_node.parent
        result = parent.insert(key, right_node)

        # If the parent was split, recursively update the tree
        if result:
            new_parent, mid_key = result
            self._insert_in_parent(parent, mid_key, new_parent)

    def _find_leaf_node(self, key: Any) -> BPlusTreeLeafNode:
        """
        Find the leaf node where a key should be inserted.

        Args:
            key: The key to search for

        Returns:
            The leaf node where the key should be inserted
        """
        node = self.root

        # Traverse the tree to find the leaf node
        while not node.is_leaf:
            node = node.find_child(key)

        return node

    def find(self, key: Any) -> Optional[Any]:
        """
        Find a value by key in the B+ Tree.

        Args:
            key: The key to search for

        Returns:
            The value associated with the key, or None if not found
        """
        leaf_node = self._find_leaf_node(key)
        return leaf_node.find(key)

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

        # Find the leaf node where the start key should be
        leaf_node = self._find_leaf_node(start_key)

        # Collect all key-value pairs within the range
        while leaf_node:
            result.extend(leaf_node.range_query(start_key, end_key))

            # If we've reached the end of the range, stop
            if leaf_node.keys and leaf_node.keys[-1] >= end_key:
                break

            # Move to the next leaf node
            leaf_node = leaf_node.next_leaf

        return result

    def delete(self, key: Any) -> bool:
        """
        Delete a key-value pair from the B+ Tree.

        Args:
            key: The key to delete

        Returns:
            True if the key was found and deleted, False otherwise
        """
        # Find the leaf node where the key should be
        leaf_node = self._find_leaf_node(key)

        # Delete the key-value pair from the leaf node
        success, underflow = leaf_node.delete(key)

        if not success:
            return False

        # If the leaf node is underfilled, handle it
        if underflow and len(leaf_node.keys) > 0:  # Don't handle empty root
            self._handle_underflow(leaf_node)

        # If the root is an internal node with only one child, make the child the new root
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]
            self.root.parent = None
            self.height -= 1

        return True

    def _handle_underflow(self, node: BPlusTreeNode) -> None:
        """
        Handle underflow in a node by borrowing from siblings or merging with a sibling.

        Args:
            node: The node that is underfilled
        """
        # If the node is the root, we don't need to handle underflow
        if node.parent is None:
            return

        parent = node.parent
        node_index = parent.find_child_index(node)

        # Try to borrow from the left sibling
        if node_index > 0:
            left_sibling = parent.children[node_index - 1]
            # Check if the left sibling has enough keys to spare
            if len(left_sibling.keys) > self.order // 2:
                if node.is_leaf:
                    # Borrow from the left sibling (leaf node)
                    new_key = node.borrow_from_sibling(left_sibling, True)
                    # Update the parent key
                    parent.keys[node_index - 1] = new_key
                else:
                    # Borrow from the left sibling (internal node)
                    node.borrow_from_sibling(left_sibling, True, node_index - 1)
                return

        # Try to borrow from the right sibling
        if node_index < len(parent.children) - 1:
            right_sibling = parent.children[node_index + 1]
            # Check if the right sibling has enough keys to spare
            if len(right_sibling.keys) > self.order // 2:
                if node.is_leaf:
                    # Borrow from the right sibling (leaf node)
                    new_key = node.borrow_from_sibling(right_sibling, False)
                    # Update the parent key
                    parent.keys[node_index] = new_key
                else:
                    # Borrow from the right sibling (internal node)
                    node.borrow_from_sibling(right_sibling, False, node_index)
                return

        # If we can't borrow, merge with a sibling
        if node_index > 0:
            # Merge with the left sibling
            left_sibling = parent.children[node_index - 1]
            if node.is_leaf:
                node.merge_with_sibling(left_sibling, True)
            else:
                node.merge_with_sibling(left_sibling, True, node_index - 1)

            # Delete the parent key
            success, underflow = parent.delete_key(node_index - 1)

            # If the parent is now underfilled, handle it recursively
            if underflow and len(parent.keys) > 0:  # Don't handle empty root
                self._handle_underflow(parent)
        else:
            # Merge with the right sibling
            right_sibling = parent.children[node_index + 1]
            if node.is_leaf:
                node.merge_with_sibling(right_sibling, False)
            else:
                node.merge_with_sibling(right_sibling, False, node_index)

            # Delete the parent key
            success, underflow = parent.delete_key(node_index)

            # If the parent is now underfilled, handle it recursively
            if underflow and len(parent.keys) > 0:  # Don't handle empty root
                self._handle_underflow(parent)

    def update(self, key: Any, value: Any) -> bool:
        """
        Update the value associated with a key.

        Args:
            key: The key to update
            value: The new value

        Returns:
            True if the key was found and updated, False otherwise
        """
        # Find the leaf node where the key should be
        leaf_node = self._find_leaf_node(key)

        # Update the value associated with the key
        return leaf_node.update(key, value)

    def save_to_file(self, filename: str) -> None:
        """
        Save the B+ Tree to a file.

        Args:
            filename: The name of the file to save to
        """
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load_from_file(filename: str) -> 'BPlusTree':
        """
        Load a B+ Tree from a file.

        Args:
            filename: The name of the file to load from

        Returns:
            The loaded B+ Tree
        """
        with open(filename, 'rb') as f:
            return pickle.load(f)
