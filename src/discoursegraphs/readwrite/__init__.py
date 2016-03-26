# discoursegraphs.readwrite: input/output functionality

"""
The ``readwrite`` package contains importers, exporters and other
output functionality. Basically, it allows you to convert annotated
linguistic documents into a graph-based representation for further
processing.
"""

from discoursegraphs.readwrite.anaphoricity import AnaphoraDocumentGraph, read_anaphoricity
from discoursegraphs.readwrite.brackets import write_brackets
from discoursegraphs.readwrite.brat import write_brat
from discoursegraphs.readwrite.conano import ConanoDocumentGraph, read_conano
from discoursegraphs.readwrite.conll import ConllDocumentGraph, read_conll, write_conll
from discoursegraphs.readwrite.decour import DecourDocumentGraph, read_decour
from discoursegraphs.readwrite.dot import write_dot
from discoursegraphs.readwrite.exmaralda import (
    ExmaraldaDocumentGraph, read_exb, read_exmaralda, write_exmaralda, write_exb)
from discoursegraphs.readwrite.exportxml import read_exportxml
from discoursegraphs.readwrite.gexf import write_gexf
from discoursegraphs.readwrite.graphml import write_graphml
from discoursegraphs.readwrite.mmax2 import MMAXDocumentGraph, read_mmax2
from discoursegraphs.readwrite.neo4j import write_neo4j, write_geoff
from discoursegraphs.readwrite.paulaxml.paula import PaulaDocument, write_paula
from discoursegraphs.readwrite.ptb import PTBDocumentGraph, read_ptb, read_mrg
from discoursegraphs.readwrite.rst.rs3 import RSTGraph, read_rst, read_rs3
from discoursegraphs.readwrite.rst.dis import read_dis
from discoursegraphs.readwrite.salt.saltxmi import SaltDocument, SaltXMIGraph
from discoursegraphs.readwrite.tiger import TigerDocumentGraph, read_tiger
