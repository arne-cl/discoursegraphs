#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

'''
The 'exportxml' module will convert a corpus in Negra ExportXML format [1]
(e.g. Tüba-D/Z [2]) into a document graph. We can't base the code on networkx,
as it can't handle large graphs (Tüba-D/Z contains 1.7 million nodes).

[1] http://www.sfs.uni-tuebingen.de/en/ascl/resources/corpora/export-format.html
[2] http://www.sfs.uni-tuebingen.de/en/ascl/resources/corpora/tueba-dz.html

NB: Never, ever use add_edge() in igraph! Always use add_edges(), it is
much faster.
'''

import os
from lxml import etree

import igraph as ig


class ExportXMLDocumentGraph(ig.Graph):
    def __init__(self, exportxml_filepath, name=None, namespace='exportxml',
                 limit=None):
        """
        Parameters
        ----------
        limit : int or None
            only parse the first n sentences (to save time, RAM etc.)
        """
        # super calls __init__() of base class ig.Graph
        super(ExportXMLDocumentGraph, self).__init__(directed=True)

        self.name = name if name else os.path.basename(exportxml_filepath)
        self.ns = namespace
        self.root = self.ns+':root_node'
        self.add_vertex(self.root, layers={self.ns})

        # in igraph, adding a single edge is prohibitively slow,
        # as the whole index of the graph has to be rebuild!
        # to speed this up, store the edges in a list & call add_edges() once!
        edges = []
        relations = {}

        treeiter = etree.iterparse(exportxml_filepath, tag='sentence')
        if limit:
            for i in xrange(limit):
                try:
                    _action, sentence = treeiter.next()
                    self.add_sentence(sentence, edges, relations)
                except StopIteration as e:
                    break # we've already parsed all sentences in that file
        else: # parse all sentences
            for _action, sentence in treeiter:
                self.add_sentence(sentence, edges, relations)
        self.add_edges(edges)

        # igraph doesn't store nodes/edge names in a dict, so a lookup would be O(n)
        node_name2id = {node['name']: node.index for node in self.vs}
        edge_endpoints2id = {(edge.source, edge.target): edge.index
                             for edge in self.es}

        for (source, target) in relations:
            relation_type = relations[(source, target)]
            if target:
                edge_endpoints = (node_name2id[source], node_name2id[target])
                self.es[edge_endpoints2id[edge_endpoints]]['exportxml:relation_type'] = relation_type
            else:
                # there's no antecedent in case of an expletive anaphoric relation
                self.vs[node_name2id[source]]['exportxml:anaphora_type'] = relation_type

    def add_sentence(self, sentence, edges, relations):
        """
        Parameters
        ----------
        sentence : etree.Element
            etree representation of a sentence
            (syntax tree with coreference annotation)
        edges : list of (str, str)
            a (potentially empty) list of edges, represented as (source
            node ID, target node ID) tuples. this will be used to cache
            edges, as add_edge() is much slower than add_edges() in ``igraph``.
        relations : dict
            maps from an edge (i.e. (source node ID, target node ID)) to
            its anaphoric relation type (e.g. 'coreference',
            'expletive')
        """
        sent_root_id = sentence.attrib['origin']
        self.add_vertex(sent_root_id, label=sent_root_id)
        edges.append((self.root, sent_root_id))

        for element in sentence.iter('node', 'word', 'anaphora'):
            parent_element = element.getparent()
            # some <anaphora> are children of <word> elements
            if parent_element.tag in ('node', 'word'):
                parent_id = parent_element.attrib['id']
            elif parent_element.tag == 'sentence':
                parent_id = parent_element.attrib['origin']
            else:
                sys.stderr.write("Unexpected parent '{}' of element '{}'\n".format(parent_element, element))
            element_id = element.attrib.get('id') # <anaphora> doesn't have an ID

            if element.tag == 'node':
                node_attrs = {'{}:{}'.format(self.ns, key):val for (key, val) in element.attrib.items()}
                self.add_vertex(element_id, label=element.attrib['cat'],
                                **node_attrs)
                edges.append((parent_id, element_id))
            elif element.tag == 'word':
                node_attrs = {'{}:{}'.format(self.ns, key):val for (key, val) in element.attrib.items()}
                self.add_vertex(element_id, label=element.attrib['form'],
                                **node_attrs)
                edges.append((parent_id, element_id))

            else: # element.tag == 'anaphora'
                # <anaphora> doesn't have an ID, but it's tied to its parent element
                antecedent_str, relation_type = parse_anaphora(element, parent_id)

                if antecedent_str:
                    # there might be more than one antecedent
                    for antecedent_id in antecedent_str.split(','):
                        edge = (parent_id, antecedent_id)
                        edges.append(edge)
                        relations[edge] = relation_type
                else:
                    # there's no antecedent in case of an expletive anaphoric relation
                    relations[(parent_id, None)] = relation_type


def parse_anaphora(anaphora, source_id):
    """
    Parameters
    ----------
    anaphora : etree.Element
        an <anaphora> element
    source_id : str
        the node ID of the anaphora (points either to a <node> or a <word>)

    Returns
    -------
    antecedent : str
        node ID of the antecedent, e.g. ``s_4_n_527``
    relation_type : str
        anaphoric relation type, e.g. ``anaphoric`` or ``coreferential``
    """
    # there's only one <relation> child element
    relation = anaphora.getchildren()[0]
    return relation.attrib['antecedent'], relation.attrib['type']



read_exportxml = ExportXMLDocumentGraph
