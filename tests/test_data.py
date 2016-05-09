#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discourseinfostat.programming@arne.cl>

import discoursegraphs


def test_data_installation():
    """the `data` directory was installed properly with the package"""
    src_root_dir = discoursegraphs.SRC_ROOT_DIR
    package_root_dir = discoursegraphs.get_package_root_dir(src_root_dir)
    # implicitly vs. explicitly setting the parameter
    assert package_root_dir == discoursegraphs.get_package_root_dir()

    # if we can't find the documents, this will be 0
    assert len(discoursegraphs.corpora.pcc) == 176
