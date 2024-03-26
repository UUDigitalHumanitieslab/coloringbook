#!/usr/bin/env python

# (c) 2014-2023 Research Software Lab, Centre for Digital Humanities, Utrecht University
# Licensed under the EUPL-1.2 or later. You may obtain a copy of the license at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12.

"""
    Management script for running a local test server, database migrations, etc.

    All subcommands require that you pass the path to a configuration file,
    like so:

    python manage.py -c CONFIG_FILE <command>

    The CONFIG_FILE must either be an absolute path, or relative to the
    coloringbook package. See
    coloringbook.__doc__ for more information about configuration.

    Running migrations:

    python manage.py -Ac CONFIG_FILE db <subcommand>

    You need to pass the -A flag in order to prevent Flask-Admin from running
    and then chocking because the table definitions don't match the database.

    Running the test server:

    python manage.py -c CONFIG_FILE runserver [-d] [-r]

    Pass the -d flag to enable debugging. Pass the -r flag to automatically
    reload the application when source files are modified.
"""

from flask.ext.script import Manager
from flask_migrate import MigrateCommand

from coloringbook import create_app

manager = Manager(create_app)
manager.add_option('-c', '--config', dest='config')
manager.add_option('-A', '--no-admin', dest='disable_admin', default=False, action='store_true')
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
