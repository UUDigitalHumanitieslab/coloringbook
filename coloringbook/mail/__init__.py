from flask_mail import Mail

mail_client = Mail()


def create_mail(app):
    app.config["MAIL_DEFAULT_SENDER"] = "noreply@coloringbook.nl"

    mail_client.init_app(app)
