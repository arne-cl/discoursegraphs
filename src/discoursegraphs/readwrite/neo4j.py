#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
The ``neo4j`` module converts a ``DiscourseDocumentGraph`` into a ``Geoff``
string which can be imported into a ``Neo4j`` graph database.
"""

from copy import deepcopy

from discoursegraphs.util import ensure_utf8
from discoursegraphs.readwrite.generic import layerset2list
from discoursegraphs.readwrite.geoff import graph2geoff


def add_node_ids_as_labels(discoursegraph):
    """
    Adds the ID of each node of a discourse graph as a label (an attribute
    named ``label`` with the value of the node ID) to itself. This will
    ignore nodes whose ID isn't a string or which already have a label
    attribute.

    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id, properties in discoursegraph.nodes_iter(data=True):
        if 'label' not in properties and isinstance(node_id, (str, unicode)):
            discoursegraph.node[node_id]['label'] = ensure_utf8(node_id)


def convert_to_geoff(discoursegraph):
    """
    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
        the discourse document graph to be converted into GEOFF format

    Returns
    -------
    geoff : string
        a geoff string representation of the discourse graph.
    """
    dg_copy = deepcopy(discoursegraph)
    layerset2list(dg_copy)
    add_node_ids_as_labels(dg_copy)
    return graph2geoff(dg_copy, 'LINKS_TO')


def write_geoff(discoursegraph, output_file):
    """
    converts a DiscourseDocumentGraph into a Geoff file and
    writes it to the given file (or file path).
    """
    if isinstance(output_file, str):
        with open(output_file, 'w') as outfile:
            outfile.write(convert_to_geoff(discoursegraph))
    else:  # output_file is a file object
        output_file.write(convert_to_geoff(discoursegraph))


# alias for write_geoff(): convert document graph into a Geoff file
write_neo4j = write_geoff
