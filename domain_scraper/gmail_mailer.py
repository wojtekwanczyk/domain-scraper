import json
import os
import pkg_resources
import ssl
import smtplib

from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from pprint import pprint

class GmailMailer:
    def __init__(self, dbfile, subscribers):
        self.host = 'smtp.gmail.com'
        self.port = 465
        self.dbfile = dbfile
        self.subscribers = subscribers
        try:
            self.sender = os.environ['GMAIL_APP_USERNAME']
            self.password = os.environ['GMAIL_APP_PASSWORD']
        except KeyError as err:
            print(f'Please set missing env variable for script to work: {err!s}')
        self.emails_to_send = None
        self.msg = None

    def read_emails_to_send(self, all=False):
        """
        Reads emails from dbfile and 
        filters out only not sent messages (if 'all' is set to False)

        Throws FileNotFoundError when DB_FILE does not exist
        """
        with open(self.dbfile, 'r') as f:
            dbfile_dict = json.load(f)

        sent_emails = dbfile_dict.get('sent_emails', [])
        if not sent_emails or all:
            self.emails_to_send = dbfile_dict['domains']
        else:
            self.emails_to_send = {
                msg: domains
                for msg, domains in dbfile_dict['domains'].items()
                if msg not in sent_emails 
            }
        # TODO substitute with logging
        print("messages to send:")
        pprint(self.emails_to_send)
    
    def update_sent_emails(self):
        """Updates sent emails in dbfile to avoid sending duplicated emails (same Message-ID)"""
        with open(self.dbfile, 'r') as f:
            dbfile_dict = json.load(f)

        unique_new_msgids = set(self.emails_to_send.keys())
        if 'sent_emails' in dbfile_dict:
            unique_old_msgids = set(dbfile_dict['sent_emails'])
            merged_msgids = unique_old_msgids.union(unique_new_msgids)
            dbfile_dict['sent_emails'] = list(merged_msgids)
        else:
            dbfile_dict['sent_emails'] = list(unique_new_msgids)

        with open(self.dbfile, 'w') as f:
            dbfile_dict = json.dump(dbfile_dict, f, indent=2)

    def prepare_msg(self):
        self.msg = MIMEMultipart('alternative')
        self.msg['From'] = self.sender
        self.msg['To'] = self.subscribers
        today = date.today().strftime('%B %d, %Y')
        self.msg['Subject'] = f'Domain Scraper update for {today}'

        html_template_resource = pkg_resources.resource_filename(__name__, 'templates/summary.html')
        with open(html_template_resource) as f:
            html_template = Template(f.read())
        html_body = html_template.render(domains=self.emails_to_send)
        part1 = MIMEText(json.dumps(self.emails_to_send, indent=2), 'plain')
        part2 = MIMEText(html_body, 'html')
        self.msg.attach(part1)
        self.msg.attach(part2)

    def send_email(self, all=False):
        try:
            self.read_emails_to_send(all=all)
        except FileNotFoundError as err:
            print(f"DB FILE missing: ({err.filename}). Please run domain scraping first")
            return False
        if not self.emails_to_send:
            # TODO substitute with logging
            print("No new messages, skipping email sending")
            return False

        self.update_sent_emails()
        self.prepare_msg()

        # TODO substitute print with logging
        print(f'Sending email to {self.subscribers}')
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
            server.login(self.sender, self.password)
            server.send_message(self.msg)
        print("Email sent.")
