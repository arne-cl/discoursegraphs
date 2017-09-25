#!/usr/bin/env python
# coding: utf-8
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

from lxml import etree
import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.exportxml import ExportXMLDocumentGraph
from discoursegraphs.readwrite.freqt import (
    docgraph2freqt, node2freqt, FREQT_ESCAPE_FUNC, write_freqt)


# Issue #143: KeyError 's144_23': the word occurs after </sentence> !
text9_s144 = """
<text xml:id="text_9" origin="T990507.13">
  <edu-range xml:id="edus9_18_0-19_0">
   <discRel relation="Parallel" marking="auch" arg2="edu_9_20_0"/>
   <sentence xml:id="s143">
    <edu xml:id="edu_9_18_0">
     <discRel relation="Contrast" marking="dagegen|*eher" arg2="edu_9_19_0"/>
     <node xml:id="s143_508" cat="SIMPX" func="--">
      <node xml:id="s143_501" cat="VF" func="-" parent="s143_508">
       <node xml:id="s143_500" cat="NX" func="ON" parent="s143_501">
        <relation type="anaphoric" target="s142_511"/>
        <word xml:id="s143_1" form="Diese" pos="PDS" morph="np*" lemma="dieser|diese|dieses" func="HD" parent="s143_500" dephead="s143_2" deprel="SUBJ"/>
       </node>
      </node>
      <node xml:id="s143_503" cat="LK" func="-" parent="s143_508">
       <node xml:id="s143_502" cat="VXFIN" func="HD" parent="s143_503">
        <word xml:id="s143_2" form="saufen" pos="VVFIN" morph="3pis" lemma="saufen" func="HD" parent="s143_502" deprel="ROOT"/>
       </node>
      </node>
      <node xml:id="s143_507" cat="MF" func="-" parent="s143_508">
       <node xml:id="s143_504" cat="ADVX" func="V-MOD" parent="s143_507">
        <word xml:id="s143_3" form="&#246;fter" pos="ADV" lemma="&#246;fter" func="HD" parent="s143_504" dephead="s143_2" deprel="ADV"/>
       </node>
       <node xml:id="s143_506" cat="PX" func="V-MOD" parent="s143_507">
        <word xml:id="s143_4" form="in" pos="APPR" morph="d" lemma="in" func="-" parent="s143_506" dephead="s143_2" deprel="PP"/>
        <node xml:id="s143_505" cat="NX" func="HD" parent="s143_506">
         <word xml:id="s143_5" form="Gesellschaft" pos="NN" morph="dsf" lemma="Gesellschaft" func="HD" parent="s143_505" dephead="s143_4" deprel="PN"/>
        </node>
       </node>
      </node>
     </node>
     <word xml:id="s143_6" form="." pos="$." lemma="." func="--" deprel="ROOT"/>
    </edu>
   </sentence>
   <sentence xml:id="s144" span="s144_1..s144_23">
    <node xml:id="s144_528" cat="SIMPX" func="--" span="s144_1..s144_22">
     <edu xml:id="edu_9_19_0">
      <discRel relation="Explanation-Cause" marking="-" arg2="edu_9_19_1"/>
      <node xml:id="s144_525" cat="SIMPX" func="KONJ" parent="s144_528">
       <node xml:id="s144_514" cat="VF" func="-" parent="s144_525">
        <node xml:id="s144_500" cat="NX" func="ON" parent="s144_514">
         <word xml:id="s144_1" form="Frauen" pos="NN" morph="npf" lemma="Frau" func="HD" parent="s144_500" dephead="s144_2" deprel="SUBJ"/>
        </node>
       </node>
       <node xml:id="s144_515" cat="LK" func="-" parent="s144_525">
        <node xml:id="s144_501" cat="VXFIN" func="HD" parent="s144_515">
         <word xml:id="s144_2" form="erleben" pos="VVFIN" morph="3pis" lemma="erleben" func="HD" parent="s144_501" deprel="ROOT"/>
        </node>
       </node>
       <node xml:id="s144_523" cat="MF" func="-" parent="s144_525">
        <node xml:id="s144_502" cat="NX" func="OA" parent="s144_523">
         <word xml:id="s144_3" form="den" pos="ART" morph="asm" lemma="der" func="-" parent="s144_502" dephead="s144_4" deprel="DET"/>
         <word xml:id="s144_4" form="Vollrausch" pos="NN" morph="asm" lemma="Vollrausch" func="HD" parent="s144_502" dephead="s144_2" deprel="OBJA"/>
        </node>
        <node xml:id="s144_503" cat="PX" func="MOD" parent="s144_523">
         <word xml:id="s144_5" form="dagegen" pos="PROP" lemma="dagegen" func="HD" parent="s144_503" dephead="s144_2" deprel="PP"/>
        </node>
        <node xml:id="s144_504" cat="ADVX" func="MOD" parent="s144_523">
         <word xml:id="s144_6" form="eher" pos="ADV" lemma="eher" func="HD" parent="s144_504" dephead="s144_2" deprel="ADV"/>
        </node>
        <node xml:id="s144_520" cat="ADJX" func="V-MOD" parent="s144_523">
         <node xml:id="s144_505" cat="ADJX" func="KONJ" parent="s144_520">
          <word xml:id="s144_7" form="heimlich" pos="ADJD" lemma="heimlich" func="HD" parent="s144_505" dephead="s144_2" deprel="ADV"/>
         </node>
         <word xml:id="s144_8" form="und" pos="KON" lemma="und" func="-" parent="s144_520" dephead="s144_7" deprel="KON"/>
         <node xml:id="s144_516" cat="PX" func="KONJ" parent="s144_520">
          <word xml:id="s144_9" form="zu" pos="APPR" morph="d" lemma="zu" func="-" parent="s144_516" dephead="s144_8" deprel="CJ"/>
          <node xml:id="s144_506" cat="NX" func="HD" parent="s144_516">
           <word xml:id="s144_10" form="Hause" pos="NN" morph="dsn" lemma="Haus" func="HD" parent="s144_506" dephead="s144_9" deprel="PN"/>
          </node>
         </node>
        </node>
       </node>
      </node>
      <word xml:id="s144_11" form="-" pos="$(" lemma="-" func="--" deprel="ROOT"/>
     </edu>
    </node>
   </sentence>
  </edu-range>
  <edu xml:id="edu_9_19_1">
   <node xml:id="s144_527" cat="SIMPX" func="KONJ" parent="s144_528">
    <node xml:id="s144_521" cat="VF" func="-" parent="s144_527">
     <node xml:id="s144_517" cat="PX" func="OA-MOD" parent="s144_521">
      <word xml:id="s144_12" form="au&#223;er" pos="APPR" morph="d" lemma="au&#223;er" func="-" parent="s144_517" dephead="s144_19" deprel="PP"/>
      <node xml:id="s144_507" cat="NX" func="HD" parent="s144_517">
       <word xml:id="s144_13" form="Weiberfastnacht" pos="NN" morph="dsf" lemma="Weiberfastnacht" func="HD" parent="s144_507" dephead="s144_12" deprel="PN"/>
      </node>
     </node>
    </node>
    <node xml:id="s144_518" cat="LK" func="-" parent="s144_527">
     <node xml:id="s144_508" cat="VXFIN" func="HD" parent="s144_518">
      <word xml:id="s144_14" form="bietet" pos="VVFIN" morph="3sis" lemma="bieten" func="HD" parent="s144_508" dephead="s144_2" deprel="KON"/>
     </node>
    </node>
    <node xml:id="s144_526" cat="MF" func="-" parent="s144_527">
     <node xml:id="s144_509" cat="NX" func="ON" parent="s144_526">
      <word xml:id="s144_15" form="die" pos="ART" morph="nsf" lemma="die" func="-" parent="s144_509" dephead="s144_16" deprel="DET"/>
      <word xml:id="s144_16" form="&#214;ffentlichkeit" pos="NN" morph="nsf" lemma="&#214;ffentlichkeit" func="HD" parent="s144_509" dephead="s144_14" deprel="SUBJ"/>
     </node>
     <node xml:id="s144_510" cat="NX" func="OD" parent="s144_526">
      <relation type="anaphoric" target="s144_500"/>
      <word xml:id="s144_17" form="ihnen" pos="PPER" morph="dp*3" lemma="sie" func="HD" parent="s144_510" dephead="s144_14" deprel="OBJD"/>
     </node>
     <node xml:id="s144_511" cat="ADVX" func="MOD" parent="s144_526">
      <word xml:id="s144_18" form="kaum" pos="ADV" lemma="kaum" func="HD" parent="s144_511" dephead="s144_14" deprel="ADV"/>
     </node>
     <node xml:id="s144_524" cat="NX" func="OA" parent="s144_526">
      <node xml:id="s144_512" cat="NX" func="HD" parent="s144_524">
       <word xml:id="s144_19" form="Orte" pos="NN" morph="apm" lemma="Ort" func="HD" parent="s144_512" dephead="s144_14" deprel="OBJA"/>
      </node>
      <node xml:id="s144_522" cat="PX" func="-" parent="s144_524">
       <word xml:id="s144_20" form="f&#252;r" pos="APPR" morph="a" lemma="f&#252;r" func="-" parent="s144_522" dephead="s144_19" deprel="PP"/>
       <node xml:id="s144_519" cat="NX" func="HD" parent="s144_522">
        <node xml:id="s144_513" cat="ADJX" func="-" parent="s144_519">
         <word xml:id="s144_21" form="ungehemmte" pos="ADJA" morph="asf" lemma="ungehemmt" func="HD" parent="s144_513" dephead="s144_22" deprel="ATTR"/>
        </node>
        <word xml:id="s144_22" form="Alkoholzufuhr" pos="NN" morph="asf" lemma="Alkoholzufuhr" func="HD" parent="s144_519" dephead="s144_20" deprel="PN"/>
       </node>
      </node>
     </node>
    </node>
   </node>
   <word xml:id="s144_23" form="." pos="$." lemma="." func="--" deprel="ROOT"/>
  </edu>
</text>
"""


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

        # the root node has no label attribute. here, the node ID is used
        # instead
        assert u'(TEXT)' == node2freqt(self.docgraph, 'TEXT', child_str='',
                                       include_pos=False)
        assert u'(TEXT)' == node2freqt(self.docgraph, 'TEXT', child_str='',
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

    @staticmethod
    def test_docgraph2freqt_escaped():
        """Convert a docgraph into a FREQT string, with/out POS tags and escaping."""
        docgraph = dg.DiscourseDocumentGraph(root='TEXT')
        assert '(TEXT)' == node2freqt(docgraph, docgraph.root, escape_func=FREQT_ESCAPE_FUNC)
        assert '(TEXT)' == node2freqt(docgraph, docgraph.root, escape_func=lambda x: x)

        docgraph = dg.DiscourseDocumentGraph(root='(TEXT)')
        assert '(-LRB-TEXT-RRB-)' == node2freqt(docgraph, docgraph.root, escape_func=FREQT_ESCAPE_FUNC)
        assert '((TEXT))' == node2freqt(docgraph, docgraph.root, escape_func=lambda x: x)

        docgraph = dg.DiscourseDocumentGraph(root='TE(X)T')
        assert '(TE-LRB-X-RRB-T)' == node2freqt(docgraph, docgraph.root, escape_func=FREQT_ESCAPE_FUNC)
        assert '(TE(X)T)' == node2freqt(docgraph, docgraph.root, escape_func=lambda x: x)

        # sentence: I am (un)certain .
        docgraph = dg.DiscourseDocumentGraph(root='ROOT')
        ns = docgraph.ns

        nodes = [
            ('S', {'label': 'S', 'layers': {ns+':syntax'}}),
            ('NP', {'label': 'NP', 'layers': {ns+':syntax'}}),
            ('VP', {'label': 'VP', 'layers': {ns+':syntax'}}),
            ('ADJP', {'label': 'ADJP', 'layers': {ns+':syntax'}}),
            ('token1', {ns+':token': 'I', ns+':pos': 'PRP', 'layers': {ns+':token'}}),
            ('token2', {ns+':token': 'am', ns+':pos': 'VBP', 'layers': {ns+':token'}}),
            ('token3', {ns+':token': '(un)certain', ns+':pos': 'JJ', 'layers': {ns+':token'}}),
            ('token4', {ns+':token': '.', ns+':pos': '$(', 'layers': {ns+':token'}}),
        ]

        edges = [
            ('ROOT', 'S', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('S', 'NP', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('S', 'VP', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('NP', 'token1', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('VP', 'token2', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('VP', 'ADJP', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('ADJP', 'token3', {'edge_type': dg.EdgeTypes.dominance_relation}),
            ('S', 'token4', {'edge_type': dg.EdgeTypes.dominance_relation}),
        ]

        docgraph.add_nodes_from(nodes)
        docgraph.add_edges_from(edges)
        docgraph.tokens = ['token'+str(tok_id) for tok_id in range(1, 5)]

        # generate FREQT string without POS; don't escape brackets
        freqtstr_nopos_noescape = u"(ROOT(S(NP(I))(VP(am)(ADJP((un)certain)))(.)))"
        assert freqtstr_nopos_noescape == docgraph2freqt(
            docgraph, docgraph.root, include_pos=False,
            escape_func=lambda x: x)

        # generate FREQT string without POS; escape brackets
        freqtstr_nopos_escape = u"(ROOT(S(NP(I))(VP(am)(ADJP(-LRB-un-RRB-certain)))(.)))"
        assert freqtstr_nopos_escape == docgraph2freqt(
            docgraph, docgraph.root, include_pos=False,
            escape_func=FREQT_ESCAPE_FUNC)

        # generate FREQT string with POS; don't escape brackets
        freqtstr_pos_noescape = u"(ROOT(S(NP(PRP(I)))(VP(VBP(am))(ADJP(JJ((un)certain))))($((.))))"
        assert freqtstr_pos_noescape == docgraph2freqt(
            docgraph, docgraph.root, include_pos=True,
            escape_func=lambda x: x)

        # generate FREQT string with POS; escape brackets
        freqtstr_pos_escape = u"(ROOT(S(NP(PRP(I)))(VP(VBP(am))(ADJP(JJ(-LRB-un-RRB-certain))))($-LRB-(.))))"
        assert freqtstr_pos_escape == docgraph2freqt(
            docgraph, docgraph.root, include_pos=True,
            escape_func=FREQT_ESCAPE_FUNC)


def test_write_freqt():
    """convert an ExportXML file into a FREQT str (with/out POS tags)"""
    edg = dg.read_exportxml(
        os.path.join(dg.DATA_ROOT_DIR, 'exportxml-example.xml')).next()
    temp_file = NamedTemporaryFile(delete=False)
    temp_file.close()
    write_freqt(edg, temp_file.name, include_pos=False)
    os.unlink(temp_file.name)

    temp_file = NamedTemporaryFile(delete=False)
    temp_file.close()
    write_freqt(edg, temp_file.name, include_pos=True)
    os.unlink(temp_file.name)


def test_docgraph2freqt_fix144():
    """
    convert an ExportXML document graph into a FREQT str, where the original
    ExportXML segment contains a <sentence> element that does not embed all
    <word> elements that belong to the sentence.

    The sentence covers the tokens 1 to 23
    (<sentence xml:id="s144" span="s144_1..s144_23">), but the <sentence>
    element only embeds the <word> elements 1 to 11.
    """
    text9_tree = etree.fromstring(text9_s144)
    text9_graph = ExportXMLDocumentGraph(text9_tree)
    docgraph2freqt(text9_graph, include_pos=False)


def test_docgraph2freqt_ptb():
    """convert a PTB parse string into a FREQT string."""
    ptb_str = ("(ROOT (S (ADVP (RB Ideologically)) (, ,) (NP (PRP he)) "
               "(VP (VBZ aligns) (PP (IN with) (NP (NN anarcho-syndicalism) "
               "(CC and) (NN libertarian) (NN socialism)))) (. .)))")
    pdg = dg.read_ptb.fromstring(ptb_str)

    freqt_str_pos = docgraph2freqt(pdg, include_pos=True)
    freqt_str_nopos = docgraph2freqt(pdg, include_pos=False)

    expected_freqt_str_pos = (
        "(ROOT(S(ADVP(RB(Ideologically)))(,(,))(NP(PRP(he)))(VP(VBZ(aligns))"
        "(PP(IN(with))(NP(NN(anarcho-syndicalism))(CC(and))(NN(libertarian))"
        "(NN(socialism)))))(.(.))))")
    assert freqt_str_pos == expected_freqt_str_pos

    expected_freqt_str_nopos = (
        "(ROOT(S(ADVP(Ideologically))(,)(NP(he))(VP(aligns)(PP(with)(NP"
        "(anarcho-syndicalism)(and)(libertarian)(socialism))))(.)))")
    assert freqt_str_nopos == expected_freqt_str_nopos

    # a PTB string that contains two sentences
    double_pdg = dg.read_ptb.fromstring(ptb_str+"\n"+ptb_str)
    double_freqt_str_pos = docgraph2freqt(double_pdg, include_pos=True)

    assert double_freqt_str_pos == \
        expected_freqt_str_pos+"\n"+expected_freqt_str_pos


def test_docgraph2freqt_ptb_escapes():
    """convert a PTB string with escaped '(' and ')' into a FREQT string."""
    ptb_str = ("(S (NP (PRP It)) (VP (VBZ is) (ADJP (PRN (-LRB- -LRB-) "
               "(ADVP (RB almost)) (-RRB- -RRB-)) (JJ perfect))) (. .))")
    pdg = dg.read_ptb.fromstring(ptb_str)
    assert dg.get_text(pdg) == u"It is ( almost ) perfect ."

    expected_freqt_str_pos = "(S(NP(PRP(It)))(VP(VBZ(is))(ADJP(PRN(-LRB-(-LRB-))(ADVP(RB(almost)))(-RRB-(-RRB-)))(JJ(perfect))))(.(.)))"
    freqt_str_pos = docgraph2freqt(pdg, include_pos=True)
    assert freqt_str_pos == expected_freqt_str_pos

    expected_freqt_str_nopos = "(S(NP(It))(VP(is)(ADJP(PRN(-LRB-)(ADVP(almost))(-RRB-))(perfect)))(.))"
    freqt_str_nopos = docgraph2freqt(pdg, include_pos=False)
    assert freqt_str_nopos == expected_freqt_str_nopos
