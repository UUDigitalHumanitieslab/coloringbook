# (c) 2014-2023 Research Software Lab, Centre for Digital Humanities, Utrecht University
# Licensed under the EUPL-1.2 or later. You may obtain a copy of the license at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12.

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
        SECRET_KEY = '1234567890'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        MAIL_SERVER = "smtp.uu.nl"
        MAIL_PORT = 587
        MAIL_USE_TLS = True
        MAIL_USE_SSL = False
        MAIL_USERNAME = "test"
        MAIL_PASSWORD = "test"
        MAIL_DEFAULT_SENDER = "test"
        # Ensures Flask Mail does not send any real emails.
        TESTING = True
    return coloringbook.create_app(config, create_db=True, use_test_db=True)
