#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
The ``paula`` module converts a ``DiscourseDocumentGraph`` (possibly
containing multiple annotation layers) into a PAULA XML document. Our goal is
to produce the subset of the PAULA 'specification' that is understood by the
SaltNPepper converter framework

TODO: in Tiger (and other dominance graphs, there are no spans, only structs,
      e.g. struct: NP -> tok1, tok2, tok3)
"""

import os
from collections import defaultdict

from lxml import etree
from lxml.etree import Comment
from lxml.builder import ElementMaker

from discoursegraphs import (EdgeTypes, get_text, get_top_level_layers,
                             istoken, select_edges_by, select_nodes_by_layer,
                             tokens2text)
from discoursegraphs.util import (create_dir, ensure_xpointer_compatibility,
                                  natural_sort_key)
from discoursegraphs.relabel import relabel_nodes


NSMAP = {'xlink': 'http://www.w3.org/1999/xlink',
         'xml': 'http://www.w3.org/XML/1998/namespace'}
XMLBASE = '{%s}base' % NSMAP['xml']
XLINKHREF = '{%s}href' % NSMAP['xlink']

IGNORED_EDGE_ATTRIBS = ('layers', 'label', 'tiger:idref')
IGNORED_NODE_ATTRIBS = ('layers', 'label', 'metadata', 'tokens', 'tiger:id',
                        'tiger:art_id', 'tiger:orig_id')
IGNORED_TOKEN_ATTRIBS = IGNORED_NODE_ATTRIBS + ('tiger:token', 'tiger:word')


class PaulaDTDs(object):
    """
    enumerator for PAULA XML document type definitions (DTDs)

    Attributes
    ----------
    header : dtd
        ???
    struct : dtd
        for annoSet and hierarchical structure (tree/dependency) files
    mark : dtd
        for tokenization and span markable files
    text : dtd
        for primary text files
    feat : dtd
        for all files that use <feat> (instead of <multifeat>!) to annotate
        something, e.g. document/(sub)corpus metadata; annoFeat;
        token/span/struct/(pointing) rel annotation files
    rel : dtd
        for pointing relation files
    multifeat : dtd
        for all files that use <multifeat> to annotate something
    """
    header = 'paula_header.dtd'
    struct = 'paula_struct.dtd'
    mark = 'paula_mark.dtd'
    text = 'paula_text.dtd'
    feat = 'paula_feat.dtd'
    rel = 'paula_rel.dtd'
    multifeat = 'paula_multiFeat.dtd'


class PaulaDocument(object):
    """
    This class converts a DiscourseDocumentGraph into a PAULA XML document
    (i.e. a set of XML files describing one document annotated on multiple
    labels).
    """
    def __init__(self, docgraph, corpus_name='mycorpus', human_readable=False,
                 saltnpepper_compatible=True):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        corpus_name : str
            name of the corpus this document belongs to
        human_readable : bool
            adds node/edge label <!-- comments --> to the XML output for
            debugging purposes
        saltnpepper_compatible : bool
            don't generate certain PAULA file types that SaltNPepper can't
            handle
        """
        self.dg = docgraph
        self.human_readable = human_readable
        # remove file extension from document name
        self.name = docgraph.name.rsplit('.')[0]
        self.corpus_name = corpus_name
        # map file types to paula IDs
        self.paulamap = defaultdict(lambda: defaultdict(str))
        # map paula IDs to etrees
        self.files = {}
        # map file IDs to DTDs
        self.file2dtd = {}

        self.__make_xpointer_compatible()
        self.__gen_primary_text_file()
        self.__gen_tokenization_file()

        for top_level_layer in get_top_level_layers(docgraph):
            self.__gen_token_anno_file(top_level_layer)
            self.__gen_span_markables_file(top_level_layer,
                                           saltnpepper_compatible)
            self.__gen_hierarchy_file(top_level_layer)
            self.__gen_struct_anno_files(top_level_layer)
            self.__gen_rel_anno_file(top_level_layer)
            self.__gen_pointing_file(top_level_layer)
            self.__gen_pointing_anno_file(top_level_layer)
        self.__gen_annoset_file()

    def __make_xpointer_compatible(self):
        """
        ensure that all node and IDs in the document graph are valid
        xpointer IDs. this will relabel all node IDs in place in the discourse
        graph and change its ``.tokens`` list accordingly.
        """

        node_id_map = {node: ensure_xpointer_compatibility(node)
                       for node in self.dg.nodes_iter()}

        old_token_ids = self.dg.tokens
        # replace document graph with node relabeled version
        self.dg = relabel_nodes(self.dg, node_id_map, copy=True)
        self.dg.tokens = [node_id_map[tok] for tok in old_token_ids]

    def __gen_primary_text_file(self):
        """
        generate the PAULA file that contains the primary text of the document
        graph. (PAULA documents can have more than one primary text, but
        discoursegraphs only works with documents that are based on exactly one
        primary text.)

        Example
        -------
        <?xml version="1.0" standalone="no"?>
        <!DOCTYPE paula SYSTEM "paula_text.dtd">
        <paula version="1.1">
            <header paula_id="maz-1423.text" type="text"/>
            <body>Zum Angewöhnen ...</body>
        </paula>
        """
        paula_id = '{0}.{1}.text'.format(self.corpus_name, self.name)
        E, tree = gen_paula_etree(paula_id)
        tree.append(E.body(get_text(self.dg)))
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.text
        return paula_id

    def __gen_tokenization_file(self):
        """
        generate the PAULA file that contains the tokenization of the document
        graph. (In general, a PAULA document may contain more than one
        tokenization, but in discoursegraphs we'll only work with documents
        that have exactly one tokenization.)

        Example
        -------
        <?xml version="1.0" standalone="no"?>
        <!DOCTYPE paula SYSTEM "paula_mark.dtd">
        <paula version="1.1">
            <header paula_id="nolayer.maz-1423.tok"/>
            <markList xmlns:xlink="http://www.w3.org/1999/xlink" type="tok"
                xml:base="maz-1423.text.xml">
                <mark id="sTok1"
                    xlink:href="#xpointer(string-range(//body,'',1,3))" />
                <mark id="sTok2"
                    xlink:href="#xpointer(string-range(//body,'',5,10))" />
                ...
            </markList>
        </paula>
        """
        paula_id = '{0}.{1}.tok'.format(self.corpus_name, self.name)
        E, tree = gen_paula_etree(paula_id)
        self.paulamap['tokenization'] = paula_id

        base_paula_id = '{0}.{1}.text'.format(self.corpus_name, self.name)
        mlist = E('markList',
                  {'type': 'tok',
                   XMLBASE: base_paula_id+'.xml'})
        tok_tuples = self.dg.get_tokens()
        for (tid, onset, tlen) in get_onsets(tok_tuples):
            # even SaltNPepper still uses xpointers for string-ranges!
            xp = "#xpointer(string-range(//body,'',{0},{1}))".format(onset, tlen)
            mlist.append(E('mark', {'id': tid,
                                    XLINKHREF: xp}))
        tree.append(mlist)
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.mark
        return paula_id

    def __gen_span_markables_file(self, layer, saltnpepper_compatible=True):
        """
        <mark> elements are used to group tokens (continuous or discontinuos
        spans) for further annotation.
        A span markable file (*_seg.xml) contains a list of spans and the type
        of annotation that is applied to them
        (stored in <markList type="annotation type..."). As a consequence,
        each span markable file contains only spans of a single type
        (in discoursegraph: spans from a single namespace, e.g. syntax
        categories or entity mentions).

        Note: The annotations themselves are stored in other files, using
        <feat> or <multiFeat> elements.
        """
        paula_id = '{0}.{1}.{2}_{3}_seg'.format(layer, self.corpus_name,
                                            self.name, layer)
        E, tree = gen_paula_etree(paula_id)
        base_paula_id = '{0}.{1}.tok'.format(self.corpus_name, self.name)
        mlist = E('markList',
                  {'type': layer,
                   XMLBASE: base_paula_id+'.xml'})

        span_dict = defaultdict(lambda: defaultdict(str))
        edges = select_edges_by(self.dg, layer=layer,
                                edge_type=EdgeTypes.spanning_relation,
                                data=True)
        for source_id, target_id, edge_attrs in edges:
            span_dict[source_id][target_id] = edge_attrs

        target_dict = defaultdict(list)
        for source_id in span_dict:
            targets = sorted(span_dict[source_id], key=natural_sort_key)
            if saltnpepper_compatible:  # SNP doesn't like xpointer ranges
                xp = ' '.join('#{0}'.format(target_id)
                              for target_id in targets)
            else:  # PAULA XML 1.1 specification
                xp = '#xpointer(id({0})/range-to(id({1})))'.format(targets[0],
                                                                 targets[-1])
            mark = E('mark', {XLINKHREF: xp})
            if self.human_readable:
                # add <!-- comments --> containing the token strings
                mark.append(Comment(tokens2text(self.dg, targets)))
                target_dict[targets[0]].append(mark)
            else:
                mlist.append(mark)

        if self.human_readable:  # order <mark> elements by token ordering
            for target in sorted(target_dict, key=natural_sort_key):
                for mark in target_dict[target]:
                    mlist.append(mark)

        tree.append(mlist)
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.mark
        return paula_id

    def __gen_token_anno_file(self, top_level_layer):
        """
        creates an etree representation of a <multiFeat> file that describes
        all the annotations that only span one token (e.g. POS, lemma etc.).

        Note: discoursegraphs will create one token annotation file for each
        top level layer (e.g. conano, tiger etc.).
        """
        base_paula_id = '{0}.{1}.tok'.format(self.corpus_name, self.name)
        paula_id = '{0}.{1}.{2}.tok_multiFeat'.format(top_level_layer,
                                                   self.corpus_name,
                                                   self.name)
        E, tree = gen_paula_etree(paula_id)
        mflist = E('multiFeatList',
                   {XMLBASE: base_paula_id+'.xml'})

        for token_id in self.dg.tokens:
            mfeat = E('multiFeat',
                      {XLINKHREF: '#{0}'.format(token_id)})
            token_dict = self.dg.node[token_id]
            for feature in token_dict:
                # TODO: highly inefficient! refactor!1!!
                if feature not in IGNORED_TOKEN_ATTRIBS \
                   and feature.startswith(top_level_layer):
                    mfeat.append(E('feat',
                                   {'name': feature,
                                    'value': token_dict[feature]}))

            if self.human_readable:  # adds token string as a <!-- comment -->
                mfeat.append(Comment(token_dict[self.dg.ns+':token']))
            mflist.append(mfeat)

        tree.append(mflist)
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.multifeat
        return paula_id

    def __gen_hierarchy_file(self, layer):
        """
        Hierarchical structures (<structList> elements) are used to create
        hierarchically nested annotation graphs (e.g. to express consists-of
        relationships or dominance-edges in syntax trees, RST).
        A <struct> element will be created for each hierarchical node
        (e.g. an NP) with edges (<rel> elements) to each dominated element
        (e.g. tokens, other <struct> elements).

        NOTE: The types/labels of these newly create hierarchical nodes and
        edges aren't stored in this file, but in feat/multiFeat files
        referencing this one! See: __gen_struct_anno_files() and
        __gen_rel_anno_file()).

        There will be one hierarchy file for each top level layer.
        TODO: check, if we can omit hierarchy files for layers that don't
              contain dominance edges
        """
        paula_id = '{0}.{1}.{2}_{3}'.format(layer, self.corpus_name, self.name,
                                        layer)
        self.paulamap['hierarchy'][layer] = paula_id
        E, tree = gen_paula_etree(paula_id)

        dominance_edges = select_edges_by(
            self.dg, layer=layer, edge_type=EdgeTypes.dominance_relation,
            data=True)
        span_edges = select_edges_by(
            self.dg, layer=layer, edge_type=EdgeTypes.spanning_relation,
            data=True)
        dominance_dict = defaultdict(lambda: defaultdict(str))
        for source_id, target_id, edge_attrs in dominance_edges:
            if source_id != layer+':root_node':
                dominance_dict[source_id][target_id] = edge_attrs

        # in PAULA XML, token spans are also part of the hierarchy
        for source_id, target_id, edge_attrs in span_edges:
            if istoken(self.dg, target_id):
                dominance_dict[source_id][target_id] = edge_attrs

        # NOTE: we don't add a base file here, because the nodes could be
        # tokens or structural nodes
        slist = E('structList', {'type': layer})
        for source_id in dominance_dict:
            struct = E('struct',
                       {'id': str(source_id)})
            if self.human_readable:
                struct.append(Comment(self.dg.node[source_id].get('label')))

            for target_id in dominance_dict[source_id]:
                if istoken(self.dg, target_id):
                    href = '{0}.xml#{1}'.format(self.paulamap['tokenization'],
                                              target_id)
                else:
                    href = '#{0}'.format(target_id)

                rel = E(
                    'rel',
                    {'id': 'rel_{0}_{1}'.format(source_id, target_id),
                     'type': dominance_dict[source_id][target_id]['edge_type'],
                     XLINKHREF: href})
                struct.append(rel)
                if self.human_readable:
                    struct.append(
                        Comment(self.dg.node[target_id].get('label')))
            slist.append(struct)
        tree.append(slist)
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.struct
        return paula_id

    def __gen_struct_anno_files(self, top_level_layer):
        """
        A struct annotation file contains node (struct) attributes (of
        non-token nodes). It is e.g. used to annotate the type of a syntactic
        category (NP, VP etc.).

        See also: __gen_hierarchy_file()
        """
        paula_id = '{0}.{1}.{2}_{3}_struct'.format(top_level_layer,
                                               self.corpus_name, self.name,
                                               top_level_layer)
        E, tree = gen_paula_etree(paula_id)

        base_paula_id = self.paulamap['hierarchy'][top_level_layer]
        mflist = E('multiFeatList',
                   {XMLBASE: base_paula_id+'.xml'})

        for node_id in select_nodes_by_layer(self.dg, top_level_layer):
            if not istoken(self.dg, node_id):
                mfeat = E('multiFeat',
                          {XLINKHREF: '#{0}'.format(node_id)})
                node_dict = self.dg.node[node_id]
                for attr in node_dict:
                    if attr not in IGNORED_NODE_ATTRIBS:
                        mfeat.append(
                            E('feat',
                              {'name': attr, 'value': node_dict[attr]}))
                if self.human_readable:  # adds node label as a <!--comment-->
                    mfeat.append(Comment(node_dict.get('label')))
                mflist.append(mfeat)
        tree.append(mflist)
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.multifeat
        return paula_id

    def __gen_rel_anno_file(self, top_level_layer):
        """
        A rel annotation file contains edge (rel)
        attributes. It is e.g. used to annotate the type of a dependency
        relation (subj, obj etc.).

        See also: __gen_hierarchy_file()
        """
        paula_id = '{0}.{1}.{2}_{3}_rel'.format(top_level_layer, self.corpus_name,
                                            self.name, top_level_layer)
        E, tree = gen_paula_etree(paula_id)

        dominance_edges = select_edges_by(
            self.dg, layer=top_level_layer,
            edge_type=EdgeTypes.dominance_relation, data=True)
        dominance_dict = defaultdict(lambda: defaultdict(str))
        for source_id, target_id, edge_attrs in dominance_edges:
            if source_id != top_level_layer+':root_node':
                dominance_dict[source_id][target_id] = edge_attrs

        base_paula_id = self.paulamap['hierarchy'][top_level_layer]
        mflist = E('multiFeatList',
                   {XMLBASE: base_paula_id+'.xml'})
        for source_id in dominance_dict:
            for target_id in dominance_dict[source_id]:
                rel_href = '#rel_{0}_{1}'.format(source_id, target_id)
                mfeat = E('multiFeat',
                          {XLINKHREF: rel_href})
                edge_attrs = dominance_dict[source_id][target_id]
                for edge_attr in edge_attrs:
                    if edge_attr not in IGNORED_EDGE_ATTRIBS:
                        mfeat.append(E('feat',
                                       {'name': edge_attr,
                                        'value': edge_attrs[edge_attr]}))

                if self.human_readable:  # adds edge label as a <!--comment-->
                    source_label = self.dg.node[source_id].get('label')
                    target_label = self.dg.node[target_id].get('label')
                    mfeat.append(Comment(u'{0} - {1}'.format(source_label,
                                                           target_label)))
                mflist.append(mfeat)

        tree.append(mflist)
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.multifeat
        return paula_id

    def __gen_pointing_file(self, top_level_layer):
        """
        Creates etree representations of PAULA XML files modeling pointing
        relations. Pointing relations are ahierarchical edges between any
        two nodes (``tok``, ``mark`` or ``struct``). They are used to signal
        pointing relations between tokens (e.g. in a dependency parse tree)
        or the coreference link between anaphora and antecedent.
        """
        paula_id = '{0}.{1}.{2}_{3}_pointing'.format(top_level_layer,
                                                 self.corpus_name, self.name,
                                                 top_level_layer)
        self.paulamap['pointing'][top_level_layer] = paula_id
        E, tree = gen_paula_etree(paula_id)

        pointing_edges = select_edges_by(self.dg, layer=top_level_layer,
                                         edge_type=EdgeTypes.pointing_relation,
                                         data=True)
        pointing_dict = defaultdict(lambda: defaultdict(str))
        for source_id, target_id, edge_attrs in pointing_edges:
            pointing_dict[source_id][target_id] = edge_attrs

        # NOTE: we don't add a base file here, because the nodes could be
        # tokens or structural nodes
        rlist = E('relList')
        for source_id in pointing_dict:
            for target_id in pointing_dict[source_id]:
                source_href = self.__gen_node_href(top_level_layer, source_id)
                target_href = self.__gen_node_href(top_level_layer, target_id)
                rel = E('rel',
                        {'id': 'rel_{0}_{1}'.format(source_id, target_id),
                         XLINKHREF: source_href,
                         'target': target_href})

                # adds source/target node labels as a <!-- comment -->
                if self.human_readable:
                    source_label = self.dg.node[source_id].get('label')
                    target_label = self.dg.node[target_id].get('label')
                    rel.append(Comment(u'{0} - {1}'.format(source_label,
                                                         target_label)))
                rlist.append(rel)
        tree.append(rlist)
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.rel
        return paula_id

    def __gen_pointing_anno_file(self, top_level_layer):
        """
        A pointing relation annotation file contains edge (rel)
        attributes. It is e.g. used to annotate the type of a pointing
        relation.

        TODO: merge code with __gen_rel_anno_file() if possible!
        """
        paula_id = '{0}.{1}.{2}_{3}_pointing_multiFeat'.format(top_level_layer,
                                                           self.corpus_name,
                                                           self.name,
                                                           top_level_layer)
        E, tree = gen_paula_etree(paula_id)

        pointing_edges = select_edges_by(self.dg, layer=top_level_layer,
                                         edge_type=EdgeTypes.pointing_relation,
                                         data=True)
        pointing_dict = defaultdict(lambda: defaultdict(str))
        for source_id, target_id, edge_attrs in pointing_edges:
            pointing_dict[source_id][target_id] = edge_attrs

        base_paula_id = self.paulamap['pointing'][top_level_layer]
        mflist = E('multiFeatList',
                   {XMLBASE: base_paula_id+'.xml'})
        for source_id in pointing_dict:
            for target_id in pointing_dict[source_id]:
                rel_href = '#rel_{0}_{1}'.format(source_id, target_id)
                mfeat = E('multiFeat',
                          {XLINKHREF: rel_href})
                edge_attrs = pointing_dict[source_id][target_id]
                for edge_attr in edge_attrs:
                    if edge_attr not in IGNORED_EDGE_ATTRIBS:
                        mfeat.append(E('feat',
                                       {'name': edge_attr,
                                        'value': edge_attrs[edge_attr]}))

                if self.human_readable:  # adds edge label as a <!--comment-->
                    source_label = self.dg.node[source_id].get('label')
                    target_label = self.dg.node[target_id].get('label')
                    mfeat.append(Comment(u'{0} - {1}'.format(source_label,
                                                           target_label)))
                mflist.append(mfeat)

        tree.append(mflist)
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.multifeat
        return paula_id

    def __gen_annoset_file(self):
        """
        An ``annoSet`` file describes the set of annotations contained in a
        document (i.e. it lists all annotation files that belong to a PAULA
        document). Each PAULA document must contain an annoSet file.

        An ``annoSet`` file can also be used to list the contents of a
        (sub)corpus, but we're not using this feature in discoursegraphs, yet.
        """
        paula_id = '{0}.{1}.anno'.format(self.corpus_name, self.name)
        E, tree = gen_paula_etree(paula_id)

        slist = E('structList', {'type': 'annoSet'})
        # NOTE: we could group all the annotations into different structs
        # but I don't see the point. We're already using namespaces, after all
        struct = E('struct', {'id': 'anno_all_annotations'})
        for i, file_id in enumerate(self.files):
            struct.append(E('rel',
                            {'id': 'rel_{0}'.format(i),
                             XLINKHREF: file_id+'.xml'}))
        slist.append(struct)
        tree.append(slist)
        self.files[paula_id] = tree
        self.file2dtd[paula_id] = PaulaDTDs.struct
        return paula_id

    def __gen_node_href(self, layer, node_id):
        """
        generates a complete xlink:href for any node (token node,
        structure node etc.) in the docgraph. This will only work AFTER
        the corresponding PAULA files have been created (and their file names
        are registered in ``self.paulamap``).
        """
        if istoken(self.dg, node_id):
            base_paula_id = self.paulamap['tokenization']
        else:
            base_paula_id = self.paulamap['hierarchy'][layer]
        return '{0}.xml#{1}'.format(base_paula_id, node_id)


