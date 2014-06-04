#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

from collections import defaultdict
from lxml import etree
from lxml.builder import ElementMaker
from discoursegraphs import DiscourseDocumentGraph
from discoursegraphs.util import natural_sort_key


class ExmaraldaWriter(object):
    """
    This class converts a DiscourseDocumentGraph into an Exmaralda file.
    """
    def __init__(self, docgraph, output_path):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        output_path : str
            relative or absolute path to the Exmaralda file to be created
        """
        self.toknode2id = {node_id:i
                           for i, node_id in enumerate(docgraph.tokens)}
        self.E = ElementMaker()
        self.tier_count = 0
        self.tree = self.__add_document_structure(docgraph)

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

    def __add_document_structure(self, docgraph):
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
            # very dirty hack
            # TODO: fix Issue #36
            layer_hierarchy = layer.split(':')
            layer_category = layer_hierarchy[-1]
            if len(layer_hierarchy) == 2 \
            and layer_category not in ('token', 'root'):
                temp_tier = E('tier',
                {'id': "TIE{}".format(self.tier_count), 'category': layer_category, 'type':"t",
                 'display-name': "[{}]".format(layer)})
                self.tier_count += 1

                for node_id in get_nodes_from_layer(docgraph, layer):
                    span_node_ids = get_span(docgraph, node_id)
                    if span_node_ids:
                        first_tier_node = self.toknode2id[span_node_ids[0]]
                        last_tier_node = self.toknode2id[span_node_ids[-1]]
                        event_label = docgraph.node[node_id].get('label', '')
                        temp_tier.append(E('event', {'start': "T{}".format(first_tier_node), 'end': "T{}".format(last_tier_node+1)}, event_label))

                body.append(temp_tier)
        root.append(body)
        return root

    def __add_token_tiers(self, docgraph, body, default_ns='tiger'):
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
        default_ns : str
            the default namespace (i.a. used to extract the token strings
            only once)
        """
        E = self.E
        token_tier = E('tier', {
            'id': "TIE{}".format(self.tier_count), 'category': "tok", 'type':"t",
            'display-name': "[tok]"})
        self.tier_count += 1

        token_attribs = defaultdict(lambda : defaultdict(str))
        for token_node_id in docgraph.tokens:
            for attrib in docgraph.node[token_node_id]:
                if attrib not in ('layers', 'label') \
                and attrib.split(':')[-1] not in ('token', 'id', 'word', 'morph', 'lemma'):
                    token_attribs[attrib][token_node_id] = docgraph.node[token_node_id][attrib]

        for i, (_tok_id, token_str) in enumerate(docgraph.get_tokens()):
            # Original: <event start="T0" end="T1">Zum</event>
            token_tier.append(E('event', {'start': "T{}".format(i), 'end': "T{}".format(i+1)}, token_str))
        body.append(token_tier)

        for anno_tier in token_attribs:
            category = anno_tier.split(':')[-1]
            temp_tier = E('tier',
                {'id': "TIE{}".format(self.tier_count), 'category': category, 'type':"t",
                 'display-name': "[{}]".format(anno_tier)})
            self.tier_count += 1
            for token_node_id in token_attribs[anno_tier]:
                token_tier_id = self.toknode2id[token_node_id]
                token_attrib = token_attribs[anno_tier][token_node_id]
                temp_tier.append(E('event', {'start': "T{}".format(token_tier_id), 'end': "T{}".format(token_tier_id+1)}, token_attrib))
            body.append(temp_tier)
        return body


def get_annotation_layers(docgraph):
    """
    WARNING: this is higly inefficient!
    Fix this via Issue #36.

    Returns
    -------
    all_layers : set or dict
        the set of all annotation layers used in the given graph
    """
    all_layers = set()
    for node_id, node_attribs in docgraph.nodes_iter(data=True):
        for layer in node_attribs['layers']:
            all_layers.add(layer)
    return all_layers

def get_span(docgraph, node_id):
    """
    returns all the tokens that are dominated or in a span relation with
    the given node.

    Returns
    -------
    span : list of str
        sorted list of token nodes (token node IDs)
    """
    span = []
    for from_id, to_id, edge_attribs in docgraph.out_edges_iter(node_id, data=True):
        if from_id == to_id:
            pass  # ignore self-loops
        # ignore pointing relations
        if edge_attribs['edge_type'] != 'points_to':
            if docgraph.ns+':token' in docgraph.node[to_id]:
                span.append(to_id)
            else:
                span.extend(get_span(docgraph, to_id))
    return sorted(span, key=natural_sort_key)

def get_nodes_from_layer(docgraph, layer):
    """
    Returns
    -------
    nodes : generator of str
        a container/list of node IDs that are present in the given layer
    """
    for node_id, node_attribs in docgraph.nodes_iter(data=True):
        if layer in node_attribs['layers']:
            yield node_id


if __name__ == "__main__":
    import os
    import sys
    import argparse
    import cPickle as pickle
    from discoursegraphs.util import ensure_utf8

    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='pickle file of a document graph to be converted')
    parser.add_argument('output_file', nargs='?', default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)

    with open(args.input_file, 'rb') as docgraph_file:
        docgraph = pickle.load(docgraph_file)
    exmaralda = ExmaraldaWriter(docgraph, args.output_file)
    exmaralda_str = etree.tostring(exmaralda.tree, pretty_print=True,
                                   xml_declaration=True, encoding='UTF-8')

    if isinstance(args.output_file, file):
        args.output_file.write(exmaralda_str)
    else:
        with open(args.output_file, 'w') as exmaralda_file:
            exmaralda_file.write(exmaralda_str)

