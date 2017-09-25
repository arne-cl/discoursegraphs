#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from copy import deepcopy
import os

from networkx import is_directed_acyclic_graph
import pytest

import discoursegraphs as dg
from discoursegraphs.discoursegraph import create_token_mapping, get_kwic
from discoursegraphs.corpora import pcc

"""
This module contains some tests for the ``discoursegraph`` module.
"""

DOC_ID = 'maz-10374'


def add_tokens(docgraph, tokens):
    """add tokens (list of str) to a document graph"""
    for token in tokens:
        node_id = len(docgraph.tokens)
        while node_id in docgraph.tokens:
            node_id += 1

        docgraph.add_node(
            node_id, layers={docgraph.ns, docgraph.ns+':token'},
            attr_dict={docgraph.ns+':token': token})
        docgraph.tokens.append(node_id)


class TestDiscourseDocumentGraph(object):
    """create and manipulate document graphs"""
    def setup(self):
        """create an empty DiscourseDocumentGraph"""
        self.docgraph = dg.DiscourseDocumentGraph()
        assert isinstance(self.docgraph, dg.DiscourseDocumentGraph)
        assert self.docgraph.name == ''
        assert self.docgraph.nodes() == ['discoursegraph:root_node']

    @staticmethod
    def test_docgraph_name_namespace():
        """create a docgraph with a user-defined name and namespace"""
        name = 'mydoc'
        ns = 'weird'
        ddg = dg.DiscourseDocumentGraph(name=name, namespace=ns)
        assert isinstance(ddg, dg.DiscourseDocumentGraph)
        assert ddg.name == name
        assert ddg.nodes() == ['{}:root_node'.format(ns)]

    def test_add_node(self):
        """add nodes to the graph, with and without layers"""
        # add node without any additional attributes / layers
        self.docgraph.add_node(1)
        assert len(self.docgraph.node) == 2
        assert self.docgraph.node[1] == {'layers': {'discoursegraph'}}

        # add nodes with additional layer(s)
        self.docgraph.add_node(2, layers={'foo'})
        assert len(self.docgraph.node) == 3
        assert self.docgraph.node[2] == {'layers': {'foo'}}

        self.docgraph.add_node(3, layers={'foo', 'bar'})
        assert len(self.docgraph.node) == 4
        assert self.docgraph.node[3] == {'layers': {'foo', 'bar'}}

        self.docgraph.add_node(4, layers={self.docgraph.ns, 'foo', 'bar'})
        assert len(self.docgraph.node) == 5
        assert self.docgraph.node[4] == \
            {'layers': {'discoursegraph', 'foo', 'bar'}}

        # re-add an already existing node with different layer(s)
        # this will simply add the new layers to the existing set
        self.docgraph.add_node(4, layers={'bla'})
        assert len(self.docgraph.node) == 5
        assert self.docgraph.node[4] == \
            {'layers': {'discoursegraph', 'foo', 'bar', 'bla'}}

        self.docgraph.add_node(4, layers={'xyz', 'abc'})
        assert len(self.docgraph.node) == 5
        assert self.docgraph.node[4] == \
            {'layers': {'discoursegraph', 'foo', 'bar', 'bla', 'xyz', 'abc'}}

        # try to add node with bad layers
        # 'layers' must be a set of str
        with pytest.raises(AssertionError) as excinfo:
            self.docgraph.add_node(666, layers='foo')
        with pytest.raises(AssertionError) as excinfo:
            self.docgraph.add_node(666, layers=['foo'])
        with pytest.raises(AssertionError) as excinfo:
            self.docgraph.add_node(666, layers={23})
        with pytest.raises(AssertionError) as excinfo:
            self.docgraph.add_node(666, layers={'foo', 23})

    def test_add_node_with_attributes(self):
        """add nodes to the graph, with and without attributes"""
        # add node without attributes
        self.docgraph.add_node(1, attr_dict=None)
        assert len(self.docgraph.node) == 2
        assert self.docgraph.node[1] == {'layers': {'discoursegraph'}}

        # add node with attributes
        self.docgraph.add_node(2, attr_dict={'cat': 'NP'})
        assert len(self.docgraph.node) == 3
        assert self.docgraph.node[2] == \
            {'layers': {'discoursegraph'},
             'cat': 'NP'}

        self.docgraph.add_node(3, attr_dict={'cat': 'NP', 'lemma': 'dog'})
        assert len(self.docgraph.node) == 4
        assert self.docgraph.node[3] == \
            {'layers': {'discoursegraph'},
             'cat': 'NP', 'lemma': 'dog'}

        # overwrite attribute of existing node
        self.docgraph.add_node(2, attr_dict={'cat': 'N'})
        assert len(self.docgraph.node) == 4
        assert self.docgraph.node[2] == \
            {'layers': {'discoursegraph'},
             'cat': 'N'}

        # overwrite attribute of existing node add additional attrib
        self.docgraph.add_node(2, attr_dict={'cat': 'NP', 'score': 0.5})
        assert len(self.docgraph.node) == 4
        assert self.docgraph.node[2] == \
            {'layers': {'discoursegraph'},
             'cat': 'NP', 'score': 0.5}

        # try to add node with bad attributes
        # 'attr_dict' must be a dict
        with pytest.raises(AssertionError) as excinfo:
            self.docgraph.add_node(666, attr_dict='foo')
        with pytest.raises(AssertionError) as excinfo:
            self.docgraph.add_node(666, attr_dict=['foo'])
        with pytest.raises(AssertionError) as excinfo:
            #~ import pudb; pudb.set_trace()
            self.docgraph.add_node(666, attr_dict={23})
        with pytest.raises(AssertionError) as excinfo:
            self.docgraph.add_node(666, attr_dict={'foo', 23})

    def test_add_nodes_from(self):
        """add multiple nodes at once"""
        assert len(self.docgraph.node) == 1  # the root node is already present

        # add nodes without layers / attributes
        self.docgraph.add_nodes_from(range(5))
        assert len(self.docgraph.node) == 6

        for node_id in range(5):
            assert self.docgraph.node[node_id] == {'layers': {'discoursegraph'}}

        # re-add nodes with an additional layer
        self.docgraph.add_nodes_from([(0, {'layers':{'foo'}}), (1, {'layers':{'bar'}})])
        assert self.docgraph.node[0] == \
                {'layers': {'discoursegraph', 'foo'}}
        assert self.docgraph.node[1] == \
                {'layers': {'discoursegraph', 'bar'}}

    @pytest.mark.xfail
    def test_add_nodes_from_fail(self):
        """this is an implementation error. layers should never be overwritten,
        only appended."""
        self.docgraph.add_nodes_from((0,1))
        # re-add nodes with an additional layer
        self.docgraph.add_nodes_from((0,1), layers={'foo'})

        for node_id in (0,1):
            assert self.docgraph.node[node_id] == \
                {'layers': {'discoursegraph', 'foo'}}

    def test_add_edge(self):
        self.docgraph.add_nodes_from(
            [(1, {'layers':{'token'}, 'word':'hello'}),
             (2, {'layers':{'token'}, 'word':'world'})])

        assert self.docgraph.edges(data=True) == []

        # in a multi-digraph, we can have multiple edges between nodes
        self.docgraph.add_edge(1, 2, layers={'generic'})
        self.docgraph.add_edge(1, 2, layers={'tokens'}, weight=0.7)

        assert self.docgraph.edges(data=True) == \
            [(1, 2, {'layers': {'generic'}}),
             (1, 2, {'layers': {'tokens'}, 'weight': 0.7})]

        # there are two edges between the nodes 1 and 2
        # this will update only the 'weight' attribute of the second one (key=1)
        self.docgraph.add_edge(1, 2, layers={'tokens'}, key=1, weight=1.0)
        assert self.docgraph.edges(data=True) == \
            [(1, 2, {'layers': {'generic'}}),
             (1, 2, {'layers': {'tokens'}, 'weight': 1.0})]

        # add an additional layer to the second multiedge
        self.docgraph.add_edge(1, 2, layers={'foo'}, key=1)
        assert self.docgraph.edges(data=True) == \
            [(1, 2, {'layers': {'generic'}}),
             (1, 2, {'layers': {'foo', 'tokens'}, 'weight': 1.0})]

        with pytest.raises(AttributeError) as excinfo:
            # 'attr_dict' must be a dict
            self.docgraph.add_edge(1, 2, attr_dict='bar')

    def test_add_edges_from(self):
        """add multiple edges at once"""
        # multiple edges between the same nodes
        self.docgraph.add_edges_from(
            [(1, 2, {'layers': {'int'}, 'weight': 23}),
             (1, 2, {'layers': {'int'}, 'weight': 42})])
        assert self.docgraph.edges(data=True) == \
            [(1, 2, {'layers': {'int'}, 'weight': 23}),
             (1, 2, {'layers': {'int'}, 'weight': 42})]

        # update the first edge (key=0), overwrite its 'weigth'
        # the 'layers' value is not overwritten, but appended
        self.docgraph.add_edges_from([(1, 2, 0, {'layers':{'number'}, 'weight':66})])
        assert self.docgraph.edges(data=True) == \
            [(1, 2, {'layers': {'int', 'number'}, 'weight': 66}),
             (1, 2, {'layers': {'int'}, 'weight': 42})]

        # this combines attributes given in the edge-specific ebunch and
        # the attr_dict, which applies to all edges fed to this method
        # call
        self.docgraph.add_edges_from(
            ebunch=[(3, 4, {'layers': {'ptb'}})],
            attr_dict={'score': 0.5})
        assert self.docgraph[3][4] == {0: {'layers': {'ptb'}, 'score': 0.5}}

        self.docgraph.add_edges_from(
            ebunch=[(4, 5, {'layers': {'ptb'}})],
            attr_dict={'score': 0.5, 'layers': {'fake'}})
        assert self.docgraph[4][5] == {0: {'layers': {'fake', 'ptb'}, 'score': 0.5}}


        # ebunch must be a (u, v, attribs) or (u, v, key, attribs) tuple
        with pytest.raises(AttributeError) as excinfo:
            self.docgraph.add_edges_from(ebunch=[(1, 2)])
        with pytest.raises(AttributeError) as excinfo:
            self.docgraph.add_edges_from(ebunch=[(1, 2)], attr_dict='bogus')

        # attr_dict must be a dict
        with pytest.raises(AttributeError) as excinfo:
            self.docgraph.add_edges_from(
                ebunch=[(1, 2, {'layers': {'ptb'}})],
                attr_dict='bogus')

        # (u, v, attribs): attribs must be a dict
        with pytest.raises(TypeError) as excinfo:
            self.docgraph.add_edges_from([(1, 2, 'bar')])

    def test_add_layer(self):
        """add a layer to existing nodes or edges"""
        self.docgraph.add_node(1)
        self.docgraph.add_layer(1, 'fake')
        assert self.docgraph.node[1] == {'layers': {'discoursegraph', 'fake'}}

        self.docgraph.add_edge(1, 2)
        self.docgraph.add_layer((1, 2), 'fake')
        assert self.docgraph[1][2] == {0: {'layers': {'discoursegraph', 'fake'}}}

    def test_add_offsets_get_offsets(self):
        """annotate tokens with offsets and retrieve them."""
        # add a few tokens to the docgraph
        add_tokens(self.docgraph, ['Ich', 'bin', 'ein', 'Berliner', '.'])
        assert len(self.docgraph.tokens) == 5

        # get_offsets() will trigger add_offsets() on first run
        self.docgraph.get_offsets()

        assert self.docgraph.get_offsets(0) == (0, 3)
        assert self.docgraph.get_offsets(1) == (4, 7)
        assert self.docgraph.get_offsets(2) == (8, 11)
        assert self.docgraph.get_offsets(3) == (12, 20)
        assert self.docgraph.get_offsets(4) == (21, 22)
        assert list(self.docgraph.get_offsets()) == \
            [(0, 0, 3), (1, 4, 7), (2, 8, 11), (3, 12, 20), (4, 21, 22)]

        # adding the offsets again (with the default namespace) must not
        # change anything
        nodes_dict = deepcopy(self.docgraph.node)
        self.docgraph.add_offsets()
        assert self.docgraph.node == nodes_dict

    @staticmethod
    def test_get_phrases():
        """extract all VPs from a document"""
        ptb_filepath = os.path.join(dg.DATA_ROOT_DIR, 'ptb-example.mrg')
        #~ import pudb; pudb.set_trace()
        pdg = dg.read_ptb(ptb_filepath)
        list(pdg.get_phrases(cat_val='PP'))

        verb_phrase_node_ids = list(pdg.get_phrases(cat_val='VP'))
        assert verb_phrase_node_ids == [6, 67, 68, 71, 124, 138, 206]
        assert dg.get_text(pdg, 206) == \
            'aligns with anarcho-syndicalism and libertarian socialism'

    def test_get_tokens(self):
        # add a few tokens to the docgraph
        add_tokens(self.docgraph, ['dogs', 'bite'])
        assert list(self.docgraph.get_tokens()) == [(0, 'dogs'), (1, 'bite')]
        assert list(self.docgraph.get_tokens(token_strings_only=True)) == ['dogs', 'bite']

    def test_merge_graphs(self):
        """merge a very simple graph into an empty graph"""
        # create a simple graph with 3 tokens, all dominated by the root node
        token_graph = dg.DiscourseDocumentGraph(
            name='example.tok', namespace='tokenized')
        add_tokens(token_graph, ['He', 'sleeps', '.'])
        for token_node in token_graph.tokens:
            token_graph.add_edge(token_graph.root, token_node,
                                 edge_type=dg.EdgeTypes.dominance_relation)
        assert len(token_graph) == 4
        assert len(token_graph.edges()) == 3

        assert self.docgraph.name == ''
        assert self.docgraph.tokens == []
        assert len(self.docgraph) == 1
        self.docgraph.merge_graphs(token_graph)

        assert self.docgraph.name == 'example.tok'
        assert len(self.docgraph.tokens) == 3
        assert len(self.docgraph) == 4
        assert len(token_graph.edges()) == 3


