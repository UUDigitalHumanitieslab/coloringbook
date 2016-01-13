#!/usr/bin/env python

# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Management script for running a local test server.
    
    Note that this script relies on the presence of a
    COLORINGBOOK_CONFIG environment variable which contains the name
    of a Python module with configuration settings (see
    coloringbook.__doc__ for more information about configuration).
    The PYTHONPATH should be set such that the module can be found by
    name.

    For example, if you run this script from your home directory while
    your configuration is in /etc/www/coloring.py, you might run the
    following commands:
    
    export PYTHONPATH=/etc/www
    export COLORINGBOOK_CONFIG=coloring
    python manage.py
"""

from coloringbook import create_app
import os

if __name__ == '__main__':
    app = create_app(__import__(os.environ['COLORINGBOOK_CONFIG']))
    app.debug = True
    app.run()
