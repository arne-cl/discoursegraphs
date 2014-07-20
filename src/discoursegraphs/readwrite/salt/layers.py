#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the parsing of SALT layers.
"""

import re
from lxml.builder import ElementMaker

from discoursegraphs.readwrite.salt.elements import SaltElement
from discoursegraphs.readwrite.salt.util import NAMESPACES

DIGITS = re.compile('\d+')


class SaltLayer(SaltElement):
    """
    A ``SaltLayer`` instances describes a Salt XML layer. In Salt, a layer
    groups nodes and edges belonging to the same annotation level, e.g.
    syntax or information structure.

    Attributes
    ----------
    nodes : list of int
        a list of node indices which point to the nodes belonging to this
        layer
    edges : list of int
        a list of edge indices which point to the edges belonging to this
        layer
    """
    def __init__(self, name, element_id, xsi_type, labels, nodes, edges,
                 xml=None):
        """
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
        nodes : list of int
            a list of node indices which point to the nodes belonging to this
            layer
        edges : list of int
            a list of edge indices which point to the edges belonging to this
            layer
        xml : lxml.etree._Element or None
            an etree element parsed from a SaltXML document
        """
        super(SaltLayer, self).__init__(name, element_id, xsi_type, labels,
                                        xml)
        self.nodes = nodes
        self.edges = edges

    @classmethod
    def from_etree(cls, etree_element):
        """
        creates a ``SaltLayer`` instance from the etree representation of an
        <layers> element from a SaltXMI file.
        """
        ins = SaltElement.from_etree(etree_element)
        # TODO: this looks dangerous, ask Stackoverflow about it!
        # convert SaltElement into SaltLayer
        ins.__class__ = SaltLayer.mro()[0]

        # add nodes and edges that belong to this layer (if any)
        for element in ('nodes', 'edges'):
            elem_list = []
            xpath_result = etree_element.xpath('@'+element)
            if xpath_result:
                val_str = xpath_result[0]
                elem_list.extend(int(elem_id)
                                 for elem_id in DIGITS.findall(val_str))
            setattr(ins, element, elem_list)
        return ins

    def to_etree(self):
        """
        creates an etree element of a ``SaltLayer`` that mimicks a SaltXMI
        <layers> element
        """
        nodes_attrib_val = ' '.join('//@nodes.{}'.format(node_id)
                                    for node_id in self.nodes)
        edges_attrib_val = ' '.join('//@edges.{}'.format(edge_id)
                                    for edge_id in self.edges)

        attribs = {
            '{{{pre}}}type'.format(pre=NAMESPACES['xsi']): self.xsi_type,
            'nodes': nodes_attrib_val, 'edges': edges_attrib_val}
        # a layer might have no nodes or edges attributed to it
        non_empty_attribs = {key: val for (key, val) in attribs.items()
                             if val is not None}

        E = ElementMaker()
        layer = E('layers', non_empty_attribs)
        label_elements = (label.to_etree() for label in self.labels)
        layer.extend(label_elements)
        return layer
