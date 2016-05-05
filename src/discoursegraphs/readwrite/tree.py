#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code to convert discourse graphs into rooted, ordered
trees.
"""

from collections import defaultdict, deque
from functools import partial

import networkx as nx

from discoursegraphs import (
    EdgeTypes, istoken, select_neighbors_by_edge_attribute)


def get_child_nodes(docgraph, parent_node_id, data=False):
    """Yield all nodes that the given node dominates or spans."""
    return select_neighbors_by_edge_attribute(
        docgraph=docgraph,
        source=parent_node_id,
        attribute='edge_type',
        value=[EdgeTypes.dominance_relation,
               EdgeTypes.spanning_relation],
        data=data)


def horizontal_positions(docgraph, sentence_root=None):
    """return map: node ID -> first token index (int) it covers"""
    # calculate positions for the whole graph
    if (sentence_root is None) or (sentence_root == docgraph.root) \
        or ('tokens' not in docgraph.node[sentence_root]):
            sentence_root = docgraph.root
            token_nodes = docgraph.tokens
            path = {}
    else:  # calculate positions only for the given sentence subgraph
        token_nodes = docgraph.node[sentence_root]['tokens']
        path = {sentence_root: 0}

    predecessors = nx.predecessor(docgraph, sentence_root)

    for i, token_node in enumerate(token_nodes):
        start_node = token_node
        while predecessors[start_node]:
            if start_node not in path:
                path[start_node] = i
            start_node = predecessors[start_node][0]
    return path


def sorted_bfs_edges(G, source=None):
    """Produce edges in a breadth-first-search starting at source.

    Neighbors appear in the order a linguist would expect in a syntax tree.
    The result will only contain edges that express a dominance or spanning
    relation, i.e. edges expressing pointing or precedence relations will
    be ignored.

    Parameters
    ----------
    G : DiscourseDocumentGraph

    source : node
       Specify starting node for breadth-first search and return edges in
       the component reachable from source.

    Returns
    -------
    edges: generator
       A generator of edges in the breadth-first-search.
    """
    if source is None:
        source = G.root

    xpos = horizontal_positions(G, source)
    neighbors = G.neighbors_iter
    visited = set([source])
    source_children = get_child_nodes(G, source)
    queue = deque([(source, iter(sorted(source_children,
                                        key=lambda x: xpos[x])))])
    while queue:
        parent, children = queue[0]
        try:
            child = next(children)
            if child not in visited:
                yield parent, child
                visited.add(child)
                grandchildren = get_child_nodes(G, child)
                queue.append((child, iter(sorted(grandchildren,
                                                 key=lambda x: xpos[x]))))
        except StopIteration:
            queue.popleft()


def sorted_bfs_successors(G, source=None):
    """Return dictionary of successors in breadth-first-search from source.

    Parameters
    ----------
    G : DiscourseDocumentGraph graph

    source : node
       Specify starting node for breadth-first search and return edges in
       the component reachable from source.

    Returns
    -------
    succ: dict
       A dictionary with nodes as keys and list of succssors nodes as values.
    """
    if source is None:
        source = G.root

    d = defaultdict(list)
    for s,t in sorted_bfs_edges(G, source):
        d[s].append(t)
    return dict(d)


def node2bracket(docgraph, node_id, child_str=''):
    """convert a docgraph node into a PTB-style string."""
    node_attrs = docgraph.node[node_id]
    if istoken(docgraph, node_id):
        pos_str = node_attrs.get(docgraph.ns+':pos', '')
        token_str = node_attrs[docgraph.ns+':token']
        return u"({pos}{space1}{token}{space2}{child})".format(
            pos=pos_str, space1=bool(pos_str)*' ', token=token_str,
            space2=bool(child_str)*' ', child=child_str)
    else:  # node is not a token
        label_str=node_attrs.get('label', '')
        return u"({label}{space}{child})".format(
            label=label_str, space=bool(label_str and child_str)*' ',
            child=child_str)


def tree2bracket(docgraph, root=None, successors=None):
    """convert a docgraph into a PTB-style string.

    If root (a node ID) is given, only convert the subgraph that this
    node domintes/spans into a PTB-style string.
    """
    if root is None:
        root = docgraph.root
    if successors is None:
        successors = sorted_bfs_successors(docgraph, root)

    if root in successors:
        embed_str = u" ".join(tree2bracket(docgraph, child, successors)
                              for child in successors[root])
        return node2bracket(docgraph, root, embed_str)
    else:
        return node2bracket(docgraph, root)
