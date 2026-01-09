from flask_mail import Mail, Message
import os

mail = Mail()

def send_new_signal_email(recipients):
    if not recipients:
        return

    msg = Message(
        subject="📢 New Trading Signal Available",
        recipients=recipients,
        body=(
            "Hello,\n\n"
            "A new trading signal has just been posted by the admin.\n"
            "Please log in to your account to view it.\n\n"
            "Best regards,\n"
            "NARI Signals Team"
        )
    )

    mail.send(msg)
