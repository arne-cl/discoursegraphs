#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""Basic tests for the ``rs3tree`` module"""

import os

import pytest
import re

from discoursegraphs import t
from discoursegraphs.readwrite.tree import p
from discoursegraphs.readwrite.rst.rs3 import RSTTree
from discoursegraphs.readwrite.rst.rs3.rs3tree import n, s
import discoursegraphs as dg

RS3TREE_DIR = os.path.join(dg.DATA_ROOT_DIR, 'rs3tree')
PCC_RS3_DIR = os.path.join(dg.DATA_ROOT_DIR,
                           'potsdam-commentary-corpus-2.0.0', 'rst')


def example2tree(rs3tree_example_filename, rs3tree_dir=RS3TREE_DIR, debug=False):
    """Return the absolute path of an example file."""
    filepath = os.path.join(rs3tree_dir, rs3tree_example_filename)
    return RSTTree(filepath, debug=debug)


def generate_pcc_test_case(filepath, error):
    basename = os.path.basename(filepath)
    doc_id_regex = re.compile('^.*maz-(\d+)\..*')
    doc_id = doc_id_regex.search(basename).groups()[0]
    result = (
        "@pytest.mark.xfail\n"
        "def test_pcc_{0}():\n"
        "\t# error: {1}\n"
        "\t#~ import pudb; pudb.set_trace()\n"
        "\t#~ produced = rstviewer_vs_rsttree('{2}', rs3tree_dir=PCC_RS3_DIR)\n"
        "\tproduced = example2tree('{2}', rs3tree_dir=PCC_RS3_DIR)\n"
        "\tassert 1 == 0\n".format(doc_id, error, basename))
    return result


def test_pcc_3367():
    produced = example2tree('maz-3367-excerpt.rs3', rs3tree_dir=RS3TREE_DIR)

    list_2_7 = ('list', [
        ('N', ['2']),
        ('N', ['3']),
        ('N', ['4']),
        ('N', ['5']),
        ('N', ['6']),
        ('N', ['7']),
    ])

    evidence_2_9 = ('evidence', [
        ('S', [list_2_7]),
        ('N', [
            ('concession', [
                ('S', ['8']),
                ('N', ['9']),
            ])
        ])
    ])

    interpretation_2_12 = ('interpretation', [
        ('S', [evidence_2_9]),
        ('N', [
            ('evaluation-s', [
                ('N', ['10']),
                ('S', [
                    ('conjunction', [
                        ('N', ['11']),
                        ('N', ['12'])
                    ])
                ])
            ])
        ])
    ])

    eval_13_14 = ('evaluation-n', [
        ('S', ['13']),
        ('N', ['14'])
    ])

    anti_15_16 = ('antithesis', [
        ('S', ['15']),
        ('N', ['16'])
    ])

    list_15_17 = t('list', [
        ('N', [anti_15_16]),
        ('N', ['17'])
    ])

    cond_18_19 = ('condition', [
        ('S', ['18']),
        ('N', ['19'])
    ])

    reason_20_23 = ('reason', [
        ('S', ['20']),
        ('N', [
            ('reason', [
                ('N', ['21']),
                ('S', [
                    ('conjunction', [
                        ('N', ['22']),
                        ('N', ['23'])
                    ])
                ])
            ])
        ])
    ])

    inner_tree_18_23 = ('evidence', [
        ('N', [cond_18_19]),
        ('S', [reason_20_23])
    ])

    second_tree_15_23 = ('evidence', [
        ('S', [list_15_17]),
        ('N', [inner_tree_18_23])
    ])

    third_tree_13_23 = ('evidence', [
        ('S', [eval_13_14]),
        ('N', [second_tree_15_23])
    ])

    background_2_23 = ('background', [
        ('S', [interpretation_2_12]),
        ('N', [third_tree_13_23])
    ])

    expected = t('virtual-root', [
        ('N', ['1']),
        ('N', [background_2_23])
    ])

    assert produced.tree.leaves() == [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
        '11', '12', '13', '14', '15', '16', '17', '18', '19',
        '20', '21', '22', '23']
    assert expected == produced.tree