def paula_etree_to_string(tree, dtd_filename):
    """convert a PAULA etree into an XML string."""
    return etree.tostring(
        tree, pretty_print=True, xml_declaration=True,
        encoding="UTF-8", standalone='no',
        doctype='<!DOCTYPE paula SYSTEM "{0}">'.format(dtd_filename))


def gen_paula_etree(paula_id):
    """
    creates an element tree representation of an empty PAULA XML file.
    """
    E = ElementMaker(nsmap=NSMAP)
    tree = E('paula', version='1.1')
    tree.append(E('header', paula_id=paula_id))
    return E, tree


def get_onsets(token_tuples):
    """
    Parameters
    ----------
    token_tuples : list of (str, unicode)
        a list/generator of (token ID, token string) tuples

    Returns
    -------
    onset_tuples : generator of (str, int, int)
        A list/generator of (token ID, onset, token length) tuples.
        Note that PAULA starts counting string onsets with 1!
    """
    onset = 1
    for (token_id, token) in token_tuples:
        yield (token_id, onset, len(token))
        onset += (len(token) + 1)


def write_paula(docgraph, output_root_dir, human_readable=False):
    """
    converts a DiscourseDocumentGraph into a set of PAULA XML files
    representing the same document.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        the document graph to be converted
    """
    paula_document = PaulaDocument(docgraph, human_readable=human_readable)
    error_msg = ("Please specify an output directory.\nPaula documents consist"
                 " of multiple files, so we can't just pipe them to STDOUT.")
    assert isinstance(output_root_dir, str), error_msg
    document_dir = os.path.join(output_root_dir, paula_document.name)
    if not os.path.isdir(document_dir):
        create_dir(document_dir)
    for paula_id in paula_document.files:
        with open(os.path.join(document_dir, paula_id+'.xml'), 'w') as outfile:
            outfile.write(
                paula_etree_to_string(paula_document.files[paula_id],
                                      paula_document.file2dtd[paula_id]))
