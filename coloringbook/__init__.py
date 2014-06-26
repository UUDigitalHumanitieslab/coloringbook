from flask import Flask

from .models import db
from .views import site
from .admin import admin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://coloringbook@localhost/coloringbook'

db.init_app(app)
admin.init_app(app)

app.register_blueprint(site)
