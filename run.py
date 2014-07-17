#!/usr/bin/env python

from coloringbook import create_app

if __name__ == '__main__':
    app = create_app()
    app.debug = True
    app.run()
