#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""Basic tests for the ``rs3tree`` module"""

import os

import pytest

from discoursegraphs import t
from discoursegraphs.readwrite.rst.rs3 import RSTTree
import discoursegraphs as dg


def example2tree(rs3tree_example_filename):
    """Return the absolute path of an example file."""
    filepath = os.path.join(dg.DATA_ROOT_DIR, 'rs3tree',
                            rs3tree_example_filename)
    return RSTTree(filepath)


def test_segments_only_trees():
    """Files without a single root must get a virtual one."""
    # minimal case: file without any segments
    produced = example2tree("empty.rs3")
    expected = t("")

    assert expected == produced.tree

    # one segment only
    produced = example2tree('only-one-segment.rs3')
    expected = t("foo")

    assert expected == produced.tree

    # two segments w/out a root
    produced = example2tree("foo-bar-only-segments.rs3")
    expected = t("virtual-root",
                 [("N", "foo"), ("N", "bar")])

    assert expected == produced.tree

    # three segments w/out a root
    produced = example2tree('eins-zwei-drei-only-segments.rs3')
    expected = t("virtual-root",
                 [("N", "eins"), ("N", "zwei"), ("N", "drei")])

    assert expected == produced.tree


def test_single_nucsat_relation():
    produced = example2tree("foo-bar-circ-foo-to-bar.rs3")
    expected = t("circumstance", [
        ("S", "foo"),
        ("N", "bar")])

    assert expected == produced.tree

    produced = example2tree("foo-bar-elab-foo-to-bar.rs3")
    expected = t("elaboration", [
        ("S", "foo"),
        ("N", "bar")])

    assert expected == produced.tree

    produced = example2tree("foo-bar-circ-bar-to-foo.rs3")
    expected = t("circumstance", [
        ("N", "foo"),
        ("S", "bar")])

    assert expected == produced.tree

    produced = example2tree("foo-bar-elab-bar-to-foo.rs3")
    expected = t("elaboration", [
        ("N", "foo"),
        ("S", "bar")])

    assert expected == produced.tree


def test_single_nucsat_relation_topspan():
    """It doesn't matter if there is a span above a single N-S relation."""
    produced1 = example2tree("foo-bar-circ-foo-to-bar-plus-top-span.rs3")
    produced2 = example2tree("foo-bar-circ-foo-to-bar.rs3")
    expected = t("circumstance", [
        ("S", "foo"),
        ("N", "bar")])
    assert expected == produced1.tree == produced2.tree


def test_single_multinuc_relation_topspan():
    """It doesn't matter if there is a span above a single multinuc relation."""
    produced1 = example2tree("foo-bar-foo-joint-bar.rs3")
    produced2 = example2tree("foo-bar-foo-joint-bar-plus-top-span.rs3")
    expected = t("joint", [
        ("N", "foo"),
        ("N", "bar")])

    assert expected == produced1.tree == produced2.tree


