DiscourseGraphs
===============

This library enables you to process linguistic corpora with multiple levels
of annotations by:

1. converting the different annotation formats into separate graphs and 
2. merging these graphs into a single multidigraph (based on the common
   tokenization of the annotation layers)

So far, the following formats can be imported and merged:

* `TigerXML`_ (a format for representing tree-like syntax graphs with
  secondary edges)
* RS3 (a format used by `RSTTool`_ to
  annotate documents with Rhetorical Structure Theory)
* an ad-hoc plain text format for annotating expletives (you're probably not
  interested in)

.. _`TigerXML`: http://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/TIGERSearch/doc/html/TigerXML.html
.. _`RSTTool`: http://www.wagsoft.com/RSTTool/


Installation
------------

::

    git clone https://github.com/arne-cl/discoursegraphs.git
    cd discoursegraphs
    python setup.py install # prepend 'sudo' if needed



Requirements
------------

- `lxml`
- `networkx`
- `graphviz`
- `pygraphviz`

License
-------

3-Clause BSD.

Author
------
Arne Neumann


People who downloaded this also like
------------------------------------

- `SaltNPepper`_ a converter framework for various linguistic data formats

.. _`SaltNPepper`: https://korpling.german.hu-berlin.de/p/projects/saltnpepper/wiki/
