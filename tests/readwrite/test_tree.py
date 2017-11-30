#!/usr/bin/env python
# coding: utf-8
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from lxml import etree

from discoursegraphs.readwrite.exportxml import ExportXMLDocumentGraph
from discoursegraphs.readwrite.tree import (debug_root_label,
    DGParentedTree, get_child_nodes, horizontal_positions, node2bracket,
    sorted_bfs_edges, sorted_bfs_successors, t, tree2bracket)
import discoursegraphs as dg


text0_str = """
<text xml:id="text_0" origin="foo-corpus">
 <sentence xml:id="s1">
  <node xml:id="s1_505" cat="SIMPX" func="--">
   <node xml:id="s1_501" cat="LK" func="-" parent="s1_505">
    <node xml:id="s1_500" cat="VXFIN" func="HD" parent="s1_501">
     <word xml:id="s1_1" form="Verschlampte" pos="VVFIN" morph="3sit" lemma="verschlampen" func="HD" parent="s1_500" deprel="ROOT"/>
    </node>
   </node>
   <node xml:id="s1_504" cat="MF" func="-" parent="s1_505">
    <node xml:id="s1_502" cat="NX" func="ON" parent="s1_504">
     <word xml:id="s1_2" form="die" pos="ART" morph="nsf" lemma="die" func="-" parent="s1_502" dephead="s1_3" deprel="DET"/>
     <ne xml:id="ne_2" type="ORG">
      <word xml:id="s1_3" form="AFD" pos="NN" morph="nsf" lemma="AFD" func="HD" parent="s1_502" dephead="s1_1" deprel="SUBJ"/>
     </ne>
    </node>
    <node xml:id="s1_503" cat="NX" func="OA" parent="s1_504">
     <word xml:id="s1_4" form="Spendengeld" pos="NN" morph="asn" lemma="Spendengeld" func="HD" parent="s1_503" dephead="s1_1" deprel="OBJA"/>
    </node>
   </node>
  </node>
  <word xml:id="s1_5" form="?" pos="$." lemma="?" func="--" deprel="ROOT"/>
 </sentence>
</text>
"""


