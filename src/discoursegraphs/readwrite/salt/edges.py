#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the parsing of SALT edges.
"""

from elements import (Element, get_graph_element_id, get_annotations,
    get_layer_id)


class Edge(Element):
    """
    An edge connects a source node with a target node and belongs to a layer.
    """
    def __init__(self, element, element_id, doc_id):
        """
        Every edge has these attributes (in addition to the attributes inherited
        from the ``Element`` class, i.e. ``xml``, ``name`` and ``type``):

        Attributes
        ----------
        edge_id : int
            the index of the edge
        graph_id : str
            the ``saltCore:SElementId`` value string, e.g. `edge123`
        layer : int or None
            the index of the layer that the edge belongs to, or ``None`` if the
            edge doesn't belong to a layer
        source : int
            the index of the source node connected to the edge
        target : int
            the index of the target node connected to the edge
        """
        super(Edge, self).__init__(element, doc_id)
        self.edge_id = element_id
        self.layer = get_layer_id(element)
        self.source = get_node_id(element, 'source')
        self.target = get_node_id(element, 'target')
        self.graph_id = get_graph_element_id(element)

    def __str__(self):
        ret_str = super(Edge, self).__str__() + "\n"
        ret_str += "source node: {0}\n".format(self.source)
        ret_str += "target node: {0}".format(self.target)
        return ret_str

class SpanningRelation(Edge):
    """
    Every SpanningRelation edge inherits all the attributes from `Edge`
    (and `Element`). A ``SpanningRelation`` is an ``Edgde`` that links a
    ``SpanNode`` to a ``TokenNode``.

    A SpanningRelation edge looks like this::

        <edges xsi:type="sDocumentStructure:SSpanningRelation" source="//@nodes.167" target="//@nodes.59" layers="//@layers.1">
            <labels xsi:type="saltCore:SFeature" namespace="salt" name="SNAME" valueString="sSpanRel27"/>
            <labels xsi:type="saltCore:SElementId" namespace="graph" name="id" valueString="edge181"/>
        </edges>

    """
    def __init__(self, element, element_id, doc_id):
        """A ``SpanningRelation`` is created just like an ``Edge``."""
        super(SpanningRelation, self).__init__(element, element_id, doc_id)
        pass

class TextualRelation(Edge):
    """
    An TextualRelation edge always links a token (source node) to the
    PrimaryTextNode (target node 0). Textual relations don't belong to a layer.
    A TextualRelation contains the onset/offset of a token. This enables us to
    retrieve the text/string of a token from the documents primary text.

    Every TextualRelation has these attributes (in addition to those inherited
    from `Edge` and `Element`):

    :ivar onset: `int` representing the string onset of the source node
    (`TokenNode`)
    :ivar offset: `int` representing the string offset of the source node
    (`TokenNode`)
    """
    def __init__(self, element, element_id, doc_id):
        super(TextualRelation, self).__init__(element, element_id, doc_id)
        self.onset = get_string_onset(element)
        self.offset = get_string_offset(element)


class DominanceRelation(Edge):
    """
    A `DominanceRelation` edge always links a `StructureNode` (source) to a
    `TokenNode` (target). Every `DominanceRelation` has a `feature` attribute:

    :ivar feature: `dict` of (`str`, `str`) key-value pairs which e.g. describe
    the syntactical constituent a token belongs to, such as {'tiger.func': 'PP'}.

    A DominanceRelation edge looks like this::

        <edges xsi:type="sDocumentStructure:SDominanceRelation" source="//@nodes.251" target="//@nodes.134" layers="//@layers.2">
            <labels xsi:type="saltCore:SFeature" namespace="saltCore" name="STYPE" valueString="edge"/>
            <labels xsi:type="saltCore:SFeature" namespace="salt" name="SNAME" valueString="sDomRel185"/>
            <labels xsi:type="saltCore:SElementId" namespace="graph" name="id" valueString="edge530"/>
            <labels xsi:type="saltCore:SAnnotation" name="tiger.func" valueString="OC"/>
        </edges>

    """
    def __init__(self, element, element_id, doc_id):
        super(DominanceRelation, self).__init__(element, element_id, doc_id)
        self.features = get_annotations(element)


def get_node_id(edge, node_type):
    """
    returns the source or target node id of an edge, depending on the
    node_type given.
    """
    assert node_type in ('source', 'target')
    _, node_id_str = edge.attrib[node_type].split('.') # e.g. //@nodes.251
    return int(node_id_str)

def get_string_onset(edge):
    onset_label = edge.find('labels[@name="SSTART"]')
    onset_str = onset_label.xpath('@valueString')[0]
    return int(onset_str)

def get_string_offset(edge):
    onset_label = edge.find('labels[@name="SEND"]')
    onset_str = onset_label.xpath('@valueString')[0]
    return int(onset_str)
