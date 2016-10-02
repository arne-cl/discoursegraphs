#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

from lxml import etree
import pytest

from discoursegraphs import get_span, get_text
from discoursegraphs.corpora import pcc
from discoursegraphs.readwrite.tiger import TigerSentenceGraph

import discoursegraphs as dg

"""
This module contains some tests for the ``discoursegraphs.readwrite.tiger``
module, which converts a TigerXML file into a ``DiscourseDocumentGraph``.
"""


SENTENCE_WITHOUT_SECEDGE = """
<s xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="s389" art_id="13125" orig_id="ID_maz-13125">
<graph root="s389_503">
<terminals>
<t id="s389_1" word="Was" lemma="--" pos="PWS" morph="--"/>
<t id="s389_2" word="man" lemma="--" pos="PIS" morph="--"/>
<t id="s389_3" word="nicht" lemma="--" pos="PTKNEG" morph="--"/>
<t id="s389_4" word="durch" lemma="--" pos="APPR" morph="--"/>
<t id="s389_5" word="Augenschein" lemma="--" pos="NN" morph="--"/>
<t id="s389_6" word="nachprüfen" lemma="--" pos="VVINF" morph="--"/>
<t id="s389_7" word="kann" lemma="--" pos="VMFIN" morph="--"/>
<t id="s389_8" word="," lemma="--" pos="$," morph="--"/>
<t id="s389_9" word="ist" lemma="--" pos="VAFIN" morph="--"/>
<t id="s389_10" word="manipulierbar" lemma="--" pos="ADJD" morph="--"/>
<t id="s389_11" word="." lemma="--" pos="$." morph="--"/>
</terminals>
<nonterminals>
<nt id="s389_500" cat="PP">
<edge label="AC" idref="s389_4"/>
<edge label="NK" idref="s389_5"/>
 </nt>
<nt id="s389_501" cat="VP">
<edge label="OA" idref="s389_1"/>
<edge label="HD" idref="s389_6"/>
<edge label="MO" idref="s389_500"/>
 </nt>
<nt id="s389_502" cat="S">
<edge label="SB" idref="s389_2"/>
<edge label="NG" idref="s389_3"/>
<edge label="HD" idref="s389_7"/>
<edge label="OC" idref="s389_501"/>
 </nt>
<nt id="s389_503" cat="S">
<edge label="HD" idref="s389_9"/>
<edge label="PD" idref="s389_10"/>
<edge label="SB" idref="s389_502"/>
 </nt>
</nonterminals>
</graph>
</s>
"""

SENTENCE_WITH_SECEDGE = """
<s xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="s367" art_id="12976" orig_id="ID_maz-12976">
<graph root="s367_508">
<terminals>
<t id="s367_1" word="Es" lemma="--" pos="PPER" morph="--"></t>
<t id="s367_2" word="kann" lemma="--" pos="VMFIN" morph="--"></t>
<t id="s367_3" word="nicht" lemma="--" pos="PTKNEG" morph="--"></t>
<t id="s367_4" word="sein" lemma="--" pos="VAINF" morph="--"></t>
<t id="s367_5" word="," lemma="--" pos="$," morph="--"></t>
<t id="s367_6" word="dass" lemma="--" pos="KOUS" morph="--">
<secedge label="CP" idref="s367_505"/></t>
<t id="s367_7" word="die" lemma="--" pos="ART" morph="--"></t>
<t id="s367_8" word="Basis" lemma="--" pos="NN" morph="--"></t>
<t id="s367_9" word="gewissermaßen" lemma="--" pos="ADV" morph="--"></t>
<t id="s367_10" word="die" lemma="--" pos="ART" morph="--"></t>
<t id="s367_11" word="Moral" lemma="--" pos="NN" morph="--"></t>
<t id="s367_12" word="pachtet" lemma="--" pos="VVFIN" morph="--"></t>
<t id="s367_13" word="und" lemma="--" pos="KON" morph="--"></t>
<t id="s367_14" word="ihn" lemma="--" pos="PPER" morph="--"></t>
<t id="s367_15" word="die" lemma="--" pos="ART" morph="--"></t>
<t id="s367_16" word="realpolitische" lemma="--" pos="ADJA" morph="--"></t>
<t id="s367_17" word="Schmutzarbeit" lemma="--" pos="NN" morph="--"></t>
<t id="s367_18" word="machen" lemma="--" pos="VVINF" morph="--"></t>
<t id="s367_19" word="lässt" lemma="--" pos="VVFIN" morph="--"></t>
<t id="s367_20" word="." lemma="--" pos="$." morph="--"></t>
</terminals>
<nonterminals>
<nt id="s367_500" cat="NP">
<edge label="NK" idref="s367_7"/>
<edge label="NK" idref="s367_8"/>
<secedge label="SB" idref="s367_505"/>
 </nt>
<nt id="s367_501" cat="NP">
<edge label="NK" idref="s367_10"/>
<edge label="NK" idref="s367_11"/>
 </nt>
<nt id="s367_502" cat="NP">
<edge label="NK" idref="s367_15"/>
<edge label="NK" idref="s367_16"/>
<edge label="NK" idref="s367_17"/>
 </nt>
<nt id="s367_503" cat="S">
<edge label="CP" idref="s367_6"/>
<edge label="MO" idref="s367_9"/>
<edge label="HD" idref="s367_12"/>
<edge label="SB" idref="s367_500"/>
<edge label="OA" idref="s367_501"/>
 </nt>
<nt id="s367_504" cat="VP">
<edge label="HD" idref="s367_18"/>
<edge label="OA" idref="s367_502"/>
 </nt>
<nt id="s367_505" cat="S">
<edge label="OA" idref="s367_14"/>
<edge label="HD" idref="s367_19"/>
<edge label="OC" idref="s367_504"/>
 </nt>
<nt id="s367_506" cat="CS">
<edge label="CD" idref="s367_13"/>
<edge label="CJ" idref="s367_503"/>
<edge label="CJ" idref="s367_505"/>
 </nt>
<nt id="s367_507" cat="NP">
<edge label="PH" idref="s367_1"/>
<edge label="RE" idref="s367_506"/>
 </nt>
<nt id="s367_508" cat="S">
<edge label="HD" idref="s367_2"/>
<edge label="NG" idref="s367_3"/>
<edge label="OC" idref="s367_4"/>
<edge label="SB" idref="s367_507"/>
 </nt>
</nonterminals>
</graph>
</s>
"""


