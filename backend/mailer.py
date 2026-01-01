# mailer.py
from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def send_email(to_email, subject, html_body):
    try:
        msg = Message(subject,
                      sender=(current_app.config['MAIL_FROM_NAME'], current_app.config['MAIL_FROM']),
                      recipients=[to_email])
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error("Mail send error: %s", str(e))
        return False
