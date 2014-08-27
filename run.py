#!/usr/bin/env python

# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

from coloringbook import create_app
import os

if __name__ == '__main__':
    app = create_app(__import__(os.environ['COLORINGBOOK_CONFIG']))
    app.debug = True
    app.run()