def test_get_kwic():
    """keyword in context"""
    tokens = ['Ich', 'bin', 'ein', 'Berliner', '.']
    assert get_kwic(tokens, 2, context_window=0) == \
        ([], 'ein', [])
    assert get_kwic(tokens, 2, context_window=1) == \
        (['bin'], 'ein', ['Berliner'])
    assert get_kwic(tokens, 2, context_window=2) == \
        (['Ich', 'bin'], 'ein', ['Berliner', '.'])
    assert get_kwic(tokens, 1, context_window=2) == \
        (['Ich'], 'bin', ['ein', 'Berliner'])
    assert get_kwic(tokens, 2, context_window=3) == \
        (['Ich', 'bin'], 'ein', ['Berliner', '.'])


def test_create_token_mapping():
    """check if two docgraphs cover the same text with the same tokenization"""
    # merging must fail when tokens aren't identical
    first_graph = dg.DiscourseDocumentGraph(name='first')
    add_tokens(first_graph, ['Ich', 'bin', 'ein', 'Berliner', '.'])

    second_graph = dg.DiscourseDocumentGraph(name='second')
    add_tokens(second_graph, ['Ich', 'bin', 'kein', 'Berliner', '.'])

    with pytest.raises(ValueError) as excinfo:
        create_token_mapping(first_graph, second_graph, verbose=False)
    assert 'Tokenization mismatch' in str(excinfo.value)
    assert 'kein != ein' in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        create_token_mapping(first_graph, second_graph, verbose=True)
    assert 'Tokenization mismatch' in str(excinfo.value)
    assert 'Ich bin [[ein]] Berliner .' in str(excinfo.value)
    assert 'Ich bin [[kein]] Berliner .' in str(excinfo.value)


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