class TestTree(object):
    """Tests for PTB-style export"""
    def setup_class(cls):
        """parse the text string into an ExportXML docgraph"""
        cls.tree = etree.fromstring(text0_str)
        cls.docgraph = ExportXMLDocumentGraph(cls.tree)

    def test_get_child_nodes(self):
        """Interpreting a graph as a tree, we find all children of a node."""
        assert self.docgraph.root == 'text_0'
        child_nodes_1 = set(get_child_nodes(self.docgraph, 's1', data=False))
        assert child_nodes_1 == {'s1_505', 's1_5'}

        # child nodes with attributes
        child_nodes_503 = list(get_child_nodes(self.docgraph, 's1_503', data=True))
        assert child_nodes_503 == [
            ('s1_4', {
                'exportxml:form': 'Spendengeld',
                'exportxml:pos': 'NN',
                'exportxml:morph': 'asn',
                'exportxml:lemma': 'Spendengeld',
                'exportxml:func': 'HD',
                'exportxml:parent': 's1_503',
                'exportxml:dephead': 's1_1',
                'exportxml:deprel': 'OBJA',
                'exportxml:token': 'Spendengeld',
                'label': 'Spendengeld',
                'layers': set(['exportxml', 'exportxml:token'])})]

        # tokens don't have children
        for parent_node in ('s1_1', 's1_2', 's1_3', 's1_4', 's1_5'):
            assert not set(get_child_nodes(self.docgraph, parent_node, data=True))

    def test_horizontal_positions(self):
        """Interpreting a graph as a tree, we can order the nodes on the x-axis."""
        x_positions = horizontal_positions(self.docgraph, sentence_root=None)
        expected_positions = {
            's1': 0,
            's1_505': 0, 's1_5': 4,
            's1_501': 0, 's1_504': 1,
            's1_500': 0, 's1_502': 1, 's1_503': 3,
            's1_1': 0, 's1_2': 1, 's1_3': 2, 's1_4': 3}
        assert x_positions == expected_positions

        x_positions_s1 = horizontal_positions(self.docgraph, sentence_root='s1')
        assert x_positions_s1 == expected_positions

    def test_sorted_bfs_edges(self):
        """Interpreting a graph as an ordered rooted tree, we find all
        its edges in BFS order.
        """
        bfs_edges = list(sorted_bfs_edges(self.docgraph, source=None))
        expected_edges = [
            ('text_0', 's1'),
            ('s1', 's1_505'), ('s1', 's1_5'),
            ('s1_505', 's1_501'), ('s1_505', 's1_504'),
            ('s1_501', 's1_500'),
            ('s1_504', 's1_502'), ('s1_504', 's1_503'),
            ('s1_500', 's1_1'),
            ('s1_502', 's1_2'), ('s1_502', 's1_3'),
            ('s1_503', 's1_4')]
        assert bfs_edges == expected_edges

        bfs_edges_no_root = list(sorted_bfs_edges(self.docgraph, source='s1'))
        assert bfs_edges_no_root == expected_edges[1:]

    def test_sorted_bfs_successors(self):
        """Interpreting a graph as a tree, we find the children of each node."""
        root_successors = sorted_bfs_successors(self.docgraph, source=None)
        expected_successors = {
            'text_0': ['s1'],
            's1': ['s1_505', 's1_5'],
            's1_505': ['s1_501', 's1_504'],
            's1_501': ['s1_500'],
            's1_504': ['s1_502', 's1_503'],
            's1_500': ['s1_1'],
            's1_502': ['s1_2', 's1_3'],
            's1_503': ['s1_4']}
        assert root_successors == expected_successors

        s1_successors = sorted_bfs_successors(self.docgraph, source='s1')
        expected_successors.pop('text_0')
        assert s1_successors == expected_successors

    @staticmethod
    def test_node2bracket():
        """A docgraph node can be converted into PTB-style bracket notation."""
        ddg = dg.DiscourseDocumentGraph()
        ns = ddg.ns

        ddg.add_node(5)
        assert node2bracket(ddg, node_id=5) == u'()'
        #~ import pudb; pudb.set_trace()
        assert node2bracket(ddg, node_id=5, child_str='()') == u'(())'

        ddg.add_node(4, attr_dict={'label': 'S'})
        assert node2bracket(ddg, node_id=4) == u'(S)'
        assert node2bracket(ddg, node_id=4, child_str='') == u'(S)'
        assert node2bracket(ddg, node_id=4, child_str='(NP Ernst)') == u'(S (NP Ernst))'

        ddg.add_node(3, attr_dict={ns+':token': 'Horst'})
        assert node2bracket(ddg, node_id=3) == u'(Horst)'
        assert node2bracket(ddg, node_id=3, child_str='()') == u'(Horst ())'

        ddg.add_node(2, attr_dict={ns+':token': 'Horst', ns+':pos': 'N'})
        assert node2bracket(ddg, node_id=2) == u'(N Horst)'
        assert node2bracket(ddg, node_id=2, child_str='(N Schneider)') == u'(N Horst (N Schneider))'

        # if node is a token and has a label attribute, the output contains
        # the token attrib, not the label
        ddg.add_node(1, attr_dict={
            ns+':token': u'Björn', ns+':pos': 'NE', 'label': u'Horst'})
        assert node2bracket(ddg, node_id=1) == u'(NE Björn)'
        assert node2bracket(ddg, node_id=1, child_str='(N Schneider)') == u'(NE Björn (N Schneider))'

        ddg.add_node(6, attr_dict={
            ns+':token': u'Björn', 'label': u'Horst'})
        assert node2bracket(ddg, node_id=6) == u'(Björn)'
        assert node2bracket(ddg, node_id=6, child_str='(Schneider)') == u'(Björn (Schneider))'

    def test_tree2bracket(self):
        """A (part of a) docgraph can be converted into PTB-style bracket notation."""
        tree_str = tree2bracket(self.docgraph, 's1')
        expected_str = (u'((SIMPX (LK (VXFIN (VVFIN Verschlampte))) '
                         '(MF (NX (ART die) (NN AFD)) (NX (NN Spendengeld)))) '
                         '($. ?))')

        assert tree_str == expected_str

        root_str = tree2bracket(self.docgraph, self.docgraph.root)
        assert root_str == u"({})".format(expected_str)

        root_str = tree2bracket(self.docgraph)
        assert root_str == u"({})".format(expected_str)

        subgraph_successors = sorted_bfs_successors(self.docgraph, 's1_502')
        subtree_str = tree2bracket(self.docgraph, root='s1_502',
                                   successors=subgraph_successors)
        assert subtree_str == u"(NX (ART die) (NN AFD))"


def test_t():
    assert t("", []) == DGParentedTree("", [])
    assert t("") == DGParentedTree("", [])

    assert t("foo", []) == DGParentedTree("foo", [])
    assert t("foo") == DGParentedTree("foo", [])

    assert t("foo", ["bar"]) == DGParentedTree("foo", ["bar"])
    assert t("foo", ["bar", "baz"]) == DGParentedTree("foo", ["bar", "baz"])


def test_debug_root_label():
    label = 'Foo'
    node_id = '21'

    assert debug_root_label(label, debug=False, root_id=None) == label
    assert debug_root_label(label, debug=False, root_id=node_id) == label
    assert debug_root_label(label, debug=True, root_id=None) == label
    assert debug_root_label(label, debug=True, root_id=node_id) == "Foo (21)"
