#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""Basic tests for the ``rs3tree`` module"""

import os

import pytest

from discoursegraphs import t
from discoursegraphs.readwrite.tree import p
from discoursegraphs.readwrite.rst.rs3 import RSTTree
import discoursegraphs as dg

RS3TREE_DIR = os.path.join(dg.DATA_ROOT_DIR, 'rs3tree')
PCC_RS3_DIR = os.path.join(dg.DATA_ROOT_DIR,
                           'potsdam-commentary-corpus-2.0.0', 'rst')


def example2tree(rs3tree_example_filename, rs3tree_dir=RS3TREE_DIR):
    """Return the absolute path of an example file."""
    filepath = os.path.join(rs3tree_dir, rs3tree_example_filename)
    return RSTTree(filepath)


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


"""
children = defaultdict(list)
for child_id in self.child_dict[elem_id]:
    children[self.elem_dict[child_id]['nuclearity']].append(child_id)

nuc_subtree = self.dt(start_node=children['nucleus'], debug=debug)
nuc_tree = t('N', nuc_subtree, debug=debug, root_id=elem_id)


group2tree('32'):
    else: 3 span group nucleus

            >>> elem
            {'nuclearity': 'nucleus', 'parent': '33',
             'element_type': 'group', 'reltype': 'span',
             'relname': 'span', 'group_type': 'span'}

        elif len(self.child_dict[elem_id]) > 2:
            raise TooManyChildrenError

                >>> self.child_dict[elem_id] # '32'
                ['26', '28', '31']

                >>> sat26_tree = self.dt(start_node='26', debug=debug)
                >>> sat26_tree.pretty_print()
                (S, interpretation ... "Reste vom Sonntag ... teuer zu stehen")

                >>> sat28_tree.pretty_print()
                (S, reason ... "Entsorgung nur noch ... Appelle umsonst") # EDU 17-19, relation restatement

                >>> sat31_tree.pretty_print() # no 'N' or 'S' as root
                (reason, [N cause, S e-elab] ... "Denn angesichts ... dringend benötigt"

                >>> children
                defaultdict(list, {'nucleus': ['31'], 'satellite': ['26', '28']})


"""
@pytest.mark.xfail
def test_pcc_8501():
    produced = example2tree('maz-8509.rs3', rs3tree_dir=PCC_RS3_DIR)
    assert 1 == 0


@pytest.mark.xfail
def test_parse_complete_pcc():
    okay = 0.0
    fail = 0.0
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        try:
            x = dg.readwrite.RSTTree(rfile)
            okay += 1
        except Exception as e:
            #~ print i, os.path.basename(rfile), "FAIL"
            #~ print "\t", e
            #~ import pudb; pudb.set_trace()
            #~ x = dg.readwrite.RSTTree(rfile)
            fail += 1

    print "{}% success".format(okay / (okay+fail) * 100)
    assert okay == 176