def test_tiger_sentence_spans():
    """
    convert a TigerXML sentence (without a secondary edge) into a
    ``TigerSentenceGraph`` and check, if the syntax nodes cover the right
    tokens / string spans.
    """
    maz_13125_s389 = etree.fromstring(SENTENCE_WITHOUT_SECEDGE)
    tsg = TigerSentenceGraph(maz_13125_s389)

    # the root element should cover the complete sentence
    assert get_span(tsg, 's389_503') == [
        's389_1', 's389_2', 's389_3', 's389_4', 's389_5', 's389_6', 's389_7',
        's389_8', 's389_9', 's389_10', 's389_11']
    assert get_text(tsg, 's389_503') == \
        u"Was man nicht durch Augenschein nachprüfen kann , ist manipulierbar ."
    assert dg.is_continuous(tsg, 's389_503')

    # a subordinated ('SB') clause
    assert get_span(tsg, 's389_502') == [
        's389_1', 's389_2', 's389_3', 's389_4', 's389_5', 's389_6', 's389_7']
    assert get_text(tsg, 's389_502') == \
        u"Was man nicht durch Augenschein nachprüfen kann"
    assert dg.is_continuous(tsg, 's389_502')

    # a discontinuously annotated VP ('OC', i.e. a clausal object)
    assert get_span(tsg, 's389_501') == [
        's389_1', 's389_4', 's389_5', 's389_6']
    assert get_text(tsg, 's389_501') == \
        u"Was durch Augenschein nachprüfen"
    assert not dg.is_continuous(tsg, 's389_501')

    # a PP modifier ('MO')
    assert get_span(tsg, 's389_500') == ['s389_4', 's389_5']
    assert get_text(tsg, 's389_500') == \
        u"durch Augenschein"
    assert dg.is_continuous(tsg, 's389_500')


