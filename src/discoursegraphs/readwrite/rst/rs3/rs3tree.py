#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""This module converts .rs3 files into `NLTK ParentedTree`s."""

import codecs
from collections import defaultdict
import logging
import tempfile
import textwrap
from operator import itemgetter, methodcaller
import os

from lxml import etree
from lxml.builder import E

from discoursegraphs.readwrite.tree import (
    DGParentedTree, debug_root_label, p, t, is_leaf)
from discoursegraphs.readwrite.rst.rs3 import extract_relationtypes

NUCLEARITY_LABELS = ('N', 'S')
VIRTUAL_ROOT = 'virtual-root'


class SchemaTypes(object):
    """Enumerator of RST schema types"""
    one_sided = 'one_sided' # S-S-N or N-S-S
    two_sided = 'two_sided' # S-N-S


class NoRootError(ValueError):
    """An RST Tree with multiple nodes without an ancestor."""
    pass


class TooManyChildrenError(ValueError):
    """An RST node with more child nodes than the theory allows."""
    pass


class TooFewChildrenError(ValueError):
    """An RST node with less child nodes than the theory allows."""
    pass


class RSTTree(object):
    """An RSTTree is a DGParentedTree representation of an .rs3 file."""
    def __init__(self, rs3_file, word_wrap=0, debug=False):
        self.debug = debug
        self.filepath = rs3_file
        self.child_dict, self.elem_dict, self.edus, self.reltypes = \
            get_rs3_data(rs3_file, word_wrap=word_wrap)
        self.edu_set = set(self.edus)
        self.edu_strings = [self.elem_dict[edu_id]['text']
                            for edu_id in self.edus]
        self.tree = self.dt()

    @classmethod
    def fromstring(cls, rs3_string):
        """Create an RSTTree instance from a string content an *.rs3 file."""
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(rs3_string)
        temp.close()
        rst_tree = cls(rs3_file=temp.name)
        os.unlink(temp.name)
        return rst_tree

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

    def pprint(self):
        """Return an s-expression representation of the RSTTree.

        Note: This looks like the .dis format (i.e. the format used by
        the RST-DT corpus, but it would still need some post-processing
        to be compatible.
        """
        return self.tree.pprint()

    def __getitem__(self, key):
        return self.tree.__getitem__(key)

    def node_height(self, node_id):
        assert node_id in self.elem_dict

        height = 0
        lookup_id = node_id

        while lookup_id is not None:
            lookup_id = self.elem_dict[lookup_id]['parent']
            height += 1
        return height

    def get_relname(self, node_id):
        return self.elem_dict[node_id]['relname']

    def dt(self, start_node=None):
        """main method to create an RSTTree from the output of get_rs3_data().

        TODO: add proper documentation
        """
        if start_node is None:
            return self.root2tree(start_node=start_node)

        elem_id = start_node
        if elem_id not in self.elem_dict:
            return []

        elem = self.elem_dict[elem_id]
        elem_type = elem['element_type']

        assert elem_type in ('segment', 'group')

        if elem_type == 'segment':
            return self.segment2tree(
                elem_id, elem, elem_type, start_node=start_node)

        else:
            return self.group2tree(
                elem_id, elem, elem_type, start_node=start_node)

    def root2tree(self, start_node=None):
        root_nodes = self.child_dict[start_node]
        num_roots = len(root_nodes)
        if num_roots == 1:
            return self.dt(start_node=root_nodes[0])
        elif num_roots > 1:
            # An undesired, but common case (at least in the PCC corpus).
            # This happens if there's one EDU not to connected to the rest
            # of the tree (e.g. a headline). We will just make all 'root'
            # nodes part of a multinuc relation called VIRTUAL_ROOT.
            logging.log(logging.INFO,
                        "File '{}' has {} roots!".format(
                            os.path.basename(self.filepath), num_roots))

            root_subtrees = [n_wrap(self.dt(start_node=root_id),
                                    debug=self.debug, root_id=root_id)
                             for root_id in root_nodes]
            sorted_subtrees = self.sort_subtrees(*root_subtrees)

            # assign the root_id of the highest subtree to the virtual root
            max_height, virtual_root_id = max((st.height(), st.root_id)
                                              for st in sorted_subtrees)

            return t(VIRTUAL_ROOT, sorted_subtrees, debug=self.debug,
                     root_id=virtual_root_id)
        else:
            return t('')

    def group2tree(self, elem_id, elem, elem_type, start_node=None):
        reltype = elem.get('reltype')
        root_wrap = s_wrap if reltype == 'rst' else n_wrap

        # rst: this elem is the S in an N-S relation
        # multinuc: this elem is one of several Ns in a multinuc relation
        if reltype in ('rst', 'multinuc'):
            if len(self.child_dict[elem_id]) == 1:
                # this group is the root of another N-S relation
                subtree_id = self.child_dict[elem_id][0]
                subtree = self.dt(start_node=subtree_id)

            else:
                subtrees = [self.elem_wrap(self.dt(start_node=c), debug=self.debug, root_id=c)
                            for c in self.child_dict[elem_id]]
                sorted_subtrees = self.sort_subtrees(*subtrees)
                first_child_id = self.child_dict[elem_id][0]
                subtrees_relname = self.get_relname(first_child_id)
                subtree = t(subtrees_relname, sorted_subtrees, debug=self.debug, root_id=elem_id)
            return root_wrap(subtree, debug=self.debug, root_id=elem_id)

        else:
            assert reltype in ('', None, 'span'), \
                "Unexpected combination: elem_type '%s' and reltype '%s'" \
                    % (elem_type, elem['reltype'])

            # this elem is the N in an N-S relation
            if elem['group_type'] == 'multinuc':
                # this elem is also the 'root node' of a multinuc relation
                child_ids = self.child_dict[elem_id]
                multinuc_child_ids = [c for c in child_ids
                                      if self.elem_dict[c]['reltype'] == 'multinuc']
                multinuc_relname = self.get_relname(multinuc_child_ids[0])

                multinuc_elements = [self.dt(start_node=mc)
                                     for mc in multinuc_child_ids]
                sorted_subtrees = self.sort_subtrees(*multinuc_elements)

                multinuc_subtree = t(
                    multinuc_relname, [sorted_subtrees], debug=self.debug,
                    root_id=elem_id)

                other_child_ids = [c for c in child_ids
                                   if c not in multinuc_child_ids]

                if other_child_ids:
                    # this element is the N in an S-N-S schema
                    nuc_tree = t('N', multinuc_subtree, debug=self.debug, root_id=elem_id)

                    assert all([self.elem_dict[child_id]['nuclearity'] == 'satellite'
                                for child_id in other_child_ids])

                    sat_subtrees = [self.dt(start_node=child_id)
                                    for child_id in other_child_ids]
                    return self.order_schema(nuc_tree, sat_subtrees)

                else:
                    # this elem is only the head of a multinuc relation
                    # TODO: does this make sense / is this ever reached?
                    return multinuc_subtree

            else:
                #~ assert elem['group_type'] == 'span', \
                    #~ "Unexpected group_type '%s'" % elem['group_type']
                if len(self.child_dict[elem_id]) == 1:
                    # this span at the top of a tree was only added for visual purposes
                    child_id = self.child_dict[elem_id][0]
                    return self.dt(start_node=child_id)

                elif len(self.child_dict[elem_id]) == 2:
                    # this elem is the N of an N-S relation (child: S), but is also
                    # a span over another relation (child: N)
                    children = {}
                    for child_id in self.child_dict[elem_id]:
                        children[self.elem_dict[child_id]['nuclearity']] = child_id

                    sat_id = children['satellite']
                    sat_subtree = self.dt(start_node=sat_id)

                    nuc_subtree = self.dt(start_node=children['nucleus'])
                    nuc_tree = n_wrap(nuc_subtree, debug=self.debug, root_id=elem_id)

                    return self.sorted_nucsat_tree(nuc_tree, sat_subtree)

                elif len(self.child_dict[elem_id]) > 2:
                    children = defaultdict(list)
                    for child_id in self.child_dict[elem_id]:
                        children[self.elem_dict[child_id]['nuclearity']].append(child_id)

                    assert len(children['nucleus']) == 1

                    nuc_subtree = self.dt(start_node=children['nucleus'][0])
                    nuc_tree = t('N', nuc_subtree, debug=self.debug, root_id=elem_id)

                    sat_subtrees = [self.dt(start_node=sat_child_id)
                                    for sat_child_id in children['satellite']]

                    return self.order_schema(nuc_tree, sat_subtrees)

                else: #len(child_dict[elem_id]) == 0
                    raise TooFewChildrenError(
                        "A span group ('%s)' should have at least 1 child: %s" \
                            % (elem_id, self.child_dict[elem_id]))

    def segment2tree(self, elem_id, elem, elem_type, start_node=None):
        if elem['reltype'] == 'rst':
            # this elem is the S in an N-S relation
            root_label = 'S'
        else:
            root_label = 'N'

        tree = t(root_label, [elem['text']], debug=self.debug, root_id=elem_id)

        if elem_id not in self.child_dict:
            # this might be a root segment without any children
            # (e.g. a headline in PCC) or the only segment in a span
            # (which makes no sense in RST)
            if elem.get('reltype') in ('span', '', None):
                if elem['nuclearity'] != 'root':
                    logging.log(
                        logging.INFO,
                        "Segment '{}' in file '{}' is a non-root nucleus without children".format(
                            elem_id, os.path.basename(self.filepath)))

                    if elem.get('relname') == 'span':
                        parent_elem = self.elem_dict.get(elem.get('parent'))
                        if parent_elem:
                            elem['relname'] = parent_elem.get('relname')

            return tree

        if len(self.child_dict[elem_id]) == 1:
            # this segment is (also) the N in an N-S relation
            sat_id = self.child_dict[elem_id][0]
            sat_subtree = self.dt(start_node=sat_id)
            return self.sorted_nucsat_tree(tree, sat_subtree)

        elif len(self.child_dict[elem_id]) >= 2:
            # this segment is (also) the N in an RST schema,
            # as such it must only have satellites as children
            assert all([self.elem_dict[child_id]['nuclearity'] == 'satellite'
                        for child_id in self.child_dict[elem_id]])

            sat_subtrees = [self.dt(start_node=child_id)
                            for child_id in self.child_dict[elem_id]]
            return self.order_schema(tree, sat_subtrees)

    def order_schema(self, nuc_tree, sat_trees):
        nuc_pos = self.get_linear_position(nuc_tree)
        sat_tree_pos_tuples = [(sat_tree, self.get_linear_position(sat_tree))
                               for sat_tree in sat_trees]
        sat_tree_pos_tuples = sorted(sat_tree_pos_tuples, key=itemgetter(1))

        assert not any(
            [sat_pos == nuc_pos
             for (sat_tree, sat_pos) in sat_tree_pos_tuples]), \
             "Subtrees can't have the same linear positions."

        sat_trees_prec_nuc = []
        sat_trees_succ_nuc = []
        for (sat_tree, sat_pos) in sat_tree_pos_tuples:
            if sat_pos < nuc_pos:
                sat_trees_prec_nuc.append((sat_tree, sat_pos))
            else:
                sat_trees_succ_nuc.append((sat_tree, sat_pos))

        # A N is combined with its preceeding satellites in
        # this way (nuc-3 (nuc-2 (nuc-1 nuc))), while succeeding
        # satellites are combined like this: (((nuc nuc+1) nuc+2) nuc+3).
        # Therefore, it is easier to reverse the list of preceeding
        # satellites for combining N with all satellites.
        sat_trees_prec_nuc.reverse()

        prec_heights = [t.height() for (t, pos) in sat_trees_prec_nuc]
        succ_heights = [t.height() for (t, pos) in sat_trees_succ_nuc]

        max_height_prec = max(prec_heights) if prec_heights else 0
        max_height_succ = max(succ_heights) if succ_heights else 0

        if max_height_prec >= max_height_succ:
            return self.convert_schema(
                (nuc_tree, nuc_pos), sat_trees_prec_nuc, sat_trees_succ_nuc)
        else:
            return self.convert_schema(
                (nuc_tree, nuc_pos), sat_trees_succ_nuc, sat_trees_prec_nuc)

    def convert_schema(self, nuc_tuple, inner_sat_tuples, outer_sat_tuples):
        """subtrees are represented as (tree, linear tree position) tuples.

        returns relation as root node.
        """
        nuc_tree, nuc_pos = nuc_tuple
        sat_tuples = inner_sat_tuples + outer_sat_tuples
        last_sat_tuple_pos = len(sat_tuples)-1

        for i, (sat_tree, sat_pos) in enumerate(sat_tuples):
            relname = self.get_relname(sat_tree.root_id)
            if sat_pos < nuc_pos:
                ordered_trees = [sat_tree, nuc_tree]
            else:
                ordered_trees = [nuc_tree, sat_tree]

            if i == last_sat_tuple_pos:
                nuc_tree = t(relname, ordered_trees, debug=self.debug, root_id=nuc_tree.root_id)
            else:
                nuc_tree = t('N', [(relname, ordered_trees)], debug=self.debug, root_id=nuc_tree.root_id)
        return nuc_tree

    def get_linear_position(self, subtree):
        first_leaf_text = subtree.leaves()[0]
        return self.edu_strings.index(first_leaf_text)

    def sort_subtrees(self, *subtrees):
        """sort the given subtrees (of type DGParentedTree) based on their
        linear position in this RSTTree. If two subtrees have the same
        linear position in the RSTTree (i.e. one is a child of the other),
        they are sorted by their height in reverse order (i.e. the child
        appears before its parent).
        """
        subtrees_desc_height = sorted(subtrees,
                                      key=methodcaller('node_height', self),
                                      reverse=True)
        return sorted(subtrees_desc_height,
                      key=methodcaller('get_position', self))

    def sorted_nucsat_tree(self, nuc_tree, sat_tree):
        sorted_subtrees = self.sort_subtrees(nuc_tree, sat_tree)
        relname = self.get_relname(sat_tree.root_id)
        return t(relname, sorted_subtrees, debug=self.debug, root_id=nuc_tree.root_id)

    def elem_wrap(self, tree, debug=False, root_id=None):
        """takes a DGParentedTree and puts a nucleus or satellite on top,
        depending on the nuclearity of the root element of the tree.
        """
        if root_id is None:
            root_id = tree.root_id

        elem = self.elem_dict[root_id]
        if elem['nuclearity'] == 'nucleus':
            return n_wrap(tree, debug=debug, root_id=root_id)
        else:
            return s_wrap(tree, debug=debug, root_id=root_id)


