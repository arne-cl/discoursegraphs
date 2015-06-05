#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code to convert document graphs to GML files.
"""

from networkx import write_gml as nx_write_gml

from discoursegraphs.readwrite.generic import ensure_ascii_labels
from discoursegraphs.readwrite.generic import (layerset2str,
                                               attriblist2str)


def write_gml(docgraph, output_file):
    """
    takes a document graph, converts it into GML format and writes it to
    a file.
    """
    layerset2str(docgraph)
    attriblist2str(docgraph)
    ensure_ascii_labels(docgraph)
    nx_write_gml(docgraph, output_file)
