"""Argument parser for domain-scraper module"""

import logging
import os
import shutil
import sys
from argparse import ArgumentParser
from argparse import Namespace
from time import time
from typing import Optional
from email.message import Message
from email.parser import BytesHeaderParser
from email.policy import default

from .gmail_mailer import GmailMailer
from .domain_scraper import DomainScraper


INPUT_DIR = os.environ.get("INPUT_DIR", "emails/input")
ARCHIVE_DIR = os.environ.get("ARCHIVE_DIR", "emails/archive")
DB_FILE = os.environ.get("DB_FILE", "db/email_database.json")

logger = logging.getLogger(__name__)


def parse_arguments() -> Namespace:
    """Parse arguments from command line"""
    parser = ArgumentParser(
        "Scrape domains from emails and send summary email"
    )
    parser.add_argument("-e", "--email", help="Path to single email to scrape")
    parser.add_argument(
        "-d", "--dbfile", default=DB_FILE, help="File to save scraped domains"
    )
    parser.add_argument(
        "-i", "--input-dir", default=INPUT_DIR, help="Input directory to read emails"
    )
    parser.add_argument(
        "-a",
        "--archive-dir",
        default=ARCHIVE_DIR,
        help="Archive directory to move emails",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force sending email with all scraped domains instead of only new emails",
    )
    parser.add_argument(
        "-l",
        "--logging-level",
        default="DEBUG",
        help="Set logging level",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
    )
    subparsers = parser.add_subparsers()

    scrape_parser = subparsers.add_parser("scrape")
    scrape_parser.set_defaults(func=scrape)

    send_parser = subparsers.add_parser("send")
    send_parser.set_defaults(func=send)

    default_parser = subparsers.add_parser("scrape-and-send")
    default_parser.set_defaults(func=scrape_and_send)

    clean_parser = subparsers.add_parser("clean")
    clean_parser.set_defaults(func=clean)

    return parser.parse_args()


def scrape(args: Namespace) -> None:
    """Scrape domains from emails from input_dir and print them"""
    emails = read_emails_from_dir(args.input_dir, args.archive_dir)
    scraper = DomainScraper()
    scraper.scrape_from_emails(emails)
    scraper.save(args.dbfile)


def send(args: Namespace) -> Optional[int]:
    """Read domains from file and send email with update to DOMAIN_SUBSCRIBERS"""
    try:
        subscribers = os.environ["DOMAINS_SUBSCRIBERS"]
    except KeyError:
        logger.error(
            "DOMAINS_SUBSCRIBERS variable is not set, cannot send summary; exiting..."
        )
        return 1
    mailer = GmailMailer(args.dbfile, subscribers)
    mailer.send_email(all_emails=args.force)
    return 0


def scrape_and_send(args: Namespace) -> Optional[int|None]:
    """Default command: Scrape domains and send email with summary"""
    scrape(args)
    return send(args)


def clean(args: Namespace) -> None:
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
            original_filename = filename.rsplit(sep="_", maxsplit=1)[0]
            original_filepath = os.path.join(args.input_dir, original_filename)
            shutil.move(filepath, original_filepath)


def read_emails_from_dir(input_dir: str, archive_dir: str) -> list[Message]:
    """Parse emails from input_dir, move them to archive_dir"""
    emails_list: list[Message] = []
    if not os.path.isdir(input_dir):
        logger.warning("INPUT_DIR (%s) does not exist!", input_dir)
        return emails_list  # empty list
    if not os.path.isdir(archive_dir):
        os.mkdir(archive_dir)

    parser = BytesHeaderParser(policy=default)
    for email_filename in os.listdir(input_dir):

        # read and parse email
        email_path = os.path.join(input_dir, email_filename)
        with open(email_path, "rb") as file:
            email: Message = parser.parse(file)
            emails_list.append(email)

        # move parsed email to ARCHIVE_DIR
        # timestamp added to avoid OSError during renaming
        new_email_name = email_filename + "_{}".format(int(time()))
        new_email_path = os.path.join(archive_dir, new_email_name)
        shutil.move(email_path, new_email_path)
    return emails_list


def main() -> Optional[int|None]:
    """Configure logging, parse arguments and invoke proper function"""

    args = parse_arguments()
    if not hasattr(args, "func"):
        args.func = scrape_and_send

    logging.basicConfig(level=args.logging_level)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
