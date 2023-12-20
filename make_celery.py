from coloringbook import create_app

flask_app = create_app('CONFIG.py')
celery_app = flask_app.extensions["celery"]
