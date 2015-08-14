#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code to convert document graphs to graphviz graphs
("dot files") and manipulate them.
"""

import codecs
from tempfile import NamedTemporaryFile

from networkx.drawing.nx_pydot import to_pydot

try:
	import pydot
except ImportError:
	raise ImportError("write_dot() requires pydot",
					  "http://code.google.com/p/pydot/")


def write_dot(G, output_file):
    """write a NetworkX graph G to a Graphviz dot file (UTF-8)."""
    P=to_pydot(G)
    with codecs.open(output_file, mode='w', encoding='utf8') as out:
		out.write(P.to_string())


def print_dot(docgraph, ignore_node_labels=False):
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

    Parameters
    ----------
    ignore_node_labels : bool
        If True, use the ID of a node as its node label
    """
    tmp_file = NamedTemporaryFile()
    if ignore_node_labels:
        tmpgraph = docgraph.copy()
        for node, ndict in tmpgraph.nodes_iter(data=True):
            ndict.pop('label', None)
    else:
        tmpgraph = docgraph

    write_dot(tmpgraph, tmp_file.name)
    # write_dot does not seem to produce valid utf8 for all files, that's
    # why we're adding error handling here
    #
    # maz-10175.rs3, maz-10374.rs3 and maz-13758.rs3 cause this
    # error: UnicodeDecodeError: 'utf8' codec can't decode byte 0xc3 in
    # position ...: invalid continuation byte
    return codecs.open(tmp_file.name, encoding='utf8', errors='replace').read()
