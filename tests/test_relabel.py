#!/usr/bin/env python
import networkx as nx
from networkx import empty_graph, DiGraph, Graph, MultiDiGraph, MultiGraph

import pytest

from discoursegraphs.relabel import relabel_nodes, convert_node_labels_to_integers


"""
This module contains tests for the relabel module, which was slightly adapted
from the same module in networkx. Tests were 'translated' from nose to py.test.
"""


def assert_edges_equal(edges1, edges2):
    # Assumes iterables with u,v nodes as
    # edge tuples (u,v), or
    # edge tuples with data dicts (u,v,d), or
    # edge tuples with keys and data dicts (u,v,k, d)
    from collections import defaultdict
    d1 = defaultdict(dict)
    d2 = defaultdict(dict)
    c1 = 0
    for c1,e in enumerate(edges1):
        u, v = e[0], e[1]
        data = e[2:]
        d1[u][v] = data
        d1[v][u] = data
    c2 = 0
    for c2, e in enumerate(edges2):
        u, v = e[0], e[1]
        data = e[2:]
        d2[u][v] = data
        d2[v][u] = data
    assert c1 == c2
    assert d1 == d2



def test_convert_node_labels_to_integers():
    """test stopped working after converting it from nose -> pytest

    Fixed: NetworkX 3.x empty_graph() has empty name, and degree is now a method.
    """
    # test that empty graph converts fine for all options
    G = empty_graph()
    H = convert_node_labels_to_integers(G, 100)
    # NetworkX 3.x: empty_graph() has empty name, so result is "()_with_int_labels"
    assert H.name == '()_with_int_labels'
    assert list(H.nodes()) == []
    assert list(H.edges()) == []

    for opt in ["default", "sorted", "increasing degree",
                "decreasing degree"]:
        G = empty_graph()
        H = convert_node_labels_to_integers(G, 100, ordering=opt)
        assert H.name == '()_with_int_labels'
        assert list(H.nodes()) == []
        assert list(H.edges()) == []

    G = empty_graph()
    G.add_edges_from([('A','B'), ('A','C'), ('B','C'), ('C','D')])
    G.name="paw"
    H = convert_node_labels_to_integers(G)
    degH = (d for n, d in H.degree())
    degG = (d for n, d in G.degree())
    assert sorted(degH) == sorted(degG)

    H = convert_node_labels_to_integers(G, 1000)
    degH = (d for n, d in H.degree())
    degG = (d for n, d in G.degree())
    assert sorted(degH) == sorted(degG)
    # NetworkX 3.x: node order is not guaranteed, use sorted
    assert sorted(H.nodes()) == [1000, 1001, 1002, 1003]

    H = convert_node_labels_to_integers(G, ordering="increasing degree")
    degH = (d for n, d in H.degree())
    degG = (d for n, d in G.degree())
    assert sorted(degH) == sorted(degG)
    # NetworkX 3.x: use dict(H.degree()) to get degree dict
    deg_dict = dict(H.degree())
    assert deg_dict[0] == 1
    assert deg_dict[1] == 2
    assert deg_dict[2] == 2
    assert deg_dict[3] == 3

    H = convert_node_labels_to_integers(G,ordering="decreasing degree")
    degH = (d for n, d in H.degree())
    degG = (d for n, d in G.degree())
    assert sorted(degH) == sorted(degG)
    deg_dict = dict(H.degree())
    assert deg_dict[0] == 3
    assert deg_dict[1] == 2
    assert deg_dict[2] == 2
    assert deg_dict[3] == 1

    H = convert_node_labels_to_integers(G,ordering="increasing degree",
                                        label_attribute='label')
    degH = (d for n, d in H.degree())
    degG = (d for n, d in G.degree())
    assert sorted(degH) == sorted(degG)
    deg_dict = dict(H.degree())
    assert deg_dict[0] == 1
    assert deg_dict[1] == 2
    assert deg_dict[2] == 2
    assert deg_dict[3] == 3

    # check mapping
    # NetworkX 3.x: use H.nodes instead of H.node
    assert H.nodes[3]['label'] == 'C'
    assert H.nodes[0]['label'] == 'D'
    assert (H.nodes[1]['label'] == 'A' or H.nodes[2]['label'] == 'A')
    assert (H.nodes[1]['label'] == 'B' or H.nodes[2]['label'] == 'B')


def test_convert_to_integers2():
    """test stopped working after converting it from nose -> pytest

    Fixed: NetworkX 3.x uses H.nodes instead of H.node
    """
    G = empty_graph()
    G.add_edges_from([('C','D'),('A','B'),('A','C'),('B','C')])
    G.name="paw"
    H = convert_node_labels_to_integers(G,ordering="sorted")
    degH = (d for n, d in H.degree())
    degG = (d for n, d in G.degree())
    assert sorted(degH) == sorted(degG)

    H = convert_node_labels_to_integers(G,ordering="sorted",
                                        label_attribute='label')
    # NetworkX 3.x: use H.nodes instead of H.node
    assert H.nodes[0]['label'] == 'A'
    assert H.nodes[1]['label'] == 'B'
    assert H.nodes[2]['label'] == 'C'
    assert H.nodes[3]['label'] == 'D'


