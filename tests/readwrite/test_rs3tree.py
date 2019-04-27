#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""Basic tests for the ``rs3tree`` module"""

import logging
import os
import re

from lxml import etree
from nltk.tree import ParentedTree
import pytest


from discoursegraphs.readwrite.tree import p, t, debug_root_label
from discoursegraphs.readwrite.rst.rs3 import extract_relationtypes, RSTTree
from discoursegraphs.readwrite.rst.rs3.rs3tree import n, s, TooManyChildrenError, VIRTUAL_ROOT
import discoursegraphs as dg

RS3TREE_DIR = os.path.join(dg.DATA_ROOT_DIR, 'rs3tree')
PCC_RS3_DIR = os.path.join(dg.DATA_ROOT_DIR,
                           'potsdam-commentary-corpus-2.0.0', 'rst')


def example2tree(rs3tree_example_filename, rs3tree_dir=RS3TREE_DIR, debug=False):
    """Given the filename of an rs3 file and its directory, return an RSTTree instance of it."""
    filepath = os.path.join(rs3tree_dir, rs3tree_example_filename)
    return RSTTree(filepath, debug=debug)


def get_relations_from_rs3file(rs3_filepath):
    utf8_parser = etree.XMLParser(encoding="utf-8")
    rs3_xml_tree = etree.parse(rs3_filepath, utf8_parser)
    return extract_relationtypes(rs3_xml_tree)


def no_double_ns(tree, filename, debug=False, root_id=None):
    """Return True, iff there is no nucleus/satellite in the given ParentedTree
    that has a nucleus or satellite as a child node.
    """
    assert isinstance(tree, ParentedTree)

    if root_id is None:
        root_id = tree.root_id
    expected_labels = [debug_root_label('N', debug=debug, root_id=root_id),
                       debug_root_label('S', debug=debug, root_id=root_id)]

    tree_label = tree.label()
    tree_has_nsroot = tree_label in expected_labels

    for node in tree:
        if isinstance(node, ParentedTree):
            if tree_has_nsroot and node.label() in expected_labels:
                return False

            subtree_is_okay = no_double_ns(node, filename, debug=debug, root_id=root_id)
            if not subtree_is_okay:
                return False

    return True


def test_no_double_ns():
    """The test function no_double_ns() works as expected."""
    bad_tree = t('N', [
        ('S', ['foo']),
        ('N', ['bar'])
    ])

    bad_embedded_tree = t('joint', [
        ('N', [
            ('N', ['foo'])
        ]),
        ('N', ['bar']),
    ])

    good_tree = t('elabortate', [
        ('S', ['foo']),
        ('N', ['bar'])
    ])

    assert no_double_ns(bad_tree, "testfile") == False
    assert no_double_ns(bad_embedded_tree, "testfile") == False
    assert no_double_ns(good_tree, "testfile") == True


def relnodes_have_ns_children(rst_tree, tree=None, debug=False, root_id=None):
    """Return True, iff every relation node (either rst or multinuc) in the
    given RSTTree has only nucleii and/or satellites as children.
    """
    def expected_labels(root_rel, debug, root_id):
        labels = ('N', 'S') if root_rel == 'rst' else ('N')
        return [debug_root_label(label, debug=debug, root_id=root_id)
                for label in labels]

    if tree is None:
        tree = rst_tree.tree

    if root_id is None:
        root_id = tree.root_id

    assert isinstance(tree, ParentedTree)
    relations = get_relations_from_rs3file(rst_tree.filepath)
    relations[VIRTUAL_ROOT] = 'multinuc'

    norm_tree_label = tree.label().split()[0] # works for 'label' and 'label (node_id)'
    tree_has_relroot = norm_tree_label in relations
    if tree_has_relroot:
        root_rel = relations[norm_tree_label]

    for node in tree:
        if isinstance(node, ParentedTree):
            if tree_has_relroot and node.label() not in expected_labels(root_rel, debug, node.root_id):
                logging.log(
                    logging.WARN,
                    "File {0}: Node '{1}' has child '{2}'".format(
                        os.path.basename(rst_tree.filepath), norm_tree_label, node.label()))
                return False

            subtree_is_okay = relnodes_have_ns_children(
                rst_tree, tree=node, debug=debug, root_id=root_id)
            if not subtree_is_okay:
                return False

    return True


