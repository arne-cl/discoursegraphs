#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts `DGParentedTree`s into .dis files.
"""

import codecs
import os
import re

import discoursegraphs as dg
from discoursegraphs.readwrite.tree import DGParentedTree, t, is_leaf


class DisFileWriter(object):
    def __init__(self, dgtree, output_filepath=None):
        # dgtree is an RSTTree or DisTree (and contains a DGParentedTree / nltk.tree.ParentedTree)
        if hasattr(dgtree, 'tree') and isinstance(dgtree.tree, DGParentedTree):
            dgtree = dgtree.tree

        self.dgtree = dgtree
        self.disfiletree = convert(dgtree)

        if output_filepath is not None:
            with codecs.open(output_filepath, 'w', 'utf-8') as outfile:
                outfile.write(self.to_dis_format())

    def to_dis_format(self):
        """Return a string representation of the tree in .dis format."""
        dis_raw_str = self.disfiletree.pformat()
        return re.sub('_!(.*?)_!', join_lines, dis_raw_str, flags=re.DOTALL)

    def _repr_png_(self):
        """This PNG representation will be automagically used inside
        IPython notebooks.
        """
        return self.disfiletree._repr_png_()

    def __str__(self):
        return self.disfiletree.__str__()

    def pretty_print(self):
        """Return a pretty-printed representation of the RSTTree."""
        return self.disfiletree.pretty_print()

    def __getitem__(self, key):
        return self.disfiletree.__getitem__(key)


def convert(parented_tree):
    if is_root(parented_tree):
        span_description = make_span(parented_tree)
        children = [span_description]
        for subtree in get_nucsat_subtrees(parented_tree):
            children.append(convert(subtree))
        orphaned_children = [orphanize(child) for child in children]
        return t('Root', orphaned_children)
    elif is_leaf(parented_tree):
        return make_edu(parented_tree)
    else:
        span_description = make_span(parented_tree)
        rel_description = make_rel2par(parented_tree)
        children = [span_description, rel_description]
        for subtree in get_nucsat_subtrees(parented_tree):
            children.append(convert(subtree))
        tree_label = convert_label(parented_tree.label())
        orphaned_children = [orphanize(child) for child in children]
        return t(tree_label, orphaned_children)


def is_root(parented_tree):
    return hasattr(parented_tree, 'parent') and parented_tree.parent() is None


def subtree_leaf_positions(subtree):
    """Return tree positions of all leaves of a subtree."""
    relative_leaf_positions = subtree.treepositions('leaves')
    subtree_root_pos = subtree.treeposition()
    absolute_leaf_positions = []
    for rel_leaf_pos in relative_leaf_positions:
        absolute_leaf_positions.append( subtree_root_pos + rel_leaf_pos)
    return absolute_leaf_positions


def all_leaf_positions(parented_tree):
    """Return tree positions of all leaves of a ParentedTree,
    even if the input is only a subtree of that ParentedTree.
    """
    return parented_tree.root().treepositions('leaves')


def make_span(parented_tree):
    """create a 'span' or 'leaf' subtree for dis/lisp/RST-DT-formatted trees.
    
    Examples:
           span     (a subtree that covers the leaves 1 to 7)
         ___|____   
        1        7 

        leaf        (a subtree that only covers leaf 7)
         |   
         7
    """
    all_leaves = all_leaf_positions(parented_tree)
    if is_root(parented_tree):
        return t('span', ['1', str(len(all_leaves))])
    
    subtree_leaves = subtree_leaf_positions(parented_tree)
    if len(subtree_leaves) == 1:
        edu_id = all_leaves.index(subtree_leaves[0]) + 1
        return t('leaf', [str(edu_id)])
    elif len(subtree_leaves) > 1:
        first_edu_id = all_leaves.index(subtree_leaves[0]) + 1
        last_edu_id = all_leaves.index(subtree_leaves[-1]) + 1
        return t('span', [str(first_edu_id), str(last_edu_id)])
    else:
        raise NotImplementedError('Subtree has no leaves')


def get_siblings(parented_subtree):
    subtree_pos = parented_subtree.treeposition()
    parent = parented_subtree.parent()
    if parent is None:
        return []
    
    siblings = []
    for child in parent:
        child_pos = child.treeposition()
        if child_pos != subtree_pos:
            siblings.append(child_pos)
    return siblings


def make_rel2par(nuc_or_sat_subtree):
    if is_root(nuc_or_sat_subtree):
        raise ValueError("Root node can't have a relation.")
    subtree_root_label = nuc_or_sat_subtree.label()
    parent_label = nuc_or_sat_subtree.parent().label()
    if subtree_root_label == 'S':
        return t('rel2par', [parent_label])
    elif subtree_root_label == 'N':
        siblings = get_siblings(nuc_or_sat_subtree)
        root = nuc_or_sat_subtree.root()
        sibling_labels = [root[sib].label() for sib in siblings]
        if len(siblings) == 1 and sibling_labels[0] == 'S':
            return t('rel2par', ['span'])
        elif all([label == 'N' for label in sibling_labels]):
            return t('rel2par', [parent_label])
        else:
            raise ValueError(
                "Can't mix sibling types. Expected 'N' or 'S', got: {}".format(sibling_labels))
    else:
        raise ValueError(
            "Unknown nuclearity. Expected 'N' or 'S', got: {}".format(subtree_root_label))


def make_edu(edu_string):
    tokens = edu_string.split()
    tokens[0] = u'_!' + tokens[0]
    tokens[-1] = tokens[-1] + u'_!'
    return t('text', tokens)


def get_nucsat_subtrees(parented_tree):
    """Return all direct children of the given tree, that are either
    a nucleus, satellite or a leaf node (i.e. all children except
    for relation nodes.)
    """
    if is_leaf(parented_tree):
        return [parented_tree]
    
    nucsat_children = []
    for child in parented_tree:
        if  is_leaf(child) or child.label() in ('N', 'S'):
            nucsat_children.append(child)
        else:
            nucsat_children.extend( get_nucsat_subtrees(child) )
    return nucsat_children


def orphanize(parented_subtree):
    if is_leaf(parented_subtree):
        return parented_subtree
    else:
        parented_subtree._parent = None
        return parented_subtree


def convert_label(label):
    if label == 'N':
        return 'Nucleus'
    elif label == 'S':
        return 'Satellite'
    else:
        return label


def join_lines(matchobj):
    edu_multiline_str = matchobj.group(0)
    ed_oneline_str = u' '.join(line.strip()
                               for line in edu_multiline_str.splitlines())
    return re.sub('\n', '', ed_oneline_str)


def write_dis(dgtree, output_file=None):
    """Convert a DGParentedTree representation of an RST tree into a .dis file"""
    return DisFileWriter(dgtree, output_filepath=output_file)

