from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from ..models import *

admin = Admin(name='Coloringbook')

admin.add_view(ModelView(Fill, db.session))