def test_select_nodes_by_attribute():
    """Are node lists are correctly filtered based on their attribs/values?"""
    pdg = pcc[DOC_ID]

    # don't filter any nodes
    all_node_ids = list(dg.select_nodes_by_attribute(pdg))
    assert len(pdg) == len(pdg.nodes()) == len(all_node_ids) == 342
    all_nodes = list(dg.select_nodes_by_attribute(pdg, data=True))
    assert len(all_node_ids) == len(all_nodes)

    # select all tokens
    all_token_ids = list(
        dg.select_nodes_by_attribute(pdg, attribute='tiger:token'))
    assert len(pdg.tokens) == len(all_token_ids) == 174
    all_tokens = list(
        dg.select_nodes_by_attribute(pdg, attribute='tiger:token', data=True))
    assert len(all_token_ids) == len(all_tokens)

    # select all occurences of the lemma 'mit'
    mit_token_ids = list(dg.select_nodes_by_attribute(
        pdg, attribute='tiger:lemma', value='mit'))
    assert len(mit_token_ids) == 3
    mit_tokens = list(dg.select_nodes_by_attribute(
        pdg, attribute='tiger:lemma', value='mit', data=True))
    assert len(mit_token_ids) == len(mit_tokens)

    # select all nodes, whose lemma is either 'mit' or 'und'
    mitund_token_ids = list(dg.select_nodes_by_attribute(
        pdg, attribute='tiger:lemma', value=['mit', 'und']))
    assert len(mitund_token_ids) == 6
    mitund_tokens = list(dg.select_nodes_by_attribute(
        pdg, attribute='tiger:lemma', value={'mit', 'und'}, data=True))
    assert len(mitund_token_ids) == len(mitund_tokens)

    # does the data parameter work with all other parameter settings
    for list_of_nodes in (all_nodes, all_tokens, mit_tokens, mitund_tokens):
        for node_id, attr_dict in list_of_nodes:
            assert isinstance(node_id, (str, int))
            assert isinstance(attr_dict, dict)


