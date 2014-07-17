from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from ..models import db, Survey, Page, Color

from .views import FillView

def create_admin ( ):
    sess = db.session
    admin = Admin(name='Coloringbook')
    admin.add_view(ModelView(Survey, sess, name = 'Surveys'))
    admin.add_view(ModelView(Page, sess, name = 'Pages'))
    admin.add_view(ModelView(Color, sess, name = 'Colors'))
    admin.add_view(FillView(sess))
    return admin
