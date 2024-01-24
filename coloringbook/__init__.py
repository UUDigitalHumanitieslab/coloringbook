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
    SQLALCHEMY_DATABASE_URI. For example,
    
    >>> class config:
    ...     SQLALCHEMY_DATABASE_URI = 'sqlite://'  # in-memory database
    ...     SECRET_KEY = 'abcdefghijklmnopqrstuvwxyz'
    ...     TESTING = True
    ... 
    >>> application = create_app(config)
    
    Note that the class itself is passed as the configuration object
    in this example. An imported module which has a global
    SQLALCHEMY_DATABASE_URI constant defined also works. Just make
    sure that your configuration module is in the PYTHONPATH, and then
    run `import your_module` and `create_app(your_module)`.
    
    Instead of importing the module, you may also pass the path to the module
    as a string.

    It is strongly recommend that whatever file contains your
    configuration does not reside in a directory from which files may
    potentially be served in production.
"""

from flask import Flask
from flask_migrate import Migrate

from .models import db
from .views import site
from .admin import create_admin
from .mail import create_mail
from .task_worker import celery_init_app


migrate = Migrate()


def create_app(config, disable_admin=False, create_db=False, instance=None):
    app = Flask(__name__, instance_path=instance)

    # The following line may be uncommented, and the corresponding
    # file created, if we ever decide that the application needs
    # default settings.
    ## app.config.from_object('coloringbook.defaults')

    if type(config) in (str, unicode):
        app.config.from_pyfile(config)
    else:
        app.config.from_object(config)

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
