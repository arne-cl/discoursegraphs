#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts an MMAX2-annotated document into a networkx-based directed
graph (``DiscourseDocumentGraph``).
"""

import os
from lxml import etree

import discoursegraphs as dg
from discoursegraphs import (DiscourseDocumentGraph, EdgeTypes,
                             select_nodes_by_layer)
from discoursegraphs.util import add_prefix, ensure_unicode, natural_sort_key
from discoursegraphs.readwrite.generic import convert_spanstring, generic_converter_cli


class MMAXProject(object):
    """
    represents an MMAX annotation project, which may contain one or more
    files annotated on zero or more levels.

    TODO: refactor this into an MMAXCorpusGraph(DiscourseCorpusGraph)
    """
    def __init__(self, project_path):
        self.project_path = project_path
        self.paths, self.annotations, self.stylesheet = \
            self._parse_common_paths_file(project_path)

    @staticmethod
    def _parse_common_paths_file(project_path):
        """
        Parses a common_paths.xml file and returns a dictionary of paths,
        a dictionary of annotation level descriptions and the filename
        of the style file.

        Parameters
        ----------
        project_path : str
            path to the root directory of the MMAX project

        Returns
        -------
        paths : dict
            maps from MMAX file types (str, e.g. 'basedata' or 'markable')
            to the relative path (str) containing files of this type
        annotations : dict
            maps from MMAX annotation level names (str, e.g. 'sentence',
            'primmark') to a dict of features.
            The features are: 'schemefile' (maps to a file),
            'customization_file' (ditto) and 'file_extension' (maps to the
            file name ending used for all annotations files of this level)
        stylefile : str
            name of the (default) style file used in this MMAX project
        """
        common_paths_file = os.path.join(project_path, 'common_paths.xml')
        tree = etree.parse(common_paths_file)

        paths = {}
        path_vars = ['basedata', 'scheme', 'style', 'style', 'customization',
                     'markable']
        for path_var in path_vars:
            specific_path = tree.find('//{}_path'.format(path_var)).text
            paths[path_var] = specific_path if specific_path else project_path
        paths['project_path'] = project_path

        annotations = {}
        for level in tree.iterfind('//level'):
            annotations[level.attrib['name']] = {
                'schemefile': level.attrib['schemefile'],
                'customization_file': level.attrib['customization_file'],
                'file_extension': level.text[1:]}

        stylesheet = tree.find('//stylesheet').text
        return paths, annotations, stylesheet


class MMAXDocumentGraph(DiscourseDocumentGraph):
    """
    represents a MMAX2-annotated document as a multidigraph.

    Attributes
    ----------
    ns : str
        the namespace of the graph (default: mmax)
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text
    root : str
        name of the document root node ID
        (default: 'mmax:root_node')
    """
    def __init__(self, mmax_base_file, name=None, namespace='mmax',
                 precedence=False, connected=False,
                 ignore_sentence_annotations=True):
        """
        Parameters
        ----------
        mmax_base_file : str
            relative or absolute path to an MMAX2 document base file (*.mmax)
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input *.mmax file is used.
        namespace : str
            the namespace of the graph (default: mmax)
        precedence : bool
            add precedence relation edges (root precedes token1, which precedes
            token2 etc.)
        connected : bool
            Make the graph connected, i.e. add an edge from root to each
            token. This doesn't do anything, if
            precendence=True.
        ignore_sentence_annotations : bool
            If True, sentences will not be annotated in the document graph
            (i.e. there will be no 'mmax:sentence' node for each sentence
            and no edge connecting it to each token node). (Default: True)
            Only set this to false if you know what you're doing, as this
            will mess up the output of Exmaralda, CoNLL and the like (i.e.
            they will interpret sentence annotations as coreferences)!
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(MMAXDocumentGraph, self).__init__(namespace=namespace)

        self.name = name if name else os.path.basename(mmax_base_file)
        self.ns = namespace
        self.root = self.ns+':root_node'
        self.add_node(self.root, layers={self.ns})
        self.tokens = []
        self.ignore_sentence_annotations = ignore_sentence_annotations

        mmax_base_file = os.path.abspath(os.path.expanduser(mmax_base_file))
        mmax_rootdir, _ = os.path.split(mmax_base_file)

        self.mmax_project = MMAXProject(mmax_rootdir)
        words_file = self.get_word_file(mmax_base_file)

        if precedence:
            self.add_token_layer(words_file, connected=False)
            self.add_precedence_relations()
        else:
            self.add_token_layer(words_file, connected)

        if self.ignore_sentence_annotations:
            annotation_layers = set(self.mmax_project.annotations)
            annotation_layers.discard('sentence')
        else:
            annotation_layers = self.mmax_project.annotations

        for layer_name in annotation_layers:
            layer_dict = self.mmax_project.annotations[layer_name]
            file_id = self.get_file_id(mmax_base_file)
            annotation_file = os.path.join(
                mmax_rootdir,
                self.mmax_project.paths['markable'],
                file_id+layer_dict['file_extension'])
            self.add_annotation_layer(annotation_file, layer_name)

        # the sentence root nodes can only be extracted after all the
        # annotation layers are parsed
        sentence_root_nodes, token_nodes = self.get_sentences_and_token_nodes()
        sentence_token_tuples = sort_sentences_by_token_order(sentence_root_nodes, token_nodes)
        self.sentences, token_nodes = zip(*sentence_token_tuples)
        # add the list of tokens in a sentence to the sentence root node
        for sent_root_id, sent_token_node_ids in sentence_token_tuples:
            self.node[sent_root_id]['tokens'] = sent_token_node_ids

    def get_sentences_and_token_nodes(self):
        """
        Returns a list of sentence root node IDs and a list of sentences,
        where each list contains the token node IDs of that sentence.
        Both lists will be empty if sentences were not annotated in the original
        MMAX2 data.

        TODO: Refactor this! There's code overlap with
        self.add_annotation_layer(). Ideally, we would always import sentence
        annotations and filter them out in the exporters (e.g. Exmaralda,
        CoNLL), probably by modifying get_pointing_chains().

        Returns
        -------
        sentence_root_nodes : list of str
            a list of all sentence root node IDs, in the order they occur in the
            text
        token_nodes : list of list of str
            a list of lists. each list represents a sentence and contains
            token node IDs (in the order they occur in the text)
        """
        token_nodes = []
        # if sentence annotations were ignored during MMAXDocumentGraph
        # construction, we need to extract sentence/token node IDs manually
        if self.ignore_sentence_annotations:
            mp = self.mmax_project
            layer_dict = mp.annotations['sentence']
            file_id = self.get_file_id(self.name)
            sentence_anno_file = os.path.join(mp.project_path,
                mp.paths['markable'], file_id+layer_dict['file_extension'])
            tree = etree.parse(sentence_anno_file)
            root = tree.getroot()
            sentence_root_nodes = []
            for markable in root.iterchildren():
                sentence_root_nodes.append(markable.attrib['id'])

                sentence_token_nodes = []
                for token_id in spanstring2tokens(self, markable.attrib['span']):
                    # ignore token IDs that aren't used in the *_words.xml file
                    # NOTE: we only need this filter for broken files in the PCC corpus
                    if token_id in self.tokens:
                        sentence_token_nodes.append(token_id)
                        self.add_node(markable.attrib['id'], layers={self.ns, self.ns+':sentence'})
                token_nodes.append(sentence_token_nodes)
        else:
            sentence_root_nodes = list(select_nodes_by_layer(self, self.ns+':sentence'))
            for sent_node in sentence_root_nodes:
                sentence_token_nodes = []
                for token_id in self.get_token_nodes_from_sentence(sent_node):
                    # ignore token IDs that aren't used in the *_words.xml file
                    # NOTE: we only need this filter for broken files in the PCC corpus
                    if token_id in self.tokens:
                        sentence_token_nodes.append(token_id)
                token_nodes.append(sentence_token_nodes)
        return sentence_root_nodes, token_nodes

    def get_token_nodes_from_sentence(self, sentence_root_node):
        """returns a list of token node IDs belonging to the given sentence"""
        return spanstring2tokens(self, self.node[sentence_root_node][self.ns+':span'])

    @staticmethod
    def get_file_id(mmax_base_file):
        """
        given an MMAX base file (``*.mmax``), returns its file ID.
        """
        # removes '.mmax' from filename
        return os.path.basename(mmax_base_file)[:-5]

    def get_word_file(self, mmax_base_file):
        """
        parses an MMAX base file (``*.mmax``) and returns the path
        to the corresponding ``_words.xml`` file (which contains
        the tokens of the document).
        """
        return os.path.join(self.mmax_project.paths['project_path'],
                            self.mmax_project.paths['basedata'],
                            etree.parse(mmax_base_file).find('//words').text)

    def add_token_layer(self, words_file, connected):
        """
        parses a _words.xml file, adds every token to the document graph
        and adds an edge from the MMAX root node to it.

        Parameters
        ----------
        connected : bool
            Make the graph connected, i.e. add an edge from root to each
            token.
        """
        for word in etree.parse(words_file).iterfind('//word'):
            token_node_id = word.attrib['id']
            self.tokens.append(token_node_id)
            token_str = ensure_unicode(word.text)
            self.add_node(token_node_id,
                          layers={self.ns, self.ns+':token'},
                          attr_dict={self.ns+':token': token_str,
                                     'label': token_str})
            if connected:
                self.add_edge(self.root, token_node_id,
                              layers={self.ns, self.ns+':token'})

    def add_annotation_layer(self, annotation_file, layer_name):
        """
        adds all markables from the given annotation layer to the discourse
        graph.
        """
        assert os.path.isfile(annotation_file), \
            "Annotation file doesn't exist: {}".format(annotation_file)
        tree = etree.parse(annotation_file)
        root = tree.getroot()

        default_layers = {self.ns, self.ns+':markable', self.ns+':'+layer_name}

        # avoids eml.org namespace handling
        for markable in root.iterchildren():
            markable_node_id = markable.attrib['id']
            markable_attribs = add_prefix(markable.attrib, self.ns+':')
            self.add_node(markable_node_id,
                          layers=default_layers,
                          attr_dict=markable_attribs,
                          label=markable_node_id+':'+layer_name)

            for target_node_id in spanstring2tokens(self, markable.attrib['span']):
                # manually add to_node if it's not in the graph, yet
                # cf. issue #39
                if target_node_id not in self:
                    self.add_node(target_node_id,
                                  # adding 'mmax:layer_name' here could be
                                  # misleading (e.g. each token would be part
                                  # of the 'mmax:sentence' layer
                                  layers={self.ns, self.ns+':markable'},
                                  label=target_node_id)

                self.add_edge(markable_node_id, target_node_id,
                              layers=default_layers,
                              edge_type=EdgeTypes.spanning_relation,
                              label=self.ns+':'+layer_name)

            # this is a workaround for Chiarcos-style MMAX files
            if has_antecedent(markable):
                antecedent_pointer = markable.attrib['anaphor_antecedent']
                # mmax2 supports weird double antecedents,
                # e.g. "markable_1000131;markable_1000132", cf. Issue #40
                #
                # handling these double antecendents increases the number of
                # chains, cf. commit edc28abdc4fd36065e8bbf5900eeb4d1326db153
                for antecedent in antecedent_pointer.split(';'):
                    ante_split = antecedent.split(":")
                    if len(ante_split) == 2:
                        # mark group:markable_n or secmark:markable_n as such
                        edge_label = '{}:antecedent'.format(ante_split[0])
                    else:
                        edge_label = ':antecedent'

                    # handles both 'markable_n' and 'layer:markable_n'
                    antecedent_node_id = ante_split[-1]
                    if len(ante_split) == 2:
                        antecedent_layer = ante_split[0]
                        default_layers.add('{0}:{1}'.format(self.ns, antecedent_layer))

                    # manually add antecedent node if it's not yet in the graph
                    # cf. issue #39
                    if antecedent_node_id not in self:
                        self.add_node(antecedent_node_id,
                                      layers=default_layers)

                    self.add_edge(markable_node_id, antecedent_node_id,
                                  layers=default_layers,
                                  edge_type=EdgeTypes.pointing_relation,
                                  label=self.ns+edge_label)


