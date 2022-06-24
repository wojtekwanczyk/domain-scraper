"""Argument parser for domain-scraper module"""

import logging
import os
from argparse import ArgumentParser
from argparse import Namespace
from typing import Optional

from .config import DEVELOPMENT as CONFIG
from .gmail_mailer import GmailMailer


logger = logging.getLogger(__name__)


def parse_arguments() -> Namespace:
    """Parse arguments from command line"""
    parser = ArgumentParser("Scrape domains from emails and send summary email")
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
        "-s",
        "--save-to-file",
        action="store_true",
        default=False,
        help="Save scraped domains to dbfile instead of printing to stdout",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force sending email with all scraped domains instead of only new emails",
    )
    parser.add_argument(
        "-S",
        "--send-email",
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
    parser.add_argument(
        "-e",
        "--email",
        help="Path to only one email to scrape; with this option,"
        "input-dir is ignored",
    )
    parser.add_argument(
        "-c",
        "--clean",
        action="store_true",
        default=False,
        help="Development purposes: remove dbfile and move all emails "
        "from archive_dir back to input_dir",
    )

    return parser.parse_args()


def send(args: Namespace) -> Optional[int]:
    """Read domains from file and send email with update to DOMAIN_SUBSCRIBERS"""
    subscribers = os.environ["DOMAINS_SUBSCRIBERS"]
    mailer = GmailMailer(args.dbfile, subscribers)
    mailer.send_email(all_emails=args.force)
    return 0
