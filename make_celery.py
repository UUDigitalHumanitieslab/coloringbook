from coloringbook import create_app

flask_app = create_app('config.py')
celery_app = flask_app.extensions["celery"]
