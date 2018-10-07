#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code that is used by more than one RST-related modules.
"""

class RSTBaseTree(object):
    """Base class for converter's from from RST file formats into
    DGParentedTree-based trees.
    """
    def _repr_png_(self):
        """This PNG representation will be automagically used inside
        IPython notebooks.
        """
        return self.tree._repr_png_()

    def __str__(self):
        return self.tree.__str__()

    def label(self):
        """Return the label of the tree's root element."""
        return self.tree.label()

    def pretty_print(self):
        """Return a pretty-printed representation of the RSTTree."""
        return self.tree.pretty_print()

    def __getitem__(self, key):
        return self.tree.__getitem__(key)


def get_segment_label(segment, segment_type, segment_text, ns, tokenized):
    """
    generates an appropriate node label for a segment (useful for dot
    visualization).
    """
    segment_prefix = segment_type[0] if segment_type else '_'
    if tokenized:
        segment_label = u'[{0}]:{1}:segment:{2}'.format(
            segment_prefix, ns, segment.attrib['id'])
    else:
        # if the graph is not tokenized, put (the beginning of) the
        # segment's text into its label
        segment_label = u'[{0}]:{1}: {2}...'.format(
            segment_prefix, segment.attrib['id'], segment_text[:20])
    return segment_label
