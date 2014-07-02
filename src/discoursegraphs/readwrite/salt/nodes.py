#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the parsing of SALT nodes.

TODO: add docstring to SaltNode subclasses
"""

import elements
import layers


class SaltNode(elements.SaltElement):
    """
    A SaltNode inherits all the attributes from `SaltElement`, i.e. 'name', 'type' and
    'xml'. Additional attributes:

    Attributes
    ----------
    features : dict
        a dictionary of all the SAnnotation attributes of a layer,
        e.g. lemma, morph or pos
    layer : int
        an integer representing the index of the layer the node belongs to
        or None
    node_id : int
        the index of the node
    """
    def __init__(self, element, element_id, doc_id):
        super(SaltNode, self).__init__(element, doc_id)
        self.layer = elements.get_layer_id(element)
        self.node_id = element_id
        if elements.has_annotations(element):
            self.features = elements.get_annotations(element)
        else:
            self.features = {}

    def __str__(self):
        """
        returns the string representation of a `SaltNode`, which contains the facts
        from `SaltElement` plus the node's layer and its features.
        """
        ret_str = super(SaltNode, self).__str__() + "\n"

        if self.layer is not None: # mere check for existence would ignore '0'
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
    def __init__(self, element, element_id, doc_id):
        super(PrimaryTextNode, self).__init__(element, element_id, doc_id)
        self.text = extract_primary_text(element)

    def __str__(self):
        node_string = super(PrimaryTextNode, self).__str__()
        return "{0}\nprimary text:\n{1}".format(node_string, self.text.encode('utf-8'))


class TokenNode(SaltNode):
    """
    A TokenNode describes a token, including its annotation features,
    e.g. tiger.pos = ART. It inherits all attributes from `SaltNode`, i.e. 'layer'
    and 'features' as well as those from `SaltElement`.

    A sentence boundary is marked by TokenNode.features['tiger.pos'] == '$.'
    """
    def __init__(self, element, element_id, doc_id):
        super(TokenNode, self).__init__(element, element_id, doc_id)
        pass

class SpanNode(SaltNode):
    """
    A SpanNode contains all the I{SAnnotation}s features made to a span
    (e.g. coreference), but it DOES NOT tell you which tokens belong to that
    span. A SpanningRelation edge connects a SpanNode to one TokenNode.

    A SpanNode looks like this::

        <nodes xsi:type="sDocumentStructure:SSpan" layers="//@layers.1">
            <labels xsi:type="saltCore:SFeature" namespace="salt" name="SNAME" valueString="sSpan1"/>
            <labels xsi:type="saltCore:SElementId" namespace="graph" name="id" valueString="pcc_maz176_merged_paula/maz-0002/maz-0002_graph#sSpan1"/>
            <labels xsi:type="saltCore:SAnnotation" name="coref.referentiality" valueString="referring"/>
            <labels xsi:type="saltCore:SAnnotation" name="coref.anaphor_antecedent" valueString="#primmarkSeg_25"/>
            <labels xsi:type="saltCore:SAnnotation" name="coref.type" valueString="anaphoric"/>
            <labels xsi:type="saltCore:SAnnotation" name="coref.phrase_type" valueString="np"/>
            <labels xsi:type="saltCore:SAnnotation" name="coref.grammatical_role" valueString="sbj"/>
        </nodes>

    """
    def __init__(self, element, element_id, doc_id):
        super(SpanNode, self).__init__(element, element_id, doc_id)
        pass

class StructureNode(SaltNode):
    """
    A StructureNode contains all the I{SAnnotation}s features made to a span
    (i.e. syntactic constituents), but it DOES NOT tell you which tokens belong to that
    constituent.

    A StructureNode looks like this::

        <nodes xsi:type="sDocumentStructure:SStructure" layers="//@layers.2">
            <labels xsi:type="saltCore:SFeature" namespace="salt" name="SNAME" valueString="const_4"/>
            <labels xsi:type="saltCore:SElementId" namespace="graph" name="id" valueString="pcc_maz176_merged_paula/maz-0002/maz-0002_graph#const_4"/>
            <labels xsi:type="saltCore:SAnnotation" name="tiger.cat" valueString="PP"/>
        </nodes>

    """
    def __init__(self, element, element_id, doc_id):
        super(StructureNode, self).__init__(element, element_id, doc_id)
        pass


def extract_sentences(nodes, token_node_indices):
    """
    given a list of ``SaltNode``s, returns a list of lists, where each list
    contains the indices of the nodes belonging to that sentence.
    """
    sents = []
    tokens = []
    for i, node in enumerate(nodes):
        if i in token_node_indices:
            if node.features['tiger.pos'] != '$.':
                tokens.append(i)
            else: # start a new sentence, if 'tiger.pos' is '$.'
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
    return tree.findall("//nodes[@layers='//@layers.{0}']".format(layer_number))
