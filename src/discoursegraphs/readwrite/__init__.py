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
from discoursegraphs.readwrite.freqt import docgraph2freqt, write_freqt
from discoursegraphs.readwrite.gexf import write_gexf
from discoursegraphs.readwrite.graphml import write_graphml
from discoursegraphs.readwrite.mmax2 import MMAXDocumentGraph, read_mmax2
from discoursegraphs.readwrite.neo4j import write_neo4j, write_geoff
from discoursegraphs.readwrite.paulaxml.paula import PaulaDocument, write_paula
from discoursegraphs.readwrite.ptb import PTBDocumentGraph, read_ptb, read_mrg
from discoursegraphs.readwrite.rst.rs3 import RSTGraph, RSTTree, read_rst, read_rs3
from discoursegraphs.readwrite.rst.rs3.rs3tree import read_rs3tree
from discoursegraphs.readwrite.rst.rs3.rs3filewriter import RS3FileWriter, write_rs3
from discoursegraphs.readwrite.rst.hilda import HILDARSTTree, read_hilda
from discoursegraphs.readwrite.rst.heilman_sagae_2015 import HS2015RSTTree, read_hs2015tree
from discoursegraphs.readwrite.rst.dis.disgraph import read_dis
from discoursegraphs.readwrite.rst.dis.distree import read_distree
from discoursegraphs.readwrite.rst.dis.disfilewriter import DisFileWriter, write_dis
from discoursegraphs.readwrite.rst.dplp import DPLPRSTTree, read_dplp
from discoursegraphs.readwrite.rst.dis.codra import read_codra
from discoursegraphs.readwrite.rst.urml import URMLDocumentGraph, read_urml
from discoursegraphs.readwrite.salt.saltxmi import SaltDocument, SaltXMIGraph
from discoursegraphs.readwrite.tiger import TigerDocumentGraph, read_tiger
from discoursegraphs.readwrite.tree import t, tree2bracket
