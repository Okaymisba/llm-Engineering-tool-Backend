import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

sender_email = os.getenv("SENDER_EMAIL")
app_password = os.getenv("EMAIL_APP_PASSWORD")


def generate_OTP(length=6):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp


def send_email(receiver_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        print("OTP sent successfully.")
    except Exception as e:
        print(f"Failed to send OTP. Error: {e}")
        return e