def get_rs3_data(rs3_file, word_wrap=0):
    """helper function to build RSTTrees: data on parent-child relations
    and node attributes.

    TODO: add proper documentation
    """
    rs3_etree = etree.parse(rs3_file)
    reltypes = extract_relationtypes(rs3_etree)

    elements = defaultdict(lambda: defaultdict(str))
    children = defaultdict(list)
    ordered_edus = []

    for elem in rs3_etree.iter('segment', 'group'):
        elem_id = elem.attrib['id']
        parent_id = elem.attrib.get('parent')
        elements[elem_id]['parent'] = parent_id
        children[parent_id].append(elem_id)

        relname = elem.attrib.get('relname')
        elements[elem_id]['relname'] = relname
        if relname is None:
            # Nodes without a parent have no relname attribute.
            # They might well the N of a relation.
            elements[elem_id]['nuclearity'] = 'root'
        else:
            reltype = reltypes.get(relname, 'span')
            elements[elem_id]['reltype'] = reltype
            if reltype == 'rst':
                # this elem is the S of an N-S relation, its parent is the N
                elements[elem_id]['nuclearity'] = 'satellite'
            elif reltype == 'multinuc':
                # this elem is one of several Ns of a multinuc relation.
                # its parent is the multinuc relation node.
                elements[elem_id]['nuclearity'] = 'nucleus'
            elif reltype == 'span':
                # this elem is the N of an N-S relation, its parent is a span
                elements[elem_id]['nuclearity'] = 'nucleus'
            else:
                raise NotImplementedError("Unknown reltype: {}".format(reltypes[relname]))

        elem_type = elem.tag
        elements[elem_id]['element_type'] = elem_type

        if elem_type == 'segment':
            edu_text = normalize_edu_string(elem.text)
            if word_wrap != 0:
                dedented_text = textwrap.dedent(edu_text).strip()
                edu_text = textwrap.fill(dedented_text, width=word_wrap)

            elements[elem_id]['text'] = edu_text
            ordered_edus.append(elem_id)

        else:  # elem_type == 'group':
            elements[elem_id]['group_type'] = elem.attrib.get('type')

    if len(elements) > 0:
        # add VIRTUAL_ROOT to reltypes dict for export, but only if the
        # rs3 file is not empty
        reltypes[VIRTUAL_ROOT] = 'multinuc'

    return children, elements, ordered_edus, reltypes


