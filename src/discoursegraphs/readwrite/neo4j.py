#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from neonx import write_to_neo, get_geoff
from discoursegraphs import DiscourseDocumentGraph

def make_json_encodable(discoursegraph):
    """
    typecasts all `layers` sets to lists to make the graph
    convertible into `geoff` format.
    
    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id in discoursegraph:
        discoursegraph.node[node_id]['layers'] = \
            list(discoursegraph.node[node_id]['layers'])
    for (from_id, to_id) in adg.edges_iter():
        # there might be multiple edges between 2 nodes
        edge_dict = adg.edge[from_id][to_id]
        for edge_id in edge_dict:
            edge_dict[edge_id]['layers'] = \
                list(edge_dict[edge_id]['layers'])


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
    make_json_encodable(discoursegraphs)
    return get_geoff(discoursegraph, 'LINKS_TO')


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
    make_json_encodable(discoursegraphs)
    return write_to_neo("http://localhost:7474/db/data/",
        discoursegraph, 'LINKS_TO')
