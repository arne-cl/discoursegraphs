#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code to convert document graphs to GEXF files.
"""

from networkx import write_gexf as nx_write_gexf
from discoursegraphs.readwrite.generic import (
    attriblist2str, layerset2str, remove_root_metadata)


def write_gexf(docgraph, output_file):
    """
    takes a document graph, converts it into GEXF format and writes it to
    a file.
    """
    remove_root_metadata(docgraph)
    layerset2str(docgraph)
    attriblist2str(docgraph)
    nx_write_gexf(docgraph, output_file)