def test_tiger_sentence_with_secedge_spans():
    """
    convert a TigerXML sentence (without a secondary edge) into a
    ``TigerSentenceGraph`` and check, if the syntax nodes cover the right
    tokens / string spans.
    """
    maz_12976_s367 = etree.fromstring(SENTENCE_WITH_SECEDGE)
    tsg_secedge = TigerSentenceGraph(maz_12976_s367)
    
    # sentence root
    assert get_span(tsg_secedge, 's367_508') == [
        's367_1', 's367_2', 's367_3', 's367_4', 's367_5', 's367_6', 's367_7',
        's367_8', 's367_9', 's367_10', 's367_11', 's367_12', 's367_13',
        's367_14', 's367_15', 's367_16', 's367_17', 's367_18', 's367_19',
        's367_20']
    assert get_text(tsg_secedge, 's367_508') == \
        u"Es kann nicht sein , dass die Basis gewissermaßen die Moral pachtet und ihn die realpolitische Schmutzarbeit machen lässt ."
    assert dg.is_continuous(tsg_secedge, 's367_508')

    # discontinuous NP
    assert get_span(tsg_secedge, 's367_507') == [
        's367_1', 's367_6', 's367_7', 's367_8', 's367_9', 's367_10', 's367_11',
        's367_12', 's367_13', 's367_14', 's367_15', 's367_16', 's367_17',
        's367_18', 's367_19']
    assert get_text(tsg_secedge, 's367_507') == \
        u"Es dass die Basis gewissermaßen die Moral pachtet und ihn die realpolitische Schmutzarbeit machen lässt"
    assert not dg.is_continuous(tsg_secedge, 's367_507')

    # a coordinated sentence ('CS')
    assert get_span(tsg_secedge, 's367_506') == [
        's367_6', 's367_7', 's367_8', 's367_9', 's367_10', 's367_11',
        's367_12', 's367_13', 's367_14', 's367_15', 's367_16', 's367_17',
        's367_18', 's367_19']
    assert get_text(tsg_secedge, 's367_506') == \
        u"dass die Basis gewissermaßen die Moral pachtet und ihn die realpolitische Schmutzarbeit machen lässt"
    assert dg.is_continuous(tsg_secedge, 's367_506')

    # a conjunct sentence ('CJ') with an ingoing secondary edge
    assert get_span(tsg_secedge, 's367_503') == [
        's367_6', 's367_7', 's367_8', 's367_9', 's367_10', 's367_11',
        's367_12']
    assert get_text(tsg_secedge, 's367_503') == \
        u"dass die Basis gewissermaßen die Moral pachtet"
    assert dg.is_continuous(tsg_secedge, 's367_503')

    assert get_span(tsg_secedge, 's367_500') == ['s367_7', 's367_8']
    assert get_text(tsg_secedge, 's367_500') == u"die Basis"
    assert dg.is_continuous(tsg_secedge, 's367_500')

    assert get_span(tsg_secedge, 's367_501') == ['s367_10', 's367_11']
    assert get_text(tsg_secedge, 's367_501') == u"die Moral"
    assert dg.is_continuous(tsg_secedge, 's367_501')

    # a conjunct sentence ('CJ') with an ingoing secondary edge
    assert get_span(tsg_secedge, 's367_505') == [
        's367_14', 's367_15', 's367_16', 's367_17', 's367_18', 's367_19']
    assert get_text(tsg_secedge, 's367_505') == \
        u"ihn die realpolitische Schmutzarbeit machen lässt"
    assert dg.is_continuous(tsg_secedge, 's367_505')

    # a clausal object ('OC') VP
    assert get_span(tsg_secedge, 's367_504') == [
        's367_15', 's367_16', 's367_17', 's367_18']
    assert get_text(tsg_secedge, 's367_504') == \
        u"die realpolitische Schmutzarbeit machen"
    assert dg.is_continuous(tsg_secedge, 's367_504')

    assert get_span(tsg_secedge, 's367_502') == [
        's367_15', 's367_16', 's367_17']
    assert get_text(tsg_secedge, 's367_502') == \
        u"die realpolitische Schmutzarbeit"
    assert dg.is_continuous(tsg_secedge, 's367_502')


def test_select_nodes_by_layer():
    """Are Tiger syntax nodes correctly filtered based on their layer?"""
    tiger_fpath = os.path.join(pcc.path, 'syntax/maz-10374.xml')
    tdg = dg.read_tiger(tiger_fpath)
    tiger_node_ids = list(dg.select_nodes_by_layer(tdg, 'tiger'))
    tiger_nodes = list(dg.select_nodes_by_layer(tdg, 'tiger', data=True))
    assert len(tdg) == len(tiger_node_ids) == 253


def test_fix_148():
    """Are all Tiger sentence root nodes part of the 'tiger:syntax' layer?"""
    # 00002: with VROOT, 10374: normal sentence root
    for tiger_doc in ('maz-00002.xml', 'maz-10374.xml'):
        tiger_fpath = os.path.join(pcc.path, 'syntax', tiger_doc)
        tdg = dg.read_tiger(tiger_fpath)
        assert all('tiger:syntax' in tdg.node[node_id]['layers']
                   for node_id in dg.select_nodes_by_layer(
                       tdg, 'tiger:sentence:root'))
