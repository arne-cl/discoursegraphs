#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles LXML etree elements from SALT documents.

:var NAMESPACES: the namespaces used in SaltXML files
"""

from lxml import etree # used by doctests only
from collections import defaultdict

NAMESPACES = {'xmi': 'http://www.omg.org/XMI',
              'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
              'sDocumentStructure': 'sDocumentStructure',
              'saltCore': 'saltCore'}

class SaltElement(object):
    """
    An `SaltElement` is the most basic data structure used in `SaltDocument`s and
    `LinguisticDocument`s. `Node`s, `SaltEdge`s and {SaltLayer}s are derived from it.

    :ivar name: a `str` that contains the SNAME of a SaltXML element
    :ivar type: a `str` that contains the xsi:type of a SaltXML element
    :ivar xml: a `lxml.etree._Element` that represents a SaltXML element
    """
    def __init__(self, element, doc_id):
        """
        A `SaltElement` instance is created from an `etree._Element` representing
        a SaltXML document.

        >>> node_str = '''
        ... <nodes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="sDocumentStructure:SToken">
        ...     <labels name="SNAME" valueString="tok_1"/>
        ... </nodes>'''
        >>> node = etree.fromstring(node_str)
        >>> e = SaltElement(node)
        >>> e.name, e.type
        ('tok_1', 'SToken')

        Parameters
        ----------
        element : lxml.etree._Element
            an etree element parsed from a SaltXML document
        doc_id : str
            the document ID of the Salt document that the element
        """
        self.doc_id = doc_id
        self.xml = element
        self.name = get_element_name(element)
        self.type = get_xsi_type(element)

    def __str__(self):
        """
        returns the name, Salt type and XML representation of a `SaltElement`.
        """
        ret_str = "name: %s\n" % self.name
        ret_str += "Salt type: %s\n\n" % self.type
        ret_str += "XML representation:\n%s" % etree.tostring(self.xml)
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
        if get_xsi_type(label) == 'SAnnotation':
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


def get_xsi_type(element):
    """
    returns the type of an element of the XML tree, i.e. nodes, edges,
    layers etc.), raises an exception if the element has no 'xsi:type'
    attribute.
    """
    #.xpath() always returns a list, so we need to select the first element
    try:
        type_with_namespace = element.xpath('@xsi:type', namespaces=NAMESPACES)[0]
        salt_ns, element_type = type_with_namespace.split(':')
        return element_type
    except:
        raise Exception, ("The '{0}' element has no 'xsi:type' but has these "
            "attribs:\n{1}").format(element.tag, element.attrib)

def get_element_name(element):
    """get the element name of a node, e.g. 'tok_1'"""
    id_label = element.find('labels[@name="SNAME"]')
    return id_label.xpath('@valueString')[0]

def get_graph_element_id(element):
    """
    returns the graph element id of a label/element, e.g. "pcc_maz176_merged_paula/maz-0002/maz-0002_graph#tok_1" or "edge177".
    returns none, if no graph element id is present.
    """
    graph_id_label = element.find('labels[@name="id"]')
    if graph_id_label is not None: # 'is not None' used b/c of FutureWarning
        return graph_id_label.attrib['valueString']
    else:
        return None

def get_layer_id(element):
    """
    returns the layer id from an element (e.g. Node or SaltEdge).
    returns None for elements that don't belong to a layer.

    :param element: an etree element parsed from a SaltXML document
    :type element: an `lxml.etree._Element`
    :rtype: `int` or None
    """
    if element.xpath('@layers'):
        layer_string = element.xpath('@layers')[0]
        _prefix, layer = layer_string.split('.') # '//@layers.0' -> '0'
        return int(layer)
    else:
        return None

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


