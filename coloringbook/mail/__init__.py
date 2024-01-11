from flask_mail import Mail

mail_client = Mail()


def create_mail(app):
    mail_client.init_app(app)
