#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
"""

import sys
from collections import OrderedDict
from lxml import etree
import argparse
import re
import pudb  # TODO: rm debug

from discoursegraphs import DiscourseDocumentGraph
from discoursegraphs.util import ensure_unicode

REDUCE_WHITESPACE_RE = re.compile(' +')


class ConanoDocumentGraph(DiscourseDocumentGraph):
    """
    represents a Conano XML file as a multidigraph.

    Attributes
    ----------
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text
    root : str
        name of the document root node ID
    """
        """
        reads a Conano XML file and converts it into a multidigraph.
        Parameters
        ----------
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(DiscourseDocumentGraph, self).__init__()

        if name is not None:
            self.name = os.path.basename(conano_filepath)
        """


        Parameters
        ----------
        token_id : int
        """
        self.add_node(
            token_id,
            else:







if __name__ == "__main__":
