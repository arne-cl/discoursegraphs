#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts a *.dis file (used by old versions of RSTTool to
annotate rhetorical structure) into a networkx-based directed graph
(``DiscourseDocumentGraph``).
"""

import os

from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.readwrite.generic import generic_converter_cli
from discoursegraphs.readwrite.rst.dis.common import (
    DisFile, get_child_types, get_edu_text, get_node_id, get_node_type,
    get_relation_type, get_tree_type, SUBTREE_TYPES)


class RSTLispDocumentGraph(DiscourseDocumentGraph):
    """
    A directed graph with multiple edges (based on a networkx
    MultiDiGraph) that represents the rhetorical structure of a
    document. It is generated from a *.dis file.

    Attributes
    ----------
    name : str
        name, ID of the document or file name of the input file
    ns : str
        the namespace of the document (default: rst)
    root : str
        name of the document root node ID
    tokens : list of str
        sorted list of all token node IDs contained in this document graph
    """
    def __init__(self, dis_filepath, name=None, namespace='rst',
                 tokenize=True, precedence=False):
        """
        Creates an RSTLispDocumentGraph from a Rhetorical Structure *.dis file and adds metadata
        to it.

        Parameters
        ----------
        dis_filepath : str
            absolute or relative path to the Rhetorical Structure *.dis file to be
            parsed.
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the document (default: rst)
        precedence : bool
            If True, add precedence relation edges
            (root precedes token1, which precedes token2 etc.)
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(RSTLispDocumentGraph, self).__init__()

        self.name = name if name else os.path.basename(dis_filepath)
        self.ns = namespace
        self.root = 0
        self.add_node(self.root, layers={self.ns}, label=self.ns+':root_node')
        if 'discoursegraph:root_node' in self:
            self.remove_node('discoursegraph:root_node')

        self.tokenized = tokenize
        self.tokens = []
        self.dis_tree = DisFile(dis_filepath).tree
        self.parse_dis_tree(self.dis_tree)

        if precedence:
            self.add_precedence_relations()

    def parse_dis_tree(self, dis_tree, indent=0):
        """parse a *.dis ParentedTree into this document graph"""
        tree_type = get_tree_type(dis_tree)
        assert tree_type in SUBTREE_TYPES
        if tree_type == 'Root':
            # replace generic root node with tree root
            old_root_id = self.root
            root_id = get_node_id(dis_tree, self.ns)
            self.root = root_id
            self.add_node(root_id)
            self.remove_node(old_root_id)

            children = dis_tree[1:]
            for child in children:
                child_id = get_node_id(child, self.ns)
                self.add_edge(
                    root_id, child_id,
                    #~ attr_dict={self.ns+':rel_type': relation_type},
                    edge_type=EdgeTypes.dominance_relation)

                self.parse_dis_tree(child, indent=indent+1)

        else: # tree_type in ('Nucleus', 'Satellite')
            node_id = get_node_id(dis_tree, self.ns)
            node_type = get_node_type(dis_tree)
            relation_type = get_relation_type(dis_tree)
            if node_type == 'leaf':
                edu_text = get_edu_text(dis_tree[-1])
                self.add_node(node_id, attr_dict={
                    self.ns+':text': edu_text,
                    'label': u'{0}: {1}'.format(node_id, edu_text[:20])})
                if self.tokenized:
                    edu_tokens = edu_text.split()
                    for i, token in enumerate(edu_tokens):
                        token_node_id = '{0}_{1}'.format(node_id, i)
                        self.tokens.append(token_node_id)
                        self.add_node(token_node_id, attr_dict={self.ns+':token': token,
                                                                'label': token})
                        self.add_edge(node_id, '{0}_{1}'.format(node_id, i))

            else: # node_type == 'span'
                self.add_node(node_id, attr_dict={self.ns+':rel_type': relation_type,
                                                  self.ns+':node_type': node_type})
                children = dis_tree[3:]
                child_types = get_child_types(children)

                expected_child_types = set(['Nucleus', 'Satellite'])
                unexpected_child_types = set(child_types).difference(expected_child_types)
                assert not unexpected_child_types, \
                    "Node '{0}' contains unexpected child types: {1}\n".format(
                        node_id, unexpected_child_types)

                if 'Satellite' not in child_types:
                    # span only contains nucleii -> multinuc
                    for child in children:
                        child_node_id = get_node_id(child, self.ns)
                        self.add_edge(node_id, child_node_id, attr_dict={
                            self.ns+':rel_type': relation_type})

                elif len(child_types['Satellite']) == 1 and len(children) == 1:
                    if tree_type == 'Nucleus':
                        child = children[0]
                        child_node_id = get_node_id(child, self.ns)
                        self.add_edge(
                            node_id, child_node_id,
                            attr_dict={self.ns+':rel_type': relation_type},
                            edge_type=EdgeTypes.dominance_relation)
                    else:
                        assert tree_type == 'Satellite'
                        raise NotImplementedError("I don't know how to combine two satellites")

                elif len(child_types['Satellite']) == 1 and len(child_types['Nucleus']) == 1:
                    # standard RST relation, where one satellite is dominated by one nucleus
                    nucleus_index = child_types['Nucleus'][0]
                    satellite_index = child_types['Satellite'][0]

                    nucleus_node_id = get_node_id(children[nucleus_index], self.ns)
                    satellite_node_id = get_node_id(children[satellite_index], self.ns)
                    self.add_edge(node_id, nucleus_node_id, attr_dict={self.ns+':rel_type': 'span'},
                                  edge_type=EdgeTypes.spanning_relation)
                    self.add_edge(nucleus_node_id, satellite_node_id,
                                  attr_dict={self.ns+':rel_type': relation_type},
                                  edge_type=EdgeTypes.dominance_relation)
                else:
                    raise ValueError("Unexpected child combinations: {}\n".format(child_types))

                for child in children:
                    self.parse_dis_tree(child, indent=indent+1)


# pseudo-function to create a document graph from a RST (.dis) file
read_dis = RSTLispDocumentGraph


if __name__ == '__main__':
    generic_converter_cli(RSTLispDocumentGraph, 'RST (rhetorical structure)')
