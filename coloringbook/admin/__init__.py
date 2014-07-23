from os.path import join, dirname

from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.fileadmin import FileAdmin

from ..models import db, Page, Color, Language


def create_admin (app):
    sess = db.session
    admin = Admin(name='Coloringbook', app=app)
    with app.app_context():
        from .views import SurveyView, FillView
    admin.add_view(FillView(sess))
    admin.add_view(SurveyView(sess))
    admin.add_view(ModelView(Page, sess, name = 'Pages'))
    admin.add_view(ModelView(Color, sess, name = 'Colors'))
    admin.add_view(ModelView(Language, sess, name = 'Languages'))
    fpath = join(dirname(dirname(__file__)), 'static')
    admin.add_view(FileAdmin(fpath, '/static/', name = 'Files'))
    return admin
