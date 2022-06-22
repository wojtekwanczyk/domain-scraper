"""Prepares and sends email with scraped domains to DOMAINS_SUBSCRIBERS"""

import json
import logging
import os
import ssl
import smtplib

from datetime import date
from pprint import pformat
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pkg_resources
from jinja2 import Template


logger = logging.getLogger(__name__)


class GmailMailer:
    """Prepares and sends email with scraped domains to DOMAINS_SUBSCRIBERS"""

    def __init__(self, dbfile, subscribers):
        self.host = "smtp.gmail.com"
        self.port = 465
        self.dbfile = dbfile
        self.subscribers = subscribers
        try:
            self.sender = os.environ["GMAIL_APP_USERNAME"]
            self.password = os.environ["GMAIL_APP_PASSWORD"]
        except KeyError as err:
            logger.error(
                "Please set missing env variable for script to work: %s", str(err)
            )
        self.emails_to_send = None
        self.msg = None

    def read_emails_to_send(self, all_emails=False):
        """
        Reads emails from dbfile and
        filters out only not sent messages (if 'all_emails' is set to False)

        Throws FileNotFoundError when DB_FILE does not exist
        """
        with open(self.dbfile, "r", encoding="utf-8") as file:
            dbfile_dict = json.load(file)

        sent_emails = dbfile_dict.get("sent_emails", [])
        if not sent_emails or all_emails:
            self.emails_to_send = dbfile_dict["domains"]
        else:
            self.emails_to_send = {
                msg: domains
                for msg, domains in dbfile_dict["domains"].items()
                if msg not in sent_emails
            }
        logger.debug("messages to send:\n%s", pformat(self.emails_to_send))

    def update_sent_emails(self):
        """Updates sent emails in dbfile to avoid sending duplicated emails (same Message-ID)"""
        with open(self.dbfile, "r", encoding="utf-8") as file:
            dbfile_dict = json.load(file)

        unique_new_msgids = set(self.emails_to_send.keys())
        if "sent_emails" in dbfile_dict:
            unique_old_msgids = set(dbfile_dict["sent_emails"])
            merged_msgids = unique_old_msgids.union(unique_new_msgids)
            dbfile_dict["sent_emails"] = list(merged_msgids)
        else:
            dbfile_dict["sent_emails"] = list(unique_new_msgids)

        with open(self.dbfile, "w", encoding="utf-8") as file:
            json.dump(dbfile_dict, file, indent=2)

    def prepare_msg(self):
        """Prepare MIMEMultipart message"""
        self.msg = MIMEMultipart("alternative")
        self.msg["From"] = self.sender
        self.msg["To"] = self.subscribers
        today = date.today().strftime("%B %d, %Y")
        self.msg["Subject"] = "Domain Scraper update for {}".format(today)

        html_template_resource = pkg_resources.resource_filename(
            __name__, "templates/summary.html"
        )
        with open(html_template_resource, encoding="utf-8") as file:
            html_template = Template(file.read())
        html_body = html_template.render(domains=self.emails_to_send)
        part1 = MIMEText(json.dumps(self.emails_to_send, indent=2), "plain")
        part2 = MIMEText(html_body, "html")
        self.msg.attach(part1)
        self.msg.attach(part2)

    def send_email(self, all_emails=False):
        """
        Send email to DOMAINS_SUBSCRIBERS
        Returns False if dbfile is missing or no new domains are scraped
        """
        try:
            self.read_emails_to_send(all_emails=all_emails)
        except FileNotFoundError as err:
            logger.warning(
                "DB FILE missing: (%s). Please run domain scraping first", err.filename
            )
            return False
        if not self.emails_to_send:
            logger.info("No new messages, skipping email sending")
            return False

        self.update_sent_emails()
        self.prepare_msg()

        logger.info("Sending email to %s", self.subscribers)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
            server.login(self.sender, self.password)
            server.send_message(self.msg)
        logger.info("Email sent.")
        return True
