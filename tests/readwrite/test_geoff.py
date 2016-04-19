#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Basic tests for the ``geoff`` module, slightly modified from 
Rohit Aggarwal's neonx library: github.com/ducky427/neonx.
"""

import datetime
import json

import networkx as nx
import pytest

from discoursegraphs.readwrite.geoff import graph2geoff


def test_graph2geoff_digraph():
    result = """(0)
(1)
(2 {"debug": "test\\""})
(0)-[:LINK_TO {"debug": false}]->(1)
(0)-[:LINK_TO]->(2)"""
    graph = nx.balanced_tree(2, 1, create_using=nx.DiGraph())
    graph.node[2]['debug'] = 'test"'
    graph[0][1]['debug'] = False
    assert graph2geoff(graph, 'LINK_TO') == result


def test_graph2geoff_graph():
    result = """(0)
(1)
(2 {"debug": "test\\""})
(0)-[:LINK_TO {"debug": false}]->(1)
(1)-[:LINK_TO {"debug": false}]->(0)
(0)-[:LINK_TO]->(2)
(2)-[:LINK_TO]->(0)"""
    graph = nx.balanced_tree(2, 1)
    graph.node[2]['debug'] = 'test"'
    graph[0][1]['debug'] = False
    assert graph2geoff(graph, 'LINK_TO') == result


class DateEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return o.strftime('%Y-%m-%d')
        return json.JSONEncoder.default(self, o)


def test_graph2geoff_digraph_fail():
    today = datetime.date(2012, 1, 1)

    graph = nx.balanced_tree(2, 1, create_using=nx.DiGraph())
    graph.node[2]['debug'] = 'test"'
    graph[0][1]['debug'] = today

    with pytest.raises(TypeError) as excinfo:
        graph2geoff(graph, 'LINK_TO')


def test_graph2geoff_digraph_custom():
    today = datetime.date(2012, 1, 1)
    result = """(0)
(1)
(2 {"debug": "test\\""})
(0)-[:LINK_TO {"debug": "2012-01-01"}]->(1)
(0)-[:LINK_TO]->(2)"""
    graph = nx.balanced_tree(2, 1, create_using=nx.DiGraph())
    graph.node[2]['debug'] = 'test"'
    graph[0][1]['debug'] = today

    data = graph2geoff(graph, 'LINK_TO', DateEncoder())
    assert data == result
