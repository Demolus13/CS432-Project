# Lightweight DBMS with B+ Tree Index

This project implements a lightweight database management system (DBMS) in Python that supports basic operations (insert, update, delete, select, aggregation, range queries) on tables stored with a B+ Tree index. It includes a web-based user interface for interacting with the database, performance analysis tools, and visualization components.

## Overview

The system is built around a B+ Tree implementation that provides efficient O(log n) search operations and O(log n + k) range queries. The B+ Tree structure ensures that data retrieval operations are fast even with large datasets, making it suitable for database indexing.

## Features

### Core Database Features

- **B+ Tree Indexing**: Efficient O(log n) search operations and O(log n + k) range queries
- **Database Operations**: Create, select, and delete databases
- **Table Operations**: Create, select, and delete tables with custom schemas
- **Record Operations**: Insert, update, delete, and select records
- **Range Queries**: Efficiently retrieve records within a specified key range
- **Data Persistence**: Save and load database state to/from disk

### Performance Analysis

- **Benchmarking**: Compare B+ Tree performance against a brute force approach
- **Metrics**: Measure execution time and memory usage for various operations
- **Visualization**: Generate performance graphs for different data sizes
- **Operations Tested**: Insertion, search, range query, deletion, and random operations

### Visualization

- **B+ Tree Structure**: Visualize the internal structure of B+ Trees
- **Node Representation**: Clearly display internal and leaf nodes with their keys and values
- **Tree Hierarchy**: Show parent-child relationships between nodes
- **Leaf Node Linkage**: Visualize the linked list structure of leaf nodes for efficient range queries

### User Interface

- **Web-Based**: Easy-to-use interface built with Flask
- **Database Management**: Create, select, and delete databases
- **Table Management**: Define table schemas with custom fields and types
- **Record Operations**: Form-based interface for CRUD operations
- **Dark Mode**: Catppuccin Mocha color scheme for better readability
- **Responsive Design**: Adapts to different screen sizes

## Technical Details

### B+ Tree Implementation

- **Node Structure**: Base node class with specialized leaf and internal node classes
- **Operations**:
  - **Insertion**: O(log n) time complexity
  - **Deletion**: O(log n) time complexity
  - **Search**: O(log n) time complexity
  - **Range Query**: O(log n + k) time complexity, where k is the number of elements in the range
- **Self-Balancing**: Maintains balanced height through node splitting and merging
- **Leaf Node Linkage**: Leaf nodes are linked for efficient range queries
- **Binary Search**: Used for optimizing search operations within nodes

### Database Management

- **Database**: Manages a collection of tables with persistence
- **Table**: Represents a table with a schema, primary key, and B+ Tree index
- **Schema**: Defines the structure of a table with column names and types
- **Persistence**: Uses pickle for serialization and deserialization

### Performance Analysis

- **Comparison**: B+ Tree vs. Brute Force approach
- **Metrics**: Execution time and memory usage
- **Data Sizes**: Configurable benchmark sizes (default: 100, 500, 1000, 5000, 10000)
- **Memory Measurement**: Complete traversal of the B+ Tree structure for accurate memory usage

### Visualization

- **Graphviz**: Uses system-installed Graphviz for high-quality visualizations
- **Node Styling**: Different colors for internal and leaf nodes
- **Edge Styling**: Clear representation of parent-child relationships
- **Leaf Linkage**: Dashed lines showing the linked list structure of leaf nodes

## Directory Structure

```
.
├── database/              # Core database implementation
│   ├── __init__.py
│   ├── bplustree.py       # B+ Tree implementation
│   ├── bruteforce.py      # Brute force approach for comparison
│   ├── db_manager.py      # Database manager
│   ├── performance_analyzer.py  # Performance analysis tools
│   ├── table.py           # Table implementation
│   └── visualizer.py      # Tree visualization
├── templates/             # HTML templates for the web UI
│   ├── index.html         # Main dashboard
│   ├── visualization.html # B+ Tree visualization page
│   └── performance.html   # Performance testing page
├── static/               # Static files (CSS, images, etc.)
├── data/                 # Database files
├── app.py                # Flask web application
├── report.ipynb          # Report and Visualizations
├── requirements.txt      # Project dependencies
└── README.md             # This file
```

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - Windows: `.\.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
5. For visualization, install Graphviz on your system:
   - Windows: Download from [Graphviz website](https://graphviz.org/download/)
   - Linux: `sudo apt-get install graphviz`
   - Mac: `brew install graphviz`

## Usage

### Running the Web Application

```
python app.py
```

This will start the Flask web server. Open your browser and navigate to `http://127.0.0.1:5000` to access the web interface.

### Web Interface Features

1. **Database Management**:
   - Create, select, and delete databases
   - Create, select, and delete tables with custom schemas
   - View table schemas and data

2. **Record Operations**:
   - Insert new records
   - Update existing records
   - Delete records
   - Select records by primary key
   - Perform range queries

3. **Visualization**:
   - Visualize the B+ Tree structure of a table
   - View tree properties (height, order, node count)
   - See the relationships between nodes

4. **Performance Testing**:
   - Run performance tests comparing B+ Tree and brute force approaches
   - View performance metrics for different operations
   - Analyze results with interactive charts

### Using the Database

```python
from database.db_manager import Database

# Create a database
db = Database('my_db')

# Create a table
users_schema = {
    'id': 'int',
    'name': 'str',
    'email': 'str',
    'age': 'int'
}
users_table = db.create_table('users', users_schema, 'id')

# Insert a record
users_table.insert({'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'age': 30})

# Save the database
db.save()

# Query a record
user = users_table.select(1)
print(user)
```

### Running the Performance Analysis

```python
from database.performance_analyzer import PerformanceAnalyzer

# Create a performance analyzer
analyzer = PerformanceAnalyzer(b_plus_tree_order=4)

# Define the data sizes to benchmark
sizes = [100, 500, 1000, 5000, 10000]

# Run the benchmarks
results = analyzer.run_benchmarks(sizes, num_samples=3)

# Plot the results
analyzer.plot_results(sizes, save_path='performance_results.png')
```

### Visualizing the B+ Tree

```python
from database.bplustree import BPlusTree
from database.visualizer import BPlusTreeVisualizer

# Create a B+ Tree
tree = BPlusTree(order=4)

# Insert some key-value pairs
for i in range(10):
    tree.insert(i, f"value_{i}")

# Visualize the tree
visualizer = BPlusTreeVisualizer(tree)
visualizer.visualize('b_plus_tree_example')
```

## Report

The `report.ipynb` notebook contains a detailed report on the implementation and performance analysis of the DBMS. It includes:

- Introduction to the problem and solution
- Implementation details of the B+ Tree operations
- Performance analysis comparing the B+ Tree with a brute force approach
- Visualization of the B+ Tree structure
- Conclusion and future improvements

To run the notebook:

```
jupyter notebook report.ipynb
```

## Website UI

The web interface provides a user-friendly way to interact with the database.

```
python app.py
```

Open your browser and navigate to `http://127.0.0.1:5000` to access the web interface.
