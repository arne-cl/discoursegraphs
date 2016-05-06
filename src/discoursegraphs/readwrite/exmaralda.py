#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
The ``exmaralda`` module converts a ``DiscourseDocumentGraph`` (possibly
containing multiple annotation layers) into an Exmaralda ``*.exb`` file
and vice versa.
"""

import os
import sys
from collections import defaultdict
from lxml import etree
from lxml.builder import ElementMaker

from discoursegraphs import (DiscourseDocumentGraph, EdgeTypes,
                             get_annotation_layers,
                             get_pointing_chains, get_span,
                             select_nodes_by_layer)
from discoursegraphs.util import create_dir


class ExmaraldaFile(object):
    """
    This class converts a DiscourseDocumentGraph into an Exmaralda file.

    Attributes
    ----------
    toknode2id : dict
        maps from a token node ID to its Exmaralda ID (ID in the common
        timeline)
    """
    def __init__(self, docgraph, remove_redundant_layers=True):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        """
        self.toknode2id = {node_id: i
                           for i, node_id in enumerate(docgraph.tokens)}
        self.E = ElementMaker()
        self.tier_count = 0
        self.tree = self.__add_document_structure(docgraph,
                                                  remove_redundant_layers)

    def __str__(self):
        """
        returns the generated Exmaralda ``*.exb`` file as a string.
        """
        return etree.tostring(self.tree, pretty_print=True,
                              xml_declaration=True, encoding='UTF-8')

    def write(self, output_filepath):
        """
        serialize the ExmaraldaFile instance and write it to a file.

        Parameters
        ----------
        output_filepath : str
            relative or absolute path to the Exmaralda file to be created
        """
        with open(output_filepath, 'w') as out_file:
            out_file.write(self.__str__())

    def __create_document_header(self):
        """
        Look, mum! XML generation without string concatenation!1!!

        This creates an empty, but functional header for an Exmaralda *.exb
        file.
        """
        E = self.E
        root = E('basic-transcription')
        head = E('head')

        meta = E('meta-information')
        project = E('project-name')
        tname = E('transcription-name')
        ref_file = E('referenced-file', url="")
        ud = E('ud-meta-information')
        comment = E('comment')
        tconvention = E('transcription-convention')
        meta.append(project)
        meta.append(tname)
        meta.append(ref_file)
        meta.append(ud)
        meta.append(comment)
        meta.append(tconvention)

        speakers = E('speakertable')
        head.append(meta)
        head.append(speakers)
        root.append(head)
        return root

    def __add_document_structure(self, docgraph,
                                 remove_redundant_layers=True):
        """return an Exmaralda XML etree representation a docgraph"""
        E = self.E
        root = self.__create_document_header()

        body = E('basic-body')
        timeline = E('common-timeline')

        # for n tokens we need to create n+1 timeline indices
        for i in xrange(len(docgraph.tokens)+1):
            idx = str(i)
            # example: <tli id="T0" time="0"/>
            timeline.append(E('tli', {'id': 'T'+idx, 'time': idx}))

        body.append(timeline)
        body = self.__add_token_tiers(docgraph, body)

        annotation_layers = get_annotation_layers(docgraph)
        for layer in annotation_layers:
            if not remove_redundant_layers:  # add all layers
                self.__add_annotation_tier(docgraph, body, layer)
            elif is_informative(layer):  # only add informative layers
                self.__add_annotation_tier(docgraph, body, layer)

        self.__add_coreference_chain_tiers(docgraph, body)
        root.append(body)
        return root

    def __add_annotation_tier(self, docgraph, body, annotation_layer):
        """
        adds a span-based annotation layer as a <tier> to the Exmaralda <body>.

        Parameter
        ---------
        docgraph : DiscourseDocumentGraph
            the document graph from which the chains will be extracted
        body : etree._Element
            an etree representation of the <basic_body> element (and all its
            descendants) of the Exmaralda file
        annotation_layer : str
            the name of a layer, e.g. 'tiger', 'tiger:token' or 'mmax:sentence'
        """
        layer_cat = annotation_layer.split(':')[-1]
        temp_tier = self.E('tier',
                           {'id': "TIE{}".format(self.tier_count),
                            'category': layer_cat, 'type': "t",
                            'display-name': "[{}]".format(annotation_layer)})
        self.tier_count += 1

        for node_id in select_nodes_by_layer(docgraph, annotation_layer):
            span_node_ids = get_span(docgraph, node_id)
            if span_node_ids:
                start_id, end_id = self.__span2event(span_node_ids)
                event_label = docgraph.node[node_id].get('label', '')
                event = self.E('event',
                               {'start': "T{}".format(start_id),
                                'end': "T{}".format(end_id)},
                               event_label)
                temp_tier.append(event)
        body.append(temp_tier)

    def __add_coreference_chain_tiers(self, docgraph, body,
                                      min_chain_length=3):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph from which the chains will be extracted
        body : etree._Element
            an etree representation of the <basic_body> element (and all its
            descendants) of the Exmaralda file
        min_chain_length : int
            don't add tiers for chains with less than N elements (default: 3)

        TODO: this method assumes that each pointing relation chains signifies
        a coreference chain.
        """
        E = self.E

        for i, chain in enumerate(get_pointing_chains(docgraph)):
            chain_tier = E('tier',
                           {'id': "TIE{}".format(self.tier_count),
                            'category': "chain", 'type': "t",
                            'display-name': "[coref-chain-{}]".format(i)})
            self.tier_count += 1

            chain_length = len(chain)
            if chain_length < min_chain_length:
                continue  # ignore short chains

            for j, node_id in enumerate(chain):
                span_node_ids = get_span(docgraph, node_id)
                if span_node_ids:
                    start_id, end_id = self.__span2event(span_node_ids)
                    element_str = "chain_{0}: {1}/{2}".format(
                        i, chain_length-j, chain_length)
                    chain_tier.append(
                        E('event', {'start': "T{}".format(start_id),
                                    'end': "T{}".format(end_id)}, element_str))
            body.append(chain_tier)

    def __add_token_tiers(self, docgraph, body):
        """
        adds all tiers that annotate single tokens (e.g. token string, lemma,
        POS tag) to the etree representation of the Exmaralda XML file.

        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        body : etree._Element
            an etree representation of the <basic_body> element (and all its
            descendants) of the Exmaralda file
        """
        E = self.E
        token_tier = E('tier',
                       {'id': "TIE{}".format(self.tier_count),
                        'category': "tok", 'type': "t",
                        'display-name': "[tok]"})
        self.tier_count += 1

        token_attribs = defaultdict(lambda: defaultdict(str))
        for token_node_id in docgraph.tokens:
            for attrib in docgraph.node[token_node_id]:
                is_boring_attrib = attrib in ('layers', 'label')
                is_boring_cat = attrib.split(':')[-1] in ('token',
                                                          'id', 'word',
                                                          'morph', 'lemma')
                if not is_boring_attrib and not is_boring_cat:
                    token_attribs[attrib][token_node_id] = \
                        docgraph.node[token_node_id][attrib]

        for i, (_tok_id, token_str) in enumerate(docgraph.get_tokens()):
            # example: <event start="T0" end="T1">Zum</event>
            token_tier.append(
                E('event', {'start': "T{}".format(i),
                            'end': "T{}".format(i+1)}, token_str))
        body.append(token_tier)

        for anno_tier in token_attribs:
            category = anno_tier.split(':')[-1]
            temp_tier = E(
                'tier', {'id': "TIE{}".format(self.tier_count),
                         'category': category, 'type': "t",
                         'display-name': "[{}]".format(anno_tier)})
            self.tier_count += 1
            for token_node_id in token_attribs[anno_tier]:
                token_tier_id = self.toknode2id[token_node_id]
                token_attrib = token_attribs[anno_tier][token_node_id]
                temp_tier.append(
                    E('event', {'start': "T{}".format(token_tier_id),
                                'end': "T{}".format(token_tier_id+1)},
                      token_attrib))
            body.append(temp_tier)
        return body

    def __span2event(self, span_node_ids):
        """
        converts a span of tokens (list of token node IDs) into an Exmaralda
        event (start and end ID).

        Parameters
        ----------
        span_node_ids : list of str
            sorted list of node IDs representing a span of tokens

        Returns
        -------
        event : tuple of (str, str)
            event start ID and event end ID
        """
        return (self.toknode2id[span_node_ids[0]],
                self.toknode2id[span_node_ids[-1]]+1)


class ExmaraldaDocumentGraph(DiscourseDocumentGraph):
    """graph representation of an Exmaralda-annotated document"""
    def __init__(self, exmaralda_file, name=None, namespace='exmaralda',
                 token_tier='tok', ignored_tier_categories=None):
        """
        generates a document graph from an Exmaralda *.exb file

        Parameters
        ----------
        exmaralda_file : str
            path to an *.exb file
        name : str or None
            name of the document graph. If None, will be set to the input
            file's basename
        namespace : str
            namespace of the graph, default: exmaralda
        token_tier: str
            the category attribute of the <tier> that contains the tokens.
            default: tok
        ignored_tier_categories : None or list of str
            a list of tier categories which will not be added to the document
            graph
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(ExmaraldaDocumentGraph, self).__init__()
        self.name = name if name else os.path.basename(exmaralda_file)
        self.ns = namespace
        self.root = self.ns+':root_node'

        tree = etree.parse(exmaralda_file)
        self.tokens = []

        self.__add_tokenization(tree)

        if ignored_tier_categories:
            for tier in tree.iter('tier'):
                if tier.attrib['category'] not in ignored_tier_categories:
                    self.__add_tier(tier, token_tier_name=token_tier)
        else:
            for tier in tree.iter('tier'):
                self.__add_tier(tier, token_tier_name=token_tier)

    def __add_tokenization(self, tree):
        """adds a node for each token ID in the document"""
        for token_id in self.get_token_ids(tree):
            self.add_node(token_id, layers={self.ns})
            self.tokens.append(token_id)

    def __add_tier(self, tier, token_tier_name):
        """
        adds a tier to the document graph (either as additional attributes
        to the token nodes or as a span node with outgoing edges to the token
        nodes it represents)
        """
        if tier.attrib['category'] == token_tier_name:
            self.__add_tokens(tier)
        else:
            if self.is_token_annotation_tier(tier):
                self.__add_token_annotation_tier(tier)

            else:
                self.__add_span_tier(tier)

    def __add_tokens(self, token_tier):
        """
        adds all tokens to the document graph. Exmaralda considers them to
        be annotations as well, that's why we could only extract the token
        node IDs from the timeline (using ``__add_tokenization()``), but not
        the tokens themselves.

        Parameters
        ----------
        token_tier : etree._Element
            an etree element representing the <tier> which contains the tokens
        """
        for event in token_tier.iter('event'):
            assert len(self.gen_token_range(event.attrib['start'],
                       event.attrib['end'])) == 1, \
                "Events in the token tier must not span more than one token."
            token_id = event.attrib['start']
            self.node[token_id][self.ns+':token'] = event.text

    def is_token_annotation_tier(self, tier):
        """
        returns True, iff all events in the given tier annotate exactly one
        token.
        """
        for i, event in enumerate(tier.iter('event')):
            if self.indexdelta(event.attrib['end'], event.attrib['start']) != 1:
                return False
        return True

    def __add_token_annotation_tier(self, tier):
        """
        adds a tier to the document graph, in which each event annotates
        exactly one token.
        """
        for i, event in enumerate(tier.iter('event')):
            anno_key = '{0}:{1}'.format(self.ns, tier.attrib['category'])
            anno_val = event.text if event.text else ''
            self.node[event.attrib['start']][anno_key] = anno_val

    def __add_span_tier(self, tier):
        """
        adds a tier to the document graph in which each event annotates a span
        of one or more tokens.
        """
        tier_id = tier.attrib['id']
        # add the tier's root node with an inbound edge from the document root
        self.add_node(
            tier_id, layers={self.ns, self.ns+':tier'},
            attr_dict={self.ns+':category': tier.attrib['category'],
                       self.ns+':type': tier.attrib['type'],
                       self.ns+':display-name': tier.attrib['display-name']})
        self.add_edge(self.root, tier_id, edge_type=EdgeTypes.dominance_relation)

        # add a node for each span, containing an annotation.
        # add an edge from the tier root to each span and an edge from each
        # span to the tokens it represents
        for i, event in enumerate(tier.iter('event')):
            span_id = '{}_{}'.format(tier_id, i)
            span_tokens = self.gen_token_range(event.attrib['start'], event.attrib['end'])
            annotation = event.text if event.text else ''
            self.add_node(
                span_id, layers={self.ns, self.ns+':span'},
                attr_dict={self.ns+':annotation': annotation,
                           'label': annotation})
            self.add_edge(tier_id, span_id, edge_type=EdgeTypes.dominance_relation)

            for token_id in span_tokens:
                self.add_edge(span_id, token_id,
                              edge_type=EdgeTypes.spanning_relation)

    @staticmethod
    def get_token_ids(tree):
        """
        returns a list of all token IDs occuring the the given exmaralda file,
        sorted by their time stamp in ascending order.
        """
        def tok2time(token_element):
            '''
            extracts the time (float) of a <tli> element
            (i.e. the absolute position of a token in the document)
            '''
            return float(token_element.attrib['time'])

        timeline = tree.find('//common-timeline')
        return (tok.attrib['id']
                for tok in sorted((tli for tli in timeline.iterchildren()),
                                  key=tok2time))

    @staticmethod
    def tokenid2index(token_id):
        """converts a token ID (e.g. 'T0') to its index (i.e. 0)"""
        return int(token_id[1:])

    def indexdelta(self, stop_id, start_id):
        """returns the distance (int) between to idices.

        Two consecutive tokens must have a delta of 1.
        """
        return self.tokenid2index(stop_id) - self.tokenid2index(start_id)

    def gen_token_range(self, start_id, stop_id):
        """
        returns a list of all token IDs in the given, left-closed,
        right-open interval (i.e. includes start_id, but excludes stop_id)

        >>> gen_token_range('T0', 'T1')
        ['T0']

        >>> gen_token_range('T1', 'T5')
        ['T1', 'T2', 'T3', 'T4']
        """
        index_range = range(self.tokenid2index(start_id), self.tokenid2index(stop_id))
        return ["T{}".format(index) for index in index_range]


