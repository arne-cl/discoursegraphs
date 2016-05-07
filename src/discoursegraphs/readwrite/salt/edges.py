#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the parsing of SALT edges.
"""

from lxml.builder import ElementMaker

from discoursegraphs.readwrite.salt.util import NAMESPACES
from discoursegraphs.readwrite.salt.elements import (SaltElement,
                                                     get_annotations,
                                                     get_layer_ids)


class SaltEdge(SaltElement):
    """
    An edge connects a source node with a target node, belongs to a layer
    and has two or more labels attached to it.
    """
    def __init__(self, name, element_id, xsi_type, labels, source, target,
                 layers=None):
        """
        Every edge has these attributes (in addition to the attributes
        inherited from the ``SaltElement`` class):

        Attributes
        ----------
        layers : list of int or None
            list of indices of the layers that the edge belongs to,
            or ``None`` if the edge doesn't belong to any layer
        source : int
            the index of the source node connected to the edge
        target : int
            the index of the target node connected to the edge
        """
        super(SaltEdge, self).__init__(name, element_id, xsi_type, labels, xml)
        self.layers = [] if layers is None else layers
        self.source = source
        self.target = target

    @classmethod
    def from_etree(cls, etree_element):
        """
        creates a ``SaltEdge`` instance from the etree representation of an
        <edges> element from a SaltXMI file.
        """
        ins = SaltElement.from_etree(etree_element)
        # TODO: this looks dangerous, ask Stackoverflow about it!
        ins.__class__ = SaltEdge.mro()[0]  # convert SaltElement into SaltEdge
        ins.layers = get_layer_ids(etree_element)
        ins.source = get_node_id(etree_element, 'source')
        ins.target = get_node_id(etree_element, 'target')
        return ins

    def to_etree(self):
        """
        creates an etree element of a ``SaltEdge`` that mimicks a SaltXMI
        <edges> element
        """
        layers_attrib_val = ' '.join('//@layers.{}'.format(layer_id)
                                     for layer_id in self.layers)

        attribs = {
            '{{{pre}}}type'.format(pre=NAMESPACES['xsi']): self.xsi_type,
            'source': "//@nodes.{}".format(self.source),
            'target': "//@nodes.{}".format(self.target),
            'layers': layers_attrib_val}
        # an edge might belong to one or more layers
        non_empty_attribs = {key: val for (key, val) in attribs.items()
                             if val is not None}

        E = ElementMaker()
        edge = E('edges', non_empty_attribs)
        label_elements = (label.to_etree() for label in self.labels)
        edge.extend(label_elements)
        return edge

    def __str__(self):
        ret_str = super(SaltEdge, self).__str__() + "\n"
        ret_str += "source node: {0}\n".format(self.source)
        ret_str += "target node: {0}".format(self.target)
        return ret_str


class SpanningRelation(SaltEdge):
    """
    Every SpanningRelation edge inherits all the attributes from `SaltEdge`
    (and `SaltElement`). A ``SpanningRelation`` is an ``Edgde`` that links a
    ``SpanNode`` to a ``TokenNode``.

    A SpanningRelation edge looks like this::

        <edges xsi:type="sDocumentStructure:SSpanningRelation"
            source="//@nodes.167" target="//@nodes.59" layers="//@layers.1">
            <labels xsi:type="saltCore:SFeature" namespace="salt" name="SNAME"
                valueString="sSpanRel27"/>
            <labels xsi:type="saltCore:SElementId" namespace="graph" name="id"
                valueString="edge181"/>
        </edges>
    """
    def __init__(self, name, element_id, xsi_type, labels, source, target,
                 layers=None, xml=None):
        """A ``SpanningRelation`` is created just like an ``SaltEdge``."""
        super(SpanningRelation, self).__init__(name, element_id, xsi_type,
                                               labels, source, target,
                                               layers=layers, xml=xml)


class TextualRelation(SaltEdge):
    """
    An TextualRelation edge always links a token (source node) to the
    PrimaryTextNode (target node 0). Textual relations don't belong to a layer.
    A TextualRelation contains the onset/offset of a token. This enables us to
    retrieve the text/string of a token from the documents primary text.

    Every TextualRelation has these attributes (in addition to those inherited
    from `SaltEdge` and `SaltElement`):

    Attributes
    ----------
    onset : int
        the string onset of the source node (``TokenNode``)
    offset : int
        the string offset of the source node (``TokenNode``)
    """
    def __init__(self, name, element_id, xsi_type, labels, source, target,
                 onset, offset, layers=None, xml=None):
        super(TextualRelation, self).__init__(name, element_id, xsi_type,
                                              labels, source, target,
                                              layers, xml)
        self.onset = onset
        self.offset = offset

    @classmethod
    def from_etree(cls, etree_element):
        """
        create a ``TextualRelation`` instance from an etree element
        representing an <edges> element with xsi:type
        'sDocumentStructure:STextualRelation'.
        """
        ins = SaltEdge.from_etree(etree_element)
        # TODO: this looks dangerous, ask Stackoverflow about it!
        # convert SaltEdge into TextualRelation
        ins.__class__ = TextualRelation.mro()[0]
        ins.onset = get_string_onset(etree_element)
        ins.offset = get_string_offset(etree_element)
        return ins


class DominanceRelation(SaltEdge):
    """
    A ``DominanceRelation`` edge always links a ``StructureNode`` (source) to a
    ``TokenNode`` (target). It looks like this::

        <edges xsi:type="sDocumentStructure:SDominanceRelation"
            source="//@nodes.251" target="//@nodes.134" layers="//@layers.2">
            <labels xsi:type="saltCore:SFeature" namespace="saltCore"
                name="STYPE" valueString="edge"/>
            <labels xsi:type="saltCore:SFeature" namespace="salt" name="SNAME"
                valueString="sDomRel185"/>
            <labels xsi:type="saltCore:SElementId" namespace="graph" name="id"
                valueString="edge530"/>
            <labels xsi:type="saltCore:SAnnotation" name="tiger.func"
                valueString="OC"/>
        </edges>

    Attributes
    ----------
    features : dict of (str, str)
        key-value pairs which e.g. describe the syntactical constituent a token
        belongs to, such as {'tiger.func': 'PP'}.
    """
    def __init__(self, name, element_id, xsi_type, labels, source, target,
                 features=None, layers=None, xml=None):
        super(DominanceRelation, self).__init__(name, element_id, xsi_type,
                                                labels, source, target,
                                                layers, xml)
        self.features = {} if features is None else features

    @classmethod
    def from_etree(cls, etree_element):
        """
        create a ``DominanceRelation`` instance from an etree element
        representing an <edges> element with xsi:type
        'sDocumentStructure:SDominanceRelation'.
        """
        ins = SaltEdge.from_etree(etree_element)
        # TODO: this looks dangerous, ask Stackoverflow about it!
        # convert SaltEdge into DominanceRelation
        ins.__class__ = DominanceRelation.mro()[0]
        ins.features = get_annotations(etree_element)
        return ins


def get_node_id(edge, node_type):
    """
    returns the source or target node id of an edge, depending on the
    node_type given.
    """
    assert node_type in ('source', 'target')
    _, node_id_str = edge.attrib[node_type].split('.')  # e.g. //@nodes.251
    return int(node_id_str)


def get_string_onset(edge):
    """return the onset (int) of a string"""
    onset_label = edge.find('labels[@name="SSTART"]')
    onset_str = onset_label.xpath('@valueString')[0]
    return int(onset_str)


def get_string_offset(edge):
    """return the offset (int) of a string"""
    onset_label = edge.find('labels[@name="SEND"]')
    onset_str = onset_label.xpath('@valueString')[0]
    return int(onset_str)
