#!/usr/bin/env python

from coloringbook import app, db

if __name__ == '__main__':
    app.debug = True
    db.create_all(app = app)  # pass app because of Flask-SQLAlchemy contexts
    app.run()
