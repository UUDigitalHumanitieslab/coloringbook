from flask.ext.admin import Admin

from ..models import db

from .views import FillView

def create_admin ( ):
    admin = Admin(name='Coloringbook')
    admin.add_view(FillView(db.session))
    return admin
