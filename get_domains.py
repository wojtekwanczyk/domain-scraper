import click
import json
import os
import re

from collections import defaultdict
from email.parser import BytesHeaderParser
from email.policy import default
from pprint import pprint

INPUT_DIR = 'input'
DB_FILE = 'email_database.json'


def read_emails_from_dir(input_dir):
    emails = []
    parser = BytesHeaderParser(policy=default)
    for email_filename in os.listdir(input_dir):
        email_path = os.path.join(input_dir, email_filename)
        # throws FIleNotFoundError on non-existent dir
        with open(email_path, 'rb') as ef:
            emails.append(parser.parse(ef))
    return emails


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
    pass

if __name__ == '__main__':
    cli()