def test_relnodes_have_ns_children():
    """The test function relnodes_have_ns_children works as expected."""
    # we will only use the rst_tree to extract relations
    dummy_rst_tree = example2tree('maz-00001-excerpt.rs3', rs3tree_dir=RS3TREE_DIR)

    bad_inner = ('conjunction', [
        ('explanation', [
            ('S', ['foo']),
            ('N', ['bar'])
        ]),
        n(['5'])
    ])

    bad_tree = t('cause', [
        s(['3']),
        n([bad_inner])
    ])

    good_inner = ('conjunction', [
        n(['4']),
        n(['5'])
    ])

    good_tree = t('cause', [
        s(['3']),
        n([good_inner])
    ])

    # disable logging for expected warning
    logging.disable(logging.CRITICAL)
    assert relnodes_have_ns_children(dummy_rst_tree, tree=bad_tree, debug=False, root_id=None) is False
    logging.disable(logging.NOTSET)

    assert relnodes_have_ns_children(dummy_rst_tree, tree=good_tree, debug=False, root_id=None) is True


def no_span_nodes(tree, debug=False, root_id=None):
    """Return True, iff there is no span node in the given ParentedTree."""
    assert isinstance(tree, ParentedTree)

    if root_id is None:
        root_id = tree.root_id
    span_label = debug_root_label('span', debug=debug, root_id=root_id)

    if tree.label() == span_label:
        return False

    for node in tree:
        if isinstance(node, ParentedTree) :
            if node.label() == span_label:
                return False

            subtree_is_okay = no_span_nodes(node, debug=debug, root_id=root_id)
            if not subtree_is_okay:
                return False

    return True


def test_no_span_nodes():
    """The no_span_nodes test function works as expected."""
    good_tree = t('joint', [
        ('N', ['foo']),
        ('N', [
            ('background', [
                ('S', ['bar']),
                ('N', ['baz'])])]),
        ]
    )

    bad_tree = t('joint', [
        ('N', ['foo']),
        ('N', [
            ('span', [
                ('S', ['bar']),
                ('N', ['baz'])])]),
        ]
    )

    assert no_span_nodes(good_tree) is True
    assert no_span_nodes(bad_tree) is False


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


