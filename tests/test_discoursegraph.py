#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from copy import deepcopy
import os

import pytest

import discoursegraphs as dg
from discoursegraphs.discoursegraph import create_token_mapping, get_kwic

"""
This module contains some tests for the ``discoursegraph`` module.
"""

def add_tokens(docgraph, tokens):
    """add tokens (list of str) to a document graph"""
    for token in tokens:
        node_id = len(docgraph.tokens)
        while node_id in docgraph.tokens:
            node_id += 1

        docgraph.add_node(
            node_id, layers={docgraph.ns+':token'},
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

    def test_docgraph_name_namespace(self):
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
        with pytest.raises(AssertionError) as excinfo:
            self.docgraph.add_edges_from([(1, 2, 'bar')])

        # (u, v, attribs): attribs must contain a 'layers' key
        with pytest.raises(AssertionError) as excinfo:
            self.docgraph.add_edges_from([(1, 2, {'score': 0.5})])

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

    def test_get_phrases(self):
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
