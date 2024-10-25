# (c) 2014-2023 Research Software Lab, Centre for Digital Humanities, Utrecht University
# Licensed under the EUPL-1.2 or later. You may obtain a copy of the license at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12.

"""
    This is the head of the coloringbook package.

    Its primary purpose is to deliver a fully configured WSGI
    application object which can be run either in production or in a
    test environment. When run, the application will serve all the
    various pages of the Coloring Book web application.

    In order to run the create_app function, you need to pass any
    Python object with member variables that can be used to configure
    the application. At the very least this should include
    SQLALCHEMY_DATABASE_URI, unless `use_test_db` is set to True, in
    which case an in-memory SQLite database is used.

    For example,

    >>> class config:
    ...     SECRET_KEY = 'abcdefghijklmnopqrstuvwxyz'
    ...     TESTING = True
    ...
    >>> application = create_app(config, create_db=True, use_test_db=True)

    Note that the class itself is passed as the configuration object
    in this example. An imported module with global constants defined
    also works. Just make sure that your configuration module is in the
    PYTHONPATH, and then run `import your_module` and
    `create_app(your_module)`.

    Instead of importing the module, you may also pass the path to the module
    as a string.

    It is strongly recommended that whatever file contains your
    configuration does not reside in a directory from which files may
    potentially be served in production.
"""

from logging.config import dictConfig
from os import environ
from flask import Flask
from flask_migrate import Migrate

from .models import db
from .views import site
from .admin import create_admin
from .mail import create_mail
from .task_worker import celery_init_app


migrate = Migrate()

def compose_db_uri():
    """
    Compose the database URI (SQLALCHEMY_DATABASE_URI)
    from environment variables.
    """
    db_username = environ.get("DB_USER")
    db_password = environ.get("DB_PASSWORD")
    db_host = environ.get("DB_HOST")
    db_port = environ.get("DB_PORT")
    db_name = environ.get("DB_DB")

    if not all([db_username, db_password, db_host, db_port, db_name]):
        raise ValueError("Database environment variables not set.")

    return "mysql://{}:{}@{}:{}/{}".format(db_username, db_password, db_host, db_port, db_name)


def create_app(config, disable_admin=False, create_db=False, use_test_db=False, instance=None):
    """
    Create and configure the Flask application.

    Args:
        config: The configuration object or path to the configuration file.
        disable_admin: A boolean indicating whether to disable the admin interface. Default is False.
        create_db: A boolean indicating whether to create a new database. Default is False.
        use_test_db: A boolean indicating whether to use a (SQLite) test database. Default is False.
        instance: The path to the instance folder. Default is None.

    Returns:
        The Flask application.

    """

    # Set up logging. https://flask.palletsprojects.com/en/1.1.x/logging/
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })

    app = Flask(__name__, instance_path=instance)

    # The following line may be uncommented, and the corresponding
    # file created, if we ever decide that the application needs
    # default settings.
    ## app.config.from_object('coloringbook.defaults')

    if type(config) in (str, unicode):
        app.config.from_pyfile(config)
    else:
        app.config.from_object(config)

    if use_test_db is True:
        app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite://'
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = compose_db_uri()

    db.init_app(app)
    if create_db:
        db.create_all(app=app)

    migrate.init_app(app, db)
    app.register_blueprint(site)
    if not disable_admin:
        create_admin(app)

    create_mail(app)
    celery_init_app(app)

    return app

# In production mode, provide an entrypoint for Gunicorn.
production_mode = environ.get("DEVELOPMENT", "1") == "0"
if production_mode is True:
    config_file = environ.get("CONFIG_FILE", "config.py")
    prod_app = create_app(config_file)
