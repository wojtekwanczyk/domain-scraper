"""Argument parser for domain-scraper module"""

import argparse
import os
import shutil
import sys

from email.parser import BytesHeaderParser
from email.policy import default
from time import time

from domain_scraper import GmailMailer
from domain_scraper import DomainScraper


INPUT_DIR = os.environ.get('INPUT_DIR', 'emails/input')
ARCHIVE_DIR = os.environ.get('ARCHIVE_DIR', 'emails/archive')
DB_FILE = os.environ.get('DB_FILE', 'db/email_database.json')

def main():
    """Parse arguments from command line"""
    parser = argparse.ArgumentParser("Scrape domains from emails and send summary email")
    parser.add_argument('-e', '--email', help="Path to single email to scrape")
    parser.add_argument('-d', '--dbfile', default=DB_FILE,
                        help="File to save scraped domains")
    parser.add_argument('-i', '--input-dir', default=INPUT_DIR,
         help="Input directory to read emails")
    parser.add_argument('-a', '--archive-dir', default=ARCHIVE_DIR,
        help="Archive directory to move emails")
    parser.add_argument('-f', '--force', action='store_true', default=False,
        help="Force sending email with all scraped domains instead of only new emails")
    subparsers = parser.add_subparsers()

    scrape_parser = subparsers.add_parser('scrape')
    scrape_parser.set_defaults(func=scrape)

    send_parser = subparsers.add_parser('send')
    send_parser.set_defaults(func=send)

    default_parser = subparsers.add_parser('scrape-and-send')
    default_parser.set_defaults(func=scrape_and_send)

    clean_parser = subparsers.add_parser('clean')
    clean_parser.set_defaults(func=clean)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        args.func = scrape_and_send

    return args.func(args)

def scrape(args):
    """Scrape domains from emails from input_dir and print them"""
    emails = read_emails_from_dir(args.input_dir, args.archive_dir)
    scraper = DomainScraper()
    scraper.scrape_from_emails(emails)
    scraper.save(args.dbfile)

def send(args):
    """Read domains from file and send email with update to DOMAIN_SUBSCRIBERS"""
    try:
        # TODO: 'domains_subscribers' should be validated with regex
        # as comma separated valid email addresses
        subscribers = os.environ['DOMAINS_SUBSCRIBERS']
    except KeyError:
        print("DOMAINS_SUBSCRIBERS variable is not set, cannot send summary; exiting...")
        return
    mailer = GmailMailer(args.dbfile, subscribers)
    mailer.send_email(all_emails=args.force)

def scrape_and_send(args):
    """Default command: Scrape domains and send email with summary"""
    scrape(args)
    send(args)

def clean(args):
    """
    For testing purposes.
    Remove dbfile, move content from archive_dir to input_dir.
    """
    if os.path.isfile(args.dbfile):
        os.unlink(args.dbfile)

    if not os.path.isdir(args.input_dir):
        os.mkdir(args.input_dir)

    if os.path.isdir(args.archive_dir):
        file_names = os.listdir(args.archive_dir)
        for filename in file_names:
            filepath = os.path.join(args.archive_dir, filename)
            # remove timestamps
            original_filename = filename.rsplit(sep='_', maxsplit=1)[0]
            original_filepath = os.path.join(args.input_dir, original_filename)
            shutil.move(filepath, original_filepath)

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


if __name__ == '__main__':
    sys.exit(main())
