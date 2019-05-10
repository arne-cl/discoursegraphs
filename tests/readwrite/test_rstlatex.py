#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""Basic tests for the ``rstlatex`` module"""

# Python 2/3 compatibility
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.tree import t
from discoursegraphs.readwrite.rst.rstlatex import MULTISAT_RELNAME


def test_writetofile():
    """A single nucleus-satellite relation is converted into rst.sty format
    and written to a file.
    """
    sat_before_nuc = \
    t('circumstance', [
            ('S', ['sat first']),
            ('N', ['nuc second'])
    ])
    
    tempfile = NamedTemporaryFile()
    dg.write_rstlatex(sat_before_nuc, tempfile.name)
    
    with open(tempfile.name, 'r') as rstlatex_file:
        assert rstlatex_file.read() == u'\\dirrel\n\t{circumstance}{sat first}\n\t{}{nuc second}\n'


def test_nucsat():
    """A single nucleus-satellite relation is converted into rst.sty format."""
    sat_before_nuc = \
    t('circumstance', [
            ('S', ['sat first']),
            ('N', ['nuc second'])
    ])
    
    result = dg.write_rstlatex(sat_before_nuc)
    assert result.rstlatextree == u'\\dirrel\n\t{circumstance}{sat first}\n\t{}{nuc second}'

    nuc_before_sat = \
    t('circumstance', [
            ('N', ['nuc first']),
            ('S', ['sat second'])
        ])

    result = dg.write_rstlatex(nuc_before_sat)
    assert result.rstlatextree == u'\\dirrel\n\t{}{nuc first}\n\t{circumstance}{sat second}'


def test_multinuc():
    """A multinuclear relation is converted into rst.sty format."""
    contrast = \
    t('contrast', [
            ('N', ['nuc-1']),
            ('N', ['nuc-2'])
        ])

    result = dg.write_rstlatex(contrast)
    assert result.rstlatextree == u'\\multirel{contrast}\n\t{\\rstsegment{nuc-1}}\n\t{\\rstsegment{nuc-2}}'

    joint = \
    t('joint', [
            ('N', ['nuc-1']),
            ('N', ['nuc-2']),
            ('N', ['nuc-3'])
        ])

    result = dg.write_rstlatex(joint)
    assert result.rstlatextree == u'\\multirel{joint}\n\t{\\rstsegment{nuc-1}}\n\t{\\rstsegment{nuc-2}}\n\t{\\rstsegment{nuc-3}}'


def gen_numbered_nucsat(first_element, number):
    expected_elems = ('N', 'S')
    assert first_element in expected_elems

    nuc = ('N', ['nuc'])
    sat = ('S', ['sat-{}'.format(number)])

    if first_element == 'N':
        return t('nuc-sat-{}'.format(number), [nuc, sat])
    else:
        return t('sat-nuc-{}'.format(number), [sat, nuc])


