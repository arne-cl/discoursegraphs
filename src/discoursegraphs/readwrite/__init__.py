# discoursegraphs.readwrite: input/output functionality

"""
The ``readwrite`` package contains importers, exporters and other
output functionality. Basically, it allows you to convert annotated
linguistic documents into a graph-based representation for further
processing.
"""

from discoursegraphs.readwrite.tiger import TigerDocumentGraph
from discoursegraphs.readwrite.anaphoricity import AnaphoraDocumentGraph
from discoursegraphs.readwrite.rst import RSTGraph
