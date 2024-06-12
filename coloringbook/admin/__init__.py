# (c) 2014-2023 Research Software Lab, Centre for Digital Humanities, Utrecht University
# Licensed under the EUPL-1.2 or later. You may obtain a copy of the license at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12.

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

from ..models import db, WelcomeText, PrivacyText, InstructionText, SuccessText


def create_admin(app):
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
    admin = Admin(name='Coloring Book', app=app, base_template='admin/style_master.html')
    with app.app_context():
        from .views import *
    admin.add_view(FillView(sess))
    admin.add_view(SubjectView(sess))
    admin.add_view(SurveyView(sess))
    admin.add_view(PageView(sess))
    admin.add_view(DrawingView(sess))
    admin.add_view(SoundView(sess))
    admin.add_view(TextView(WelcomeText, sess, name='Welcome Text', endpoint='welcome_text'))
    admin.add_view(StartingFormView(sess))
    admin.add_view(TextView(PrivacyText, sess, name='Privacy Text', endpoint='privacy_text'))
    admin.add_view(TextView(InstructionText, sess, name='Instruction Text', endpoint='instruction_text'))
    admin.add_view(EndingFormView(sess))
    admin.add_view(TextView(SuccessText, sess, name='Success Text', endpoint='success_text'))
    admin.add_view(ButtonSetView(sess))
    admin.add_view(ColorView(sess, category='Utilities'))
    admin.add_view(LanguageView(sess, category='Utilities'))
    return admin
