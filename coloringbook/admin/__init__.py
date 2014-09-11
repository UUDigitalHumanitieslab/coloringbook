# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    This is the head of the admin subpackage.
    
    The purpose of the package is to define a flask.ext.admin.Admin
    object, which will be responsible for serving the administrative
    backend of the web application. Most of the work is done in the
    submodules, this module only provides the create_admin function.
"""

from os.path import join, dirname

from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.fileadmin import FileAdmin

from ..models import db, Page, Color, Language


def create_admin (app):
    """
        Create an Admin object on Flask instance `app` and return it.
        
        `app` must be a live Flask instance which has already been
        configured. Using this function basically goes like this:
        
        >>> import coloringbook, flask
        >>> application = flask.Flask(__name__)
        >>> application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        >>> from coloringbook.models import db
        >>> db.init_app(application)
        >>> db.create_all(app = application)
        >>> admin = create_admin(application)
        
    """
    sess = db.session
    admin = Admin(name='Coloringbook', app=app)
    with app.app_context():
        from .views import *
    admin.add_view(FillView(sess))
    admin.add_view(SurveyView(sess))
    admin.add_view(PageView(sess))
    admin.add_view(DrawingView(sess))
    admin.add_view(SoundView(sess))
    admin.add_view(ModelView(Color, sess, name = 'Colors'))
    admin.add_view(ModelView(Language, sess, name = 'Languages'))
    return admin
