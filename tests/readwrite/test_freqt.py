
from tempfile import NamedTemporaryFile

from lxml import etree
import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.exportxml import ExportXMLDocumentGraph
from discoursegraphs.readwrite.freqt import docgraph2freqt, node2freqt, write_freqt


class TestFreqtTree(object):
    """Tests for FREQT export"""
    def setup_class(cls):
        """generate a simple docgraph for testing the FREQT export"""
        cls.docgraph = dg.DiscourseDocumentGraph(root='TEXT')
        ns = cls.docgraph.ns

        nodes = [
            ('S', {'label': 'S', 'layers': {ns+':syntax'}}),
            ('NP1', {'label': 'NP', 'layers': {ns+':syntax'}}),
            ('VP', {'label': 'VP', 'layers': {ns+':syntax'}}),
            ('NP2', {'label': 'NP', 'layers': {ns+':syntax'}}),
            ('PP', {'label': 'PP', 'layers': {ns+':syntax'}}),
            ('NP3', {'label': 'NP', 'layers': {ns+':syntax'}}),
            ('token1', {ns+':token': 'I', ns+':pos': 'PRON', 'layers': {ns+':token'}}),
            ('token2', {ns+':token': 'saw', ns+':pos': 'VVFIN', 'layers': {ns+':token'}}),
            ('token3', {ns+':token': 'a', ns+':pos': 'DET', 'layers': {ns+':token'}}),
            ('token4', {ns+':token': 'girl', ns+':pos': 'N', 'layers': {ns+':token'}}),
            ('token5', {ns+':token': 'with', ns+':pos': 'PREP', 'layers': {ns+':token'}}),
            ('token6', {ns+':token': 'a', ns+':pos': 'DET', 'layers': {ns+':token'}}),
            ('token7', {ns+':token': 'telescope', ns+':pos': 'N', 'layers': {ns+':token'}}),
            ('token8', {ns+':token': '.', ns+':pos': 'PUNCT', 'layers': {ns+':token'}}),
        ]

        edges = [
            ('TEXT', 'S', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('S', 'NP1', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('S', 'VP', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('S', 'token8', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('NP1', 'token1', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('VP', 'token2', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('VP', 'NP2', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('VP', 'PP', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('NP2', 'token3', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('NP2', 'token4', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('PP', 'token5', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('PP', 'NP3', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('NP3', 'token6', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('NP3', 'token7', {'edge_type': dg.EdgeTypes.dominance_relation}),
        ]

        cls.docgraph.add_nodes_from(nodes)
        cls.docgraph.add_edges_from(edges)
        cls.docgraph.tokens = ['token'+str(tok_id) for tok_id in range(1, 9)]

    def test_node2freqt(self):
        """A node can be converted into a FREQT string."""
        assert u'(I)' == node2freqt(self.docgraph, 'token1', child_str='',
                                    include_pos=False)
        assert u'(PRON(I))' == node2freqt(self.docgraph, 'token1', child_str='',
                                          include_pos=True)

        assert u'(NP)' == node2freqt(self.docgraph, 'NP1', child_str='',
                                    include_pos=False)
        assert u'(NP(PRON(I)))' == node2freqt(
            self.docgraph, 'NP1', child_str='(PRON(I))', include_pos=False)
        assert u'(NP)' == node2freqt(self.docgraph, 'NP1', child_str='',
                                    include_pos=True)
        assert u'(NP(PRON(I)))' == node2freqt(
            self.docgraph, 'NP1', child_str='(PRON(I))', include_pos=True)

        # the root node has no label attribute
        assert u'()' == node2freqt(self.docgraph, 'TEXT', child_str='',
                                    include_pos=False)
        assert u'()' == node2freqt(self.docgraph, 'TEXT', child_str='',
                                    include_pos=True)

    def test_docgraph2freqt(self):
        """A docgraph can be converted into a FREQT string, with/out POS tags."""
        expected = u'(S(NP(I))(VP(saw)(NP(a)(girl))(PP(with)(NP(a)(telescope))))(.))'
        freqt_str = docgraph2freqt(self.docgraph, root='S', include_pos=False)
        assert freqt_str == expected

        expected_with_pos = (u'(S(NP(PRON(I)))(VP(VVFIN(saw))(NP(DET(a))'
                              '(N(girl)))(PP(PREP(with))(NP(DET(a))'
                              '(N(telescope)))))(PUNCT(.)))')
        freqt_pos_str = docgraph2freqt(self.docgraph, root='S', include_pos=True)
        assert freqt_pos_str == expected_with_pos
