#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import pytest

import discoursegraphs as dg

"""
This module contains some tests for the ``discoursegraph`` module.
"""

def test_is_continuous():
    """tests, if a discontinuous span of tokens is recognised as such.

    The node ``lower`` spans the two non-adjacent tokens 1 and 4.

            root
              |
         ---upper---
         |    |    |
    -----|--lower--|----
    |    |         |   |
    1    2         3   4
    """
    docgraph = dg.DiscourseDocumentGraph()
    docgraph.add_node('1', attr_dict={'discoursegraph:token': '1'})
    docgraph.add_node('2', attr_dict={'discoursegraph:token': '2'})
    docgraph.add_node('3', attr_dict={'discoursegraph:token': '3'})
    docgraph.add_node('4', attr_dict={'discoursegraph:token': '4'})
    docgraph.add_edge(docgraph.root, 'upper', edge_type=dg.EdgeTypes.dominance_relation)
    docgraph.add_edge('upper', 'lower', edge_type=dg.EdgeTypes.dominance_relation)
    docgraph.add_edge('lower', '1', edge_type=dg.EdgeTypes.spanning_relation)
    docgraph.add_edge('upper', '2', edge_type=dg.EdgeTypes.spanning_relation)
    docgraph.add_edge('upper', '3', edge_type=dg.EdgeTypes.spanning_relation)
    docgraph.add_edge('lower', '4', edge_type=dg.EdgeTypes.spanning_relation)
    # determine order of the tokens
    docgraph.tokens = ['1', '2', '3', '4']

    assert dg.is_continuous(docgraph, docgraph.root)
    assert dg.is_continuous(docgraph, 'upper')
    assert not dg.is_continuous(docgraph, 'lower')
    assert dg.is_continuous(docgraph, '1')
    assert dg.is_continuous(docgraph, '2')
    assert dg.is_continuous(docgraph, '3')
    assert dg.is_continuous(docgraph, '4')
