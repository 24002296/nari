# mailer.py
from flask_mail import Mail, Message
from flask import current_app

from flask_mail import Message
from app import mail   # ✅ IMPORT, DO NOT RECREATE

def send_new_signal_email(recipients):
    msg = Message(
        subject="📢 New Signal Available",
        recipients=recipients,
        body=(
            "Hello,\n\n"
            "A new trading signal has just been posted by the admin.\n"
            "Please log in to your account to view it.\n\n"
            "Regards,\n"
            "NARI Team"
        )
    )
    mail.send(msg)