def test_pcc_00001():
    # original error: A multinuc segment (18) should not have children: ['40']
    #  WARNING:root:File maz-00001.rs3: Node 'conjunction' has child 'condition'
    produced = example2tree('maz-00001-excerpt.rs3', rs3tree_dir=RS3TREE_DIR)

    con_4_5 = ('conjunction', [
        n(['4']),
        n(['5'])
    ])

    cause_3_5 = ('cause', [
        s(['3']),
        n([con_4_5])
    ])

    cause_6_7 = ('cause', [
        n(['6']),
        s(['7'])
    ])

    inter_3_7 = ('interpretation', [
        n([cause_3_5]),
        s([cause_6_7])
    ])

    inter_2_7 = ('interpretation', [
        s(['2']),
        n([inter_3_7])
    ])

    eval_2_8 = ('evaluation-n', [
        s([inter_2_7]),
        n(['8'])
    ])

    cond_13_14 = ('condition', [
        n(['13']),
        s(['14'])
    ])

    conj_12_14 = ('conjunction', [
        n(['12']),
        n([cond_13_14])
    ])

    evidence_11_14 = ('evidence', [
        n(['11']),
        s([conj_12_14])
    ])

    reason_10_14 = ('reason', [
        n(['10']),
        s([evidence_11_14])
    ])

    list_9_14 = ('list', [
        n(['9']),
        n([reason_10_14])
    ])

    reason_2_14 = ('reason', [
        n([eval_2_8]),
        s([list_9_14])
    ])

    reason_17_18 = ('reason', [
        n(['17']),
        s(['18'])
    ])

    conj_16_18 = ('conjunction', [
        n(['16']),
        n([reason_17_18])
    ])

    reason_15_18 = ('reason', [
        n(['15']),
        s([conj_16_18])
    ])

    elab_19_20 = ('elaboration', [
        n(['19']),
        s(['20'])
    ])

    dis_21_22 = ('disjunction', [
        n(['21']),
        n(['22'])
    ])

    inter_19_22 = ('interpretation', [
        s([elab_19_20]),
        n([dis_21_22])
    ])

    result_15_22 = ('result', [
        n([reason_15_18]),
        s([inter_19_22])
    ])

    joint_2_22 = ('joint', [
        n([reason_2_14]),
        n([result_15_22])
    ])

    expected = t(VIRTUAL_ROOT, [
        n(['1']),
        n([joint_2_22])
    ])

    assert produced.edu_strings == produced.tree.leaves() == [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
        '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22']
    assert expected == produced.tree


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

    expected = t(VIRTUAL_ROOT, [
        ('N', ['1']),
        ('N', [background_2_23])
    ])

    assert produced.edu_strings == produced.tree.leaves() == [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
        '11', '12', '13', '14', '15', '16', '17', '18', '19',
        '20', '21', '22', '23']
    assert expected == produced.tree


def test_segments_only_trees():
    """Files without a single root must get a virtual one."""
    # minimal case: file without any segments
    produced = example2tree("empty.rs3")
    expected = t("", [])

    assert produced.edu_strings == produced.tree.leaves() == []
    assert expected == produced.tree

    # one segment only
    produced = example2tree('only-one-segment.rs3')
    expected = t("N", ["foo"])

    assert produced.edu_strings == produced.tree.leaves() == ['foo']
    assert expected == produced.tree

    # two segments w/out a root
    produced = example2tree("foo-bar-only-segments.rs3")
    expected = t(VIRTUAL_ROOT,
                 [("N", ["foo"]), ("N", ["bar"])])

    assert produced.edu_strings == produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    # three segments w/out a root
    produced = example2tree('eins-zwei-drei-only-segments.rs3')
    expected = t(VIRTUAL_ROOT,
                 [("N", ["eins"]), ("N", ["zwei"]), ("N", ["drei"])])

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree


def test_single_nucsat_relation():
    produced = example2tree("foo-bar-circ-foo-to-bar.rs3")
    expected = t("circumstance", [
        ("S", ["foo"]),
        ("N", ["bar"])])

    assert produced.edu_strings == produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree("foo-bar-elab-foo-to-bar.rs3")
    expected = t("elaboration", [
        ("S", ["foo"]),
        ("N", ["bar"])])

    assert produced.edu_strings == produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree("foo-bar-circ-bar-to-foo.rs3")
    expected = t("circumstance", [
        ("N", ["foo"]),
        ("S", ["bar"])])

    assert produced.edu_strings == produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree("foo-bar-elab-bar-to-foo.rs3")
    expected = t("elaboration", [
        ("N", ["foo"]),
        ("S", ["bar"])])

    assert produced.edu_strings == produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree


def test_single_nucsat_relation_topspan():
    """It doesn't matter if there is a span above a single N-S relation."""
    produced1 = example2tree("foo-bar-circ-foo-to-bar-plus-top-span.rs3")
    produced2 = example2tree("foo-bar-circ-foo-to-bar.rs3")
    expected = t("circumstance", [
        ("S", ["foo"]),
        ("N", ["bar"])])

    assert produced1.edu_strings == produced1.tree.leaves() == ['foo', 'bar']
    assert produced2.edu_strings == produced2.tree.leaves() == ['foo', 'bar']
    assert expected == produced1.tree == produced2.tree


