#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discourseinfostat.programming@arne.cl>

import discoursegraphs


def test_data_installation():
    """the `data` directory was installed properly with the package"""
    package_root_dir = discoursegraphs.PACKAGE_ROOT_DIR
    assert len(package_root_dir) != 2

    # if we can't find the documents, this will be 0
    assert len(discoursegraphs.corpora.pcc) == 176
