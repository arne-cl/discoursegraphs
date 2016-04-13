#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code to convert document graphs to graphviz graphs
("dot files") and manipulate them.
"""

import re
import codecs

import networkx as nx
from networkx.drawing.nx_agraph import write_dot

QUOTE_RE = re.compile('"') # a single "-char
UNQUOTE_RE = re.compile('^"(.*)"$') # a string beginning and ending with a "-char


def quote_for_pydot(string):
    """
    takes a string (or int) and encloses it with "-chars. if the string
    contains "-chars itself, they will be escaped.
    """
    if isinstance(string, int):
        string = str(string)
    escaped_str = QUOTE_RE.sub(r'\\"', string)
    return u'"{}"'.format(escaped_str)


def unquote_from_pydot(string):
    """
    removes the "-char from the beginning and end of a pydot-quoted string
    and de-escapes \\-escaped "-chars."""
    return UNQUOTE_RE.match(string).groups()[0].replace('\\"', '"')


def _preprocess_nodes_for_pydot(nodes_with_data):
    """throw away all node attributes, except for 'label'"""
    for (node_id, attrs) in nodes_with_data:
        if 'label' in attrs:
            yield (quote_for_pydot(node_id),
                   {'label': quote_for_pydot(attrs['label'])})
        else:
            yield (quote_for_pydot(node_id), {})


def _preprocess_edges_for_pydot(edges_with_data):
    """throw away all edge attributes, except for 'label'"""
    for (source, target, attrs) in edges_with_data:
        if 'label' in attrs:
            yield (quote_for_pydot(source), quote_for_pydot(target),
                   {'label': quote_for_pydot(attrs['label'])})
        else:
            yield (quote_for_pydot(source), quote_for_pydot(target), {})


def preprocess_for_pydot(docgraph):
    """
    takes a document graph and strips all the information that aren't
    necessary for visualizing it with graphviz. ensures that all
    node/edge names and labels are properly quoted.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        a document graph
    Returns
    -------
    stripped_graph : networkx.MultiDiGraph
        a graph containing only information that is needed for graphviz
    """
    stripped_graph = nx.MultiDiGraph()
    stripped_graph.name = docgraph.name

    nodes = _preprocess_nodes_for_pydot(docgraph.nodes_iter(data=True))
    edges = _preprocess_edges_for_pydot(docgraph.edges_iter(data=True))

    stripped_graph.add_nodes_from(nodes)
    stripped_graph.add_edges_from(edges)
    return stripped_graph


def print_dot(docgraph):
    """
    converts a document graph into a dot file and returns it as a string.

    If this function call is prepended by %dotstr,
    it will display the given document graph as a dot/graphviz graph
    in the currently running IPython notebook session.

    To use this function, the gvmagic IPython notebook extension
    needs to be installed once::

        %install_ext https://raw.github.com/cjdrake/ipython-magic/master/gvmagic.py

    In order to visualize dot graphs in your currently running
    IPython notebook, run this command once::

        %load_ext gvmagic
    """
    stripped_graph = preprocess_for_pydot(docgraph)
    return nx.drawing.nx_pydot.to_pydot(stripped_graph).to_string()