def test_select_nodes_by_layer():
    """Are nodes correctly filtered based on their layer?"""
    ddg = dg.DiscourseDocumentGraph(namespace='test')
    assert len(ddg) == 1
    add_tokens(ddg, ['The', 'dog', 'barks', '.'])
    assert len(ddg) == 5

    # don't filter any nodes
    all_node_ids = list(dg.select_nodes_by_layer(ddg))
    all_nodes = list(dg.select_nodes_by_layer(ddg, data=True))
    assert len(all_node_ids) == len(all_nodes) == 5

    test_node_ids = list(dg.select_nodes_by_layer(ddg, 'test'))
    test_nodes = list(dg.select_nodes_by_layer(ddg, 'test', data=True))
    assert len(ddg) == len(test_node_ids) == len(test_nodes) == 5

    ddg.add_node(10, layers={'foo'})
    ddg.add_node(11, layers={'bar'})

    # filter several layers
    test_foo_ids = list(dg.select_nodes_by_layer(ddg, layer={'test', 'foo'}))
    test_foo_nodes = list(dg.select_nodes_by_layer(
        ddg, layer={'test', 'foo'}, data=True))
    assert len(test_foo_ids) == len(test_foo_nodes) == 6
    test_foobar_ids = list(dg.select_nodes_by_layer(
        ddg, layer={'test', 'foo', 'bar'}))
    assert len(test_foobar_ids) == 7

    # test if data=True works as expected
    for nodelist in (all_nodes, test_nodes, test_foo_nodes):
        for node_id, attr_dict in nodelist:
            assert isinstance(node_id, (str, int))
            assert isinstance(attr_dict, dict)


