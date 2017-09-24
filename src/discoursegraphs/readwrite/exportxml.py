#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

'''
The ``exportxml`` module will convert a corpus in Negra ExportXML format [1]
(e.g. Tüba-D/Z [2]) into a document graph.

[1] http://www.sfs.uni-tuebingen.de/resources/exformat3.ps
[2] http://www.sfs.uni-tuebingen.de/ascl/ressourcen/corpora/tueba-dz.html

Usage
=====

1.  How to extract coreference relations from Tüba-D/Z?

The corpus distinguishes four different types of coreference relations:

- anaphoric (``Anaphorisches Pronomen``)
- cataphoric (``Kataphorisches Pronomen``)
- coreferential (``Diskurs-altes nicht-Pronomen``)
- splitRelation (a word or syntax category node is marked as an anaphora
  with multiple antecedents)

In order to simplify the query process, I marked all these relations as
``exportxml:coreference``.

Here are the coresponding definitions in the ExportXML header:

<edge name="relation" parent="word|node">
  <enum-attr name="type">
   <val name="anaphoric" description="Anaphorisches Pronomen"/>
   <val name="cataphoric" description="Kataphorisches Pronomen"/>
   <val name="coreferential" description="Diskurs-altes nicht-Pronomen"/>
  </enum-attr>
  <node-ref name="target"/>
</edge>

<edge name="splitRelation" parent="word|node">
  <enum-attr name="type">
  </enum-attr>
  <text-attr name="target"/>
</edge>


'''

import os
import re
import sys
import warnings

from lxml import etree

import discoursegraphs as dg
from discoursegraphs import DiscourseDocumentGraph
from discoursegraphs.readwrite.generic import (
    convert_spanstring, XMLElementCountTarget)
from discoursegraphs.util import add_prefix


# example node ID: 's_1_n_506' -> sentence 1, node 506
NODE_ID_REGEX = re.compile('s_(\d+)_n_(\d+)')


class ExportXMLCorpus(object):
    """
    represents an ExportXML formatted corpus (e.g. Tüba-D/Z) as an
    iterable over ExportXMLDocumentGraph instances (or an iterable over
    <text> elements if ``debug`` is set to ``True``).

    This class is used to 'parse' an ExportXML file iteratively, using as
    little memory as possible. To retrieve the document graphs of the
    documents contained in the corpus, simply iterate over the class
    instance (or use the ``.next()`` method).
    """
    def __init__(self, exportxml_file, name=None, debug=False):
        """
        Parameters
        ----------
        exportxml_file : str
            path to an ExportXML formatted corpus file
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        debug : bool
            If True, yield the etree element representations of the <text>
            elements found in the document.
            If False, create an iterator that parses the documents
            contained in the file into ExportXMLDocumentGraph instances.
            (default: False)
        """
        self.name = name if name else os.path.basename(exportxml_file)
        self._num_of_documents = None
        self.exportxml_file = exportxml_file
        self.path = os.path.abspath(exportxml_file)
        self.debug = debug

        self.__context = None
        self._reset_corpus_iterator()

    def _reset_corpus_iterator(self):
        """
        create an iterator over all documents in the file (i.e. all
        <text> elements). The recover parameter is used, as the Tüba-D/Z 8.0
        corpus used for testing isn't completely valid XML (i.e. there are two
        element IDs used twice).

        Once you have iterated over all documents, call this method again
        if you want to iterate over them again.
        """
        self.__context = etree.iterparse(self.exportxml_file, events=('end',),
                                         tag='text', recover=True)

    def __len__(self):
        if self._num_of_documents is not None:
            return self._num_of_documents
        elif self.name == 'tuebadz-8.0-mit-NE+Anaphern+Diskurs.exml.xml':
            return 3258  # I'll burn in hell for this!
        else:
            return self._get_num_of_documents()

    def _get_num_of_documents(self):
        '''
        counts the number of documents in an ExportXML file.
        adapted from Listing 2 on
        http://www.ibm.com/developerworks/library/x-hiperfparse/
        '''
        parser = etree.XMLParser(target = XMLElementCountTarget('text'))
        # When iterated over, 'results' will contain the output from
        # target parser's close() method
        num_of_documents = etree.parse(self.exportxml_file, parser)
        self._num_of_documents = num_of_documents
        return num_of_documents

    def __iter__(self):
        return iter(self.text_iter(self.__context))

    def next(self):
        # to build an iterable, __iter__() would be sufficient,
        # but adding a next() method is quite common
        return self.__iter__().next()

    def text_iter(self, context):
        """
        Iterates over all the elements in an iterparse context
        (here: <text> elements) and yields an ExportXMLDocumentGraph instance
        for each of them. For efficiency, the elements are removed from the
        DOM / main memory after processing them.

        If ``self.debug`` is set to ``True`` (in the ``__init__`` method),
        this method will yield <text> elements, which can be used to construct
        ``ExportXMLDocumentGraph``s manually.
        """
        for _event, elem in context:
            if not self.debug:
                yield ExportXMLDocumentGraph(elem, name=elem.attrib[add_ns('id')])
            else:
                yield elem
            # removes element (and references to it) from memory after processing it
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        del context