def test_multisat():
    """A set of relations sharing the same nucleus is converted into rst.sty format."""
    # S-N-S
    sat_nuc_sat = t(MULTISAT_RELNAME, [
        ('S', gen_numbered_nucsat('S', 1)),
        ('S', gen_numbered_nucsat('N', 1))
    ])

    result = dg.write_rstlatex(sat_nuc_sat)
    assert result.rstlatextree == u'\\dirrel\n\t{sat-nuc-1}{sat-1}\n\t{}{nuc}\n\t{nuc-sat-1}{sat-1}'
    
    # S-S-N
    sat_sat_nuc = t(MULTISAT_RELNAME, [
        ('S', gen_numbered_nucsat('S', 1)),
        ('S', gen_numbered_nucsat('S', 2))
    ])

    result = dg.write_rstlatex(sat_sat_nuc)
    assert result.rstlatextree == u'\\dirrel\n\t{sat-nuc-1}{sat-1}\n\t{sat-nuc-2}{sat-2}\n\t{}{nuc}'

    # N-S-S
    nuc_sat_sat = t(MULTISAT_RELNAME, [
        ('S', gen_numbered_nucsat('N', 1)),
        ('S', gen_numbered_nucsat('N', 2))
    ])

    result = dg.write_rstlatex(nuc_sat_sat)
    assert result.rstlatextree == u'\\dirrel\n\t{}{nuc}\n\t{nuc-sat-1}{sat-1}\n\t{nuc-sat-2}{sat-2}'

    # S-N-S-S
    sat_nuc_sat_sat = t(MULTISAT_RELNAME, [
        ('S', gen_numbered_nucsat('S', 1)),
        ('S', gen_numbered_nucsat('N', 1)),
        ('S', gen_numbered_nucsat('N', 2))
    ])

    result = dg.write_rstlatex(sat_nuc_sat_sat)
    assert result.rstlatextree == u'\\dirrel\n\t{sat-nuc-1}{sat-1}\n\t{}{nuc}\n\t{nuc-sat-1}{sat-1}\n\t{nuc-sat-2}{sat-2}'

    # S-S-N-S
    sat_sat_nuc_sat = t(MULTISAT_RELNAME, [
        ('S', gen_numbered_nucsat('S', 1)),
        ('S', gen_numbered_nucsat('S', 2)),
        ('S', gen_numbered_nucsat('N', 1))
    ])

    result = dg.write_rstlatex(sat_sat_nuc_sat)
    assert result.rstlatextree == u'\\dirrel\n\t{sat-nuc-1}{sat-1}\n\t{sat-nuc-2}{sat-2}\n\t{}{nuc}\n\t{nuc-sat-1}{sat-1}'
    
    # S-S-S-N-S
    sat_sat_sat_nuc_sat = t(MULTISAT_RELNAME, [
        ('S', gen_numbered_nucsat('S', 1)),
        ('S', gen_numbered_nucsat('S', 2)),
        ('S', gen_numbered_nucsat('S', 3)),
        ('S', gen_numbered_nucsat('N', 1))
    ])

    result = dg.write_rstlatex(sat_sat_sat_nuc_sat)
    assert result.rstlatextree == u'\\dirrel\n\t{sat-nuc-1}{sat-1}\n\t{sat-nuc-2}{sat-2}\n\t{sat-nuc-3}{sat-3}\n\t{}{nuc}\n\t{nuc-sat-1}{sat-1}'
    
    # S-N-S-S-S
    sat_nuc_sat_sat_sat = t(MULTISAT_RELNAME, [
        ('S', gen_numbered_nucsat('S', 1)),
        ('S', gen_numbered_nucsat('N', 1)),
        ('S', gen_numbered_nucsat('N', 2)),
        ('S', gen_numbered_nucsat('N', 3))
    ])

    result = dg.write_rstlatex(sat_nuc_sat_sat_sat)
    assert result.rstlatextree == u'\\dirrel\n\t{sat-nuc-1}{sat-1}\n\t{}{nuc}\n\t{nuc-sat-1}{sat-1}\n\t{nuc-sat-2}{sat-2}\n\t{nuc-sat-3}{sat-3}'

    # S-S-S-N-S-S-S
    sat_sat_sat_nuc_sat_sat_sat = t(MULTISAT_RELNAME, [
        ('S', gen_numbered_nucsat('S', 1)),
        ('S', gen_numbered_nucsat('S', 2)),
        ('S', gen_numbered_nucsat('S', 3)),
        ('S', gen_numbered_nucsat('N', 1)),
        ('S', gen_numbered_nucsat('N', 2)),
        ('S', gen_numbered_nucsat('N', 3))
    ])

    # ~ import pudb; pudb.set_trace() 
    result = dg.write_rstlatex(sat_sat_sat_nuc_sat_sat_sat)
    assert result.rstlatextree == u'\\dirrel\n\t{sat-nuc-1}{sat-1}\n\t{sat-nuc-2}{sat-2}\n\t{sat-nuc-3}{sat-3}\n\t{}{nuc}\n\t{nuc-sat-1}{sat-1}\n\t{nuc-sat-2}{sat-2}\n\t{nuc-sat-3}{sat-3}'
