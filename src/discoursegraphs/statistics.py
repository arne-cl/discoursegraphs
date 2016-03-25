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
    for key, count in sorted(counter.items(), key=itemgetter(1), reverse=True):
        print "{0}{1} - {2}".format('\t'*tab, key, count)


def print_most_common(counter, number=5, tab=1):
    """print the most common elements of a counter"""
    for key, count in counter.most_common(number):
        print "{0}{1} - {2}".format('\t'*tab, key, count)


def node_statistics(docgraph):
    """print basic statistics about a node, e.g. layer/attribute counts"""
    print "Node statistics\n==============="
    layer_counts = Counter()
    attrib_counts = Counter()
    for node_id, node_attrs in docgraph.nodes_iter(data=True):
        for layer in node_attrs['layers']:
            layer_counts[layer] += 1
        for attrib in node_attrs:
            attrib_counts[attrib] += 1

    print "\nnumber of nodes with layers"
    print_sorted_counter(layer_counts)
    print "\nnumber of nodes with attributes"
    print_sorted_counter(attrib_counts)


def edge_statistics(docgraph):
    """print basic statistics about an edge, e.g. layer/attribute counts"""
    print "Edge statistics\n==============="
    layer_counts = Counter()
    attrib_counts = Counter()
    source_counts = Counter()
    target_counts = Counter()
    for source, target, edge_attrs in docgraph.edges_iter(data=True):
        for layer in edge_attrs['layers']:
            layer_counts[layer] += 1
        for attrib in edge_attrs:
            attrib_counts[attrib] += 1
        source_counts[source] += 1
        target_counts[target] += 1

    print "\nnumber of edges with layers"
    print_sorted_counter(layer_counts)
    print "\nnumber of edges with attributes"
    print_sorted_counter(attrib_counts)

    print "\nmost common source edges"
    print_most_common(source_counts)
    print "\nmost common target edges"
    print_most_common(target_counts)


def info(docgraph):
    """print node and edge statistics of a document graph"""
    print networkx.info(docgraph), '\n'
    node_statistics(docgraph)
    print
    edge_statistics(docgraph)
