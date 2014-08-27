# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

from flask import Flask

from .models import db
from .views import site
from .admin import create_admin

def create_app (config):
    app = Flask(__name__)
    
    # The following line may be uncommented, and the corresponding 
    # file created, if we ever decide that the application needs
    # default settings.
    ## app.config.from_object('coloringbook.defaults')
    
    app.config.from_object(config)

    db.init_app(app)
    db.create_all(app = app)  # pass app because of Flask-SQLAlchemy contexts
    create_admin(app)
    app.register_blueprint(site)
    
    return app

