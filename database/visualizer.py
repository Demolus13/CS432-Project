"""
Visualization tools for B+ Tree using system-installed Graphviz.
"""
import os
import subprocess
import tempfile
from typing import Dict, Any, Optional

from .bplustree import BPlusTree, BPlusTreeNode, BPlusTreeLeafNode, BPlusTreeInternalNode


class BPlusTreeVisualizer:
    """Class for visualizing B+ Trees using system-installed Graphviz."""

    def __init__(self, tree: BPlusTree):
        """
        Initialize the visualizer.

        Args:
            tree: The B+ Tree to visualize
        """
        self.tree = tree
        self.node_map = {}  # Maps nodes to their IDs
        self.node_count = 0
        self.dot_content = []  # Store DOT language content

    def visualize(self, filename: str = 'b_plus_tree', view: bool = True) -> None:
        """
        Visualize the B+ Tree using system-installed Graphviz.

        Args:
            filename: The name of the output file
            view: Whether to open the visualization
        """
        # Reset state
        self.node_map = {}
        self.node_count = 0
        self.dot_content = []

        # Start DOT file content
        self.dot_content.append('digraph "B+ Tree" {')
        self.dot_content.append('  rankdir=TB;')
        self.dot_content.append('  size="10,10";')
        self.dot_content.append('  dpi=300;')
        self.dot_content.append('  bgcolor="#f8f9fa";')
        # No title here - we'll display it in the HTML instead
        self.dot_content.append('  fontsize=20;')
        self.dot_content.append('  fontname="Arial";')
        # Increase spacing between layers
        self.dot_content.append('  ranksep=1.5;')
        # Add some spacing between nodes on the same rank
        self.dot_content.append('  nodesep=0.5;')

        # Create subgraphs for each level
        self._create_level_subgraphs()

        # Add edges between nodes
        self._add_edges()

        # Add leaf node linkage
        self._add_leaf_linkage()

        # Close the DOT file content
        self.dot_content.append('}')

        # Create static directory if it doesn't exist
        os.makedirs('static', exist_ok=True)

        # Ensure the filename is in the static directory
        if not filename.startswith('static/'):
            filename = os.path.join('static', filename)

        # Write DOT content to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.dot', delete=False, mode='w') as dot_file:
            dot_file.write('\n'.join(self.dot_content))
            dot_path = dot_file.name

        try:
            # Run dot command to generate the image
            output_path = f"{filename}.png"
            subprocess.run(['dot', '-Tpng', dot_path, '-o', output_path], check=True)

            # Open the image if requested
            if view:
                if os.name == 'nt':  # Windows
                    os.startfile(output_path)
                elif os.name == 'posix':  # Linux/Mac
                    subprocess.run(['xdg-open', output_path], check=True)
        finally:
            # Clean up the temporary DOT file
            os.unlink(dot_path)

    def _create_level_subgraphs(self) -> None:
        """
        Create subgraphs for each level of the tree to ensure proper layout.
        """
        # Create a dictionary to store nodes at each level
        level_nodes = {}
        self._collect_nodes_by_level(self.tree.root, 0, level_nodes)

        # Create a subgraph for each level
        for level, nodes in level_nodes.items():
            self.dot_content.append(f'  subgraph cluster_level_{level} {{')
            self.dot_content.append('    rank=same;')

            for node in nodes:
                node_id = f'node_{self.node_count}'
                self.node_map[node] = node_id
                self.node_count += 1

                # Create the node label using HTML-like labels
                if node.is_leaf:
                    if hasattr(node, 'values'):
                        # Create a simplified HTML-like label for leaf nodes with values
                        label_parts = [f'<TD PORT="f{i}">Key: {k}</TD>' for i, k in enumerate(node.keys)]
                        label = f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5"><TR>{"".join(label_parts)}</TR></TABLE>>'
                        self.dot_content.append(f'    {node_id} [label={label}, shape=none, style="filled,rounded", fillcolor="#4895ef", color="#3f37c9", penwidth=1.5, margin=0.2];')
                    else:
                        # Simple leaf node without values
                        label_parts = [f'<TD PORT="f{i}">{k}</TD>' for i, k in enumerate(node.keys)]
                        label = f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5"><TR>{"".join(label_parts)}</TR></TABLE>>'
                        self.dot_content.append(f'    {node_id} [label={label}, shape=none, style="filled,rounded", fillcolor="#4895ef", color="#3f37c9", penwidth=1.5, margin=0.2];')
                else:
                    # Create a more detailed HTML-like label for internal nodes
                    label_parts = [f'<TD PORT="f{i}">{k}</TD>' for i, k in enumerate(node.keys)]
                    label = f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5"><TR>{"".join(label_parts)}</TR></TABLE>>'
                    self.dot_content.append(f'    {node_id} [label={label}, shape=none, style="filled,rounded", fillcolor="#4ade80", color="#3f37c9", penwidth=1.5, margin=0.2];')

            self.dot_content.append('  }')

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
                    edge_label = f'<= {node.keys[i]}'
                    # Connect from the port of the key to the child
                    self.dot_content.append(f'  {node_id}:f{i} -> {child_id} [label="{edge_label}", fontsize=14, penwidth=1.8, color="#4361ee", fontcolor="#212529", arrowsize=0.8];')
                else:
                    edge_label = f'> {node.keys[-1]}'
                    # Connect from the node to the child (no specific port)
                    self.dot_content.append(f'  {node_id} -> {child_id} [label="{edge_label}", fontsize=14, penwidth=1.8, color="#4361ee", fontcolor="#212529", arrowsize=0.8];')

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
            self.dot_content.append(
                f'  {self.node_map[leaf_node]} -> {self.node_map[leaf_node.next_leaf]} '
                f'[style=dashed, color="#ef476f", constraint=false, label="next", fontcolor="#ef476f", fontsize=14, penwidth=2.2, arrowsize=0.8];'
            )
            leaf_node = leaf_node.next_leaf