def test_select_edges_by_attribute():
    """test if edges can be filtered for attributes/values"""
    # create a simple graph with 3 tokens, all dominated by the root node
    # and with precedence relations between the tokens
    token_graph = dg.DiscourseDocumentGraph(
        name='example.tok', namespace='tokenized')
    add_tokens(token_graph, ['He', 'sleeps', '.'])
    for token_node in token_graph.tokens:
        token_graph.add_edge(token_graph.root, token_node,
                             edge_type=dg.EdgeTypes.dominance_relation)

    for src, target in [(0, 1), (1, 2)]:
        token_graph.add_edge(
            src, target, edge_type=dg.EdgeTypes.precedence_relation)

    assert len(token_graph) == 4

    all_edge_ids = list(dg.select_edges_by_attribute(token_graph))
    all_edges = list(dg.select_edges_by_attribute(token_graph, data=True))
    assert len(token_graph.edges()) == len(all_edge_ids) == len(all_edges) == 5

    # test if data=True works as expected
    for src, target, attrs in all_edges:
        assert isinstance(src, (str, int))
        assert isinstance(target, (str, int))
        assert isinstance(attrs, dict)

    # edges with any edge_type
    edges_with_edgetype = list(dg.select_edges_by_attribute(
        token_graph, attribute='edge_type'))
    assert len(edges_with_edgetype) == 5

    # edges with dominance relation edge_type
    dominance_edge_ids = list(dg.select_edges_by_attribute(
        token_graph, attribute='edge_type',
        value=dg.EdgeTypes.dominance_relation))
    assert len(dominance_edge_ids) == 3

    # edges with dominance or precedence edge_type
    dominance_or_precendence = list(dg.select_edges_by_attribute(
        token_graph, attribute='edge_type',
        value=[dg.EdgeTypes.dominance_relation,
               dg.EdgeTypes.precedence_relation]))
    assert len(dominance_or_precendence) == 5


