#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the parsing of SALT nodes.

TODO: add docstring to SaltNode subclasses
"""

from lxml.builder import ElementMaker

from discoursegraphs.readwrite.salt.util import NAMESPACES
from discoursegraphs.readwrite.salt.elements import (SaltElement,
                                                     get_layer_ids,
                                                     get_annotations)


class SaltNode(SaltElement):
    """
    A SaltNode inherits all the attributes from `SaltElement`, i.e. 'name',
    'xsi_type' and 'xml'. Additional attributes:

    Attributes
    ----------
    features : dict
        a dictionary of all the SAnnotation attributes of a layer,
        e.g. lemma, morph or pos
    layers : list of int or None
        list of indices of the layers that the node belongs to,
        or ``None`` if the node doesn't belong to any layer
    """
    def __init__(self, name, element_id, xsi_type, labels, layers=None,
                 features=None, xml=None):
        super(SaltNode, self).__init__(name, element_id, xsi_type, labels, xml)
        self.features = {} if features is None else features
        self.layers = layers

    @classmethod
    def from_etree(cls, etree_element):
        """
        creates a ``SaltNode`` instance from the etree representation of an
        <nodes> element from a SaltXMI file.
        """
        ins = SaltElement.from_etree(etree_element)
        # TODO: this looks dangerous, ask Stackoverflow about it!
        ins.__class__ = SaltNode.mro()[0]  # convert SaltElement into SaltNode
        ins.layers = get_layer_ids(etree_element)
        ins.features = get_annotations(etree_element)
        return ins

    def to_etree(self):
        """
        creates an etree element of a ``SaltNode`` that mimicks a SaltXMI
        <nodes> element
        """
        layers_attrib_val = ' '.join('//@layers.{}'.format(layer_id)
                                     for layer_id in self.layers)

        attribs = {
            '{{{pre}}}type'.format(pre=NAMESPACES['xsi']): self.xsi_type,
            'layers': layers_attrib_val}

        E = ElementMaker()
        node = E('nodes', attribs)
        label_elements = (label.to_etree() for label in self.labels)
        node.extend(label_elements)
        return node

    def __str__(self):
        """
        returns the string representation of a ``SaltNode``, which contains the
        facts from ``SaltElement`` plus the node's layer and its features.
        """
        ret_str = super(SaltNode, self).__str__() + "\n"

        if self.layer is not None:  # mere check for existence would ignore '0'
            ret_str += "layer: {0}\n".format(self.layer)

        if self.features:
            ret_str += "\nfeatures:\n"
            for key, value in self.features.items():
                ret_str += "\t{0}: {1}\n".format(key, value)

        if hasattr(self, 'dominates'):
            ret_str += "\ndominates: {0}\n".format(self.dominates)
        if hasattr(self, 'dominated_by'):
            ret_str += "dominated by: {0}\n".format(self.dominated_by)
        return ret_str


class PrimaryTextNode(SaltNode):
    """
    A PrimaryTextNode inherits all the attributes from `SaltNode` and adds

    Attributes
    ----------
    text : str
        the string representing the text of a document
    """
    def __init__(self, name, element_id, xsi_type, labels, text, layers=None,
                 features=None, xml=None):
        super(PrimaryTextNode, self).__init__(name, element_id, xsi_type,
                                              labels, layers, features, xml)
        self.text = text

    @classmethod
    def from_etree(cls, etree_element):
        """
        creates a ``PrimaryTextNode`` instance from the etree representation of
        a <nodes> element from a SaltXMI file.
        """
        ins = SaltNode.from_etree(etree_element)
        # TODO: this looks dangerous, ask Stackoverflow about it!
        # convert SaltNode into PrimaryTextNode
        ins.__class__ = PrimaryTextNode.mro()[0]
        ins.text = extract_primary_text(etree_element)
        return ins

    def __str__(self):
        node_string = super(PrimaryTextNode, self).__str__()
        return ("{0}\nprimary text:\n"
                "{1}".format(node_string, self.text.encode('utf-8')))


class TokenNode(SaltNode):
    """
    A TokenNode describes a token, including its annotation features,
    e.g. tiger.pos = ART. It inherits all attributes from ``SaltNode``,
    i.e. 'layer' and 'features' as well as those from `SaltElement`.

    A sentence boundary is marked by TokenNode.features['tiger.pos'] == '$.'
    """
    def __init__(self, element, element_id, doc_id):
        super(TokenNode, self).__init__(element, element_id, doc_id)


class SpanNode(SaltNode):
    """
    A SpanNode contains all the I{SAnnotation}s features made to a span
    (e.g. coreference), but it DOES NOT tell you which tokens belong to that
    span. A SpanningRelation edge connects a SpanNode to one TokenNode.

    A SpanNode looks like this::

        <nodes xsi:type="sDocumentStructure:SSpan" layers="//@layers.1">
            <labels xsi:type="saltCore:SFeature" namespace="salt" name="SNAME"
                valueString="sSpan1"/>
            <labels xsi:type="saltCore:SElementId" namespace="graph" name="id"
                valueString="pcc_maz176/maz-0002/maz-0002_graph#sSpan1"/>
            <labels xsi:type="saltCore:SAnnotation" name="coref.referentiality"
                valueString="referring"/>
            <labels xsi:type="saltCore:SAnnotation"
                name="coref.anaphor_antecedent" valueString="#primmarkSeg_25"/>
            <labels xsi:type="saltCore:SAnnotation" name="coref.type"
                valueString="anaphoric"/>
            <labels xsi:type="saltCore:SAnnotation" name="coref.phrase_type"
                valueString="np"/>
            <labels xsi:type="saltCore:SAnnotation"
                name="coref.grammatical_role" valueString="sbj"/>
        </nodes>
    """
    def __init__(self, element, element_id, doc_id):
        super(SpanNode, self).__init__(element, element_id, doc_id)


class StructureNode(SaltNode):
    """
    A StructureNode contains all the I{SAnnotation}s features made to a span
    (i.e. syntactic constituents), but it DOES NOT tell you which tokens belong
    to that constituent.

    A StructureNode looks like this::

        <nodes xsi:type="sDocumentStructure:SStructure" layers="//@layers.2">
            <labels xsi:type="saltCore:SFeature" namespace="salt" name="SNAME"
                valueString="const_4"/>
            <labels xsi:type="saltCore:SElementId" namespace="graph" name="id"
                valueString="pcc_maz176/maz-0002/maz-0002_graph#const_4"/>
            <labels xsi:type="saltCore:SAnnotation" name="tiger.cat"
                valueString="PP"/>
        </nodes>
    """
    def __init__(self, element, element_id, doc_id):
        super(StructureNode, self).__init__(element, element_id, doc_id)


def extract_sentences(nodes, token_node_indices):
    """
    given a list of ``SaltNode``\s, returns a list of lists, where each list
    contains the indices of the nodes belonging to that sentence.
    """
    sents = []
    tokens = []
    for i, node in enumerate(nodes):
        if i in token_node_indices:
            if node.features['tiger.pos'] != '$.':
                tokens.append(i)
            else:  # start a new sentence, if 'tiger.pos' is '$.'
                tokens.append(i)
                sents.append(tokens)
                tokens = []
    return sents


def extract_primary_text(sTextualDS_node):
    """
    extracts the primary text from an STextualDS node.

    NOTE: In most corpora only one primary text will be linked to a document,
    but this might not always be the case (e.g. in corpora of parallel texts).
    """
    text_element = sTextualDS_node.find('labels[@name="SDATA"]')
    return text_element.xpath('@valueString')[0]


def get_nodes_by_layer(tree, layer_number):
    """return all nodes beloning to the given layer"""
    return tree.findall(
        "//nodes[@layers='//@layers.{0}']".format(layer_number))