def test_single_multinuc_relation_topspan():
    """It doesn't matter if there is a span above a single multinuc relation."""
    produced1 = example2tree("foo-bar-foo-joint-bar.rs3")
    produced2 = example2tree("foo-bar-foo-joint-bar-plus-top-span.rs3")
    expected = t("joint", [
        ("N", ["foo"]),
        ("N", ["bar"])])

    assert produced1.edu_strings == produced1.tree.leaves() == ['foo', 'bar']
    assert produced2.edu_strings == produced2.tree.leaves() == ['foo', 'bar']
    assert expected == produced1.tree == produced2.tree


def test_single_multinuc_relation():
    produced = example2tree("foo-bar-foo-joint-bar.rs3")
    expected = t("joint", [
        ("N", ["foo"]),
        ("N", ["bar"])])

    assert produced.edu_strings == produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree("foo-bar-foo-conj-bar.rs3")
    expected = t("conjunction", [
        ("N", ["foo"]),
        ("N", ["bar"])])

    assert produced.edu_strings == produced.tree.leaves() == ['foo', 'bar']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(joint-eins-and-zwei-and-drei).rs3')
    expected = t("joint", [
        ("N", ["eins"]),
        ("N", ["zwei"]),
        ("N", ["drei"])])

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree


def test_nested_nucsat_relation():
    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-to-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("circumstance", [
                ("S", ["eins"]),
                ("N", ["zwei"])])]),
        ("S", ["drei"])])

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-from-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("circumstance", [
                ("N", ["eins"]),
                ("S", ["zwei"])])]),
        ("S", ["drei"])])

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-from-zwei)-to-drei).rs3')
    expected = t("circumstance", [
        ("S", [
            ("circumstance", [
                ("N", ["eins"]),
                ("S", ["zwei"])])]),
        ("N", ["drei"])])

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-to-zwei)-to-drei.rs3')
    expected = t("circumstance", [
        ("S", [
            ("circumstance", [
                ("S", ["eins"]),
                ("N", ["zwei"])])]),
        ("N", ["drei"])])

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree


def test_nested_nucsat_multinuc_relation():
    produced = example2tree('eins-zwei-drei-(circ-eins-to-(joint-zwei-and-drei).rs3')
    expected = t("circumstance", [
        ("S", ["eins"]),
        ("N", [
            ("joint", [
                ("N", ["zwei"]),
                ("N", ["drei"])])])])

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
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

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-eins-from-(joint-zwei-and-drei).rs3')
    expected = t("circumstance", [
        ("N", ["eins"]),
        ("S", [
            ("joint", [
                ("N", ["zwei"]),
                ("N", ["drei"])])])])

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
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

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
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

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei']
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

    assert produced1.edu_strings == produced1.tree.leaves() == ['eins', 'zwei', 'drei']
    assert produced2.edu_strings == produced2.tree.leaves() == ['eins', 'zwei', 'drei']
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

    assert produced.edu_strings == produced.tree.leaves() == ['eins', 'zwei', 'drei', 'vier', 'fuenf']
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

    assert produced1.edu_strings == produced1.tree.leaves() == ['eins', 'zwei', 'drei']
    assert produced2.edu_strings == produced2.tree.leaves() == ['eins', 'zwei', 'drei']
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

    assert produced1.edu_strings == produced1.tree.leaves() == ['eins', 'zwei', 'drei', 'vier']
    assert produced2.edu_strings == produced2.tree.leaves() == ['eins', 'zwei', 'drei', 'vier']
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

    expected = t(VIRTUAL_ROOT, [
        n(['1']),
        n([inter_2_18])
    ])

    assert produced.edu_strings == produced.tree.leaves() == [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
        '11', '12', '13', '14', '15', '16', '17', '18']
    assert expected == produced.tree


