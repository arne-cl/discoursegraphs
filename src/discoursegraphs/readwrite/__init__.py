# discoursegraphs.readwrite: input/output functionality

"""
The ``readwrite`` package contains importers, exporters and other
output functionality. Basically, it allows you to convert annotated
linguistic documents into a graph-based representation for further
processing.
"""

__all__ = [
    'AnaphoraDocumentGraph', 'ConanoDocumentGraph', 'MMAXDocumentGraph',
    'PaulaDocument', 'write_paula', 'RSTGraph', 'SaltDocument', 'SaltXMIGraph',
    'TigerDocumentGraph'
]

from discoursegraphs.readwrite.anaphoricity import AnaphoraDocumentGraph
from discoursegraphs.readwrite.conano import ConanoDocumentGraph
from discoursegraphs.readwrite.mmax2 import MMAXDocumentGraph
from discoursegraphs.readwrite.paulaxml.paula import PaulaDocument, write_paula
from discoursegraphs.readwrite.rst import RSTGraph
from discoursegraphs.readwrite.salt.saltxmi import SaltDocument, SaltXMIGraph
from discoursegraphs.readwrite.tiger import TigerDocumentGraph
