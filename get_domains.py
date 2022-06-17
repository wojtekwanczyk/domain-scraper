import click
import os
import re
from email.parser import BytesHeaderParser
from email.policy import default

INPUT_DIR = 'input'


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

    def get_domains_for_email(self, email):
        domains = set()
        received_headers = email.get_all('Received')
        for received in received_headers:
            if domain := self.from_regex.search(received):
                domains.add(domain.group(1))
            if domain := self.by_regex.search(received):
                domains.add(domain.group(1))
        return domains

    def scrape_from_emails(self, emails):
        domains = set()
        for email in emails:
            domains.update(self.get_domains_for_email(email))
        return domains


@click.group()
def cli():
    pass

@cli.command()
@click.option('-i', '--input-dir', default=INPUT_DIR, help='Input directory to read emails')
def scrape_domains(input_dir):
    """Scrape domains from emails from input_dir and print them"""
    emails = read_emails_from_dir(input_dir)
    print(DomainScraper().scrape_from_emails(emails))

@cli.command()
def send_summary():
    """Read domains from file and send email with update to DOMAIN_SUBSCRIBERS"""
    pass

if __name__ == '__main__':
    cli()

