import json
import os
import ssl
import smtplib

from datetime import date
from email.message import EmailMessage
from pprint import pprint

class DomainMailer:
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.host = 'smtp.gmail.com'
        self.port = 465
        try:
            self.sender = os.environ['GMAIL_APP_USERNAME']
            self.password = os.environ['GMAIL_APP_PASSWORD']
            self.domains_subscribers = os.environ['DOMAINS_SUBSCRIBERS'] # TODO 'domains_subscribers' should be validated with regex as comma separated valid email addresses 
        except KeyError as err:
            print(f'Please set missing env variable for script to work: {err!s}')
        self.messages_to_send = None

    def read_messages_to_send(self):
        ""
        try:
            with open(self.dbfile, 'r') as f:
                dbfile_dict = json.load(f)
        except FileNotFoundError as err:
            raise FileNotFoundError(f"DB FILE missing ({err.filename}). Call 'get_domains.py scrape-domains' first")
        if sent_messages := dbfile_dict.get('sent_messages', []):
            self.messages_to_send = {
                msg: domains
                for msg, domains in dbfile_dict['domains'].items()
                if msg not in sent_messages 
            }
        else:
            self.messages_to_send = dbfile_dict['domains']
        # TODO substitute with logging
        print("messages to send:")
        pprint(self.messages_to_send)
    
    def update_sent_messages(self):
        with open(self.dbfile, 'r') as f:
            dbfile_dict = json.load(f)
        if 'sent_messages' in dbfile_dict:
            dbfile_dict['sent_messages'].extend(list(self.messages_to_send.keys()))
        else:
            dbfile_dict['sent_messages'] = list(self.messages_to_send.keys())
        with open(self.dbfile, 'w') as f:
            dbfile_dict = json.dump(dbfile_dict, f, indent=2)

    def send_email(self):
        self.read_messages_to_send()
        if not self.messages_to_send:
            # TODO substitute with logging
            print("No new messages, skipping email sending")
            return
        self.update_sent_messages()
        msg = EmailMessage()
        msg['From'] = self.sender
        msg['To'] = self.domains_subscribers
        today = date.today().strftime('%B %d, %Y')
        msg['Subject'] = f'Domain Scraper update for {today}'
        msg.set_content(json.dumps(self.messages_to_send))
        # TODO substitute print with logging
        print(f'Sending email to {self.domains_subscribers}')
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
            server.login(self.sender, self.password)
            server.send_message(msg)