def test_segments_only_trees():
    """Files without a single root must get a virtual one."""
    # minimal case: file without any segments
    produced = example2tree("empty.rs3")
    expected = t("", [])

    assert produced.tree.leaves() == []
    assert expected == produced.tree

    # one segment only
    produced = example2tree('only-one-segment.rs3')
    expected = t("N", ["foo"])

    assert produced.tree.leaves() == ['foo']
    assert expected == produced.tree

    # two segments w/out a root
    produced = example2tree("foo-bar-only-segments.rs3")
    expected = t("virtual-root",
                 [("N", ["foo"]), ("N", ["bar"])])

    assert produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    # three segments w/out a root
    produced = example2tree('eins-zwei-drei-only-segments.rs3')
    expected = t("virtual-root",
                 [("N", ["eins"]), ("N", ["zwei"]), ("N", ["drei"])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree


def test_single_nucsat_relation():
    produced = example2tree("foo-bar-circ-foo-to-bar.rs3")
    expected = t("circumstance", [
        ("S", ["foo"]),
        ("N", ["bar"])])

    assert produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree("foo-bar-elab-foo-to-bar.rs3")
    expected = t("elaboration", [
        ("S", ["foo"]),
        ("N", ["bar"])])

    assert produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree("foo-bar-circ-bar-to-foo.rs3")
    expected = t("circumstance", [
        ("N", ["foo"]),
        ("S", ["bar"])])

    assert produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree("foo-bar-elab-bar-to-foo.rs3")
    expected = t("elaboration", [
        ("N", ["foo"]),
        ("S", ["bar"])])

    assert produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree


def test_single_nucsat_relation_topspan():
    """It doesn't matter if there is a span above a single N-S relation."""
    produced1 = example2tree("foo-bar-circ-foo-to-bar-plus-top-span.rs3")
    produced2 = example2tree("foo-bar-circ-foo-to-bar.rs3")
    expected = t("circumstance", [
        ("S", ["foo"]),
        ("N", ["bar"])])

    assert produced1.tree.leaves() == ['foo', 'bar']
    assert produced2.tree.leaves() == ['foo', 'bar']
    assert expected == produced1.tree == produced2.tree


def test_single_multinuc_relation_topspan():
    """It doesn't matter if there is a span above a single multinuc relation."""
    produced1 = example2tree("foo-bar-foo-joint-bar.rs3")
    produced2 = example2tree("foo-bar-foo-joint-bar-plus-top-span.rs3")
    expected = t("joint", [
        ("N", ["foo"]),
        ("N", ["bar"])])

    assert produced1.tree.leaves() == ['foo', 'bar']
    assert produced2.tree.leaves() == ['foo', 'bar']
    assert expected == produced1.tree == produced2.tree


def test_single_multinuc_relation():
    produced = example2tree("foo-bar-foo-joint-bar.rs3")
    expected = t("joint", [
        ("N", ["foo"]),
        ("N", ["bar"])])

    assert produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree("foo-bar-foo-conj-bar.rs3")
    expected = t("conjunction", [
        ("N", ["foo"]),
        ("N", ["bar"])])

    assert produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(joint-eins-and-zwei-and-drei).rs3')
    expected = t("joint", [
        ("N", ["eins"]),
        ("N", ["zwei"]),
        ("N", ["drei"])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree


def test_nested_nucsat_relation():
    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-to-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("circumstance", [
                ("S", ["eins"]),
                ("N", ["zwei"])])]),
        ("S", ["drei"])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-from-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("circumstance", [
                ("N", ["eins"]),
                ("S", ["zwei"])])]),
        ("S", ["drei"])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-from-zwei)-to-drei).rs3')
    expected = t("circumstance", [
        ("S", [
            ("circumstance", [
                ("N", ["eins"]),
                ("S", ["zwei"])])]),
        ("N", ["drei"])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-to-zwei)-to-drei.rs3')
    expected = t("circumstance", [
        ("S", [
            ("circumstance", [
                ("S", ["eins"]),
                ("N", ["zwei"])])]),
        ("N", ["drei"])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree


def test_nested_nucsat_multinuc_relation():
    produced = example2tree('eins-zwei-drei-(circ-eins-to-(joint-zwei-and-drei).rs3')
    expected = t("circumstance", [
        ("S", ["eins"]),
        ("N", [
            ("joint", [
                ("N", ["zwei"]),
                ("N", ["drei"])])])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(joint-eins-and-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("joint", [
                ("N", ["eins"]),
                ("N", ["zwei"])
            ])
        ]),
        ("S", ["drei"])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-eins-from-(joint-zwei-and-drei).rs3')
    expected = t("circumstance", [
        ("N", ["eins"]),
        ("S", [
            ("joint", [
                ("N", ["zwei"]),
                ("N", ["drei"])])])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(joint-eins-and-zwei)-to-drei).rs3')
    expected = t("circumstance", [
        ("S", [
            ("joint", [
                ("N", ["eins"]),
                ("N", ["zwei"])
            ])
        ]),
        ("N", ["drei"])])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(elab-eins-from-(joint-zwei-and-drei).rs3')
    expected = t('elaboration', [
        ("N", ["eins"]),
        ("S", [
            ("joint", [
                ("N", ["zwei"]),
                ("N", ["drei"])
            ])
        ])
    ])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree


def test_single_sns_schema_topspan():
    """It doesn't matter if there's a span above a S-N-S schema."""
    produced1 = example2tree("schema-elab-elab.rs3")
    produced2 = example2tree("schema-elab-elab-plus-top-span.rs3")

    expected = t('elaboration', [
        ('N', [
            ('elaboration', [
                ('S', ['eins']),
                ('N', ['zwei'])
            ])
        ]),
        ('S', ['drei'])
    ])

    assert produced1.tree.leaves() == ['eins', 'zwei', 'drei']
    assert produced2.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced1.tree == produced2.tree


def test_nested_sns_schema():
    produced = example2tree('maz-10575-excerpt.rs3')
    expected = t('interpretation', [
        ('N', [
            ('circumstance', [
                ('S', ['eins']),
                ('N', [
                    ('contrast', [
                        ('N', ['zwei']),
                        ('N', [
                            ('cause', [
                                ('N', ['drei']),
                                ('S', ['vier'])
                            ])
                        ])
                    ])
                ])
            ])
        ]),
        ('S', ['fuenf'])
    ])

    assert produced.tree.leaves() == ['eins', 'zwei', 'drei', 'vier', 'fuenf']
    assert expected == produced.tree


def test_single_nss_schema_topspan():
    """It doesn't matter if there's a span above a N-S-S schema."""
    produced1 = example2tree('n-s-s-schema-eins-zwei-drei.rs3')
    produced2 = example2tree('n-s-s-schema-eins-zwei-drei-plus-top-span.rs3')
    expected = t('background', [
        ('N', [
            ('elaboration', [
                ('N', ['eins']),
                ('S', ['zwei'])
            ])
        ]),
        ('S', ['drei'])
    ])

    assert produced1.tree.leaves() == ['eins', 'zwei', 'drei']
    assert produced2.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced1.tree == produced2.tree


def test_nested_nss_schema_topspan():
    """It doesn't matter if there's a span above a nested N-S-S schema."""
    produced1 = example2tree('n-s-s-schema-eins-zwei-(joint-drei-vier).rs3')
    produced2 = example2tree('n-s-s-schema-eins-zwei-(joint-drei-vier)-plus-top-span.rs3')
    expected = t('background', [
        ('N', [
            ('elaboration', [
                ('N', ['eins']),
                ('S', ['zwei'])
            ])]),
        ('S', [
            ('joint', [
                ('N', ['drei']),
                ('N', ['vier'])
            ])
        ])
    ])

    assert produced1.tree.leaves() == ['eins', 'zwei', 'drei', 'vier']
    assert produced2.tree.leaves() == ['eins', 'zwei', 'drei', 'vier']
    assert produced1.tree == produced2.tree
    assert expected == produced1.tree == produced2.tree


def test_pcc_10207():
    produced = example2tree('maz-10207-excerpt.rs3', rs3tree_dir=RS3TREE_DIR)

    prep_2_3 = ('preparation', [
        s(['2']),
        n(['3'])
    ])

    inter_2_4 = ('interpretation', [
        s([prep_2_3]),
        n(['4'])
    ])

    inter_2_5 = ('interpretation', [
        n([inter_2_4]),
        s(['5'])
    ])

    inter_2_6 = ('interpretation', [
        n([inter_2_5]),
        s(['6'])
    ])

    elab_7_8 = ('e-elaboration', [
        n(['7']),
        s(['8'])
    ])

    list_9_11 = ('list', [
        n(['9']),
        n(['10']),
        n(['11'])
    ])

    concession_7_11 = ('concession', [
        s([elab_7_8]),
        n([list_9_11])
    ])

    concession_14_15 = ('concession', [
        s(['14']),
        n(['15'])
    ])

    inter_16_17 = ('interpretation', [
        n(['16']),
        s(['17'])
    ])

    joint_14_17 = ('joint', [
        n([concession_14_15]),
        n([inter_16_17])
    ])

    inter_13_17 = ('interpretation', [
        n(['13']),
        s([joint_14_17])
    ])

    justify_12_17 = ('justify', [
        s(['12']),
        n([inter_13_17])
    ])

    list_7_17 = ('list', [
        n([concession_7_11]),
        n([justify_12_17])
    ])

    back_2_17 = ('background', [
        s([inter_2_6]),
        n([list_7_17])
    ])

    inter_2_18 = ('interpretation', [
        n([back_2_17]),
        s(['18'])
    ])

    expected = t('virtual-root', [
        n(['1']),
        n([inter_2_18])
    ])

    assert produced.tree.leaves() == [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
        '11', '12', '13', '14', '15', '16', '17', '18']
    assert expected == produced.tree


@pytest.mark.xfail
def test_pcc_11279():
        # error: 
        #~ import pudb; pudb.set_trace()
        #~ produced = rstviewer_vs_rsttree('maz-11279.rs3', rs3tree_dir=PCC_RS3_DIR)
        produced = example2tree('maz-11279.rs3', rs3tree_dir=PCC_RS3_DIR)
        assert 1 == 0


@pytest.mark.xfail
def test_pcc_6918():
        # error: Segment has more than two children
        #~ import pudb; pudb.set_trace()
        #~ produced = rstviewer_vs_rsttree('maz-6918.rs3', rs3tree_dir=PCC_RS3_DIR)
        produced = example2tree('maz-6918.rs3', rs3tree_dir=PCC_RS3_DIR)
        assert 1 == 0


@pytest.mark.xfail
def test_pcc_00001():
        # error: A multinuc segment (18) should not have children: ['40']
        #~ import pudb; pudb.set_trace()
        #~ produced = rstviewer_vs_rsttree('maz-00001.rs3', rs3tree_dir=PCC_RS3_DIR)
        produced = example2tree('maz-00001.rs3', rs3tree_dir=PCC_RS3_DIR)
        assert 1 == 0


@pytest.mark.xfail
def test_pcc_14654():
        # error: Can't parse a multinuc group (28) with more than 2 non-multinuc children: ['25', '30', '31']
        #~ import pudb; pudb.set_trace()
        #~ produced = rstviewer_vs_rsttree('maz-14654.rs3', rs3tree_dir=PCC_RS3_DIR)
        produced = example2tree('maz-14654.rs3', rs3tree_dir=PCC_RS3_DIR)
        assert 1 == 0


@pytest.mark.xfail
def test_parse_complete_pcc():
    okay = 0.0
    fail = 0.0
    print "\n"
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        try:
            x = dg.readwrite.RSTTree(rfile)
            okay += 1
        except Exception as e:
            #~ print i, os.path.basename(rfile), "FAIL"
            #~ print "\t", e
            #~ x = dg.readwrite.RSTTree(rfile)
            fail += 1
            #~ print generate_pcc_test_case(rfile, e)

    print "\n{}% success".format(okay / (okay+fail) * 100)
    assert okay == 176
