from flask_mail import Message
from extensions import mail

def send_new_signal_email(recipients):
    msg = Message(
        subject="📢 New Signal Posted",
        recipients=recipients,
        body=(
            "Hello,\n\n"
            "A new trading signal has been posted by the admin.\n\n"
            "⚠️ Trading involves risk. Educational purposes only.\n\n"
            "Please log in to view the signal.\n\n"
            "— NARI Team"
        )
    )
    mail.send(msg)


def send_reset_email(email, reset_link):
    msg = Message(
        subject="Password Reset",
        recipients=[email],
        body=(
            "You requested a password reset.\n\n"
            f"Reset your password using the link below:\n{reset_link}\n\n"
            "This link expires in 30 minutes.\n\n"
            "If you did not request this, ignore this email."
        )
    )
    mail.send(msg)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)

