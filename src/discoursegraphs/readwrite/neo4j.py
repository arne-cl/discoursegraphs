#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
The ``neo4j`` module converts a ``DiscourseDocumentGraph`` into a ``Geoff``
string and/or exports it to a running ``Neo4j`` graph database.
"""

from neonx import write_to_neo, get_geoff
from discoursegraphs.util import ensure_utf8
from discoursegraphs.readwrite.generic import layerset2list


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
    layerset2list(discoursegraph)
    add_node_ids_as_labels(discoursegraph)
    return get_geoff(discoursegraph, 'LINKS_TO')


def write_geoff(discoursegraph, output_file):
    """
    converts a DiscourseDocumentGraph into a Geoff file and
    writes it to the given file (or file path).
    """
    assert isinstance(output_file, (str, file))
    if isinstance(output_file, str):
        with open(output_file, 'w') as outfile:
            outfile.write(convert_to_geoff(discoursegraph))
    else:  # output_file is a file object
        output_file.write(convert_to_geoff(discoursegraph))


# alias for write_geoff(): convert document graph into a Geoff file
write_neo4j = write_geoff


def upload_to_neo4j(discoursegraph):
    """
    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
        the discourse document graph to be uploaded to the local neo4j
        instance/

    Returns
    -------
    neonx_results : list of dict
        list of results from the `write_to_neo` function of neonx.
    """
    layerset2list(discoursegraph)
    add_node_ids_as_labels(discoursegraph)
    # neonx requires a label_name as a fallback, in case a node doesn't
    # have the specified label_attrib to extract the label from
    return write_to_neo("http://localhost:7474/db/data/",
                        discoursegraph, edge_rel_name='LINKS_TO',
                        edge_rel_attrib='edge_type', label_attrib='label',
                        label_name='discoursegraph:fallback_label')