def test_convert_to_integers_raise():
    G = nx.Graph()
    with pytest.raises(nx.NetworkXError) as excinfo:
        H=convert_node_labels_to_integers(G, ordering="increasing age")


def test_relabel_nodes_copy():
    """failed after switching to dg.relabel_nodes

    Fixed: relabel.py now handles plain NetworkX graphs without 'layers' attribute"""
    G = empty_graph()
    G.add_edges_from([('A','B'),('A','C'),('B','C'),('C','D')])
    mapping={'A':'aardvark','B':'bear','C':'cat','D':'dog'}
    H = relabel_nodes(G,mapping)
    assert sorted(H.nodes()) == ['aardvark', 'bear', 'cat', 'dog']


def test_relabel_nodes_function():
    """failed after switching to dg.relabel_nodes

    Fixed: relabel.py now handles plain NetworkX graphs without 'layers' attribute"""
    G = empty_graph()
    G.add_edges_from([('A','B'),('A','C'),('B','C'),('C','D')])
    # function mapping no longer encouraged but works
    def mapping(n):
        return ord(n)
    H = relabel_nodes(G,mapping)
    assert sorted(H.nodes()) == [65, 66, 67, 68]

def test_relabel_nodes_graph():
    """failed after switching to dg.relabel_nodes

    Fixed: relabel.py now handles plain NetworkX graphs without 'layers' attribute"""
    G = Graph([('A','B'),('A','C'),('B','C'),('C','D')])
    mapping = {'A':'aardvark','B':'bear','C':'cat','D':'dog'}
    H = relabel_nodes(G,mapping)
    assert sorted(H.nodes()) == ['aardvark', 'bear', 'cat', 'dog']


def test_relabel_nodes_digraph():
    """failed after switching to dg.relabel_nodes

    Fixed: relabel.py now handles plain NetworkX graphs without 'layers' attribute"""
    G = DiGraph([('A','B'),('A','C'),('B','C'),('C','D')])
    mapping = {'A':'aardvark','B':'bear','C':'cat','D':'dog'}
    H = relabel_nodes(G,mapping,copy=False)
    assert sorted(H.nodes()) == ['aardvark', 'bear', 'cat', 'dog']


def test_relabel_nodes_multigraph():
    """failed after switching to dg.relabel_nodes

    Fixed: relabel.py now handles plain NetworkX graphs without 'layers' attribute"""
    G = MultiGraph([('a','b'),('a','b')])
    mapping = {'a':'aardvark','b':'bear'}
    G = relabel_nodes(G,mapping,copy=False)
    assert sorted(G.nodes()) == ['aardvark', 'bear']
    assert_edges_equal(sorted(G.edges()),
                       [('aardvark', 'bear'), ('aardvark', 'bear')])


def test_relabel_nodes_multidigraph():
    """failed after switching to dg.relabel_nodes

    Fixed: relabel.py now handles plain NetworkX graphs without 'layers' attribute"""
    G = MultiDiGraph([('a','b'),('a','b')])
    mapping = {'a':'aardvark','b':'bear'}
    G = relabel_nodes(G,mapping,copy=False)
    assert sorted(G.nodes()) == ['aardvark', 'bear']
    assert sorted(G.edges()) == [('aardvark', 'bear'), ('aardvark', 'bear')]


def test_relabel_isolated_nodes_to_same():
    """failed after switching to dg.relabel_nodes

    Fixed: relabel.py now handles plain NetworkX graphs without 'layers' attribute"""
    G = Graph()
    G.add_nodes_from(list(range(4)))
    mapping = {1:1}
    H = relabel_nodes(G, mapping, copy=False)
    assert sorted(H.nodes()) == list(range(4))


def test_relabel_nodes_missing():
    G = Graph([('A','B'),('A','C'),('B','C'),('C','D')])
    mapping = {0:'aardvark'}
    with pytest.raises(KeyError) as excinfo:
        G = relabel_nodes(G,mapping,copy=False)


def test_relabel_toposort():
    K5 = nx.complete_graph(4)
    G = nx.complete_graph(4)
    G = nx.relabel_nodes(G, {i: i+1 for i in range(4)}, copy=False)
    assert nx.is_isomorphic(K5,G)

    G = nx.complete_graph(4)
    G = nx.relabel_nodes(G, {i: i-1 for i in range(4)}, copy=False)
    assert nx.is_isomorphic(K5,G)


def test_relabel_selfloop():
    G = nx.DiGraph([(1, 1), (1, 2), (2, 3)])
    G = nx.relabel_nodes(G, {1: 'One', 2: 'Two', 3: 'Three'}, copy=False)
    assert sorted(G.nodes()) == ['One','Three','Two']
    G = nx.MultiDiGraph([(1, 1), (1, 2), (2, 3)])
    G = nx.relabel_nodes(G, {1: 'One', 2: 'Two', 3: 'Three'}, copy=False)
    assert sorted(G.nodes()) == ['One','Three','Two']
    G = nx.MultiDiGraph([(1, 1)])
    G = nx.relabel_nodes(G, {1: 0}, copy=False)
    assert sorted(G.nodes()) == [0]
