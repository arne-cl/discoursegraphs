#!/usr/bin/env python
# coding: utf-8
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import pytest

from discoursegraphs.readwrite.generic import convert_spanstring


def test_convert_spanstring():
    """convert a string describing a (non-contiguous) sequence of tokens into a
    list of all these tokens
    """
    assert [] == convert_spanstring('')

    # span strings used in MMAX2
    assert ['word_1'] == convert_spanstring('word_1')
    assert ['word_2', 'word_3'] == convert_spanstring('word_2,word_3')
    assert ['word_7', 'word_8', 'word_9', 'word_10', 'word_11'] == \
        convert_spanstring('word_7..word_11')
    assert ['word_2', 'word_3', 'word_7', 'word_8', 'word_9'] == \
        convert_spanstring('word_2,word_3,word_7..word_9')
    assert convert_spanstring('word_7..word_9,word_15,word_17..word_19') == \
        ['word_7', 'word_8', 'word_9', 'word_15', 'word_17', 'word_18',
         'word_19']

    # span strings used in ExportXML, see issue #143
    assert convert_spanstring('s149_7..s149_11') == \
        ['s149_7', 's149_8', 's149_9', 's149_10', 's149_11']

    assert convert_spanstring("s45327_4,s45327_7") == ['s45327_4', 's45327_7']
    assert convert_spanstring("s48169_9..s48169_10,s48169_12") == \
        ['s48169_9', 's48169_10', 's48169_12']

    assert convert_spanstring("s8826_17..s8826_18,s8826_20..s8826_21") == \
        ['s8826_17', 's8826_18', 's8826_20', 's8826_21']

    # ExportXML also uses spanstrings that cover tokens from more than one
    # sentence. Until we need to implement those, make sure they fail
    # (cf. see issue #144).
    with pytest.raises(AssertionError):
        convert_spanstring('s2011_6..s2012_13')