class ExportXMLDocumentGraph(DiscourseDocumentGraph):
    """
    represents an ExportXML document as a document graph.
    """
    def __init__(self, text_element=None, name=None, namespace='exportxml',
                 precedence=False, ignore_relations=False,
                 ignore_splitrelations=False, ignore_secedges=False):
        """
        creates a document graph from a <text> element from an ExportXML file.

        Parameters
        ----------
        text_element : lxml.etree._Element or str or None
            A <text> element from an ExportXML file parsed with lxml or
            a path to a file containing a <text> element. If None, return
            an empty document graph.
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the xml:id of the <text> element is used
        namespace : str
            the namespace of the document (default: exportxml)
        precedence : bool
            If True, add precedence relation edges
            (root precedes token1, which precedes token2 etc.)
        ignore_relations : bool
            If True, don't add pointing relations representing coreferences
            and discourse relations.
        ignore_splitrelations : bool
            If True, don't add pointing coreference relations where the
            antecedent consists of non-adjacent tokens
        ignore_secedges : bool
            If True, don't add pointing relations representing secondary
            edges (between elements in a syntax tree)
        """
        text_id = text_element.attrib[add_ns('id')]
        # super calls __init__() of base class DiscourseDocumentGraph
        super(ExportXMLDocumentGraph, self).__init__(namespace=namespace, root=text_id)

        if text_element is None:
            return

        if isinstance(text_element, str):
            _event, text_element = etree.iterparse(
                text_element, events=('end',), tag='text', recover=True).next()

        self.name = name if name else text_id

        self.sentences = []
        self.tokens = []

        self.ignore_relations = ignore_relations
        self.ignore_splitrelations = ignore_splitrelations
        self.ignore_secedges = ignore_secedges

        self.parsers = {
            'connective': self.add_connective,
            'discRel': self.add_discrel,
            'edu': self.add_edu,
            'edu-range': self.add_edurange,
            'ne': self.add_ne,
            # add_node() is already present in graph classes
            'node': self.add_node_element,
            'relation': self.add_relation,
            'secEdge': self.add_secedge,
            'sentence': self.add_sentence,
            'splitRelation': self.add_splitrelation,
            'topic': self.add_topic,
            'word': self.add_word
        }

        self.parse_descedant_elements(text_element)

        if precedence:
            self.add_precedence_relations()

    def parse_child_elements(self, element):
        '''parses all children of an etree element'''
        for child in element.iterchildren():
            self.parsers[child.tag](child)

    def parse_descedant_elements(self, element):
        '''parses all descendants of an etree element'''
        for descendant in element.iterdescendants():
            self.parsers[descendant.tag](descendant)

    def add_connective(self, connective):
        """
        Parameters
        ----------
        connective : etree.Element
            etree representation of a <connective> element
            (annotates connective tokens)

        Example
        -------
          <word xml:id="s29_1" form="Als" pos="KOUS" lemma="als" func="-"
                parent="s29_500" dephead="s29_14" deprel="KONJ">
              <connective konn="als" rel1="Temporal" rel2="enable"/>
          </word>
        """
        word_node_id = self.get_element_id(connective)
        # add a key 'connective' to the token with add rel1/rel2 attributes as a dict and
        # add the token to the namespace:connective layer
        connective_attribs = {key: val for (key, val) in connective.attrib.items() if key != 'konn'}
        word_node = self.node[word_node_id]
        word_node['layers'].add(self.ns+':connective')
        word_node.update({'connective': connective_attribs})

    def add_discrel(self, discrel):
        """
        Add a discourse relation to the document graph.

        Parameters
        ----------
        add_discrel : etree.Element
            etree representation of a <discRel> element which describes the
            relation between two EDUs.
            The ID of the other EDU is given in the arg2 attribute.
            Note, that arg2 can either reference an EDU (e.g. edu_9_3_2
            or an EDU range, e.g. edus9_3_1-5_0).

        Example
        -------

           <edu xml:id="edu_9_3_0">
            <discRel relation="Explanation-Speechact" marking="-" arg2="edus9_3_1-5_0"/>
            <node xml:id="s128_504" cat="SIMPX" func="--">
            ...
            </node>
            <word xml:id="s128_3" form=":" pos="$." lemma=":" func="--" deprel="ROOT"/>
           </edu>

             <edu xml:id="edu_9_3_1">
              <discRel relation="Continuation" marking="-" arg2="edu_9_3_2"/>
              <node xml:id="s128_506" cat="VF" func="-" parent="s128_525">
              ...
              </node>
              ...
             </edu>
        """
        if self.ignore_relations is False:
            arg1_id = self.get_element_id(discrel)
            arg2_id = discrel.attrib['arg2']
            reltype = discrel.attrib['relation']
            discrel_attribs = self.element_attribs_to_dict(discrel)
            self.node[arg1_id].update(discrel_attribs)
            self.add_layer(arg1_id, self.ns+':discourse')
            self.add_layer(arg1_id, self.ns+':relation')
            self.add_edge(arg1_id, arg2_id,
                          layers={self.ns, self.ns+':discourse', self.ns+':relation'},
                          edge_type=dg.EdgeTypes.pointing_relation,
                          relation=reltype,
                          label='discourse:'+reltype)

    def add_edu(self, edu):
        """
        Parameters
        ----------
        edu : etree.Element
            etree representation of a <edu> element
            (annotates an EDU)
            Note: the arg1 EDU has a discRel child, the arg2 doesn't

        Example
        -------
        <edu xml:id="edu_55_21_1">
         <discRel relation="Explanation-Cause" marking="-|*um zu" arg2="edu_55_21_2"/>
         <word xml:id="s905_9" form="und" pos="KON" lemma="und" func="-" parent="s905_526" dephead="s905_3" deprel="KON"/>
         <node xml:id="s905_525" cat="FKONJ" func="KONJ" parent="s905_526" span="s905_10..s905_19">

        ...

       <edu xml:id="edu_55_21_2" span="s905_14..s905_20">
        <node xml:id="s905_524" cat="NF" func="-" parent="s905_525">
        """
        edu_id = self.get_element_id(edu)
        edu_attribs = self.element_attribs_to_dict(edu) # contains 'span' or nothing
        self.add_node(edu_id, layers={self.ns, self.ns+':edu'}, attr_dict=edu_attribs)

        edu_token_ids = []
        for word in edu.iterdescendants('word'):
            word_id = self.get_element_id(word)
            edu_token_ids.append(word_id)
            self.add_edge(edu_id, word_id, layers={self.ns, self.ns+':edu'},
                          edge_type=dg.EdgeTypes.spanning_relation)

        self.node[edu_id]['tokens'] = edu_token_ids

    def add_edurange(self, edurange):
        """
        Parameters
        ----------
        edurange : etree.Element
            etree representation of a <edurange> element
            (annotation that groups a number of EDUs)
            <edu-range> seems to glue together a number of `<edu> elements,
            which may be scattered over a number of sentences
            <edu-range> may or may not contain a span attribute
            (it seems that the span attribute is present, when <edu-range> is
            a descendent of <sentence>)

        Example
        -------

           <edu-range xml:id="edus9_3_1-5_0" span="s128_4..s130_7">
            <node xml:id="s128_525" cat="SIMPX" func="--">
             <edu xml:id="edu_9_3_1">
              <discRel relation="Continuation" marking="-" arg2="edu_9_3_2"/>
              <node xml:id="s128_506" cat="VF" func="-" parent="s128_525">
               <node xml:id="s128_505" cat="NX" func="ON" parent="s128_506">
                <relation type="expletive"/>
                <word xml:id="s128_4" form="Es" pos="PPER" morph="nsn3" lemma="es" func="HD" parent="s128_505" dephead="s128_5" deprel="SUBJ"/>
               </node>
              </node>

            ...

          <edu-range xml:id="edus37_8_0-8_1">
           <discRel relation="Restatement" marking="-" arg2="edu_37_9_0"/>
           <sentence xml:id="s660">
        """
        edurange_id = self.get_element_id(edurange)
        edurange_attribs = self.element_attribs_to_dict(edurange) # contains 'span' or nothing
        self.add_node(edurange_id, layers={self.ns, self.ns+':edu:range'}, attr_dict=edurange_attribs)
        for edu in edurange.iterdescendants('edu'):
            edu_id = self.get_element_id(edu)
            self.add_edge(edurange_id, edu_id, layers={self.ns, self.ns+':edu:range'},
                          edge_type=dg.EdgeTypes.spanning_relation)

    def add_ne(self, ne):
        """
        Parameters
        ----------
        ne : etree.Element
            etree representation of a <ne> element
            (marks a text span -- (one or more <node> or <word> elements) as a named entity)

        Example
        -------
            <ne xml:id="ne_23" type="PER">
             <word xml:id="s3_2" form="Ute" pos="NE" morph="nsf" lemma="Ute" func="-" parent="s3_501" dephead="s3_1" deprel="APP"/>
             <word xml:id="s3_3" form="Wedemeier" pos="NE" morph="nsf" lemma="Wedemeier" func="-" parent="s3_501" dephead="s3_2" deprel="APP"/>
            </ne>
        """
        ne_id = self.get_element_id(ne)
        ne_label = 'ne:'+ne.attrib['type']
        self.add_node(ne_id, layers={self.ns, self.ns+':ne'},
                      attr_dict=self.element_attribs_to_dict(ne),
                      label=ne_label)
        # possible children: [('word', 78703), ('node', 11152), ('ne', 49)]
        for child in ne.iterchildren():
            child_id = self.get_element_id(child)
            self.add_edge(ne_id, child_id, layers={self.ns, self.ns+':ne'},
                          edge_type=dg.EdgeTypes.spanning_relation,
                          label=ne_label)

    def add_node_element(self, node):
        """Add a (syntax category) <node> to the document graph.

        Parameters
        ----------
        node : etree.Element
            etree representation of a <node> element
            A <node> describes an element of a syntax tree.
            The root <node> element does not have a parent attribute,
            while non-root nodes do

        Example
        -------
        <node xml:id="s1_505" cat="SIMPX" func="--">
            <node xml:id="s1_501" cat="LK" func="-" parent="s1_505">

            # this is the root of the syntax tree of the sentence, but
            # it is not the root node of the sentence, since there might
            # be nodes outside of the tree which are children of the
            # sentence root node (e.g. <word> elements representing a
            # quotation mark)

        """
        node_id = self.get_element_id(node)
        if 'parent' in node.attrib:
            parent_id = self.get_parent_id(node)
        else:
            # <node> is the root of the syntax tree of a sentence,
            # but it might be embedded in a <edu> or <edu-range>.
            # we want to attach it directly to the <sentence> element
            parent_id = self.get_sentence_id(node)
        self.add_node(node_id, layers={self.ns, self.ns+':syntax'},
                      attr_dict=self.element_attribs_to_dict(node),
                      label=node.attrib['cat'])
        self.add_edge(parent_id, node_id, edge_type=dg.EdgeTypes.dominance_relation)

    def add_relation(self, relation):
        """
        Parameters
        ----------
        relation : etree.Element
            etree representation of a <relation> element
            A <relation> always has a type attribute and inherits
            its ID from its parent element. In the case of a non-expletive
            relation, it also has a target attribute.

        Example
        -------

          <node xml:id="s29_501" cat="NX" func="ON" parent="s29_523">
           <relation type="expletive"/>
           <word xml:id="s29_2" form="es" pos="PPER" morph="nsn3" lemma="es"
                 func="HD" parent="s29_501" dephead="s29_14" deprel="SUBJ"/>
          </node>

          ...

         <node xml:id="s4_507" cat="NX" func="ON" parent="s4_513">
          <relation type="coreferential" target="s1_502"/>
          <node xml:id="s4_505" cat="NX" func="HD" parent="s4_507">
          ...
          </node>
         </node>
        """
        if self.ignore_relations is False:
            parent_node_id = self.get_parent_id(relation)
            reltype = relation.attrib['type']
            # add relation type information to parent node
            self.node[parent_node_id].update({'relation': reltype})
            self.add_layer(parent_node_id, self.ns+':'+reltype)
            if 'target' in relation.attrib:
                # if the relation has no target, it is either 'expletive' or
                # 'inherent_reflexive', both of which should not be part of the
                # 'markable' layer
                self.add_layer(parent_node_id, self.ns+':markable')
                target_id = relation.attrib['target']
                self.add_edge(parent_node_id, target_id,
                              layers={self.ns, self.ns+':'+reltype,
                                      self.ns+':coreference'},
                              label=reltype,
                              edge_type=dg.EdgeTypes.pointing_relation)
                self.add_layer(target_id, self.ns+':markable')

    def add_secedge(self, secedge):
        """
        Parameters
        ----------
        secedge : etree.Element
            etree representation of a <secedge> element
        A <secEdge> element has a cat and a parent attribute,
        but inherits its ID from its parent element.
        It describes a secondary edge in a tree-like syntax representation.

        Example
        -------
           <node xml:id="s10_505" cat="VXINF" func="OV" parent="s10_507">
            <secEdge cat="refvc" parent="s10_504"/>
            <word xml:id="s10_6" form="worden" pos="VAPP" lemma="werden%passiv" func="HD" parent="s10_505" dephead="s10_7" deprel="AUX"/>
           </node>
        """
        if self.ignore_secedges is False:
            edge_source = self.get_parent_id(secedge)
            edge_target = self.get_element_id(secedge)
            self.add_edge(edge_source, edge_target,
                          layers={self.ns, self.ns+':secedge'},
                          label='secedge:'+secedge.attrib['cat'],
                          edge_type=dg.EdgeTypes.pointing_relation)

    def add_sentence(self, sentence):
        """
        Parameters
        ----------
        sentence : etree.Element
            etree representation of a sentence
            (syntax tree with coreference annotation)
        """
        sent_root_id = sentence.attrib[add_ns('id')]
        # add edge from document root to sentence root
        self.add_edge(self.root, sent_root_id, edge_type=dg.EdgeTypes.dominance_relation)
        self.sentences.append(sent_root_id)

        sentence_token_ids = []

        if 'span' in sentence.attrib:
            # the sentence element looks like this:
            # <sentence xml:id="s144" span="s144_1..s144_23">, which means that
            # there might be <word> elements which belong to this sentence but
            # occur after the closing </sentence> element
            span_str = sentence.attrib['span']
            sentence_token_ids.extend(convert_spanstring(span_str))
        else:  # a normal sentence element, i.e. <sentence xml:id="s143">
            for descendant in sentence.iterdescendants('word'):
                sentence_token_ids.append(self.get_element_id(descendant))

        self.node[sent_root_id]['tokens'] = sentence_token_ids

    def add_splitrelation(self, splitrelation):
        """
        Parameters
        ----------
        splitrelation : etree.Element
            etree representation of a <splitRelation> element
            A <splitRelation> annotates its parent element (e.g. as an anaphora).
            Its parent can be either a <word> or a <node>.
            A <splitRelation> has a target attribute, which describes
            the targets (plural! e.g. antecedents) of the relation.

        Example
        -------
            <node xml:id="s2527_528" cat="NX" func="-" parent="s2527_529">
             <splitRelation type="split_antecedent" target="s2527_504 s2527_521"/>
             <word xml:id="s2527_32" form="beider" pos="PIDAT" morph="gpf" lemma="beide" func="-" parent="s2527_528" dephead="s2527_33" deprel="DET"/>
             <word xml:id="s2527_33" form="Firmen" pos="NN" morph="gpf" lemma="Firma" func="HD" parent="s2527_528" dephead="s2527_31" deprel="GMOD"/>
            </node>

            <word xml:id="s3456_12" form="ihr" pos="PPOSAT" morph="nsm" lemma="ihr" func="-" parent="s3456_507" dephead="s3456_14" deprel="DET">
             <splitRelation type="split_antecedent" target="s3456_505 s3456_9"/>
            </word>
        """
        if self.ignore_relations is False and self.ignore_splitrelations is False:
            source_id = self.get_element_id(splitrelation)
            # the target attribute looks like this: target="s2527_504 s2527_521"
            target_node_ids = splitrelation.attrib['target'].split()
            # we'll create an additional node which spans all target nodes
            target_span_id = '__'.join(target_node_ids)
            reltype = splitrelation.attrib['type']
            self.add_node(source_id,
                          layers={self.ns, self.ns+':relation', self.ns+':'+reltype, self.ns+':markable'})
            self.add_node(target_span_id,
                          layers={self.ns, self.ns+':targetspan', self.ns+':'+reltype, self.ns+':markable'})
            self.add_edge(source_id, target_span_id,
                          layers={self.ns, self.ns+':coreference', self.ns+':splitrelation', self.ns+':'+reltype},
                          edge_type=dg.EdgeTypes.pointing_relation)

            for target_node_id in target_node_ids:
                self.add_edge(target_span_id, target_node_id,
                              layers={self.ns, self.ns+':'+reltype},
                              edge_type=dg.EdgeTypes.spanning_relation)

    def add_topic(self, topic):
        """
        Parameters
        ----------
        topic : etree.Element
            etree representation of a <topic> element
            (topic annotation of a text span, e.g. a sentence, edu or edu-range)

        Example
        -------
            <topic xml:id="topic_9_0" description="Kuli">
                <sentence xml:id="s128">

            ...

            <topic xml:id="topic_37_1" description="Die Pläne der AG">
                <edu-range xml:id="edus37_8_0-8_1">
                    <discRel relation="Restatement" marking="-" arg2="edu_37_9_0"/>
                        <sentence xml:id="s660">
        """
        topic_id = self.get_element_id(topic)
        self.add_node(topic_id, layers={self.ns, self.ns+':topic'},
                      description=topic.attrib['description'])
        topic_tokens = []
        for word in topic.iterdescendants('word'):
            word_id = self.get_element_id(word)
            topic_tokens.append(word_id)
            self.add_edge(topic_id, word_id, layers={self.ns, self.ns+':topic'},
                          edge_type=dg.EdgeTypes.spanning_relation)
        self.node[topic_id]['tokens'] = topic_tokens

    def add_word(self, word):
        """
        Parameters
        ----------
        word : etree.Element
            etree representation of a <word> element
            (i.e. a token, which might contain child elements)
        """
        word_id = self.get_element_id(word)
        if word.getparent().tag in ('node', 'sentence'):
            parent_id = self.get_parent_id(word)
        else:
            # ExportXML is an inline XML format. Therefore, a <word>
            # might be embedded in weird elements. If this is the case,
            # attach it directly to the closest <node> or <sentence> node
            try:
                parent = word.iterancestors(tag=('node', 'sentence')).next()
                parent_id = self.get_element_id(parent)
            except StopIteration as e:
                # there's at least one weird edge case, where a <word> is
                # embedded like this: (text (topic (edu (word))))
                # here, we guess the sentence ID from the
                parent_id = self.get_element_id(word).split('_')[0]

        self.tokens.append(word_id)
        # use all attributes except for the ID
        word_attribs = self.element_attribs_to_dict(word)
        # add the token string under the key namespace:token
        token_str = word_attribs[self.ns+':form']
        word_attribs.update({self.ns+':token': token_str, 'label': token_str})
        self.add_node(word_id, layers={self.ns, self.ns+':token'},
                      attr_dict=word_attribs)
        self.add_edge(parent_id, word_id, edge_type=dg.EdgeTypes.dominance_relation)
        self.parse_child_elements(word)

    def element_attribs_to_dict(self, element):
        """
        Convert the ``.attrib`` attributes of an etree element into a dict,
        leaving out the xml:id attribute. Each key will be prepended by graph's
        namespace.
        """
        return {self.ns+':'+key: val for (key, val) in element.attrib.items()
                if key != add_ns('id')}

    @staticmethod
    def get_element_id(element):
        """
        Returns the ID of an element (or, if the element doesn't have one:
        the ID of its parent). Returns an error, if both elements have no ID.
        """
        id_attrib_key = add_ns('id')
        if id_attrib_key in element.attrib:
            return element.attrib[id_attrib_key]
        try:
            return element.getparent().attrib[id_attrib_key]
        except KeyError as e:
            raise KeyError(
                'Neither the element "{0}" nor its parent "{1}" '
                'have an ID'.format(element, element.getparent()))

    @staticmethod
    def get_parent_id(element):
        """returns the ID of the parent of the given element"""
        if 'parent' in element.attrib:
            return element.attrib['parent']
        else:
            return element.getparent().attrib[add_ns('id')]

    def get_sentence_id(self, element):
        """returns the ID of the sentence the given element belongs to."""
        try:
            sentence_elem = element.iterancestors('sentence').next()
        except StopIteration as e:
            warnings.warn("<{}> element is not a descendant of a <sentence> "
                          "We'll try to extract the sentence ID from the "
                          "prefix of the element ID".format(element.tag))
            return self.get_element_id(element).split('_')[0]
        return self.get_element_id(sentence_elem)


def add_ns(key, ns='http://www.w3.org/XML/1998/namespace'):
    """
    adds a namespace prefix to a string, e.g. turns 'foo' into
    '{http://www.w3.org/XML/1998/namespace}foo'
    """
    return '{{{namespace}}}{key}'.format(namespace=ns, key=key)


read_exportxml = ExportXMLCorpus
