import click
import json
import os
import re
import ssl
import smtplib

from collections import defaultdict
from datetime import date
from email.message import EmailMessage
from email.parser import BytesHeaderParser
from email.policy import default
from pprint import pprint


INPUT_DIR = 'input'
DB_FILE = 'email_database.json'


class DomainScraper:
    def __init__(self):
        separators = 'from|by|via|with|id|for|;'
        self.from_regex = re.compile(f'from\s+(.+?)\s+({separators})')
        self.by_regex = re.compile(f'by\s+(.+?)\s+({separators})')
        self.domains = dict()

    def scrape_from_emails(self, emails):
        for email in emails:
            email_domains = self.get_domains_for_email(email)
            self.domains.update(email_domains)

    def get_domains_for_email(self, email):
        received_headers = email.get_all('Received')
        email_domains = set()
        for received in received_headers:
            if domain := self.from_regex.search(received):
                email_domains.add(domain.group(1))
            if domain := self.by_regex.search(received):
                email_domains.add(domain.group(1))
        message_id = email['Message-ID'].strip('\t<>')
        return {message_id: list(email_domains)}
    
    def save(self, dbfile):
        try:
            with open(dbfile, 'r') as f:
                dbfile_dict = json.load(f)
        except FileNotFoundError:
            dbfile_dict = defaultdict(dict)
        dbfile_dict['domains'] = self.domains
        pprint(dbfile_dict)
        with open(dbfile, 'w') as f:
            json.dump(dbfile_dict, f, indent=2)

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


def read_emails_from_dir(input_dir):
    emails = []
    parser = BytesHeaderParser(policy=default)
    for email_filename in os.listdir(input_dir):
        email_path = os.path.join(input_dir, email_filename)
        # throws FileNotFoundError on non-existent dir
        with open(email_path, 'rb') as ef:
            emails.append(parser.parse(ef))
    return emails


@click.group()
def cli():
    pass

@cli.command()
@click.option('-i', '--input-dir', default=INPUT_DIR, help='Input directory to read emails')
@click.option('-f', '--dbfile', default=DB_FILE, help='File to save scraped domains')
def scrape_domains(input_dir, dbfile):
    """Scrape domains from emails from input_dir and print them"""
    emails = read_emails_from_dir(input_dir)
    scraper = DomainScraper()
    scraper.scrape_from_emails(emails)
    scraper.save(dbfile)

@cli.command()
@click.option('-f', '--dbfile', default=DB_FILE, help='File with scraped domains')
def send_summary(dbfile):
    """Read domains from file and send email with update to DOMAIN_SUBSCRIBERS"""
    # TODO add option to send all domains, not only gatehered since last email
    mailer = DomainMailer(DB_FILE)
    mailer.send_email()

if __name__ == '__main__':
    cli()

