"""Argument parser for domain-scraper module"""

import logging
import os
import shutil
from argparse import ArgumentParser
from argparse import Namespace
from typing import Optional

from .config import DEVELOPMENT as CONFIG
from .gmail_mailer import GmailMailer
from .domain_scraper import DomainScraper
from .email_parser import EmailParser


logger = logging.getLogger(__name__)


def parse_arguments() -> Namespace:
    """Parse arguments from command line"""
    parser = ArgumentParser("Scrape domains from emails and send summary email")
    parser.add_argument("-e", "--email", help="Path to single email to scrape")
    parser.add_argument(
        "-d",
        "--dbfile",
        default=CONFIG["DB_FILE"],
        help="File to save scraped domains",
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        default=CONFIG["INPUT_DIR"],
        help="Input directory to read emails",
    )
    parser.add_argument(
        "-a",
        "--archive-dir",
        default=CONFIG["ARCHIVE_DIR"],
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
    scrape_parser.add_argument(
        "-e",
        "--email",
        help="Path to single email to scrape; with this option,"
        "input-dir is ignored and scraped domains are printed to stdout",
    )

    send_parser = subparsers.add_parser("send")
    send_parser.set_defaults(func=send)

    default_parser = subparsers.add_parser("scrape-and-send")
    default_parser.set_defaults(func=scrape_and_send)

    clean_parser = subparsers.add_parser("clean")
    clean_parser.set_defaults(func=clean)

    return parser.parse_args()


def scrape(args: Namespace) -> None:
    """Scrape domains from emails and save them to dbfile"""
    email_parser = EmailParser(args.archive_dir)
    if args.email:
        logger.debug("Scraping from single file: %s", args.email)
        emails = [email_parser.parse_email(args.email)]
    else:
        logger.debug("Scraping from input dir: %s", args.input_dir)
        emails = email_parser.parse_emails_from_dir(args.input_dir)

    scraper = DomainScraper()
    scraper.scrape_from_emails(emails)
    scraper.save(args.dbfile)

    if args.email:
        domains_list = next(iter(scraper.domains.values()))
        print("\n".join(domains_list))


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


def scrape_and_send(args: Namespace) -> Optional[int | None]:
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
