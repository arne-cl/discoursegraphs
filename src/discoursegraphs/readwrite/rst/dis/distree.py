#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts a *.dis file (used by old versions of RSTTool to
annotate rhetorical structure) into an DisTree.
"""

import argparse
import os
import sys
import tempfile

from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.readwrite.rst.dis.common import (
    DisFile, get_child_types, get_edu_text, get_node_type, get_relation_type,
    get_tree_type, ROOT, NUC, SAT, SUBTREE_TYPES)
from discoursegraphs.readwrite.tree import t, word_wrap_tree


class DisRSTTree(object):
    """An DisRSTTree is a DGParentedTree representation (Rhetorical Structure tree)
    parsed from a .dis file."""
    def __init__(self, dis_filepath, word_wrap=0, debug=False):
        self.debug = debug
        self.filepath = dis_filepath
        self.child_dict, self.elem_dict, self.edus, self.reltypes = None, None, None, None # FIXME: implement if needed
        self.edu_set = None  # FIXME: implement if needed
        self.edu_strings = None  # FIXME: implement if needed
        
        self.disfile_tree = DisFile(dis_filepath).tree
        tree = dis2tree(self.disfile_tree)
        self.tree = word_wrap_tree(tree, width=word_wrap)

    @classmethod
    def fromstring(cls, dis_string):
        """Create a DisRSTTree instance from a string containing a *.dis parse."""
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(dis_string)
        temp.close()
        dis_tree = cls(dis_filepath=temp.name)
        os.unlink(temp.name)
        return dis_tree

    def _repr_png_(self):
        """This PNG representation will be automagically used inside
        IPython notebooks.
        """
        return self.tree._repr_png_()

    def __str__(self):
        return self.tree.__str__()

    def label(self):
        return self.tree.label()

    def pretty_print(self):
        """Return a pretty-printed representation of the RSTTree."""
        return self.tree.pretty_print()

    def __getitem__(self, key):
        return self.tree.__getitem__(key)


def dis2tree(dis_tree, wrap_tree=False):
    assert get_tree_type(dis_tree) in SUBTREE_TYPES, "tree_type: {}".format(get_tree_type(dis_tree))
    if get_node_type(dis_tree) == 'leaf':
        return leaf2tree(dis_tree)
    
    if is_root(dis_tree):
        children = dis_tree[1:]
    else:
        children = dis_tree[2:]

    child_types = get_child_types(children)    
    if len(child_types) == 1: # this is a multinuc relation
        assert NUC in child_types, "child_types: {}".format(child_types)
        assert len(child_types[NUC]) > 1, "len: {}".format(len(child_types[NUC]))
        
        subtrees = [dis2tree(children[child_id], wrap_tree=True) for child_id in child_types[NUC]]
        
        # all subtrees of a multinuc have the same relation, so we can just read it from the first one
        reltype = get_relation_type(children[0])      
        
    else: # this is a nucleus-satellite relation
        assert len(child_types) == 2, "child_types: {}".format(child_types)
        assert NUC in child_types and SAT in child_types, "child_types: {}".format(child_types)
        assert len(child_types[NUC]) == 1 and len(child_types[SAT]) == 1, \
            "child_types: {}".format(child_types)
        
        nuc_child_id = child_types[NUC][0]
        nuc_subtree = dis2tree(children[nuc_child_id], wrap_tree=True)

        sat_child_id = child_types[SAT][0]
        sat_child = children[sat_child_id]
        sat_subtree = dis2tree(sat_child, wrap_tree=True)

        # determine order of subtrees
        if nuc_child_id < sat_child_id:
            subtrees = [nuc_subtree, sat_subtree]
        else:
            subtrees = [sat_subtree, nuc_subtree]
        
        # the relation type is only stored in the satellite
        reltype = get_relation_type(sat_child)

    rst_tree = t(reltype, subtrees)
    return get_wrapped_tree(dis_tree, rst_tree, wrap_tree=wrap_tree)


def get_wrapped_tree(dis_tree, rst_tree, wrap_tree=False):
    if wrap_tree:
        tree_wrapper = get_element_wrapper(dis_tree)
        return tree_wrapper(rst_tree)
    return rst_tree


def is_root(dis_tree):
    return get_tree_type(dis_tree) == ROOT


def leaf2tree(dis_subtree):
    assert get_tree_type(dis_subtree) in SUBTREE_TYPES, "tree_type: {}".format(get_tree_type(dis_subtree))
    assert get_node_type(dis_subtree) == 'leaf', "node_type: {}".format(get_node_type(dis_subtree))

    elem_wrapper = get_element_wrapper(dis_subtree)
    return elem_wrapper([get_edu_text(dis_subtree[2])])


def get_element_wrapper(dis_tree):
    label = dis_tree.label()
    return n_wrap if label == NUC else s_wrap


def n_wrap(tree):
    return t('N', [tree])


def s_wrap(tree):
    return t('S', [tree])


# pseudo-function to create a document tree from a RST (.dis) file
read_distree = DisRSTTree


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='*.dis RST file to be converted')
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)
    
    DisRSTTree(args.input_file).pretty_print()