def normalize_edu_string(edu_string):
    """Remove superfluous whitespace from an EDU and return it."""
    return u' '.join(edu_string.strip().split())


def n(children):
    return ('N', children)


def s(children):
    return ('S', children)


def n_wrap(tree, debug=False, root_id=None):
    """Ensure the given tree has a nucleus as its root.

    If the root of the tree is a nucleus, return it.
    If the root of the tree is a satellite, replace the satellite
    with a nucleus and return the tree.
    If the root of the tree is a relation, place a nucleus on top
    and return the tree.
    """
    root_label = tree.label()

    expected_n_root = debug_root_label('N', debug=debug, root_id=tree.root_id)
    expected_s_root = debug_root_label('S', debug=debug, root_id=tree.root_id)

    if root_label == expected_n_root:
        return tree
    elif root_label == expected_s_root:
        tree.set_label(expected_n_root)
        return tree
    else:
        return t('N', [tree], debug=debug, root_id=root_id)


def s_wrap(tree, debug=False, root_id=None):
    """Ensure the given tree has a nucleus as its root.

    If the root of the tree is a satellite, return it.
    If the root of the tree is a nucleus, replace the nucleus
    with a satellite and return the tree.
    If the root of the tree is a relation, place a satellite on top
    and return the tree.
    """
    root_label = tree.label()

    expected_n_root = debug_root_label('N', debug, tree.root_id)
    expected_s_root = debug_root_label('S', debug, tree.root_id)

    if root_label == expected_s_root:
        return tree
    elif root_label == expected_n_root:
        tree.set_label(expected_s_root)
        return tree
    else:
        return t('S', [tree], debug=debug, root_id=root_id)


def extract_relations(dgtree, relations=None):
    """Extracts relations from a DGParentedTree.

    Given a DGParentedTree, returns a (relation name, relation type) dict
    of all the RST relations occurring in that tree.
    """
    if hasattr(dgtree, 'reltypes'):
        # dgtree is an RSTTree or a DisTree that contains a DGParentedTree
        return dgtree.reltypes

    if relations is None:
        relations = {}

    if is_leaf(dgtree):
        return relations

    root_label = dgtree.label()
    if root_label == '':
        assert dgtree == DGParentedTree('', []), \
            "The tree has no root label, but isn't empty: {}".format(dgtree)
        return relations
    elif root_label in NUCLEARITY_LABELS:
        for child in dgtree:
            relations.update(extract_relations(child, relations))
    else:  # dgtree is a 'relation' node
        child_labels = [child.label() for child in dgtree]
        assert all(label in NUCLEARITY_LABELS for label in child_labels)
        if 'S' in child_labels:
            relations[root_label] = 'rst'
        else:
            relations[root_label] = 'multinuc'
        for child in dgtree:
            relations.update(extract_relations(child, relations))

    return relations


# pseudo-function to create a document tree from a .rs3 file
read_rs3tree = RSTTree


