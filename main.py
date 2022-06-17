import click
import os

from email.parser import BytesHeaderParser
from email.policy import default

from scraper import DomainMailer
from scraper import DomainScraper


# TODO could be moved to separate config file
INPUT_DIR = 'input'
DB_FILE = 'email_database.json'

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

