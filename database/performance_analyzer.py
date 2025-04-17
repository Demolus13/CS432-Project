"""
Performance analyzer for comparing B+ Tree and Brute Force DB.
"""
import time
import random
import matplotlib.pyplot as plt
import numpy as np
import psutil
import os
from typing import List, Tuple, Dict, Any, Callable
import gc

from .bplustree import BPlusTree
from .bruteforce import BruteForceDB


class PerformanceAnalyzer:
    """Class for analyzing the performance of B+ Tree and Brute Force DB."""

    def __init__(self, b_plus_tree_order: int = 4):
        """
        Initialize the performance analyzer.

        Args:
            b_plus_tree_order: The order of the B+ Tree
        """
        self.b_plus_tree_order = b_plus_tree_order
        self.results = {
            'insertion': {'b_plus_tree': [], 'brute_force': []},
            'search': {'b_plus_tree': [], 'brute_force': []},
            'range_query': {'b_plus_tree': [], 'brute_force': []},
            'deletion': {'b_plus_tree': [], 'brute_force': []},
            'random': {'b_plus_tree': [], 'brute_force': []},
            'memory': {'b_plus_tree': [], 'brute_force': []}
        }

    def measure_insertion_time(self, keys: List[Any], values: List[Any]) -> Tuple[float, float]:
        """
        Measure the time taken to insert keys and values into both data structures.

        Args:
            keys: The keys to insert
            values: The values to insert

        Returns:
            A tuple of (b_plus_tree_time, brute_force_time)
        """
        # Measure B+ Tree insertion time
        b_plus_tree = BPlusTree(self.b_plus_tree_order)
        start_time = time.time()
        for i in range(len(keys)):
            b_plus_tree.insert(keys[i], values[i])
        b_plus_tree_time = time.time() - start_time

        # Measure Brute Force DB insertion time
        brute_force_db = BruteForceDB()
        start_time = time.time()
        for i in range(len(keys)):
            brute_force_db.insert(keys[i], values[i])
        brute_force_time = time.time() - start_time

        return b_plus_tree_time, brute_force_time

    def measure_search_time(self, keys: List[Any], search_keys: List[Any]) -> Tuple[float, float]:
        """
        Measure the time taken to search for keys in both data structures.

        Args:
            keys: The keys to insert
            search_keys: The keys to search for

        Returns:
            A tuple of (b_plus_tree_time, brute_force_time)
        """
        # Create and populate the data structures
        b_plus_tree = BPlusTree(self.b_plus_tree_order)
        brute_force_db = BruteForceDB()

        for i in range(len(keys)):
            b_plus_tree.insert(keys[i], i)
            brute_force_db.insert(keys[i], i)

        # Measure B+ Tree search time
        start_time = time.time()
        for key in search_keys:
            b_plus_tree.find(key)
        b_plus_tree_time = time.time() - start_time

        # Measure Brute Force DB search time
        start_time = time.time()
        for key in search_keys:
            brute_force_db.find(key)
        brute_force_time = time.time() - start_time

        return b_plus_tree_time, brute_force_time

    def measure_range_query_time(self, keys: List[Any], ranges: List[Tuple[Any, Any]]) -> Tuple[float, float]:
        """
        Measure the time taken to perform range queries in both data structures.

        Args:
            keys: The keys to insert
            ranges: A list of (start_key, end_key) tuples

        Returns:
            A tuple of (b_plus_tree_time, brute_force_time)
        """
        # Create and populate the data structures
        b_plus_tree = BPlusTree(self.b_plus_tree_order)
        brute_force_db = BruteForceDB()

        for i in range(len(keys)):
            b_plus_tree.insert(keys[i], i)
            brute_force_db.insert(keys[i], i)

        # Measure B+ Tree range query time
        start_time = time.time()
        for start_key, end_key in ranges:
            b_plus_tree.range_query(start_key, end_key)
        b_plus_tree_time = time.time() - start_time

        # Measure Brute Force DB range query time
        start_time = time.time()
        for start_key, end_key in ranges:
            brute_force_db.range_query(start_key, end_key)
        brute_force_time = time.time() - start_time

        return b_plus_tree_time, brute_force_time

    def measure_deletion_time(self, keys: List[Any], delete_keys: List[Any]) -> Tuple[float, float]:
        """
        Measure the time taken to delete keys from both data structures.

        Args:
            keys: The keys to insert
            delete_keys: The keys to delete

        Returns:
            A tuple of (b_plus_tree_time, brute_force_time)
        """
        # Create and populate the data structures
        b_plus_tree = BPlusTree(self.b_plus_tree_order)
        brute_force_db = BruteForceDB()

        for i in range(len(keys)):
            b_plus_tree.insert(keys[i], i)
            brute_force_db.insert(keys[i], i)

        # Measure B+ Tree deletion time
        start_time = time.time()
        for key in delete_keys:
            b_plus_tree.delete(key)
        b_plus_tree_time = time.time() - start_time

        # Measure Brute Force DB deletion time
        start_time = time.time()
        for key in delete_keys:
            brute_force_db.delete(key)
        brute_force_time = time.time() - start_time

        return b_plus_tree_time, brute_force_time

    def measure_random_operations_time(self, keys: List[Any], num_operations: int) -> Tuple[float, float]:
        """
        Measure the time taken to perform random operations in both data structures.

        Args:
            keys: The keys to use
            num_operations: The number of random operations to perform

        Returns:
            A tuple of (b_plus_tree_time, brute_force_time)
        """
        # Handle the case where there are not enough keys
        if len(keys) < 2:
            return 0.0, 0.0

        # Create and populate the data structures
        b_plus_tree = BPlusTree(self.b_plus_tree_order)
        brute_force_db = BruteForceDB()

        # Insert half of the keys initially (at least 1)
        half = max(1, len(keys) // 2)
        for i in range(half):
            b_plus_tree.insert(keys[i], i)
            brute_force_db.insert(keys[i], i)

        # Define the operations
        operations = ['insert', 'search']

        # Add delete and range_query operations only if there are enough keys
        if half > 0:
            operations.append('delete')
        if len(keys) > 1:
            operations.append('range_query')

        # Measure B+ Tree random operations time
        start_time = time.time()
        for _ in range(num_operations):
            op = random.choice(operations)
            try:
                if op == 'insert':
                    # Choose from the second half of keys, or any key if there's only one
                    if half < len(keys):
                        key = random.choice(keys[half:])
                    else:
                        key = random.choice(keys)
                    b_plus_tree.insert(key, key)
                elif op == 'search':
                    key = random.choice(keys)
                    b_plus_tree.find(key)
                elif op == 'delete':
                    # Choose from the first half of keys
                    key = random.choice(keys[:half])
                    b_plus_tree.delete(key)
                elif op == 'range_query':
                    # Ensure we have keys to choose from
                    start_key = random.choice(keys)
                    # Find keys that are greater than or equal to start_key
                    greater_keys = [k for k in keys if k >= start_key]
                    if greater_keys:
                        end_key = random.choice(greater_keys)
                        b_plus_tree.range_query(start_key, end_key)
                    else:
                        # If no greater keys, use start_key as end_key
                        b_plus_tree.range_query(start_key, start_key)
            except Exception as e:
                # Skip this operation if it fails
                print(f"Error in B+ Tree operation {op}: {e}")
                continue
        b_plus_tree_time = time.time() - start_time

        # Measure Brute Force DB random operations time
        start_time = time.time()
        for _ in range(num_operations):
            op = random.choice(operations)
            try:
                if op == 'insert':
                    # Choose from the second half of keys, or any key if there's only one
                    if half < len(keys):
                        key = random.choice(keys[half:])
                    else:
                        key = random.choice(keys)
                    brute_force_db.insert(key, key)
                elif op == 'search':
                    key = random.choice(keys)
                    brute_force_db.find(key)
                elif op == 'delete':
                    # Choose from the first half of keys
                    key = random.choice(keys[:half])
                    brute_force_db.delete(key)
                elif op == 'range_query':
                    # Ensure we have keys to choose from
                    start_key = random.choice(keys)
                    # Find keys that are greater than or equal to start_key
                    greater_keys = [k for k in keys if k >= start_key]
                    if greater_keys:
                        end_key = random.choice(greater_keys)
                        brute_force_db.range_query(start_key, end_key)
                    else:
                        # If no greater keys, use start_key as end_key
                        brute_force_db.range_query(start_key, start_key)
            except Exception as e:
                # Skip this operation if it fails
                print(f"Error in Brute Force operation {op}: {e}")
                continue
        brute_force_time = time.time() - start_time

        return b_plus_tree_time, brute_force_time

    def measure_memory_usage(self, keys: List[Any]) -> Tuple[float, float]:
        """
        Measure the memory usage of both data structures.

        Args:
            keys: The keys to insert

        Returns:
            A tuple of (b_plus_tree_memory, brute_force_memory)
        """
        # Force garbage collection
        gc.collect()

        # Measure B+ Tree memory usage
        process = psutil.Process(os.getpid())
        base_memory = process.memory_info().rss / 1024 / 1024  # MB

        b_plus_tree = BPlusTree(self.b_plus_tree_order)
        for i in range(len(keys)):
            b_plus_tree.insert(keys[i], i)

        b_plus_tree_memory = process.memory_info().rss / 1024 / 1024 - base_memory

        # Force garbage collection
        del b_plus_tree
        gc.collect()

        # Measure Brute Force DB memory usage
        base_memory = process.memory_info().rss / 1024 / 1024  # MB

        brute_force_db = BruteForceDB()
        for i in range(len(keys)):
            brute_force_db.insert(keys[i], i)

        brute_force_memory = process.memory_info().rss / 1024 / 1024 - base_memory

        return b_plus_tree_memory, brute_force_memory

    def run_benchmarks(self, sizes: List[int], num_samples: int = 3) -> Dict[str, Dict[str, List[float]]]:
        """
        Run benchmarks for different data sizes.

        Args:
            sizes: The data sizes to benchmark
            num_samples: The number of samples to take for each size

        Returns:
            A dictionary of benchmark results
        """
        for size in sizes:
            print(f"Running benchmarks for size {size}...")

            b_plus_tree_insertion_times = []
            brute_force_insertion_times = []

            b_plus_tree_search_times = []
            brute_force_search_times = []

            b_plus_tree_range_query_times = []
            brute_force_range_query_times = []

            b_plus_tree_deletion_times = []
            brute_force_deletion_times = []

            b_plus_tree_random_times = []
            brute_force_random_times = []

            b_plus_tree_memory = []
            brute_force_memory = []

            for _ in range(num_samples):
                # Generate random keys and values
                keys = random.sample(range(size * 10), size)
                values = [f"value_{i}" for i in range(size)]

                # Measure insertion time
                b_plus_tree_time, brute_force_time = self.measure_insertion_time(keys, values)
                b_plus_tree_insertion_times.append(b_plus_tree_time)
                brute_force_insertion_times.append(brute_force_time)

                # Generate random search keys
                search_keys = random.sample(keys, min(size, 100))

                # Measure search time
                b_plus_tree_time, brute_force_time = self.measure_search_time(keys, search_keys)
                b_plus_tree_search_times.append(b_plus_tree_time)
                brute_force_search_times.append(brute_force_time)

                # Generate random range queries
                ranges = []
                for _ in range(min(size, 10)):
                    start_key = random.choice(keys)
                    # Find keys that are greater than or equal to start_key
                    greater_keys = [k for k in keys if k >= start_key]
                    if greater_keys:
                        end_key = random.choice(greater_keys)
                    else:
                        # If no greater keys, use start_key as end_key
                        end_key = start_key
                    ranges.append((start_key, end_key))

                # Measure range query time
                b_plus_tree_time, brute_force_time = self.measure_range_query_time(keys, ranges)
                b_plus_tree_range_query_times.append(b_plus_tree_time)
                brute_force_range_query_times.append(brute_force_time)

                # Generate random delete keys
                delete_keys = random.sample(keys, min(size, 100))

                # Measure deletion time
                b_plus_tree_time, brute_force_time = self.measure_deletion_time(keys, delete_keys)
                b_plus_tree_deletion_times.append(b_plus_tree_time)
                brute_force_deletion_times.append(brute_force_time)

                # Measure random operations time
                b_plus_tree_time, brute_force_time = self.measure_random_operations_time(keys, min(size, 100))
                b_plus_tree_random_times.append(b_plus_tree_time)
                brute_force_random_times.append(brute_force_time)

                # Measure memory usage
                b_plus_tree_mem, brute_force_mem = self.measure_memory_usage(keys)
                b_plus_tree_memory.append(b_plus_tree_mem)
                brute_force_memory.append(brute_force_mem)

            # Calculate average times
            self.results['insertion']['b_plus_tree'].append(np.mean(b_plus_tree_insertion_times))
            self.results['insertion']['brute_force'].append(np.mean(brute_force_insertion_times))

            self.results['search']['b_plus_tree'].append(np.mean(b_plus_tree_search_times))
            self.results['search']['brute_force'].append(np.mean(brute_force_search_times))

            self.results['range_query']['b_plus_tree'].append(np.mean(b_plus_tree_range_query_times))
            self.results['range_query']['brute_force'].append(np.mean(brute_force_range_query_times))

            self.results['deletion']['b_plus_tree'].append(np.mean(b_plus_tree_deletion_times))
            self.results['deletion']['brute_force'].append(np.mean(brute_force_deletion_times))

            self.results['random']['b_plus_tree'].append(np.mean(b_plus_tree_random_times))
            self.results['random']['brute_force'].append(np.mean(brute_force_random_times))

            self.results['memory']['b_plus_tree'].append(np.mean(b_plus_tree_memory))
            self.results['memory']['brute_force'].append(np.mean(brute_force_memory))

        return self.results

    def plot_results(self, sizes: List[int], save_path: str = None) -> None:
        """
        Plot the benchmark results.

        Args:
            sizes: The data sizes used in the benchmarks
            save_path: The path to save the plots to
        """
        operations = ['insertion', 'search', 'range_query', 'deletion', 'random']

        # Create a figure with subplots
        fig, axs = plt.subplots(3, 2, figsize=(15, 15))
        axs = axs.flatten()

        # Plot time results
        for i, operation in enumerate(operations):
            axs[i].plot(sizes, self.results[operation]['b_plus_tree'], 'o-', label='B+ Tree')
            axs[i].plot(sizes, self.results[operation]['brute_force'], 's-', label='Brute Force')
            axs[i].set_xlabel('Data Size')
            axs[i].set_ylabel('Time (s)')
            axs[i].set_title(f'{operation.replace("_", " ").title()} Time')
            axs[i].legend()
            axs[i].grid(True)

        # Plot memory usage
        axs[5].plot(sizes, self.results['memory']['b_plus_tree'], 'o-', label='B+ Tree')
        axs[5].plot(sizes, self.results['memory']['brute_force'], 's-', label='Brute Force')
        axs[5].set_xlabel('Data Size')
        axs[5].set_ylabel('Memory (MB)')
        axs[5].set_title('Memory Usage')
        axs[5].legend()
        axs[5].grid(True)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)

        plt.close()