def test_select_edges_by():
    """test various combinations of edge filters (layer/edge type)"""
    sg1 = make_sentencegraph1()

    # don't filter any edges
    all_edge_ids = list(dg.select_edges_by(sg1, layer=None, edge_type=None))
    all_edges = list(dg.select_edges_by(sg1, layer=None, edge_type=None, data=True))
    assert len(all_edge_ids) == len(all_edges) == len(sg1.edges()) == 20

    # filter layer, but not edge type
    expected_sytax_edge_ids = {
        (sg1.root, 'S'), ('S', 'NP1'), ('S', 'VP1'), ('S', 'SBAR'),
        ('SBAR', 'NP2'), ('SBAR', 'VP2')}
    syntax_edge_ids = list(dg.select_edges_by(
        sg1, layer=sg1.ns+':syntax', edge_type=None))
    syntax_edges = list(dg.select_edges_by(
        sg1, layer=sg1.ns+':syntax', edge_type=None, data=True))
    assert len(syntax_edge_ids) == len(syntax_edges) == 6
    assert set(syntax_edge_ids) == expected_sytax_edge_ids

    precedence_edge_ids = list(dg.select_edges_by(
        sg1, layer=sg1.ns+':precedence', edge_type=None))
    precedence_edges = list(dg.select_edges_by(
        sg1, layer=sg1.ns+':precedence', edge_type=None, data=True))
    assert len(precedence_edge_ids) == len(precedence_edges) == 7
    assert set(precedence_edge_ids) == {(i, i+1) for i in range(7)}

    # filter layer and edge type
    syndom_edge_ids = list(dg.select_edges_by(
        sg1, layer=sg1.ns+':syntax',
        edge_type=dg.EdgeTypes.dominance_relation))
    syndom_edges = list(dg.select_edges_by(
        sg1, layer=sg1.ns+':syntax',
        edge_type=dg.EdgeTypes.dominance_relation, data=True))
    assert len(syndom_edge_ids) == len(syndom_edges) == 6
    assert set(syndom_edge_ids) == expected_sytax_edge_ids

    # filter edge type, but not layer
    dom_edge_ids = list(dg.select_edges_by(
        sg1, layer=None, edge_type=dg.EdgeTypes.dominance_relation))
    dom_edges = list(dg.select_edges_by(
        sg1, layer=None, edge_type=dg.EdgeTypes.dominance_relation, data=True))
    assert len(dom_edge_ids) == len(dom_edges) == 6
    assert set(dom_edge_ids) == expected_sytax_edge_ids

    # test if data=True works as expected
    edge_lists = (all_edges, syntax_edges, precedence_edges, syndom_edges,
                  dom_edges)
    for edge_list in edge_lists:
        for src, target, attrs in edge_list:
            assert isinstance(src, (str, int))
            assert isinstance(target, (str, int))
            assert isinstance(attrs, dict)