def test_single_multinuc_relation():
    produced = example2tree("foo-bar-foo-joint-bar.rs3")
    expected = t("joint", [
        ("N", "foo"),
        ("N", "bar")])

    assert expected == produced.tree

    produced = example2tree("foo-bar-foo-conj-bar.rs3")
    expected = t("conjunction", [
        ("N", "foo"),
        ("N", "bar")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(joint-eins-and-zwei-and-drei).rs3')
    expected = t("joint", [
        ("N", "eins"),
        ("N", "zwei"),
        ("N", "drei")])

    assert expected == produced.tree


def test_nested_nucsat_relation():
    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-to-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("circumstance", [
                ("S", "eins"),
                ("N", "zwei")])]),
        ("S", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-from-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("circumstance", [
                ("N", "eins"),
                ("S", "zwei")])]),
        ("S", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-from-zwei)-to-drei).rs3')
    expected = t("circumstance", [
        ("S", [
            ("circumstance", [
                ("N", "eins"),
                ("S", "zwei")])]),
        ("N", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-to-zwei)-to-drei.rs3')
    expected = t("circumstance", [
        ("S", [
            ("circumstance", [
                ("S", "eins"),
                ("N", "zwei")])]),
        ("N", "drei")])

    assert expected == produced.tree


def test_nested_nucsat_multinuc_relation():
    produced = example2tree('eins-zwei-drei-(circ-eins-to-(joint-zwei-and-drei).rs3')
    expected = t("circumstance", [
        ("S", "eins"),
        ("N", [
            ("joint", [
                ("N", "zwei"),
                ("N", "drei")])])])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(joint-eins-and-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("joint", [
                ("N", "eins"),
                ("N", "zwei")
            ])
        ]),
        ("S", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-eins-from-(joint-zwei-and-drei).rs3')
    expected = t("circumstance", [
        ("N", "eins"),
        ("S", [
            ("joint", [
                ("N", "zwei"),
                ("N", "drei")])])])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(joint-eins-and-zwei)-to-drei).rs3')
    expected = t("circumstance", [
        ("S", [
            ("joint", [
                ("N", "eins"),
                ("N", "zwei")
            ])
        ]),
        ("N", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(elab-eins-from-(joint-zwei-and-drei).rs3')
    expected = t('elaboration', [
        ("N", "eins"),
        ("S", [
            ("joint", [
                ("N", "zwei"),
                ("N", "drei")
            ])
        ])
    ])

    assert expected == produced.tree


def test_single_schema():
    produced1 = example2tree("schema-elab-elab.rs3")

    expected = t('elaboration', [
        ('N', [
            ('elaboration', [
                ('S', 'eins'),
                ('N', 'zwei')
            ])
        ]),
        ('S', 'drei')
    ])

    assert expected == produced1.tree


def test_single_schema_topspan():
    produced1 = example2tree("schema-elab-elab.rs3")
    produced2 = example2tree("schema-elab-elab-plus-top-span.rs3")

    expected = t('elaboration', [
        ('N', [
            ('elaboration', [
                ('S', 'eins'),
                ('N', 'zwei')
            ])
        ]),
        ('S', 'drei')
    ])

    assert expected == produced1.tree == produced2.tree

"""
maz-10575.rs3

dt('33'):
    group2tree('33'):
        ...
        assert elem.get('reltype') in ('', 'span')
        ...
        if len(self.child_dict[elem_id]) == 1:
            ...
            return dt('32')

dt('32'):
    group2tree('32'):
        ...
        assert elem.get('reltype') in ('', 'span')
        ...
        elif len(self.child_dict[elem_id]) == 2:
            sat_subtree = self.dt(start_node=sat_id='30')
            
dt('30'):
    group2tree('30'):
        if elem['reltype'] == 'rst':
            if len(self.child_dict[elem_id]) == 1:
                subtree = self.dt(start_node=subtree_id='29')

dt('29'):
    group2tree('29'):
        ...
        assert elem.get('reltype') in ('', 'span')
        ...
        if elem['group_type'] == 'multinuc':

            >>> multinuc_subtree.pretty_print()
                             contrast                         
                    ____________|_______                       
                   |                    N                     
                   |                    |                      
                   |                  cause                   
                   |             _______|___________           
                   N            N                   S         
                   |            |                   |          
            Viele aus Intere einige ,        weil es in ander 
                 sse ,          |            en Gruppen keine 
                   |            |           n Platz mehr gab .
                   |            |                   |          
                  ...          ...                 ...        

            >>> other_child_ids                                                                                                                                                     
            ['8', '10']

            >>> sat1_tree = self.dt(start_node='8', debug=debug)

            >>> sat1_tree.pretty_print()
                    S        
                    |         
             Die 30 Mädchen  
            und Jungen haben 
              sich eher zufä 
               llig in der   
             Neigungsgruppe  
              Biologie und   
             Umwelt zusammeng
                efunden .    
                    |         
                   ... 

            >>> sat2_tree = self.dt(start_node='10', debug=debug)
            >>> sat2_tree.pretty_print()
                   S        
                   |         
            Vielleicht fande
            n auch die geste
              rn die Bestä  
             tigung , dass  
             sie letztlich  
            doch gar keine  
             so schlechte   
            Wahl getroffen  
                haben .     
                   |         
                  ... 

            else:  #len(other_child_ids) > 1
                raise TooManyChildrenError
                

"""
def test_parse_complete_pcc():
    okay = 0.0
    fail = 0.0
    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        try:
            x = dg.readwrite.RSTTree(rfile)
            okay += 1
        except Exception as e:
            print i, os.path.basename(rfile), "FAIL"
            print "\t", e
            #~ import pudb; pudb.set_trace()
            #~ x = dg.readwrite.RSTTree(rfile)
            fail += 1


    print "{}% success".format(okay / (okay+fail) * 100)
    assert okay == 176
