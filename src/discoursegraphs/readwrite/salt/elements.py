#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles LXML etree elements from SALT documents.

:var NAMESPACES: the namespaces used in SaltXML files
"""

from lxml import etree  # used by doctests only
from collections import defaultdict

from discoursegraphs.readwrite.salt.labels import SaltLabel
from discoursegraphs.readwrite.salt.util import get_xsi_type, NAMESPACES


class SaltElement(object):
    """
    A ``SaltElement`` is the most basic data structure used in
    ``SaltDocument``s and ``LinguisticDocument``s.
    ``SaltNode``, ``SaltEdge`` and ``SaltLayer`` are derived from it.

    Attributes
    ----------
    name : str
        the name (the ``valueString`` of the ``SNAME`` label of a) of a SaltXML
        element
    xsi_type : str
        the ``xsi:type`` of a SaltXML element
    labels : list of SaltLabel
        the list of labels attached to this SaltElement
    xml : lxml.etree._Element or None
        contains the etree element representation of an SaltXMI file element
        that this SaltElement was created from. Contains None, If the
        SaltElement was created from scratch.
    """
    def __init__(self, name, element_id, xsi_type, labels, xml=None):
        """
        creates a `SaltElement` instance

        >>> node_str = '''
        ... <nodes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        ... xsi:type="sDocumentStructure:SToken">
        ...     <labels name="SNAME" valueString="tok_1"/>
        ... </nodes>'''
        >>> node = etree.fromstring(node_str)
        >>> e = SaltElement(node, 'document_23')
        >>> e.name, e.xsi_type
        ('tok_1', 'SToken')

        Parameters
        ----------
        name : str
            the name (the ``valueString`` of the ``SNAME`` label of a) of a
            SaltXML element
        element_id : str
            the ID of the edge (i.e. the valueString attribute of the label
            with xsi:type ``saltCore:SElementId`` and name ``id``,
            e.g. `edge123)
        xsi_type : str
            the ``xsi:type`` of a SaltXML element
        labels : list of SaltLabel
            the list of labels attached to this SaltElement
        xml : lxml.etree._Element or None
            an etree element parsed from a SaltXML document
        """
        self.name = name
        self.element_id = element_id
        self.xsi_type = xsi_type
        self.labels = labels
        self.xml = xml

    @classmethod
    def from_etree(cls, etree_element):
        """
        creates a `SaltElement` from an `etree._Element` representing
        an element in a SaltXMI file.
        """
        label_elements = get_subelements(etree_element, 'labels')
        labels = [SaltLabel.from_etree(elem) for elem in label_elements]
        return cls(name=get_element_name(etree_element),
                   element_id=get_graph_element_id(etree_element),
                   xsi_type=get_xsi_type(etree_element),
                   labels=labels,
                   xml=etree_element)

    def __str__(self):
        """
        returns the name, Salt type and XML representation of a `SaltElement`.
        """
        ret_str = "name: {0}\n".format(self.name)
        ret_str += "Salt type: {0}\n\n".format(self.xsi_type)
        ret_str += "XML representation:\n{0}".format(etree.tostring(self.xml))
        return ret_str


def has_annotations(element):
    """
    returns True, if an etree element is annotated, i.e. it has children with
    the tag 'labels' and xsi:type 'saltCore:SAnnotation'.
    returns False, otherwise.
    """
    # explicit 'is not None' used because of a FutureWarning
    if element.find('labels[@xsi:type="saltCore:SAnnotation"]',
                    NAMESPACES) is not None:
        return True
    else:
        return False


def get_annotations(element):
    """
    returns a dictionary of all the annotation features of an element,
    e.g. tiger.pos = ART or coref.type = anaphoric.
    """
    from labels import get_annotation
    annotations = {}
    for label in element.getchildren():
        if get_xsi_type(label) == 'saltCore:SAnnotation':
            annotations.update([get_annotation(label)])
    return annotations


def get_elements(tree, tag_name):
    """
    returns a list of all elements of an XML tree that have a certain tag name,
    e.g. layers, edges etc.

    Parameters
    ----------
    tree : lxml.etree._ElementTree
        an ElementTree that represents a complete SaltXML document
    tag_name : str
        the name of an XML tag, e.g. 'nodes', 'edges', 'labels'
    """
    return tree.findall("//{0}".format(tag_name))


def get_subelements(element, tag_name):
    """
    returns a list of all child elements of an element with a certain tag name,
    e.g. labels.
    """
    return element.findall(tag_name)


def get_element_name(element):
    """get the element name of a node, e.g. 'tok_1'"""
    id_label = element.find('labels[@name="SNAME"]')
    return id_label.xpath('@valueString')[0]


def get_graph_element_id(element):
    """
    returns the graph element id of a label/element,
    e.g. "pcc_maz176_merged_paula/maz-0002/maz-0002_graph#tok_1" or "edge177".
    returns none, if no graph element id is present.
    """
    graph_id_label = element.find('labels[@name="id"]')
    if graph_id_label is not None:  # 'is not None' used b/c of FutureWarning
        return graph_id_label.attrib['valueString']
    else:
        return None


def get_layer_ids(element):
    """
    returns the layer ids from a SaltElement (i.e. a node, edge or layer).

    Parameters
    ----------
    element : lxml.etree._Element
        an etree element parsed from a SaltXML document

    Returns
    -------
    layers: list of int
        list of layer indices. list might be empty.
    """
    layers = []
    if element.xpath('@layers'):
        layers_string = element.xpath('@layers')[0]
        for layer_string in layers_string.split():
            _prefix, layer = layer_string.split('.')  # '//@layers.0' -> '0'
            layers.append(int(layer))
    return layers


def element_statistics(tree, element_type):
    """
    Prints the names and counts of all elements present in an
    `etree._ElementTree`, e.g. a SaltDocument::

        SStructure: 65
        SSpan: 32
        SToken: 154
        STextualDS: 1

    Parameters
    ----------
    tree : lxml.etree._ElementTree
        an ElementTree that represents a complete SaltXML document
    element_type : str
        an XML tag, e.g. 'nodes', 'edges', 'labels'
    """
    elements = get_elements(tree, element_type)
    stats = defaultdict(int)
    for i, element in enumerate(elements):
        stats[get_xsi_type(element)] += 1
    for (etype, count) in stats.items():
        print "{0}: {1}".format(etype, count)