def has_antecedent(markable):
    """
    checks, if a markable has an antecedent. This function is only useful
    for Chiarcos-style MMAX projects, where anaphoric relations are marked
    as pointing relations between markables.

    Parameters
    ----------
    markable : etree._Element
        an etree element representing an MMAX markable

    Returns
    -------
    has_antecedent : bool
        Returns True, iff the markable has an antecedent.
    """
    return ('anaphor_antecedent' in markable.attrib
            and markable.attrib['anaphor_antecedent'] != 'empty')


def spanstring2tokens(docgraph, span_string):
    """
    Converts a span string (e.g. 'word_88..word_91') into a list of token
    IDs (e.g. ['word_88', 'word_89', 'word_90', 'word_91']. Token IDs that
    do not occur in the given document graph will be filtered out.

    Q: Why are some token IDs missing in a document graph?
    A: They either have been removed manually (e.g. because someone thought
       the annotation/tokenization was 'wrong') or have been renamed
       during the merging of several document graphs.

    Parameters
    ----------
    docgraph : MMAXDocumentGraph
        a document graph which represent an MMAX2 annotated document
    span_string : str
        a string representing a (non)-contiguous series of tokens by their
        token IDs

    Returns
    -------
    existing_tokens : list of str
        a list of all those tokens that are represented by the span string
        and which actually exist in the given graph
    """
    tokens = convert_spanstring(span_string)
    existing_nodes = set(docgraph.nodes())

    existing_tokens = []
    for tok in tokens:
        if tok in existing_nodes:
            existing_tokens.append(tok)
        else: # we're trying to catch all token IDs that have been
              # renamed during merging of document graphs / annotation layers
            if hasattr(docgraph, 'renamed_nodes'):
                renamed_token_id = docgraph.renamed_nodes.get(tok)
                if renamed_token_id in existing_nodes:
                    existing_tokens.append(renamed_token_id)
            # else: there was no merging /renaming going on, so the
            # token is missing because it's <word> element was removed
            # from the associated *_words.xml file.
            # This is another 'bug' in the PCC corpus, cf. issue #134
    return existing_tokens


