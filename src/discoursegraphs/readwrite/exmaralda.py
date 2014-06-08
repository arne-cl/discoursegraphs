#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

from collections import defaultdict
from lxml import etree
from lxml.builder import ElementMaker
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
        self.toknode2id = {node_id: i
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
            layer_levels = layer.split(':')
            layer_cat = layer_levels[-1]
            if len(layer_levels) == 2 and layer_cat not in ('token', 'root'):
                temp_tier = E('tier',
                              {'id': "TIE{}".format(self.tier_count),
                               'category': layer_cat, 'type': "t",
                               'display-name': "[{}]".format(layer)})
                self.tier_count += 1

                for node_id in select_nodes_by_layer(docgraph, layer):
                    span_node_ids = get_span(docgraph, node_id)
                    if span_node_ids:
                        first_tier_node = self.toknode2id[span_node_ids[0]]
                        last_tier_node = self.toknode2id[span_node_ids[-1]]
                        event_label = docgraph.node[node_id].get('label', '')
                        event = E('event',
                                  {'start': "T{}".format(first_tier_node),
                                   'end': "T{}".format(last_tier_node+1)},
                                  event_label)
                        temp_tier.append(event)

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
        token_tier = E('tier',
                       {'id': "TIE{}".format(self.tier_count),
                        'category': "tok", 'type': "t",
                        'display-name': "[tok]"})
        self.tier_count += 1

        token_attribs = defaultdict(lambda: defaultdict(str))
        for token_node_id in docgraph.tokens:
            for attrib in docgraph.node[token_node_id]:
                boring_attrib = attrib in ('layers', 'label')
                boring_cat = attrib.split(':')[-1] in ('token',
                                                       'id', 'word', 'morph',
                                                       'lemma')
                if not boring_attrib and not boring_cat:
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
    for from_id, to_id, edge_attribs in docgraph.out_edges_iter(node_id,
                                                                data=True):
        if from_id == to_id:
            pass  # ignore self-loops
        # ignore pointing relations
        if edge_attribs['edge_type'] != 'points_to':
            if docgraph.ns+':token' in docgraph.node[to_id]:
                span.append(to_id)
            else:
                span.extend(get_span(docgraph, to_id))
    return sorted(span, key=natural_sort_key)

def get_text(docgraph, node_id):
    """
    returns the text (joined token strings) that the given node dominates
    or spans.
    """
    tokens = (docgraph.node[node_id][docgraph.ns+':token']
              for node_id in get_span(docgraph, node_id))
    return ' '.join(tokens)


def select_nodes_by_layer(docgraph, layer):
    """
    Get all nodes belonging to the given layer.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        document graph from which the nodes will be extracted
    layer : str
        name of the layer

    Returns
    -------
    nodes : generator of str
        a container/list of node IDs that are present in the given layer
    """
    for node_id, node_attribs in docgraph.nodes_iter(data=True):
        if layer in node_attribs['layers']:
            yield node_id


def select_edges_by_edgetype(docgraph, edge_type, data=False):
    """
    Get all edges with the given edge type.
    """
    for (from_id, to_id, edge_attribs) in docgraph.edges(data=True):
        if edge_attribs['edge_type'] == edge_type:
            if data:
                yield (from_id, to_id, edge_attribs)
            else:
                yield (from_id, to_id)


def get_pointing_chains(docgraph):
    """
    returns a list of chained pointing relations (e.g. coreference chains)
    found in the given document graph.
    """
    pointing_relations = select_edges_by_edgetype(docgraph, 'points_to')
    rel_dict = {from_id: to_id for from_id, to_id in pointing_relations}

    def walk_chain(rel_dict, from_id):
        """
        given a dict of pointing relations and a start node, this function
        will return a list of node IDs representing a path beginning with that
        node.

        Parameters
        ----------
        rel_dict : dict
            a dictionary mapping from an edge source node (node ID str)
            to a set of edge target nodes (node ID str)
        from_id : str

        Returns
        -------
        unique_chains : list of str
            a chain of pointing relations, represented as a list of node IDs
        """
        chain = [from_id]
        to_id = rel_dict[from_id]
        if to_id in rel_dict:
            chain.extend(walk_chain(rel_dict, to_id))
        else:
            chain.append(to_id)
        return chain

    all_chains = [walk_chain(rel_dict, from_id)
                  for from_id in rel_dict.iterkeys()]

    # don't return partial chains, i.e. instead of returning [a,b], [b,c] and
    # [a,b,c,d], just return [a,b,c,d]
    unique_chains = []
    for i, chain in enumerate(all_chains):
        other_chains = all_chains[:i] + all_chains[i+1:]
        if any([chain[0] in other_chain for other_chain in other_chains]):
            continue  # ignore this chain, test the next one
        unique_chains.append(chain)
    return unique_chains


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