def test_multinuc_with_two_satellites():
    """A multinuc that is also the nucleus of two other RST relations
    is handled correctly.
    """
    produced = example2tree('multinuc-plus-two-satellites.rs3', rs3tree_dir=RS3TREE_DIR)

    joint_5_6 = ('joint', [
        ('N', ['fuenf']),
        ('N', ['sechs'])
    ])

    conj_2_3 = ('conjunction', [
        ('N', ['zwei']),
        ('N', ['drei'])
    ])

    inter_2_4 = ('interpretation', [
        ('N', [conj_2_3]),
        ('S', ['vier'])
    ])

    inter_2_6 = ('interpretation', [
        ('N', [inter_2_4]),
        ('S', [joint_5_6])])

    expected = t('interpretation', [
        ('S', ['eins']),
        ('N', [inter_2_6])
    ])

    assert produced.edu_strings == produced.tree.leaves() == [
        'eins', 'zwei', 'drei', 'vier', 'fuenf', 'sechs']
    assert expected == produced.tree


def test_parse_complete_pcc():
    """All *.rs3 files can be parsed into RSTTree instances."""
    okay = 0.0
    fail = 0.0
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        try:
            x = dg.readwrite.RSTTree(rfile)
            okay += 1
        except Exception as e:
            logging.log(logging.WARN,
                    "File '{0}' can't be parsed into an RSTTree: {1}".format(
                        os.path.basename(rfile), e))
            fail += 1

    success_rate = okay / (okay+fail) * 100
    assert success_rate == 100, \
        "{0}% of PCC files could be parsed ({1} of {2})".format(success_rate, okay, okay+fail)


def test_complete_pcc_edu_order():
    """The order of EDUs in all generated RSTTrees is the same as in the
    original *.rs3 files.
    """
    okay = 0.0
    fail = 0.0
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        try:
            rst_tree = dg.readwrite.RSTTree(rfile)
            if rst_tree.edu_strings == rst_tree.tree.leaves():
                okay += 1
            else:
                fail += 1

                logging.log(logging.WARN,
                        "EDU order in file '{}' is wrong!".format(
                            os.path.basename(rfile)))

        except TooManyChildrenError as e:
            pass

    success_rate = okay / (okay+fail) * 100
    assert success_rate == 100, \
        "\n{0}% of parsed PCC files have correct EDU order ({1} of {2})".format(success_rate, okay, okay+fail)


def test_complete_pcc_no_double_ns():
    """There is no PCC file in which a nucleus/satellite has a nucleus or
    satellite as a child.
    """
    okay = 0.0
    fail = 0.0
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        filename = os.path.basename(rfile)
        try:
            rst_tree = dg.readwrite.RSTTree(rfile)
            if no_double_ns(rst_tree.tree, filename):
                okay += 1
            else:
                fail += 1

                logging.log(logging.WARN,
                        "File '{}' has N/S->N/S parent/child".format(
                            os.path.basename(rfile)))

        except TooManyChildrenError as e:
            pass

    success_rate = okay / (okay+fail) * 100
    assert success_rate == 100, \
        "\n{0}% of parsed PCC files have no N/S->N/S parent/child ({1} of {2})".format(success_rate, okay, okay+fail)

    okay = 0.0
    fail = 0.0
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        filename = os.path.basename(rfile)
        try:
            rst_tree = dg.readwrite.RSTTree(rfile)
            if no_double_ns(rst_tree.tree, filename, debug=True):
                okay += 1
            else:
                fail += 1

                logging.log(logging.WARN,
                        "File '{}' has N/S->N/S parent/child in debug mode".format(
                            os.path.basename(rfile)))

        except TooManyChildrenError as e:
            pass

    success_rate = okay / (okay+fail) * 100
    assert success_rate == 100, \
        "\n{0}% of debug-parsed PCC files have no N/S->N/S parent/child ({1} of {2})".format(success_rate, okay, okay+fail)


