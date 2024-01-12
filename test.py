#!/usr/bin/env python

# (c) 2014-2023 Research Software Lab, Centre for Digital Humanities, Utrecht University
# Licensed under the EUPL-1.2 or later. You may obtain a copy of the license at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12.

"""
    Script for automatically running the doctest test cases.
"""

from doctest import testmod, ELLIPSIS

import coloringbook, coloringbook.testing

def test_all():
    testmod(coloringbook.testing)
    testmod(coloringbook)
    testmod(coloringbook.models)
    testmod(coloringbook.views, optionflags = ELLIPSIS)
    testmod(coloringbook.admin)
    testmod(coloringbook.admin.utilities, optionflags = ELLIPSIS)
    testmod(coloringbook.admin.forms)
    testmod(coloringbook.admin.views)
    testmod(coloringbook.utilities)
    testmod(coloringbook.mail.utilities)

if __name__ == '__main__':
    test_all()