def is_informative(layer):
    """
    returns true, iff the annotation layer contains information that 'makes
    sense' in Exmaralda (i.e. there are annotations we don't need and which
    would clutter the Exmaralda Partitur editor).

    Parameters
    ----------
    layer : str
        the name of a layer, e.g. 'tiger', 'tiger:token' or 'mmax:sentence'

    Returns
    -------
    is_informative : bool
        Returns True, iff the layer is likely to contain information that
        should be exported to Exmaralda. Usually, we don't want to include
        information about sentence or token boundaries, since they are already
        obvious from the token layer.
    """
    # very dirty hack
    # TODO: fix Issue #36 (efficient self.layers / get_hierarchical_layers()
    return layer not in ('tiger', 'tiger:token', 'tiger:sentence:root',
                         'tiger:sentence:vroot', 'tiger:edge', 'tiger:secedge',
                         'exmaralda', 'exmaralda:tier',
                         'discoursegraph')


# pseudo-function to create a document graph from an Exmaralda file
read_exb = read_exmaralda = ExmaraldaDocumentGraph


def write_exb(docgraph, output_file):
    """
    converts a DiscourseDocumentGraph into an Exmaralda ``*.exb`` file and
    writes it to the given file (or file path).
    """
    exmaralda_file = ExmaraldaFile(docgraph)
    assert isinstance(output_file, (str, file))
    if isinstance(output_file, str):
        path_to_file = os.path.dirname(output_file)
        if not os.path.isdir(path_to_file):
            create_dir(path_to_file)
        exmaralda_file.write(output_file)
    else:  # output_file is a file object
        output_file.write(exmaralda_file.__str__())


# alias for write_exb(): convert docgraph into Exmaralda file
write_exmaralda = write_exb


if __name__ == "__main__":
    import argparse
    import cPickle as pickle

    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='pickle file of a document graph to be converted')
    parser.add_argument('output_file', nargs='?', default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)

    with open(args.input_file, 'rb') as docgraph_file:
        docgraph = pickle.load(docgraph_file)
    write_exb(docgraph, args.output_file)
