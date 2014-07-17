from flask import Flask

from .models import db
from .views import site
from .admin import create_admin

def create_app ( ):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://coloringbook@localhost/coloringbook'

    db.init_app(app)
    db.create_all(app = app)  # pass app because of Flask-SQLAlchemy contexts
    create_admin().init_app(app)
    app.register_blueprint(site)
    
    return app
