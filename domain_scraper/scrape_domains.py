"""Script for scraping domains from Received headers of email Messages."""

import argparse
import collections
import datetime
import email
import json
import logging
import os
import re
import shutil
import smtplib
import ssl
import sys
import time

from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jinja2
import pkg_resources

from domain_scraper import config
from domain_scraper.parser import parse_arguments

logger = logging.getLogger(__name__)
REGEX_FROM = re.compile(r"from\s+(.+?)\s+(by|via|with|id|for|;)")
REGEX_BY = re.compile(r"by\s+(.+?)\s+(from|via|with|id|for|;)")
CONFIG = config.DEVELOPMENT


class MessageDomains:

    """Represents scraped domains from regular email Message object.

    This class uses global variables:
        - REGEX_FROM
        - REGEX_BY
    """

    def __init__(self, msg: Message):
        """Scrapes all domains from "Received" headers of msg object."""
        self.msgid = msg.get('Message-ID')
        received_headers = msg.get_all("Received")
        domains_set = set()  # use set to avoid duplicates
        for received_header in received_headers:
            if domain := REGEX_FROM.search(received_header):
                domains_set.add(domain.group(1))
            if domain := REGEX_BY.search(received_header):
                domains_set.add(domain.group(1))
        self.domains = list(domains_set)

    def __str__(self) -> str:
        """Returns str representation of MessageDomains."""
        domains_str = "\n\t".join(self.domains)
        return "MsgID {}:\n\t{}".format(self.msgid, domains_str)


def make_parent_dir(file: str) -> None:
    """Create file's parent directory if it does not exist."""
    dirname = os.path.dirname(file)
    if dirname and not os.path.exists(dirname):
        logger.debug(
            "Parent directory for %s does not exists, creating %s", file, dirname
        )
        os.makedirs(dirname)


def is_input_correct(args: argparse.Namespace) -> bool:
    """Assures that required directories and files from args exist."""
    if args.save_to_file:
        make_parent_dir(args.dbfile)

    if args.email:
        if not os.path.isfile(args.email):
            logger.error("Email file does not exist: %s", args.email)
            return False
    else:
        if not os.path.isdir(args.archive_dir):
            os.makedirs(args.archive_dir)
        if not os.path.isdir(args.input_dir):
            logger.error("INPUT_DIR (%s) does not exist!", args.input_dir)
            return False

    if args.send_email and not all(CONFIG.values()):
        logger.error("Please set required environmental variables to send email")
        return False

    return True


def parse_emails(input_dir: str, archive_dir: str) -> list[MessageDomains]:
    """Parses emails from input_dir and moves them to archive_dir."""
    result = []
    for email_name in os.listdir(input_dir):
        email_file = os.path.join(input_dir, email_name)
        with open(email_file, "rb") as file:
            msg = email.message_from_binary_file(file)
        archive_email(email_file, archive_dir)
        result.append(MessageDomains(msg))
    return result


def archive_email(email_file: str, archive_dir: str) -> None:
    """Move email to archive_dir."""
    email_name = os.path.basename(email_file)
    new_email_name = email_name + "_{}".format(int(time.time()))
    new_email_file = os.path.join(archive_dir, new_email_name)
    shutil.move(email_file, new_email_file)


def append_to_dbfile(data: list[MessageDomains], file: str) -> None:
    """Append scraped domains to dbfile.

    If file does not exist, it will be created.
    """
    try:
        with open(file, "r") as file_handle:
            dbfile_dict = json.load(file_handle)
    except FileNotFoundError:
        dbfile_dict = collections.defaultdict(dict)

    for msg in data:
        dbfile_dict["messages"].update({msg.msgid: msg.domains})

    logger.debug("Saving result to file: %s", file)
    with open(file, "w") as file_handle:
        json.dump(dbfile_dict, file_handle, indent=2)


def prepare_msg(data: list[MessageDomains]) -> Message:
    """Prepare MIMEMultipart message."""
    msg = MIMEMultipart("alternative")
    today = datetime.date.today().strftime("%B %d, %Y")
    msg["Subject"] = f"Domain Scraper update for {today}"
    msg["To"] = CONFIG['DOMAINS_SUBSCRIBERS']

    html_template_resource = pkg_resources.resource_filename(
        __name__, "templates/summary.html"
    )
    with open(html_template_resource) as file:
        html_template = jinja2.Template(file.read())
    html_body = html_template.render(messages=data)
    part1 = MIMEText("\n".join(map(str, data)), "plain")
    part2 = MIMEText(html_body, "html")
    msg.attach(part1)
    msg.attach(part2)

    return msg


def send_email(data: list[MessageDomains]) -> int:
    """Sends data to DOMAINS_SUBSCRIBERS."""
    msg = prepare_msg(data)
    logger.info("Sending email to %s", CONFIG['DOMAINS_SUBSCRIBERS'])
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        CONFIG['EMAIL_HOST'], CONFIG['EMAIL_PORT'], context=context
    ) as server:
        server.login(CONFIG['GMAIL_APP_USERNAME'], CONFIG['GMAIL_APP_PASSWORD'])
        server.send_message(msg)
    logger.info("Email sent.")
    return 0


def clean(args: argparse.Namespace) -> None:
    """Remove dbfile, move content from archive_dir to input_dir.

    Only for testing purposes.
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


def main() -> int:
    """Configure logging, parse arguments and invoke proper functions."""

    args = parse_arguments()
    logging.basicConfig(level=args.logging_level)

    if not is_input_correct(args):
        return 1

    if args.clean:
        clean(args)
        return 0

    if args.email:
        logger.debug("Scraping from single file: %s", args.email)
        with open(args.email, "rb") as file:
            msg = email.message_from_binary_file(file)
        data = [MessageDomains(msg)]
    else:
        logger.debug("Scraping from input dir: %s", args.input_dir)
        data = parse_emails(args.input_dir, args.archive_dir)

    if data:
        if args.save_to_file:
            append_to_dbfile(data, args.dbfile)

        if args.print:
            print("\n".join(map(str, data)))

        if args.send_email:
            send_email(data)
    else:
        logger.warning("No new messages")

    return 0


if __name__ == "__main__":
    sys.exit(main())