def make_sentencegraph1():
    """return a docgraph containing one sentence with syntax and coreference
    annotation, as well as precedence relations.

    The graph is cyclic because of a coreference relation (pointing relation).
    """
    docgraph = dg.DiscourseDocumentGraph()
    # tokens: 0    1       2    3     4      5       6     7
    add_tokens(docgraph,
        ['Guido', 'died', ',', 'he', 'was', 'only', '54', '.'])

    # add syntax structure (nodes, dominance and spanning relations)
    docgraph.add_node('S', layers={docgraph.ns+':syntax'})
    docgraph.add_node('NP1', layers={docgraph.ns+':syntax'})
    docgraph.add_node('VP1', layers={docgraph.ns+':syntax'})
    docgraph.add_node('SBAR', layers={docgraph.ns+':syntax'})
    docgraph.add_node('NP2', layers={docgraph.ns+':syntax'})
    docgraph.add_node('VP2', layers={docgraph.ns+':syntax'})

    dom_rels = [(docgraph.root, 'S'), ('S', 'NP1'), ('S', 'VP1'),
                ('S', 'SBAR'), ('SBAR', 'NP2'), ('SBAR', 'VP2')]
    for src, target in dom_rels:
        docgraph.add_edge(src, target, layers={docgraph.ns+':syntax'},
                          edge_type=dg.EdgeTypes.dominance_relation)

    span_rels = [('NP1', 0), ('VP1', 1), ('NP2', 3), ('VP2', 4), ('VP2', 5),
                 ('VP2', 6)]
    for src, target in span_rels:
        docgraph.add_edge(src, target,
                          edge_type=dg.EdgeTypes.spanning_relation)

    # coreference: he -> Guido
    docgraph.add_edge(3, 0, layers={docgraph.ns+':coreference'},
                      edge_type=dg.EdgeTypes.pointing_relation)

    # add precedence relations
    prec_rels = [(i, i+1) for i in range(7)]
    for src, target in prec_rels:
        docgraph.add_edge(src, target, layers={docgraph.ns+':precedence'},
                          edge_type=dg.EdgeTypes.pointing_relation)
    return docgraph


def test_get_span():
    """get spans from an sentence graph with dominance, spanning and
    pointing relations, but without self-loops"""
    sg1 = make_sentencegraph1()
    assert is_directed_acyclic_graph(sg1) is False
    assert len(sg1) == 15

    # token nodes only "span" themselves
    for i in range(8):
        assert dg.get_span(sg1, i) == [i]

    # the sentence covers all tokens, except for the markers ',' and '.'
    assert dg.get_span(sg1, 'S') == [0, 1, 3, 4, 5, 6]
    assert dg.get_span(sg1, 'NP1') == [0]
    assert dg.get_span(sg1, 'VP1') == [1]
    assert dg.get_span(sg1, 'SBAR') == [3, 4, 5, 6]
    assert dg.get_span(sg1, 'NP2') == [3]
    assert dg.get_span(sg1, 'VP2') == [4, 5, 6]

    # the debug parameter should 'raise' a warning (since the graph is
    # cyclic), but the result must be the same)
    assert dg.get_span(sg1, 'S', debug=True) == [0, 1, 3, 4, 5, 6]

    # get_span() must be robust against self-loops
    sg1.add_edge('SBAR', 'SBAR', layers={sg1.ns+':selfloop'},
                 edge_type=dg.EdgeTypes.dominance_relation)
    assert dg.get_span(sg1, 'S') == [0, 1, 3, 4, 5, 6]
    assert dg.get_span(sg1, 'SBAR') == [3, 4, 5, 6]
    assert dg.get_span(sg1, 'SBAR', debug=True) == [3, 4, 5, 6]

    # get_span() won't be able to recover from a dominance relation
    # (non self)-loop
    sg1.add_edge('NP1', 'S', layers={sg1.ns+':loop'},
                 edge_type=dg.EdgeTypes.dominance_relation)
    with pytest.raises(RuntimeError) as excinfo:
        assert dg.get_span(sg1, 'S')


