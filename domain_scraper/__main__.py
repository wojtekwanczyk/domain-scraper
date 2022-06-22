"""Argument parser for domain-scraper module"""

import os
import shutil

from email.parser import BytesHeaderParser
from email.policy import default
from time import time

import click

from domain_scraper import GmailMailer
from domain_scraper import DomainScraper


INPUT_DIR = os.environ.get('INPUT_DIR', 'emails/input')
ARCHIVE_DIR = os.environ.get('ARCHIVE_DIR', 'emails/archive')
DB_FILE = os.environ.get('DB_FILE', 'db/email_database.json')

def read_emails_from_dir(input_dir, archive_dir):
    """Parse emails from input_dir, move them to archive_dir"""
    emails_list = []
    if not os.path.isdir(input_dir):
        print(f"INPUT_DIR ({input_dir}) does not exist!")
        return emails_list # empty list
    if not os.path.isdir(archive_dir):
        os.mkdir(archive_dir)

    parser = BytesHeaderParser(policy=default)
    for email_filename in os.listdir(input_dir):
        # TODO: what if file is not a valid email?

        # read and parse email
        email_path = os.path.join(input_dir, email_filename)
        with open(email_path, 'rb') as file:
            emails_list.append(parser.parse(file))

        # move parsed email to ARCHIVE_DIR
        # timestamp added to avoid OSError during renaming
        new_email_name = f"{email_filename}_{str(int(time()))}"
        new_email_path = os.path.join(archive_dir, new_email_name)
        shutil.move(email_path, new_email_path)
    return emails_list


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        scrape_and_send.callback(INPUT_DIR, ARCHIVE_DIR, DB_FILE)

@cli.command()
@click.option('-i', '--input-dir', default=INPUT_DIR, help='Input directory to read emails')
@click.option('-a', '--archive-dir', default=ARCHIVE_DIR, help='Archive directory to move emails')
@click.option('-f', '--dbfile', default=DB_FILE, help='File to save scraped domains')
def scrape(input_dir, archive_dir, dbfile):
    """Scrape domains from emails from input_dir and print them"""
    emails = read_emails_from_dir(input_dir, archive_dir)
    scraper = DomainScraper()
    scraper.scrape_from_emails(emails)
    scraper.save(dbfile)

@cli.command()
@click.option('-f', '--dbfile', default=DB_FILE, help='File with scraped domains')
@click.option('-a', '--all-emails', is_flag=True, help='Send email with all scraped domains instead of only new emails')
def send(dbfile, all_emails):
    """Read domains from file and send email with update to DOMAIN_SUBSCRIBERS"""
    try:
        # TODO: 'domains_subscribers' should be validated with regex
        # as comma separated valid email addresses
        subscribers = os.environ['DOMAINS_SUBSCRIBERS']
    except KeyError:
        print("DOMAINS_SUBSCRIBERS variable is not set, cannot send summary; exiting...")
        return
    mailer = GmailMailer(dbfile, subscribers)
    mailer.send_email(all_emails=all_emails)

@cli.command()
def clean():
    """For testing purposes: remove DB_FILE, rename ARCHIVE_DIR to INPUT_DIR"""
    if not os.path.isdir(INPUT_DIR):
        os.mkdir(INPUT_DIR)

    if os.path.isdir(ARCHIVE_DIR):
        file_names = os.listdir(ARCHIVE_DIR)
        for filename in file_names:
            filepath = os.path.join(ARCHIVE_DIR, filename)
            # remove timestamps
            original_filename = filename.rsplit(sep='_', maxsplit=1)[0]
            original_filepath = os.path.join(INPUT_DIR, original_filename)
            shutil.move(filepath, original_filepath)
    if os.path.isfile(DB_FILE):
        os.unlink(DB_FILE)

@cli.command()
@click.option('-i', '--input-dir', default=INPUT_DIR, help='Input directory to read emails')
@click.option('-a', '--archive-dir', default=ARCHIVE_DIR, help='Archive directory to move emails')
@click.option('-f', '--dbfile', default=DB_FILE, help='File to save scraped domains')
def scrape_and_send(input_dir, archive_dir, dbfile):
    """Default command: Scrape domains and send email with summary"""
    scrape.callback(input_dir, archive_dir, dbfile)
    send.callback(dbfile, False)


if __name__ == '__main__':
    cli()