def test_complete_pcc_relnodes_have_ns_children():
    """All relation nodes in all PCC files have only nucleii and/or satellites
    as children.
    """
    debug = False
    okay = 0.0
    fail = 0.0
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        filename = os.path.basename(rfile)
        try:
            rst_tree = dg.readwrite.RSTTree(rfile, debug=debug)
            if relnodes_have_ns_children(rst_tree, debug=debug):
                okay += 1
            else:
                fail += 1
                logging.log(logging.WARN,
                        "File '{}' has bad relname children".format(
                            os.path.basename(rfile)))

        except TooManyChildrenError as e:
            pass

    success_rate = okay / (okay+fail) * 100
    assert success_rate == 100, \
        "\n{0}% of parsed PCC files have  only relname->N/S parent/child relations ({1} of {2})".format(success_rate, okay, okay+fail)

    debug = True
    okay = 0.0
    fail = 0.0
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        filename = os.path.basename(rfile)
        try:
            rst_tree = dg.readwrite.RSTTree(rfile, debug=debug)
            if relnodes_have_ns_children(rst_tree, debug=debug):
                okay += 1
            else:
                relnodes_have_ns_children(rst_tree, debug=debug)

                fail += 1
                logging.log(logging.WARN,
                        "File '{}' has bad relname children in debug-mode".format(
                            os.path.basename(rfile)))

        except TooManyChildrenError as e:
            pass

    success_rate = okay / (okay+fail) * 100
    assert success_rate == 100, \
        "\n{0}% of debug-parsed PCC files have  only relname->N/S parent/child relations ({1} of {2})".format(success_rate, okay, okay+fail)


def test_complete_pcc_no_span_nodes():
    """There are no 'span' nodes in any PCC file."""
    okay = 0.0
    fail = 0.0

    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        filename = os.path.basename(rfile)
        try:
            rst_tree = dg.readwrite.RSTTree(rfile)
            if no_span_nodes(rst_tree.tree, debug=rst_tree.debug):
                okay += 1
            else:
                fail += 1
                logging.log(logging.WARN,
                        "File '{}' has bad span nodes".format(
                            os.path.basename(rfile)))

        except TooManyChildrenError as e:
            pass

    success_rate = okay / (okay+fail) * 100
    assert success_rate == 100, \
        "\n{0}% of parsed PCC files have no bad span nodes ({1} of {2})".format(success_rate, okay, okay+fail)

    okay = 0.0
    fail = 0.0
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        filename = os.path.basename(rfile)
        try:
            rst_tree = dg.readwrite.RSTTree(rfile, debug=True)
            if no_span_nodes(rst_tree.tree, debug=rst_tree.debug):
                okay += 1
            else:
                fail += 1
                logging.log(logging.WARN,
                        "File '{}' has bad span nodes in debug mode".format(
                            os.path.basename(rfile)))

        except TooManyChildrenError as e:
            pass

    success_rate = okay / (okay+fail) * 100
    assert success_rate == 100, \
        "\n{0}% of debug-parsed PCC files have no bad span nodes ({1} of {2})".format(success_rate, okay, okay+fail)


def test_fix_one_edu_span():
    """A span consisting of only one EDU is parsed correctly."""
    produced = example2tree('one-edu-span.rs3', rs3tree_dir=RS3TREE_DIR)
    expected = t(
        'preparation', [
            ('S', ['13']),
            ('N', [
                ('antithesis', [
                    ('S', ['14']),
                    ('N', [
                        ('interpretation', [
                            ('N', ['15']),
                            ('S', ['16'])])])])])])

    assert no_span_nodes(produced.tree)
    assert produced.edu_strings == produced.tree.leaves() == [
        '13', '14', '15', '16']
    assert expected == produced.tree

