# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Auxiliary functions for testing purposes, only imported from doctests.
    
    Typical way to use this module is to type something like the
    following at the top of your doctest:
    
    >>> import coloringbook.testing as t
    >>> testapp = t.get_fixture_app()
    
"""

import coloringbook


def get_fixture_app():
    class config:
        SQLALCHEMY_DATABASE_URI = 'sqlite://'
        SECRET_KEY = '1234567890'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
    return coloringbook.create_app(config, create_db=True)
