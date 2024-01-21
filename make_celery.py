from coloringbook import create_app
from os import environ

config_location = environ.get("CONFIG_LOCATION", "config.py")

flask_app = create_app(config_location)
celery_app = flask_app.extensions["celery"]
