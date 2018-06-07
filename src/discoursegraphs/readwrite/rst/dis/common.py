#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains common functions for parsing *.dis files
(used by old versions of RSTTool to annotate rhetorical structure).

It contains some MIT licensed code from
github.com/EducationalTestingService/discourse-parsing
"""

from collections import defaultdict
import os
import re
import tempfile

from nltk.tree import ParentedTree

from discoursegraphs.readwrite.ptb import PTB_BRACKET_ESCAPE


ROOT = 'Root'
NUC = 'Nucleus'
SAT = 'Satellite'
SUBTREE_TYPES = (ROOT, NUC, SAT)
NODE_TYPES = ('leaf', 'span')


class DisFile(object):
    """A DisFile instance represents the structure of a *.dis file as a ParentedTree.

    NOTE: The resulting tree represents the file format (i.e. the syntax of a *.dis file),
    not its meaning (i.e. it doesn't look like an RST tree).
    """
    def __init__(self, dis_filepath):
        self.filepath = dis_filepath

        with open(dis_filepath) as disfile:
            rst_tree_str = disfile.read().strip()
            rst_tree_str = fix_rst_treebank_tree_str(rst_tree_str)
            rst_tree_str = convert_parens_in_rst_tree_str(rst_tree_str)
            self.tree = ParentedTree.fromstring(rst_tree_str)

    @classmethod
    def fromstring(cls, dis_string):
        """Create a DisFile instance from a string containing a *.dis parse."""
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(dis_string)
        temp.close()
        dis_file = cls(dis_filepath=temp.name)
        os.unlink(temp.name)
        return dis_file


def get_edu_text(text_subtree):
    """return the text of the given EDU subtree"""
    assert text_subtree.label() == 'text', "text_subtree: {}".format(text_subtree)
    # remove '_!' prefix and suffix from EDU
    leaves = text_subtree.leaves()
    leaves[0] = leaves[0].lstrip('_!')
    leaves[-1] = leaves[-1].rstrip('_!')
    return u' '.join(word.decode('utf-8') for word in leaves)


def get_tree_type(tree):
    """
    returns the type of the (sub)tree: Root, Nucleus or Satellite

    Parameters
    ----------
    tree : nltk.tree.ParentedTree
        a tree representing a rhetorical structure (or a part of it)
    """
    tree_type = tree.label()
    assert tree_type in SUBTREE_TYPES, "tree_type: {}".format(tree_type)
    return tree_type


def get_node_type(tree):
    """
    returns the node type (leaf or span) of a subtree (i.e. Nucleus or Satellite)

    Parameters
    ----------
    tree : nltk.tree.ParentedTree
        a tree representing a rhetorical structure (or a part of it)
    """
    node_type = tree[0].label()
    assert node_type in NODE_TYPES, "node_type: {}".format(node_type)
    return node_type


def get_node_id(nuc_or_sat, namespace=None):
    """return the node ID of the given nucleus or satellite"""
    node_type = get_node_type(nuc_or_sat)
    if node_type == 'leaf':
        leaf_id = nuc_or_sat[0].leaves()[0]
        if namespace is not None:
            return '{0}:{1}'.format(namespace, leaf_id)
        else:
            return string(leaf_id)

    #else: node_type == 'span'
    span_start = nuc_or_sat[0].leaves()[0]
    span_end = nuc_or_sat[0].leaves()[1]
    if namespace is not None:
        return '{0}:span:{1}-{2}'.format(namespace, span_start, span_end)
    else:
        return 'span:{0}-{1}'.format(span_start, span_end)

def get_relation_type(tree):
    """
    returns the RST relation type attached to the parent node of an RST relation,
    e.g. `span`, `elaboration` or `antithesis`.

    Parameters
    ----------
    tree : nltk.tree.ParentedTree
        a tree representing a rhetorical structure (or a part of it)

    Returns
    -------
    relation_type : str
        the type of the rhetorical relation that this (sub)tree represents
    """
    return tree[1][0]


def get_child_types(children):
    """
    maps from (sub)tree type (i.e. Nucleus or Satellite) to a list
    of all children of this type
    """
    child_types = defaultdict(list)
    for i, child in enumerate(children):
        child_types[get_tree_type(child)].append(i)
    return child_types


def fix_rst_treebank_tree_str(rst_tree_str):
    '''
    This removes some unexplained comments in two files that cannot be parsed.
    - data/RSTtrees-WSJ-main-1.0/TRAINING/wsj_2353.out.dis
    - data/RSTtrees-WSJ-main-1.0/TRAINING/wsj_2367.out.dis

    source: github.com/EducationalTestingService/discourse-parsing
    original license: MIT
    '''
    return re.sub(r'\)//TT_ERR', ')', rst_tree_str)


def convert_parens_in_rst_tree_str(rst_tree_str):
    '''
    This converts any brackets and parentheses in the EDUs of the RST discourse
    treebank to look like Penn Treebank tokens (e.g., -LRB-),
    so that the NLTK tree API doesn't crash when trying to read in the
    RST trees.

    source: github.com/EducationalTestingService/discourse-parsing
    original license: MIT
    '''
    for bracket_type, bracket_replacement in PTB_BRACKET_ESCAPE.items():
        rst_tree_str = \
            re.sub('(_![^_(?=!)]*)\\{}([^_(?=!)]*_!)'.format(bracket_type),
                   '\\g<1>{}\\g<2>'.format(bracket_replacement),
                   rst_tree_str)
    return rst_tree_str
