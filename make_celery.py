from coloringbook import create_app
from os import environ

config_file = environ.get("CONFIG_FILE", "config.py")

flask_app = create_app(config_file)
celery_app = flask_app.extensions["celery"]