def spanstring2text(docgraph, span_string):
    """
    converts a span of tokens (str, e.g. 'word_88..word_91') into a string
    that contains the tokens itself.
    """
    token_node_ids = spanstring2tokens(docgraph, span_string)
    return u' '.join(docgraph.node[tok_node_id][docgraph.ns+':token']
                     for tok_node_id in token_node_ids)


def sort_sentences_by_token_order(sentence_root_nodes, token_nodes):
    """
    Given a list of sentence markables (i.e. sentence root nodes) and a list of
    lists of token markables (one list per sentence), returns a list of
    (sentence root node, token nodes) tuples. The result is sorted by the
    order in which the tokens occur in the text.

    Parameters
    ----------
    sentence_root_nodes : list of str
        a list of all sentence root node IDs
    token_nodes : list of list of str
        a list of lists. each list represents a sentence and contains
        token node IDs (in the order they occur in the text)

    Returns
    -------
    sorted_sentence_tuples : list of (str, list of str) tuples
        a list of all sentences in the order they occur in the text. each
        sentence is represented by an list of ordered token node IDs
    """
    def sentence_sort_key(sentence_token_tuple):
        """
        extracts a sortable key from the first token node ID of a sentence
        """
        return natural_sort_key(sentence_token_tuple[1][0])

    sentence_token_tuples = zip(sentence_root_nodes, token_nodes)
    return sorted(sentence_token_tuples, key=sentence_sort_key)


