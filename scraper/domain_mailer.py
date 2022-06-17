import json
import os
import ssl
import smtplib

from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
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
        self.msg = None

    def read_messages_to_send(self, all=False):
        ""
        try:
            with open(self.dbfile, 'r') as f:
                dbfile_dict = json.load(f)
        except FileNotFoundError as err:
            raise FileNotFoundError(f"DB FILE missing ({err.filename}). Call 'get_domains.py scrape-domains' first")
        sent_messages = dbfile_dict.get('sent_messages', [])
        if not sent_messages or all:
            self.messages_to_send = dbfile_dict['domains']
        else:
            self.messages_to_send = {
                msg: domains
                for msg, domains in dbfile_dict['domains'].items()
                if msg not in sent_messages 
            }
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

    def prepare_msg(self):
        self.msg = MIMEMultipart('alternative')
        self.msg['From'] = self.sender
        self.msg['To'] = self.domains_subscribers
        today = date.today().strftime('%B %d, %Y')
        self.msg['Subject'] = f'Domain Scraper update for {today}'

        with open('templates/summary.html') as f:
            html_template = Template(f.read())
        html_body = html_template.render(domains=self.messages_to_send)
        part1 = MIMEText(json.dumps(self.messages_to_send, indent=2), 'plain')
        part2 = MIMEText(html_body, 'html')
        self.msg.attach(part1)
        self.msg.attach(part2)

    def send_email(self, all=False):
        self.read_messages_to_send(all=all)
        if not self.messages_to_send:
            # TODO substitute with logging
            print("No new messages, skipping email sending")
            return

        self.update_sent_messages()
        self.prepare_msg()

        # TODO substitute print with logging
        print(f'Sending email to {self.domains_subscribers}')
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
            server.login(self.sender, self.password)
            server.send_message(self.msg)
