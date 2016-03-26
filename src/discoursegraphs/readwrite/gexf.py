#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code to convert document graphs to GEXF files.
"""

from copy import deepcopy

from networkx import write_gexf as nx_write_gexf
from discoursegraphs.readwrite.generic import (
    attriblist2str, layerset2str, remove_root_metadata)


def write_gexf(docgraph, output_file):
    """
    takes a document graph, converts it into GEXF format and writes it to
    a file.
    """
    dg_copy = deepcopy(docgraph)
    remove_root_metadata(dg_copy)
    layerset2str(dg_copy)
    attriblist2str(dg_copy)
    nx_write_gexf(dg_copy, output_file)
