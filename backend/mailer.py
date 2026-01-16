# mailer.py
from flask_mail import Message
from extensions import mail
import smtplib
from email.message import EmailMessage
import os

def send_new_signal_email(recipients):
    msg = Message(
        subject="📢 New Signal Available",
        recipients=recipients,
        body=(
            "Hello,\n\n"
            "A new trading signal has just been posted.\n"
            "Please log in to view it.\n\n"
            "Regards,\n"
            "NARI Team"
        )
    )
    mail.send(msg)

EMAIL = os.getenv("MAIL_USER")
PASSWORD = os.getenv("MAIL_PASS")

def send_email(to, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)


def send_reset_email(to, reset_link):
    msg = Message(
        subject="🔐 Password Reset Request",
        recipients=[to],
        body=f"""
Hello,

You requested to reset your password.

Click the link below to set a new password:
{reset_link}

This link will expire in 30 minutes.

If you did not request this, please ignore this email.

—
NARI Team
"""
    )
    mail.send(msg)
