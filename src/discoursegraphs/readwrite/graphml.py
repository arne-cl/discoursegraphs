#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code to convert document graphs to GraphML files.
"""

from networkx import write_graphml as nx_write_graphml
from discoursegraphs.readwrite.generic import (
    attriblist2str, layerset2str, remove_root_metadata)


def write_graphml(docgraph, output_file):
    """
    takes a document graph, converts it into GraphML format and writes it to
    a file.
    """
    layerset2str(docgraph)
    attriblist2str(docgraph)
    remove_root_metadata(docgraph)
    nx_write_graphml(docgraph, output_file)

