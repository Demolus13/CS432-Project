"""
Visualization tools for B+ Tree.
"""
from graphviz import Digraph
from typing import Dict, Any, Optional

from .bplustree import BPlusTree, BPlusTreeNode, BPlusTreeLeafNode, BPlusTreeInternalNode


class BPlusTreeVisualizer:
    """Class for visualizing B+ Trees with enhanced features."""

    def __init__(self, tree: BPlusTree):
        """
        Initialize the visualizer.

        Args:
            tree: The B+ Tree to visualize
        """
        self.tree = tree
        self.dot = None
        self.node_map = {}  # Maps nodes to their IDs
        self.node_count = 0

    def visualize(self, filename: str = 'b_plus_tree', view: bool = True) -> None:
        """
        Visualize the B+ Tree.

        Args:
            filename: The name of the output file
            view: Whether to open the visualization
        """
        self.dot = Digraph(comment='B+ Tree')
        self.dot.attr(rankdir='TB', size='8,8', dpi='300')
        self.node_map = {}
        self.node_count = 0

        # Add a title
        self.dot.attr(label=f'B+ Tree (Order {self.tree.order}, Height {self.tree.height})')
        self.dot.attr(fontsize='20')

        # Create subgraphs for each level to ensure proper layout
        self._create_level_subgraphs()

        # Add edges between nodes
        self._add_edges()

        # Add leaf node linkage
        self._add_leaf_linkage()

        # Save the visualization
        self.dot.render(filename, view=view, format='png')

    def _create_level_subgraphs(self) -> None:
        """
        Create subgraphs for each level of the tree to ensure proper layout.
        """
        # Create a dictionary to store nodes at each level
        level_nodes = {}
        self._collect_nodes_by_level(self.tree.root, 0, level_nodes)

        # Create a subgraph for each level
        for level, nodes in level_nodes.items():
            with self.dot.subgraph(name=f'cluster_level_{level}') as c:
                c.attr(rank='same')
                for node in nodes:
                    node_id = f'node_{self.node_count}'
                    self.node_map[node] = node_id
                    self.node_count += 1

                    # Create the node label
                    if node.is_leaf:
                        if hasattr(node, 'values'):
                            # Create a more detailed label for leaf nodes with values
                            label = '{ ' + ' | '.join([f'<f{i}> {k}\\n{v}' for i, (k, v) in enumerate(zip(node.keys, node.values))]) + ' }'
                            c.node(node_id, label, shape='record', style='filled', fillcolor='lightblue')
                        else:
                            label = '{ ' + ' | '.join([f'<f{i}> {k}' for i, k in enumerate(node.keys)]) + ' }'
                            c.node(node_id, label, shape='record', style='filled', fillcolor='lightblue')
                    else:
                        # Create a more detailed label for internal nodes
                        ports = [f'<f{i}> {k}' for i, k in enumerate(node.keys)]
                        label = '{ ' + ' | '.join(ports) + ' }'
                        c.node(node_id, label, shape='record', style='filled', fillcolor='lightgreen')

    def _collect_nodes_by_level(self, node: BPlusTreeNode, level: int, level_nodes: dict) -> None:
        """
        Collect nodes at each level of the tree.

        Args:
            node: The current node
            level: The current level
            level_nodes: Dictionary to store nodes at each level
        """
        if level not in level_nodes:
            level_nodes[level] = []

        level_nodes[level].append(node)

        if not node.is_leaf:
            for child in node.children:
                self._collect_nodes_by_level(child, level + 1, level_nodes)

    def _add_edges(self) -> None:
        """
        Add edges between nodes to show parent-child relationships.
        """
        # Add edges from internal nodes to their children
        self._add_node_edges(self.tree.root)

    def _add_node_edges(self, node: BPlusTreeNode) -> None:
        """
        Add edges from a node to its children.

        Args:
            node: The node to add edges from
        """
        if not node.is_leaf:
            node_id = self.node_map[node]
            
            for i, child in enumerate(node.children):
                child_id = self.node_map[child]
                
                # Create edge with appropriate label and style
                if i < len(node.keys):
                    edge_label = f'≤ {node.keys[i]}'
                    # Connect from the port of the key to the child
                    self.dot.edge(f'{node_id}:f{i}', child_id, 
                                 label=edge_label, 
                                 fontsize='10',
                                 penwidth='1.5')
                else:
                    edge_label = f'> {node.keys[-1]}'
                    # Connect from the node to the child (no specific port)
                    self.dot.edge(node_id, child_id, 
                                 label=edge_label, 
                                 fontsize='10',
                                 penwidth='1.5')
                
                # Recursively add edges for the child's children
                self._add_node_edges(child)

    def _add_leaf_linkage(self) -> None:
        """Add edges between leaf nodes to show the linked list."""
        # Find the leftmost leaf node
        leaf_node = self.tree.root
        while not leaf_node.is_leaf:
            leaf_node = leaf_node.children[0]
        
        # Add edges between leaf nodes following the next_leaf pointers
        while leaf_node.next_leaf is not None:
            self.dot.edge(self.node_map[leaf_node], 
                         self.node_map[leaf_node.next_leaf], 
                         style='dashed', 
                         color='red', 
                         constraint='false',
                         label='next',
                         fontcolor='red',
                         fontsize='10',
                         penwidth='2.0')
            leaf_node = leaf_node.next_leaf
