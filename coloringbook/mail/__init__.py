from flask_mail import Mail

mail_client = Mail()


def create_mail(app):
    # TODO: configure this

    # app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
    # app.config['MAIL_PORT'] = 2525
    # app.config['MAIL_USERNAME'] = 'your_username'
    # app.config['MAIL_PASSWORD'] = 'your_password'
    # app.config['MAIL_USE_TLS'] = True
    # app.config['MAIL_USE_SSL'] = False
    app.config["MAIL_DEFAULT_SENDER"] = "noreply@coloringbook.nl"

    mail_client.init_app(app)
