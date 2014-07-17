from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from ..models import db, Page, Color

from .views import SurveyView, FillView

def create_admin ( ):
    sess = db.session
    admin = Admin(name='Coloringbook')
    admin.add_view(SurveyView(sess))
    admin.add_view(ModelView(Page, sess, name = 'Pages'))
    admin.add_view(ModelView(Color, sess, name = 'Colors'))
    admin.add_view(FillView(sess))
    return admin
