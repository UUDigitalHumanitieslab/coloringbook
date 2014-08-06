from flask import Flask

from .models import db
from .views import site
from .admin import create_admin

def create_app ( ):
    app = Flask(__name__)
    
    # The following line may be uncommented, and the corresponding 
    # file created, if we ever decide that the application needs
    # default settings.
    ## app.config.from_object('coloringbook.defaults')
    
    # $COLORINGBOOK_CONFIG should be the path to an external config
    # file. If placing the file in the same directory as run.py and
    # coloringbook.wsgi, it is recommend to call it config.py because
    # that name is banned from versioning by .gitignore. At the very
    # least, it should define SQLALCHEMY_DATABASE_URI.
    app.config.from_envvar('COLORINGBOOK_CONFIG')

    db.init_app(app)
    db.create_all(app = app)  # pass app because of Flask-SQLAlchemy contexts
    create_admin().init_app(app)
    app.register_blueprint(site)
    
    return app