def test_get_span_offsets():
    """test, if offsets can be retrieved from tokens, spans of tokens or
    dominating nodes.
    """
    sg1 = make_sentencegraph1()

    sg1_offsets = \
    [
        [0, (0, 5)],
        [1, (6, 10)],
        [2, (11, 12)],
        [3, (13, 15)],
        [4, (16, 19)],
        [5, (20, 24)],
        [6, (25, 27)],
        [7, (28, 29)],
        ['S', (0, 27)],
        ['NP1', (0, 5)],
        ['VP1', (6, 10)],
        ['SBAR', (13, 27)],
        ['NP2', (13, 15)],
        ['VP2', (16, 27)]
    ]

    for token_node_id, (onset, offset) in sg1_offsets:
        assert dg.get_span_offsets(sg1, token_node_id) == (onset, offset)

    with pytest.raises(KeyError) as excinfo:
        offsets = dg.get_span_offsets(sg1, 'foo')
    assert "doesn't span any tokens" in excinfo.value.message


def test_multiedge_keyincrement():
    """test, if keys are automatically incremented when adding multiple edges
    between two nodes. This tests redundant code common to add_edge() and
    add_edges_from().
    """
    dg1 = dg.DiscourseDocumentGraph()

    # add an edge with a key. keys are used in multigraphs to distinguish
    # between multiple edges between the same nodes
    dg1.add_edge('a', 'b', layers={'love'}, key=1)
    assert len(dg1.edge['a']['b']) == 1
    # add another edge between the same nodes.
    # keys should auto-increment, especially if the key is already in use
    dg1.add_edge('a', 'b', layers={'hate'})
    assert len(dg1.edge['a']['b']) == 2
    assert 'love' in dg1.edge['a']['b'][1]['layers']
    assert 'hate' in dg1.edge['a']['b'][2]['layers']

    # the method add_edges_from should show the same behaviour
    dg2 = dg.DiscourseDocumentGraph()
    dg2.add_edges_from([('a', 'b', 1, {'layers': {'love'}})])
    assert len(dg2.edge['a']['b']) == 1
    dg2.add_edges_from([('a', 'b', {'layers': {'hate'}})])
    assert len(dg2.edge['a']['b']) == 2
    assert 'love' in dg2.edge['a']['b'][1]['layers']
    assert 'hate' in dg2.edge['a']['b'][2]['layers']


def test_select_neighbors_by_layer():
    """test, if we can find nodes connected via outgoing edges, which belong
    to the given layer(s).
    """
    sg1 = make_sentencegraph1()
    # [(0, 'Guido'), (1, 'died'), (2, ','), (3, 'he'), (4, 'was'),
    #  (5, 'only'), (6, '54'), (7, '.')]
    for punct_token in (2, 7):
        sg1.add_edge('S', punct_token, layers={'unconnected'},
                     edge_type=dg.EdgeTypes.dominance_relation)

    unconnected_tokens = list(dg.select_neighbors_by_layer(
        sg1, 'S', layer=sg1.ns+':token'))
    assert unconnected_tokens == [2, 7]

    cat_nodes = list(dg.select_neighbors_by_layer(
        sg1, 'S', layer=sg1.ns+':syntax'))
    # there's no explicit node order, so we'll have to resort to sets
    assert set(cat_nodes) == {'NP1', 'VP1', 'SBAR'}

    # find all neighbors within the syntax or the token layer
    all_neighbors = list(dg.select_neighbors_by_layer(
        sg1, 'S', layer={sg1.ns+':syntax', sg1.ns+':token'}))
    assert set(all_neighbors) == {'NP1', 'VP1', 'SBAR', 2, 7}

    assert list(dg.select_neighbors_by_layer(
        sg1, 'VP1', layer=sg1.ns+':token')) == [1] # via dominance
    assert list(dg.select_neighbors_by_layer(
        sg1, 0, layer=sg1.ns+':token')) == [1] # via precedence
    assert list(dg.select_neighbors_by_layer(
        sg1, 3, layer=sg1.ns+':token')) == [0, 4] # 3->0 coref, 3->4 precedence
