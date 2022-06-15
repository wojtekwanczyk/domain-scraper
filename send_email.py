
import os
import ssl
import smtplib
from email.message import EmailMessage

HOST = 'smtp.gmail.com'
PORT = 465
FROM = os.env['GMAIL_APP_USERNAME']
PASSWORD = os.env['GMAIL_APP_PASSWORD']

def send_email(to, content):
    msg = EmailMessage()
    msg['From'] = FROM
    msg['To'] = to
    msg['Subject'] = 'Test message'
    msg.set_content(content)
    print(f'Sending email to {to}')
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(HOST, PORT, context=context) as server:
        server.login(FROM, PASSWORD)
        server.send_message(msg)

if __name__ == '__main__':
    to = 'wwanc@softserveinc.com'
    msg = 'Test email body'
    send_email(to, msg)

