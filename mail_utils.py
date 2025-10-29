from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def send_welcome_email(user):
    msg = Message(
        subject="Welcome to Mtaa Haven!",
        recipients=[user.email],
        body=f"Hi {user.first_name},\n\nThanks for signing up. Start exploring properties or managing your rentals today!"
    )
    mail.send(msg)