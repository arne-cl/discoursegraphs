#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""This module converts .rs3 files into `NLTK ParentedTree`s."""

from collections import defaultdict
import textwrap
from operator import itemgetter, methodcaller

from lxml import etree

from discoursegraphs.readwrite.tree import t, p, debug_root_label
from discoursegraphs.readwrite.rst.rs3 import extract_relationtypes


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
        self.child_dict, self.elem_dict, self.edus = get_rs3_data(rs3_file, word_wrap=word_wrap)
        self.edu_set = set(self.edus)
        self.edu_strings = [self.elem_dict[edu_id]['text']
                            for edu_id in self.edus]
        self.tree = self.dt()

    def _repr_png_(self):
        """This PNG representation will be automagically used inside
        IPython notebooks.
        """
        return self.tree._repr_png_()

    def __str__(self):
        return self.tree.__str__()

    def pretty_print(self):
        """Return a pretty-printed representation of the RSTTree."""
        return self.tree.pretty_print()

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
        if len(root_nodes) == 1:
            return self.dt(start_node=root_nodes[0])
        elif len(root_nodes) > 1:
            # An undesired, but common case (at least in the PCC corpus).
            # This happens if there's one EDU not to connected to the rest
            # of the tree (e.g. a headline). We will just make all 'root'
            # nodes part of a multinuc relation called 'virtual-root'.
            root_subtrees = [self.dt(start_node=root_id)
                             for root_id in root_nodes]
            # ensure that each subtree is marked as a nucleus
            nuc_subtrees = [n_wrap(st, debug=self.debug) for st in root_subtrees]
            return t('virtual-root', nuc_subtrees, debug=self.debug)
        else:
            return t('')

    def group2tree(self, elem_id, elem, elem_type, start_node=None):
        if elem['reltype'] == 'rst':
            # this elem is the S in an N-S relation

            if len(self.child_dict[elem_id]) == 1:
                # this elem is the S in an N-S relation, but it's also the root of
                # another N-S relation
                subtree_id = self.child_dict[elem_id][0]
                subtree = self.dt(start_node=subtree_id)

            else:
                assert len(self.child_dict[elem_id]) > 1
                # this elem is the S in an N-S relation, but it's also the root of
                # a multinuc relation
                subtrees = [self.dt(start_node=c)
                            for c in self.child_dict[elem_id]]
                sorted_subtrees = self.sort_subtrees(*subtrees)
                first_child_id = self.child_dict[elem_id][0]
                subtrees_relname = self.elem_dict[first_child_id]['relname']

                subtree = t(subtrees_relname, sorted_subtrees, debug=self.debug, root_id=elem_id)
            return s_wrap(subtree, debug=self.debug, root_id=elem_id)

        elif elem['reltype'] == 'multinuc':
            # this elem is one of several Ns in a multinuc relation
            subtrees = [self.dt(start_node=c)
                        for c in self.child_dict[elem_id]]
            return t('N', subtrees, debug=self.debug, root_id=elem_id)

        else:
            assert elem.get('reltype') in ('', 'span'), \
                "Unexpected combination: elem_type '%s' and reltype '%s'" \
                    % (elem_type, elem['reltype'])

            # this elem is the N in an N-S relation
            if elem['group_type'] == 'multinuc':
                # this elem is also the 'root node' of a multinuc relation
                child_ids = self.child_dict[elem_id]
                multinuc_child_ids = [c for c in child_ids
                                      if self.elem_dict[c]['reltype'] == 'multinuc']
                multinuc_relname = self.elem_dict[multinuc_child_ids[0]]['relname']
                multinuc_subtree = t(multinuc_relname, [
                    self.dt(start_node=mc)
                    for mc in multinuc_child_ids], debug=self.debug, root_id=elem_id)

                other_child_ids = [c for c in child_ids
                                   if c not in multinuc_child_ids]

                if not other_child_ids:
                    # this elem is only the head of a multinuc relation
                    # TODO: does this make sense / is this ever reached?
                    return multinuc_subtree

                elif len(other_child_ids) == 1:
                    nuc_tree = t('N', multinuc_subtree, debug=self.debug, root_id=elem_id)
                    sat_id = other_child_ids[0]
                    sat_subtree = self.dt(start_node=sat_id)
                    return self.sorted_nucsat_tree(nuc_tree, sat_subtree)

                elif len(other_child_ids) == 2:
                    # this element is the N in an S-N-S schema
                    nuc_tree = t('N', multinuc_subtree, debug=self.debug, root_id=elem_id)
                    sat1_id = other_child_ids[0]
                    sat2_id = other_child_ids[1]

                    sat1_tree = self.dt(start_node=sat1_id)
                    sat2_tree = self.dt(start_node=sat2_id)

                    schema_type = self.get_schema_type(nuc_tree, sat1_tree, sat2_tree)
                    if schema_type == SchemaTypes.one_sided:
                        return self.order_one_sided_schema(nuc_tree, sat1_tree, sat2_tree)

                    else:
                        return self.order_two_sided_schema(nuc_tree, sat1_tree, sat2_tree)

                else:  #len(other_child_ids) > 2
                    raise TooManyChildrenError(
                        "Can't parse a multinuc group (%s) with more than 2 non-multinuc children: %s" \
                            % (elem_id, other_child_ids))

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
        assert elem.get('reltype') in ('rst', 'multinuc', 'span', '', None)
        if elem['reltype'] == 'rst':
            # this elem is the S in an N-S relation
            assert elem_id not in self.child_dict, \
                "A satellite segment (%s) should not have children: %s" \
                    % (elem_id, self.child_dict[elem_id])
            return t('S', [elem['text']], debug=self.debug, root_id=elem_id)

        elif elem['reltype'] == 'multinuc':
            # this elem is one of several Ns in a multinuc relation
            assert elem_id not in self.child_dict, \
                "A multinuc segment (%s) should not have children: %s" \
                    % (elem_id, self.child_dict[elem_id])
            return t('N', [elem['text']], debug=self.debug, root_id=elem_id)

        else:
            # this segment is either an N or an unconnected root node
            # (which we will convert into an N as well)
            nuc_tree = t('N', [elem['text']], debug=self.debug, root_id=elem_id)

            if not self.child_dict.has_key(elem_id):
                # a root segment without any children (e.g. a headline in PCC)
                assert elem['nuclearity'] == 'root'
                return nuc_tree

            if len(self.child_dict[elem_id]) == 1:
                # this segment is the N in an N-S relation
                sat_id = self.child_dict[elem_id][0]
                sat_subtree = self.dt(start_node=sat_id)
                return self.sorted_nucsat_tree(nuc_tree, sat_subtree)

            elif len(self.child_dict[elem_id]) == 2:
                # this segment is the N in an S-N-S schema
                sat1_id = self.child_dict[elem_id][0]
                sat2_id = self.child_dict[elem_id][1]

                sat1_tree = self.dt(start_node=sat1_id)
                sat2_tree = self.dt(start_node=sat2_id)

                schema_type = self.get_schema_type(nuc_tree, sat1_tree, sat2_tree)
                if schema_type == SchemaTypes.one_sided:
                    return self.order_one_sided_schema(nuc_tree, sat1_tree, sat2_tree)

                else:
                    return self.order_two_sided_schema(nuc_tree, sat1_tree, sat2_tree)

            else:
                # this segment is a nucleus and must only have satellites as children
                assert all([self.elem_dict[child_id]['nuclearity'] == 'satellite'
                            for child_id in self.child_dict[elem_id]])

                sat_subtrees = [self.dt(start_node=child_id)
                                for child_id in self.child_dict[elem_id]]

                return self.order_schema(nuc_tree, sat_subtrees)



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
        """subtrees are represented as (tree, linear tree position) tuples"""
        nuc_tree, nuc_pos = nuc_tuple

        for sat_tuples in (inner_sat_tuples, outer_sat_tuples):
            for sat_tree, sat_pos in sat_tuples:
                relname = self.elem_dict[sat_tree.root_id]['relname']
                if sat_pos < nuc_pos:
                    ordered_trees = [sat_tree, nuc_tree]
                else:
                    ordered_trees = [nuc_tree, sat_tree]
                nuc_tree = t('N', [(relname, ordered_trees)], root_id=nuc_tree.root_id)

        return nuc_tree

    def get_schema_type(self, nuc_tree, sat1_tree, sat2_tree):
        """Determine the type of an RST schema.
        Returns 'one_sided' iff the relation is in N-S-S or S-S-N order
        or 'two_sided' iff the relation is in S-N-S order.
        """
        nuc_pos = self.get_linear_position(nuc_tree)
        sat1_pos = self.get_linear_position(sat1_tree)
        sat2_pos = self.get_linear_position(sat2_tree)

        if nuc_pos == sat1_pos == sat2_pos:
            raise NotImplementedError("Unexpected RST schema")

        elif sat1_pos <= nuc_pos and sat2_pos <= nuc_pos:
            return SchemaTypes.one_sided

        elif sat1_pos >= nuc_pos and sat2_pos >= nuc_pos:
            return SchemaTypes.one_sided

        else:
            return SchemaTypes.two_sided

    def order_one_sided_schema(self, nuc_tree, sat1_tree, sat2_tree):
        """convert a one-sided RST schema (a nucleus is shared by two
        satellites, which are both either on the left or on the right of it)
        into a regular RST subtree.
        """
        nuc_pos = self.get_linear_position(nuc_tree)
        sat1_pos = self.get_linear_position(sat1_tree)
        sat2_pos = self.get_linear_position(sat2_tree)

        if abs(nuc_pos - sat1_pos) < abs(nuc_pos - sat2_pos):
            inner_sat_tree = sat1_tree
            outer_sat_tree = sat2_tree
        else:
            inner_sat_tree = sat2_tree
            outer_sat_tree = sat1_tree

        inner_relation = self.elem_dict[inner_sat_tree.root_id]['relname']
        inner_subtrees = self.sort_subtrees(nuc_tree, inner_sat_tree)

        inner_tree = t('N', [(inner_relation, inner_subtrees)],
                       debug=self.debug, root_id=inner_sat_tree.root_id)

        return self.sorted_nucsat_tree(inner_tree, outer_sat_tree)

    def order_two_sided_schema(self, nuc_tree, sat1_tree, sat2_tree):
        """convert a two-sided RST schema (a nucleus is shared by and in
        between two satellites) into a regular RST subtree.

        TODO: add proper documentation
        """
        if sat1_tree.height() == sat2_tree.height():
            sat1_pos = self.get_linear_position(sat1_tree)
            sat2_pos = self.get_linear_position(sat2_tree)

            if sat1_pos < sat2_pos:
                more_important_sat = sat1_tree
                less_important_sat = sat2_tree
            else:
                more_important_sat = sat2_tree
                less_important_sat = sat1_tree

        elif sat1_tree.height() > sat2_tree.height():
            more_important_sat = sat1_tree
            less_important_sat = sat2_tree

        else:
            more_important_sat = sat2_tree
            less_important_sat = sat1_tree

        inner_relation = self.elem_dict[more_important_sat.root_id]['relname']
        inner_subtrees = self.sort_subtrees(nuc_tree, more_important_sat)

        inner_tree = t('N', [(inner_relation, inner_subtrees)],
                       debug=self.debug, root_id=more_important_sat.root_id)

        return self.sorted_nucsat_tree(inner_tree, less_important_sat)

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
        relname = self.elem_dict[sat_tree.root_id]['relname']
        return t(relname, sorted_subtrees, debug=self.debug, root_id=nuc_tree.root_id)


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
            edu_text = elem.text.strip()
            if word_wrap != 0:
                dedented_text = textwrap.dedent(edu_text).strip()
                edu_text = textwrap.fill(dedented_text, width=word_wrap)

            elements[elem_id]['text'] = edu_text
            ordered_edus.append(elem_id)

        else:  # elem_type == 'group':
            elements[elem_id]['group_type'] = elem.attrib.get('type')
    return children, elements, ordered_edus


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
