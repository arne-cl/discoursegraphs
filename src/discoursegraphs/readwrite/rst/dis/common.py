#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains common functions for parsing *.dis files
(used by old versions of RSTTool to annotate rhetorical structure).

It contains some MIT licensed code from
github.com/EducationalTestingService/discourse-parsing
"""

import re

from nltk.tree import ParentedTree

from discoursegraphs.readwrite.ptb import PTB_BRACKET_ESCAPE

SUBTREE_TYPES = ('Root', 'Nucleus', 'Satellite')
NODE_TYPES = ('leaf', 'span')


class DisFile(object):
    """A DisFile instance represents the structure of a *.dis file as a ParentedTree.
    
    NOTE: The resulting tree represents the file format (i.e. the syntax of a *.dis file),
    not its meaning (i.e. it doesn't look like an RST tree).
    """
    def __init__(self, dis_filepath):
        self.filepath = dis_filepath
        
        with open(dis_filepath) as disfile:
            rst_tree_str = disfile.read().strip()
            rst_tree_str = fix_rst_treebank_tree_str(rst_tree_str)
            rst_tree_str = convert_parens_in_rst_tree_str(rst_tree_str)
            self.tree = ParentedTree.fromstring(rst_tree_str)

    @classmethod
    def fromstring(cls, dis_string):
        """Create a DisFile instance from a string containing a *.dis parse."""
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(dis_string)
        temp.close()
        dis_file = cls(dis_filepath=temp.name)
        os.unlink(temp.name)
        return dis_file



def fix_rst_treebank_tree_str(rst_tree_str):
    '''
    This removes some unexplained comments in two files that cannot be parsed.
    - data/RSTtrees-WSJ-main-1.0/TRAINING/wsj_2353.out.dis
    - data/RSTtrees-WSJ-main-1.0/TRAINING/wsj_2367.out.dis

    source: github.com/EducationalTestingService/discourse-parsing
    original license: MIT
    '''
    return re.sub(r'\)//TT_ERR', ')', rst_tree_str)


def convert_parens_in_rst_tree_str(rst_tree_str):
    '''
    This converts any brackets and parentheses in the EDUs of the RST discourse
    treebank to look like Penn Treebank tokens (e.g., -LRB-),
    so that the NLTK tree API doesn't crash when trying to read in the
    RST trees.

    source: github.com/EducationalTestingService/discourse-parsing
    original license: MIT
    '''
    for bracket_type, bracket_replacement in PTB_BRACKET_ESCAPE.items():
        rst_tree_str = \
            re.sub('(_![^_(?=!)]*)\\{}([^_(?=!)]*_!)'.format(bracket_type),
                   '\\g<1>{}\\g<2>'.format(bracket_replacement),
                   rst_tree_str)
    return rst_tree_str
