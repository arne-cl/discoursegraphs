
import argparse
import os
import re
import sys

from discoursegraphs.readwrite.rst.dis.distree import DisRSTTree

EDU_START_RE = re.compile("^_!")
EDU_END_RE = re.compile("_!$")
TRIPLE_ESCAPE_RE = re.compile(r'\\\\\\"') # string contains a " char


class CodraRSTTree(DisRSTTree):
    """A CodraRSTTree is basically just a DisRSTTree with some added clean-up code.

    The CODRA RST parser uses the same *.dis format that was used by the RST-DT corpus
    and early versions of RSTTool, but it's string escaping is different.
    """
    def __init__(self, dis_filepath, word_wrap=0, debug=False):
        super(CodraRSTTree, self).__init__(dis_filepath, word_wrap=word_wrap, debug=debug)
        self.cleanup_codra_edus()

    def cleanup_codra_edus(self):
        """Remove leading/trailing '_!' from CODRA EDUs and unescape its double quotes."""
        for leafpos in self.tree.treepositions('leaves'):
            edu_str = self.tree[leafpos]

            edu_str = EDU_START_RE.sub("", edu_str)
            edu_str = TRIPLE_ESCAPE_RE.sub('"', edu_str)
            edu_str = EDU_END_RE.sub("", edu_str)

            self.tree[leafpos] = edu_str

# pseudo-function to create a document tree from a RST (.codra) file
read_codra = CodraRSTTree


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='*.codra RST file to be converted')
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)

    CodraRSTTree(args.input_file).pretty_print()
