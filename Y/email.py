from flask_mail import Message
from flask import current_app
from Y import mail
from threading import Thread


def send_async_email(app, msg):
    try:
        with app.app_context():
            mail.send(msg)
        print("email sent")
    except Exception as e:
        print("email not sent")
        print(e)

# 'asynchronous' function
# function returns immediately so that the application can continue running concurrently while email is 
# being sent by a background thread
def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body

    try:
        # send_async_email function runs in a background thread
        Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
    except Exception as e:
        print(e)