def get_potential_markables(docgraph):
    """
    returns a list of all NPs and PPs in the given docgraph.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        a document graph that (at least) contains syntax trees
        (imported from Tiger XML files)

    Returns
    -------
    potential_markables : list of str or int
        Node IDs of all nodes that represent an NP/PP syntactical category/phrase
        in the input document. If an NP is embedded in a PP, only the node
        ID of the PP is returned.
    """
    potential_markables = []

    for node_id, nattr in dg.select_nodes_by_layer(docgraph, 'tiger:syntax', data=True):
        if nattr['tiger:cat'] == 'NP':
            # if an NP is embedded into a PP, only print the PP
            pp_parent = False
            for source, target in docgraph.in_edges(node_id):
                parent_node = docgraph.node[source]
                if 'tiger:cat' in parent_node and parent_node['tiger:cat'] == 'PP':
                    potential_markables.append(source) # add parent PP phrase
                    pp_parent = True
            if not pp_parent:
                potential_markables.append(node_id) # add NP phrase

        elif nattr['tiger:cat'] == 'PP':
            potential_markables.append(node_id) # add PP phrase
    return potential_markables



# instanciate an MMAX document graph with a pseudo-function
read_mmax2 = MMAXDocumentGraph


if __name__ == "__main__":
    generic_converter_cli(MMAXDocumentGraph,
                          '*.mmax file (MMAX2 annotation file)')
