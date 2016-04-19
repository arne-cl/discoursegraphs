#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# original author: Rohit Aggarwal <rohit.neonx@mailnull.com>,
# originally published under MIT license at github.com/ducky427/neonx
#
# minor modifications: Arne Neumann <discoursegraphs.programming@arne.cl>

import json
import networkx as nx


def node2geoff(node_name, properties, encoder):
    """converts a NetworkX node into a Geoff string.

    Parameters
    ----------
    node_name : str or int
        the ID of a NetworkX node
    properties : dict
        a dictionary of node attributes
    encoder : json.JSONEncoder
        an instance of a JSON encoder (e.g. `json.JSONEncoder`)

    Returns
    -------
    geoff : str
        a Geoff string
    """
    if properties:
        return '({0} {1})'.format(node_name,
                                  encoder.encode(properties))
    else:
        return '({0})'.format(node_name)


def edge2geoff(from_node, to_node, properties, edge_relationship_name, encoder):
    """converts a NetworkX edge into a Geoff string.

    Parameters
    ----------
    from_node : str or int
        the ID of a NetworkX source node
    to_node : str or int
        the ID of a NetworkX target node
    properties : dict
        a dictionary of edge attributes
    edge_relationship_name : str
        string that describes the relationship between the two nodes
    encoder : json.JSONEncoder
        an instance of a JSON encoder (e.g. `json.JSONEncoder`)

    Returns
    -------
    geoff : str
        a Geoff string
    """
    edge_string = None
    if properties:
        args = [from_node, edge_relationship_name,
                encoder.encode(properties), to_node]
        edge_string = '({0})-[:{1} {2}]->({3})'.format(*args)
    else:
        args = [from_node, edge_relationship_name, to_node]
        edge_string = '({0})-[:{1}]->({2})'.format(*args)

    return edge_string


def graph2geoff(graph, edge_rel_name, encoder=None):
    """ Get the `graph` as Geoff string. The edges between the nodes
    have relationship name `edge_rel_name`. The code
    below shows a simple example::

        # create a graph
        import networkx as nx
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        G.add_edge(1, 2)
        G.add_edge(2, 3)

        # get the geoff string
        geoff_string = graph2geoff(G, 'LINKS_TO')

    If the properties are not json encodable, please pass a custom JSON encoder
    class. See `JSONEncoder
    <http://docs.python.org/2/library/json.html#json.JSONEncoder/>`_.

    Parameters
    ----------
    graph : Graph or DiGraph
        a NetworkX Graph or a DiGraph
    edge_rel_name : str
        relationship name between the nodes
    encoder: JSONEncoder or None
        JSONEncoder object. Defaults to JSONEncoder.

    Returns
    -------
    geoff : str
        a Geoff string
    """
    if encoder is None:
        encoder = json.JSONEncoder()
    is_digraph = isinstance(graph, nx.DiGraph)

    lines = []
    lapp = lines.append
    for node_name, properties in graph.nodes(data=True):
        lapp(node2geoff(node_name, properties, encoder))

    for from_node, to_node, properties in graph.edges(data=True):
        lapp(edge2geoff(from_node, to_node, properties, edge_rel_name, encoder))
        if not is_digraph:
            lapp(edge2geoff(to_node, from_node, properties, edge_rel_name,
                          encoder))

    return '\n'.join(lines)
