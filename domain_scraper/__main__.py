#!/usr/bin/env python3

import click
import os
import shutil

from email.parser import BytesHeaderParser
from email.policy import default
from time import time

from domain_scraper import DomainMailer
from domain_scraper import DomainScraper


# TODO could be moved to separate config file
INPUT_DIR = os.environ.get('INPUT_DIR', 'emails/input')
ARCHIVE_DIR = os.environ.get('ARCHIVE_DIR', 'emails/archive')
DB_FILE = os.environ.get('DB_FILE', 'db/email_database.json')

def read_emails_from_dir(input_dir, archive_dir):
    if not os.path.isdir(archive_dir):
        os.mkdir(archive_dir)

    emails = []
    parser = BytesHeaderParser(policy=default)
    for email_filename in os.listdir(input_dir):
        email_path = os.path.join(input_dir, email_filename)
        # throws FileNotFoundError on non-existent dir
        with open(email_path, 'rb') as ef:
            emails.append(parser.parse(ef))
        new_email_name = f"{email_filename}_{str(int(time()))}" # timestamp added to avoid OSError during renaming
        new_email_path = os.path.join(archive_dir, new_email_name)
        shutil.move(email_path, new_email_path) # move parsed emails to archive
    return emails


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
@click.option('-a', '--all', is_flag=True, help='Send email with all scraped domains instead of only new emails')
def send(dbfile, all):
    """Read domains from file and send email with update to DOMAIN_SUBSCRIBERS"""
    try:
        subscribers = os.environ['DOMAINS_SUBSCRIBERS'] # TODO 'domains_subscribers' should be validated with regex as comma separated valid email addresses 
    except KeyError:
        print("DOMAINS_SUBSCRIBERS variable is not set, cannot send summary; exiting...")
        return
    mailer = DomainMailer(dbfile, subscribers)
    mailer.send_email(all=all)

@cli.command()
def clean():
    """For testing purposes: remove DB_FILE, rename ARCHIVE_DIR to INPUT_DIR"""
    if os.path.isdir(ARCHIVE_DIR):
        file_names = os.listdir(ARCHIVE_DIR)
        for file_name in file_names:
            shutil.move(os.path.join(ARCHIVE_DIR, file_name), INPUT_DIR)
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

