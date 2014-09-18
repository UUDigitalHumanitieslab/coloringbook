#!/usr/bin/env python

# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Script for automatically running the doctest test cases.
"""

from doctest import testmod, ELLIPSIS

import coloringbook, coloringbook.testing

def test_all ( ):
    testmod(coloringbook.testing)
    testmod(coloringbook)
    testmod(coloringbook.models)
    testmod(coloringbook.views, optionflags = ELLIPSIS)
    testmod(coloringbook.admin)
    testmod(coloringbook.admin.utilities)
    testmod(coloringbook.admin.forms)
    testmod(coloringbook.admin.views)

if __name__ == '__main__':
    test_all()
