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


from flask_mail import Message
from extensions import mail
import threading

def send_reset_email_async(app, to, reset_link):
    def send():
        with app.app_context():
            try:
                msg = Message(
                    subject="🔐 Password Reset",
                    recipients=[to],
                    body=f"""
HU DIVHA VHALIMI

You requested a password reset.

Reset your password using this link:
{reset_link}

This link expires in 30 minutes.

If you didn’t request this, ignore this email.
"""
                )
                mail.send(msg)
                print("✅ Reset email sent")
            except Exception as e:
                print("❌ Email failed:", e)

    threading.Thread(target=send).start()
