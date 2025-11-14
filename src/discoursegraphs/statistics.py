#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
The ``statistics`` module contains functions for basic, descriptive statistics
on discourse graphs (e.g. labelled node/edge counts).
"""

from collections import Counter
from operator import itemgetter

import networkx


def print_sorted_counter(counter, tab=1):
    """print all elements of a counter in descending order"""
    # Sort by count (descending), then by key (ascending) for deterministic output
    for key, count in sorted(list(counter.items()), key=lambda x: (-x[1], x[0])):
        print("{0}{1} - {2}".format('\t'*tab, key, count))


def print_most_common(counter, number=5, tab=1):
    """print the most common elements of a counter"""
    # Sort by count (descending), then by key (ascending) for deterministic output
    items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))[:number]
    for key, count in items:
        print("{0}{1} - {2}".format('\t'*tab, key, count))


def node_statistics(docgraph):
    """print basic statistics about a node, e.g. layer/attribute counts"""
    print("Node statistics\n===============")
    layer_counts = Counter()
    attrib_counts = Counter()
    for node_id, node_attrs in docgraph.nodes(data=True):
        for layer in node_attrs['layers']:
            layer_counts[layer] += 1
        for attrib in node_attrs:
            attrib_counts[attrib] += 1

    print("\nnumber of nodes with layers")
    print_sorted_counter(layer_counts)
    print("\nnumber of nodes with attributes")
    print_sorted_counter(attrib_counts)


def edge_statistics(docgraph):
    """print basic statistics about an edge, e.g. layer/attribute counts"""
    print("Edge statistics\n===============")
    layer_counts = Counter()
    attrib_counts = Counter()
    source_counts = Counter()
    target_counts = Counter()
    for source, target, edge_attrs in docgraph.edges(data=True):
        for layer in edge_attrs['layers']:
            layer_counts[layer] += 1
        for attrib in edge_attrs:
            attrib_counts[attrib] += 1
        source_counts[source] += 1
        target_counts[target] += 1

    print("\nnumber of edges with layers")
    print_sorted_counter(layer_counts)
    print("\nnumber of edges with attributes")
    print_sorted_counter(attrib_counts)

    print("\nmost common source edges")
    print_most_common(source_counts)
    print("\nmost common target edges")
    print_most_common(target_counts)


def info(docgraph):
    """print node and edge statistics of a document graph"""
    # networkx.info() was removed in NetworkX 3.x
    # Reimplemented to match the old format for compatibility
    print(f"Name: {docgraph.name}")
    print(f"Type: {type(docgraph).__name__}")
    print(f"Number of nodes: {docgraph.number_of_nodes()}")
    print(f"Number of edges: {docgraph.number_of_edges()}")
    # Calculate and print average degree
    num_nodes = docgraph.number_of_nodes()
    if num_nodes > 0:
        avg_in = sum(d for n, d in docgraph.in_degree()) / num_nodes
        avg_out = sum(d for n, d in docgraph.out_degree()) / num_nodes
        print(f"Average in degree: {avg_in:8.4f}")
        print(f"Average out degree: {avg_out:8.4f} ")
    print()
    node_statistics(docgraph)
    print()
    edge_statistics(docgraph)
