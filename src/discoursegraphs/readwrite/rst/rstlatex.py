#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code to generate figures of RST trees in Latex
(using the rst.sty package).
"""

# Python 2/3 compatibility
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import codecs
import string
import re

import nltk

from discoursegraphs.readwrite.rst.rs3.rs3tree import RSTTree


MULTISAT_RELNAME = 'MONONUC-MULTISAT'

RSTSEGMENT_TEMPLATE = string.Template("""\\rstsegment{$segment}""") # \rstsegment{Foo}
NUC_TEMPLATE = string.Template("""{}{$nucleus}""")
SAT_TEMPLATE = string.Template("""{$relation}{$satellite}""")

MULTINUC_TEMPLATE = string.Template("""\multirel{$relation}$nucleus_segments""")

RSTLATEX_TREE_RE = re.compile("\\\(dirrel|multirel)")


class RSTLatexFileWriter(object):
    def __init__(self, tree, output_filepath=None):
        self.tree = tree
        self.rstlatextree = rsttree2rstlatex(tree)

        if output_filepath is not None:
            with codecs.open(output_filepath, 'w', 'utf-8') as outfile:
                outfile.write(self.rstlatextree + '\n')

    def __str__(self):
        return self.rstlatextree


def is_nltktreelike(obj):
    """Returns true, iff the given object behaves like an nltk.Tree.

    This is a "duck-typing" workaround as most RST tree classes do not
    inherit from nltk.Tree but rather embed it.
    """
    return hasattr(obj, 'label') and callable(obj.label)


def get_node_type(tree):
    """Returns the type of the root node of the given RST tree
    (one of 'N', 'S', 'relation' or 'edu'.)
    """
    if is_nltktreelike(tree):
        if tree.label() in ('N', 'S'):
            return tree.label()
        else:
            return 'relation'

    elif isinstance(tree, basestring):
        return 'edu'

    else:
        raise ValueError("Unknown tree/node type: {}".format(type(tree)))


def is_edu_segment(rstlatex_string):
    """Returns true, iff the given string does not contain an RST subtree."""
    return RSTLATEX_TREE_RE.search(rstlatex_string) is None


def wrap_edu_segment(edu_segment):
    """Wraps the string content of an EDU in RST Latex markup."""
    return RSTSEGMENT_TEMPLATE.substitute(segment=edu_segment)


def make_nucsat(relname, nuc_types, elements):
    """Creates a rst.sty Latex string representation of a standard RST relation
    (one nucleus, one satellite).
    """
    assert len(elements) == 2 and len(nuc_types) == 2, \
        "A nucsat relation must have two elements."
    assert set(nuc_types) == set(['N', 'S']), \
        "A nucsat relation must consist of one nucleus and one satellite."
 
    result = "\dirrel"
    for i, nuc_type in enumerate(nuc_types):
        element = elements[i]
        if is_edu_segment(element):
            element = wrap_edu_segment(element)

        if nuc_type == 'N':
            result += '\n\t' + NUC_TEMPLATE.substitute(nucleus=element)
        else:
            result += '\n\t' + SAT_TEMPLATE.substitute(satellite=element, relation=relname)
    return result


def make_multinuc(relname, nucleii):
    """Creates a rst.sty Latex string representation of a multi-nuclear RST relation."""
    nuc_strings = []
    for nucleus in nucleii:
        if is_edu_segment(nucleus):
            nucleus = wrap_edu_segment(nucleus)

        nuc_strings.append(nucleus)
    nucleii_string = "\n\t" + "\n\t".join(nuc_strings)
    return MULTINUC_TEMPLATE.substitute(relation=relname, nucleus_segments=nucleii_string)


def make_multisat(nucsat_tuples):
    """Creates a rst.sty Latex string representation of a multi-satellite RST subtree
    (i.e. merge a set of nucleus-satellite relations that share the same nucleus
    into one subtree).
    """
    nucsat_tuples = [tup for tup in nucsat_tuples]  # unpack the iterable, so we can check its length
    assert len(nucsat_tuples) > 1, \
        "A multisat relation bundle must contain more than one relation"

    result = "\dirrel\n\t"
    first_relation, remaining_relations = nucsat_tuples[0], nucsat_tuples[1:]
    
    relname, nuc_types, elements = first_relation
    first_nucleus_pos = current_nucleus_pos = nuc_types.index('N')
    result_segments = []

    # add children (nucleus and satellites) to resulting (sub)tree
    for i, nuc_type in enumerate(nuc_types):
        element = elements[i]
        if is_edu_segment(element):
            element = wrap_edu_segment(element)

        if nuc_type == 'N':
            result_segments.append(NUC_TEMPLATE.substitute(nucleus=element))
        else:
            result_segments.append(SAT_TEMPLATE.substitute(satellite=element, relation=relname))

    # reorder children
    for (relname, nuc_types, elements) in remaining_relations:
        for i, nuc_type in enumerate(nuc_types):
            if nuc_type == 'N':  # all relations share the same nucleus, so we don't need to reprocess it.
                continue
            else:
                result_segment = SAT_TEMPLATE.substitute(satellite=elements[i], relation=relname)
                if i < first_nucleus_pos:  # satellite comes before the nucleus
                    result_segments.insert(current_nucleus_pos, result_segment)
                    current_nucleus_pos += 1
                else:
                    result_segments.append(result_segment)
    
    return result + '\n\t'.join(result_segments)


def rsttree2rstlatex(tree, indent_level=0):
    node_type = get_node_type(tree)
    if node_type == 'relation':
        relname = tree.label()
        
        expected_types = set(['N', 'S'])
        child_node_types = [get_node_type(child) for child in tree]
        observed_types = set(child_node_types)

        unexpected_types = observed_types.difference(expected_types)
        assert unexpected_types == set(), \
            "Observed types ({}) contain unexpected types ({})".format(observed_types, unexpected_types)
        
        subtree_strings = [rsttree2rstlatex(grandchild, indent_level=indent_level+1)
                           for child in tree
                           for grandchild in child]

        if observed_types == set('N'):  # relation only consists of nucleii
            return indent_tab(make_multinuc(relname=relname, nucleii=subtree_strings), indent_level)

        elif relname == MULTISAT_RELNAME:  # multiple relations sharing the same nucleus
            relations = [grandchild for child in tree for grandchild in child]
            relnames = [rel.label() for rel in relations]
            nuctypes_per_relation = [[elem.label() for elem in relation] for relation in relations]
            subtree_strings_per_relation = [[rsttree2rstlatex(elem[0]) for elem in relation] for relation in relations]
            nucsat_tuples = zip(relnames, nuctypes_per_relation, subtree_strings_per_relation)
            return indent_tab(make_multisat(nucsat_tuples), indent_level)
        
        else: # a "normal" relation between one nucleus and one satellite
            assert len(child_node_types) == 2, "A nuc/sat relationship must consist of two elements"
            return indent_tab(make_nucsat(relname, child_node_types, subtree_strings), indent_level)

    elif node_type == 'edu':
        return " ".join(tree.split())

    elif node_type in ('N', 'S'):  # a single segment not in any relation
        return indent_tab(string.Template("\rstsegment{$content}").substitute(content=tree[0]), indent_level)

    else:
        raise ValueError("Can't handle this node: {}".format(tree.label())) 


def indent(text, amount, ch=' '):
    """Indents a string by the given amount of characters."""
    padding = amount * ch
    return ''.join(padding+line for line in text.splitlines(True))

def indent_tab(text, number):
    """Indents a string by the given number of tabs (one tab = 8 spaces)."""
    return indent(text, number, '\t')


def write_rstlatex(tree, output_file=None):
    """Converts an RST tree into a rst.sty Latex string representation"""
    return RSTLatexFileWriter(tree, output_filepath=output_file)
