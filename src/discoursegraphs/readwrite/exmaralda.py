#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

from lxml import etree
from lxml.builder import ElementMaker
from discoursegraphs import DiscourseDocumentGraph

import pudb # TODO: rm

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
        self.E = ElementMaker()
        self.tree = self.__add_document_structure(docgraph)

    def __create_document_header(self):
        """
        this creates an empty, but functional header for an Exmaralda *.exb
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

        annotation_layers = get_annotation_layers(docgraph)
        for layer in annotation_layers:
            # very dirty hack
            # TODO: fix Issue #36
            #~ if len(layer.split(':')) == 2:
                #~ print layer
            # Original: <tier id="TIE0" category="tok" type="t" display-name="[tok]">
            #
            # Examples:
            #
            # layer_id: mmax:token
            # layer_category: token
            # layer_label: [token]
            pass
            #~ E('tier', {'id': layer_id, 'category': layer_category, 'type':"t",
                       #~ 'display-name': layer_label})
            for anno_element in layer:
            # Original: <event start="T0" end="T1">Zum</event>
                pass



        body.append(timeline)
        body = self.__add_token_tiers(docgraph, body)
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
            'id': "TIE0", 'category': "tok", 'type':"t",
            'display-name': "[tok]"})

        for i, (_tok_id, token_str) in enumerate(docgraph.get_tokens()):
            # Original: <event start="T0" end="T1">Zum</event>
            token_tier.append(E('event', {'start': "T{}".format(i), 'end': "T{}".format(i+1)}, token_str))
        body.append(token_tier)
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


if __name__ == "__main__":
    import os
    import sys
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
    exmaralda = ExmaraldaWriter(docgraph, args.output_file)
    exmaralda_str = etree.tostring(exmaralda.tree, pretty_print=True,
                                   xml_declaration=True, encoding='UTF-8')

    if isinstance(args.output_file, file):
        args.output_file.write(exmaralda_str)
    else:
        with open(args.output_file, 'w') as exmaralda_file:
            exmaralda_file.write(exmaralda_str)

    #~ pudb.set_trace()
    #~ for token_id in docgraph.tokens:
        #~ print docgraph.node[token_id]
